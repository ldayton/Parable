"""Python backend: IR → Python code."""

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
    SliceConvert,
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
    TupleAssign,
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


# Python builtins that shouldn't be shadowed by variable names
_PYTHON_BUILTINS = frozenset({
    "abs", "all", "any", "ascii", "bin", "bool", "breakpoint", "bytearray",
    "bytes", "callable", "chr", "classmethod", "compile", "complex", "delattr",
    "dict", "dir", "divmod", "enumerate", "eval", "exec", "filter", "float",
    "format", "frozenset", "getattr", "globals", "hasattr", "hash", "help",
    "hex", "id", "input", "int", "isinstance", "issubclass", "iter", "len",
    "list", "locals", "map", "max", "memoryview", "min", "next", "object",
    "oct", "open", "ord", "pow", "print", "property", "range", "repr",
    "reversed", "round", "set", "setattr", "slice", "sorted", "staticmethod",
    "str", "sum", "super", "tuple", "type", "vars", "zip",
})


def _safe_name(name: str) -> str:
    """Rename variables that shadow Python builtins."""
    if name in _PYTHON_BUILTINS:
        return name + "_"
    return name


class PythonBackend:
    """Emit Python code from IR."""

    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self.receiver_name: str | None = None

    def emit(self, module: Module) -> str:
        """Emit Python code from IR Module."""
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
        self._line('"""Generated Python code."""')
        self._line()
        self._line("from __future__ import annotations")
        self._line()
        self._line("from dataclasses import dataclass, field")
        self._line("from typing import Protocol")
        self._line()
        self._line()
        self._line("def _intPtr(val: int) -> int | None:")
        self._line("    return None if val == -1 else val")
        self._line()
        self._line()
        self._line("def _parseInt(s: str, base: int) -> int:")
        self._line("    return int(s, base)")
        self._line()
        self._line()
        self._line("def _intToStr(n: int) -> str:")
        self._line("    return str(n)")
        need_blank = True
        if module.constants:
            self._line()
            for const in module.constants:
                self._emit_constant(const)
        for iface in module.interfaces:
            if need_blank:
                self._line()
                self._line()
            self._emit_interface(iface)
            need_blank = True
        for struct in module.structs:
            if need_blank:
                self._line()
                self._line()
            self._emit_struct(struct)
            need_blank = True
        for func in module.functions:
            if need_blank:
                self._line()
                self._line()
            self._emit_function(func)
            need_blank = True

    def _emit_constant(self, const: Constant) -> None:
        typ = self._type(const.typ)
        val = self._expr(const.value)
        self._line(f"{const.name}: {typ} = {val}")

    def _emit_interface(self, iface: InterfaceDef) -> None:
        self._line(f"class {iface.name}(Protocol):")
        self.indent += 1
        if not iface.methods:
            self._line("pass")
        for method in iface.methods:
            params = self._params(method.params, with_self=True)
            ret = self._type(method.ret)
            self._line(f"def {method.name}({params}) -> {ret}: ...")
        self.indent -= 1

    def _emit_struct(self, struct: Struct) -> None:
        base_list = list(struct.implements) if struct.implements else []
        if struct.is_exception:
            exc_base = struct.embedded_type if struct.embedded_type else "Exception"
            base_list.insert(0, exc_base)
        else:
            self._line("@dataclass")
        bases = ", ".join(base_list)
        if bases:
            self._line(f"class {struct.name}({bases}):")
        else:
            self._line(f"class {struct.name}:")
        self.indent += 1
        if struct.doc:
            self._line(f'"""{struct.doc}"""')
        if not struct.fields and not struct.methods:
            self._line("pass")
        for fld in struct.fields:
            self._emit_field(fld)
        for i, method in enumerate(struct.methods):
            if i > 0 or struct.fields:
                self._line()
            self._emit_method(method)
        self.indent -= 1

    def _emit_field(self, fld: Field) -> None:
        typ = self._type(fld.typ)
        if fld.default is not None:
            default = self._expr(fld.default)
        else:
            default = self._field_default(fld.typ)
        self._line(f"{fld.name}: {typ} = {default}")

    def _emit_function(self, func: Function) -> None:
        if func.doc:
            pass  # We'll put docstring inside
        params = self._params(func.params, with_self=False)
        ret = self._type(func.ret)
        self._line(f"def {func.name}({params}) -> {ret}:")
        self.indent += 1
        if func.doc:
            self._line(f'"""{func.doc}"""')
        if not func.body:
            self._line("pass")
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1

    def _emit_method(self, func: Function) -> None:
        params = self._params(func.params, with_self=True)
        ret = self._type(func.ret)
        self._line(f"def {func.name}({params}) -> {ret}:")
        self.indent += 1
        if func.doc:
            self._line(f'"""{func.doc}"""')
        if func.receiver:
            self.receiver_name = func.receiver.name
        if not func.body:
            self._line("pass")
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.receiver_name = None
        self.indent -= 1

    def _params(self, params: list, with_self: bool) -> str:
        parts = []
        if with_self:
            parts.append("self")
        for p in params:
            typ = self._type(p.typ)
            parts.append(f"{_safe_name(p.name)}: {typ}")
        return ", ".join(parts)

    def _emit_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDecl(name=name, typ=typ, value=value):
                py_type = self._type(typ)
                safe = _safe_name(name)
                if value is not None:
                    val = self._expr(value)
                    self._line(f"{safe}: {py_type} = {val}")
                else:
                    self._line(f"{safe}: {py_type}")
            case Assign(target=target, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                self._line(f"{lv} = {val}")
            case TupleAssign(targets=targets, value=value):
                lvalues = ", ".join(self._lvalue(t) for t in targets)
                val = self._expr(value)
                self._line(f"{lvalues} = {val}")
            case OpAssign(target=target, op=op, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                self._line(f"{lv} {op}= {val}")
            case ExprStmt(expr=Var(name="_skip_docstring")):
                pass  # Skip docstring markers
            case ExprStmt(expr=Var(name="_pass")):
                self._line("pass")
            case ExprStmt(expr=expr):
                self._line(self._expr(expr))
            case Return(value=value):
                if value is not None:
                    self._line(f"return {self._expr(value)}")
                else:
                    self._line("return")
            case If(cond=cond, then_body=then_body, else_body=else_body, init=init):
                if init is not None:
                    self._emit_stmt(init)
                self._line(f"if {self._expr(cond)}:")
                self.indent += 1
                if not then_body:
                    self._line("pass")
                for s in then_body:
                    self._emit_stmt(s)
                self.indent -= 1
                if else_body:
                    self._line("else:")
                    self.indent += 1
                    for s in else_body:
                        self._emit_stmt(s)
                    self.indent -= 1
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
                self._line(f"while {self._expr(cond)}:")
                self.indent += 1
                if not body:
                    self._line("pass")
                for s in body:
                    self._emit_stmt(s)
                self.indent -= 1
            case Break(label=_):
                self._line("break")
            case Continue(label=_):
                self._line("continue")
            case Block(body=body):
                for s in body:
                    self._emit_stmt(s)
            case TryCatch(
                body=body, catch_var=catch_var, catch_body=catch_body, reraise=reraise
            ):
                self._emit_try_catch(body, catch_var, catch_body, reraise)
            case Raise(error_type=error_type, message=message, pos=pos, reraise_var=reraise_var):
                if reraise_var:
                    self._line(f"raise {reraise_var}")
                else:
                    msg = self._expr(message)
                    p = self._expr(pos)
                    self._line(f"raise {error_type}({msg}, {p})")
            case SoftFail():
                self._line("return None")
            case _:
                raise NotImplementedError(f"Unknown statement: {type(stmt).__name__}")

    def _emit_type_switch(
        self, expr: Expr, binding: str, cases: list[TypeCase], default: list[Stmt]
    ) -> None:
        var = self._expr(expr)
        for i, case in enumerate(cases):
            type_name = self._type_name_for_check(case.typ)
            keyword = "if" if i == 0 else "elif"
            self._line(f"{keyword} isinstance({var}, {type_name}):")
            self.indent += 1
            self._line(f"{binding} = {var}")
            if not case.body:
                self._line("pass")
            for s in case.body:
                self._emit_stmt(s)
            self.indent -= 1
        if default:
            self._line("else:")
            self.indent += 1
            for s in default:
                self._emit_stmt(s)
            self.indent -= 1

    def _emit_match(self, expr: Expr, cases: list, default: list[Stmt]) -> None:
        self._line(f"match {self._expr(expr)}:")
        self.indent += 1
        for case in cases:
            patterns = " | ".join(self._expr(p) for p in case.patterns)
            self._line(f"case {patterns}:")
            self.indent += 1
            if not case.body:
                self._line("pass")
            for s in case.body:
                self._emit_stmt(s)
            self.indent -= 1
        if default:
            self._line("case _:")
            self.indent += 1
            for s in default:
                self._emit_stmt(s)
            self.indent -= 1
        self.indent -= 1

    def _emit_for_range(
        self,
        index: str | None,
        value: str | None,
        iterable: Expr,
        body: list[Stmt],
    ) -> None:
        iter_expr = self._expr(iterable)
        # Wrap with (... or []) if iterable might be None (Optional type or field access)
        if isinstance(iterable.typ, Optional) or isinstance(iterable, FieldAccess):
            iter_expr = f"({iter_expr} or [])"
        idx = _safe_name(index) if index else None
        val = _safe_name(value) if value else None
        if idx is not None and val is not None:
            self._line(f"for {idx}, {val} in enumerate({iter_expr}):")
        elif val is not None:
            self._line(f"for {val} in {iter_expr}:")
        elif idx is not None:
            self._line(f"for {idx} in range(len({iter_expr})):")
        else:
            self._line(f"for _ in {iter_expr}:")
        self.indent += 1
        if not body:
            self._line("pass")
        for s in body:
            self._emit_stmt(s)
        self.indent -= 1

    def _emit_for_classic(
        self,
        init: Stmt | None,
        cond: Expr | None,
        post: Stmt | None,
        body: list[Stmt],
    ) -> None:
        # Check for simple iteration pattern: for i := 0; i < len(x); i++
        if (range_info := _extract_range_pattern(init, cond, post)) is not None:
            var_name, iterable_expr = range_info
            self._line(f"for {_safe_name(var_name)} in range(len({self._expr(iterable_expr)})):")
            self.indent += 1
            if not body:
                self._line("pass")
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            return
        # Fallback: emit as while loop
        if init is not None:
            self._emit_stmt(init)
        cond_str = self._expr(cond) if cond else "True"
        self._line(f"while {cond_str}:")
        self.indent += 1
        if not body and post is None:
            self._line("pass")
        for s in body:
            self._emit_stmt(s)
        if post is not None:
            self._emit_stmt(post)
        self.indent -= 1

    def _emit_try_catch(
        self,
        body: list[Stmt],
        catch_var: str | None,
        catch_body: list[Stmt],
        reraise: bool,
    ) -> None:
        self._line("try:")
        self.indent += 1
        if not body:
            self._line("pass")
        for s in body:
            self._emit_stmt(s)
        self.indent -= 1
        var = _safe_name(catch_var) if catch_var else "_e"
        self._line(f"except Exception as {var}:")
        self.indent += 1
        if not catch_body and not reraise:
            self._line("pass")
        for s in catch_body:
            self._emit_stmt(s)
        if reraise:
            self._line("raise")
        self.indent -= 1

    def _expr(self, expr: Expr) -> str:
        match expr:
            case IntLit(value=value):
                return str(value)
            case FloatLit(value=value):
                return str(value)
            case StringLit(value=value):
                return _string_literal(value)
            case BoolLit(value=value):
                return "True" if value else "False"
            case NilLit():
                return "None"
            case Var(name=name):
                if name == self.receiver_name:
                    return "self"
                return _safe_name(name)
            case FieldAccess(obj=obj, field=field):
                # Convert tuple field access (F0, F1, etc.) to index access
                if field.startswith("F") and field[1:].isdigit():
                    return f"{self._expr(obj)}[{field[1:]}]"
                return f"{self._expr(obj)}.{field}"
            case Index(obj=obj, index=index):
                return f"{self._expr(obj)}[{self._expr(index)}]"
            case SliceExpr(obj=obj, low=low, high=high):
                return self._slice_expr(obj, low, high)
            case Call(func=func, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                return f"{func}({args_str})"
            case MethodCall(obj=obj, method=method, args=args, receiver_type=receiver_type):
                args_str = ", ".join(self._expr(a) for a in args)
                py_method = _method_name(method, receiver_type)
                obj_str = self._expr(obj)
                # Wrap receiver in parens for compound expressions (BinaryOp, UnaryOp, etc.)
                if isinstance(obj, (BinaryOp, UnaryOp, Ternary)):
                    obj_str = f"({obj_str})"
                return f"{obj_str}.{py_method}({args_str})"
            case StaticCall(on_type=on_type, method=method, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                type_name = self._type_name_for_check(on_type)
                return f"{type_name}.{method}({args_str})"
            case BinaryOp(op=">", left=Len(expr=inner), right=IntLit(value=0)):
                # Convert len(x) > 0 back to truthy check for Python
                return self._expr(inner)
            case BinaryOp(op="==", left=Len(expr=inner), right=IntLit(value=0)):
                # Convert len(x) == 0 back to "not x" for Python
                return f"not {self._expr(inner)}"
            case BinaryOp(op=op, left=left, right=right):
                py_op = _binary_op(op)
                left_str = self._maybe_paren(left, op, is_left=True)
                right_str = self._maybe_paren(right, op, is_left=False)
                return f"{left_str} {py_op} {right_str}"
            case UnaryOp(op=op, operand=operand):
                py_op = _unary_op(op)
                # For 'not', wrap compound expressions in parens for correct precedence
                if op == "!" and isinstance(operand, BinaryOp):
                    return f"{py_op}({self._expr(operand)})"
                return f"{py_op}{self._expr(operand)}"
            case Ternary(cond=cond, then_expr=then_expr, else_expr=else_expr):
                return f"{self._expr(then_expr)} if {self._cond_expr(cond)} else {self._expr(else_expr)}"
            case Cast(expr=inner, to_type=to_type):
                # Cast from list[int] (bytearray) to string needs bytes().decode()
                if to_type == Primitive(kind="string") and isinstance(inner.typ, Slice):
                    return f'bytes({self._expr(inner)}).decode("utf-8", errors="replace")'
                # Cast from rune to string is chr() in Python
                if to_type == Primitive(kind="string") and inner.typ == Primitive(kind="rune"):
                    return f"chr({self._expr(inner)})"
                # Cast from string to []byte is .encode() in Python
                if isinstance(to_type, Slice) and to_type.element == Primitive(kind="byte"):
                    return f'{self._expr(inner)}.encode("utf-8")'
                # Cast from string/char/byte to int is ord() in Python
                if to_type == Primitive(kind="int") and inner.typ in (Primitive(kind="string"), Primitive(kind="byte"), Primitive(kind="rune")):
                    return f"ord({self._expr(inner)})"
                # Most casts in Python are no-ops
                return self._expr(inner)
            case TypeAssert(expr=inner):
                # Python doesn't have type assertions at runtime
                return self._expr(inner)
            case IsType(expr=inner, tested_type=tested_type):
                type_name = self._type_name_for_check(tested_type)
                return f"isinstance({self._expr(inner)}, {type_name})"
            case IsNil(expr=inner, negated=negated):
                op = "is not" if negated else "is"
                return f"{self._expr(inner)} {op} None"
            case Len(expr=inner):
                return f"len({self._expr(inner)})"
            case MakeSlice(element_type=element_type, length=length):
                if length is not None:
                    zero = self._zero_value(element_type)
                    return f"[{zero}] * {self._expr(length)}"
                return "[]"
            case MakeMap():
                return "{}"
            case SliceLit(elements=elements):
                elems = ", ".join(self._expr(e) for e in elements)
                return f"[{elems}]"
            case MapLit(entries=entries):
                if not entries:
                    return "{}"
                pairs = ", ".join(
                    f"{self._expr(k)}: {self._expr(v)}" for k, v in entries
                )
                return f"{{{pairs}}}"
            case SetLit(elements=elements):
                if not elements:
                    return "set()"
                elems = ", ".join(self._expr(e) for e in elements)
                return f"{{{elems}}}"
            case StructLit(struct_name=struct_name, fields=fields):
                # Skip None fields to use dataclass defaults
                non_none = [(k, v) for k, v in fields.items() if not isinstance(v, NilLit)]
                args = ", ".join(f"{k}={self._expr(v)}" for k, v in non_none)
                return f"{struct_name}({args})"
            case TupleLit(elements=elements):
                elems = ", ".join(self._expr(e) for e in elements)
                if len(elements) == 1:
                    return f"({elems},)"
                return f"({elems})"
            case StringConcat(parts=parts):
                return " + ".join(self._expr(p) for p in parts)
            case StringFormat(template=template, args=args):
                return self._format_string(template, args)
            case SliceConvert(source=source):
                return self._expr(source)
            case _:
                raise NotImplementedError(f"Unknown expression: {type(expr).__name__}")

    def _slice_expr(self, obj: Expr, low: Expr | None, high: Expr | None) -> str:
        obj_str = self._expr(obj)
        low_str = self._expr(low) if low else ""
        high_str = self._expr(high) if high else ""
        return f"{obj_str}[{low_str}:{high_str}]"

    def _format_string(self, template: str, args: list[Expr]) -> str:
        import re
        # First escape literal braces that aren't placeholders
        # Replace {N} with a marker, escape all other braces, then restore
        markers = {}
        result = template
        for i in range(len(args)):
            marker = f"\x00PLACEHOLDER{i}\x00"
            markers[marker] = i
            result = result.replace(f"{{{i}}}", marker, 1)
        # Also mark %v placeholders
        pv_markers = []
        while "%v" in result:
            marker = f"\x00PV{len(pv_markers)}\x00"
            pv_markers.append(marker)
            result = result.replace("%v", marker, 1)
        # Escape literal braces for f-string
        result = result.replace("{", "{{").replace("}", "}}")
        # Restore placeholders as f-string interpolations
        for marker, i in markers.items():
            if i < len(args):
                result = result.replace(marker, f"{{{self._expr(args[i])}}}")
        for j, marker in enumerate(pv_markers):
            if j < len(args):
                result = result.replace(marker, f"{{{self._expr(args[j])}}}")
        # Use triple quotes for multi-line strings, escape quotes otherwise
        if "\n" in result:
            return f'f"""{result}"""'
        result = result.replace('"', '\\"')
        return f'f"{result}"'

    def _lvalue(self, lv: LValue) -> str:
        match lv:
            case VarLV(name=name):
                if name == self.receiver_name:
                    return "self"
                return _safe_name(name)
            case FieldLV(obj=obj, field=field):
                return f"{self._expr(obj)}.{field}"
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
                return f"list[{self._type(element)}]"
            case Array(element=element, size=size):
                # Python doesn't distinguish arrays; use list
                return f"list[{self._type(element)}]"
            case Map(key=key, value=value):
                return f"dict[{self._type(key)}, {self._type(value)}]"
            case Set(element=element):
                return f"set[{self._type(element)}]"
            case Tuple(elements=elements):
                parts = ", ".join(self._type(e) for e in elements)
                return f"tuple[{parts}]"
            case Pointer(target=target):
                return self._type(target)
            case Optional(inner=inner):
                return f"{self._type(inner)} | None"
            case StructRef(name=name):
                return name
            case Interface(name=name):
                return name
            case Union(name=name, variants=variants):
                if name:
                    return name
                parts = " | ".join(self._type(v) for v in variants)
                return parts
            case FuncType(params=params, ret=ret):
                # Use Callable from typing
                params_str = ", ".join(self._type(p) for p in params)
                return f"Callable[[{params_str}], {self._type(ret)}]"
            case StringSlice():
                return "str"
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

    def _zero_value(self, typ: Type) -> str:
        match typ:
            case Primitive(kind="int") | Primitive(kind="byte"):
                return "0"
            case Primitive(kind="float"):
                return "0.0"
            case Primitive(kind="bool"):
                return "False"
            case Primitive(kind="string"):
                return '""'
            case _:
                return "None"

    def _field_default(self, typ: Type) -> str:
        """Generate default value for dataclass field."""
        match typ:
            case Slice() | Array():
                return "field(default_factory=list)"
            case Map():
                return "field(default_factory=dict)"
            case Set():
                return "field(default_factory=set)"
            case _:
                return self._zero_value(typ)

    def _cond_expr(self, expr: Expr) -> str:
        """Emit a condition expression, wrapping in parens only if needed for ternary."""
        match expr:
            case BinaryOp(op=op) if op in ("and", "or", "&&", "||"):
                return f"({self._expr(expr)})"
            case _:
                return self._expr(expr)

    def _maybe_paren(self, expr: Expr, parent_op: str, is_left: bool) -> str:
        """Wrap expression in parens if needed for operator precedence."""
        match expr:
            case BinaryOp(op=child_op):
                if _needs_parens(child_op, parent_op, is_left):
                    return f"({self._expr(expr)})"
            case Ternary():
                return f"({self._expr(expr)})"
        return self._expr(expr)


def _primitive_type(kind: str) -> str:
    match kind:
        case "string":
            return "str"
        case "int":
            return "int"
        case "float":
            return "float"
        case "bool":
            return "bool"
        case "byte":
            return "int"
        case "rune":
            return "str"
        case "void":
            return "None"
        case _:
            raise NotImplementedError(f"Unknown primitive: {kind}")


def _method_name(method: str, receiver_type: Type) -> str:
    """Convert method name based on receiver type."""
    if isinstance(receiver_type, Slice) and method == "append":
        return "append"
    return method


def _binary_op(op: str) -> str:
    match op:
        case "&&":
            return "and"
        case "||":
            return "or"
        case _:
            return op


def _unary_op(op: str) -> str:
    match op:
        case "!":
            return "not "
        case "&" | "*":
            return ""  # Python has no address-of/deref; objects are references
        case _:
            return op


# Precedence levels (higher = binds tighter)
_PRECEDENCE = {
    "or": 1, "||": 1,
    "and": 2, "&&": 2,
    "==": 3, "!=": 3, "<": 3, ">": 3, "<=": 3, ">=": 3,
    "+": 4, "-": 4,
    "*": 5, "/": 5, "%": 5,
}


def _needs_parens(child_op: str, parent_op: str, is_left: bool) -> bool:
    """Determine if a child binary op needs parens inside a parent binary op."""
    child_prec = _PRECEDENCE.get(child_op, 0)
    parent_prec = _PRECEDENCE.get(parent_op, 0)
    if child_prec < parent_prec:
        return True
    if child_prec == parent_prec and not is_left:
        # Same precedence on right side needs parens for non-associative ops
        return child_op in ("==", "!=", "<", ">", "<=", ">=")
    return False


def _string_literal(value: str) -> str:
    return f'"{escape_string(value)}"'


def _extract_range_pattern(
    init: Stmt | None, cond: Expr | None, post: Stmt | None
) -> tuple[str, Expr] | None:
    """Extract simple range iteration pattern: for i := 0; i < len(x); i++.

    Returns (var_name, iterable_expr) if pattern matches, None otherwise.
    """
    if init is None or cond is None or post is None:
        return None
    # Check init: i := 0
    if not isinstance(init, VarDecl):
        return None
    if not isinstance(init.value, IntLit) or init.value.value != 0:
        return None
    var_name = init.name
    # Check cond: i < len(x)
    if not isinstance(cond, BinaryOp) or cond.op != "<":
        return None
    if not isinstance(cond.left, Var) or cond.left.name != var_name:
        return None
    if not isinstance(cond.right, Len):
        return None
    iterable_expr = cond.right.expr
    # Check post: i = i + 1 or i += 1
    if isinstance(post, OpAssign):
        if post.op != "+" or not isinstance(post.target, VarLV):
            return None
        if post.target.name != var_name:
            return None
        if not isinstance(post.value, IntLit) or post.value.value != 1:
            return None
    elif isinstance(post, Assign):
        if not isinstance(post.target, VarLV) or post.target.name != var_name:
            return None
        if not isinstance(post.value, BinaryOp) or post.value.op != "+":
            return None
        if not isinstance(post.value.left, Var) or post.value.left.name != var_name:
            return None
        if not isinstance(post.value.right, IntLit) or post.value.right.value != 1:
            return None
    else:
        return None
    return (var_name, iterable_expr)
