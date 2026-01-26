"""Function and method emission for Go transpiler."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from .go_manual import MANUAL_FUNCTIONS, MANUAL_METHODS
from .go_types import FunctionAnalysis, ScopeInfo

if TYPE_CHECKING:
    from .go_types import ClassInfo, FuncInfo, ParamInfo, SymbolTable, VarInfo

    class _EmitFunctionsMixinProtocol:
        """Type stubs for methods from other mixins (TYPE_CHECKING only)."""

        symbols: SymbolTable
        current_class: str | None
        current_method: str | None
        current_func_info: FuncInfo | None
        current_return_type: str
        indent: int
        declared_vars: set[str]
        byte_vars: set[str]
        tuple_vars: dict[str, list[str]]
        tuple_func_vars: dict[str, str]
        var_types: dict[str, str]
        var_assign_sources: dict[str, str]
        returned_vars: set[str]
        scope_tree: dict[int, ScopeInfo]
        next_scope_id: int
        var_usage: VarInfo
        hoisted_vars: dict[str, int]
        scope_id_map: dict[int, int]
        SKIP_BODY_FUNCTIONS: set[str]
        SKIP_METHODS: set[str]

        def emit(self, text: str) -> None: ...
        def visit_expr(self, node: ast.expr) -> str: ...
        def _to_go_var(self, name: str) -> str: ...
        def _to_go_func_name(self, name: str) -> str: ...
        def _to_go_field_name(self, name: str) -> str: ...
        def _py_type_to_go(self, py_type: str, concrete_nodes: bool = False) -> str: ...
        def _snake_to_camel(self, name: str) -> str: ...
        def _emit_bool_expr(self, node: ast.expr) -> str: ...
        def _is_string_subscript(self, node: ast.Subscript) -> bool: ...
        def _is_string_expr(self, node: ast.expr) -> bool: ...
        def _infer_literal_elem_type(self, node: ast.expr) -> str: ...
        def _emit_stmt(self, stmt: ast.stmt) -> None: ...
        def _collect_isinstance_chain(self, stmts: list[ast.stmt], idx: int) -> list: ...
        def _emit_type_switch(self, var_name: str, cases: list) -> None: ...
        def _detect_assign_check_return(
            self, stmts: list[ast.stmt], idx: int
        ) -> tuple | None: ...
        def _emit_assign_check_return(
            self, var_name: str, call: ast.Call, ret_type: str
        ) -> None: ...
        def _collect_var_scopes(self, stmts: list[ast.stmt], scope_id: int) -> None: ...
        def _compute_hoisting(self) -> None: ...
        def _exclude_assign_check_return_vars(self, stmts: list[ast.stmt]) -> None: ...
        def _populate_var_types_from_usage(self, stmts: list[ast.stmt]) -> None: ...
        def _infer_object_class(self, node: ast.expr) -> str: ...
        def _collect_append_element_types(self, stmts: list[ast.stmt]) -> dict[str, str]: ...
        def _collect_nullable_node_vars(self, stmts: list[ast.stmt]) -> set[str]: ...
        def _collect_nullable_string_vars(self, stmts: list[ast.stmt]) -> set[str]: ...
        def _collect_multi_node_type_vars(self, stmts: list[ast.stmt]) -> set[str]: ...
        def _infer_var_type_from_name(self, var_name: str) -> str: ...
        def _get_current_method_return_type(self) -> str: ...
        def _format_params(self, params: list[ParamInfo]) -> str: ...
        def _infer_type_from_expr(self, node: ast.expr) -> str: ...


class EmitFunctionsMixin:
    """Mixin for function and method code emission."""

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
        # Track return type for nil → zero value conversion
        self.current_return_type = func_info.return_type if func_info else ""
        # Run all analysis first
        analysis = self._analyze_function(stmts, func_info)
        self._analysis = analysis
        # Bridge: copy analysis results to self for emission (temporary)
        self.declared_vars = analysis.declared_vars
        self.var_types = analysis.var_types
        self.scope_tree = analysis.scope_tree
        self.next_scope_id = len(analysis.scope_tree) + 1
        self.var_usage = analysis.var_usage
        self.hoisted_vars = analysis.hoisted_vars
        self.scope_id_map = analysis.scope_id_map
        self.returned_vars = analysis.returned_vars
        self.byte_vars = analysis.byte_vars
        self.tuple_vars = analysis.tuple_vars
        self.tuple_func_vars = analysis.tuple_func_vars
        self.var_assign_sources = analysis.var_assign_sources
        # Emit hoisted declarations for function scope (scope 0)
        self._emit_hoisted_vars(analysis, 0, stmts)
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

    def _analyze_function(
        self, stmts: list[ast.stmt], func_info: "FuncInfo | None"
    ) -> FunctionAnalysis:
        """Perform all analysis for a function body, returning analysis results."""
        analysis = FunctionAnalysis()
        # Initialize scope tree with function scope (scope 0)
        analysis.scope_tree[0] = ScopeInfo(0, None, 0)
        # Initialize from params
        if func_info:
            for p in func_info.params:
                go_name = self._to_go_var(p.name)
                analysis.declared_vars.add(go_name)
                analysis.var_types[go_name] = p.go_type
        # Temporarily swap self state with analysis fields so existing methods work
        old_declared = getattr(self, "declared_vars", set())
        old_var_types = getattr(self, "var_types", {})
        old_scope_tree = getattr(self, "scope_tree", {})
        old_next_scope_id = getattr(self, "next_scope_id", 1)
        old_var_usage = getattr(self, "var_usage", {})
        old_hoisted_vars = getattr(self, "hoisted_vars", {})
        old_scope_id_map = getattr(self, "scope_id_map", {})
        old_returned_vars = getattr(self, "returned_vars", set())
        old_byte_vars = getattr(self, "byte_vars", set())
        old_tuple_vars = getattr(self, "tuple_vars", {})
        old_tuple_func_vars = getattr(self, "tuple_func_vars", {})
        old_var_assign_sources = getattr(self, "var_assign_sources", {})
        try:
            self.declared_vars = analysis.declared_vars
            self.var_types = analysis.var_types
            self.scope_tree = analysis.scope_tree
            self.next_scope_id = 1
            self.var_usage = analysis.var_usage
            self.hoisted_vars = analysis.hoisted_vars
            self.scope_id_map = analysis.scope_id_map
            self.returned_vars = analysis.returned_vars
            self.byte_vars = analysis.byte_vars
            self.tuple_vars = analysis.tuple_vars
            self.tuple_func_vars = analysis.tuple_func_vars
            self.var_assign_sources = analysis.var_assign_sources
            # Run analysis methods
            self._analyze_var_types(stmts)
            self._collect_var_scopes(stmts, scope_id=0)
            self._compute_hoisting()
            self._exclude_assign_check_return_vars(stmts)
            self._populate_var_types_from_usage(stmts)
            self._scan_returned_vars(stmts)
        finally:
            # Restore old state
            self.declared_vars = old_declared
            self.var_types = old_var_types
            self.scope_tree = old_scope_tree
            self.next_scope_id = old_next_scope_id
            self.var_usage = old_var_usage
            self.hoisted_vars = old_hoisted_vars
            self.scope_id_map = old_scope_id_map
            self.returned_vars = old_returned_vars
            self.byte_vars = old_byte_vars
            self.tuple_vars = old_tuple_vars
            self.tuple_func_vars = old_tuple_func_vars
            self.var_assign_sources = old_var_assign_sources
        return analysis

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
        # Set up minimal analysis for constructor body
        analysis = FunctionAnalysis()
        func_info = class_info.methods.get("__init__")
        if func_info:
            for p in func_info.params:
                go_name = self._to_go_var(p.name)
                analysis.declared_vars.add(go_name)
                analysis.var_types[go_name] = p.go_type
        self._analysis = analysis
        # Bridge: also set on self for compatibility
        self.var_types = analysis.var_types
        self.declared_vars = analysis.declared_vars
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

    def _emit_hoisted_vars(
        self, analysis: FunctionAnalysis, scope_id: int, stmts: list[ast.stmt]
    ):
        """Emit hoisted variable declarations for a scope."""
        # Collect additional type info
        append_types = self._collect_append_element_types(stmts)
        nullable_node_vars = self._collect_nullable_node_vars(stmts)
        nullable_string_vars = self._collect_nullable_string_vars(stmts)
        multi_node_vars = self._collect_multi_node_type_vars(stmts)
        for var, hoist_scope in analysis.hoisted_vars.items():
            if hoist_scope != scope_id:
                continue
            if var in analysis.declared_vars:
                continue
            # Get type from var_types first
            go_type = analysis.var_types.get(var)
            # Try to infer from first value if no type yet
            info = analysis.var_usage.get(var)
            if info and info.first_value and not go_type:
                go_type = self._infer_type_from_expr(info.first_value)
            # Check append() calls for element type
            if var in append_types:
                elem_type = append_types[var]
                if elem_type and (
                    not go_type or go_type in ("interface{}", "[]interface{}", "[]string")
                ):
                    go_type = f"[]{elem_type}"
            # Check if var is None-initialized but later assigned Node types
            if var in nullable_node_vars:
                if not go_type or go_type == "interface{}":
                    go_type = "Node"
            # Check if var is None-initialized but later assigned string types
            if var in nullable_string_vars:
                if not go_type or go_type == "interface{}":
                    go_type = "string"
            # Check if var is assigned multiple different concrete Node types
            if var in multi_node_vars:
                if go_type and go_type.startswith("*") and go_type[1:] in self.symbols.classes:
                    if self.symbols.classes[go_type[1:]].is_node:
                        go_type = "Node"
            if not go_type or go_type in ("interface{}", "[]interface{}"):
                go_type = self._infer_var_type_from_name(var) or go_type or "interface{}"
            # Special case: 'results' in a method that returns []Node
            if var.lower() == "results" and self.current_method:
                method_ret = self._get_current_method_return_type()
                if method_ret == "[]Node":
                    go_type = method_ret
            # Special case: if expr says byte but name says string, prefer string
            if go_type == "byte":
                name_type = self._infer_var_type_from_name(var)
                if name_type == "string":
                    go_type = "string"
            self.emit(f"var {var} {go_type}")
            analysis.declared_vars.add(var)
            analysis.var_types[var] = go_type
