"""IR analysis passes (read-only, no transformations).

Annotations added (see scope.py for scope-related annotations):
    VarDecl.initial_value_unused: bool - initial value overwritten before any read
    TryCatch.hoisted_vars: list[tuple[str, Type | None]] - variables needing hoisting
    TryCatch.catch_var_unused: bool - catch variable is never referenced
    If.hoisted_vars: list[tuple[str, Type | None]] - variables needing hoisting from branches
"""

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
    Interface,
    Match,
    Module,
    OpAssign,
    Return,
    Stmt,
    TryCatch,
    Tuple,
    TupleAssign,
    Type,
    TypeSwitch,
    Var,
    VarDecl,
    VarLV,
    While,
)
from src.type_overrides import VAR_TYPE_OVERRIDES

from .returns import analyze_returns, always_returns, contains_return
from .scope import analyze_scope, _collect_assigned_vars, _collect_used_vars


def analyze(module: Module) -> None:
    """Run all analysis passes, annotating IR nodes in place."""
    analyze_scope(module)
    _analyze_initial_value_usage(module)  # Sets has_catch_returns on TryCatch
    analyze_returns(module)  # Check if functions need named returns (must be after initial_value_usage)
    _analyze_hoisting_all(module)
    _analyze_unused_tuple_targets_all(module)


# ============================================================
# INITIAL VALUE USAGE ANALYSIS
# ============================================================


def _analyze_initial_value_usage(module: Module) -> None:
    """Find VarDecls where initial value is overwritten before any read."""
    for func in module.functions:
        _analyze_initial_value_in_function(func)
    for struct in module.structs:
        for method in struct.methods:
            _analyze_initial_value_in_function(method)


def _analyze_initial_value_in_function(func: Function) -> None:
    """Analyze a function for unused initial values."""
    _analyze_initial_value_in_stmts(func.body)


def _analyze_initial_value_in_stmts(stmts: list[Stmt]) -> None:
    """Analyze statements for VarDecls with unused initial values."""
    for i, stmt in enumerate(stmts):
        if isinstance(stmt, VarDecl) and stmt.value is not None:
            stmt.initial_value_unused = _is_written_before_read(stmt.name, stmts[i + 1:])
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
    for attr in ('obj', 'left', 'right', 'operand', 'cond', 'then_expr', 'else_expr',
                 'expr', 'index', 'low', 'high', 'ptr', 'value', 'message', 'pos',
                 'iterable', 'target', 'inner', 'on_type', 'length', 'capacity'):
        if hasattr(expr, attr) and _expr_reads(name, getattr(expr, attr)):
            return True
    if hasattr(expr, 'args'):
        for arg in expr.args:
            if _expr_reads(name, arg):
                return True
    if hasattr(expr, 'elements'):
        for elem in expr.elements:
            if _expr_reads(name, elem):
                return True
    if hasattr(expr, 'parts'):
        for part in expr.parts:
            if _expr_reads(name, part):
                return True
    if hasattr(expr, 'entries'):
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
    if hasattr(expr, 'fields') and isinstance(expr.fields, dict):
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


# ============================================================
# VARIABLE HOISTING ANALYSIS
# ============================================================


def _merge_types(t1: Type | None, t2: Type | None) -> Type | None:
    """Merge two types, preferring concrete interface over Interface("any").

    When hoisting variables assigned in multiple branches:
    - If one branch assigns nil (Interface("any")) and another assigns Node, use Node
    - Go interfaces are nil-able, so Interface("Node") can hold nil without widening
    - If both are different Node subtypes, use Interface("Node") as the common type
    """
    if t1 is None:
        return t2
    if t2 is None:
        return t1
    if t1 == t2:
        return t1
    # Prefer named interface over "any" (nil gets typed as Interface("any"))
    if isinstance(t1, Interface) and t1.name == "any" and isinstance(t2, Interface):
        return t2
    if isinstance(t2, Interface) and t2.name == "any" and isinstance(t1, Interface):
        return t1
    # Prefer any concrete type over Interface("any")
    if isinstance(t1, Interface) and t1.name == "any":
        return t2
    if isinstance(t2, Interface) and t2.name == "any":
        return t1
    # If one is Interface("Node") and other is StructRef, use Interface("Node")
    if isinstance(t1, Interface) and t1.name == "Node":
        return t1
    if isinstance(t2, Interface) and t2.name == "Node":
        return t2
    # If both are different StructRefs, they're likely Node subtypes - use Interface("Node")
    # This handles cases like BraceGroup vs ArithmeticCommand assigned to same variable
    from .ir import StructRef
    if isinstance(t1, StructRef) and isinstance(t2, StructRef) and t1.name != t2.name:
        return Interface("Node")
    # Otherwise keep first type (arbitrary but deterministic)
    return t1


def _merge_var_types(result: dict[str, Type | None], new_vars: dict[str, Type | None]) -> None:
    """Merge new_vars into result, using type merging for conflicts."""
    for name, typ in new_vars.items():
        if name in result:
            result[name] = _merge_types(result[name], typ)
        else:
            result[name] = typ


def _vars_first_assigned_in(stmts: list[Stmt], already_declared: set[str]) -> dict[str, Type | None]:
    """Find variables first assigned in these statements (not already declared)."""
    result: dict[str, Type | None] = {}
    for stmt in stmts:
        if isinstance(stmt, Assign) and getattr(stmt, 'is_declaration', False):
            if isinstance(stmt.target, VarLV):
                name = stmt.target.name
                if name not in already_declared:
                    # Prefer decl_typ (unified type from frontend) over value.typ
                    new_type = getattr(stmt, 'decl_typ', None) or getattr(stmt.value, 'typ', None)
                    if name in result:
                        result[name] = _merge_types(result[name], new_type)
                    else:
                        result[name] = new_type
        elif isinstance(stmt, TupleAssign) and getattr(stmt, 'is_declaration', False):
            for i, target in enumerate(stmt.targets):
                if isinstance(target, VarLV):
                    name = target.name
                    if name not in already_declared and name not in result:
                        # Type from tuple element if available
                        val_typ = getattr(stmt.value, 'typ', None)
                        if isinstance(val_typ, Tuple) and i < len(val_typ.elements):
                            result[name] = val_typ.elements[i]
                        else:
                            result[name] = None
        # Recurse into nested structures
        elif isinstance(stmt, If):
            # For sibling branches, use the SAME already_declared set (before processing either branch)
            # This allows the same variable to be assigned in both branches with different types
            branch_declared = already_declared | set(result.keys())
            _merge_var_types(result, _vars_first_assigned_in(stmt.then_body, branch_declared))
            _merge_var_types(result, _vars_first_assigned_in(stmt.else_body, branch_declared))
        elif isinstance(stmt, While):
            _merge_var_types(result, _vars_first_assigned_in(stmt.body, already_declared | set(result.keys())))
        elif isinstance(stmt, ForRange):
            _merge_var_types(result, _vars_first_assigned_in(stmt.body, already_declared | set(result.keys())))
        elif isinstance(stmt, ForClassic):
            _merge_var_types(result, _vars_first_assigned_in(stmt.body, already_declared | set(result.keys())))
        elif isinstance(stmt, Block):
            _merge_var_types(result, _vars_first_assigned_in(stmt.body, already_declared | set(result.keys())))
        elif isinstance(stmt, TryCatch):
            # For try/catch, use the same pattern as if/else - both branches start fresh
            branch_declared = already_declared | set(result.keys())
            _merge_var_types(result, _vars_first_assigned_in(stmt.body, branch_declared))
            _merge_var_types(result, _vars_first_assigned_in(stmt.catch_body, branch_declared))
    return result


def _analyze_hoisting(func: Function) -> None:
    """Annotate TryCatch and If nodes with variables needing hoisting."""
    func_name = func.name
    # Collect function-level declared variables
    func_declared = set(p.name for p in func.params)
    for stmt in func.body:
        if isinstance(stmt, VarDecl):
            func_declared.add(stmt.name)

    def apply_type_overrides(hoisted: list[tuple[str, Type | None]]) -> list[tuple[str, Type | None]]:
        """Apply VAR_TYPE_OVERRIDES to hoisted variables."""
        result = []
        for name, typ in hoisted:
            override_key = (func_name, name)
            if override_key in VAR_TYPE_OVERRIDES:
                result.append((name, VAR_TYPE_OVERRIDES[override_key]))
            else:
                result.append((name, typ))
        return result

    def analyze_stmts(stmts: list[Stmt], outer_declared: set[str]) -> None:
        """Analyze statements, annotating nodes that need hoisting."""
        declared = set(outer_declared)

        for i, stmt in enumerate(stmts):
            if isinstance(stmt, TryCatch):
                # Find vars first assigned inside try/catch bodies
                inner_new = _vars_first_assigned_in(
                    stmt.body + stmt.catch_body, declared
                )

                # Find vars used after this statement
                used_after = _collect_used_vars(stmts[i + 1:])

                # Vars needing hoisting = first assigned inside AND used after
                needs_hoisting = [
                    (name, typ) for name, typ in inner_new.items()
                    if name in used_after
                ]
                stmt.hoisted_vars = apply_type_overrides(needs_hoisting)

                # These are now effectively declared for subsequent analysis
                declared.update(name for name, _ in needs_hoisting)

                # Recurse into try/catch bodies
                analyze_stmts(stmt.body, declared)
                analyze_stmts(stmt.catch_body, declared)

            elif isinstance(stmt, If):
                # Find vars first assigned inside if branches
                inner_new = _vars_first_assigned_in(
                    stmt.then_body + stmt.else_body, declared
                )

                # Find vars used after this statement
                used_after = _collect_used_vars(stmts[i + 1:])

                # Find vars assigned in then_body but used in else_body (cross-branch)
                then_new = _vars_first_assigned_in(stmt.then_body, declared)
                else_used = _collect_used_vars(stmt.else_body)

                # Vars needing hoisting = first assigned inside AND (used after OR cross-branch)
                needs_hoisting = []
                for name, typ in inner_new.items():
                    if name in used_after:
                        needs_hoisting.append((name, typ))
                    elif name in then_new and name in else_used:
                        needs_hoisting.append((name, typ))
                stmt.hoisted_vars = apply_type_overrides(needs_hoisting)

                # These are now effectively declared for subsequent analysis
                declared.update(name for name, _ in needs_hoisting)

                # Recurse into if branches
                if stmt.init:
                    analyze_stmts([stmt.init], declared)
                analyze_stmts(stmt.then_body, declared)
                analyze_stmts(stmt.else_body, declared)

            elif isinstance(stmt, VarDecl):
                declared.add(stmt.name)
            elif isinstance(stmt, Assign) and getattr(stmt, 'is_declaration', False):
                if isinstance(stmt.target, VarLV):
                    declared.add(stmt.target.name)
            elif isinstance(stmt, TupleAssign) and getattr(stmt, 'is_declaration', False):
                for target in stmt.targets:
                    if isinstance(target, VarLV):
                        declared.add(target.name)
            elif isinstance(stmt, While):
                # Find vars first assigned inside while body
                inner_new = _vars_first_assigned_in(stmt.body, declared)
                # Find vars used after this statement
                used_after = _collect_used_vars(stmts[i + 1:])
                # Vars needing hoisting = first assigned inside AND used after
                needs_hoisting = [
                    (name, typ) for name, typ in inner_new.items()
                    if name in used_after
                ]
                stmt.hoisted_vars = apply_type_overrides(needs_hoisting)
                # These are now effectively declared for subsequent analysis
                declared.update(name for name, _ in needs_hoisting)
                analyze_stmts(stmt.body, declared)
            elif isinstance(stmt, ForRange):
                # Find vars first assigned inside for body
                inner_new = _vars_first_assigned_in(stmt.body, declared)
                # Find vars used after this statement
                used_after = _collect_used_vars(stmts[i + 1:])
                # Vars needing hoisting = first assigned inside AND used after
                needs_hoisting = [
                    (name, typ) for name, typ in inner_new.items()
                    if name in used_after
                ]
                stmt.hoisted_vars = apply_type_overrides(needs_hoisting)
                # These are now effectively declared for subsequent analysis
                declared.update(name for name, _ in needs_hoisting)
                analyze_stmts(stmt.body, declared)
            elif isinstance(stmt, ForClassic):
                if stmt.init:
                    analyze_stmts([stmt.init], declared)
                analyze_stmts(stmt.body, declared)
            elif isinstance(stmt, Block):
                analyze_stmts(stmt.body, declared)
            elif isinstance(stmt, (Match, TypeSwitch)):
                # Only collect from cases that DON'T return (vars that might escape)
                # Cases that return keep their variables local (no need to hoist)
                non_returning_stmts: list[Stmt] = []
                for case in stmt.cases:
                    if not always_returns(case.body):
                        non_returning_stmts.extend(case.body)
                if not always_returns(stmt.default):
                    non_returning_stmts.extend(stmt.default)
                # Find vars first assigned inside non-returning branches
                inner_new = _vars_first_assigned_in(non_returning_stmts, declared)
                # Find vars used after this statement
                used_after = _collect_used_vars(stmts[i + 1:])
                # Vars needing hoisting = first assigned inside AND used after
                needs_hoisting = [
                    (name, typ) for name, typ in inner_new.items()
                    if name in used_after
                ]
                stmt.hoisted_vars = apply_type_overrides(needs_hoisting)
                # Update declared set
                declared.update(name for name, _ in needs_hoisting)
                # Recurse into case bodies
                for case in stmt.cases:
                    analyze_stmts(case.body, declared)
                analyze_stmts(stmt.default, declared)

    analyze_stmts(func.body, func_declared)


def _analyze_hoisting_all(module: Module) -> None:
    """Run hoisting analysis on all functions."""
    for func in module.functions:
        _analyze_hoisting(func)
    for struct in module.structs:
        for method in struct.methods:
            _analyze_hoisting(method)


def _iter_all_stmts(stmts: list[Stmt]):
    """Iterate over all statements recursively."""
    for stmt in stmts:
        yield stmt
        if isinstance(stmt, If):
            yield from _iter_all_stmts(stmt.then_body)
            yield from _iter_all_stmts(stmt.else_body)
        elif isinstance(stmt, While):
            yield from _iter_all_stmts(stmt.body)
        elif isinstance(stmt, ForRange):
            yield from _iter_all_stmts(stmt.body)
        elif isinstance(stmt, ForClassic):
            yield from _iter_all_stmts(stmt.body)
        elif isinstance(stmt, Block):
            yield from _iter_all_stmts(stmt.body)
        elif isinstance(stmt, TryCatch):
            yield from _iter_all_stmts(stmt.body)
            yield from _iter_all_stmts(stmt.catch_body)
        elif isinstance(stmt, (Match, TypeSwitch)):
            for case in stmt.cases:
                yield from _iter_all_stmts(case.body)
            yield from _iter_all_stmts(stmt.default)


def _analyze_unused_tuple_targets(func: Function) -> None:
    """Mark indices of unused tuple targets for emitting _ in Go."""
    used_vars = _collect_used_vars(func.body)
    for stmt in _iter_all_stmts(func.body):
        if isinstance(stmt, TupleAssign):
            unused = []
            for i, t in enumerate(stmt.targets):
                if isinstance(t, VarLV) and t.name != "_" and t.name not in used_vars:
                    unused.append(i)
            if unused:
                stmt.unused_indices = unused


def _analyze_unused_tuple_targets_all(module: Module) -> None:
    """Run unused tuple target analysis on all functions."""
    for func in module.functions:
        _analyze_unused_tuple_targets(func)
    for struct in module.structs:
        for method in struct.methods:
            _analyze_unused_tuple_targets(method)
