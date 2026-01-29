"""Type inference utilities extracted from frontend.py."""
from __future__ import annotations

from ..ir import (
    BOOL,
    BYTE,
    FLOAT,
    INT,
    STRING,
    VOID,
    FuncType,
    Interface,
    Map,
    Optional,
    Pointer,
    Set,
    Slice,
    StructRef,
    SymbolTable,
    Tuple,
    Type,
)

# Python type -> IR type mapping for primitives
TYPE_MAP: dict[str, Type] = {
    "str": STRING,
    "int": INT,
    "bool": BOOL,
    "float": FLOAT,
    "bytes": Slice(BYTE),
    "bytearray": Slice(BYTE),
}


def split_union_types(s: str) -> list[str]:
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


def split_type_args(s: str) -> list[str]:
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


def extract_struct_name(typ: Type) -> str | None:
    """Extract struct name from wrapped types like Pointer, Optional, etc."""
    if isinstance(typ, StructRef):
        return typ.name
    if isinstance(typ, Pointer):
        return extract_struct_name(typ.target)
    if isinstance(typ, Optional):
        return extract_struct_name(typ.inner)
    return None


def is_node_interface_type(typ: Type | None) -> bool:
    """Check if a type is the Node interface type."""
    if typ is None:
        return False
    # Interface("Node")
    if isinstance(typ, Interface) and typ.name == "Node":
        return True
    # StructRef("Node")
    if isinstance(typ, StructRef) and typ.name == "Node":
        return True
    return False


def is_node_subtype(typ: Type | None, node_types: set[str]) -> bool:
    """Check if a type is a Node subtype (pointer to struct implementing Node)."""
    if typ is None:
        return False
    # Check Pointer(StructRef(X)) where X is a Node subclass
    if isinstance(typ, Pointer) and isinstance(typ.target, StructRef):
        struct_name = typ.target.name
        if struct_name in node_types:
            return True
    return False


def is_node_subclass(name: str, symbols: SymbolTable) -> bool:
    """Check if a class is a Node subclass (directly or transitively)."""
    if name == "Node":
        return True
    info = symbols.structs.get(name)
    if not info:
        return False
    return any(is_node_subclass(base, symbols) for base in info.bases)


def parse_callable_type(
    py_type: str,
    concrete_nodes: bool,
    symbols: SymbolTable,
    node_types: set[str],
) -> Type:
    """Parse Callable[[], ReturnType] -> FuncType."""
    inner = py_type[9:-1]  # Remove "Callable[" and "]"
    parts = split_type_args(inner)
    if len(parts) >= 2:
        args_str = parts[0]
        ret_type = parts[-1]
        ret = py_type_to_ir(ret_type, symbols, node_types, concrete_nodes)
        # Handle empty args list "[]"
        if args_str == "[]":
            return FuncType(params=(), ret=ret)
        # Handle args list like "[int, str]"
        if args_str.startswith("[") and args_str.endswith("]"):
            args_inner = args_str[1:-1]
            if args_inner:
                param_types = tuple(
                    py_type_to_ir(a.strip(), symbols, node_types, concrete_nodes)
                    for a in args_inner.split(",")
                )
                return FuncType(params=param_types, ret=ret)
            return FuncType(params=(), ret=ret)
    return Interface("any")


def py_type_to_ir(
    py_type: str,
    symbols: SymbolTable,
    node_types: set[str],
    concrete_nodes: bool = False,
) -> Type:
    """Convert Python type string to IR Type."""
    if not py_type:
        return Interface("any")
    # Handle simple types
    if py_type in TYPE_MAP:
        return TYPE_MAP[py_type]
    # Handle bare "list" without type args
    if py_type == "list":
        return Slice(Interface("any"))
    # Handle bare "dict" without type args
    if py_type == "dict":
        return Map(STRING, Interface("any"))
    # Handle bare "set" without type args
    if py_type == "set":
        return Set(Interface("any"))
    # Handle X | None -> Optional[base type]
    if " | " in py_type:
        parts = split_union_types(py_type)
        if len(parts) > 1:
            parts = [p for p in parts if p != "None"]
            if len(parts) == 1:
                inner = py_type_to_ir(parts[0], symbols, node_types, concrete_nodes)
                # For Node | None, use Node interface (interfaces are nilable in Go)
                if parts[0] == "Node" or is_node_subclass(parts[0], symbols):
                    return Interface("Node")
                # For str | None, just use string (empty string represents None)
                if inner == STRING:
                    return STRING
                # For int | None, use int with -1 sentinel (handled elsewhere)
                if inner == INT:
                    return Optional(inner)
                return Optional(inner)
            # If all parts are Node subclasses, return Node interface (nilable)
            if all(is_node_subclass(p, symbols) for p in parts):
                return Interface("Node")
            return Interface("any")
    # Handle list[X]
    if py_type.startswith("list["):
        inner = py_type[5:-1]
        return Slice(py_type_to_ir(inner, symbols, node_types, concrete_nodes))
    # Handle dict[K, V]
    if py_type.startswith("dict["):
        inner = py_type[5:-1]
        parts = split_type_args(inner)
        if len(parts) == 2:
            return Map(
                py_type_to_ir(parts[0], symbols, node_types, concrete_nodes),
                py_type_to_ir(parts[1], symbols, node_types, concrete_nodes),
            )
    # Handle set[X]
    if py_type.startswith("set["):
        inner = py_type[4:-1]
        return Set(py_type_to_ir(inner, symbols, node_types, concrete_nodes))
    # Handle tuple[...] - parse element types for typed tuples
    if py_type.startswith("tuple["):
        inner = py_type[6:-1]
        parts = split_type_args(inner)
        elements = tuple(py_type_to_ir(p, symbols, node_types, concrete_nodes) for p in parts)
        return Tuple(elements)
    # Handle Callable
    if py_type.startswith("Callable["):
        return parse_callable_type(py_type, concrete_nodes, symbols, node_types)
    # Handle class names
    if py_type in symbols.structs:
        info = symbols.structs[py_type]
        if info.is_node or py_type == "Node":
            if concrete_nodes and py_type != "Node":
                return Pointer(StructRef(py_type))
            return Interface("Node")
        return Pointer(StructRef(py_type))
    # Known internal types
    if py_type in ("Token", "QuoteState", "ParseContext", "Lexer", "Parser"):
        return Pointer(StructRef(py_type))
    # Type aliases - union types of Node subtypes
    if py_type in ("ArithNode", "CondNode"):
        return Interface("Node")
    # Python builtin aliases
    if py_type == "bytearray":
        return Slice(BYTE)
    if py_type == "tuple":
        return Interface("any")
    # Type alias mappings
    if py_type == "CommandSub":
        return Pointer(StructRef("CommandSubstitution"))
    if py_type == "ProcessSub":
        return Pointer(StructRef("ProcessSubstitution"))
    # Unknown type - return as interface
    return Interface(py_type)


def py_return_type_to_ir(
    py_type: str,
    symbols: SymbolTable,
    node_types: set[str],
) -> Type:
    """Convert Python return type to IR, handling tuples as multiple returns."""
    if not py_type or py_type == "None":
        return VOID
    # Handle unions before tuple
    if " | " in py_type:
        parts = split_union_types(py_type)
        if len(parts) > 1:
            parts = [p for p in parts if p != "None"]
            if len(parts) == 1:
                return py_return_type_to_ir(parts[0], symbols, node_types)
            # Check if all parts are Node subclasses -> return Node interface
            if all(p in node_types for p in parts):
                return StructRef("Node")
            return Interface("any")
    # Handle tuple[...] specially for return types
    if py_type.startswith("tuple["):
        inner = py_type[6:-1]
        parts = split_type_args(inner)
        elements = tuple(py_type_to_ir(p, symbols, node_types, concrete_nodes=True) for p in parts)
        return Tuple(elements)
    # For non-tuples, use standard conversion with concrete node types
    return py_type_to_ir(py_type, symbols, node_types, concrete_nodes=True)
