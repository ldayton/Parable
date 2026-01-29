"""Liveness analysis: initial_value_unused, catch_var_unused, binding_unused, unused_indices."""

from src.ir import (
    Assign,
    Block,
    DerefLV,
    ExprStmt,
    FieldLV,
    ForClassic,
    ForRange,
    Function,
    If,
    IndexLV,
    Match,
    Module,
    OpAssign,
    Return,
    Stmt,
    TryCatch,
    TupleAssign,
    TypeSwitch,
    Var,
    VarDecl,
    VarLV,
    While,
)
from .returns import contains_return
from .scope import _collect_assigned_vars, _collect_used_vars


def analyze_liveness(module: Module) -> None:
    """Run liveness analysis: unused initial values, catch vars, bindings, tuple targets."""
    for func in module.functions:
        _analyze_initial_value_in_function(func)
        _analyze_unused_tuple_targets(func)
    for struct in module.structs:
        for method in struct.methods:
            _analyze_initial_value_in_function(method)
            _analyze_unused_tuple_targets(method)


def _analyze_initial_value_in_function(func: Function) -> None:
    """Analyze a function for unused initial values."""
    _analyze_initial_value_in_stmts(func.body)


def _analyze_initial_value_in_stmts(stmts: list[Stmt]) -> None:
    """Analyze statements for VarDecls with unused initial values."""
    for i, stmt in enumerate(stmts):
        if isinstance(stmt, VarDecl) and stmt.value is not None:
            stmt.initial_value_unused = _is_written_before_read(stmt.name, stmts[i + 1 :])
        # Recurse into nested structures
        if isinstance(stmt, If):
            _analyze_initial_value_in_stmts(stmt.then_body)
            _analyze_initial_value_in_stmts(stmt.else_body)
        elif isinstance(stmt, While):
            _analyze_initial_value_in_stmts(stmt.body)
        elif isinstance(stmt, ForRange):
            _analyze_initial_value_in_stmts(stmt.body)
        elif isinstance(stmt, ForClassic):
            _analyze_initial_value_in_stmts(stmt.body)
        elif isinstance(stmt, Block):
            _analyze_initial_value_in_stmts(stmt.body)
        elif isinstance(stmt, TryCatch):
            _analyze_initial_value_in_stmts(stmt.body)
            _analyze_initial_value_in_stmts(stmt.catch_body)
            # Check if catch variable is used
            if stmt.catch_var:
                used = _collect_used_vars(stmt.catch_body)
                stmt.catch_var_unused = stmt.catch_var not in used
            else:
                stmt.catch_var_unused = True
            # Check if try or catch body contains Return statements
            # This affects how the TryCatch should be emitted (IIFE vs defer pattern)
            stmt.has_returns = contains_return(stmt.body) or contains_return(stmt.catch_body)
            # Track if specifically the catch body has returns (needs named return pattern)
            stmt.has_catch_returns = contains_return(stmt.catch_body)
        elif isinstance(stmt, Match):
            for case in stmt.cases:
                _analyze_initial_value_in_stmts(case.body)
            _analyze_initial_value_in_stmts(stmt.default)
        elif isinstance(stmt, TypeSwitch):
            # Check if the binding variable is used in any case body
            all_stmts: list[Stmt] = []
            for case in stmt.cases:
                all_stmts.extend(case.body)
            all_stmts.extend(stmt.default)
            used_vars = _collect_used_vars(all_stmts)
            stmt.binding_unused = stmt.binding not in used_vars
            # Check if the binding is reassigned in any case body
            # If so, Go's type switch shadowing will cause type errors
            assigned_vars = _collect_assigned_vars(all_stmts)
            stmt.binding_reassigned = stmt.binding in assigned_vars
            # Recurse into case bodies
            for case in stmt.cases:
                _analyze_initial_value_in_stmts(case.body)
            _analyze_initial_value_in_stmts(stmt.default)


def _is_written_before_read(name: str, stmts: list[Stmt]) -> bool:
    """Check if variable is assigned before any read in statement sequence.

    Returns True if the first access to `name` is a write (assignment).
    Returns False if the first access is a read, or if there's no access.
    """
    for stmt in stmts:
        result = _first_access_type(name, stmt)
        if result == "read":
            return False
        if result == "write":
            return True
    return False


def _first_access_type(name: str, stmt: Stmt) -> str | None:
    """Determine if first access to `name` in stmt is 'read', 'write', or None."""
    if isinstance(stmt, VarDecl):
        if stmt.value and _expr_reads(name, stmt.value):
            return "read"
        return None
    elif isinstance(stmt, Assign):
        # Check RHS first (read), then LHS (write)
        if _expr_reads(name, stmt.value):
            return "read"
        if isinstance(stmt.target, VarLV) and stmt.target.name == name:
            return "write"
        # Check for reads in complex lvalues
        if _lvalue_reads(name, stmt.target):
            return "read"
        return None
    elif isinstance(stmt, OpAssign):
        # OpAssign reads before writing (x += 1 reads x)
        if isinstance(stmt.target, VarLV) and stmt.target.name == name:
            return "read"
        if _expr_reads(name, stmt.value):
            return "read"
        if _lvalue_reads(name, stmt.target):
            return "read"
        return None
    elif isinstance(stmt, TupleAssign):
        if _expr_reads(name, stmt.value):
            return "read"
        for target in stmt.targets:
            if isinstance(target, VarLV) and target.name == name:
                return "write"
        return None
    elif isinstance(stmt, ExprStmt):
        if _expr_reads(name, stmt.expr):
            return "read"
        return None
    elif isinstance(stmt, Return):
        if stmt.value and _expr_reads(name, stmt.value):
            return "read"
        return None
    elif isinstance(stmt, Block):
        # Blocks execute sequentially
        for s in stmt.body:
            result = _first_access_type(name, s)
            if result:
                return result
        return None
    elif isinstance(stmt, If):
        # Condition is always evaluated
        if _expr_reads(name, stmt.cond):
            return "read"
        # Branches: conservative - if either branch reads first, consider it a read
        # Only return "write" if BOTH branches write first (guaranteed write)
        then_result = _first_access_in_stmts(name, stmt.then_body)
        else_result = _first_access_in_stmts(name, stmt.else_body)
        if then_result == "read" or else_result == "read":
            return "read"
        if then_result == "write" and else_result == "write":
            return "write"
        return None
    elif isinstance(stmt, While):
        if _expr_reads(name, stmt.cond):
            return "read"
        # Loop body might not execute, so can't guarantee write
        result = _first_access_in_stmts(name, stmt.body)
        if result == "read":
            return "read"
        return None
    elif isinstance(stmt, ForRange):
        if _expr_reads(name, stmt.iterable):
            return "read"
        result = _first_access_in_stmts(name, stmt.body)
        if result == "read":
            return "read"
        return None
    elif isinstance(stmt, ForClassic):
        if stmt.init:
            result = _first_access_type(name, stmt.init)
            if result:
                return result
        if stmt.cond and _expr_reads(name, stmt.cond):
            return "read"
        return None
    elif isinstance(stmt, TryCatch):
        # Try body might partially execute
        result = _first_access_in_stmts(name, stmt.body)
        if result == "read":
            return "read"
        # Catch body might execute
        catch_result = _first_access_in_stmts(name, stmt.catch_body)
        if catch_result == "read":
            return "read"
        return None
    return None


def _first_access_in_stmts(name: str, stmts: list[Stmt]) -> str | None:
    """Find first access type in a list of statements."""
    for stmt in stmts:
        result = _first_access_type(name, stmt)
        if result:
            return result
    return None


def _expr_reads(name: str, expr) -> bool:
    """Check if expression reads the variable."""
    if expr is None:
        return False
    if isinstance(expr, Var):
        return expr.name == name
    # Check all expression children
    for attr in (
        "obj",
        "left",
        "right",
        "operand",
        "cond",
        "then_expr",
        "else_expr",
        "expr",
        "index",
        "low",
        "high",
        "ptr",
        "value",
        "message",
        "pos",
        "iterable",
        "target",
        "inner",
        "on_type",
        "length",
        "capacity",
    ):
        if hasattr(expr, attr) and _expr_reads(name, getattr(expr, attr)):
            return True
    if hasattr(expr, "args"):
        for arg in expr.args:
            if _expr_reads(name, arg):
                return True
    if hasattr(expr, "elements"):
        for elem in expr.elements:
            if _expr_reads(name, elem):
                return True
    if hasattr(expr, "parts"):
        for part in expr.parts:
            if _expr_reads(name, part):
                return True
    if hasattr(expr, "entries"):
        entries = expr.entries
        if isinstance(entries, dict):
            for v in entries.values():
                if _expr_reads(name, v):
                    return True
        else:
            for item in entries:
                if isinstance(item, tuple) and len(item) == 2:
                    if _expr_reads(name, item[1]):
                        return True
    if hasattr(expr, "fields") and isinstance(expr.fields, dict):
        for v in expr.fields.values():
            if _expr_reads(name, v):
                return True
    return False


def _lvalue_reads(name: str, lv) -> bool:
    """Check if lvalue reads the variable (e.g., arr[i] reads arr and i)."""
    if isinstance(lv, VarLV):
        return False  # Simple var assignment doesn't read
    elif isinstance(lv, IndexLV):
        return _expr_reads(name, lv.obj) or _expr_reads(name, lv.index)
    elif isinstance(lv, FieldLV):
        return _expr_reads(name, lv.obj)
    elif isinstance(lv, DerefLV):
        return _expr_reads(name, lv.ptr)
    return False


def iter_all_stmts(stmts: list[Stmt]):
    """Iterate over all statements recursively."""
    for stmt in stmts:
        yield stmt
        if isinstance(stmt, If):
            yield from iter_all_stmts(stmt.then_body)
            yield from iter_all_stmts(stmt.else_body)
        elif isinstance(stmt, While):
            yield from iter_all_stmts(stmt.body)
        elif isinstance(stmt, ForRange):
            yield from iter_all_stmts(stmt.body)
        elif isinstance(stmt, ForClassic):
            yield from iter_all_stmts(stmt.body)
        elif isinstance(stmt, Block):
            yield from iter_all_stmts(stmt.body)
        elif isinstance(stmt, TryCatch):
            yield from iter_all_stmts(stmt.body)
            yield from iter_all_stmts(stmt.catch_body)
        elif isinstance(stmt, (Match, TypeSwitch)):
            for case in stmt.cases:
                yield from iter_all_stmts(case.body)
            yield from iter_all_stmts(stmt.default)


def _analyze_unused_tuple_targets(func: Function) -> None:
    """Mark indices of unused tuple targets for emitting _ in Go."""
    used_vars = _collect_used_vars(func.body)
    for stmt in iter_all_stmts(func.body):
        if isinstance(stmt, TupleAssign):
            unused = []
            for i, t in enumerate(stmt.targets):
                if isinstance(t, VarLV) and t.name != "_" and t.name not in used_vars:
                    unused.append(i)
            if unused:
                stmt.unused_indices = unused
