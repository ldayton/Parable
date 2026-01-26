"""TypeScript backend: IR → TypeScript code."""

from __future__ import annotations

from src.backend.util import escape_string
from src.ir import (
    Array,
    Assign,
    BinaryOp,
    Block,
    BoolLit,
    Break,
    Call,
    Cast,
    Constant,
    Continue,
    DerefLV,
    Expr,
    ExprStmt,
    Field,
    FieldAccess,
    FieldLV,
    FloatLit,
    ForClassic,
    ForRange,
    FuncType,
    Function,
    If,
    Index,
    IndexLV,
    IntLit,
    Interface,
    InterfaceDef,
    IsNil,
    IsType,
    Len,
    LValue,
    MakeMap,
    MakeSlice,
    Map,
    MapLit,
    Match,
    MethodCall,
    Module,
    NilLit,
    OpAssign,
    Optional,
    Pointer,
    Primitive,
    Raise,
    Receiver,
    Return,
    Set,
    SetLit,
    Slice,
    SliceExpr,
    SliceLit,
    SoftFail,
    StaticCall,
    Stmt,
    StringConcat,
    StringFormat,
    StringLit,
    StringSlice,
    Struct,
    StructLit,
    StructRef,
    TupleLit,
    Ternary,
    TryCatch,
    Tuple,
    Type,
    TypeAssert,
    TypeCase,
    TypeSwitch,
    UnaryOp,
    Union,
    Var,
    VarDecl,
    VarLV,
    While,
)


class TsBackend:
    """Emit TypeScript code from IR."""

    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self.receiver_name: str | None = None

    def emit(self, module: Module) -> str:
        """Emit TypeScript code from IR Module."""
        self.indent = 0
        self.lines = []
        self._emit_module(module)
        return "\n".join(self.lines)

    def _line(self, text: str = "") -> None:
        if text:
            self.lines.append("  " * self.indent + text)
        else:
            self.lines.append("")

    def _emit_module(self, module: Module) -> None:
        if module.doc:
            self._line(f"/** {module.doc} */")
        need_blank = False
        if module.constants:
            for const in module.constants:
                self._emit_constant(const)
            need_blank = True
        for iface in module.interfaces:
            if need_blank:
                self._line()
            self._emit_interface(iface)
            need_blank = True
        for struct in module.structs:
            if need_blank:
                self._line()
            self._emit_struct(struct)
            need_blank = True
        for func in module.functions:
            if need_blank:
                self._line()
            self._emit_function(func)
            need_blank = True

    def _emit_constant(self, const: Constant) -> None:
        typ = self._type(const.typ)
        val = self._expr(const.value)
        self._line(f"const {const.name}: {typ} = {val};")

    def _emit_interface(self, iface: InterfaceDef) -> None:
        self._line(f"interface {iface.name} {{")
        self.indent += 1
        for method in iface.methods:
            params = self._params(method.params)
            ret = self._type(method.ret)
            self._line(f"{_camel(method.name)}({params}): {ret};")
        self.indent -= 1
        self._line("}")

    def _emit_struct(self, struct: Struct) -> None:
        if struct.doc:
            self._line(f"/** {struct.doc} */")
        implements = ""
        if struct.implements:
            implements = f" implements {', '.join(struct.implements)}"
        self._line(f"class {struct.name}{implements} {{")
        self.indent += 1
        for fld in struct.fields:
            self._emit_field(fld)
        if struct.fields:
            self._line()
            self._emit_constructor(struct)
        for i, method in enumerate(struct.methods):
            if i > 0 or struct.fields:
                self._line()
            self._emit_method(method)
        self.indent -= 1
        self._line("}")

    def _emit_field(self, fld: Field) -> None:
        typ = self._type(fld.typ)
        self._line(f"{_camel(fld.name)}: {typ};")

    def _emit_constructor(self, struct: Struct) -> None:
        params = ", ".join(
            f"{_camel(f.name)}: {self._type(f.typ)}" for f in struct.fields
        )
        self._line(f"constructor({params}) {{")
        self.indent += 1
        for fld in struct.fields:
            name = _camel(fld.name)
            self._line(f"this.{name} = {name};")
        self.indent -= 1
        self._line("}")

    def _emit_function(self, func: Function) -> None:
        if func.doc:
            self._line(f"/** {func.doc} */")
        params = self._params(func.params)
        ret = self._type(func.ret)
        self._line(f"function {_camel(func.name)}({params}): {ret} {{")
        self.indent += 1
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")

    def _emit_method(self, func: Function) -> None:
        if func.doc:
            self._line(f"/** {func.doc} */")
        params = self._params(func.params)
        ret = self._type(func.ret)
        self._line(f"{_camel(func.name)}({params}): {ret} {{")
        self.indent += 1
        if func.receiver:
            self.receiver_name = func.receiver.name
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.receiver_name = None
        self.indent -= 1
        self._line("}")

    def _params(self, params: list) -> str:
        parts = []
        for p in params:
            typ = self._type(p.typ)
            parts.append(f"{_camel(p.name)}: {typ}")
        return ", ".join(parts)

    def _emit_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDecl(name=name, typ=typ, value=value):
                keyword = "let" if getattr(stmt, 'is_reassigned', False) else "const"
                if value is not None:
                    val = self._expr(value)
                    if _can_infer_type(value):
                        self._line(f"{keyword} {_camel(name)} = {val};")
                    else:
                        ts_type = self._type(typ)
                        self._line(f"{keyword} {_camel(name)}: {ts_type} = {val};")
                else:
                    ts_type = self._type(typ)
                    self._line(f"{keyword} {_camel(name)}: {ts_type};")
            case Assign(target=target, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                self._line(f"{lv} = {val};")
            case OpAssign(target=target, op=op, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                self._line(f"{lv} {op}= {val};")
            case ExprStmt(expr=expr):
                self._line(f"{self._expr(expr)};")
            case Return(value=value):
                if value is not None:
                    self._line(f"return {self._expr(value)};")
                else:
                    self._line("return;")
            case If(cond=cond, then_body=then_body, else_body=else_body, init=init):
                if init is not None:
                    self._emit_stmt(init)
                self._line(f"if ({self._expr(cond)}) {{")
                self.indent += 1
                for s in then_body:
                    self._emit_stmt(s)
                self.indent -= 1
                if else_body:
                    self._line("} else {")
                    self.indent += 1
                    for s in else_body:
                        self._emit_stmt(s)
                    self.indent -= 1
                self._line("}")
            case TypeSwitch(
                expr=expr, binding=binding, cases=cases, default=default
            ):
                self._emit_type_switch(expr, binding, cases, default)
            case Match(expr=expr, cases=cases, default=default):
                self._emit_match(expr, cases, default)
            case ForRange(index=index, value=value, iterable=iterable, body=body):
                self._emit_for_range(index, value, iterable, body)
            case ForClassic(init=init, cond=cond, post=post, body=body):
                self._emit_for_classic(init, cond, post, body)
            case While(cond=cond, body=body):
                self._line(f"while ({self._expr(cond)}) {{")
                self.indent += 1
                for s in body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("}")
            case Break(label=label):
                if label:
                    self._line(f"break {label};")
                else:
                    self._line("break;")
            case Continue(label=label):
                if label:
                    self._line(f"continue {label};")
                else:
                    self._line("continue;")
            case Block(body=body):
                self._line("{")
                self.indent += 1
                for s in body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("}")
            case TryCatch(
                body=body, catch_var=catch_var, catch_body=catch_body, reraise=reraise
            ):
                self._emit_try_catch(body, catch_var, catch_body, reraise)
            case Raise(error_type=error_type, message=message, pos=pos):
                msg = self._expr(message)
                p = self._expr(pos)
                self._line(f"throw new {error_type}({msg}, {p});")
            case SoftFail():
                self._line("return null;")
            case _:
                raise NotImplementedError(f"Unknown statement: {type(stmt).__name__}")

    def _emit_type_switch(
        self, expr: Expr, binding: str, cases: list[TypeCase], default: list[Stmt]
    ) -> None:
        var = self._expr(expr)
        for i, case in enumerate(cases):
            type_name = self._type_name_for_check(case.typ)
            keyword = "if" if i == 0 else "} else if"
            self._line(f"{keyword} ({var} instanceof {type_name}) {{")
            self.indent += 1
            self._line(f"const {_camel(binding)} = {var} as {self._type(case.typ)};")
            for s in case.body:
                self._emit_stmt(s)
            self.indent -= 1
        if default:
            self._line("} else {")
            self.indent += 1
            for s in default:
                self._emit_stmt(s)
            self.indent -= 1
        self._line("}")

    def _emit_match(self, expr: Expr, cases: list, default: list[Stmt]) -> None:
        self._line(f"switch ({self._expr(expr)}) {{")
        self.indent += 1
        for case in cases:
            for pattern in case.patterns:
                self._line(f"case {self._expr(pattern)}:")
            self.indent += 1
            for s in case.body:
                self._emit_stmt(s)
            if not _ends_with_return(case.body):
                self._line("break;")
            self.indent -= 1
        if default:
            self._line("default:")
            self.indent += 1
            for s in default:
                self._emit_stmt(s)
            self.indent -= 1
        self.indent -= 1
        self._line("}")

    def _emit_for_range(
        self,
        index: str | None,
        value: str | None,
        iterable: Expr,
        body: list[Stmt],
    ) -> None:
        iter_expr = self._expr(iterable)
        if index is not None and value is not None:
            self._line(f"for (let {_camel(index)} = 0; {_camel(index)} < {iter_expr}.length; {_camel(index)}++) {{")
            self.indent += 1
            self._line(f"const {_camel(value)} = {iter_expr}[{_camel(index)}];")
        elif value is not None:
            self._line(f"for (const {_camel(value)} of {iter_expr}) {{")
            self.indent += 1
        elif index is not None:
            self._line(f"for (let {_camel(index)} = 0; {_camel(index)} < {iter_expr}.length; {_camel(index)}++) {{")
            self.indent += 1
        else:
            self._line(f"for (const _ of {iter_expr}) {{")
            self.indent += 1
        for s in body:
            self._emit_stmt(s)
        self.indent -= 1
        self._line("}")

    def _emit_for_classic(
        self,
        init: Stmt | None,
        cond: Expr | None,
        post: Stmt | None,
        body: list[Stmt],
    ) -> None:
        init_str = self._stmt_inline(init) if init else ""
        cond_str = self._expr(cond) if cond else ""
        post_str = self._stmt_inline(post) if post else ""
        self._line(f"for ({init_str}; {cond_str}; {post_str}) {{")
        self.indent += 1
        for s in body:
            self._emit_stmt(s)
        self.indent -= 1
        self._line("}")

    def _stmt_inline(self, stmt: Stmt) -> str:
        match stmt:
            case VarDecl(name=name, typ=typ, value=value):
                keyword = "let" if getattr(stmt, 'is_reassigned', False) else "const"
                if value is not None:
                    if _can_infer_type(value):
                        return f"{keyword} {_camel(name)} = {self._expr(value)}"
                    else:
                        ts_type = self._type(typ)
                        return f"{keyword} {_camel(name)}: {ts_type} = {self._expr(value)}"
                ts_type = self._type(typ)
                return f"{keyword} {_camel(name)}: {ts_type}"
            case Assign(target=VarLV(name=name), value=BinaryOp(op=op, left=Var(name=left_name), right=IntLit(value=1))) if name == left_name and op in ("+", "-"):
                return f"{_camel(name)}++" if op == "+" else f"{_camel(name)}--"
            case Assign(target=target, value=value):
                return f"{self._lvalue(target)} = {self._expr(value)}"
            case OpAssign(target=target, op=op, value=value):
                return f"{self._lvalue(target)} {op}= {self._expr(value)}"
            case ExprStmt(expr=expr):
                return self._expr(expr)
            case _:
                raise NotImplementedError(f"Cannot inline: {type(stmt).__name__}")

    def _emit_try_catch(
        self,
        body: list[Stmt],
        catch_var: str | None,
        catch_body: list[Stmt],
        reraise: bool,
    ) -> None:
        self._line("try {")
        self.indent += 1
        for s in body:
            self._emit_stmt(s)
        self.indent -= 1
        var = _camel(catch_var) if catch_var else "_e"
        self._line(f"}} catch ({var}) {{")
        self.indent += 1
        for s in catch_body:
            self._emit_stmt(s)
        if reraise:
            self._line(f"throw {var};")
        self.indent -= 1
        self._line("}")

    def _expr(self, expr: Expr) -> str:
        match expr:
            case IntLit(value=value):
                return str(value)
            case FloatLit(value=value):
                return str(value)
            case StringLit(value=value):
                return _string_literal(value)
            case BoolLit(value=value):
                return "true" if value else "false"
            case NilLit():
                return "null"
            case Var(name=name):
                if name == self.receiver_name:
                    return "this"
                return _camel(name)
            case FieldAccess(obj=obj, field=field):
                return f"{self._expr(obj)}.{_camel(field)}"
            case Index(obj=obj, index=index):
                return f"{self._expr(obj)}[{self._expr(index)}]"
            case SliceExpr(obj=obj, low=low, high=high):
                return self._slice_expr(obj, low, high)
            case Call(func=func, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                return f"{_camel(func)}({args_str})"
            case MethodCall(obj=obj, method=method, args=args, receiver_type=receiver_type):
                args_str = ", ".join(self._expr(a) for a in args)
                ts_method = _method_name(method, receiver_type)
                return f"{self._expr(obj)}.{ts_method}({args_str})"
            case StaticCall(on_type=on_type, method=method, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                type_name = self._type_name_for_check(on_type)
                return f"{type_name}.{_camel(method)}({args_str})"
            case BinaryOp(op=op, left=left, right=right):
                ts_op = _binary_op(op)
                left_str = self._expr_with_precedence(left, op, is_right=False)
                right_str = self._expr_with_precedence(right, op, is_right=True)
                return f"{left_str} {ts_op} {right_str}"
            case UnaryOp(op=op, operand=operand):
                return f"{op}{self._expr(operand)}"
            case Ternary(cond=cond, then_expr=then_expr, else_expr=else_expr):
                return f"{self._expr(cond)} ? {self._expr(then_expr)} : {self._expr(else_expr)}"
            case Cast(expr=inner, to_type=to_type):
                ts_type = self._type(to_type)
                from_type = self._type(inner.typ) if hasattr(inner, 'typ') else None
                if from_type == ts_type:
                    return self._expr(inner)
                return f"({self._expr(inner)} as {ts_type})"
            case TypeAssert(expr=inner, asserted=asserted):
                return f"({self._expr(inner)} as {self._type(asserted)})"
            case IsType(expr=inner, tested_type=tested_type):
                type_name = self._type_name_for_check(tested_type)
                return f"{self._expr(inner)} instanceof {type_name}"
            case IsNil(expr=inner, negated=negated):
                op = "!==" if negated else "==="
                return f"{self._expr(inner)} {op} null"
            case Len(expr=inner):
                return f"{self._expr(inner)}.length"
            case MakeSlice(element_type=_, length=length, capacity=_):
                if length is not None:
                    return f"new Array({self._expr(length)})"
                return "[]"
            case MakeMap():
                return "new Map()"
            case SliceLit(elements=elements):
                elems = ", ".join(self._expr(e) for e in elements)
                return f"[{elems}]"
            case MapLit(entries=entries):
                if not entries:
                    return "new Map()"
                pairs = ", ".join(
                    f"[{self._expr(k)}, {self._expr(v)}]" for k, v in entries
                )
                return f"new Map([{pairs}])"
            case SetLit(elements=elements):
                elems = ", ".join(self._expr(e) for e in elements)
                return f"new Set([{elems}])"
            case StructLit(struct_name=struct_name, fields=fields):
                args = ", ".join(self._expr(v) for v in fields.values())
                return f"new {struct_name}({args})"
            case TupleLit(elements=elements):
                elems = ", ".join(self._expr(e) for e in elements)
                return f"[{elems}]"
            case StringConcat(parts=parts):
                return " + ".join(self._expr(p) for p in parts)
            case StringFormat(template=template, args=args):
                return self._format_string(template, args)
            case _:
                raise NotImplementedError(f"Unknown expression: {type(expr).__name__}")

    def _slice_expr(self, obj: Expr, low: Expr | None, high: Expr | None) -> str:
        obj_str = self._expr(obj)
        if low is None and high is None:
            return f"{obj_str}.slice()"
        elif low is None:
            return f"{obj_str}.slice(0, {self._expr(high)})"
        elif high is None:
            return f"{obj_str}.slice({self._expr(low)})"
        else:
            return f"{obj_str}.slice({self._expr(low)}, {self._expr(high)})"

    def _expr_with_precedence(self, expr: Expr, parent_op: str, is_right: bool) -> str:
        """Wrap expr in parens if needed based on operator precedence."""
        inner = self._expr(expr)
        if not isinstance(expr, BinaryOp):
            return inner
        child_prec = _op_precedence(expr.op)
        parent_prec = _op_precedence(parent_op)
        # Need parens if child has lower precedence, or same precedence on right side
        needs_parens = child_prec < parent_prec or (child_prec == parent_prec and is_right)
        return f"({inner})" if needs_parens else inner

    def _format_string(self, template: str, args: list[Expr]) -> str:
        result = template
        for i, arg in enumerate(args):
            result = result.replace(f"{{{i}}}", f"${{{self._expr(arg)}}}", 1)
        return f"`{result}`"

    def _lvalue(self, lv: LValue) -> str:
        match lv:
            case VarLV(name=name):
                if name == self.receiver_name:
                    return "this"
                return _camel(name)
            case FieldLV(obj=obj, field=field):
                return f"{self._expr(obj)}.{_camel(field)}"
            case IndexLV(obj=obj, index=index):
                return f"{self._expr(obj)}[{self._expr(index)}]"
            case DerefLV(ptr=ptr):
                return self._expr(ptr)
            case _:
                raise NotImplementedError(f"Unknown lvalue: {type(lv).__name__}")

    def _type(self, typ: Type) -> str:
        match typ:
            case Primitive(kind=kind):
                return _primitive_type(kind)
            case Slice(element=element):
                return f"{self._type(element)}[]"
            case Array(element=element):
                return f"{self._type(element)}[]"
            case Map(key=key, value=value):
                return f"Map<{self._type(key)}, {self._type(value)}>"
            case Set(element=element):
                return f"Set<{self._type(element)}>"
            case Tuple(elements=elements):
                parts = ", ".join(self._type(e) for e in elements)
                return f"[{parts}]"
            case Pointer(target=target):
                return self._type(target)
            case Optional(inner=inner):
                return f"{self._type(inner)} | null"
            case StructRef(name=name):
                return name
            case Interface(name=name):
                return name
            case Union(name=name, variants=variants):
                if name:
                    return name
                parts = " | ".join(self._type(v) for v in variants)
                return f"({parts})"
            case FuncType(params=params, ret=ret):
                params_str = ", ".join(
                    f"p{i}: {self._type(p)}" for i, p in enumerate(params)
                )
                return f"(({params_str}) => {self._type(ret)})"
            case StringSlice():
                return "string"
            case _:
                raise NotImplementedError(f"Unknown type: {type(typ).__name__}")

    def _type_name_for_check(self, typ: Type) -> str:
        match typ:
            case StructRef(name=name):
                return name
            case Interface(name=name):
                return name
            case _:
                return self._type(typ)


def _primitive_type(kind: str) -> str:
    match kind:
        case "string":
            return "string"
        case "int" | "float" | "byte" | "rune":
            return "number"
        case "bool":
            return "boolean"
        case "void":
            return "void"
        case _:
            raise NotImplementedError(f"Unknown primitive: {kind}")


def _camel(name: str) -> str:
    if name in ("this", "self"):
        return "this"
    if "_" not in name:
        return name
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _method_name(method: str, receiver_type: Type) -> str:
    """Convert method name based on receiver type."""
    if isinstance(receiver_type, Slice) and method == "append":
        return "push"
    return _camel(method)


def _binary_op(op: str) -> str:
    match op:
        case "&&":
            return "&&"
        case "||":
            return "||"
        case "==":
            return "==="
        case "!=":
            return "!=="
        case _:
            return op


def _string_literal(value: str) -> str:
    return f'"{escape_string(value)}"'


def _ends_with_return(body: list[Stmt]) -> bool:
    """Check if a statement list ends with a return (no break needed)."""
    return bool(body) and isinstance(body[-1], Return)


def _op_precedence(op: str) -> int:
    """Return precedence level for binary operator (higher = binds tighter)."""
    match op:
        case "||":
            return 1
        case "&&":
            return 2
        case "==" | "!=" | "===" | "!==":
            return 3
        case "<" | ">" | "<=" | ">=":
            return 4
        case "+" | "-":
            return 5
        case "*" | "/" | "%":
            return 6
        case _:
            return 10


def _can_infer_type(value: Expr) -> bool:
    """Check if TypeScript can infer the type from the value expression."""
    match value:
        case IntLit() | FloatLit() | StringLit() | BoolLit():
            return True
        case NilLit():
            return False  # null needs type annotation
        case Var() | FieldAccess() | Index():
            return True
        case Call() | MethodCall() | StaticCall():
            return True
        case BinaryOp() | UnaryOp() | Ternary():
            return True
        case SliceLit(elements=elements):
            return len(elements) > 0  # Empty array needs type
        case MapLit(entries=entries):
            return len(entries) > 0  # Empty map needs type
        case SetLit(elements=elements):
            return len(elements) > 0  # Empty set needs type
        case StructLit() | TupleLit():
            return True
        case SliceExpr() | Len() | Cast() | TypeAssert():
            return True
        case MakeSlice() | MakeMap():
            return False  # new Array(n) and new Map() need type annotations
        case StringConcat() | StringFormat():
            return True
        case _:
            return False
