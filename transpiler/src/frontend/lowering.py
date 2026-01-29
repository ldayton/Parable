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


# ============================================================
# TYPE NARROWING HELPERS
# ============================================================


def is_isinstance_call(node: ast.expr) -> tuple[str, str] | None:
    """Check if node is isinstance(var, Type). Returns (var_name, type_name) or None."""
    if not isinstance(node, ast.Call):
        return None
    if not isinstance(node.func, ast.Name) or node.func.id != "isinstance":
        return None
    if len(node.args) != 2:
        return None
    if not isinstance(node.args[0], ast.Name):
        return None
    if not isinstance(node.args[1], ast.Name):
        return None
    return (node.args[0].id, node.args[1].id)


def is_kind_check(node: ast.expr, kind_to_class: dict[str, str]) -> tuple[str, str] | None:
    """Check if node is x.kind == "typename". Returns (var_name, class_name) or None."""
    if not isinstance(node, ast.Compare):
        return None
    if len(node.ops) != 1 or not isinstance(node.ops[0], ast.Eq):
        return None
    if len(node.comparators) != 1:
        return None
    # Check for x.kind on left side
    if not isinstance(node.left, ast.Attribute) or node.left.attr != "kind":
        return None
    if not isinstance(node.left.value, ast.Name):
        return None
    var_name = node.left.value.id
    # Check for string constant on right side
    comparator = node.comparators[0]
    if not isinstance(comparator, ast.Constant) or not isinstance(comparator.value, str):
        return None
    kind_value = comparator.value
    # Map kind string to class name
    if kind_value not in kind_to_class:
        return None
    return (var_name, kind_to_class[kind_value])


def extract_isinstance_or_chain(
    node: ast.expr, kind_to_class: dict[str, str]
) -> tuple[str, list[str]] | None:
    """Extract isinstance/kind checks from expression. Returns (var_name, [type_names]) or None."""
    # Handle simple isinstance call
    simple = is_isinstance_call(node)
    if simple:
        return (simple[0], [simple[1]])
    # Handle x.kind == "typename" pattern
    kind_check = is_kind_check(node, kind_to_class)
    if kind_check:
        return (kind_check[0], [kind_check[1]])
    # Handle isinstance(x, A) or isinstance(x, B) or ...
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
        var_name: str | None = None
        type_names: list[str] = []
        for value in node.values:
            check = is_isinstance_call(value) or is_kind_check(value, kind_to_class)
            if not check:
                return None  # Not all are isinstance/kind calls
            if var_name is None:
                var_name = check[0]
            elif var_name != check[0]:
                return None  # Different variables
            type_names.append(check[1])
        if var_name and type_names:
            return (var_name, type_names)
    return None


def extract_isinstance_from_and(node: ast.expr) -> tuple[str, str] | None:
    """Extract isinstance(var, Type) from compound AND expression.
    Returns (var_name, type_name) or None if no isinstance found."""
    if not isinstance(node, ast.BoolOp) or not isinstance(node.op, ast.And):
        return None
    # Check each value in the AND chain for isinstance
    for value in node.values:
        result = is_isinstance_call(value)
        if result:
            return result
    return None


def extract_kind_check(
    node: ast.expr, kind_to_struct: dict[str, str], kind_source_vars: dict[str, str]
) -> tuple[str, str] | None:
    """Extract kind-based type narrowing from `kind == "value"` or `node.kind == "value"`.
    Returns (node_var_name, struct_name) or None if not a kind check."""
    # Match: kind == "value" where kind was previously assigned from node.kind
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq):
        left = node.left
        right = node.comparators[0]
        # Check for var == "kind_value" pattern
        if isinstance(left, ast.Name) and isinstance(right, ast.Constant) and isinstance(right.value, str):
            kind_var = left.id
            kind_value = right.value
            if kind_value in kind_to_struct:
                # Look up which Node-typed variable this kind var came from
                if kind_var in kind_source_vars:
                    node_var = kind_source_vars[kind_var]
                    return (node_var, kind_to_struct[kind_value])
        # Check for node.kind == "value" pattern
        if isinstance(left, ast.Attribute) and left.attr == "kind" and isinstance(left.value, ast.Name):
            node_var = left.value.id
            if isinstance(right, ast.Constant) and isinstance(right.value, str):
                kind_value = right.value
                if kind_value in kind_to_struct:
                    return (node_var, kind_to_struct[kind_value])
    return None


def extract_attr_kind_check(
    node: ast.expr, kind_to_struct: dict[str, str]
) -> tuple[tuple[str, ...], str] | None:
    """Extract kind check for attribute paths like `node.body.kind == "value"`.
    Returns (attr_path_tuple, struct_name) or None."""
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq):
        left = node.left
        right = node.comparators[0]
        # Check for expr.kind == "value" pattern where expr is an attribute chain
        if (isinstance(left, ast.Attribute) and left.attr == "kind"
            and isinstance(right, ast.Constant) and isinstance(right.value, str)):
            kind_value = right.value
            if kind_value in kind_to_struct:
                # Extract the attribute path (e.g., node.body -> ("node", "body"))
                attr_path = get_attr_path(left.value)
                if attr_path and len(attr_path) > 1:  # Only for chains, not simple vars
                    return (attr_path, kind_to_struct[kind_value])
    return None


def get_attr_path(node: ast.expr) -> tuple[str, ...] | None:
    """Extract attribute path as tuple (e.g., node.body -> ("node", "body"))."""
    if isinstance(node, ast.Name):
        return (node.id,)
    elif isinstance(node, ast.Attribute) and isinstance(node.value, (ast.Name, ast.Attribute)):
        base = get_attr_path(node.value)
        if base:
            return base + (node.attr,)
    return None


def resolve_type_name(
    name: str, type_map: dict[str, "ir.Type"], symbols: "ir.SymbolTable"
) -> "ir.Type":
    """Resolve a class name to an IR type (for isinstance checks)."""
    from ..ir import Interface, Pointer, StructRef
    # Handle primitive types
    if name in type_map:
        return type_map[name]
    if name in symbols.structs:
        return Pointer(StructRef(name))
    return Interface(name)
