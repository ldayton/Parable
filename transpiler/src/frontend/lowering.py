"""Lowering utilities extracted from frontend.py."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from ..ir import Loc

if TYPE_CHECKING:
    from .. import ir


@dataclass
class LoweringDispatch:
    """Callbacks for mutual recursion during lowering."""
    lower_expr: Callable[[ast.expr], "ir.Expr"]
    lower_stmt: Callable[[ast.stmt], "ir.Stmt"]
    lower_stmts: Callable[[list[ast.stmt]], list["ir.Stmt"]]
    lower_lvalue: Callable[[ast.expr], "ir.LValue"]
    lower_expr_as_bool: Callable[[ast.expr], "ir.Expr"]


def loc_from_node(node: ast.AST) -> Loc:
    """Create Loc from AST node."""
    if hasattr(node, "lineno"):
        return Loc(
            line=node.lineno,
            col=node.col_offset,
            end_line=getattr(node, "end_lineno", node.lineno) or node.lineno,
            end_col=getattr(node, "end_col_offset", node.col_offset) or node.col_offset,
        )
    return Loc.unknown()


def binop_to_str(op: ast.operator) -> str:
    """Convert AST binary operator to string."""
    return {
        ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
        ast.FloorDiv: "/", ast.Mod: "%", ast.Pow: "**",
        ast.LShift: "<<", ast.RShift: ">>",
        ast.BitOr: "|", ast.BitXor: "^", ast.BitAnd: "&",
    }.get(type(op), "+")


def cmpop_to_str(op: ast.cmpop) -> str:
    """Convert AST comparison operator to string."""
    return {
        ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=",
        ast.Gt: ">", ast.GtE: ">=", ast.Is: "==", ast.IsNot: "!=",
        ast.In: "in", ast.NotIn: "not in",
    }.get(type(op), "==")


def unaryop_to_str(op: ast.unaryop) -> str:
    """Convert AST unary operator to string."""
    return {ast.Not: "!", ast.USub: "-", ast.UAdd: "+", ast.Invert: "~"}.get(type(op), "-")
