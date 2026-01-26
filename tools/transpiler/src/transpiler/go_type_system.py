"""Type system utilities for Go transpiler."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .go_types import SymbolTable

# Python type -> Go type mapping
TYPE_MAP: dict[str, str] = {
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
KIND_TO_TYPE: dict[str, str] = {
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


class TypeSystemMixin:
    """Mixin providing type conversion methods for Go transpiler."""

    # These are expected to be set by the main class
    symbols: "SymbolTable"

    def _annotation_to_str(self, node: ast.expr | None) -> str:
        """Convert type annotation AST to string."""
        match node:
            case None:
                return ""
            case ast.Name(id=name):
                return name
            case ast.Constant(value=None):
                return "None"
            case ast.Constant(value=v):
                return str(v)
            case ast.Subscript(value=val, slice=ast.Tuple(elts=elts)):
                base = self._annotation_to_str(val)
                args = ", ".join(self._annotation_to_str(e) for e in elts)
                return f"{base}[{args}]"
            case ast.Subscript(value=val, slice=slc):
                base = self._annotation_to_str(val)
                return f"{base}[{self._annotation_to_str(slc)}]"
            case ast.BinOp(left=left, right=right, op=ast.BitOr()):
                return f"{self._annotation_to_str(left)} | {self._annotation_to_str(right)}"
            case ast.Attribute(attr=attr):
                return attr
            case _:
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
        if py_type in TYPE_MAP:
            return TYPE_MAP[py_type]
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
        current: list[str] = []
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
        current: list[str] = []
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
        match node:
            case ast.Constant(value=bool()):
                return "bool"
            case ast.Constant(value=int()):
                return "int"
            case ast.Constant(value=str()):
                return "string"
            case ast.Constant(value=None):
                return ""
            case ast.List(elts=[first, *_]):
                return "[]" + self._infer_type(first, param_types)
            case ast.List():
                return "[]interface{}"
            case ast.Dict(values=values) if values and all(
                isinstance(v, ast.Constant) and isinstance(v.value, str) for v in values
            ):
                return "map[string]string"
            case ast.Dict():
                return "map[string]interface{}"
            case ast.Name(id=name) if name in param_types:
                return self._py_type_to_go(param_types[name])
            case ast.Name(id="True" | "False"):
                return "bool"
            case ast.Name(id="None"):
                return ""
            case ast.Call(func=ast.Name(id="len")):
                return "int"
            case ast.Call(func=ast.Name(id=func_name)) if func_name in self.symbols.classes:
                info = self.symbols.classes[func_name]
                return "Node" if info.is_node else "*" + func_name
            case ast.Call(func=ast.Name(id="QuoteState")):
                return "*QuoteState"
            case ast.Call(func=ast.Name(id="ContextStack")):
                return "*ContextStack"
            case ast.Attribute(value=ast.Name(id=obj_name)) if obj_name in param_types:
                return self._py_type_to_go(param_types[obj_name])
            case ast.Attribute(value=ast.Name(id=class_name)) if class_name in (
                "ParserStateFlags",
                "DolbraceState",
                "TokenType",
                "MatchedPairFlags",
                "WordCtx",
                "ParseContext",
            ):
                return "int"
        return "interface{}"
