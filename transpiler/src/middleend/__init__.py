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

from .liveness import analyze_liveness, iter_all_stmts
from .returns import analyze_returns, always_returns, contains_return
from .scope import analyze_scope, _collect_assigned_vars, _collect_used_vars


def analyze(module: Module) -> None:
    """Run all analysis passes, annotating IR nodes in place."""
    analyze_scope(module)
    analyze_liveness(module)  # Sets has_catch_returns on TryCatch
    analyze_returns(module)  # Check if functions need named returns (must be after initial_value_usage)
    _analyze_hoisting_all(module)


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


