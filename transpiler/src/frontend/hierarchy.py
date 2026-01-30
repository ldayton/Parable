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


def is_node_subclass(name: str, symbols: SymbolTable) -> bool:
    """Check if a class is a Node subclass (directly or transitively)."""
    if name == "Node":
        return True
    info = symbols.structs.get(name)
    if not info:
        return False
    return any(is_node_subclass(base, symbols) for base in info.bases)


@dataclass
class SubtypeRel:
    """Pre-computed subtype relations for efficient lookups."""
    node_types: set[str] = field(default_factory=set)
    exception_types: set[str] = field(default_factory=set)

    def is_node(self, name: str) -> bool:
        return name in self.node_types

    def is_exception(self, name: str) -> bool:
        return name in self.exception_types


def build_hierarchy(symbols: SymbolTable) -> SubtypeRel:
    """Phase 7: Build class hierarchy and mark subtype flags."""
    rel = SubtypeRel()
    for name, info in symbols.structs.items():
        # Mark Node subclasses
        info.is_node = is_node_subclass(name, symbols)
        if info.is_node:
            rel.node_types.add(name)
        # Mark Exception subclasses
        info.is_exception = is_exception_subclass(name, symbols)
        if info.is_exception:
            rel.exception_types.add(name)
    return rel
