"""Builder utilities extracted from frontend.py."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from ..ir import INT, Function, Loc, Param, Pointer, StructRef
from ..type_overrides import PARAM_TYPE_OVERRIDES

if TYPE_CHECKING:
    from .. import ir
    from ..ir import FuncInfo, StructInfo, SymbolTable, Type


@dataclass
class BuilderCallbacks:
    """Callbacks for builder phase that need lowering/type conversion."""
    annotation_to_str: Callable[[ast.expr | None], str]
    py_type_to_ir: Callable[[str, bool], "Type"]
    py_return_type_to_ir: Callable[[str], "Type"]
    lower_expr: Callable[[ast.expr], "ir.Expr"]
    lower_stmts: Callable[[list[ast.stmt]], list["ir.Stmt"]]
    collect_var_types: Callable[[list[ast.stmt]], tuple[dict, dict, set, dict]]
    is_exception_subclass: Callable[[str], bool]
    extract_union_struct_names: Callable[[str], list[str]]
    loc_from_node: Callable[[ast.AST], "Loc"]


def build_forwarding_constructor(
    class_name: str,
    parent_class: str,
    symbols: "SymbolTable",
) -> Function:
    """Build a forwarding constructor for exception subclasses with no __init__."""
    from .. import ir
    # Get parent class info to copy its parameters
    parent_info = symbols.structs.get(parent_class)
    if not parent_info:
        raise ValueError(f"Unknown parent class: {parent_class}")
    # Build parameters from parent's __init__ params
    params: list[Param] = []
    for param_name in parent_info.init_params:
        # Check for parameter type overrides
        typ = INT  # Default
        override_key = (f"New{class_name}", param_name)
        if override_key in PARAM_TYPE_OVERRIDES:
            typ = PARAM_TYPE_OVERRIDES[override_key]
        else:
            # Try parent constructor override
            parent_key = (f"New{parent_class}", param_name)
            if parent_key in PARAM_TYPE_OVERRIDES:
                typ = PARAM_TYPE_OVERRIDES[parent_key]
            else:
                # Get from parent's field type
                field_info = parent_info.fields.get(param_name)
                if field_info:
                    typ = field_info.typ
        params.append(Param(name=param_name, typ=typ, loc=Loc.unknown()))
    # Build body: return &ClassName{ParentClass{...}}
    # Use StructLit with embedded type
    body: list[ir.Stmt] = []
    # Create parent struct literal
    parent_lit = ir.StructLit(
        struct_name=parent_class,
        fields={param_name: ir.Var(name=param_name, typ=params[i].typ) for i, param_name in enumerate(parent_info.init_params)},
        typ=StructRef(parent_class),
    )
    # Create struct with embedded parent - typ=Pointer makes backend emit &
    struct_lit = ir.StructLit(
        struct_name=class_name,
        fields={},
        typ=Pointer(StructRef(class_name)),
        embedded_value=parent_lit,
    )
    # Return pointer to struct
    ret = ir.Return(value=struct_lit)
    body.append(ret)
    return Function(
        name=f"New{class_name}",
        params=params,
        ret=Pointer(StructRef(class_name)),
        body=body,
        loc=Loc.unknown(),
    )
