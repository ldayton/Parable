#!/usr/bin/env python3
"""Transpile parable.py's restricted Python subset to Go."""

import ast
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from .go_emit_expr import EmitExpressionsMixin
from .go_emit_structure import EmitStructureMixin
from .go_manual import MANUAL_FUNCTIONS, MANUAL_METHODS
from .go_naming import NamingMixin
from .go_overrides import (
    FIELD_TYPE_OVERRIDES,
    TUPLE_ELEMENT_TYPES,
    UNION_FIELDS,
)
from .go_scope import ScopeAnalysisMixin
from .go_symbols import SymbolsMixin
from .go_type_system import KIND_TO_TYPE, TYPE_MAP, TypeSystemMixin
from .go_types import (
    FuncInfo,
    ParamInfo,
    ScopeInfo,
    SymbolTable,
    VarInfo,
)


class GoTranspiler(NamingMixin, TypeSystemMixin, SymbolsMixin, EmitExpressionsMixin, ScopeAnalysisMixin, EmitStructureMixin, ast.NodeVisitor):
    """Transpiles Python AST to Go source code."""

    def __init__(self):
        self.indent = 0
        self.output: list[str] = []
        self.symbols = SymbolTable()
        self.tree: ast.Module | None = None
        self.current_class: str | None = None
        self.current_method: str | None = None  # Current method name being emitted
        self.current_func_info: FuncInfo | None = None  # Current method's FuncInfo
        self.declared_vars: set[str] = set()  # Track declared local variables per function
        self.current_return_type: str = ""  # Go return type of current function/method
        self.byte_vars: set[str] = set()  # Track variables holding bytes (from string subscripts)
        self.tuple_vars: dict[str, list[str]] = {}  # Map tuple var name to element var names
        self.tuple_func_vars: dict[str, str] = {}  # Map var name to tuple-returning function name
        self.returned_vars: set[str] = set()  # Track variables used in return statements
        self.union_field_types: dict[
            tuple[str, str], str
        ] = {}  # Map (receiver, field) to current type
        self._type_switch_var: tuple[str, str] | None = (
            None  # (original_var, switch_var) during type switch
        )
        self._type_switch_type: str | None = None  # Current narrowed type in type switch case
        # Scope tracking for idiomatic variable declarations
        self.scope_tree: dict[int, ScopeInfo] = {}
        self.next_scope_id: int = 0
        self.var_usage: dict[str, VarInfo] = {}
        self.hoisted_vars: dict[str, int] = {}  # var -> scope_id to declare at
        self.scope_id_map: dict[int, int] = {}  # AST node id -> scope_id (for emission phase)

    def emit(self, text: str):
        """Emit a line of Go code at the current indentation level."""
        self.output.append("\t" * self.indent + text)

    def emit_raw(self, text: str):
        """Emit a line of Go code without indentation."""
        self.output.append(text)

    def transpile(self, source: str) -> str:
        """Transpile Python source to Go."""
        self.tree = ast.parse(source)
        # Pass 1-3: Build symbol table
        self._collect_symbols(self.tree)
        # Pass 4: Emit Go code
        self.visit(self.tree)
        return "\n".join(self.output)

    # ========== Code Emission ==========

    def _emit_function(self, node: ast.FunctionDef):
        """Emit a top-level function."""
        func_info = self.symbols.functions.get(node.name)
        if not func_info:
            return
        go_name = self._to_go_func_name(node.name)
        params_str = self._format_params(func_info.params)
        return_str = func_info.return_type
        if return_str:
            self.emit(f"func {go_name}({params_str}) {return_str} {{")
        else:
            self.emit(f"func {go_name}({params_str}) {{")
        self.indent += 1
        # Check for manually implemented functions first
        if node.name in MANUAL_FUNCTIONS:
            MANUAL_FUNCTIONS[node.name](self)
        # Skip body for complex functions
        elif node.name in self.SKIP_BODY_FUNCTIONS:
            self.emit('panic("TODO: function needs manual transpilation")')
        else:
            self._emit_body(node.body, func_info)
        self.indent -= 1
        self.emit("}")
        self.emit("")

    def _emit_all_methods(self, tree: ast.Module):
        """Emit methods for all classes."""
        # Skip error types (special handling) and Node (interface, no methods)
        skip = {"ParseError", "MatchedPairError", "Node"}
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name not in skip:
                self._emit_class_methods(node)

    def _emit_class_methods(self, node: ast.ClassDef):
        """Emit methods for a class."""
        class_info = self.symbols.classes[node.name]
        self.current_class = node.name
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef):
                self._emit_method(stmt, class_info)
        self.current_class = None

    def _emit_method(self, node: ast.FunctionDef, class_info: ClassInfo):
        """Emit a method."""
        if node.name == "__init__":
            self._emit_constructor(node, class_info)
            return
        if node.name == "__repr__":
            return  # Skip __repr__ for now
        func_info = class_info.methods.get(node.name)
        if not func_info:
            return
        # Track current method for return type inference
        self.current_method = node.name
        self.current_func_info = func_info
        go_name = self._to_go_func_name(node.name)
        params_str = self._format_params(func_info.params)
        return_str = func_info.return_type
        receiver = class_info.name[0].lower()
        if return_str:
            self.emit(
                f"func ({receiver} *{class_info.name}) {go_name}({params_str}) {return_str} {{"
            )
        else:
            self.emit(f"func ({receiver} *{class_info.name}) {go_name}({params_str}) {{")
        self.indent += 1
        # Check for manually implemented methods first
        manual_key = (class_info.name, node.name)
        if manual_key in MANUAL_METHODS:
            MANUAL_METHODS[manual_key](self, receiver)
        # Skip body for complex methods
        elif node.name in self.SKIP_METHODS:
            self.emit('panic("TODO: method needs manual implementation")')
        else:
            self._emit_body(node.body, func_info)
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.current_method = None
        self.current_func_info = None

    def _emit_constructor(self, node: ast.FunctionDef, class_info: ClassInfo):
        """Emit a constructor function."""
        func_info = class_info.methods.get("__init__")
        if not func_info:
            return
        params_str = self._format_params(func_info.params)
        receiver = class_info.name[0].lower()
        self.emit(f"func New{class_info.name}({params_str}) *{class_info.name} {{")
        self.indent += 1
        # Reset declared vars and add parameters
        self.declared_vars = set()
        for p in func_info.params:
            self.declared_vars.add(self._to_go_var(p.name))
        # Create the struct
        self.emit(f"{receiver} := &{class_info.name}{{}}")
        self.declared_vars.add(receiver)
        # Emit body
        self._emit_constructor_body(node.body, class_info)
        self.emit(f"return {receiver}")
        self.indent -= 1
        self.emit("}")
        self.emit("")

    def _emit_body(self, stmts: list[ast.stmt], func_info: FuncInfo | None = None):
        """Emit function/method body statements."""
        # Reset declared vars and add parameters
        self.declared_vars = set()
        self.byte_vars = set()  # Reset byte variable tracking
        self.var_types: dict[str, str] = {}  # Inferred types for local vars
        self.tuple_vars = {}  # Reset tuple variable tracking
        self.returned_vars = set()  # Reset returned variable tracking
        self.var_assign_sources: dict[str, str] = {}  # Track assignment sources for type inference
        # Reset scope tracking
        self.scope_tree = {0: ScopeInfo(0, None, 0)}
        self.next_scope_id = 1
        self.var_usage = {}
        self.hoisted_vars = {}
        self.scope_id_map = {}
        # Track return type for nil → zero value conversion
        self.current_return_type = func_info.return_type if func_info else ""
        if func_info:
            for p in func_info.params:
                go_name = self._to_go_var(p.name)
                self.declared_vars.add(go_name)
                self.var_types[go_name] = p.go_type
        # Pre-pass: analyze variable types from usage
        self._analyze_var_types(stmts)
        # Collect variable scopes and compute hoisting
        self._collect_var_scopes(stmts, scope_id=0)
        self._compute_hoisting()
        # Exclude variables that are only used in assign-check-return patterns
        # (these get rewritten to if tmp := ...; tmp != nil { return tmp })
        self._exclude_assign_check_return_vars(stmts)
        # Populate var_types with append element types for all vars (not just hoisted)
        # This ensures inline := declarations get correct types for empty list init
        self._populate_var_types_from_usage(stmts)
        # Emit hoisted declarations for function scope (scope 0)
        self._emit_hoisted_vars(0, stmts)
        # Pre-scan for variables used in return statements (needed for tuple passthrough)
        self._scan_returned_vars(stmts)
        # Emit all statements
        emitted_any = False
        skip_until = 0  # Skip statements consumed by type switch
        for i, stmt in enumerate(stmts):
            if i < skip_until:
                continue
            # Skip docstrings
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                if isinstance(stmt.value.value, str):
                    continue
            # Check for isinstance chain that can be emitted as type switch
            isinstance_chain = self._collect_isinstance_chain(stmts, i)
            if len(isinstance_chain) >= 1:
                try:
                    self._emit_type_switch(isinstance_chain[0][1], isinstance_chain)
                    emitted_any = True
                    skip_until = i + len(isinstance_chain)
                    continue
                except NotImplementedError as e:
                    self.emit(f'panic("TODO: {e}")')
                    emitted_any = True
                    skip_until = i + len(isinstance_chain)
                    continue
            # Check for assign-then-check-return pattern (typed-nil fix)
            assign_check = self._detect_assign_check_return(stmts, i)
            if assign_check:
                var_name, method_call, return_type = assign_check
                self._emit_assign_check_return(var_name, method_call, return_type)
                emitted_any = True
                skip_until = i + 2  # Skip both statements
                continue
            try:
                self._emit_stmt(stmt)
                emitted_any = True
            except NotImplementedError as e:
                self.emit(f'panic("TODO: {e}")')
                emitted_any = True
        # If function has return type but body is empty, add placeholder
        if not emitted_any:
            if func_info and func_info.return_type:
                self.emit('panic("TODO: empty body")')

    def _emit_stmts_with_patterns(self, stmts: list[ast.stmt]):
        """Emit statements with pattern detection for typed-nil fixes."""
        skip_until = 0
        for i, stmt in enumerate(stmts):
            if i < skip_until:
                continue
            # Check for assign-then-check-return pattern (typed-nil fix)
            assign_check = self._detect_assign_check_return(stmts, i)
            if assign_check:
                var_name, method_call, return_type = assign_check
                self._emit_assign_check_return(var_name, method_call, return_type)
                skip_until = i + 2  # Skip both statements
                continue
            try:
                self._emit_stmt(stmt)
            except NotImplementedError as e:
                self.emit(f'panic("TODO: {e}")')

    def _scan_returned_vars(self, stmts: list[ast.stmt]):
        """Pre-scan statements to find variables used in return statements."""
        for stmt in stmts:
            self._scan_stmt_for_returns(stmt)

    def _scan_stmt_for_returns(self, stmt: ast.stmt):
        """Recursively scan a statement for return statements with variable values."""
        if isinstance(stmt, ast.Return):
            if isinstance(stmt.value, ast.Name):
                var_name = self._to_go_var(stmt.value.id)
                self.returned_vars.add(var_name)
        elif isinstance(stmt, ast.If):
            for s in stmt.body:
                self._scan_stmt_for_returns(s)
            for s in stmt.orelse:
                self._scan_stmt_for_returns(s)
        elif isinstance(stmt, (ast.For, ast.While)):
            for s in stmt.body:
                self._scan_stmt_for_returns(s)
            for s in stmt.orelse:
                self._scan_stmt_for_returns(s)
        elif isinstance(stmt, ast.With):
            for s in stmt.body:
                self._scan_stmt_for_returns(s)
        elif isinstance(stmt, ast.Try):
            for s in stmt.body:
                self._scan_stmt_for_returns(s)
            for handler in stmt.handlers:
                for s in handler.body:
                    self._scan_stmt_for_returns(s)
            for s in stmt.orelse:
                self._scan_stmt_for_returns(s)
            for s in stmt.finalbody:
                self._scan_stmt_for_returns(s)

    def _analyze_var_types(self, stmts: list[ast.stmt]):
        """Pre-analyze statements to infer variable types from usage."""
        for stmt in stmts:
            self._analyze_stmt_var_types(stmt)

    def _analyze_stmt_var_types(self, stmt: ast.stmt):
        """Analyze a statement for variable type info."""
        # Handle annotated assignments: x: list[str] = []
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            var_name = self._to_go_var(stmt.target.id)
            try:
                py_type = ast.unparse(stmt.annotation)
                go_type = self._py_type_to_go(py_type)
                if go_type:
                    self.var_types[var_name] = go_type
            except Exception:
                pass
        if isinstance(stmt, ast.Assign):
            if len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                var_name = self._to_go_var(stmt.targets[0].id)
                # If assigning a list, track its type
                if isinstance(stmt.value, ast.List):
                    if not stmt.value.elts:
                        # Only set if not already known from annotation
                        if var_name not in self.var_types:
                            # For result variables, use return type if available
                            if var_name == "result" and self.current_return_type.startswith("[]"):
                                self.var_types[var_name] = self.current_return_type
                            else:
                                self.var_types[var_name] = "[]interface{}"  # default for empty
                    else:
                        # Infer from first element
                        elem_type = self._infer_literal_elem_type(stmt.value.elts[0])
                        if var_name not in self.var_types:
                            self.var_types[var_name] = f"[]{elem_type}"
                # If assigning from string subscript (single index, not slice), treat as string
                # (we convert to string() during emission)
                elif isinstance(stmt.value, ast.Subscript) and not isinstance(
                    stmt.value.slice, ast.Slice
                ):
                    if self._is_string_subscript(stmt.value):
                        self.var_types[var_name] = "string"
                # If assigning from a method call that returns string
                elif isinstance(stmt.value, ast.Call) and isinstance(
                    stmt.value.func, ast.Attribute
                ):
                    method = stmt.value.func.attr
                    if method in (
                        "join",
                        "lower",
                        "upper",
                        "strip",
                        "lstrip",
                        "rstrip",
                        "replace",
                        "format",
                        "decode",
                        "advance",
                        "peek",
                        "peek_at",
                    ):  # Parser methods returning string
                        self.var_types[var_name] = "string"
                # If assigning from _ternary(cond, a, b), infer type from a/b
                elif isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name):
                    if stmt.value.func.id == "_ternary" and len(stmt.value.args) >= 3:
                        # Check if either value arg is a string
                        if self._is_string_expr(stmt.value.args[1]) or self._is_string_expr(
                            stmt.value.args[2]
                        ):
                            self.var_types[var_name] = "string"
                # If assigning from inline ternary (a if cond else b), infer type from a/b
                elif isinstance(stmt.value, ast.IfExp):
                    if self._is_string_expr(stmt.value.body) or self._is_string_expr(
                        stmt.value.orelse
                    ):
                        self.var_types[var_name] = "string"
                # If assigning from self.field, infer type from field (for union types)
                elif isinstance(stmt.value, ast.Attribute):
                    if isinstance(stmt.value.value, ast.Name) and stmt.value.value.id == "self":
                        field_name = stmt.value.attr
                        if self.current_class:
                            class_info = self.symbols.classes.get(self.current_class)
                            if class_info and field_name in class_info.fields:
                                field_type = class_info.fields[field_name].go_type
                                if field_type:
                                    self.var_types[var_name] = field_type
        # Look for append calls to infer list element types
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
            if isinstance(call.func, ast.Attribute) and call.func.attr == "append":
                if isinstance(call.func.value, ast.Name) and call.args:
                    var_name = self._to_go_var(call.func.value.id)
                    elem_type = self._infer_elem_type_from_arg(call.args[0])
                    if elem_type and var_name in self.var_types:
                        if self.var_types[var_name] == "[]interface{}":
                            self.var_types[var_name] = f"[]{elem_type}"
        # Look for assignments to self.field = var to infer var type from field type
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                    if target.value.id == "self" and isinstance(stmt.value, ast.Name):
                        field_name = target.attr
                        var_name = self._to_go_var(stmt.value.id)
                        # Look up field type from class
                        if self.current_class:
                            class_info = self.symbols.classes.get(self.current_class)
                            if class_info and field_name in class_info.fields:
                                field_type = class_info.fields[field_name].go_type
                                if field_type and var_name in self.var_types:
                                    if self.var_types[var_name] == "[]interface{}":
                                        self.var_types[var_name] = field_type
        # Recurse into control flow
        if isinstance(stmt, ast.If):
            self._analyze_var_types(stmt.body)
            self._analyze_var_types(stmt.orelse)
        elif isinstance(stmt, ast.While):
            self._analyze_var_types(stmt.body)
        elif isinstance(stmt, ast.For):
            # Track loop variable type from iter - range over string yields rune
            iter_base = stmt.iter
            # Handle subscript like name[1:]
            if isinstance(iter_base, ast.Subscript):
                iter_base = iter_base.value
            if isinstance(iter_base, ast.Name):
                iter_var = self._snake_to_camel(iter_base.id)
                iter_type = self.var_types.get(iter_var, "")
                if iter_type == "string" or iter_base.id in ("name", "text", "s", "source"):
                    # Loop variable is rune when ranging over string
                    if isinstance(stmt.target, ast.Tuple):
                        # for i, c in range(s) - c is the rune
                        if len(stmt.target.elts) == 2:
                            c_var = stmt.target.elts[1]
                            if isinstance(c_var, ast.Name):
                                var_name = self._to_go_var(c_var.id)
                                self.var_types[var_name] = "rune"
                    elif isinstance(stmt.target, ast.Name):
                        var_name = self._to_go_var(stmt.target.id)
                        self.var_types[var_name] = "rune"
            self._analyze_var_types(stmt.body)
        # Infer types from usage patterns: Node methods and boolean context
        self._infer_types_from_usage(stmt)

    def _infer_types_from_usage(self, stmt: ast.stmt):
        """Infer variable types from how they are used in the statement."""
        # Collect variables used with Node methods (.kind, .to_sexp) -> Node
        for node in ast.walk(stmt):
            # Detect x.kind() or x.to_sexp() -> x is Node
            if isinstance(node, ast.Attribute):
                if node.attr in ("kind", "to_sexp"):
                    if isinstance(node.value, ast.Name):
                        var_name = self._to_go_var(node.value.id)
                        # Only upgrade untyped vars to Node, not interface{} which is
                        # intentional for union types like CondNode | str
                        if var_name not in self.var_types:
                            self.var_types[var_name] = "Node"
            # Detect function calls - infer argument types from function parameters
            if isinstance(node, ast.Call):
                self._infer_types_from_call_args(node)

    def _infer_types_from_call_args(self, call: ast.Call):
        """Infer variable types from function call arguments."""
        # Get function info to find parameter types
        func_info = None
        if isinstance(call.func, ast.Name):
            func_info = self.symbols.functions.get(call.func.id)
        elif isinstance(call.func, ast.Attribute):
            method_name = call.func.attr
            # Try to find method in current class
            if self.current_class:
                class_info = self.symbols.classes.get(self.current_class)
                if class_info and method_name in class_info.methods:
                    func_info = class_info.methods[method_name]
        if func_info and call.args:
            for i, arg in enumerate(call.args):
                if i < len(func_info.params):
                    param_type = func_info.params[i].go_type
                    # Only set type if it's a specific type (not generic interface{})
                    if (
                        param_type
                        and param_type not in ("interface{}", "[]interface{}")
                        and isinstance(arg, ast.Name)
                    ):
                        var_name = self._to_go_var(arg.id)
                        # Don't propagate pointer-to-slice types - caller should use slice type and add &
                        if param_type.startswith("*[]"):
                            param_type = param_type[1:]  # Strip leading * for slices only
                        if (
                            var_name not in self.var_types
                            or self.var_types[var_name] == "interface{}"
                        ):
                            self.var_types[var_name] = param_type

    def _infer_expr_type(self, node: ast.expr) -> str:
        """Infer the Go type of an expression."""
        # Variable reference
        if isinstance(node, ast.Name):
            var_name = self._to_go_var(node.id)
            return self.var_types.get(var_name, "")
        # Attribute access (self.field or obj.field)
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                obj_name = node.value.id
                if obj_name == "self" and self.current_class:
                    class_info = self.symbols.classes.get(self.current_class)
                    if class_info and node.attr in class_info.fields:
                        return class_info.fields[node.attr].go_type
        return ""

    def _infer_elem_type_from_arg(self, node: ast.expr) -> str:
        """Infer Go type from an expression being appended."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return "string"
            if isinstance(node.value, int):
                return "int"
            if isinstance(node.value, bool):
                return "bool"
        if isinstance(node, ast.Name):
            var_name = self._to_go_var(node.id)
            if var_name in self.var_types:
                return self.var_types[var_name]
            # Common string variable names
            if node.id in ("s", "c", "char", "text", "value", "line"):
                return "string"
        # If it's a string subscript (single index, not slice), treat as string
        # (we convert to string() during emission)
        if isinstance(node, ast.Subscript):
            # Slice operation (s[i:j]) returns string if source is string
            if isinstance(node.slice, ast.Slice):
                if self._is_string_subscript(node):
                    return "string"  # Slice of string is still string
            elif self._is_string_subscript(node):
                return "string"  # Single index will be converted to string
        # Method calls that return known types
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            method = node.func.attr
            if method in ("to_sexp", "join", "lower", "upper", "strip", "lstrip", "rstrip"):
                return "string"
            if method in ("find", "rfind", "index"):
                return "int"
        return ""

    def _emit_constructor_body(self, stmts: list[ast.stmt], class_info: ClassInfo):
        """Emit constructor body, handling self.x = y assignments."""
        receiver = class_info.name[0].lower()
        # Set up var_types with parameter types for if statement handling
        self.var_types = {}
        self.declared_vars = set()
        func_info = class_info.methods.get("__init__")
        if func_info:
            for p in func_info.params:
                go_name = self._to_go_var(p.name)
                self.declared_vars.add(go_name)
                self.var_types[go_name] = p.go_type
        for stmt in stmts:
            # Skip docstrings
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                continue
            # Handle super().__init__() - skip for now, Go doesn't have super
            if self._is_super_call(stmt):
                continue
            # Handle self.x = y assignments
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                target = stmt.targets[0]
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    field_name = target.attr
                    # For Node structs, keep 'kind' lowercase to avoid conflict with Kind() method
                    if class_info.is_node and field_name == "kind":
                        field = "kind"
                    else:
                        field = self._to_go_field_name(field_name)
                    field_type = ""
                    if field_name in class_info.fields:
                        field_type = class_info.fields[field_name].go_type or ""
                    # Check for None assigned to string field - use "" instead of nil
                    if isinstance(stmt.value, ast.Constant) and stmt.value.value is None:
                        if field_type == "string":
                            value = '""'
                        elif field_type == "int":
                            # Use -1 as sentinel for nullable int
                            value = "-1"
                        else:
                            value = "nil"
                    # Check for empty list - use correct slice type
                    elif isinstance(stmt.value, ast.List) and not stmt.value.elts:
                        if field_type and field_type.startswith("["):
                            value = f"{field_type}{{}}"
                        else:
                            value = "[]interface{}{}"
                    # Check for list with nil elements - use correct slice type
                    elif isinstance(stmt.value, ast.List) and all(
                        isinstance(e, ast.Constant) and e.value is None for e in stmt.value.elts
                    ):
                        if field_type and field_type.startswith("["):
                            nils = ", ".join(["nil"] * len(stmt.value.elts))
                            value = f"{field_type}{{{nils}}}"
                        else:
                            value = self.visit_expr(stmt.value)
                    # Check for ternary with empty list default: x if x is not None else []
                    elif (
                        isinstance(stmt.value, ast.IfExp)
                        and isinstance(stmt.value.orelse, ast.List)
                        and not stmt.value.orelse.elts
                        and field_type
                        and field_type.startswith("[")
                    ):
                        # Emit: _ternary(x != nil, x, []Type{})
                        test = self._emit_bool_expr(stmt.value.test)
                        body = self.visit_expr(stmt.value.body)
                        value = f"_ternary({test}, {body}, {field_type}{{}})"
                    else:
                        value = self.visit_expr(stmt.value)
                    # Special handling for Lexer/Parser: after Source, emit Source_runes
                    if class_info.name in ("Lexer", "Parser") and field_name == "source":
                        self.emit(f"{receiver}.Source = {value}")
                        self.emit(f"{receiver}.Source_runes = []rune({value})")
                        continue
                    # Special handling for Lexer/Parser: Length uses Source_runes
                    if class_info.name in ("Lexer", "Parser") and field_name == "length":
                        self.emit(f"{receiver}.Length = len({receiver}.Source_runes)")
                        continue
                    self.emit(f"{receiver}.{field} = {value}")
                    continue
            # Handle self.x: Type = y annotated assignments
            if isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
                target = stmt.target
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    field_name = target.attr
                    # For Node structs, keep 'kind' lowercase to avoid conflict with Kind() method
                    if class_info.is_node and field_name == "kind":
                        field = "kind"
                    else:
                        field = self._to_go_field_name(field_name)
                    field_type = ""
                    if field_name in class_info.fields:
                        field_type = class_info.fields[field_name].go_type or ""
                    # Check for None
                    if isinstance(stmt.value, ast.Constant) and stmt.value.value is None:
                        if field_type == "string":
                            value = '""'
                        elif field_type == "int":
                            value = "-1"
                        else:
                            value = "nil"
                    # Check for empty list
                    elif isinstance(stmt.value, ast.List) and not stmt.value.elts:
                        if field_type and field_type.startswith("["):
                            value = f"{field_type}{{}}"
                        else:
                            value = "[]interface{}{}"
                    # Check for list of all None elements (e.g., [None, None, None, None])
                    elif isinstance(stmt.value, ast.List) and all(
                        isinstance(e, ast.Constant) and e.value is None for e in stmt.value.elts
                    ):
                        if field_type and field_type.startswith("["):
                            nils = ", ".join(["nil"] * len(stmt.value.elts))
                            value = f"{field_type}{{{nils}}}"
                        else:
                            value = self.visit_expr(stmt.value)
                    # Check for ternary with empty list default: x if x is not None else []
                    elif (
                        isinstance(stmt.value, ast.IfExp)
                        and isinstance(stmt.value.orelse, ast.List)
                        and not stmt.value.orelse.elts
                        and field_type
                        and field_type.startswith("[")
                    ):
                        # Emit: _ternary(x != nil, x, []Type{})
                        test = self._emit_bool_expr(stmt.value.test)
                        body = self.visit_expr(stmt.value.body)
                        value = f"_ternary({test}, {body}, {field_type}{{}})"
                    else:
                        value = self.visit_expr(stmt.value)
                    self.emit(f"{receiver}.{field} = {value}")
                    continue
            self._emit_stmt(stmt)

    def _is_super_call(self, stmt: ast.stmt) -> bool:
        """Check if statement is super().__init__() call."""
        if not isinstance(stmt, ast.Expr):
            return False
        if not isinstance(stmt.value, ast.Call):
            return False
        call = stmt.value
        if not isinstance(call.func, ast.Attribute):
            return False
        if call.func.attr != "__init__":
            return False
        if not isinstance(call.func.value, ast.Call):
            return False
        if not isinstance(call.func.value.func, ast.Name):
            return False
        return call.func.value.func.id == "super"

    def _emit_stmt(self, stmt: ast.stmt):
        """Emit a single statement."""
        method = f"_emit_stmt_{stmt.__class__.__name__}"
        if hasattr(self, method):
            getattr(self, method)(stmt)
        else:
            raise NotImplementedError(f"Statement type {stmt.__class__.__name__}")

    def _emit_stmt_Expr(self, stmt: ast.Expr):
        """Emit expression statement."""
        # Skip docstrings
        if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
            return
        expr = self.visit_expr(stmt.value)
        # Handle append which needs to be a statement
        if "= append(" in expr:
            self.emit(expr)
        else:
            self.emit(expr)

    def _emit_stmt_Assign(self, stmt: ast.Assign):
        """Emit assignment statement."""
        if len(stmt.targets) == 1:
            target = stmt.targets[0]
            # Handle tuple unpacking: a, b = x, y
            if isinstance(target, ast.Tuple):
                self._emit_tuple_unpack(target, stmt.value)
                return
            # Check if RHS is a tuple-returning function call assigned to single var
            if isinstance(target, ast.Name) and isinstance(stmt.value, ast.Call):
                ret_info = self._get_return_type_info(stmt.value)
                if ret_info and len(ret_info) > 1:
                    target_str = self.visit_expr(target)
                    # Generate synthetic variable names for tuple elements
                    elem_vars = [f"{target_str}{i}" for i in range(len(ret_info))]
                    # Check which vars are actually used later (to avoid declaring unused ones)
                    # If the base variable is returned, we need all synthetic vars declared
                    need_all = target_str in self.returned_vars
                    used_vars = []
                    for v in elem_vars:
                        if v in self.declared_vars or need_all:
                            used_vars.append(v)  # Already declared or returned means it's used
                        else:
                            used_vars.append("_")  # Not declared means unused, use blank identifier
                    # Check if all used elem_vars are already declared (redeclaration)
                    non_blank = [v for v in used_vars if v != "_"]
                    all_declared = all(v in self.declared_vars for v in non_blank)
                    for i, v in enumerate(elem_vars):
                        if v != "_" and used_vars[i] != "_":
                            self.declared_vars.add(v)
                            self.var_types[v] = ret_info[i]
                    self.tuple_vars[target_str] = elem_vars
                    call_str = self.visit_expr(stmt.value)
                    op = "=" if all_declared else ":="
                    self.emit(f"{', '.join(used_vars)} {op} {call_str}")
                    return
            target_str = self.visit_expr(target)
            # If in type switch context and assigning to the switched variable,
            # assign to the original variable (not the narrowed one)
            if isinstance(target, ast.Name) and self._type_switch_var:
                orig_var, narrowed_var = self._type_switch_var
                if target_str == narrowed_var:
                    target_str = orig_var
            # Check if this is a new variable (local name, not attribute)
            if isinstance(target, ast.Name):
                if target_str not in self.declared_vars:
                    self.declared_vars.add(target_str)
                    # Use inferred type for empty list initialization
                    if isinstance(stmt.value, ast.List) and not stmt.value.elts:
                        if target_str in self.var_types:
                            go_type = self.var_types[target_str]
                            self.emit(f"{target_str} := {go_type}{{}}")
                            return
                    value = self.visit_expr(stmt.value)
                    # Track if this variable holds a byte (from string subscript)
                    if self._is_string_char_subscript(stmt.value):
                        self.byte_vars.add(target_str)
                    # Track if assigned from a tuple-returning function
                    self._track_tuple_func_assignment(target_str, stmt.value)
                    # Track assignment source for procsub/cmdsub type inference
                    self._track_assign_source(target_str, stmt.value)
                    # Track type for subsequent accesses (e.g., subscript on interface{})
                    if target_str not in self.var_types:
                        inferred_type = self._infer_type_from_expr(stmt.value)
                        if inferred_type:
                            self.var_types[target_str] = inferred_type
                    # Add type assertion for tuple element access (inline declaration)
                    target_type = self.var_types.get(target_str, "")
                    if (
                        target_type
                        and target_type != "interface{}"
                        and self._is_tuple_element_access(stmt.value)
                    ):
                        value = f"{value}.({target_type})"
                    self.emit(f"{target_str} := {value}")
                    return
            # Use inferred type for empty list assignment to typed variables
            if isinstance(stmt.value, ast.List) and not stmt.value.elts:
                if target_str in self.var_types:
                    go_type = self.var_types[target_str]
                    self.emit(f"{target_str} = {go_type}{{}}")
                    return
            value = self.visit_expr(stmt.value)
            # Track if this variable holds a byte (from string subscript)
            if isinstance(target, ast.Name) and self._is_string_char_subscript(stmt.value):
                self.byte_vars.add(target_str)
            # Track assignment source for procsub/cmdsub type inference
            if isinstance(target, ast.Name):
                self._track_assign_source(target_str, stmt.value)
            # Convert nil to -1 if assigning to int field (self.x = None)
            if (
                isinstance(target, ast.Attribute)
                and isinstance(stmt.value, ast.Constant)
                and stmt.value.value is None
            ):
                if (
                    isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                    and self.current_class
                ):
                    class_info = self.symbols.classes.get(self.current_class)
                    if class_info and target.attr in class_info.fields:
                        field_type = class_info.fields[target.attr].go_type or ""
                        if field_type == "int":
                            value = "-1"
            # Convert byte to string if assigning to string-typed variable
            if isinstance(target, ast.Name):
                target_type = self.var_types.get(target_str, "")
                if target_type == "string" and self._is_byte_expr(stmt.value):
                    value = f"string({value})"
                # Convert nil to -1 if assigning to int variable
                if (
                    target_type == "int"
                    and isinstance(stmt.value, ast.Constant)
                    and stmt.value.value is None
                ):
                    value = "-1"
                # Convert nil to "" if assigning to string variable
                if (
                    target_type == "string"
                    and isinstance(stmt.value, ast.Constant)
                    and stmt.value.value is None
                ):
                    value = '""'
                # Add type assertion for getattr calls when target has known type
                if (
                    target_type
                    and target_type != "interface{}"
                    and self._is_getattr_call(stmt.value)
                ):
                    value = f"{value}.({target_type})"
                # Add type assertion for tuple element access when target has known type
                if (
                    target_type
                    and target_type != "interface{}"
                    and self._is_tuple_element_access(stmt.value)
                ):
                    value = f"{value}.({target_type})"
                # Add type assertion for subscript on []Node when target is concrete ptr type
                if (
                    target_type
                    and target_type.startswith("*")
                    and self._is_node_list_subscript(stmt.value)
                ):
                    value = f"{value}.({target_type})"
            # For method calls to certain patterns, use := to create new local (avoids scope issues)
            # This handles cases where same var name is used in sibling if blocks
            # But skip this if the variable was already pre-declared
            if isinstance(target, ast.Name) and isinstance(stmt.value, ast.Call):
                if target_str not in self.declared_vars:  # Not a pre-declared variable
                    # Only do this for known method calls that return strings (like _parse_matched_pair)
                    if isinstance(stmt.value.func, ast.Attribute):
                        method = stmt.value.func.attr
                        if method in (
                            "_parse_matched_pair",
                            "_ParseMatchedPair",
                            "_collect_param_argument",
                            "_CollectParamArgument",
                        ):
                            self.declared_vars.add(target_str)
                            self.emit(f"{target_str} := {value}")
                            return
            # Track if assigned from a tuple-returning function
            if isinstance(target, ast.Name):
                self._track_tuple_func_assignment(target_str, stmt.value)
            self.emit(f"{target_str} = {value}")
        else:
            # Multiple assignment targets: a = b = value
            # In Go, assign to each target
            value = self.visit_expr(stmt.value)
            for target in stmt.targets:
                target_str = self.visit_expr(target)
                if isinstance(target, ast.Name) and target_str not in self.declared_vars:
                    self.declared_vars.add(target_str)
                    self.emit(f"{target_str} := {value}")
                else:
                    self.emit(f"{target_str} = {value}")

    def _emit_tuple_unpack(self, target: ast.Tuple, value: ast.expr):
        """Emit tuple unpacking: a, b = x, y"""
        target_names = []
        for elt in target.elts:
            # Handle Python's discard pattern: _, x = func()
            if isinstance(elt, ast.Name) and elt.id == "_":
                target_names.append("_")
            else:
                name = self.visit_expr(elt)
                target_names.append(name)
                if isinstance(elt, ast.Name):
                    camel = self._to_go_var(elt.id)
                    self.declared_vars.add(camel)
        # Handle value side
        if isinstance(value, ast.Tuple):
            # a, b = x, y - for tuple literals, check if vars exist
            value_exprs = [self.visit_expr(v) for v in value.elts]
            self.emit(f"{', '.join(target_names)} := {', '.join(value_exprs)}")
        elif isinstance(value, ast.Call):
            # a, b = func() - always use := for function calls returning multiple values
            # This ensures fresh local variables are created in the current scope
            value_expr = self.visit_expr(value)
            self.emit(f"{', '.join(target_names)} := {value_expr}")
            # Suppress unused variable warnings for non-blank tuple elements
            for name in target_names:
                if name != "_":
                    self.emit(f"_ = {name}")
        else:
            # Other cases - need to unpack at runtime
            raise NotImplementedError(f"Tuple unpacking from {type(value).__name__}")

    def _emit_stmt_AnnAssign(self, stmt: ast.AnnAssign):
        """Emit annotated assignment."""
        if stmt.value:
            target = self.visit_expr(stmt.target)
            py_type = self._annotation_to_str(stmt.annotation)
            # Handle None assignment to optional types (int | None, etc.)
            if isinstance(stmt.value, ast.Constant) and stmt.value.value is None:
                if " | None" in py_type:
                    # Extract base type
                    base_type = py_type.split("|")[0].strip()
                    go_base = self._py_type_to_go(base_type)
                    # Use sentinel values for nullable primitives
                    if go_base == "int":
                        # Use -1 as sentinel for nullable int (positions are never negative)
                        if isinstance(stmt.target, ast.Name):
                            if target not in self.declared_vars:
                                self.declared_vars.add(target)
                                self.emit(f"{target} := -1")
                            else:
                                self.emit(f"{target} = -1")
                            self.var_types[target] = "int"
                            return
            # Use type annotation to determine the Go type for empty lists
            if isinstance(stmt.value, ast.List) and not stmt.value.elts:
                go_type = self._py_type_to_go(py_type)
                if go_type and go_type.startswith("["):
                    value = f"{go_type}{{}}"
                    # Store type for later use in append inference
                    if isinstance(stmt.target, ast.Name):
                        self.var_types[target] = go_type
                else:
                    value = self.visit_expr(stmt.value)
            else:
                value = self.visit_expr(stmt.value)
            # Use := for first declaration, = for reassignment
            if isinstance(stmt.target, ast.Name) and target not in self.declared_vars:
                self.declared_vars.add(target)
                self.emit(f"{target} := {value}")
            else:
                self.emit(f"{target} = {value}")

    def _emit_stmt_AugAssign(self, stmt: ast.AugAssign):
        """Emit augmented assignment (+=, -=, etc.)."""
        target = self.visit_expr(stmt.target)
        op = self._binop_to_go(stmt.op)
        value = self.visit_expr(stmt.value)
        self.emit(f"{target} {op}= {value}")

    def _emit_stmt_Return(self, stmt: ast.Return):
        """Emit return statement."""
        if stmt.value:
            # Handle tuple return type (multiple return values)
            if self.current_return_type.startswith("(") and isinstance(stmt.value, ast.Tuple):
                values = [
                    self._emit_tuple_return_element(e, i) for i, e in enumerate(stmt.value.elts)
                ]
                self.emit(f"return {', '.join(values)}")
                return
            # Check for None return - convert to zero value based on return type
            if isinstance(stmt.value, ast.Constant) and stmt.value.value is None:
                # Special handling for tuple return types
                if self.current_return_type.startswith("("):
                    inner = self.current_return_type[1:-1]
                    parts = [p.strip() for p in inner.split(",")]
                    zero_values = [self._nil_to_zero_value(p) for p in parts]
                    value = ", ".join(zero_values)
                else:
                    value = self._nil_to_zero_value(self.current_return_type)
            # Check for single-char string subscript (byte) being returned as string
            elif self.current_return_type == "string" and self._is_string_char_subscript(
                stmt.value
            ):
                value = f"string({self.visit_expr(stmt.value)})"
            # Check for byte variable being returned as string
            elif self.current_return_type == "string" and self._is_byte_variable(stmt.value):
                value = f"string({self.visit_expr(stmt.value)})"
            # Check for interface field being returned as concrete pointer type
            elif self.current_return_type.startswith("*") and self._is_interface_field(stmt.value):
                value = f"{self.visit_expr(stmt.value)}.({self.current_return_type})"
            # Check for []Node subscript being returned as concrete pointer type
            elif self.current_return_type.startswith("*") and self._is_node_list_subscript(
                stmt.value
            ):
                value = f"{self.visit_expr(stmt.value)}.({self.current_return_type})"
            # Check for attribute access returning Node when we need concrete type
            elif self.current_return_type.startswith("*") and self._is_node_field_access(
                stmt.value
            ):
                value = f"{self.visit_expr(stmt.value)}.({self.current_return_type})"
            # Check for returning a tuple variable (passthrough pattern)
            elif isinstance(stmt.value, ast.Name):
                var_name = self._to_go_var(stmt.value.id)
                if var_name in self.tuple_vars:
                    elem_vars = self.tuple_vars[var_name]
                    self.emit(f"return {', '.join(elem_vars)}")
                    return
                # Use visit_expr to handle type switch variable rewriting
                value = self.visit_expr(stmt.value)
            else:
                value = self.visit_expr(stmt.value)
            self.emit(f"return {value}")
        else:
            self.emit("return")

    def _emit_tuple_return_element(self, node: ast.expr, index: int) -> str:
        """Emit a single element of a tuple return, with type conversion if needed."""
        # Get the expected type for this position from the return type
        if self.current_return_type.startswith("("):
            inner = self.current_return_type[1:-1]
            parts = [p.strip() for p in inner.split(",")]
            expected_type = parts[index] if index < len(parts) else ""
        else:
            expected_type = ""
        # Convert None to appropriate zero value
        if isinstance(node, ast.Constant) and node.value is None:
            return self._nil_to_zero_value(expected_type)
        # Convert empty list to typed empty slice
        if isinstance(node, ast.List) and not node.elts:
            if expected_type.startswith("[]"):
                return f"{expected_type}{{}}"
        return self.visit_expr(node)

    def _nil_to_zero_value(self, go_type: str) -> str:
        """Convert nil to appropriate zero value based on Go type."""
        if go_type == "string":
            return '""'
        if go_type == "int":
            return "0"
        if go_type == "bool":
            return "false"
        if go_type.startswith("[]"):
            return "nil"  # Slices can be nil
        if go_type.startswith("*"):
            return "nil"  # Pointers can be nil
        if go_type.startswith("map["):
            return "nil"  # Maps can be nil
        return "nil"  # Default to nil for interfaces and other types

    def _is_string_char_subscript(self, node: ast.expr) -> bool:
        """Check if node is a single-character string subscript (returns byte in Go)."""
        if not isinstance(node, ast.Subscript):
            return False
        # Must be single index, not slice
        if isinstance(node.slice, ast.Slice):
            return False
        # Check if the value being subscripted is a known string attribute
        if isinstance(node.value, ast.Attribute):
            # Common string fields: source, Source
            if node.value.attr.lower() == "source":
                return True
        # Also handle local variables that are strings
        if isinstance(node.value, ast.Name):
            name = node.value.id
            if name in ("source", "s", "text", "line"):
                return True
        return False

    def _track_tuple_func_assignment(self, var_name: str, value: ast.expr):
        """Track if a variable is assigned from a known tuple-returning function."""
        if not isinstance(value, ast.Call):
            return
        func_name = None
        if isinstance(value.func, ast.Name):
            func_name = value.func.id
        elif isinstance(value.func, ast.Attribute):
            func_name = value.func.attr
        if func_name:
            go_func_name = self._to_go_func_name(func_name)
            if go_func_name in TUPLE_ELEMENT_TYPES:
                self.tuple_func_vars[var_name] = go_func_name

    def _track_assign_source(self, var_name: str, value: ast.expr):
        """Track assignment source for procsub/cmdsub type inference."""
        if isinstance(value, ast.Subscript) and isinstance(value.value, ast.Name):
            source_name = value.value.id
            if source_name in ("procsub_parts", "cmdsub_parts"):
                self.var_assign_sources[var_name] = source_name

    def _is_byte_variable(self, node: ast.expr) -> bool:
        """Check if node is a variable known to hold a byte."""
        if not isinstance(node, ast.Name):
            return False
        go_name = self._to_go_var(node.id)
        return go_name in self.byte_vars

    def _is_interface_field(self, node: ast.expr) -> bool:
        """Check if node is an attribute access on a struct field typed as Node/interface{}."""
        if not isinstance(node, ast.Attribute):
            return False
        # Look up the field type from the receiver's class
        if isinstance(node.value, ast.Name):
            var_name = self._to_go_var(node.value.id)
            var_type = self.var_types.get(var_name, "")
            # Strip pointer prefix to get class name
            class_name = var_type.lstrip("*")
            if class_name in self.symbols.classes:
                class_info = self.symbols.classes[class_name]
                if node.attr in class_info.fields:
                    field_type = class_info.fields[node.attr].go_type or ""
                    return field_type in ("Node", "interface{}")
        return False

    def _is_node_field_access(self, node: ast.expr) -> bool:
        """Check if node is an attribute access that returns Node."""
        if not isinstance(node, ast.Attribute):
            return False
        # Check if the field type is Node
        field_type = self._get_field_type_from_attr(node)
        return field_type in ("Node", "interface{}")

    def _get_field_type_from_attr(self, node: ast.Attribute) -> str:
        """Get the field type from an attribute access expression."""
        if isinstance(node.value, ast.Name):
            var_name = self._to_go_var(node.value.id)
            var_type = self.var_types.get(var_name, "")
            class_name = var_type.lstrip("*")
            if class_name in self.symbols.classes:
                class_info = self.symbols.classes[class_name]
                if node.attr in class_info.fields:
                    return class_info.fields[node.attr].go_type or ""
        # For more complex expressions, try to infer the type
        field_name = node.attr
        type_assertion = self._get_type_for_field(field_name)
        if type_assertion:
            # The field needs a type assertion, meaning it's probably Node
            class_name = type_assertion.lstrip("*")
            if class_name in self.symbols.classes:
                class_info = self.symbols.classes[class_name]
                if field_name in class_info.fields:
                    return class_info.fields[field_name].go_type or ""
        return ""

    def _emit_stmt_If(self, stmt: ast.If):
        """Emit if statement."""
        # Pre-declare variables assigned across if/elif/else branches to avoid Go scoping issues
        self._predeclare_if_chain_vars(stmt)
        self._emit_if_chain(stmt, is_first=True)

    def _predeclare_if_chain_vars(self, stmt: ast.If):
        """Pre-declare variables that are assigned in multiple if/elif/else branches."""
        # Collect assignments from all branches with their types
        branch_vars: list[dict[str, str]] = []
        self._collect_if_chain_assignments(stmt, branch_vars)
        if len(branch_vars) < 2:
            return  # No elif/else, no scoping issue
        # Find all variables across branches
        all_vars: dict[str, str] = {}
        for vars in branch_vars:
            for var, go_type in vars.items():
                if var not in all_vars:
                    all_vars[var] = go_type
        # Pre-declare variables that are new (not already declared)
        for var, go_type in all_vars.items():
            if var not in self.declared_vars:
                # Use known type from var_types if available, else inferred type
                actual_type = self.var_types.get(var, go_type)
                self.emit(f"var {var} {actual_type}")
                self.declared_vars.add(var)

    def _collect_if_chain_assignments(self, stmt: ast.If, branch_vars: list[dict[str, str]]):
        """Collect variable assignments from if/elif/else branches."""
        # Collect from if body
        if_vars = self._collect_branch_assignments(stmt.body)
        branch_vars.append(if_vars)
        # Process orelse
        if stmt.orelse:
            if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                # elif chain - recurse
                self._collect_if_chain_assignments(stmt.orelse[0], branch_vars)
            else:
                # else branch
                else_vars = self._collect_branch_assignments(stmt.orelse)
                branch_vars.append(else_vars)

    # Methods that always use := for assignment (to avoid scope shadowing issues)
    FORCE_NEW_LOCAL_METHODS = {
        "_parse_matched_pair",
        "_ParseMatchedPair",
        "_collect_param_argument",
        "_CollectParamArgument",
    }

    def _collect_branch_assignments(self, stmts: list[ast.stmt]) -> dict[str, str]:
        """Collect variable names and inferred types assigned in a list of statements (recursive)."""
        vars: dict[str, str] = {}
        for s in stmts:
            if isinstance(s, ast.Assign):
                for target in s.targets:
                    if isinstance(target, ast.Name):
                        # For tuple-returning functions, only collect vars that are predeclared
                        # (i.e., actually used) - unused ones will use _ in the assignment
                        if isinstance(s.value, ast.Call):
                            ret_info = self._get_return_type_info(s.value)
                            if ret_info and len(ret_info) > 1:
                                go_name = self._to_go_var(target.id)
                                for i, elem_type in enumerate(ret_info):
                                    synth_name = f"{go_name}{i}"
                                    # Only collect if already predeclared (actually used)
                                    if synth_name in self.declared_vars:
                                        vars[synth_name] = elem_type
                                continue
                            # Skip assignments from methods that force := usage
                            if isinstance(s.value.func, ast.Attribute):
                                if s.value.func.attr in self.FORCE_NEW_LOCAL_METHODS:
                                    continue
                        go_name = self._to_go_var(target.id)
                        # Use single-type inference to avoid tuple types
                        go_type = self._infer_single_type_from_expr(s.value)
                        vars[go_name] = go_type
                    elif isinstance(target, ast.Tuple):
                        # Skip tuple unpacking - it uses := which creates fresh locals
                        # Pre-declaring these would cause "declared and not used" errors
                        pass
            elif isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name):
                go_name = self._to_go_var(s.target.id)
                try:
                    py_type = ast.unparse(s.annotation)
                    go_type = self._py_type_to_go(py_type)
                except Exception:
                    go_type = "interface{}"
                vars[go_name] = go_type
            # Recursively collect from nested if statements
            elif isinstance(s, ast.If):
                nested = self._collect_branch_assignments(s.body)
                vars.update(nested)
                if s.orelse:
                    nested = self._collect_branch_assignments(s.orelse)
                    vars.update(nested)
            # Recursively collect from loops
            elif isinstance(s, (ast.For, ast.While)):
                nested = self._collect_branch_assignments(s.body)
                vars.update(nested)
        return vars

    def _infer_tuple_element_type(self, value: ast.expr, index: int) -> str:
        """Infer the type of a specific element from a tuple-returning expression."""
        # If it's a method call, look up the return type
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
            class_name = self._infer_object_class(value.func.value)
            if class_name:
                method = value.func.attr
                class_info = self.symbols.classes.get(class_name)
                if class_info and method in class_info.methods:
                    func_info = class_info.methods[method]
                    ret_type = func_info.return_type
                    if ret_type.startswith("("):
                        inner = ret_type[1:-1]
                        parts = [p.strip() for p in inner.split(",")]
                        if index < len(parts):
                            return parts[index]
        return "interface{}"

    def _infer_type_from_expr(self, node: ast.expr) -> str:
        """Infer Go type from a Python expression."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return "bool"
            if isinstance(node.value, int):
                return "int"
            if isinstance(node.value, str):
                return "string"
            if isinstance(node.value, float):
                return "float64"
        if isinstance(node, ast.BinOp):
            # Bitwise operations on flags yield int
            if isinstance(node.op, (ast.BitOr, ast.BitAnd, ast.BitXor)):
                return "int"
            # Arithmetic operations yield int
            if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.FloorDiv, ast.Mod)):
                left_type = self._infer_type_from_expr(node.left)
                right_type = self._infer_type_from_expr(node.right)
                # String concatenation
                if isinstance(node.op, ast.Add):
                    if left_type == "string" or right_type == "string":
                        return "string"
                if left_type == "int" or right_type == "int":
                    return "int"
        if isinstance(node, ast.Attribute):
            # Common patterns: self.pos + 1 → int, self.length → int
            if node.attr in ("pos", "length", "Pos", "Length"):
                return "int"
            # Boolean fields
            if node.attr in ("single", "double", "Single", "Double"):
                return "bool"
            # Class constants (flags) are int
            if isinstance(node.value, ast.Name):
                class_name = node.value.id
                if class_name in (
                    "MatchedPairFlags",
                    "ParserStateFlags",
                    "DolbraceState",
                    "TokenType",
                    "WordCtx",
                    "ParseContext",
                ):
                    return "int"
                # Look up field type from class info
                obj_class = self._infer_object_class(node.value)
                if obj_class and obj_class in self.symbols.classes:
                    class_info = self.symbols.classes[obj_class]
                    if node.attr in class_info.fields:
                        return class_info.fields[node.attr].go_type or ""
        if isinstance(node, ast.Name):
            # Look up variable type from var_types (includes parameters)
            var_name = self._to_go_var(node.id)
            if var_name in self.var_types:
                return self.var_types[var_name]
            # Common variable names with known types
            if node.id in ("start", "end", "pos", "i", "j", "n", "length", "count", "depth"):
                return "int"
            # Module-level constants (usually ints or strings)
            if node.id.startswith("_") and node.id.isupper():
                return "int"  # Convention: _UPPER_CASE constants are int
            if node.id.isupper():
                return "int"  # All-caps are usually constants
        if isinstance(node, ast.Compare):
            return "bool"
        if isinstance(node, ast.BoolOp):
            return "bool"
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return "bool"
        if isinstance(node, ast.List):
            return "[]interface{}"
        if isinstance(node, ast.Dict):
            # Infer map type from values
            if node.values and all(
                isinstance(v, ast.Constant) and isinstance(v.value, str) for v in node.values
            ):
                return "map[string]string"
            return "map[string]interface{}"
        # Slice expression - preserves the slice type
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
            # parts[0:i] where parts is []Node -> []Node
            # word[1:] where word is string -> string
            if isinstance(node.value, ast.Name):
                var_name = self._to_go_var(node.value.id)
                var_type = self.var_types.get(var_name, "")
                if var_type.startswith("[]"):
                    return var_type  # []Node -> []Node (slicing preserves type)
                if var_type == "string":
                    return "string"  # string[1:] -> string
        # Subscript - infer element type from collection type
        if isinstance(node, ast.Subscript) and not isinstance(node.slice, ast.Slice):
            # Get the collection type
            if isinstance(node.value, ast.Attribute):
                # self.commands[i] -> look up field type
                if isinstance(node.value.value, ast.Name) and node.value.value.id == "self":
                    if self.current_class:
                        class_info = self.symbols.classes.get(self.current_class)
                        if class_info and node.value.attr in class_info.fields:
                            field_type = class_info.fields[node.value.attr].go_type or ""
                            # Extract element type from slice type
                            if field_type.startswith("[]"):
                                return field_type[2:]  # []Node -> Node
                # var.attr[i] -> look up var's type, then field type
                elif isinstance(node.value.value, ast.Name):
                    var_name = self._to_go_var(node.value.value.id)
                    var_type = self.var_types.get(var_name, "")
                    # Extract class name from *ClassName
                    if var_type.startswith("*"):
                        class_name = var_type[1:]
                        if class_name in self.symbols.classes:
                            class_info = self.symbols.classes[class_name]
                            if node.value.attr in class_info.fields:
                                field_info = class_info.fields[node.value.attr]
                                # Use Python type for more specific inference
                                py_type = field_info.py_type
                                if py_type.startswith("list["):
                                    inner_py = py_type[5:-1]
                                    # Convert inner type with concrete_nodes=True
                                    elem_type = self._py_type_to_go(inner_py, concrete_nodes=True)
                                    return elem_type
                                field_type = field_info.go_type or ""
                                if field_type.startswith("[]"):
                                    return field_type[2:]  # []*Word -> *Word
            # Variable subscript
            if isinstance(node.value, ast.Name):
                var_name = self._to_go_var(node.value.id)
                var_type = self.var_types.get(var_name, "")
                if var_type.startswith("[]"):
                    return var_type[2:]  # []Node -> Node
        # Method calls with known return types
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                method = node.func.attr
                # Methods that return bool
                if method in (
                    "outer_double",
                    "outer_single",
                    "OuterDouble",
                    "OuterSingle",
                    "startswith",
                    "endswith",
                    "isalpha",
                    "isdigit",
                    "isalnum",
                    "isspace",
                ):
                    return "bool"
                # Methods that return int
                if method in ("find", "rfind", "index", "rindex", "count"):
                    return "int"
                # Methods that return string
                if method in (
                    "_parse_matched_pair",
                    "_ParseMatchedPair",
                    "advance",
                    "Advance",
                    "peek",
                    "Peek",
                    "to_sexp",
                    "ToSexp",
                ):
                    return "string"
                # Methods that return known types from class methods
                class_name = self._infer_object_class(node.func.value)
                if class_name:
                    class_info = self.symbols.classes.get(class_name)
                    if class_info and method in class_info.methods:
                        return class_info.methods[method].return_type or "interface{}"
            elif isinstance(node.func, ast.Name):
                # _sublist preserves the slice type of its first argument
                if node.func.id == "_sublist" and node.args:
                    first_arg_type = self._infer_type_from_expr(node.args[0])
                    if first_arg_type.startswith("[]"):
                        return first_arg_type
                # list() preserves the slice type of its argument
                if node.func.id == "list" and node.args:
                    first_arg_type = self._infer_type_from_expr(node.args[0])
                    if first_arg_type.startswith("[]"):
                        return first_arg_type
                # Built-in type conversions
                if node.func.id == "bool":
                    return "bool"
                if node.func.id == "int":
                    return "int"
                if node.func.id == "str":
                    return "string"
                if node.func.id == "len":
                    return "int"
                if node.func.id == "bytearray":
                    return "[]byte"
                # Check if it's a class constructor
                if node.func.id in self.symbols.classes:
                    return "*" + node.func.id
                # Look up function return types
                if node.func.id in self.symbols.functions:
                    func_info = self.symbols.functions[node.func.id]
                    ret_type = func_info.return_type
                    if ret_type:
                        return self._py_type_to_go(ret_type)
        # Ternary expression: infer from the "then" branch
        if isinstance(node, ast.IfExp):
            return self._infer_type_from_expr(node.body)
        return "interface{}"

    def _infer_single_type_from_expr(self, node: ast.expr) -> str:
        """Infer Go type from a Python expression, but never return tuple types."""
        result = self._infer_type_from_expr(node)
        # Tuple types can't be used for single var declarations
        if result.startswith("("):
            return "interface{}"
        return result

    def _get_return_value_count(self, node: ast.Call) -> int:
        """Get the number of return values from a function call."""
        ret_info = self._get_return_type_info(node)
        return len(ret_info) if ret_info else 1

    def _get_return_type_info(self, node: ast.Call) -> list[str] | None:
        """Get the return types from a function call. Returns list of Go types or None."""
        # Look up the return type from the function/method signature
        ret_type = ""
        if isinstance(node.func, ast.Attribute):
            method = node.func.attr
            class_name = self._infer_object_class(node.func.value)
            if class_name:
                class_info = self.symbols.classes.get(class_name)
                if class_info and method in class_info.methods:
                    ret_type = class_info.methods[method].return_type
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.symbols.functions:
                ret_type = self.symbols.functions[func_name].return_type
        if ret_type.startswith("("):
            # Parse tuple type: (T1, T2) -> ["T1", "T2"]
            inner = ret_type[1:-1]
            return [t.strip() for t in inner.split(",")]
        elif ret_type:
            return [ret_type]
        return None

    def _detect_union_discriminator(self, test: ast.expr) -> tuple[str, str, str] | None:
        """Detect if test is a union field discriminator comparison (var == nil).
        Returns (receiver, field, discriminator_var) if found, None otherwise."""
        # Look for pattern: discriminatorVar == nil
        if not isinstance(test, ast.Compare):
            return None
        if len(test.ops) != 1 or not isinstance(test.ops[0], (ast.Eq, ast.Is)):
            return None
        if len(test.comparators) != 1:
            return None
        # Check if comparing to None/nil
        comp = test.comparators[0]
        if not (isinstance(comp, ast.Constant) and comp.value is None):
            return None
        # Check if left side is a discriminator variable
        if not isinstance(test.left, ast.Name):
            return None
        disc_var = self._to_go_var(test.left.id)
        # Check if this discriminator matches any union field
        for (receiver_type, field_name), (expected_disc, _, _) in UNION_FIELDS.items():
            if disc_var == expected_disc:
                return (receiver_type, field_name, disc_var)
        return None

    def _detect_kind_check(self, test: ast.expr) -> tuple[str, str] | None:
        """Detect `var.kind == "literal"` or `var is not None and var.kind == "literal"`.
        Returns (var_name, kind_literal) or None."""
        # Handle compound: `var is not None and var.kind == "literal"`
        # Go type assertion handles nil check implicitly, so we can emit just the assertion
        if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.And):
            for value in test.values:
                result = self._detect_simple_kind_check(value)
                if result:
                    return result
            return None
        return self._detect_simple_kind_check(test)

    def _detect_simple_kind_check(self, test: ast.expr) -> tuple[str, str] | None:
        """Detect simple `var.kind == "literal"`. Returns (var_name, kind_literal) or None."""
        if not isinstance(test, ast.Compare):
            return None
        if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
            return None
        if not isinstance(test.left, ast.Attribute) or test.left.attr != "kind":
            return None
        if not isinstance(test.left.value, ast.Name):
            return None
        comp = test.comparators[0]
        if not isinstance(comp, ast.Constant) or not isinstance(comp.value, str):
            return None
        if comp.value not in KIND_TO_TYPE:
            return None
        return (test.left.value.id, comp.value)

    def _emit_kind_type_narrowing(self, stmt: ast.If, kind_info: tuple[str, str], is_first: bool):
        """Emit kind-based type narrowing as Go type assertion."""
        var_name, kind_literal = kind_info
        type_name = KIND_TO_TYPE[kind_literal]
        go_var = self._to_go_var(var_name)
        narrowed_var = go_var[0].lower()
        if narrowed_var == go_var:
            narrowed_var = go_var + "T"
        if is_first:
            self.emit(f"if {narrowed_var}, ok := {go_var}.(*{type_name}); ok {{")
        else:
            self.emit_raw(
                "\t" * self.indent
                + f"}} else if {narrowed_var}, ok := {go_var}.(*{type_name}); ok {{"
            )
        self.indent += 1
        # Set type narrowing context (reuses existing _type_switch_var mechanism)
        old_switch_var = self._type_switch_var
        old_switch_type = self._type_switch_type
        self._type_switch_var = (go_var, narrowed_var)
        self._type_switch_type = f"*{type_name}"
        try:
            for s in stmt.body:
                self._emit_stmt(s)
        except NotImplementedError:
            self.emit('panic("TODO")')
        # Restore context
        self._type_switch_var = old_switch_var
        self._type_switch_type = old_switch_type
        self.indent -= 1
        # Handle elif/else chains
        if stmt.orelse:
            if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                self._emit_if_chain(stmt.orelse[0], is_first=False)
            else:
                self.emit_raw("\t" * self.indent + "} else {")
                self.indent += 1
                for s in stmt.orelse:
                    self._emit_stmt(s)
                self.indent -= 1
                self.emit("}")
        else:
            self.emit("}")

    def _emit_if_chain(self, stmt: ast.If, is_first: bool):
        """Emit if/elif/else chain."""
        # Check for kind-based type narrowing
        kind_info = self._detect_kind_check(stmt.test)
        if kind_info:
            return self._emit_kind_type_narrowing(stmt, kind_info, is_first)
        test = self._emit_bool_expr(stmt.test)
        # Check for union field discriminator pattern
        union_info = self._detect_union_discriminator(stmt.test)
        union_key = None
        if union_info:
            receiver_type, field_name, disc_var = union_info
            _, nil_type, non_nil_type = UNION_FIELDS[(receiver_type, field_name)]
            union_key = (receiver_type, field_name)
        if is_first:
            self.emit(f"if {test} {{")
        else:
            self.emit_raw("\t" * self.indent + f"}} else if {test} {{")
        self.indent += 1
        # Set union field type for body (nil branch = string for discriminator == nil)
        if union_key:
            self.union_field_types[union_key] = nil_type
        self._emit_stmts_with_patterns(stmt.body)
        # Clear union field type after body
        if union_key:
            del self.union_field_types[union_key]
        self.indent -= 1
        if stmt.orelse:
            if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                # elif - continue chain
                self._emit_if_chain(stmt.orelse[0], is_first=False)
            else:
                # else - set non-nil type
                self.emit_raw("\t" * self.indent + "} else {")
                self.indent += 1
                if union_key:
                    self.union_field_types[union_key] = non_nil_type
                self._emit_stmts_with_patterns(stmt.orelse)
                if union_key:
                    del self.union_field_types[union_key]
                self.indent -= 1
                self.emit("}")
        else:
            self.emit("}")

    def _emit_stmt_While(self, stmt: ast.While):
        """Emit while loop."""
        test = self._emit_bool_expr(stmt.test)
        self.emit(f"for {test} {{")
        self.indent += 1
        try:
            for s in stmt.body:
                self._emit_stmt(s)
        except NotImplementedError:
            self.emit('panic("TODO: incomplete implementation")')
        self.indent -= 1
        self.emit("}")

    def _emit_stmt_For(self, stmt: ast.For):
        """Emit for loop."""
        # Check for `for _ in x:` (discard loop variable) before visiting
        is_discard = isinstance(stmt.target, ast.Name) and stmt.target.id == "_"
        target = self.visit_expr(stmt.target) if not is_discard else "_"
        # Handle range()
        if isinstance(stmt.iter, ast.Call) and isinstance(stmt.iter.func, ast.Name):
            if stmt.iter.func.id == "range":
                self._emit_range_for(stmt, target, is_discard)
                return
        # Standard for-each
        iter_expr = self.visit_expr(stmt.iter)
        # Track loop variable type from iterable's element type
        if not is_discard and isinstance(stmt.target, ast.Name):
            elem_type = self._get_iter_element_type(stmt.iter)
            if elem_type:
                self.var_types[target] = elem_type
        # Handle `for _ in x:` (discard loop variable)
        if is_discard:
            self.emit(f"for range {iter_expr} {{")
        else:
            self.emit(f"for _, {target} := range {iter_expr} {{")
        self.indent += 1
        try:
            for s in stmt.body:
                self._emit_stmt(s)
        except NotImplementedError:
            self.emit('panic("TODO: incomplete implementation")')
        self.indent -= 1
        self.emit("}")

    def _get_iter_element_type(self, node: ast.expr) -> str:
        """Get the element type for iterating over an expression."""
        if isinstance(node, ast.Name):
            var_name = self._to_go_var(node.id)
            var_type = self.var_types.get(var_name, "")
            if var_type.startswith("[]"):
                return var_type[2:]  # []interface{} -> interface{}
            if var_type == "string":
                return "rune"
        return ""

    def _emit_range_for(self, stmt: ast.For, target: str, is_discard: bool = False):
        """Emit for loop over range()."""
        args = stmt.iter.args
        # For discarded loop variable, use anonymous loop
        if is_discard:
            end = self.visit_expr(args[0]) if args else "0"
            self.emit(f"for _i := 0; _i < {end}; _i++ {{")
        elif len(args) == 1:
            end = self.visit_expr(args[0])
            self.emit(f"for {target} := 0; {target} < {end}; {target}++ {{")
        elif len(args) == 2:
            start = self.visit_expr(args[0])
            end = self.visit_expr(args[1])
            self.emit(f"for {target} := {start}; {target} < {end}; {target}++ {{")
        else:
            start = self.visit_expr(args[0])
            end = self.visit_expr(args[1])
            step = self.visit_expr(args[2])
            # Check for negative step
            if isinstance(args[2], ast.UnaryOp) and isinstance(args[2].op, ast.USub):
                self.emit(f"for {target} := {start}; {target} > {end}; {target} += {step} {{")
            else:
                self.emit(f"for {target} := {start}; {target} < {end}; {target} += {step} {{")
        self.indent += 1
        try:
            for s in stmt.body:
                self._emit_stmt(s)
        except NotImplementedError:
            self.emit('panic("TODO: incomplete implementation")')
        self.indent -= 1
        self.emit("}")

    def _emit_stmt_Break(self, stmt: ast.Break):
        """Emit break statement."""
        self.emit("break")

    def _emit_stmt_Continue(self, stmt: ast.Continue):
        """Emit continue statement."""
        self.emit("continue")

    def _emit_stmt_Pass(self, stmt: ast.Pass):
        """Emit pass (no-op in Go)."""
        pass  # Go doesn't need explicit pass

    def _emit_stmt_FunctionDef(self, stmt: ast.FunctionDef):
        """Skip local function definitions - they need to be inlined or helper funcs."""
        # Local functions like format_arith_val are converted to helper functions
        pass

    def _emit_stmt_Raise(self, stmt: ast.Raise):
        """Emit raise as panic."""
        if stmt.exc:
            exc = self.visit_expr(stmt.exc)
            self.emit(f"panic({exc})")
        else:
            self.emit("panic(nil)")

    def _has_return_in_block(self, stmts: list[ast.stmt]) -> bool:
        """Check if a block contains return statements (complex try/except pattern)."""
        for s in stmts:
            if isinstance(s, ast.Return):
                return True
            if isinstance(s, ast.If):
                if self._has_return_in_block(s.body) or self._has_return_in_block(s.orelse):
                    return True
            if isinstance(s, (ast.For, ast.While)):
                if self._has_return_in_block(s.body):
                    return True
        return False

    def _is_try_assign_except_return(self, stmt: ast.Try) -> bool:
        """Check if this is a 'try: x = call() except: return fallback' pattern."""
        # Must have exactly one statement in try body that's an assignment
        if len(stmt.body) != 1:
            return False
        if not isinstance(stmt.body[0], ast.Assign):
            return False
        assign = stmt.body[0]
        # Must assign to a single name
        if len(assign.targets) != 1 or not isinstance(assign.targets[0], ast.Name):
            return False
        # Must have exactly one handler
        if len(stmt.handlers) != 1:
            return False
        handler = stmt.handlers[0]
        # Handler must end with a return statement
        if not handler.body or not isinstance(handler.body[-1], ast.Return):
            return False
        return True

    def _emit_try_assign_except_return(self, stmt: ast.Try):
        """Emit 'try: x = call() except: cleanup; return fallback' pattern.

        Generates:
            var x Type
            parseOk := true
            func() {
                defer func() { if r := recover(); r != nil { parseOk = false } }()
                x = call()
            }()
            if !parseOk { cleanup; return fallback }
        """
        assign = stmt.body[0]
        var_name = self._to_go_var(assign.targets[0].id)
        handler = stmt.handlers[0]
        # Get the return statement (last in handler)
        return_stmt = handler.body[-1]
        # Get cleanup statements (all but the return)
        cleanup_stmts = handler.body[:-1]
        # Pre-declare the variable with its type (infer from call if possible)
        # Skip if already declared (e.g., by _predeclare_all_locals)
        if var_name not in self.declared_vars:
            var_type = self._infer_call_return_type(assign.value)
            if var_type:
                self.emit(f"var {var_name} {var_type}")
            else:
                self.emit(f"var {var_name} interface{{}}")
            self.declared_vars.add(var_name)
        # Emit the success flag
        self.emit("parseOk := true")
        self.declared_vars.add("parseOk")
        # Emit IIFE with defer/recover
        self.emit("func() {")
        self.indent += 1
        self.emit("defer func() {")
        self.indent += 1
        self.emit("if r := recover(); r != nil {")
        self.indent += 1
        self.emit("parseOk = false")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}()")
        # Emit the assignment
        call_expr = self.visit_expr(assign.value)
        self.emit(f"{var_name} = {call_expr}")
        self.indent -= 1
        self.emit("}()")
        # Emit the error check and fallback
        self.emit("if !parseOk {")
        self.indent += 1
        for s in cleanup_stmts:
            self._emit_stmt(s)
        self._emit_stmt(return_stmt)
        self.indent -= 1
        self.emit("}")

    def _infer_call_return_type(self, node: ast.expr) -> str | None:
        """Infer the return type of a function call."""
        if not isinstance(node, ast.Call):
            return None
        func_name = None
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
        if not func_name:
            return None
        go_func_name = self._to_go_func_name(func_name)
        # Check if it's a known method
        if go_func_name in TUPLE_ELEMENT_TYPES:
            # Returns first element type for tuple-returning funcs
            return TUPLE_ELEMENT_TYPES[go_func_name][0]
        # Common return types for parser methods
        if "parse" in func_name.lower() or "Parse" in go_func_name:
            return "Node"
        return None

    def _emit_stmt_Try(self, stmt: ast.Try):
        """Emit try/except as defer/recover pattern."""
        # We'll wrap the try block in an immediately-invoked function with defer/recover
        # Pattern: func() { defer func() { if r := recover(); r != nil { handler } }(); body }()
        if not stmt.handlers:
            # No handlers, just emit body
            for s in stmt.body:
                self._emit_stmt(s)
            return
        # Check for "try assign, except return fallback" pattern:
        # try: result = call() except Error: cleanup; return fallback
        if self._is_try_assign_except_return(stmt):
            self._emit_try_assign_except_return(stmt)
            return
        # Check for complex patterns (return statements inside try) - skip these
        if self._has_return_in_block(stmt.body) or self._has_return_in_block(stmt.handlers[0].body):
            raise NotImplementedError("try/except with return")
        # Single handler expected (all our cases)
        handler = stmt.handlers[0]
        # Determine the pattern based on handler body
        is_reraise = False
        handler_stmts = []
        for h in handler.body:
            if isinstance(h, ast.Raise):
                is_reraise = True
            elif isinstance(h, ast.Pass):
                pass  # Silent pass - no handler statements
            else:
                handler_stmts.append(h)
        # Start the IIFE
        self.emit("func() {")
        self.indent += 1
        # Emit the defer/recover
        self.emit("defer func() {")
        self.indent += 1
        self.emit("if r := recover(); r != nil {")
        self.indent += 1
        # Emit handler statements (cleanup before re-raise, or fallback assignment)
        for h in handler_stmts:
            self._emit_stmt(h)
        if is_reraise:
            self.emit("panic(r)")
        # If silent pass, we just swallow the panic (no action needed)
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}()")
        # Emit try body
        for s in stmt.body:
            self._emit_stmt(s)
        self.indent -= 1
        self.emit("}()")

    def _format_params(self, params: list[ParamInfo]) -> str:
        """Format parameter list for Go function signature."""
        parts = []
        for p in params:
            go_name = self._to_go_var(p.name)
            go_type = p.go_type or "interface{}"
            parts.append(f"{go_name} {go_type}")
        return ", ".join(parts)


def main():
    if len(sys.argv) < 2:
        print("Usage: transpiler --transpile-go <input.py>", file=sys.stderr)
        sys.exit(1)
    source = Path(sys.argv[1]).read_text()
    transpiler = GoTranspiler()
    code = transpiler.transpile(source)
    if shutil.which("goimports"):
        result = subprocess.run(["goimports"], input=code, capture_output=True, text=True)
        if result.returncode == 0:
            code = result.stdout
        else:
            print(f"goimports failed: {result.stderr}", file=sys.stderr)
    print(code)


if __name__ == "__main__":
    main()
