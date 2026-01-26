#!/usr/bin/env python3
"""Transpile parable.py's restricted Python subset to Go."""

import ast
import shutil
import subprocess
import sys
from pathlib import Path

from .go_emit_expr import EmitExpressionsMixin
from .go_emit_func import EmitFunctionsMixin
from .go_emit_stmt import EmitStatementsMixin
from .go_emit_structure import EmitStructureMixin
from .go_naming import NamingMixin
from .go_scope import ScopeAnalysisMixin
from .go_symbols import SymbolsMixin
from .go_type_system import TypeSystemMixin
from .go_types import FuncInfo, ParamInfo, SymbolTable


class GoTranspiler(
    NamingMixin,
    TypeSystemMixin,
    SymbolsMixin,
    EmitExpressionsMixin,
    EmitStatementsMixin,
    EmitFunctionsMixin,
    ScopeAnalysisMixin,
    EmitStructureMixin,
    ast.NodeVisitor,
):
    """Transpiles Python AST to Go source code."""

    def __init__(self):
        self.indent = 0
        self.output: list[str] = []
        self.symbols = SymbolTable()
        self.tree: ast.Module | None = None
        self.current_class: str | None = None
        self.current_method: str | None = None  # Current method name being emitted
        self.current_func_info: FuncInfo | None = None  # Current method's FuncInfo
        self.current_return_type: str = ""  # Go return type of current function/method
        self.union_field_types: dict[
            tuple[str, str], str
        ] = {}  # Map (receiver, field) to current type
        self._type_switch_var: tuple[str, str] | None = (
            None  # (original_var, switch_var) during type switch
        )
        self._type_switch_type: str | None = None  # Current narrowed type in type switch case

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
            if var_name in self._ctx.var_types:
                return self._ctx.var_types[var_name]
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
                var_type = self._ctx.var_types.get(var_name, "")
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
                    var_type = self._ctx.var_types.get(var_name, "")
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
                var_type = self._ctx.var_types.get(var_name, "")
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
