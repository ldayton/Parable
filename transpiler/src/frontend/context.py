"""Context objects for frontend lowering."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..ir import FuncInfo, SymbolTable, Type


@dataclass
class TypeContext:
    """Context for bidirectional type inference (Pierce & Turner style)."""
    expected: Type | None = None
    var_types: dict[str, Type] = field(default_factory=dict)
    return_type: Type | None = None
    tuple_vars: dict[str, list[str]] = field(default_factory=dict)
    sentinel_ints: set[str] = field(default_factory=set)
    narrowed_vars: set[str] = field(default_factory=set)
    kind_source_vars: dict[str, str] = field(default_factory=dict)
    union_types: dict[str, list[str]] = field(default_factory=dict)
    list_element_unions: dict[str, list[str]] = field(default_factory=dict)
    narrowed_attr_paths: dict[tuple[str, ...], str] = field(default_factory=dict)


@dataclass
class FrontendContext:
    """Immutable-ish context passed through lowering."""
    symbols: SymbolTable
    type_ctx: TypeContext
    current_func_info: FuncInfo | None
    current_class_name: str
    node_types: set[str]
    kind_to_struct: dict[str, str]
    kind_to_class: dict[str, str]
    current_catch_var: str | None
