"""Swift backend: IR → Swift code."""

from __future__ import annotations

from src.backend.util import escape_string as _escape_string_generic

from src.ir import (
    Args,
    Array,
    Assign,
    BinaryOp,
    Block,
    BoolLit,
    Break,
    Call,
    Cast,
    CharAt,
    CharClassify,
    CharLen,
    CharLit,
    Constant,
    Continue,
    DerefLV,
    DictComp,
    EntryPoint,
    Enum,
    EnumVariant,
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
    GetEnv,
    If,
    Index,
    IndexLV,
    IntLit,
    IntToStr,
    InterfaceDef,
    InterfaceRef,
    IsNil,
    IsType,
    LastElement,
    Len,
    ListComp,
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
    Print,
    Raise,
    ReadAll,
    ReadLine,
    Return,
    SentinelToOptional,
    Set,
    SetComp,
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
    Struct,
    StructLit,
    StructRef,
    Substring,
    Ternary,
    TryCatch,
    TrimChars,
    Truthy,
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


def escape_string(value: str) -> str:
    """Escape a string for use in a Swift string literal.

    Swift uses \\u{XXXX} format for Unicode escapes, not \\uXXXX.
    """
    result = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
        .replace("\r", "\\r")
        .replace("\x01", "\\u{0001}")
        .replace("\x7f", "\\u{007f}")
    )
    return result


# Swift reserved words that need escaping with backticks
_SWIFT_RESERVED = frozenset({
    # Keywords used in declarations
    "associatedtype", "class", "deinit", "enum", "extension", "fileprivate",
    "func", "import", "init", "inout", "internal", "let", "open", "operator",
    "private", "protocol", "public", "rethrows", "static", "struct", "subscript",
    "typealias", "var",
    # Keywords used in statements
    "break", "case", "continue", "default", "defer", "do", "else", "fallthrough",
    "for", "guard", "if", "in", "repeat", "return", "switch", "where", "while",
    # Keywords used in expressions and types
    "as", "Any", "catch", "false", "is", "nil", "super", "self", "Self", "throw",
    "throws", "true", "try", "Type",
    # Context-sensitive keywords
    "associativity", "convenience", "dynamic", "didSet", "final", "get", "infix",
    "indirect", "lazy", "left", "mutating", "none", "nonmutating", "optional",
    "override", "postfix", "precedence", "prefix", "Protocol", "required", "right",
    "set", "unowned", "weak", "willSet",
    # Built-in types
    "String", "Int", "Double", "Bool", "Float", "Character", "Array", "Dictionary",
    "Set", "Optional", "Error",
})


def _safe_name(name: str) -> str:
    """Escape Swift reserved words with backticks and normalize to camelCase."""
    # Handle leading underscore
    if name.startswith("_"):
        prefix = "_"
        name = name[1:]
    else:
        prefix = ""
    # Convert snake_case to camelCase
    if "_" in name:
        parts = name.split("_")
        result = parts[0].lower() + "".join(p.capitalize() for p in parts[1:])
    # Convert PascalCase to camelCase (for interface method names)
    elif name and name[0].isupper() and not name.isupper():
        result = name[0].lower() + name[1:]
    else:
        result = name
    if prefix + result in _SWIFT_RESERVED:
        return f"`{prefix}{result}`"
    return prefix + result


def _safe_type_name(name: str) -> str:
    """Handle type names (PascalCase), escaping reserved words."""
    if name in _SWIFT_RESERVED:
        return f"`{name}`"
    return name


class SwiftBackend:
    """Emit Swift code from IR."""

    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self.receiver_name: str | None = None
        self.current_class: str = ""
        self.struct_fields: dict[str, list[tuple[str, Type]]] = {}
        self._hoisted_vars: set[str] = set()
        self._declared_vars: set[str] = set()
        self._optional_hoisted: set[str] = set()
        self._interface_names: set[str] = set()
        self.temp_counter = 0
        self._type_switch_binding_rename: dict[str, str] = {}
        self._func_params: set[str] = set()
        self._current_return_type: Type | None = None
        self._throwing_funcs: set[str] = set()
        self._nil_returning_funcs: set[str] = set()
        self._expr_has_try: bool = False

    def emit(self, module: Module) -> str:
        """Emit Swift code from IR Module."""
        self.indent = 0
        self.lines = []
        self.struct_fields = {}
        self._hoisted_vars = set()
        self._optional_hoisted = set()
        self._interface_names = {iface.name for iface in module.interfaces}
        self._throwing_funcs = set()
        self._nil_returning_funcs = set()
        self._collect_struct_fields(module)
        self._collect_throwing_funcs(module)
        self._collect_nil_returning_funcs(module)
        self._emit_module(module)
        return "\n".join(self.lines)

    def _collect_struct_fields(self, module: Module) -> None:
        """Collect field information for all structs."""
        for struct in module.structs:
            self.struct_fields[struct.name] = [(f.name, f.typ) for f in struct.fields]

    def _collect_throwing_funcs(self, module: Module) -> None:
        """Collect names of functions/methods that can throw (direct or indirect)."""
        all_funcs: list[Function] = list(module.functions)
        for struct in module.structs:
            all_funcs.extend(struct.methods)
        # Direct throws
        for func in all_funcs:
            if _can_throw(func.body):
                self._throwing_funcs.add(func.name)
        # Iterate to find indirect throws (calls to throwing functions)
        changed = True
        while changed:
            changed = False
            for func in all_funcs:
                if func.name not in self._throwing_funcs:
                    if _calls_any(func.body, self._throwing_funcs):
                        self._throwing_funcs.add(func.name)
                        changed = True

    def _collect_nil_returning_funcs(self, module: Module) -> None:
        """Collect names of functions/methods that can return nil."""
        all_funcs: list[Function] = list(module.functions)
        for struct in module.structs:
            all_funcs.extend(struct.methods)
        for func in all_funcs:
            if _returns_nil(func.body):
                self._nil_returning_funcs.add(func.name)

    def _line(self, text: str = "") -> None:
        if text:
            self.lines.append("    " * self.indent + text)
        else:
            self.lines.append("")

    def _emit_module(self, module: Module) -> None:
        self._line("import Foundation")
        self._line()
        # Emit helper functions first
        self._emit_helpers()
        # Emit constants
        if module.constants:
            for const in module.constants:
                self._emit_constant(const)
            self._line()
        # Emit enums
        for enum_def in module.enums:
            self._emit_enum(enum_def)
            self._line()
        # Emit interfaces as protocols
        for iface in module.interfaces:
            self._emit_interface(iface)
            self._line()
        # Emit structs as classes
        for struct in module.structs:
            self._emit_struct(struct)
            self._line()
        # Emit free functions
        for func in module.functions:
            self._emit_function(func)
            self._line()

    def _emit_helpers(self) -> None:
        """Emit helper functions needed by generated code."""
        self._line("// Helper functions")
        self._line("func _charAt(_ s: String, _ i: Int) -> String {")
        self.indent += 1
        self._line("let idx = s.index(s.startIndex, offsetBy: i)")
        self._line("return String(s[idx])")
        self.indent -= 1
        self._line("}")
        self._line()
        self._line("func _charArray(_ s: String) -> [String] {")
        self.indent += 1
        self._line("s.map { String($0) }")
        self.indent -= 1
        self._line("}")
        self._line()
        self._line("func range(_ end: Int) -> [Int] {")
        self.indent += 1
        self._line("Swift.Array(0..<end)")
        self.indent -= 1
        self._line("}")
        self._line()
        self._line("func range(_ start: Int, _ end: Int) -> [Int] {")
        self.indent += 1
        self._line("Swift.Array(start..<end)")
        self.indent -= 1
        self._line("}")
        self._line()
        self._line("func range(_ start: Int, _ end: Int, _ step: Int) -> [Int] {")
        self.indent += 1
        self._line("stride(from: start, to: end, by: step).map { $0 }")
        self.indent -= 1
        self._line("}")
        self._line()
        self._line("func readAllStdin() -> String {")
        self.indent += 1
        self._line("var result = \"\"")
        self._line("while let line = readLine(strippingNewline: false) {")
        self.indent += 1
        self._line("result += line")
        self.indent -= 1
        self._line("}")
        self._line("return result")
        self.indent -= 1
        self._line("}")
        self._line()

    def _emit_constant(self, const: Constant) -> None:
        typ = self._type(const.typ)
        val = self._expr(const.value)
        name = _safe_name(const.name)
        self._line(f"let {name}: {typ} = {val}")

    def _emit_enum(self, enum_def: Enum) -> None:
        """Emit Swift enum declaration."""
        name = _safe_type_name(enum_def.name)
        # Check if all variants have int or no explicit values
        all_int = all(v.value is None or isinstance(v.value, int) for v in enum_def.variants)
        if all_int:
            self._line(f"enum {name}: Int {{")
            self.indent += 1
            for variant in enum_def.variants:
                vname = _safe_name(variant.name)
                if variant.value is not None:
                    self._line(f"case {vname} = {variant.value}")
                else:
                    self._line(f"case {vname}")
            self.indent -= 1
            self._line("}")
        else:
            # String enum
            self._line(f"enum {name}: String {{")
            self.indent += 1
            for variant in enum_def.variants:
                vname = _safe_name(variant.name)
                if isinstance(variant.value, str):
                    self._line(f'case {vname} = "{variant.value}"')
                else:
                    self._line(f"case {vname}")
            self.indent -= 1
            self._line("}")

    def _emit_interface(self, iface: InterfaceDef) -> None:
        """Emit interface as Swift protocol."""
        self._line(f"protocol {_safe_type_name(iface.name)} {{")
        self.indent += 1
        for fld in iface.fields:
            typ = self._type(fld.typ)
            name = _safe_name(fld.name)
            self._line(f"var {name}: {typ} {{ get set }}")
        for method in iface.methods:
            params = self._params(method.params)
            ret = self._type(method.ret)
            name = _safe_name(method.name)
            if ret == "Void":
                self._line(f"func {name}({params})")
            else:
                self._line(f"func {name}({params}) -> {ret}")
        self.indent -= 1
        self._line("}")

    def _emit_struct(self, struct: Struct) -> None:
        """Emit struct as Swift class."""
        class_name = _safe_type_name(struct.name)
        self.current_class = struct.name
        if struct.doc:
            self._line(f"/// {struct.doc}")
        # Build class declaration - superclass must come first in Swift
        inherits: list[str] = []
        if struct.embedded_type:
            inherits.append(_safe_type_name(struct.embedded_type))
        # Only add Error protocol if not inheriting from another exception class
        if struct.is_exception and not struct.embedded_type:
            inherits.append("Error")
        for iface in struct.implements:
            inherits.append(_safe_type_name(iface))
        if inherits:
            self._line(f"class {class_name}: {', '.join(inherits)} {{")
        else:
            self._line(f"class {class_name} {{")
        self.indent += 1
        # Emit fields
        for fld in struct.fields:
            self._emit_field(fld)
        if struct.fields:
            self._line()
        # Emit initializer
        self._emit_initializer(struct)
        # Emit methods
        for method in struct.methods:
            self._line()
            self._emit_method(method)
        self.indent -= 1
        self._line("}")
        self.current_class = ""

    def _emit_field(self, fld: Field) -> None:
        typ = self._type(fld.typ)
        name = _safe_name(fld.name)
        if isinstance(fld.typ, Optional):
            self._line(f"var {name}: {typ}")
        elif isinstance(fld.typ, Pointer):
            # Pointers are to class types, use implicitly unwrapped optional
            self._line(f"var {name}: {typ}!")
        elif isinstance(fld.typ, (InterfaceRef, Union)):
            # Interface/protocol types can't have default instances, use implicitly unwrapped optional
            self._line(f"var {name}: ({typ})!")
        else:
            # Use default value to satisfy protocol requirements
            default = self._default_value(fld.typ)
            self._line(f"var {name}: {typ} = {default}")

    def _emit_initializer(self, struct: Struct) -> None:
        """Emit Swift initializer."""
        class_name = _safe_type_name(struct.name)
        if not struct.fields:
            if struct.embedded_type:
                # Child class with no new fields - need to pass through to parent
                parent_fields = self.struct_fields.get(struct.embedded_type, [])
                if parent_fields:
                    param_parts = []
                    arg_parts = []
                    for fname, ftyp in parent_fields:
                        pname = _safe_name(fname)
                        ptyp = self._type(ftyp)
                        default = self._default_value(ftyp)
                        param_parts.append(f"{pname}: {ptyp} = {default}")
                        arg_parts.append(f"{pname}: {pname}")
                    params = ", ".join(param_parts)
                    args = ", ".join(arg_parts)
                    self._line(f"override init({params}) {{")
                    self.indent += 1
                    self._line(f"super.init({args})")
                    self.indent -= 1
                    self._line("}")
                else:
                    self._line("override init() { super.init() }")
            else:
                self._line("init() {}")
            return
        # Build parameter list with defaults matching field types
        param_parts: list[str] = []
        for f in struct.fields:
            typ = self._type(f.typ)
            name = _safe_name(f.name)
            default = self._default_value(f.typ)
            if isinstance(f.typ, (InterfaceRef, Union)):
                # Interface types become optional in field, so param should match
                param_parts.append(f"{name}: ({typ})? = {default}")
            elif isinstance(f.typ, Pointer):
                # Pointer fields are implicitly unwrapped optional, param is optional
                param_parts.append(f"{name}: {typ}? = {default}")
            else:
                param_parts.append(f"{name}: {typ} = {default}")
        params = ", ".join(param_parts)
        self._line(f"init({params}) {{")
        self.indent += 1
        for f in struct.fields:
            name = _safe_name(f.name)
            if isinstance(f.typ, Pointer):
                # Optional param to implicitly unwrapped field
                self._line(f"if let {name} = {name} {{ self.{name} = {name} }}")
            else:
                self._line(f"self.{name} = {name}")
        self.indent -= 1
        self._line("}")

    def _emit_function(self, func: Function) -> None:
        self._hoisted_vars = set()
        self._optional_hoisted = set()
        self._declared_vars = {p.name for p in func.params}
        self._func_params = {p.name for p in func.params if isinstance(p.typ, FuncType)}
        self._current_return_type = func.ret
        if func.doc:
            self._line(f"/// {func.doc}")
        params = self._params(func.params)
        ret = self._type(func.ret)
        name = _safe_name(func.name)
        throws = " throws" if func.name in self._throwing_funcs else ""
        if _returns_nil(func.body) and not ret.endswith("?"):
            ret += "?"
        if ret == "Void":
            self._line(f"func {name}({params}){throws} {{")
        else:
            self._line(f"func {name}({params}){throws} -> {ret} {{")
        self.indent += 1
        self._emit_param_var_shadows(func.params)
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")
        self._current_return_type = None

    def _emit_method(self, func: Function) -> None:
        self._hoisted_vars = set()
        self._optional_hoisted = set()
        self._declared_vars = {p.name for p in func.params}
        self._func_params = {p.name for p in func.params if isinstance(p.typ, FuncType)}
        self._current_return_type = func.ret
        if func.doc:
            self._line(f"/// {func.doc}")
        params = self._params(func.params)
        ret = self._type(func.ret)
        name = _safe_name(func.name)
        if func.receiver:
            self.receiver_name = func.receiver.name
        throws = " throws" if func.name in self._throwing_funcs else ""
        if _returns_nil(func.body) and not ret.endswith("?"):
            ret += "?"
        if ret == "Void":
            self._line(f"func {name}({params}){throws} {{")
        else:
            self._line(f"func {name}({params}){throws} -> {ret} {{")
        self.indent += 1
        self._emit_param_var_shadows(func.params)
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")
        self.receiver_name = None
        self._current_return_type = None

    def _params(self, params: list[Param]) -> str:
        parts = []
        for p in params:
            typ = self._type(p.typ)
            name = _safe_name(p.name)
            if isinstance(p.typ, Pointer) and _is_mutable_value_type(p.typ.target):
                parts.append(f"_ {name}: inout {typ}")
            else:
                parts.append(f"_ {name}: {typ}")
        return ", ".join(parts)

    def _emit_param_var_shadows(self, params: list[Param]) -> None:
        """Emit var shadows for collection-type parameters that need mutation."""
        for p in params:
            # Skip Pointer params - those use inout instead of var shadows
            if isinstance(p.typ, Pointer):
                continue
            if p.typ and _is_mutable_value_type(p.typ):
                name = _safe_name(p.name)
                self._line(f"var {name} = {name}")

    def _emit_hoisted_vars(
        self, stmt: If | While | ForRange | ForClassic | TryCatch | Match | TypeSwitch
    ) -> None:
        hoisted_vars = stmt.hoisted_vars
        for name, typ in hoisted_vars:
            var_name = _safe_name(name)
            if typ:
                swift_type = self._type(typ)
                default = self._default_value(typ)
                # Make optional if default is nil OR if the type is a reference/interface
                # type that may be assigned from nil-returning functions
                needs_optional = default == "nil" or isinstance(typ, (InterfaceRef, StructRef, Union, Pointer))
                if needs_optional and not swift_type.endswith("?"):
                    swift_type += "?"
                    default = "nil"
                if needs_optional:
                    self._optional_hoisted.add(name)
                self._line(f"var {var_name}: {swift_type} = {default}")
            else:
                self._line(f"var {var_name}: Any?")
                self._optional_hoisted.add(name)
            self._hoisted_vars.add(name)
            self._declared_vars.add(name)

    def _try_expr(self, expr: Expr) -> str:
        """Emit expression, prefixing 'try' if it contains a throwing call."""
        self._expr_has_try = False
        result = self._expr(expr)
        if self._expr_has_try:
            return f"try {result}"
        return result

    def _emit_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDecl(name=name, typ=typ, value=value):
                var_name = _safe_name(name)
                self._declared_vars.add(name)
                swift_type = self._type(typ)
                if isinstance(typ, Optional):
                    self._optional_hoisted.add(name)
                if value is not None:
                    val = self._try_expr(value)
                    if _expr_can_be_nil(value, self._nil_returning_funcs) and not swift_type.endswith("?"):
                        swift_type += "?"
                        self._optional_hoisted.add(name)
                    elif isinstance(value, TupleLit) and isinstance(typ, Tuple):
                        swift_type = self._tuple_type_with_nil(typ, value)
                    keyword = "var" if stmt.is_reassigned or _is_mutable_value_type(typ) else "let"
                    self._line(f"{keyword} {var_name}: {swift_type} = {val}")
                else:
                    self._line(f"var {var_name}: {swift_type}")
            case Assign(target=target, value=value):
                val = self._try_expr(value)
                lv = self._lvalue(target)
                target_name = target.name if isinstance(target, VarLV) else None
                is_hoisted = target_name and target_name in self._hoisted_vars
                needs_decl = target_name and target_name not in self._declared_vars and not is_hoisted
                if (stmt.is_declaration and not is_hoisted) or needs_decl:
                    decl_type = stmt.decl_typ if stmt.decl_typ is not None else value.typ
                    swift_type = self._type(decl_type) if decl_type else "Any"
                    if _expr_can_be_nil(value, self._nil_returning_funcs) and not swift_type.endswith("?"):
                        swift_type += "?"
                        if target_name:
                            self._optional_hoisted.add(target_name)
                    self._line(f"var {lv}: {swift_type} = {val}")
                    if target_name:
                        self._declared_vars.add(target_name)
                else:
                    self._line(f"{lv} = {val}")
            case OpAssign(target=target, op=op, value=value):
                lv = self._lvalue(target)
                val = self._try_expr(value)
                self._line(f"{lv} {op}= {val}")
            case TupleAssign(targets=targets, value=value):
                self._emit_tuple_assign(stmt)
            case NoOp():
                pass
            case ExprStmt(expr=expr):
                e = self._try_expr(expr)
                self._line(f"{e}")
            case Return(value=value):
                if value is not None:
                    val = self._try_expr(value)
                    self._line(f"return {val}")
                else:
                    self._line("return")
            case If(cond=cond, then_body=then_body, else_body=else_body, init=init):
                self._emit_hoisted_vars(stmt)
                if init is not None:
                    self._emit_stmt(init)
                self._line(f"if {self._try_expr(cond)} {{")
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
                self._emit_type_switch(stmt)
            case Match(expr=expr, cases=cases, default=default):
                self._emit_match(stmt)
            case ForRange(index=index, value=value, iterable=iterable, body=body):
                self._emit_for_range(stmt)
            case ForClassic(init=init, cond=cond, post=post, body=body):
                self._emit_for_classic(stmt)
            case While(cond=cond, body=body):
                self._emit_hoisted_vars(stmt)
                self._line(f"while {self._try_expr(cond)} {{")
                self.indent += 1
                for s in body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("}")
            case Break(label=label):
                self._line("break")
            case Continue(label=label):
                self._line("continue")
            case Block(body=body):
                no_scope = stmt.no_scope
                if not no_scope:
                    self._line("do {")
                    self.indent += 1
                for s in body:
                    self._emit_stmt(s)
                if not no_scope:
                    self.indent -= 1
                    self._line("}")
            case TryCatch(body=body, catch_var=catch_var, catch_type=catch_type, catch_body=catch_body, reraise=reraise):
                self._emit_try_catch(stmt)
            case Raise(error_type=error_type, message=message, pos=pos, reraise_var=reraise_var):
                if reraise_var:
                    self._line(f"throw {_safe_name(reraise_var)}")
                else:
                    self._expr_has_try = False
                    msg = self._expr(message)
                    pos_expr = self._expr(pos)
                    prefix = "try " if self._expr_has_try else ""
                    self._line(f"throw {prefix}{_safe_type_name(error_type)}(message: {msg}, pos: {pos_expr})")
            case SoftFail():
                self._line("return nil")
            case Print(value=value, newline=newline, stderr=stderr):
                val = self._try_expr(value)
                if stderr:
                    if newline:
                        self._line(f'fputs({val} + "\\n", stderr)')
                    else:
                        self._line(f"fputs({val}, stderr)")
                else:
                    if newline:
                        self._line(f"print({val})")
                    else:
                        self._line(f'print({val}, terminator: "")')
            case EntryPoint(function_name=function_name):
                pass
            case _:
                self._line("// TODO: unknown statement")

    def _emit_tuple_assign(self, stmt: TupleAssign) -> None:
        value = stmt.value
        targets = stmt.targets
        is_decl = stmt.is_declaration
        new_targets = stmt.new_targets
        value_type = value.typ
        if isinstance(value_type, Tuple):
            val_str = self._try_expr(value)
            self.temp_counter += 1
            temp_var = f"_tuple{self.temp_counter}"
            self._line(f"let {temp_var} = {val_str}")
            for i, target in enumerate(targets):
                target_name = target.name if isinstance(target, VarLV) else f"_t{i}"
                is_hoisted = target_name in self._hoisted_vars
                is_new = is_decl or (target_name and target_name in new_targets)
                lv = self._lvalue(target)
                accessor = f"{temp_var}.{i}"
                elem_type = value_type.elements[i] if i < len(value_type.elements) else None
                if is_hoisted or not is_new:
                    self._line(f"{lv} = {accessor}")
                else:
                    swift_type = self._type(elem_type) if elem_type else "Any"
                    self._line(f"var {lv}: {swift_type} = {accessor}")
                    if target_name:
                        self._declared_vars.add(target_name)
                        if isinstance(elem_type, Optional):
                            self._optional_hoisted.add(target_name)
        else:
            val_str = self._try_expr(value)
            self.temp_counter += 1
            temp_var = f"_tuple{self.temp_counter}"
            self._line(f"let {temp_var} = {val_str}")
            for i, target in enumerate(targets):
                lv = self._lvalue(target)
                target_name = target.name if isinstance(target, VarLV) else None
                is_hoisted = target_name and target_name in self._hoisted_vars
                if (is_decl or (target_name and target_name in new_targets)) and not is_hoisted:
                    self._line(f"var {lv} = {temp_var}.{i}")
                    if target_name:
                        self._declared_vars.add(target_name)
                else:
                    self._line(f"{lv} = {temp_var}.{i}")

    def _emit_type_switch(self, stmt: TypeSwitch) -> None:
        self._emit_hoisted_vars(stmt)
        var = self._expr(stmt.expr)
        binding = _safe_name(stmt.binding)
        # Use a unique name to avoid shadowing the switched variable
        case_binding = f"_{binding}" if binding == var else binding
        cases = stmt.cases
        default = stmt.default
        # Use switch with case let pattern matching
        self._line(f"switch {var} {{")
        for case in cases:
            type_name = self._type_name_for_check(case.typ)
            self._line(f"case let {case_binding} as {type_name}:")
            self.indent += 1
            self._type_switch_binding_rename[stmt.binding] = case_binding
            saved_decl = set(self._declared_vars)
            saved_hoist = set(self._hoisted_vars)
            saved_opt = set(self._optional_hoisted)
            for s in case.body:
                self._emit_stmt(s)
            self._declared_vars = saved_decl
            self._hoisted_vars = saved_hoist
            self._optional_hoisted = saved_opt
            self._type_switch_binding_rename.pop(stmt.binding, None)
            self.indent -= 1
        if default:
            self._line("default:")
            self.indent += 1
            saved_decl = set(self._declared_vars)
            saved_hoist = set(self._hoisted_vars)
            saved_opt = set(self._optional_hoisted)
            for s in default:
                self._emit_stmt(s)
            self._declared_vars = saved_decl
            self._hoisted_vars = saved_hoist
            self._optional_hoisted = saved_opt
            self.indent -= 1
        else:
            self._line("default:")
            self.indent += 1
            self._line("break")
            self.indent -= 1
        self._line("}")

    def _emit_match(self, stmt: Match) -> None:
        self._emit_hoisted_vars(stmt)
        expr_str = self._expr(stmt.expr)
        self._line(f"switch {expr_str} {{")
        for case in stmt.cases:
            patterns_str = ", ".join(self._expr(p) for p in case.patterns)
            self._line(f"case {patterns_str}:")
            self.indent += 1
            saved_decl = set(self._declared_vars)
            saved_hoist = set(self._hoisted_vars)
            saved_opt = set(self._optional_hoisted)
            for s in case.body:
                self._emit_stmt(s)
            self._declared_vars = saved_decl
            self._hoisted_vars = saved_hoist
            self._optional_hoisted = saved_opt
            self.indent -= 1
        if stmt.default:
            self._line("default:")
            self.indent += 1
            saved_decl = set(self._declared_vars)
            saved_hoist = set(self._hoisted_vars)
            saved_opt = set(self._optional_hoisted)
            for s in stmt.default:
                self._emit_stmt(s)
            self._declared_vars = saved_decl
            self._hoisted_vars = saved_hoist
            self._optional_hoisted = saved_opt
            self.indent -= 1
        else:
            self._line("default:")
            self.indent += 1
            self._line("break")
            self.indent -= 1
        self._line("}")

    def _emit_for_range(self, stmt: ForRange) -> None:
        self._emit_hoisted_vars(stmt)
        iter_expr = self._expr(stmt.iterable)
        iter_type = stmt.iterable.typ
        if isinstance(iter_type, Optional):
            iter_expr = f"{iter_expr}!"
            iter_type = iter_type.inner
        is_string = isinstance(iter_type, Primitive) and iter_type.kind == "string"
        index = stmt.index
        value = stmt.value
        body = stmt.body
        if value is not None and index is not None:
            idx = _safe_name(index)
            val = _safe_name(value)
            val_hoisted = value in self._hoisted_vars
            if is_string:
                # Convert string to array for indexed access
                self._line(f"let _chars = _charArray({iter_expr})")
                self._line(f"for {idx} in 0..<_chars.count {{")
                self.indent += 1
                if val_hoisted:
                    self._line(f"{val} = _chars[{idx}]")
                else:
                    self._line(f"let {val} = _chars[{idx}]")
            else:
                self._line(f"for ({idx}, {val}) in {iter_expr}.enumerated() {{")
                self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        elif value is not None:
            val = _safe_name(value)
            is_hoisted = value in self._hoisted_vars
            if is_string:
                # Always use temp variable for strings since loop yields Character, not String
                self.temp_counter += 1
                temp = f"_c{self.temp_counter}"
                self._line(f"for {temp} in {iter_expr} {{")
                self.indent += 1
                if is_hoisted:
                    self._line(f"{val} = String({temp})")
                else:
                    self._line(f"let {val} = String({temp})")
            else:
                if is_hoisted:
                    self.temp_counter += 1
                    temp = f"_e{self.temp_counter}"
                    self._line(f"for {temp} in {iter_expr} {{")
                    self.indent += 1
                    self._line(f"{val} = {temp}")
                else:
                    self._line(f"for {val} in {iter_expr} {{")
                    self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        elif index is not None:
            idx = _safe_name(index)
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

    def _emit_for_classic(self, stmt: ForClassic) -> None:
        self._emit_hoisted_vars(stmt)
        # Swift doesn't have C-style for, use while
        if stmt.init:
            self._emit_stmt(stmt.init)
        cond_str = self._expr(stmt.cond) if stmt.cond else "true"
        self._line(f"while {cond_str} {{")
        self.indent += 1
        for s in stmt.body:
            self._emit_stmt(s)
        if stmt.post:
            self._emit_stmt(stmt.post)
        self.indent -= 1
        self._line("}")

    def _emit_try_catch(self, stmt: TryCatch) -> None:
        self._emit_hoisted_vars(stmt)
        self._line("do {")
        self.indent += 1
        for s in stmt.body:
            self._emit_stmt(s)
        self.indent -= 1
        exc_type = stmt.catch_type.name if isinstance(stmt.catch_type, StructRef) else "Error"
        is_generic = exc_type in ("Exception", "Error")
        needs_binding = (not stmt.catch_var_unused or stmt.reraise) and stmt.catch_var
        needs_reraise_binding = stmt.reraise and not stmt.catch_var
        if is_generic:
            if needs_binding:
                var = _safe_name(stmt.catch_var)
                self._line(f"}} catch let {var} {{")
            elif needs_reraise_binding:
                self._line("} catch let _err {")
            else:
                self._line("} catch {")
        else:
            if needs_binding:
                var = _safe_name(stmt.catch_var)
                self._line(f"}} catch let {var} as {_safe_type_name(exc_type)} {{")
            elif needs_reraise_binding:
                self._line(f"}} catch let _err as {_safe_type_name(exc_type)} {{")
            else:
                self._line(f"}} catch is {_safe_type_name(exc_type)} {{")
        self.indent += 1
        for s in stmt.catch_body:
            self._emit_stmt(s)
        if stmt.reraise:
            if stmt.catch_var:
                self._line(f"throw {_safe_name(stmt.catch_var)}")
            else:
                self._line("throw _err")
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
                return f'"{escape_string(value)}"'
            case BoolLit(value=value):
                return "true" if value else "false"
            case NilLit():
                return "nil"
            case Var(name=name):
                if name in self._type_switch_binding_rename:
                    return self._type_switch_binding_rename[name]
                if name == self.receiver_name:
                    return "self"
                result = _safe_name(name)
                if name in self._optional_hoisted:
                    result += "!"
                return result
            case FieldAccess(obj=obj, field=field):
                obj_str = self._expr(obj)
                obj_type = obj.typ
                if isinstance(obj_type, Optional) and not obj_str.endswith("!"):
                    obj_str = f"{obj_str}!"
                    obj_type = obj_type.inner
                # Handle tuple field access (F0, F1 -> .0, .1)
                if isinstance(obj_type, Tuple) and field.startswith("F") and field[1:].isdigit():
                    idx = int(field[1:])
                    return f"{obj_str}.{idx}"
                return f"{obj_str}.{_safe_name(field)}"
            case FuncRef(name=name, obj=obj):
                if obj is not None:
                    obj_str = self._expr(obj)
                    return f"{obj_str}.{_safe_name(name)}"
                return _safe_name(name)
            case Index(obj=obj, index=index):
                obj_str = self._expr(obj)
                idx_str = self._expr(index)
                obj_type = obj.typ
                # String indexing in Swift requires special handling
                if isinstance(obj_type, Primitive) and obj_type.kind == "string":
                    return f"_charAt({obj_str}, {idx_str})"
                if isinstance(obj_type, Tuple):
                    if isinstance(index, IntLit):
                        return f"{obj_str}.{index.value}"
                    return f"{obj_str}[{idx_str}]"
                return f"{obj_str}[{idx_str}]"
            case SliceExpr(obj=obj, low=low, high=high):
                return self._slice_expr(obj, low, high)
            case ParseInt(string=s, base=b):
                return f"Int({self._expr(s)}, radix: {self._expr(b)})!"
            case IntToStr(value=v):
                return f"String({self._expr(v)})"
            case CharClassify(kind=kind, char=char):
                char_str = self._expr(char)
                char_type = char.typ
                method_map = {
                    "digit": "isNumber",
                    "alpha": "isLetter",
                    "space": "isWhitespace",
                    "upper": "isUppercase",
                    "lower": "isLowercase",
                }
                is_rune = isinstance(char_type, Primitive) and char_type.kind == "rune"
                if is_rune:
                    char_access = f"Character(UnicodeScalar({char_str})!)"
                    if kind == "alnum":
                        return f"({char_access}.isLetter || {char_access}.isNumber)"
                    return f"{char_access}.{method_map[kind]}"
                # String path
                if kind == "alnum":
                    return f"({char_str}.first?.isLetter ?? false || {char_str}.first?.isNumber ?? false)"
                return f"({char_str}.first?.{method_map[kind]} ?? false)"
            case TrimChars(string=s, chars=chars, mode=mode):
                s_str = self._expr(s)
                if isinstance(chars, StringLit) and chars.value == " \t\n\r":
                    if mode == "both":
                        return f"{s_str}.trimmingCharacters(in: .whitespacesAndNewlines)"
                    elif mode == "left":
                        return f'String({s_str}.drop(while: {{ $0.isWhitespace }}))'
                    else:
                        return f'String({s_str}.reversed().drop(while: {{ $0.isWhitespace }}).reversed())'
                chars_str = self._expr(chars)
                return f"{s_str}.trimmingCharacters(in: CharacterSet(charactersIn: {chars_str}))"
            case Call(func=func, args=args):
                return self._call(func, args)
            case MethodCall(obj=obj, method=method, args=args, receiver_type=receiver_type):
                return self._method_call(obj, method, args, receiver_type)
            case StaticCall(on_type=on_type, method=method, args=args):
                args_str = ", ".join(self._emit_arg(a) for a in args)
                type_name = self._type_name_for_check(on_type)
                return f"{type_name}.{_safe_name(method)}({args_str})"
            case Truthy(expr=e):
                inner_str = self._expr(e)
                inner_type = e.typ
                if _is_string_type(inner_type):
                    return f"(!{inner_str}.isEmpty)"
                if isinstance(inner_type, (Slice, Map, Set)):
                    return f"(!{inner_str}.isEmpty)"
                if isinstance(inner_type, Optional):
                    inner_inner = inner_type.inner
                    if isinstance(inner_inner, (Slice, Map, Set)):
                        return f"({inner_str} != nil && !{inner_str}!.isEmpty)"
                    if isinstance(inner_inner, Primitive) and inner_inner.kind == "string":
                        return f"({inner_str} != nil && !{inner_str}!.isEmpty)"
                    return f"({inner_str} != nil)"
                if isinstance(inner_type, Primitive) and inner_type.kind == "int":
                    return f"({inner_str} != 0)"
                if isinstance(inner_type, Primitive) and inner_type.kind == "bool":
                    # Check if this is a negated optional check (e.g., !comment where comment is nullable)
                    if isinstance(e, UnaryOp) and e.op == "!" and isinstance(e.operand, Var):
                        var_name = e.operand.name
                        if var_name in self._optional_hoisted:
                            return f"({self._expr(e.operand)} == nil)"
                    return inner_str
                return f"({inner_str} != nil)"
            case BinaryOp(op="in", left=left, right=right):
                return self._containment_check(left, right, negated=False)
            case BinaryOp(op="not in", left=left, right=right):
                return self._containment_check(left, right, negated=True)
            case BinaryOp(op=op, left=left, right=right):
                left_str = self._expr(left)
                right_str = self._expr(right)
                swift_op = _binary_op(op)
                return f"{left_str} {swift_op} {right_str}"
            case UnaryOp(op="&", operand=operand):
                inner = self._expr(operand)
                if operand.typ and _is_mutable_value_type(operand.typ):
                    return f"&{inner}"
                return inner
            case UnaryOp(op="*", operand=operand):
                return self._expr(operand)
            case UnaryOp(op=op, operand=operand):
                # Wrap operand in parens if it's a binary operation to ensure correct precedence
                operand_str = self._expr(operand)
                if isinstance(operand, BinaryOp):
                    operand_str = f"({operand_str})"
                return f"{op}{operand_str}"
            case Ternary(cond=cond, then_expr=then_expr, else_expr=else_expr):
                return f"({self._expr(cond)} ? {self._expr(then_expr)} : {self._expr(else_expr)})"
            case Cast(expr=inner, to_type=to_type):
                return self._cast(inner, to_type)
            case TypeAssert(expr=inner, asserted=asserted):
                type_name = self._type(asserted)
                inner_str = self._expr(inner)
                if expr.safe:
                    return f"({inner_str} as! {type_name})"
                return f"({inner_str} as! {type_name})"
            case IsType(expr=inner, tested_type=tested_type):
                type_name = self._type_name_for_check(tested_type)
                return f"({self._expr(inner)} is {type_name})"
            case IsNil(expr=inner, negated=negated):
                inner_str = self._expr(inner)
                if inner_str.endswith("!"):
                    inner_str = inner_str[:-1]
                if negated:
                    return f"{inner_str} != nil"
                return f"{inner_str} == nil"
            case Len(expr=inner):
                inner_str = self._expr(inner)
                inner_type = inner.typ
                if isinstance(inner_type, Optional):
                    inner_str = f"{inner_str}!"
                return f"{inner_str}.count"
            case MakeSlice(element_type=element_type, length=length, capacity=capacity):
                elem_type = self._type(element_type)
                if length:
                    default = self._default_value(element_type)
                    return f"[{elem_type}](repeating: {default}, count: {self._expr(length)})"
                return f"[{elem_type}]()"
            case MakeMap(key_type=key_type, value_type=value_type):
                kt = self._type(key_type)
                vt = self._type(value_type)
                return f"[{kt}: {vt}]()"
            case SliceLit(elements=elements, element_type=element_type):
                elems = ", ".join(self._expr(e) for e in elements)
                return f"[{elems}]"
            case MapLit(entries=entries, key_type=key_type, value_type=value_type):
                if not entries:
                    kt = self._type(key_type)
                    vt = self._type(value_type)
                    return f"[{kt}: {vt}]()"
                pairs = ", ".join(f"{self._expr(k)}: {self._expr(v)}" for k, v in entries)
                return f"[{pairs}]"
            case SetLit(elements=elements, element_type=element_type):
                elems = ", ".join(self._expr(e) for e in elements)
                return f"Set([{elems}])"
            case StructLit(struct_name=struct_name, fields=fields, embedded_value=embedded_value):
                return self._struct_lit(struct_name, fields, embedded_value)
            case TupleLit(elements=elements):
                elems = ", ".join(self._expr(e) for e in elements)
                return f"({elems})"
            case StringConcat(parts=parts):
                return " + ".join(self._expr(p) for p in parts)
            case StringFormat(template=template, args=args):
                return self._format_string(template, args)
            case CharLit(value=value):
                return str(ord(value))
            case CharAt(string=s, index=index):
                s_str = self._expr(s)
                idx_str = self._expr(index)
                return f"Int(_charAt({s_str}, {idx_str}).unicodeScalars.first!.value)"
            case CharLen(string=s):
                return f"{self._expr(s)}.count"
            case Substring(string=s, low=low, high=high):
                s_str = self._expr(s)
                if low and high:
                    lo = self._expr(low)
                    hi = self._expr(high)
                    return f"String({s_str}[{s_str}.index({s_str}.startIndex, offsetBy: {lo})..<{s_str}.index({s_str}.startIndex, offsetBy: min({hi}, {s_str}.count))])"
                elif low:
                    lo = self._expr(low)
                    return f"String({s_str}.dropFirst({lo}))"
                elif high:
                    hi = self._expr(high)
                    return f"String({s_str}.prefix({hi}))"
                return s_str
            case LastElement(sequence=seq):
                return f"{self._expr(seq)}.last!"
            case SliceConvert(source=source, target_element_type=target_elem):
                return self._expr(source)
            case SentinelToOptional(expr=e, sentinel=sentinel):
                e_str = self._expr(e)
                sentinel_str = self._expr(sentinel)
                return f"({e_str} == {sentinel_str} ? nil : {e_str})"
            case Args():
                return "CommandLine.arguments"
            case GetEnv(name=name, default=default):
                name_str = self._expr(name)
                if default:
                    default_str = self._expr(default)
                    return f"(ProcessInfo.processInfo.environment[{name_str}] ?? {default_str})"
                return f"ProcessInfo.processInfo.environment[{name_str}]"
            case ReadLine():
                return 'readLine() ?? ""'
            case ReadAll():
                return "readAllStdin()"
            case ListComp(element=element, target=target, iterable=iterable, condition=condition):
                iter_str = self._expr(iterable)
                elem_str = self._expr(element)
                var = _safe_name(target)
                if condition:
                    cond_str = self._expr(condition)
                    return f"{iter_str}.filter {{ {var} in {cond_str} }}.map {{ {var} in {elem_str} }}"
                return f"{iter_str}.map {{ {var} in {elem_str} }}"
            case SetComp(element=element, target=target, iterable=iterable, condition=condition):
                iter_str = self._expr(iterable)
                elem_str = self._expr(element)
                var = _safe_name(target)
                if condition:
                    cond_str = self._expr(condition)
                    return f"Set({iter_str}.filter {{ {var} in {cond_str} }}.map {{ {var} in {elem_str} }})"
                return f"Set({iter_str}.map {{ {var} in {elem_str} }})"
            case DictComp(key=key, value=value, target=target, iterable=iterable, condition=condition):
                iter_str = self._expr(iterable)
                key_str = self._expr(key)
                val_str = self._expr(value)
                var = _safe_name(target)
                if condition:
                    cond_str = self._expr(condition)
                    return f"Dictionary(uniqueKeysWithValues: {iter_str}.filter {{ {var} in {cond_str} }}.map {{ {var} in ({key_str}, {val_str}) }})"
                return f"Dictionary(uniqueKeysWithValues: {iter_str}.map {{ {var} in ({key_str}, {val_str}) }})"
            case _:
                return "nil /* TODO: unknown expression */"

    def _emit_arg(self, arg: Expr) -> str:
        """Emit an argument expression, adding & for inout (Pointer-to-value-type) args."""
        s = self._expr(arg)
        if isinstance(arg.typ, Pointer) and _is_mutable_value_type(arg.typ.target) and not s.startswith("&"):
            return f"&{s}"
        return s

    def _call(self, func: str, args: list[Expr]) -> str:
        args_str = ", ".join(self._emit_arg(a) for a in args)
        if func == "int" and len(args) == 2:
            return f"Int({self._expr(args[0])}, radix: {self._expr(args[1])})!"
        if func == "str":
            if args and isinstance(args[0].typ, Slice):
                elem_type = args[0].typ.element
                if isinstance(elem_type, Primitive) and elem_type.kind == "byte":
                    return f"String(bytes: {self._expr(args[0])}, encoding: .utf8)!"
            return f"String({self._expr(args[0])})"
        if func == "len":
            arg = self._expr(args[0])
            return f"{arg}.count"
        if func == "range":
            return f"range({args_str})"
        if func == "ord":
            arg = self._expr(args[0])
            return f"Int({arg}.unicodeScalars.first!.value)"
        if func == "chr":
            return f"String(Character(UnicodeScalar({self._expr(args[0])})!))"
        if func == "abs":
            return f"abs({self._expr(args[0])})"
        if func == "min":
            return f"min({args_str})"
        if func == "max":
            return f"max({args_str})"
        if func in ("_intPtr", "_int_ptr"):
            return self._expr(args[0])
        if func in self._throwing_funcs or func in self._func_params:
            self._expr_has_try = True
        return f"{_safe_name(func)}({args_str})"

    def _method_call(self, obj: Expr, method: str, args: list[Expr], receiver_type: Type) -> str:
        args_str = ", ".join(self._emit_arg(a) for a in args)
        obj_str = self._expr(obj)
        if isinstance(receiver_type, Optional):
            obj_str = f"{obj_str}!"
            receiver_type = receiver_type.inner
        if isinstance(receiver_type, Slice):
            if method == "append" and args:
                return f"{obj_str}.append({args_str})"
            if method == "extend" and args:
                return f"{obj_str}.append(contentsOf: {args_str})"
            if method == "pop":
                if args:
                    idx = self._expr(args[0])
                    if isinstance(args[0], IntLit) and args[0].value == 0:
                        return f"{obj_str}.removeFirst()"
                    return f"{obj_str}.remove(at: {idx})"
                return f"{obj_str}.removeLast()"
            if method == "copy":
                return f"Swift.Array({obj_str})"
            if method == "insert":
                # insert(index, value) -> insert(value, at: index)
                if len(args) == 2:
                    idx = self._expr(args[0])
                    val = self._expr(args[1])
                    return f"{obj_str}.insert({val}, at: {idx})"
        if isinstance(receiver_type, Primitive) and receiver_type.kind == "string":
            if method == "startswith":
                if len(args) == 2:
                    prefix_str = self._expr(args[0])
                    pos_str = self._expr(args[1])
                    return f"String({obj_str}.dropFirst({pos_str})).hasPrefix({prefix_str})"
                return f"{obj_str}.hasPrefix({args_str})"
            if method == "endswith":
                if args and isinstance(args[0], TupleLit):
                    checks = [f"{obj_str}.hasSuffix({self._expr(e)})" for e in args[0].elements]
                    return "(" + " || ".join(checks) + ")"
                return f"{obj_str}.hasSuffix({args_str})"
            if method == "find":
                if args:
                    needle = self._expr(args[0])
                    # Use distance(from:to:) for correct character index
                    return f"({obj_str}.range(of: {needle}).map {{ {obj_str}.distance(from: {obj_str}.startIndex, to: $0.lowerBound) }} ?? -1)"
                return f"({obj_str}.range(of: {args_str}).map {{ {obj_str}.distance(from: {obj_str}.startIndex, to: $0.lowerBound) }} ?? -1)"
            if method == "rfind":
                if args:
                    needle = self._expr(args[0])
                    return f"({obj_str}.range(of: {needle}, options: .backwards).map {{ {obj_str}.distance(from: {obj_str}.startIndex, to: $0.lowerBound) }} ?? -1)"
            if method == "replace":
                if len(args) == 2:
                    old = self._expr(args[0])
                    new = self._expr(args[1])
                    return f"{obj_str}.replacingOccurrences(of: {old}, with: {new})"
            if method == "split":
                # Swift split takes a Character or uses components(separatedBy:) for String
                return f"{obj_str}.components(separatedBy: {args_str})"
            if method == "join":
                return f"{args_str}.joined(separator: {obj_str})"
            if method == "lower":
                return f"{obj_str}.lowercased()"
            if method == "upper":
                return f"{obj_str}.uppercased()"
            if method == "strip":
                return f"{obj_str}.trimmingCharacters(in: .whitespacesAndNewlines)"
        if isinstance(receiver_type, Map):
            if method == "get" and len(args) == 2:
                key = self._expr(args[0])
                default = self._expr(args[1])
                return f"({obj_str}[{key}] ?? {default})"
            if method == "keys":
                return f"Swift.Array({obj_str}.keys)"
            if method == "values":
                return f"Swift.Array({obj_str}.values)"
        if isinstance(receiver_type, Set):
            if method == "add":
                return f"{obj_str}.insert({args_str})"
            if method == "remove":
                return f"{obj_str}.remove({args_str})"
            if method == "contains":
                return f"{obj_str}.contains({args_str})"
        # Fallback translations for Python method names
        if method == "endswith":
            return f"{obj_str}.hasSuffix({args_str})"
        if method == "startswith":
            if len(args) == 2:
                prefix_str = self._expr(args[0])
                pos_str = self._expr(args[1])
                return f"String({obj_str}.dropFirst({pos_str})).hasPrefix({prefix_str})"
            return f"{obj_str}.hasPrefix({args_str})"
        if method == "join":
            return f"{args_str}.joined(separator: {obj_str})"
        if method in self._throwing_funcs:
            self._expr_has_try = True
        return f"{obj_str}.{_safe_name(method)}({args_str})"

    def _slice_expr(self, obj: Expr, low: Expr | None, high: Expr | None) -> str:
        obj_str = self._expr(obj)
        obj_type = obj.typ
        if isinstance(obj_type, Primitive) and obj_type.kind == "string":
            if low and high:
                lo = self._expr(low)
                hi = self._expr(high)
                return f"String({obj_str}[{obj_str}.index({obj_str}.startIndex, offsetBy: {lo})..<{obj_str}.index({obj_str}.startIndex, offsetBy: min({hi}, {obj_str}.count))])"
            elif low:
                lo = self._expr(low)
                return f"String({obj_str}.dropFirst({lo}))"
            elif high:
                hi = self._expr(high)
                return f"String({obj_str}.prefix({hi}))"
            return obj_str
        # Array slicing
        if low and high:
            return f"Swift.Array({obj_str}[({self._expr(low)})..<({self._expr(high)})])"
        elif low:
            return f"Swift.Array({obj_str}[({self._expr(low)})...])"
        elif high:
            return f"Swift.Array({obj_str}[..<({self._expr(high)})])"
        return f"Swift.Array({obj_str})"

    def _containment_check(self, item: Expr, container: Expr, negated: bool) -> str:
        item_str = self._expr(item)
        container_str = self._expr(container)
        container_type = container.typ
        neg = "!" if negated else ""
        if isinstance(container_type, Set):
            return f"{neg}{container_str}.contains({item_str})"
        if isinstance(container_type, Map):
            return f"({container_str}[{item_str}] {'==' if negated else '!='} nil)"
        if isinstance(container_type, Primitive) and container_type.kind == "string":
            return f"{neg}{container_str}.contains({item_str})"
        return f"{neg}{container_str}.contains({item_str})"

    def _cast(self, inner: Expr, to_type: Type) -> str:
        inner_str = self._expr(inner)
        swift_type = self._type(to_type)
        inner_type = inner.typ
        if isinstance(to_type, Primitive):
            if to_type.kind == "int":
                if isinstance(inner_type, Primitive) and inner_type.kind == "float":
                    return f"Int({inner_str})"
                if isinstance(inner_type, Primitive) and inner_type.kind == "string":
                    return f"Int({inner_str})!"
                return inner_str
            if to_type.kind == "float":
                if isinstance(inner_type, Primitive) and inner_type.kind == "int":
                    return f"Double({inner_str})"
                return inner_str
            if to_type.kind == "string":
                if isinstance(inner_type, Slice):
                    elem = inner_type.element
                    if isinstance(elem, Primitive) and elem.kind == "byte":
                        return f"String(bytes: {inner_str}, encoding: .utf8)!"
                if isinstance(inner_type, Primitive) and inner_type.kind == "rune":
                    return f"String(Character(UnicodeScalar({inner_str})!))"
                return f"String({inner_str})"
            if to_type.kind == "rune":
                if isinstance(inner_type, Primitive) and inner_type.kind == "string":
                    return f"Int({inner_str}.unicodeScalars.first!.value)"
                return inner_str
            if to_type.kind == "byte":
                if isinstance(inner_type, Primitive) and inner_type.kind == "int":
                    return f"UInt8({inner_str})"
                if isinstance(inner_type, Primitive) and inner_type.kind == "string":
                    return f"UInt8({inner_str}.unicodeScalars.first!.value)"
                if isinstance(inner_type, Primitive) and inner_type.kind == "rune":
                    return f"UInt8({inner_str})"
                return f"UInt8({inner_str})"
        # String to bytes conversion
        if isinstance(to_type, Slice) and isinstance(to_type.element, Primitive) and to_type.element.kind == "byte":
            if isinstance(inner_type, Primitive) and inner_type.kind == "string":
                return f"Swift.Array({inner_str}.utf8)"
        return f"({inner_str} as! {swift_type})"

    def _format_string(self, template: str, args: list[Expr]) -> str:
        result = template
        # Handle {0}, {1} style placeholders
        for i, arg in enumerate(args):
            if isinstance(arg, StringLit):
                val = arg.value.replace("\\", "\\\\")
                result = result.replace(f"{{{i}}}", val, 1)
            else:
                result = result.replace(f"{{{i}}}", f"\\({self._expr(arg)})", 1)
        # Handle %v placeholders
        arg_idx = 0
        while "%v" in result:
            if arg_idx >= len(args):
                break
            arg = args[arg_idx]
            arg_idx += 1
            if isinstance(arg, StringLit):
                val = arg.value.replace("\\", "\\\\")
                result = result.replace("%v", val, 1)
            else:
                result = result.replace("%v", f"\\({self._expr(arg)})", 1)
        escaped = escape_string(result)
        return f'"{escaped}"'

    def _struct_lit(self, struct_name: str, fields: dict[str, Expr], embedded_value: Expr | None) -> str:
        safe_name = _safe_type_name(struct_name)
        field_info = self.struct_fields.get(struct_name, [])
        if field_info:
            ordered_args = []
            for field_name, field_type in field_info:
                param_name = _safe_name(field_name)
                if field_name in fields:
                    field_val = fields[field_name]
                    # NilLit for collection fields should use empty collection, not nil
                    if isinstance(field_val, NilLit) and isinstance(field_type, (Slice, Array, Map, Set)):
                        ordered_args.append(f"{param_name}: {self._default_value(field_type)}")
                    else:
                        ordered_args.append(f"{param_name}: {self._expr(field_val)}")
                else:
                    default = self._default_value(field_type)
                    ordered_args.append(f"{param_name}: {default}")
            return f"{safe_name}({', '.join(ordered_args)})"
        elif embedded_value is not None:
            if isinstance(embedded_value, StructLit):
                parent_args = ", ".join(f"{_safe_name(k)}: {self._expr(v)}" for k, v in embedded_value.fields.items())
                return f"{safe_name}({parent_args})"
            return f"{safe_name}({self._expr(embedded_value)})"
        elif not fields:
            return f"{safe_name}()"
        else:
            args = ", ".join(f"{_safe_name(k)}: {self._expr(v)}" for k, v in fields.items())
            return f"{safe_name}({args})"

    def _tuple_type_with_nil(self, typ: Tuple, lit: TupleLit) -> str:
        """Emit a tuple type, making elements optional where the literal has nil."""
        parts = []
        for i, elem_type in enumerate(typ.elements):
            t = self._type(elem_type)
            if i < len(lit.elements) and isinstance(lit.elements[i], NilLit) and not t.endswith("?"):
                t += "?"
            parts.append(t)
        return f"({', '.join(parts)})"

    def _lvalue(self, lv: LValue) -> str:
        match lv:
            case VarLV(name=name):
                if name == self.receiver_name:
                    return "self"
                return _safe_name(name)
            case FieldLV(obj=obj, field=field):
                obj_str = self._expr(obj)
                if isinstance(obj.typ, Optional):
                    obj_str = f"{obj_str}!"
                return f"{obj_str}.{_safe_name(field)}"
            case IndexLV(obj=obj, index=index):
                return f"{self._expr(obj)}[{self._expr(index)}]"
            case DerefLV(ptr=ptr):
                return self._expr(ptr)
            case _:
                return "nil /* lvalue: unknown */"

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
                types = ", ".join(self._type(t) for t in elements)
                return f"({types})"
            case Pointer(target=target):
                # Pointers just map to the target type (classes are reference types)
                return self._type(target)
            case Optional(inner=inner):
                inner_type = self._type(inner)
                return f"{inner_type}?"
            case StructRef(name=name):
                return _safe_type_name(name)
            case InterfaceRef(name=name):
                if name == "any":
                    return "Any"
                return _safe_type_name(name)
            case Union(name=name):
                if name:
                    return _safe_type_name(name)
                return "Any"
            case FuncType(params=params, ret=ret):
                if not params:
                    return f"() throws -> {self._type(ret)}"
                param_types = ", ".join(self._type(p) for p in params)
                return f"({param_types}) throws -> {self._type(ret)}"
            case _:
                return "Any"

    def _type_name_for_check(self, typ: Type) -> str:
        match typ:
            case StructRef(name=name):
                return _safe_type_name(name)
            case InterfaceRef(name=name):
                return _safe_type_name(name)
            case Pointer(target=target):
                return self._type_name_for_check(target)
            case _:
                return self._type(typ)

    def _element_type(self, typ: Type) -> str:
        match typ:
            case Optional(inner=inner):
                return self._element_type(inner)
            case Slice(element=element):
                return self._type(element)
            case Array(element=element):
                return self._type(element)
            case _:
                return "Any"

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
            case Slice(element=element):
                return "[]"
            case Tuple(elements=elements):
                defaults = ", ".join(self._default_value(t) for t in elements)
                return f"({defaults})"
            case Optional():
                return "nil"
            case Pointer():
                return "nil"  # Pointers can be nil
            case Map():
                return "[:]"
            case Set():
                return "Set()"
            case StructRef(name=name):
                return f"{_safe_type_name(name)}()"
            case InterfaceRef():
                return "nil"  # Can't instantiate protocols
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
            return "Int"
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


def _can_throw(stmts: list[Stmt]) -> bool:
    """Check if a list of statements contains a Raise not caught by TryCatch."""
    for s in stmts:
        if isinstance(s, Raise):
            return True
        if isinstance(s, If):
            if _can_throw(s.then_body) or _can_throw(s.else_body):
                return True
        elif isinstance(s, (While, ForRange, ForClassic)):
            if _can_throw(s.body):
                return True
        elif isinstance(s, Block):
            if _can_throw(s.body):
                return True
        elif isinstance(s, TypeSwitch):
            for c in s.cases:
                if _can_throw(c.body):
                    return True
            if s.default and _can_throw(s.default):
                return True
        elif isinstance(s, Match):
            for c in s.cases:
                if _can_throw(c.body):
                    return True
            if s.default and _can_throw(s.default):
                return True
        elif isinstance(s, TryCatch):
            # Raises inside try body are caught, but catch body can re-throw
            if _can_throw(s.catch_body):
                return True
    return False


def _calls_any(stmts: list[Stmt], func_names: set[str]) -> bool:
    """Check if statements contain a call to any of the named functions."""
    for s in stmts:
        if _stmt_calls_any(s, func_names):
            return True
    return False


def _stmt_calls_any(s: Stmt, names: set[str]) -> bool:
    """Check if a statement calls any of the named functions."""
    if isinstance(s, (ExprStmt, Return)):
        expr = s.expr if isinstance(s, ExprStmt) else s.value
        if expr and _expr_calls_any(expr, names):
            return True
    elif isinstance(s, (VarDecl, Assign)):
        val = s.value
        if val and _expr_calls_any(val, names):
            return True
    elif isinstance(s, OpAssign):
        if _expr_calls_any(s.value, names):
            return True
    elif isinstance(s, TupleAssign):
        if _expr_calls_any(s.value, names):
            return True
    elif isinstance(s, Print):
        if _expr_calls_any(s.value, names):
            return True
    elif isinstance(s, Raise):
        if s.message and _expr_calls_any(s.message, names):
            return True
        if s.pos and _expr_calls_any(s.pos, names):
            return True
    elif isinstance(s, If):
        return _calls_any(s.then_body, names) or _calls_any(s.else_body, names)
    elif isinstance(s, (While, ForRange, ForClassic)):
        return _calls_any(s.body, names)
    elif isinstance(s, Block):
        return _calls_any(s.body, names)
    elif isinstance(s, TypeSwitch):
        for c in s.cases:
            if _calls_any(c.body, names):
                return True
        if s.default and _calls_any(s.default, names):
            return True
    elif isinstance(s, Match):
        for c in s.cases:
            if _calls_any(c.body, names):
                return True
        if s.default and _calls_any(s.default, names):
            return True
    elif isinstance(s, TryCatch):
        # Calls in try body are handled, but catch body propagates
        if _calls_any(s.catch_body, names):
            return True
    return False


def _expr_calls_any(e: Expr, names: set[str]) -> bool:
    """Check if an expression calls any of the named functions."""
    if isinstance(e, Call):
        if e.func in names:
            return True
        return any(_expr_calls_any(a, names) for a in e.args)
    if isinstance(e, MethodCall):
        if e.method in names:
            return True
        if _expr_calls_any(e.obj, names):
            return True
        return any(_expr_calls_any(a, names) for a in e.args)
    if isinstance(e, StaticCall):
        return any(_expr_calls_any(a, names) for a in e.args)
    if isinstance(e, BinaryOp):
        return _expr_calls_any(e.left, names) or _expr_calls_any(e.right, names)
    if isinstance(e, UnaryOp):
        return _expr_calls_any(e.operand, names)
    if isinstance(e, Ternary):
        return _expr_calls_any(e.cond, names) or _expr_calls_any(e.then_expr, names) or _expr_calls_any(e.else_expr, names)
    return False


def _expr_can_be_nil(expr: Expr, nil_funcs: set[str] | None = None) -> bool:
    """Check if an expression can produce nil."""
    if isinstance(expr, NilLit):
        return True
    if isinstance(expr, Ternary):
        return _expr_can_be_nil(expr.then_expr, nil_funcs) or _expr_can_be_nil(expr.else_expr, nil_funcs)
    if nil_funcs:
        if isinstance(expr, Call) and expr.func in nil_funcs:
            return True
        if isinstance(expr, MethodCall) and expr.method in nil_funcs:
            return True
    return False


def _is_mutable_value_type(typ: Type) -> bool:
    """Check if a type is a mutable value type in Swift (needs var for mutation)."""
    if isinstance(typ, Optional):
        return _is_mutable_value_type(typ.inner)
    if isinstance(typ, Pointer):
        return _is_mutable_value_type(typ.target)
    return isinstance(typ, (Slice, Array, Map, Set))


def _returns_nil(stmts: list[Stmt]) -> bool:
    """Check if statements contain a return-nil (SoftFail or Return(NilLit))."""
    for s in stmts:
        if isinstance(s, SoftFail):
            return True
        if isinstance(s, Return) and isinstance(s.value, NilLit):
            return True
        if isinstance(s, If):
            if _returns_nil(s.then_body) or _returns_nil(s.else_body):
                return True
        elif isinstance(s, (While, ForRange, ForClassic)):
            if _returns_nil(s.body):
                return True
        elif isinstance(s, Block):
            if _returns_nil(s.body):
                return True
        elif isinstance(s, TypeSwitch):
            for c in s.cases:
                if _returns_nil(c.body):
                    return True
            if s.default and _returns_nil(s.default):
                return True
        elif isinstance(s, Match):
            for c in s.cases:
                if _returns_nil(c.body):
                    return True
            if s.default and _returns_nil(s.default):
                return True
        elif isinstance(s, TryCatch):
            if _returns_nil(s.body) or _returns_nil(s.catch_body):
                return True
    return False


def _is_string_type(typ: Type) -> bool:
    return isinstance(typ, Primitive) and typ.kind == "string"
