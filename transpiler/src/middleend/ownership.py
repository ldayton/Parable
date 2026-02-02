"""Ownership inference and escape analysis.

Annotates IR nodes with ownership classifications:
- owned: Value owned by this binding (constructor result, copy)
- borrowed: Reference to caller's value (params, field access)
- shared: Runtime-managed (ambiguous ownership, escapes detected)
- weak: Back-reference (no ownership, prevents cycles)

Escape detection identifies borrowed references that outlive their source:
- Field storage: self.field = borrowed_param
- Return: return borrowed_ref (unless transitive from param)
- Collection addition: list.append(borrowed_ref)

Annotations added:
    VarDecl.ownership: Ownership - ownership classification for variable
    Param.ownership: Ownership - already defaults to borrowed
    Expr.escapes: bool - True if value escapes its scope
    OwnershipInfo: Module-level summary of escape analysis results
"""

from dataclasses import dataclass, field

from src.ir import (
    Assign,
    BinaryOp,
    Block,
    Call,
    Cast,
    DictComp,
    Expr,
    ExprStmt,
    FieldAccess,
    FieldLV,
    ForClassic,
    ForRange,
    Function,
    Index,
    IndexLV,
    IsNil,
    IsType,
    Len,
    ListComp,
    MakeMap,
    MakeSlice,
    MapLit,
    Match,
    MethodCall,
    Module,
    OpAssign,
    Ownership,
    OwnershipInfo,
    Return,
    SetComp,
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
    Truthy,
    TypeAssert,
    TypeSwitch,
    UnaryOp,
    Var,
    VarDecl,
    VarLV,
    While,
)


@dataclass
class OwnershipContext:
    """Context for ownership analysis within a function."""
    var_ownership: dict[str, Ownership] = field(default_factory=dict)
    params: set[str] = field(default_factory=set)
    escaping: set[str] = field(default_factory=set)
    current_struct: str | None = None


def analyze_ownership(module: Module) -> OwnershipInfo:
    """Analyze ownership and escapes for all functions/methods in module."""
    info = OwnershipInfo()
    for func in module.functions:
        _analyze_function(func, info, None)
    for struct in module.structs:
        for method in struct.methods:
            _analyze_function(method, info, struct.name)
    return info


def _analyze_function(func: Function, info: OwnershipInfo, struct_name: str | None) -> None:
    """Analyze a single function for ownership and escapes."""
    ctx = OwnershipContext(current_struct=struct_name)
    for param in func.params:
        ctx.params.add(param.name)
        ctx.var_ownership[param.name] = "borrowed"
    for stmt in func.body:
        _analyze_stmt(stmt, ctx, info)
    info.escaping_vars.update(ctx.escaping)


def _analyze_stmt(stmt: Stmt, ctx: OwnershipContext, info: OwnershipInfo) -> None:
    """Analyze a statement for ownership and escape."""
    if isinstance(stmt, VarDecl):
        if stmt.value:
            _analyze_expr(stmt.value, ctx, info, escaping=False)
            ownership = _infer_expr_ownership(stmt.value, ctx)
            stmt.ownership = ownership
            ctx.var_ownership[stmt.name] = ownership
        else:
            stmt.ownership = "owned"
            ctx.var_ownership[stmt.name] = "owned"
    elif isinstance(stmt, Assign):
        _analyze_expr(stmt.value, ctx, info, escaping=False)
        if isinstance(stmt.target, VarLV):
            ownership = _infer_expr_ownership(stmt.value, ctx)
            ctx.var_ownership[stmt.target.name] = ownership
        elif isinstance(stmt.target, FieldLV):
            _analyze_expr(stmt.target.obj, ctx, info, escaping=False)
            _check_field_escape(stmt.target, stmt.value, ctx, info)
        elif isinstance(stmt.target, IndexLV):
            _analyze_expr(stmt.target.obj, ctx, info, escaping=False)
            _analyze_expr(stmt.target.index, ctx, info, escaping=False)
            _check_collection_escape(stmt.target, stmt.value, ctx, info)
    elif isinstance(stmt, TupleAssign):
        _analyze_expr(stmt.value, ctx, info, escaping=False)
        for target in stmt.targets:
            if isinstance(target, VarLV):
                ctx.var_ownership[target.name] = "owned"
    elif isinstance(stmt, OpAssign):
        _analyze_expr(stmt.value, ctx, info, escaping=False)
        if isinstance(stmt.target, FieldLV):
            _analyze_expr(stmt.target.obj, ctx, info, escaping=False)
        elif isinstance(stmt.target, IndexLV):
            _analyze_expr(stmt.target.obj, ctx, info, escaping=False)
            _analyze_expr(stmt.target.index, ctx, info, escaping=False)
    elif isinstance(stmt, ExprStmt):
        _analyze_expr(stmt.expr, ctx, info, escaping=False)
    elif isinstance(stmt, Return):
        if stmt.value:
            _analyze_expr(stmt.value, ctx, info, escaping=False)
            _check_return_escape(stmt.value, ctx, info)
    elif isinstance(stmt, If):
        _analyze_expr(stmt.cond, ctx, info, escaping=False)
        if stmt.init:
            _analyze_stmt(stmt.init, ctx, info)
        for s in stmt.then_body:
            _analyze_stmt(s, ctx, info)
        for s in stmt.else_body:
            _analyze_stmt(s, ctx, info)
    elif isinstance(stmt, While):
        _analyze_expr(stmt.cond, ctx, info, escaping=False)
        for s in stmt.body:
            _analyze_stmt(s, ctx, info)
    elif isinstance(stmt, ForRange):
        _analyze_expr(stmt.iterable, ctx, info, escaping=False)
        if stmt.index:
            ctx.var_ownership[stmt.index] = "owned"
        if stmt.value:
            ctx.var_ownership[stmt.value] = "borrowed"
        for s in stmt.body:
            _analyze_stmt(s, ctx, info)
    elif isinstance(stmt, ForClassic):
        if stmt.init:
            _analyze_stmt(stmt.init, ctx, info)
        if stmt.cond:
            _analyze_expr(stmt.cond, ctx, info, escaping=False)
        if stmt.post:
            _analyze_stmt(stmt.post, ctx, info)
        for s in stmt.body:
            _analyze_stmt(s, ctx, info)
    elif isinstance(stmt, Block):
        for s in stmt.body:
            _analyze_stmt(s, ctx, info)
    elif isinstance(stmt, TryCatch):
        for s in stmt.body:
            _analyze_stmt(s, ctx, info)
        if stmt.catch_var:
            ctx.var_ownership[stmt.catch_var] = "owned"
        for s in stmt.catch_body:
            _analyze_stmt(s, ctx, info)
    elif isinstance(stmt, Match):
        _analyze_expr(stmt.expr, ctx, info, escaping=False)
        for case in stmt.cases:
            for s in case.body:
                _analyze_stmt(s, ctx, info)
        for s in stmt.default:
            _analyze_stmt(s, ctx, info)
    elif isinstance(stmt, TypeSwitch):
        _analyze_expr(stmt.expr, ctx, info, escaping=False)
        for case in stmt.cases:
            if stmt.binding:
                ctx.var_ownership[stmt.binding] = "borrowed"
            for s in case.body:
                _analyze_stmt(s, ctx, info)
        for s in stmt.default:
            _analyze_stmt(s, ctx, info)


def _analyze_expr(expr: Expr, ctx: OwnershipContext, info: OwnershipInfo, escaping: bool) -> None:
    """Analyze an expression, optionally marking it as escaping."""
    if escaping:
        ownership = _infer_expr_ownership(expr, ctx)
        if ownership == "borrowed":
            expr.escapes = True
            if isinstance(expr, Var):
                ctx.escaping.add(expr.name)
                info.escaping_vars.add(expr.name)
    if isinstance(expr, Var):
        pass
    elif isinstance(expr, FieldAccess):
        _analyze_expr(expr.obj, ctx, info, escaping=False)
    elif isinstance(expr, Index):
        _analyze_expr(expr.obj, ctx, info, escaping=False)
        _analyze_expr(expr.index, ctx, info, escaping=False)
    elif isinstance(expr, SliceExpr):
        _analyze_expr(expr.obj, ctx, info, escaping=False)
        if expr.low:
            _analyze_expr(expr.low, ctx, info, escaping=False)
        if expr.high:
            _analyze_expr(expr.high, ctx, info, escaping=False)
        if expr.step:
            _analyze_expr(expr.step, ctx, info, escaping=False)
    elif isinstance(expr, BinaryOp):
        _analyze_expr(expr.left, ctx, info, escaping=False)
        _analyze_expr(expr.right, ctx, info, escaping=False)
    elif isinstance(expr, UnaryOp):
        _analyze_expr(expr.operand, ctx, info, escaping=False)
    elif isinstance(expr, Ternary):
        _analyze_expr(expr.cond, ctx, info, escaping=False)
        _analyze_expr(expr.then_expr, ctx, info, escaping)
        _analyze_expr(expr.else_expr, ctx, info, escaping)
    elif isinstance(expr, Call):
        for arg in expr.args:
            _analyze_expr(arg, ctx, info, escaping=False)
    elif isinstance(expr, MethodCall):
        _analyze_expr(expr.obj, ctx, info, escaping=False)
        method_escapes = expr.method in ("append", "add", "extend", "update", "insert")
        for arg in expr.args:
            _analyze_expr(arg, ctx, info, escaping=method_escapes)
    elif isinstance(expr, StaticCall):
        for arg in expr.args:
            _analyze_expr(arg, ctx, info, escaping=False)
    elif isinstance(expr, Cast):
        _analyze_expr(expr.expr, ctx, info, escaping)
    elif isinstance(expr, TypeAssert):
        _analyze_expr(expr.expr, ctx, info, escaping)
    elif isinstance(expr, IsType):
        _analyze_expr(expr.expr, ctx, info, escaping=False)
    elif isinstance(expr, IsNil):
        _analyze_expr(expr.expr, ctx, info, escaping=False)
    elif isinstance(expr, Truthy):
        _analyze_expr(expr.expr, ctx, info, escaping=False)
    elif isinstance(expr, Len):
        _analyze_expr(expr.expr, ctx, info, escaping=False)
    elif isinstance(expr, MakeSlice):
        if expr.length:
            _analyze_expr(expr.length, ctx, info, escaping=False)
        if expr.capacity:
            _analyze_expr(expr.capacity, ctx, info, escaping=False)
    elif isinstance(expr, StructLit):
        for value in expr.fields.values():
            _analyze_expr(value, ctx, info, escaping=True)
        if expr.embedded_value:
            _analyze_expr(expr.embedded_value, ctx, info, escaping=True)
    elif isinstance(expr, SliceLit):
        for elem in expr.elements:
            _analyze_expr(elem, ctx, info, escaping=True)
    elif isinstance(expr, MapLit):
        for k, v in expr.entries:
            _analyze_expr(k, ctx, info, escaping=True)
            _analyze_expr(v, ctx, info, escaping=True)
    elif isinstance(expr, SetLit):
        for elem in expr.elements:
            _analyze_expr(elem, ctx, info, escaping=True)
    elif isinstance(expr, TupleLit):
        for elem in expr.elements:
            _analyze_expr(elem, ctx, info, escaping=True)
    elif isinstance(expr, StringConcat):
        for part in expr.parts:
            _analyze_expr(part, ctx, info, escaping=False)
    elif isinstance(expr, StringFormat):
        for arg in expr.args:
            _analyze_expr(arg, ctx, info, escaping=False)
    elif isinstance(expr, ListComp):
        _analyze_expr(expr.iterable, ctx, info, escaping=False)
        _analyze_expr(expr.element, ctx, info, escaping=True)
        if expr.condition:
            _analyze_expr(expr.condition, ctx, info, escaping=False)
    elif isinstance(expr, SetComp):
        _analyze_expr(expr.iterable, ctx, info, escaping=False)
        _analyze_expr(expr.element, ctx, info, escaping=True)
        if expr.condition:
            _analyze_expr(expr.condition, ctx, info, escaping=False)
    elif isinstance(expr, DictComp):
        _analyze_expr(expr.iterable, ctx, info, escaping=False)
        _analyze_expr(expr.key, ctx, info, escaping=True)
        _analyze_expr(expr.value, ctx, info, escaping=True)
        if expr.condition:
            _analyze_expr(expr.condition, ctx, info, escaping=False)


def _infer_expr_ownership(expr: Expr, ctx: OwnershipContext) -> Ownership:
    """Infer ownership classification for an expression."""
    if isinstance(expr, StructLit):
        return "owned"
    if isinstance(expr, (SliceLit, MapLit, SetLit, TupleLit, MakeSlice, MakeMap)):
        return "owned"
    if isinstance(expr, (Call, StaticCall)):
        return "owned"
    if isinstance(expr, MethodCall):
        if expr.method == "copy":
            return "owned"
        return "owned"
    if isinstance(expr, Var):
        return ctx.var_ownership.get(expr.name, "borrowed")
    if isinstance(expr, FieldAccess):
        return "borrowed"
    if isinstance(expr, Index):
        return "borrowed"
    if isinstance(expr, SliceExpr):
        return "borrowed"
    if isinstance(expr, Ternary):
        then_own = _infer_expr_ownership(expr.then_expr, ctx)
        else_own = _infer_expr_ownership(expr.else_expr, ctx)
        return _join_ownership(then_own, else_own)
    if isinstance(expr, Cast):
        return _infer_expr_ownership(expr.expr, ctx)
    if isinstance(expr, TypeAssert):
        return _infer_expr_ownership(expr.expr, ctx)
    if isinstance(expr, (ListComp, SetComp, DictComp)):
        return "owned"
    return "owned"


def _join_ownership(o1: Ownership, o2: Ownership) -> Ownership:
    """Join ownership classifications from branches."""
    if o1 == o2:
        return o1
    if o1 == "shared" or o2 == "shared":
        return "shared"
    if (o1 == "owned" and o2 == "borrowed") or (o1 == "borrowed" and o2 == "owned"):
        return "shared"
    if o1 == "weak" or o2 == "weak":
        return "shared"
    return "shared"


def _check_field_escape(target: FieldLV, value: Expr, ctx: OwnershipContext, info: OwnershipInfo) -> None:
    """Check if assigning to a field causes a borrowed value to escape."""
    ownership = _infer_expr_ownership(value, ctx)
    if ownership == "borrowed":
        value.escapes = True
        if isinstance(value, Var):
            ctx.escaping.add(value.name)
            info.escaping_vars.add(value.name)


def _check_collection_escape(target: IndexLV, value: Expr, ctx: OwnershipContext, info: OwnershipInfo) -> None:
    """Check if assigning to a collection index causes a borrowed value to escape."""
    ownership = _infer_expr_ownership(value, ctx)
    if ownership == "borrowed":
        value.escapes = True
        if isinstance(value, Var):
            ctx.escaping.add(value.name)
            info.escaping_vars.add(value.name)


def _check_return_escape(value: Expr, ctx: OwnershipContext, info: OwnershipInfo) -> None:
    """Check if returning causes a borrowed value to escape."""
    ownership = _infer_expr_ownership(value, ctx)
    if ownership == "borrowed":
        if isinstance(value, Var) and value.name not in ctx.params:
            value.escapes = True
            ctx.escaping.add(value.name)
            info.escaping_vars.add(value.name)
        elif isinstance(value, FieldAccess):
            if isinstance(value.obj, Var) and value.obj.name not in ctx.params:
                value.escapes = True


# Import If here to avoid circular import at module level
from src.ir import If  # noqa: E402
