"""IR analysis passes that annotate nodes with backend-useful information.

Fields added to IR nodes:
    VarDecl.is_reassigned: bool  - variable is assigned after its declaration
    Param.is_modified: bool      - parameter is assigned/mutated in function body
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
    TupleAssign,
    TypeSwitch,
    Var,
    VarDecl,
    VarLV,
    While,
)


def analyze(module: Module) -> None:
    """Run all analysis passes, annotating IR nodes in place."""
    _analyze_reassignments(module)


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
    params: dict[str, Param] = {p.name: p for p in func.params}

    # Initialize annotations
    for p in func.params:
        p.is_modified = False

    def mark_reassigned(name: str) -> None:
        if name in declared:
            declared[name].is_reassigned = True
        elif name in params:
            params[name].is_modified = True

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

    def check_stmt(stmt: Stmt) -> None:
        if isinstance(stmt, VarDecl):
            stmt.is_reassigned = False
            declared[stmt.name] = stmt
            if stmt.value:
                check_expr(stmt.value)
        elif isinstance(stmt, Assign):
            check_lvalue(stmt.target)
            check_expr(stmt.value)
        elif isinstance(stmt, OpAssign):
            check_lvalue(stmt.target)
            check_expr(stmt.value)
        elif isinstance(stmt, TupleAssign):
            for target in stmt.targets:
                if isinstance(target, VarLV):
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
                check_stmt(stmt.init)
            for s in stmt.then_body:
                check_stmt(s)
            for s in stmt.else_body:
                check_stmt(s)
        elif isinstance(stmt, While):
            check_expr(stmt.cond)
            for s in stmt.body:
                check_stmt(s)
        elif isinstance(stmt, ForRange):
            for s in stmt.body:
                check_stmt(s)
        elif isinstance(stmt, ForClassic):
            if stmt.init:
                check_stmt(stmt.init)
            if stmt.cond:
                check_expr(stmt.cond)
            if stmt.post:
                check_stmt(stmt.post)
            for s in stmt.body:
                check_stmt(s)
        elif isinstance(stmt, Block):
            for s in stmt.body:
                check_stmt(s)
        elif isinstance(stmt, TryCatch):
            for s in stmt.body:
                check_stmt(s)
            for s in stmt.catch_body:
                check_stmt(s)
        elif isinstance(stmt, Match):
            check_expr(stmt.expr)
            for case in stmt.cases:
                for s in case.body:
                    check_stmt(s)
            for s in stmt.default:
                check_stmt(s)
        elif isinstance(stmt, TypeSwitch):
            check_expr(stmt.expr)
            for case in stmt.cases:
                for s in case.body:
                    check_stmt(s)
            for s in stmt.default:
                check_stmt(s)

    def check_expr(expr) -> None:
        """Check for mutating method calls on declared variables."""
        if isinstance(expr, MethodCall):
            if isinstance(expr.obj, Var):
                mark_reassigned(expr.obj.name)
            check_expr(expr.obj)
            for arg in expr.args:
                check_expr(arg)

    for stmt in func.body:
        check_stmt(stmt)
