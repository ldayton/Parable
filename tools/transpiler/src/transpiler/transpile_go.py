#!/usr/bin/env python3
"""Transpile parable.py's restricted Python subset to Go."""

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path


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
    }

    def __init__(self):
        self.indent = 0
        self.output: list[str] = []
        self.symbols = SymbolTable()
        self.tree: ast.Module | None = None
        self.current_class: str | None = None
        self.declared_vars: set[str] = set()  # Track declared local variables per function

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

    def _extract_func_info(
        self, node: ast.FunctionDef, is_method: bool = False
    ) -> FuncInfo:
        """Extract function signature information."""
        params = []
        for arg in node.args.args:
            if arg.arg == "self":
                continue
            py_type = self._annotation_to_str(arg.annotation) if arg.annotation else ""
            go_type = self._py_type_to_go(py_type) if py_type else "interface{}"
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
            return_type = self._py_type_to_go(py_return)
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

    def _py_type_to_go(self, py_type: str) -> str:
        """Convert Python type string to Go type."""
        if not py_type:
            return ""
        # Handle simple types
        if py_type in self.TYPE_MAP:
            return self.TYPE_MAP[py_type]
        # Handle bare "list" without type args
        if py_type == "list":
            return "[]interface{}"
        # Handle list[X]
        if py_type.startswith("list["):
            inner = py_type[5:-1]
            return "[]" + self._py_type_to_go(inner)
        # Handle dict[K, V]
        if py_type.startswith("dict["):
            inner = py_type[5:-1]
            parts = self._split_type_args(inner)
            if len(parts) == 2:
                return f"map[{self._py_type_to_go(parts[0])}]{self._py_type_to_go(parts[1])}"
        # Handle tuple[...]
        if py_type.startswith("tuple["):
            inner = py_type[6:-1]
            parts = self._split_type_args(inner)
            # For now, tuples become structs or multiple returns - handle later
            return "interface{}"
        # Handle X | None -> *X or X (use zero value)
        if " | None" in py_type or " | " in py_type:
            # Strip None from union
            parts = [p.strip() for p in py_type.split("|")]
            parts = [p for p in parts if p != "None"]
            if len(parts) == 1:
                return self._py_type_to_go(parts[0])
            return "interface{}"
        # Handle class names (Node subclasses become interface, others become struct)
        if py_type in self.symbols.classes:
            info = self.symbols.classes[py_type]
            if info.is_node or py_type == "Node":
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
        # Bare dict/set without type args
        if py_type == "dict":
            return "map[string]interface{}"
        if py_type == "set":
            return "map[interface{}]struct{}"
        # Handle set[X]
        if py_type.startswith("set["):
            inner = py_type[4:-1]
            return f"map[{self._py_type_to_go(inner)}]struct{{}}"
        return py_type

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
        return "interface{}"

    # ========== Code Emission ==========

    def visit_Module(self, node: ast.Module):
        """Emit package declaration and all definitions."""
        self.emit("package parable")
        self.emit("")
        # Emit imports
        self._emit_imports()
        # Emit error types first
        self._emit_error_types()
        # Emit Node interface
        self._emit_node_interface()
        # Emit all structs
        self._emit_all_structs()
        # Emit helper functions
        self._emit_helper_functions(node)
        # Emit methods for all classes
        self._emit_all_methods(node)

    def _emit_imports(self):
        """Emit Go import statements."""
        self.emit("import (")
        self.indent += 1
        self.emit('"fmt"')
        self.emit('"strings"')
        self.emit('"strconv"')
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
        self.emit('return fmt.Sprintf("Parse error at line %d, position %d: %s", e.Line, e.Pos, e.Message)')
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
        # MatchedPairError
        self.emit("// MatchedPairError is raised when a matched pair is unclosed at EOF.")
        self.emit("type MatchedPairError struct {")
        self.indent += 1
        self.emit("ParseError")
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
        # Character helper - get rune from string
        self.emit("func _runeAt(s string, i int) rune {")
        self.indent += 1
        self.emit("if i < len(s) {")
        self.indent += 1
        self.emit("return rune(s[i])")
        self.indent -= 1
        self.emit("}")
        self.emit("return 0")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # String to rune (first char)
        self.emit("func _strToRune(s string) rune {")
        self.indent += 1
        self.emit("if len(s) > 0 {")
        self.indent += 1
        self.emit("return rune(s[0])")
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
        self.emit("if len(v) > 0 {")
        self.indent += 1
        self.emit("return rune(v[0])")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("return 0")
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
        if info.constants and not info.fields and not any(
            m for m in info.methods if m != "__init__" or info.methods[m].params
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
            go_name = self._to_go_field_name(field_name)
            go_type = field_info.go_type or "interface{}"
            self.emit(f"{go_name} {go_type}")
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

    def _emit_helper_functions(self, tree: ast.Module):
        """Emit module-level helper functions."""
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                self._emit_function(node)

    # Functions that require duck typing (Part 6d) or have complex scoping - skip body for now
    SKIP_BODY_FUNCTIONS = {
        # Duck typing (Part 6d)
        "_format_cond_body",
        "_format_cond_value",
        "_collect_cmdsubs",
        "_collect_assignments",
        "_starts_with_subshell",
        "_format_cmdsub_node",
        "_format_redirect",
        "_format_heredoc_body",
        # Complex scoping (need variable hoisting)
        "_skip_heredoc",
        "_skip_double_quoted",
        "_find_heredoc_content_end",
        "_collapse_whitespace",
        "_normalize_heredoc_delimiter",
        "_skip_matched_pair",
        "_skip_single_quoted",
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
        # Skip body for complex functions
        if node.name in self.SKIP_BODY_FUNCTIONS:
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
        go_name = self._to_go_method_name(node.name)
        params_str = self._format_params(func_info.params)
        return_str = func_info.return_type
        receiver = class_info.name[0].lower()
        if return_str:
            self.emit(f"func ({receiver} *{class_info.name}) {go_name}({params_str}) {return_str} {{")
        else:
            self.emit(f"func ({receiver} *{class_info.name}) {go_name}({params_str}) {{")
        self.indent += 1
        self._emit_body(node.body, func_info)
        self.indent -= 1
        self.emit("}")
        self.emit("")

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
        self.var_types: dict[str, str] = {}  # Inferred types for local vars
        if func_info:
            for p in func_info.params:
                go_name = self._to_go_param_name(p.name)
                self.declared_vars.add(go_name)
                self.var_types[go_name] = p.go_type
        # Pre-pass: analyze variable types from usage
        self._analyze_var_types(stmts)
        # Emit all statements
        emitted_any = False
        for stmt in stmts:
            # Skip docstrings
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                if isinstance(stmt.value.value, str):
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
                self.emit(f'panic("TODO: empty body")')

    def _analyze_var_types(self, stmts: list[ast.stmt]):
        """Pre-analyze statements to infer variable types from usage."""
        for stmt in stmts:
            self._analyze_stmt_var_types(stmt)

    def _analyze_stmt_var_types(self, stmt: ast.stmt):
        """Analyze a statement for variable type info."""
        if isinstance(stmt, ast.Assign):
            if len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                var_name = self._snake_to_camel(stmt.targets[0].id)
                var_name = self._safe_go_name(var_name)
                # If assigning a list, track its type
                if isinstance(stmt.value, ast.List):
                    if not stmt.value.elts:
                        self.var_types[var_name] = "[]interface{}"  # default for empty
                    else:
                        # Infer from first element
                        elem_type = self._infer_literal_elem_type(stmt.value.elts[0])
                        self.var_types[var_name] = f"[]{elem_type}"
                # If assigning from string subscript, it's a byte
                elif self._is_string_subscript(stmt.value):
                    self.var_types[var_name] = "byte"
        # Look for append calls to infer list element types
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
            if isinstance(call.func, ast.Attribute) and call.func.attr == "append":
                if isinstance(call.func.value, ast.Name) and call.args:
                    var_name = self._snake_to_camel(call.func.value.id)
                    var_name = self._safe_go_name(var_name)
                    elem_type = self._infer_elem_type_from_arg(call.args[0])
                    if elem_type and var_name in self.var_types:
                        if self.var_types[var_name] == "[]interface{}":
                            self.var_types[var_name] = f"[]{elem_type}"
        # Recurse into control flow
        if isinstance(stmt, ast.If):
            self._analyze_var_types(stmt.body)
            self._analyze_var_types(stmt.orelse)
        elif isinstance(stmt, ast.While) or isinstance(stmt, ast.For):
            self._analyze_var_types(stmt.body)

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
            var_name = self._snake_to_camel(node.id)
            var_name = self._safe_go_name(var_name)
            if var_name in self.var_types:
                return self.var_types[var_name]
            # Common string variable names
            if node.id in ("s", "c", "char", "text", "value", "line"):
                return "string"
        # If it's a string subscript, it's a byte/rune
        if isinstance(node, ast.Subscript):
            if self._is_string_subscript(node):
                return "byte"
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
                    field = self._to_go_field_name(target.attr)
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
            target_str = self.visit_expr(target)
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
                    self.emit(f"{target_str} := {value}")
                    return
            value = self.visit_expr(stmt.value)
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
        all_new = True
        for elt in target.elts:
            name = self.visit_expr(elt)
            target_names.append(name)
            if isinstance(elt, ast.Name):
                camel = self._snake_to_camel(elt.id)
                camel = self._safe_go_name(camel)
                if camel in self.declared_vars:
                    all_new = False
                else:
                    self.declared_vars.add(camel)
            else:
                all_new = False
        # Handle value side
        if isinstance(value, ast.Tuple):
            # a, b = x, y
            value_exprs = [self.visit_expr(v) for v in value.elts]
            if all_new:
                self.emit(f"{', '.join(target_names)} := {', '.join(value_exprs)}")
            else:
                self.emit(f"{', '.join(target_names)} = {', '.join(value_exprs)}")
        elif isinstance(value, ast.Call):
            # a, b = func()  - function returns multiple values
            value_expr = self.visit_expr(value)
            if all_new:
                self.emit(f"{', '.join(target_names)} := {value_expr}")
            else:
                self.emit(f"{', '.join(target_names)} = {value_expr}")
        else:
            # Other cases - need to unpack at runtime
            raise NotImplementedError(f"Tuple unpacking from {type(value).__name__}")

    def _emit_stmt_AnnAssign(self, stmt: ast.AnnAssign):
        """Emit annotated assignment."""
        if stmt.value:
            target = self.visit_expr(stmt.target)
            value = self.visit_expr(stmt.value)
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
            value = self.visit_expr(stmt.value)
            self.emit(f"return {value}")
        else:
            self.emit("return")

    def _emit_stmt_If(self, stmt: ast.If):
        """Emit if statement."""
        self._emit_if_chain(stmt, is_first=True)

    def _emit_if_chain(self, stmt: ast.If, is_first: bool):
        """Emit if/elif/else chain."""
        test = self._emit_bool_expr(stmt.test)
        if is_first:
            self.emit(f"if {test} {{")
        else:
            self.emit_raw("\t" * self.indent + f"}} else if {test} {{")
        self.indent += 1
        try:
            for s in stmt.body:
                self._emit_stmt(s)
        except NotImplementedError:
            self.emit('panic("TODO: incomplete implementation")')
        self.indent -= 1
        if stmt.orelse:
            if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                # elif - continue chain
                self._emit_if_chain(stmt.orelse[0], is_first=False)
            else:
                # else
                self.emit_raw("\t" * self.indent + "} else {")
                self.indent += 1
                try:
                    for s in stmt.orelse:
                        self._emit_stmt(s)
                except NotImplementedError:
                    self.emit('panic("TODO: incomplete implementation")')
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

    def _emit_stmt_Raise(self, stmt: ast.Raise):
        """Emit raise as panic."""
        if stmt.exc:
            exc = self.visit_expr(stmt.exc)
            self.emit(f"panic({exc})")
        else:
            self.emit("panic(nil)")

    def _emit_stmt_Try(self, stmt: ast.Try):
        """Emit try/except as defer/recover pattern."""
        raise NotImplementedError("try/except")

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
            return f'"{escaped}"'
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
        # Convert to camelCase and handle reserved words
        camel = self._snake_to_camel(name)
        return self._safe_go_name(camel)

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
        return f"{value}.{attr}"

    def _is_interface_method(self, value: ast.expr, attr: str) -> bool:
        """Check if attribute is a method on an interface type."""
        # Node interface methods
        if attr in ("kind", "to_sexp"):
            # Check if value is likely a Node
            if isinstance(value, ast.Name):
                name = value.id
                if name in ("node", "n", "child", "elem", "item", "body", "left", "right", "operand"):
                    return True
            return True  # Assume it's a method if uncertain
        return False

    def _needs_node_assertion(self, value: ast.expr) -> bool:
        """Check if calling Node method on this expr needs a type assertion."""
        # If it's a loop variable from a bare list (interface{}), needs assertion
        if isinstance(value, ast.Name):
            var_name = self._snake_to_camel(value.id)
            var_name = self._safe_go_name(var_name)
            var_type = self.var_types.get(var_name, "")
            # If type is interface{} or unknown, needs assertion
            if var_type == "interface{}" or var_type == "":
                # Common loop variable names from untyped lists
                if value.id in ("r", "item", "elem", "x", "e", "part"):
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
        }
        if func_name in char_funcs and param_index == 0:
            return True
        return False

    def visit_expr_Subscript(self, node: ast.Subscript) -> str:
        """Convert subscript access (indexing/slicing)."""
        value = self.visit_expr(node.value)
        if isinstance(node.slice, ast.Slice):
            lower = self.visit_expr(node.slice.lower) if node.slice.lower else "0"
            upper = self.visit_expr(node.slice.upper) if node.slice.upper else ""
            if upper:
                return f"{value}[{lower}:{upper}]"
            return f"{value}[{lower}:]"
        index = self.visit_expr(node.slice)
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
        """Emit expression in boolean context, handling slice/map truthiness."""
        # If it's a simple Name that might be a slice/map, convert to len check
        if isinstance(node, ast.Name):
            var_name = self._snake_to_camel(node.id)
            var_name = self._safe_go_name(var_name)
            var_type = self.var_types.get(var_name, "")
            # Check if it's a slice or map type
            if var_type.startswith("[]") or var_type.startswith("map["):
                return f"len({var_name}) > 0"
            # Check by variable name heuristics
            if node.id in ("redirects", "parts", "words", "commands", "args", "elts", "items"):
                return f"len({self.visit_expr(node)}) > 0"
        # If it's an attribute access that looks like a slice field
        if isinstance(node, ast.Attribute):
            if node.attr in ("redirects", "parts", "words", "commands", "args", "body", "elts"):
                return f"len({self.visit_expr(node)}) > 0"
        # For UnaryOp Not, already handled above
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return f"!({self._emit_bool_expr(node.operand)})"
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
            # Handle string subscript compared with single-char string
            right = self._emit_comparand(comparator, node.left)
            op_str = self._cmpop_to_go(op)
            result = f"{result} {op_str} {right}"
        return result

    def _emit_comparand(self, node: ast.expr, left: ast.expr) -> str:
        """Emit right side of comparison, handling byte vs string."""
        # If left is a string subscript and right is a single-char string, use rune literal
        if self._is_byte_expr(left):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if len(node.value) == 1:
                    return self._char_to_rune_literal(node.value)
        return self.visit_expr(node)

    def _is_byte_expr(self, node: ast.expr) -> bool:
        """Check if expression evaluates to a byte (e.g., string subscript or byte variable)."""
        if self._is_string_subscript(node):
            return True
        # Check if it's a variable known to be a byte
        if isinstance(node, ast.Name):
            var_name = self._snake_to_camel(node.id)
            var_name = self._safe_go_name(var_name)
            return self.var_types.get(var_name) == "byte"
        return False

    def _is_string_subscript(self, node: ast.expr) -> bool:
        """Check if node is a string subscript (e.g., s[i])."""
        if not isinstance(node, ast.Subscript):
            return False
        # Check if the value being subscripted is likely a string
        # This is heuristic - we check if it's a Name that looks like a string var
        if isinstance(node.value, ast.Name):
            name = node.value.id
            # Common string variable names
            if name in ("s", "text", "source", "inner", "value", "char", "c", "line"):
                return True
            # Check if it ends with common string suffixes
            if name.endswith("_str") or name.endswith("text") or name.endswith("line"):
                return True
        # Check for self.source, self.text, etc.
        if isinstance(node.value, ast.Attribute):
            attr = node.value.attr
            if attr in ("source", "text", "value", "line", "inner"):
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

    def _emit_in_check(
        self, left: ast.expr, container: ast.expr, negated: bool
    ) -> str:
        """Emit Go code for 'x in container' check."""
        left_expr = self.visit_expr(left)
        # String membership
        if isinstance(container, ast.Constant) and isinstance(container.value, str):
            container_expr = self.visit_expr(container)
            # If left is a byte expression, convert to rune
            if self._is_byte_expr(left):
                left_expr = f"rune({left_expr})"
            if negated:
                return f"!strings.ContainsRune({container_expr}, {left_expr})"
            return f"strings.ContainsRune({container_expr}, {left_expr})"
        # For other containers, use a helper or inline check
        container_expr = self.visit_expr(container)
        if negated:
            return f"!_contains({container_expr}, {left_expr})"
        return f"_contains({container_expr}, {left_expr})"

    def visit_expr_BoolOp(self, node: ast.BoolOp) -> str:
        """Convert boolean operations (and/or)."""
        op = " && " if isinstance(node.op, ast.And) else " || "
        values = [self.visit_expr(v) for v in node.values]
        return op.join(values)

    def visit_expr_IfExp(self, node: ast.IfExp) -> str:
        """Convert ternary expression. Go doesn't have ternary, use helper func."""
        test = self.visit_expr(node.test)
        body = self.visit_expr(node.body)
        orelse = self.visit_expr(node.orelse)
        # Use an inline if helper function
        return f"_ternary({test}, {body}, {orelse})"

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
        args_str = ", ".join(args)
        # Handle Node interface methods - may need type assertion
        if method in ("to_sexp", "kind"):
            # If obj might not be typed as Node, add assertion
            if self._needs_node_assertion(node.func.value):
                go_method = self._snake_to_pascal(method)
                return f"{obj}.(Node).{go_method}()"
        # Handle Python string/list methods
        if method == "append":
            return self._emit_append(obj, args, node.args)
        method_map = {
            "startswith": lambda o, a: f"strings.HasPrefix({o}, {a[0]})",
            "endswith": lambda o, a: f"strings.HasSuffix({o}, {a[0]})",
            "strip": lambda o, a: f"strings.TrimSpace({o})",
            "lstrip": lambda o, a: f"strings.TrimLeft({o}, {a[0]})" if a else f"strings.TrimLeft({o}, \" \\t\")",
            "rstrip": lambda o, a: f"strings.TrimRight({o}, {a[0]})" if a else f"strings.TrimRight({o}, \" \\t\")",
            "find": lambda o, a: f"strings.Index({o}, {a[0]})",
            "rfind": lambda o, a: f"strings.LastIndex({o}, {a[0]})",
            "replace": lambda o, a: f"strings.ReplaceAll({o}, {a[0]}, {a[1]})",
            "join": lambda o, a: f"strings.Join({a[0]}, {o})",
            "lower": lambda o, a: f"strings.ToLower({o})",
            "upper": lambda o, a: f"strings.ToUpper({o})",
            "isalpha": self._emit_isalpha,
            "isdigit": self._emit_isdigit,
            "isalnum": self._emit_isalnum,
            "pop": self._emit_pop,
            "extend": self._emit_extend,
            "get": self._emit_dict_get,
            "encode": lambda o, a: f"[]byte({o})",
            "decode": lambda o, a: f"string({o})",
        }
        if method in method_map:
            handler = method_map[method]
            if callable(handler):
                return handler(obj, args)
        # Default: convert to Go method call
        go_method = self._snake_to_pascal(method)
        return f"{obj}.{go_method}({args_str})"

    def _emit_append(self, obj: str, args: list[str], orig_args: list[ast.expr] | None = None) -> str:
        """Emit append call - Go requires reassignment."""
        arg = args[0]
        # If appending a byte to a string slice, convert
        if obj in self.var_types and self.var_types[obj] == "[]string":
            if orig_args and self._is_byte_expr(orig_args[0]):
                arg = f"string({arg})"
        return f"{obj} = append({obj}, {arg})"

    def _emit_pop(self, obj: str, args: list[str]) -> str:
        """Emit pop call."""
        raise NotImplementedError("list.pop()")

    def _emit_extend(self, obj: str, args: list[str]) -> str:
        """Emit extend call."""
        return f"{obj} = append({obj}, {args[0]}...)"

    def _emit_isalpha(self, obj: str, args: list[str]) -> str:
        """Emit isalpha check."""
        # Handle both string and byte/rune cases
        return f"unicode.IsLetter(_runeFromChar({obj}))"

    def _emit_isdigit(self, obj: str, args: list[str]) -> str:
        """Emit isdigit check."""
        return f"unicode.IsDigit(_runeFromChar({obj}))"

    def _emit_isalnum(self, obj: str, args: list[str]) -> str:
        """Emit isalnum check."""
        return f"(unicode.IsLetter(_runeFromChar({obj})) || unicode.IsDigit(_runeFromChar({obj})))"

    def _emit_dict_get(self, obj: str, args: list[str]) -> str:
        """Emit dict.get() call."""
        key = args[0]
        # Special case: ANSI_C_ESCAPES uses rune keys
        if obj == "ANSICEscapes" or obj == "ANSI_C_ESCAPES":
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
        args_str = ", ".join(args)
        # Handle builtins
        builtin_map = {
            "len": lambda a: f"len({a[0]})",
            "str": lambda a: f"fmt.Sprint({a[0]})" if a else '""',
            "int": lambda a: f"_mustAtoi({a[0]})" if len(a) == 1 else f"_parseInt({a[0]}, {a[1]})",
            "bool": lambda a: f"({a[0]} != 0)" if a else "false",
            "ord": lambda a: f"rune({a[0]}[0])" if a else "0",
            "chr": lambda a: f"string(rune({a[0]}))",
            "isinstance": self._emit_isinstance,
            "getattr": self._emit_getattr,
            "range": lambda a: "/* range */",
            "list": lambda a: f"append([]interface{{}}, {a[0]}...)" if a else "[]interface{}{}",
            "set": lambda a: f"_makeSet({a[0]})" if a else "make(map[interface{}]struct{})",
            "max": lambda a: f"_max({', '.join(a)})",
            "min": lambda a: f"_min({', '.join(a)})",
            "bytearray": lambda a: "[]byte{}",
        }
        if name in builtin_map:
            return builtin_map[name](args)
        # Handle helper functions
        if name in ("_substring", "_sublist"):
            return f"{args[0]}[{args[1]}:{args[2]}]"
        if name == "_repeat_str":
            return f"strings.Repeat({args[0]}, {args[1]})"
        if name == "_starts_with_at":
            return f"strings.HasPrefix({args[0]}[{args[1]}:], {args[2]})"
        # Handle class constructors
        if name in self.symbols.classes:
            return f"New{name}({args_str})"
        # Default function call
        go_name = self._to_go_func_name(name)
        return f"{go_name}({args_str})"

    def _emit_isinstance(self, args: list[str]) -> str:
        """Emit isinstance check using type assertion."""
        raise NotImplementedError("isinstance")

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
        return "interface{}"

    def visit_expr_Dict(self, node: ast.Dict) -> str:
        """Convert dict literals."""
        if not node.keys:
            return "map[string]interface{}{}"
        pairs = []
        for k, v in zip(node.keys, node.values, strict=True):
            pairs.append(f"{self.visit_expr(k)}: {self.visit_expr(v)}")
        return "map[string]interface{}{" + ", ".join(pairs) + "}"

    def visit_expr_Tuple(self, node: ast.Tuple) -> str:
        """Convert tuple literals (as slices in Go)."""
        elements = ", ".join(self.visit_expr(e) for e in node.elts)
        return f"[]interface{{}}{{{elements}}}"

    def visit_expr_Set(self, node: ast.Set) -> str:
        """Convert set literals."""
        if not node.elts:
            return "make(map[interface{}]struct{})"
        elements = ", ".join(f"{self.visit_expr(e)}: {{}}" for e in node.elts)
        return f"map[interface{{}}]struct{{}}{{{elements}}}"

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
    print(transpiler.transpile(source))


if __name__ == "__main__":
    main()
