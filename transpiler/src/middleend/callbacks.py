"""Callback parameter analysis - propagate receiver types from bound methods.

When a Callable parameter is passed a bound method (FuncRef with receiver),
we need to update the parameter's FuncType to include the receiver type.
This enables C backend to emit correct function pointer signatures.
"""

from src.ir import (
    Call,
    Expr,
    FuncRef,
    FuncType,
    MethodCall,
    Module,
    Param,
    Stmt,
)


def analyze_callbacks(module: Module) -> None:
    """Propagate receiver types from FuncRef arguments to function parameters."""
    # Build a map of function/method names to their Param objects
    func_params: dict[str, list[Param]] = {}
    for func in module.functions:
        func_params[func.name] = func.params
    for struct in module.structs:
        for method in struct.methods:
            key = f"{struct.name}.{method.name}"
            func_params[key] = method.params
    # Scan all call sites for FuncRef arguments with receivers
    for func in module.functions:
        _scan_stmts(func.body, func_params)
    for struct in module.structs:
        for method in struct.methods:
            _scan_stmts(method.body, func_params, struct.name)


def _scan_stmts(stmts: list[Stmt], func_params: dict[str, list[Param]], current_struct: str | None = None) -> None:
    """Scan statements for call sites with FuncRef arguments."""
    for stmt in stmts:
        _scan_stmt(stmt, func_params, current_struct)


def _scan_stmt(stmt: Stmt, func_params: dict[str, list[Param]], current_struct: str | None) -> None:
    """Scan a statement for call sites with FuncRef arguments."""
    from src.ir import (
        Assign,
        Block,
        ExprStmt,
        ForClassic,
        ForRange,
        If,
        Match,
        OpAssign,
        Return,
        TryCatch,
        TupleAssign,
        TypeSwitch,
        VarDecl,
        While,
    )
    if isinstance(stmt, ExprStmt):
        _scan_expr(stmt.expr, func_params, current_struct)
    elif isinstance(stmt, VarDecl):
        if stmt.value:
            _scan_expr(stmt.value, func_params, current_struct)
    elif isinstance(stmt, Assign):
        _scan_expr(stmt.value, func_params, current_struct)
    elif isinstance(stmt, TupleAssign):
        _scan_expr(stmt.value, func_params, current_struct)
    elif isinstance(stmt, OpAssign):
        _scan_expr(stmt.value, func_params, current_struct)
    elif isinstance(stmt, Return):
        if stmt.value:
            _scan_expr(stmt.value, func_params, current_struct)
    elif isinstance(stmt, If):
        _scan_expr(stmt.cond, func_params, current_struct)
        _scan_stmts(stmt.then_body, func_params, current_struct)
        _scan_stmts(stmt.else_body, func_params, current_struct)
    elif isinstance(stmt, While):
        _scan_expr(stmt.cond, func_params, current_struct)
        _scan_stmts(stmt.body, func_params, current_struct)
    elif isinstance(stmt, ForRange):
        _scan_expr(stmt.iterable, func_params, current_struct)
        _scan_stmts(stmt.body, func_params, current_struct)
    elif isinstance(stmt, ForClassic):
        if stmt.init:
            _scan_stmt(stmt.init, func_params, current_struct)
        if stmt.cond:
            _scan_expr(stmt.cond, func_params, current_struct)
        if stmt.post:
            _scan_stmt(stmt.post, func_params, current_struct)
        _scan_stmts(stmt.body, func_params, current_struct)
    elif isinstance(stmt, Block):
        _scan_stmts(stmt.body, func_params, current_struct)
    elif isinstance(stmt, TryCatch):
        _scan_stmts(stmt.body, func_params, current_struct)
        _scan_stmts(stmt.catch_body, func_params, current_struct)
    elif isinstance(stmt, TypeSwitch):
        _scan_expr(stmt.expr, func_params, current_struct)
        for case in stmt.cases:
            _scan_stmts(case.body, func_params, current_struct)
        _scan_stmts(stmt.default, func_params, current_struct)
    elif isinstance(stmt, Match):
        _scan_expr(stmt.expr, func_params, current_struct)
        for case in stmt.cases:
            _scan_stmts(case.body, func_params, current_struct)
        _scan_stmts(stmt.default, func_params, current_struct)


def _scan_expr(expr: Expr, func_params: dict[str, list[Param]], current_struct: str | None) -> None:
    """Scan an expression for call sites with FuncRef arguments."""
    from src.ir import (
        AddrOf,
        BinaryOp,
        Cast,
        DictComp,
        FieldAccess,
        Index,
        IsNil,
        IsType,
        Len,
        ListComp,
        MapLit,
        SetComp,
        SetLit,
        SliceExpr,
        SliceLit,
        StructLit,
        Ternary,
        Truthy,
        TupleLit,
        TypeAssert,
        UnaryOp,
    )
    if isinstance(expr, MethodCall):
        # Check if any argument is a FuncRef with receiver
        for i, arg in enumerate(expr.args):
            if isinstance(arg, FuncRef) and arg.obj is not None:
                # This is a bound method being passed as argument
                arg_type = arg.typ
                if isinstance(arg_type, FuncType) and arg_type.receiver:
                    # Look up the target method's parameter
                    receiver_type = expr.receiver_type
                    struct_name = ""
                    from src.ir import Pointer, StructRef
                    if isinstance(receiver_type, Pointer) and isinstance(receiver_type.target, StructRef):
                        struct_name = receiver_type.target.name
                    elif isinstance(receiver_type, StructRef):
                        struct_name = receiver_type.name
                    key = f"{struct_name}.{expr.method}"
                    if key in func_params:
                        params = func_params[key]
                        if i < len(params):
                            param = params[i]
                            if isinstance(param.typ, FuncType) and param.typ.receiver is None:
                                # Update parameter's FuncType to include receiver
                                param.typ = FuncType(
                                    params=param.typ.params,
                                    ret=param.typ.ret,
                                    captures=param.typ.captures,
                                    receiver=arg_type.receiver,
                                )
        # Recurse into subexpressions
        _scan_expr(expr.obj, func_params, current_struct)
        for arg in expr.args:
            _scan_expr(arg, func_params, current_struct)
    elif isinstance(expr, Call):
        # Check free function calls
        for i, arg in enumerate(expr.args):
            if isinstance(arg, FuncRef) and arg.obj is not None:
                arg_type = arg.typ
                if isinstance(arg_type, FuncType) and arg_type.receiver:
                    if expr.func in func_params:
                        params = func_params[expr.func]
                        if i < len(params):
                            param = params[i]
                            if isinstance(param.typ, FuncType) and param.typ.receiver is None:
                                param.typ = FuncType(
                                    params=param.typ.params,
                                    ret=param.typ.ret,
                                    captures=param.typ.captures,
                                    receiver=arg_type.receiver,
                                )
        for arg in expr.args:
            _scan_expr(arg, func_params, current_struct)
    elif isinstance(expr, BinaryOp):
        _scan_expr(expr.left, func_params, current_struct)
        _scan_expr(expr.right, func_params, current_struct)
    elif isinstance(expr, UnaryOp):
        _scan_expr(expr.operand, func_params, current_struct)
    elif isinstance(expr, Ternary):
        _scan_expr(expr.cond, func_params, current_struct)
        _scan_expr(expr.then_expr, func_params, current_struct)
        _scan_expr(expr.else_expr, func_params, current_struct)
    elif isinstance(expr, Index):
        _scan_expr(expr.obj, func_params, current_struct)
        _scan_expr(expr.index, func_params, current_struct)
    elif isinstance(expr, SliceExpr):
        _scan_expr(expr.obj, func_params, current_struct)
        if expr.low:
            _scan_expr(expr.low, func_params, current_struct)
        if expr.high:
            _scan_expr(expr.high, func_params, current_struct)
    elif isinstance(expr, FieldAccess):
        _scan_expr(expr.obj, func_params, current_struct)
    elif isinstance(expr, Cast):
        _scan_expr(expr.expr, func_params, current_struct)
    elif isinstance(expr, TypeAssert):
        _scan_expr(expr.expr, func_params, current_struct)
    elif isinstance(expr, IsType):
        _scan_expr(expr.expr, func_params, current_struct)
    elif isinstance(expr, IsNil):
        _scan_expr(expr.expr, func_params, current_struct)
    elif isinstance(expr, Truthy):
        _scan_expr(expr.expr, func_params, current_struct)
    elif isinstance(expr, Len):
        _scan_expr(expr.expr, func_params, current_struct)
    elif isinstance(expr, AddrOf):
        _scan_expr(expr.operand, func_params, current_struct)
    elif isinstance(expr, StructLit):
        for v in expr.fields.values():
            _scan_expr(v, func_params, current_struct)
        if expr.embedded_value:
            _scan_expr(expr.embedded_value, func_params, current_struct)
    elif isinstance(expr, SliceLit):
        for e in expr.elements:
            _scan_expr(e, func_params, current_struct)
    elif isinstance(expr, SetLit):
        for e in expr.elements:
            _scan_expr(e, func_params, current_struct)
    elif isinstance(expr, MapLit):
        for k, v in expr.entries:
            _scan_expr(k, func_params, current_struct)
            _scan_expr(v, func_params, current_struct)
    elif isinstance(expr, TupleLit):
        for e in expr.elements:
            _scan_expr(e, func_params, current_struct)
    elif isinstance(expr, ListComp):
        _scan_expr(expr.element, func_params, current_struct)
        _scan_expr(expr.iterable, func_params, current_struct)
        if expr.condition:
            _scan_expr(expr.condition, func_params, current_struct)
    elif isinstance(expr, SetComp):
        _scan_expr(expr.element, func_params, current_struct)
        _scan_expr(expr.iterable, func_params, current_struct)
        if expr.condition:
            _scan_expr(expr.condition, func_params, current_struct)
    elif isinstance(expr, DictComp):
        _scan_expr(expr.key, func_params, current_struct)
        _scan_expr(expr.value, func_params, current_struct)
        _scan_expr(expr.iterable, func_params, current_struct)
        if expr.condition:
            _scan_expr(expr.condition, func_params, current_struct)
