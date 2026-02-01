"""Hoisting analysis: compute variables needing hoisting for Go emission."""

from src.ir import (
    Assign,
    Block,
    ForClassic,
    ForRange,
    Function,
    If,
    Match,
    Module,
    Primitive,
    Slice,
    Stmt,
    TryCatch,
    Tuple,
    TupleAssign,
    Type,
    TypeSwitch,
    VarDecl,
    VarLV,
    While,
)

from .returns import always_returns
from .scope import _collect_assigned_vars, _collect_used_vars
from .type_flow import join_types


def analyze_hoisting(module: Module) -> None:
    """Run hoisting analysis on all functions."""
    hierarchy_root = module.hierarchy_root
    for func in module.functions:
        _analyze_hoisting(func, hierarchy_root)
    for struct in module.structs:
        for method in struct.methods:
            _analyze_hoisting(method, hierarchy_root)


def _merge_var_types(
    result: dict[str, Type | None], new_vars: dict[str, Type | None], hierarchy_root: str | None = None
) -> None:
    """Merge new_vars into result, using type joining for conflicts."""
    for name, typ in new_vars.items():
        if name in result:
            result[name] = join_types(result[name], typ, hierarchy_root)
        else:
            result[name] = typ


def _vars_first_assigned_in(
    stmts: list[Stmt], already_declared: set[str], hierarchy_root: str | None = None
) -> dict[str, Type | None]:
    """Find variables first assigned in these statements (not already declared)."""
    result: dict[str, Type | None] = {}
    for stmt in stmts:
        if isinstance(stmt, Assign) and stmt.is_declaration:
            if isinstance(stmt.target, VarLV):
                name = stmt.target.name
                if name not in already_declared:
                    # Prefer decl_typ (unified type from frontend) over value.typ
                    new_type = stmt.decl_typ if stmt.decl_typ is not None else stmt.value.typ
                    if name in result:
                        result[name] = join_types(result[name], new_type, hierarchy_root)
                    else:
                        result[name] = new_type
        elif isinstance(stmt, TupleAssign) and stmt.is_declaration:
            for i, target in enumerate(stmt.targets):
                if isinstance(target, VarLV):
                    name = target.name
                    if name not in already_declared and name not in result:
                        # Type from tuple element if available
                        val_typ = stmt.value.typ
                        if isinstance(val_typ, Tuple) and i < len(val_typ.elements):
                            result[name] = val_typ.elements[i]
                        else:
                            result[name] = None
        # Recurse into nested structures
        elif isinstance(stmt, If):
            # For sibling branches, use the SAME already_declared set (before processing either branch)
            # This allows the same variable to be assigned in both branches with different types
            branch_declared = already_declared | set(result.keys())
            _merge_var_types(result, _vars_first_assigned_in(stmt.then_body, branch_declared, hierarchy_root), hierarchy_root)
            _merge_var_types(result, _vars_first_assigned_in(stmt.else_body, branch_declared, hierarchy_root), hierarchy_root)
        elif isinstance(stmt, While):
            _merge_var_types(
                result, _vars_first_assigned_in(stmt.body, already_declared | set(result.keys()), hierarchy_root), hierarchy_root
            )
        elif isinstance(stmt, ForRange):
            _merge_var_types(
                result, _vars_first_assigned_in(stmt.body, already_declared | set(result.keys()), hierarchy_root), hierarchy_root
            )
        elif isinstance(stmt, ForClassic):
            _merge_var_types(
                result, _vars_first_assigned_in(stmt.body, already_declared | set(result.keys()), hierarchy_root), hierarchy_root
            )
        elif isinstance(stmt, Block):
            _merge_var_types(
                result, _vars_first_assigned_in(stmt.body, already_declared | set(result.keys()), hierarchy_root), hierarchy_root
            )
        elif isinstance(stmt, TryCatch):
            # For try/catch, use the same pattern as if/else - both branches start fresh
            branch_declared = already_declared | set(result.keys())
            _merge_var_types(result, _vars_first_assigned_in(stmt.body, branch_declared, hierarchy_root), hierarchy_root)
            _merge_var_types(result, _vars_first_assigned_in(stmt.catch_body, branch_declared, hierarchy_root), hierarchy_root)
    return result


def _filter_hoisted_vars(
    inner_new: dict[str, Type | None], used_after: set[str]
) -> list[tuple[str, Type | None]]:
    """Filter variables that need hoisting (assigned inside AND used after)."""
    result: list[tuple[str, Type | None]] = []
    for name, typ in inner_new.items():
        if name in used_after:
            result.append((name, typ))
    return result


def _update_declared_from_hoisted(
    declared: set[str], needs_hoisting: list[tuple[str, Type | None]]
) -> None:
    """Update declared set with hoisted variable names."""
    for name, _ in needs_hoisting:
        declared.add(name)


def _collect_conflicting_loop_vars(
    stmts: list[Stmt], all_func_assigned: set[str]
) -> list[tuple[str, Type | None]]:
    """Collect ForRange loop variables that conflict with function-level assignments."""
    result: list[tuple[str, Type | None]] = []
    for stmt in stmts:
        if isinstance(stmt, ForRange):
            if stmt.value and stmt.value in all_func_assigned:
                elem_type: Type | None = None
                if isinstance(stmt.iterable.typ, Slice):
                    elem_type = stmt.iterable.typ.element
                elif isinstance(stmt.iterable.typ, Primitive) and stmt.iterable.typ.kind == "string":
                    elem_type = Primitive("string")
                result.append((stmt.value, elem_type))
            if stmt.index and stmt.index in all_func_assigned:
                result.append((stmt.index, Primitive("int")))
            result.extend(_collect_conflicting_loop_vars(stmt.body, all_func_assigned))
        elif isinstance(stmt, If):
            result.extend(_collect_conflicting_loop_vars(stmt.then_body, all_func_assigned))
            result.extend(_collect_conflicting_loop_vars(stmt.else_body, all_func_assigned))
        elif isinstance(stmt, While):
            result.extend(_collect_conflicting_loop_vars(stmt.body, all_func_assigned))
        elif isinstance(stmt, ForClassic):
            result.extend(_collect_conflicting_loop_vars(stmt.body, all_func_assigned))
        elif isinstance(stmt, Block):
            result.extend(_collect_conflicting_loop_vars(stmt.body, all_func_assigned))
        elif isinstance(stmt, TryCatch):
            result.extend(_collect_conflicting_loop_vars(stmt.body, all_func_assigned))
            result.extend(_collect_conflicting_loop_vars(stmt.catch_body, all_func_assigned))
        elif isinstance(stmt, (Match, TypeSwitch)):
            for case in stmt.cases:
                result.extend(_collect_conflicting_loop_vars(case.body, all_func_assigned))
            result.extend(_collect_conflicting_loop_vars(stmt.default, all_func_assigned))
    return result


def _analyze_stmts(
    func_name: str,
    stmts: list[Stmt],
    outer_declared: set[str],
    all_func_assigned: set[str] | None = None,
    hierarchy_root: str | None = None,
) -> None:
    """Analyze statements, annotating nodes that need hoisting."""
    declared = set(outer_declared)
    if all_func_assigned is None:
        all_func_assigned = set()
    for i, stmt in enumerate(stmts):
        if isinstance(stmt, TryCatch):
            inner_new = _vars_first_assigned_in(stmt.body + stmt.catch_body, declared, hierarchy_root)
            used_after = _collect_used_vars(stmts[i + 1 :])
            needs_hoisting = _filter_hoisted_vars(inner_new, used_after)
            stmt.hoisted_vars = needs_hoisting
            _update_declared_from_hoisted(declared, needs_hoisting)
            _analyze_stmts(func_name, stmt.body, declared, all_func_assigned, hierarchy_root)
            _analyze_stmts(func_name, stmt.catch_body, declared, all_func_assigned, hierarchy_root)
        elif isinstance(stmt, If):
            inner_new = _vars_first_assigned_in(stmt.then_body + stmt.else_body, declared, hierarchy_root)
            used_after = _collect_used_vars(stmts[i + 1 :])
            then_new = _vars_first_assigned_in(stmt.then_body, declared, hierarchy_root)
            else_used = _collect_used_vars(stmt.else_body)
            needs_hoisting: list[tuple[str, Type | None]] = []
            for name, typ in inner_new.items():
                if name in used_after:
                    needs_hoisting.append((name, typ))
                elif name in then_new and name in else_used:
                    needs_hoisting.append((name, typ))
            stmt.hoisted_vars = needs_hoisting
            _update_declared_from_hoisted(declared, needs_hoisting)
            if stmt.init:
                _analyze_stmts(func_name, [stmt.init], declared, all_func_assigned, hierarchy_root)
            _analyze_stmts(func_name, stmt.then_body, declared, all_func_assigned, hierarchy_root)
            _analyze_stmts(func_name, stmt.else_body, declared, all_func_assigned, hierarchy_root)
        elif isinstance(stmt, VarDecl):
            declared.add(stmt.name)
        elif isinstance(stmt, Assign) and stmt.is_declaration:
            if isinstance(stmt.target, VarLV):
                declared.add(stmt.target.name)
        elif isinstance(stmt, TupleAssign) and stmt.is_declaration:
            for target in stmt.targets:
                if isinstance(target, VarLV):
                    declared.add(target.name)
        elif isinstance(stmt, While):
            inner_new = _vars_first_assigned_in(stmt.body, declared, hierarchy_root)
            used_after = _collect_used_vars(stmts[i + 1 :])
            needs_hoisting = _filter_hoisted_vars(inner_new, used_after)
            # Also hoist ForRange loop variables that conflict with function-level assignments
            loop_var_conflicts = _collect_conflicting_loop_vars(stmt.body, all_func_assigned)
            for var_tuple in loop_var_conflicts:
                if var_tuple not in needs_hoisting:
                    needs_hoisting.append(var_tuple)
            stmt.hoisted_vars = needs_hoisting
            _update_declared_from_hoisted(declared, needs_hoisting)
            _analyze_stmts(func_name, stmt.body, declared, all_func_assigned, hierarchy_root)
        elif isinstance(stmt, ForRange):
            inner_new = _vars_first_assigned_in(stmt.body, declared, hierarchy_root)
            used_after = _collect_used_vars(stmts[i + 1 :])
            needs_hoisting = _filter_hoisted_vars(inner_new, used_after)
            # Note: Loop variable hoisting is now handled at the enclosing While level
            # by _collect_conflicting_loop_vars
            stmt.hoisted_vars = needs_hoisting
            _update_declared_from_hoisted(declared, needs_hoisting)
            _analyze_stmts(func_name, stmt.body, declared, all_func_assigned, hierarchy_root)
        elif isinstance(stmt, ForClassic):
            if stmt.init:
                _analyze_stmts(func_name, [stmt.init], declared, all_func_assigned, hierarchy_root)
            _analyze_stmts(func_name, stmt.body, declared, all_func_assigned, hierarchy_root)
        elif isinstance(stmt, Block):
            _analyze_stmts(func_name, stmt.body, declared, all_func_assigned, hierarchy_root)
        elif isinstance(stmt, (Match, TypeSwitch)):
            non_returning_stmts: list[Stmt] = []
            all_case_stmts: list[Stmt] = []
            for case in stmt.cases:
                all_case_stmts.extend(case.body)
                if not always_returns(case.body):
                    non_returning_stmts.extend(case.body)
            all_case_stmts.extend(stmt.default)
            if not always_returns(stmt.default):
                non_returning_stmts.extend(stmt.default)
            inner_new = _vars_first_assigned_in(non_returning_stmts, declared, hierarchy_root)
            # Also get all assignments in ALL case bodies (including returning ones)
            all_inner = _vars_first_assigned_in(all_case_stmts, declared, hierarchy_root)
            used_after = _collect_used_vars(stmts[i + 1 :])
            assigned_after = _collect_assigned_vars(stmts[i + 1 :])
            needs_hoisting: list[tuple[str, Type | None]] = []
            # Hoist if assigned inside AND (used or assigned) after
            for name, typ in inner_new.items():
                if name in used_after or name in assigned_after:
                    needs_hoisting.append((name, typ))
            # Also hoist if assigned in ANY case AND assigned after (to avoid C# shadowing)
            for name, typ in all_inner.items():
                if name in assigned_after and (name, typ) not in needs_hoisting:
                    needs_hoisting.append((name, typ))
            # Also hoist ForRange loop variables that conflict with function-level assignments
            loop_var_conflicts = _collect_conflicting_loop_vars(all_case_stmts, all_func_assigned)
            for var_tuple in loop_var_conflicts:
                if var_tuple not in needs_hoisting:
                    needs_hoisting.append(var_tuple)
            stmt.hoisted_vars = needs_hoisting
            _update_declared_from_hoisted(declared, needs_hoisting)
            for case in stmt.cases:
                _analyze_stmts(func_name, case.body, declared, all_func_assigned, hierarchy_root)
            _analyze_stmts(func_name, stmt.default, declared, all_func_assigned, hierarchy_root)


def _analyze_hoisting(func: Function, hierarchy_root: str | None = None) -> None:
    """Annotate TryCatch and If nodes with variables needing hoisting."""
    func_name = func.name
    func_declared: set[str] = set()
    for p in func.params:
        func_declared.add(p.name)
    for stmt in func.body:
        if isinstance(stmt, VarDecl):
            func_declared.add(stmt.name)
    # Collect ALL variables assigned anywhere in the function
    all_func_assigned = _collect_assigned_vars(func.body)
    _analyze_stmts(func_name, func.body, func_declared, all_func_assigned, hierarchy_root)
