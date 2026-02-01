"""JavaScript backend: IR → JavaScript code.

Simpler than TypeScript - no type annotations, interfaces, or casts.
"""

from __future__ import annotations

from src.backend.util import escape_string
from src.ir import (
    INT,
    STRING,
    Array,
    Assign,
    BinaryOp,
    Block,
    BoolLit,
    Break,
    Call,
    Cast,
    CharClassify,
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
    FuncRef,
    FuncType,
    Function,
    If,
    Index,
    IndexLV,
    IntLit,
    IntToStr,
    InterfaceDef,
    InterfaceRef,
    IsNil,
    IsType,
    Len,
    LValue,
    MakeMap,
    MakeSlice,
    Map,
    MapLit,
    Match,
    MatchCase,
    MethodCall,
    Module,
    NilLit,
    NoOp,
    OpAssign,
    Optional,
    Param,
    ParseInt,
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
    TupleAssign,
    TupleLit,
    Ternary,
    TryCatch,
    TrimChars,
    Truthy,
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


class JsBackend:
    """Emit JavaScript code from IR."""

    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self.receiver_name: str | None = None
        self.current_struct: str | None = None
        self.struct_fields: dict[str, list[str]] = {}  # struct name -> [field_names]
        self._hoisted_vars: set[str] = set()  # vars hoisted in current scope

    def emit(self, module: Module) -> str:
        """Emit JavaScript code from IR Module."""
        self.indent = 0
        self.lines = []
        self.struct_fields = {}
        self._hoisted_vars = set()
        for struct in module.structs:
            self.struct_fields[struct.name] = [f.name for f in struct.fields]
        self._emit_module(module)
        return "\n".join(self.lines)

    def _line(self, text: str = "") -> None:
        if text:
            self.lines.append("  " * self.indent + text)
        else:
            self.lines.append("")

    def _emit_preamble(self) -> None:
        """Emit helper functions needed by generated code."""
        self._line("function range(start, end, step) {")
        self.indent += 1
        self._line("if (end === undefined) { end = start; start = 0; }")
        self._line("if (step === undefined) { step = 1; }")
        self._line("const result = [];")
        self._line("if (step > 0) {")
        self.indent += 1
        self._line("for (var i = start; i < end; i += step) result.push(i);")
        self.indent -= 1
        self._line("} else {")
        self.indent += 1
        self._line("for (var i = start; i > end; i += step) result.push(i);")
        self.indent -= 1
        self._line("}")
        self._line("return result;")
        self.indent -= 1
        self._line("}")

    def _emit_module(self, module: Module) -> None:
        if module.doc:
            self._line(f"/** {module.doc} */")
        self._emit_preamble()
        need_blank = True
        if module.constants:
            for const in module.constants:
                self._emit_constant(const)
            need_blank = True
        # Skip interfaces - JavaScript has no interface construct
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
        # Emit CommonJS exports for test runner
        self._line()
        self._line("// CommonJS exports")
        self._line("if (typeof module !== 'undefined') {")
        self.indent += 1
        self._line("module.exports = { parse, ParseError };")
        self.indent -= 1
        self._line("}")

    def _emit_constant(self, const: Constant) -> None:
        val = self._expr(const.value)
        self._line(f"const {const.name} = {val};")

    def _emit_struct(self, struct: Struct) -> None:
        if struct.doc:
            self._line(f"/** {struct.doc} */")
        extends = ""
        if struct.embedded_type:
            extends = f" extends {struct.embedded_type}"
        self._line(f"class {_safe_name(struct.name)}{extends} {{")
        self.indent += 1
        # No field declarations in JavaScript - just constructor
        if struct.fields:
            self._emit_constructor(struct)
        self.current_struct = struct.name
        for i, method in enumerate(struct.methods):
            if i > 0 or struct.fields:
                self._line()
            self._emit_method(method)
        self.current_struct = None
        self.indent -= 1
        self._line("}")

    def _emit_constructor(self, struct: Struct) -> None:
        params = ", ".join(
            f"{_camel(f.name)} = {self._default_value(f.typ)}"
            for f in struct.fields
        )
        self._line(f"constructor({params}) {{")
        self.indent += 1
        for fld in struct.fields:
            name = _camel(fld.name)
            # For array/slice fields, convert null to empty array
            is_nullable_slice = isinstance(fld.typ, Optional) and isinstance(
                fld.typ.inner, (Slice, Array)
            )
            if isinstance(fld.typ, (Slice, Array)) and not is_nullable_slice:
                self._line(f"this.{name} = {name} ?? [];")
            else:
                self._line(f"this.{name} = {name};")
        self.indent -= 1
        self._line("}")

    def _default_value(self, typ: Type) -> str:
        """Return default value for a type."""
        if isinstance(typ, Primitive):
            if typ.kind == "string":
                return '""'
            if typ.kind in ("int", "float", "byte", "rune"):
                return "0"
            if typ.kind == "bool":
                return "false"
        if isinstance(typ, Optional):
            return "null"
        if isinstance(typ, (Slice, Array)):
            return "[]"
        if isinstance(typ, Map):
            return "new Map()"
        if isinstance(typ, Set):
            return "new Set()"
        return "null"

    def _emit_function(self, func: Function) -> None:
        self._hoisted_vars = set()
        if func.doc:
            self._line(f"/** {func.doc} */")
        params = self._params(func.params)
        self._line(f"function {_camel(func.name)}({params}) {{")
        self.indent += 1
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")

    def _emit_method(self, func: Function) -> None:
        self._hoisted_vars = set()
        if func.doc:
            self._line(f"/** {func.doc} */")
        params = self._params(func.params)
        self._line(f"{_camel(func.name)}({params}) {{")
        self.indent += 1
        if func.receiver:
            self.receiver_name = func.receiver.name
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.receiver_name = None
        self.indent -= 1
        self._line("}")

    def _params(self, params: list[Param]) -> str:
        return ", ".join(_camel(p.name) for p in params)

    def _emit_hoisted_vars(self, hoisted_vars: list[tuple[str, Type]]) -> None:
        """Emit var declarations for hoisted variables before control structures."""
        for name, _ in hoisted_vars:
            js_name = _camel(name)
            if name not in self._hoisted_vars:
                self._line(f"var {js_name};")
                self._hoisted_vars.add(name)

    def _emit_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDecl(name=name, typ=typ, value=value):
                if value is not None:
                    val = self._expr(value)
                    self._line(f"let {_camel(name)} = {val};")
                else:
                    self._line(f"let {_camel(name)};")
            case Assign(target=target, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                # Check if variable was hoisted (already declared)
                var_name = target.name if isinstance(target, VarLV) else None
                is_hoisted = var_name is not None and var_name in self._hoisted_vars
                if stmt.is_declaration and not is_hoisted:
                    self._line(f"let {lv} = {val};")
                else:
                    self._line(f"{lv} = {val};")
            case TupleAssign(targets=targets, value=value):
                lvalues = ", ".join(self._lvalue(t) for t in targets)
                val = self._expr(value)
                # Check if all targets are hoisted
                all_hoisted = all(
                    isinstance(t, VarLV) and t.name in self._hoisted_vars
                    for t in targets
                )
                if stmt.is_declaration and not all_hoisted:
                    self._line(f"let [{lvalues}] = {val};")
                else:
                    new_targets = stmt.new_targets
                    for name in new_targets:
                        if name not in self._hoisted_vars:
                            self._line(f"let {_camel(name)};")
                    self._line(f"[{lvalues}] = {val};")
            case OpAssign(target=target, op=op, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                self._line(f"{lv} {op}= {val};")
            case NoOp():
                pass
            case ExprStmt(expr=expr):
                self._line(f"{self._expr(expr)};")
            case Return(value=value):
                if value is not None:
                    self._line(f"return {self._expr(value)};")
                else:
                    self._line("return;")
            case If(cond=cond, then_body=then_body, else_body=else_body, init=init):
                self._emit_hoisted_vars(stmt.hoisted_vars)
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
                self._emit_hoisted_vars(stmt.hoisted_vars)
                self._emit_type_switch(expr, binding, cases, default)
            case Match(expr=expr, cases=cases, default=default):
                self._emit_hoisted_vars(stmt.hoisted_vars)
                self._emit_match(expr, cases, default)
            case ForRange(index=index, value=value, iterable=iterable, body=body):
                self._emit_hoisted_vars(stmt.hoisted_vars)
                self._emit_for_range(index, value, iterable, body)
            case ForClassic(init=init, cond=cond, post=post, body=body):
                self._emit_hoisted_vars(stmt.hoisted_vars)
                self._emit_for_classic(init, cond, post, body)
            case While(cond=cond, body=body):
                self._emit_hoisted_vars(stmt.hoisted_vars)
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
                for s in body:
                    self._emit_stmt(s)
            case TryCatch(body=body, catch_var=catch_var, catch_body=catch_body, reraise=reraise):
                self._emit_hoisted_vars(stmt.hoisted_vars)
                self._emit_try_catch(body, catch_var, catch_body, reraise)
            case Raise(error_type=error_type, message=message, pos=pos, reraise_var=reraise_var):
                if reraise_var:
                    self._line(f"throw {_camel(reraise_var)}")
                elif error_type == "MatchedPairError":
                    self._line(f"throw new {error_type}()")
                else:
                    p = self._expr(pos)
                    if isinstance(message, StringLit):
                        msg_val = (
                            message.value.replace("\\", "\\\\")
                            .replace("`", "\\`")
                            .replace("$", "\\$")
                        )
                        self._line(f"throw new {error_type}(`{msg_val} at position ${{{p}}}`, {p})")
                    else:
                        msg = self._expr(message)
                        self._line(
                            f"throw new {error_type}(`${{{msg}}} at position ${{{p}}}`, {p})"
                        )
            case SoftFail():
                self._line("return null;")
            case _:
                raise NotImplementedError("Unknown statement")

    def _emit_type_switch(
        self, expr: Expr, binding: str, cases: list[TypeCase], default: list[Stmt]
    ) -> None:
        var = self._expr(expr)
        binding_name = _camel(binding)
        shadows = isinstance(expr, Var) and _camel(expr.name) == binding_name
        for i, case in enumerate(cases):
            keyword = "if" if i == 0 else "} else if"
            if isinstance(case.typ, Primitive):
                js_typeof = _typeof_check(case.typ.kind)
                self._line(f"{keyword} (typeof {var} === '{js_typeof}') {{")
            else:
                type_name = self._type_name_for_check(case.typ)
                self._line(f"{keyword} ({var} instanceof {type_name}) {{")
            self.indent += 1
            if not shadows:
                self._line(f"const {binding_name} = {var};")
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

    def _emit_match(self, expr: Expr, cases: list[MatchCase], default: list[Stmt]) -> None:
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
        if self._try_emit_map(index, value, iterable, body):
            return
        iter_expr = self._expr(iterable)
        iter_type = iterable.typ
        is_string = isinstance(iter_type, Primitive) and iter_type.kind == "string"
        if index is not None and value is not None:
            self._line(
                f"for (var {_camel(index)} = 0; {_camel(index)} < {iter_expr}.length; {_camel(index)}++) {{"
            )
            self.indent += 1
            self._line(f"const {_camel(value)} = {iter_expr}[{_camel(index)}];")
        elif value is not None:
            self._line(f"for (const {_camel(value)} of {iter_expr}) {{")
            self.indent += 1
        elif index is not None:
            self._line(
                f"for (var {_camel(index)} = 0; {_camel(index)} < {iter_expr}.length; {_camel(index)}++) {{"
            )
            self.indent += 1
        else:
            self._line(f"for (const _ of {iter_expr}) {{")
            self.indent += 1
        for s in body:
            self._emit_stmt(s)
        self.indent -= 1
        self._line("}")

    def _try_emit_map(
        self,
        index: str | None,
        value: str | None,
        iterable: Expr,
        body: list[Stmt],
    ) -> bool:
        """Try to emit ForRange as .map(). Returns True if successful."""
        if index is not None or value is None:
            return False
        if len(body) != 1:
            return False
        stmt = body[0]
        if not isinstance(stmt, ExprStmt):
            return False
        expr = stmt.expr
        if not isinstance(expr, MethodCall):
            return False
        if expr.method != "append":
            return False
        if len(expr.args) != 1:
            return False
        if not isinstance(expr.obj, Var):
            return False
        transform_expr = expr.args[0]
        if not self._expr_uses_var(transform_expr, value):
            return False
        accumulator = self._expr(expr.obj)
        iter_expr = self._expr(iterable)
        transform = self._expr(transform_expr)
        self._line(f"{accumulator}.push(...{iter_expr}.map({_camel(value)} => {transform}));")
        return True

    def _expr_uses_var(self, expr: Expr, var_name: str) -> bool:
        """Check if an expression uses a variable (shallow check)."""
        if isinstance(expr, Var):
            return expr.name == var_name
        if isinstance(expr, MethodCall):
            if self._expr_uses_var(expr.obj, var_name):
                return True
            return any(self._expr_uses_var(a, var_name) for a in expr.args)
        if isinstance(expr, Call):
            return any(self._expr_uses_var(a, var_name) for a in expr.args)
        if isinstance(expr, FieldAccess):
            return self._expr_uses_var(expr.obj, var_name)
        if isinstance(expr, Index):
            return self._expr_uses_var(expr.obj, var_name) or self._expr_uses_var(
                expr.index, var_name
            )
        if isinstance(expr, BinaryOp):
            return self._expr_uses_var(expr.left, var_name) or self._expr_uses_var(
                expr.right, var_name
            )
        if isinstance(expr, UnaryOp):
            return self._expr_uses_var(expr.operand, var_name)
        if isinstance(expr, Ternary):
            return (
                self._expr_uses_var(expr.cond, var_name)
                or self._expr_uses_var(expr.then_expr, var_name)
                or self._expr_uses_var(expr.else_expr, var_name)
            )
        if isinstance(expr, Cast):
            return self._expr_uses_var(expr.expr, var_name)
        if isinstance(expr, SliceLit):
            return any(self._expr_uses_var(e, var_name) for e in expr.elements)
        if isinstance(expr, TupleLit):
            return any(self._expr_uses_var(e, var_name) for e in expr.elements)
        if isinstance(expr, StructLit):
            return any(self._expr_uses_var(v, var_name) for v in expr.fields.values())
        return False

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
                if value is not None:
                    return f"let {_camel(name)} = {self._expr(value)}"
                return f"let {_camel(name)}"
            case Assign(
                target=VarLV(name=name),
                value=BinaryOp(op=op, left=Var(name=left_name), right=IntLit(value=1)),
            ) if name == left_name and op in ("+", "-"):
                return f"{_camel(name)}++" if op == "+" else f"{_camel(name)}--"
            case Assign(target=target, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                if stmt.is_declaration:
                    return f"let {lv} = {val}"
                return f"{lv} = {val}"
            case OpAssign(target=target, op=op, value=value):
                return f"{self._lvalue(target)} {op}= {self._expr(value)}"
            case ExprStmt(expr=expr):
                return self._expr(expr)
            case _:
                raise NotImplementedError("Cannot inline")

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
                if field.startswith("F") and field[1:].isdigit():
                    return f"{self._expr(obj)}[{field[1:]}]"
                obj_str = self._expr(obj)
                field_str = _camel(field)
                return f"{obj_str}.{field_str}"
            case FuncRef(name=name, obj=obj):
                if obj is not None:
                    obj_str = self._expr(obj)
                    return f"{obj_str}.{_camel(name)}.bind({obj_str})"
                return _camel(name)
            case Index(obj=obj, index=index, typ=typ):
                obj_str = self._expr(obj)
                idx_str = self._expr(index)
                obj_type = obj.typ
                if (
                    obj_type == STRING
                    and isinstance(typ, Primitive)
                    and typ.kind in ("int", "byte", "rune")
                ):
                    return f"{obj_str}.charCodeAt({idx_str})"
                return f"{obj_str}[{idx_str}]"
            case SliceExpr(obj=obj, low=low, high=high):
                return self._slice_expr(obj, low, high)
            case ParseInt(string=s, base=b):
                return f"parseInt({self._expr(s)}, {self._expr(b)})"
            case IntToStr(value=v):
                return f"String({self._expr(v)})"
            case CharClassify(kind=kind, char=char):
                regex_map = {
                    "digit": r"/^\d+$/",
                    "alpha": r"/^[a-zA-Z]+$/",
                    "alnum": r"/^[a-zA-Z0-9]+$/",
                    "space": r"/^\s+$/",
                    "upper": r"/^[A-Z]+$/",
                    "lower": r"/^[a-z]+$/",
                }
                return f"{regex_map[kind]}.test({self._expr(char)})"
            case TrimChars(string=s, chars=chars, mode=mode):
                s_str = self._expr(s)
                if isinstance(chars, StringLit) and chars.value == " \t\n\r":
                    method_map = {"left": "trimStart", "right": "trimEnd", "both": "trim"}
                    return f"{s_str}.{method_map[mode]}()"
                escaped = _escape_regex_class(chars.value) if isinstance(chars, StringLit) else "..."
                if mode == "left":
                    return f"{s_str}.replace(/^[{escaped}]+/, '')"
                elif mode == "right":
                    return f"{s_str}.replace(/[{escaped}]+$/, '')"
                else:
                    return f"{s_str}.replace(/^[{escaped}]+/, '').replace(/[{escaped}]+$/, '')"
            case Call(func="_intPtr", args=[arg]):
                return self._expr(arg)
            case Call(func=func, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                return f"{_camel(func)}({args_str})"
            case MethodCall(obj=obj, method="join", args=[arr], receiver_type=_):
                return f"{self._expr(arr)}.join({self._expr(obj)})"
            case MethodCall(
                obj=obj, method="extend", args=[other], receiver_type=receiver_type
            ) if _is_array_type(receiver_type):
                return f"{self._expr(obj)}.push(...{self._expr(other)})"
            case MethodCall(obj=obj, method="copy", args=[], receiver_type=receiver_type) if (
                _is_array_type(receiver_type)
            ):
                return f"{self._expr(obj)}.slice()"
            case MethodCall(
                obj=obj, method="get", args=[key, default], receiver_type=receiver_type
            ) if isinstance(receiver_type, Map):
                return f"{self._expr(obj)}.get({self._expr(key)}) ?? {self._expr(default)}"
            case MethodCall(
                obj=obj, method="replace", args=[StringLit(value=old_str), new], receiver_type=_
            ):
                escaped = _escape_regex_literal(old_str)
                return f"{self._expr(obj)}.replace(/{escaped}/g, {self._expr(new)})"
            case MethodCall(
                obj=obj, method=method, args=[TupleLit(elements=elements)], receiver_type=_
            ) if method in ("startswith", "endswith"):
                js_method = "startsWith" if method == "startswith" else "endsWith"
                obj_str = self._expr(obj)
                checks = [f"{obj_str}.{js_method}({self._expr(e)})" for e in elements]
                return f"({' || '.join(checks)})"
            case MethodCall(
                obj=obj, method="pop", args=[IntLit(value=0)], receiver_type=receiver_type
            ) if _is_array_type(receiver_type):
                # Python: list.pop(0) -> JS: list.shift()
                return f"{self._expr(obj)}.shift()"
            case MethodCall(obj=obj, method=method, args=args, receiver_type=receiver_type):
                args_str = ", ".join(self._expr(a) for a in args)
                js_method = _method_name(method, receiver_type)
                return f"{self._expr(obj)}.{js_method}({args_str})"
            case StaticCall(on_type=on_type, method=method, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                type_name = self._type_name_for_check(on_type)
                return f"{type_name}.{_camel(method)}({args_str})"
            case Truthy(expr=e):
                inner_str = self._expr(e)
                inner_type = e.typ
                if isinstance(inner_type, (Slice, Map, Set)) or inner_type == STRING:
                    return f"({inner_str}.length > 0)"
                if isinstance(inner_type, Optional) and isinstance(inner_type.inner, (Slice, Map, Set)):
                    return f"({inner_str}.length > 0)"
                if inner_type == INT:
                    if isinstance(e, BinaryOp):
                        return f"(({inner_str}) !== 0)"
                    return f"({inner_str} !== 0)"
                return f"({inner_str} != null)"
            case BinaryOp(op="in", left=left, right=right):
                return self._containment_check(left, right, negated=False)
            case BinaryOp(op="not in", left=left, right=right):
                return self._containment_check(left, right, negated=True)
            case BinaryOp(op=op, left=left, right=right):
                js_op = _binary_op(op)
                left_str = self._expr_with_precedence(left, op, is_right=False)
                right_str = self._expr_with_precedence(right, op, is_right=True)
                return f"{left_str} {js_op} {right_str}"
            case UnaryOp(op="&", operand=operand):
                return self._expr(operand)
            case UnaryOp(op="*", operand=operand):
                return self._expr(operand)
            case UnaryOp(op="!", operand=BinaryOp(op="!=", left=left, right=right)):
                left_str = self._expr_with_precedence(left, "===", is_right=False)
                right_str = self._expr_with_precedence(right, "===", is_right=True)
                return f"{left_str} === {right_str}"
            case UnaryOp(op="!", operand=BinaryOp(op="==", left=left, right=right)):
                left_str = self._expr_with_precedence(left, "!==", is_right=False)
                right_str = self._expr_with_precedence(right, "!==", is_right=True)
                return f"{left_str} !== {right_str}"
            case UnaryOp(op=op, operand=operand):
                inner = self._expr(operand)
                if isinstance(operand, BinaryOp):
                    inner = f"({inner})"
                return f"{op}{inner}"
            case Ternary(cond=cond, then_expr=then_expr, else_expr=else_expr):
                return f"({self._expr(cond)} ? {self._expr(then_expr)} : {self._expr(else_expr)})"
            case Cast(expr=inner, to_type=to_type):
                # No type casts in JavaScript - just emit the inner expression
                # But handle string/byte conversions
                if (
                    isinstance(to_type, Slice)
                    and isinstance(to_type.element, Primitive)
                    and to_type.element.kind == "byte"
                    and isinstance(inner.typ, Primitive)
                    and inner.typ.kind == "string"
                ):
                    return f"Array.from(new TextEncoder().encode({self._expr(inner)}))"
                if (
                    isinstance(to_type, Primitive)
                    and to_type.kind == "string"
                    and isinstance(inner.typ, Slice)
                    and isinstance(inner.typ.element, Primitive)
                    and inner.typ.element.kind == "byte"
                ):
                    return f"new TextDecoder().decode(new Uint8Array({self._expr(inner)}))"
                if (
                    isinstance(to_type, Primitive)
                    and to_type.kind == "string"
                    and isinstance(inner.typ, Primitive)
                    and inner.typ.kind in ("rune", "int")
                ):
                    return f"String.fromCodePoint({self._expr(inner)})"
                return self._expr(inner)
            case TypeAssert(expr=inner, asserted=asserted):
                # No type assertions in JavaScript - just emit the inner expression
                return self._expr(inner)
            case IsType(expr=inner, tested_type=tested_type):
                if isinstance(tested_type, Primitive):
                    js_typeof = _typeof_check(tested_type.kind)
                    return f"typeof {self._expr(inner)} === '{js_typeof}'"
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
                pairs = ", ".join(f"[{self._expr(k)}, {self._expr(v)}]" for k, v in entries)
                return f"new Map([{pairs}])"
            case SetLit(elements=elements):
                elems = ", ".join(self._expr(e) for e in elements)
                return f"new Set([{elems}])"
            case StructLit(struct_name=struct_name, fields=fields):
                field_names = self.struct_fields.get(struct_name, [])
                ordered_args = []
                for field_name in field_names:
                    if field_name in fields:
                        ordered_args.append(self._expr(fields[field_name]))
                    else:
                        ordered_args.append("null")
                args = ", ".join(ordered_args)
                return f"new {_safe_name(struct_name)}({args})"
            case TupleLit(elements=elements):
                elems = ", ".join(self._expr(e) for e in elements)
                return f"[{elems}]"
            case StringConcat(parts=parts):
                wrapped_parts: list[str] = []
                for p in parts:
                    expr_str = self._expr(p)
                    if " ?? " in expr_str:
                        wrapped_parts.append(f"({expr_str})")
                    else:
                        wrapped_parts.append(expr_str)
                return " + ".join(wrapped_parts)
            case StringFormat(template=template, args=args):
                return self._format_string(template, args)
            case SliceConvert(source=source):
                return self._expr(source)
            case _:
                raise NotImplementedError("Unknown expression")

    def _containment_check(self, item: Expr, container: Expr, negated: bool) -> str:
        """Generate containment check: `x in y` or `x not in y`."""
        item_str = self._expr(item)
        container_str = self._expr(container)
        container_type = container.typ
        neg = "!" if negated else ""
        if isinstance(container_type, (Set, Map)):
            return f"{neg}{container_str}.has({item_str})"
        return f"{neg}{container_str}.includes({item_str})"

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
        if " ?? " in inner and parent_op in ("+", "-", "*", "/", "%"):
            return f"({inner})"
        if not isinstance(expr, BinaryOp):
            return inner
        child_prec = _op_precedence(expr.op)
        parent_prec = _op_precedence(parent_op)
        needs_parens = child_prec < parent_prec or (child_prec == parent_prec and is_right)
        return f"({inner})" if needs_parens else inner

    def _format_string(self, template: str, args: list[Expr]) -> str:
        result = template
        for i, arg in enumerate(args):
            if isinstance(arg, StringLit):
                val = arg.value.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
                result = result.replace(f"{{{i}}}", val, 1)
            else:
                result = result.replace(f"{{{i}}}", f"${{{self._expr(arg)}}}", 1)
        arg_idx = 0
        while "%v" in result:
            if arg_idx >= len(args):
                break
            arg = args[arg_idx]
            arg_idx += 1
            if isinstance(arg, StringLit):
                val = arg.value.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
                result = result.replace("%v", val, 1)
            else:
                result = result.replace("%v", f"${{{self._expr(arg)}}}", 1)
        result = result.replace("`", "\\`")
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
                raise NotImplementedError("Unknown lvalue")

    def _type_name_for_check(self, typ: Type) -> str:
        match typ:
            case StructRef(name=name):
                return _safe_name(name)
            case InterfaceRef(name=name):
                return _safe_name(name)
            case Pointer(target=target):
                return self._type_name_for_check(target)
            case _:
                return "Object"


def _typeof_check(kind: str) -> str:
    """Return the typeof result for a primitive type check."""
    match kind:
        case "string":
            return "string"
        case "int" | "float" | "byte" | "rune":
            return "number"
        case "bool":
            return "boolean"
        case _:
            return "object"


def _camel(name: str, is_receiver_ref: bool = False) -> str:
    """Convert snake_case or PascalCase to camelCase."""
    if name in ("this", "self") and is_receiver_ref:
        return "this"
    if "_" not in name:
        if name and name[0].isupper():
            name = name[0].lower() + name[1:]
        return _safe_name(name)
    parts = name.split("_")
    if len(parts) > 1 and any(p.isupper() for p in parts[1:]):
        return _safe_name(name)
    result = parts[0] + "".join(p.capitalize() for p in parts[1:])
    return _safe_name(result)


_JS_RESERVED = {
    "var",
    "var",
    "const",
    "function",
    "class",
    "Array",
    "Function",
    "Object",
    "String",
    "Number",
    "Boolean",
    "Symbol",
    "Map",
    "Set",
    "Promise",
    "Error",
}


def _safe_name(name: str) -> str:
    """Rename JavaScript reserved words to safe alternatives."""
    if name in _JS_RESERVED:
        return f"{name}Name"
    return name


_STRING_METHOD_MAP = {
    "startswith": "startsWith",
    "endswith": "endsWith",
    "lower": "toLowerCase",
    "upper": "toUpperCase",
    "find": "indexOf",
    "rfind": "lastIndexOf",
}


def _is_array_type(typ: Type) -> bool:
    """Check if type is an array/slice type, possibly wrapped in Pointer."""
    if isinstance(typ, (Slice, Array)):
        return True
    if isinstance(typ, Pointer) and isinstance(typ.target, (Slice, Array)):
        return True
    return False


def _method_name(method: str, receiver_type: Type) -> str:
    """Convert method name based on receiver type."""
    if _is_array_type(receiver_type) and method == "append":
        return "push"
    if method in _STRING_METHOD_MAP:
        return _STRING_METHOD_MAP[method]
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


def _escape_regex_class(chars: str) -> str:
    """Escape characters for use in a regex character class []."""
    result = []
    for c in chars:
        if c in r"]\^-":
            result.append(f"\\{c}")
        elif c == "\t":
            result.append("\\t")
        elif c == "\n":
            result.append("\\n")
        elif c == "\r":
            result.append("\\r")
        else:
            result.append(c)
    return "".join(result)


def _escape_regex_literal(s: str) -> str:
    """Escape a string for use as a literal in a regex pattern."""
    result = []
    for c in s:
        if c in r"\^$.*+?()[]{}|":
            result.append(f"\\{c}")
        elif c == "\t":
            result.append("\\t")
        elif c == "\n":
            result.append("\\n")
        elif c == "\r":
            result.append("\\r")
        else:
            result.append(c)
    return "".join(result)


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
        case "|":
            return 3
        case "^":
            return 4
        case "&":
            return 5
        case "==" | "!=" | "===" | "!==":
            return 6
        case "<" | ">" | "<=" | ">=":
            return 7
        case "<<" | ">>":
            return 8
        case "+" | "-":
            return 9
        case "*" | "/" | "%":
            return 10
        case _:
            return 11
