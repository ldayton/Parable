"""Builder utilities extracted from frontend.py."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from ..ir import Loc

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
