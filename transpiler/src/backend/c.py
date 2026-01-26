"""C backend: IR → C code."""

from __future__ import annotations

from src.ir import (
    BOOL,
    VOID,
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
    Function,
    FuncType,
    If,
    Index,
    IndexLV,
    IntLit,
    Interface,
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


class CBackend:
    """Emit C code from IR."""

    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self.receiver_name: str | None = None
        self.current_struct: str = ""
        self.declared_vars: set[str] = set()
        self.structs: dict[str, Struct] = {}
        self.tuple_types: dict[tuple[str, ...], str] = {}  # (elem_types...) -> struct name
        self.tuple_counter = 0

    def emit(self, module: Module) -> str:
        self.indent = 0
        self.lines = []
        self.tuple_types = {}
        self.tuple_counter = 0
        self.structs = {s.name: s for s in module.structs}
        # Pre-scan to collect tuple types
        self._collect_tuple_types(module)
        self._emit_header(module)
        self._emit_forward_decls(module)
        self._emit_tuple_defs()
        self._emit_type_defs(module)
        self._emit_constants(module.constants)
        for struct in module.structs:
            self._emit_struct(struct)
        self._emit_prototypes(module)
        for func in module.functions:
            self._emit_function(func)
        for struct in module.structs:
            for method in struct.methods:
                self._emit_method(struct, method)
        return "\n".join(self.lines)

    def _line(self, text: str = "") -> None:
        if text:
            self.lines.append("    " * self.indent + text)
        else:
            self.lines.append("")

    def _collect_tuple_types(self, module: Module) -> None:
        """Pre-scan module to collect all tuple types used."""
        for func in module.functions:
            self._collect_tuple_from_type(func.ret)
            for p in func.params:
                self._collect_tuple_from_type(p.typ)
            for stmt in func.body:
                self._collect_tuple_from_stmt(stmt)
        for struct in module.structs:
            for method in struct.methods:
                self._collect_tuple_from_type(method.ret)
                for stmt in method.body:
                    self._collect_tuple_from_stmt(stmt)

    def _collect_tuple_from_type(self, typ: Type) -> None:
        if isinstance(typ, Tuple):
            self._register_tuple(typ)
        elif isinstance(typ, Slice):
            self._collect_tuple_from_type(typ.element)
        elif isinstance(typ, Optional):
            self._collect_tuple_from_type(typ.inner)

    def _collect_tuple_from_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDecl(typ=typ, value=value):
                self._collect_tuple_from_type(typ)
                if value:
                    self._collect_tuple_from_expr(value)
            case Assign(value=value):
                self._collect_tuple_from_expr(value)
            case Return(value=value):
                if value:
                    self._collect_tuple_from_expr(value)
            case If(then_body=then_body, else_body=else_body):
                for s in then_body:
                    self._collect_tuple_from_stmt(s)
                for s in else_body:
                    self._collect_tuple_from_stmt(s)
            case While(body=body):
                for s in body:
                    self._collect_tuple_from_stmt(s)
            case ForRange(body=body):
                for s in body:
                    self._collect_tuple_from_stmt(s)
            case ForClassic(body=body):
                for s in body:
                    self._collect_tuple_from_stmt(s)
            case Block(body=body):
                for s in body:
                    self._collect_tuple_from_stmt(s)
            case _:
                pass

    def _collect_tuple_from_expr(self, expr: Expr) -> None:
        if isinstance(expr, TupleLit):
            if isinstance(expr.typ, Tuple):
                self._register_tuple(expr.typ)
            for e in expr.elements:
                self._collect_tuple_from_expr(e)
        elif hasattr(expr, 'typ') and isinstance(expr.typ, Tuple):
            self._register_tuple(expr.typ)

    def _register_tuple(self, typ: Tuple) -> str:
        key = tuple(self._type(e) for e in typ.elements)
        if key not in self.tuple_types:
            self.tuple_counter += 1
            self.tuple_types[key] = f"Tuple{self.tuple_counter}"
        return self.tuple_types[key]

    def _emit_tuple_defs(self) -> None:
        if not self.tuple_types:
            return
        for elem_types, name in self.tuple_types.items():
            fields = "; ".join(f"{t} f{i}" for i, t in enumerate(elem_types))
            self._line(f"typedef struct {{ {fields}; }} {name};")
        self._line("")

    def _emit_header(self, module: Module) -> None:
        self._line("#include <stdio.h>")
        self._line("#include <stdlib.h>")
        self._line("#include <string.h>")
        self._line("#include <stdbool.h>")
        self._line("#include <stdint.h>")
        self._line("#include <stdarg.h>")
        self._line("")
        self._line("#define PARABLE_PANIC(msg) do { fprintf(stderr, \"panic: %s\\n\", msg); exit(1); } while(0)")
        self._line("")
        self._line("typedef struct { char* data; size_t len; size_t cap; } String;")
        self._line("")
        self._line("static String String_new(const char* s) {")
        self.indent += 1
        self._line("size_t len = s ? strlen(s) : 0;")
        self._line("String str = {malloc(len + 1), len, len + 1};")
        self._line("if (s) memcpy(str.data, s, len + 1);")
        self._line("else str.data[0] = '\\0';")
        self._line("return str;")
        self.indent -= 1
        self._line("}")
        self._line("")
        self._line("static String parable_strcat(String a, String b) {")
        self.indent += 1
        self._line("size_t len = a.len + b.len;")
        self._line("String str = {malloc(len + 1), len, len + 1};")
        self._line("memcpy(str.data, a.data, a.len);")
        self._line("memcpy(str.data + a.len, b.data, b.len + 1);")
        self._line("return str;")
        self.indent -= 1
        self._line("}")
        self._line("")
        self._line("static String parable_slice(String s, size_t start, size_t end) {")
        self.indent += 1
        self._line("if (start > s.len) start = s.len;")
        self._line("if (end > s.len) end = s.len;")
        self._line("if (start > end) start = end;")
        self._line("size_t len = end - start;")
        self._line("String str = {malloc(len + 1), len, len + 1};")
        self._line("memcpy(str.data, s.data + start, len);")
        self._line("str.data[len] = '\\0';")
        self._line("return str;")
        self.indent -= 1
        self._line("}")
        self._line("")
        self._line("static String parable_sprintf(const char* fmt, ...) {")
        self.indent += 1
        self._line("va_list args, args2;")
        self._line("va_start(args, fmt);")
        self._line("va_copy(args2, args);")
        self._line("int len = vsnprintf(NULL, 0, fmt, args);")
        self._line("va_end(args);")
        self._line("String str = {malloc(len + 1), len, len + 1};")
        self._line("vsnprintf(str.data, len + 1, fmt, args2);")
        self._line("va_end(args2);")
        self._line("return str;")
        self.indent -= 1
        self._line("}")
        self._line("")
        self._line("#define SLICE_DEF(T, NAME) \\")
        self._line("typedef struct { T* data; size_t len; size_t cap; } NAME; \\")
        self._line("static NAME NAME##_new(size_t cap) { \\")
        self._line("    NAME s = {malloc(sizeof(T) * (cap ? cap : 1)), 0, cap ? cap : 1}; return s; } \\")
        self._line("static void NAME##_append(NAME* s, T val) { \\")
        self._line("    if (s->len >= s->cap) { s->cap = s->cap ? s->cap * 2 : 1; \\")
        self._line("    s->data = realloc(s->data, sizeof(T) * s->cap); } s->data[s->len++] = val; }")
        self._line("")
        self._line("SLICE_DEF(int, IntSlice)")
        self._line("SLICE_DEF(bool, BoolSlice)")
        self._line("SLICE_DEF(double, FloatSlice)")
        self._line("SLICE_DEF(String, StringSlice)")
        self._line("")

    def _emit_forward_decls(self, module: Module) -> None:
        if not module.structs:
            return
        for struct in module.structs:
            self._line(f"typedef struct {struct.name} {struct.name};")
        self._line("")

    def _emit_type_defs(self, module: Module) -> None:
        for struct in module.structs:
            self._line(f"SLICE_DEF({struct.name}*, {struct.name}Slice)")
        if module.structs:
            self._line("")

    def _emit_constants(self, constants: list[Constant]) -> None:
        if not constants:
            return
        for const in constants:
            c_type = self._type(const.typ)
            value = self._expr(const.value)
            if isinstance(const.typ, Primitive) and const.typ.kind == "string":
                self._line(f"static const char* {const.name} = {value};")
            else:
                self._line(f"static const {c_type} {const.name} = {value};")
        self._line("")

    def _emit_struct(self, struct: Struct) -> None:
        self._line(f"struct {struct.name} {{")
        self.indent += 1
        for field in struct.fields:
            self._line(f"{self._type(field.typ)} {field.name};")
        self.indent -= 1
        self._line("};")
        self._line("")

    def _emit_prototypes(self, module: Module) -> None:
        protos = []
        for func in module.functions:
            protos.append(self._prototype(func, None))
        for struct in module.structs:
            for method in struct.methods:
                protos.append(self._prototype(method, struct))
        if protos:
            for proto in protos:
                self._line(f"{proto};")
            self._line("")

    def _prototype(self, func: Function, struct: Struct | None) -> str:
        ret = self._type(func.ret) if func.ret != VOID else "void"
        params = []
        if struct:
            name = f"{struct.name}_{func.name}"
            params.append(f"{struct.name}* self")
        else:
            name = func.name
        for p in func.params:
            params.append(f"{self._type(p.typ)} {p.name}")
        return f"{ret} {name}({', '.join(params) if params else 'void'})"

    def _emit_function(self, func: Function) -> None:
        self.declared_vars = set(p.name for p in func.params)
        self.receiver_name = None
        ret = self._type(func.ret) if func.ret != VOID else "void"
        params = [f"{self._type(p.typ)} {p.name}" for p in func.params]
        self._line(f"{ret} {func.name}({', '.join(params) if params else 'void'}) {{")
        self.indent += 1
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")
        self._line("")

    def _emit_method(self, struct: Struct, func: Function) -> None:
        self.declared_vars = {"self"} | set(p.name for p in func.params)
        self.receiver_name = "self"
        self.current_struct = struct.name
        ret = self._type(func.ret) if func.ret != VOID else "void"
        params = [f"{struct.name}* self"] + [f"{self._type(p.typ)} {p.name}" for p in func.params]
        self._line(f"{ret} {struct.name}_{func.name}({', '.join(params)}) {{")
        self.indent += 1
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")
        self._line("")
        self.current_struct = ""

    def _emit_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDecl(name=name, typ=typ, value=value):
                self.declared_vars.add(name)
                if value:
                    self._line(f"{self._type(typ)} {name} = {self._expr(value)};")
                else:
                    self._line(f"{self._type(typ)} {name};")
            case Assign(target=target, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                if isinstance(target, VarLV) and target.name not in self.declared_vars:
                    self.declared_vars.add(target.name)
                    self._line(f"{self._type(value.typ)} {lv} = {val};")
                else:
                    self._line(f"{lv} = {val};")
            case OpAssign(target=target, op=op, value=value):
                self._line(f"{self._lvalue(target)} {op}= {self._expr(value)};")
            case ExprStmt(expr=expr):
                if isinstance(expr, MethodCall) and expr.method == "append":
                    obj = self._expr(expr.obj)
                    st = self._slice_type(expr.receiver_type)
                    self._line(f"{st}_append(&{obj}, {self._expr(expr.args[0])});")
                else:
                    self._line(f"{self._expr(expr)};")
            case Return(value=value):
                self._line(f"return {self._expr(value)};" if value else "return;")
            case If(cond=cond, then_body=then_body, else_body=else_body):
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
            case While(cond=cond, body=body):
                self._line(f"while ({self._expr(cond)}) {{")
                self.indent += 1
                for s in body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("}")
            case ForRange(index=index, value=value, iterable=iterable, body=body):
                actual = iterable.args[0] if isinstance(iterable, Call) and iterable.func == "enumerate" else iterable
                it = self._expr(actual)
                idx = index or "_i"
                self._line(f"for (size_t {idx} = 0; {idx} < {it}.len; {idx}++) {{")
                self.indent += 1
                if value:
                    self._line(f"{self._elem_type(actual.typ)} {value} = {it}.data[{idx}];")
                for s in body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("}")
            case ForClassic(init=init, cond=cond, post=post, body=body):
                init_s = self._stmt_inline(init) if init else ""
                cond_s = self._expr(cond) if cond else ""
                post_s = self._stmt_inline(post) if post else ""
                self._line(f"for ({init_s}; {cond_s}; {post_s}) {{")
                self.indent += 1
                for s in body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("}")
            case Break():
                self._line("break;")
            case Continue():
                self._line("continue;")
            case Block(body=body):
                self._line("{")
                self.indent += 1
                for s in body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("}")
            case Match(expr=expr, cases=cases, default=default):
                self._line(f"switch ({self._expr(expr)}) {{")
                for case in cases:
                    for p in case.patterns:
                        self._line(f"case {self._expr(p)}:")
                    self.indent += 1
                    for s in case.body:
                        self._emit_stmt(s)
                    self._line("break;")
                    self.indent -= 1
                if default:
                    self._line("default:")
                    self.indent += 1
                    for s in default:
                        self._emit_stmt(s)
                    self._line("break;")
                    self.indent -= 1
                self._line("}")
            case TryCatch(body=body, catch_body=catch_body):
                self._line("/* try */")
                for s in body:
                    self._emit_stmt(s)
                if catch_body:
                    self._line("/* catch (not supported) */")
            case Raise(message=message):
                self._line(f"PARABLE_PANIC({self._expr(message)});")
            case SoftFail():
                self._line("return NULL;")
            case _:
                self._line(f"/* TODO: {type(stmt).__name__} */")

    def _stmt_inline(self, stmt: Stmt) -> str:
        match stmt:
            case VarDecl(name=name, typ=typ, value=value):
                self.declared_vars.add(name)
                return f"{self._type(typ)} {name} = {self._expr(value)}" if value else f"{self._type(typ)} {name}"
            case Assign(target=target, value=value):
                return f"{self._lvalue(target)} = {self._expr(value)}"
            case OpAssign(target=target, op=op, value=value):
                return f"{self._lvalue(target)} {op}= {self._expr(value)}"
        return ""

    def _expr(self, expr: Expr) -> str:
        match expr:
            case IntLit(value=v):
                return str(v)
            case FloatLit(value=v):
                return str(v)
            case StringLit(value=v):
                escaped = v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
                return f'"{escaped}"'
            case BoolLit(value=v):
                return "true" if v else "false"
            case NilLit():
                return "NULL"
            case Var(name=name):
                return "self" if name == self.receiver_name else name
            case FieldAccess(obj=obj, field=field, through_pointer=ptr):
                op = "->" if ptr or self._is_ptr(obj) else "."
                return f"{self._expr(obj)}{op}{field}"
            case Index(obj=obj, index=index):
                o, i = self._expr(obj), self._expr(index)
                # Tuple indexing: access .f0, .f1, etc.
                if isinstance(obj.typ, Tuple) and isinstance(index, IntLit):
                    return f"{o}.f{index.value}"
                if isinstance(obj.typ, Slice) or (isinstance(obj.typ, Primitive) and obj.typ.kind == "string"):
                    return f"{o}.data[{i}]"
                return f"{o}[{i}]"
            case SliceExpr(obj=obj, low=low, high=high):
                o = self._expr(obj)
                l = self._expr(low) if low else "0"
                h = self._expr(high) if high else f"{o}.len"
                return f"parable_slice({o}, {l}, {h})"
            case Call(func=func, args=args):
                return f"{func}({', '.join(self._expr(a) for a in args)})"
            case MethodCall(obj=obj, method=method, args=args, receiver_type=rt):
                if isinstance(rt, Slice) and method == "append":
                    return "/* append */"
                recv = self._type_name(rt) or self.current_struct
                args_s = ", ".join(self._expr(a) for a in args)
                ptr = "" if self._is_ptr(obj) else "&"
                return f"{recv}_{method}({ptr}{self._expr(obj)}{', ' + args_s if args_s else ''})"
            case StaticCall(on_type=t, method=m, args=args):
                return f"{self._type_name(t)}_{m}({', '.join(self._expr(a) for a in args)})"
            case BinaryOp(op=op, left=left, right=right):
                l, r = self._expr(left), self._expr(right)
                if self._is_str(left.typ) or self._is_str(right.typ) or isinstance(left, StringLit) or isinstance(right, StringLit):
                    ld = l if isinstance(left, StringLit) else f"{l}.data"
                    rd = r if isinstance(right, StringLit) else f"{r}.data"
                    if op == "==":
                        return f"(strcmp({ld}, {rd}) == 0)"
                    if op == "!=":
                        return f"(strcmp({ld}, {rd}) != 0)"
                op = {"and": "&&", "or": "||", "&&": "&&", "||": "||"}.get(op, op)
                return f"({l} {op} {r})"
            case UnaryOp(op=op, operand=operand):
                op = "!" if op == "not" else op
                return f"{op}{self._expr(operand)}"
            case Ternary(cond=cond, then_expr=then_expr, else_expr=else_expr):
                return f"({self._expr(cond)} ? {self._expr(then_expr)} : {self._expr(else_expr)})"
            case Cast(expr=inner, to_type=to_type):
                return f"(({self._type(to_type)}){self._expr(inner)})"
            case IsNil(expr=inner, negated=neg):
                return f"({self._expr(inner)} {'!=' if neg else '=='} NULL)"
            case Len(expr=inner):
                return f"{self._expr(inner)}.len"
            case MakeSlice(element_type=et, length=length):
                return f"{self._slice_type_elem(et)}_new({self._expr(length) if length else '0'})"
            case MakeMap():
                return "/* MakeMap */"
            case SliceLit(elements=elements, element_type=et):
                st = self._slice_type_elem(et)
                if not elements:
                    return f"{st}_new(0)"
                ct = self._type(et)
                elems = ", ".join(self._expr(e) for e in elements)
                return f"(({st}){{({ct}[]){{{elems}}}, {len(elements)}, {len(elements)}}})"
            case MapLit(entries=entries):
                return f"/* MapLit({len(entries)}) */"
            case SetLit(elements=elements):
                return f"/* SetLit({len(elements)}) */"
            case StructLit(struct_name=name, fields=fields):
                fs = ", ".join(f".{k} = {self._expr(v)}" for k, v in fields.items())
                return f"(&({name}){{{fs}}})"
            case TupleLit(elements=elements):
                if isinstance(expr.typ, Tuple):
                    tup_name = self._type(expr.typ)
                    fields = ", ".join(f".f{i} = {self._expr(e)}" for i, e in enumerate(elements))
                    return f"({tup_name}){{{fields}}}"
                # Fallback
                elems = ", ".join(self._expr(e) for e in elements)
                return f"/* tuple */({elems})"
            case StringConcat(parts=parts):
                if not parts:
                    return 'String_new("")'
                if len(parts) == 1:
                    return self._expr(parts[0])
                # Build concatenation using parable_strcat
                result = self._expr(parts[0])
                for p in parts[1:]:
                    result = f"parable_strcat({result}, {self._expr(p)})"
                return result
            case StringFormat(template=template, args=args):
                # Convert {0}, {1} to %s, %d, etc.
                fmt = template
                specs = []
                for i, arg in enumerate(args):
                    spec = self._format_spec(arg.typ) if hasattr(arg, "typ") else "%s"
                    fmt = fmt.replace(f"{{{i}}}", spec, 1)
                    # For strings, pass .data; for other types pass the value
                    if hasattr(arg, "typ") and self._is_str(arg.typ):
                        specs.append(f"{self._expr(arg)}.data")
                    else:
                        specs.append(self._expr(arg))
                escaped = fmt.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
                args_str = ", ".join(specs)
                return f'parable_sprintf("{escaped}", {args_str})' if args_str else f'String_new("{escaped}")'
            case _:
                return f"/* TODO: {type(expr).__name__} */"

    def _lvalue(self, lv: LValue) -> str:
        match lv:
            case VarLV(name=name):
                return "self" if name == self.receiver_name else name
            case FieldLV(obj=obj, field=field):
                op = "->" if self._is_ptr(obj) else "."
                return f"{self._expr(obj)}{op}{field}"
            case IndexLV(obj=obj, index=index):
                o = self._expr(obj)
                if isinstance(obj.typ, Slice):
                    return f"{o}.data[{self._expr(index)}]"
                return f"{o}[{self._expr(index)}]"
            case DerefLV(ptr=ptr):
                return f"*{self._expr(ptr)}"
        return "/* lvalue */"

    def _type(self, typ: Type) -> str:
        match typ:
            case Primitive(kind=k):
                return {"string": "String", "int": "int", "bool": "bool", "float": "double", "byte": "char", "rune": "int32_t", "void": "void"}.get(k, "void*")
            case Slice(element=e):
                return self._slice_type_elem(e)
            case Array(element=e, size=s):
                return f"{self._type(e)}[{s}]"
            case Pointer(target=t):
                return f"{self._type(t)}*"
            case Optional(inner=i):
                inner = self._type(i)
                return inner if "*" in inner else f"{inner}*"
            case StructRef(name=n):
                return f"{n}*"
            case Interface() | Map() | Union():
                return "void*"
            case Tuple(elements=elements):
                key = tuple(self._type(e) for e in elements)
                if key in self.tuple_types:
                    return self.tuple_types[key]
                # Fallback: register on the fly
                return self._register_tuple(typ)
            case StringSlice():
                return "String"
        return "void*"

    def _slice_type(self, typ: Type) -> str:
        return self._slice_type_elem(typ.element) if isinstance(typ, Slice) else "Slice"

    def _slice_type_elem(self, elem: Type) -> str:
        if isinstance(elem, Primitive):
            return {"int": "IntSlice", "bool": "BoolSlice", "float": "FloatSlice", "string": "StringSlice"}.get(elem.kind, "Slice")
        if isinstance(elem, StructRef):
            return f"{elem.name}Slice"
        return "Slice"

    def _elem_type(self, typ: Type) -> str:
        if isinstance(typ, Slice):
            return self._type(typ.element)
        if isinstance(typ, Array):
            return self._type(typ.element)
        return "int"

    def _type_name(self, typ: Type) -> str:
        if isinstance(typ, StructRef):
            return typ.name
        if isinstance(typ, Pointer) and isinstance(typ.target, StructRef):
            return typ.target.name
        return ""

    def _is_ptr(self, expr: Expr) -> bool:
        if isinstance(expr, Var) and expr.name == "self":
            return True
        return isinstance(expr.typ, (Pointer, StructRef, Optional))

    def _is_str(self, typ: Type) -> bool:
        return isinstance(typ, Primitive) and typ.kind == "string"

    def _format_spec(self, typ: Type) -> str:
        """Get printf format specifier for a type."""
        if isinstance(typ, Primitive):
            return {"string": "%s", "int": "%d", "bool": "%d", "float": "%f", "byte": "%c", "rune": "%c"}.get(typ.kind, "%s")
        return "%s"
