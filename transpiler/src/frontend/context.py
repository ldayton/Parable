"""Context objects for frontend lowering."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .. import ir
    from ..ir import FuncInfo, Loc, SymbolTable, Type


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

    symbols: "SymbolTable"
    type_ctx: TypeContext
    current_func_info: "FuncInfo | None"
    current_class_name: str
    node_types: set[str]
    kind_to_struct: dict[str, str]
    kind_to_class: dict[str, str]
    current_catch_var: str | None
    exception_subclasses: set[str]


@dataclass
class LoweringDispatch:
    """Callbacks for recursive lowering.

    These callbacks allow extracted lowering functions to call back into
    the Frontend instance for recursive lowering and type inference.

    Why these callbacks must stay (cannot be inlined):
    - lower_expr/lower_expr_as_bool/lower_stmts/lower_lvalue: Recursive calls
    - lower_expr_List: Bidirectional type inference for constructors
    - infer_expr_type_from_ast: Uses mutable _type_ctx state
    - annotation_to_str: Recursive AST traversal with self reference
    - merge_keyword_args/fill_default_args/etc: Pass lower_expr/infer callbacks
    - set_catch_var: Mutates Frontend instance state
    """

    # Recursive lowering (MUST STAY - recursive)
    lower_expr: Callable[[ast.expr], "ir.Expr"]
    lower_expr_as_bool: Callable[[ast.expr], "ir.Expr"]
    lower_stmts: Callable[[list[ast.stmt]], list["ir.Stmt"]]
    lower_lvalue: Callable[[ast.expr], "ir.LValue"]
    # Bidirectional type inference (MUST STAY - uses expected type context)
    lower_expr_List: Callable[[ast.List, "Type | None"], "ir.Expr"]
    # Type inference (MUST STAY - uses mutable _type_ctx)
    infer_expr_type_from_ast: Callable[[ast.expr], "Type"]
    # Helper (MUST STAY - recursive AST traversal)
    annotation_to_str: Callable[[ast.expr | None], str]
    # Argument handling (MUST STAY - pass lower_expr/infer callbacks internally)
    merge_keyword_args: Callable[["Type", str, list, ast.Call], list]
    fill_default_args: Callable[["Type", str, list], list]
    merge_keyword_args_for_func: Callable[["FuncInfo", list, ast.Call], list]
    add_address_of_for_ptr_params: Callable[["Type", str, list, list[ast.expr]], list]
    deref_for_slice_params: Callable[["Type", str, list, list[ast.expr]], list]
    deref_for_func_slice_params: Callable[[str, list, list[ast.expr]], list]
    coerce_sentinel_to_ptr: Callable[["Type", str, list, list], list]
    # Exception handling (MUST STAY - mutates instance state)
    set_catch_var: Callable[[str | None], str | None]
