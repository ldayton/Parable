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
from src.type_overrides import VAR_TYPE_OVERRIDES

from .returns import always_returns
from .scope import _collect_used_vars
from .type_flow import join_types


def analyze_hoisting(module: Module) -> None:
    """Run hoisting analysis on all functions."""
    for func in module.functions:
        _analyze_hoisting(func)
    for struct in module.structs:
        for method in struct.methods:
            _analyze_hoisting(method)


def _merge_var_types(result: dict[str, Type | None], new_vars: dict[str, Type | None]) -> None:
    """Merge new_vars into result, using type joining for conflicts."""
    for name, typ in new_vars.items():
        if name in result:
            result[name] = join_types(result[name], typ)
        else:
            result[name] = typ


def _vars_first_assigned_in(
    stmts: list[Stmt], already_declared: set[str]
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
                        result[name] = join_types(result[name], new_type)
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
            _merge_var_types(result, _vars_first_assigned_in(stmt.then_body, branch_declared))
            _merge_var_types(result, _vars_first_assigned_in(stmt.else_body, branch_declared))
        elif isinstance(stmt, While):
            _merge_var_types(
                result, _vars_first_assigned_in(stmt.body, already_declared | set(result.keys()))
            )
        elif isinstance(stmt, ForRange):
            _merge_var_types(
                result, _vars_first_assigned_in(stmt.body, already_declared | set(result.keys()))
            )
        elif isinstance(stmt, ForClassic):
            _merge_var_types(
                result, _vars_first_assigned_in(stmt.body, already_declared | set(result.keys()))
            )
        elif isinstance(stmt, Block):
            _merge_var_types(
                result, _vars_first_assigned_in(stmt.body, already_declared | set(result.keys()))
            )
        elif isinstance(stmt, TryCatch):
            # For try/catch, use the same pattern as if/else - both branches start fresh
            branch_declared = already_declared | set(result.keys())
            _merge_var_types(result, _vars_first_assigned_in(stmt.body, branch_declared))
            _merge_var_types(result, _vars_first_assigned_in(stmt.catch_body, branch_declared))
    return result


def _apply_type_overrides(
    func_name: str, hoisted: list[tuple[str, Type | None]]
) -> list[tuple[str, Type | None]]:
    """Apply VAR_TYPE_OVERRIDES to hoisted variables."""
    result: list[tuple[str, Type | None]] = []
    for name, typ in hoisted:
        override_key = (func_name, name)
        if override_key in VAR_TYPE_OVERRIDES:
            result.append((name, VAR_TYPE_OVERRIDES[override_key]))
        else:
            result.append((name, typ))
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


def _analyze_stmts(
    func_name: str, stmts: list[Stmt], outer_declared: set[str]
) -> None:
    """Analyze statements, annotating nodes that need hoisting."""
    declared = set(outer_declared)
    for i, stmt in enumerate(stmts):
        if isinstance(stmt, TryCatch):
            inner_new = _vars_first_assigned_in(stmt.body + stmt.catch_body, declared)
            used_after = _collect_used_vars(stmts[i + 1 :])
            needs_hoisting = _filter_hoisted_vars(inner_new, used_after)
            stmt.hoisted_vars = _apply_type_overrides(func_name, needs_hoisting)
            _update_declared_from_hoisted(declared, needs_hoisting)
            _analyze_stmts(func_name, stmt.body, declared)
            _analyze_stmts(func_name, stmt.catch_body, declared)
        elif isinstance(stmt, If):
            inner_new = _vars_first_assigned_in(stmt.then_body + stmt.else_body, declared)
            used_after = _collect_used_vars(stmts[i + 1 :])
            then_new = _vars_first_assigned_in(stmt.then_body, declared)
            else_used = _collect_used_vars(stmt.else_body)
            needs_hoisting: list[tuple[str, Type | None]] = []
            for name, typ in inner_new.items():
                if name in used_after:
                    needs_hoisting.append((name, typ))
                elif name in then_new and name in else_used:
                    needs_hoisting.append((name, typ))
            stmt.hoisted_vars = _apply_type_overrides(func_name, needs_hoisting)
            _update_declared_from_hoisted(declared, needs_hoisting)
            if stmt.init:
                _analyze_stmts(func_name, [stmt.init], declared)
            _analyze_stmts(func_name, stmt.then_body, declared)
            _analyze_stmts(func_name, stmt.else_body, declared)
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
            inner_new = _vars_first_assigned_in(stmt.body, declared)
            used_after = _collect_used_vars(stmts[i + 1 :])
            needs_hoisting = _filter_hoisted_vars(inner_new, used_after)
            stmt.hoisted_vars = _apply_type_overrides(func_name, needs_hoisting)
            _update_declared_from_hoisted(declared, needs_hoisting)
            _analyze_stmts(func_name, stmt.body, declared)
        elif isinstance(stmt, ForRange):
            inner_new = _vars_first_assigned_in(stmt.body, declared)
            used_after = _collect_used_vars(stmts[i + 1 :])
            needs_hoisting = _filter_hoisted_vars(inner_new, used_after)
            stmt.hoisted_vars = _apply_type_overrides(func_name, needs_hoisting)
            _update_declared_from_hoisted(declared, needs_hoisting)
            _analyze_stmts(func_name, stmt.body, declared)
        elif isinstance(stmt, ForClassic):
            if stmt.init:
                _analyze_stmts(func_name, [stmt.init], declared)
            _analyze_stmts(func_name, stmt.body, declared)
        elif isinstance(stmt, Block):
            _analyze_stmts(func_name, stmt.body, declared)
        elif isinstance(stmt, (Match, TypeSwitch)):
            non_returning_stmts: list[Stmt] = []
            for case in stmt.cases:
                if not always_returns(case.body):
                    non_returning_stmts.extend(case.body)
            if not always_returns(stmt.default):
                non_returning_stmts.extend(stmt.default)
            inner_new = _vars_first_assigned_in(non_returning_stmts, declared)
            used_after = _collect_used_vars(stmts[i + 1 :])
            needs_hoisting = _filter_hoisted_vars(inner_new, used_after)
            stmt.hoisted_vars = _apply_type_overrides(func_name, needs_hoisting)
            _update_declared_from_hoisted(declared, needs_hoisting)
            for case in stmt.cases:
                _analyze_stmts(func_name, case.body, declared)
            _analyze_stmts(func_name, stmt.default, declared)


def _analyze_hoisting(func: Function) -> None:
    """Annotate TryCatch and If nodes with variables needing hoisting."""
    func_name = func.name
    func_declared: set[str] = set()
    for p in func.params:
        func_declared.add(p.name)
    for stmt in func.body:
        if isinstance(stmt, VarDecl):
            func_declared.add(stmt.name)
    _analyze_stmts(func_name, func.body, func_declared)
