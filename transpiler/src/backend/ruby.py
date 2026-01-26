"""Ruby backend: IR → Ruby code."""

from __future__ import annotations

from src.backend.util import escape_string, to_pascal, to_snake
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


class RubyBackend:
    """Emit Ruby code from IR."""

    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self.receiver_name: str | None = None
        self.current_class: str = ""

    def emit(self, module: Module) -> str:
        """Emit Ruby code from IR Module."""
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
        module_name = to_pascal(module.name)
        self._line(f"module {module_name}")
        self.indent += 1
        if module.constants:
            for const in module.constants:
                self._emit_constant(const)
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
        # Remove trailing blank line
        if self.lines and self.lines[-1] == "":
            self.lines.pop()
        self.indent -= 1
        self._line("end")

    def _emit_constant(self, const: Constant) -> None:
        name = const.name.upper()
        val = self._expr(const.value)
        self._line(f"{name} = {val}")

    def _emit_interface(self, iface: InterfaceDef) -> None:
        self._line(f"module {iface.name}")
        self.indent += 1
        for method in iface.methods:
            params = ", ".join(to_snake(p.name) for p in method.params)
            name = to_snake(method.name)
            if params:
                self._line(f"def {name}({params})")
            else:
                self._line(f"def {name}")
            self.indent += 1
            self._line("raise NotImplementedError")
            self.indent -= 1
            self._line("end")
        self.indent -= 1
        self._line("end")

    def _emit_struct(self, struct: Struct) -> None:
        self.current_class = struct.name
        self._line(f"class {struct.name}")
        self.indent += 1
        if struct.fields:
            field_names = ", ".join(f":{to_snake(f.name)}" for f in struct.fields)
            self._line(f"attr_accessor {field_names}")
            self._line("")
            self._emit_constructor(struct)
        for i, method in enumerate(struct.methods):
            if i > 0 or struct.fields:
                self._line("")
            self._emit_method(method)
        self.indent -= 1
        self._line("end")
        self.current_class = ""

    def _emit_constructor(self, struct: Struct) -> None:
        params = ", ".join(to_snake(f.name) for f in struct.fields)
        self._line(f"def initialize({params})")
        self.indent += 1
        for f in struct.fields:
            name = to_snake(f.name)
            self._line(f"@{name} = {name}")
        self.indent -= 1
        self._line("end")

    def _emit_function(self, func: Function) -> None:
        params = ", ".join(to_snake(p.name) for p in func.params)
        name = to_snake(func.name)
        if params:
            self._line(f"def self.{name}({params})")
        else:
            self._line(f"def self.{name}")
        self.indent += 1
        if not func.body:
            self._line("raise NotImplementedError")
        self._emit_body(func.body)
        self.indent -= 1
        self._line("end")

    def _emit_method(self, func: Function) -> None:
        params = ", ".join(to_snake(p.name) for p in func.params)
        name = to_snake(func.name)
        if func.receiver:
            self.receiver_name = func.receiver.name
        if params:
            self._line(f"def {name}({params})")
        else:
            self._line(f"def {name}")
        self.indent += 1
        if not func.body:
            self._line("raise NotImplementedError")
        self._emit_body(func.body)
        self.indent -= 1
        self._line("end")
        self.receiver_name = None

    def _emit_body(self, body: list[Stmt]) -> None:
        """Emit function body with implicit return for last statement."""
        if not body:
            return
        for stmt in body[:-1]:
            self._emit_stmt(stmt)
        last = body[-1]
        if isinstance(last, Return) and last.value is not None:
            if isinstance(last.value, TupleLit):
                elements = ", ".join(self._expr(e) for e in last.value.elements)
                self._line(f"[{elements}]")
            else:
                self._line(self._expr(last.value))
        elif isinstance(last, Return) and last.value is None:
            pass  # Implicit nil return
        else:
            self._emit_stmt(last)

    def _emit_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDecl(name=name, typ=typ, value=value):
                var_name = to_snake(name)
                if value is not None:
                    val = self._expr(value)
                    self._line(f"{var_name} = {val}")
                else:
                    default = self._default_value(typ)
                    self._line(f"{var_name} = {default}")
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
                self._line(e)
            case Return(value=value):
                if value is not None:
                    if isinstance(value, TupleLit):
                        elements = ", ".join(self._expr(e) for e in value.elements)
                        self._line(f"return [{elements}]")
                    else:
                        self._line(f"return {self._expr(value)}")
                else:
                    self._line("return")
            case If(cond=cond, then_body=then_body, else_body=else_body, init=init):
                if init is not None:
                    self._emit_stmt(init)
                self._line(f"if {self._expr(cond)}")
                self.indent += 1
                for s in then_body:
                    self._emit_stmt(s)
                self.indent -= 1
                if else_body:
                    self._line("else")
                    self.indent += 1
                    for s in else_body:
                        self._emit_stmt(s)
                    self.indent -= 1
                self._line("end")
            case TypeSwitch(expr=expr, binding=binding, cases=cases, default=default):
                self._emit_type_switch(expr, binding, cases, default)
            case Match(expr=expr, cases=cases, default=default):
                self._emit_match(expr, cases, default)
            case ForRange(index=index, value=value, iterable=iterable, body=body):
                self._emit_for_range(index, value, iterable, body)
            case ForClassic(init=init, cond=cond, post=post, body=body):
                self._emit_for_classic(init, cond, post, body)
            case While(cond=cond, body=body):
                self._line(f"while {self._expr(cond)}")
                self.indent += 1
                for s in body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("end")
            case Break(label=label):
                self._line("break")
            case Continue(label=label):
                self._line("next")
            case Block(body=body):
                for s in body:
                    self._emit_stmt(s)
            case TryCatch(body=body, catch_var=catch_var, catch_body=catch_body, reraise=reraise):
                self._emit_try_catch(body, catch_var, catch_body, reraise)
            case Raise(error_type=error_type, message=message, pos=pos):
                msg = self._expr(message)
                self._line(f"raise {msg}")
            case SoftFail():
                self._line("return nil")
            case _:
                self._line(f"# TODO: {type(stmt).__name__}")

    def _emit_type_switch(
        self, expr: Expr, binding: str, cases: list[TypeCase], default: list[Stmt]
    ) -> None:
        var = self._expr(expr)
        bind_name = to_snake(binding)
        self._line(f"{bind_name} = {var}")
        self._line(f"case {bind_name}")
        for case in cases:
            type_name = self._type_name_for_check(case.typ)
            self._line(f"when {type_name}")
            self.indent += 1
            for s in case.body:
                self._emit_stmt(s)
            self.indent -= 1
        if default:
            self._line("else")
            self.indent += 1
            for s in default:
                self._emit_stmt(s)
            self.indent -= 1
        self._line("end")

    def _emit_match(self, expr: Expr, cases: list, default: list[Stmt]) -> None:
        expr_str = self._expr(expr)
        self._line(f"case {expr_str}")
        for case in cases:
            patterns = ", ".join(self._expr(p) for p in case.patterns)
            self._line(f"when {patterns}")
            self.indent += 1
            self._emit_case_body(case.body)
            self.indent -= 1
        if default:
            self._line("else")
            self.indent += 1
            self._emit_case_body(default)
            self.indent -= 1
        self._line("end")

    def _emit_case_body(self, body: list[Stmt]) -> None:
        """Emit case body with implicit return for last statement."""
        if not body:
            return
        for stmt in body[:-1]:
            self._emit_stmt(stmt)
        last = body[-1]
        if isinstance(last, Return) and last.value is not None:
            self._line(self._expr(last.value))
        elif isinstance(last, Return) and last.value is None:
            self._line("nil")
        else:
            self._emit_stmt(last)

    def _emit_for_range(
        self,
        index: str | None,
        value: str | None,
        iterable: Expr,
        body: list[Stmt],
    ) -> None:
        iter_expr = self._expr(iterable)
        if value is not None and index is not None:
            idx = to_snake(index)
            val = to_snake(value)
            self._line(f"{iter_expr}.each_with_index do |{val}, {idx}|")
            self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("end")
        elif value is not None:
            val = to_snake(value)
            self._line(f"{iter_expr}.each do |{val}|")
            self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("end")
        elif index is not None:
            idx = to_snake(index)
            self._line(f"(0...{iter_expr}.length).each do |{idx}|")
            self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("end")
        else:
            self._line(f"{iter_expr}.each do")
            self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("end")

    def _emit_for_classic(
        self,
        init: Stmt | None,
        cond: Expr | None,
        post: Stmt | None,
        body: list[Stmt],
    ) -> None:
        if init:
            self._emit_stmt(init)
        cond_str = self._expr(cond) if cond else "true"
        self._line(f"while {cond_str}")
        self.indent += 1
        for s in body:
            self._emit_stmt(s)
        if post:
            self._emit_stmt(post)
        self.indent -= 1
        self._line("end")

    def _emit_try_catch(
        self,
        body: list[Stmt],
        catch_var: str | None,
        catch_body: list[Stmt],
        reraise: bool,
    ) -> None:
        self._line("begin")
        self.indent += 1
        for s in body:
            self._emit_stmt(s)
        self.indent -= 1
        var = to_snake(catch_var) if catch_var else "e"
        self._line(f"rescue => {var}")
        self.indent += 1
        for s in catch_body:
            self._emit_stmt(s)
        if reraise:
            self._line("raise")
        self.indent -= 1
        self._line("end")

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
                    return name.upper()
                return to_snake(name)
            case FieldAccess(obj=obj, field=field):
                obj_str = self._expr(obj)
                if obj_str == "self":
                    return f"@{to_snake(field)}"
                return f"{obj_str}.{to_snake(field)}"
            case Index(obj=obj, index=index):
                obj_str = self._expr(obj)
                idx_str = self._expr(index)
                return f"{obj_str}[{idx_str}]"
            case SliceExpr(obj=obj, low=low, high=high):
                return self._slice_expr(obj, low, high)
            case Call(func=func, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                func_name = to_snake(func)
                return f"{func_name}({args_str})"
            case MethodCall(obj=obj, method=method, args=args, receiver_type=receiver_type):
                return self._method_call(obj, method, args, receiver_type)
            case StaticCall(on_type=on_type, method=method, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                type_name = self._type_name_for_check(on_type)
                if args_str:
                    return f"{type_name}.{to_snake(method)}({args_str})"
                return f"{type_name}.{to_snake(method)}"
            case BinaryOp(op=op, left=left, right=right):
                ruby_op = _binary_op(op)
                left_str = self._expr(left)
                right_str = self._expr(right)
                return f"{left_str} {ruby_op} {right_str}"
            case UnaryOp(op=op, operand=operand):
                return f"{op}{self._expr(operand)}"
            case Ternary(cond=cond, then_expr=then_expr, else_expr=else_expr):
                return f"{self._expr(cond)} ? {self._expr(then_expr)} : {self._expr(else_expr)}"
            case Cast(expr=inner, to_type=to_type):
                return self._cast(inner, to_type)
            case TypeAssert(expr=inner, asserted=asserted, safe=safe):
                return self._expr(inner)
            case IsType(expr=inner, tested_type=tested_type):
                type_name = self._type_name_for_check(tested_type)
                return f"{self._expr(inner)}.is_a?({type_name})"
            case IsNil(expr=inner, negated=negated):
                if negated:
                    return f"!{self._expr(inner)}.nil?"
                return f"{self._expr(inner)}.nil?"
            case Len(expr=inner):
                return f"{self._expr(inner)}.length"
            case MakeSlice(element_type=element_type, length=length, capacity=capacity):
                if length:
                    return f"Array.new({self._expr(length)})"
                return "[]"
            case MakeMap(key_type=key_type, value_type=value_type):
                return "{}"
            case SliceLit(elements=elements, element_type=element_type):
                if not elements:
                    return "[]"
                elems = ", ".join(self._expr(e) for e in elements)
                return f"[{elems}]"
            case MapLit(entries=entries, key_type=key_type, value_type=value_type):
                if not entries:
                    return "{}"
                pairs = ", ".join(
                    f"{self._expr(k)} => {self._expr(v)}" for k, v in entries
                )
                return f"{{{pairs}}}"
            case SetLit(elements=elements, element_type=element_type):
                if not elements:
                    return "Set.new"
                elems = ", ".join(self._expr(e) for e in elements)
                return f"Set.new([{elems}])"
            case StructLit(struct_name=struct_name, fields=fields):
                if not fields:
                    return f"{struct_name}.new"
                args = ", ".join(self._expr(v) for v in fields.values())
                return f"{struct_name}.new({args})"
            case TupleLit(elements=elements):
                elems = ", ".join(self._expr(e) for e in elements)
                return f"[{elems}]"
            case StringConcat(parts=parts):
                return " + ".join(self._expr(p) for p in parts)
            case StringFormat(template=template, args=args):
                return self._format_string(template, args)
            case _:
                return f"nil # TODO: {type(expr).__name__}"

    def _method_call(self, obj: Expr, method: str, args: list[Expr], receiver_type: Type) -> str:
        args_str = ", ".join(self._expr(a) for a in args)
        obj_str = self._expr(obj)
        if isinstance(receiver_type, Slice):
            if method == "append" and args:
                return f"{obj_str}.push({args_str})"
            if method == "pop" and not args:
                return f"{obj_str}.pop"
            if method == "copy":
                return f"{obj_str}.dup"
        if isinstance(receiver_type, Primitive) and receiver_type.kind == "string":
            if method == "startswith":
                return f"{obj_str}.start_with?({args_str})"
            if method == "endswith":
                return f"{obj_str}.end_with?({args_str})"
            if method == "find":
                return f"({obj_str}.index({args_str}) || -1)"
            if method == "replace":
                return f"{obj_str}.gsub({args_str})"
            if method == "split":
                return f"{obj_str}.split({args_str})"
            if method == "join":
                return f"{args_str}.join({obj_str})"
            if method == "strip" or method == "trim":
                return f"{obj_str}.strip"
            if method == "lower":
                return f"{obj_str}.downcase"
            if method == "upper":
                return f"{obj_str}.upcase"
        if args_str:
            return f"{obj_str}.{to_snake(method)}({args_str})"
        return f"{obj_str}.{to_snake(method)}"

    def _slice_expr(self, obj: Expr, low: Expr | None, high: Expr | None) -> str:
        obj_str = self._expr(obj)
        if low and high:
            return f"{obj_str}[{self._expr(low)}...{self._expr(high)}]"
        elif low:
            return f"{obj_str}[{self._expr(low)}..]"
        elif high:
            return f"{obj_str}[0...{self._expr(high)}]"
        return f"{obj_str}.dup"

    def _cast(self, inner: Expr, to_type: Type) -> str:
        inner_str = self._expr(inner)
        if isinstance(to_type, Primitive):
            if to_type.kind == "int":
                return f"{inner_str}.to_i"
            if to_type.kind == "float":
                return f"{inner_str}.to_f"
            if to_type.kind == "string":
                return f"{inner_str}.to_s"
        return inner_str

    def _format_string(self, template: str, args: list[Expr]) -> str:
        import re
        result = template
        for i, arg in enumerate(args):
            result = result.replace(f"{{{i}}}", f"#{{{self._expr(arg)}}}")
        result = result.replace("%v", "%s")
        result = re.sub(r'%s', lambda m: f"#{{{self._expr(args.pop(0)) if args else ''}}}", result)
        escaped = result.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    def _lvalue(self, lv: LValue) -> str:
        match lv:
            case VarLV(name=name):
                if name == self.receiver_name:
                    return "self"
                return to_snake(name)
            case FieldLV(obj=obj, field=field):
                obj_str = self._expr(obj)
                if obj_str == "self":
                    return f"@{to_snake(field)}"
                return f"{obj_str}.{to_snake(field)}"
            case IndexLV(obj=obj, index=index):
                return f"{self._expr(obj)}[{self._expr(index)}]"
            case DerefLV(ptr=ptr):
                return self._expr(ptr)
            case _:
                return f"nil # lvalue: {type(lv).__name__}"

    def _type_name_for_check(self, typ: Type) -> str:
        match typ:
            case StructRef(name=name):
                return name
            case Interface(name=name):
                return name
            case Pointer(target=target):
                return self._type_name_for_check(target)
            case Primitive(kind="int"):
                return "Integer"
            case Primitive(kind="float"):
                return "Float"
            case Primitive(kind="string"):
                return "String"
            case Primitive(kind="bool"):
                return "TrueClass"
            case _:
                return "Object"

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
            case Slice():
                return "[]"
            case Map():
                return "{}"
            case Optional():
                return "nil"
            case _:
                return "nil"


def _binary_op(op: str) -> str:
    match op:
        case "&&":
            return "&&"
        case "||":
            return "||"
        case _:
            return op


def _string_literal(value: str) -> str:
    return f'"{escape_string(value)}"'
