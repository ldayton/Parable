"""Swift backend: IR → Swift code."""

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


class SwiftBackend:
    """Emit Swift code from IR."""

    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self.receiver_name: str | None = None
        self.current_class: str = ""

    def emit(self, module: Module) -> str:
        """Emit Swift code from IR Module."""
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
        self._line("import Foundation")
        self._line("")
        if module.constants:
            self._line("enum Constants {")
            self.indent += 1
            for const in module.constants:
                self._emit_constant(const)
            self.indent -= 1
            self._line("}")
            self._line("")
        for iface in module.interfaces:
            self._emit_interface(iface)
            self._line("")
        for struct in module.structs:
            self._emit_struct(struct)
            self._line("")
        for func in module.functions:
            self._emit_function(func)
            self._line("")

    def _emit_constant(self, const: Constant) -> None:
        typ = self._type(const.typ)
        val = self._expr(const.value)
        name = _to_screaming_snake(const.name)
        self._line(f"static let {name}: {typ} = {val}")

    def _emit_interface(self, iface: InterfaceDef) -> None:
        self._line(f"protocol {iface.name} {{")
        self.indent += 1
        for method in iface.methods:
            params = self._params(method.params)
            ret = self._type(method.ret)
            name = _to_camel(method.name)
            if ret == "Void":
                self._line(f"func {name}({params})")
            else:
                self._line(f"func {name}({params}) -> {ret}")
        self.indent -= 1
        self._line("}")

    def _emit_struct(self, struct: Struct) -> None:
        self.current_class = struct.name
        self._line(f"class {struct.name} {{")
        self.indent += 1
        for fld in struct.fields:
            self._emit_field(fld)
        if struct.fields:
            self._line("")
        self._emit_init(struct)
        for i, method in enumerate(struct.methods):
            self._line("")
            self._emit_method(method)
        self.indent -= 1
        self._line("}")
        self.current_class = ""

    def _emit_init(self, struct: Struct) -> None:
        """Emit initializer with all fields as parameters."""
        if not struct.fields:
            return
        params = ", ".join(
            f"{_to_camel(f.name)}: {self._type(f.typ)}" for f in struct.fields
        )
        self._line(f"init({params}) {{")
        self.indent += 1
        for f in struct.fields:
            name = _to_camel(f.name)
            self._line(f"self.{name} = {name}")
        self.indent -= 1
        self._line("}")

    def _emit_field(self, fld: Field) -> None:
        typ = self._type(fld.typ)
        self._line(f"var {_to_camel(fld.name)}: {typ}")

    def _emit_function(self, func: Function) -> None:
        params = self._params(func.params)
        ret = self._type(func.ret)
        name = _to_camel(func.name)
        if ret == "Void":
            self._line(f"func {name}({params}) {{")
        else:
            self._line(f"func {name}({params}) -> {ret} {{")
        self.indent += 1
        if not func.body:
            self._line('fatalError("todo")')
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")

    def _emit_method(self, func: Function) -> None:
        params = self._params(func.params)
        ret = self._type(func.ret)
        name = _to_camel(func.name)
        if func.receiver:
            self.receiver_name = func.receiver.name
        if ret == "Void":
            self._line(f"func {name}({params}) {{")
        else:
            self._line(f"func {name}({params}) -> {ret} {{")
        self.indent += 1
        if not func.body:
            self._line('fatalError("todo")')
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")
        self.receiver_name = None

    def _params(self, params: list) -> str:
        parts = []
        for p in params:
            typ = self._type(p.typ)
            parts.append(f"_ {_to_camel(p.name)}: {typ}")
        return ", ".join(parts)

    def _emit_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDecl(name=name, typ=typ, value=value, mutable=mutable):
                swift_type = self._type(typ)
                var_name = _to_camel(name)
                keyword = "var" if mutable else "let"
                if value is not None:
                    val = self._expr(value)
                    self._line(f"{keyword} {var_name}: {swift_type} = {val}")
                else:
                    default = self._default_value(typ)
                    self._line(f"{keyword} {var_name}: {swift_type} = {default}")
            case Assign(target=target, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                self._line(f"{lv} = {val}")
            case OpAssign(target=target, op=op, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                self._line(f"{lv} {op}= {val}")
            case ExprStmt(expr=expr):
                e = self._expr(expr)
                self._line(f"{e}")
            case Return(value=value):
                if value is not None:
                    self._line(f"return {self._expr(value)}")
                else:
                    self._line("return")
            case If(cond=cond, then_body=then_body, else_body=else_body, init=init):
                if init is not None:
                    self._emit_stmt(init)
                self._line(f"if {self._expr(cond)} {{")
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
                self._line(f"while {self._expr(cond)} {{")
                self.indent += 1
                for s in body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("}")
            case Break(label=label):
                if label:
                    self._line(f"break {label}")
                else:
                    self._line("break")
            case Continue(label=label):
                if label:
                    self._line(f"continue {label}")
                else:
                    self._line("continue")
            case Block(body=body):
                self._line("do {")
                self.indent += 1
                for s in body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("}")
            case TryCatch(body=body, catch_var=catch_var, catch_body=catch_body, reraise=reraise):
                self._emit_try_catch(body, catch_var, catch_body, reraise)
            case Raise(error_type=error_type, message=message, pos=pos):
                msg = self._expr(message)
                self._line(f"throw NSError(domain: {msg}, code: 0)")
            case SoftFail():
                self._line("return nil")
            case _:
                self._line(f"// TODO: {type(stmt).__name__}")

    def _emit_type_switch(
        self, expr: Expr, binding: str, cases: list[TypeCase], default: list[Stmt]
    ) -> None:
        var = self._expr(expr)
        bind_name = _to_camel(binding)
        self._line(f"let {bind_name}: Any = {var}")
        for i, case in enumerate(cases):
            type_name = self._type_name_for_check(case.typ)
            keyword = "if" if i == 0 else "} else if"
            self._line(f"{keyword} {bind_name} is {type_name} {{")
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
        self._line(f"switch {expr_str} {{")
        for case in cases:
            patterns = ", ".join(self._expr(p) for p in case.patterns)
            self._line(f"case {patterns}:")
            self.indent += 1
            for s in case.body:
                self._emit_stmt(s)
            self.indent -= 1
        if default:
            self._line("default:")
            self.indent += 1
            for s in default:
                self._emit_stmt(s)
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
            idx = _to_camel(index)
            val = _to_camel(value)
            self._line(f"for ({idx}, {val}) in {iter_expr}.enumerated() {{")
            self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        elif value is not None:
            val = _to_camel(value)
            self._line(f"for {val} in {iter_expr} {{")
            self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        elif index is not None:
            idx = _to_camel(index)
            self._line(f"for {idx} in 0..<{iter_expr}.count {{")
            self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        else:
            self._line(f"for _ in {iter_expr} {{")
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
        # Swift doesn't have C-style for loops, use while
        if init:
            self._emit_stmt(init)
        cond_str = self._expr(cond) if cond else "true"
        self._line(f"while {cond_str} {{")
        self.indent += 1
        for s in body:
            self._emit_stmt(s)
        if post:
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
        self._line("do {")
        self.indent += 1
        for s in body:
            self._emit_stmt(s)
        self.indent -= 1
        var = _to_camel(catch_var) if catch_var else "error"
        self._line(f"}} catch let {var} {{")
        self.indent += 1
        for s in catch_body:
            self._emit_stmt(s)
        if reraise:
            self._line(f"throw {var}")
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
                return "nil"
            case Var(name=name):
                if name == self.receiver_name:
                    return "self"
                if name.isupper():
                    return f"Constants.{_to_screaming_snake(name)}"
                return _to_camel(name)
            case FieldAccess(obj=obj, field=field):
                return f"{self._expr(obj)}.{_to_camel(field)}"
            case Index(obj=obj, index=index):
                obj_str = self._expr(obj)
                idx_str = self._expr(index)
                return f"{obj_str}[{idx_str}]"
            case SliceExpr(obj=obj, low=low, high=high):
                return self._slice_expr(obj, low, high)
            case Call(func=func, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                return f"{_to_camel(func)}({args_str})"
            case MethodCall(obj=obj, method=method, args=args, receiver_type=receiver_type):
                return self._method_call(obj, method, args, receiver_type)
            case StaticCall(on_type=on_type, method=method, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                type_name = self._type_name_for_check(on_type)
                return f"{type_name}.{_to_camel(method)}({args_str})"
            case BinaryOp(op=op, left=left, right=right):
                swift_op = _binary_op(op)
                left_str = self._expr(left)
                right_str = self._expr(right)
                return f"({left_str} {swift_op} {right_str})"
            case UnaryOp(op=op, operand=operand):
                return f"{op}{self._expr(operand)}"
            case Ternary(cond=cond, then_expr=then_expr, else_expr=else_expr):
                return f"({self._expr(cond)} ? {self._expr(then_expr)} : {self._expr(else_expr)})"
            case Cast(expr=inner, to_type=to_type):
                return self._cast(inner, to_type)
            case TypeAssert(expr=inner, asserted=asserted, safe=safe):
                type_name = self._type(asserted)
                return f"({self._expr(inner)} as! {type_name})"
            case IsType(expr=inner, tested_type=tested_type):
                type_name = self._type_name_for_check(tested_type)
                return f"({self._expr(inner)} is {type_name})"
            case IsNil(expr=inner, negated=negated):
                if negated:
                    return f"({self._expr(inner)} != nil)"
                return f"({self._expr(inner)} == nil)"
            case Len(expr=inner):
                inner_str = self._expr(inner)
                if isinstance(inner.typ, Primitive) and inner.typ.kind == "string":
                    return f"{inner_str}.count"
                return f"{inner_str}.count"
            case MakeSlice(element_type=element_type, length=length, capacity=capacity):
                typ = self._type(element_type)
                return f"[{typ}]()"
            case MakeMap(key_type=key_type, value_type=value_type):
                kt = self._type(key_type)
                vt = self._type(value_type)
                return f"[{kt}: {vt}]()"
            case SliceLit(elements=elements, element_type=element_type):
                if not elements:
                    typ = self._type(element_type)
                    return f"[{typ}]()"
                elems = ", ".join(self._expr(e) for e in elements)
                return f"[{elems}]"
            case MapLit(entries=entries, key_type=key_type, value_type=value_type):
                kt = self._type(key_type)
                vt = self._type(value_type)
                if not entries:
                    return f"[{kt}: {vt}]()"
                pairs = ", ".join(
                    f"{self._expr(k)}: {self._expr(v)}" for k, v in entries
                )
                return f"[{pairs}]"
            case SetLit(elements=elements, element_type=element_type):
                et = self._type(element_type)
                if not elements:
                    return f"Set<{et}>()"
                elems = ", ".join(self._expr(e) for e in elements)
                return f"Set([{elems}])"
            case StructLit(struct_name=struct_name, fields=fields):
                if not fields:
                    return f"{struct_name}()"
                args = ", ".join(f"{_to_camel(k)}: {self._expr(v)}" for k, v in fields.items())
                return f"{struct_name}({args})"
            case TupleLit(elements=elements):
                elems = ", ".join(self._expr(e) for e in elements)
                return f"({elems})"
            case StringConcat(parts=parts):
                return " + ".join(self._expr(p) for p in parts)
            case StringFormat(template=template, args=args):
                return self._format_string(template, args)
            case _:
                return f"nil /* TODO: {type(expr).__name__} */"

    def _method_call(self, obj: Expr, method: str, args: list[Expr], receiver_type: Type) -> str:
        args_str = ", ".join(self._expr(a) for a in args)
        obj_str = self._expr(obj)
        # Handle slice methods
        if isinstance(receiver_type, Slice):
            if method == "append" and args:
                return f"{obj_str}.append({args_str})"
            if method == "pop" and not args:
                return f"{obj_str}.removeLast()"
            if method == "copy":
                return f"Array({obj_str})"
        # String methods
        if isinstance(receiver_type, Primitive) and receiver_type.kind == "string":
            if method == "startswith":
                return f"{obj_str}.hasPrefix({args_str})"
            if method == "endswith":
                return f"{obj_str}.hasSuffix({args_str})"
            if method == "find":
                return f"({obj_str}.range(of: {args_str})?.lowerBound.utf16Offset(in: {obj_str}) ?? -1)"
            if method == "replace":
                return f"{obj_str}.replacingOccurrences(of: {args_str})"
            if method == "split":
                return f"{obj_str}.components(separatedBy: {args_str})"
            if method == "join":
                return f"{obj_str}.joined(separator: {args_str})"
            if method == "strip" or method == "trim":
                return f"{obj_str}.trimmingCharacters(in: .whitespaces)"
            if method == "lower":
                return f"{obj_str}.lowercased()"
            if method == "upper":
                return f"{obj_str}.uppercased()"
        if args_str:
            return f"{obj_str}.{_to_camel(method)}({args_str})"
        return f"{obj_str}.{_to_camel(method)}()"

    def _slice_expr(self, obj: Expr, low: Expr | None, high: Expr | None) -> str:
        obj_str = self._expr(obj)
        if isinstance(obj.typ, Primitive) and obj.typ.kind == "string":
            if low and high:
                low_str = self._expr(low)
                high_str = self._expr(high)
                return f"String({obj_str}[{obj_str}.index({obj_str}.startIndex, offsetBy: {low_str})..<{obj_str}.index({obj_str}.startIndex, offsetBy: {high_str})])"
            elif low:
                low_str = self._expr(low)
                return f"String({obj_str}[{obj_str}.index({obj_str}.startIndex, offsetBy: {low_str})...])"
            elif high:
                high_str = self._expr(high)
                return f"String({obj_str}[..<{obj_str}.index({obj_str}.startIndex, offsetBy: {high_str})])"
            return obj_str
        # Array slice
        if low and high:
            return f"Array({obj_str}[{self._expr(low)}..<{self._expr(high)}])"
        elif low:
            return f"Array({obj_str}[{self._expr(low)}...])"
        elif high:
            return f"Array({obj_str}[..<{self._expr(high)}])"
        return f"Array({obj_str})"

    def _cast(self, inner: Expr, to_type: Type) -> str:
        inner_str = self._expr(inner)
        swift_type = self._type(to_type)
        if isinstance(to_type, Primitive):
            if to_type.kind == "int":
                return f"Int({inner_str})"
            if to_type.kind == "float":
                return f"Double({inner_str})"
            if to_type.kind == "byte":
                return f"UInt8({inner_str})"
            if to_type.kind == "string":
                return f"String({inner_str})"
        return f"({inner_str} as! {swift_type})"

    def _format_string(self, template: str, args: list[Expr]) -> str:
        import re
        # Convert {0}, {1}, etc. to %@
        result = re.sub(r'\{\d+\}', '%@', template)
        result = result.replace("%v", "%@")
        escaped = result.replace("\\", "\\\\").replace('"', '\\"')
        args_str = ", ".join(self._expr(a) for a in args)
        if args_str:
            return f'String(format: "{escaped}", {args_str})'
        return f'"{escaped}"'

    def _lvalue(self, lv: LValue) -> str:
        match lv:
            case VarLV(name=name):
                if name == self.receiver_name:
                    return "self"
                return _to_camel(name)
            case FieldLV(obj=obj, field=field):
                return f"{self._expr(obj)}.{_to_camel(field)}"
            case IndexLV(obj=obj, index=index):
                obj_str = self._expr(obj)
                idx_str = self._expr(index)
                return f"{obj_str}[{idx_str}]"
            case DerefLV(ptr=ptr):
                return self._expr(ptr)
            case _:
                return f"nil /* lvalue: {type(lv).__name__} */"

    def _type(self, typ: Type) -> str:
        match typ:
            case Primitive(kind=kind):
                return _primitive_type(kind)
            case Slice(element=element):
                elem = self._type(element)
                return f"[{elem}]"
            case Array(element=element, size=size):
                return f"[{self._type(element)}]"
            case Map(key=key, value=value):
                kt = self._type(key)
                vt = self._type(value)
                return f"[{kt}: {vt}]"
            case Set(element=element):
                et = self._type(element)
                return f"Set<{et}>"
            case Tuple(elements=elements):
                parts = ", ".join(self._type(e) for e in elements)
                return f"({parts})"
            case Pointer(target=target):
                return self._type(target)
            case Optional(inner=inner):
                return f"{self._type(inner)}?"
            case StructRef(name=name):
                return name
            case Interface(name=name):
                if name == "any":
                    return "Any"
                return name
            case Union(name=name, variants=variants):
                if name:
                    return name
                return "Any"
            case FuncType(params=params, ret=ret):
                param_types = ", ".join(self._type(p) for p in params)
                ret_type = self._type(ret)
                return f"({param_types}) -> {ret_type}"
            case StringSlice():
                return "String"
            case _:
                return "Any"

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
                return '"\0"'
            case Slice():
                elem = self._type(typ.element)
                return f"[{elem}]()"
            case Optional():
                return "nil"
            case _:
                return "nil"


def _primitive_type(kind: str) -> str:
    match kind:
        case "string":
            return "String"
        case "int":
            return "Int"
        case "float":
            return "Double"
        case "bool":
            return "Bool"
        case "byte":
            return "UInt8"
        case "rune":
            return "Character"
        case "void":
            return "Void"
        case _:
            return "Any"


def _binary_op(op: str) -> str:
    match op:
        case "&&":
            return "&&"
        case "||":
            return "||"
        case _:
            return op


def _to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    if name.startswith("_"):
        name = name[1:]
    if "_" not in name:
        return name[0].lower() + name[1:] if name else name
    parts = name.split("_")
    return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])


def _to_screaming_snake(name: str) -> str:
    """Convert to SCREAMING_SNAKE_CASE."""
    return name.upper()


def _string_literal(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
        .replace("\r", "\\r")
    )
    return f'"{escaped}"'
