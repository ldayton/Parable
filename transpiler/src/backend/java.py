"""Java backend: IR → Java code."""

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


class JavaBackend:
    """Emit Java code from IR."""

    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self.receiver_name: str | None = None
        self.current_class: str = ""
        self.tuple_records: dict[tuple, str] = {}  # tuple signature -> record name
        self.tuple_counter = 0

    def emit(self, module: Module) -> str:
        """Emit Java code from IR Module."""
        self.indent = 0
        self.lines = []
        self.tuple_records = {}
        self.tuple_counter = 0
        self._collect_tuple_types(module)
        self._emit_module(module)
        return "\n".join(self.lines)

    def _collect_tuple_types(self, module: Module) -> None:
        """Collect all unique tuple types used in the module."""
        def visit_type(typ: Type) -> None:
            if isinstance(typ, Tuple):
                sig = tuple(self._type(t) for t in typ.elements)
                if sig not in self.tuple_records:
                    self.tuple_counter += 1
                    self.tuple_records[sig] = f"Tuple{self.tuple_counter}"
        def visit_func(func: Function) -> None:
            visit_type(func.ret)
            for stmt in func.body:
                visit_stmt(stmt)
        def visit_stmt(stmt: Stmt) -> None:
            match stmt:
                case VarDecl(typ=typ, value=value):
                    visit_type(typ)
                    if value:
                        visit_expr(value)
                case Return(value=value):
                    if value:
                        visit_expr(value)
                case If(then_body=then_body, else_body=else_body):
                    for s in then_body:
                        visit_stmt(s)
                    for s in else_body:
                        visit_stmt(s)
                case While(body=body):
                    for s in body:
                        visit_stmt(s)
                case ForRange(body=body):
                    for s in body:
                        visit_stmt(s)
                case ForClassic(body=body):
                    for s in body:
                        visit_stmt(s)
                case Block(body=body):
                    for s in body:
                        visit_stmt(s)
                case TryCatch(body=body, catch_body=catch_body):
                    for s in body:
                        visit_stmt(s)
                    for s in catch_body:
                        visit_stmt(s)
                case _:
                    pass
        def visit_expr(expr: Expr) -> None:
            match expr:
                case MethodCall(typ=typ):
                    visit_type(typ)
                case TupleLit(typ=typ):
                    visit_type(typ)
                case _:
                    pass
        for struct in module.structs:
            for method in struct.methods:
                visit_func(method)
        for func in module.functions:
            visit_func(func)

    def _line(self, text: str = "") -> None:
        if text:
            self.lines.append("    " * self.indent + text)
        else:
            self.lines.append("")

    def _emit_module(self, module: Module) -> None:
        self._line("import java.util.*;")
        self._line("")
        if module.constants:
            self._line("final class Constants {")
            self.indent += 1
            for const in module.constants:
                self._emit_constant(const)
            self.indent -= 1
            self._line("}")
            self._line("")
        # Emit record definitions for tuple types
        for sig, name in self.tuple_records.items():
            self._emit_tuple_record(name, sig)
            self._line("")
        for iface in module.interfaces:
            self._emit_interface(iface)
            self._line("")
        for struct in module.structs:
            self._emit_struct(struct)
            self._line("")
        for func in module.functions:
            # Free functions go in a utility class
            pass
        if module.functions:
            self._emit_functions_class(module)

    def _emit_tuple_record(self, name: str, sig: tuple) -> None:
        """Emit a record definition for a tuple type."""
        fields = ", ".join(f"{typ} f{i}" for i, typ in enumerate(sig))
        self._line(f"record {name}({fields}) {{}}")

    def _emit_constant(self, const: Constant) -> None:
        typ = self._type(const.typ)
        val = self._expr(const.value)
        name = _to_screaming_snake(const.name)
        self._line(f"public static final {typ} {name} = {val};")

    def _emit_interface(self, iface: InterfaceDef) -> None:
        self._line(f"interface {iface.name} {{")
        self.indent += 1
        for method in iface.methods:
            params = self._params(method.params)
            ret = self._type(method.ret)
            name = _to_camel(method.name)
            self._line(f"{ret} {name}({params});")
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
        # Default constructor
        self._emit_default_constructor(struct)
        self._line("")
        for i, method in enumerate(struct.methods):
            if i > 0:
                self._line("")
            self._emit_method(method)
        self.indent -= 1
        self._line("}")
        self.current_class = ""

    def _emit_default_constructor(self, struct: Struct) -> None:
        """Emit a constructor with all fields as parameters."""
        if not struct.fields:
            return
        params = ", ".join(
            f"{self._type(f.typ)} {_to_camel(f.name)}" for f in struct.fields
        )
        self._line(f"{struct.name}({params}) {{")
        self.indent += 1
        for f in struct.fields:
            name = _to_camel(f.name)
            self._line(f"this.{name} = {name};")
        self.indent -= 1
        self._line("}")

    def _emit_field(self, fld: Field) -> None:
        typ = self._type(fld.typ)
        self._line(f"{typ} {_to_camel(fld.name)};")

    def _emit_functions_class(self, module: Module) -> None:
        """Emit free functions as static methods in a utility class."""
        self._line(f"final class {_to_pascal(module.name)}Functions {{")
        self.indent += 1
        self._line(f"private {_to_pascal(module.name)}Functions() {{}}")
        self._line("")
        for i, func in enumerate(module.functions):
            if i > 0:
                self._line("")
            self._emit_function(func)
        self.indent -= 1
        self._line("}")

    def _emit_function(self, func: Function) -> None:
        params = self._params(func.params)
        ret = self._type(func.ret)
        name = _to_camel(func.name)
        self._line(f"static {ret} {name}({params}) {{")
        self.indent += 1
        if not func.body:
            self._line('throw new UnsupportedOperationException("todo");')
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
        self._line(f"{ret} {name}({params}) {{")
        self.indent += 1
        if not func.body:
            self._line('throw new UnsupportedOperationException("todo");')
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")
        self.receiver_name = None

    def _params(self, params: list) -> str:
        parts = []
        for p in params:
            typ = self._type(p.typ)
            parts.append(f"{typ} {_to_camel(p.name)}")
        return ", ".join(parts)

    def _emit_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDecl(name=name, typ=typ, value=value, mutable=mutable):
                java_type = self._type(typ)
                var_name = _to_camel(name)
                if value is not None:
                    val = self._expr(value)
                    self._line(f"{java_type} {var_name} = {val};")
                else:
                    default = self._default_value(typ)
                    self._line(f"{java_type} {var_name} = {default};")
            case Assign(target=target, value=value):
                val = self._expr(value)
                # Special handling for ArrayList index assignment
                if isinstance(target, IndexLV) and isinstance(target.obj.typ, Slice):
                    obj_str = self._expr(target.obj)
                    idx_str = self._expr(target.index)
                    self._line(f"{obj_str}.set({idx_str}, {val});")
                else:
                    lv = self._lvalue(target)
                    self._line(f"{lv} = {val};")
            case OpAssign(target=target, op=op, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                self._line(f"{lv} {op}= {val};")
            case ExprStmt(expr=expr):
                e = self._expr(expr)
                self._line(f"{e};")
            case Return(value=value):
                if value is not None:
                    if isinstance(value, TupleLit):
                        # Use record type for tuple returns
                        record_name = self._tuple_record_name(value.typ)
                        elements = ", ".join(self._expr(e) for e in value.elements)
                        self._line(f"return new {record_name}({elements});")
                    else:
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
            case TryCatch(body=body, catch_var=catch_var, catch_body=catch_body, reraise=reraise):
                self._emit_try_catch(body, catch_var, catch_body, reraise)
            case Raise(error_type=error_type, message=message, pos=pos):
                msg = self._expr(message)
                self._line(f"throw new RuntimeException({msg});")
            case SoftFail():
                self._line("return null;")
            case _:
                self._line(f"// TODO: {type(stmt).__name__}")

    def _emit_type_switch(
        self, expr: Expr, binding: str, cases: list[TypeCase], default: list[Stmt]
    ) -> None:
        var = self._expr(expr)
        bind_name = _to_camel(binding)
        self._line(f"Object {bind_name} = {var};")
        for i, case in enumerate(cases):
            type_name = self._type_name_for_check(case.typ)
            keyword = "if" if i == 0 else "} else if"
            self._line(f"{keyword} ({bind_name} instanceof {type_name}) {{")
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
        # Java switch on strings
        self._line(f"switch ({expr_str}) {{")
        self.indent += 1
        for case in cases:
            for pattern in case.patterns:
                self._line(f"case {self._expr(pattern)}:")
            self.indent += 1
            for s in case.body:
                self._emit_stmt(s)
            # Add break if body doesn't end with return
            if case.body and not isinstance(case.body[-1], Return):
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
        if value is not None and index is not None:
            # Need index - use traditional for loop
            idx = _to_camel(index)
            val = _to_camel(value)
            self._line(f"for (int {idx} = 0; {idx} < {iter_expr}.size(); {idx}++) {{")
            self.indent += 1
            elem_type = self._element_type(iterable.typ)
            self._line(f"{elem_type} {val} = {iter_expr}.get({idx});")
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        elif value is not None:
            val = _to_camel(value)
            elem_type = self._element_type(iterable.typ)
            self._line(f"for ({elem_type} {val} : {iter_expr}) {{")
            self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        elif index is not None:
            idx = _to_camel(index)
            self._line(f"for (int {idx} = 0; {idx} < {iter_expr}.size(); {idx}++) {{")
            self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        else:
            self._line(f"for (var _item : {iter_expr}) {{")
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
                java_type = self._type(typ)
                var_name = _to_camel(name)
                if value:
                    return f"{java_type} {var_name} = {self._expr(value)}"
                return f"{java_type} {var_name}"
            case Assign(target=target, value=value):
                # Check for i = i + 1 pattern and convert to i++
                if isinstance(value, BinaryOp) and value.op == "+":
                    if isinstance(value.right, IntLit) and value.right.value == 1:
                        if isinstance(target, VarLV) and isinstance(value.left, Var):
                            if target.name == value.left.name:
                                return f"{_to_camel(target.name)}++"
                return f"{self._lvalue(target)} = {self._expr(value)}"
            case OpAssign(target=target, op=op, value=value):
                return f"{self._lvalue(target)} {op}= {self._expr(value)}"
            case _:
                return ""

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
        var = _to_camel(catch_var) if catch_var else "e"
        self._line(f"}} catch (Exception {var}) {{")
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
                    return "this"
                if name.isupper():
                    return f"Constants.{_to_screaming_snake(name)}"
                return _to_camel(name)
            case FieldAccess(obj=obj, field=field):
                return f"{self._expr(obj)}.{_to_camel(field)}"
            case Index(obj=obj, index=index):
                obj_str = self._expr(obj)
                idx_str = self._expr(index)
                # Use record field access for tuples
                if isinstance(obj.typ, Tuple):
                    if isinstance(index, IntLit):
                        return f"{obj_str}.f{index.value}()"
                    return f"{obj_str}.f{idx_str}()"
                # Use .get() for ArrayList, .charAt() for String
                if isinstance(obj.typ, Slice):
                    return f"{obj_str}.get({idx_str})"
                if isinstance(obj.typ, Primitive) and obj.typ.kind == "string":
                    return f"{obj_str}.charAt({idx_str})"
                if isinstance(obj.typ, Map):
                    return f"{obj_str}.get({idx_str})"
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
                java_op = _binary_op(op)
                # Detect len(x) > 0 -> !x.isEmpty(), len(x) == 0 -> x.isEmpty()
                if isinstance(left, Len) and isinstance(right, IntLit) and right.value == 0:
                    inner_str = self._expr(left.expr)
                    if java_op == ">" or java_op == "!=":
                        return f"!{inner_str}.isEmpty()"
                    if java_op == "==":
                        return f"{inner_str}.isEmpty()"
                    if java_op == "<=":
                        return f"{inner_str}.isEmpty()"
                left_str = self._expr(left)
                right_str = self._expr(right)
                # String comparison needs .equals()
                if java_op == "==" and _is_string_type(left.typ):
                    return f"{left_str}.equals({right_str})"
                if java_op == "!=" and _is_string_type(left.typ):
                    return f"!{left_str}.equals({right_str})"
                return f"({left_str} {java_op} {right_str})"
            case UnaryOp(op=op, operand=operand):
                return f"{op}{self._expr(operand)}"
            case Ternary(cond=cond, then_expr=then_expr, else_expr=else_expr):
                return f"({self._expr(cond)} ? {self._expr(then_expr)} : {self._expr(else_expr)})"
            case Cast(expr=inner, to_type=to_type):
                return self._cast(inner, to_type)
            case TypeAssert(expr=inner, asserted=asserted, safe=safe):
                type_name = self._type(asserted)
                return f"(({type_name}) {self._expr(inner)})"
            case IsType(expr=inner, tested_type=tested_type):
                type_name = self._type_name_for_check(tested_type)
                return f"({self._expr(inner)} instanceof {type_name})"
            case IsNil(expr=inner, negated=negated):
                if negated:
                    return f"({self._expr(inner)} != null)"
                return f"({self._expr(inner)} == null)"
            case Len(expr=inner):
                inner_str = self._expr(inner)
                if isinstance(inner.typ, Primitive) and inner.typ.kind == "string":
                    return f"{inner_str}.length()"
                if isinstance(inner.typ, Array):
                    return f"{inner_str}.length"
                return f"{inner_str}.size()"
            case MakeSlice(element_type=element_type, length=length, capacity=capacity):
                typ = self._type(element_type)
                if capacity:
                    cap = self._expr(capacity)
                    return f"new ArrayList<{_box_type(typ)}>({cap})"
                if length:
                    length_str = self._expr(length)
                    return f"new ArrayList<{_box_type(typ)}>({length_str})"
                return f"new ArrayList<{_box_type(typ)}>()"
            case MakeMap(key_type=key_type, value_type=value_type):
                kt = _box_type(self._type(key_type))
                vt = _box_type(self._type(value_type))
                return f"new HashMap<{kt}, {vt}>()"
            case SliceLit(elements=elements, element_type=element_type):
                if not elements:
                    typ = _box_type(self._type(element_type))
                    return f"new ArrayList<{typ}>()"
                elems = ", ".join(self._expr(e) for e in elements)
                typ = _box_type(self._type(element_type))
                return f"new ArrayList<{typ}>(Arrays.asList({elems}))"
            case MapLit(entries=entries, key_type=key_type, value_type=value_type):
                kt = _box_type(self._type(key_type))
                vt = _box_type(self._type(value_type))
                if not entries:
                    return f"new HashMap<{kt}, {vt}>()"
                # Java doesn't have map literals, use Map.of() or build manually
                pairs = ", ".join(
                    f"{self._expr(k)}, {self._expr(v)}" for k, v in entries
                )
                return f"new HashMap<{kt}, {vt}>(Map.of({pairs}))"
            case SetLit(elements=elements, element_type=element_type):
                et = _box_type(self._type(element_type))
                if not elements:
                    return f"new HashSet<{et}>()"
                elems = ", ".join(self._expr(e) for e in elements)
                return f"new HashSet<{et}>(Arrays.asList({elems}))"
            case StructLit(struct_name=struct_name, fields=fields):
                if not fields:
                    return f"new {struct_name}()"
                # Need to pass fields in constructor order - assume same order as defined
                args = ", ".join(self._expr(v) for v in fields.values())
                return f"new {struct_name}({args})"
            case TupleLit(elements=elements, typ=typ):
                record_name = self._tuple_record_name(typ)
                elems = ", ".join(self._expr(e) for e in elements)
                return f"new {record_name}({elems})"
            case StringConcat(parts=parts):
                return " + ".join(self._expr(p) for p in parts)
            case StringFormat(template=template, args=args):
                return self._format_string(template, args)
            case _:
                return f"null /* TODO: {type(expr).__name__} */"

    def _method_call(self, obj: Expr, method: str, args: list[Expr], receiver_type: Type) -> str:
        args_str = ", ".join(self._expr(a) for a in args)
        obj_str = self._expr(obj)
        # Handle slice methods
        if isinstance(receiver_type, Slice):
            if method == "append" and args:
                return f"{obj_str}.add({args_str})"
            if method == "pop" and not args:
                return f"{obj_str}.remove({obj_str}.size() - 1)"
            if method == "copy":
                return f"new ArrayList<>({obj_str})"
        # String methods
        if isinstance(receiver_type, Primitive) and receiver_type.kind == "string":
            if method == "startswith":
                return f"{obj_str}.startsWith({args_str})"
            if method == "endswith":
                return f"{obj_str}.endsWith({args_str})"
            if method == "find":
                return f"{obj_str}.indexOf({args_str})"
            if method == "replace":
                return f"{obj_str}.replace({args_str})"
            if method == "split":
                return f"Arrays.asList({obj_str}.split({args_str}))"
            if method == "join":
                return f"String.join({obj_str}, {args_str})"
            if method == "strip" or method == "trim":
                return f"{obj_str}.trim()"
            if method == "lower":
                return f"{obj_str}.toLowerCase()"
            if method == "upper":
                return f"{obj_str}.toUpperCase()"
        return f"{obj_str}.{_to_camel(method)}({args_str})"

    def _slice_expr(self, obj: Expr, low: Expr | None, high: Expr | None) -> str:
        obj_str = self._expr(obj)
        if isinstance(obj.typ, Primitive) and obj.typ.kind == "string":
            if low and high:
                return f"{obj_str}.substring({self._expr(low)}, {self._expr(high)})"
            elif low:
                return f"{obj_str}.substring({self._expr(low)})"
            elif high:
                return f"{obj_str}.substring(0, {self._expr(high)})"
            return obj_str
        # ArrayList subList
        if low and high:
            return f"new ArrayList<>({obj_str}.subList({self._expr(low)}, {self._expr(high)}))"
        elif low:
            return f"new ArrayList<>({obj_str}.subList({self._expr(low)}, {obj_str}.size()))"
        elif high:
            return f"new ArrayList<>({obj_str}.subList(0, {self._expr(high)}))"
        return f"new ArrayList<>({obj_str})"

    def _cast(self, inner: Expr, to_type: Type) -> str:
        inner_str = self._expr(inner)
        java_type = self._type(to_type)
        if isinstance(to_type, Primitive):
            if to_type.kind == "int":
                return f"(int) ({inner_str})"
            if to_type.kind == "float":
                return f"(double) ({inner_str})"
            if to_type.kind == "byte":
                return f"(byte) ({inner_str})"
            if to_type.kind == "string":
                return f"String.valueOf({inner_str})"
        return f"(({java_type}) {inner_str})"

    def _format_string(self, template: str, args: list[Expr]) -> str:
        import re
        # Convert {0}, {1}, etc. to %s
        result = re.sub(r'\{\d+\}', '%s', template)
        result = result.replace("%v", "%s")
        escaped = result.replace("\\", "\\\\").replace('"', '\\"')
        args_str = ", ".join(self._expr(a) for a in args)
        if args_str:
            return f'String.format("{escaped}", {args_str})'
        return f'"{escaped}"'

    def _lvalue(self, lv: LValue) -> str:
        match lv:
            case VarLV(name=name):
                if name == self.receiver_name:
                    return "this"
                return _to_camel(name)
            case FieldLV(obj=obj, field=field):
                return f"{self._expr(obj)}.{_to_camel(field)}"
            case IndexLV(obj=obj, index=index):
                obj_str = self._expr(obj)
                idx_str = self._expr(index)
                # Note: ArrayList assignment needs special handling in Assign
                return f"{obj_str}[{idx_str}]"
            case DerefLV(ptr=ptr):
                return self._expr(ptr)
            case _:
                return f"null /* lvalue: {type(lv).__name__} */"

    def _type(self, typ: Type) -> str:
        match typ:
            case Primitive(kind=kind):
                return _primitive_type(kind)
            case Slice(element=element):
                elem = _box_type(self._type(element))
                return f"List<{elem}>"
            case Array(element=element, size=size):
                return f"{self._type(element)}[]"
            case Map(key=key, value=value):
                kt = _box_type(self._type(key))
                vt = _box_type(self._type(value))
                return f"Map<{kt}, {vt}>"
            case Set(element=element):
                et = _box_type(self._type(element))
                return f"Set<{et}>"
            case Tuple(elements=elements):
                # Use generated record type
                return self._tuple_record_name(typ)
            case Pointer(target=target):
                return self._type(target)
            case Optional(inner=inner):
                return self._type(inner)
            case StructRef(name=name):
                return name
            case Interface(name=name):
                if name == "any":
                    return "Object"
                return name
            case Union(name=name, variants=variants):
                if name:
                    return name
                return "Object"
            case FuncType(params=params, ret=ret):
                # Java functional interfaces are complex - use Object for now
                return "Object"
            case StringSlice():
                return "String"
            case _:
                return "Object"

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

    def _element_type(self, typ: Type) -> str:
        match typ:
            case Slice(element=element):
                return self._type(element)
            case Array(element=element):
                return self._type(element)
            case _:
                return "Object"

    def _tuple_record_name(self, typ: Type) -> str:
        """Get the record name for a tuple type."""
        if isinstance(typ, Tuple):
            sig = tuple(self._type(t) for t in typ.elements)
            return self.tuple_records.get(sig, "Object[]")
        return "Object[]"

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
                elem = _box_type(self._type(typ.element))
                return f"new ArrayList<{elem}>()"
            case Optional():
                return "null"
            case _:
                return "null"


def _primitive_type(kind: str) -> str:
    match kind:
        case "string":
            return "String"
        case "int":
            return "int"
        case "float":
            return "double"
        case "bool":
            return "boolean"
        case "byte":
            return "byte"
        case "rune":
            return "char"
        case "void":
            return "void"
        case _:
            return "Object"


def _box_type(typ: str) -> str:
    """Convert primitive types to boxed types for generics."""
    match typ:
        case "int":
            return "Integer"
        case "double":
            return "Double"
        case "boolean":
            return "Boolean"
        case "byte":
            return "Byte"
        case "char":
            return "Character"
        case "long":
            return "Long"
        case "float":
            return "Float"
        case "short":
            return "Short"
        case _:
            return typ


def _binary_op(op: str) -> str:
    match op:
        case "&&":
            return "&&"
        case "||":
            return "||"
        case _:
            return op


def _is_string_type(typ: Type) -> bool:
    if isinstance(typ, Primitive) and typ.kind == "string":
        return True
    if isinstance(typ, StringSlice):
        return True
    return False


def _to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    if name.startswith("_"):
        name = name[1:]
    if "_" not in name:
        return name[0].lower() + name[1:] if name else name
    parts = name.split("_")
    return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])


def _to_pascal(name: str) -> str:
    """Convert snake_case to PascalCase."""
    if name.startswith("_"):
        name = name[1:]
    parts = name.split("_")
    return "".join(p.capitalize() for p in parts)


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
