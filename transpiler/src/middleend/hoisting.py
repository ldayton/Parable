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
                        result[name] = join_types(result[name], new_type)
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
