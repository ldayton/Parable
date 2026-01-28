"""Java backend: IR → Java code."""

from __future__ import annotations

from src.backend.util import escape_string, to_camel, to_pascal, to_screaming_snake

# Java reserved words that need escaping
_JAVA_RESERVED = frozenset({
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "final", "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native", "new",
    "package", "private", "protected", "public", "return", "short", "static",
    "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
    "transient", "try", "void", "volatile", "while", "true", "false", "null",
})

# Java standard library classes that conflict with user-defined types
_JAVA_STDLIB_CLASSES = frozenset({
    "List", "Map", "Set", "String", "Integer", "Boolean", "Double", "Float",
    "Long", "Short", "Byte", "Character", "Object", "Class", "System",
    "Runtime", "Thread", "Exception", "Error", "Throwable", "Optional",
})


def _java_safe_name(name: str) -> str:
    """Escape Java reserved words by appending underscore."""
    result = to_camel(name)
    if result in _JAVA_RESERVED:
        return result + "_"
    return result


def _java_safe_class(name: str) -> str:
    """Escape class names that conflict with Java stdlib."""
    if name in _JAVA_STDLIB_CLASSES:
        return name + "Node"
    return name
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


class JavaBackend:
    """Emit Java code from IR."""

    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self.receiver_name: str | None = None
        self.current_class: str = ""
        self.tuple_records: dict[tuple, str] = {}  # tuple signature -> record name
        self.tuple_counter = 0
        self.optional_tuples: set[tuple] = set()  # (T, bool) patterns -> use Optional<T>
        self.struct_fields: dict[str, list[tuple[str, Type]]] = {}  # struct name -> [(field_name, type)]
        self.temp_counter: int = 0  # for unique temp variable names

    def emit(self, module: Module) -> str:
        """Emit Java code from IR Module."""
        self.indent = 0
        self.lines = []
        self.tuple_records = {}
        self.tuple_counter = 0
        self.optional_tuples = set()
        self.struct_fields = {}
        self.temp_counter = 0
        self._module_name = module.name
        self._collect_struct_fields(module)
        self._collect_tuple_types(module)
        self._emit_module(module)
        return "\n".join(self.lines)

    def _collect_struct_fields(self, module: Module) -> None:
        """Collect field information for all structs."""
        for struct in module.structs:
            self.struct_fields[struct.name] = [(f.name, f.typ) for f in struct.fields]

    def _collect_tuple_types(self, module: Module) -> None:
        """Collect all unique tuple types used in the module."""
        def visit_type(typ: Type) -> None:
            if isinstance(typ, Tuple):
                sig = tuple(self._type(t) for t in typ.elements)
                # Detect (T, bool) pattern - use Optional<T> instead of synthetic record
                # But NOT for (bool, bool) - that's just a two-bool tuple
                if (len(typ.elements) == 2
                    and isinstance(typ.elements[1], Primitive)
                    and typ.elements[1].kind == "bool"
                    and not (isinstance(typ.elements[0], Primitive) and typ.elements[0].kind == "bool")):
                    self.optional_tuples.add(sig)
                elif sig not in self.tuple_records:
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
        name = to_screaming_snake(const.name)
        self._line(f"public static final {typ} {name} = {val};")

    def _emit_interface(self, iface: InterfaceDef) -> None:
        self._line(f"interface {iface.name} {{")
        self.indent += 1
        for method in iface.methods:
            params = self._params(method.params)
            ret = self._type(method.ret)
            name = to_camel(method.name)
            self._line(f"{ret} {name}({params});")
        self.indent -= 1
        self._line("}")

    def _emit_struct(self, struct: Struct) -> None:
        class_name = _java_safe_class(struct.name)
        self.current_class = class_name
        implements_clause = ""
        if struct.implements:
            impl_names = [_java_safe_class(n) for n in struct.implements]
            implements_clause = f" implements {', '.join(impl_names)}"
        self._line(f"class {class_name}{implements_clause} {{")
        self.indent += 1
        for fld in struct.fields:
            self._emit_field(fld)
        if struct.fields:
            self._line("")
        # Default constructor
        self._emit_default_constructor(struct)
        self._line("")
        # Generate getters for interface methods that map to fields
        # e.g., if interface requires getKind() and struct has kind field
        field_names = {f.name for f in struct.fields}
        method_names = {m.name for m in struct.methods}
        if "Node" in struct.implements and "kind" in field_names and "GetKind" not in method_names:
            self._line("public String getKind() { return this.kind; }")
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
        class_name = _java_safe_class(struct.name)
        params = ", ".join(
            f"{self._type(f.typ)} {_java_safe_name(f.name)}" for f in struct.fields
        )
        self._line(f"{class_name}({params}) {{")
        self.indent += 1
        for f in struct.fields:
            name = _java_safe_name(f.name)
            self._line(f"this.{name} = {name};")
        self.indent -= 1
        self._line("}")

    def _emit_field(self, fld: Field) -> None:
        typ = self._type(fld.typ)
        self._line(f"{typ} {_java_safe_name(fld.name)};")

    def _emit_functions_class(self, module: Module) -> None:
        """Emit free functions as static methods in a utility class."""
        self._line(f"final class {to_pascal(module.name)}Functions {{")
        self.indent += 1
        self._line(f"private {to_pascal(module.name)}Functions() {{}}")
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
        name = to_camel(func.name)
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
        name = to_camel(func.name)
        if func.receiver:
            self.receiver_name = func.receiver.name
        # Use public for interface implementation compatibility
        self._line(f"public {ret} {name}({params}) {{")
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
            parts.append(f"{typ} {_java_safe_name(p.name)}")
        return ", ".join(parts)

    def _emit_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDecl(name=name, typ=typ, value=value, mutable=mutable):
                java_type = self._type(typ)
                var_name = _java_safe_name(name)
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
                    if getattr(stmt, 'is_declaration', False):
                        # First assignment to variable - need type declaration
                        value_type = getattr(value, 'typ', None)
                        if value_type:
                            java_type = self._type(value_type)
                            self._line(f"{java_type} {lv} = {val};")
                        else:
                            # Fallback to Object if type unknown
                            self._line(f"Object {lv} = {val};")
                    else:
                        self._line(f"{lv} = {val};")
            case OpAssign(target=target, op=op, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                self._line(f"{lv} {op}= {val};")
            case TupleAssign(targets=targets, value=value):
                # Java doesn't have destructuring - emit individual assignments
                val_str = self._expr(value)
                value_type = getattr(value, 'typ', None)
                is_decl = getattr(stmt, 'is_declaration', False)
                new_targets = getattr(stmt, 'new_targets', [])
                # For tuple types, access fields with .f0(), .f1(), etc.
                if isinstance(value_type, Tuple):
                    # Store tuple in temp variable if it's a complex expression
                    if not isinstance(value, Var):
                        self.temp_counter += 1
                        temp_name = f"_tuple{self.temp_counter}"
                        record_name = self._tuple_record_name(value_type)
                        self._line(f"{record_name} {temp_name} = {val_str};")
                        val_str = temp_name
                    for i, target in enumerate(targets):
                        lv = self._lvalue(target)
                        target_name = target.name if isinstance(target, VarLV) else None
                        if is_decl or (target_name and target_name in new_targets):
                            elem_type = self._type(value_type.elements[i]) if i < len(value_type.elements) else "Object"
                            self._line(f"{elem_type} {lv} = {val_str}.f{i}();")
                        else:
                            self._line(f"{lv} = {val_str}.f{i}();")
                else:
                    # Fallback: treat as array index
                    for i, target in enumerate(targets):
                        lv = self._lvalue(target)
                        target_name = target.name if isinstance(target, VarLV) else None
                        if is_decl or (target_name and target_name in new_targets):
                            self._line(f"Object {lv} = {val_str}[{i}];")
                        else:
                            self._line(f"{lv} = {val_str}[{i}];")
            case ExprStmt(expr=Var(name=name)) if name in (
                "_skip_docstring", "_pass", "_skip_super_init"
            ):
                pass  # Skip marker statements
            case ExprStmt(expr=expr):
                e = self._expr(expr)
                self._line(f"{e};")
            case Return(value=value):
                if value is not None:
                    if isinstance(value, TupleLit):
                        # Check if this is an optional tuple (T, bool)
                        if self._is_optional_tuple(value.typ):
                            self._line(f"return {self._emit_optional_tuple(value)};")
                        else:
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
        bind_name = _java_safe_name(binding)
        # Don't re-declare if binding to same variable
        if not (isinstance(expr, Var) and _java_safe_name(expr.name) == bind_name):
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
            idx = _java_safe_name(index)
            val = _java_safe_name(value)
            self._line(f"for (int {idx} = 0; {idx} < {iter_expr}.size(); {idx}++) {{")
            self.indent += 1
            elem_type = self._element_type(iterable.typ)
            self._line(f"{elem_type} {val} = {iter_expr}.get({idx});")
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        elif value is not None:
            val = _java_safe_name(value)
            elem_type = self._element_type(iterable.typ)
            self._line(f"for ({elem_type} {val} : {iter_expr}) {{")
            self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        elif index is not None:
            idx = _java_safe_name(index)
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
                var_name = _java_safe_name(name)
                if value:
                    return f"{java_type} {var_name} = {self._expr(value)}"
                return f"{java_type} {var_name}"
            case Assign(target=target, value=value):
                # Check for i = i + 1 pattern and convert to i++
                if isinstance(value, BinaryOp) and value.op == "+":
                    if isinstance(value.right, IntLit) and value.right.value == 1:
                        if isinstance(target, VarLV) and isinstance(value.left, Var):
                            if target.name == value.left.name:
                                return f"{_java_safe_name(target.name)}++"
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
        var = _java_safe_name(catch_var) if catch_var else "e"
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
                # Check if this is a constant (all uppercase, or ClassName_CONSTANT pattern)
                if name.isupper() or (name[0].isupper() and "_" in name and name.split("_", 1)[1].isupper()):
                    return f"Constants.{to_screaming_snake(name)}"
                return _java_safe_name(name)
            case FieldAccess(obj=obj, field=field):
                obj_str = self._expr(obj)
                # Tuple record fields are accessed as methods in Java records
                # Field names F0/f0, F1/f1, etc. are tuple field accessors - use method syntax
                lower_field = field.lower()
                if lower_field.startswith("f") and len(lower_field) > 1 and lower_field[1:].isdigit():
                    return f"{obj_str}.{lower_field}()"
                return f"{obj_str}.{_java_safe_name(field)}"
            case Index(obj=obj, index=index):
                obj_str = self._expr(obj)
                idx_str = self._expr(index)
                # Use Optional methods for (T, bool) tuples
                if isinstance(obj.typ, Tuple) and self._is_optional_tuple(obj.typ):
                    if isinstance(index, IntLit):
                        if index.value == 0:
                            return f"{obj_str}.get()"
                        if index.value == 1:
                            return f"{obj_str}.isPresent()"
                    return f"{obj_str}.get()"  # fallback
                # Use record field access for other tuples
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
                # Handle built-in functions
                if func == "int" and len(args) == 2:
                    # int(s, base) -> Integer.parseInt(s, base)
                    return f"Integer.parseInt({args_str})"
                if func == "_parseInt":
                    # Frontend generates _parseInt for int(s, base)
                    return f"Integer.parseInt({args_str})"
                if func == "str":
                    return f"String.valueOf({args_str})"
                if func == "len":
                    arg = self._expr(args[0])
                    arg_type = getattr(args[0], 'typ', None)
                    if isinstance(arg_type, Primitive) and arg_type.kind == "string":
                        return f"{arg}.length()"
                    return f"{arg}.size()"
                if func == "range":
                    # Return an IntStream or List<Integer>
                    if len(args) == 1:
                        return f"java.util.stream.IntStream.range(0, {self._expr(args[0])}).boxed().toList()"
                    elif len(args) == 2:
                        return f"java.util.stream.IntStream.range({self._expr(args[0])}, {self._expr(args[1])}).boxed().toList()"
                    else:  # 3 args: start, stop, step
                        start = self._expr(args[0])
                        stop = self._expr(args[1])
                        step = self._expr(args[2])
                        return f"java.util.stream.IntStream.iterate({start}, i -> i < {stop}, i -> i + {step}).boxed().toList()"
                if func == "ord":
                    return f"(int) ({self._expr(args[0])}.charAt(0))"
                if func == "chr":
                    return f"String.valueOf((char) ({self._expr(args[0])}))"
                if func == "abs":
                    return f"Math.abs({args_str})"
                if func == "min":
                    return f"Math.min({args_str})"
                if func == "max":
                    return f"Math.max({args_str})"
                # Module-level functions are in {ModuleName}Functions class
                func_class = f"{to_pascal(self._module_name)}Functions"
                return f"{func_class}.{to_camel(func)}({args_str})"
            case MethodCall(obj=obj, method=method, args=[TupleLit(elements=elements)], receiver_type=_) if method in ("startswith", "endswith"):
                # Python str.startswith/endswith with tuple → disjunction of checks
                java_method = "startsWith" if method == "startswith" else "endsWith"
                obj_str = self._expr(obj)
                checks = [f"{obj_str}.{java_method}({self._expr(e)})" for e in elements]
                return f"({' || '.join(checks)})"
            case MethodCall(obj=obj, method=method, args=args, receiver_type=receiver_type):
                return self._method_call(obj, method, args, receiver_type)
            case StaticCall(on_type=on_type, method=method, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                type_name = self._type_name_for_check(on_type)
                return f"{type_name}.{to_camel(method)}({args_str})"
            case BinaryOp(op="in", left=left, right=right):
                return self._containment_check(left, right, negated=False)
            case BinaryOp(op="not in", left=left, right=right):
                return self._containment_check(left, right, negated=True)
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
                # Bitwise operators need parens due to low precedence
                if java_op in ("&", "|", "^"):
                    return f"({left_str} {java_op} {right_str})"
                return f"{left_str} {java_op} {right_str}"
            case UnaryOp(op="&", operand=operand):
                return self._expr(operand)  # Java passes objects by reference
            case UnaryOp(op="*", operand=operand):
                return self._expr(operand)  # Java has no pointer dereference
            case UnaryOp(op="!", operand=operand):
                # Java ! only works on booleans; for ints, use == 0
                operand_type = getattr(operand, 'typ', None)
                if isinstance(operand_type, Primitive) and operand_type.kind == "int":
                    return f"({self._expr(operand)} == 0)"
                # Check for bitwise & operand (result is int even if typ not set)
                if isinstance(operand, BinaryOp) and operand.op == "&":
                    return f"({self._expr(operand)} == 0)"
                # Check for addition/subtraction (e.g., !pos + 1) - result is int
                if isinstance(operand, BinaryOp) and operand.op in ("+", "-", "*", "/", "%"):
                    return f"({self._expr(operand)} == 0)"
                return f"!{self._expr(operand)}"
            case UnaryOp(op=op, operand=operand):
                return f"{op}{self._expr(operand)}"
            case Ternary(cond=cond, then_expr=then_expr, else_expr=else_expr):
                return f"{self._expr(cond)} ? {self._expr(then_expr)} : {self._expr(else_expr)}"
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
                    return f"{self._expr(inner)} != null"
                return f"{self._expr(inner)} == null"
            case Len(expr=inner):
                inner_str = self._expr(inner)
                if isinstance(inner.typ, Primitive) and inner.typ.kind == "string":
                    return f"{inner_str}.length()"
                if isinstance(inner.typ, Array):
                    return f"{inner_str}.length"
                return f"{inner_str}.size()"
            case MakeSlice(element_type=element_type, length=length, capacity=capacity):
                if capacity:
                    cap = self._expr(capacity)
                    return f"new ArrayList<>({cap})"
                if length:
                    length_str = self._expr(length)
                    return f"new ArrayList<>({length_str})"
                return "new ArrayList<>()"
            case MakeMap(key_type=key_type, value_type=value_type):
                return "new HashMap<>()"
            case SliceLit(elements=elements, element_type=element_type):
                if not elements:
                    return "new ArrayList<>()"
                elems = ", ".join(self._expr(e) for e in elements)
                return f"new ArrayList<>(List.of({elems}))"
            case MapLit(entries=entries, key_type=key_type, value_type=value_type):
                if not entries:
                    return "new HashMap<>()"
                # Map.of() only supports up to 10 entries; use ofEntries for more
                if len(entries) <= 10:
                    pairs = ", ".join(
                        f"{self._expr(k)}, {self._expr(v)}" for k, v in entries
                    )
                    return f"new HashMap<>(Map.of({pairs}))"
                else:
                    entries_str = ", ".join(
                        f"Map.entry({self._expr(k)}, {self._expr(v)})" for k, v in entries
                    )
                    return f"new HashMap<>(Map.ofEntries({entries_str}))"
            case SetLit(elements=elements, element_type=element_type):
                if not elements:
                    return "new HashSet<>()"
                elems = ", ".join(self._expr(e) for e in elements)
                return f"new HashSet<>(Set.of({elems}))"
            case StructLit(struct_name=struct_name, fields=fields):
                safe_name = _java_safe_class(struct_name)
                # Use struct field order, fill in missing fields with defaults
                field_info = self.struct_fields.get(struct_name, [])
                if field_info:
                    ordered_args = []
                    for field_name, field_type in field_info:
                        if field_name in fields:
                            ordered_args.append(self._expr(fields[field_name]))
                        else:
                            ordered_args.append(self._default_value(field_type))
                    return f"new {safe_name}({', '.join(ordered_args)})"
                elif not fields:
                    return f"new {safe_name}()"
                else:
                    args = ", ".join(self._expr(v) for v in fields.values())
                    return f"new {safe_name}({args})"
            case TupleLit(elements=elements, typ=typ):
                if self._is_optional_tuple(typ):
                    return self._emit_optional_tuple(expr)
                record_name = self._tuple_record_name(typ)
                elems = ", ".join(self._expr(e) for e in elements)
                # Fallback to Object[] uses array literal syntax
                if record_name == "Object[]":
                    return f"new Object[]{{{elems}}}"
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
            if method == "rfind":
                return f"{obj_str}.lastIndexOf({args_str})"
            if method == "replace":
                return f"{obj_str}.replace({args_str})"
            if method == "split":
                return f"Arrays.asList({obj_str}.split({args_str}))"
            if method == "join":
                return f"String.join({obj_str}, {args_str})"
            if method == "strip" or method == "trim":
                return f"{obj_str}.trim()"
            if method == "lstrip":
                if args:
                    # lstrip with chars argument - use regex
                    return f"{obj_str}.replaceFirst(\"^[\" + {args_str} + \"]+\", \"\")"
                return f"{obj_str}.stripLeading()"
            if method == "rstrip":
                if args:
                    # rstrip with chars argument - use regex
                    return f"{obj_str}.replaceFirst(\"[\" + {args_str} + \"]+$\", \"\")"
                return f"{obj_str}.stripTrailing()"
            if method == "lower":
                return f"{obj_str}.toLowerCase()"
            if method == "upper":
                return f"{obj_str}.toUpperCase()"
            if method == "isalpha":
                return f"{obj_str}.chars().allMatch(Character::isLetter)"
            if method == "isalnum":
                return f"{obj_str}.chars().allMatch(Character::isLetterOrDigit)"
            if method == "isdigit":
                return f"{obj_str}.chars().allMatch(Character::isDigit)"
            if method == "isspace":
                return f"{obj_str}.chars().allMatch(Character::isWhitespace)"
        # Fallback: convert common Python methods to Java equivalents
        if method == "append":
            return f"{obj_str}.add({args_str})"
        if method == "extend":
            return f"{obj_str}.addAll({args_str})"
        if method == "remove":
            return f"{obj_str}.remove({args_str})"
        if method == "clear":
            return f"{obj_str}.clear()"
        if method == "insert":
            return f"{obj_str}.add({args_str})"
        return f"{obj_str}.{to_camel(method)}({args_str})"

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

    def _containment_check(self, item: Expr, container: Expr, negated: bool) -> str:
        """Generate containment check: `x in y` or `x not in y`."""
        item_str = self._expr(item)
        container_str = self._expr(container)
        container_type = getattr(container, 'typ', None)
        neg = "!" if negated else ""
        # For sets and maps, use contains/containsKey
        if isinstance(container_type, Set):
            return f"{neg}{container_str}.contains({item_str})"
        if isinstance(container_type, Map):
            return f"{neg}{container_str}.containsKey({item_str})"
        # For strings, use indexOf != -1 (or contains for char in string)
        if isinstance(container_type, Primitive) and container_type.kind == "string":
            if negated:
                return f"{container_str}.indexOf({item_str}) == -1"
            return f"{container_str}.indexOf({item_str}) != -1"
        # For lists/arrays, use contains
        return f"{neg}{container_str}.contains({item_str})"

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
        escaped = result.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        args_str = ", ".join(self._expr(a) for a in args)
        if args_str:
            return f'String.format("{escaped}", {args_str})'
        return f'"{escaped}"'

    def _lvalue(self, lv: LValue) -> str:
        match lv:
            case VarLV(name=name):
                if name == self.receiver_name:
                    return "this"
                return _java_safe_name(name)
            case FieldLV(obj=obj, field=field):
                return f"{self._expr(obj)}.{_java_safe_name(field)}"
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
                sig = tuple(self._type(t) for t in elements)
                if sig in self.optional_tuples:
                    inner = _box_type(self._type(elements[0]))
                    return f"Optional<{inner}>"
                return self._tuple_record_name(typ)
            case Pointer(target=target):
                return self._type(target)
            case Optional(inner=inner):
                return self._type(inner)
            case StructRef(name=name):
                return _java_safe_class(name)
            case Interface(name=name):
                if name == "any":
                    return "Object"
                return _java_safe_class(name)
            case Union(name=name, variants=variants):
                if name:
                    return _java_safe_class(name)
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
                return _java_safe_class(name)
            case Interface(name=name):
                return _java_safe_class(name)
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

    def _is_optional_tuple(self, typ: Type) -> bool:
        """Check if this tuple type should be represented as Optional<T>."""
        if isinstance(typ, Tuple):
            sig = tuple(self._type(t) for t in typ.elements)
            return sig in self.optional_tuples
        return False

    def _emit_optional_tuple(self, lit: TupleLit) -> str:
        """Emit a (T, bool) tuple as Optional<T>."""
        value_expr = self._expr(lit.elements[0])
        ok_expr = lit.elements[1]
        # If the bool is a literal, we can emit Optional.of() or Optional.empty()
        if isinstance(ok_expr, BoolLit):
            if ok_expr.value:
                return f"Optional.of({value_expr})"
            return "Optional.empty()"
        # If bool is a variable, we need a conditional
        ok_str = self._expr(ok_expr)
        return f"({ok_str} ? Optional.of({value_expr}) : Optional.empty())"

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
                return "new ArrayList<>()"
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


def _string_literal(value: str) -> str:
    return f'"{escape_string(value)}"'
