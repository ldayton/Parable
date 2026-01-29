"""Type inference utilities extracted from frontend.py."""
from __future__ import annotations

from ..ir import (
    Interface,
    Optional,
    Pointer,
    StructRef,
    Type,
)


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
