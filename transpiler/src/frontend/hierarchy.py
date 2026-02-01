"""Phase 7: Class hierarchy analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..ir import SymbolTable


def is_exception_subclass(name: str, symbols: SymbolTable) -> bool:
    """Check if a class is an Exception subclass (directly or transitively)."""
    if name == "Exception":
        return True
    info = symbols.structs.get(name)
    if not info:
        return False
    return any(is_exception_subclass(base, symbols) for base in info.bases)


def find_hierarchy_root(symbols: SymbolTable) -> str | None:
    """Find the single root of the class hierarchy (e.g., "Node").

    Returns the name of the class that:
    - Has no base classes
    - Is used as a base class (directly or transitively)
    - Is the only such root (returns None if multiple or none)
    """
    used_as_base: set[str] = set()
    for info in symbols.structs.values():
        for base in info.bases:
            if base != "Exception" and not is_exception_subclass(base, symbols):
                used_as_base.add(base)
    roots = [
        n
        for n in used_as_base
        if symbols.structs.get(n) and len(symbols.structs[n].bases) == 0
    ]
    return roots[0] if len(roots) == 1 else None


def is_node_subclass(
    name: str, symbols: SymbolTable, hierarchy_root: str | None = None
) -> bool:
    """Check if a class is a Node subclass (directly or transitively)."""
    if hierarchy_root is None:
        hierarchy_root = find_hierarchy_root(symbols)
    if hierarchy_root is None:
        return False
    if name == hierarchy_root:
        return True
    info = symbols.structs.get(name)
    if not info:
        return False
    return any(is_node_subclass(base, symbols, hierarchy_root) for base in info.bases)


@dataclass
class SubtypeRel:
    """Pre-computed subtype relations for efficient lookups."""

    hierarchy_root: str | None = None
    node_types: set[str] = field(default_factory=set)
    exception_types: set[str] = field(default_factory=set)

    def is_node(self, name: str) -> bool:
        return name in self.node_types

    def is_exception(self, name: str) -> bool:
        return name in self.exception_types


def build_hierarchy(symbols: SymbolTable) -> SubtypeRel:
    """Phase 7: Build class hierarchy and mark subtype flags."""
    hierarchy_root = find_hierarchy_root(symbols)
    rel = SubtypeRel(hierarchy_root=hierarchy_root)
    for name, info in symbols.structs.items():
        # Mark Node subclasses
        info.is_node = is_node_subclass(name, symbols, hierarchy_root)
        if info.is_node:
            rel.node_types.add(name)
        # Mark Exception subclasses
        info.is_exception = is_exception_subclass(name, symbols)
        if info.is_exception:
            rel.exception_types.add(name)
    return rel
