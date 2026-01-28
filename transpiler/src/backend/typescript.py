"""TypeScript backend: IR → TypeScript code."""

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
    TupleAssign,
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
        self.current_struct: str | None = None  # Track current struct for method binding
        self.struct_fields: dict[str, list[str]] = {}  # struct name -> field names in order

    def emit(self, module: Module) -> str:
        """Emit TypeScript code from IR Module."""
        self.indent = 0
        self.lines = []
        self.struct_fields = {}
        # Pre-collect struct field orders for StructLit emission
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
        # TextEncoder/TextDecoder are available in Node.js but TypeScript needs declarations
        self._line("declare var TextEncoder: { new(): { encode(s: string): Uint8Array } };")
        self._line("declare var TextDecoder: { new(): { decode(b: Uint8Array): string } };")
        self._line("function range(start: number, end?: number, step?: number): number[] {")
        self.indent += 1
        self._line("if (end === undefined) { end = start; start = 0; }")
        self._line("if (step === undefined) { step = 1; }")
        self._line("const result: number[] = [];")
        self._line("if (step > 0) {")
        self.indent += 1
        self._line("for (let i = start; i < end; i += step) result.push(i);")
        self.indent -= 1
        self._line("} else {")
        self.indent += 1
        self._line("for (let i = start; i > end; i += step) result.push(i);")
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
        # Emit CommonJS exports for test runner
        self._line()
        self._line("// CommonJS exports")
        self._line("declare var module: any;")
        self._line("if (typeof module !== 'undefined') {")
        self.indent += 1
        self._line("module.exports = { parse, ParseError };")
        self.indent -= 1
        self._line("}")

    def _emit_constant(self, const: Constant) -> None:
        typ = self._type(const.typ)
        val = self._expr(const.value)
        self._line(f"const {const.name}: {typ} = {val};")

    def _emit_interface(self, iface: InterfaceDef) -> None:
        self._line(f"interface {_safe_name(iface.name)} {{")
        self.indent += 1
        # Node interface needs a kind property for type discrimination
        if iface.name == "Node":
            self._line("kind: string;")
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
            implements = f" implements {', '.join(_safe_name(i) for i in struct.implements)}"
        self._line(f"class {_safe_name(struct.name)}{implements} {{")
        self.indent += 1
        for fld in struct.fields:
            self._emit_field(fld)
        if struct.fields:
            self._line()
            self._emit_constructor(struct)
        # Add getKind() method for Node implementations that have a kind field
        has_kind_field = any(f.name == "kind" for f in struct.fields)
        has_getkind_method = any(m.name in ("GetKind", "get_kind") for m in struct.methods)
        if "Node" in struct.implements and has_kind_field and not has_getkind_method:
            self._line()
            self._line("getKind(): string {")
            self.indent += 1
            self._line("return this.kind;")
            self.indent -= 1
            self._line("}")
        self.current_struct = struct.name
        for i, method in enumerate(struct.methods):
            if i > 0 or struct.fields:
                self._line()
            self._emit_method(method)
        self.current_struct = None
        self.indent -= 1
        self._line("}")

    def _emit_field(self, fld: Field) -> None:
        typ = self._type(fld.typ)
        self._line(f"{_camel(fld.name)}: {typ};")

    def _emit_constructor(self, struct: Struct) -> None:
        # Add default values so parameterless construction works
        params = ", ".join(
            f"{_camel(f.name)}: {self._type(f.typ)} = {self._default_value(f.typ)}"
            for f in struct.fields
        )
        self._line(f"constructor({params}) {{")
        self.indent += 1
        for fld in struct.fields:
            name = _camel(fld.name)
            # For array/slice fields, convert null to empty array (Python passes None, JS needs [])
            # But don't do this for Optional(Slice(...)) - null has semantic meaning there
            is_nullable_slice = isinstance(fld.typ, Optional) and isinstance(fld.typ.inner, (Slice, Array))
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
                # Use var with 'any' type for function-scoped semantics (matches Python/Go)
                # The 'any' type prevents TypeScript errors when same var is re-declared
                # with a different inferred type in a different branch
                if value is not None:
                    val = self._expr(value)
                    self._line(f"var {_camel(name)}: any = {val};")
                else:
                    self._line(f"var {_camel(name)}: any;")
            case Assign(target=target, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                if getattr(stmt, 'is_declaration', False):
                    # Use var with any type for function-scoped semantics
                    self._line(f"var {lv}: any = {val};")
                else:
                    self._line(f"{lv} = {val};")
            case TupleAssign(targets=targets, value=value):
                lvalues = ", ".join(self._lvalue(t) for t in targets)
                val = self._expr(value)
                if getattr(stmt, 'is_declaration', False):
                    # Use var with any type for function-scoped semantics
                    self._line(f"var [{lvalues}]: any = {val};")
                else:
                    # Check for new_targets - variables that need pre-declaration
                    new_targets = getattr(stmt, 'new_targets', [])
                    for name in new_targets:
                        self._line(f"var {_camel(name)}: any;")
                    self._line(f"[{lvalues}] = {val};")
            case OpAssign(target=target, op=op, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                self._line(f"{lv} {op}= {val};")
            case ExprStmt(expr=Var(name=name)) if name in (
                "_skip_docstring", "_pass", "_skip_super_init"
            ):
                pass  # Skip marker statements
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
                # Use standard Error since custom error types aren't defined
                self._line(f"throw new Error(`${{{msg}}} at position ${{{p}}}`)")
            case SoftFail():
                self._line("return null;")
            case _:
                raise NotImplementedError(f"Unknown statement: {type(stmt).__name__}")

    def _emit_type_switch(
        self, expr: Expr, binding: str, cases: list[TypeCase], default: list[Stmt]
    ) -> None:
        var = self._expr(expr)
        binding_name = _camel(binding)
        # Check if binding would shadow the expression variable
        shadows = isinstance(expr, Var) and _camel(expr.name) == binding_name
        for i, case in enumerate(cases):
            keyword = "if" if i == 0 else "} else if"
            # Primitive types use typeof, classes use instanceof
            if isinstance(case.typ, Primitive):
                ts_typeof = _typeof_check(case.typ.kind)
                self._line(f"{keyword} (typeof {var} === '{ts_typeof}') {{")
            else:
                type_name = self._type_name_for_check(case.typ)
                self._line(f"{keyword} ({var} instanceof {type_name}) {{")
            self.indent += 1
            # Skip const declaration if it would shadow - TypeScript narrows type automatically
            if not shadows:
                self._line(f"const {binding_name} = {var} as {self._type(case.typ)};")
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
                # Use var with any type for function-scoped semantics
                if value is not None:
                    return f"var {_camel(name)}: any = {self._expr(value)}"
                return f"var {_camel(name)}: any"
            case Assign(target=VarLV(name=name), value=BinaryOp(op=op, left=Var(name=left_name), right=IntLit(value=1))) if name == left_name and op in ("+", "-"):
                return f"{_camel(name)}++" if op == "+" else f"{_camel(name)}--"
            case Assign(target=target, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                if getattr(stmt, 'is_declaration', False):
                    # Use var with any type for function-scoped semantics
                    return f"var {lv}: any = {val}"
                return f"{lv} = {val}"
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
                # Tuple field access: F0, F1, etc. → [0], [1], etc.
                if field.startswith("F") and field[1:].isdigit():
                    return f"{self._expr(obj)}[{field[1:]}]"
                obj_str = self._expr(obj)
                field_str = _camel(field)
                # Check if this is a method reference on 'this' (needs .bind(this))
                # If accessing 'this.method' where method is not a struct field,
                # it's a method reference being passed as a callback
                if (obj_str == "this" and
                    self.current_struct is not None and
                    field not in self.struct_fields.get(self.current_struct, [])):
                    return f"{obj_str}.{field_str}.bind(this)"
                return f"{obj_str}.{field_str}"
            case Index(obj=obj, index=index, typ=typ):
                obj_str = self._expr(obj)
                idx_str = self._expr(index)
                # String indexing returns char code (number) in our IR
                obj_type = getattr(obj, 'typ', None)
                if obj_type == STRING and typ == INT:
                    return f"{obj_str}.charCodeAt({idx_str})"
                return f"{obj_str}[{idx_str}]"
            case SliceExpr(obj=obj, low=low, high=high):
                return self._slice_expr(obj, low, high)
            case Call(func="_parseInt", args=args):
                # _parseInt(s, base) → parseInt(s, base)
                args_str = ", ".join(self._expr(a) for a in args)
                return f"parseInt({args_str})"
            case Call(func="_intToStr", args=[arg]):
                # _intToStr(n) → String(n)
                return f"String({self._expr(arg)})"
            case Call(func="_intPtr", args=[arg]):
                # _intPtr is a Python type hint, just return the argument
                return self._expr(arg)
            case Call(func=func, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                return f"{_camel(func)}({args_str})"
            case MethodCall(obj=obj, method="join", args=[arr], receiver_type=_):
                # "sep".join(arr) → arr.join("sep")
                # Python's join is a string method; always swap receiver and arg for TypeScript
                return f"{self._expr(arr)}.join({self._expr(obj)})"
            case MethodCall(obj=obj, method="extend", args=[other], receiver_type=receiver_type) if _is_array_type(receiver_type):
                # arr.extend(other) → arr.push(...other)
                return f"{self._expr(obj)}.push(...{self._expr(other)})"
            case MethodCall(obj=obj, method="copy", args=[], receiver_type=receiver_type) if _is_array_type(receiver_type):
                # arr.copy() → arr.slice()
                return f"{self._expr(obj)}.slice()"
            case MethodCall(obj=obj, method="isalnum", args=_, receiver_type=_):
                return f"/^[a-zA-Z0-9]$/.test({self._expr(obj)})"
            case MethodCall(obj=obj, method="isdigit", args=_, receiver_type=_):
                return f"/^[0-9]$/.test({self._expr(obj)})"
            case MethodCall(obj=obj, method="isalpha", args=_, receiver_type=_):
                return f"/^[a-zA-Z]$/.test({self._expr(obj)})"
            case MethodCall(obj=obj, method="isspace", args=_, receiver_type=_):
                return f"/^\\s$/.test({self._expr(obj)})"
            case MethodCall(obj=obj, method="lstrip", args=[StringLit(value=chars)], receiver_type=_):
                # Python lstrip with chars → regex replace (JS trimStart takes no args)
                escaped = _escape_regex_class(chars)
                return f"{self._expr(obj)}.replace(/^[{escaped}]+/, '')"
            case MethodCall(obj=obj, method="rstrip", args=[StringLit(value=chars)], receiver_type=_):
                # Python rstrip with chars → regex replace (JS trimEnd takes no args)
                escaped = _escape_regex_class(chars)
                return f"{self._expr(obj)}.replace(/[{escaped}]+$/, '')"
            case MethodCall(obj=obj, method="strip", args=[StringLit(value=chars)], receiver_type=_):
                # Python strip with chars → regex replace (JS trim takes no args)
                escaped = _escape_regex_class(chars)
                return f"{self._expr(obj)}.replace(/^[{escaped}]+/, '').replace(/[{escaped}]+$/, '')"
            case MethodCall(obj=obj, method="get", args=[key, default], receiver_type=receiver_type) if isinstance(receiver_type, Map):
                # Python dict.get(key, default) → JS Map.get(key) ?? default
                return f"{self._expr(obj)}.get({self._expr(key)}) ?? {self._expr(default)}"
            case MethodCall(obj=obj, method="replace", args=[StringLit(value=old_str), new], receiver_type=_):
                # Python str.replace replaces ALL occurrences; JS replace only replaces first
                # Use regex with global flag for all-occurrence replacement
                escaped = _escape_regex_literal(old_str)
                return f"{self._expr(obj)}.replace(/{escaped}/g, {self._expr(new)})"
            case MethodCall(obj=obj, method=method, args=args, receiver_type=receiver_type):
                args_str = ", ".join(self._expr(a) for a in args)
                ts_method = _method_name(method, receiver_type)
                return f"{self._expr(obj)}.{ts_method}({args_str})"
            case StaticCall(on_type=on_type, method=method, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                type_name = self._type_name_for_check(on_type)
                return f"{type_name}.{_camel(method)}({args_str})"
            case BinaryOp(op="in", left=left, right=right):
                return self._containment_check(left, right, negated=False)
            case BinaryOp(op="not in", left=left, right=right):
                return self._containment_check(left, right, negated=True)
            case BinaryOp(op=op, left=left, right=right):
                ts_op = _binary_op(op)
                left_str = self._expr_with_precedence(left, op, is_right=False)
                right_str = self._expr_with_precedence(right, op, is_right=True)
                return f"{left_str} {ts_op} {right_str}"
            case UnaryOp(op="&", operand=operand):
                return self._expr(operand)  # TypeScript passes objects by reference
            case UnaryOp(op="*", operand=operand):
                return self._expr(operand)  # TypeScript has no pointer dereference
            case UnaryOp(op=op, operand=operand):
                inner = self._expr(operand)
                # Wrap in parentheses if operand is a binary expression (precedence)
                if isinstance(operand, BinaryOp):
                    inner = f"({inner})"
                return f"{op}{inner}"
            case Ternary(cond=cond, then_expr=then_expr, else_expr=else_expr):
                return f"{self._expr(cond)} ? {self._expr(then_expr)} : {self._expr(else_expr)}"
            case Cast(expr=inner, to_type=to_type):
                ts_type = self._type(to_type)
                from_type = self._type(inner.typ) if hasattr(inner, 'typ') else None
                if from_type == ts_type:
                    return self._expr(inner)
                # string to []byte: use TextEncoder for proper UTF-8 encoding
                if (isinstance(to_type, Slice) and
                    isinstance(to_type.element, Primitive) and
                    to_type.element.kind == "byte" and
                    hasattr(inner, 'typ') and
                    isinstance(inner.typ, Primitive) and
                    inner.typ.kind == "string"):
                    return f"Array.from(new TextEncoder().encode({self._expr(inner)}))"
                # []byte to string: use TextDecoder for proper UTF-8 decoding
                if (isinstance(to_type, Primitive) and
                    to_type.kind == "string" and
                    hasattr(inner, 'typ') and
                    isinstance(inner.typ, Slice) and
                    isinstance(inner.typ.element, Primitive) and
                    inner.typ.element.kind == "byte"):
                    return f"new TextDecoder().decode(new Uint8Array({self._expr(inner)}))"
                # Use 'as unknown as' to allow any type conversion
                return f"({self._expr(inner)} as unknown as {ts_type})"
            case TypeAssert(expr=inner, asserted=asserted):
                return f"({self._expr(inner)} as unknown as {self._type(asserted)})"
            case IsType(expr=inner, tested_type=tested_type):
                # Primitive types use typeof, classes use instanceof
                if isinstance(tested_type, Primitive):
                    ts_typeof = _typeof_check(tested_type.kind)
                    return f"typeof {self._expr(inner)} === '{ts_typeof}'"
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
                # Cast args to any to suppress type errors from IR type mismatches
                # Use struct field order for positional constructor args
                field_order = self.struct_fields.get(struct_name, [])
                ordered_args = []
                for field_name in field_order:
                    if field_name in fields:
                        ordered_args.append(f"{self._expr(fields[field_name])} as any")
                    else:
                        # Missing field - use default value based on type
                        ordered_args.append("[] as any")  # Most common default for missing is empty array
                args = ", ".join(ordered_args)
                return f"new {_safe_name(struct_name)}({args})"
            case TupleLit(elements=elements):
                elems = ", ".join(self._expr(e) for e in elements)
                return f"[{elems}]"
            case StringConcat(parts=parts):
                # Wrap parts that have lower precedence than + (like ??)
                def wrap_part(p):
                    expr_str = self._expr(p)
                    # ?? has lower precedence than +, needs parens
                    if " ?? " in expr_str:
                        return f"({expr_str})"
                    return expr_str
                return " + ".join(wrap_part(p) for p in parts)
            case StringFormat(template=template, args=args):
                return self._format_string(template, args)
            case SliceConvert(source=source):
                return self._expr(source)  # TypeScript arrays are covariant
            case _:
                raise NotImplementedError(f"Unknown expression: {type(expr).__name__}")

    def _containment_check(self, item: Expr, container: Expr, negated: bool) -> str:
        """Generate containment check: `x in y` or `x not in y`."""
        item_str = self._expr(item)
        container_str = self._expr(container)
        container_type = getattr(container, 'typ', None)
        neg = "!" if negated else ""
        if isinstance(container_type, (Set, Map)):
            return f"{neg}{container_str}.has({item_str})"
        # For strings and arrays, use includes
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
        # Check for ?? in emitted string - it has lower precedence than + and other ops
        # This handles cases like Map.get(key) ?? default inside string concatenation
        if " ?? " in inner and parent_op in ("+", "-", "*", "/", "%"):
            return f"({inner})"
        if not isinstance(expr, BinaryOp):
            return inner
        child_prec = _op_precedence(expr.op)
        parent_prec = _op_precedence(parent_op)
        # Need parens if child has lower precedence, or same precedence on right side
        needs_parens = child_prec < parent_prec or (child_prec == parent_prec and is_right)
        return f"({inner})" if needs_parens else inner

    def _format_string(self, template: str, args: list[Expr]) -> str:
        result = template
        # Handle {0}, {1} style placeholders
        for i, arg in enumerate(args):
            result = result.replace(f"{{{i}}}", f"${{{self._expr(arg)}}}", 1)
        # Handle %v placeholders (sequential)
        arg_iter = iter(args)
        while "%v" in result:
            try:
                arg = next(arg_iter)
                result = result.replace("%v", f"${{{self._expr(arg)}}}", 1)
            except StopIteration:
                break
        # Escape backticks in the template
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
                return _safe_name(name)
            case Interface(name=name):
                return _safe_name(name)
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
                return _safe_name(name)
            case Interface(name=name):
                return _safe_name(name)
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
    """Convert snake_case or PascalCase to camelCase.

    Args:
        name: The identifier name
        is_receiver_ref: True if this is a reference to the method receiver
                        (should become 'this'), False otherwise
    """
    if name in ("this", "self") and is_receiver_ref:
        return "this"
    if "_" not in name:
        # Convert PascalCase to camelCase (lowercase first letter)
        if name and name[0].isupper():
            name = name[0].lower() + name[1:]
        return _safe_name(name)
    # Don't convert SCREAMING_SNAKE_CASE constants - preserve underscores
    # These have uppercase letters after the first underscore
    parts = name.split("_")
    if len(parts) > 1 and any(p.isupper() for p in parts[1:]):
        return _safe_name(name)
    result = parts[0] + "".join(p.capitalize() for p in parts[1:])
    return _safe_name(result)


# TypeScript reserved words and built-in type names that may be used as identifiers in source
_TS_RESERVED = {
    "var", "let", "const", "function", "class", "interface", "type", "enum",
    "Array", "Function", "Object", "String", "Number", "Boolean", "Symbol",
    "Map", "Set", "Promise", "Error",
}


def _safe_name(name: str) -> str:
    """Rename TypeScript reserved words to safe alternatives."""
    if name in _TS_RESERVED:
        return f"{name}Name"
    return name


# Python string method → TypeScript string method
_STRING_METHOD_MAP = {
    "startswith": "startsWith",
    "endswith": "endsWith",
    "rstrip": "trimEnd",
    "lstrip": "trimStart",
    "strip": "trim",
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
    # Apply string method mapping unconditionally - these methods only exist on strings
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
    # Characters that need escaping in a character class: ] \ ^ -
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
    # Characters that have special meaning in regex: \ ^ $ . * + ? ( ) [ ] { } |
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
    """Return precedence level for binary operator (higher = binds tighter).

    TypeScript precedence (lower number = lower precedence):
    - Bitwise OR/XOR/AND have LOWER precedence than comparison operators
    - This differs from Python, so we must wrap bitwise ops in parens when compared
    """
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
