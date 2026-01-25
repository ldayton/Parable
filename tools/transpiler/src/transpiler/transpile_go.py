#!/usr/bin/env python3
"""Transpile parable.py's restricted Python subset to Go."""

import ast
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ScopeInfo:
    """Information about a scope in the scope tree."""

    id: int
    parent: int | None  # None for function scope (root)
    depth: int  # 0 for function scope


@dataclass
class VarInfo:
    """Information about a variable's usage across scopes."""

    name: str
    go_type: str
    assign_scopes: set[int] = field(default_factory=set)  # All scope IDs where assigned
    read_scopes: set[int] = field(default_factory=set)  # Scope IDs where read
    first_value: "ast.expr | None" = None  # First assigned value (for type inference)


@dataclass
class FieldInfo:
    """Information about a struct field."""

    name: str
    py_type: str  # Original Python type annotation
    go_type: str  # Resolved Go type


@dataclass
class ParamInfo:
    """Information about a function parameter."""

    name: str
    py_type: str
    go_type: str
    default: ast.expr | None = None


@dataclass
class FuncInfo:
    """Information about a function or method."""

    name: str
    params: list[ParamInfo]
    return_type: str  # Go type
    is_method: bool = False
    receiver_type: str = ""  # For methods, the type that owns this method


@dataclass
class ClassInfo:
    """Information about a class/struct."""

    name: str
    bases: list[str]
    fields: dict[str, FieldInfo] = field(default_factory=dict)
    methods: dict[str, FuncInfo] = field(default_factory=dict)
    is_node: bool = False  # True if this is a Node subclass
    constants: dict[str, int | str] = field(default_factory=dict)  # Class-level constants


class SymbolTable:
    """Symbol table for type resolution."""

    def __init__(self):
        self.classes: dict[str, ClassInfo] = {}
        self.functions: dict[str, FuncInfo] = {}
        self.constants: dict[str, str] = {}  # name -> Go type

    def is_node_subclass(self, class_name: str) -> bool:
        """Check if a class is a Node subclass (directly or transitively)."""
        if class_name == "Node":
            return True
        info = self.classes.get(class_name)
        if not info:
            return False
        for base in info.bases:
            if self.is_node_subclass(base):
                return True
        return False


class GoTranspiler(ast.NodeVisitor):
    """Transpiles Python AST to Go source code."""

    # Python type -> Go type mapping
    TYPE_MAP = {
        "str": "string",
        "int": "int",
        "bool": "bool",
        "None": "",
        "float": "float64",
        "bytes": "[]byte",
        # Type aliases used in annotations
        "CommandSub": "*CommandSubstitution",
        "ProcessSub": "*ProcessSubstitution",
    }

    # Node kind string -> Go type name mapping (for kind-based type narrowing)
    KIND_TO_TYPE = {
        # Arithmetic nodes
        "var": "ArithVar",
        "number": "ArithNumber",
        "binary-op": "ArithBinaryOp",
        "unary-op": "ArithUnaryOp",
        "pre-incr": "ArithPreIncr",
        "post-incr": "ArithPostIncr",
        "pre-decr": "ArithPreDecr",
        "post-decr": "ArithPostDecr",
        "assign": "ArithAssign",
        "ternary": "ArithTernary",
        "subscript": "ArithSubscript",
        "comma": "ArithComma",
        "escape": "ArithEscape",
        "arith-deprecated": "ArithDeprecated",
        "arith-concat": "ArithConcat",
        "empty": "ArithEmpty",
        # Command nodes
        "command": "Command",
        "pipeline": "Pipeline",
        "list": "List",
        "subshell": "Subshell",
        "brace-group": "BraceGroup",
        "negation": "Negation",
        "heredoc": "HereDoc",
        "redirect": "Redirect",
        "word": "Word",
    }

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

    # ========== Symbol Collection Passes ==========

    def _collect_symbols(self, tree: ast.Module):
        """Collect all type information in multiple passes."""
        # Pass 1: Collect class names and inheritance
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [self._get_base_name(b) for b in node.bases]
                self.symbols.classes[node.name] = ClassInfo(
                    name=node.name, bases=bases, fields={}, methods={}
                )
        # Mark Node subclasses
        for name, info in self.symbols.classes.items():
            info.is_node = self.symbols.is_node_subclass(name)
        # Pass 2: Collect function signatures
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                self.symbols.functions[node.name] = self._extract_func_info(node)
            elif isinstance(node, ast.ClassDef):
                self._collect_class_methods(node)
        # Pass 3: Collect struct fields from __init__
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                self._collect_class_fields(node)

    def _get_base_name(self, base: ast.expr) -> str:
        """Extract base class name from AST node."""
        if isinstance(base, ast.Name):
            return base.id
        if isinstance(base, ast.Attribute):
            return base.attr
        return ""

    def _collect_class_methods(self, node: ast.ClassDef):
        """Collect method signatures for a class."""
        class_info = self.symbols.classes[node.name]
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef):
                func_info = self._extract_func_info(stmt, is_method=True)
                func_info.receiver_type = node.name
                class_info.methods[stmt.name] = func_info

    def _collect_class_fields(self, node: ast.ClassDef):
        """Collect struct fields from class definition and __init__."""
        class_info = self.symbols.classes[node.name]
        # Collect class-level annotations
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                py_type = self._annotation_to_str(stmt.annotation)
                go_type = self._py_type_to_go(py_type)
                class_info.fields[stmt.target.id] = FieldInfo(
                    name=stmt.target.id, py_type=py_type, go_type=go_type
                )
        # Collect class-level constant assignments (for enum-like classes)
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and isinstance(stmt.value, ast.Constant):
                        # This is a class-level constant
                        class_info.constants[target.id] = stmt.value.value
        # Collect fields from __init__ assignments
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                self._collect_init_fields(stmt, class_info)

    def _collect_init_fields(self, init: ast.FunctionDef, class_info: ClassInfo):
        """Collect fields assigned in __init__."""
        param_types = {}
        for arg in init.args.args:
            if arg.arg != "self" and arg.annotation:
                param_types[arg.arg] = self._annotation_to_str(arg.annotation)
        for stmt in ast.walk(init):
            # Handle regular assignment: self.x = value
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                    ):
                        field_name = target.attr
                        if field_name not in class_info.fields:
                            go_type = self._infer_type(stmt.value, param_types)
                            class_info.fields[field_name] = FieldInfo(
                                name=field_name, py_type="", go_type=go_type
                            )
            # Handle annotated assignment: self.x: Type = value
            elif isinstance(stmt, ast.AnnAssign):
                if (
                    isinstance(stmt.target, ast.Attribute)
                    and isinstance(stmt.target.value, ast.Name)
                    and stmt.target.value.id == "self"
                ):
                    field_name = stmt.target.attr
                    if field_name not in class_info.fields:
                        py_type = self._annotation_to_str(stmt.annotation)
                        go_type = self._py_type_to_go(py_type)
                        # Apply field type overrides
                        override_key = (class_info.name, field_name)
                        if override_key in self.FIELD_TYPE_OVERRIDES:
                            go_type = self.FIELD_TYPE_OVERRIDES[override_key]
                        class_info.fields[field_name] = FieldInfo(
                            name=field_name, py_type=py_type, go_type=go_type
                        )

    # Override parameter types for functions with bare "list" annotations
    # Maps (method_name, param_name) -> Go type
    # Use *[]T (pointer-to-slice) for parameters that are mutated by the callee
    PARAM_TYPE_OVERRIDES = {
        ("_read_bracket_expression", "chars"): "*[]string",
        ("_read_bracket_expression", "parts"): "*[]Node",
        ("_parse_dollar_expansion", "chars"): "*[]string",
        ("_parse_dollar_expansion", "parts"): "*[]Node",
        ("_scan_double_quote", "chars"): "*[]string",
        ("_scan_double_quote", "parts"): "*[]Node",
        ("restore_from", "saved_stack"): "[]*ParseContext",
        ("copy_stack", "_result"): "[]*ParseContext",  # return type hint
        # SavedParserState constructor parameters
        ("__init__", "pending_heredocs"): "[]Node",
        # Token constructor parameters
        ("__init__", "parts"): "[]Node",
        ("__init__", "ctx_stack"): "[]*ParseContext",
        # List class methods - parts is always []Node, op_names is map[string]string
        ("_to_sexp_with_precedence", "parts"): "[]Node",
        ("_to_sexp_with_precedence", "op_names"): "map[string]string",
        ("_to_sexp_amp_and_higher", "parts"): "[]Node",
        ("_to_sexp_amp_and_higher", "op_names"): "map[string]string",
        ("_to_sexp_and_or", "parts"): "[]Node",
        ("_to_sexp_and_or", "op_names"): "map[string]string",
        # Redirect handling - only reads, no mutation
        ("_append_redirects", "redirects"): "[]Node",
        # Bytearray mutation - needs pointer to avoid losing appends
        ("_append_with_ctlesc", "result"): "*[]byte",
    }

    # Override field types for fields without proper annotations
    # Maps (class_name, field_name) -> Go type (field_name is Python name, lowercase)
    FIELD_TYPE_OVERRIDES = {
        ("Lexer", "_word_context"): "int",
        ("Parser", "_word_context"): "int",
        # Source_runes for rune-based indexing (Unicode support)
        ("Lexer", "source_runes"): "[]rune",
        ("Parser", "source_runes"): "[]rune",
        # Untyped list fields that need concrete slice types
        ("SavedParserState", "pending_heredocs"): "[]Node",
        ("SavedParserState", "ctx_stack"): "[]*ParseContext",
        ("SavedParserState", "token_history"): "[]*Token",
        ("Parser", "_token_history"): "[]*Token",
        # Dynamically created fields for arithmetic parsing
        ("Parser", "_arith_src"): "string",
        ("Parser", "_arith_pos"): "int",
        # QuoteState uses tuple stack - use custom struct
        ("QuoteState", "_stack"): "[]quoteStackEntry",
        ("Parser", "_arith_len"): "int",
    }

    # Override return types for methods that return generic list
    # Maps method_name -> Go return type
    RETURN_TYPE_OVERRIDES = {
        "_collect_cmdsubs": "[]Node",
        "_collect_procsubs": "[]Node",
        "_collect_redirects": "[]Node",
        "copy_stack": "[]*ParseContext",
        "parse_for": "Node",  # Returns For | ForArith | None
    }

    # Tuple element types for functions returning tuples with typed elements
    # Maps function_name -> {element_index -> Go type}
    TUPLE_ELEMENT_TYPES = {
        "_ConsumeSingleQuote": {0: "int", 1: "[]string"},
        "_ConsumeDoubleQuote": {0: "int", 1: "[]string"},
        "_ConsumeBracketClass": {0: "int", 1: "[]string"},
    }

    # Union field discriminators for Node | str union types
    # Maps (receiver_type, field_name) -> (discriminator_var, nil_type, non_nil_type)
    # discriminator_var is the variable that holds getattr(field, "kind", nil)
    # field_name is the Python name (lowercase), not the Go name
    UNION_FIELDS = {
        ("ConditionalExpr", "body"): ("bodyKind", "string", "Node"),
    }

    def _extract_func_info(self, node: ast.FunctionDef, is_method: bool = False) -> FuncInfo:
        """Extract function signature information."""
        params = []
        for arg in node.args.args:
            if arg.arg == "self":
                continue
            py_type = self._annotation_to_str(arg.annotation) if arg.annotation else ""
            go_type = self._py_type_to_go(py_type) if py_type else "interface{}"
            # Check for overrides
            override_key = (node.name, arg.arg)
            if override_key in self.PARAM_TYPE_OVERRIDES:
                go_type = self.PARAM_TYPE_OVERRIDES[override_key]
            params.append(ParamInfo(name=arg.arg, py_type=py_type, go_type=go_type))
        # Handle defaults
        defaults = node.args.defaults
        if defaults:
            offset = len(params) - len(defaults)
            for i, default in enumerate(defaults):
                params[offset + i].default = default
        return_type = ""
        if node.returns:
            py_return = self._annotation_to_str(node.returns)
            return_type = self._py_return_type_to_go(py_return)
        # Apply return type overrides
        if node.name in self.RETURN_TYPE_OVERRIDES:
            return_type = self.RETURN_TYPE_OVERRIDES[node.name]
        return FuncInfo(
            name=node.name,
            params=params,
            return_type=return_type,
            is_method=is_method,
        )

    def _annotation_to_str(self, node: ast.expr | None) -> str:
        """Convert type annotation AST to string."""
        if node is None:
            return ""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Constant):
            return str(node.value) if node.value is not None else "None"
        if isinstance(node, ast.Subscript):
            base = self._annotation_to_str(node.value)
            if isinstance(node.slice, ast.Tuple):
                args = ", ".join(self._annotation_to_str(e) for e in node.slice.elts)
            else:
                args = self._annotation_to_str(node.slice)
            return f"{base}[{args}]"
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            left = self._annotation_to_str(node.left)
            right = self._annotation_to_str(node.right)
            return f"{left} | {right}"
        if isinstance(node, ast.Attribute):
            return node.attr
        return ""

    def _py_type_to_go(self, py_type: str, concrete_nodes: bool = False) -> str:
        """Convert Python type string to Go type.

        Args:
            py_type: Python type string
            concrete_nodes: If True, return concrete pointer types for Node subclasses
                           instead of the Node interface. Useful for return types.
        """
        if not py_type:
            return ""
        # Handle simple types
        if py_type in self.TYPE_MAP:
            return self.TYPE_MAP[py_type]
        # Handle bare "list" without type args
        if py_type == "list":
            return "[]interface{}"
        # Handle bare "dict" without type args
        if py_type == "dict":
            return "map[string]interface{}"
        # Handle bare "set" without type args
        if py_type == "set":
            return "map[interface{}]struct{}"
        # Handle X | None -> use base type (nil becomes zero value)
        # MUST come before list[...] check to handle "list[X | Y] | None" correctly
        # But only if there's a top-level union (not inside brackets)
        if " | " in py_type:
            parts = self._split_union_types(py_type)
            # Only process if this is actually a top-level union (more than 1 part)
            if len(parts) > 1:
                parts = [p for p in parts if p != "None"]
                if len(parts) == 1:
                    return self._py_type_to_go(parts[0], concrete_nodes)
                # If all parts are Node subclasses, return Node
                elif all(self.symbols.is_node_subclass(p) for p in parts):
                    return "Node"
                return "interface{}"
        # Handle list[X]
        if py_type.startswith("list["):
            inner = py_type[5:-1]
            return "[]" + self._py_type_to_go(inner, concrete_nodes)
        # Handle dict[K, V]
        if py_type.startswith("dict["):
            inner = py_type[5:-1]
            parts = self._split_type_args(inner)
            if len(parts) == 2:
                return f"map[{self._py_type_to_go(parts[0], concrete_nodes)}]{self._py_type_to_go(parts[1], concrete_nodes)}"
        # Handle set[X]
        if py_type.startswith("set["):
            inner = py_type[4:-1]
            return f"map[{self._py_type_to_go(inner, concrete_nodes)}]struct{{}}"
        # Handle tuple[...] - for fields/params, use interface{}
        # (for return types, use _py_return_type_to_go instead)
        if py_type.startswith("tuple["):
            return "interface{}"
        # Handle Callable[[], ReturnType] -> func() ReturnType
        if py_type.startswith("Callable["):
            inner = py_type[9:-1]  # Remove "Callable[" and "]"
            parts = self._split_type_args(inner)
            if len(parts) >= 2:
                # First part is args (list), second is return type
                args_str = parts[0]
                ret_type = parts[-1]
                go_ret = self._py_type_to_go(ret_type, concrete_nodes)
                # Handle empty args list "[]"
                if args_str == "[]":
                    return f"func() {go_ret}"
                # Handle args list like "[int, str]"
                elif args_str.startswith("[") and args_str.endswith("]"):
                    args_inner = args_str[1:-1]
                    if args_inner:
                        arg_types = [
                            self._py_type_to_go(a.strip(), concrete_nodes)
                            for a in args_inner.split(",")
                        ]
                        return f"func({', '.join(arg_types)}) {go_ret}"
                    else:
                        return f"func() {go_ret}"
            # Unknown Callable format
            return "interface{}"
        # Handle class names (Node subclasses become interface, others become struct)
        if py_type in self.symbols.classes:
            info = self.symbols.classes[py_type]
            if info.is_node or py_type == "Node":
                if concrete_nodes and py_type != "Node":
                    return "*" + py_type  # Concrete pointer type
                return "Node"  # Interface type
            return "*" + py_type  # Pointer to struct
        # Known internal types
        if py_type in ("Token", "QuoteState", "ParseContext", "Lexer", "Parser"):
            return "*" + py_type
        # Type aliases - union types of Node subtypes, treat as Node
        if py_type in ("ArithNode", "CondNode"):
            return "Node"
        # Python builtin aliases
        if py_type == "bytearray":
            return "[]byte"
        if py_type == "tuple":
            return "interface{}"
        # Unknown type - return as-is (could be a type alias)
        return py_type

    def _py_return_type_to_go(self, py_type: str) -> str:
        """Convert Python return type to Go, handling tuples as multiple returns."""
        if not py_type:
            return ""
        # Handle unions (e.g., "tuple[int, str] | None") before tuple
        if " | " in py_type:
            parts = self._split_union_types(py_type)
            if len(parts) > 1:
                # Remove None from union and recurse on remainder
                parts = [p for p in parts if p != "None"]
                if len(parts) == 1:
                    return self._py_return_type_to_go(parts[0])
                # Multiple non-None types - can't represent in Go return
                return "interface{}"
        # Handle tuple[...] specially for return types -> (T1, T2)
        if py_type.startswith("tuple["):
            inner = py_type[6:-1]
            parts = self._split_type_args(inner)
            go_parts = [self._py_type_to_go(p, concrete_nodes=True) for p in parts]
            return f"({', '.join(go_parts)})"
        # For non-tuples, use standard conversion with concrete node types
        return self._py_type_to_go(py_type, concrete_nodes=True)

    def _split_union_types(self, s: str) -> list[str]:
        """Split union types on | respecting nested brackets."""
        parts = []
        current = []
        depth = 0
        for c in s:
            if c == "[":
                depth += 1
                current.append(c)
            elif c == "]":
                depth -= 1
                current.append(c)
            elif c == "|" and depth == 0:
                parts.append("".join(current).strip())
                current = []
            else:
                current.append(c)
        if current:
            parts.append("".join(current).strip())
        return parts

    def _split_type_args(self, s: str) -> list[str]:
        """Split type arguments like 'K, V' respecting nested brackets."""
        parts = []
        current = []
        depth = 0
        for c in s:
            if c == "[":
                depth += 1
                current.append(c)
            elif c == "]":
                depth -= 1
                current.append(c)
            elif c == "," and depth == 0:
                parts.append("".join(current).strip())
                current = []
            else:
                current.append(c)
        if current:
            parts.append("".join(current).strip())
        return parts

    def _infer_type(self, node: ast.expr, param_types: dict[str, str]) -> str:
        """Infer Go type from an expression."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return "bool"
            if isinstance(node.value, int):
                return "int"
            if isinstance(node.value, str):
                return "string"
            if node.value is None:
                return ""
        if isinstance(node, ast.List):
            if node.elts:
                elem_type = self._infer_type(node.elts[0], param_types)
                return "[]" + elem_type
            return "[]interface{}"
        if isinstance(node, ast.Dict):
            if node.values and all(
                isinstance(v, ast.Constant) and isinstance(v.value, str) for v in node.values
            ):
                return "map[string]string"
            return "map[string]interface{}"
        if isinstance(node, ast.Name):
            if node.id in param_types:
                return self._py_type_to_go(param_types[node.id])
            if node.id == "True" or node.id == "False":
                return "bool"
            if node.id == "None":
                return ""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                # Built-in functions with known return types
                if func_name == "len":
                    return "int"
                if func_name in self.symbols.classes:
                    info = self.symbols.classes[func_name]
                    if info.is_node:
                        return "Node"
                    return "*" + func_name
                if func_name == "QuoteState":
                    return "*QuoteState"
                if func_name == "ContextStack":
                    return "*ContextStack"
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id in param_types:
                return self._py_type_to_go(param_types[node.value.id])
            # Handle class constants (e.g., ParserStateFlags.NONE) - these are ints
            if isinstance(node.value, ast.Name):
                class_name = node.value.id
                if class_name in (
                    "ParserStateFlags",
                    "DolbraceState",
                    "TokenType",
                    "MatchedPairFlags",
                    "WordCtx",
                    "ParseContext",
                ):
                    return "int"
        return "interface{}"

    # ========== Code Emission ==========

    def visit_Module(self, node: ast.Module):
        """Emit package declaration and all definitions."""
        # Package comment with usage example
        self.emit("// Package parable is a recursive descent parser for bash.")
        self.emit("//")
        self.emit("// MIT License - https://github.com/ldayton/Parable")
        self.emit("//")
        self.emit('//   import "parable"')
        self.emit('//   ast, err := parable.Parse("ps aux | grep python")')
        self.emit("package parable")
        self.emit("")
        # Emit imports
        self._emit_imports()
        # Emit error types first
        self._emit_error_types()
        # Emit Node interface
        self._emit_node_interface()
        # Emit module-level constants
        self._emit_module_constants(node)
        # Emit helper types
        self._emit_helper_types()
        # Emit all structs
        self._emit_all_structs()
        # Emit helper functions
        self._emit_helper_functions(node)
        # Emit methods for all classes
        self._emit_all_methods(node)

    def _emit_module_constants(self, tree: ast.Module):
        """Emit module-level constants."""
        # Skip these as they're manually emitted or handled specially
        skip_constants = {"ANSI_C_ESCAPES"}
        constants = []
        sets = []  # For set literals like RESERVED_WORDS
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        if name in skip_constants:
                            continue
                        # Check if it's a constant (uppercase or _UPPERCASE)
                        if name.isupper() or (name.startswith("_") and name[1:].isupper()):
                            if isinstance(node.value, ast.Constant):
                                constants.append((name, node.value.value))
                            elif isinstance(node.value, ast.Set):
                                # Handle set literals as map[string]bool for O(1) lookup
                                elts = []
                                for elt in node.value.elts:
                                    if isinstance(elt, ast.Constant):
                                        elts.append(elt.value)
                                if elts:
                                    sets.append((name, elts))
        if constants:
            self.emit("// Module-level constants")
            self.emit("const (")
            self.indent += 1
            for name, value in constants:
                # Convert Python name to Go name (remove leading underscore, use CamelCase)
                go_name = name.lstrip("_")
                # Convert SCREAMING_CASE to CamelCase
                parts = go_name.split("_")
                go_name = "".join(p.capitalize() for p in parts)
                if isinstance(value, int):
                    self.emit(f"{go_name} = {value}")
                elif isinstance(value, str):
                    self.emit(f'{go_name} = "{value}"')
                else:
                    self.emit(f"{go_name} = {value}")
            self.indent -= 1
            self.emit(")")
            self.emit("")
        # Emit sets as map[string]bool for O(1) lookup (Go doesn't have set type)
        for name, values in sets:
            go_name = name.lstrip("_")
            parts = go_name.split("_")
            go_name = "".join(p.capitalize() for p in parts)
            self.emit(f"var {go_name} = map[string]bool{{")
            self.indent += 1
            for val in sorted(values):
                self.emit(f'"{val}": true,')
            self.indent -= 1
            self.emit("}")
            self.emit("")

    def _emit_imports(self):
        """Emit Go import statements."""
        self.emit("import (")
        self.indent += 1
        self.emit('"fmt"')
        self.emit('"reflect"')
        self.emit('"strconv"')
        self.emit('"strings"')
        self.emit('"unicode"')
        self.emit('"unicode/utf8"')
        self.indent -= 1
        self.emit(")")
        self.emit("")
        # Suppress unused import warnings until we implement bodies
        self.emit("var (")
        self.indent += 1
        self.emit("_ = fmt.Sprintf")
        self.emit("_ = strings.Contains")
        self.emit("_ = strconv.Atoi")
        self.emit("_ = unicode.IsLetter")
        self.emit("_ = utf8.RuneCountInString")
        self.indent -= 1
        self.emit(")")
        self.emit("")

    def _emit_error_types(self):
        """Emit ParseError and MatchedPairError structs."""
        # ParseError
        self.emit("// ParseError is raised when parsing fails.")
        self.emit("type ParseError struct {")
        self.indent += 1
        self.emit("Message string")
        self.emit("Pos     int")
        self.emit("Line    int")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("func (e *ParseError) Error() string {")
        self.indent += 1
        self.emit("if e.Line != 0 && e.Pos != 0 {")
        self.indent += 1
        self.emit(
            'return fmt.Sprintf("Parse error at line %d, position %d: %s", e.Line, e.Pos, e.Message)'
        )
        self.indent -= 1
        self.emit("}")
        self.emit("if e.Pos != 0 {")
        self.indent += 1
        self.emit('return fmt.Sprintf("Parse error at position %d: %s", e.Pos, e.Message)')
        self.indent -= 1
        self.emit("}")
        self.emit('return fmt.Sprintf("Parse error: %s", e.Message)')
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # ParseError constructor
        self.emit("func NewParseError(message string, pos int, line int) *ParseError {")
        self.indent += 1
        self.emit("return &ParseError{Message: message, Pos: pos, Line: line}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # MatchedPairError
        self.emit("// MatchedPairError is raised when a matched pair is unclosed at EOF.")
        self.emit("type MatchedPairError struct {")
        self.indent += 1
        self.emit("ParseError")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # MatchedPairError constructor
        self.emit("func NewMatchedPairError(message string, pos int, line int) *MatchedPairError {")
        self.indent += 1
        self.emit("return &MatchedPairError{ParseError{Message: message, Pos: pos, Line: line}}")
        self.indent -= 1
        self.emit("}")
        self.emit("")

    def _emit_node_interface(self):
        """Emit the Node interface."""
        self.emit("// Node is the base interface for all AST nodes.")
        self.emit("type Node interface {")
        self.indent += 1
        self.emit("Kind() string")
        self.emit("ToSexp() string")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Emit helper functions and constants
        self._emit_helpers()

    def _emit_helpers(self):
        """Emit helper functions needed by transpiled code."""
        # ANSI-C escapes map
        self.emit("// ANSICEscapes maps ANSI-C escape characters to byte values")
        self.emit("var ANSICEscapes = map[rune]int{")
        self.indent += 1
        self.emit("'a': 0x07, 'b': 0x08, 'e': 0x1B, 'E': 0x1B,")
        self.emit("'f': 0x0C, 'n': 0x0A, 'r': 0x0D, 't': 0x09,")
        self.emit("'v': 0x0B, '\\\\': 0x5C, '\"': 0x22, '?': 0x3F,")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Helper functions
        self.emit("func _mapGet[K comparable, V any](m map[K]V, key K, def V) V {")
        self.indent += 1
        self.emit("if v, ok := m[key]; ok {")
        self.indent += 1
        self.emit("return v")
        self.indent -= 1
        self.emit("}")
        self.emit("return def")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("func _ternary[T any](cond bool, a, b T) T {")
        self.indent += 1
        self.emit("if cond {")
        self.indent += 1
        self.emit("return a")
        self.indent -= 1
        self.emit("}")
        self.emit("return b")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Helper to detect typed nil (e.g., (*Command)(nil) assigned to Node interface)
        self.emit("func _isNilNode(n Node) bool {")
        self.indent += 1
        self.emit("if n == nil {")
        self.indent += 1
        self.emit("return true")
        self.indent -= 1
        self.emit("}")
        self.emit("v := reflect.ValueOf(n)")
        self.emit("return v.Kind() == reflect.Ptr && v.IsNil()")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Character helper - get character (rune) from string at character index
        self.emit("func _runeAt(s string, i int) string {")
        self.indent += 1
        self.emit("runes := []rune(s)")
        self.emit("if i < 0 || i >= len(runes) {")
        self.indent += 1
        self.emit('return ""')
        self.indent -= 1
        self.emit("}")
        self.emit("return string(runes[i])")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Rune length helper - get character count (not byte count)
        self.emit("func _runeLen(s string) int {")
        self.indent += 1
        self.emit("return utf8.RuneCountInString(s)")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # String to rune (first char) - uses for range to get first rune
        self.emit("func _strToRune(s string) rune {")
        self.indent += 1
        self.emit("for _, r := range s {")
        self.indent += 1
        self.emit("return r")
        self.indent -= 1
        self.emit("}")
        self.emit("return 0")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Convert any char type (string, byte, rune) to rune
        self.emit("func _runeFromChar(c interface{}) rune {")
        self.indent += 1
        self.emit("switch v := c.(type) {")
        self.emit("case rune:")
        self.indent += 1
        self.emit("return v")
        self.indent -= 1
        self.emit("case byte:")
        self.indent += 1
        self.emit("return rune(v)")
        self.indent -= 1
        self.emit("case string:")
        self.indent += 1
        self.emit("for _, r := range v {")
        self.indent += 1
        self.emit("return r")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("return 0")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Contains helper for `in` operator
        self.emit("func _contains[T comparable](slice []T, val T) bool {")
        self.indent += 1
        self.emit("for _, v := range slice {")
        self.indent += 1
        self.emit("if v == val {")
        self.indent += 1
        self.emit("return true")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("return false")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Contains helper for interface{} slices
        self.emit("func _containsAny(slice []interface{}, val interface{}) bool {")
        self.indent += 1
        self.emit("for _, v := range slice {")
        self.indent += 1
        self.emit("if v == val {")
        self.indent += 1
        self.emit("return true")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("return false")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # parseInt helper - int(str, base) equivalent
        self.emit("func _parseInt(s string, base int) int {")
        self.indent += 1
        self.emit("v, err := strconv.ParseInt(s, base, 64)")
        self.emit("if err != nil {")
        self.indent += 1
        self.emit("return 0")
        self.indent -= 1
        self.emit("}")
        self.emit("return int(v)")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # max/min helpers for int
        self.emit("func _max(a, b int) int {")
        self.indent += 1
        self.emit("if a > b {")
        self.indent += 1
        self.emit("return a")
        self.indent -= 1
        self.emit("}")
        self.emit("return b")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("func _min(a, b int) int {")
        self.indent += 1
        self.emit("if a < b {")
        self.indent += 1
        self.emit("return a")
        self.indent -= 1
        self.emit("}")
        self.emit("return b")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # mustAtoi helper - int(str) equivalent
        self.emit("func _mustAtoi(s string) int {")
        self.indent += 1
        self.emit("v, err := strconv.Atoi(s)")
        self.emit("if err != nil {")
        self.indent += 1
        self.emit("return 0")
        self.indent -= 1
        self.emit("}")
        self.emit("return v")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # _strIsDigits helper - str.isdigit() equivalent (true if non-empty and all digits)
        self.emit("func _strIsDigits(s string) bool {")
        self.indent += 1
        self.emit("if len(s) == 0 {")
        self.indent += 1
        self.emit("return false")
        self.indent -= 1
        self.emit("}")
        self.emit("for _, r := range s {")
        self.indent += 1
        self.emit("if !unicode.IsDigit(r) {")
        self.indent += 1
        self.emit("return false")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("return true")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # _getattr helper - getattr(obj, attr, default) equivalent using reflection
        self.emit("func _getattr(obj interface{}, attr string, def interface{}) interface{} {")
        self.indent += 1
        self.emit("if obj == nil {")
        self.indent += 1
        self.emit("return def")
        self.indent -= 1
        self.emit("}")
        self.emit("v := reflect.ValueOf(obj)")
        self.emit("if v.Kind() == reflect.Ptr {")
        self.indent += 1
        self.emit("v = v.Elem()")
        self.indent -= 1
        self.emit("}")
        self.emit("if v.Kind() != reflect.Struct {")
        self.indent += 1
        self.emit("return def")
        self.indent -= 1
        self.emit("}")
        self.emit("// Convert snake_case to PascalCase")
        self.emit("fieldName := _snakeToPascal(attr)")
        self.emit("f := v.FieldByName(fieldName)")
        self.emit("if !f.IsValid() {")
        self.indent += 1
        self.emit("// Try lowercase 'kind' field")
        self.emit('if attr == "kind" {')
        self.indent += 1
        self.emit('f = v.FieldByName("kind")')
        self.emit("if f.IsValid() {")
        self.indent += 1
        self.emit("return f.Interface()")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("return def")
        self.indent -= 1
        self.emit("}")
        self.emit("return f.Interface()")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # _FormatArithVal helper - formats arithmetic values for to_sexp
        self.emit("func _FormatArithVal(s string) string {")
        self.indent += 1
        self.emit("w := NewWord(s, []Node{})")
        self.emit("val := w._ExpandAllAnsiCQuotes(s)")
        self.emit("val = w._StripLocaleStringDollars(val)")
        self.emit("val = w._FormatCommandSubstitutions(val, false)")
        self.emit(
            'val = strings.ReplaceAll(strings.ReplaceAll(val, "\\\\", "\\\\\\\\"), "\\"", "\\\\\\"")'
        )
        self.emit(
            'val = strings.ReplaceAll(strings.ReplaceAll(val, "\\n", "\\\\n"), "\\t", "\\\\t")'
        )
        self.emit("return val")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # _snakeToPascal helper
        self.emit("func _snakeToPascal(s string) string {")
        self.indent += 1
        self.emit('parts := strings.Split(s, "_")')
        self.emit("for i, p := range parts {")
        self.indent += 1
        self.emit("if len(p) > 0 {")
        self.indent += 1
        self.emit("parts[i] = strings.ToUpper(p[:1]) + p[1:]")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit('return strings.Join(parts, "")')
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # _Substring helper - rune-based substring extraction
        self.emit("func _Substring(s string, start int, end int) string {")
        self.indent += 1
        self.emit("runes := []rune(s)")
        self.emit("if start < 0 {")
        self.indent += 1
        self.emit("start = 0")
        self.indent -= 1
        self.emit("}")
        self.emit("if end > len(runes) {")
        self.indent += 1
        self.emit("end = len(runes)")
        self.indent -= 1
        self.emit("}")
        self.emit("if start >= end {")
        self.indent += 1
        self.emit('return ""')
        self.indent -= 1
        self.emit("}")
        self.emit("return string(runes[start:end])")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # _pop helper - pop from slice (generic)
        self.emit("func _pop[T any](s *[]T) T {")
        self.indent += 1
        self.emit("last := (*s)[len(*s)-1]")
        self.emit("*s = (*s)[:len(*s)-1]")
        self.emit("return last")
        self.indent -= 1
        self.emit("}")
        self.emit("")

    def _emit_helper_types(self):
        """Emit helper types used by transpiled code."""
        # quoteStackEntry is used by QuoteState._Stack to hold (single, double) tuples
        self.emit("// quoteStackEntry holds pushed quote state (single, double)")
        self.emit("type quoteStackEntry struct {")
        self.indent += 1
        self.emit("single bool")
        self.emit("double bool")
        self.indent -= 1
        self.emit("}")
        self.emit("")

    def _emit_all_structs(self):
        """Emit all struct definitions."""
        # Skip error types (already emitted) and Node (interface)
        skip = {"ParseError", "MatchedPairError", "Node"}
        for name, info in self.symbols.classes.items():
            if name in skip:
                continue
            self._emit_struct(name, info)

    def _emit_struct(self, name: str, info: ClassInfo):
        """Emit a single struct definition."""
        is_node = "Node" in info.bases
        # Emit class constants first
        if info.constants:
            self.emit(f"// {name} constants")
            self.emit("const (")
            self.indent += 1
            for const_name, const_value in info.constants.items():
                go_const_name = f"{name}_{const_name}"
                if isinstance(const_value, int):
                    # Format hex values
                    if const_value > 9 and const_value not in (10, 100, 1000):
                        self.emit(f"{go_const_name} = 0x{const_value:02X}")
                    else:
                        self.emit(f"{go_const_name} = {const_value}")
                else:
                    self.emit(f'{go_const_name} = "{const_value}"')
            self.indent -= 1
            self.emit(")")
            self.emit("")
        # Skip struct emission for enum-only classes (no fields, no __init__)
        if (
            info.constants
            and not info.fields
            and not any(m for m in info.methods if m != "__init__" or info.methods[m].params)
        ):
            return
        self.emit(f"type {name} struct {{")
        self.indent += 1
        # Embed base classes (except Node which is an interface)
        for base in info.bases:
            if base != "Node" and base != "Exception":
                self.emit(base)
        # Emit fields
        for field_name, field_info in info.fields.items():
            go_type = field_info.go_type or "interface{}"
            # Check for field type overrides
            override_key = (name, field_name)
            if override_key in self.FIELD_TYPE_OVERRIDES:
                go_type = self.FIELD_TYPE_OVERRIDES[override_key]
            # For Node structs, make 'kind' lowercase to avoid conflict with Kind() method
            if is_node and field_name == "kind":
                self.emit(f"kind {go_type}")
            else:
                go_name = self._to_go_field_name(field_name)
                self.emit(f"{go_name} {go_type}")
        # Emit additional fields from FIELD_TYPE_OVERRIDES that don't exist in the class
        for (class_name, field_name), go_type in self.FIELD_TYPE_OVERRIDES.items():
            if class_name == name and field_name not in info.fields:
                go_name = self._to_go_field_name(field_name)
                self.emit(f"{go_name} {go_type}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # For Node structs, emit Kind() and ToSexp() methods to implement Node interface
        if is_node:
            receiver = name[0].lower()
            self.emit(f"func ({receiver} *{name}) Kind() string {{")
            self.indent += 1
            self.emit(f"return {receiver}.kind")
            self.indent -= 1
            self.emit("}")
            self.emit("")
            # ToSexp() will be implemented by the actual method, emit stub if not defined
            if "to_sexp" not in info.methods:
                self.emit(f"func ({receiver} *{name}) ToSexp() string {{")
                self.indent += 1
                self.emit('panic("TODO: ToSexp not implemented")')
                self.indent -= 1
                self.emit("}")
                self.emit("")

    def _to_go_field_name(self, name: str) -> str:
        """Convert Python field name to Go exported field name."""
        if name.startswith("_"):
            # Private fields stay private but capitalize rest
            return name[0] + self._capitalize_first(name[1:])
        return self._capitalize_first(name)

    def _capitalize_first(self, name: str) -> str:
        """Capitalize first letter of name."""
        if not name:
            return name
        return name[0].upper() + name[1:]

    # Functions that are replaced by hardcoded Go implementations (skip transpilation)
    SKIP_FUNCTIONS = {
        "_substring",  # Replaced by rune-based _Substring in _emit_helpers()
    }

    def _emit_helper_functions(self, tree: ast.Module):
        """Emit module-level helper functions."""
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                if node.name in self.SKIP_FUNCTIONS:
                    continue
                self._emit_function(node)

    # Functions that require duck typing (Part 6d) or have complex patterns - skip body for now
    SKIP_BODY_FUNCTIONS = {
        # Duck typing (Part 6d) - isinstance-based dispatch
        "_format_cond_value",
        "_collect_cmdsubs",
        "_collect_assignments",
        # Complex lexer methods with walrus operators
        "_parse_matched_pair",
        "_read_bracket_regex",
    }

    # Methods that truly need manual implementation (tuple stacks, complex patterns)
    # KEEP THIS MINIMAL - fix transpiler issues rather than skipping methods
    SKIP_METHODS = {
        # Higher-order function patterns and arithmetic parsing
        # Higher-order function - not called, kept as stub
        "_arith_parse_left_assoc",
    }

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
        if node.name in self.MANUAL_FUNCTIONS:
            self.MANUAL_FUNCTIONS[node.name](self)
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
        go_name = self._to_go_method_name(node.name)
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
        if manual_key in self.MANUAL_METHODS:
            self.MANUAL_METHODS[manual_key](self, receiver)
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

    # Manually implemented methods that need special Go code
    # Populated after method definitions below
    MANUAL_METHODS: dict[tuple[str, str], "Callable[[GoTranspiler, str], None]"] = {
        ("QuoteState", "push"): lambda t, r: GoTranspiler._emit_quotestate_push(t, r),
        ("QuoteState", "pop"): lambda t, r: GoTranspiler._emit_quotestate_pop(t, r),
        ("QuoteState", "copy"): lambda t, r: GoTranspiler._emit_quotestate_copy(t, r),
        ("QuoteState", "outer_double"): lambda t, r: GoTranspiler._emit_quotestate_outer_double(
            t, r
        ),
        # Arithmetic parser - inline left_assoc pattern
        ("Parser", "_arith_parse_logical_or"): lambda t, r: GoTranspiler._emit_arith_left_assoc(
            t, r, ["||"], "_ArithParseLogicalAnd"
        ),
        ("Parser", "_arith_parse_logical_and"): lambda t, r: GoTranspiler._emit_arith_left_assoc(
            t, r, ["&&"], "_ArithParseBitwiseOr"
        ),
        ("Parser", "_arith_parse_equality"): lambda t, r: GoTranspiler._emit_arith_left_assoc(
            t, r, ["==", "!="], "_ArithParseComparison"
        ),
        # Heredoc gathering - minimal implementation (full heredocs not yet supported)
        ("Parser", "_gather_heredoc_bodies"): lambda t, r: GoTranspiler._emit_gather_heredoc_bodies(
            t, r
        ),
        # Heredoc parsing - needs type assertion for _pending_heredocs iteration
        ("Parser", "_parse_heredoc"): lambda t, r: GoTranspiler._emit_parse_heredoc(t, r),
        # Process substitution - try/except pattern with recover
        ("Parser", "_parse_process_substitution"): lambda t,
        r: GoTranspiler._emit_parse_process_substitution(t, r),
        # Backtick substitution - complex heredoc tracking in local vars
        ("Parser", "_parse_backtick_substitution"): lambda t,
        r: GoTranspiler._emit_parse_backtick_substitution(t, r),
        # Command substitution - needs _isNilNode for typed nil check
        ("Parser", "_parse_command_substitution"): lambda t,
        r: GoTranspiler._emit_parse_command_substitution(t, r),
        # Funsub (brace command substitution) - needs _isNilNode for typed nil check
        ("Parser", "_parse_funsub"): lambda t, r: GoTranspiler._emit_parse_funsub(t, r),
    }

    @staticmethod
    def _emit_quotestate_push(t: "GoTranspiler", receiver: str):
        """Emit QuoteState.Push() body."""
        t.emit(
            f"{receiver}._Stack = append({receiver}._Stack, quoteStackEntry{{{receiver}.Single, {receiver}.Double}})"
        )
        t.emit(f"{receiver}.Single = false")
        t.emit(f"{receiver}.Double = false")

    @staticmethod
    def _emit_quotestate_pop(t: "GoTranspiler", receiver: str):
        """Emit QuoteState.Pop() body."""
        t.emit(f"if len({receiver}._Stack) > 0 {{")
        t.indent += 1
        t.emit(f"entry := {receiver}._Stack[len({receiver}._Stack)-1]")
        t.emit(f"{receiver}._Stack = {receiver}._Stack[:len({receiver}._Stack)-1]")
        t.emit(f"{receiver}.Single = entry.single")
        t.emit(f"{receiver}.Double = entry.double")
        t.indent -= 1
        t.emit("}")

    @staticmethod
    def _emit_quotestate_copy(t: "GoTranspiler", receiver: str):
        """Emit QuoteState.Copy() body."""
        t.emit("qs := &QuoteState{}")
        t.emit(f"qs.Single = {receiver}.Single")
        t.emit(f"qs.Double = {receiver}.Double")
        t.emit(f"qs._Stack = make([]quoteStackEntry, len({receiver}._Stack))")
        t.emit(f"copy(qs._Stack, {receiver}._Stack)")
        t.emit("return qs")

    @staticmethod
    def _emit_quotestate_outer_double(t: "GoTranspiler", receiver: str):
        """Emit QuoteState.OuterDouble() body."""
        t.emit(f"if len({receiver}._Stack) == 0 {{")
        t.indent += 1
        t.emit("return false")
        t.indent -= 1
        t.emit("}")
        t.emit(f"return {receiver}._Stack[len({receiver}._Stack)-1].double")

    @staticmethod
    def _emit_arith_left_assoc(t: "GoTranspiler", receiver: str, ops: list[str], next_fn: str):
        """Emit inlined left-associative binary operator parsing."""
        t.emit(f"left := {receiver}.{next_fn}()")
        t.emit("for {")
        t.indent += 1
        t.emit(f"{receiver}._ArithSkipWs()")
        t.emit("matched := false")
        for i, op in enumerate(ops):
            cond = "if" if i == 0 else "} else if"
            t.emit(f'{cond} {receiver}._ArithMatch("{op}") {{')
            t.indent += 1
            t.emit(f'{receiver}._ArithConsume("{op}")')
            t.emit(f"{receiver}._ArithSkipWs()")
            t.emit(f'left = NewArithBinaryOp("{op}", left, {receiver}.{next_fn}())')
            t.emit("matched = true")
            t.indent -= 1
        t.emit("}")
        t.emit("if !matched {")
        t.indent += 1
        t.emit("break")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit("return left")

    @staticmethod
    def _emit_gather_heredoc_bodies(t: "GoTranspiler", receiver: str):
        """Emit full _GatherHeredocBodies implementation."""
        t.emit(f"for _, heredocNode := range {receiver}._Pending_heredocs {{")
        t.indent += 1
        t.emit("heredoc := heredocNode.(*HereDoc)")
        t.emit("var contentLines []string")
        t.emit(f"lineStart := {receiver}.Pos")
        t.emit("")
        t.emit(f"for {receiver}.Pos < {receiver}.Length {{")
        t.indent += 1
        t.emit(f"lineStart = {receiver}.Pos")
        t.emit(f"line, lineEnd := {receiver}._ReadHeredocLine(heredoc.Quoted)")
        t.emit(
            f"matches, checkLine := {receiver}._LineMatchesDelimiter(line, heredoc.Delimiter, heredoc.Strip_tabs)"
        )
        t.emit("")
        t.emit("if matches {")
        t.indent += 1
        t.emit(f"if lineEnd < {receiver}.Length {{")
        t.indent += 1
        t.emit(f"{receiver}.Pos = lineEnd + 1")
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit(f"{receiver}.Pos = lineEnd")
        t.indent -= 1
        t.emit("}")
        t.emit("break")
        t.indent -= 1
        t.emit("}")
        t.emit("")
        t.emit("// Check for delimiter followed by cmdsub/procsub closer")
        t.emit("normalizedCheck := _NormalizeHeredocDelimiter(checkLine)")
        t.emit("normalizedDelim := _NormalizeHeredocDelimiter(heredoc.Delimiter)")
        t.emit("")
        t.emit("// In command substitution: line starts with delimiter")
        t.emit(
            f'if {receiver}._Eof_token == ")" && strings.HasPrefix(normalizedCheck, normalizedDelim) {{'
        )
        t.indent += 1
        t.emit("tabsStripped := len(line) - len(checkLine)")
        t.emit(f"{receiver}.Pos = lineStart + tabsStripped + len(heredoc.Delimiter)")
        t.emit("break")
        t.indent -= 1
        t.emit("}")
        t.emit("")
        t.emit("// At EOF with line starting with delimiter (process sub case)")
        t.emit(f"if lineEnd >= {receiver}.Length &&")
        t.indent += 1
        t.emit("strings.HasPrefix(normalizedCheck, normalizedDelim) &&")
        t.emit(f"{receiver}._In_process_sub {{")
        t.indent -= 1
        t.indent += 1
        t.emit("tabsStripped := len(line) - len(checkLine)")
        t.emit(f"{receiver}.Pos = lineStart + tabsStripped + len(heredoc.Delimiter)")
        t.emit("break")
        t.indent -= 1
        t.emit("}")
        t.emit("")
        t.emit("// Add line to content")
        t.emit("contentLine := line")
        t.emit("if heredoc.Strip_tabs {")
        t.indent += 1
        t.emit('contentLine = strings.TrimLeft(line, "\\t")')
        t.indent -= 1
        t.emit("}")
        t.emit("")
        t.emit(f"if lineEnd < {receiver}.Length {{")
        t.indent += 1
        t.emit('contentLines = append(contentLines, contentLine+"\\n")')
        t.emit(f"{receiver}.Pos = lineEnd + 1")
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit("// EOF - bash keeps trailing newline unless escaped")
        t.emit("addNewline := true")
        t.emit("if !heredoc.Quoted && _CountTrailingBackslashes(line)%2 == 1 {")
        t.indent += 1
        t.emit("addNewline = false")
        t.indent -= 1
        t.emit("}")
        t.emit("if addNewline {")
        t.indent += 1
        t.emit('contentLines = append(contentLines, contentLine+"\\n")')
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit("contentLines = append(contentLines, contentLine)")
        t.indent -= 1
        t.emit("}")
        t.emit(f"{receiver}.Pos = {receiver}.Length")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit("")
        t.emit('heredoc.Content = strings.Join(contentLines, "")')
        t.indent -= 1
        t.emit("}")
        t.emit(f"{receiver}._Pending_heredocs = []Node{{}}")

    @staticmethod
    def _emit_parse_heredoc(t: "GoTranspiler", receiver: str):
        """Emit _ParseHeredoc with proper type assertion for _pending_heredocs."""
        t.emit(f"startPos := {receiver}.Pos")
        t.emit(f"{receiver}._SetState(ParserStateFlags_PST_HEREDOC)")
        t.emit(f"delimiter, quoted := {receiver}._ParseHeredocDelimiter()")
        t.emit(f"for _, existing := range {receiver}._Pending_heredocs {{")
        t.indent += 1
        t.emit("h := existing.(*HereDoc)")
        t.emit("if h._Start_pos == startPos && h.Delimiter == delimiter {")
        t.indent += 1
        t.emit(f"{receiver}._ClearState(ParserStateFlags_PST_HEREDOC)")
        t.emit("return h")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit('heredoc := NewHereDoc(delimiter, "", stripTabs, quoted, fd, false)')
        t.emit("heredoc._Start_pos = startPos")
        t.emit(f"{receiver}._Pending_heredocs = append({receiver}._Pending_heredocs, heredoc)")
        t.emit(f"{receiver}._ClearState(ParserStateFlags_PST_HEREDOC)")
        t.emit("return heredoc")

    @staticmethod
    def _emit_parse_process_substitution(t: "GoTranspiler", receiver: str):
        """Emit _ParseProcessSubstitution with panic recovery for try/except pattern."""
        # Initial checks
        t.emit(f"if {receiver}.AtEnd() || !_IsRedirectChar({receiver}.Peek()) {{")
        t.indent += 1
        t.emit('return nil, ""')
        t.indent -= 1
        t.emit("}")
        t.emit("")
        t.emit(f"start := {receiver}.Pos")
        t.emit(f"direction := {receiver}.Advance()")
        t.emit("")
        t.emit(f'if {receiver}.AtEnd() || {receiver}.Peek() != "(" {{')
        t.indent += 1
        t.emit(f"{receiver}.Pos = start")
        t.emit('return nil, ""')
        t.indent -= 1
        t.emit("}")
        t.emit(f"{receiver}.Advance()")
        t.emit("")
        # Save state
        t.emit(f"saved := {receiver}._SaveParserState()")
        t.emit(f"oldInProcessSub := {receiver}._In_process_sub")
        t.emit(f"{receiver}._In_process_sub = true")
        t.emit(f"{receiver}._SetState(ParserStateFlags_PST_EOFTOKEN)")
        t.emit(f'{receiver}._Eof_token = ")"')
        t.emit("")
        # Use defer/recover for panic recovery
        t.emit("var result struct {")
        t.indent += 1
        t.emit("node Node")
        t.emit("text string")
        t.emit("ok   bool")
        t.indent -= 1
        t.emit("}")
        t.emit("")
        t.emit("func() {")
        t.indent += 1
        t.emit("defer func() {")
        t.indent += 1
        t.emit("if r := recover(); r != nil {")
        t.indent += 1
        t.emit("result.ok = false")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}()")
        t.emit("")
        t.emit(f"cmd := {receiver}.ParseList(true)")
        t.emit("if _isNilNode(cmd) {")
        t.indent += 1
        t.emit("cmd = NewEmpty()")
        t.indent -= 1
        t.emit("}")
        t.emit("")
        t.emit(f"{receiver}.SkipWhitespaceAndNewlines()")
        t.emit(f'if {receiver}.AtEnd() || {receiver}.Peek() != ")" {{')
        t.indent += 1
        t.emit('panic("not at closing paren")')
        t.indent -= 1
        t.emit("}")
        t.emit("")
        t.emit(f"{receiver}.Advance()")
        t.emit(f"text := _Substring({receiver}.Source, start, {receiver}.Pos)")
        t.emit("text = _StripLineContinuationsCommentAware(text)")
        t.emit("result.node = NewProcessSubstitution(direction, cmd)")
        t.emit("result.text = text")
        t.emit("result.ok = true")
        t.indent -= 1
        t.emit("}()")
        t.emit("")
        # Restore state
        t.emit(f"{receiver}._RestoreParserState(saved)")
        t.emit(f"{receiver}._In_process_sub = oldInProcessSub")
        t.emit("")
        t.emit("if result.ok {")
        t.indent += 1
        t.emit("return result.node, result.text")
        t.indent -= 1
        t.emit("}")
        t.emit("")
        # Error case - check if we should error or fall back
        t.emit('contentStartChar := ""')
        t.emit(f"if start+2 < {receiver}.Length {{")
        t.indent += 1
        t.emit(f"contentStartChar = string({receiver}.Source[start+2])")
        t.indent -= 1
        t.emit("}")
        t.emit("")
        t.emit(
            'if contentStartChar == " " || contentStartChar == "\\t" || contentStartChar == "\\n" {'
        )
        t.indent += 1
        t.emit('panic(NewParseError("Invalid process substitution", start, 0))')
        t.indent -= 1
        t.emit("}")
        t.emit("")
        # Fall back to matched pair scanning
        t.emit(f"{receiver}.Pos = start + 2")
        t.emit(f"{receiver}._Lexer.Pos = {receiver}.Pos")
        t.emit(f'{receiver}._Lexer._ParseMatchedPair("(", ")", 0, false)')
        t.emit(f"{receiver}.Pos = {receiver}._Lexer.Pos")
        t.emit(f"text := _Substring({receiver}.Source, start, {receiver}.Pos)")
        t.emit("text = _StripLineContinuationsCommentAware(text)")
        t.emit("return nil, text")

    @staticmethod
    def _emit_parse_backtick_substitution(t: "GoTranspiler", receiver: str):
        """Emit _ParseBacktickSubstitution with heredoc tracking."""
        # Initial check
        t.emit(f'if {receiver}.AtEnd() || {receiver}.Peek() != "`" {{')
        t.indent += 1
        t.emit('return nil, ""')
        t.indent -= 1
        t.emit("}")
        t.emit("")
        t.emit(f"start := {receiver}.Pos")
        t.emit(f"{receiver}.Advance()")
        t.emit("")
        # Initialize tracking vars
        t.emit("contentChars := []string{}")
        t.emit('textChars := []string{"`"}')
        t.emit("")
        # Heredoc tracking
        t.emit("type heredocInfo struct {")
        t.indent += 1
        t.emit("delimiter string")
        t.emit("stripTabs bool")
        t.indent -= 1
        t.emit("}")
        t.emit("pendingHeredocs := []heredocInfo{}")
        t.emit("inHeredocBody := false")
        t.emit('currentHeredocDelim := ""')
        t.emit("currentHeredocStrip := false")
        t.emit("")
        # Main loop
        t.emit(f'for !{receiver}.AtEnd() && (inHeredocBody || {receiver}.Peek() != "`") {{')
        t.indent += 1
        # Heredoc body mode
        t.emit("if inHeredocBody {")
        t.indent += 1
        t.emit(f"lineStart := {receiver}.Pos")
        t.emit("lineEnd := lineStart")
        t.emit(f'for lineEnd < {receiver}.Length && string({receiver}.Source[lineEnd]) != "\\n" {{')
        t.indent += 1
        t.emit("lineEnd++")
        t.indent -= 1
        t.emit("}")
        t.emit(f"line := _Substring({receiver}.Source, lineStart, lineEnd)")
        t.emit("checkLine := line")
        t.emit("if currentHeredocStrip {")
        t.indent += 1
        t.emit('checkLine = strings.TrimLeft(line, "\\t")')
        t.indent -= 1
        t.emit("}")
        t.emit("")
        # Found delimiter
        t.emit("if checkLine == currentHeredocDelim {")
        t.indent += 1
        t.emit("for _, ch := range line {")
        t.indent += 1
        t.emit("contentChars = append(contentChars, string(ch))")
        t.emit("textChars = append(textChars, string(ch))")
        t.indent -= 1
        t.emit("}")
        t.emit(f"{receiver}.Pos = lineEnd")
        t.emit(
            f'if {receiver}.Pos < {receiver}.Length && string({receiver}.Source[{receiver}.Pos]) == "\\n" {{'
        )
        t.indent += 1
        t.emit('contentChars = append(contentChars, "\\n")')
        t.emit('textChars = append(textChars, "\\n")')
        t.emit(f"{receiver}.Advance()")
        t.indent -= 1
        t.emit("}")
        t.emit("inHeredocBody = false")
        t.emit("if len(pendingHeredocs) > 0 {")
        t.indent += 1
        t.emit("currentHeredocDelim = pendingHeredocs[0].delimiter")
        t.emit("currentHeredocStrip = pendingHeredocs[0].stripTabs")
        t.emit("pendingHeredocs = pendingHeredocs[1:]")
        t.emit("inHeredocBody = true")
        t.indent -= 1
        t.emit("}")
        # Delimiter with trailing content
        t.emit(
            "} else if strings.HasPrefix(checkLine, currentHeredocDelim) && len(checkLine) > len(currentHeredocDelim) {"
        )
        t.indent += 1
        t.emit("tabsStripped := len(line) - len(checkLine)")
        t.emit("endPos := tabsStripped + len(currentHeredocDelim)")
        t.emit("for i := 0; i < endPos; i++ {")
        t.indent += 1
        t.emit("contentChars = append(contentChars, string(line[i]))")
        t.emit("textChars = append(textChars, string(line[i]))")
        t.indent -= 1
        t.emit("}")
        t.emit(f"{receiver}.Pos = lineStart + endPos")
        t.emit("inHeredocBody = false")
        t.emit("if len(pendingHeredocs) > 0 {")
        t.indent += 1
        t.emit("currentHeredocDelim = pendingHeredocs[0].delimiter")
        t.emit("currentHeredocStrip = pendingHeredocs[0].stripTabs")
        t.emit("pendingHeredocs = pendingHeredocs[1:]")
        t.emit("inHeredocBody = true")
        t.indent -= 1
        t.emit("}")
        # Not delimiter - add line
        t.emit("} else {")
        t.indent += 1
        t.emit("for _, ch := range line {")
        t.indent += 1
        t.emit("contentChars = append(contentChars, string(ch))")
        t.emit("textChars = append(textChars, string(ch))")
        t.indent -= 1
        t.emit("}")
        t.emit(f"{receiver}.Pos = lineEnd")
        t.emit(
            f'if {receiver}.Pos < {receiver}.Length && string({receiver}.Source[{receiver}.Pos]) == "\\n" {{'
        )
        t.indent += 1
        t.emit('contentChars = append(contentChars, "\\n")')
        t.emit('textChars = append(textChars, "\\n")')
        t.emit(f"{receiver}.Advance()")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit("continue")
        t.indent -= 1
        t.emit("}")
        t.emit("")
        # Normal character processing
        t.emit(f"c := {receiver}.Peek()")
        t.emit("")
        # Escape handling
        t.emit(f'if c == "\\\\" && {receiver}.Pos+1 < {receiver}.Length {{')
        t.indent += 1
        t.emit(f"nextC := string({receiver}.Source[{receiver}.Pos+1])")
        t.emit('if nextC == "\\n" {')
        t.indent += 1
        t.emit(f"{receiver}.Advance()")
        t.emit(f"{receiver}.Advance()")
        t.indent -= 1
        t.emit("} else if _IsEscapeCharInBacktick(nextC) {")
        t.indent += 1
        t.emit(f"{receiver}.Advance()")
        t.emit(f"escaped := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, escaped)")
        t.emit('textChars = append(textChars, "\\\\")')
        t.emit("textChars = append(textChars, escaped)")
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit(f"ch := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, ch)")
        t.emit("textChars = append(textChars, ch)")
        t.indent -= 1
        t.emit("}")
        t.emit("continue")
        t.indent -= 1
        t.emit("}")
        t.emit("")
        # Heredoc declaration
        t.emit(
            f'if c == "<" && {receiver}.Pos+1 < {receiver}.Length && string({receiver}.Source[{receiver}.Pos+1]) == "<" {{'
        )
        t.indent += 1
        # Check for here-string <<<
        t.emit(
            f'if {receiver}.Pos+2 < {receiver}.Length && string({receiver}.Source[{receiver}.Pos+2]) == "<" {{'
        )
        t.indent += 1
        t.emit(f"contentChars = append(contentChars, {receiver}.Advance())")
        t.emit('textChars = append(textChars, "<")')
        t.emit(f"contentChars = append(contentChars, {receiver}.Advance())")
        t.emit('textChars = append(textChars, "<")')
        t.emit(f"contentChars = append(contentChars, {receiver}.Advance())")
        t.emit('textChars = append(textChars, "<")')
        t.emit(f"for !{receiver}.AtEnd() && _IsWhitespaceNoNewline({receiver}.Peek()) {{")
        t.indent += 1
        t.emit(f"ch := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, ch)")
        t.emit("textChars = append(textChars, ch)")
        t.indent -= 1
        t.emit("}")
        t.emit(
            f'for !{receiver}.AtEnd() && !_IsWhitespace({receiver}.Peek()) && {receiver}.Peek() != "(" && {receiver}.Peek() != ")" {{'
        )
        t.indent += 1
        t.emit(f'if {receiver}.Peek() == "\\\\" && {receiver}.Pos+1 < {receiver}.Length {{')
        t.indent += 1
        t.emit(f"ch := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, ch)")
        t.emit("textChars = append(textChars, ch)")
        t.emit(f"ch = {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, ch)")
        t.emit("textChars = append(textChars, ch)")
        t.emit(f'}} else if {receiver}.Peek() == "\\"" || {receiver}.Peek() == "\'" {{')
        t.indent += 1
        t.emit(f"quote := {receiver}.Peek()")
        t.emit(f"ch := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, ch)")
        t.emit("textChars = append(textChars, ch)")
        t.emit(f"for !{receiver}.AtEnd() && {receiver}.Peek() != quote {{")
        t.indent += 1
        t.emit(f'if quote == "\\"" && {receiver}.Peek() == "\\\\" {{')
        t.indent += 1
        t.emit(f"ch = {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, ch)")
        t.emit("textChars = append(textChars, ch)")
        t.indent -= 1
        t.emit("}")
        t.emit(f"ch = {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, ch)")
        t.emit("textChars = append(textChars, ch)")
        t.indent -= 1
        t.emit("}")
        t.emit(f"if !{receiver}.AtEnd() {{")
        t.indent += 1
        t.emit(f"ch = {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, ch)")
        t.emit("textChars = append(textChars, ch)")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit(f"ch := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, ch)")
        t.emit("textChars = append(textChars, ch)")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit("continue")
        t.indent -= 1
        t.emit("}")
        t.emit("")
        # Regular heredoc <<
        t.emit(f"contentChars = append(contentChars, {receiver}.Advance())")
        t.emit('textChars = append(textChars, "<")')
        t.emit(f"contentChars = append(contentChars, {receiver}.Advance())")
        t.emit('textChars = append(textChars, "<")')
        t.emit("stripTabs := false")
        t.emit(f'if !{receiver}.AtEnd() && {receiver}.Peek() == "-" {{')
        t.indent += 1
        t.emit("stripTabs = true")
        t.emit(f"contentChars = append(contentChars, {receiver}.Advance())")
        t.emit('textChars = append(textChars, "-")')
        t.indent -= 1
        t.emit("}")
        # Skip whitespace
        t.emit(f"for !{receiver}.AtEnd() && _IsWhitespaceNoNewline({receiver}.Peek()) {{")
        t.indent += 1
        t.emit(f"ch := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, ch)")
        t.emit("textChars = append(textChars, ch)")
        t.indent -= 1
        t.emit("}")
        # Parse delimiter
        t.emit("delimiterChars := []string{}")
        t.emit(f"if !{receiver}.AtEnd() {{")
        t.indent += 1
        t.emit(f"ch := {receiver}.Peek()")
        t.emit("if _IsQuote(ch) {")
        t.indent += 1
        t.emit(f"quote := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, quote)")
        t.emit("textChars = append(textChars, quote)")
        t.emit(f"for !{receiver}.AtEnd() && {receiver}.Peek() != quote {{")
        t.indent += 1
        t.emit(f"dch := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, dch)")
        t.emit("textChars = append(textChars, dch)")
        t.emit("delimiterChars = append(delimiterChars, dch)")
        t.indent -= 1
        t.emit("}")
        t.emit(f"if !{receiver}.AtEnd() {{")
        t.indent += 1
        t.emit(f"closing := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, closing)")
        t.emit("textChars = append(textChars, closing)")
        t.indent -= 1
        t.emit("}")
        t.emit('} else if ch == "\\\\" {')
        t.indent += 1
        t.emit(f"esc := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, esc)")
        t.emit("textChars = append(textChars, esc)")
        t.emit(f"if !{receiver}.AtEnd() {{")
        t.indent += 1
        t.emit(f"dch := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, dch)")
        t.emit("textChars = append(textChars, dch)")
        t.emit("delimiterChars = append(delimiterChars, dch)")
        t.indent -= 1
        t.emit("}")
        t.emit(f"for !{receiver}.AtEnd() && !_IsMetachar({receiver}.Peek()) {{")
        t.indent += 1
        t.emit(f"dch := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, dch)")
        t.emit("textChars = append(textChars, dch)")
        t.emit("delimiterChars = append(delimiterChars, dch)")
        t.indent -= 1
        t.emit("}")
        t.emit("} else {")
        t.indent += 1
        t.emit(
            f'for !{receiver}.AtEnd() && !_IsMetachar({receiver}.Peek()) && {receiver}.Peek() != "`" {{'
        )
        t.indent += 1
        t.emit(f"ch := {receiver}.Peek()")
        t.emit("if _IsQuote(ch) {")
        t.indent += 1
        t.emit(f"quote := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, quote)")
        t.emit("textChars = append(textChars, quote)")
        t.emit(f"for !{receiver}.AtEnd() && {receiver}.Peek() != quote {{")
        t.indent += 1
        t.emit(f"dch := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, dch)")
        t.emit("textChars = append(textChars, dch)")
        t.emit("delimiterChars = append(delimiterChars, dch)")
        t.indent -= 1
        t.emit("}")
        t.emit(f"if !{receiver}.AtEnd() {{")
        t.indent += 1
        t.emit(f"closing := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, closing)")
        t.emit("textChars = append(textChars, closing)")
        t.indent -= 1
        t.emit("}")
        t.emit('} else if ch == "\\\\" {')
        t.indent += 1
        t.emit(f"esc := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, esc)")
        t.emit("textChars = append(textChars, esc)")
        t.emit(f"if !{receiver}.AtEnd() {{")
        t.indent += 1
        t.emit(f"dch := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, dch)")
        t.emit("textChars = append(textChars, dch)")
        t.emit("delimiterChars = append(delimiterChars, dch)")
        t.indent -= 1
        t.emit("}")
        t.emit("} else {")
        t.indent += 1
        t.emit(f"dch := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, dch)")
        t.emit("textChars = append(textChars, dch)")
        t.emit("delimiterChars = append(delimiterChars, dch)")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit('delimiter := strings.Join(delimiterChars, "")')
        t.emit('if delimiter != "" {')
        t.indent += 1
        t.emit("pendingHeredocs = append(pendingHeredocs, heredocInfo{delimiter, stripTabs})")
        t.indent -= 1
        t.emit("}")
        t.emit("continue")
        t.indent -= 1
        t.emit("}")
        t.emit("")
        # Newline - check for heredoc body mode
        t.emit('if c == "\\n" {')
        t.indent += 1
        t.emit(f"ch := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, ch)")
        t.emit("textChars = append(textChars, ch)")
        t.emit("if len(pendingHeredocs) > 0 {")
        t.indent += 1
        t.emit("currentHeredocDelim = pendingHeredocs[0].delimiter")
        t.emit("currentHeredocStrip = pendingHeredocs[0].stripTabs")
        t.emit("pendingHeredocs = pendingHeredocs[1:]")
        t.emit("inHeredocBody = true")
        t.indent -= 1
        t.emit("}")
        t.emit("continue")
        t.indent -= 1
        t.emit("}")
        t.emit("")
        # Regular character
        t.emit(f"ch := {receiver}.Advance()")
        t.emit("contentChars = append(contentChars, ch)")
        t.emit("textChars = append(textChars, ch)")
        t.indent -= 1
        t.emit("}")
        t.emit("")
        # Check for unterminated backtick
        t.emit(f"if {receiver}.AtEnd() {{")
        t.indent += 1
        t.emit('panic(NewParseError("Unterminated backtick", start, 0))')
        t.indent -= 1
        t.emit("}")
        t.emit("")
        t.emit(f"{receiver}.Advance()")
        t.emit('textChars = append(textChars, "`")')
        t.emit('text := strings.Join(textChars, "")')
        t.emit('content := strings.Join(contentChars, "")')
        t.emit("")
        # Handle heredocs whose bodies follow the closing backtick
        t.emit("if len(pendingHeredocs) > 0 {")
        t.indent += 1
        t.emit("delimiters := make([]interface{}, len(pendingHeredocs))")
        t.emit("for i, h := range pendingHeredocs {")
        t.indent += 1
        t.emit("delimiters[i] = []interface{}{h.delimiter, h.stripTabs}")
        t.indent -= 1
        t.emit("}")
        t.emit(
            f"heredocStart, heredocEnd := _FindHeredocContentEnd({receiver}.Source, {receiver}.Pos, delimiters)"
        )
        t.emit("if heredocEnd > heredocStart {")
        t.indent += 1
        t.emit(f"content = content + _Substring({receiver}.Source, heredocStart, heredocEnd)")
        t.emit(f"if {receiver}._Cmdsub_heredoc_end < 0 {{")
        t.indent += 1
        t.emit(f"{receiver}._Cmdsub_heredoc_end = heredocEnd")
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit(f"if heredocEnd > {receiver}._Cmdsub_heredoc_end {{")
        t.indent += 1
        t.emit(f"{receiver}._Cmdsub_heredoc_end = heredocEnd")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit("")
        # Parse the content as a command list
        t.emit(f"subParser := NewParser(content, false, {receiver}._Extglob)")
        t.emit("cmd := subParser.ParseList(true)")
        t.emit("if _isNilNode(cmd) {")
        t.indent += 1
        t.emit("cmd = NewEmpty()")
        t.indent -= 1
        t.emit("}")
        t.emit("")
        t.emit("return NewCommandSubstitution(cmd, false), text")

    @staticmethod
    def _emit_parse_command_substitution(t: "GoTranspiler", receiver: str):
        """Emit _ParseCommandSubstitution with _isNilNode check for typed nil."""
        # Variable declarations
        t.emit("var start int")
        t.emit("_ = start")
        t.emit("var saved *SavedParserState")
        t.emit("_ = saved")
        t.emit("var cmd Node")
        t.emit("_ = cmd")
        t.emit("var textEnd int")
        t.emit("_ = textEnd")
        t.emit("var text string")
        t.emit("_ = text")
        # Initial checks
        t.emit(f'if {receiver}.AtEnd() || {receiver}.Peek() != "$" {{')
        t.indent += 1
        t.emit('return nil, ""')
        t.indent -= 1
        t.emit("}")
        t.emit(f"start = {receiver}.Pos")
        t.emit(f"{receiver}.Advance()")
        t.emit("")
        t.emit(f'if {receiver}.AtEnd() || {receiver}.Peek() != "(" {{')
        t.indent += 1
        t.emit(f"{receiver}.Pos = start")
        t.emit('return nil, ""')
        t.indent -= 1
        t.emit("}")
        t.emit(f"{receiver}.Advance()")
        t.emit("")
        # Save state and set up for parsing
        t.emit(f"saved = {receiver}._SaveParserState()")
        t.emit(
            f"{receiver}._SetState(ParserStateFlags_PST_CMDSUBST | ParserStateFlags_PST_EOFTOKEN)"
        )
        t.emit(f'{receiver}._Eof_token = ")"')
        t.emit("")
        # Parse command list with _isNilNode check for typed nil
        t.emit(f"cmd = {receiver}.ParseList(true)")
        t.emit("if _isNilNode(cmd) {")
        t.indent += 1
        t.emit("cmd = NewEmpty()")
        t.indent -= 1
        t.emit("}")
        t.emit("")
        # Check for closing paren
        t.emit(f"{receiver}.SkipWhitespaceAndNewlines()")
        t.emit(f'if {receiver}.AtEnd() || {receiver}.Peek() != ")" {{')
        t.indent += 1
        t.emit(f"{receiver}._RestoreParserState(saved)")
        t.emit(f"{receiver}.Pos = start")
        t.emit('return nil, ""')
        t.indent -= 1
        t.emit("}")
        t.emit("")
        t.emit(f"{receiver}.Advance()")
        t.emit(f"textEnd = {receiver}.Pos")
        t.emit(f"text = _Substring({receiver}.Source, start, textEnd)")
        t.emit("")
        t.emit(f"{receiver}._RestoreParserState(saved)")
        t.emit("return NewCommandSubstitution(cmd, false), text")

    @staticmethod
    def _emit_parse_funsub(t: "GoTranspiler", receiver: str):
        """Emit _ParseFunsub with _isNilNode check for typed nil."""
        # Variable declarations
        t.emit("var saved *SavedParserState")
        t.emit("_ = saved")
        t.emit("var cmd Node")
        t.emit("_ = cmd")
        t.emit("var text string")
        t.emit("_ = text")
        # Sync parser and skip leading |
        t.emit(f"{receiver}._SyncParser()")
        t.emit(f'if !({receiver}.AtEnd()) && {receiver}.Peek() == "|" {{')
        t.indent += 1
        t.emit(f"{receiver}.Advance()")
        t.indent -= 1
        t.emit("}")
        t.emit("")
        # Save state and set up for parsing
        t.emit(f"saved = {receiver}._SaveParserState()")
        t.emit(
            f"{receiver}._SetState(ParserStateFlags_PST_CMDSUBST | ParserStateFlags_PST_EOFTOKEN)"
        )
        t.emit(f'{receiver}._Eof_token = "}}"')
        t.emit("")
        # Parse command list with _isNilNode check for typed nil
        t.emit(f"cmd = {receiver}.ParseList(true)")
        t.emit("if _isNilNode(cmd) {")
        t.indent += 1
        t.emit("cmd = NewEmpty()")
        t.indent -= 1
        t.emit("}")
        t.emit("")
        # Check for closing brace
        t.emit(f"{receiver}.SkipWhitespaceAndNewlines()")
        t.emit(f'if {receiver}.AtEnd() || {receiver}.Peek() != "}}" {{')
        t.indent += 1
        t.emit(f"{receiver}._RestoreParserState(saved)")
        t.emit('panic(NewMatchedPairError("unexpected EOF looking for `}\'", start, 0))')
        t.indent -= 1
        t.emit("}")
        t.emit("")
        t.emit(f"{receiver}.Advance()")
        t.emit(f"text = _Substring({receiver}.Source, start, {receiver}.Pos)")
        t.emit(f"{receiver}._RestoreParserState(saved)")
        t.emit(f"{receiver}._SyncLexer()")
        t.emit("return NewCommandSubstitution(cmd, true), text")

    MANUAL_FUNCTIONS: dict[str, "Callable[[GoTranspiler], None]"] = {
        "_format_heredoc_body": lambda t: GoTranspiler._emit_format_heredoc_body(t),
        "_starts_with_subshell": lambda t: GoTranspiler._emit_starts_with_subshell(t),
        "_format_cond_body": lambda t: GoTranspiler._emit_format_cond_body(t),
        "_format_redirect": lambda t: GoTranspiler._emit_format_redirect(t),
        "_find_heredoc_content_end": lambda t: GoTranspiler._emit_find_heredoc_content_end(t),
        "_format_cmdsub_node": lambda t: GoTranspiler._emit_format_cmdsub_node(t),
    }

    @staticmethod
    def _emit_format_heredoc_body(t: "GoTranspiler"):
        """Emit _FormatHeredocBody body."""
        t.emit("h := r.(*HereDoc)")
        t.emit('return "\\n" + h.Content + h.Delimiter + "\\n"')

    @staticmethod
    def _emit_starts_with_subshell(t: "GoTranspiler"):
        """Emit _StartsWithSubshell body."""
        t.emit('if node.Kind() == "subshell" {')
        t.indent += 1
        t.emit("return true")
        t.indent -= 1
        t.emit("}")
        t.emit('if node.Kind() == "list" {')
        t.indent += 1
        t.emit("list := node.(*List)")
        t.emit("for _, p := range list.Parts {")
        t.indent += 1
        t.emit('if p.Kind() != "operator" {')
        t.indent += 1
        t.emit("return _StartsWithSubshell(p)")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit("return false")
        t.indent -= 1
        t.emit("}")
        t.emit('if node.Kind() == "pipeline" {')
        t.indent += 1
        t.emit("pipeline := node.(*Pipeline)")
        t.emit("if len(pipeline.Commands) > 0 {")
        t.indent += 1
        t.emit("return _StartsWithSubshell(pipeline.Commands[0])")
        t.indent -= 1
        t.emit("}")
        t.emit("return false")
        t.indent -= 1
        t.emit("}")
        t.emit("return false")

    @staticmethod
    def _emit_format_cond_body(t: "GoTranspiler"):
        """Emit _FormatCondBody body."""
        t.emit("kind := node.Kind()")
        t.emit('if kind == "unary-test" {')
        t.indent += 1
        t.emit("ut := node.(*UnaryTest)")
        t.emit("operandVal := ut.Operand.(*Word).GetCondFormattedValue()")
        t.emit('return ut.Op + " " + operandVal')
        t.indent -= 1
        t.emit("}")
        t.emit('if kind == "binary-test" {')
        t.indent += 1
        t.emit("bt := node.(*BinaryTest)")
        t.emit("leftVal := bt.Left.(*Word).GetCondFormattedValue()")
        t.emit("rightVal := bt.Right.(*Word).GetCondFormattedValue()")
        t.emit('return leftVal + " " + bt.Op + " " + rightVal')
        t.indent -= 1
        t.emit("}")
        t.emit('if kind == "cond-and" {')
        t.indent += 1
        t.emit("ca := node.(*CondAnd)")
        t.emit('return _FormatCondBody(ca.Left) + " && " + _FormatCondBody(ca.Right)')
        t.indent -= 1
        t.emit("}")
        t.emit('if kind == "cond-or" {')
        t.indent += 1
        t.emit("co := node.(*CondOr)")
        t.emit('return _FormatCondBody(co.Left) + " || " + _FormatCondBody(co.Right)')
        t.indent -= 1
        t.emit("}")
        t.emit('if kind == "cond-not" {')
        t.indent += 1
        t.emit("cn := node.(*CondNot)")
        t.emit('return "! " + _FormatCondBody(cn.Operand)')
        t.indent -= 1
        t.emit("}")
        t.emit('if kind == "cond-paren" {')
        t.indent += 1
        t.emit("cp := node.(*CondParen)")
        t.emit('return "( " + _FormatCondBody(cp.Inner) + " )"')
        t.indent -= 1
        t.emit("}")
        t.emit('return ""')

    @staticmethod
    def _emit_format_redirect(t: "GoTranspiler"):
        """Emit _FormatRedirect body."""
        t.emit('if r.Kind() == "heredoc" {')
        t.indent += 1
        t.emit("h := r.(*HereDoc)")
        t.emit("var op string")
        t.emit("if h.Strip_tabs {")
        t.indent += 1
        t.emit('op = "<<-"')
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit('op = "<<"')
        t.indent -= 1
        t.emit("}")
        t.emit("if h.Fd > 0 {")
        t.indent += 1
        t.emit("op = strconv.Itoa(h.Fd) + op")
        t.indent -= 1
        t.emit("}")
        t.emit("var delim string")
        t.emit("if h.Quoted {")
        t.indent += 1
        t.emit('delim = "\'" + h.Delimiter + "\'"')
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit("delim = h.Delimiter")
        t.indent -= 1
        t.emit("}")
        t.emit("if heredocOpOnly {")
        t.indent += 1
        t.emit("return op + delim")
        t.indent -= 1
        t.emit("}")
        t.emit('return op + delim + "\\n" + h.Content + h.Delimiter + "\\n"')
        t.indent -= 1
        t.emit("}")
        t.emit("rd := r.(*Redirect)")
        t.emit("op := rd.Op")
        t.emit('if op == "1>" {')
        t.indent += 1
        t.emit('op = ">"')
        t.indent -= 1
        t.emit('} else if op == "0<" {')
        t.indent += 1
        t.emit('op = "<"')
        t.indent -= 1
        t.emit("}")
        t.emit("targetWord := rd.Target.(*Word)")
        t.emit("target := targetWord.Value")
        t.emit("target = targetWord._ExpandAllAnsiCQuotes(target)")
        t.emit("target = targetWord._StripLocaleStringDollars(target)")
        t.emit("target = targetWord._FormatCommandSubstitutions(target, false)")
        t.emit('if strings.HasPrefix(target, "&") {')
        t.indent += 1
        t.emit("wasInputClose := false")
        t.emit('if target == "&-" && strings.HasSuffix(op, "<") {')
        t.indent += 1
        t.emit("wasInputClose = true")
        t.emit('op = _Substring(op, 0, len(op)-1) + ">"')
        t.indent -= 1
        t.emit("}")
        t.emit("afterAmp := _Substring(target, 1, len(target))")
        t.emit(
            "isLiteralFd := afterAmp == \"-\" || (len(afterAmp) > 0 && afterAmp[0] >= '0' && afterAmp[0] <= '9')"
        )
        t.emit("if isLiteralFd {")
        t.indent += 1
        t.emit('if op == ">" || op == ">&" {')
        t.indent += 1
        t.emit("if wasInputClose {")
        t.indent += 1
        t.emit('op = "0>"')
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit('op = "1>"')
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit('} else if op == "<" || op == "<&" {')
        t.indent += 1
        t.emit('op = "0<"')
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit('if op == "1>" {')
        t.indent += 1
        t.emit('op = ">"')
        t.indent -= 1
        t.emit('} else if op == "0<" {')
        t.indent += 1
        t.emit('op = "<"')
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit("return op + target")
        t.indent -= 1
        t.emit("}")
        t.emit('if strings.HasSuffix(op, "&") {')
        t.indent += 1
        t.emit("return op + target")
        t.indent -= 1
        t.emit("}")
        t.emit("if compact {")
        t.indent += 1
        t.emit("return op + target")
        t.indent -= 1
        t.emit("}")
        t.emit('return op + " " + target')

    @staticmethod
    def _emit_find_heredoc_content_end(t: "GoTranspiler"):
        """Emit _FindHeredocContentEnd body."""
        t.emit("if len(delimiters) == 0 {")
        t.indent += 1
        t.emit("return start, start")
        t.indent -= 1
        t.emit("}")
        t.emit("pos := start")
        t.emit('for pos < len(source) && string(source[pos]) != "\\n" {')
        t.indent += 1
        t.emit("pos++")
        t.indent -= 1
        t.emit("}")
        t.emit("if pos >= len(source) {")
        t.indent += 1
        t.emit("return start, start")
        t.indent -= 1
        t.emit("}")
        t.emit("contentStart := pos")
        t.emit("pos++")
        t.emit("for _, dt := range delimiters {")
        t.indent += 1
        t.emit("delimTuple := dt.([]interface{})")
        t.emit("delimiter := delimTuple[0].(string)")
        t.emit("stripTabs := delimTuple[1].(bool)")
        t.emit("for pos < len(source) {")
        t.indent += 1
        t.emit("lineStart := pos")
        t.emit("lineEnd := pos")
        t.emit('for lineEnd < len(source) && string(source[lineEnd]) != "\\n" {')
        t.indent += 1
        t.emit("lineEnd++")
        t.indent -= 1
        t.emit("}")
        t.emit("line := _Substring(source, lineStart, lineEnd)")
        t.emit("for lineEnd < len(source) {")
        t.indent += 1
        t.emit("trailingBs := 0")
        t.emit("for j := len(line) - 1; j >= 0; j-- {")
        t.indent += 1
        t.emit('if string(line[j]) == "\\\\" {')
        t.indent += 1
        t.emit("trailingBs++")
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit("break")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit("if trailingBs%2 == 0 {")
        t.indent += 1
        t.emit("break")
        t.indent -= 1
        t.emit("}")
        t.emit("line = _Substring(line, 0, len(line)-1)")
        t.emit("lineEnd++")
        t.emit("nextLineStart := lineEnd")
        t.emit('for lineEnd < len(source) && string(source[lineEnd]) != "\\n" {')
        t.indent += 1
        t.emit("lineEnd++")
        t.indent -= 1
        t.emit("}")
        t.emit("line = line + _Substring(source, nextLineStart, lineEnd)")
        t.indent -= 1
        t.emit("}")
        t.emit("var lineStripped string")
        t.emit("if stripTabs {")
        t.indent += 1
        t.emit('lineStripped = strings.TrimLeft(line, "\\t")')
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit("lineStripped = line")
        t.indent -= 1
        t.emit("}")
        t.emit("if lineStripped == delimiter {")
        t.indent += 1
        t.emit("if lineEnd < len(source) {")
        t.indent += 1
        t.emit("pos = lineEnd + 1")
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit("pos = lineEnd")
        t.indent -= 1
        t.emit("}")
        t.emit("break")
        t.indent -= 1
        t.emit("}")
        t.emit(
            "if strings.HasPrefix(lineStripped, delimiter) && len(lineStripped) > len(delimiter) {"
        )
        t.indent += 1
        t.emit("tabsStripped := len(line) - len(lineStripped)")
        t.emit("pos = lineStart + tabsStripped + len(delimiter)")
        t.emit("break")
        t.indent -= 1
        t.emit("}")
        t.emit("if lineEnd < len(source) {")
        t.indent += 1
        t.emit("pos = lineEnd + 1")
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit("pos = lineEnd")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit("return contentStart, pos")

    @staticmethod
    def _emit_format_cmdsub_node(t: "GoTranspiler"):
        """Emit _FormatCmdsubNode body - large switch on node.Kind()."""
        t.emit("if _isNilNode(node) {")
        t.indent += 1
        t.emit('return ""')
        t.indent -= 1
        t.emit("}")
        t.emit('sp := _RepeatStr(" ", indent)')
        t.emit('innerSp := _RepeatStr(" ", indent+4)')
        t.emit("switch node.Kind() {")
        # case "empty"
        t.emit('case "empty":')
        t.indent += 1
        t.emit('return ""')
        t.indent -= 1
        # case "command"
        t.emit('case "command":')
        t.indent += 1
        t.emit("cmd := node.(*Command)")
        t.emit("parts := []string{}")
        t.emit("for _, wn := range cmd.Words {")
        t.indent += 1
        t.emit("w := wn.(*Word)")
        t.emit("val := w._ExpandAllAnsiCQuotes(w.Value)")
        t.emit("val = w._StripLocaleStringDollars(val)")
        t.emit("val = w._NormalizeArrayWhitespace(val)")
        t.emit("val = w._FormatCommandSubstitutions(val, false)")
        t.emit("parts = append(parts, val)")
        t.indent -= 1
        t.emit("}")
        t.emit("heredocs := []Node{}")
        t.emit("for _, r := range cmd.Redirects {")
        t.indent += 1
        t.emit('if r.Kind() == "heredoc" {')
        t.indent += 1
        t.emit("heredocs = append(heredocs, r)")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit("for _, r := range cmd.Redirects {")
        t.indent += 1
        t.emit("parts = append(parts, _FormatRedirect(r, compactRedirects, true))")
        t.indent -= 1
        t.emit("}")
        t.emit("var result string")
        t.emit("if compactRedirects && len(cmd.Words) > 0 && len(cmd.Redirects) > 0 {")
        t.indent += 1
        t.emit('wordParts := strings.Join(parts[:len(cmd.Words)], " ")')
        t.emit('redirectParts := strings.Join(parts[len(cmd.Words):], "")')
        t.emit("result = wordParts + redirectParts")
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit('result = strings.Join(parts, " ")')
        t.indent -= 1
        t.emit("}")
        t.emit("for _, h := range heredocs {")
        t.indent += 1
        t.emit("result = result + _FormatHeredocBody(h)")
        t.indent -= 1
        t.emit("}")
        t.emit("return result")
        t.indent -= 1
        # case "pipeline"
        t.emit('case "pipeline":')
        t.indent += 1
        t.emit("pipeline := node.(*Pipeline)")
        t.emit("type cmdPair struct {")
        t.indent += 1
        t.emit("cmd Node")
        t.emit("needsRedirect bool")
        t.indent -= 1
        t.emit("}")
        t.emit("cmds := []cmdPair{}")
        t.emit("i := 0")
        t.emit("for i < len(pipeline.Commands) {")
        t.indent += 1
        t.emit("c := pipeline.Commands[i]")
        t.emit('if c.Kind() == "pipe-both" {')
        t.indent += 1
        t.emit("i++")
        t.emit("continue")
        t.indent -= 1
        t.emit("}")
        t.emit(
            'needsRedirect := i+1 < len(pipeline.Commands) && pipeline.Commands[i+1].Kind() == "pipe-both"'
        )
        t.emit("cmds = append(cmds, cmdPair{c, needsRedirect})")
        t.emit("i++")
        t.indent -= 1
        t.emit("}")
        t.emit("resultParts := []string{}")
        t.emit("for idx, pair := range cmds {")
        t.indent += 1
        t.emit(
            "formatted := _FormatCmdsubNode(pair.cmd, indent, inProcsub, false, procsubFirst && idx == 0)"
        )
        t.emit("isLast := idx == len(cmds)-1")
        t.emit("hasHeredoc := false")
        t.emit('if pair.cmd.Kind() == "command" {')
        t.indent += 1
        t.emit("c := pair.cmd.(*Command)")
        t.emit("for _, r := range c.Redirects {")
        t.indent += 1
        t.emit('if r.Kind() == "heredoc" {')
        t.indent += 1
        t.emit("hasHeredoc = true")
        t.emit("break")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit("if pair.needsRedirect {")
        t.indent += 1
        t.emit("if hasHeredoc {")
        t.indent += 1
        t.emit('firstNl := strings.Index(formatted, "\\n")')
        t.emit("if firstNl != -1 {")
        t.indent += 1
        t.emit(
            'formatted = _Substring(formatted, 0, firstNl) + " 2>&1" + _Substring(formatted, firstNl, len(formatted))'
        )
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit('formatted = formatted + " 2>&1"')
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit('formatted = formatted + " 2>&1"')
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit("if !isLast && hasHeredoc {")
        t.indent += 1
        t.emit('firstNl := strings.Index(formatted, "\\n")')
        t.emit("if firstNl != -1 {")
        t.indent += 1
        t.emit(
            'formatted = _Substring(formatted, 0, firstNl) + " |" + _Substring(formatted, firstNl, len(formatted))'
        )
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit("resultParts = append(resultParts, formatted)")
        t.indent -= 1
        t.emit("}")
        t.emit('compactPipe := inProcsub && len(cmds) > 0 && cmds[0].cmd.Kind() == "subshell"')
        t.emit('result := ""')
        t.emit("for idx, part := range resultParts {")
        t.indent += 1
        t.emit("if idx > 0 {")
        t.indent += 1
        t.emit('if strings.HasSuffix(result, "\\n") {')
        t.indent += 1
        t.emit('result = result + "  " + part')
        t.indent -= 1
        t.emit("} else if compactPipe {")
        t.indent += 1
        t.emit('result = result + "|" + part')
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit('result = result + " | " + part')
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit("result = part")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit("return result")
        t.indent -= 1
        # case "list"
        t.emit('case "list":')
        t.indent += 1
        t.emit("list := node.(*List)")
        t.emit("hasHeredoc := false")
        t.emit("for _, p := range list.Parts {")
        t.indent += 1
        t.emit('if p.Kind() == "command" {')
        t.indent += 1
        t.emit("c := p.(*Command)")
        t.emit("for _, r := range c.Redirects {")
        t.indent += 1
        t.emit('if r.Kind() == "heredoc" {')
        t.indent += 1
        t.emit("hasHeredoc = true")
        t.emit("break")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit('} else if p.Kind() == "pipeline" {')
        t.indent += 1
        t.emit("pl := p.(*Pipeline)")
        t.emit("for _, c := range pl.Commands {")
        t.indent += 1
        t.emit('if c.Kind() == "command" {')
        t.indent += 1
        t.emit("cmd := c.(*Command)")
        t.emit("for _, r := range cmd.Redirects {")
        t.indent += 1
        t.emit('if r.Kind() == "heredoc" {')
        t.indent += 1
        t.emit("hasHeredoc = true")
        t.emit("break")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit("if hasHeredoc {")
        t.indent += 1
        t.emit("break")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit("resultList := []string{}")
        t.emit("skippedSemi := false")
        t.emit("cmdCount := 0")
        t.emit("for _, p := range list.Parts {")
        t.indent += 1
        t.emit('if p.Kind() == "operator" {')
        t.indent += 1
        t.emit("op := p.(*Operator)")
        t.emit('if op.Op == ";" {')
        t.indent += 1
        t.emit(
            'if len(resultList) > 0 && strings.HasSuffix(resultList[len(resultList)-1], "\\n") {'
        )
        t.indent += 1
        t.emit("skippedSemi = true")
        t.emit("continue")
        t.indent -= 1
        t.emit("}")
        t.emit(
            'if len(resultList) >= 3 && resultList[len(resultList)-2] == "\\n" && strings.HasSuffix(resultList[len(resultList)-3], "\\n") {'
        )
        t.indent += 1
        t.emit("skippedSemi = true")
        t.emit("continue")
        t.indent -= 1
        t.emit("}")
        t.emit('resultList = append(resultList, ";")')
        t.emit("skippedSemi = false")
        t.indent -= 1
        t.emit('} else if op.Op == "\\n" {')
        t.indent += 1
        t.emit('if len(resultList) > 0 && resultList[len(resultList)-1] == ";" {')
        t.indent += 1
        t.emit("skippedSemi = false")
        t.emit("continue")
        t.indent -= 1
        t.emit("}")
        t.emit(
            'if len(resultList) > 0 && strings.HasSuffix(resultList[len(resultList)-1], "\\n") {'
        )
        t.indent += 1
        t.emit("if skippedSemi {")
        t.indent += 1
        t.emit('resultList = append(resultList, " ")')
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit('resultList = append(resultList, "\\n")')
        t.indent -= 1
        t.emit("}")
        t.emit("skippedSemi = false")
        t.emit("continue")
        t.indent -= 1
        t.emit("}")
        t.emit('resultList = append(resultList, "\\n")')
        t.emit("skippedSemi = false")
        t.indent -= 1
        t.emit('} else if op.Op == "&" {')
        t.indent += 1
        t.emit(
            'if len(resultList) > 0 && strings.Contains(resultList[len(resultList)-1], "<<") && strings.Contains(resultList[len(resultList)-1], "\\n") {'
        )
        t.indent += 1
        t.emit("last := resultList[len(resultList)-1]")
        t.emit('if strings.Contains(last, " |") || strings.HasPrefix(last, "|") {')
        t.indent += 1
        t.emit('resultList[len(resultList)-1] = last + " &"')
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit('firstNl := strings.Index(last, "\\n")')
        t.emit(
            'resultList[len(resultList)-1] = _Substring(last, 0, firstNl) + " &" + _Substring(last, firstNl, len(last))'
        )
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit('resultList = append(resultList, " &")')
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit(
            'if len(resultList) > 0 && strings.Contains(resultList[len(resultList)-1], "<<") && strings.Contains(resultList[len(resultList)-1], "\\n") {'
        )
        t.indent += 1
        t.emit("last := resultList[len(resultList)-1]")
        t.emit('firstNl := strings.Index(last, "\\n")')
        t.emit(
            'resultList[len(resultList)-1] = _Substring(last, 0, firstNl) + " " + op.Op + " " + _Substring(last, firstNl, len(last))'
        )
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit('resultList = append(resultList, " "+op.Op)')
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit(
            'if len(resultList) > 0 && !strings.HasSuffix(resultList[len(resultList)-1], " ") && !strings.HasSuffix(resultList[len(resultList)-1], "\\n") {'
        )
        t.indent += 1
        t.emit('resultList = append(resultList, " ")')
        t.indent -= 1
        t.emit("}")
        t.emit(
            "formattedCmd := _FormatCmdsubNode(p, indent, inProcsub, compactRedirects, procsubFirst && cmdCount == 0)"
        )
        t.emit("if len(resultList) > 0 {")
        t.indent += 1
        t.emit("last := resultList[len(resultList)-1]")
        t.emit('if strings.Contains(last, " || \\n") || strings.Contains(last, " && \\n") {')
        t.indent += 1
        t.emit('formattedCmd = " " + formattedCmd')
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit("if skippedSemi {")
        t.indent += 1
        t.emit('formattedCmd = " " + formattedCmd')
        t.emit("skippedSemi = false")
        t.indent -= 1
        t.emit("}")
        t.emit("resultList = append(resultList, formattedCmd)")
        t.emit("cmdCount++")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit('s := strings.Join(resultList, "")')
        t.emit('if strings.Contains(s, " &\\n") && strings.HasSuffix(s, "\\n") {')
        t.indent += 1
        t.emit('return s + " "')
        t.indent -= 1
        t.emit("}")
        t.emit('for strings.HasSuffix(s, ";") {')
        t.indent += 1
        t.emit("s = _Substring(s, 0, len(s)-1)")
        t.indent -= 1
        t.emit("}")
        t.emit("if !hasHeredoc {")
        t.indent += 1
        t.emit('for strings.HasSuffix(s, "\\n") {')
        t.indent += 1
        t.emit("s = _Substring(s, 0, len(s)-1)")
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit("return s")
        t.indent -= 1
        # case "if"
        t.emit('case "if":')
        t.indent += 1
        t.emit("ifNode := node.(*If)")
        t.emit("cond := _FormatCmdsubNode(ifNode.Condition, indent, false, false, false)")
        t.emit("thenBody := _FormatCmdsubNode(ifNode.Then_body, indent+4, false, false, false)")
        t.emit('result := "if " + cond + "; then\\n" + innerSp + thenBody + ";"')
        t.emit("if ifNode.Else_body != nil {")
        t.indent += 1
        t.emit("elseBody := _FormatCmdsubNode(ifNode.Else_body, indent+4, false, false, false)")
        t.emit('result = result + "\\n" + sp + "else\\n" + innerSp + elseBody + ";"')
        t.indent -= 1
        t.emit("}")
        t.emit('result = result + "\\n" + sp + "fi"')
        t.emit("return result")
        t.indent -= 1
        # case "while"
        t.emit('case "while":')
        t.indent += 1
        t.emit("whileNode := node.(*While)")
        t.emit("cond := _FormatCmdsubNode(whileNode.Condition, indent, false, false, false)")
        t.emit("body := _FormatCmdsubNode(whileNode.Body, indent+4, false, false, false)")
        t.emit('result := "while " + cond + "; do\\n" + innerSp + body + ";\\n" + sp + "done"')
        t.emit("for _, r := range whileNode.Redirects {")
        t.indent += 1
        t.emit('result = result + " " + _FormatRedirect(r, false, false)')
        t.indent -= 1
        t.emit("}")
        t.emit("return result")
        t.indent -= 1
        # case "until"
        t.emit('case "until":')
        t.indent += 1
        t.emit("untilNode := node.(*Until)")
        t.emit("cond := _FormatCmdsubNode(untilNode.Condition, indent, false, false, false)")
        t.emit("body := _FormatCmdsubNode(untilNode.Body, indent+4, false, false, false)")
        t.emit('result := "until " + cond + "; do\\n" + innerSp + body + ";\\n" + sp + "done"')
        t.emit("for _, r := range untilNode.Redirects {")
        t.indent += 1
        t.emit('result = result + " " + _FormatRedirect(r, false, false)')
        t.indent -= 1
        t.emit("}")
        t.emit("return result")
        t.indent -= 1
        # case "for"
        t.emit('case "for":')
        t.indent += 1
        t.emit("forNode := node.(*For)")
        t.emit("varName := forNode.Var")
        t.emit("body := _FormatCmdsubNode(forNode.Body, indent+4, false, false, false)")
        t.emit("var result string")
        t.emit("if forNode.Words != nil {")
        t.indent += 1
        t.emit("wordVals := []string{}")
        t.emit("for _, wn := range forNode.Words {")
        t.indent += 1
        t.emit("wordVals = append(wordVals, wn.(*Word).Value)")
        t.indent -= 1
        t.emit("}")
        t.emit('words := strings.Join(wordVals, " ")')
        t.emit('if words != "" {')
        t.indent += 1
        t.emit(
            'result = "for " + varName + " in " + words + ";\\n" + sp + "do\\n" + innerSp + body + ";\\n" + sp + "done"'
        )
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit(
            'result = "for " + varName + " in ;\\n" + sp + "do\\n" + innerSp + body + ";\\n" + sp + "done"'
        )
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit(
            'result = "for " + varName + " in \\"$@\\";\\n" + sp + "do\\n" + innerSp + body + ";\\n" + sp + "done"'
        )
        t.indent -= 1
        t.emit("}")
        t.emit("for _, r := range forNode.Redirects {")
        t.indent += 1
        t.emit('result = result + " " + _FormatRedirect(r, false, false)')
        t.indent -= 1
        t.emit("}")
        t.emit("return result")
        t.indent -= 1
        # case "for-arith"
        t.emit('case "for-arith":')
        t.indent += 1
        t.emit("forArith := node.(*ForArith)")
        t.emit("body := _FormatCmdsubNode(forArith.Body, indent+4, false, false, false)")
        t.emit(
            'result := "for ((" + forArith.Init + "; " + forArith.Cond + "; " + forArith.Incr + "))\\ndo\\n" + innerSp + body + ";\\n" + sp + "done"'
        )
        t.emit("for _, r := range forArith.Redirects {")
        t.indent += 1
        t.emit('result = result + " " + _FormatRedirect(r, false, false)')
        t.indent -= 1
        t.emit("}")
        t.emit("return result")
        t.indent -= 1
        # case "case"
        t.emit('case "case":')
        t.indent += 1
        t.emit("caseNode := node.(*Case)")
        t.emit("word := caseNode.Word.(*Word).Value")
        t.emit("patterns := []string{}")
        t.emit("for i, pn := range caseNode.Patterns {")
        t.indent += 1
        t.emit("p := pn.(*CasePattern)")
        t.emit('pat := strings.ReplaceAll(p.Pattern, "|", " | ")')
        t.emit("var body string")
        t.emit("if p.Body != nil {")
        t.indent += 1
        t.emit("body = _FormatCmdsubNode(p.Body, indent+8, false, false, false)")
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit('body = ""')
        t.indent -= 1
        t.emit("}")
        t.emit("term := p.Terminator")
        t.emit('patIndent := _RepeatStr(" ", indent+8)')
        t.emit('termIndent := _RepeatStr(" ", indent+4)')
        t.emit("var bodyPart string")
        t.emit('if body != "" {')
        t.indent += 1
        t.emit('bodyPart = patIndent + body + "\\n"')
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit('bodyPart = "\\n"')
        t.indent -= 1
        t.emit("}")
        t.emit("if i == 0 {")
        t.indent += 1
        t.emit('patterns = append(patterns, " "+pat+")\\n"+bodyPart+termIndent+term)')
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit('patterns = append(patterns, pat+")\\n"+bodyPart+termIndent+term)')
        t.indent -= 1
        t.emit("}")
        t.indent -= 1
        t.emit("}")
        t.emit('patternStr := strings.Join(patterns, "\\n"+_RepeatStr(" ", indent+4))')
        t.emit('redirects := ""')
        t.emit("if len(caseNode.Redirects) > 0 {")
        t.indent += 1
        t.emit("redirectParts := []string{}")
        t.emit("for _, r := range caseNode.Redirects {")
        t.indent += 1
        t.emit("redirectParts = append(redirectParts, _FormatRedirect(r, false, false))")
        t.indent -= 1
        t.emit("}")
        t.emit('redirects = " " + strings.Join(redirectParts, " ")')
        t.indent -= 1
        t.emit("}")
        t.emit('return "case " + word + " in" + patternStr + "\\n" + sp + "esac" + redirects')
        t.indent -= 1
        # case "function"
        t.emit('case "function":')
        t.indent += 1
        t.emit("funcNode := node.(*Function)")
        t.emit("name := funcNode.Name")
        t.emit("var innerBody Node")
        t.emit('if funcNode.Body.Kind() == "brace-group" {')
        t.indent += 1
        t.emit("bg := funcNode.Body.(*BraceGroup)")
        t.emit("innerBody = bg.Body")
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit("innerBody = funcNode.Body")
        t.indent -= 1
        t.emit("}")
        t.emit("body := _FormatCmdsubNode(innerBody, indent+4, false, false, false)")
        t.emit('body = strings.TrimSuffix(body, ";")')
        t.emit('return "function " + name + " () \\n{ \\n" + innerSp + body + "\\n}"')
        t.indent -= 1
        # case "subshell"
        t.emit('case "subshell":')
        t.indent += 1
        t.emit("subshell := node.(*Subshell)")
        t.emit(
            "body := _FormatCmdsubNode(subshell.Body, indent, inProcsub, compactRedirects, false)"
        )
        t.emit('redirects := ""')
        t.emit("if len(subshell.Redirects) > 0 {")
        t.indent += 1
        t.emit("redirectParts := []string{}")
        t.emit("for _, r := range subshell.Redirects {")
        t.indent += 1
        t.emit("redirectParts = append(redirectParts, _FormatRedirect(r, false, false))")
        t.indent -= 1
        t.emit("}")
        t.emit('redirects = strings.Join(redirectParts, " ")')
        t.indent -= 1
        t.emit("}")
        t.emit("if procsubFirst {")
        t.indent += 1
        t.emit('if redirects != "" {')
        t.indent += 1
        t.emit('return "(" + body + ") " + redirects')
        t.indent -= 1
        t.emit("}")
        t.emit('return "(" + body + ")"')
        t.indent -= 1
        t.emit("}")
        t.emit('if redirects != "" {')
        t.indent += 1
        t.emit('return "( " + body + " ) " + redirects')
        t.indent -= 1
        t.emit("}")
        t.emit('return "( " + body + " )"')
        t.indent -= 1
        # case "brace-group"
        t.emit('case "brace-group":')
        t.indent += 1
        t.emit("bg := node.(*BraceGroup)")
        t.emit("body := _FormatCmdsubNode(bg.Body, indent, false, false, false)")
        t.emit('body = strings.TrimSuffix(body, ";")')
        t.emit("var terminator string")
        t.emit('if strings.HasSuffix(body, " &") {')
        t.indent += 1
        t.emit('terminator = " }"')
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit('terminator = "; }"')
        t.indent -= 1
        t.emit("}")
        t.emit('redirects := ""')
        t.emit("if len(bg.Redirects) > 0 {")
        t.indent += 1
        t.emit("redirectParts := []string{}")
        t.emit("for _, r := range bg.Redirects {")
        t.indent += 1
        t.emit("redirectParts = append(redirectParts, _FormatRedirect(r, false, false))")
        t.indent -= 1
        t.emit("}")
        t.emit('redirects = strings.Join(redirectParts, " ")')
        t.indent -= 1
        t.emit("}")
        t.emit('if redirects != "" {')
        t.indent += 1
        t.emit('return "{ " + body + terminator + " " + redirects')
        t.indent -= 1
        t.emit("}")
        t.emit('return "{ " + body + terminator')
        t.indent -= 1
        # case "arith-cmd"
        t.emit('case "arith-cmd":')
        t.indent += 1
        t.emit("arith := node.(*ArithmeticCommand)")
        t.emit('return "((" + arith.Raw_content + "))"')
        t.indent -= 1
        # case "cond-expr"
        t.emit('case "cond-expr":')
        t.indent += 1
        t.emit("condExpr := node.(*ConditionalExpr)")
        t.emit("body := _FormatCondBody(condExpr.Body.(Node))")
        t.emit('return "[[ " + body + " ]]"')
        t.indent -= 1
        # case "negation"
        t.emit('case "negation":')
        t.indent += 1
        t.emit("neg := node.(*Negation)")
        t.emit("if neg.Pipeline != nil {")
        t.indent += 1
        t.emit('return "! " + _FormatCmdsubNode(neg.Pipeline, indent, false, false, false)')
        t.indent -= 1
        t.emit("}")
        t.emit('return "! "')
        t.indent -= 1
        # case "time"
        t.emit('case "time":')
        t.indent += 1
        t.emit("timeNode := node.(*Time)")
        t.emit("var prefix string")
        t.emit("if timeNode.Posix {")
        t.indent += 1
        t.emit('prefix = "time -p "')
        t.indent -= 1
        t.emit("} else {")
        t.indent += 1
        t.emit('prefix = "time "')
        t.indent -= 1
        t.emit("}")
        t.emit("if timeNode.Pipeline != nil {")
        t.indent += 1
        t.emit("return prefix + _FormatCmdsubNode(timeNode.Pipeline, indent, false, false, false)")
        t.indent -= 1
        t.emit("}")
        t.emit("return prefix")
        t.indent -= 1
        # default
        t.emit("}")
        t.emit('return ""')

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
            self.declared_vars.add(self._to_go_param_name(p.name))
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
                go_name = self._to_go_param_name(p.name)
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

    # ========== Scope-Aware Variable Declaration ==========

    def _new_scope(self, parent: int) -> int:
        """Create a new scope as a child of parent."""
        scope_id = self.next_scope_id
        self.next_scope_id += 1
        parent_depth = self.scope_tree[parent].depth if parent in self.scope_tree else -1
        self.scope_tree[scope_id] = ScopeInfo(scope_id, parent, parent_depth + 1)
        return scope_id

    def _is_ancestor(self, ancestor: int, descendant: int) -> bool:
        """True if ancestor is a proper ancestor of descendant."""
        current = self.scope_tree[descendant].parent
        while current is not None:
            if current == ancestor:
                return True
            current = self.scope_tree[current].parent
        return False

    def _is_ancestor_or_equal(self, ancestor: int, descendant: int) -> bool:
        """True if ancestor is an ancestor of or equal to descendant."""
        return ancestor == descendant or self._is_ancestor(ancestor, descendant)

    def _compute_lca(self, scope_ids: set[int]) -> int:
        """Compute lowest common ancestor of a set of scopes."""
        if len(scope_ids) == 1:
            return next(iter(scope_ids))

        def ancestors(s: int) -> set[int]:
            result = {s}
            current = self.scope_tree[s].parent
            while current is not None:
                result.add(current)
                current = self.scope_tree[current].parent
            return result

        common = ancestors(next(iter(scope_ids)))
        for s in scope_ids:
            common &= ancestors(s)
        # Return deepest common ancestor
        return max(common, key=lambda s: self.scope_tree[s].depth)

    def _needs_hoisting(self, var_info: VarInfo) -> tuple[bool, int | None]:
        """Determine if a variable needs hoisting and to which scope."""
        if not var_info.assign_scopes:
            return (False, None)
        all_scopes = var_info.assign_scopes | var_info.read_scopes
        if not all_scopes:
            return (False, None)
        lca = self._compute_lca(all_scopes)
        # Case 1: Assignments in sibling/divergent branches (e.g., if/else)
        # Must hoist if LCA is not one of the assignment scopes
        if lca not in var_info.assign_scopes:
            return (True, lca)
        # Case 2: Assignment in inner scope, read in outer scope
        for assign_scope in var_info.assign_scopes:
            for read_scope in var_info.read_scopes:
                if not self._is_ancestor_or_equal(assign_scope, read_scope):
                    return (True, lca)
        # Case 3: Multiple assignments where inner would shadow outer
        if len(var_info.assign_scopes) > 1:
            min_scope = min(var_info.assign_scopes, key=lambda s: self.scope_tree[s].depth)
            for scope in var_info.assign_scopes:
                if scope != min_scope and not self._is_ancestor(min_scope, scope):
                    return (True, lca)
        return (False, None)

    def _record_var_assign(self, var: str, scope_id: int, value: ast.expr | None):
        """Record a variable assignment at a scope."""
        if var not in self.var_usage:
            self.var_usage[var] = VarInfo(var, "")
        self.var_usage[var].assign_scopes.add(scope_id)
        # Infer type from first assignment
        if not self.var_usage[var].go_type and value:
            self.var_usage[var].first_value = value

    def _record_var_read(self, var: str, scope_id: int):
        """Record a variable read at a scope."""
        if var not in self.var_usage:
            self.var_usage[var] = VarInfo(var, "")
        self.var_usage[var].read_scopes.add(scope_id)

    def _collect_var_scopes(self, stmts: list[ast.stmt], scope_id: int):
        """Collect variable assignment/read scopes recursively."""
        for stmt in stmts:
            # Store scope mapping for emission phase
            self.scope_id_map[id(stmt)] = scope_id
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        # For tuple-returning function calls, collect synthetic vars
                        if isinstance(stmt.value, ast.Call):
                            ret_info = self._get_return_type_info(stmt.value)
                            if ret_info and len(ret_info) > 1:
                                var_name = self._to_go_var(target.id)
                                for i, elem_type in enumerate(ret_info):
                                    synth_name = f"{var_name}{i}"
                                    self._record_var_assign(synth_name, scope_id, None)
                                    self.var_types[synth_name] = elem_type
                                continue
                        var_name = self._to_go_var(target.id)
                        self._record_var_assign(var_name, scope_id, stmt.value)
                        # Infer type while we have context
                        expr_type = self._infer_type_from_expr(stmt.value)
                        if expr_type and expr_type not in ("interface{}", "[]interface{}"):
                            if var_name not in self.var_types or self.var_types[var_name] in (
                                "interface{}",
                                "[]interface{}",
                            ):
                                self.var_types[var_name] = expr_type
                    # Tuple targets use := (handled separately)
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                var_name = self._to_go_var(stmt.target.id)
                self._record_var_assign(var_name, scope_id, stmt.value)
            elif isinstance(stmt, ast.If):
                # Check for isinstance pattern to narrow type during collection
                isinstance_info = self._detect_isinstance_if(stmt.test)
                then_scope = self._new_scope(parent=scope_id)
                if isinstance_info:
                    var_py, type_name = isinstance_info
                    var_go = self._to_go_var(var_py)
                    old_type = self.var_types.get(var_go)
                    self.var_types[var_go] = f"*{type_name}"
                    self._collect_var_scopes(stmt.body, then_scope)
                    if old_type is not None:
                        self.var_types[var_go] = old_type
                    else:
                        self.var_types.pop(var_go, None)
                else:
                    self._collect_var_scopes(stmt.body, then_scope)
                if stmt.orelse:
                    else_scope = self._new_scope(parent=scope_id)
                    self._collect_var_scopes(stmt.orelse, else_scope)
            elif isinstance(stmt, ast.While):
                body_scope = self._new_scope(parent=scope_id)
                self._collect_var_scopes(stmt.body, body_scope)
            elif isinstance(stmt, ast.For):
                # Loop var handled by range syntax, just recurse
                body_scope = self._new_scope(parent=scope_id)
                self._collect_var_scopes(stmt.body, body_scope)
            elif isinstance(stmt, ast.With):
                # Collect with-item variables
                for item in stmt.items:
                    if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                        var_name = self._to_go_var(item.optional_vars.id)
                        self._record_var_assign(var_name, scope_id, None)
                body_scope = self._new_scope(parent=scope_id)
                self._collect_var_scopes(stmt.body, body_scope)
            elif isinstance(stmt, ast.Try):
                body_scope = self._new_scope(parent=scope_id)
                self._collect_var_scopes(stmt.body, body_scope)
                # Track exception handler variable names to exclude from read collection
                # (Go uses recover() pattern, not exception variables)
                except_vars: set[str] = set()
                for handler in stmt.handlers:
                    handler_scope = self._new_scope(parent=scope_id)
                    if handler.name:
                        var_name = self._to_go_var(handler.name)
                        except_vars.add(var_name)
                        # Don't record the exception variable - Go uses recover() pattern
                    self._collect_var_scopes(handler.body, handler_scope)
                # Remove exception vars from read tracking (they become 'r' in Go)
                for var in except_vars:
                    if var in self.var_usage:
                        self.var_usage[var].read_scopes.clear()
                        self.var_usage[var].assign_scopes.clear()
                if stmt.orelse:
                    else_scope = self._new_scope(parent=scope_id)
                    self._collect_var_scopes(stmt.orelse, else_scope)
                if stmt.finalbody:
                    finally_scope = self._new_scope(parent=scope_id)
                    self._collect_var_scopes(stmt.finalbody, finally_scope)
            # Collect reads from all expressions in this statement
            self._collect_reads_in_scope(stmt, scope_id)

    def _collect_reads_in_scope(self, node: ast.AST, scope_id: int):
        """Collect variable reads from any AST node."""
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            var_name = self._to_go_var(node.id)
            self._record_var_read(var_name, scope_id)
        # Handle tuple element access: result[0] -> result0
        elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int):
                var_name = self._to_go_var(node.value.id)
                self._record_var_read(f"{var_name}{node.slice.value}", scope_id)
        for child in ast.iter_child_nodes(node):
            self._collect_reads_in_scope(child, scope_id)

    def _compute_hoisting(self):
        """Determine which vars need hoisting vs inline :="""
        # Collect all reads first to filter unused vars
        reads: set[str] = set()
        for var, info in self.var_usage.items():
            if info.read_scopes:
                reads.add(var)
        # Collect append types and nullable vars for type inference
        # (These require the full statement list, so we reuse existing methods)
        for var, info in self.var_usage.items():
            if var not in reads:
                continue  # Skip unused vars
            needs_hoist, hoist_scope = self._needs_hoisting(info)
            if needs_hoist and hoist_scope is not None:
                self.hoisted_vars[var] = hoist_scope

    def _exclude_assign_check_return_vars(self, stmts: list[ast.stmt]):
        """Remove vars from hoisting that are only used in assign-check-return patterns."""
        consumed_vars: set[str] = set()
        self._scan_assign_check_return_vars(stmts, consumed_vars)
        for var in consumed_vars:
            if var in self.hoisted_vars:
                del self.hoisted_vars[var]
            if var in self.var_usage:
                del self.var_usage[var]
            # Also clear var_types so pattern detection works during emission
            if var in self.var_types:
                del self.var_types[var]

    def _scan_assign_check_return_vars(self, stmts: list[ast.stmt], consumed: set[str]):
        """Recursively scan for vars consumed by assign-check-return patterns."""
        i = 0
        while i < len(stmts):
            stmt = stmts[i]
            # Check for the pattern: result = self.method(); if result: return result
            # Use a looser check that doesn't require the var type to be "Node"
            match = self._detect_assign_check_return_loose(stmts, i)
            if match:
                go_var = match
                consumed.add(go_var)
                i += 2  # Skip both statements
                continue
            # Recurse into nested blocks
            if isinstance(stmt, ast.If):
                self._scan_assign_check_return_vars(stmt.body, consumed)
                if stmt.orelse:
                    self._scan_assign_check_return_vars(stmt.orelse, consumed)
            elif isinstance(stmt, ast.While):
                self._scan_assign_check_return_vars(stmt.body, consumed)
            elif isinstance(stmt, ast.For):
                self._scan_assign_check_return_vars(stmt.body, consumed)
            elif isinstance(stmt, ast.Try):
                self._scan_assign_check_return_vars(stmt.body, consumed)
                for handler in stmt.handlers:
                    self._scan_assign_check_return_vars(handler.body, consumed)
            i += 1

    def _detect_assign_check_return_loose(self, stmts: list[ast.stmt], idx: int) -> str | None:
        """Looser version of _detect_assign_check_return for pre-scan.
        Returns the Go variable name if pattern matches, None otherwise.
        Doesn't require var_types to be populated."""
        if idx + 1 >= len(stmts):
            return None
        # First statement must be: result = self.method()
        assign = stmts[idx]
        if not isinstance(assign, ast.Assign):
            return None
        if len(assign.targets) != 1:
            return None
        target = assign.targets[0]
        if not isinstance(target, ast.Name):
            return None
        var_name = target.id
        # RHS must be a method call
        if not isinstance(assign.value, ast.Call):
            return None
        call = assign.value
        if not isinstance(call.func, ast.Attribute):
            return None
        if not isinstance(call.func.value, ast.Name) or call.func.value.id != "self":
            return None
        method_name = call.func.attr
        # Check if this method returns a concrete pointer type
        return_type = self._get_method_return_type(method_name)
        if not return_type or not return_type.startswith("*"):
            return None
        # Second statement must be: if result: return result
        if_stmt = stmts[idx + 1]
        if not isinstance(if_stmt, ast.If):
            return None
        # Test must be just the variable name (truthy check)
        test_var_name = None
        if isinstance(if_stmt.test, ast.Name):
            test_var_name = if_stmt.test.id
        elif isinstance(if_stmt.test, ast.Compare):
            cmp = if_stmt.test
            if (
                isinstance(cmp.left, ast.Name)
                and len(cmp.ops) == 1
                and isinstance(cmp.ops[0], ast.IsNot)
                and len(cmp.comparators) == 1
                and isinstance(cmp.comparators[0], ast.Constant)
                and cmp.comparators[0].value is None
            ):
                test_var_name = cmp.left.id
        if test_var_name != var_name:
            return None
        # Body must be: return result
        if len(if_stmt.body) != 1:
            return None
        ret = if_stmt.body[0]
        if not isinstance(ret, ast.Return):
            return None
        if not isinstance(ret.value, ast.Name) or ret.value.id != var_name:
            return None
        # No else branch
        if if_stmt.orelse:
            return None
        go_var = self._to_go_var(var_name)
        return go_var

    def _populate_var_types_from_usage(self, stmts: list[ast.stmt]):
        """Populate var_types for all variables based on usage patterns."""
        append_types = self._collect_append_element_types(stmts)
        nullable_node_vars = self._collect_nullable_node_vars(stmts)
        nullable_string_vars = self._collect_nullable_string_vars(stmts)
        multi_node_vars = self._collect_multi_node_type_vars(stmts)
        for var, _info in self.var_usage.items():
            go_type = self.var_types.get(var)
            # Check append() calls for element type
            if var in append_types:
                elem_type = append_types[var]
                if elem_type and (
                    not go_type or go_type in ("interface{}", "[]interface{}", "[]string")
                ):
                    self.var_types[var] = f"[]{elem_type}"
                    continue
            # Check if var is None-initialized but later assigned Node types
            if var in nullable_node_vars:
                if not go_type or go_type == "interface{}":
                    self.var_types[var] = "Node"
                    continue
            # Check if var is None-initialized but later assigned string types
            if var in nullable_string_vars:
                if not go_type or go_type == "interface{}":
                    self.var_types[var] = "string"
                    continue
            # Check if var is assigned multiple different concrete Node types
            if var in multi_node_vars:
                if go_type and go_type.startswith("*") and go_type[1:] in self.symbols.classes:
                    if self.symbols.classes[go_type[1:]].is_node:
                        self.var_types[var] = "Node"
                        continue
            # Infer from name if no specific type
            if not go_type or go_type in ("interface{}", "[]interface{}"):
                name_type = self._infer_var_type_from_name(var)
                if name_type:
                    self.var_types[var] = name_type

    def _emit_hoisted_vars(self, scope_id: int, stmts: list[ast.stmt]):
        """Emit hoisted variable declarations for a scope."""
        # Collect additional type info
        append_types = self._collect_append_element_types(stmts)
        nullable_node_vars = self._collect_nullable_node_vars(stmts)
        nullable_string_vars = self._collect_nullable_string_vars(stmts)
        multi_node_vars = self._collect_multi_node_type_vars(stmts)
        for var, hoist_scope in self.hoisted_vars.items():
            if hoist_scope != scope_id:
                continue
            if var in self.declared_vars:
                continue
            # Get type from var_types first
            go_type = self.var_types.get(var)
            # Try to infer from first value if no type yet
            info = self.var_usage.get(var)
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
            self.declared_vars.add(var)
            self.var_types[var] = go_type

    def _predeclare_all_locals(self, stmts: list[ast.stmt]):
        """Pre-declare ALL local variables at function top (C-style).

        This completely avoids Go's block-scoping issues by declaring all
        variables upfront. Assignments then use = instead of :=.
        """
        # Collect all variable assignments recursively
        assignments: dict[str, ast.expr | None] = {}  # var name -> first value (for type inference)
        self._collect_all_assignments(stmts, assignments)
        # Collect all variable reads to filter out unused vars
        reads: set[str] = set()
        self._collect_all_reads(stmts, reads)
        # Collect element types from append() calls for better list type inference
        append_types = self._collect_append_element_types(stmts)
        # Collect variables that are None-initialized but later assigned Node types
        nullable_node_vars = self._collect_nullable_node_vars(stmts)
        # Collect variables that are None-initialized but later assigned string types
        nullable_string_vars = self._collect_nullable_string_vars(stmts)
        # Collect variables assigned multiple different concrete Node types
        multi_node_vars = self._collect_multi_node_type_vars(stmts)
        # Emit var declarations for all collected variables that are actually read
        for var_name, first_value in assignments.items():
            if var_name not in self.declared_vars and var_name in reads:
                # Try to get type from var_types first (from annotations, etc.)
                go_type = self.var_types.get(var_name)
                # But always try to infer from expression for more specific types
                if first_value is not None:
                    expr_type = self._infer_type_from_expr(first_value)
                    # Prefer expression type if it's more specific than var_types
                    if expr_type and expr_type not in ("interface{}", "[]interface{}"):
                        if not go_type or go_type in (
                            "interface{}",
                            "[]interface{}",
                            "map[string]interface{}",
                        ):
                            go_type = expr_type
                # Check append() calls for element type - this is more reliable than name heuristics
                if var_name in append_types:
                    elem_type = append_types[var_name]
                    if elem_type and (
                        not go_type or go_type in ("interface{}", "[]interface{}", "[]string")
                    ):
                        go_type = f"[]{elem_type}"
                # Check if var is None-initialized but later assigned Node types
                if var_name in nullable_node_vars:
                    if not go_type or go_type == "interface{}":
                        go_type = "Node"
                # Check if var is None-initialized but later assigned string types
                if var_name in nullable_string_vars:
                    if not go_type or go_type == "interface{}":
                        go_type = "string"
                # Check if var is assigned multiple different concrete Node types
                if var_name in multi_node_vars:
                    if go_type and go_type.startswith("*") and go_type[1:] in self.symbols.classes:
                        if self.symbols.classes[go_type[1:]].is_node:
                            go_type = "Node"
                if not go_type or go_type in ("interface{}", "[]interface{}"):
                    # Try harder - check if it's a known pattern
                    go_type = self._infer_var_type_from_name(var_name) or go_type or "interface{}"
                # Special case: 'results' (plural) in a method that returns []Node
                # Don't apply to 'result' (singular) which may be a single Node
                if var_name.lower() == "results" and self.current_method:
                    method_ret = self._get_current_method_return_type()
                    if method_ret == "[]Node":
                        go_type = method_ret
                # Special case: if expr says byte but name says string, prefer string
                # (handles cases like `direction = value[i]` used in string concatenation)
                if go_type == "byte":
                    name_type = self._infer_var_type_from_name(var_name)
                    if name_type == "string":
                        go_type = "string"
                self.emit(f"var {var_name} {go_type}")
                # Suppress unused variable warning immediately
                self.emit(f"_ = {var_name}")
                self.declared_vars.add(var_name)
                self.var_types[var_name] = go_type

    def _get_current_method_return_type(self) -> str:
        """Get the return type of the current method being emitted."""
        if hasattr(self, "current_func_info") and self.current_func_info:
            return self.current_func_info.return_type or ""
        return ""

    def _collect_all_assignments(
        self, stmts: list[ast.stmt], assignments: dict[str, ast.expr | None]
    ):
        """Recursively collect all variable assignments in a statement list."""
        for stmt in stmts:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        # For tuple-returning function calls, collect synthetic vars
                        if isinstance(stmt.value, ast.Call):
                            ret_info = self._get_return_type_info(stmt.value)
                            if ret_info and len(ret_info) > 1:
                                var_name = self._to_go_var(target.id)
                                for i, elem_type in enumerate(ret_info):
                                    synth_name = f"{var_name}{i}"
                                    if synth_name not in assignments:
                                        assignments[synth_name] = None
                                        # Store type for pre-declaration
                                        self.var_types[synth_name] = elem_type
                                continue
                        var_name = self._to_go_var(target.id)
                        if var_name not in assignments:
                            assignments[var_name] = stmt.value
                            # Infer type now while we have isinstance context
                            expr_type = self._infer_type_from_expr(stmt.value)
                            if expr_type and expr_type not in ("interface{}", "[]interface{}"):
                                if var_name not in self.var_types or self.var_types[var_name] in (
                                    "interface{}",
                                    "[]interface{}",
                                ):
                                    self.var_types[var_name] = expr_type
                    elif isinstance(target, ast.Tuple):
                        # Don't pre-declare tuple unpacking targets
                        # The unpacking statement itself uses := which declares them
                        pass
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                var_name = self._to_go_var(stmt.target.id)
                if var_name not in assignments:
                    assignments[var_name] = stmt.value
            elif isinstance(stmt, ast.For):
                # Don't pre-declare loop variables - for statement handles that
                # Just recurse into body
                self._collect_all_assignments(stmt.body, assignments)
            elif isinstance(stmt, ast.While):
                self._collect_all_assignments(stmt.body, assignments)
            elif isinstance(stmt, ast.If):
                # Check for isinstance pattern to narrow type during collection
                isinstance_info = self._detect_isinstance_if(stmt.test)
                if isinstance_info:
                    var_py, type_name = isinstance_info
                    var_go = self._to_go_var(var_py)
                    old_type = self.var_types.get(var_go)
                    self.var_types[var_go] = f"*{type_name}"
                    self._collect_all_assignments(stmt.body, assignments)
                    # Restore original type
                    if old_type is not None:
                        self.var_types[var_go] = old_type
                    else:
                        self.var_types.pop(var_go, None)
                else:
                    self._collect_all_assignments(stmt.body, assignments)
                if stmt.orelse:
                    self._collect_all_assignments(stmt.orelse, assignments)
            elif isinstance(stmt, ast.With):
                # Collect with-item variables
                for item in stmt.items:
                    if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                        var_name = self._to_go_var(item.optional_vars.id)
                        if var_name not in assignments:
                            assignments[var_name] = None
                self._collect_all_assignments(stmt.body, assignments)
            elif isinstance(stmt, ast.Try):
                self._collect_all_assignments(stmt.body, assignments)
                for handler in stmt.handlers:
                    if handler.name:
                        var_name = self._to_go_var(handler.name)
                        if var_name not in assignments:
                            assignments[var_name] = None
                    self._collect_all_assignments(handler.body, assignments)
                self._collect_all_assignments(stmt.orelse, assignments)
                self._collect_all_assignments(stmt.finalbody, assignments)

    def _collect_all_reads(self, stmts: list[ast.stmt], reads: set[str]):
        """Recursively collect all variable reads in a statement list."""
        for stmt in stmts:
            self._collect_reads_in_node(stmt, reads)

    def _collect_reads_in_node(self, node: ast.AST, reads: set[str]):
        """Collect variable reads from any AST node."""
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            var_name = self._to_go_var(node.id)
            reads.add(var_name)
        # Handle tuple element access: result[0] -> result0
        elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int):
                var_name = self._to_go_var(node.value.id)
                reads.add(f"{var_name}{node.slice.value}")
        for child in ast.iter_child_nodes(node):
            self._collect_reads_in_node(child, reads)

    def _collect_append_element_types(self, stmts: list[ast.stmt]) -> dict[str, str]:
        """Collect element types from append() calls to infer list types."""
        result: dict[str, str] = {}
        self._collect_appends_recursive(stmts, result)
        return result

    def _collect_appends_recursive(self, stmts: list[ast.stmt], result: dict[str, str]):
        """Recursively find append calls and infer element types."""
        for stmt in stmts:
            # Look for: var.append(value)
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                if (
                    isinstance(call.func, ast.Attribute)
                    and call.func.attr == "append"
                    and isinstance(call.func.value, ast.Name)
                    and call.args
                ):
                    var_name = self._to_go_var(call.func.value.id)
                    # Infer element type from the argument
                    elem_type = self._infer_append_element_type(call.args[0])
                    if elem_type and var_name not in result:
                        result[var_name] = elem_type
            # Recurse into control flow
            if isinstance(stmt, ast.If):
                self._collect_appends_recursive(stmt.body, result)
                self._collect_appends_recursive(stmt.orelse, result)
            elif isinstance(stmt, ast.For):
                self._collect_appends_recursive(stmt.body, result)
            elif isinstance(stmt, ast.While):
                self._collect_appends_recursive(stmt.body, result)
            elif isinstance(stmt, ast.Try):
                self._collect_appends_recursive(stmt.body, result)
                for handler in stmt.handlers:
                    self._collect_appends_recursive(handler.body, result)
            elif isinstance(stmt, ast.With):
                self._collect_appends_recursive(stmt.body, result)

    def _infer_append_element_type(self, node: ast.expr) -> str:
        """Infer the Go type of an element being appended.

        Returns 'Node' for Node subtypes since []Node is the common interface type
        used in function signatures, even when appending concrete types like *Word.
        """
        # Variable reference - check var_types or infer from name
        if isinstance(node, ast.Name):
            var_name = self._to_go_var(node.id)
            if var_name in self.var_types:
                vtype = self.var_types[var_name]
                # Convert concrete Node types to Node interface for slice compatibility
                if vtype.startswith("*") and vtype[1:] in self.symbols.classes:
                    if self.symbols.classes[vtype[1:]].is_node:
                        return "Node"
                return vtype
            # Common patterns - return Node for AST node types
            if node.id in (
                "word",
                "w",
                "redirect",
                "redir",
                "cmd",
                "command",
                "node",
                "n",
                "result",
                "elem",
                "item",
                "part",
            ):
                return "Node"
        # Method call that returns a known type
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                method = node.func.attr
                # Parse methods that return Node types
                if method.startswith("parse") or method.startswith("Parse"):
                    return "Node"
                if method in ("_Advance", "_advance", "Advance", "advance"):
                    return "string"
            # Constructor call for a Node class
            elif isinstance(node.func, ast.Name):
                if node.func.id in self.symbols.classes:
                    if self.symbols.classes[node.func.id].is_node:
                        return "Node"
        # String literal
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return "string"
        return ""

    def _collect_nullable_typed_vars(
        self, stmts: list[ast.stmt], type_checker: Callable[[ast.expr], bool]
    ) -> set[str]:
        """Collect variables first assigned None then later assigned a typed value."""
        none_vars: set[str] = set()
        self._collect_none_assigned_vars(stmts, none_vars)
        result: set[str] = set()
        self._collect_typed_assigned_vars(stmts, none_vars, result, type_checker)
        return result

    def _collect_nullable_node_vars(self, stmts: list[ast.stmt]) -> set[str]:
        """Collect variables first assigned None but later assigned Nodes."""
        return self._collect_nullable_typed_vars(stmts, self._is_node_returning_expr)

    def _collect_nullable_string_vars(self, stmts: list[ast.stmt]) -> set[str]:
        """Collect variables first assigned None but later assigned strings."""
        return self._collect_nullable_typed_vars(stmts, self._is_string_returning_expr)

    def _collect_typed_assigned_vars(
        self,
        stmts: list[ast.stmt],
        candidates: set[str],
        result: set[str],
        type_checker: Callable[[ast.expr], bool],
    ):
        """Find candidate vars later assigned values matching type_checker."""
        for stmt in stmts:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        var_name = self._to_go_var(target.id)
                        if var_name in candidates and type_checker(stmt.value):
                            result.add(var_name)
            # Recurse into control flow
            if isinstance(stmt, ast.If):
                self._collect_typed_assigned_vars(stmt.body, candidates, result, type_checker)
                self._collect_typed_assigned_vars(stmt.orelse, candidates, result, type_checker)
            elif isinstance(stmt, ast.For):
                self._collect_typed_assigned_vars(stmt.body, candidates, result, type_checker)
            elif isinstance(stmt, ast.While):
                self._collect_typed_assigned_vars(stmt.body, candidates, result, type_checker)
            elif isinstance(stmt, ast.Try):
                self._collect_typed_assigned_vars(stmt.body, candidates, result, type_checker)
                for handler in stmt.handlers:
                    self._collect_typed_assigned_vars(
                        handler.body, candidates, result, type_checker
                    )
            elif isinstance(stmt, ast.With):
                self._collect_typed_assigned_vars(stmt.body, candidates, result, type_checker)

    def _is_string_returning_expr(self, node: ast.expr) -> bool:
        """Check if an expression returns a string type."""
        # String literals
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return True
        # Variable reference - check if we know its type
        if isinstance(node, ast.Name):
            var_type = self.var_types.get(self._to_go_var(node.id), "")
            return var_type == "string"
        # JoinedStr (f-string)
        if isinstance(node, ast.JoinedStr):
            return True
        # String methods
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            method = node.func.attr
            if method in ("join", "strip", "lstrip", "rstrip", "lower", "upper", "replace"):
                return True
        return False

    def _collect_none_assigned_vars(self, stmts: list[ast.stmt], result: set[str]):
        """Find variables first assigned None."""
        for stmt in stmts:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        if isinstance(stmt.value, ast.Constant) and stmt.value.value is None:
                            result.add(self._to_go_var(target.id))
            # Recurse into control flow
            if isinstance(stmt, ast.If):
                self._collect_none_assigned_vars(stmt.body, result)
                self._collect_none_assigned_vars(stmt.orelse, result)
            elif isinstance(stmt, ast.For):
                self._collect_none_assigned_vars(stmt.body, result)
            elif isinstance(stmt, ast.While):
                self._collect_none_assigned_vars(stmt.body, result)
            elif isinstance(stmt, ast.Try):
                self._collect_none_assigned_vars(stmt.body, result)
                for handler in stmt.handlers:
                    self._collect_none_assigned_vars(handler.body, result)
            elif isinstance(stmt, ast.With):
                self._collect_none_assigned_vars(stmt.body, result)

    def _is_node_returning_expr(self, node: ast.expr) -> bool:
        """Check if an expression returns a Node type."""
        # Method calls to parse_* methods return Node
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            method = node.func.attr
            # Parse methods return Node types
            if method.startswith("parse") or method.startswith("_parse"):
                return True
            if method.startswith("Parse") or method.startswith("_Parse"):
                return True
            # Check if method is in class and returns Node
            class_name = self._infer_object_class(node.func.value)
            if class_name:
                class_info = self.symbols.classes.get(class_name)
                if class_info and method in class_info.methods:
                    ret_type = class_info.methods[method].return_type or ""
                    if ret_type == "Node" or ret_type.endswith("| None") and "Node" in ret_type:
                        return True
                    # Check if return type is a Node subclass
                    if ret_type.startswith("*") and ret_type[1:] in self.symbols.classes:
                        if self.symbols.classes[ret_type[1:]].is_node:
                            return True
        # Node constructor
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in self.symbols.classes:
                if self.symbols.classes[node.func.id].is_node:
                    return True
        return False

    def _collect_multi_node_type_vars(self, stmts: list[ast.stmt]) -> set[str]:
        """Collect variables assigned multiple different concrete Node types.

        Pattern:
            result = self.parse_brace_group()  # *BraceGroup
            if cond:
                result = self.parse_subshell()  # *Subshell

        These should be typed as Node, not the first concrete type.
        """
        # Collect all Node types assigned to each variable
        var_node_types: dict[str, set[str]] = {}
        self._collect_var_node_types(stmts, var_node_types)
        # Variables with multiple different Node types should be typed as Node
        result: set[str] = set()
        for var_name, types in var_node_types.items():
            if len(types) > 1:
                result.add(var_name)
        return result

    def _collect_var_node_types(self, stmts: list[ast.stmt], result: dict[str, set[str]]):
        """Collect the concrete Node types assigned to each variable."""
        for stmt in stmts:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        var_name = self._to_go_var(target.id)
                        node_type = self._get_concrete_node_type(stmt.value)
                        if node_type:
                            if var_name not in result:
                                result[var_name] = set()
                            result[var_name].add(node_type)
            # Recurse into control flow
            if isinstance(stmt, ast.If):
                self._collect_var_node_types(stmt.body, result)
                self._collect_var_node_types(stmt.orelse, result)
            elif isinstance(stmt, ast.For):
                self._collect_var_node_types(stmt.body, result)
            elif isinstance(stmt, ast.While):
                self._collect_var_node_types(stmt.body, result)
            elif isinstance(stmt, ast.Try):
                self._collect_var_node_types(stmt.body, result)
                for handler in stmt.handlers:
                    self._collect_var_node_types(handler.body, result)
            elif isinstance(stmt, ast.With):
                self._collect_var_node_types(stmt.body, result)

    def _get_concrete_node_type(self, node: ast.expr) -> str:
        """Get the concrete Node type from an expression, or empty string if not a Node."""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                method = node.func.attr
                class_name = self._infer_object_class(node.func.value)
                if class_name:
                    class_info = self.symbols.classes.get(class_name)
                    if class_info and method in class_info.methods:
                        ret_type = class_info.methods[method].return_type or ""
                        # Return concrete Node types (e.g., *BraceGroup, *Subshell)
                        if ret_type.startswith("*") and ret_type[1:] in self.symbols.classes:
                            if self.symbols.classes[ret_type[1:]].is_node:
                                return ret_type
                        # Return "Node" for methods that return Node interface
                        if ret_type == "Node":
                            return "Node"
            elif isinstance(node.func, ast.Name):
                # Node constructor
                if node.func.id in self.symbols.classes:
                    if self.symbols.classes[node.func.id].is_node:
                        return "*" + node.func.id
        return ""

    def _infer_var_type_from_name(self, var_name: str) -> str:
        """Infer type from common variable naming patterns."""
        name_lower = var_name.lower()
        # Boolean patterns
        if name_lower.startswith(("is", "has", "was", "can", "should", "in_", "at_")):
            return "bool"
        if name_lower in ("ok", "found", "done", "valid", "exists", "passnext", "wasdollar"):
            return "bool"
        # Integer patterns
        if name_lower in (
            "i",
            "j",
            "k",
            "n",
            "idx",
            "index",
            "count",
            "depth",
            "len",
            "length",
            "start",
            "end",
            "pos",
            "offset",
            "size",
            "num",
            "line",
            "col",
            "flags",
            "state",
            "ctx",
            "mode",
        ):
            return "int"
        if name_lower.endswith(
            ("count", "depth", "pos", "idx", "index", "len", "size", "flags", "state")
        ):
            return "int"
        if "dolbrace" in name_lower:
            return "int"
        # Token patterns
        if name_lower in ("tok", "token", "savedlast"):
            return "*Token"
        if name_lower.endswith("token") or name_lower.endswith("tok"):
            return "*Token"
        # String patterns (be careful not to include names that could be slices like "result")
        if name_lower in (
            "s",
            "ch",
            "char",
            "name",
            "text",
            "value",
            "content",
            "nested",
            "arg",
            "inner",
            "escaped",
            "afterbrace",
            "opstart",
            "rest",
            "ansistr",
            "expanded",
            "resultstr",
            "leadingws",
            "normalizedws",
            "stripped",
            "direction",
            "rawcontent",
            "rawstripped",
            "spaced",
            "prefix",
            "suffix",
            "originner",
            "closing",
            "finaloutput",
            "formatted",
            "leftsexp",
            "rightsexp",
            "fdtarget",
            "outval",
            "raw",
            "targetval",
        ):
            return "string"
        if name_lower.endswith(("str", "text", "name", "char", "content", "sexp")):
            return "string"
        # Byte patterns - single character variables from string subscripts
        if name_lower in ("byteval", "firstchar", "ctrlchar"):
            return "byte"
        # Node list patterns
        if name_lower in ("parts", "elements", "children", "nodes"):
            return "[]Node"
        if name_lower.endswith("parts") or name_lower.endswith("nodes"):
            return "[]Node"
        # String list patterns
        if name_lower in ("chars", "lines", "words"):
            return "[]string"
        if name_lower.endswith("chars") or name_lower.endswith("lines"):
            return "[]string"
        # Int list patterns (positions, indices)
        if name_lower.endswith("positions"):
            return "[]int"
        # Segment list patterns (slices of nodes)
        if name_lower == "segments":
            return "[][]Node"
        # Segment variable (slice of nodes)
        if name_lower == "seg":
            return "[]Node"
        # Node patterns (nullable in Python, but Node in Go since nil is valid)
        if name_lower in ("iftrue", "iffalse"):
            return "Node"
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
                go_name = self._to_go_param_name(p.name)
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
            if go_func_name in self.TUPLE_ELEMENT_TYPES:
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
        for (receiver_type, field_name), (expected_disc, _, _) in self.UNION_FIELDS.items():
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
        if comp.value not in self.KIND_TO_TYPE:
            return None
        return (test.left.value.id, comp.value)

    def _emit_kind_type_narrowing(self, stmt: ast.If, kind_info: tuple[str, str], is_first: bool):
        """Emit kind-based type narrowing as Go type assertion."""
        var_name, kind_literal = kind_info
        type_name = self.KIND_TO_TYPE[kind_literal]
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
            _, nil_type, non_nil_type = self.UNION_FIELDS[(receiver_type, field_name)]
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
        if go_func_name in self.TUPLE_ELEMENT_TYPES:
            # Returns first element type for tuple-returning funcs
            return self.TUPLE_ELEMENT_TYPES[go_func_name][0]
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
            go_name = self._to_go_param_name(p.name)
            go_type = p.go_type or "interface{}"
            parts.append(f"{go_name} {go_type}")
        return ", ".join(parts)

    def _to_go_func_name(self, name: str) -> str:
        """Convert Python function name to Go function name."""
        if name.startswith("_"):
            # Keep leading underscore for private functions
            return name[0] + self._snake_to_pascal(name[1:])
        return self._snake_to_pascal(name)

    def _to_go_method_name(self, name: str) -> str:
        """Convert Python method name to Go method name."""
        if name.startswith("_"):
            return name[0] + self._snake_to_pascal(name[1:])
        return self._snake_to_pascal(name)

    def _to_go_param_name(self, name: str) -> str:
        """Convert Python parameter name to Go parameter name."""
        # Handle reserved words
        reserved = {
            "type": "typ",
            "func": "fn",
            "var": "variable",
            "range": "rng",
            "map": "m",
            "interface": "iface",
            "chan": "ch",
            "select": "sel",
            "case": "caseVal",
            "default": "defaultVal",
            "package": "pkg",
            "import": "imp",
            "go": "goVal",
            "defer": "deferVal",
            "return": "ret",
            "break": "brk",
            "continue": "cont",
            "fallthrough": "fallthru",
            "if": "ifVal",
            "else": "elseVal",
            "for": "forVal",
            "switch": "switchVal",
            "const": "constVal",
            "struct": "structVal",
        }
        camel = self._snake_to_camel(name)
        return reserved.get(camel, camel)

    def _snake_to_pascal(self, name: str) -> str:
        """Convert snake_case to PascalCase."""
        return "".join(word.capitalize() for word in name.split("_"))

    def _snake_to_camel(self, name: str) -> str:
        """Convert snake_case to camelCase."""
        if name == "_":
            return "_"
        parts = name.split("_")
        # Filter out empty parts from leading underscores
        parts = [p for p in parts if p]
        if not parts:
            return name
        return parts[0] + "".join(word.capitalize() for word in parts[1:])

    # ========== Expression Emission ==========

    def visit_expr(self, node: ast.expr) -> str:
        """Convert a Python expression to Go code string."""
        method = f"visit_expr_{node.__class__.__name__}"
        if hasattr(self, method):
            return getattr(self, method)(node)
        raise NotImplementedError(f"Expression type {node.__class__.__name__}")

    def visit_expr_Constant(self, node: ast.Constant) -> str:
        """Convert constant literals."""
        if isinstance(node.value, bool):
            return "true" if node.value else "false"
        if isinstance(node.value, int):
            return str(node.value)
        if isinstance(node.value, str):
            value = node.value
            # Escape for Go string literal
            escaped = (
                value.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\t", "\\t")
                .replace("\r", "\\r")
            )
            # Escape control characters
            result = []
            for c in escaped:
                ord_c = ord(c)
                if ord_c < 32 or ord_c == 127:
                    result.append(f"\\x{ord_c:02x}")
                else:
                    result.append(c)
            return f'"{"".join(result)}"'
        if node.value is None:
            return "nil"
        if isinstance(node.value, bytes):
            # Convert bytes to []byte literal
            return "[]byte{" + ", ".join(str(b) for b in node.value) + "}"
        return repr(node.value)

    def visit_expr_Name(self, node: ast.Name) -> str:
        """Convert variable names."""
        mapping = {
            "True": "true",
            "False": "false",
            "None": "nil",
            "self": self._get_receiver_name(),
        }
        name = mapping.get(node.id, node.id)
        # Handle class name constants (e.g., TokenType.WORD)
        if name in self.symbols.classes:
            return name
        # Handle module-level constants (SCREAMING_CASE or _SCREAMING_CASE)
        if name.isupper() or (name.startswith("_") and name[1:].isupper()):
            go_name = name.lstrip("_")
            parts = go_name.split("_")
            return "".join(p.capitalize() for p in parts)
        # Convert to camelCase and handle reserved words
        result = self._to_go_var(name)
        # Rewrite variable references in type switch context
        if self._type_switch_var and result == self._type_switch_var[0]:
            return self._type_switch_var[1]
        return result

    def _safe_go_name(self, name: str) -> str:
        """Make sure name is not a Go reserved word."""
        reserved = {
            "type": "typ",
            "func": "fn",
            "var": "variable",
            "range": "rng",
            "map": "m",
            "interface": "iface",
            "chan": "ch",
            "select": "sel",
            "case": "caseVal",
            "default": "defaultVal",
            "package": "pkg",
            "import": "imp",
            "go": "goVal",
            "defer": "deferVal",
            "return": "ret",
            "break": "brk",
            "continue": "cont",
            "fallthrough": "fallthru",
            "if": "ifVal",
            "else": "elseVal",
            "for": "forVal",
            "switch": "switchVal",
            "const": "constVal",
            "struct": "structVal",
        }
        return reserved.get(name, name)

    def _to_go_var(self, name: str) -> str:
        """Convert a Python variable name to a Go variable name."""
        return self._safe_go_name(self._snake_to_camel(name))

    def _get_receiver_name(self) -> str:
        """Get receiver name for current class context."""
        if self.current_class:
            return self.current_class[0].lower()
        return "self"

    def visit_expr_Attribute(self, node: ast.Attribute) -> str:
        """Convert attribute access."""
        attr_name = node.attr
        # Check for class constant access like DolbraceState.PARAM
        if isinstance(node.value, ast.Name):
            class_name = node.value.id
            if class_name in self.symbols.classes:
                class_info = self.symbols.classes[class_name]
                if attr_name in class_info.constants:
                    return f"{class_name}_{attr_name}"
        value = self.visit_expr(node.value)
        # Check if this is accessing a method that should be called (like node.kind -> node.Kind())
        if self._is_interface_method(node.value, attr_name):
            go_attr = self._to_go_method_name(attr_name)
            return f"{value}.{go_attr}()"
        attr = self._to_go_field_name(attr_name)
        # Check if accessing a union field with a type hint
        if isinstance(node.value, ast.Name) and node.value.id == "self" and self.current_class:
            union_key = (self.current_class, attr_name)
            if union_key in self.union_field_types:
                field_type = self.union_field_types[union_key]
                return f"{value}.{attr}.({field_type})"
        # Check if value needs type assertion for struct-specific field access
        value_type = self._get_expr_element_type(node.value)
        if value_type in ("interface{}", "Node"):
            type_assertion = self._get_type_for_field(attr_name, node.value)
            if type_assertion:
                return f"{value}.({type_assertion}).{attr}"
        return f"{value}.{attr}"

    def _get_expr_type(self, node: ast.expr) -> str:
        """Get the Go type of an expression."""
        # Variable reference
        if isinstance(node, ast.Name):
            var_name = self._to_go_var(node.id)
            return self.var_types.get(var_name, "")
        # Attribute access - look up field type in struct
        if isinstance(node, ast.Attribute):
            # self.x -> look up field type in current class
            if isinstance(node.value, ast.Name) and node.value.id == "self" and self.current_class:
                class_info = self.symbols.classes.get(self.current_class)
                if class_info and node.attr in class_info.fields:
                    return class_info.fields[node.attr].go_type or ""
            # obj.x -> look up field type in object's class
            obj_class = self._infer_object_class(node.value)
            if obj_class and obj_class in self.symbols.classes:
                class_info = self.symbols.classes[obj_class]
                if node.attr in class_info.fields:
                    return class_info.fields[node.attr].go_type or ""
        return ""

    def _get_expr_element_type(self, node: ast.expr) -> str:
        """Get the type that an expression evaluates to (for type assertion decisions)."""
        # Variable reference
        if isinstance(node, ast.Name):
            var_name = self._to_go_var(node.id)
            # If in type switch and this is the switched variable, use narrowed type
            if self._type_switch_var and var_name == self._type_switch_var[0]:
                return self._type_switch_type or ""
            return self.var_types.get(var_name, "")
        # Subscript on a slice - get the element type
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            var_name = self._to_go_var(node.value.id)
            var_type = self.var_types.get(var_name, "")
            if var_type.startswith("[]"):
                return var_type[2:]  # []Node -> Node
        # Attribute access - look up field type in struct
        if isinstance(node, ast.Attribute):
            # Get the class of the object being accessed
            obj_class = self._infer_object_class(node.value)
            if obj_class and obj_class in self.symbols.classes:
                class_info = self.symbols.classes[obj_class]
                if node.attr in class_info.fields:
                    return class_info.fields[node.attr].go_type or ""
        return ""

    def _get_type_for_field(
        self, field_name: str, value_node: ast.expr | None = None
    ) -> str | None:
        """Get the type assertion needed for a field access on interface{} or Node."""
        # Special case: .command field exists on both CommandSubstitution and ProcessSubstitution
        # Determine which type based on the assignment source tracked in var_assign_sources
        if field_name == "command" and value_node is not None:
            if isinstance(value_node, ast.Name):
                var_name = self._to_go_var(value_node.id)
                source = getattr(self, "var_assign_sources", {}).get(var_name, "")
                if source == "procsub_parts":
                    return "*ProcessSubstitution"
                elif source == "cmdsub_parts":
                    return "*CommandSubstitution"
        field_to_type = {
            "command": "*CommandSubstitution",
            "body": "*ProcessSubstitution",
            "elements": "*ArrayNode",
            "parts": "*Word",
            "words": "*Command",
            "redirects": "*Command",
            "op": "*Operator",
            "value": "*Word",  # For Target.Value where Target is Node
            "target": "*Redirect",  # For Redirect.Target
        }
        return field_to_type.get(field_name)

    def _find_method_owner(self, method_name: str) -> str | None:
        """Find which struct type owns a given method."""
        # Search all classes for this method
        for class_name, class_info in self.symbols.classes.items():
            if method_name in class_info.methods:
                if class_info.is_node:
                    return "*" + class_name
                return "*" + class_name
        return None

    def _is_interface_method(self, value: ast.expr, attr: str) -> bool:
        """Check if attribute is a method on an interface type."""
        # Node interface methods
        if attr in ("kind", "to_sexp"):
            # Check if value is self in a non-Node class (like ParseContext) - kind is a field there
            if isinstance(value, ast.Name) and value.id == "self":
                if self.current_class and not self.symbols.is_node_subclass(self.current_class):
                    return False  # It's a field access in a non-Node class
            # Check if value is likely a Node
            if isinstance(value, ast.Name):
                name = value.id
                if name in (
                    "node",
                    "n",
                    "child",
                    "elem",
                    "item",
                    "body",
                    "left",
                    "right",
                    "operand",
                ):
                    return True
            return True  # Assume it's a method if uncertain
        return False

    def _needs_node_assertion(self, value: ast.expr) -> bool:
        """Check if calling Node method on this expr needs a type assertion."""
        # If it's a variable with interface{} type, needs assertion
        if isinstance(value, ast.Name):
            var_name = self._to_go_var(value.id)
            var_type = self.var_types.get(var_name, "")
            # If type is interface{}, needs assertion
            if var_type == "interface{}":
                return True
        return False

    def _func_expects_string_param(self, func_name: str, param_index: int) -> bool:
        """Check if a function parameter expects string (for byte conversion)."""
        # Single-character helper functions that take string param at index 0
        char_funcs = {
            "_is_whitespace",
            "_is_whitespace_no_newline",
            "_is_metachar",
            "_is_hex_digit",
            "_is_octal_digit",
            "_get_ansi_escape",
            "_is_funsub_char",
            "_is_extglob_prefix",
            "_is_digit",
            "_is_special_param_unbraced",
            "_is_simple_param_op",
            "_is_escape_char_in_backtick",
        }
        if func_name in char_funcs and param_index == 0:
            return True
        return False

    def _fill_default_args(self, func_name: str, args: list[str]) -> list[str]:
        """Fill in default argument values for functions with optional params."""
        # Look up function info
        func_info = self.symbols.functions.get(func_name)
        if not func_info:
            # Check if it's a class constructor (__init__)
            class_info = self.symbols.classes.get(func_name)
            if class_info:
                if "__init__" in class_info.methods:
                    func_info = class_info.methods["__init__"]
                else:
                    # Check parent classes for inherited __init__
                    for base in class_info.bases:
                        base_info = self.symbols.classes.get(base)
                        if base_info and "__init__" in base_info.methods:
                            func_info = base_info.methods["__init__"]
                            break
            if not func_info:
                return args
        # Check if we need to add default values
        expected_params = len(func_info.params)
        provided_args = len(args)
        if provided_args >= expected_params:
            return args
        # Add defaults for missing args
        result = list(args)
        for i in range(provided_args, expected_params):
            param = func_info.params[i]
            if param.default is not None:
                default_val = self.visit_expr(param.default)
                # Convert nil to zero value based on parameter type
                if default_val == "nil":
                    default_val = self._nil_to_zero_value(param.go_type)
                result.append(default_val)
            else:
                # No default, can't fill in
                break
        return result

    def _merge_keyword_args(
        self, func_name: str, args: list[str], keywords: list[ast.keyword]
    ) -> list[str]:
        """Merge keyword arguments into positional argument list."""
        if not keywords:
            return args
        # Look up function info to get parameter names and positions
        func_info = self.symbols.functions.get(func_name)
        if not func_info:
            # Check if it's a class constructor
            class_info = self.symbols.classes.get(func_name)
            if class_info:
                if "__init__" in class_info.methods:
                    func_info = class_info.methods["__init__"]
                else:
                    # Check parent classes for inherited __init__
                    for base in class_info.bases:
                        base_info = self.symbols.classes.get(base)
                        if base_info and "__init__" in base_info.methods:
                            func_info = base_info.methods["__init__"]
                            break
            if not func_info:
                return args
        # Build param name to index mapping
        param_indices: dict[str, int] = {}
        for i, param in enumerate(func_info.params):
            param_indices[param.name] = i
        # Merge keyword args at correct positions
        result = list(args)
        for kw in keywords:
            if kw.arg is None:
                continue  # **kwargs not supported
            if kw.arg in param_indices:
                idx = param_indices[kw.arg]
                # Extend result list if needed, using zero values based on param type
                while len(result) <= idx:
                    fill_idx = len(result)
                    if fill_idx < len(func_info.params):
                        fill_type = func_info.params[fill_idx].go_type
                        result.append(self._nil_to_zero_value(fill_type))
                    else:
                        result.append("nil")
                result[idx] = self.visit_expr(kw.value)
        return result

    def _infer_object_class(self, node: ast.expr) -> str | None:
        """Infer the class name of an object expression."""
        if isinstance(node, ast.Attribute):
            # self._parser -> Parser, l._parser -> Parser
            attr = node.attr
            if attr.startswith("_"):
                attr = attr[1:]
            attr_pascal = self._snake_to_pascal(attr)
            if attr_pascal in self.symbols.classes:
                return attr_pascal
            # self.something -> might need to look up field type
            if isinstance(node.value, ast.Name) and node.value.id == "self":
                # Look up the field type in current class
                if self.current_class:
                    class_info = self.symbols.classes.get(self.current_class)
                    if class_info and node.attr in class_info.fields:
                        field_info = class_info.fields[node.attr]
                        field_type = field_info.py_type
                        # Extract class name from type like "Parser | None"
                        for word in field_type.replace("|", " ").split():
                            if word in self.symbols.classes:
                                return word
        # self -> current class
        if isinstance(node, ast.Name):
            if node.id == "self" and self.current_class:
                return self.current_class
            # Check local variable type
            var_name = self._to_go_var(node.id)
            var_type = self.var_types.get(var_name, "")
            # Extract class name from pointer type like "*Word"
            if var_type.startswith("*"):
                class_name = var_type[1:]
                if class_name in self.symbols.classes:
                    return class_name
            elif var_type in self.symbols.classes:
                return var_type
        # Subscript expression: parts[0] -> Node if parts is []Node
        if isinstance(node, ast.Subscript):
            elem_type = self._get_expr_element_type(node)
            if elem_type == "Node":
                return "Node"  # Special case - it's the Node interface
            if elem_type in self.symbols.classes:
                return elem_type
        # Constructor call: Word(...) -> Word
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            class_name = node.func.id
            if class_name in self.symbols.classes:
                return class_name
        return None

    def _merge_keyword_args_for_method(
        self, class_name: str, method: str, args: list[str], keywords: list[ast.keyword]
    ) -> list[str]:
        """Merge keyword arguments for a method call."""
        if not keywords:
            return args
        class_info = self.symbols.classes.get(class_name)
        if not class_info:
            return args
        # Try original name first, then camelCase, then PascalCase
        method_key = method
        if method_key not in class_info.methods:
            method_key = self._snake_to_camel(method)
        if method_key not in class_info.methods:
            method_key = self._snake_to_pascal(method)
        if method_key not in class_info.methods:
            return args
        func_info = class_info.methods[method_key]
        # Build param name to index mapping
        param_indices: dict[str, int] = {}
        for i, param in enumerate(func_info.params):
            param_indices[param.name] = i
        # Merge keyword args
        result = list(args)
        for kw in keywords:
            if kw.arg is None:
                continue
            if kw.arg in param_indices:
                idx = param_indices[kw.arg]
                while len(result) <= idx:
                    fill_idx = len(result)
                    if fill_idx < len(func_info.params):
                        fill_type = func_info.params[fill_idx].go_type
                        result.append(self._nil_to_zero_value(fill_type))
                    else:
                        result.append("nil")
                result[idx] = self.visit_expr(kw.value)
        return result

    def _fill_default_args_for_method(
        self, class_name: str, method: str, args: list[str]
    ) -> list[str]:
        """Fill in default argument values for a method call."""
        class_info = self.symbols.classes.get(class_name)
        if not class_info:
            return args
        # Try original name first, then camelCase, then PascalCase
        method_key = method
        if method_key not in class_info.methods:
            method_key = self._snake_to_camel(method)
        if method_key not in class_info.methods:
            method_key = self._snake_to_pascal(method)
        if method_key not in class_info.methods:
            return args
        func_info = class_info.methods[method_key]
        expected_params = len(func_info.params)
        provided_args = len(args)
        if provided_args >= expected_params:
            return args
        result = list(args)
        for i in range(provided_args, expected_params):
            param = func_info.params[i]
            if param.default is not None:
                default_val = self.visit_expr(param.default)
                if default_val == "nil":
                    default_val = self._nil_to_zero_value(param.go_type)
                result.append(default_val)
            else:
                break
        return result

    def _add_address_of_for_ptr_slice_params(
        self, class_name: str, method: str, args: list[str], orig_args: list[ast.expr]
    ) -> list[str]:
        """Add & when passing slice to pointer-to-slice parameter."""
        class_info = self.symbols.classes.get(class_name)
        if not class_info:
            return args
        # Try original name first, then camelCase, then PascalCase
        method_key = method
        if method_key not in class_info.methods:
            method_key = self._snake_to_camel(method)
        if method_key not in class_info.methods:
            method_key = self._snake_to_pascal(method)
        if method_key not in class_info.methods:
            return args
        func_info = class_info.methods[method_key]
        result = list(args)
        for i, arg_str in enumerate(result):
            if i >= len(func_info.params) or i >= len(orig_args):
                break
            param = func_info.params[i]
            param_type = param.go_type
            if not param_type or not param_type.startswith("*[]"):
                continue
            # Check if the argument is a slice variable (not already a pointer)
            if isinstance(orig_args[i], ast.Name):
                var_name = self._to_go_var(orig_args[i].id)
                arg_type = self.var_types.get(var_name, "")
                if arg_type and arg_type.startswith("[]") and not arg_type.startswith("[]*"):
                    result[i] = f"&{arg_str}"
        return result

    def visit_expr_Subscript(self, node: ast.Subscript) -> str:
        """Convert subscript access (indexing/slicing)."""
        # Check if accessing tuple variable element (cmdsub_result[0] -> cmdsubResult0)
        if isinstance(node.value, ast.Name) and isinstance(node.slice, ast.Constant):
            var_name = self._to_go_var(node.value.id)
            if var_name in self.tuple_vars and isinstance(node.slice.value, int):
                idx = node.slice.value
                elem_vars = self.tuple_vars[var_name]
                if 0 <= idx < len(elem_vars):
                    return elem_vars[idx]
        value = self.visit_expr(node.value)
        if isinstance(node.slice, ast.Slice):
            # Check if slicing a string - need rune-based slicing
            is_string_slice = self._is_string_slice(node)
            # For Lexer/Parser Source slices, use Source_runes directly
            is_source_slice = self._is_lexer_source_slice(node)
            # Compute len function based on type
            len_func = "_runeLen" if is_string_slice else "len"
            if is_source_slice:
                receiver = self.current_class[0].lower()
                len_func = f"len({receiver}.Source_runes)"
            # Handle negative indices (Python [:-1] -> Go [:len(x)-1])
            lower = ""
            upper = ""
            if node.slice.lower:
                if isinstance(node.slice.lower, ast.UnaryOp) and isinstance(
                    node.slice.lower.op, ast.USub
                ):
                    # Negative lower bound: -N -> len(x)-N
                    n = self.visit_expr(node.slice.lower.operand)
                    if is_source_slice:
                        lower = f"{len_func}-{n}"
                    elif is_string_slice:
                        lower = f"{len_func}({value})-{n}"
                    else:
                        lower = f"len({value})-{n}"
                elif (
                    isinstance(node.slice.lower, ast.Constant)
                    and isinstance(node.slice.lower.value, int)
                    and node.slice.lower.value < 0
                ):
                    # Negative constant lower bound
                    if is_source_slice:
                        lower = f"{len_func}{node.slice.lower.value}"
                    elif is_string_slice:
                        lower = f"{len_func}({value}){node.slice.lower.value}"
                    else:
                        lower = f"len({value}){node.slice.lower.value}"
                else:
                    lower = self.visit_expr(node.slice.lower)
            else:
                lower = "0"
            if node.slice.upper:
                if isinstance(node.slice.upper, ast.UnaryOp) and isinstance(
                    node.slice.upper.op, ast.USub
                ):
                    # Negative upper bound: -N -> len(x)-N
                    n = self.visit_expr(node.slice.upper.operand)
                    if is_source_slice:
                        upper = f"{len_func}-{n}"
                    elif is_string_slice:
                        upper = f"{len_func}({value})-{n}"
                    else:
                        upper = f"len({value})-{n}"
                elif (
                    isinstance(node.slice.upper, ast.Constant)
                    and isinstance(node.slice.upper.value, int)
                    and node.slice.upper.value < 0
                ):
                    # Negative constant upper bound
                    if is_source_slice:
                        upper = f"{len_func}{node.slice.upper.value}"
                    elif is_string_slice:
                        upper = f"{len_func}({value}){node.slice.upper.value}"
                    else:
                        upper = f"len({value}){node.slice.upper.value}"
                else:
                    upper = self.visit_expr(node.slice.upper)
            # Emit the slice
            if is_source_slice:
                receiver = self.current_class[0].lower()
                if upper:
                    return f"string({receiver}.Source_runes[{lower}:{upper}])"
                return f"string({receiver}.Source_runes[{lower}:])"
            if is_string_slice:
                if upper:
                    return f"_Substring({value}, {lower}, {upper})"
                return f"_Substring({value}, {lower}, {len_func}({value}))"
            if upper:
                return f"{value}[{lower}:{upper}]"
            return f"{value}[{lower}:]"
        index = self.visit_expr(node.slice)
        # Check if indexing a string - use rune-based access
        if self._is_string_subscript(node):
            # Check if this is self.source[i] in Lexer/Parser - use Source_runes
            if self._is_lexer_source_subscript(node):
                # Use pre-converted Source_runes for O(1) access
                receiver = self._get_receiver_name()
                return f"string({receiver}.Source_runes[{index}])"
            # General string indexing - use _runeAt helper
            return f"_runeAt({value}, {index})"
        # Check if indexing an interface{} variable (needs type assertion)
        if isinstance(node.value, ast.Name):
            var_name = self._to_go_var(node.value.id)
            var_type = self.var_types.get(var_name, "")
            if var_type == "interface{}":
                # Type assert to []interface{} then index
                base_expr = f"{value}.([]interface{{}})[{index}]"
                # Check if we know the element type from a tuple function
                # Only add assertion for slice types (for append contexts); simple types
                # are handled by the assignment handler
                if var_name in self.tuple_func_vars and isinstance(node.slice, ast.Constant):
                    func_name = self.tuple_func_vars[var_name]
                    idx = node.slice.value
                    if func_name in self.TUPLE_ELEMENT_TYPES:
                        elem_types = self.TUPLE_ELEMENT_TYPES[func_name]
                        if idx in elem_types:
                            elem_type = elem_types[idx]
                            # Only add type assertion for slice types (e.g., []string)
                            # Simple types like int are handled by assignment target type
                            if elem_type.startswith("[]"):
                                return f"{base_expr}.({elem_type})"
                return base_expr
        return f"{value}[{index}]"

    def visit_expr_BinOp(self, node: ast.BinOp) -> str:
        """Convert binary operations."""
        left = self.visit_expr(node.left)
        right = self.visit_expr(node.right)
        op = self._binop_to_go(node.op)
        # Handle floor division
        if isinstance(node.op, ast.FloorDiv):
            return f"{left} / {right}"  # Go int division is floor
        # Handle power
        if isinstance(node.op, ast.Pow):
            return f"int(math.Pow(float64({left}), float64({right})))"
        # Handle true division (Python / always returns float)
        if isinstance(node.op, ast.Div):
            return f"float64({left}) / float64({right})"
        # Width-rank auto-casting for mixed int/float arithmetic
        if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult)):
            left_type = self._infer_type_from_expr(node.left)
            right_type = self._infer_type_from_expr(node.right)
            if left_type == "float64" and right_type == "int":
                right = f"float64({right})"
            elif left_type == "int" and right_type == "float64":
                left = f"float64({left})"
        return f"{left} {op} {right}"

    def _binop_to_go(self, op: ast.operator) -> str:
        """Convert Python binary operator to Go."""
        ops = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.FloorDiv: "/",
            ast.Mod: "%",
            ast.LShift: "<<",
            ast.RShift: ">>",
            ast.BitOr: "|",
            ast.BitXor: "^",
            ast.BitAnd: "&",
        }
        return ops.get(type(op), "/* ? */")

    def visit_expr_UnaryOp(self, node: ast.UnaryOp) -> str:
        """Convert unary operations."""
        if isinstance(node.op, ast.Not):
            operand = self._emit_bool_expr(node.operand)
            return f"!({operand})"
        operand = self.visit_expr(node.operand)
        if isinstance(node.op, ast.USub):
            return f"-{operand}"
        if isinstance(node.op, ast.UAdd):
            return f"+{operand}"
        if isinstance(node.op, ast.Invert):
            return f"^{operand}"
        return f"/* TODO: UnaryOp */{operand}"

    def _emit_bool_expr(self, node: ast.expr) -> str:
        """Emit expression in boolean context, handling slice/map/string truthiness."""
        # Handle tuple element access (cmdsub_result[0] -> cmdsubResult0)
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name) and isinstance(node.slice, ast.Constant):
                var_name = self._to_go_var(node.value.id)
                if var_name in self.tuple_vars and isinstance(node.slice.value, int):
                    idx = node.slice.value
                    elem_vars = self.tuple_vars[var_name]
                    if 0 <= idx < len(elem_vars):
                        elem_var = elem_vars[idx]
                        elem_type = self.var_types.get(elem_var, "")
                        if elem_type == "Node" or elem_type.startswith("*"):
                            return f"{elem_var} != nil"
                        if elem_type.startswith("[]") or elem_type.startswith("map["):
                            return f"len({elem_var}) > 0"
                        if elem_type == "string":
                            return f"len({elem_var}) > 0"
        # If it's a simple Name that might be a slice/map/string, convert appropriately
        if isinstance(node, ast.Name):
            var_name = self._to_go_var(node.id)
            var_type = self.var_types.get(var_name, "")
            # Check if it's a Node type (interface, might be nil)
            if var_type == "Node" or var_type.startswith("*"):
                return f"{var_name} != nil"
            # Check if it's a slice or map type
            if var_type.startswith("[]") or var_type.startswith("map["):
                return f"len({var_name}) > 0"
            if var_type == "string":
                return f"len({var_name}) > 0"
            # Check if it's an int type (needs != 0 check)
            if var_type == "int":
                return f"{var_name} != 0"
            # Check by variable name heuristics for Node types
            if node.id.endswith(("_node", "Node", "_result")) or node.id in (
                "paramNode",
                "arithNode",
                "cmdNode",
                "node",
                "result",
            ):
                return f"{self.visit_expr(node)} != nil"
            # Check by variable name heuristics
            if node.id in ("redirects", "parts", "words", "commands", "args", "elts", "items"):
                return f"len({self.visit_expr(node)}) > 0"
            # String variable name heuristics
            if node.id in (
                "s",
                "name",
                "value",
                "text",
                "line",
                "word",
                "op",
                "delimiter",
                "param",
                "content",
                "nested",
                "arg",
                "inner",
                "trailing",
            ):
                return f"len({self.visit_expr(node)}) > 0"
        # If it's an attribute access that looks like a slice field
        if isinstance(node, ast.Attribute):
            if node.attr in ("redirects", "parts", "words", "commands", "args", "elts"):
                return f"len({self.visit_expr(node)}) > 0"
            # Optional Node fields need nil check
            if node.attr in ("else_body", "condition", "else_clause", "finally_clause", "body"):
                return f"{self.visit_expr(node)} != nil"
            # Look up field type from local variable's class
            if isinstance(node.value, ast.Name) and node.value.id != "self":
                var_name = self._to_go_var(node.value.id)
                var_type = self.var_types.get(var_name, "")
                if var_type.startswith("*"):
                    class_name = var_type[1:]
                    if class_name in self.symbols.classes:
                        class_info = self.symbols.classes[class_name]
                        if node.attr in class_info.fields:
                            field_type = class_info.fields[node.attr].go_type or ""
                            if field_type == "string":
                                return f"len({self.visit_expr(node)}) > 0"
                            if field_type.startswith("[]") or field_type.startswith("map["):
                                return f"len({self.visit_expr(node)}) > 0"
                            if field_type == "Node" or field_type.startswith("*"):
                                return f"{self.visit_expr(node)} != nil"
            # Look up field type from class
            if isinstance(node.value, ast.Name) and node.value.id == "self" and self.current_class:
                class_info = self.symbols.classes.get(self.current_class)
                if class_info and node.attr in class_info.fields:
                    field_type = class_info.fields[node.attr].go_type or ""
                    if field_type == "Node" or field_type.startswith("*"):
                        return f"{self.visit_expr(node)} != nil"
                    if field_type == "string":
                        return f'{self.visit_expr(node)} != ""'
                    if field_type.startswith("[]") or field_type.startswith("map["):
                        return f"len({self.visit_expr(node)}) > 0"
        # For UnaryOp Not, already handled above
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return f"!({self._emit_bool_expr(node.operand)})"
        # For bitwise AND, convert to != 0
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitAnd):
            return f"({self.visit_expr(node)}) != 0"
        # For getattr calls with bool default, add type assertion
        if self._is_getattr_call(node):
            # Check the default value (third argument)
            if len(node.args) >= 3:
                default = node.args[2]
                if isinstance(default, ast.Constant) and isinstance(default.value, bool):
                    return f"{self.visit_expr(node)}.(bool)"
        # For len() calls in boolean context, compare to 0
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "len":
            return f"{self.visit_expr(node)} > 0"
        # For string methods that return strings, check if non-empty
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            method = node.func.attr
            if method in (
                "strip",
                "lstrip",
                "rstrip",
                "lower",
                "upper",
                "replace",
                "peek",
                "Peek",
                "peek_word",
                "PeekWord",
            ):
                return f'{self.visit_expr(node)} != ""'
        # Default: just emit the expression
        return self.visit_expr(node)

    def visit_expr_Compare(self, node: ast.Compare) -> str:
        """Convert comparison operations."""
        result = self.visit_expr(node.left)
        for op, comparator in zip(node.ops, node.comparators, strict=True):
            # Handle 'in' operator
            if isinstance(op, ast.In):
                return self._emit_in_check(node.left, comparator, negated=False)
            if isinstance(op, ast.NotIn):
                return self._emit_in_check(node.left, comparator, negated=True)
            # Handle Node-typed field compared to None - use _isNilNode() to catch typed nils
            if (
                isinstance(op, ast.Is)
                and isinstance(comparator, ast.Constant)
                and comparator.value is None
            ):
                # Check for self.field of type Node
                if (
                    isinstance(node.left, ast.Attribute)
                    and isinstance(node.left.value, ast.Name)
                    and node.left.value.id == "self"
                    and self.current_class
                ):
                    class_info = self.symbols.classes.get(self.current_class)
                    if class_info and node.left.attr in class_info.fields:
                        field_type = class_info.fields[node.left.attr].go_type or ""
                        if field_type == "Node":
                            return f"_isNilNode({result})"
                # Check for local variable of type Node
                if isinstance(node.left, ast.Name):
                    var_name = self._to_go_var(node.left.id)
                    var_type = self.var_types.get(var_name, "")
                    if var_type == "Node":
                        return f"_isNilNode({result})"
            if (
                isinstance(op, ast.IsNot)
                and isinstance(comparator, ast.Constant)
                and comparator.value is None
            ):
                # Check for self.field of type Node
                if (
                    isinstance(node.left, ast.Attribute)
                    and isinstance(node.left.value, ast.Name)
                    and node.left.value.id == "self"
                    and self.current_class
                ):
                    class_info = self.symbols.classes.get(self.current_class)
                    if class_info and node.left.attr in class_info.fields:
                        field_type = class_info.fields[node.left.attr].go_type or ""
                        if field_type == "Node":
                            return f"!_isNilNode({result})"
                # Check for local variable of type Node
                if isinstance(node.left, ast.Name):
                    var_name = self._to_go_var(node.left.id)
                    var_type = self.var_types.get(var_name, "")
                    if var_type == "Node":
                        return f"!_isNilNode({result})"
            # Handle string subscript compared with single-char string
            right = self._emit_comparand(comparator, node.left)
            op_str = self._cmpop_to_go(op)
            result = f"{result} {op_str} {right}"
        return result

    def _emit_comparand(self, node: ast.expr, left: ast.expr) -> str:
        """Emit right side of comparison, handling byte vs string."""
        # Use rune literals for byte expressions (string subscripts or byte-typed variables)
        # But not for variables that could be strings from method calls
        if self._is_byte_expr(left) and not self._could_be_string_from_method(left):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if len(node.value) == 1:
                    return self._char_to_rune_literal(node.value)
        # Handle comparison to None - use "" only for known string variables
        if isinstance(node, ast.Constant) and node.value is None:
            if isinstance(left, ast.Name):
                var_name = self._to_go_var(left.id)
                var_type = self.var_types.get(var_name, "")
                # For int variables with sentinel value, compare to -1
                if var_type == "int":
                    return "-1"
                # Only convert to "" for string variables, not slices/pointers
                if var_type == "string":
                    return '""'
                # Heuristic: common string variable names from nullable functions
                if left.id in ("c", "ch", "eof_token", "op", "param", "content", "nested", "arg"):
                    return '""'
                # Heuristic: position variables use -1 sentinel
                if (
                    left.id.endswith("_pos")
                    or left.id.endswith("Pos")
                    or left.id in ("bracket_start_pos", "bracketStartPos")
                ):
                    return "-1"
            # Handle attribute access (e.g., l._eof_token, self.op)
            if isinstance(left, ast.Attribute):
                # Look up field type from class
                if (
                    isinstance(left.value, ast.Name)
                    and left.value.id == "self"
                    and self.current_class
                ):
                    class_info = self.symbols.classes.get(self.current_class)
                    if class_info and left.attr in class_info.fields:
                        field_type = class_info.fields[left.attr].go_type or ""
                        if field_type == "string":
                            return '""'
                        if field_type == "int":
                            return "-1"
                # Heuristic: common string field names
                if left.attr in ("_eof_token", "op", "arg", "param"):
                    return '""'
            # Handle method calls that return string (e.g., _lex_peek_case_terminator())
            if isinstance(left, ast.Call) and isinstance(left.func, ast.Attribute):
                method = left.func.attr
                class_name = self._infer_object_class(left.func.value)
                if class_name:
                    class_info = self.symbols.classes.get(class_name)
                    if class_info and method in class_info.methods:
                        ret_type = class_info.methods[method].return_type or ""
                        if ret_type == "string":
                            return '""'
                        if ret_type == "int":
                            return "-1"
        return self.visit_expr(node)

    def _is_getattr_call(self, node: ast.expr) -> bool:
        """Check if expression is a getattr() call."""
        if not isinstance(node, ast.Call):
            return False
        if isinstance(node.func, ast.Name) and node.func.id == "getattr":
            return True
        return False

    def _is_tuple_element_access(self, node: ast.expr) -> bool:
        """Check if expression is accessing a tuple element (subscript on interface{} var)."""
        if not isinstance(node, ast.Subscript):
            return False
        if not isinstance(node.slice, ast.Constant):
            return False
        if isinstance(node.value, ast.Name):
            var_name = self._to_go_var(node.value.id)
            var_type = self.var_types.get(var_name, "")
            if var_type == "interface{}":
                return True

    def _is_node_list_subscript(self, node: ast.expr) -> bool:
        """Check if expression is a subscript on a []Node field (returns Node)."""
        if not isinstance(node, ast.Subscript):
            return False
        if isinstance(node.slice, ast.Slice):
            return False  # Slice returns slice, not element
        # Check for var.field[i] pattern
        if isinstance(node.value, ast.Attribute) and isinstance(node.value.value, ast.Name):
            var_name = self._to_go_var(node.value.value.id)
            var_type = self.var_types.get(var_name, "")
            # Check if this is the type switch variable
            if self._type_switch_var and var_name == self._type_switch_var[0]:
                var_type = self._type_switch_type or ""
            if var_type.startswith("*"):
                class_name = var_type[1:]
                if class_name in self.symbols.classes:
                    class_info = self.symbols.classes[class_name]
                    if node.value.attr in class_info.fields:
                        field_type = class_info.fields[node.value.attr].go_type or ""
                        if field_type == "[]Node":
                            return True
        return False

    def _is_byte_expr(self, node: ast.expr) -> bool:
        """Check if expression evaluates to a byte/rune (e.g., rune slice subscript or byte variable)."""
        # Note: string subscripts are now converted to string() so they're not byte expressions
        # Check if it's a subscript of a rune slice
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            var_name = self._to_go_var(node.value.id)
            var_type = self.var_types.get(var_name, "")
            if var_type == "[]rune":
                return True
        # Check if it's a variable known to be a byte or rune
        if isinstance(node, ast.Name):
            var_name = self._to_go_var(node.id)
            var_type = self.var_types.get(var_name, "")
            if var_type in ("byte", "rune"):
                return True
        return False

    def _could_be_string_from_method(self, node: ast.expr) -> bool:
        """Check if a variable could be a string from method calls like advance/peek.
        Used to avoid treating such variables as runes even if typed from for-range."""
        if not isinstance(node, ast.Name):
            return False
        # Variable 'ch' is commonly reassigned from advance() after being used in for-range
        # Only include specific names known to have this dual-use pattern
        return node.id in ("ch", "dch", "esc", "quote", "closing")

    def _is_int_expr(self, node: ast.expr) -> bool:
        """Check if expression evaluates to an int."""
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, int)
            and not isinstance(node.value, bool)
        ):
            return True
        if isinstance(node, ast.Name):
            var_name = self._to_go_var(node.id)
            var_type = self.var_types.get(var_name, "")
            if var_type == "int":
                return True
        # ord() returns int
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "ord":
            return True
        if isinstance(node, ast.BinOp):
            # Only arithmetic operations (not string concat) yield int
            if isinstance(
                node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
            ):
                # Add can be string concat, so check operands
                if isinstance(node.op, ast.Add):
                    if self._is_string_expr(node.left) or self._is_string_expr(node.right):
                        return False
                return self._is_int_expr(node.left) or self._is_int_expr(node.right)
            # Bitwise ops are always int
            if isinstance(node.op, (ast.BitOr, ast.BitAnd, ast.BitXor, ast.LShift, ast.RShift)):
                return True
        return False

    def _is_string_expr(self, node: ast.expr) -> bool:
        """Check if expression evaluates to a string."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return True
        if isinstance(node, ast.Name):
            var_name = self._to_go_var(node.id)
            var_type = self.var_types.get(var_name, "")
            if var_type == "string":
                return True
        # String concatenation
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            if self._is_string_expr(node.left) or self._is_string_expr(node.right):
                return True
        # String slice (not single-char subscript which is byte)
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
            if self._is_string_subscript(node):
                return True
        # Call that returns string
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id == "_substring":
                    return True
            if isinstance(node.func, ast.Attribute):
                method = node.func.attr
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
                    "encode",
                ):
                    return True
        return False

    def _is_ord_of_byte(self, node: ast.expr) -> bool:
        """Check if node is ord() called on a byte expression or string subscript."""
        if not isinstance(node, ast.Call):
            return False
        if not isinstance(node.func, ast.Name) or node.func.id != "ord":
            return False
        if not node.args:
            return False
        arg = node.args[0]
        # String subscripts give bytes, even though we convert them to string elsewhere
        if self._is_string_subscript(arg):
            return True
        if self._is_byte_expr(arg):
            return True
        if isinstance(arg, ast.Name):
            var_name = self._to_go_var(arg.id)
            var_type = self.var_types.get(var_name, "")
            if var_type in ("byte", "rune"):
                return True
        return False

    def _extract_ord_arg(self, node: ast.Call) -> str:
        """Extract the argument from an ord() call, returning raw byte value for string subscripts."""
        if node.args:
            arg = node.args[0]
            # For string subscripts, return raw s[i] without string() wrapper
            if self._is_string_subscript(arg):
                value = self.visit_expr(arg.value)
                index = self.visit_expr(arg.slice)
                return f"{value}[{index}]"
            return self.visit_expr(arg)
        return "0"

    def _is_string_subscript(self, node: ast.expr) -> bool:
        """Check if node is a string subscript (e.g., s[i] or chars[i][j])."""
        if not isinstance(node, ast.Subscript):
            return False
        # Check for nested subscript: chars[i][j] where chars is []string
        # In this case chars[i] is a string, and chars[i][j] is a byte
        if isinstance(node.value, ast.Subscript):
            inner_var = node.value.value
            if isinstance(inner_var, ast.Name):
                var_name = self._to_go_var(inner_var.id)
                var_type = self.var_types.get(var_name, "")
                # If subscripting into a []string element, the result is a byte
                if var_type == "[]string":
                    return True
                # Heuristic: common names for string slices
                if inner_var.id in (
                    "chars",
                    "text_chars",
                    "name_chars",
                    "delimiter_chars",
                    "content_chars",
                    "pattern_chars",
                ):
                    return True
        # Check if the value being subscripted is likely a string
        # This is heuristic - we check if it's a Name that looks like a string var
        if isinstance(node.value, ast.Name):
            name = node.value.id
            # Check var_types first
            go_name = self._to_go_var(name)
            var_type = self.var_types.get(go_name, "")
            if var_type == "string":
                return True
            # Common string variable names
            if name in (
                "s",
                "text",
                "source",
                "inner",
                "value",
                "char",
                "c",
                "line",
                "name",
                "word",
                "op",
                "delimiter",
                "prefix",
                "suffix",
                "result_str",
                "inner_str",
                "outer_str",
            ):
                return True
            # Check if it ends with common string suffixes
            if name.endswith("_str") or name.endswith("text") or name.endswith("line"):
                return True
        # Check for self.source, self.text, etc.
        if isinstance(node.value, ast.Attribute):
            attr = node.value.attr
            if attr in (
                "source",
                "text",
                "value",
                "line",
                "inner",
                "name",
                "word",
                "pattern",
                "_arith_src",
            ):
                return True
        return False

    def _is_lexer_source_subscript(self, node: ast.Subscript) -> bool:
        """Check if node is self.source[i] access in Lexer/Parser context."""
        if not isinstance(node.value, ast.Attribute):
            return False
        if node.value.attr != "source":
            return False
        # Check if we're in a Lexer or Parser class
        if self.current_class in ("Lexer", "Parser"):
            return True
        return False

    def _is_string_slice(self, node: ast.Subscript) -> bool:
        """Check if node is a string slice (e.g., s[start:end])."""
        if not isinstance(node.slice, ast.Slice):
            return False
        # Check if the value being sliced is likely a string
        if isinstance(node.value, ast.Name):
            name = node.value.id
            go_name = self._to_go_var(name)
            var_type = self.var_types.get(go_name, "")
            if var_type == "string":
                return True
            # Common string variable names
            if name in (
                "s",
                "text",
                "source",
                "inner",
                "value",
                "line",
                "name",
                "word",
                "op",
                "delimiter",
                "prefix",
                "suffix",
            ):
                return True
        if isinstance(node.value, ast.Attribute):
            if node.value.attr in (
                "source",
                "text",
                "value",
                "line",
                "inner",
                "name",
                "word",
                "pattern",
                "_arith_src",
            ):
                return True
        return False

    def _is_lexer_source_slice(self, node: ast.Subscript) -> bool:
        """Check if node is self.source[start:end] in Lexer/Parser context."""
        if not isinstance(node.slice, ast.Slice):
            return False
        if not isinstance(node.value, ast.Attribute):
            return False
        if node.value.attr != "source":
            return False
        if self.current_class in ("Lexer", "Parser"):
            return True
        return False

    def _char_to_rune_literal(self, c: str) -> str:
        """Convert a single character to a Go rune literal."""
        if c == "\n":
            return "'\\n'"
        if c == "\t":
            return "'\\t'"
        if c == "\r":
            return "'\\r'"
        if c == "\\":
            return "'\\\\'"
        if c == "'":
            return "'\\''"
        if c == '"':
            return "'\"'"
        # Handle control characters and non-printable characters
        ord_c = ord(c)
        if ord_c < 32 or ord_c == 127:
            return f"'\\x{ord_c:02x}'"
        if ord_c > 127:
            return f"'\\u{ord_c:04x}'"
        return f"'{c}'"

    def _cmpop_to_go(self, op: ast.cmpop) -> str:
        """Convert Python comparison operator to Go."""
        ops = {
            ast.Eq: "==",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
            ast.Is: "==",
            ast.IsNot: "!=",
        }
        return ops.get(type(op), "/* ? */")

    def _emit_in_check(self, left: ast.expr, container: ast.expr, negated: bool) -> str:
        """Emit Go code for 'x in container' check."""
        left_expr = self.visit_expr(left)
        # String membership - literal string
        if isinstance(container, ast.Constant) and isinstance(container.value, str):
            container_expr = self.visit_expr(container)
            # If left is a byte expression, use ContainsRune
            if self._is_byte_expr(left):
                left_expr = f"rune({left_expr})"
                if negated:
                    return f"!strings.ContainsRune({container_expr}, {left_expr})"
                return f"strings.ContainsRune({container_expr}, {left_expr})"
            # For string left, use Contains
            if negated:
                return f"!strings.Contains({container_expr}, {left_expr})"
            return f"strings.Contains({container_expr}, {left_expr})"
        # String membership - variable with string type
        if isinstance(container, ast.Name):
            var_name = self._to_go_var(container.id)
            var_type = self.var_types.get(var_name, "")
            if var_type == "string":
                container_expr = self.visit_expr(container)
                # If left is a byte expression, use ContainsRune
                if self._is_byte_expr(left):
                    left_expr = f"rune({left_expr})"
                    if negated:
                        return f"!strings.ContainsRune({container_expr}, {left_expr})"
                    return f"strings.ContainsRune({container_expr}, {left_expr})"
                # For string left, use Contains
                if negated:
                    return f"!strings.Contains({container_expr}, {left_expr})"
                return f"strings.Contains({container_expr}, {left_expr})"
        # For other containers, use a helper or inline check
        container_expr = self.visit_expr(container)
        # Check if container is a set (map in Go) - either module-level or parameter
        if isinstance(container, ast.Name):
            name = container.id
            # Module-level sets are uppercase
            is_module_set = name.isupper() or (name.startswith("_") and name[1:].isupper())
            # Check if it's a parameter/variable typed as map[string]struct{}
            var_name = self._to_go_var(name)
            var_type = self.var_types.get(var_name, "")
            is_set_type = var_type.startswith("map[") and var_type.endswith("]struct{}")
            if is_module_set:
                # Module-level sets use map[string]bool - direct access works
                if negated:
                    return f"!{container_expr}[{left_expr}]"
                return f"{container_expr}[{left_expr}]"
            if is_set_type:
                # Parameter/variable sets use map[string]struct{} - need comma ok idiom
                # Create inline check: func() bool { _, ok := m[k]; return ok }()
                if negated:
                    return f"func() bool {{ _, ok := {container_expr}[{left_expr}]; return !ok }}()"
                return f"func() bool {{ _, ok := {container_expr}[{left_expr}]; return ok }}()"
        # Use _containsAny for interface{} slices, _contains for typed slices
        if "[]interface{}" in container_expr:
            func_name = "_containsAny"
        else:
            func_name = "_contains"
        if negated:
            return f"!{func_name}({container_expr}, {left_expr})"
        return f"{func_name}({container_expr}, {left_expr})"

    def visit_expr_BoolOp(self, node: ast.BoolOp) -> str:
        """Convert boolean operations (and/or)."""
        is_and = isinstance(node.op, ast.And)
        op = " && " if is_and else " || "
        # Check for isinstance(x, T) and x.attr pattern
        if is_and and len(node.values) >= 2:
            isinstance_info = self._detect_isinstance_call(node.values[0])
            if isinstance_info:
                var_name, type_name = isinstance_info
                # Check if subsequent operands access attributes on the same variable
                if self._subsequent_ops_use_var(node.values[1:], var_name):
                    return self._emit_isinstance_and_attr(var_name, type_name, node.values[1:])
        # Use _emit_bool_expr for each operand to handle truthiness conversions
        # Parenthesize nested BoolOps with different operators due to precedence
        # In Go, && has higher precedence than ||, so:
        # - Or inside And needs parentheses: a && (b || c)
        # - And inside Or does not: a || b && c is already correct
        values = []
        for v in node.values:
            expr = self._emit_bool_expr(v)
            # If this is an And and the value is an Or BoolOp, wrap in parentheses
            if is_and and isinstance(v, ast.BoolOp) and isinstance(v.op, ast.Or):
                expr = f"({expr})"
            values.append(expr)
        return op.join(values)

    def _detect_isinstance_call(self, node: ast.expr) -> tuple[str, str] | None:
        """Detect isinstance(var, Type) call. Returns (var_name, type_name) or None."""
        if not isinstance(node, ast.Call):
            return None
        if not isinstance(node.func, ast.Name) or node.func.id != "isinstance":
            return None
        if len(node.args) != 2:
            return None
        if not isinstance(node.args[0], ast.Name):
            return None
        if not isinstance(node.args[1], ast.Name):
            return None
        return (node.args[0].id, node.args[1].id)

    def _subsequent_ops_use_var(self, operands: list[ast.expr], var_name: str) -> bool:
        """Check if any operand accesses an attribute on the given variable."""
        for op in operands:
            if isinstance(op, ast.Attribute):
                if isinstance(op.value, ast.Name) and op.value.id == var_name:
                    return True
        return False

    def _emit_isinstance_and_attr(
        self, var_name: str, type_name: str, subsequent_ops: list[ast.expr]
    ) -> str:
        """Emit combined isinstance + attribute access pattern.

        Pattern: isinstance(x, T) and x.attr
        Go: func() bool { t, ok := x.(*T); return ok && t.Attr }()
        """
        go_var = self._to_go_var(var_name)
        # Emit subsequent conditions, replacing var access with casted variable
        casted_var = "t"
        conditions = ["ok"]
        for op in subsequent_ops:
            if (
                isinstance(op, ast.Attribute)
                and isinstance(op.value, ast.Name)
                and op.value.id == var_name
            ):
                # Replace x.attr with t.Attr
                go_attr = self._to_go_field_name(op.attr)
                conditions.append(f"{casted_var}.{go_attr}")
            else:
                # Other condition, emit as-is
                conditions.append(self._emit_bool_expr(op))
        return_expr = " && ".join(conditions)
        return (
            f"func() bool {{ {casted_var}, ok := {go_var}.(*{type_name}); return {return_expr} }}()"
        )

    def visit_expr_IfExp(self, node: ast.IfExp) -> str:
        """Convert ternary expression. Go doesn't have ternary, use helper func."""
        # Check for pattern: arr[idx] if idx < len(arr) else None
        # This requires lazy evaluation to avoid index-out-of-bounds panic
        if self._is_bounds_guarded_subscript(node):
            return self._emit_lazy_ternary(node)
        test = self._emit_bool_expr(node.test)
        body = self.visit_expr(node.body)
        orelse = self.visit_expr(node.orelse)
        # Check if we need to cast for Node interface compatibility
        body_type = self._infer_type_from_expr(node.body)
        orelse_type = self._infer_type_from_expr(node.orelse)
        # If one is Node and other is *SomeNodeSubclass, cast to Node
        if body_type == "Node" and orelse_type.startswith("*"):
            class_name = orelse_type[1:]
            if class_name in self.symbols.classes and self.symbols.classes[class_name].is_node:
                orelse = f"Node({orelse})"
        elif orelse_type == "Node" and body_type.startswith("*"):
            class_name = body_type[1:]
            if class_name in self.symbols.classes and self.symbols.classes[class_name].is_node:
                body = f"Node({body})"
        # Use an inline if helper function
        return f"_ternary({test}, {body}, {orelse})"

    def _is_bounds_guarded_subscript(self, node: ast.IfExp) -> bool:
        """Check if ternary is: arr[idx] if idx < len(arr) else None."""
        # Body must be subscript access
        if not isinstance(node.body, ast.Subscript):
            return False
        # Orelse must be None
        if not (isinstance(node.orelse, ast.Constant) and node.orelse.value is None):
            return False
        # Test must be Compare with single < operator
        if not isinstance(node.test, ast.Compare):
            return False
        if len(node.test.ops) != 1 or not isinstance(node.test.ops[0], ast.Lt):
            return False
        if len(node.test.comparators) != 1:
            return False
        # Right side of compare must be len(arr) where arr matches subscript value
        comparator = node.test.comparators[0]
        if not isinstance(comparator, ast.Call):
            return False
        if not (isinstance(comparator.func, ast.Name) and comparator.func.id == "len"):
            return False
        if len(comparator.args) != 1:
            return False
        # Check arr in len(arr) matches arr in arr[idx]
        len_arg = comparator.args[0]
        subscript_value = node.body.value
        if not self._ast_names_equal(len_arg, subscript_value):
            return False
        # Check idx in idx < len(arr) matches idx in arr[idx]
        left_idx = node.test.left
        subscript_idx = node.body.slice
        return self._ast_names_equal(left_idx, subscript_idx)

    def _ast_names_equal(self, a: ast.expr, b: ast.expr) -> bool:
        """Check if two AST nodes represent the same name/attribute."""
        if isinstance(a, ast.Name) and isinstance(b, ast.Name):
            return a.id == b.id
        if isinstance(a, ast.Attribute) and isinstance(b, ast.Attribute):
            return a.attr == b.attr and self._ast_names_equal(a.value, b.value)
        return False

    def _emit_lazy_ternary(self, node: ast.IfExp) -> str:
        """Emit IIFE for lazy evaluation of bounds-guarded subscript."""
        test = self._emit_bool_expr(node.test)
        body = self.visit_expr(node.body)
        body_type = self._infer_type_from_expr(node.body)
        return f"func() {body_type} {{ if {test} {{ return {body} }}; return nil }}()"

    def visit_expr_Call(self, node: ast.Call) -> str:
        """Convert function/method calls."""
        args = [self.visit_expr(a) for a in node.args]
        args_str = ", ".join(args)
        # Method call
        if isinstance(node.func, ast.Attribute):
            return self._emit_method_call(node)
        # Function call
        if isinstance(node.func, ast.Name):
            return self._emit_func_call(node)
        return f"{self.visit_expr(node.func)}({args_str})"

    def _emit_method_call(self, node: ast.Call) -> str:
        """Emit method call."""
        obj = self.visit_expr(node.func.value)
        method = node.func.attr
        args = [self.visit_expr(a) for a in node.args]
        # Handle keyword arguments and default values for class methods
        class_name = self._infer_object_class(node.func.value)
        if class_name:
            args = self._merge_keyword_args_for_method(class_name, method, args, node.keywords)
            args = self._fill_default_args_for_method(class_name, method, args)
            # Add & when passing slice to pointer-to-slice parameter
            args = self._add_address_of_for_ptr_slice_params(class_name, method, args, node.args)
        args_str = ", ".join(args)
        # Handle Node interface methods - may need type assertion
        if method in ("to_sexp", "kind"):
            # If obj might not be typed as Node, add assertion
            if self._needs_node_assertion(node.func.value):
                go_method = self._snake_to_pascal(method)
                return f"{obj}.(Node).{go_method}()"
        # Handle struct-specific methods called on Node-typed expressions
        obj_type = self._get_expr_element_type(node.func.value)
        if obj_type == "Node" and method not in ("to_sexp", "kind"):
            # Method is not on Node interface - need to find which struct has it
            struct_type = self._find_method_owner(method)
            if struct_type:
                go_method = self._to_go_method_name(method)
                return f"{obj}.({struct_type}).{go_method}({args_str})"
        # Handle Python string/list methods
        if method == "append":
            return self._emit_append(obj, args, node.args)
        method_map = {
            "startswith": lambda o, a: f"strings.HasPrefix({o}, {a[0]})",
            "endswith": lambda o, a: f"strings.HasSuffix({o}, {a[0]})",
            "strip": lambda o, a: f"strings.TrimSpace({o})",
            "lstrip": lambda o, a: f"strings.TrimLeft({o}, {a[0]})"
            if a
            else f'strings.TrimLeft({o}, " \\t\\n\\r\\x0b\\x0c")',
            "rstrip": lambda o, a: f"strings.TrimRight({o}, {a[0]})"
            if a
            else f'strings.TrimRight({o}, " \\t\\n\\r\\x0b\\x0c")',
            "find": lambda o, a: f"strings.Index({o}, {a[0]})",
            "rfind": lambda o, a: f"strings.LastIndex({o}, {a[0]})",
            "replace": lambda o, a: f"strings.ReplaceAll({o}, {a[0]}, {a[1]})",
            "join": self._emit_join,
            "lower": lambda o, a: f"strings.ToLower({o})",
            "upper": lambda o, a: f"strings.ToUpper({o})",
            "isalpha": self._emit_isalpha,
            "isdigit": self._emit_isdigit,
            "isalnum": self._emit_isalnum,
            "isspace": self._emit_isspace,
            "pop": self._emit_pop,
            "extend": self._emit_extend,
            "get": self._emit_dict_get,
            "encode": self._emit_encode,
            "decode": lambda o, a: f"string({o})",
        }
        if method in method_map:
            handler = method_map[method]
            if callable(handler):
                self._current_method_node = node
                result = handler(obj, args)
                self._current_method_node = None
                return result
        # Default: convert to Go method call
        go_method = self._to_go_method_name(method)
        return f"{obj}.{go_method}({args_str})"

    def _emit_append(
        self, obj: str, args: list[str], orig_args: list[ast.expr] | None = None
    ) -> str:
        """Emit append call - Go requires reassignment."""
        arg = args[0]
        obj_type = self.var_types.get(obj, "")
        # Handle pointer-to-slice types - dereference for append
        if obj_type.startswith("*[]"):
            elem_type = obj_type[3:]  # e.g., "*[]Node" -> "Node"
            # If appending interface{} to *[]Node, add type assertion
            if elem_type == "Node" and orig_args:
                arg_type = self._infer_type_from_expr(orig_args[0])
                if arg_type == "interface{}":
                    arg = f"{arg}.(Node)"
            # If appending a byte to a *[]string, convert
            if elem_type == "string":
                if orig_args and self._is_byte_expr(orig_args[0]):
                    arg = f"string({arg})"
            # If appending an int to *[]byte, convert to byte
            if elem_type == "byte" and orig_args:
                if self._is_int_expr(orig_args[0]):
                    arg = f"byte({arg})"
            return f"*{obj} = append(*{obj}, {arg})"
        # If appending interface{} to []Node, add type assertion
        if obj_type == "[]Node" and orig_args:
            arg_type = self._infer_type_from_expr(orig_args[0])
            if arg_type == "interface{}":
                arg = f"{arg}.(Node)"
        # If appending a byte to a string slice, convert
        if obj_type == "[]string":
            if orig_args and self._is_byte_expr(orig_args[0]):
                arg = f"string({arg})"
        # If appending to []byte
        elif obj_type == "[]byte":
            if orig_args and self._is_byte_expr(orig_args[0]):
                pass  # Already a byte, use as-is
            elif orig_args and self._is_ord_of_byte(orig_args[0]):
                # ord() of a byte - extract the byte directly
                arg = self._extract_ord_arg(orig_args[0])
            elif orig_args and self._is_int_expr(orig_args[0]):
                arg = f"byte({arg})"
            elif (
                orig_args
                and isinstance(orig_args[0], ast.Constant)
                and isinstance(orig_args[0].value, str)
            ):
                if len(orig_args[0].value) == 1:
                    arg = self._char_to_rune_literal(orig_args[0].value)
                else:
                    # Multi-character string - use spread operator
                    return f"{obj} = append({obj}, []byte({arg})...)"
            elif orig_args and isinstance(orig_args[0], ast.Name):
                # Variable - check its type
                var_name = self._to_go_var(orig_args[0].id)
                var_type = self.var_types.get(var_name, "")
                if var_type == "string":
                    # String variable appended to []byte - use spread
                    return f"{obj} = append({obj}, []byte({arg})...)"
            elif orig_args and self._is_string_expr(orig_args[0]):
                # String expression (concatenation, slice, etc) - use spread
                return f"{obj} = append({obj}, []byte({arg})...)"
        # If appending string char to []rune
        elif obj_type == "[]rune":
            # Check if arg is a string constant - convert to rune
            if (
                orig_args
                and isinstance(orig_args[0], ast.Constant)
                and isinstance(orig_args[0].value, str)
            ):
                if len(orig_args[0].value) == 1:
                    arg = self._char_to_rune_literal(orig_args[0].value)
        return f"{obj} = append({obj}, {arg})"

    def _emit_pop(self, obj: str, args: list[str]) -> str:
        """Emit pop call - returns last element and removes it.
        For slices: use _pop helper
        For objects with Pop() method (like QuoteState): call the method
        """
        # Check if this is an object with a Pop() method
        obj_type = self.var_types.get(obj, "")
        if obj_type in ("*QuoteState", "QuoteState"):
            return f"{obj}.Pop()"
        return f"_pop(&{obj})"

    def _emit_extend(self, obj: str, args: list[str]) -> str:
        """Emit extend call."""
        return f"{obj} = append({obj}, {args[0]}...)"

    def _emit_join(self, obj: str, args: list[str]) -> str:
        """Emit join call - strings.Join or string() for []rune or []byte."""
        list_arg = args[0]
        # Check if the list argument is a []rune or []byte variable
        list_type = self.var_types.get(list_arg, "")
        if list_type == "[]rune":
            # For []rune with empty separator, just convert to string
            if obj == '""':
                return f"string({list_arg})"
            # For non-empty separator, need to convert runes to strings first
            return f"strings.Join(_runesToStrings({list_arg}), {obj})"
        if list_type == "[]byte":
            # For []byte with empty separator, just convert to string
            if obj == '""':
                return f"string({list_arg})"
            # For non-empty separator, need to convert bytes to strings first
            return f"strings.Join(_bytesToStrings({list_arg}), {obj})"
        return f"strings.Join({list_arg}, {obj})"

    def _emit_encode(self, obj: str, args: list[str]) -> str:
        """Emit encode call - convert string to []byte."""
        # Check if the object is already a byte (from string subscript)
        if hasattr(self, "_current_method_node") and self._current_method_node:
            # _current_method_node is a Call, func is the Attribute, func.value is the object
            if isinstance(self._current_method_node.func, ast.Attribute):
                value_node = self._current_method_node.func.value
                if self._is_byte_expr(value_node):
                    # Already a byte, just wrap in slice for extend compatibility
                    return f"[]byte{{{obj}}}"
        return f"[]byte({obj})"

    def _emit_isalpha(self, obj: str, args: list[str]) -> str:
        """Emit isalpha check."""
        # Handle both string and byte/rune cases
        return f"unicode.IsLetter(_runeFromChar({obj}))"

    def _emit_isdigit(self, obj: str, args: list[str]) -> str:
        """Emit isdigit check - true if non-empty and all characters are digits."""
        return f"_strIsDigits({obj})"

    def _emit_isalnum(self, obj: str, args: list[str]) -> str:
        """Emit isalnum check."""
        return f"(unicode.IsLetter(_runeFromChar({obj})) || unicode.IsDigit(_runeFromChar({obj})))"

    def _emit_isspace(self, obj: str, args: list[str]) -> str:
        """Emit isspace check - true if non-empty and all whitespace."""
        return f'(len({obj}) > 0 && strings.TrimSpace({obj}) == "")'

    def _emit_dict_get(self, obj: str, args: list[str]) -> str:
        """Emit dict.get() call."""
        key = args[0]
        # Special case: ANSI_C_ESCAPES uses rune keys
        if obj in ("ANSICEscapes", "ANSI_C_ESCAPES", "AnsiCEscapes"):
            obj = "ANSICEscapes"  # Use the manually emitted name
            key = f"_strToRune({key})"
        if len(args) > 1:
            default = args[1]
            return f"_mapGet({obj}, {key}, {default})"
        return f"{obj}[{key}]"

    def _emit_func_call(self, node: ast.Call) -> str:
        """Emit function call."""
        name = node.func.id
        args = []
        for i, a in enumerate(node.args):
            arg_str = self.visit_expr(a)
            # Convert byte to string for functions that expect string parameters
            if self._func_expects_string_param(name, i) and self._is_byte_expr(a):
                arg_str = f"string({arg_str})"
            args.append(arg_str)
        # Handle keyword arguments
        args = self._merge_keyword_args(name, args, node.keywords)
        # Add default values for missing parameters
        args = self._fill_default_args(name, args)
        args_str = ", ".join(args)
        # Handle builtins
        builtin_map = {
            "len": lambda a: self._emit_len(node.args[0], a[0]),
            "str": lambda a: f"fmt.Sprint({a[0]})" if a else '""',
            "int": lambda a: f"_mustAtoi({a[0]})" if len(a) == 1 else f"_parseInt({a[0]}, {a[1]})",
            "bool": lambda a: f"({a[0]} != 0)" if a else "false",
            "ord": self._emit_ord,
            "chr": lambda a: f"string(rune({a[0]}))",
            "isinstance": self._emit_isinstance,
            "getattr": self._emit_getattr,
            "range": lambda a: "/* range */",
            "list": self._emit_list,
            "set": lambda a: f"_makeSet({a[0]})" if a else "make(map[interface{}]struct{})",
            "max": lambda a: f"_max({', '.join(a)})",
            "min": lambda a: f"_min({', '.join(a)})",
            "bytearray": lambda a: "[]byte{}",
        }
        if name in builtin_map:
            self._current_call_node = node
            result = builtin_map[name](args)
            self._current_call_node = None
            return result
        # Handle helper functions
        if name == "_substring":
            # Use helper function with bounds checking (Python slicing is safe)
            return f"_Substring({args[0]}, {args[1]}, {args[2]})"
        if name == "_sublist":
            return f"{args[0]}[{args[1]}:{args[2]}]"
        if name == "_repeat_str":
            return f"strings.Repeat({args[0]}, {args[1]})"
        if name == "_starts_with_at":
            return f"strings.HasPrefix({args[0]}[{args[1]}:], {args[2]})"
        # Handle local functions that are translated to helpers
        if name == "format_arith_val":
            return f"_FormatArithVal({args_str})"
        # Handle class constructors
        if name in self.symbols.classes:
            # Fix empty list types based on constructor parameter types
            class_info = self.symbols.classes[name]
            if "__init__" in class_info.methods:
                init_info = class_info.methods["__init__"]
                fixed_args = []
                for i, arg in enumerate(args):
                    if arg == "[]interface{}{}" and i < len(init_info.params):
                        param_type = init_info.params[i].go_type
                        if param_type and param_type.startswith("[]"):
                            arg = f"{param_type}{{}}"
                    fixed_args.append(arg)
                args_str = ", ".join(fixed_args)
            return f"New{name}({args_str})"
        # Default function call
        go_name = self._to_go_func_name(name)
        return f"{go_name}({args_str})"

    def _emit_list(self, args: list[str]) -> str:
        """Emit list() call - create a copy of a slice."""
        if not args:
            return "[]interface{}{}"
        # Try to infer the slice type from the argument
        if hasattr(self, "_current_call_node") and self._current_call_node:
            call_args = self._current_call_node.args
            if call_args:
                arg_type = self._infer_expr_type(call_args[0])
                if arg_type and arg_type.startswith("[]"):
                    return f"append({arg_type}{{}}, {args[0]}...)"
        return f"append([]interface{{}}{{}}, {args[0]}...)"

    def _emit_len(self, arg_node: ast.expr, arg_str: str) -> str:
        """Emit len() call - use _runeLen for strings, len() otherwise."""
        # Check if the argument is a string expression
        if self._is_string_expr(arg_node):
            # For Lexer/Parser Source, use len(Source_runes) for O(1) access
            if isinstance(arg_node, ast.Attribute):
                if arg_node.attr == "source" and self.current_class in ("Lexer", "Parser"):
                    receiver = self.current_class[0].lower()
                    return f"len({receiver}.Source_runes)"
            return f"_runeLen({arg_str})"
        return f"len({arg_str})"

    def _is_string_expr(self, node: ast.expr) -> bool:
        """Check if node evaluates to a string type."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return True
        if isinstance(node, ast.Name):
            go_name = self._to_go_var(node.id)
            var_type = self.var_types.get(go_name, "")
            if var_type == "string":
                return True
            # Common string variable names
            if node.id in (
                "s",
                "text",
                "source",
                "inner",
                "value",
                "char",
                "c",
                "line",
                "name",
                "word",
                "op",
                "delimiter",
                "prefix",
                "suffix",
            ):
                return True
        if isinstance(node, ast.Attribute):
            if node.attr in (
                "source",
                "text",
                "value",
                "line",
                "inner",
                "name",
                "word",
                "pattern",
                "_arith_src",
            ):
                return True
        # String method calls return strings
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            method = node.func.attr
            if method in (
                "strip",
                "lstrip",
                "rstrip",
                "lower",
                "upper",
                "replace",
                "join",
                "format",
                "split",
            ):
                return True
        return False

    def _emit_ord(self, args: list[str]) -> str:
        """Emit ord() call - get code point of a character.

        Python's ord() always returns int, so we return int.
        """
        if not args:
            return "0"
        arg = args[0]
        # Check if the current call arg is already a byte/rune expression
        if hasattr(self, "_current_call_node") and self._current_call_node:
            call_args = self._current_call_node.args
            if call_args:
                # If it's a string subscript, emit as int(s[i]) directly
                # (bypass the string() conversion we normally do)
                if self._is_string_subscript(call_args[0]):
                    # Get raw subscript without string() wrapper
                    value = self.visit_expr(call_args[0].value)
                    index = self.visit_expr(call_args[0].slice)
                    return f"int({value}[{index}])"
                if self._is_byte_expr(call_args[0]):
                    return f"int({arg})"  # Already a byte, convert to int
            # Also check if it's a variable with byte type
            if call_args and isinstance(call_args[0], ast.Name):
                var_name = self._to_go_var(call_args[0].id)
                var_type = self.var_types.get(var_name, "")
                if var_type in ("byte", "rune"):
                    return f"int({arg})"  # Already a byte/rune, convert to int
        return f"int(rune({arg}[0]))"

    def _emit_isinstance(self, args: list[str]) -> str:
        """Emit isinstance check using type assertion."""
        if not hasattr(self, "_current_call_node") or not self._current_call_node:
            raise NotImplementedError("isinstance: no call node context")
        call_node = self._current_call_node
        if len(call_node.args) < 2:
            raise NotImplementedError("isinstance: need 2 args")
        obj = args[0]
        type_arg = call_node.args[1]
        # Extract type names from AST
        type_names: list[str] = []
        if isinstance(type_arg, ast.Name):
            type_names.append(type_arg.id)
        elif isinstance(type_arg, ast.Tuple):
            for elt in type_arg.elts:
                if isinstance(elt, ast.Name):
                    type_names.append(elt.id)
        if not type_names:
            raise NotImplementedError(f"isinstance: unsupported type pattern {ast.dump(type_arg)}")
        # Generate Go type assertion(s)
        if len(type_names) == 1:
            return f"func() bool {{ _, ok := {obj}.(*{type_names[0]}); return ok }}()"
        # Multiple types - check each in turn
        checks = []
        for i, tn in enumerate(type_names):
            var = f"ok{i + 1}"
            checks.append(f"_, {var} := {obj}.(*{tn})")
        return_expr = " || ".join(f"ok{i + 1}" for i in range(len(type_names)))
        return f"func() bool {{ {'; '.join(checks)}; return {return_expr} }}()"

    def _detect_isinstance_if(self, test: ast.expr) -> tuple[str, str] | None:
        """Detect if test is `isinstance(var, Type)`. Returns (var_name, type_name) or None."""
        if not isinstance(test, ast.Call):
            return None
        if not isinstance(test.func, ast.Name) or test.func.id != "isinstance":
            return None
        if len(test.args) != 2:
            return None
        var_arg, type_arg = test.args
        if not isinstance(var_arg, ast.Name):
            return None
        if not isinstance(type_arg, ast.Name):
            return None  # Only single type for now, not tuples
        return (var_arg.id, type_arg.id)

    def _collect_isinstance_chain(
        self, stmts: list[ast.stmt], start_idx: int
    ) -> list[tuple[ast.If, str, str]]:
        """Collect consecutive `if isinstance(same_var, T):` statements.
        Returns list of (stmt, var_name, type_name) tuples."""
        result: list[tuple[ast.If, str, str]] = []
        if start_idx >= len(stmts):
            return result
        first_stmt = stmts[start_idx]
        if not isinstance(first_stmt, ast.If):
            return result
        first_info = self._detect_isinstance_if(first_stmt.test)
        if not first_info:
            return result
        target_var = first_info[0]
        result.append((first_stmt, first_info[0], first_info[1]))
        # Look for more isinstance checks on the same variable
        for i in range(start_idx + 1, len(stmts)):
            stmt = stmts[i]
            if not isinstance(stmt, ast.If):
                break
            info = self._detect_isinstance_if(stmt.test)
            if not info or info[0] != target_var:
                break
            # Must not have elif/else - only simple if isinstance(...):
            if stmt.orelse:
                break
            result.append((stmt, info[0], info[1]))
        return result

    def _detect_assign_check_return(
        self, stmts: list[ast.stmt], idx: int
    ) -> tuple[str, ast.Call, str] | None:
        """Detect pattern: result = self.method(); if result: return result
        Returns (var_name, method_call, return_type) or None.
        This pattern causes typed-nil issues when method returns concrete type
        but variable is interface type."""
        if idx + 1 >= len(stmts):
            return None
        # First statement must be: result = self.method()
        assign = stmts[idx]
        if not isinstance(assign, ast.Assign):
            return None
        if len(assign.targets) != 1:
            return None
        target = assign.targets[0]
        if not isinstance(target, ast.Name):
            return None
        var_name = target.id
        # RHS must be a method call
        if not isinstance(assign.value, ast.Call):
            return None
        call = assign.value
        if not isinstance(call.func, ast.Attribute):
            return None
        if not isinstance(call.func.value, ast.Name) or call.func.value.id != "self":
            return None
        method_name = call.func.attr
        # Check if this method returns a concrete pointer type
        return_type = self._get_method_return_type(method_name)
        if not return_type or not return_type.startswith("*"):
            return None
        # Variable should be interface type (Node) or untyped (for assign-check-return pattern)
        # The pattern transformation avoids typed-nil issues and unused variable issues
        go_var = self._to_go_var(var_name)
        var_type = self.var_types.get(go_var, "")
        # Accept if type is Node, empty (untyped), or interface{}
        if var_type not in ("Node", "", "interface{}"):
            return None
        # Second statement must be: if result: return result
        # OR: if result is not None: return result
        if_stmt = stmts[idx + 1]
        if not isinstance(if_stmt, ast.If):
            return None
        # Test must be just the variable name (truthy check)
        # OR a comparison: result is not None
        test_var_name = None
        if isinstance(if_stmt.test, ast.Name):
            test_var_name = if_stmt.test.id
        elif isinstance(if_stmt.test, ast.Compare):
            # Check for: result is not None
            cmp = if_stmt.test
            if (
                isinstance(cmp.left, ast.Name)
                and len(cmp.ops) == 1
                and isinstance(cmp.ops[0], ast.IsNot)
                and len(cmp.comparators) == 1
                and isinstance(cmp.comparators[0], ast.Constant)
                and cmp.comparators[0].value is None
            ):
                test_var_name = cmp.left.id
        if test_var_name != var_name:
            return None
        # Body must be single return statement returning the same variable
        if len(if_stmt.body) != 1:
            return None
        ret = if_stmt.body[0]
        if not isinstance(ret, ast.Return) or not isinstance(ret.value, ast.Name):
            return None
        if ret.value.id != var_name:
            return None
        # Must not have else clause
        if if_stmt.orelse:
            return None
        return (var_name, call, return_type)

    def _get_method_return_type(self, method_name: str) -> str | None:
        """Get the return type of a method if it's a concrete pointer type."""
        # Parser methods that return concrete types
        parser_methods = {
            "parse_brace_group": "*BraceGroup",
            "parse_subshell": "*Subshell",
            "parse_if": "*If",
            "parse_while": "*While",
            "parse_until": "*Until",
            "parse_for": "*For",
            "parse_select": "*Select",
            "parse_case": "*Case",
            "parse_function": "*Function",
            "parse_coproc": "*Coproc",
            "parse_arithmetic_command": "*ArithmeticCommand",
            "parse_conditional_expr": "*ConditionalExpr",
            "parse_comment": "*Comment",
        }
        return parser_methods.get(method_name)

    def _emit_assign_check_return(self, var_name: str, method_call: ast.Call, return_type: str):
        """Emit pattern: if tmp := method(); tmp != nil { return tmp }
        This avoids typed-nil interface issues."""
        go_var = self._to_go_var(var_name)
        # Generate the method call expression
        call_expr = self.visit_expr(method_call)
        # Use a short temp variable name
        tmp_var = go_var[0].lower() + "Tmp"
        if tmp_var == go_var:
            tmp_var = go_var + "Tmp"
        self.emit(f"if {tmp_var} := {call_expr}; {tmp_var} != nil {{")
        self.indent += 1
        self.emit(f"return {tmp_var}")
        self.indent -= 1
        self.emit("}")

    def _emit_type_switch(self, var_name: str, cases: list[tuple[ast.If, str, str]]):
        """Emit Go type switch for isinstance chain."""
        go_var = self._to_go_var(var_name)
        # Use short switch variable name (e.g., node -> n)
        switch_var = go_var[0].lower()
        if switch_var == go_var:
            switch_var = go_var + "T"  # Avoid shadowing
        self.emit(f"switch {switch_var} := {go_var}.(type) {{")
        for stmt, _, type_name in cases:
            # Convert Python type name to Go type (e.g., str -> string)
            go_type = self.TYPE_MAP.get(type_name, type_name)
            # Primitives don't get * prefix, class types do
            if type_name in self.TYPE_MAP:
                case_type = go_type
            else:
                case_type = f"*{go_type}"
            self.emit(f"case {case_type}:")
            self.indent += 1
            # Set up type switch context for variable rewriting
            old_switch_var = self._type_switch_var
            old_switch_type = self._type_switch_type
            self._type_switch_var = (go_var, switch_var)
            self._type_switch_type = case_type
            # Track narrowed type for field access
            old_var_type = self.var_types.get(switch_var)
            self.var_types[switch_var] = case_type
            try:
                for s in stmt.body:
                    self._emit_stmt(s)
            except NotImplementedError:
                self.emit('panic("TODO: incomplete implementation")')
            # Restore context
            self._type_switch_var = old_switch_var
            self._type_switch_type = old_switch_type
            if old_var_type is not None:
                self.var_types[switch_var] = old_var_type
            else:
                self.var_types.pop(switch_var, None)
            self.indent -= 1
        # Check if the last isinstance has an else branch that doesn't contain more isinstance checks
        # This handles patterns like: if isinstance(body, str): ... else: body.to_sexp()
        last_stmt = cases[-1][0]
        if last_stmt.orelse and not self._else_contains_isinstance(last_stmt.orelse, cases[0][1]):
            self.emit("default:")
            self.indent += 1
            # In the default case, the switch variable still holds the value but with interface{} type
            old_switch_var = self._type_switch_var
            self._type_switch_var = (go_var, switch_var)
            try:
                for s in last_stmt.orelse:
                    self._emit_stmt(s)
            except NotImplementedError:
                self.emit('panic("TODO: incomplete implementation")')
            self._type_switch_var = old_switch_var
            self.indent -= 1
        self.emit("}")

    def _else_contains_isinstance(self, stmts: list[ast.stmt], var_name: str) -> bool:
        """Check if else branch contains isinstance checks on the same variable."""
        for stmt in stmts:
            if isinstance(stmt, ast.If):
                info = self._detect_isinstance_if(stmt.test)
                if info and info[0] == var_name:
                    return True
                # Recursively check elif/else branches
                if stmt.orelse and self._else_contains_isinstance(stmt.orelse, var_name):
                    return True
        return False

    def _emit_getattr(self, args: list[str]) -> str:
        """Emit getattr call."""
        obj = args[0]
        attr = args[1]
        if len(args) > 2:
            default = args[2]
            return f"_getattr({obj}, {attr}, {default})"
        return f"_getattr({obj}, {attr}, nil)"

    def visit_expr_List(self, node: ast.List) -> str:
        """Convert list literals."""
        if not node.elts:
            # Empty list - try to infer type from context, fallback to interface{}
            return "[]interface{}{}"
        # Infer element type from first element
        first = node.elts[0]
        elem_type = self._infer_literal_elem_type(first)
        elements = ", ".join(self.visit_expr(e) for e in node.elts)
        return f"[]{elem_type}{{{elements}}}"

    def _infer_literal_elem_type(self, node: ast.expr) -> str:
        """Infer Go type from a literal element."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return "string"
            if isinstance(node.value, int):
                return "int"
            if isinstance(node.value, bool):
                return "bool"
        # Handle string concatenation (BinOp with Add involving strings)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left_type = self._infer_literal_elem_type(node.left)
            right_type = self._infer_literal_elem_type(node.right)
            if left_type == "string" or right_type == "string":
                return "string"
        # Handle class constructor calls
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            class_name = node.func.id
            if class_name in self.symbols.classes:
                info = self.symbols.classes[class_name]
                if info.is_node:
                    return "Node"
                return "*" + class_name
        # Handle variable references - look up type
        if isinstance(node, ast.Name):
            var_name = self._to_go_var(node.id)
            var_type = self.var_types.get(var_name, "")
            if var_type and var_type != "interface{}":
                return var_type
        return "interface{}"

    def visit_expr_Dict(self, node: ast.Dict) -> str:
        """Convert dict literals."""
        if not node.keys:
            return "map[string]interface{}{}"
        pairs = []
        for k, v in zip(node.keys, node.values, strict=True):
            pairs.append(f"{self.visit_expr(k)}: {self.visit_expr(v)}")
        # Use map[string]string if all values are string constants
        if node.values and all(
            isinstance(v, ast.Constant) and isinstance(v.value, str) for v in node.values
        ):
            return "map[string]string{" + ", ".join(pairs) + "}"
        return "map[string]interface{}{" + ", ".join(pairs) + "}"

    def visit_expr_Tuple(self, node: ast.Tuple) -> str:
        """Convert tuple literals (as slices in Go)."""
        elements = ", ".join(self.visit_expr(e) for e in node.elts)
        return f"[]interface{{}}{{{elements}}}"

    def visit_expr_Set(self, node: ast.Set) -> str:
        """Convert set literals."""
        if not node.elts:
            return "make(map[interface{}]struct{})"
        # Check if all elements are string constants - use map[string] for type safety
        all_strings = all(
            isinstance(e, ast.Constant) and isinstance(e.value, str) for e in node.elts
        )
        key_type = "string" if all_strings else "interface{}"
        elements = ", ".join(f"{self.visit_expr(e)}: {{}}" for e in node.elts)
        return f"map[{key_type}]struct{{}}{{{elements}}}"

    def visit_expr_JoinedStr(self, node: ast.JoinedStr) -> str:
        """Convert f-strings to fmt.Sprintf."""
        format_parts = []
        args = []
        for part in node.values:
            if isinstance(part, ast.Constant):
                # Escape % for fmt.Sprintf
                format_parts.append(part.value.replace("%", "%%"))
            elif isinstance(part, ast.FormattedValue):
                format_parts.append("%v")
                args.append(self.visit_expr(part.value))
        format_str = "".join(format_parts).replace('"', '\\"').replace("\n", "\\n")
        if args:
            return f'fmt.Sprintf("{format_str}", {", ".join(args)})'
        return f'"{format_str}"'

    def visit_expr_Lambda(self, node: ast.Lambda) -> str:
        """Convert lambda expressions."""
        params = [self._to_go_param_name(a.arg) for a in node.args.args]
        params_str = ", ".join(f"{p} interface{{}}" for p in params)
        body = self.visit_expr(node.body)
        return f"func({params_str}) interface{{}} {{ return {body} }}"


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
