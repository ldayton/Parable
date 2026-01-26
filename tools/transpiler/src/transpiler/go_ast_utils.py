"""Pure AST utility functions for Go transpiler."""

from __future__ import annotations

import ast

from .go_overrides import UNION_FIELDS
from .go_type_system import KIND_TO_TYPE


def is_super_call(stmt: ast.stmt) -> bool:
    """Check if statement is super().__init__() call."""
    if not isinstance(stmt, ast.Expr):
        return False
    if not isinstance(stmt.value, ast.Call):
        return False
    call = stmt.value
    if not isinstance(call.func, ast.Attribute):
        return False
    if call.func.attr != "__init__":
        return False
    if not isinstance(call.func.value, ast.Call):
        return False
    if not isinstance(call.func.value.func, ast.Name):
        return False
    return call.func.value.func.id == "super"


def has_return_in_block(stmts: list[ast.stmt]) -> bool:
    """Check if a block contains return statements (complex try/except pattern)."""
    for s in stmts:
        if isinstance(s, ast.Return):
            return True
        if isinstance(s, ast.If):
            if has_return_in_block(s.body) or has_return_in_block(s.orelse):
                return True
        if isinstance(s, (ast.For, ast.While)):
            if has_return_in_block(s.body):
                return True
    return False


def is_try_assign_except_return(stmt: ast.Try) -> bool:
    """Check if this is a 'try: x = call() except: return fallback' pattern."""
    # Must have exactly one statement in try body that's an assignment
    if len(stmt.body) != 1:
        return False
    if not isinstance(stmt.body[0], ast.Assign):
        return False
    assign = stmt.body[0]
    # Must assign to a single name
    if len(assign.targets) != 1 or not isinstance(assign.targets[0], ast.Name):
        return False
    # Must have exactly one handler
    if len(stmt.handlers) != 1:
        return False
    handler = stmt.handlers[0]
    # Handler must end with a return statement
    if not handler.body or not isinstance(handler.body[-1], ast.Return):
        return False
    return True


def detect_union_discriminator(
    test: ast.expr, to_go_var_fn: callable
) -> tuple[str, str, str] | None:
    """Detect if test is a union field discriminator comparison (var == nil).
    Returns (receiver, field, discriminator_var) if found, None otherwise."""
    # Look for pattern: discriminatorVar == nil
    if not isinstance(test, ast.Compare):
        return None
    if len(test.ops) != 1 or not isinstance(test.ops[0], (ast.Eq, ast.Is)):
        return None
    if len(test.comparators) != 1:
        return None
    # Check if comparing to None/nil
    comp = test.comparators[0]
    if not (isinstance(comp, ast.Constant) and comp.value is None):
        return None
    # Check if left side is a discriminator variable
    if not isinstance(test.left, ast.Name):
        return None
    disc_var = to_go_var_fn(test.left.id)
    # Check if this discriminator matches any union field
    for (receiver_type, field_name), (expected_disc, _, _) in UNION_FIELDS.items():
        if disc_var == expected_disc:
            return (receiver_type, field_name, disc_var)
    return None


def detect_kind_check(test: ast.expr) -> tuple[str, str] | None:
    """Detect `var.kind == "literal"` or `var is not None and var.kind == "literal"`.
    Returns (var_name, kind_literal) or None."""
    # Handle compound: `var is not None and var.kind == "literal"`
    # Go type assertion handles nil check implicitly, so we can emit just the assertion
    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.And):
        for value in test.values:
            result = detect_simple_kind_check(value)
            if result:
                return result
        return None
    return detect_simple_kind_check(test)


def detect_simple_kind_check(test: ast.expr) -> tuple[str, str] | None:
    """Detect simple `var.kind == "literal"`. Returns (var_name, kind_literal) or None."""
    if not isinstance(test, ast.Compare):
        return None
    if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
        return None
    if not isinstance(test.left, ast.Attribute) or test.left.attr != "kind":
        return None
    if not isinstance(test.left.value, ast.Name):
        return None
    comp = test.comparators[0]
    if not isinstance(comp, ast.Constant) or not isinstance(comp.value, str):
        return None
    if comp.value not in KIND_TO_TYPE:
        return None
    return (test.left.value.id, comp.value)


def is_string_char_subscript(node: ast.expr) -> bool:
    """Check if node is a single-character string subscript (returns byte in Go)."""
    if not isinstance(node, ast.Subscript):
        return False
    # Must be single index, not slice
    if isinstance(node.slice, ast.Slice):
        return False
    # Check if the value being subscripted is a known string attribute
    if isinstance(node.value, ast.Attribute):
        # Common string fields: source, Source
        if node.value.attr.lower() == "source":
            return True
    # Also handle local variables that are strings
    if isinstance(node.value, ast.Name):
        name = node.value.id
        if name in ("source", "s", "text", "line"):
            return True
    return False
