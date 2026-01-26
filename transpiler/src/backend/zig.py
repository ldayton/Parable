"""Zig backend: IR → Zig code."""

from __future__ import annotations

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
    Ternary,
    TryCatch,
    Tuple,
    TupleLit,
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


class ZigBackend:
    """Emit Zig code from IR."""

    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self.receiver_name: str | None = None
        self.current_struct: str = ""

    def emit(self, module: Module) -> str:
        """Emit Zig code from IR Module."""
        self.indent = 0
        self.lines = []
        self._emit_module(module)
        return "\n".join(self.lines)

    def _line(self, text: str = "") -> None:
        if text:
            self.lines.append("    " * self.indent + text)
        else:
            self.lines.append("")

    def _emit_module(self, module: Module) -> None:
        self._line("const std = @import(\"std\");")
        self._line("const mem = std.mem;")
        self._line("const Allocator = std.mem.Allocator;")
        self._line("const ArrayList = std.ArrayList;")
        self._line("")
        if module.constants:
            for const in module.constants:
                self._emit_constant(const)
            self._line("")
        for struct in module.structs:
            self._emit_struct(struct)
        for func in module.functions:
            self._emit_function(func)

    def _emit_constant(self, const: Constant) -> None:
        typ = self._type(const.typ)
        val = self._expr(const.value)
        self._line(f"pub const {const.name}: {typ} = {val};")

    def _emit_struct(self, struct: Struct) -> None:
        self.current_struct = struct.name
        self._line(f"pub const {struct.name} = struct {{")
        self.indent += 1
        for fld in struct.fields:
            self._emit_field(fld)
        if struct.fields and struct.methods:
            self._line("")
        for i, method in enumerate(struct.methods):
            if i > 0:
                self._line("")
            self._emit_method(method)
        self.indent -= 1
        self._line("};")
        self._line("")
        self.current_struct = ""

    def _emit_field(self, fld: Field) -> None:
        typ = self._type(fld.typ)
        self._line(f"{_to_snake(fld.name)}: {typ},")

    def _emit_function(self, func: Function) -> None:
        params = self._params(func.params)
        ret = self._type(func.ret)
        name = _to_snake(func.name)
        pub = "pub " if not name.startswith("_") else ""
        if ret == "void":
            self._line(f"{pub}fn {name}({params}) void {{")
        else:
            self._line(f"{pub}fn {name}({params}) {ret} {{")
        self.indent += 1
        if not func.body:
            self._line("@panic(\"todo\");")
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")
        self._line("")

    def _emit_method(self, func: Function) -> None:
        params = self._method_params(func.params, func.receiver)
        ret = self._type(func.ret)
        name = _to_snake(func.name)
        pub = "pub " if not name.startswith("_") else ""
        if func.receiver:
            self.receiver_name = func.receiver.name
        if ret == "void":
            self._line(f"{pub}fn {name}({params}) void {{")
        else:
            self._line(f"{pub}fn {name}({params}) {ret} {{")
        self.indent += 1
        if not func.body:
            self._line("@panic(\"todo\");")
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")
        self.receiver_name = None

    def _params(self, params: list) -> str:
        parts = []
        for p in params:
            typ = self._type(p.typ)
            parts.append(f"{_to_snake(p.name)}: {typ}")
        return ", ".join(parts)

    def _method_params(self, params: list, receiver: Receiver | None) -> str:
        parts = []
        if receiver:
            if receiver.mutable or receiver.pointer:
                parts.append(f"self: *{receiver.typ.name}")
            else:
                parts.append(f"self: *const {receiver.typ.name}")
        for p in params:
            typ = self._type(p.typ)
            parts.append(f"{_to_snake(p.name)}: {typ}")
        return ", ".join(parts)

    def _emit_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDecl(name=name, typ=typ, value=value, mutable=mutable):
                zig_type = self._type(typ)
                if value is not None:
                    val = self._expr(value)
                    if mutable:
                        self._line(f"var {_to_snake(name)}: {zig_type} = {val};")
                    else:
                        self._line(f"const {_to_snake(name)}: {zig_type} = {val};")
                else:
                    default = self._default_value(typ)
                    if mutable:
                        self._line(f"var {_to_snake(name)}: {zig_type} = {default};")
                    else:
                        self._line(f"const {_to_snake(name)}: {zig_type} = {default};")
            case Assign(target=target, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                self._line(f"{lv} = {val};")
            case OpAssign(target=target, op=op, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                self._line(f"{lv} {op}= {val};")
            case ExprStmt(expr=expr):
                e = self._expr(expr)
                # Zig requires discarding unused values
                if not e.endswith(";"):
                    self._line(f"_ = {e};")
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
            case TypeSwitch(expr=expr, binding=binding, cases=cases, default=default):
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
                    self._line(f"break :{label};")
                else:
                    self._line("break;")
            case Continue(label=label):
                if label:
                    self._line(f"continue :{label};")
                else:
                    self._line("continue;")
            case Block(body=body):
                self._line("{")
                self.indent += 1
                for s in body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("}")
            case TryCatch(body=body, catch_var=catch_var, catch_body=catch_body, reraise=reraise):
                self._emit_try_catch(body, catch_var, catch_body, reraise)
            case Raise(error_type=error_type, message=message, pos=pos):
                msg = self._expr(message)
                self._line(f"@panic({msg});")
            case SoftFail():
                self._line("return null;")
            case _:
                self._line(f"// TODO: {type(stmt).__name__}")

    def _emit_type_switch(
        self, expr: Expr, binding: str, cases: list[TypeCase], default: list[Stmt]
    ) -> None:
        var = self._expr(expr)
        self._line(f"// type switch on {var}")
        self._line(f"const {_to_snake(binding)} = {var};")
        # Zig doesn't have runtime type switching like Go, emit as if-else chain
        for i, case in enumerate(cases):
            type_name = self._type_name_for_check(case.typ)
            keyword = "if" if i == 0 else "} else if"
            self._line(f"{keyword} (@TypeOf({var}) == {type_name}) {{")
            self.indent += 1
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
        expr_str = self._expr(expr)
        self._line(f"switch ({expr_str}) {{")
        self.indent += 1
        for case in cases:
            patterns = ", ".join(self._expr(p) for p in case.patterns)
            self._line(f"{patterns} => {{")
            self.indent += 1
            for s in case.body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("},")
        if default:
            self._line("else => {")
            self.indent += 1
            for s in default:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("},")
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
        if value is not None and index is not None:
            # Zig for with index requires manual tracking or enumeration
            self._line(f"for ({iter_expr}, 0..) |{_to_snake(value)}, {_to_snake(index)}| {{")
        elif value is not None:
            self._line(f"for ({iter_expr}) |{_to_snake(value)}| {{")
        elif index is not None:
            self._line(f"for ({iter_expr}, 0..) |_, {_to_snake(index)}| {{")
        else:
            self._line(f"for ({iter_expr}) |_| {{")
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
        # Zig doesn't have C-style for loops, convert to while
        if init is not None:
            self._emit_stmt(init)
        cond_str = self._expr(cond) if cond else "true"
        self._line(f"while ({cond_str}) {{")
        self.indent += 1
        for s in body:
            self._emit_stmt(s)
        if post is not None:
            self._emit_stmt(post)
        self.indent -= 1
        self._line("}")

    def _emit_try_catch(
        self,
        body: list[Stmt],
        catch_var: str | None,
        catch_body: list[Stmt],
        reraise: bool,
    ) -> None:
        # Zig uses error unions, emit as comment block for now
        self._line("// try-catch block")
        self._line("{")
        self.indent += 1
        for s in body:
            self._emit_stmt(s)
        self.indent -= 1
        self._line("}")

    def _expr(self, expr: Expr) -> str:
        match expr:
            case IntLit(value=value):
                return str(value)
            case FloatLit(value=value):
                s = str(value)
                if "." not in s and "e" not in s.lower():
                    return s + ".0"
                return s
            case StringLit(value=value):
                return _string_literal(value)
            case BoolLit(value=value):
                return "true" if value else "false"
            case NilLit():
                return "null"
            case Var(name=name):
                if name == self.receiver_name:
                    return "self"
                if name.isupper():
                    return name
                return _to_snake(name)
            case FieldAccess(obj=obj, field=field):
                return f"{self._expr(obj)}.{_to_snake(field)}"
            case Index(obj=obj, index=index):
                return f"{self._expr(obj)}[{self._expr(index)}]"
            case SliceExpr(obj=obj, low=low, high=high):
                return self._slice_expr(obj, low, high)
            case Call(func=func, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                return f"{_to_snake(func)}({args_str})"
            case MethodCall(obj=obj, method=method, args=args, receiver_type=receiver_type):
                return self._method_call(obj, method, args, receiver_type)
            case StaticCall(on_type=on_type, method=method, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                type_name = self._type_name_for_check(on_type)
                return f"{type_name}.{_to_snake(method)}({args_str})"
            case BinaryOp(op=op, left=left, right=right):
                zig_op = _binary_op(op)
                # String comparison needs mem.eql
                if zig_op == "==" and _is_string_type(left.typ):
                    return f"mem.eql(u8, {self._expr(left)}, {self._expr(right)})"
                if zig_op == "!=" and _is_string_type(left.typ):
                    return f"!mem.eql(u8, {self._expr(left)}, {self._expr(right)})"
                return f"({self._expr(left)} {zig_op} {self._expr(right)})"
            case UnaryOp(op=op, operand=operand):
                zig_op = "!" if op == "!" else op
                return f"{zig_op}{self._expr(operand)}"
            case Ternary(cond=cond, then_expr=then_expr, else_expr=else_expr):
                # Zig has if expressions
                return f"if ({self._expr(cond)}) {self._expr(then_expr)} else {self._expr(else_expr)}"
            case Cast(expr=inner, to_type=to_type):
                return self._cast(inner, to_type)
            case TypeAssert(expr=inner, asserted=asserted, safe=safe):
                # Zig doesn't have dynamic type assertions
                return self._expr(inner)
            case IsType(expr=inner, tested_type=tested_type):
                type_name = self._type_name_for_check(tested_type)
                return f"@TypeOf({self._expr(inner)}) == {type_name}"
            case IsNil(expr=inner, negated=negated):
                if negated:
                    return f"{self._expr(inner)} != null"
                return f"{self._expr(inner)} == null"
            case Len(expr=inner):
                return f"{self._expr(inner)}.len"
            case MakeSlice(element_type=element_type, length=length, capacity=capacity):
                typ = self._type(element_type)
                if capacity:
                    return f"try ArrayList({typ}).initCapacity(allocator, {self._expr(capacity)})"
                if length:
                    return f"try allocator.alloc({typ}, {self._expr(length)})"
                return f"ArrayList({typ}).init(allocator)"
            case MakeMap(key_type=key_type, value_type=value_type):
                kt = self._type(key_type)
                vt = self._type(value_type)
                if kt == "[]const u8":
                    return f"std.StringHashMap({vt}).init(allocator)"
                return f"std.AutoHashMap({kt}, {vt}).init(allocator)"
            case SliceLit(elements=elements, element_type=element_type):
                if not elements:
                    return "&[_]" + self._type(element_type) + "{}"
                elems = ", ".join(self._expr(e) for e in elements)
                return f"&[_]{self._type(element_type)}{{{elems}}}"
            case MapLit(entries=entries, key_type=key_type, value_type=value_type):
                kt = self._type(key_type)
                vt = self._type(value_type)
                if kt == "[]const u8":
                    return f"std.StringHashMap({vt}).init(allocator)"
                return f"std.AutoHashMap({kt}, {vt}).init(allocator)"
            case SetLit(elements=elements, element_type=element_type):
                et = self._type(element_type)
                return f"std.AutoHashMap({et}, void).init(allocator)"
            case StructLit(struct_name=struct_name, fields=fields):
                if not fields:
                    return f"{struct_name}{{}}"
                args = ", ".join(f".{_to_snake(k)} = {self._expr(v)}" for k, v in fields.items())
                return f"{struct_name}{{ {args} }}"
            case TupleLit(elements=elements):
                elems = ", ".join(self._expr(e) for e in elements)
                return f".{{ {elems} }}"
            case StringConcat(parts=parts):
                if len(parts) == 1:
                    return self._expr(parts[0])
                # Zig uses ++ for array/slice concat
                return " ++ ".join(self._expr(p) for p in parts)
            case StringFormat(template=template, args=args):
                return self._format_string(template, args)
            case _:
                return f"undefined // TODO: {type(expr).__name__}"

    def _method_call(self, obj: Expr, method: str, args: list[Expr], receiver_type: Type) -> str:
        args_str = ", ".join(self._expr(a) for a in args)
        # Handle slice methods
        if isinstance(receiver_type, Slice):
            if method == "append" and args:
                return f"try {self._expr(obj)}.append({args_str})"
            if method == "pop" and not args:
                return f"{self._expr(obj)}.pop()"
        return f"{self._expr(obj)}.{_to_snake(method)}({args_str})"

    def _slice_expr(self, obj: Expr, low: Expr | None, high: Expr | None) -> str:
        obj_str = self._expr(obj)
        if low and high:
            return f"{obj_str}[{self._expr(low)}..{self._expr(high)}]"
        elif low:
            return f"{obj_str}[{self._expr(low)}..]"
        elif high:
            return f"{obj_str}[0..{self._expr(high)}]"
        return f"{obj_str}[0..]"

    def _cast(self, inner: Expr, to_type: Type) -> str:
        inner_str = self._expr(inner)
        zig_type = self._type(to_type)
        # Zig uses @intCast, @floatCast, etc.
        if isinstance(to_type, Primitive):
            if to_type.kind == "int":
                return f"@intCast({inner_str})"
            if to_type.kind == "float":
                return f"@floatCast({inner_str})"
            if to_type.kind == "byte":
                return f"@intCast({inner_str})"
        return f"@as({zig_type}, {inner_str})"

    def _format_string(self, template: str, args: list[Expr]) -> str:
        # Convert {0}, {1}, etc. and %v to {} for Zig
        import re
        result = re.sub(r'\{\d+\}', '{}', template)
        result = result.replace("%v", "{}").replace("%%", "%")
        escaped = result.replace("\\", "\\\\").replace('"', '\\"')
        args_str = ", ".join(self._expr(a) for a in args)
        if args_str:
            return f'std.fmt.allocPrint(allocator, "{escaped}", .{{ {args_str} }}) catch unreachable'
        return f'"{escaped}"'

    def _lvalue(self, lv: LValue) -> str:
        match lv:
            case VarLV(name=name):
                if name == self.receiver_name:
                    return "self"
                return _to_snake(name)
            case FieldLV(obj=obj, field=field):
                return f"{self._expr(obj)}.{_to_snake(field)}"
            case IndexLV(obj=obj, index=index):
                return f"{self._expr(obj)}[{self._expr(index)}]"
            case DerefLV(ptr=ptr):
                return f"{self._expr(ptr)}.*"
            case _:
                return f"undefined // lvalue: {type(lv).__name__}"

    def _type(self, typ: Type) -> str:
        match typ:
            case Primitive(kind=kind):
                return _primitive_type(kind)
            case Slice(element=element):
                return f"[]const {self._type(element)}"
            case Array(element=element, size=size):
                return f"[{size}]{self._type(element)}"
            case Map(key=key, value=value):
                kt = self._type(key)
                vt = self._type(value)
                if kt == "[]const u8":
                    return f"std.StringHashMap({vt})"
                return f"std.AutoHashMap({kt}, {vt})"
            case Set(element=element):
                return f"std.AutoHashMap({self._type(element)}, void)"
            case Tuple(elements=elements):
                # Zig uses anonymous structs for tuples
                parts = ", ".join(self._type(e) for e in elements)
                return f"struct {{ {parts} }}"
            case Pointer(target=target):
                return f"*{self._type(target)}"
            case Optional(inner=inner):
                return f"?{self._type(inner)}"
            case StructRef(name=name):
                return name
            case Interface(name=name):
                if name == "any":
                    return "*anyopaque"
                return name
            case Union(name=name, variants=variants):
                if name:
                    return name
                return "union"
            case FuncType(params=params, ret=ret):
                params_str = ", ".join(self._type(p) for p in params)
                ret_str = self._type(ret)
                return f"*const fn({params_str}) {ret_str}"
            case StringSlice():
                return "[]const u8"
            case _:
                return "*anyopaque"

    def _type_name_for_check(self, typ: Type) -> str:
        match typ:
            case StructRef(name=name):
                return name
            case Interface(name=name):
                return name
            case Pointer(target=target):
                return self._type_name_for_check(target)
            case _:
                return self._type(typ)

    def _default_value(self, typ: Type) -> str:
        match typ:
            case Primitive(kind="string"):
                return '""'
            case Primitive(kind="int"):
                return "0"
            case Primitive(kind="float"):
                return "0.0"
            case Primitive(kind="bool"):
                return "false"
            case Primitive(kind="byte"):
                return "0"
            case Primitive(kind="rune"):
                return "0"
            case Slice():
                return "&[_]{}"
            case Optional():
                return "null"
            case _:
                return "undefined"


def _primitive_type(kind: str) -> str:
    match kind:
        case "string":
            return "[]const u8"
        case "int":
            return "i64"
        case "float":
            return "f64"
        case "bool":
            return "bool"
        case "byte":
            return "u8"
        case "rune":
            return "u21"  # Unicode code point
        case "void":
            return "void"
        case _:
            return "*anyopaque"


def _binary_op(op: str) -> str:
    match op:
        case "&&":
            return "and"
        case "||":
            return "or"
        case _:
            return op


def _is_string_type(typ: Type) -> bool:
    if isinstance(typ, Primitive) and typ.kind == "string":
        return True
    if isinstance(typ, StringSlice):
        return True
    return False


def _to_snake(name: str) -> str:
    """Convert camelCase/PascalCase to snake_case."""
    if name.startswith("_"):
        name = name[1:]
    if "_" in name:
        return name.lower()
    result = []
    for i, c in enumerate(name):
        if c.isupper() and i > 0:
            result.append("_")
        result.append(c.lower())
    return "".join(result)


def _string_literal(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
    return f'"{escaped}"'
