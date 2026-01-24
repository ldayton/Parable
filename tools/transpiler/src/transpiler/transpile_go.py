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
        self.emit('panic("TODO")')
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
        self.emit('panic("TODO")')
        self.indent -= 1
        self.emit("}")
        self.emit("")

    def _emit_constructor(self, node: ast.FunctionDef, class_info: ClassInfo):
        """Emit a constructor function."""
        func_info = class_info.methods.get("__init__")
        if not func_info:
            return
        params_str = self._format_params(func_info.params)
        self.emit(f"func New{class_info.name}({params_str}) *{class_info.name} {{")
        self.indent += 1
        self.emit('panic("TODO")')
        self.indent -= 1
        self.emit("}")
        self.emit("")

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
        parts = name.split("_")
        return parts[0] + "".join(word.capitalize() for word in parts[1:])


def main():
    if len(sys.argv) < 2:
        print("Usage: transpiler --transpile-go <input.py>", file=sys.stderr)
        sys.exit(1)
    source = Path(sys.argv[1]).read_text()
    transpiler = GoTranspiler()
    print(transpiler.transpile(source))


if __name__ == "__main__":
    main()
