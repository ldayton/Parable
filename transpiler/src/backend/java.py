"""Java backend: IR → Java code.

COMPENSATIONS FOR EARLIER STAGE DEFICIENCIES
============================================

Frontend deficiencies (should be fixed in frontend.py):
- FieldAccess for "this._arith_parse_*" is special-cased to emit lambda syntax
  "() -> this.method()" - frontend should emit FuncRef IR for bound method
  references instead of FieldAccess.
- String character classification methods (isalnum, isdigit, etc.) are translated
  inline to Java streams - frontend should emit generic IR that backends map to
  stdlib, not Python method names that each backend must recognize.
- SliceConvert IR node is not handled - either frontend shouldn't emit it for
  Java-targeted code, or this backend needs to implement covariant conversion.
- VAR_TYPE_OVERRIDES and FIELD_TYPE_OVERRIDES imported from src/type_overrides
  are workarounds for Python's weak/missing type annotations. Frontend should
  infer types from usage patterns rather than requiring manual override tables.
  Backend shouldn't need to consult these - IR should have complete types.
- Loop variable types in ForRange sometimes fall back to "Object" when element
  type is unknown - frontend should infer element types from iterable types and
  include them in the IR.
- Marker variables "_skip_docstring", "_pass", "_skip_super_init" require filtering.
  Frontend should use a dedicated NoOp IR node or not emit these.

Middleend deficiencies (should be fixed in middleend.py):
- None identified. Middleend correctly passes through type information; the gaps
  originate in frontend's inability to infer types from Python source.

UNCOMPENSATED DEFICIENCIES (non-idiomatic output)
=================================================

The dominant issue is char vs String conflation. Python has only strings; Java
distinguishes char (primitive) from String (object). The backend now detects
single-char string comparisons and emits `s.charAt(i) == '('` instead of
`String.valueOf(s.charAt(i)).equals("(")`. However, multi-char comparisons and
helper predicates still use String-based patterns.
Idiomatic Java would:
  1. Track character vs string semantics in frontend
  2. Emit char type for single-character literals and charAt() results
  3. Use primitive `==` for char comparisons instead of .equals()
  4. Emit `isDigit(char)` instead of `_isDigit(String)`
Downstream consequences of this missing analysis:
  - ~175 remaining String.valueOf() calls for non-comparison contexts
  - Helper predicates take String instead of char: `_isWhitespace(String)`
    should be `Character.isWhitespace(char)` (~356 helper call sites)

Frontend deficiencies (should be fixed in frontend.py):
- Factory field overwrites: `ParseError self = new ParseError("", 0, 0);` then
  assigns each field. Frontend should emit constructor calls or StructLit. (~7 factories)
- Nullable fields without Optional: fields used with null but declared as bare
  types. Frontend should emit Optional wrapper for nullable fields. (~47 fields)
- Complex iteration patterns: `IntStream.iterate(n-1, _x -> _x < -1, _x -> _x + -1)`
  instead of `for (int i = n-1; i >= 0; i--)`. Frontend should emit ForClassic. (~7 sites)
- Exception types not in IR: TryCatch catches generic `Exception` instead of
  specific types like `ParseError`. Frontend should include exception type. (~7 sites)
- Last-element access: `list.get(list.size() - 1)` instead of `list.getLast()`.
  Frontend could emit Index with -1 sentinel that backend maps to getLast(). (~19 sites)

Middleend deficiencies (should be fixed in middleend.py):
- Unnecessary casts: `((Node) w).toSexp()` when w's type is already known to
  implement Node. Middleend should track precise types. (~70 casts)

Backend deficiencies (Java-specific, fixable in java.py):
- None identified yet. Current issues stem from frontend/middleend gaps.
"""

from __future__ import annotations

from src.backend.util import escape_string, to_camel, to_pascal, to_screaming_snake
from src.type_overrides import FIELD_TYPE_OVERRIDES, VAR_TYPE_OVERRIDES

# Java reserved words that need escaping
_JAVA_RESERVED = frozenset(
    {
        "abstract",
        "assert",
        "boolean",
        "break",
        "byte",
        "case",
        "catch",
        "char",
        "class",
        "const",
        "continue",
        "default",
        "do",
        "double",
        "else",
        "enum",
        "extends",
        "final",
        "finally",
        "float",
        "for",
        "goto",
        "if",
        "implements",
        "import",
        "instanceof",
        "int",
        "interface",
        "long",
        "native",
        "new",
        "package",
        "private",
        "protected",
        "public",
        "return",
        "short",
        "static",
        "strictfp",
        "super",
        "switch",
        "synchronized",
        "this",
        "throw",
        "throws",
        "transient",
        "try",
        "void",
        "volatile",
        "while",
        "true",
        "false",
        "null",
        "_",  # Java 9+ keyword for unused variables
    }
)

# Java standard library classes that conflict with user-defined types
_JAVA_STDLIB_CLASSES = frozenset(
    {
        "List",
        "Map",
        "Set",
        "String",
        "Integer",
        "Boolean",
        "Double",
        "Float",
        "Long",
        "Short",
        "Byte",
        "Character",
        "Object",
        "Class",
        "System",
        "Runtime",
        "Thread",
        "Exception",
        "Error",
        "Throwable",
        "Optional",
    }
)


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
    OpAssign,
    Optional,
    Param,
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


def _java_register_tuple(backend: "JavaBackend", typ: Tuple) -> None:
    """Register a tuple type in the backend's tuple records."""
    sig = tuple(backend._type(t) for t in typ.elements)
    if sig not in backend.tuple_records:
        backend.tuple_counter += 1
        backend.tuple_records[sig] = f"Tuple{backend.tuple_counter}"


def _java_visit_type(backend: "JavaBackend", typ: Type | None) -> None:
    """Visit a type and register any tuples found."""
    if typ is None:
        return
    if isinstance(typ, Tuple):
        _java_register_tuple(backend, typ)
        for elem in typ.elements:
            _java_visit_type(backend, elem)
    elif isinstance(typ, Slice):
        _java_visit_type(backend, typ.element)
    elif isinstance(typ, Optional):
        _java_visit_type(backend, typ.inner)
    elif isinstance(typ, Pointer):
        _java_visit_type(backend, typ.target)
    elif isinstance(typ, Map):
        _java_visit_type(backend, typ.key)
        _java_visit_type(backend, typ.value)


def _java_visit_expr(backend: "JavaBackend", expr: Expr | None) -> None:
    """Visit an expression and collect tuple types."""
    if expr is None:
        return
    expr_typ = expr.typ if isinstance(expr, (Var, Call, MethodCall, StaticCall, FieldAccess, Index, SliceExpr, BinaryOp, UnaryOp, Ternary, Cast, TypeAssert, Len, MakeSlice, MakeMap, SliceLit, MapLit, SetLit, StructLit, TupleLit, StringConcat, StringFormat, IsType, IsNil)) else None
    if expr_typ is not None:
        _java_visit_type(backend, expr_typ)
    if isinstance(expr, (FieldAccess, Index, SliceExpr, UnaryOp, Cast, TypeAssert, Len, IsType, IsNil)):
        if isinstance(expr, FieldAccess):
            _java_visit_expr(backend, expr.obj)
        elif isinstance(expr, Index):
            _java_visit_expr(backend, expr.obj)
            _java_visit_expr(backend, expr.index)
        elif isinstance(expr, SliceExpr):
            _java_visit_expr(backend, expr.obj)
            _java_visit_expr(backend, expr.low)
            _java_visit_expr(backend, expr.high)
        elif isinstance(expr, UnaryOp):
            _java_visit_expr(backend, expr.operand)
        elif isinstance(expr, Cast):
            _java_visit_expr(backend, expr.expr)
        elif isinstance(expr, TypeAssert):
            _java_visit_expr(backend, expr.expr)
        elif isinstance(expr, Len):
            _java_visit_expr(backend, expr.expr)
        elif isinstance(expr, IsType):
            _java_visit_expr(backend, expr.expr)
        elif isinstance(expr, IsNil):
            _java_visit_expr(backend, expr.expr)
    elif isinstance(expr, BinaryOp):
        _java_visit_expr(backend, expr.left)
        _java_visit_expr(backend, expr.right)
    elif isinstance(expr, Ternary):
        _java_visit_expr(backend, expr.cond)
        _java_visit_expr(backend, expr.then_expr)
        _java_visit_expr(backend, expr.else_expr)
    elif isinstance(expr, (Call, MethodCall, StaticCall)):
        if isinstance(expr, MethodCall):
            _java_visit_expr(backend, expr.obj)
        for arg in expr.args:
            _java_visit_expr(backend, arg)
    elif isinstance(expr, MakeSlice):
        _java_visit_type(backend, expr.element_type)
        _java_visit_expr(backend, expr.length)
        _java_visit_expr(backend, expr.capacity)
    elif isinstance(expr, MakeMap):
        _java_visit_type(backend, expr.key_type)
        _java_visit_type(backend, expr.value_type)
    elif isinstance(expr, SliceLit):
        _java_visit_type(backend, expr.element_type)
        for elem in expr.elements:
            _java_visit_expr(backend, elem)
    elif isinstance(expr, MapLit):
        _java_visit_type(backend, expr.key_type)
        _java_visit_type(backend, expr.value_type)
        for k, v in expr.entries:
            _java_visit_expr(backend, k)
            _java_visit_expr(backend, v)
    elif isinstance(expr, SetLit):
        _java_visit_type(backend, expr.element_type)
        for elem in expr.elements:
            _java_visit_expr(backend, elem)
    elif isinstance(expr, StructLit):
        for v in expr.fields.values():
            _java_visit_expr(backend, v)
    elif isinstance(expr, TupleLit):
        for elem in expr.elements:
            _java_visit_expr(backend, elem)
    elif isinstance(expr, StringConcat):
        for part in expr.parts:
            _java_visit_expr(backend, part)
    elif isinstance(expr, StringFormat):
        for arg in expr.args:
            _java_visit_expr(backend, arg)


def _java_visit_stmt(backend: "JavaBackend", stmt: Stmt) -> None:
    """Visit a statement and collect tuple types."""
    if isinstance(stmt, VarDecl):
        _java_visit_type(backend, stmt.typ)
        if stmt.value:
            _java_visit_expr(backend, stmt.value)
    elif isinstance(stmt, Assign):
        _java_visit_expr(backend, stmt.value)
    elif isinstance(stmt, OpAssign):
        _java_visit_expr(backend, stmt.value)
    elif isinstance(stmt, TupleAssign):
        _java_visit_expr(backend, stmt.value)
    elif isinstance(stmt, ExprStmt):
        _java_visit_expr(backend, stmt.expr)
    elif isinstance(stmt, Return):
        if stmt.value:
            _java_visit_expr(backend, stmt.value)
    elif isinstance(stmt, If):
        _java_visit_expr(backend, stmt.cond)
        if stmt.init:
            _java_visit_stmt(backend, stmt.init)
        for s in stmt.then_body:
            _java_visit_stmt(backend, s)
        for s in stmt.else_body:
            _java_visit_stmt(backend, s)
    elif isinstance(stmt, While):
        _java_visit_expr(backend, stmt.cond)
        for s in stmt.body:
            _java_visit_stmt(backend, s)
    elif isinstance(stmt, ForRange):
        _java_visit_expr(backend, stmt.iterable)
        for s in stmt.body:
            _java_visit_stmt(backend, s)
    elif isinstance(stmt, ForClassic):
        if stmt.init:
            _java_visit_stmt(backend, stmt.init)
        if stmt.cond:
            _java_visit_expr(backend, stmt.cond)
        if stmt.post:
            _java_visit_stmt(backend, stmt.post)
        for s in stmt.body:
            _java_visit_stmt(backend, s)
    elif isinstance(stmt, Block):
        for s in stmt.body:
            _java_visit_stmt(backend, s)
    elif isinstance(stmt, TryCatch):
        for s in stmt.body:
            _java_visit_stmt(backend, s)
        for s in stmt.catch_body:
            _java_visit_stmt(backend, s)
    elif isinstance(stmt, Match):
        _java_visit_expr(backend, stmt.expr)
        for case in stmt.cases:
            for s in case.body:
                _java_visit_stmt(backend, s)
        for s in stmt.default:
            _java_visit_stmt(backend, s)
    elif isinstance(stmt, TypeSwitch):
        _java_visit_expr(backend, stmt.expr)
        for case in stmt.cases:
            for s in case.body:
                _java_visit_stmt(backend, s)
        for s in stmt.default:
            _java_visit_stmt(backend, s)


class JavaBackend:
    """Emit Java code from IR."""

    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self.receiver_name: str | None = None
        self.current_class: str = ""
        self.tuple_records: dict[tuple[str, ...], str] = {}  # tuple signature -> record name
        self.tuple_counter = 0
        self.optional_tuples: set[tuple[str, ...]] = set()  # (T, bool) patterns -> use Optional<T>
        self.struct_fields: dict[
            str, list[tuple[str, Type]]
        ] = {}  # struct name -> [(field_name, type)]
        self.temp_counter: int = 0  # for unique temp variable names
        self._type_switch_binding_rename: dict[str, str] = {}  # binding -> narrowed name
        self._hoisted_vars: set[str] = set()  # Variables hoisted from control flow blocks
        self._current_func: str | None = None  # Current function name for type overrides
        self._func_params: set[str] = set()  # Function-typed parameter names
        self._module_name: str = ""  # Current module name

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
        self._hoisted_vars = set()
        self._type_switch_binding_rename = {}
        self._collect_struct_fields(module)
        self._collect_tuple_types(module)
        self._emit_module(module)
        return "\n".join(self.lines)

    def _emit_hoisted_vars(
        self, stmt: If | While | ForRange | ForClassic | TryCatch | Match | TypeSwitch
    ) -> None:
        """Emit declarations for hoisted variables before a control flow construct."""
        hoisted_vars = stmt.hoisted_vars
        for name, typ in hoisted_vars:
            java_type = self._type(typ) if typ else "Object"
            var_name = _java_safe_name(name)
            default = self._default_value(typ) if typ else "null"
            self._line(f"{java_type} {var_name} = {default};")
            self._hoisted_vars.add(name)

    def _collect_struct_fields(self, module: Module) -> None:
        """Collect field information for all structs."""
        for struct in module.structs:
            self.struct_fields[struct.name] = [(f.name, f.typ) for f in struct.fields]

    def _collect_tuple_types(self, module: Module) -> None:
        """Collect all unique tuple types used in the module."""
        # Visit all functions and methods
        for struct in module.structs:
            for method in struct.methods:
                _java_visit_type(self, method.ret)
                for param in method.params:
                    _java_visit_type(self, param.typ)
                for stmt in method.body:
                    _java_visit_stmt(self, stmt)
        for func in module.functions:
            _java_visit_type(self, func.ret)
            for param in func.params:
                _java_visit_type(self, param.typ)
            for stmt in func.body:
                _java_visit_stmt(self, stmt)

    def _line(self, text: str = "") -> None:
        if text:
            self.lines.append("    " * self.indent + text)
        else:
            self.lines.append("")

    def _emit_module(self, module: Module) -> None:
        self._line("import java.util.*;")
        self._line("")
        # Emit functional interface for () -> Node pattern
        self._line("@FunctionalInterface")
        self._line("interface NodeSupplier { Node call(); }")
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

    def _emit_tuple_record(self, name: str, sig: tuple[str, ...]) -> None:
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
        params = ", ".join(f"{self._type(f.typ)} {_java_safe_name(f.name)}" for f in struct.fields)
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
        # Emit _bytesToString helper for bytes.decode() calls
        self._line("")
        self._line("static String _bytesToString(List<Byte> bytes) {")
        self.indent += 1
        self._line("byte[] arr = new byte[bytes.size()];")
        self._line("for (int i = 0; i < bytes.size(); i++) arr[i] = bytes.get(i);")
        self._line("return new String(arr, java.nio.charset.StandardCharsets.UTF_8);")
        self.indent -= 1
        self._line("}")
        self.indent -= 1
        self._line("}")

    def _emit_function(self, func: Function) -> None:
        self._hoisted_vars = set()  # Reset for new function scope
        self._current_func = func.name  # Track for VAR_TYPE_OVERRIDES
        # Track function-typed parameters for proper call emission
        self._func_params = {p.name for p in func.params if isinstance(p.typ, FuncType)}
        params = self._params(func.params)
        ret = self._type(func.ret)
        name = to_camel(func.name)
        # Special case: _stringToBytes needs native implementation to avoid recursion
        if func.name == "_string_to_bytes":
            self._line(f"static {ret} {name}({params}) {{")
            self.indent += 1
            self._line("byte[] bytes = s.getBytes(java.nio.charset.StandardCharsets.UTF_8);")
            self._line("List<Byte> result = new ArrayList<>(bytes.length);")
            self._line("for (byte b : bytes) result.add(b);")
            self._line("return result;")
            self.indent -= 1
            self._line("}")
            return
        # Special case: _substring needs clamping to match Python slice semantics
        if func.name == "_substring":
            self._line(f"static {ret} {name}({params}) {{")
            self.indent += 1
            self._line("int len = s.length();")
            self._line("int clampedStart = Math.max(0, Math.min(start, len));")
            self._line("int clampedEnd = Math.max(clampedStart, Math.min(end, len));")
            self._line("return s.substring(clampedStart, clampedEnd);")
            self.indent -= 1
            self._line("}")
            return
        self._line(f"static {ret} {name}({params}) {{")
        self.indent += 1
        if not func.body:
            self._line('throw new UnsupportedOperationException("todo");')
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")
        self._current_func = None
        self._func_params = set()

    def _emit_method(self, func: Function) -> None:
        self._hoisted_vars = set()  # Reset for new function scope
        self._current_func = func.name  # Track for VAR_TYPE_OVERRIDES
        # Track function-typed parameters for proper call emission
        self._func_params = {p.name for p in func.params if isinstance(p.typ, FuncType)}
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
        self._current_func = None
        self._func_params = set()

    def _params(self, params: list[Param]) -> str:
        parts = []
        for p in params:
            typ = self._type(p.typ)
            parts.append(f"{typ} {_java_safe_name(p.name)}")
        return ", ".join(parts)

    def _emit_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDecl(name=name, typ=typ, value=value, mutable=mutable):
                # Check for type override
                override_key = (self._current_func, name) if self._current_func else None
                if override_key and override_key in VAR_TYPE_OVERRIDES:
                    java_type = self._type(VAR_TYPE_OVERRIDES[override_key])
                else:
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
                    target_name = target.name if isinstance(target, VarLV) else None
                    is_hoisted = target_name and target_name in self._hoisted_vars
                    if stmt.is_declaration and not is_hoisted:
                        # First assignment to variable - need type declaration
                        # Check for type override first
                        override_key = (
                            (self._current_func, target_name)
                            if self._current_func and target_name
                            else None
                        )
                        if override_key and override_key in VAR_TYPE_OVERRIDES:
                            java_type = self._type(VAR_TYPE_OVERRIDES[override_key])
                        else:
                            value_type = value.typ
                            if value_type is not None:
                                java_type = self._type(value_type)
                            else:
                                # Fallback to Object if type unknown
                                java_type = "Object"
                        self._line(f"{java_type} {lv} = {val};")
                    else:
                        self._line(f"{lv} = {val};")
            case OpAssign(target=target, op=op, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                self._line(f"{lv} {op}= {val};")
            case TupleAssign(targets=targets, value=value):
                # Java doesn't have destructuring - emit individual assignments
                val_str = self._expr(value)
                value_type = value.typ
                is_decl = stmt.is_declaration
                new_targets = stmt.new_targets
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
                        is_hoisted = target_name and target_name in self._hoisted_vars
                        if (
                            is_decl or (target_name and target_name in new_targets)
                        ) and not is_hoisted:
                            elem_type = (
                                self._type(value_type.elements[i])
                                if i < len(value_type.elements)
                                else "Object"
                            )
                            self._line(f"{elem_type} {lv} = {val_str}.f{i}();")
                        else:
                            self._line(f"{lv} = {val_str}.f{i}();")
                else:
                    # Fallback: treat as array index
                    for i, target in enumerate(targets):
                        lv = self._lvalue(target)
                        target_name = target.name if isinstance(target, VarLV) else None
                        is_hoisted = target_name and target_name in self._hoisted_vars
                        if (
                            is_decl or (target_name and target_name in new_targets)
                        ) and not is_hoisted:
                            self._line(f"Object {lv} = {val_str}[{i}];")
                        else:
                            self._line(f"{lv} = {val_str}[{i}];")
            case ExprStmt(expr=Var(name=name)) if name in (
                "_skip_docstring",
                "_pass",
                "_skip_super_init",
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
                self._emit_hoisted_vars(stmt)
                if init is not None:
                    self._emit_stmt(init)
                cond_str = self._expr(cond)
                # Fix pattern: !x != null -> x == null
                if cond_str.endswith(" != null") and cond_str.startswith("!"):
                    inner = cond_str[1:].replace(" != null", "")
                    cond_str = f"({inner} == null)"
                self._line(f"if ({cond_str}) {{")
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
                self._emit_type_switch(stmt, expr, binding, cases, default)
            case Match(expr=expr, cases=cases, default=default):
                self._emit_match(stmt, expr, cases, default)
            case ForRange(index=index, value=value, iterable=iterable, body=body):
                self._emit_for_range(stmt, index, value, iterable, body)
            case ForClassic(init=init, cond=cond, post=post, body=body):
                self._emit_for_classic(init, cond, post, body)
            case While(cond=cond, body=body):
                self._emit_hoisted_vars(stmt)
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
                # Check if this block should emit without braces (for statement sequences)
                no_scope = stmt.no_scope
                if not no_scope:
                    self._line("{")
                    self.indent += 1
                for s in body:
                    self._emit_stmt(s)
                if not no_scope:
                    self.indent -= 1
                    self._line("}")
            case TryCatch(body=body, catch_var=catch_var, catch_body=catch_body, reraise=reraise):
                self._emit_try_catch(stmt, body, catch_var, catch_body, reraise)
            case Raise(error_type=error_type, message=message, pos=pos):
                msg = self._expr(message)
                self._line(f"throw new RuntimeException({msg});")
            case SoftFail():
                self._line("return null;")
            case _:
                self._line("// TODO: unknown statement")

    def _emit_type_switch(
        self, stmt: Stmt, expr: Expr, binding: str, cases: list[TypeCase], default: list[Stmt]
    ) -> None:
        self._emit_hoisted_vars(stmt)
        var = self._expr(expr)
        bind_name = _java_safe_name(binding)
        # Don't re-declare if binding to same variable
        if not (isinstance(expr, Var) and _java_safe_name(expr.name) == bind_name):
            self._line(f"Object {bind_name} = {var};")
        for i, case in enumerate(cases):
            type_name = self._type_name_for_check(case.typ)
            # Create a narrowed binding name for pattern matching
            narrowed_name = f"{bind_name}{type_name.replace('Node', '')}"
            keyword = "if" if i == 0 else "} else if"
            # Use Java 16+ pattern matching: instanceof with binding
            self._line(f"{keyword} ({bind_name} instanceof {type_name} {narrowed_name}) {{")
            self.indent += 1
            # Set up renaming so references to binding use narrowed_name
            self._type_switch_binding_rename[binding] = narrowed_name
            # Save hoisted_vars - each case is a separate scope, hoisting in one
            # case shouldn't affect declarations in other cases
            saved_hoisted = self._hoisted_vars.copy()
            for s in case.body:
                self._emit_stmt(s)
            self._hoisted_vars = saved_hoisted
            self._type_switch_binding_rename.pop(binding)
            self.indent -= 1
        if default:
            self._line("} else {")
            self.indent += 1
            saved_hoisted = self._hoisted_vars.copy()
            for s in default:
                self._emit_stmt(s)
            self._hoisted_vars = saved_hoisted
            self.indent -= 1
        self._line("}")

    def _emit_match(self, stmt: Stmt, expr: Expr, cases: list[MatchCase], default: list[Stmt]) -> None:
        self._emit_hoisted_vars(stmt)
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
        stmt: Stmt,
        index: str | None,
        value: str | None,
        iterable: Expr,
        body: list[Stmt],
    ) -> None:
        self._emit_hoisted_vars(stmt)
        iter_expr = self._expr(iterable)
        iter_type = iterable.typ
        # Look up field type from FIELD_TYPE_OVERRIDES when iter_type is None
        if iter_type is None and isinstance(iterable, FieldAccess):
            field_key = (self.current_class, iterable.field)
            if field_key in FIELD_TYPE_OVERRIDES:
                iter_type = FIELD_TYPE_OVERRIDES[field_key]
        is_string = isinstance(iter_type, Primitive) and iter_type.kind == "string"
        if value is not None and index is not None:
            # Need index - use traditional for loop
            idx = _java_safe_name(index)
            val = _java_safe_name(value)
            if is_string:
                self._line(f"for (int {idx} = 0; {idx} < {iter_expr}.length(); {idx}++) {{")
                self.indent += 1
                self._line(f"String {val} = String.valueOf({iter_expr}.charAt({idx}));")
            else:
                self._line(f"for (int {idx} = 0; {idx} < {iter_expr}.size(); {idx}++) {{")
                self.indent += 1
                elem_type = self._element_type(iter_type)
                # Check VAR_TYPE_OVERRIDES for loop variable when element type is unknown
                if elem_type == "Object" and self._current_func and value:
                    override_key = (self._current_func, value)
                    if override_key in VAR_TYPE_OVERRIDES:
                        elem_type = self._type(VAR_TYPE_OVERRIDES[override_key])
                self._line(f"{elem_type} {val} = {iter_expr}.get({idx});")
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        elif value is not None:
            val = _java_safe_name(value)
            if is_string:
                # String iteration needs index-based loop
                self._line(f"for (int _i = 0; _i < {iter_expr}.length(); _i++) {{")
                self.indent += 1
                self._line(f"String {val} = String.valueOf({iter_expr}.charAt(_i));")
            else:
                elem_type = self._element_type(iter_type)
                # Check if iterating over range() - element type is Integer
                if isinstance(iterable, Call) and iterable.func == "range":
                    elem_type = "Integer"
                # Check VAR_TYPE_OVERRIDES for loop variable when element type is unknown
                if elem_type == "Object" and self._current_func and value:
                    override_key = (self._current_func, value)
                    if override_key in VAR_TYPE_OVERRIDES:
                        elem_type = self._type(VAR_TYPE_OVERRIDES[override_key])
                self._line(f"for ({elem_type} {val} : {iter_expr}) {{")
                self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        elif index is not None:
            idx = _java_safe_name(index)
            if is_string:
                self._line(f"for (int {idx} = 0; {idx} < {iter_expr}.length(); {idx}++) {{")
            else:
                self._line(f"for (int {idx} = 0; {idx} < {iter_expr}.size(); {idx}++) {{")
            self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        else:
            if is_string:
                self._line(f"for (int _i = 0; _i < {iter_expr}.length(); _i++) {{")
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
        stmt: Stmt,
        body: list[Stmt],
        catch_var: str | None,
        catch_body: list[Stmt],
        reraise: bool,
    ) -> None:
        self._emit_hoisted_vars(stmt)
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
                # Check for type switch binding rename (use narrowed name)
                if name in self._type_switch_binding_rename:
                    return self._type_switch_binding_rename[name]
                # Check if this is a constant (all uppercase, or ClassName_CONSTANT pattern)
                if name.isupper() or (
                    name[0].isupper() and "_" in name and name.split("_", 1)[1].isupper()
                ):
                    return f"Constants.{to_screaming_snake(name)}"
                return _java_safe_name(name)
            case FieldAccess(obj=obj, field=field):
                obj_str = self._expr(obj)
                # Tuple record fields are accessed as methods in Java records
                # Field names F0/f0, F1/f1, etc. are tuple field accessors - use method syntax
                lower_field = field.lower()
                if (
                    lower_field.startswith("f")
                    and len(lower_field) > 1
                    and lower_field[1:].isdigit()
                ):
                    return f"{obj_str}.{lower_field}()"
                # For .kind on Node interface, use getKind() method
                obj_type = obj.typ
                if field == "kind" and isinstance(obj_type, (InterfaceRef, StructRef)):
                    return f"{obj_str}.getKind()"
                # Method reference on self: _arith_parse_* -> () -> this._arithParse*()
                # This handles bound method references in Python that are passed as callbacks
                if obj_str == "this" and field.startswith("_arith_parse_"):
                    return f"() -> this.{to_camel(field)}()"
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
                    # int(s, base) -> Long.parseLong then cast to int (handles overflow)
                    return f"(int) Long.parseLong({args_str})"
                if func == "_parseInt":
                    # Frontend generates _parseInt for int(s, base)
                    # Use Long.parseLong to handle numbers larger than Integer.MAX_VALUE
                    return f"(int) Long.parseLong({args_str})"
                if func == "str":
                    # Check if converting bytes to string (List<Byte>)
                    if args and isinstance(args[0].typ, Slice):
                        elem_type = args[0].typ.element
                        if isinstance(elem_type, Primitive) and elem_type.kind == "byte":
                            return f"ParableFunctions._bytesToString({args_str})"
                    return f"String.valueOf({args_str})"
                if func == "len":
                    arg = self._expr(args[0])
                    arg_type = args[0].typ
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
                        # Detect negative step to use correct comparison
                        # For negative step: iterate while _x > stop
                        # For positive step: iterate while _x < stop
                        step_arg = args[2]
                        is_negative_step = (
                            isinstance(step_arg, IntLit) and step_arg.value < 0
                        ) or (
                            isinstance(step_arg, UnaryOp)
                            and step_arg.op == "-"
                            and isinstance(step_arg.operand, IntLit)
                        )
                        cmp = ">" if is_negative_step else "<"
                        return f"java.util.stream.IntStream.iterate({start}, _x -> _x {cmp} {stop}, _x -> _x + {step}).boxed().toList()"
                if func == "ord":
                    return f"(int) ({self._expr(args[0])}.charAt(0))"
                if func == "chr":
                    return f"new String(Character.toChars({self._expr(args[0])}))"
                if func == "abs":
                    return f"Math.abs({args_str})"
                if func == "min":
                    return f"Math.min({args_str})"
                if func == "max":
                    return f"Math.max({args_str})"
                # Helper functions for Go pointer boxing - inline in Java
                if func == "_intPtr" or func == "_int_ptr":
                    # Java auto-boxes int to Integer
                    return f"({self._expr(args[0])})"
                if func == "_intToStr" or func == "_int_to_str":
                    return f"String.valueOf({self._expr(args[0])})"
                # Check if calling a function-typed parameter
                if func in self._func_params:
                    return f"{func}.call()"
                # Module-level functions are in {ModuleName}Functions class
                func_class = f"{to_pascal(self._module_name)}Functions"
                return f"{func_class}.{to_camel(func)}({args_str})"
            case MethodCall(
                obj=obj, method=method, args=[TupleLit(elements=elements)], receiver_type=_
            ) if method in ("startswith", "endswith"):
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
                right_str = self._expr(right)
                # Pattern: !x != null (from Python's "not x" on nullable)
                # Convert to: x == null
                if java_op == "!=" and right_str == "null":
                    if isinstance(left, UnaryOp) and left.op == "!":
                        return f"({self._expr(left.operand)} == null)"
                    # Also check the generated string as a fallback
                    left_str_tmp = self._expr(left)
                    if left_str_tmp.startswith("!"):
                        # Strip the leading ! and use == null
                        return f"({left_str_tmp[1:]} == null)"
                # Detect len(x) > 0 -> !x.isEmpty(), len(x) == 0 -> x.isEmpty()
                if isinstance(left, Len) and isinstance(right, IntLit) and right.value == 0:
                    inner_str = self._expr(left.expr)
                    if java_op == ">" or java_op == "!=":
                        return f"!{inner_str}.isEmpty()"
                    if java_op == "==":
                        return f"{inner_str}.isEmpty()"
                    if java_op == "<=":
                        return f"{inner_str}.isEmpty()"
                # Compare _parseInt result as long to avoid int overflow before comparison
                # e.g., int(s) <= 2147483647 -> Long.parseLong(s, 10) <= 2147483647L
                if (
                    isinstance(left, Call)
                    and left.func == "_parseInt"
                    and java_op in ("<=", "<", ">", ">=")
                    and isinstance(right, IntLit)
                ):
                    args_str = ", ".join(self._expr(a) for a in left.args)
                    return f"Long.parseLong({args_str}) {java_op} {right.value}L"
                # Char comparison: s.charAt(i) == 'c' instead of String.valueOf(...).equals(...)
                # Pattern: Index(string, i) == StringLit(single_char) or Cast(Index(...)) == StringLit
                if (
                    java_op in ("==", "!=")
                    and isinstance(right, StringLit)
                    and len(right.value) == 1
                ):
                    # Unwrap Cast if present (frontend wraps string indexing in Cast)
                    inner_left = left.expr if isinstance(left, Cast) else left
                    if isinstance(inner_left, Index):
                        obj_type = inner_left.obj.typ
                        if isinstance(obj_type, Primitive) and obj_type.kind == "string":
                            obj_str = self._expr(inner_left.obj)
                            idx_str = self._expr(inner_left.index)
                            char_lit = _char_literal(right.value)
                            if java_op == "==":
                                return f"{obj_str}.charAt({idx_str}) == {char_lit}"
                            else:
                                return f"{obj_str}.charAt({idx_str}) != {char_lit}"
                left_str = self._expr(left)
                right_str = self._expr(right)
                # String comparison needs .equals() or .compareTo()
                if java_op == "==" and _is_string_type(left.typ):
                    return f"{left_str}.equals({right_str})"
                if java_op == "!=" and _is_string_type(left.typ):
                    return f"!{left_str}.equals({right_str})"
                if java_op == "<" and _is_string_type(left.typ):
                    return f"({left_str}.compareTo({right_str}) < 0)"
                if java_op == "<=" and _is_string_type(left.typ):
                    return f"({left_str}.compareTo({right_str}) <= 0)"
                if java_op == ">" and _is_string_type(left.typ):
                    return f"({left_str}.compareTo({right_str}) > 0)"
                if java_op == ">=" and _is_string_type(left.typ):
                    return f"({left_str}.compareTo({right_str}) >= 0)"
                # Bitwise operators need parens due to low precedence
                if java_op in ("&", "|", "^"):
                    return f"({left_str} {java_op} {right_str})"
                # Add parens around || when inside && to preserve precedence
                if java_op == "&&":
                    if isinstance(left, BinaryOp) and left.op == "||":
                        left_str = f"({left_str})"
                    if isinstance(right, BinaryOp) and right.op == "||":
                        right_str = f"({right_str})"
                return f"{left_str} {java_op} {right_str}"
            case UnaryOp(op="&", operand=operand):
                return self._expr(operand)  # Java passes objects by reference
            case UnaryOp(op="*", operand=operand):
                return self._expr(operand)  # Java has no pointer dereference
            case UnaryOp(op="!", operand=operand):
                # Java ! only works on booleans; for ints, use == 0
                operand_type = operand.typ
                if isinstance(operand_type, Primitive) and operand_type.kind == "int":
                    return f"({self._expr(operand)} == 0)"
                # For object types (not primitive bool), Python "not x" means "x is falsy/null"
                if isinstance(operand_type, (InterfaceRef, StructRef, Pointer)):
                    return f"({self._expr(operand)} == null)"
                # Check for bitwise & operand (result is int even if typ not set)
                if isinstance(operand, BinaryOp) and operand.op == "&":
                    return f"({self._expr(operand)} == 0)"
                # Check for arithmetic ops (e.g., !pos + 1) - result is int
                if isinstance(operand, BinaryOp) and operand.op in (
                    "+",
                    "-",
                    "*",
                    "/",
                    "%",
                    "|",
                    "^",
                ):
                    return f"({self._expr(operand)} == 0)"
                # Check for Var with unknown type - if name looks like an object var, use null check
                if isinstance(operand, Var) and operand_type is None:
                    # Heuristic: lowercase names are typically objects, not booleans
                    return f"({self._expr(operand)} == null)"
                # For complex operands (BinaryOp), wrap in parens to avoid precedence issues
                # e.g., Python's `not (a < b)` should be `!(a < b)` not `!a < b`
                if isinstance(operand, BinaryOp):
                    return f"!({self._expr(operand)})"
                return f"!{self._expr(operand)}"
            case UnaryOp(op=op, operand=operand):
                return f"{op}{self._expr(operand)}"
            case Ternary(cond=cond, then_expr=then_expr, else_expr=else_expr):
                # When else is null but then is a list, use empty ArrayList instead
                else_str = self._expr(else_expr)
                if isinstance(else_expr, NilLit) and isinstance(then_expr.typ, Slice):
                    else_str = "new ArrayList<>()"
                # Wrap in parens to avoid precedence issues (?: has very low precedence in Java)
                return f"({self._expr(cond)} ? {self._expr(then_expr)} : {else_str})"
            case Cast(expr=inner, to_type=to_type):
                return self._cast(inner, to_type)
            case TypeAssert(expr=inner, asserted=asserted, safe=safe):
                type_name = self._type(asserted)
                return f"(({type_name}) {self._expr(inner)})"
            case IsType(expr=inner, tested_type=tested_type):
                type_name = self._type_name_for_check(tested_type)
                return f"({self._expr(inner)} instanceof {type_name})"
            case IsNil(expr=inner, negated=negated):
                # Special case: !x != null (where x is an object) should be just x == null
                # This handles Python's "not x" being translated to IsNil(UnaryOp("!", x), negated=True)
                if negated and isinstance(inner, UnaryOp) and inner.op == "!":
                    inner_type = inner.operand.typ
                    if (
                        isinstance(inner_type, (InterfaceRef, StructRef, Pointer))
                        or inner_type is None
                    ):
                        return f"({self._expr(inner.operand)} == null)"
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
                # List.of() doesn't allow nulls - use Arrays.asList() which does
                return f"new ArrayList<>(Arrays.asList({elems}))"
            case MapLit(entries=entries, key_type=key_type, value_type=value_type):
                if not entries:
                    return "new HashMap<>()"
                # Map.of() only supports up to 10 entries; use ofEntries for more
                if len(entries) <= 10:
                    pairs = ", ".join(f"{self._expr(k)}, {self._expr(v)}" for k, v in entries)
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
                            field_val = fields[field_name]
                            # Handle null for int fields - use -1 sentinel
                            if (
                                isinstance(field_val, NilLit)
                                and isinstance(field_type, Primitive)
                                and field_type.kind == "int"
                            ):
                                ordered_args.append("-1")
                            # Handle null for list fields - use empty ArrayList
                            elif isinstance(field_val, NilLit) and isinstance(field_type, Slice):
                                ordered_args.append("new ArrayList<>()")
                            else:
                                ordered_args.append(self._expr(field_val))
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
                return "null /* TODO: unknown expression */"

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
                    return f'{obj_str}.replaceFirst("^[" + {args_str} + "]+", "")'
                return f"{obj_str}.stripLeading()"
            if method == "rstrip":
                if args:
                    # rstrip with chars argument - use regex
                    return f'{obj_str}.replaceFirst("[" + {args_str} + "]+$", "")'
                return f"{obj_str}.stripTrailing()"
            if method == "lower":
                return f"{obj_str}.toLowerCase()"
            if method == "upper":
                return f"{obj_str}.toUpperCase()"
            if method == "isalpha":
                return f"({obj_str}.length() > 0 && {obj_str}.chars().allMatch(Character::isLetter))"
            if method == "isalnum":
                return f"({obj_str}.length() > 0 && {obj_str}.chars().allMatch(Character::isLetterOrDigit))"
            if method == "isdigit":
                return f"({obj_str}.length() > 0 && {obj_str}.chars().allMatch(Character::isDigit))"
            if method == "isspace":
                return f"({obj_str}.length() > 0 && {obj_str}.chars().allMatch(Character::isWhitespace))"
        # Handle Map.get with default value -> getOrDefault
        if isinstance(receiver_type, Map):
            if method == "get" and len(args) == 2:
                key = self._expr(args[0])
                default = self._expr(args[1])
                return f"{obj_str}.getOrDefault({key}, {default})"
        # Handle bytes.decode() -> convert List<Byte> to String
        if method == "decode":
            return f"ParableFunctions._bytesToString({obj_str})"
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
        # Fallback for string methods when receiver_type is unknown
        if method == "isalnum":
            return f"({obj_str}.length() > 0 && {obj_str}.chars().allMatch(Character::isLetterOrDigit))"
        if method == "isalpha":
            return f"({obj_str}.length() > 0 && {obj_str}.chars().allMatch(Character::isLetter))"
        if method == "isdigit":
            return f"({obj_str}.length() > 0 && {obj_str}.chars().allMatch(Character::isDigit))"
        if method == "isspace":
            return f"({obj_str}.length() > 0 && {obj_str}.chars().allMatch(Character::isWhitespace))"
        if method == "endswith":
            return f"{obj_str}.endsWith({args_str})"
        if method == "startswith":
            return f"{obj_str}.startsWith({args_str})"
        # Fallback for join on non-string receiver (e.g., StringConcat)
        if method == "join":
            return f"String.join({obj_str}, {args_str})"
        # Cast to Node for toSexp() - this method only exists on Node interface
        if method == "to_sexp":
            return f"((Node) {obj_str}).toSexp()"
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
        container_type = container.typ
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
                # Handle List<Byte> -> String (decoding)
                inner_type = inner.typ
                if isinstance(inner_type, Slice):
                    if isinstance(inner_type.element, Primitive) and inner_type.element.kind == "byte":
                        return f"ParableFunctions._bytesToString({inner_str})"
                # Handle rune -> String (need to support supplementary codepoints)
                if isinstance(inner_type, Primitive) and inner_type.kind == "rune":
                    # The inner_str is (char) codepoint but we need to handle codepoints > 0xFFFF
                    # Extract the original codepoint expression and use Character.toChars
                    if isinstance(inner, Cast) and isinstance(inner.to_type, Primitive) and inner.to_type.kind == "rune":
                        codepoint_str = self._expr(inner.expr)
                        return f"new String(Character.toChars({codepoint_str}))"
                return f"String.valueOf({inner_str})"
        # Handle String -> List<Byte> (encoding)
        if isinstance(to_type, Slice):
            inner_type = inner.typ
            if isinstance(inner_type, Primitive) and inner_type.kind == "string":
                if isinstance(to_type.element, Primitive) and to_type.element.kind == "byte":
                    return f"ParableFunctions._stringToBytes({inner_str})"
        return f"(({java_type}) {inner_str})"

    def _format_string(self, template: str, args: list[Expr]) -> str:
        from re import sub as re_sub

        # Convert {0}, {1}, etc. to %s
        result = re_sub(r"\{\d+\}", "%s", template)
        result = result.replace("%v", "%s")
        escaped = (
            result.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )
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
                return "null /* lvalue: unknown */"

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
                # Use boxed type to allow null
                return _box_type(self._type(inner))
            case StructRef(name=name):
                return _java_safe_class(name)
            case InterfaceRef(name=name):
                if name == "any":
                    return "Object"
                return _java_safe_class(name)
            case Union(name=name, variants=variants):
                if name:
                    return _java_safe_class(name)
                return "Object"
            case FuncType(params=params, ret=ret):
                # Use NodeSupplier for () -> Node pattern
                if not params and isinstance(ret, (InterfaceRef, StructRef)):
                    return "NodeSupplier"
                return "Object"
            case _:
                return "Object"

    def _type_name_for_check(self, typ: Type) -> str:
        match typ:
            case StructRef(name=name):
                return _java_safe_class(name)
            case InterfaceRef(name=name):
                return _java_safe_class(name)
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
    # Also treat rune as string since Java converts it to String via String.valueOf()
    return isinstance(typ, Primitive) and typ.kind in ("string", "rune")


def _string_literal(value: str) -> str:
    return f'"{escape_string(value)}"'


def _char_literal(c: str) -> str:
    """Emit a Java char literal with proper escaping."""
    if c == "'":
        return "'\\''"
    if c == "\\":
        return "'\\\\'"
    if c == "\n":
        return "'\\n'"
    if c == "\r":
        return "'\\r'"
    if c == "\t":
        return "'\\t'"
    return f"'{c}'"
