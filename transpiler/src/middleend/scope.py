"""Scope analysis: declarations, reassignments, param modifications.

Annotations added:
    VarDecl.is_reassigned: bool  - variable is assigned after its declaration
    VarDecl.assignment_count: int - number of assignments after declaration
    Param.is_modified: bool      - parameter is assigned/mutated in function body
    Param.is_unused: bool        - parameter is never referenced in function body
    Assign.is_declaration: bool  - first assignment to a new variable
    TupleAssign.is_declaration: bool - first assignment to new variables
    TupleAssign.new_targets: list[str] - which targets are new declarations
"""

from src.ir import (
    Assign,
    BinaryOp,
    Block,
    Call,
    Cast,
    DerefLV,
    Expr,
    ExprStmt,
    FieldAccess,
    FieldLV,
    ForClassic,
    ForRange,
    Function,
    Index,
    IndexLV,
    InterfaceRef,
    IsNil,
    IsType,
    Len,
    MakeSlice,
    MapLit,
    Match,
    MethodCall,
    Module,
    OpAssign,
    Param,
    Return,
    SetLit,
    SliceExpr,
    SliceLit,
    StaticCall,
    Stmt,
    StringConcat,
    StringFormat,
    StructLit,
    Ternary,
    TryCatch,
    TupleAssign,
    TupleLit,
    TypeAssert,
    TypeSwitch,
    UnaryOp,
    Var,
    VarDecl,
    VarLV,
    While,
)


def analyze_scope(module: Module) -> None:
    """Analyze variable scope: declarations, reassignments, param modifications."""
    for func in module.functions:
        _analyze_function(func)
    for struct in module.structs:
        for method in struct.methods:
            _analyze_function(method)


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


def _scope_visit_expr(result: set[str], expr: Expr | None) -> None:
    """Visit an expression and collect variable names into result."""
    if expr is None:
        return
    if isinstance(expr, Var):
        result.add(expr.name)
    # Visit children based on expression type
    if isinstance(expr, FieldAccess):
        _scope_visit_expr(result, expr.obj)
    elif isinstance(expr, Index):
        _scope_visit_expr(result, expr.obj)
        _scope_visit_expr(result, expr.index)
    elif isinstance(expr, SliceExpr):
        _scope_visit_expr(result, expr.obj)
        _scope_visit_expr(result, expr.low)
        _scope_visit_expr(result, expr.high)
    elif isinstance(expr, BinaryOp):
        _scope_visit_expr(result, expr.left)
        _scope_visit_expr(result, expr.right)
    elif isinstance(expr, UnaryOp):
        _scope_visit_expr(result, expr.operand)
    elif isinstance(expr, Ternary):
        _scope_visit_expr(result, expr.cond)
        _scope_visit_expr(result, expr.then_expr)
        _scope_visit_expr(result, expr.else_expr)
    elif isinstance(expr, Call):
        for arg in expr.args:
            _scope_visit_expr(result, arg)
    elif isinstance(expr, MethodCall):
        _scope_visit_expr(result, expr.obj)
        for arg in expr.args:
            _scope_visit_expr(result, arg)
    elif isinstance(expr, StaticCall):
        for arg in expr.args:
            _scope_visit_expr(result, arg)
    elif isinstance(expr, Cast):
        _scope_visit_expr(result, expr.expr)
    elif isinstance(expr, TypeAssert):
        _scope_visit_expr(result, expr.expr)
    elif isinstance(expr, IsType):
        _scope_visit_expr(result, expr.expr)
    elif isinstance(expr, IsNil):
        _scope_visit_expr(result, expr.expr)
    elif isinstance(expr, Len):
        _scope_visit_expr(result, expr.expr)
    elif isinstance(expr, MakeSlice):
        _scope_visit_expr(result, expr.length)
        _scope_visit_expr(result, expr.capacity)
    elif isinstance(expr, SliceLit):
        for elem in expr.elements:
            _scope_visit_expr(result, elem)
    elif isinstance(expr, MapLit):
        for k, v in expr.entries:
            _scope_visit_expr(result, k)
            _scope_visit_expr(result, v)
    elif isinstance(expr, SetLit):
        for elem in expr.elements:
            _scope_visit_expr(result, elem)
    elif isinstance(expr, StructLit):
        for v in expr.fields.values():
            _scope_visit_expr(result, v)
    elif isinstance(expr, TupleLit):
        for elem in expr.elements:
            _scope_visit_expr(result, elem)
    elif isinstance(expr, StringConcat):
        for part in expr.parts:
            _scope_visit_expr(result, part)
    elif isinstance(expr, StringFormat):
        for arg in expr.args:
            _scope_visit_expr(result, arg)


def _scope_visit_stmt(result: set[str], stmt: Stmt) -> None:
    """Visit a statement and collect variable names into result."""
    if isinstance(stmt, VarDecl):
        if stmt.value:
            _scope_visit_expr(result, stmt.value)
    elif isinstance(stmt, Assign):
        _scope_visit_expr(result, stmt.value)
        if isinstance(stmt.target, IndexLV):
            _scope_visit_expr(result, stmt.target.obj)
            _scope_visit_expr(result, stmt.target.index)
        elif isinstance(stmt.target, FieldLV):
            _scope_visit_expr(result, stmt.target.obj)
        elif isinstance(stmt.target, DerefLV):
            _scope_visit_expr(result, stmt.target.ptr)
    elif isinstance(stmt, OpAssign):
        _scope_visit_expr(result, stmt.value)
        if isinstance(stmt.target, IndexLV):
            _scope_visit_expr(result, stmt.target.obj)
            _scope_visit_expr(result, stmt.target.index)
        elif isinstance(stmt.target, FieldLV):
            _scope_visit_expr(result, stmt.target.obj)
        elif isinstance(stmt.target, DerefLV):
            _scope_visit_expr(result, stmt.target.ptr)
    elif isinstance(stmt, TupleAssign):
        _scope_visit_expr(result, stmt.value)
    elif isinstance(stmt, ExprStmt):
        _scope_visit_expr(result, stmt.expr)
    elif isinstance(stmt, Return):
        if stmt.value:
            _scope_visit_expr(result, stmt.value)
    elif isinstance(stmt, If):
        _scope_visit_expr(result, stmt.cond)
        if stmt.init:
            _scope_visit_stmt(result, stmt.init)
        for s in stmt.then_body:
            _scope_visit_stmt(result, s)
        for s in stmt.else_body:
            _scope_visit_stmt(result, s)
    elif isinstance(stmt, While):
        _scope_visit_expr(result, stmt.cond)
        for s in stmt.body:
            _scope_visit_stmt(result, s)
    elif isinstance(stmt, ForRange):
        _scope_visit_expr(result, stmt.iterable)
        for s in stmt.body:
            _scope_visit_stmt(result, s)
    elif isinstance(stmt, ForClassic):
        if stmt.init:
            _scope_visit_stmt(result, stmt.init)
        if stmt.cond:
            _scope_visit_expr(result, stmt.cond)
        if stmt.post:
            _scope_visit_stmt(result, stmt.post)
        for s in stmt.body:
            _scope_visit_stmt(result, s)
    elif isinstance(stmt, Block):
        for s in stmt.body:
            _scope_visit_stmt(result, s)
    elif isinstance(stmt, TryCatch):
        for s in stmt.body:
            _scope_visit_stmt(result, s)
        for s in stmt.catch_body:
            _scope_visit_stmt(result, s)
    elif isinstance(stmt, Match):
        _scope_visit_expr(result, stmt.expr)
        for case in stmt.cases:
            for s in case.body:
                _scope_visit_stmt(result, s)
        for s in stmt.default:
            _scope_visit_stmt(result, s)
    elif isinstance(stmt, TypeSwitch):
        _scope_visit_expr(result, stmt.expr)
        for case in stmt.cases:
            for s in case.body:
                _scope_visit_stmt(result, s)
        for s in stmt.default:
            _scope_visit_stmt(result, s)


def _collect_used_vars(stmts: list[Stmt]) -> set[str]:
    """Collect all variable names referenced in statements and expressions."""
    result: set[str] = set()
    for stmt in stmts:
        _scope_visit_stmt(result, stmt)
    return result


class _ScopeContext:
    """Context for scope analysis, holding shared state."""

    def __init__(self, params: dict[str, Param], assigned: set[str]) -> None:
        self.declared: dict[str, VarDecl | Assign] = {}
        self.params: dict[str, Param] = params
        self.assigned: set[str] = assigned


def _scope_mark_reassigned(ctx: _ScopeContext, name: str) -> None:
    """Mark a variable as reassigned."""
    if name in ctx.declared:
        decl = ctx.declared[name]
        decl.is_reassigned = True
        decl.assignment_count += 1
    elif name in ctx.params:
        ctx.params[name].is_modified = True


def _scope_is_new_declaration(
    ctx: _ScopeContext, lv: VarLV | IndexLV | FieldLV | DerefLV, local_assigned: set[str]
) -> bool:
    """Check if this lvalue represents a first assignment to a variable."""
    if isinstance(lv, VarLV):
        return lv.name not in ctx.params and lv.name not in local_assigned
    return False


def _scope_check_lvalue(
    ctx: _ScopeContext, lv: VarLV | IndexLV | FieldLV | DerefLV
) -> None:
    """Mark the base variable of an lvalue as modified."""
    if isinstance(lv, VarLV):
        _scope_mark_reassigned(ctx, lv.name)
    elif isinstance(lv, IndexLV):
        if isinstance(lv.obj, Var):
            _scope_mark_reassigned(ctx, lv.obj.name)
    elif isinstance(lv, FieldLV):
        if isinstance(lv.obj, Var):
            _scope_mark_reassigned(ctx, lv.obj.name)
    elif isinstance(lv, DerefLV):
        if isinstance(lv.ptr, Var):
            _scope_mark_reassigned(ctx, lv.ptr.name)


def _scope_check_expr(ctx: _ScopeContext, expr: Expr | None) -> None:
    """Check for mutating method calls on declared variables."""
    if expr is None:
        return
    if isinstance(expr, MethodCall):
        if isinstance(expr.obj, Var):
            _scope_mark_reassigned(ctx, expr.obj.name)
        _scope_check_expr(ctx, expr.obj)
        for arg in expr.args:
            _scope_check_expr(ctx, arg)


def _scope_check_stmt(ctx: _ScopeContext, stmt: Stmt, local_assigned: set[str]) -> None:
    """Check a statement for declarations and reassignments."""
    if isinstance(stmt, VarDecl):
        stmt.is_reassigned = False
        stmt.assignment_count = 0
        ctx.declared[stmt.name] = stmt
        local_assigned.add(stmt.name)
        if stmt.value:
            _scope_check_expr(ctx, stmt.value)
    elif isinstance(stmt, Assign):
        stmt.is_declaration = _scope_is_new_declaration(ctx, stmt.target, local_assigned)
        if isinstance(stmt.target, VarLV) and stmt.is_declaration:
            local_assigned.add(stmt.target.name)
            stmt.is_reassigned = False
            stmt.assignment_count = 0
            ctx.declared[stmt.target.name] = stmt
        else:
            _scope_check_lvalue(ctx, stmt.target)
        _scope_check_expr(ctx, stmt.value)
    elif isinstance(stmt, OpAssign):
        _scope_check_lvalue(ctx, stmt.target)
        _scope_check_expr(ctx, stmt.value)
    elif isinstance(stmt, TupleAssign):
        all_new = True
        new_targets: list[str] = []
        for target in stmt.targets:
            if isinstance(target, VarLV):
                if (
                    target.name in ctx.assigned
                    or target.name in ctx.declared
                    or target.name in ctx.params
                    or target.name in local_assigned
                ):
                    all_new = False
                else:
                    new_targets.append(target.name)
                    local_assigned.add(target.name)
            else:
                all_new = False
        stmt.is_declaration = all_new
        stmt.new_targets = new_targets
        for target in stmt.targets:
            if isinstance(target, VarLV) and not stmt.is_declaration:
                _scope_mark_reassigned(ctx, target.name)
        _scope_check_expr(ctx, stmt.value)
    elif isinstance(stmt, ExprStmt):
        _scope_check_expr(ctx, stmt.expr)
    elif isinstance(stmt, Return):
        if stmt.value:
            _scope_check_expr(ctx, stmt.value)
    elif isinstance(stmt, If):
        _scope_check_expr(ctx, stmt.cond)
        if stmt.init:
            _scope_check_stmt(ctx, stmt.init, local_assigned)
        then_assigned: set[str] = set(local_assigned)
        for s in stmt.then_body:
            _scope_check_stmt(ctx, s, then_assigned)
        else_assigned: set[str] = set(local_assigned)
        for s in stmt.else_body:
            _scope_check_stmt(ctx, s, else_assigned)
    elif isinstance(stmt, While):
        _scope_check_expr(ctx, stmt.cond)
        for s in stmt.body:
            _scope_check_stmt(ctx, s, local_assigned)
    elif isinstance(stmt, ForRange):
        for s in stmt.body:
            _scope_check_stmt(ctx, s, local_assigned)
    elif isinstance(stmt, ForClassic):
        if stmt.init:
            _scope_check_stmt(ctx, stmt.init, local_assigned)
        if stmt.cond:
            _scope_check_expr(ctx, stmt.cond)
        if stmt.post:
            _scope_check_stmt(ctx, stmt.post, local_assigned)
        for s in stmt.body:
            _scope_check_stmt(ctx, s, local_assigned)
    elif isinstance(stmt, Block):
        for s in stmt.body:
            _scope_check_stmt(ctx, s, local_assigned)
    elif isinstance(stmt, TryCatch):
        try_assigned: set[str] = set(local_assigned)
        for s in stmt.body:
            _scope_check_stmt(ctx, s, try_assigned)
        catch_assigned: set[str] = set(local_assigned)
        for s in stmt.catch_body:
            _scope_check_stmt(ctx, s, catch_assigned)
    elif isinstance(stmt, Match):
        _scope_check_expr(ctx, stmt.expr)
        for case in stmt.cases:
            case_assigned: set[str] = set(local_assigned)
            for s in case.body:
                _scope_check_stmt(ctx, s, case_assigned)
        default_assigned: set[str] = set(local_assigned)
        for s in stmt.default:
            _scope_check_stmt(ctx, s, default_assigned)
    elif isinstance(stmt, TypeSwitch):
        _scope_check_expr(ctx, stmt.expr)
        for case in stmt.cases:
            case_assigned: set[str] = set(local_assigned)
            for s in case.body:
                _scope_check_stmt(ctx, s, case_assigned)
        default_assigned: set[str] = set(local_assigned)
        for s in stmt.default:
            _scope_check_stmt(ctx, s, default_assigned)


def _interface_visit_expr(expr: Expr | None) -> None:
    """Set is_interface=True on expressions typed as InterfaceRef."""
    if expr is None:
        return
    if isinstance(expr.typ, InterfaceRef):
        expr.is_interface = True
    # Recurse into child expressions
    if isinstance(expr, FieldAccess):
        _interface_visit_expr(expr.obj)
    elif isinstance(expr, Index):
        _interface_visit_expr(expr.obj)
        _interface_visit_expr(expr.index)
    elif isinstance(expr, SliceExpr):
        _interface_visit_expr(expr.obj)
        _interface_visit_expr(expr.low)
        _interface_visit_expr(expr.high)
    elif isinstance(expr, BinaryOp):
        _interface_visit_expr(expr.left)
        _interface_visit_expr(expr.right)
    elif isinstance(expr, UnaryOp):
        _interface_visit_expr(expr.operand)
    elif isinstance(expr, Ternary):
        _interface_visit_expr(expr.cond)
        _interface_visit_expr(expr.then_expr)
        _interface_visit_expr(expr.else_expr)
    elif isinstance(expr, Call):
        for arg in expr.args:
            _interface_visit_expr(arg)
    elif isinstance(expr, MethodCall):
        _interface_visit_expr(expr.obj)
        for arg in expr.args:
            _interface_visit_expr(arg)
    elif isinstance(expr, StaticCall):
        for arg in expr.args:
            _interface_visit_expr(arg)
    elif isinstance(expr, Cast):
        _interface_visit_expr(expr.expr)
    elif isinstance(expr, TypeAssert):
        _interface_visit_expr(expr.expr)
    elif isinstance(expr, IsType):
        _interface_visit_expr(expr.expr)
    elif isinstance(expr, IsNil):
        _interface_visit_expr(expr.expr)
    elif isinstance(expr, Len):
        _interface_visit_expr(expr.expr)
    elif isinstance(expr, MakeSlice):
        _interface_visit_expr(expr.length)
        _interface_visit_expr(expr.capacity)
    elif isinstance(expr, SliceLit):
        for elem in expr.elements:
            _interface_visit_expr(elem)
    elif isinstance(expr, MapLit):
        for k, v in expr.entries:
            _interface_visit_expr(k)
            _interface_visit_expr(v)
    elif isinstance(expr, SetLit):
        for elem in expr.elements:
            _interface_visit_expr(elem)
    elif isinstance(expr, StructLit):
        for v in expr.fields.values():
            _interface_visit_expr(v)
    elif isinstance(expr, TupleLit):
        for elem in expr.elements:
            _interface_visit_expr(elem)
    elif isinstance(expr, StringConcat):
        for part in expr.parts:
            _interface_visit_expr(part)
    elif isinstance(expr, StringFormat):
        for arg in expr.args:
            _interface_visit_expr(arg)


def _interface_visit_stmt(stmt: Stmt) -> None:
    """Visit a statement and annotate interface-typed expressions."""
    if isinstance(stmt, VarDecl):
        if stmt.value:
            _interface_visit_expr(stmt.value)
    elif isinstance(stmt, Assign):
        _interface_visit_expr(stmt.value)
    elif isinstance(stmt, OpAssign):
        _interface_visit_expr(stmt.value)
    elif isinstance(stmt, TupleAssign):
        _interface_visit_expr(stmt.value)
    elif isinstance(stmt, ExprStmt):
        _interface_visit_expr(stmt.expr)
    elif isinstance(stmt, Return):
        if stmt.value:
            _interface_visit_expr(stmt.value)
    elif isinstance(stmt, If):
        _interface_visit_expr(stmt.cond)
        if stmt.init:
            _interface_visit_stmt(stmt.init)
        for s in stmt.then_body:
            _interface_visit_stmt(s)
        for s in stmt.else_body:
            _interface_visit_stmt(s)
    elif isinstance(stmt, While):
        _interface_visit_expr(stmt.cond)
        for s in stmt.body:
            _interface_visit_stmt(s)
    elif isinstance(stmt, ForRange):
        _interface_visit_expr(stmt.iterable)
        for s in stmt.body:
            _interface_visit_stmt(s)
    elif isinstance(stmt, ForClassic):
        if stmt.init:
            _interface_visit_stmt(stmt.init)
        if stmt.cond:
            _interface_visit_expr(stmt.cond)
        if stmt.post:
            _interface_visit_stmt(stmt.post)
        for s in stmt.body:
            _interface_visit_stmt(s)
    elif isinstance(stmt, Block):
        for s in stmt.body:
            _interface_visit_stmt(s)
    elif isinstance(stmt, TryCatch):
        for s in stmt.body:
            _interface_visit_stmt(s)
        for s in stmt.catch_body:
            _interface_visit_stmt(s)
    elif isinstance(stmt, Match):
        _interface_visit_expr(stmt.expr)
        for case in stmt.cases:
            for s in case.body:
                _interface_visit_stmt(s)
        for s in stmt.default:
            _interface_visit_stmt(s)
    elif isinstance(stmt, TypeSwitch):
        _interface_visit_expr(stmt.expr)
        for case in stmt.cases:
            for s in case.body:
                _interface_visit_stmt(s)
        for s in stmt.default:
            _interface_visit_stmt(s)


def _annotate_interface_types(stmts: list[Stmt]) -> None:
    """Set is_interface=True on expressions typed as InterfaceRef."""
    for stmt in stmts:
        _interface_visit_stmt(stmt)


def _analyze_function(func: Function) -> None:
    """Analyze a single function for reassignments."""
    params: dict[str, Param] = {}
    for p in func.params:
        params[p.name] = p
    assigned: set[str] = set()
    for p in func.params:
        p.is_modified = False
        p.is_unused = False
        assigned.add(p.name)
    used_vars: set[str] = _collect_used_vars(func.body)
    ctx = _ScopeContext(params, assigned)
    func_assigned: set[str] = set()
    for stmt in func.body:
        _scope_check_stmt(ctx, stmt, func_assigned)
    for p in func.params:
        if p.name not in used_vars:
            p.is_unused = True
    # Annotate interface-typed expressions
    _annotate_interface_types(func.body)


# Import If here to avoid circular import at module level
from src.ir import If  # noqa: E402
