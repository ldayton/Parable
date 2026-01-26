"""IR analysis passes (read-only, no transformations).

Annotations added:
    VarDecl.is_reassigned: bool  - variable is assigned after its declaration
    Param.is_modified: bool      - parameter is assigned/mutated in function body
    Param.is_unused: bool        - parameter is never referenced in function body
    Assign.is_declaration: bool  - first assignment to a new variable
    TupleAssign.is_declaration: bool - first assignment to new variables
    TryCatch.hoisted_vars: list[tuple[str, Type | None]] - variables needing hoisting
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
    Match,
    MethodCall,
    Module,
    OpAssign,
    Param,
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


def analyze(module: Module) -> None:
    """Run all analysis passes, annotating IR nodes in place."""
    _analyze_reassignments(module)
    _analyze_hoisting_all(module)


def _collect_assigned_vars(stmts: list[Stmt]) -> set[str]:
    """Collect variable names that are assigned in a list of statements."""
    result: set[str] = set()
    for stmt in stmts:
        if isinstance(stmt, Assign):
            if isinstance(stmt.target, VarLV):
                result.add(stmt.target.name)
        elif isinstance(stmt, TupleAssign):
            for target in stmt.targets:
                if isinstance(target, VarLV):
                    result.add(target.name)
        elif isinstance(stmt, If):
            result.update(_collect_assigned_vars(stmt.then_body))
            result.update(_collect_assigned_vars(stmt.else_body))
        elif isinstance(stmt, While):
            result.update(_collect_assigned_vars(stmt.body))
        elif isinstance(stmt, ForRange):
            result.update(_collect_assigned_vars(stmt.body))
        elif isinstance(stmt, ForClassic):
            result.update(_collect_assigned_vars(stmt.body))
        elif isinstance(stmt, Block):
            result.update(_collect_assigned_vars(stmt.body))
        elif isinstance(stmt, TryCatch):
            result.update(_collect_assigned_vars(stmt.body))
            result.update(_collect_assigned_vars(stmt.catch_body))
    return result


def _collect_used_vars(stmts: list[Stmt]) -> set[str]:
    """Collect all variable names referenced in statements and expressions."""
    result: set[str] = set()

    def visit_expr(expr) -> None:
        if expr is None:
            return
        if isinstance(expr, Var):
            result.add(expr.name)
        # Recursively visit all expression attributes
        for attr in ('obj', 'left', 'right', 'operand', 'cond', 'then_expr', 'else_expr',
                     'expr', 'index', 'low', 'high', 'ptr', 'value', 'message', 'pos',
                     'iterable', 'target', 'inner', 'on_type', 'length', 'capacity'):
            if hasattr(expr, attr):
                visit_expr(getattr(expr, attr))
        if hasattr(expr, 'args'):
            for arg in expr.args:
                visit_expr(arg)
        if hasattr(expr, 'elements'):
            for elem in expr.elements:
                visit_expr(elem)
        if hasattr(expr, 'parts'):
            for part in expr.parts:
                visit_expr(part)
        if hasattr(expr, 'entries'):
            entries = expr.entries
            if isinstance(entries, dict):
                for v in entries.values():
                    visit_expr(v)
            else:
                for item in entries:
                    if isinstance(item, tuple) and len(item) == 2:
                        visit_expr(item[1])
        if hasattr(expr, 'fields') and isinstance(expr.fields, dict):
            for v in expr.fields.values():
                visit_expr(v)

    def visit_stmt(stmt: Stmt) -> None:
        if isinstance(stmt, VarDecl):
            if stmt.value:
                visit_expr(stmt.value)
        elif isinstance(stmt, (Assign, OpAssign)):
            visit_expr(stmt.value)
            # Also check lvalue targets for variable usage
            target = stmt.target
            if hasattr(target, 'obj'):
                visit_expr(target.obj)
            if hasattr(target, 'index'):
                visit_expr(target.index)
            if hasattr(target, 'ptr'):
                visit_expr(target.ptr)
        elif isinstance(stmt, TupleAssign):
            visit_expr(stmt.value)
        elif isinstance(stmt, ExprStmt):
            visit_expr(stmt.expr)
        elif isinstance(stmt, Return):
            if stmt.value:
                visit_expr(stmt.value)
        elif isinstance(stmt, If):
            visit_expr(stmt.cond)
            if stmt.init:
                visit_stmt(stmt.init)
            for s in stmt.then_body:
                visit_stmt(s)
            for s in stmt.else_body:
                visit_stmt(s)
        elif isinstance(stmt, While):
            visit_expr(stmt.cond)
            for s in stmt.body:
                visit_stmt(s)
        elif isinstance(stmt, ForRange):
            visit_expr(stmt.iterable)
            for s in stmt.body:
                visit_stmt(s)
        elif isinstance(stmt, ForClassic):
            if stmt.init:
                visit_stmt(stmt.init)
            if stmt.cond:
                visit_expr(stmt.cond)
            if stmt.post:
                visit_stmt(stmt.post)
            for s in stmt.body:
                visit_stmt(s)
        elif isinstance(stmt, Block):
            for s in stmt.body:
                visit_stmt(s)
        elif isinstance(stmt, TryCatch):
            for s in stmt.body:
                visit_stmt(s)
            for s in stmt.catch_body:
                visit_stmt(s)
        elif isinstance(stmt, Match):
            visit_expr(stmt.expr)
            for case in stmt.cases:
                for s in case.body:
                    visit_stmt(s)
            for s in stmt.default:
                visit_stmt(s)
        elif isinstance(stmt, TypeSwitch):
            visit_expr(stmt.expr)
            for case in stmt.cases:
                for s in case.body:
                    visit_stmt(s)
            for s in stmt.default:
                visit_stmt(s)

    for stmt in stmts:
        visit_stmt(stmt)
    return result


def _analyze_reassignments(module: Module) -> None:
    """Find variables and parameters that are reassigned/modified."""
    for func in module.functions:
        _analyze_function(func)
    for struct in module.structs:
        for method in struct.methods:
            _analyze_function(method)


def _analyze_function(func: Function) -> None:
    """Analyze a single function for reassignments."""
    declared: dict[str, VarDecl] = {}
    assigned: set[str] = set()  # Variables already assigned (for is_declaration)
    params: dict[str, Param] = {p.name: p for p in func.params}

    # Initialize annotations
    for p in func.params:
        p.is_modified = False
        p.is_unused = False
        assigned.add(p.name)  # Parameters are already "assigned"

    # Collect all referenced variable names
    used_vars: set[str] = _collect_used_vars(func.body)

    def mark_reassigned(name: str) -> None:
        if name in declared:
            declared[name].is_reassigned = True
        elif name in params:
            params[name].is_modified = True

    def is_new_declaration(lv, local_assigned: set[str]) -> bool:
        """Check if this lvalue represents a first assignment to a variable."""
        if isinstance(lv, VarLV):
            # Check against parameters and local_assigned (which includes VarDecls in current branch)
            return lv.name not in params and lv.name not in local_assigned
        return False

    def check_lvalue(lv) -> None:
        """Mark the base variable of an lvalue as modified."""
        if isinstance(lv, VarLV):
            mark_reassigned(lv.name)
        elif isinstance(lv, IndexLV):
            if isinstance(lv.obj, Var):
                mark_reassigned(lv.obj.name)
        elif isinstance(lv, FieldLV):
            if isinstance(lv.obj, Var):
                mark_reassigned(lv.obj.name)
        elif isinstance(lv, DerefLV):
            if isinstance(lv.ptr, Var):
                mark_reassigned(lv.ptr.name)

    def check_stmt(stmt: Stmt, local_assigned: set[str] | None = None) -> None:
        if local_assigned is None:
            local_assigned = set()
        if isinstance(stmt, VarDecl):
            stmt.is_reassigned = False
            declared[stmt.name] = stmt
            local_assigned.add(stmt.name)  # Add to branch-local, not global
            if stmt.value:
                check_expr(stmt.value)
        elif isinstance(stmt, Assign):
            # Determine if this is a declaration (first assignment to new variable)
            stmt.is_declaration = is_new_declaration(stmt.target, local_assigned)
            if isinstance(stmt.target, VarLV) and stmt.is_declaration:
                local_assigned.add(stmt.target.name)
                # Note: Don't add to outer 'assigned' - if-else branches need separate scopes
            check_lvalue(stmt.target)
            check_expr(stmt.value)
        elif isinstance(stmt, OpAssign):
            check_lvalue(stmt.target)
            check_expr(stmt.value)
        elif isinstance(stmt, TupleAssign):
            # Check if all targets are new declarations
            all_new = True
            new_targets: list[str] = []
            for target in stmt.targets:
                if isinstance(target, VarLV):
                    if (target.name in assigned or target.name in declared or
                        target.name in params or target.name in local_assigned):
                        all_new = False
                    else:
                        new_targets.append(target.name)
                        local_assigned.add(target.name)
                else:
                    all_new = False
            stmt.is_declaration = all_new
            stmt.new_targets = new_targets  # Track which specific targets are new
            for target in stmt.targets:
                if isinstance(target, VarLV) and not stmt.is_declaration:
                    mark_reassigned(target.name)
            check_expr(stmt.value)
        elif isinstance(stmt, ExprStmt):
            check_expr(stmt.expr)
        elif isinstance(stmt, Return):
            if stmt.value:
                check_expr(stmt.value)
        elif isinstance(stmt, If):
            check_expr(stmt.cond)
            if stmt.init:
                check_stmt(stmt.init, local_assigned)
            # Each branch inherits parent's assignments so they can see outer declarations
            # But siblings don't see each other's declarations
            then_assigned: set[str] = set(local_assigned)
            for s in stmt.then_body:
                check_stmt(s, then_assigned)
            else_assigned: set[str] = set(local_assigned)
            for s in stmt.else_body:
                check_stmt(s, else_assigned)
        elif isinstance(stmt, While):
            check_expr(stmt.cond)
            for s in stmt.body:
                check_stmt(s, local_assigned)
        elif isinstance(stmt, ForRange):
            for s in stmt.body:
                check_stmt(s, local_assigned)
        elif isinstance(stmt, ForClassic):
            if stmt.init:
                check_stmt(stmt.init, local_assigned)
            if stmt.cond:
                check_expr(stmt.cond)
            if stmt.post:
                check_stmt(stmt.post, local_assigned)
            for s in stmt.body:
                check_stmt(s, local_assigned)
        elif isinstance(stmt, Block):
            for s in stmt.body:
                check_stmt(s, local_assigned)
        elif isinstance(stmt, TryCatch):
            # TryCatch body is wrapped in a closure in Go
            # Closures CAN access outer variables, so inherit parent's assignments
            # But new declarations inside the closure can't escape
            try_assigned: set[str] = set(local_assigned)
            for s in stmt.body:
                check_stmt(s, try_assigned)
            catch_assigned: set[str] = set(local_assigned)
            for s in stmt.catch_body:
                check_stmt(s, catch_assigned)
        elif isinstance(stmt, Match):
            check_expr(stmt.expr)
            for case in stmt.cases:
                case_assigned: set[str] = set()
                for s in case.body:
                    check_stmt(s, case_assigned)
            default_assigned: set[str] = set()
            for s in stmt.default:
                check_stmt(s, default_assigned)
        elif isinstance(stmt, TypeSwitch):
            check_expr(stmt.expr)
            for case in stmt.cases:
                case_assigned: set[str] = set()
                for s in case.body:
                    check_stmt(s, case_assigned)
            default_assigned: set[str] = set()
            for s in stmt.default:
                check_stmt(s, default_assigned)

    def check_expr(expr) -> None:
        """Check for mutating method calls on declared variables."""
        if isinstance(expr, MethodCall):
            if isinstance(expr.obj, Var):
                mark_reassigned(expr.obj.name)
            check_expr(expr.obj)
            for arg in expr.args:
                check_expr(arg)

    func_assigned: set[str] = set()
    for stmt in func.body:
        check_stmt(stmt, func_assigned)

    # Mark unused parameters
    for p in func.params:
        if p.name not in used_vars:
            p.is_unused = True


# ============================================================
# VARIABLE HOISTING ANALYSIS
# ============================================================


def _vars_first_assigned_in(stmts: list[Stmt], already_declared: set[str]) -> dict[str, Type | None]:
    """Find variables first assigned in these statements (not already declared)."""
    result: dict[str, Type | None] = {}
    for stmt in stmts:
        if isinstance(stmt, Assign) and getattr(stmt, 'is_declaration', False):
            if isinstance(stmt.target, VarLV):
                name = stmt.target.name
                if name not in already_declared and name not in result:
                    result[name] = getattr(stmt.value, 'typ', None)
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
            result.update(_vars_first_assigned_in(stmt.then_body, already_declared | set(result.keys())))
            result.update(_vars_first_assigned_in(stmt.else_body, already_declared | set(result.keys())))
        elif isinstance(stmt, While):
            result.update(_vars_first_assigned_in(stmt.body, already_declared | set(result.keys())))
        elif isinstance(stmt, ForRange):
            result.update(_vars_first_assigned_in(stmt.body, already_declared | set(result.keys())))
        elif isinstance(stmt, ForClassic):
            result.update(_vars_first_assigned_in(stmt.body, already_declared | set(result.keys())))
        elif isinstance(stmt, Block):
            result.update(_vars_first_assigned_in(stmt.body, already_declared | set(result.keys())))
        elif isinstance(stmt, TryCatch):
            result.update(_vars_first_assigned_in(stmt.body, already_declared | set(result.keys())))
            result.update(_vars_first_assigned_in(stmt.catch_body, already_declared | set(result.keys())))
    return result


def _analyze_hoisting(func: Function) -> None:
    """Annotate TryCatch and If nodes with variables needing hoisting."""
    # Collect function-level declared variables
    func_declared = set(p.name for p in func.params)
    for stmt in func.body:
        if isinstance(stmt, VarDecl):
            func_declared.add(stmt.name)

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
                stmt.hoisted_vars = needs_hoisting

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

                # Vars needing hoisting = first assigned inside AND used after
                needs_hoisting = [
                    (name, typ) for name, typ in inner_new.items()
                    if name in used_after
                ]
                stmt.hoisted_vars = needs_hoisting

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
                analyze_stmts(stmt.body, declared)
            elif isinstance(stmt, ForRange):
                analyze_stmts(stmt.body, declared)
            elif isinstance(stmt, ForClassic):
                if stmt.init:
                    analyze_stmts([stmt.init], declared)
                analyze_stmts(stmt.body, declared)
            elif isinstance(stmt, Block):
                analyze_stmts(stmt.body, declared)
            elif isinstance(stmt, (Match, TypeSwitch)):
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
