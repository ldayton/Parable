"""C backend: IR → C11 code targeting GCC 13.

Memory model:
- Arena allocator for all heap allocations
- No individual frees - arena freed at end of parse() call
- Strings are borrowed pointers into input or arena-allocated copies

Error handling:
- Return-based errors (no setjmp/longjmp)
- Global error state (parable_parse_error, parable_error_msg)
- Parse functions return NULL on error
"""

from __future__ import annotations

from re import sub as re_sub

from src.backend.util import to_snake


def escape_string_c(value: str) -> str:
    """Escape a string for use in a C string literal (without quotes).

    Uses hex escapes for control characters instead of \\u which C doesn't allow.
    """
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
        .replace("\r", "\\r")
        .replace("\x01", "\\x01")
        .replace("\x7f", "\\x7f")
    )


from src.ir import (
    BOOL,
    BYTE,
    FLOAT,
    INT,
    RUNE,
    STRING,
    VOID,
    AddrOf,
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
    MethodSig,
    Module,
    NilLit,
    NoOp,
    OpAssign,
    Optional,
    Ownership,
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

# C reserved words that need renaming
_C_RESERVED = frozenset(
    {
        "auto",
        "break",
        "case",
        "char",
        "const",
        "continue",
        "default",
        "do",
        "double",
        "else",
        "enum",
        "extern",
        "float",
        "for",
        "goto",
        "if",
        "inline",
        "int",
        "long",
        "register",
        "restrict",
        "return",
        "short",
        "signed",
        "sizeof",
        "static",
        "struct",
        "switch",
        "typedef",
        "union",
        "unsigned",
        "void",
        "volatile",
        "while",
        "_Bool",
        "_Complex",
        "_Imaginary",
        "_Alignas",
        "_Alignof",
        "_Atomic",
        "_Generic",
        "_Noreturn",
        "_Static_assert",
        "_Thread_local",
        "bool",
        "true",
        "false",
        "NULL",
    }
)


def _safe_name(name: str) -> str:
    """Convert to snake_case and escape C reserved words, preserving leading underscores."""
    # Preserve leading underscore (important for private methods like _parse_compound_command)
    prefix = ""
    if name.startswith("_"):
        prefix = "_"
    result = to_snake(name)
    if result in _C_RESERVED:
        return prefix + result + "_"
    return prefix + result


def _type_name(name: str) -> str:
    """Convert struct/interface name to C type name (PascalCase preserved)."""
    # Keep original case for type names
    if name in _C_RESERVED:
        return name + "_"
    return name


class CBackend:
    """Emit C11 code from IR Module."""

    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self._receiver_name: str = ""
        self._receiver_type: str = ""
        self._hoisted_vars: dict[str, str] = {}  # name -> C type string
        self._current_return_type: Type = VOID
        self._module_name: str = ""
        self._struct_names: set[str] = set()
        self._interface_names: set[str] = set()
        self._tuple_types: set[str] = set()  # Track unique tuple type signatures
        self._slice_types: set[str] = set()  # Track unique slice element type names
        self._struct_fields: dict[str, list[tuple[str, Type]]] = {}
        self._interface_vars: set[str] = set()  # Variables declared as interface types
        self._constant_names: set[str] = set()  # Module-level constants (need uppercase)
        self._constant_set_values: dict[str, SetLit] = {}  # Set constant values for membership
        self._temp_counter: int = 0  # Counter for generating unique temp names
        self._function_sigs: dict[str, list[Type]] = {}  # Function name -> parameter types
        self._rvalue_temps: list[
            tuple[str, str, str]
        ] = []  # List of (struct_name, field_name, temp_name)
        self._deferred_constants: list[Constant] = []  # Constants needing runtime init
        self._try_catch_labels: list[str] = []  # Stack of goto labels for try-with-catch
        self._try_label_counter: int = 0

    def emit(self, module: Module) -> str:
        """Emit C code from IR Module."""
        self.indent = 0
        self.lines = []
        self._module_name = module.name
        self._struct_names = {s.name for s in module.structs}
        self._interface_names = {i.name for i in module.interfaces}
        self._kind_cache = {
            s.name: s.const_fields["kind"]
            for s in module.structs
            if "kind" in s.const_fields
        }
        self._tuple_types: dict[str, Tuple] = {}
        self._slice_types = set()
        self._struct_fields = {}
        self._constant_names = {c.name for c in module.constants}
        # Store SetLit values for constants to enable inline membership tests
        for c in module.constants:
            if isinstance(c.value, SetLit):
                self._constant_set_values[c.name] = c.value
        self._collect_struct_fields(module)
        self._collect_function_sigs(module)
        self._collect_tuple_types(module)
        self._collect_slice_types(module)
        self._emit_header()
        self._emit_forward_decls(module)
        self._emit_kind_constants(module)
        self._emit_helpers()
        self._emit_slice_typedefs()  # Vec types
        self._emit_tuple_types()  # Tuple types (may reference Vec types)
        self._emit_structs(module)
        self._emit_constants(module.constants)
        self._emit_function_decls(module)
        emitted_funcs: set[str] = set()  # Track emitted functions to avoid duplicates
        for func in module.functions:
            name = _safe_name(func.name)
            if name not in emitted_funcs:
                emitted_funcs.add(name)
                self._emit_function(func)
        for struct in module.structs:
            for method in struct.methods:
                method_name = f"{_type_name(struct.name)}_{_safe_name(method.name)}"
                if method_name not in emitted_funcs:
                    emitted_funcs.add(method_name)
                    self._emit_method(struct.name, method)
        self._emit_interface_dispatchers(module)
        return "\n".join(self.lines)

    def _collect_struct_fields(self, module: Module) -> None:
        """Collect field information for all structs."""
        for struct in module.structs:
            self._struct_fields[struct.name] = [(f.name, f.typ) for f in struct.fields]

    def _collect_function_sigs(self, module: Module) -> None:
        """Collect function signatures for interface parameter casting."""
        self._function_sigs = {}
        for func in module.functions:
            self._function_sigs[func.name] = [p.typ for p in func.params]
        for struct in module.structs:
            for method in struct.methods:
                # Methods are emitted as StructName_methodName
                method_name = f"{struct.name}_{method.name}"
                self._function_sigs[method_name] = [p.typ for p in method.params]

    def _collect_tuple_types(self, module: Module) -> None:
        """Scan module for tuple types to generate struct definitions."""
        for struct in module.structs:
            for f in struct.fields:
                self._visit_type_for_tuples(f.typ)
            for method in struct.methods:
                for p in method.params:
                    self._visit_type_for_tuples(p.typ)
                self._visit_type_for_tuples(method.ret)
                for s in method.body:
                    self._visit_stmt_for_tuples(s)
        for func in module.functions:
            for p in func.params:
                self._visit_type_for_tuples(p.typ)
            self._visit_type_for_tuples(func.ret)
            for s in func.body:
                self._visit_stmt_for_tuples(s)

    def _visit_type_for_tuples(self, typ: Type | None) -> None:
        """Visit a type to collect tuple type signatures."""
        if typ is None:
            return
        if isinstance(typ, Tuple):
            sig = self._tuple_sig(typ)
            self._tuple_types[sig] = typ
            for elem in typ.elements:
                self._visit_type_for_tuples(elem)
        elif isinstance(typ, Slice):
            self._visit_type_for_tuples(typ.element)
        elif isinstance(typ, Array):
            self._visit_type_for_tuples(typ.element)
        elif isinstance(typ, Map):
            self._visit_type_for_tuples(typ.key)
            self._visit_type_for_tuples(typ.value)
        elif isinstance(typ, Set):
            self._visit_type_for_tuples(typ.element)
        elif isinstance(typ, Optional):
            self._visit_type_for_tuples(typ.inner)
        elif isinstance(typ, Pointer):
            self._visit_type_for_tuples(typ.target)
        elif isinstance(typ, FuncType):
            for p in typ.params:
                self._visit_type_for_tuples(p)
            self._visit_type_for_tuples(typ.ret)

    def _visit_expr_for_tuples(self, expr: Expr | None) -> None:
        """Visit an expression to collect tuple type signatures."""
        if expr is None:
            return
        self._visit_type_for_tuples(expr.typ)
        if isinstance(expr, TupleLit):
            for e in expr.elements:
                self._visit_expr_for_tuples(e)
        elif isinstance(expr, Call):
            for a in expr.args:
                self._visit_expr_for_tuples(a)
        elif isinstance(expr, MethodCall):
            for a in expr.args:
                self._visit_expr_for_tuples(a)
        elif isinstance(expr, StaticCall):
            for a in expr.args:
                self._visit_expr_for_tuples(a)
        elif isinstance(expr, BinaryOp):
            self._visit_expr_for_tuples(expr.left)
            self._visit_expr_for_tuples(expr.right)
        elif isinstance(expr, UnaryOp):
            self._visit_expr_for_tuples(expr.operand)
        elif isinstance(expr, Ternary):
            self._visit_expr_for_tuples(expr.cond)
            self._visit_expr_for_tuples(expr.then_expr)
            self._visit_expr_for_tuples(expr.else_expr)
        elif isinstance(expr, Index):
            self._visit_expr_for_tuples(expr.obj)
            self._visit_expr_for_tuples(expr.index)
        elif isinstance(expr, SliceExpr):
            self._visit_expr_for_tuples(expr.obj)
            self._visit_expr_for_tuples(expr.low)
            self._visit_expr_for_tuples(expr.high)
        elif isinstance(expr, FieldAccess):
            self._visit_expr_for_tuples(expr.obj)
        elif isinstance(expr, Cast):
            self._visit_expr_for_tuples(expr.expr)
        elif isinstance(expr, TypeAssert):
            self._visit_expr_for_tuples(expr.expr)
        elif isinstance(expr, IsType):
            self._visit_expr_for_tuples(expr.expr)
        elif isinstance(expr, IsNil):
            self._visit_expr_for_tuples(expr.expr)
        elif isinstance(expr, Truthy):
            self._visit_expr_for_tuples(expr.expr)
        elif isinstance(expr, Len):
            self._visit_expr_for_tuples(expr.expr)
        elif isinstance(expr, SliceLit):
            for e in expr.elements:
                self._visit_expr_for_tuples(e)
        elif isinstance(expr, SetLit):
            for e in expr.elements:
                self._visit_expr_for_tuples(e)
        elif isinstance(expr, MapLit):
            for k, v in expr.entries:
                self._visit_expr_for_tuples(k)
                self._visit_expr_for_tuples(v)
        elif isinstance(expr, StructLit):
            for v in expr.fields.values():
                self._visit_expr_for_tuples(v)
        elif isinstance(expr, StringConcat):
            for p in expr.parts:
                self._visit_expr_for_tuples(p)
        elif isinstance(expr, StringFormat):
            for a in expr.args:
                self._visit_expr_for_tuples(a)

    def _visit_stmt_for_tuples(self, stmt: Stmt) -> None:
        """Visit a statement to collect tuple type signatures."""
        if isinstance(stmt, VarDecl):
            self._visit_type_for_tuples(stmt.typ)
            self._visit_expr_for_tuples(stmt.value)
        elif isinstance(stmt, Assign):
            self._visit_expr_for_tuples(stmt.value)
        elif isinstance(stmt, TupleAssign):
            self._visit_expr_for_tuples(stmt.value)
        elif isinstance(stmt, OpAssign):
            self._visit_expr_for_tuples(stmt.value)
        elif isinstance(stmt, ExprStmt):
            self._visit_expr_for_tuples(stmt.expr)
        elif isinstance(stmt, Return):
            self._visit_expr_for_tuples(stmt.value)
        elif isinstance(stmt, If):
            self._visit_expr_for_tuples(stmt.cond)
            for s in stmt.then_body:
                self._visit_stmt_for_tuples(s)
            for s in stmt.else_body:
                self._visit_stmt_for_tuples(s)
        elif isinstance(stmt, While):
            self._visit_expr_for_tuples(stmt.cond)
            for s in stmt.body:
                self._visit_stmt_for_tuples(s)
        elif isinstance(stmt, ForRange):
            self._visit_expr_for_tuples(stmt.iterable)
            for s in stmt.body:
                self._visit_stmt_for_tuples(s)
        elif isinstance(stmt, ForClassic):
            if stmt.init:
                self._visit_stmt_for_tuples(stmt.init)
            self._visit_expr_for_tuples(stmt.cond)
            if stmt.post:
                self._visit_stmt_for_tuples(stmt.post)
            for s in stmt.body:
                self._visit_stmt_for_tuples(s)
        elif isinstance(stmt, Block):
            for s in stmt.body:
                self._visit_stmt_for_tuples(s)
        elif isinstance(stmt, TryCatch):
            for s in stmt.body:
                self._visit_stmt_for_tuples(s)
            for s in stmt.catch_body:
                self._visit_stmt_for_tuples(s)
        elif isinstance(stmt, TypeSwitch):
            self._visit_expr_for_tuples(stmt.expr)
            for case in stmt.cases:
                self._visit_type_for_tuples(case.typ)
                for s in case.body:
                    self._visit_stmt_for_tuples(s)
            for s in stmt.default:
                self._visit_stmt_for_tuples(s)
        elif isinstance(stmt, Match):
            self._visit_expr_for_tuples(stmt.expr)
            for case in stmt.cases:
                for p in case.patterns:
                    self._visit_expr_for_tuples(p)
                for s in case.body:
                    self._visit_stmt_for_tuples(s)
            for s in stmt.default:
                self._visit_stmt_for_tuples(s)
        elif isinstance(stmt, Raise):
            self._visit_expr_for_tuples(stmt.message)
            self._visit_expr_for_tuples(stmt.pos)

    def _tuple_sig(self, typ: Tuple) -> str:
        """Generate a unique signature for a tuple type."""
        parts = []
        for elem in typ.elements:
            parts.append(self._type_to_c(elem))
        return "Tuple_" + "_".join(
            p.replace("*", "Ptr").replace(" ", "").replace("[", "Arr").replace("]", "")
            for p in parts
        )

    def _collect_slice_types(self, module: Module) -> None:
        """Scan module to collect all slice element types for typedef generation."""
        for struct in module.structs:
            for f in struct.fields:
                self._visit_type_for_slices(f.typ)
            for method in struct.methods:
                for p in method.params:
                    self._visit_type_for_slices(p.typ)
                self._visit_type_for_slices(method.ret)
                for s in method.body:
                    self._visit_stmt_for_slices(s)
        for func in module.functions:
            for p in func.params:
                self._visit_type_for_slices(p.typ)
            self._visit_type_for_slices(func.ret)
            for s in func.body:
                self._visit_stmt_for_slices(s)

    def _visit_type_for_slices(self, typ: Type | None) -> None:
        """Visit a type to collect slice element types."""
        if typ is None:
            return
        if isinstance(typ, Slice):
            sig = self._slice_elem_sig(typ.element)
            self._slice_types.add(sig)
            self._visit_type_for_slices(typ.element)
        elif isinstance(typ, Array):
            self._visit_type_for_slices(typ.element)
        elif isinstance(typ, Map):
            self._visit_type_for_slices(typ.key)
            self._visit_type_for_slices(typ.value)
        elif isinstance(typ, Set):
            self._visit_type_for_slices(typ.element)
        elif isinstance(typ, Optional):
            self._visit_type_for_slices(typ.inner)
        elif isinstance(typ, Pointer):
            self._visit_type_for_slices(typ.target)
        elif isinstance(typ, Tuple):
            for elem in typ.elements:
                self._visit_type_for_slices(elem)
        elif isinstance(typ, FuncType):
            for p in typ.params:
                self._visit_type_for_slices(p)
            self._visit_type_for_slices(typ.ret)

    def _visit_expr_for_slices(self, expr: Expr | None) -> None:
        """Visit an expression to collect slice types."""
        if expr is None:
            return
        self._visit_type_for_slices(expr.typ)
        if isinstance(expr, TupleLit):
            for e in expr.elements:
                self._visit_expr_for_slices(e)
        elif isinstance(expr, Call):
            for a in expr.args:
                self._visit_expr_for_slices(a)
        elif isinstance(expr, MethodCall):
            self._visit_expr_for_slices(expr.obj)
            for a in expr.args:
                self._visit_expr_for_slices(a)
        elif isinstance(expr, StaticCall):
            for a in expr.args:
                self._visit_expr_for_slices(a)
        elif isinstance(expr, BinaryOp):
            self._visit_expr_for_slices(expr.left)
            self._visit_expr_for_slices(expr.right)
        elif isinstance(expr, UnaryOp):
            self._visit_expr_for_slices(expr.operand)
        elif isinstance(expr, Ternary):
            self._visit_expr_for_slices(expr.cond)
            self._visit_expr_for_slices(expr.then_expr)
            self._visit_expr_for_slices(expr.else_expr)
        elif isinstance(expr, Index):
            self._visit_expr_for_slices(expr.obj)
            self._visit_expr_for_slices(expr.index)
        elif isinstance(expr, SliceExpr):
            self._visit_expr_for_slices(expr.obj)
            self._visit_expr_for_slices(expr.low)
            self._visit_expr_for_slices(expr.high)
        elif isinstance(expr, FieldAccess):
            self._visit_expr_for_slices(expr.obj)
        elif isinstance(expr, Cast):
            self._visit_expr_for_slices(expr.expr)
            self._visit_type_for_slices(expr.to_type)
        elif isinstance(expr, TypeAssert):
            self._visit_expr_for_slices(expr.expr)
        elif isinstance(expr, IsType):
            self._visit_expr_for_slices(expr.expr)
        elif isinstance(expr, IsNil):
            self._visit_expr_for_slices(expr.expr)
        elif isinstance(expr, Truthy):
            self._visit_expr_for_slices(expr.expr)
        elif isinstance(expr, Len):
            self._visit_expr_for_slices(expr.expr)
        elif isinstance(expr, SliceLit):
            for e in expr.elements:
                self._visit_expr_for_slices(e)
        elif isinstance(expr, SetLit):
            for e in expr.elements:
                self._visit_expr_for_slices(e)
        elif isinstance(expr, MapLit):
            for k, v in expr.entries:
                self._visit_expr_for_slices(k)
                self._visit_expr_for_slices(v)
        elif isinstance(expr, StructLit):
            for v in expr.fields.values():
                self._visit_expr_for_slices(v)
        elif isinstance(expr, StringConcat):
            for p in expr.parts:
                self._visit_expr_for_slices(p)
        elif isinstance(expr, StringFormat):
            for a in expr.args:
                self._visit_expr_for_slices(a)
        elif isinstance(expr, MakeSlice):
            self._visit_type_for_slices(expr.typ)

    def _visit_stmt_for_slices(self, stmt: Stmt) -> None:
        """Visit a statement to collect slice types."""
        if isinstance(stmt, VarDecl):
            self._visit_type_for_slices(stmt.typ)
            self._visit_expr_for_slices(stmt.value)
        elif isinstance(stmt, Assign):
            self._visit_expr_for_slices(stmt.value)
        elif isinstance(stmt, TupleAssign):
            self._visit_expr_for_slices(stmt.value)
        elif isinstance(stmt, OpAssign):
            self._visit_expr_for_slices(stmt.value)
        elif isinstance(stmt, ExprStmt):
            self._visit_expr_for_slices(stmt.expr)
        elif isinstance(stmt, Return):
            self._visit_expr_for_slices(stmt.value)
        elif isinstance(stmt, If):
            self._visit_expr_for_slices(stmt.cond)
            for s in stmt.then_body:
                self._visit_stmt_for_slices(s)
            for s in stmt.else_body:
                self._visit_stmt_for_slices(s)
        elif isinstance(stmt, While):
            self._visit_expr_for_slices(stmt.cond)
            for s in stmt.body:
                self._visit_stmt_for_slices(s)
        elif isinstance(stmt, ForRange):
            self._visit_expr_for_slices(stmt.iterable)
            for s in stmt.body:
                self._visit_stmt_for_slices(s)
        elif isinstance(stmt, ForClassic):
            if stmt.init:
                self._visit_stmt_for_slices(stmt.init)
            self._visit_expr_for_slices(stmt.cond)
            if stmt.post:
                self._visit_stmt_for_slices(stmt.post)
            for s in stmt.body:
                self._visit_stmt_for_slices(s)
        elif isinstance(stmt, Block):
            for s in stmt.body:
                self._visit_stmt_for_slices(s)
        elif isinstance(stmt, TryCatch):
            for s in stmt.body:
                self._visit_stmt_for_slices(s)
            for s in stmt.catch_body:
                self._visit_stmt_for_slices(s)
        elif isinstance(stmt, TypeSwitch):
            self._visit_expr_for_slices(stmt.expr)
            for case in stmt.cases:
                self._visit_type_for_slices(case.typ)
                for s in case.body:
                    self._visit_stmt_for_slices(s)
            for s in stmt.default:
                self._visit_stmt_for_slices(s)
        elif isinstance(stmt, Match):
            self._visit_expr_for_slices(stmt.expr)
            for case in stmt.cases:
                for p in case.patterns:
                    self._visit_expr_for_slices(p)
                for s in case.body:
                    self._visit_stmt_for_slices(s)
            for s in stmt.default:
                self._visit_stmt_for_slices(s)
        elif isinstance(stmt, Raise):
            self._visit_expr_for_slices(stmt.message)
            self._visit_expr_for_slices(stmt.pos)

    def _slice_elem_sig(self, elem: Type) -> str:
        """Generate a unique signature for a slice element type."""
        if isinstance(elem, Primitive):
            prim_map = {
                "string": "Str",
                "int": "Int",
                "bool": "Bool",
                "float": "Float",
                "byte": "Byte",
                "rune": "Rune",
                "void": "Void",
            }
            return prim_map.get(elem.kind, "Any")
        if isinstance(elem, StructRef):
            # Structs are passed by pointer, so []Foo becomes Vec of Foo*
            return elem.name
        if isinstance(elem, InterfaceRef):
            if elem.name == "any":
                return "Any"
            # Interfaces are also pointers
            return elem.name
        if isinstance(elem, Pointer):
            if isinstance(elem.target, StructRef):
                return elem.target.name
            if isinstance(elem.target, InterfaceRef):
                return elem.target.name
            inner = self._slice_elem_sig(elem.target)
            return inner
        if isinstance(elem, Slice):
            inner = self._slice_elem_sig(elem.element)
            return "Vec" + inner
        if isinstance(elem, Optional):
            return self._slice_elem_sig(elem.inner)
        if isinstance(elem, Tuple):
            # Use the tuple struct signature directly
            return self._tuple_sig(elem)
        return "Any"

    def _emit_slice_typedefs(self) -> None:
        """Emit typedefs for all slice types used."""
        if not self._slice_types:
            return
        # First emit forward decls for tuple types that are used in Vec elements
        tuple_fwd_needed = set()
        for sig in self._slice_types:
            if sig.startswith("Tuple_"):
                tuple_fwd_needed.add(sig)
        if tuple_fwd_needed:
            self._line("// === Tuple forward declarations for Vec element types ===")
            for sig in sorted(tuple_fwd_needed):
                self._line(f"typedef struct {sig} {sig};")
            self._line("")
        self._line("// === Slice (Vec) typedefs ===")
        for sig in sorted(self._slice_types):
            # Skip Byte - already defined in helpers for _str_to_bytes
            if sig == "Byte":
                continue
            elem_c = self._slice_sig_to_elem_type(sig)
            self._line(
                f"typedef struct Vec_{sig} {{ {elem_c} *data; size_t len; size_t cap; }} Vec_{sig};"
            )
        self._line("")
        # Emit string join helper if we have Vec_Str
        if "Str" in self._slice_types:
            self._line("static char *_str_join(Arena *a, const char *sep, Vec_Str vec) {")
            self._line('    if (vec.len == 0) return arena_strdup(a, "");')
            self._line("    size_t sep_len = strlen(sep);")
            self._line("    size_t total = 0;")
            self._line("    int first = 1;")
            self._line("    for (size_t i = 0; i < vec.len; i++) {")
            self._line("        if (!vec.data[i]) continue;")
            self._line("        if (!first) total += sep_len;")
            self._line("        total += strlen(vec.data[i]);")
            self._line("        first = 0;")
            self._line("    }")
            self._line('    if (first) return arena_strdup(a, "");')
            self._line("    char *result = (char *)arena_alloc(a, total + 1);")
            self._line("    char *p = result;")
            self._line("    first = 1;")
            self._line("    for (size_t i = 0; i < vec.len; i++) {")
            self._line("        if (!vec.data[i]) continue;")
            self._line("        if (!first) { memcpy(p, sep, sep_len); p += sep_len; }")
            self._line("        size_t len = strlen(vec.data[i]);")
            self._line("        memcpy(p, vec.data[i], len);")
            self._line("        p += len;")
            self._line("        first = 0;")
            self._line("    }")
            self._line("    *p = '\\0';")
            self._line("    return result;")
            self._line("}")
            self._line("")

    def _slice_sig_to_elem_type(self, sig: str) -> str:
        """Convert slice signature back to C element type."""
        prim_map = {
            "Str": "const char *",
            "Int": "int64_t",
            "Bool": "bool",
            "Float": "double",
            "Byte": "uint8_t",
            "Rune": "int32_t",
            "Void": "void",
            "Any": "void *",
        }
        if sig in prim_map:
            return prim_map[sig]
        # Struct/interface names - these are pointer types
        if sig in self._struct_names or sig in self._interface_names:
            return f"{sig} *"
        if sig.startswith("Vec"):
            inner = sig[3:]
            return f"Vec_{inner}"
        # Tuple types - already have Tuple_ prefix
        if sig.startswith("Tuple_"):
            return sig
        # Default to pointer type for unknown names
        return f"{sig} *"

    def _line(self, text: str = "") -> None:
        """Emit a line with current indentation."""
        if text:
            self.lines.append("    " * self.indent + text)
        else:
            self.lines.append("")

    def _temp_name(self, prefix: str) -> str:
        """Generate a unique temporary variable name."""
        self._temp_counter += 1
        return f"{prefix}{self._temp_counter}"

    @staticmethod
    def _is_zero_literal(expr: Expr) -> bool:
        """Check if an expression is the integer literal 0."""
        return isinstance(expr, IntLit) and expr.value == 0

    # ============================================================
    # HEADER AND HELPERS
    # ============================================================

    def _emit_header(self) -> None:
        """Emit includes and basic definitions."""
        self._line("// Generated by Tongues transpiler - C11 backend")
        self._line("#include <stdint.h>")
        self._line("#include <stdbool.h>")
        self._line("#include <stddef.h>")
        self._line("#include <stdlib.h>")
        self._line("#include <string.h>")
        self._line("#include <stdio.h>")
        self._line("#include <stdarg.h>")
        self._line("")
        self._line("// === Global error state ===")
        self._line("static int g_parse_error = 0;")
        self._line("static char g_error_msg[1024] = {0};")
        self._line("")

    def _emit_helpers(self) -> None:
        """Emit helper functions for string ops, arena, etc."""
        helpers = r"""
// === Generic 'any' interface type ===
// Used for interface{}/any types that need runtime type checking
typedef struct Any {
    int kind;
    void *data;
} Any;

// === Arena allocator (chunked, never reallocates) ===
typedef struct ArenaChunk {
    struct ArenaChunk *next;
    char *base;
    char *ptr;
    size_t cap;
} ArenaChunk;

typedef struct Arena {
    ArenaChunk *head;    // first chunk (for freeing)
    ArenaChunk *current; // current allocation chunk
    size_t chunk_size;   // default size for new chunks
} Arena;

static Arena *g_arena = NULL;
static bool g_initialized = false;

static ArenaChunk *arena_chunk_new(size_t cap) {
    ArenaChunk *c = (ArenaChunk *)malloc(sizeof(ArenaChunk));
    c->base = (char *)malloc(cap);
    c->ptr = c->base;
    c->cap = cap;
    c->next = NULL;
    return c;
}

static Arena *arena_new(size_t cap) {
    Arena *a = (Arena *)malloc(sizeof(Arena));
    a->head = arena_chunk_new(cap);
    a->current = a->head;
    a->chunk_size = cap;
    return a;
}

static void *arena_alloc(Arena *a, size_t size) {
    size = (size + 7) & ~7;  // 8-byte align
    ArenaChunk *c = a->current;
    if ((size_t)(c->ptr - c->base) + size > c->cap) {
        // Need new chunk - pick size that fits the allocation
        size_t new_cap = a->chunk_size;
        while (new_cap < size) new_cap *= 2;
        ArenaChunk *new_chunk = arena_chunk_new(new_cap);
        c->next = new_chunk;
        a->current = new_chunk;
        c = new_chunk;
    }
    void *result = c->ptr;
    c->ptr += size;
    return result;
}

static void arena_free(Arena *a) {
    if (a) {
        ArenaChunk *c = a->head;
        while (c) {
            ArenaChunk *next = c->next;
            free(c->base);
            free(c);
            c = next;
        }
        free(a);
    }
}

static void arena_reset(Arena *a) {
    // Reset all chunks to empty and set current back to head
    ArenaChunk *c = a->head;
    while (c) {
        c->ptr = c->base;
        c = c->next;
    }
    a->current = a->head;
}

static char *arena_strdup(Arena *a, const char *s) {
    size_t len = strlen(s);
    char *r = (char *)arena_alloc(a, len + 1);
    memcpy(r, s, len + 1);
    return r;
}

static char *arena_strndup(Arena *a, const char *s, size_t n) {
    char *r = (char *)arena_alloc(a, n + 1);
    memcpy(r, s, n);
    r[n] = '\0';
    return r;
}

static void init(void) {
    if (g_initialized) return;
    g_initialized = true;
    g_arena = arena_new(65536);
}

// === String helpers ===
static int32_t _rune_at(const char *s, int idx) {
    if (idx < 0 || !s) return -1;
    int i = 0;
    const unsigned char *u = (const unsigned char *)s;
    while (*u) {
        if (i == idx) {
            if (*u < 0x80) return *u;
            if ((*u & 0xE0) == 0xC0) return ((*u & 0x1F) << 6) | (u[1] & 0x3F);
            if ((*u & 0xF0) == 0xE0) return ((*u & 0x0F) << 12) | ((u[1] & 0x3F) << 6) | (u[2] & 0x3F);
            if ((*u & 0xF8) == 0xF0) return ((*u & 0x07) << 18) | ((u[1] & 0x3F) << 12) | ((u[2] & 0x3F) << 6) | (u[3] & 0x3F);
            return -1;
        }
        if (*u < 0x80) u++;
        else if ((*u & 0xE0) == 0xC0) u += 2;
        else if ((*u & 0xF0) == 0xE0) u += 3;
        else if ((*u & 0xF8) == 0xF0) u += 4;
        else u++;
        i++;
    }
    return -1;
}

static int _rune_len(const char *s) {
    if (!s) return 0;
    int len = 0;
    const unsigned char *u = (const unsigned char *)s;
    while (*u) {
        if (*u < 0x80) u++;
        else if ((*u & 0xE0) == 0xC0) u += 2;
        else if ((*u & 0xF0) == 0xE0) u += 3;
        else if ((*u & 0xF8) == 0xF0) u += 4;
        else u++;
        len++;
    }
    return len;
}

static char *_char_at_str(Arena *a, const char *s, int idx) {
    int32_t r = _rune_at(s, idx);
    if (r < 0) return arena_strdup(a, "");
    char buf[5] = {0};
    if (r < 0x80) { buf[0] = r; }
    else if (r < 0x800) { buf[0] = 0xC0 | (r >> 6); buf[1] = 0x80 | (r & 0x3F); }
    else if (r < 0x10000) { buf[0] = 0xE0 | (r >> 12); buf[1] = 0x80 | ((r >> 6) & 0x3F); buf[2] = 0x80 | (r & 0x3F); }
    else { buf[0] = 0xF0 | (r >> 18); buf[1] = 0x80 | ((r >> 12) & 0x3F); buf[2] = 0x80 | ((r >> 6) & 0x3F); buf[3] = 0x80 | (r & 0x3F); }
    return arena_strdup(a, buf);
}

static char *__c_substring(Arena *a, const char *s, int start, int end) {
    if (!s || start < 0) start = 0;
    if (end < start) return arena_strdup(a, "");
    const unsigned char *u = (const unsigned char *)s;
    const char *byte_start = NULL;
    const char *byte_end = NULL;
    int i = 0;
    while (*u) {
        if (i == start) byte_start = (const char *)u;
        if (i == end) { byte_end = (const char *)u; break; }
        if (*u < 0x80) u++;
        else if ((*u & 0xE0) == 0xC0) u += 2;
        else if ((*u & 0xF0) == 0xE0) u += 3;
        else if ((*u & 0xF8) == 0xF0) u += 4;
        else u++;
        i++;
    }
    if (!byte_start) return arena_strdup(a, "");
    if (!byte_end) byte_end = (const char *)u;
    return arena_strndup(a, byte_start, byte_end - byte_start);
}

static bool _str_startswith(const char *s, const char *prefix) {
    if (!s || !prefix) return false;
    size_t plen = strlen(prefix);
    return strncmp(s, prefix, plen) == 0;
}

static bool _str_startswith_at(const char *s, int64_t pos, const char *prefix) {
    if (!s || !prefix || pos < 0) return false;
    size_t slen = strlen(s);
    if ((size_t)pos >= slen) return false;
    size_t plen = strlen(prefix);
    if (slen - (size_t)pos < plen) return false;
    return strncmp(s + pos, prefix, plen) == 0;
}

static bool _str_endswith(const char *s, const char *suffix) {
    if (!s || !suffix) return false;
    size_t slen = strlen(s);
    size_t suflen = strlen(suffix);
    if (suflen > slen) return false;
    return strcmp(s + slen - suflen, suffix) == 0;
}

static int _str_find(const char *s, const char *sub) {
    if (!s || !sub) return -1;
    const char *p = strstr(s, sub);
    if (!p) return -1;
    // Return character index, not byte index
    int idx = 0;
    const unsigned char *u = (const unsigned char *)s;
    while ((const char *)u < p) {
        if (*u < 0x80) u++;
        else if ((*u & 0xE0) == 0xC0) u += 2;
        else if ((*u & 0xF0) == 0xE0) u += 3;
        else if ((*u & 0xF8) == 0xF0) u += 4;
        else u++;
        idx++;
    }
    return idx;
}

static int _str_rfind(const char *s, const char *sub) {
    if (!s || !sub) return -1;
    size_t slen = strlen(s);
    size_t sublen = strlen(sub);
    if (sublen > slen) return -1;
    for (size_t i = slen - sublen + 1; i > 0; i--) {
        if (strncmp(s + i - 1, sub, sublen) == 0) {
            // Return character index
            int idx = 0;
            const unsigned char *u = (const unsigned char *)s;
            while ((const char *)u < s + i - 1) {
                if (*u < 0x80) u++;
                else if ((*u & 0xE0) == 0xC0) u += 2;
                else if ((*u & 0xF0) == 0xE0) u += 3;
                else if ((*u & 0xF8) == 0xF0) u += 4;
                else u++;
                idx++;
            }
            return idx;
        }
    }
    return -1;
}

static char *_str_replace(Arena *a, const char *s, const char *old, const char *new_) {
    if (!s || !old || !new_) return arena_strdup(a, s ? s : "");
    size_t slen = strlen(s);
    size_t oldlen = strlen(old);
    size_t newlen = strlen(new_);
    if (oldlen == 0) return arena_strdup(a, s);
    // Count occurrences
    int count = 0;
    const char *p = s;
    while ((p = strstr(p, old)) != NULL) { count++; p += oldlen; }
    if (count == 0) return arena_strdup(a, s);
    size_t rlen = slen + count * (newlen - oldlen);
    char *r = (char *)arena_alloc(a, rlen + 1);
    char *dst = r;
    p = s;
    const char *prev = s;
    while ((p = strstr(p, old)) != NULL) {
        size_t n = p - prev;
        memcpy(dst, prev, n);
        dst += n;
        memcpy(dst, new_, newlen);
        dst += newlen;
        p += oldlen;
        prev = p;
    }
    strcpy(dst, prev);
    return r;
}

static char *_str_lower(Arena *a, const char *s) {
    if (!s) return arena_strdup(a, "");
    size_t len = strlen(s);
    char *r = (char *)arena_alloc(a, len + 1);
    for (size_t i = 0; i <= len; i++) {
        char c = s[i];
        if (c >= 'A' && c <= 'Z') c = c + 32;
        r[i] = c;
    }
    return r;
}

static char *_str_upper(Arena *a, const char *s) {
    if (!s) return arena_strdup(a, "");
    size_t len = strlen(s);
    char *r = (char *)arena_alloc(a, len + 1);
    for (size_t i = 0; i <= len; i++) {
        char c = s[i];
        if (c >= 'a' && c <= 'z') c = c - 32;
        r[i] = c;
    }
    return r;
}

static bool _str_is_digit(const char *s) {
    if (!s || !*s) return false;
    while (*s) {
        if (*s < '0' || *s > '9') return false;
        s++;
    }
    return true;
}

static bool _str_is_alpha(const char *s) {
    if (!s || !*s) return false;
    while (*s) {
        if (!((*s >= 'A' && *s <= 'Z') || (*s >= 'a' && *s <= 'z'))) return false;
        s++;
    }
    return true;
}

static bool _str_is_alnum(const char *s) {
    if (!s || !*s) return false;
    while (*s) {
        if (!((*s >= 'A' && *s <= 'Z') || (*s >= 'a' && *s <= 'z') || (*s >= '0' && *s <= '9'))) return false;
        s++;
    }
    return true;
}

static bool _str_is_space(const char *s) {
    if (!s || !*s) return false;
    while (*s) {
        if (*s != ' ' && *s != '\t' && *s != '\n' && *s != '\r' && *s != '\f' && *s != '\v') return false;
        s++;
    }
    return true;
}

static bool _rune_is_digit(int32_t r) { return r >= '0' && r <= '9'; }
static bool _rune_is_alpha(int32_t r) { return (r >= 'A' && r <= 'Z') || (r >= 'a' && r <= 'z'); }
static bool _rune_is_alnum(int32_t r) { return _rune_is_alpha(r) || _rune_is_digit(r); }
static bool _rune_is_space(int32_t r) { return r == ' ' || r == '\t' || r == '\n' || r == '\r' || r == '\f' || r == '\v'; }
static bool _rune_is_upper(int32_t r) { return r >= 'A' && r <= 'Z'; }
static bool _rune_is_lower(int32_t r) { return r >= 'a' && r <= 'z'; }

static char *_str_concat(Arena *a, const char *s1, const char *s2) {
    if (!s1) s1 = "";
    if (!s2) s2 = "";
    size_t len1 = strlen(s1);
    size_t len2 = strlen(s2);
    char *r = (char *)arena_alloc(a, len1 + len2 + 1);
    memcpy(r, s1, len1);
    memcpy(r + len1, s2, len2 + 1);
    return r;
}

static char *_str_repeat(Arena *a, const char *s, int n) {
    if (!s || n <= 0) return arena_strdup(a, "");
    size_t len = strlen(s);
    char *r = (char *)arena_alloc(a, len * n + 1);
    char *p = r;
    for (int i = 0; i < n; i++) { memcpy(p, s, len); p += len; }
    *p = '\0';
    return r;
}

static char *_str_trim(Arena *a, const char *s, const char *chars) {
    if (!s) return arena_strdup(a, "");
    const char *start = s;
    while (*start && strchr(chars, *start)) start++;
    if (!*start) return arena_strdup(a, "");
    const char *end = s + strlen(s) - 1;
    while (end > start && strchr(chars, *end)) end--;
    return arena_strndup(a, start, end - start + 1);
}

static char *_str_ltrim(Arena *a, const char *s, const char *chars) {
    if (!s) return arena_strdup(a, "");
    while (*s && strchr(chars, *s)) s++;
    return arena_strdup(a, s);
}

static char *_str_rtrim(Arena *a, const char *s, const char *chars) {
    if (!s || !*s) return arena_strdup(a, "");
    size_t len = strlen(s);
    while (len > 0 && strchr(chars, s[len - 1])) len--;
    return arena_strndup(a, s, len);
}

static int64_t _parse_int(const char *s, int base) {
    if (!s) return 0;
    return strtoll(s, NULL, base);
}

static char *_int_to_str(Arena *a, int64_t n) {
    char buf[32];
    snprintf(buf, sizeof(buf), "%lld", (long long)n);
    return arena_strdup(a, buf);
}

static char *_rune_to_str(Arena *a, int32_t r) {
    char buf[5] = {0};
    if (r < 0x80) { buf[0] = r; }
    else if (r < 0x800) { buf[0] = 0xC0 | (r >> 6); buf[1] = 0x80 | (r & 0x3F); }
    else if (r < 0x10000) { buf[0] = 0xE0 | (r >> 12); buf[1] = 0x80 | ((r >> 6) & 0x3F); buf[2] = 0x80 | (r & 0x3F); }
    else { buf[0] = 0xF0 | (r >> 18); buf[1] = 0x80 | ((r >> 12) & 0x3F); buf[2] = 0x80 | ((r >> 6) & 0x3F); buf[3] = 0x80 | (r & 0x3F); }
    return arena_strdup(a, buf);
}

static bool _str_contains(const char *s, const char *sub) {
    if (!s || !sub) return false;
    return strstr(s, sub) != NULL;
}

static int _str_count(const char *s, const char *sub) {
    if (!s || !sub || !*sub) return 0;
    int count = 0;
    size_t sublen = strlen(sub);
    const char *p = s;
    while ((p = strstr(p, sub)) != NULL) { count++; p += sublen; }
    return count;
}

// === Dynamic array (Vec) helpers ===
#define VEC_INIT_CAP 8

#define VEC_PUSH(a, vec, item) do { \
    if ((vec)->len >= (vec)->cap) { \
        size_t new_cap = (vec)->cap ? (vec)->cap * 2 : VEC_INIT_CAP; \
        void *new_data = arena_alloc(a, new_cap * sizeof(*(vec)->data)); \
        if ((vec)->data) memcpy(new_data, (vec)->data, (vec)->len * sizeof(*(vec)->data)); \
        (vec)->data = new_data; \
        (vec)->cap = new_cap; \
    } \
    (vec)->data[(vec)->len++] = (item); \
} while(0)

// Extend a vector with all elements from another vector
#define VEC_EXTEND(a, dest, src) do { \
    for (size_t _i = 0; _i < (src)->len; _i++) { \
        VEC_PUSH((a), (dest), (src)->data[_i]); \
    } \
} while(0)

static void _vec_extend(Arena *a, void *dest_ptr, void *src_ptr) {
    // Generic extend - caller ensures types match
    // This is a placeholder; actual use should be VEC_EXTEND macro
    (void)a; (void)dest_ptr; (void)src_ptr;
}

// === Map helpers ===
// Simple linear-scan map for small maps (arena-allocated)
typedef struct StrMap {
    const char **keys;
    const char **vals;
    int64_t *ivals;
    size_t len;
    size_t cap;
    bool is_int_val;
} StrMap;

static StrMap *_strmap_new(Arena *a, size_t cap, bool is_int_val) {
    StrMap *m = (StrMap *)arena_alloc(a, sizeof(StrMap));
    m->keys = (const char **)arena_alloc(a, cap * sizeof(const char *));
    if (is_int_val) {
        m->ivals = (int64_t *)arena_alloc(a, cap * sizeof(int64_t));
        m->vals = NULL;
    } else {
        m->vals = (const char **)arena_alloc(a, cap * sizeof(const char *));
        m->ivals = NULL;
    }
    m->len = 0;
    m->cap = cap;
    m->is_int_val = is_int_val;
    return m;
}

static void _strmap_set_str(StrMap *m, const char *key, const char *val) {
    for (size_t i = 0; i < m->len; i++) {
        if (strcmp(m->keys[i], key) == 0) { m->vals[i] = val; return; }
    }
    if (m->len < m->cap) { m->keys[m->len] = key; m->vals[m->len] = val; m->len++; }
}

static void _strmap_set_int(StrMap *m, const char *key, int64_t val) {
    for (size_t i = 0; i < m->len; i++) {
        if (strcmp(m->keys[i], key) == 0) { m->ivals[i] = val; return; }
    }
    if (m->len < m->cap) { m->keys[m->len] = key; m->ivals[m->len] = val; m->len++; }
}

static const char *_strmap_get_str(StrMap *m, const char *key, const char *def) {
    if (!m) return def;
    for (size_t i = 0; i < m->len; i++) {
        if (strcmp(m->keys[i], key) == 0) return m->vals[i];
    }
    return def;
}

static int64_t _strmap_get_int(StrMap *m, const char *key, int64_t def) {
    if (!m) return def;
    for (size_t i = 0; i < m->len; i++) {
        if (strcmp(m->keys[i], key) == 0) return m->ivals[i];
    }
    return def;
}

static bool _strmap_contains(StrMap *m, const char *key) {
    if (!m) return false;
    for (size_t i = 0; i < m->len; i++) {
        if (strcmp(m->keys[i], key) == 0) return true;
    }
    return false;
}

static uint64_t _hash_str(const char *s) {
    uint64_t h = 5381;
    while (*s) h = ((h << 5) + h) ^ (unsigned char)*s++;
    return h;
}

static uint64_t _hash_int(int64_t n) {
    return (uint64_t)n * 0x9e3779b97f4a7c15ULL;
}

// Variable-argument string formatting helper
// Pre-processes format string to convert %v to %s (vsnprintf doesn't know %v)
static char *_str_format(Arena *a, const char *fmt, ...) {
    // Convert %v to %s in format string
    size_t flen = strlen(fmt);
    char *cfmt = (char *)arena_alloc(a, flen + 1);
    const char *src = fmt;
    char *dst = cfmt;
    while (*src) {
        if (src[0] == '%' && src[1] == 'v') {
            *dst++ = '%';
            *dst++ = 's';
            src += 2;
        } else {
            *dst++ = *src++;
        }
    }
    *dst = '\0';
    va_list args1, args2;
    va_start(args1, fmt);
    va_copy(args2, args1);
    int len = vsnprintf(NULL, 0, cfmt, args1);
    va_end(args1);
    if (len < 0) { va_end(args2); return arena_strdup(a, ""); }
    char *buf = (char *)arena_alloc(a, len + 1);
    vsnprintf(buf, len + 1, cfmt, args2);
    va_end(args2);
    return buf;
}

// Vec_Byte forward declaration for _str_to_bytes
typedef struct Vec_Byte { uint8_t *data; size_t len; size_t cap; } Vec_Byte;

// String to bytes conversion (UTF-8 encoded)
static Vec_Byte _str_to_bytes(Arena *a, const char *s) {
    if (!s) return (Vec_Byte){NULL, 0, 0};
    size_t len = strlen(s);
    uint8_t *data = (uint8_t *)arena_alloc(a, len);
    memcpy(data, s, len);
    return (Vec_Byte){data, len, len};
}

// Bytes to string conversion (null-terminates the result)
static const char *_bytes_to_str(Arena *a, Vec_Byte v) {
    if (!v.data || v.len == 0) return "";
    char *s = (char *)arena_alloc(a, v.len + 1);
    memcpy(s, v.data, v.len);
    s[v.len] = '\0';
    return s;
}

// Generic set membership - string sets are NULL-terminated const char*[]
static bool _set_contains(void *set, const char *key) {
    if (!set || !key) return false;
    const char **elems = (const char **)set;
    for (; *elems; elems++) {
        if (strcmp(*elems, key) == 0) return true;
    }
    return false;
}

static bool _map_contains(void *map, const char *key) {
    return _strmap_contains((StrMap *)map, key);
}

"""
        for line in helpers.strip().split("\n"):
            self._line(line)
        self._line("")

    def _emit_forward_decls(self, module: Module) -> None:
        """Emit forward declarations for all structs and interfaces."""
        self._line("// === Forward declarations ===")
        for iface in module.interfaces:
            self._line(f"typedef struct {_type_name(iface.name)} {_type_name(iface.name)};")
        for struct in module.structs:
            self._line(f"typedef struct {_type_name(struct.name)} {_type_name(struct.name)};")
        self._line("")

    def _emit_kind_constants(self, module: Module) -> None:
        """Emit KIND_* constants for all structs and a kind_to_str helper."""
        self._line("// === Kind constants ===")
        # Generate KIND_* constants for all structs
        for i, struct in enumerate(module.structs):
            const_name = f"KIND_{_type_name(struct.name).upper()}"
            self._line(f"#define {const_name} {i + 1}")
        # Special kind for string values in any interface
        self._line(f"#define KIND_STRING {len(module.structs) + 1}")
        self._line("")
        # Generate _kind_to_str helper
        self._line("static const char *_kind_to_str(int kind) {")
        self.indent += 1
        self._line("switch (kind) {")
        for i, struct in enumerate(module.structs):
            const_name = f"KIND_{_type_name(struct.name).upper()}"
            # Get the original Python kind string from the struct name
            kind_str = self._struct_name_to_kind(struct.name)
            self._line(f'case {const_name}: return "{kind_str}";')
        self._line('default: return "";')
        self._line("}")
        self.indent -= 1
        self._line("}")
        self._line("")

    def _struct_name_to_kind(self, name: str) -> str:
        """Get the kind string for a struct, using const_fields from the IR."""
        if name in self._kind_cache:
            return self._kind_cache[name]
        # Fallback: convert PascalCase to kebab-case (e.g., UnaryTest -> unary-test)
        result = ""
        for i, c in enumerate(name):
            if c.isupper():
                if i > 0:
                    result += "-"
                result += c.lower()
            else:
                result += c
        return result

    def _emit_structs(self, module: Module) -> None:
        """Emit struct definitions."""
        # Emit interfaces as structs with vtable-style function pointers
        for iface in module.interfaces:
            self._emit_interface(iface)
        # Emit regular structs
        for struct in module.structs:
            self._emit_struct(struct)

    def _emit_interface(self, iface: InterfaceDef) -> None:
        """Emit interface as a struct with kind tag.

        For Node interfaces, we use const char *kind as the first field so that
        concrete Node subclass structs can be directly cast to Node * - they all
        have 'kind' as their first field with the same type.
        """
        self._line(f"// Interface: {iface.name}")
        self._line(f"struct {_type_name(iface.name)} {{")
        self.indent += 1
        self._line("const char * kind;")  # Must match concrete struct layout
        self.indent -= 1
        self._line("};")
        self._line("")

    def _emit_struct(self, struct: Struct) -> None:
        """Emit struct definition."""
        self._line(f"struct {_type_name(struct.name)} {{")
        self.indent += 1
        # Embedded type for exception inheritance
        if struct.embedded_type:
            self._line(f"{_type_name(struct.embedded_type)} base;")
        # For Node subclasses, emit 'kind' field first so casting to Node * works
        # (Node interface has const char *kind as first field)
        kind_field = None
        other_fields = []
        for fld in struct.fields:
            if fld.name == "kind":
                kind_field = fld
            else:
                other_fields.append(fld)
        # Emit kind first if present (Node subclasses)
        if kind_field:
            c_type = self._type_to_c(kind_field.typ)
            self._line(f"{c_type} kind;")
        # Emit other fields
        for fld in other_fields:
            c_type = self._type_to_c(fld.typ)
            c_name = _safe_name(fld.name)
            ownership_comment = ""
            if fld.ownership == "weak":
                ownership_comment = "  // weak (back-ref)"
            self._line(f"{c_type} {c_name};{ownership_comment}")
        self.indent -= 1
        self._line("};")
        self._line("")
        # Constructor function
        self._emit_struct_constructor(struct)

    def _emit_struct_constructor(self, struct: Struct) -> None:
        """Emit constructor function for struct."""
        name = _type_name(struct.name)
        # Parameters stay in original order (to match call sites)
        params = []
        for fld in struct.fields:
            c_type = self._type_to_c(fld.typ)
            c_name = _safe_name(fld.name)
            params.append(f"{c_type} {c_name}")
        param_str = ", ".join(params) if params else "void"
        self._line(f"static {name} *{name}_new({param_str}) {{")
        self.indent += 1
        self._line(f"{name} *self = ({name} *)arena_alloc(g_arena, sizeof({name}));")
        # Assign fields (order doesn't matter for assignment)
        for fld in struct.fields:
            c_name = _safe_name(fld.name)
            ownership_comment = ""
            if fld.ownership == "weak":
                ownership_comment = "  // weak (back-ref, no ownership)"
            self._line(f"self->{c_name} = {c_name};{ownership_comment}")
        self._line("return self;")
        self.indent -= 1
        self._line("}")
        self._line("")

    def _emit_tuple_types(self) -> None:
        """Emit struct definitions for tuple types."""
        if not self._tuple_types:
            return
        self._line("// === Tuple types ===")
        for sig in sorted(self._tuple_types.keys()):
            self._line(f"typedef struct {sig} {sig};")
        self._line("")
        # Emit actual struct definitions with proper field types
        for sig in sorted(self._tuple_types.keys()):
            tup = self._tuple_types[sig]
            self._line(f"struct {sig} {{")
            self.indent += 1
            for i, elem in enumerate(tup.elements):
                elem_type = self._type_to_c(elem)
                self._line(f"{elem_type} F{i};")
            self.indent -= 1
            self._line("};")
        self._line("")

    def _emit_constants(self, constants: list[Constant]) -> None:
        """Emit module-level constants."""
        if not constants:
            return
        self._line("// === Constants ===")
        for const in constants:
            c_type = self._type_to_c(const.typ)
            name = _safe_name(const.name).upper()
            value = self._emit_expr(const.value)
            if isinstance(const.typ, (Set, Map, Slice)):
                # Complex constants need to be initialized at runtime
                self._line(f"static {c_type} {name};  // initialized in init()")
                self._deferred_constants.append(const)
            else:
                self._line(f"static const {c_type} {name} = {value};")
        self._line("")

    # ============================================================
    # FUNCTION EMISSION
    # ============================================================

    def _emit_function_decls(self, module: Module) -> None:
        """Emit forward declarations for all functions and methods."""
        self._line("// === Function declarations ===")
        emitted: set[str] = set()  # Track emitted names to avoid duplicates
        # Top-level functions
        for func in module.functions:
            name = _safe_name(func.name)
            if name in emitted:
                continue
            emitted.add(name)
            ret_type = self._type_to_c(func.ret)
            params = ", ".join(
                self._param_with_type(p.typ, _safe_name(p.name)) for p in func.params
            )
            if not params:
                params = "void"
            self._line(f"static {ret_type} {name}({params});")
        # Interface method dispatchers
        for iface in module.interfaces:
            for method in iface.methods:
                method_name = f"{_type_name(iface.name)}_{_safe_name(method.name)}"
                if method_name in emitted:
                    continue
                emitted.add(method_name)
                ret_type = self._type_to_c(method.ret)
                iface_type = f"{_type_name(iface.name)} *"
                params = [f"{iface_type}self"]
                for p in method.params:
                    params.append(self._param_with_type(p.typ, _safe_name(p.name)))
                param_str = ", ".join(params)
                self._line(f"static {ret_type} {method_name}({param_str});")
        # Struct methods
        for struct in module.structs:
            for method in struct.methods:
                method_name = f"{_type_name(struct.name)}_{_safe_name(method.name)}"
                if method_name in emitted:
                    continue
                emitted.add(method_name)
                ret_type = self._type_to_c(method.ret)
                recv_type = f"{_type_name(struct.name)} *"
                recv_name = _safe_name(method.receiver.name if method.receiver else "self")
                params = [f"{recv_type}{recv_name}"]
                for p in method.params:
                    params.append(self._param_with_type(p.typ, _safe_name(p.name)))
                param_str = ", ".join(params)
                self._line(f"static {ret_type} {method_name}({param_str});")
        self._line("")

    def _emit_function(self, func: Function) -> None:
        """Emit a top-level function."""
        self._hoisted_vars = {}
        self._current_return_type = func.ret
        self._receiver_name = ""
        self._receiver_type = ""
        # Track params with interface types
        self._interface_vars: set[str] = set()
        # Track params with FuncType that have receivers (bound method callbacks)
        self._callback_params: set[str] = set()
        for p in func.params:
            if isinstance(p.typ, InterfaceRef):
                self._interface_vars.add(p.name)
            if isinstance(p.typ, FuncType) and p.typ.receiver is not None:
                self._callback_params.add(p.name)
        ret_type = self._type_to_c(func.ret)
        name = _safe_name(func.name)
        params = ", ".join(self._param_with_type(p.typ, _safe_name(p.name)) for p in func.params)
        if not params:
            params = "void"
        self._line(f"static {ret_type} {name}({params}) {{")
        self.indent += 1
        if func.name == "parse":
            self._line("init();")
            for const in self._deferred_constants:
                cname = _safe_name(const.name).upper()
                value = self._emit_expr(const.value)
                self._line(f"{cname} = {value};")
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")
        self._line("")

    def _emit_method(self, struct_name: str, func: Function) -> None:
        """Emit a struct method as a function with self parameter."""
        self._hoisted_vars = {}
        self._current_return_type = func.ret
        self._receiver_name = func.receiver.name if func.receiver else "self"
        self._receiver_type = struct_name
        # Track params with interface types
        self._interface_vars: set[str] = set()
        # Track params with FuncType that have receivers (bound method callbacks)
        self._callback_params: set[str] = set()
        for p in func.params:
            if isinstance(p.typ, InterfaceRef):
                self._interface_vars.add(p.name)
            if isinstance(p.typ, FuncType) and p.typ.receiver is not None:
                self._callback_params.add(p.name)
        ret_type = self._type_to_c(func.ret)
        method_name = f"{_type_name(struct_name)}_{_safe_name(func.name)}"
        recv_type = f"{_type_name(struct_name)} *"
        recv_name = _safe_name(self._receiver_name)
        params = [f"{recv_type}{recv_name}"]
        for p in func.params:
            params.append(self._param_with_type(p.typ, _safe_name(p.name)))
        param_str = ", ".join(params)
        self._line(f"static {ret_type} {method_name}({param_str}) {{")
        self.indent += 1
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")
        self._line("")

    # ============================================================
    # STATEMENT EMISSION
    # ============================================================

    def _emit_stmt(self, stmt: Stmt) -> None:
        """Emit a statement."""
        if isinstance(stmt, VarDecl):
            self._emit_stmt_VarDecl(stmt)
        elif isinstance(stmt, Assign):
            self._emit_stmt_Assign(stmt)
        elif isinstance(stmt, TupleAssign):
            self._emit_stmt_TupleAssign(stmt)
        elif isinstance(stmt, OpAssign):
            self._emit_stmt_OpAssign(stmt)
        elif isinstance(stmt, ExprStmt):
            self._emit_stmt_ExprStmt(stmt)
        elif isinstance(stmt, Return):
            self._emit_stmt_Return(stmt)
        elif isinstance(stmt, If):
            self._emit_stmt_If(stmt)
        elif isinstance(stmt, While):
            self._emit_stmt_While(stmt)
        elif isinstance(stmt, ForRange):
            self._emit_stmt_ForRange(stmt)
        elif isinstance(stmt, ForClassic):
            self._emit_stmt_ForClassic(stmt)
        elif isinstance(stmt, Break):
            self._line("break;")
        elif isinstance(stmt, Continue):
            self._line("continue;")
        elif isinstance(stmt, Block):
            self._emit_stmt_Block(stmt)
        elif isinstance(stmt, TryCatch):
            self._emit_stmt_TryCatch(stmt)
        elif isinstance(stmt, Raise):
            self._emit_stmt_Raise(stmt)
        elif isinstance(stmt, SoftFail):
            self._line("return NULL;")
        elif isinstance(stmt, TypeSwitch):
            self._emit_stmt_TypeSwitch(stmt)
        elif isinstance(stmt, Match):
            self._emit_stmt_Match(stmt)
        elif isinstance(stmt, NoOp):
            pass

    def _emit_stmt_VarDecl(self, stmt: VarDecl) -> None:
        c_type = self._type_to_c(stmt.typ)
        name = _safe_name(stmt.name)
        # Ownership comment for documentation
        ownership_comment = ""
        if stmt.ownership == "borrowed":
            ownership_comment = "  // borrowed"
        elif stmt.ownership == "weak":
            ownership_comment = "  // weak"
        # Track interface-typed variables for TypeAssert emission
        if isinstance(stmt.typ, InterfaceRef):
            self._interface_vars.add(stmt.name)
        # If variable was hoisted with same type, just assign (don't re-declare)
        if stmt.name in self._hoisted_vars and self._hoisted_vars[stmt.name] == c_type:
            if stmt.value:
                val = self._emit_expr(stmt.value)
                # Cast if assigning struct pointer to interface type (but not primitives or "any")
                if isinstance(stmt.typ, InterfaceRef) and stmt.typ.name != "any" and stmt.value.typ:
                    value_typ = stmt.value.typ
                    if isinstance(value_typ, (StructRef, Pointer)) and not isinstance(
                        value_typ, Primitive
                    ):
                        val = f"({c_type}){val}"
                    elif isinstance(value_typ, InterfaceRef) and value_typ.name != "any":
                        val = f"({c_type}){val}"
                self._line(f"{name} = {val};{ownership_comment}")
            # else: no-op, already initialized
            return
        if stmt.value:
            val = self._emit_expr(stmt.value)
            # Cast if assigning struct pointer to interface type (but not primitives or "any")
            if isinstance(stmt.typ, InterfaceRef) and stmt.typ.name != "any" and stmt.value.typ:
                value_typ = stmt.value.typ
                if isinstance(value_typ, (StructRef, Pointer)) and not isinstance(
                    value_typ, Primitive
                ):
                    val = f"({c_type}){val}"
                elif isinstance(value_typ, InterfaceRef) and value_typ.name != "any":
                    val = f"({c_type}){val}"
            self._line(f"{c_type} {name} = {val};{ownership_comment}")
        else:
            # Initialize to zero/NULL
            if c_type.endswith("*"):
                self._line(f"{c_type} {name} = NULL;{ownership_comment}")
            elif c_type in ("int64_t", "int32_t", "int", "size_t"):
                self._line(f"{c_type} {name} = 0;{ownership_comment}")
            elif c_type == "bool":
                self._line(f"{c_type} {name} = false;{ownership_comment}")
            elif c_type == "double":
                self._line(f"{c_type} {name} = 0.0;{ownership_comment}")
            else:
                self._line(f"{c_type} {name} = {{0}};{ownership_comment}")

    def _emit_stmt_Assign(self, stmt: Assign) -> None:
        # Map index assignment: map[key] = value -> _strmap_set_*(map, key, value)
        if isinstance(stmt.target, IndexLV) and isinstance(stmt.target.obj.typ, Map):
            obj = self._emit_expr(stmt.target.obj)
            idx = self._emit_expr(stmt.target.index)
            value = self._emit_expr(stmt.value)
            val_type = stmt.target.obj.typ.value
            if isinstance(val_type, Primitive) and val_type.kind == "int":
                self._line(f"_strmap_set_int({obj}, {idx}, {value});")
            else:
                self._line(f"_strmap_set_str({obj}, {idx}, {value});")
            return
        target = self._emit_lvalue(stmt.target)
        value = self._emit_expr(stmt.value)
        # Check escape analysis: if borrowed string value escapes (stored in field), copy it
        if isinstance(stmt.target, FieldLV) and stmt.value.escapes:
            value_typ = stmt.value.typ
            if isinstance(value_typ, Primitive) and value_typ.kind == "string":
                value = f"arena_strdup(g_arena, {value})"
        # Check if target variable was hoisted with same type - if so, just assign
        var_name = stmt.target.name if isinstance(stmt.target, VarLV) else None
        typ = stmt.decl_typ or stmt.value.typ
        # Workaround: if type is 'any' but value is integer literal, use int64_t
        if isinstance(typ, InterfaceRef) and typ.name == "any":
            val_expr = stmt.value
            # Check for integer literal (including unary minus: -1)
            is_int_lit = isinstance(val_expr, IntLit)
            if (
                isinstance(val_expr, UnaryOp)
                and val_expr.op == "-"
                and isinstance(val_expr.operand, IntLit)
            ):
                is_int_lit = True
            if is_int_lit:
                typ = INT
        c_type = self._type_to_c(typ) if typ else "void *"
        # Track interface-typed variables for TypeAssert emission
        if var_name is not None and isinstance(typ, InterfaceRef):
            self._interface_vars.add(var_name)
        # Check if we're assigning struct/pointer to interface type - need cast
        # Skip "any" interface since it can hold any type and doesn't need casts
        value_typ = stmt.value.typ
        if (
            isinstance(typ, InterfaceRef)
            and typ.name != "any"
            and value_typ
            and not isinstance(value_typ, Primitive)
        ):
            # Assigning struct pointer to interface - add cast (but not primitives)
            if isinstance(value_typ, (StructRef, Pointer)):
                value = f"({c_type}){value}"
            elif isinstance(value_typ, InterfaceRef) and value_typ.name != "any":
                # Also cast interface to interface for consistency
                value = f"({c_type}){value}"
        # Check if we're assigning interface type to concrete struct type - need cast
        elif (
            value_typ
            and isinstance(value_typ, InterfaceRef)
            and isinstance(typ, (Pointer, StructRef))
            and not isinstance(typ, InterfaceRef)
        ):
            # Assigning interface to concrete struct - direct cast works because
            # all Node subtypes have const char *kind as first field (same layout)
            value = f"({c_type}){value}"
        # Also check if source is a variable known to be interface-typed
        elif (
            isinstance(stmt.value, Var)
            and stmt.value.name in self._interface_vars
            and isinstance(typ, (Pointer, StructRef))
            and not isinstance(typ, InterfaceRef)
        ):
            value = f"({c_type}){value}"
        already_declared = var_name in self._hoisted_vars if var_name else False
        is_hoisted = already_declared and self._hoisted_vars.get(var_name) == c_type
        # Emit declaration only if middleend says is_declaration and not already hoisted with same type
        needs_decl = stmt.is_declaration and not is_hoisted
        # Workaround: if already declared with integer type and new value is compatible, don't redeclare
        if (
            already_declared
            and not is_hoisted
            and self._hoisted_vars.get(var_name) in ("int64_t", "int32_t", "int", "bool")
            and (
                c_type in ("int64_t", "int32_t", "int", "bool", "Any *", "void *")
                or c_type.startswith("Any")
            )
        ):
            needs_decl = False
        if needs_decl:
            self._line(f"{c_type} {target} = {value};")
            if var_name is not None:
                self._hoisted_vars[var_name] = c_type
        else:
            self._line(f"{target} = {value};")

    def _emit_stmt_TupleAssign(self, stmt: TupleAssign) -> None:
        # Tuple unpacking - capture tuple then extract fields
        value_type = stmt.value.typ
        if isinstance(value_type, Tuple):
            tuple_sig = self._tuple_sig(value_type)
            tmp_name = self._temp_name("_tup")
            value = self._emit_expr(stmt.value)
            self._line(f"{tuple_sig} {tmp_name} = {value};")
            for i, t in enumerate(stmt.targets):
                var_name = t.name if isinstance(t, VarLV) else None
                # Skip discard targets (empty name or underscore, typically from Python's _)
                if not var_name or var_name == "_":
                    continue
                target = self._emit_lvalue(t)
                field_type = (
                    self._type_to_c(value_type.elements[i])
                    if i < len(value_type.elements)
                    else "void *"
                )
                already_declared = var_name in self._hoisted_vars if var_name else False
                is_hoisted = already_declared and self._hoisted_vars.get(var_name) == field_type
                needs_decl = (stmt.is_declaration and not is_hoisted) or (
                    var_name is not None and not already_declared
                )
                # Same workaround as in _emit_stmt_Assign
                if (
                    already_declared
                    and not is_hoisted
                    and self._hoisted_vars.get(var_name) in ("int64_t", "int32_t", "int", "bool")
                    and (
                        field_type in ("int64_t", "int32_t", "int", "bool", "Any *", "void *")
                        or field_type.startswith("Any")
                    )
                ):
                    needs_decl = False
                if needs_decl:
                    self._line(f"{field_type} {target} = {tmp_name}.F{i};")
                    if var_name is not None:
                        self._hoisted_vars[var_name] = field_type
                else:
                    self._line(f"{target} = {tmp_name}.F{i};")
        else:
            # Fallback for non-tuple types - evaluate value once to avoid
            # side effects (e.g., --len from .pop()) being repeated
            value = self._emit_expr(stmt.value)
            active_targets = [
                (i, t) for i, t in enumerate(stmt.targets)
                if (t.name if isinstance(t, VarLV) else None) not in (None, "_")
            ]
            if len(active_targets) > 1:
                # Multiple targets: capture value in a temp to avoid re-evaluation
                tmp = self._temp_name("_tup")
                val_type = stmt.value.typ
                if isinstance(val_type, Tuple):
                    sig = self._tuple_sig(val_type)
                    self._line(f"{sig} {tmp} = {value};")
                else:
                    self._line(f"__auto_type {tmp} = {value};")
                value_expr = tmp
            else:
                value_expr = value
            for i, t in active_targets:
                var_name = t.name if isinstance(t, VarLV) else None
                target = self._emit_lvalue(t)
                already_declared = var_name in self._hoisted_vars if var_name else False
                is_hoisted = already_declared and self._hoisted_vars.get(var_name) == "void *"
                needs_decl = (stmt.is_declaration and not is_hoisted) or (
                    var_name is not None and not already_declared
                )
                if needs_decl:
                    self._line(f"void *{target} = ((void **)&({value_expr}))[{i}];")
                    if var_name is not None:
                        self._hoisted_vars[var_name] = "void *"
                else:
                    self._line(f"{target} = ((void **)&({value_expr}))[{i}];")

    def _emit_stmt_OpAssign(self, stmt: OpAssign) -> None:
        target = self._emit_lvalue(stmt.target)
        value = self._emit_expr(stmt.value)
        # String concatenation with += - check if value is or returns a string
        value_is_str = isinstance(stmt.value, StringLit) or (
            isinstance(stmt.value.typ, Primitive) and stmt.value.typ.kind == "string"
        )
        if stmt.op == "+" and value_is_str:
            self._line(f"{target} = _str_concat(g_arena, {target}, {value});")
        else:
            self._line(f"{target} {stmt.op}= {value};")

    def _emit_stmt_ExprStmt(self, stmt: ExprStmt) -> None:
        # Handle append specially
        if isinstance(stmt.expr, MethodCall) and stmt.expr.method == "append" and stmt.expr.args:
            obj = self._emit_expr(stmt.expr.obj)
            arg_expr = stmt.expr.args[0]
            arg = self._emit_expr(arg_expr)
            obj_type = stmt.expr.obj.typ
            # If appending a rune to Vec_Str, convert to string first
            actual_slice_type = obj_type
            if isinstance(obj_type, Pointer) and isinstance(obj_type.target, Slice):
                actual_slice_type = obj_type.target
            if isinstance(actual_slice_type, Slice):
                elem_type = actual_slice_type.element
                arg_type = arg_expr.typ
                if (
                    isinstance(elem_type, Primitive)
                    and elem_type.kind == "string"
                    and isinstance(arg_type, Primitive)
                    and arg_type.kind == "rune"
                ):
                    arg = f"_rune_to_str(g_arena, {arg})"
            # If obj is already a pointer to slice (from function param), don't add &
            if isinstance(obj_type, Pointer) and isinstance(obj_type.target, Slice):
                self._line(f"VEC_PUSH(g_arena, {obj}, ({arg}));")
            else:
                # Extra parens to protect compound literals with commas from macro expansion
                self._line(f"VEC_PUSH(g_arena, &{obj}, ({arg}));")
            return
        expr = self._emit_expr(stmt.expr)
        if expr:
            self._line(f"{expr};")

    def _emit_stmt_Return(self, stmt: Return) -> None:
        if stmt.value:
            # In void functions, returning NilLit should just be 'return;'
            if isinstance(stmt.value, NilLit) and self._current_return_type == VOID:
                self._line("return;")
            else:
                # Clear temps from previous statement and emit new ones
                self._rvalue_temps = []
                # Emit temp vars for rvalue slice fields in StructLits before the return
                self._emit_rvalue_temps(stmt.value)
                val = self._emit_expr(stmt.value)
                # Cast to interface type when returning struct from interface-returning function
                ret_type = self._current_return_type
                val_type = stmt.value.typ
                if isinstance(ret_type, InterfaceRef):
                    if isinstance(val_type, StructRef) or isinstance(val_type, InterfaceRef):
                        ret_c_type = self._type_to_c(ret_type)
                        val = f"({ret_c_type}){val}"
                self._line(f"return {val};")
        else:
            self._line("return;")

    def _collect_if_hoisted_vars(self, stmt: If) -> list[tuple[str, Type | None]]:
        """Collect hoisted vars from an If and all nested Ifs recursively."""
        result: list[tuple[str, Type | None]] = list(stmt.hoisted_vars)
        # Collect from nested ifs in then-branch
        for s in stmt.then_body:
            if isinstance(s, If):
                result.extend(self._collect_if_hoisted_vars(s))
        # Collect from nested ifs in else-branch (including else-if chains)
        if stmt.else_body:
            for s in stmt.else_body:
                if isinstance(s, If):
                    result.extend(self._collect_if_hoisted_vars(s))
        return result

    def _emit_stmt_If(self, stmt: If) -> None:
        # Emit hoisted variables from entire if-else chain (skip if already hoisted with same type)
        for name, typ in self._collect_if_hoisted_vars(stmt):
            c_type = self._type_to_c(typ) if typ else "void *"
            if name in self._hoisted_vars:
                # Skip if already hoisted with same type
                if self._hoisted_vars[name] == c_type:
                    continue
                # Different type - don't hoist, let it be local
                continue
            c_name = _safe_name(name)
            self._line(f"{c_type} {c_name};")
            self._hoisted_vars[name] = c_type
        cond = self._emit_expr(stmt.cond)
        self._line(f"if ({cond}) {{")
        self.indent += 1
        for s in stmt.then_body:
            self._emit_stmt(s)
        self.indent -= 1
        if stmt.else_body:
            if len(stmt.else_body) == 1 and isinstance(stmt.else_body[0], If):
                self._line("} else ")
                self._emit_stmt_If_inline(stmt.else_body[0])
            else:
                self._line("} else {")
                self.indent += 1
                for s in stmt.else_body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("}")
        else:
            self._line("}")

    def _emit_stmt_If_inline(self, stmt: If) -> None:
        """Emit if without leading indentation (for else if chains)."""
        # Add hoisted vars to tracking set (they were already emitted by outer If)
        for name, typ in stmt.hoisted_vars:
            c_type = self._type_to_c(typ) if typ else "void *"
            self._hoisted_vars[name] = c_type
        cond = self._emit_expr(stmt.cond)
        self.lines[-1] += f"if ({cond}) {{"
        self.indent += 1
        for s in stmt.then_body:
            self._emit_stmt(s)
        self.indent -= 1
        if stmt.else_body:
            if len(stmt.else_body) == 1 and isinstance(stmt.else_body[0], If):
                self._line("} else ")
                self._emit_stmt_If_inline(stmt.else_body[0])
            else:
                self._line("} else {")
                self.indent += 1
                for s in stmt.else_body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("}")
        else:
            self._line("}")

    def _emit_stmt_While(self, stmt: While) -> None:
        for name, typ in stmt.hoisted_vars:
            c_type = self._type_to_c(typ) if typ else "void *"
            if name in self._hoisted_vars:
                if self._hoisted_vars[name] == c_type:
                    continue
                continue
            c_name = _safe_name(name)
            self._line(f"{c_type} {c_name};")
            self._hoisted_vars[name] = c_type
        cond = self._emit_expr(stmt.cond)
        self._line(f"while (!g_parse_error && ({cond})) {{")
        self.indent += 1
        for s in stmt.body:
            self._emit_stmt(s)
        self.indent -= 1
        self._line("}")

    def _emit_stmt_ForRange(self, stmt: ForRange) -> None:
        for name, typ in stmt.hoisted_vars:
            c_type = self._type_to_c(typ) if typ else "void *"
            if name in self._hoisted_vars:
                if self._hoisted_vars[name] == c_type:
                    continue
                continue
            c_name = _safe_name(name)
            self._line(f"{c_type} {c_name};")
            self._hoisted_vars[name] = c_type
        iterable = self._emit_expr(stmt.iterable)
        idx = _safe_name(stmt.index) if stmt.index else "_idx"
        val = _safe_name(stmt.value) if stmt.value else "_val"
        iter_type = stmt.iterable.typ
        if isinstance(iter_type, Slice):
            elem_type = self._type_to_c(iter_type.element)
            self._line(f"for (size_t {idx} = 0; {idx} < {iterable}.len; {idx}++) {{")
            self.indent += 1
            if stmt.value:
                self._line(f"{elem_type} {val} = {iterable}.data[{idx}];")
            for s in stmt.body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        elif iter_type == STRING or (
            isinstance(iter_type, Primitive) and iter_type.kind == "string"
        ):
            # Iterate over characters
            self._line(f"for (int {idx} = 0; {idx} < _rune_len({iterable}); {idx}++) {{")
            self.indent += 1
            if stmt.value:
                self._line(f"int32_t {val} = _rune_at({iterable}, {idx});")
            for s in stmt.body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        elif isinstance(iter_type, Optional) and isinstance(iter_type.inner, Slice):
            # Optional slice - pointer to Vec, use -> for access
            inner_slice = iter_type.inner
            elem_type = self._type_to_c(inner_slice.element)
            self._line(f"if ({iterable} != NULL) {{")
            self.indent += 1
            self._line(f"for (size_t {idx} = 0; {idx} < {iterable}->len; {idx}++) {{")
            self.indent += 1
            if stmt.value:
                self._line(f"{elem_type} {val} = {iterable}->data[{idx}];")
            for s in stmt.body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
            self.indent -= 1
            self._line("}")
        else:
            # Generic iteration - emit as slice-like for now
            self._line(f"// ForRange over {iter_type}")
            elem_type = "void *"
            if isinstance(iter_type, (Slice, Array)):
                elem_type = self._type_to_c(iter_type.element)
            self._line(f"for (size_t {idx} = 0; {idx} < {iterable}.len; {idx}++) {{")
            self.indent += 1
            if stmt.value:
                self._line(f"{elem_type} {val} = {iterable}.data[{idx}];")
            for s in stmt.body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")

    def _emit_stmt_ForClassic(self, stmt: ForClassic) -> None:
        init = self._emit_stmt_inline(stmt.init) if stmt.init else ""
        cond = self._emit_expr(stmt.cond) if stmt.cond else ""
        post = self._emit_stmt_inline(stmt.post) if stmt.post else ""
        self._line(f"for ({init}; {cond}; {post}) {{")
        self.indent += 1
        for s in stmt.body:
            self._emit_stmt(s)
        self.indent -= 1
        self._line("}")

    def _emit_stmt_inline(self, stmt: Stmt) -> str:
        """Emit statement as inline string (for for loop parts)."""
        if isinstance(stmt, VarDecl):
            c_type = self._type_to_c(stmt.typ)
            name = _safe_name(stmt.name)
            if stmt.value:
                val = self._emit_expr(stmt.value)
                return f"{c_type} {name} = {val}"
            return f"{c_type} {name} = 0"
        if isinstance(stmt, Assign):
            target = self._emit_lvalue(stmt.target)
            val = self._emit_expr(stmt.value)
            return f"{target} = {val}"
        if isinstance(stmt, OpAssign):
            target = self._emit_lvalue(stmt.target)
            if isinstance(stmt.value, IntLit) and stmt.value.value == 1:
                if stmt.op == "+":
                    return f"{target}++"
                if stmt.op == "-":
                    return f"{target}--"
            val = self._emit_expr(stmt.value)
            return f"{target} {stmt.op}= {val}"
        return ""

    def _emit_stmt_Block(self, stmt: Block) -> None:
        if not stmt.no_scope:
            self._line("{")
            self.indent += 1
        for s in stmt.body:
            self._emit_stmt(s)
        if not stmt.no_scope:
            self.indent -= 1
            self._line("}")

    def _emit_stmt_TryCatch(self, stmt: TryCatch) -> None:
        # C doesn't have try/catch - simulate with g_parse_error checks
        self._line("// try {")
        for name, typ in stmt.hoisted_vars:
            c_type = self._type_to_c(typ) if typ else "void *"
            if name in self._hoisted_vars:
                if self._hoisted_vars[name] == c_type:
                    continue
                continue
            c_name = _safe_name(name)
            self._line(f"{c_type} {c_name};")
            self._hoisted_vars[name] = c_type
        if stmt.catch_body:
            label = f"_catch_{self._try_label_counter}"
            self._try_label_counter += 1
            self._try_catch_labels.append(label)
        for s in stmt.body:
            self._emit_stmt(s)
        if stmt.catch_body:
            self._try_catch_labels.pop()
            self._line(f"goto {label}_end;")
            self._line(f"{label}:;")
            self._line("if (g_parse_error) {")
            self.indent += 1
            self._line("g_parse_error = 0;")
            self._line('g_error_msg[0] = \'\\0\';')
            for s in stmt.catch_body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
            self._line(f"{label}_end:;")
        elif stmt.reraise:
            self._line("if (g_parse_error) {")
            self.indent += 1
            err_val = self._error_return_value()
            if err_val:
                self._line(f"return {err_val};")
            else:
                self._line("return;")
            self.indent -= 1
            self._line("}")
        self._line("// } catch")

    def _emit_stmt_Raise(self, stmt: Raise) -> None:
        err_val = self._error_return_value()
        in_try_catch = bool(self._try_catch_labels)
        if stmt.reraise_var:
            self._line("// re-raise")
            self._line("g_parse_error = 1;")
            if in_try_catch:
                self._line(f"goto {self._try_catch_labels[-1]};")
            elif err_val:
                self._line(f"return {err_val};")
            else:
                self._line("return;")
            return
        msg = self._emit_expr(stmt.message)
        self._line("g_parse_error = 1;")
        self._line(f'snprintf(g_error_msg, sizeof(g_error_msg), "%s", {msg});')
        if in_try_catch:
            self._line(f"goto {self._try_catch_labels[-1]};")
        elif err_val:
            self._line(f"return {err_val};")
        else:
            self._line("return;")

    def _error_return_value(self) -> str:
        """Return appropriate error value based on current function's return type."""
        ret = self._current_return_type
        if ret == VOID:
            return ""  # void functions can't return a value
        if isinstance(ret, Tuple):
            sig = self._tuple_sig(ret)
            zeros = ", ".join(
                "0"
                if isinstance(e, Primitive) and e.kind in ("int", "bool", "float", "byte", "rune")
                else "NULL"
                for e in ret.elements
            )
            return f"({sig}){{{zeros}}}"
        if isinstance(ret, Slice):
            sig = self._slice_elem_sig(ret.element)
            return f"(Vec_{sig}){{NULL, 0, 0}}"
        return "NULL"

    def _collect_stmt_hoisted_vars(self, stmt: Stmt) -> list[tuple[str, Type | None]]:
        """Recursively collect hoisted vars from a statement and its nested statements."""
        result: list[tuple[str, Type | None]] = []
        if isinstance(stmt, If):
            result.extend(self._collect_if_hoisted_vars(stmt))
        elif isinstance(stmt, While):
            result.extend(stmt.hoisted_vars)
            for s in stmt.body:
                result.extend(self._collect_stmt_hoisted_vars(s))
        elif isinstance(stmt, (ForRange, ForClassic)):
            result.extend(stmt.hoisted_vars)
            for s in stmt.body:
                result.extend(self._collect_stmt_hoisted_vars(s))
        elif isinstance(stmt, TypeSwitch):
            result.extend(stmt.hoisted_vars)
            for case in stmt.cases:
                for s in case.body:
                    result.extend(self._collect_stmt_hoisted_vars(s))
            if stmt.default:
                for s in stmt.default:
                    result.extend(self._collect_stmt_hoisted_vars(s))
        elif isinstance(stmt, Match):
            result.extend(stmt.hoisted_vars)
            for case in stmt.cases:
                for s in case.body:
                    result.extend(self._collect_stmt_hoisted_vars(s))
            if stmt.default:
                for s in stmt.default:
                    result.extend(self._collect_stmt_hoisted_vars(s))
        elif isinstance(stmt, Block):
            for s in stmt.body:
                result.extend(self._collect_stmt_hoisted_vars(s))
        elif isinstance(stmt, TryCatch):
            result.extend(stmt.hoisted_vars)
            for s in stmt.body:
                result.extend(self._collect_stmt_hoisted_vars(s))
            for s in stmt.catch_body:
                result.extend(self._collect_stmt_hoisted_vars(s))
        return result

    def _collect_case_declarations(self, stmts: list[Stmt]) -> list[tuple[str, Type | None]]:
        """Collect all variable declarations from switch case statements.

        This collects Assigns and TupleAssigns with is_declaration=True, which need
        to be pre-declared before the switch for visibility outside the case block.
        """
        result: list[tuple[str, Type | None]] = []
        for stmt in stmts:
            if isinstance(stmt, Assign):
                if stmt.is_declaration and isinstance(stmt.target, VarLV):
                    typ = stmt.decl_typ or stmt.value.typ
                    result.append((stmt.target.name, typ))
            elif isinstance(stmt, TupleAssign):
                if stmt.is_declaration:
                    for i, t in enumerate(stmt.targets):
                        if isinstance(t, VarLV):
                            typ = (
                                stmt.value.typ.elements[i]
                                if isinstance(stmt.value.typ, Tuple)
                                and i < len(stmt.value.typ.elements)
                                else None
                            )
                            result.append((t.name, typ))
            elif isinstance(stmt, VarDecl):
                result.append((stmt.name, stmt.typ))
            # Recurse into control structures
            elif isinstance(stmt, If):
                result.extend(self._collect_case_declarations(stmt.then_body))
                if stmt.else_body:
                    result.extend(self._collect_case_declarations(stmt.else_body))
            elif isinstance(stmt, While):
                result.extend(self._collect_case_declarations(stmt.body))
            elif isinstance(stmt, (ForRange, ForClassic)):
                result.extend(self._collect_case_declarations(stmt.body))
            elif isinstance(stmt, TypeSwitch):
                for case in stmt.cases:
                    result.extend(self._collect_case_declarations(case.body))
                if stmt.default:
                    result.extend(self._collect_case_declarations(stmt.default))
            elif isinstance(stmt, Match):
                for case in stmt.cases:
                    result.extend(self._collect_case_declarations(case.body))
                if stmt.default:
                    result.extend(self._collect_case_declarations(stmt.default))
            elif isinstance(stmt, TryCatch):
                result.extend(self._collect_case_declarations(stmt.body))
                result.extend(self._collect_case_declarations(stmt.catch_body))
        return result

    def _emit_stmt_TypeSwitch(self, stmt: TypeSwitch) -> None:
        # Collect hoisted vars from nested statements within this TypeSwitch
        case_hoisted: list[tuple[str, Type | None]] = list(stmt.hoisted_vars)
        for case in stmt.cases:
            for s in case.body:
                case_hoisted.extend(self._collect_stmt_hoisted_vars(s))
            # Also collect declarations directly in case body
            case_hoisted.extend(self._collect_case_declarations(case.body))
        if stmt.default:
            for s in stmt.default:
                case_hoisted.extend(self._collect_stmt_hoisted_vars(s))
            case_hoisted.extend(self._collect_case_declarations(stmt.default))
        # Only emit hoisted vars that aren't already hoisted with same type
        for name, typ in case_hoisted:
            c_type = self._type_to_c(typ) if typ else "void *"
            if name in self._hoisted_vars:
                if self._hoisted_vars[name] == c_type:
                    continue
                # Different type - don't hoist, let it be declared locally
                continue
            c_name = _safe_name(name)
            self._line(f"{c_type} {c_name};")
            self._hoisted_vars[name] = c_type
        expr = self._emit_expr(stmt.expr)
        binding = _safe_name(stmt.binding)
        # Check if any case is a primitive type (like string)
        # If so, use if-else chain with special KIND_STRING check
        has_primitive = False
        for case in stmt.cases:
            if isinstance(case.typ, Primitive):
                has_primitive = True
                break
        if has_primitive:
            self._emit_type_switch_with_primitives(stmt, expr, binding)
            return
        # Type switches in C use string comparison on kind field (all Node subtypes
        # have const char *kind as first field, allowing direct casting)
        # If binding equals expr, we need a temp to avoid shadowing issues
        switch_expr = expr
        if binding == expr:
            tmp = self._temp_name("_tsexpr")
            self._line(f"void *{tmp} = {expr};")
            switch_expr = tmp
        first = True
        for case in stmt.cases:
            type_name = self._type_to_c(case.typ).rstrip(" *")
            kind_str = self._struct_name_to_kind(type_name)
            kwd = "if" if first else "} else if"
            self._line(
                f'{kwd} (strcmp((({type_name} *){switch_expr})->kind, "{kind_str}") == 0) {{'
            )
            self.indent += 1
            # Cast directly to concrete type (same memory, different view)
            self._line(f"{type_name} *{binding} = ({type_name} *){switch_expr};")
            for s in case.body:
                self._emit_stmt(s)
            self.indent -= 1
            first = False
        if stmt.default:
            self._line("} else {")
            self.indent += 1
            for s in stmt.default:
                self._emit_stmt(s)
            self.indent -= 1
        self._line("}")
        # Note: Don't restore _hoisted_vars - let hoisted vars persist at function level
        # to avoid redeclaration of variables used across multiple TypeSwitches

    def _emit_type_switch_with_primitives(self, stmt: TypeSwitch, expr: str, binding: str) -> None:
        """Emit a TypeSwitch that includes primitive type cases as if-else chain."""
        # If binding equals expr, we need a temp to avoid shadowing issues
        switch_expr = expr
        if binding == expr:
            tmp = self._temp_name("_tsexpr")
            self._line(f"void *{tmp} = {expr};")
            switch_expr = tmp
        first = True
        for case in stmt.cases:
            if isinstance(case.typ, Primitive):
                if case.typ.kind == "string":
                    cond = f'strcmp(((Node *){switch_expr})->kind, "string") == 0'
                    kwd = "if" if first else "} else if"
                    self._line(f"{kwd} ({cond}) {{")
                    self.indent += 1
                    # For string case, we need special handling
                    # The expr is actually a const char * wrapped in an Any
                    self._line(f"const char *{binding} = (const char *){switch_expr};")
                else:
                    raise NotImplementedError("primitive type in TypeSwitch")
            else:
                type_name = self._type_to_c(case.typ).rstrip(" *")
                kind_str = self._struct_name_to_kind(type_name)
                cond = f'strcmp((({type_name} *){switch_expr})->kind, "{kind_str}") == 0'
                kwd = "if" if first else "} else if"
                self._line(f"{kwd} ({cond}) {{")
                self.indent += 1
                # Cast directly to concrete type
                self._line(f"{type_name} *{binding} = ({type_name} *){switch_expr};")
            first = False
            for s in case.body:
                self._emit_stmt(s)
            self.indent -= 1
        if stmt.default:
            self._line("} else {")
            self.indent += 1
            for s in stmt.default:
                self._emit_stmt(s)
            self.indent -= 1
        self._line("}")

    def _emit_stmt_Match(self, stmt: Match) -> None:
        for name, typ in stmt.hoisted_vars:
            c_type = self._type_to_c(typ) if typ else "void *"
            if name in self._hoisted_vars:
                if self._hoisted_vars[name] == c_type:
                    continue
                continue
            c_name = _safe_name(name)
            self._line(f"{c_type} {c_name};")
            self._hoisted_vars[name] = c_type
        expr = self._emit_expr(stmt.expr)
        self._line(f"switch ({expr}) {{")
        for case in stmt.cases:
            for pattern in case.patterns:
                p = self._emit_expr(pattern)
                self._line(f"case {p}:")
            self._line("{")
            self.indent += 1
            for s in case.body:
                self._emit_stmt(s)
            self._line("break;")
            self.indent -= 1
            self._line("}")
        if stmt.default:
            self._line("default: {")
            self.indent += 1
            for s in stmt.default:
                self._emit_stmt(s)
            self._line("break;")
            self.indent -= 1
            self._line("}")
        self._line("}")

    # ============================================================
    # EXPRESSION EMISSION
    # ============================================================

    def _emit_expr(self, expr: Expr | None) -> str:
        """Emit an expression and return C code string."""
        if expr is None:
            return "NULL"
        if isinstance(expr, IntLit):
            return str(expr.value)
        if isinstance(expr, FloatLit):
            return str(expr.value)
        if isinstance(expr, StringLit):
            return f'"{escape_string_c(expr.value)}"'
        if isinstance(expr, BoolLit):
            return "true" if expr.value else "false"
        if isinstance(expr, NilLit):
            # Check if this is a nil for a Slice type - needs empty Vec
            # Use cap=(size_t)-1 as sentinel to distinguish None from []
            if expr.typ is not None and isinstance(expr.typ, Slice):
                sig = self._slice_elem_sig(expr.typ.element)
                return f"(Vec_{sig}){{NULL, 0, (size_t)-1}}"
            # Check if this is a nil for a Tuple type - return zeroed tuple
            if expr.typ is not None and isinstance(expr.typ, Tuple):
                sig = self._tuple_sig(expr.typ)
                zeros = ", ".join(
                    "0"
                    if isinstance(e, Primitive)
                    and e.kind in ("int", "bool", "float", "byte", "rune")
                    else "NULL"
                    for e in expr.typ.elements
                )
                return f"({sig}){{{zeros}}}"
            return "NULL"
        if isinstance(expr, Var):
            return self._emit_expr_Var(expr)
        if isinstance(expr, FieldAccess):
            return self._emit_expr_FieldAccess(expr)
        if isinstance(expr, FuncRef):
            return self._emit_expr_FuncRef(expr)
        if isinstance(expr, Index):
            return self._emit_expr_Index(expr)
        if isinstance(expr, SliceExpr):
            return self._emit_expr_SliceExpr(expr)
        if isinstance(expr, SliceConvert):
            return self._emit_expr_SliceConvert(expr)
        if isinstance(expr, Call):
            return self._emit_expr_Call(expr)
        if isinstance(expr, MethodCall):
            return self._emit_expr_MethodCall(expr)
        if isinstance(expr, StaticCall):
            return self._emit_expr_StaticCall(expr)
        if isinstance(expr, BinaryOp):
            return self._emit_expr_BinaryOp(expr)
        if isinstance(expr, UnaryOp):
            return self._emit_expr_UnaryOp(expr)
        if isinstance(expr, Ternary):
            return self._emit_expr_Ternary(expr)
        if isinstance(expr, Cast):
            return self._emit_expr_Cast(expr)
        if isinstance(expr, TypeAssert):
            return self._emit_expr_TypeAssert(expr)
        if isinstance(expr, IsType):
            return self._emit_expr_IsType(expr)
        if isinstance(expr, IsNil):
            return self._emit_expr_IsNil(expr)
        if isinstance(expr, Len):
            return self._emit_expr_Len(expr)
        if isinstance(expr, MakeSlice):
            return self._emit_expr_MakeSlice(expr)
        if isinstance(expr, MakeMap):
            return self._emit_expr_MakeMap(expr)
        if isinstance(expr, SliceLit):
            return self._emit_expr_SliceLit(expr)
        if isinstance(expr, MapLit):
            return self._emit_expr_MapLit(expr)
        if isinstance(expr, SetLit):
            return self._emit_expr_SetLit(expr)
        if isinstance(expr, StructLit):
            return self._emit_expr_StructLit(expr)
        if isinstance(expr, TupleLit):
            return self._emit_expr_TupleLit(expr)
        if isinstance(expr, StringConcat):
            return self._emit_expr_StringConcat(expr)
        if isinstance(expr, StringFormat):
            return self._emit_expr_StringFormat(expr)
        if isinstance(expr, ParseInt):
            return self._emit_expr_ParseInt(expr)
        if isinstance(expr, IntToStr):
            return self._emit_expr_IntToStr(expr)
        if isinstance(expr, Truthy):
            return self._emit_expr_Truthy(expr)
        if isinstance(expr, CharClassify):
            return self._emit_expr_CharClassify(expr)
        if isinstance(expr, TrimChars):
            return self._emit_expr_TrimChars(expr)
        if isinstance(expr, AddrOf):
            return self._emit_expr_AddrOf(expr)
        return "/* TODO: unknown expr */"

    def _emit_expr_Var(self, expr: Var) -> str:
        if expr.name == "self":
            return _safe_name(self._receiver_name) if self._receiver_name else "self"
        # Constants are emitted as uppercase
        if expr.name in self._constant_names:
            return _safe_name(expr.name).upper()
        return _safe_name(expr.name)

    def _emit_expr_FieldAccess(self, expr: FieldAccess) -> str:
        obj = self._emit_expr(expr.obj)
        obj_type = expr.obj.typ
        # For tuple fields (F0, F1, etc.), preserve the case
        if isinstance(obj_type, Tuple) and expr.field.startswith("F"):
            return f"{obj}.{expr.field}"
        field = _safe_name(expr.field)
        # Handle interface types - kind is const char * first field
        if isinstance(obj_type, InterfaceRef):
            # For 'kind' field, return directly (it's already const char *)
            if field == "kind":
                return f"{obj}->kind"
            # For other fields, we can't access them on the interface directly
            # The code should use type switches or casts first
            return f"{obj}->{field}"
        # Check if obj is a pointer type
        if isinstance(obj_type, (Pointer, Optional, StructRef)):
            return f"{obj}->{field}"
        return f"{obj}.{field}"

    def _emit_expr_FuncRef(self, expr: FuncRef) -> str:
        if expr.obj is not None:
            # Method reference
            obj_type = expr.obj.typ
            if isinstance(obj_type, (Pointer, StructRef)):
                type_name = (
                    obj_type.name
                    if isinstance(obj_type, StructRef)
                    else obj_type.target.name
                    if isinstance(obj_type.target, StructRef)
                    else ""
                )
                return f"{_type_name(type_name)}_{_safe_name(expr.name)}"
        return _safe_name(expr.name)

    def _emit_expr_Index(self, expr: Index) -> str:
        obj = self._emit_expr(expr.obj)
        idx = self._emit_expr(expr.index)
        obj_type = expr.obj.typ
        if obj_type == STRING:
            # String character indexing
            result_type = expr.typ
            if result_type == BYTE or result_type == INT:
                return f"(uint8_t){obj}[{idx}]"
            return f"_char_at_str(g_arena, {obj}, {idx})"
        if isinstance(obj_type, Slice):
            return f"{obj}.data[{idx}]"
        if isinstance(obj_type, Map):
            val_type = obj_type.value
            if isinstance(val_type, Primitive) and val_type.kind == "int":
                return f"_strmap_get_int({obj}, {idx}, 0)"
            return f'_strmap_get_str({obj}, {idx}, "")'
        if isinstance(obj_type, Tuple):
            # Tuple indexing - use field name F0, F1, etc.
            if isinstance(expr.index, IntLit):
                return f"{obj}.F{expr.index.value}"
            return f"{obj}.F{idx}"
        return f"{obj}[{idx}]"

    def _emit_expr_SliceExpr(self, expr: SliceExpr) -> str:
        obj = self._emit_expr(expr.obj)
        obj_type = expr.obj.typ
        if obj_type == STRING:
            low = self._emit_expr(expr.low) if expr.low else "0"
            high = self._emit_expr(expr.high) if expr.high else f"_rune_len({obj})"
            return f"__c_substring(g_arena, {obj}, {low}, {high})"
        # Slice of slice
        low = self._emit_expr(expr.low) if expr.low else "0"
        high = self._emit_expr(expr.high) if expr.high else f"{obj}.len"
        vec_type = self._type_to_c(obj_type)
        return f"({vec_type}){{{obj}.data + {low}, {high} - {low}, {high} - {low}}}"

    def _emit_expr_SliceConvert(self, expr: SliceConvert) -> str:
        """Emit slice type conversion (e.g., list[HereDoc] -> list[Node])."""
        source = self._emit_expr(expr.source)
        source_type = expr.source.typ
        target_type = expr.typ
        # If types are compatible (same layout), cast the struct
        if isinstance(source_type, Slice) and isinstance(target_type, Slice):
            source_elem = source_type.element
            target_elem = target_type.element
            # Check if element types differ and need cast
            needs_cast = False
            if isinstance(source_elem, StructRef) and isinstance(
                target_elem, (StructRef, InterfaceRef)
            ):
                needs_cast = source_elem.name != target_elem.name
            elif isinstance(source_elem, Pointer) and isinstance(
                target_elem, (StructRef, InterfaceRef)
            ):
                # Pointer(StructRef) -> StructRef/InterfaceRef
                inner = source_elem.target
                if isinstance(inner, StructRef):
                    needs_cast = inner.name != target_elem.name
            if needs_cast:
                target_vec = self._type_to_c(target_type)
                return f"*({target_vec} *)&{source}"
        return source

    def _emit_expr_Call(self, expr: Call) -> str:
        func = expr.func
        # Special builtins
        # _int_ptr / _intPtr creates a pointer to an int value
        if func in ("_int_ptr", "_intPtr") and len(expr.args) == 1:
            arg = self._emit_expr(expr.args[0])
            return f"&{arg}"
        if func == "_repeat_str" and len(expr.args) == 2:
            s = self._emit_expr(expr.args[0])
            n = self._emit_expr(expr.args[1])
            return f"_str_repeat(g_arena, {s}, {n})"
        if func == "_sublist" and len(expr.args) == 3:
            lst = self._emit_expr(expr.args[0])
            start = self._emit_expr(expr.args[1])
            end = self._emit_expr(expr.args[2])
            # Get Vec type from the list argument's type
            list_type = expr.args[0].typ
            if isinstance(list_type, Slice):
                sig = self._slice_elem_sig(list_type.element)
                return f"((Vec_{sig}){{({lst}).data + ({start}), ({end}) - ({start}), ({end}) - ({start})}})"
            # Fallback for unknown types
            return f"/* sublist */ {lst}"
        func_name = _safe_name(func)
        arg_list: list[str] = []
        # If calling through a callback parameter with receiver, prepend self
        if func in self._callback_params and self._receiver_name:
            arg_list.append(_safe_name(self._receiver_name))
        # Look up parameter types for interface casting
        param_types = self._function_sigs.get(func, [])
        for i, a in enumerate(expr.args):
            arg_str = self._emit_expr(a)
            # Cast to interface type when needed (C requires explicit casts between struct pointer types)
            if i < len(param_types):
                param_type = param_types[i]
                arg_type = a.typ
                if isinstance(param_type, InterfaceRef):
                    # Cast if arg is a struct OR if arg is the same interface but C might use concrete type
                    # (e.g., loop variables from slices use concrete struct types)
                    param_c_type = self._type_to_c(param_type)
                    if isinstance(arg_type, StructRef):
                        arg_str = f"({param_c_type}){arg_str}"
                    elif isinstance(arg_type, InterfaceRef) and arg_type.name == param_type.name:
                        # Same interface, but C code might have concrete type - cast to be safe
                        arg_str = f"({param_c_type}){arg_str}"
                # Add & when passing Slice value to Optional(Slice) parameter
                # (matches logic in _emit_expr_StructLit)
                elif (
                    isinstance(param_type, Optional)
                    and isinstance(param_type.inner, Slice)
                    and isinstance(arg_type, Slice)
                    and not isinstance(arg_type, (Optional, Pointer))
                ):
                    arg_str = f"&{arg_str}"
            arg_list.append(arg_str)
        args = ", ".join(arg_list)
        return f"{func_name}({args})"

    def _emit_expr_MethodCall(self, expr: MethodCall) -> str:
        obj = self._emit_expr(expr.obj)
        method = expr.method
        args_expr = [self._emit_expr(a) for a in expr.args]
        obj_type = expr.obj.typ
        # String methods
        if method == "join" and expr.args:
            sep = obj
            seq = args_expr[0]
            return f"_str_join(g_arena, {sep}, {seq})"
        if method == "startswith" and expr.args:
            # Handle tuple of prefixes: s.startswith(("a", "b")) -> (starts_with || starts_with)
            if isinstance(expr.args[0], TupleLit):
                checks = [
                    f"_str_startswith({obj}, {self._emit_expr(e)})" for e in expr.args[0].elements
                ]
                return "(" + " || ".join(checks) + ")"
            if len(expr.args) >= 2:
                return f"_str_startswith_at({obj}, {args_expr[1]}, {args_expr[0]})"
            return f"_str_startswith({obj}, {args_expr[0]})"
        if method == "endswith" and expr.args:
            # Handle tuple of suffixes: s.endswith(("a", "b")) -> (ends_with || ends_with)
            if isinstance(expr.args[0], TupleLit):
                checks = [
                    f"_str_endswith({obj}, {self._emit_expr(e)})" for e in expr.args[0].elements
                ]
                return "(" + " || ".join(checks) + ")"
            return f"_str_endswith({obj}, {args_expr[0]})"
        if method == "replace" and len(expr.args) >= 2:
            return f"_str_replace(g_arena, {obj}, {args_expr[0]}, {args_expr[1]})"
        if method == "lower":
            return f"_str_lower(g_arena, {obj})"
        if method == "upper":
            return f"_str_upper(g_arena, {obj})"
        if method == "find" and expr.args:
            return f"_str_find({obj}, {args_expr[0]})"
        if method == "rfind" and expr.args:
            return f"_str_rfind({obj}, {args_expr[0]})"
        if method == "count" and expr.args:
            return f"_str_count({obj}, {args_expr[0]})"
        # Slice methods
        if isinstance(obj_type, Slice):
            if method == "append" and expr.args:
                return f"/* append {args_expr[0]} to {obj} */"
            if method == "extend" and expr.args:
                # extend adds all elements from another slice
                # Use inline loop to avoid taking address of rvalue
                src_expr = args_expr[0]
                elem_type = self._type_to_c(obj_type.element)
                return f"do {{ Vec_{self._slice_elem_sig(obj_type.element)} _src = {src_expr}; for (size_t _i = 0; _i < _src.len; _i++) {{ VEC_PUSH(g_arena, &{obj}, _src.data[_i]); }} }} while(0)"
            if method == "pop":
                if expr.args and self._is_zero_literal(expr.args[0]):
                    # pop(0) - pop from front: grab first element, shift rest
                    elem_sig = self._slice_elem_sig(obj_type.element)
                    return (
                        f"({{ {self._type_to_c(obj_type.element)} _pop0 = {obj}.data[0]; "
                        f"memmove({obj}.data, {obj}.data + 1, --{obj}.len * sizeof({obj}.data[0])); "
                        f"_pop0; }})"
                    )
                return f"{obj}.data[--{obj}.len]"
            if method == "copy":
                return f"{obj} /* copy */"
        # Dict methods
        if isinstance(obj_type, Map):
            if method == "get" and expr.args:
                key_expr = args_expr[0]
                val_type = obj_type.value
                if isinstance(val_type, Primitive) and val_type.kind == "int":
                    default = args_expr[1] if len(args_expr) > 1 else "0"
                    return f"_strmap_get_int({obj}, {key_expr}, {default})"
                default = args_expr[1] if len(args_expr) > 1 else '""'
                return f"_strmap_get_str({obj}, {key_expr}, {default})"
        # Regular method call - handle struct, interface, and pointer types
        # Unwrap Optional if present
        actual_type = obj_type
        if isinstance(obj_type, Optional):
            actual_type = obj_type.inner
        type_name = ""
        is_interface = False
        if isinstance(actual_type, StructRef):
            type_name = actual_type.name
        elif isinstance(actual_type, InterfaceRef):
            type_name = actual_type.name
            is_interface = True
        elif isinstance(actual_type, Pointer):
            inner = actual_type.target
            if isinstance(inner, StructRef):
                type_name = inner.name
            elif isinstance(inner, InterfaceRef):
                type_name = inner.name
                is_interface = True
        if type_name:
            # Handle "any" interface specially - it represents any Node type
            # so we dispatch to Node for its methods
            if type_name == "any" and method == "to_sexp":
                return f"Node_to_sexp({obj})"
            method_name = f"{_type_name(type_name)}_{_safe_name(method)}"
            all_args = [obj] + args_expr
            if is_interface:
                # Interface method call - need dispatch based on kind
                # For now, generate a call that will be handled by a dispatch function
                return f"{method_name}({', '.join(all_args)})"
            return f"{method_name}({', '.join(all_args)})"
        args = ", ".join(args_expr)
        return f"{obj}.{_safe_name(method)}({args})"

    def _emit_expr_StaticCall(self, expr: StaticCall) -> str:
        type_name = self._type_to_c(expr.on_type).rstrip(" *")
        method = _safe_name(expr.method)
        args = ", ".join(self._emit_expr(a) for a in expr.args)
        return f"{type_name}_{method}({args})"

    def _emit_expr_BinaryOp(self, expr: BinaryOp) -> str:
        op = expr.op
        # Handle rune-to-char comparisons
        left_is_rune = expr.left.typ == RUNE
        right_is_rune = expr.right.typ == RUNE
        if left_is_rune and isinstance(expr.right, StringLit) and len(expr.right.value) == 1:
            left = self._emit_expr(expr.left)
            right = self._emit_char_literal(expr.right.value)
            return f"({left} {op} {right})"
        if right_is_rune and isinstance(expr.left, StringLit) and len(expr.left.value) == 1:
            left = self._emit_char_literal(expr.left.value)
            right = self._emit_expr(expr.right)
            return f"({left} {op} {right})"
        # Handle single-char string comparisons with relational ops (for Python idioms like c >= "0")
        if (
            op in (">=", "<=", ">", "<")
            and expr.left.typ == STRING
            and isinstance(expr.right, StringLit)
            and len(expr.right.value) == 1
        ):
            left = self._emit_expr(expr.left)
            right = self._emit_char_literal(expr.right.value)
            return f"({left}[0] {op} {right})"
        if (
            op in (">=", "<=", ">", "<")
            and expr.right.typ == STRING
            and isinstance(expr.left, StringLit)
            and len(expr.left.value) == 1
        ):
            left = self._emit_char_literal(expr.left.value)
            right = self._emit_expr(expr.right)
            return f"({left} {op} {right}[0])"
        left = self._emit_expr(expr.left)
        right = self._emit_expr(expr.right)
        left_is_str = isinstance(expr.left.typ, Primitive) and expr.left.typ.kind == "string"
        right_is_str = isinstance(expr.right.typ, Primitive) and expr.right.typ.kind == "string"
        # Also treat StringLit as string - covers comparison with 'any' typed variables
        left_is_strlit = isinstance(expr.left, StringLit)
        right_is_strlit = isinstance(expr.right, StringLit)
        # String comparison - use strcmp if either is a string
        if op == "==" and (left_is_str or right_is_str or left_is_strlit or right_is_strlit):
            return f"(strcmp({left}, {right}) == 0)"
        if op == "!=" and (left_is_str or right_is_str or left_is_strlit or right_is_strlit):
            return f"(strcmp({left}, {right}) != 0)"
        # String relational comparison (compare first char if single-char literals involved)
        if op in (">=", "<=", ">", "<") and left_is_str and right_is_str:
            # Both are strings - compare first characters
            return f"({left}[0] {op} {right}[0])"
        # String concatenation
        if op == "+" and (left_is_str or right_is_str):
            return f"_str_concat(g_arena, {left}, {right})"
        # 'in' operator
        if op == "in":
            right_type = expr.right.typ
            if isinstance(right_type, Set):
                return self._emit_set_membership(left, expr.right, False)
            if isinstance(right_type, Map):
                return self._emit_map_membership(left, expr.right, False)
            return f"_str_contains({right}, {left})"
        if op == "not in":
            right_type = expr.right.typ
            if isinstance(right_type, Set):
                return self._emit_set_membership(left, expr.right, True)
            if isinstance(right_type, Map):
                return self._emit_map_membership(left, expr.right, True)
            return f"!_str_contains({right}, {left})"
        # Logical operators
        if op == "and":
            op = "&&"
        if op == "or":
            op = "||"
        return f"({left} {op} {right})"

    def _emit_char_literal(self, char: str) -> str:
        """Emit a single character as a C character literal."""
        if char == "'":
            return "'\\''"
        if char == "\\":
            return "'\\\\'"
        if char == "\n":
            return "'\\n'"
        if char == "\t":
            return "'\\t'"
        if char == "\r":
            return "'\\r'"
        if char == '"':
            return "'\"'"
        if ord(char) < 32 or ord(char) > 126:
            return f"'\\x{ord(char):02x}'"
        return f"'{char}'"

    def _emit_set_membership(self, left: str, right_expr: Expr, negated: bool) -> str:
        """Emit set membership test: x in set or x not in set."""
        # If right_expr is a Var referencing a constant set, inline the comparisons
        if isinstance(right_expr, Var) and right_expr.name in self._constant_set_values:
            set_lit = self._constant_set_values[right_expr.name]
            comparisons = []
            for elem in set_lit.elements:
                elem_str = self._emit_expr(elem)
                comparisons.append(f"(strcmp({left}, {elem_str}) == 0)")
            if not comparisons:
                return "false" if not negated else "true"
            combined = " || ".join(comparisons)
            if negated:
                return f"(!({combined}))"
            return f"({combined})"
        # For inline SetLit, emit comparisons directly
        if isinstance(right_expr, SetLit):
            comparisons = []
            for elem in right_expr.elements:
                elem_str = self._emit_expr(elem)
                comparisons.append(f"(strcmp({left}, {elem_str}) == 0)")
            if not comparisons:
                return "false" if not negated else "true"
            combined = " || ".join(comparisons)
            if negated:
                return f"(!({combined}))"
            return f"({combined})"
        # Fallback: use a helper function (would need to be implemented)
        right = self._emit_expr(right_expr)
        if negated:
            return f"!_set_contains({right}, {left})"
        return f"_set_contains({right}, {left})"

    def _emit_map_membership(self, left: str, right_expr: Expr, negated: bool) -> str:
        """Emit map membership test: key in map or key not in map."""
        right = self._emit_expr(right_expr)
        # For maps, we'd need a map_contains helper
        if negated:
            return f"!_map_contains({right}, {left})"
        return f"_map_contains({right}, {left})"

    def _emit_expr_UnaryOp(self, expr: UnaryOp) -> str:
        operand = self._emit_expr(expr.operand)
        op = expr.op
        if op == "not":
            op = "!"
        return f"{op}({operand})"

    def _emit_expr_Ternary(self, expr: Ternary) -> str:
        cond = self._emit_expr(expr.cond)
        then_expr = self._emit_expr(expr.then_expr)
        # Handle NilLit in else when result is a Slice - needs empty Vec
        if isinstance(expr.else_expr, NilLit) and isinstance(expr.typ, Slice):
            sig = self._slice_elem_sig(expr.typ.element)
            else_expr = f"(Vec_{sig}){{NULL, 0, 0}}"
        else:
            else_expr = self._emit_expr(expr.else_expr)
        return f"({cond} ? {then_expr} : {else_expr})"

    def _emit_expr_Cast(self, expr: Cast) -> str:
        inner = self._emit_expr(expr.expr)
        to_type = self._type_to_c(expr.to_type)
        # Skip redundant casts
        if to_type == "const char *" and expr.expr.typ == STRING:
            return inner
        # String to []byte: convert string to Vec_Byte
        if (
            isinstance(expr.to_type, Slice)
            and expr.to_type.element == BYTE
            and isinstance(expr.expr.typ, Primitive)
            and expr.expr.typ.kind == "string"
        ):
            return f"_str_to_bytes(g_arena, {inner})"
        # []byte to string: null-terminate and return as C string
        if (
            isinstance(expr.expr.typ, Slice)
            and expr.expr.typ.element == BYTE
            and isinstance(expr.to_type, Primitive)
            and expr.to_type.kind == "string"
        ):
            return f"_bytes_to_str(g_arena, {inner})"
        # int/rune to string: chr() — convert codepoint to UTF-8 string
        if (
            isinstance(expr.to_type, Primitive)
            and expr.to_type.kind == "string"
            and isinstance(expr.expr.typ, Primitive)
            and expr.expr.typ.kind in ("int", "rune", "byte")
        ):
            return f"_rune_to_str(g_arena, {inner})"
        return f"({to_type})({inner})"

    def _emit_expr_TypeAssert(self, expr: TypeAssert) -> str:
        inner = self._emit_expr(expr.expr)
        asserted = self._type_to_c(expr.asserted)
        # All Node subtypes have const char *kind as first field, so direct casting works
        # Double parens ensure proper precedence when followed by -> access
        return f"(({asserted})({inner}))"

    def _emit_expr_IsType(self, expr: IsType) -> str:
        inner = self._emit_expr(expr.expr)
        tested = self._type_to_c(expr.tested_type).rstrip(" *")
        kind_str = self._struct_name_to_kind(tested)
        return f'({inner} != NULL && strcmp({inner}->kind, "{kind_str}") == 0)'

    def _emit_expr_IsNil(self, expr: IsNil) -> str:
        inner = self._emit_expr(expr.expr)
        if expr.negated:
            return f"({inner} != NULL)"
        return f"({inner} == NULL)"

    def _emit_expr_Len(self, expr: Len) -> str:
        inner = self._emit_expr(expr.expr)
        inner_type = expr.expr.typ
        if inner_type == STRING:
            return f"_rune_len({inner})"
        if isinstance(inner_type, Slice):
            return f"{inner}.len"
        if isinstance(inner_type, Map):
            return f"{inner}.len"
        if isinstance(inner_type, Optional) and isinstance(inner_type.inner, (Slice, Map)):
            return f"{inner}->len"
        return f"strlen({inner})"

    def _emit_expr_MakeSlice(self, expr: MakeSlice) -> str:
        # Return an empty slice struct
        sig = self._slice_elem_sig(expr.element_type)
        return f"((Vec_{sig}){{NULL, 0, 0}})"

    def _emit_expr_MakeMap(self, expr: MakeMap) -> str:
        is_int = isinstance(expr.value_type, Primitive) and expr.value_type.kind == "int"
        return f"_strmap_new(g_arena, 16, {'true' if is_int else 'false'})"

    def _emit_expr_SliceLit(self, expr: SliceLit) -> str:
        vec_type = self._type_to_c(Slice(expr.element_type))
        if len(expr.elements) == 0:
            return f"({vec_type}){{NULL, 0, 0}}"
        # Non-empty slice - allocate array on arena using GCC statement expression
        # This avoids stack-allocated compound literals that become invalid after function return
        elem_type = self._type_to_c(expr.element_type)
        n = len(expr.elements)
        elements = [self._emit_expr(e) for e in expr.elements]
        assigns = "; ".join(f"_slc[{i}] = {e}" for i, e in enumerate(elements))
        return f"({{ {elem_type} *_slc = ({elem_type} *)arena_alloc(g_arena, {n} * sizeof({elem_type})); {assigns}; ({vec_type}){{_slc, {n}, {n}}}; }})"

    def _emit_expr_MapLit(self, expr: MapLit) -> str:
        is_int = isinstance(expr.value_type, Primitive) and expr.value_type.kind == "int"
        n = len(expr.entries)
        cap = max(n, 4)
        alloc = f"_strmap_new(g_arena, {cap}, {'true' if is_int else 'false'})"
        setter = "_strmap_set_int" if is_int else "_strmap_set_str"
        tmp = self._temp_name("_map")
        sets = "; ".join(
            f"{setter}({tmp}, {self._emit_expr(k)}, {self._emit_expr(v)})"
            for k, v in expr.entries
        )
        return f"({{ StrMap *{tmp} = {alloc}; {sets}; {tmp}; }})"

    def _emit_expr_SetLit(self, expr: SetLit) -> str:
        if isinstance(expr.element_type, Primitive) and expr.element_type.kind == "string":
            elems = ", ".join(self._emit_expr(e) for e in expr.elements)
            return f"(const char *[]){{{elems}, NULL}}"
        return "NULL"

    def _emit_expr_StructLit(self, expr: StructLit) -> str:
        name = expr.struct_name
        args = []
        # Get fields in declaration order
        if name in self._struct_fields:
            for fname, ftyp in self._struct_fields[name]:
                if fname in expr.fields:
                    field_val = expr.fields[fname]
                    # NilLit for Slice field needs empty Vec, not NULL
                    if isinstance(field_val, NilLit) and isinstance(ftyp, Slice):
                        args.append(self._default_value(ftyp))
                    else:
                        val_type = field_val.typ
                        # Add & when passing Slice value to Optional(Slice) parameter
                        if (
                            isinstance(ftyp, Optional)
                            and isinstance(ftyp.inner, Slice)
                            and isinstance(val_type, Slice)
                            and not isinstance(val_type, (Optional, Pointer))
                        ):
                            # Check if this field has a temp var (for rvalues)
                            temp_result = self._get_rvalue_temp(name, fname)
                            if temp_result is not None:
                                temp_name, is_pointer = temp_result
                                # If temp is already a pointer (heap-allocated), use directly
                                val_str = temp_name if is_pointer else f"&{temp_name}"
                            else:
                                val_str = f"&{self._emit_expr(field_val)}"
                        # Cast when passing Slice(StructA) to Slice(StructB/Interface)
                        # This handles cases like list[HereDoc] -> list[Node] where HereDoc implements Node
                        elif (
                            isinstance(ftyp, Slice)
                            and isinstance(val_type, Slice)
                            and self._needs_slice_cast(val_type, ftyp)
                        ):
                            val_str = self._emit_expr(field_val)
                            target_vec = self._type_to_c(ftyp)
                            val_str = f"*({target_vec} *)&{val_str}"
                        else:
                            val_str = self._emit_expr(field_val)
                        args.append(val_str)
                else:
                    # Default value based on type
                    args.append(self._default_value(ftyp))
        else:
            args = [self._emit_expr(v) for v in expr.fields.values()]
        return f"{_type_name(name)}_new({', '.join(args)})"

    def _default_value(self, typ: Type) -> str:
        """Return default value for a type."""
        if isinstance(typ, Slice):
            sig = self._slice_elem_sig(typ.element)
            return f"(Vec_{sig}){{NULL, 0, 0}}"
        c_type = self._type_to_c(typ)
        if c_type.endswith("*"):
            return "NULL"
        if c_type in ("int64_t", "int32_t", "int"):
            return "0"
        if c_type == "bool":
            return "false"
        if c_type == "double":
            return "0.0"
        return "0"

    def _needs_slice_cast(self, from_type: Slice, to_type: Slice) -> bool:
        """Check if slice needs cast (e.g., list[HereDoc] -> list[Node])."""
        from_elem = from_type.element
        to_elem = to_type.element
        # Different struct/interface element types need cast
        if isinstance(from_elem, StructRef) and isinstance(to_elem, (StructRef, InterfaceRef)):
            return from_elem.name != to_elem.name
        if isinstance(from_elem, InterfaceRef) and isinstance(to_elem, InterfaceRef):
            return from_elem.name != to_elem.name
        return False

    def _is_lvalue(self, expr: Expr) -> bool:
        """Check if expression is an lvalue (can take address of)."""
        return isinstance(expr, (Var, FieldAccess, Index, DerefLV))

    def _get_rvalue_temp(self, struct_name: str, field_name: str) -> tuple[str, bool] | None:
        """Get temp var name and is_pointer flag for an rvalue field, if one was created."""
        for i, entry in enumerate(self._rvalue_temps):
            sn, fn, temp = entry[0], entry[1], entry[2]
            is_pointer = entry[3] if len(entry) > 3 else False
            if sn == struct_name and fn == field_name:
                # Remove from list so nested structs with same field get different temps
                self._rvalue_temps.pop(i)
                return (temp, is_pointer)
        return None

    def _emit_rvalue_temps(self, expr: Expr) -> None:
        """Emit temp var declarations for rvalue slice fields in StructLits.

        Scans expression tree for StructLits that pass rvalue Slice to Optional(Slice) fields.
        These need temp vars since we can't take address of rvalues.
        """
        if isinstance(expr, StructLit):
            name = expr.struct_name
            if name in self._struct_fields:
                for fname, ftyp in self._struct_fields[name]:
                    if fname in expr.fields:
                        field_val = expr.fields[fname]
                        val_type = field_val.typ
                        # Check if this field needs &: Optional(Slice) param with Slice value
                        if (
                            isinstance(ftyp, Optional)
                            and isinstance(ftyp.inner, Slice)
                            and isinstance(val_type, Slice)
                            and not isinstance(val_type, (Optional, Pointer))
                        ):
                            # Heap-allocate, but pass NULL if value is None (sentinel cap)
                            tmp_name = self._temp_name("_tmp_slice")
                            vec_type = self._type_to_c(val_type)
                            val_str = self._emit_expr(field_val)
                            self._line(f"{vec_type} {tmp_name}_v = {val_str};")
                            self._line(
                                f"{vec_type} *{tmp_name} = ({tmp_name}_v.cap == (size_t)-1) ? NULL "
                                f": ({vec_type} *)arena_alloc(g_arena, sizeof({vec_type}));"
                            )
                            self._line(
                                f"if ({tmp_name} != NULL) *{tmp_name} = {tmp_name}_v;"
                            )
                            # Store tmp_name directly (it's already a pointer)
                            self._rvalue_temps.append(
                                (name, fname, tmp_name, True)
                            )  # True = already a pointer
                        # Recurse into nested StructLits
                        self._emit_rvalue_temps(field_val)
            else:
                # Unknown struct, still check field values
                for field_val in expr.fields.values():
                    self._emit_rvalue_temps(field_val)
        elif isinstance(expr, Call):
            for arg in expr.args:
                self._emit_rvalue_temps(arg)
        elif isinstance(expr, MethodCall):
            self._emit_rvalue_temps(expr.obj)
            for arg in expr.args:
                self._emit_rvalue_temps(arg)
        elif isinstance(expr, BinaryOp):
            self._emit_rvalue_temps(expr.left)
            self._emit_rvalue_temps(expr.right)
        elif isinstance(expr, UnaryOp):
            self._emit_rvalue_temps(expr.operand)
        elif isinstance(expr, Ternary):
            self._emit_rvalue_temps(expr.cond)
            self._emit_rvalue_temps(expr.then_expr)
            self._emit_rvalue_temps(expr.else_expr)
        elif isinstance(expr, FieldAccess):
            self._emit_rvalue_temps(expr.obj)
        elif isinstance(expr, Index):
            self._emit_rvalue_temps(expr.obj)
            self._emit_rvalue_temps(expr.index)

    def _emit_expr_TupleLit(self, expr: TupleLit) -> str:
        if expr.typ is None or not isinstance(expr.typ, Tuple):
            # Fallback if type is not known
            if len(expr.elements) > 0:
                return self._emit_expr(expr.elements[0])
            return "0"
        sig = self._tuple_sig(expr.typ)
        # Cast elements when needed (e.g., struct pointer to interface pointer)
        elem_strs = []
        for i, e in enumerate(expr.elements):
            elem_str = self._emit_expr(e)
            if i < len(expr.typ.elements):
                expected_type = expr.typ.elements[i]
                actual_type = e.typ
                # Get the interface type from expected if it's wrapped in Optional/Pointer
                target_iface = None
                if isinstance(expected_type, InterfaceRef):
                    target_iface = expected_type.name
                elif isinstance(expected_type, Optional) and isinstance(
                    expected_type.inner, InterfaceRef
                ):
                    target_iface = expected_type.inner.name
                elif isinstance(expected_type, Pointer) and isinstance(
                    expected_type.target, InterfaceRef
                ):
                    target_iface = expected_type.target.name
                # Get the struct type from actual if it's wrapped in Pointer
                source_is_struct = False
                if isinstance(actual_type, StructRef):
                    source_is_struct = True
                elif isinstance(actual_type, Pointer) and isinstance(actual_type.target, StructRef):
                    source_is_struct = True
                elif isinstance(actual_type, InterfaceRef):
                    source_is_struct = True  # Also cast interface to interface (for consistency)
                elif isinstance(actual_type, Optional) and isinstance(
                    actual_type.inner, InterfaceRef
                ):
                    source_is_struct = True
                # Cast if needed
                if target_iface and source_is_struct:
                    iface_c_type = self._type_to_c(InterfaceRef(target_iface))
                    elem_str = f"({iface_c_type}){elem_str}"
            elem_strs.append(elem_str)
        elements = ", ".join(elem_strs)
        return f"({sig}){{{elements}}}"

    def _emit_expr_StringConcat(self, expr: StringConcat) -> str:
        if len(expr.parts) == 0:
            return '""'
        if len(expr.parts) == 1:
            return self._emit_expr(expr.parts[0])
        # Chain concatenations
        result = self._emit_expr(expr.parts[0])
        for part in expr.parts[1:]:
            p = self._emit_expr(part)
            result = f"_str_concat(g_arena, {result}, {p})"
        return result

    def _emit_expr_StringFormat(self, expr: StringFormat) -> str:
        args_list = [self._emit_expr(a) for a in expr.args]
        # Convert {0}, {1} to %s, etc.
        template = re_sub(r"\{(\d+)\}", "%s", expr.template)
        escaped = escape_string_c(template)
        if args_list:
            args_str = ", ".join(args_list)
            # Use a helper that allocates in arena
            return f'_str_format(g_arena, "{escaped}", {args_str})'
        return f'"{escaped}"'

    def _emit_expr_ParseInt(self, expr: ParseInt) -> str:
        s = self._emit_expr(expr.string)
        base = self._emit_expr(expr.base)
        return f"_parse_int({s}, {base})"

    def _emit_expr_IntToStr(self, expr: IntToStr) -> str:
        val = self._emit_expr(expr.value)
        return f"_int_to_str(g_arena, {val})"

    def _emit_expr_Truthy(self, expr: Truthy) -> str:
        inner = self._emit_expr(expr.expr)
        inner_type = expr.expr.typ
        if inner_type == STRING:
            return f"({inner} != NULL && {inner}[0] != '\\0')"
        if inner_type == INT:
            return f"({inner} != 0)"
        if isinstance(inner_type, (Slice, Map, Set)):
            return f"({inner}.len > 0)"
        if isinstance(inner_type, Optional) and isinstance(inner_type.inner, (Slice, Map, Set)):
            return f"({inner} != NULL && {inner}->len > 0)"
        return f"({inner} != NULL)"

    def _emit_expr_CharClassify(self, expr: CharClassify) -> str:
        char = self._emit_expr(expr.char)
        char_type = expr.char.typ
        is_rune = char_type == RUNE
        kind = expr.kind
        if is_rune:
            func_map = {
                "digit": "_rune_is_digit",
                "alpha": "_rune_is_alpha",
                "alnum": "_rune_is_alnum",
                "space": "_rune_is_space",
                "upper": "_rune_is_upper",
                "lower": "_rune_is_lower",
            }
            return f"{func_map[kind]}({char})"
        # String classification
        func_map = {
            "digit": "_str_is_digit",
            "alpha": "_str_is_alpha",
            "alnum": "_str_is_alnum",
            "space": "_str_is_space",
        }
        return f"{func_map.get(kind, '_str_is_alnum')}({char})"

    def _emit_expr_TrimChars(self, expr: TrimChars) -> str:
        s = self._emit_expr(expr.string)
        chars = self._emit_expr(expr.chars)
        mode_map = {
            "left": "_str_ltrim",
            "right": "_str_rtrim",
            "both": "_str_trim",
        }
        return f"{mode_map[expr.mode]}(g_arena, {s}, {chars})"

    def _emit_expr_AddrOf(self, expr: AddrOf) -> str:
        operand = self._emit_expr(expr.operand)
        return f"&{operand}"

    # ============================================================
    # LVALUE EMISSION
    # ============================================================

    def _emit_lvalue(self, lv: LValue) -> str:
        """Emit an lvalue and return C code string."""
        if isinstance(lv, VarLV):
            return _safe_name(lv.name)
        if isinstance(lv, FieldLV):
            obj = self._emit_expr(lv.obj)
            field = _safe_name(lv.field)
            obj_type = lv.obj.typ
            if isinstance(obj_type, (Pointer, Optional, StructRef)):
                return f"{obj}->{field}"
            return f"{obj}.{field}"
        if isinstance(lv, IndexLV):
            obj = self._emit_expr(lv.obj)
            idx = self._emit_expr(lv.index)
            obj_type = lv.obj.typ
            if isinstance(obj_type, Slice):
                return f"{obj}.data[{idx}]"
            return f"{obj}[{idx}]"
        if isinstance(lv, DerefLV):
            ptr = self._emit_expr(lv.ptr)
            return f"*{ptr}"
        return "/* unknown lvalue */"

    # ============================================================
    # TYPE EMISSION
    # ============================================================

    def _type_to_c(self, typ: Type | None) -> str:
        """Convert IR Type to C type string."""
        if typ is None:
            return "void"
        if isinstance(typ, Primitive):
            return {
                "string": "const char *",
                "int": "int64_t",
                "bool": "bool",
                "float": "double",
                "byte": "uint8_t",
                "rune": "int32_t",
                "void": "void",
            }.get(typ.kind, "void *")
        if isinstance(typ, Slice):
            sig = self._slice_elem_sig(typ.element)
            return f"Vec_{sig}"
        if isinstance(typ, Array):
            elem = self._type_to_c(typ.element)
            return f"{elem}[{typ.size}]"
        if isinstance(typ, Map):
            return "StrMap *"
        if isinstance(typ, Set):
            return "void *"  # Simplified - would need proper set struct
        if isinstance(typ, Tuple):
            return self._tuple_sig(typ)
        if isinstance(typ, Pointer):
            target = self._type_to_c(typ.target)
            if target.endswith("*"):
                return target
            return f"{target} *"
        if isinstance(typ, Optional):
            inner = self._type_to_c(typ.inner)
            if inner.endswith("*"):
                return inner
            return f"{inner} *"
        if isinstance(typ, StructRef):
            return f"{_type_name(typ.name)} *"
        if isinstance(typ, InterfaceRef):
            if typ.name == "any":
                return "Any *"  # Generic 'any' interface with kind/data fields
            return f"{_type_name(typ.name)} *"
        if isinstance(typ, Union):
            return "void *"
        if isinstance(typ, FuncType):
            # Function pointers need special handling for parameter names
            # This returns the base type; use _type_to_c_param for parameters
            ret = self._type_to_c(typ.ret)
            param_types: list[str] = []
            if typ.receiver:
                param_types.append(self._type_to_c(typ.receiver))
            for p in typ.params:
                param_types.append(self._type_to_c(p))
            params = ", ".join(param_types) if param_types else "void"
            return f"{ret} (*)({params})"
        if isinstance(typ, StringSlice):
            return "const char *"
        return "void *"

    def _param_with_type(self, typ: Type, name: str) -> str:
        """Format a parameter with its type, handling function pointers correctly."""
        if isinstance(typ, FuncType):
            ret = self._type_to_c(typ.ret)
            param_types: list[str] = []
            if typ.receiver:
                param_types.append(self._type_to_c(typ.receiver))
            for p in typ.params:
                param_types.append(self._type_to_c(p))
            params = ", ".join(param_types) if param_types else "void"
            return f"{ret} (*{name})({params})"
        c_type = self._type_to_c(typ)
        return f"{c_type} {name}"

    # ============================================================
    # INTERFACE DISPATCHERS
    # ============================================================

    def _emit_interface_dispatchers(self, module: Module) -> None:
        """Emit dispatch functions for interface methods."""
        # Collect which structs implement each interface
        interface_impls: dict[str, list[str]] = {}
        for struct in module.structs:
            for iface_name in struct.implements:
                if iface_name not in interface_impls:
                    interface_impls[iface_name] = []
                interface_impls[iface_name].append(struct.name)
        # Emit dispatcher for each interface method
        for iface in module.interfaces:
            impl_structs = interface_impls.get(iface.name, [])
            for method in iface.methods:
                ret_type = self._type_to_c(method.ret)
                method_name = f"{_type_name(iface.name)}_{_safe_name(method.name)}"
                iface_type = f"{_type_name(iface.name)} *"
                params = [f"{iface_type}self"]
                param_names = ["self"]
                for p in method.params:
                    params.append(f"{self._type_to_c(p.typ)} {_safe_name(p.name)}")
                    param_names.append(_safe_name(p.name))
                param_str = ", ".join(params)
                self._line(f"static {ret_type} {method_name}({param_str}) {{")
                self.indent += 1
                # Generate if-else chain on kind string field
                # (all Node subtypes have const char *kind as first field)
                first = True
                for impl in impl_structs:
                    kind_str = self._struct_name_to_kind(impl)
                    kwd = "if" if first else "} else if"
                    self._line(f'{kwd} (strcmp(self->kind, "{kind_str}") == 0) {{')
                    self.indent += 1
                    # Cast directly to concrete type and call its method
                    concrete_method = f"{_type_name(impl)}_{_safe_name(method.name)}"
                    call_args = [f"({_type_name(impl)} *)self"] + param_names[1:]
                    if ret_type != "void":
                        self._line(f"return {concrete_method}({', '.join(call_args)});")
                    else:
                        self._line(f"{concrete_method}({', '.join(call_args)});")
                    self.indent -= 1
                    first = True  # Keep first=True since we're using if-else, not switch
                    first = False
                # Default case
                if first:
                    # No implementations - just return default
                    if ret_type == "void":
                        pass
                    elif ret_type.endswith("*"):
                        self._line("return NULL;")
                    else:
                        self._line("return 0;")
                else:
                    self._line("}")
                    # For void return, no need for else; for other returns, return default
                    if ret_type != "void":
                        if ret_type.endswith("*"):
                            self._line("return NULL;")
                        else:
                            self._line("return 0;")
                self.indent -= 1
                self._line("}")
                self._line("")
