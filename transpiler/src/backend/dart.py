"""Dart backend: IR → Dart code."""

from __future__ import annotations

from src.backend.util import escape_string as _escape_string_generic, to_camel, to_pascal


def escape_string(value: str) -> str:
    """Escape a string for use in a Dart string literal (without quotes).

    Dart requires $ to be escaped as \\$ in string literals.
    """
    return _escape_string_generic(value).replace("$", r"\$")


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

# Dart reserved words and built-in type names that need escaping
_DART_RESERVED = frozenset(
    {
        # Reserved words
        "abstract",
        "as",
        "assert",
        "async",
        "await",
        "break",
        "case",
        "catch",
        "class",
        "const",
        "continue",
        "covariant",
        "default",
        "deferred",
        "do",
        "dynamic",
        "else",
        "enum",
        "export",
        "extends",
        "extension",
        "external",
        "factory",
        "false",
        "final",
        "finally",
        "for",
        "Function",
        "get",
        "hide",
        "if",
        "implements",
        "import",
        "in",
        "interface",
        "is",
        "late",
        "library",
        "mixin",
        "new",
        "null",
        "on",
        "operator",
        "part",
        "required",
        "rethrow",
        "return",
        "set",
        "show",
        "static",
        "super",
        "switch",
        "sync",
        "this",
        "throw",
        "true",
        "try",
        "typedef",
        "var",
        "void",
        "while",
        "with",
        "yield",
        # Built-in types that would shadow dart:core
        "List",
        "Map",
        "Set",
        "String",
        "Object",
        "Type",
        "Symbol",
        "Iterator",
        "Iterable",
        "Future",
        "Stream",
        "Error",
        "Exception",
        "Duration",
        "DateTime",
        "Uri",
        "Pattern",
        "Match",
        "RegExp",
        "Comparable",
        "Expando",
        "Null",
        "Record",
    }
)


def _safe_name(name: str) -> str:
    """Escape Dart reserved words with trailing underscore."""
    result = to_camel(name)
    if result in _DART_RESERVED:
        return result + "_"
    return result


def _safe_pascal(name: str) -> str:
    """Escape reserved words for PascalCase names.

    Note: Unlike _safe_name, this does NOT convert to PascalCase since
    struct/class names in the IR are already in PascalCase. We only need
    to escape reserved words.
    """
    if name in _DART_RESERVED:
        return name + "_"
    return name


class DartBackend:
    """Emit Dart code from IR."""

    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self.receiver_name: str | None = None
        self.current_class: str = ""
        self.struct_fields: dict[str, list[tuple[str, Type]]] = {}
        self._hoisted_vars: set[str] = set()
        self._declared_vars: set[str] = set()
        self._module_name: str = ""
        self._interface_names: set[str] = set()
        self.temp_counter = 0
        # Track methods that can return null (have dynamic return type)
        self._nullable_methods: set[str] = set()
        self._type_switch_binding_rename: dict[str, str] = {}
        self._loop_temp_counter = 0
        self._func_params: set[str] = set()
        self._current_break_flag: str | None = None
        self._current_return_type: Type | None = None

    def emit(self, module: Module) -> str:
        """Emit Dart code from IR Module."""
        self.indent = 0
        self.lines = []
        self.struct_fields = {}
        self._hoisted_vars = set()
        self._module_name = module.name
        self._interface_names = {iface.name for iface in module.interfaces}
        self._collect_struct_fields(module)
        self._emit_module(module)
        return "\n".join(self.lines)

    def _collect_struct_fields(self, module: Module) -> None:
        """Collect field information for all structs."""
        for struct in module.structs:
            self.struct_fields[struct.name] = [(f.name, f.typ) for f in struct.fields]

    def _line(self, text: str = "") -> None:
        if text:
            self.lines.append("  " * self.indent + text)
        else:
            self.lines.append("")

    def _emit_module(self, module: Module) -> None:
        # Disable strict null safety checks for transpiled code
        self._line("// ignore_for_file: unnecessary_null_comparison")
        self._line("// ignore_for_file: unnecessary_non_null_assertion")
        self._line("// ignore_for_file: return_of_invalid_type")
        self._line("// ignore_for_file: argument_type_not_assignable")
        self._line("// ignore_for_file: invalid_assignment")
        self._line("// ignore_for_file: unchecked_use_of_nullable_value")
        self._line("")
        # Emit imports for dart:io and dart:convert
        self._line("import 'dart:io';")
        self._line("import 'dart:convert';")
        self._line("")
        # Emit module doc comment if present
        if module.doc:
            self._line(f"/// {module.doc}")
            self._line("")
        # Emit constants
        if module.constants:
            for const in module.constants:
                self._emit_constant(const)
            self._line("")
        # Emit enums
        for enum_def in module.enums:
            self._emit_enum(enum_def)
            self._line("")
        # Emit interfaces as abstract classes
        for iface in module.interfaces:
            self._emit_interface(iface)
            self._line("")
        # Emit structs as classes
        for struct in module.structs:
            self._emit_struct(struct)
            self._line("")
        # Emit free functions
        for func in module.functions:
            self._emit_function(func)
            self._line("")
        # Emit helper functions
        self._emit_helpers()

    def _emit_constant(self, const: Constant) -> None:
        typ = self._type(const.typ)
        val = self._expr(const.value)
        name = _safe_name(const.name)
        # Use const for compile-time constants
        if isinstance(const.typ, Primitive) and const.typ.kind in ("int", "float", "bool", "string"):
            self._line(f"const {typ} {name} = {val};")
        else:
            self._line(f"final {typ} {name} = {val};")

    def _emit_enum(self, enum_def: Enum) -> None:
        """Emit Dart enum declaration."""
        name = _safe_pascal(enum_def.name)
        # Check if all variants have int or no explicit values
        all_int = all(v.value is None or isinstance(v.value, int) for v in enum_def.variants)
        if all_int:
            # Simple enum
            self._line(f"enum {name} {{")
            self.indent += 1
            for i, variant in enumerate(enum_def.variants):
                vname = _safe_name(variant.name)
                comma = "," if i < len(enum_def.variants) - 1 else ""
                self._line(f"{vname}{comma}")
            self.indent -= 1
            self._line("}")
        else:
            # Enhanced enum with string values (Dart 2.17+)
            self._line(f"enum {name} {{")
            self.indent += 1
            for i, variant in enumerate(enum_def.variants):
                vname = _safe_name(variant.name)
                if isinstance(variant.value, str):
                    val = f'("{variant.value}")'
                else:
                    val = ""
                comma = "," if i < len(enum_def.variants) - 1 else ";"
                self._line(f"{vname}{val}{comma}")
            if any(isinstance(v.value, str) for v in enum_def.variants):
                self._line("")
                self._line("final String value;")
                self._line(f"const {name}(this.value);")
            self.indent -= 1
            self._line("}")

    def _emit_interface(self, iface: InterfaceDef) -> None:
        self._line(f"abstract class {_safe_pascal(iface.name)} {{")
        self.indent += 1
        # Emit interface fields as abstract getters
        for fld in iface.fields:
            typ = self._type(fld.typ)
            name = _safe_name(fld.name)
            self._line(f"{typ} get {name};")
        for method in iface.methods:
            params = self._params(method.params)
            ret = self._type(method.ret)
            name = _safe_name(method.name)
            self._line(f"{ret} {name}({params});")
        self.indent -= 1
        self._line("}")

    def _emit_struct(self, struct: Struct) -> None:
        class_name = _safe_pascal(struct.name)
        self.current_class = struct.name  # Keep original for field lookup
        # Emit doc comment if present
        if struct.doc:
            self._line(f"/// {struct.doc}")
        extends_clause = ""
        implements_clause = ""
        if struct.is_exception:
            if struct.embedded_type:
                # Child exception class extends parent exception
                parent = _safe_pascal(struct.embedded_type)
                extends_clause = f" extends {parent}"
            else:
                # Base exception class implements Exception (can't extend in Dart 3)
                implements_clause = " implements Exception"
        elif struct.implements:
            implements_clause = f" implements {', '.join(_safe_pascal(i) for i in struct.implements)}"
        self._line(f"class {class_name}{extends_clause}{implements_clause} {{")
        self.indent += 1
        for fld in struct.fields:
            self._emit_field(fld, struct.is_exception)
        if struct.fields:
            self._line("")
        self._emit_constructor(struct)
        for method in struct.methods:
            self._line("")
            self._emit_method(method)
        self.indent -= 1
        self._line("}")
        self.current_class = ""

    def _emit_field(self, fld: Field, is_exception: bool = False) -> None:
        typ = self._type(fld.typ)
        name = _safe_name(fld.name)
        # Make fields nullable if Optional type, otherwise use late
        if isinstance(fld.typ, Optional):
            self._line(f"{typ} {name};")
        elif isinstance(fld.typ, InterfaceRef):
            # Interface fields use dynamic to allow null (Python often passes None
            # even without Optional annotation, and code may check for null)
            self._line(f"dynamic {name};")
        else:
            self._line(f"late {typ} {name};")

    def _emit_constructor(self, struct: Struct) -> None:
        class_name = _safe_pascal(struct.name)
        if not struct.fields:
            if struct.is_exception and struct.embedded_type:
                # Child exception with no additional fields
                self._line(f"{class_name}(String message, int pos, int code) : super(message, pos, code);")
            elif struct.is_exception:
                # Base exception implements Exception, no super() call
                self._line(f"{class_name}();")
            else:
                self._line(f"{class_name}();")
            return
        # Make non-primitive constructor parameters dynamic or nullable to allow null initialization
        param_parts: list[str] = []
        for f in struct.fields:
            typ = self._type(f.typ)
            # Make struct/pointer types nullable, interface types dynamic (to allow null)
            if isinstance(f.typ, (Pointer, StructRef)) and not isinstance(f.typ, Optional):
                param_parts.append(f"{typ}? {_safe_name(f.name)}")
            elif isinstance(f.typ, InterfaceRef):
                # Use dynamic for interface types since Python allows None even without Optional
                param_parts.append(f"dynamic {_safe_name(f.name)}")
            else:
                param_parts.append(f"{typ} {_safe_name(f.name)}")
        params = ", ".join(param_parts)
        if struct.is_exception and not struct.embedded_type:
            # Base exception class implements Exception, no super() call
            self._line(f"{class_name}({params}) {{")
        else:
            self._line(f"{class_name}({params}) {{")
        self.indent += 1
        for f in struct.fields:
            param_name = _safe_name(f.name)
            # Assign with null check bypass for nullable params to late fields
            if isinstance(f.typ, (Pointer, StructRef)) and not isinstance(f.typ, Optional):
                self._line(f"if ({param_name} != null) this.{param_name} = {param_name};")
            elif isinstance(f.typ, InterfaceRef):
                # For interface types (dynamic param), only assign if non-null
                self._line(f"if ({param_name} != null) this.{param_name} = {param_name};")
            else:
                self._line(f"this.{param_name} = {param_name};")
        self.indent -= 1
        self._line("}")

    def _has_null_return(self, stmts: list[Stmt]) -> bool:
        """Check if any statement returns null, directly or indirectly via variable."""
        null_vars: set[str] = set()
        return self._check_null_return(stmts, null_vars)

    def _check_null_return(self, stmts: list[Stmt], null_vars: set[str]) -> bool:
        """Check if statements return null, tracking variables that may be null."""
        for stmt in stmts:
            # Direct return null
            if isinstance(stmt, Return) and isinstance(stmt.value, NilLit):
                return True
            # Return of a variable that was assigned null
            if isinstance(stmt, Return) and isinstance(stmt.value, Var):
                if stmt.value.name in null_vars:
                    return True
            # Track null assignments: result = None or result = null as dynamic
            # Note: targets use VarLV (variable lvalue), not Var
            if isinstance(stmt, Assign):
                if isinstance(stmt.value, NilLit):
                    if isinstance(stmt.target, VarLV):
                        null_vars.add(stmt.target.name)
                elif isinstance(stmt.value, Cast) and isinstance(stmt.value.expr, NilLit):
                    # Handles: result = null as dynamic
                    if isinstance(stmt.target, VarLV):
                        null_vars.add(stmt.target.name)
            if isinstance(stmt, If):
                # Use copies of null_vars for branches, then merge
                then_vars = null_vars.copy()
                else_vars = null_vars.copy()
                if self._check_null_return(stmt.then_body, then_vars):
                    return True
                if stmt.else_body and self._check_null_return(stmt.else_body, else_vars):
                    return True
                # Variables assigned null in either branch could be null
                null_vars.update(then_vars)
                null_vars.update(else_vars)
            if isinstance(stmt, While):
                if self._check_null_return(stmt.body, null_vars.copy()):
                    return True
            if isinstance(stmt, (ForRange, ForClassic)):
                if self._check_null_return(stmt.body, null_vars.copy()):
                    return True
        return False

    def _emit_function(self, func: Function) -> None:
        self._hoisted_vars = set()
        self._declared_vars = {p.name for p in func.params}
        self._func_params = {p.name for p in func.params if isinstance(p.typ, FuncType)}
        self._current_return_type = func.ret
        # Emit doc comment if present
        if func.doc:
            self._line(f"/// {func.doc}")
        params = self._params(func.params)
        ret = self._type(func.ret)
        # Use dynamic return type if function has return null statements
        # This avoids cascading nullable type errors while allowing null returns
        if func.body and self._has_null_return(func.body) and not isinstance(func.ret, Optional):
            ret = "dynamic"
        name = _safe_name(func.name)
        self._line(f"{ret} {name}({params}) {{")
        self.indent += 1
        if not func.body:
            self._line('throw UnimplementedError();')
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")
        self._current_return_type = None

    def _emit_method(self, func: Function) -> None:
        self._hoisted_vars = set()
        self._declared_vars = {p.name for p in func.params}
        self._func_params = {p.name for p in func.params if isinstance(p.typ, FuncType)}
        self._current_return_type = func.ret
        # Emit doc comment if present
        if func.doc:
            self._line(f"/// {func.doc}")
        params = self._params(func.params)
        ret = self._type(func.ret)
        name = _safe_name(func.name)
        # Use dynamic return type if method has return null statements
        if func.body and self._has_null_return(func.body) and not isinstance(func.ret, Optional):
            ret = "dynamic"
            self._nullable_methods.add(name)
        if func.receiver:
            self.receiver_name = func.receiver.name
        self._line(f"{ret} {name}({params}) {{")
        self.indent += 1
        if not func.body:
            self._line('throw UnimplementedError();')
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
            parts.append(f"{typ} {_safe_name(p.name)}")
        return ", ".join(parts)

    def _is_nullable_reference_type(self, typ: Type) -> bool:
        """Check if a type is a reference type that could be null during control flow."""
        if isinstance(typ, (StructRef, InterfaceRef)):
            return True
        if isinstance(typ, Pointer) and isinstance(typ.target, (StructRef, InterfaceRef)):
            return True
        if isinstance(typ, Optional):
            return self._is_nullable_reference_type(typ.inner)
        if isinstance(typ, Tuple):
            # Check if any element of the tuple is a reference type
            for elem in typ.elements:
                if self._is_nullable_reference_type(elem):
                    return True
        return False

    def _emit_hoisted_vars(
        self, stmt: If | While | ForRange | ForClassic | TryCatch | Match | TypeSwitch
    ) -> None:
        hoisted_vars = stmt.hoisted_vars
        for name, typ in hoisted_vars:
            var_name = _safe_name(name)
            if typ:
                # Use dynamic for reference types - they may be null during control flow
                if self._is_nullable_reference_type(typ):
                    self._line(f"dynamic {var_name};")
                else:
                    dart_type = self._type(typ)
                    default = self._default_value(typ)
                    self._line(f"{dart_type} {var_name} = {default};")
            else:
                self._line(f"dynamic {var_name};")
            self._hoisted_vars.add(name)
            self._declared_vars.add(name)

    def _emit_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDecl(name=name, typ=typ, value=value):
                var_name = _safe_name(name)
                self._declared_vars.add(name)
                # For Optional types initialized to null, use late keyword
                # This allows Dart to treat the variable as non-nullable after assignment
                if isinstance(typ, Optional) and (value is None or isinstance(value, NilLit)):
                    inner_type = self._type(typ.inner)
                    self._line(f"late {inner_type} {var_name};")
                elif isinstance(value, NilLit):
                    # Non-Optional type but NilLit value - make nullable for Dart
                    dart_type = self._type(typ)
                    self._line(f"{dart_type}? {var_name} = null;")
                elif value is not None:
                    dart_type = self._type(typ)
                    val = self._expr(value)
                    # If value is Ternary with NilLit else branch, make variable nullable
                    if isinstance(value, Ternary) and isinstance(value.else_expr, NilLit):
                        self._line(f"{dart_type}? {var_name} = {val};")
                    else:
                        self._line(f"{dart_type} {var_name} = {val}; ")
                else:
                    # No value - use dynamic for reference types to avoid null-safety issues
                    if isinstance(typ, (StructRef, InterfaceRef)):
                        self._line(f"dynamic {var_name}; ")
                    else:
                        dart_type = self._type(typ)
                        default = self._default_value(typ)
                        self._line(f"{dart_type} {var_name} = {default};")
            case Assign(target=target, value=value):
                val = self._expr(value)
                if isinstance(target, IndexLV) and isinstance(target.obj.typ, Slice):
                    obj_str = self._expr(target.obj)
                    idx_str = self._expr(target.index)
                    self._line(f"{obj_str}[{idx_str}] = {val};")
                else:
                    lv = self._lvalue(target)
                    target_name = target.name if isinstance(target, VarLV) else None
                    is_hoisted = target_name and target_name in self._hoisted_vars
                    if stmt.is_declaration and not is_hoisted:
                        decl_type = stmt.decl_typ if stmt.decl_typ is not None else value.typ
                        # For Optional types initialized to nil, use late keyword
                        if isinstance(decl_type, Optional) and isinstance(value, NilLit):
                            inner_type = self._type(decl_type.inner)
                            self._line(f"late {inner_type} {lv};")
                        elif isinstance(value, NilLit):
                            # Non-Optional type but NilLit value - make nullable for Dart
                            dart_type = self._type(decl_type) if decl_type else "dynamic"
                            self._line(f"{dart_type}? {lv} = null;")
                        elif isinstance(value, Ternary) and isinstance(value.else_expr, NilLit):
                            # Ternary with null else branch - make nullable
                            dart_type = self._type(decl_type) if decl_type else "dynamic"
                            self._line(f"{dart_type}? {lv} = {val};")
                        else:
                            # Check if value is a call to a nullable method - use dynamic to avoid type errors
                            # Also check if value is a method call returning a reference type that could be null
                            if isinstance(value, (MethodCall, Call)) and self._is_nullable_reference_type(value.typ):
                                self._line(f"dynamic {lv} = {val};")
                            elif isinstance(value, MethodCall) and _safe_name(value.method) in self._nullable_methods:
                                self._line(f"dynamic {lv} = {val};")
                            else:
                                dart_type = self._type(decl_type) if decl_type else "dynamic"
                                self._line(f"{dart_type} {lv} = {val}; ")
                        if target_name:
                            self._declared_vars.add(target_name)
                    else:
                        # Check if variable needs auto-declaration (not declared yet and not hoisted)
                        needs_decl = target_name and target_name not in self._declared_vars and not is_hoisted
                        # For hoisted vars (late), add ! if value is Optional type
                        if is_hoisted and isinstance(value.typ, Optional):
                            val = f"{val}!"
                        # Cast null to dynamic to bypass null safety for assignments
                        if isinstance(value, NilLit):
                            val = "null as dynamic"
                        if needs_decl:
                            # Auto-declare with dynamic type to handle null safely
                            self._line(f"dynamic {lv} = {val};")
                            self._declared_vars.add(target_name)
                        else:
                            self._line(f"{lv} = {val};")
            case OpAssign(target=target, op=op, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                self._line(f"{lv} {op}= {val};")
            case TupleAssign(targets=targets, value=value) if isinstance(
                value, MethodCall
            ) and value.method == "pop":
                self._emit_tuple_pop(stmt)
            case TupleAssign(targets=targets, value=value):
                self._emit_tuple_assign(stmt)
            case NoOp():
                pass
            case ExprStmt(expr=expr):
                e = self._expr(expr)
                self._line(f"{e};")
            case Return(value=value):
                if value is not None:
                    val = self._expr(value)
                    # For Optional return types, just return null directly
                    if isinstance(value, NilLit):
                        if isinstance(self._current_return_type, Optional):
                            val = "null"
                        else:
                            val = "null as dynamic"
                    # Add ! if returning Optional value to non-Optional return type
                    elif isinstance(value.typ, Optional) and self._current_return_type and not isinstance(self._current_return_type, Optional):
                        val = f"{val}!"
                    self._line(f"return {val};")
                else:
                    self._line("return;")
            case If(cond=cond, then_body=then_body, else_body=else_body, init=init):
                self._emit_hoisted_vars(stmt)
                if init is not None:
                    self._emit_stmt(init)
                self._line(f"if ({self._expr(cond)}) {{")
                self.indent += 1
                saved_hoisted = self._hoisted_vars.copy()
                for s in then_body:
                    self._emit_stmt(s)
                self._hoisted_vars = saved_hoisted
                self.indent -= 1
                if else_body:
                    self._line("} else {")
                    self.indent += 1
                    saved_hoisted = self._hoisted_vars.copy()
                    for s in else_body:
                        self._emit_stmt(s)
                    self._hoisted_vars = saved_hoisted
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
                self._line(f"while ({self._expr(cond)}) {{")
                self.indent += 1
                for s in body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("}")
            case Break(label=label):
                if self._current_break_flag:
                    self._line(f"{self._current_break_flag} = true;")
                self._line("break;")
            case Continue(label=label):
                self._line("continue;")
            case Block(body=body):
                no_scope = stmt.no_scope
                if not no_scope:
                    self._line("{")
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
                    self._line("rethrow;")
                else:
                    msg = self._expr(message)
                    pos_expr = self._expr(pos)
                    self._line(f"throw {error_type}({msg}, {pos_expr}, 0);")
            case SoftFail():
                # Cast to dynamic to bypass Dart's strict null safety
                self._line("return null as dynamic;")
            case Print(value=value, newline=newline, stderr=stderr):
                val = self._expr(value)
                if stderr:
                    if newline:
                        self._line(f"stderr.writeln({val});")
                    else:
                        self._line(f"stderr.write({val});")
                else:
                    if newline:
                        self._line(f"print({val});")
                    else:
                        self._line(f"stdout.write({val});")
            case EntryPoint(function_name=function_name):
                # Dart's main() is the entry point; no special marker needed
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
            val_str = self._expr(value)
            # Dart 3 supports record destructuring
            self.temp_counter += 1
            temp_var = f"_tuple{self.temp_counter}"
            self._line(f"final {temp_var} = {val_str};")
            for i, target in enumerate(targets):
                target_name = target.name if isinstance(target, VarLV) else f"_t{i}"
                is_hoisted = target_name in self._hoisted_vars
                is_new = is_decl or (target_name and target_name in new_targets)
                lv = self._lvalue(target)
                accessor = f"{temp_var}.${i + 1}"
                elem_type = value_type.elements[i] if i < len(value_type.elements) else None
                if is_hoisted or not is_new:
                    self._line(f"{lv} = {accessor};")
                else:
                    dart_type = self._type(elem_type) if elem_type else "dynamic"
                    self._line(f"{dart_type} {lv} = {accessor};")
                    if target_name:
                        self._declared_vars.add(target_name)
        else:
            # Fallback for non-tuple multi-returns
            val_str = self._expr(value)
            self.temp_counter += 1
            temp_var = f"_tuple{self.temp_counter}"
            self._line(f"final {temp_var} = {val_str};")
            for i, target in enumerate(targets):
                lv = self._lvalue(target)
                target_name = target.name if isinstance(target, VarLV) else None
                is_hoisted = target_name and target_name in self._hoisted_vars
                if (is_decl or (target_name and target_name in new_targets)) and not is_hoisted:
                    self._line(f"var {lv} = {temp_var}.${i + 1};")
                    if target_name:
                        self._declared_vars.add(target_name)
                else:
                    self._line(f"{lv} = {temp_var}.${i + 1};")

    def _emit_tuple_pop(self, stmt: TupleAssign) -> None:
        """Emit tuple unpacking from list.pop()."""
        mc = stmt.value
        if not isinstance(mc, MethodCall):
            return
        obj = self._expr(mc.obj)
        if mc.args:
            index = self._expr(mc.args[0])
        else:
            index = f"{obj}.length - 1"
        obj_type = mc.obj.typ if mc.obj else None
        elem_type = obj_type.element if isinstance(obj_type, Slice) else mc.typ
        self.temp_counter += 1
        entry_var = f"_entry{self.temp_counter}"
        self._line(f"final {entry_var} = {obj}[{index}];")
        self._line(f"{obj}.removeAt({index});")
        is_decl = stmt.is_declaration
        new_targets = stmt.new_targets
        for i, target in enumerate(stmt.targets):
            lv = self._lvalue(target)
            target_name = target.name if isinstance(target, VarLV) else None
            is_hoisted = target_name and target_name in self._hoisted_vars
            accessor = f"{entry_var}.${i + 1}"
            if isinstance(elem_type, Tuple) and i < len(elem_type.elements):
                field_type = self._type(elem_type.elements[i])
            else:
                field_type = "dynamic"
            if (is_decl or (target_name and target_name in new_targets)) and not is_hoisted:
                self._line(f"{field_type} {lv} = {accessor};")
                if target_name:
                    self._declared_vars.add(target_name)
            else:
                self._line(f"{lv} = {accessor};")

    def _is_terminal_stmt(self, stmt: Stmt) -> bool:
        """Check if a statement is a flow control terminator."""
        return isinstance(stmt, (Return, Continue, Break, Raise))

    def _type_switch_has_break(self, stmt: TypeSwitch) -> bool:
        """Check if any case in a type switch contains a Break statement."""
        for case in stmt.cases:
            for s in case.body:
                if isinstance(s, Break):
                    return True
        if stmt.default:
            for s in stmt.default:
                if isinstance(s, Break):
                    return True
        return False

    def _emit_type_switch(self, stmt: TypeSwitch) -> None:
        self._emit_hoisted_vars(stmt)
        var = self._expr(stmt.expr)
        binding = _safe_name(stmt.binding)
        cases = stmt.cases
        default = stmt.default
        # Check if any case has a Break that needs to propagate past the switch
        needs_break_flag = self._type_switch_has_break(stmt)
        break_flag = None
        old_break_flag = self._current_break_flag
        if needs_break_flag:
            self.temp_counter += 1
            break_flag = f"_breakLoop{self.temp_counter}"
            self._line(f"bool {break_flag} = false;")
            self._current_break_flag = break_flag
        # Use Dart 3 switch with type patterns
        self._line(f"switch ({var}) {{")
        self.indent += 1
        for case in cases:
            type_name = self._type_name_for_check(case.typ)
            # Handle primitive types with different pattern syntax
            if isinstance(case.typ, Primitive):
                # For primitives, use type test pattern
                narrowed_name = f"{binding}{_primitive_type(case.typ.kind)}"
                self._line(f"case {type_name} {narrowed_name}:")
            else:
                narrowed_name = f"{binding}{type_name}"
                self._line(f"case {type_name} {narrowed_name}:")
            self.indent += 1
            self._type_switch_binding_rename[stmt.binding] = narrowed_name
            saved_hoisted = self._hoisted_vars.copy()
            for s in case.body:
                self._emit_stmt(s)
            self._hoisted_vars = saved_hoisted
            self._type_switch_binding_rename.pop(stmt.binding)
            if case.body and not self._is_terminal_stmt(case.body[-1]):
                self._line("break;")
            self.indent -= 1
        if default:
            self._line("default:")
            self.indent += 1
            for s in default:
                self._emit_stmt(s)
            if default and not self._is_terminal_stmt(default[-1]):
                self._line("break;")
            self.indent -= 1
        self.indent -= 1
        self._line("}")
        self._current_break_flag = old_break_flag
        if needs_break_flag:
            self._line(f"if ({break_flag}) break;")

    def _emit_match(self, stmt: Match) -> None:
        self._emit_hoisted_vars(stmt)
        expr_str = self._expr(stmt.expr)
        self._line(f"switch ({expr_str}) {{")
        self.indent += 1
        for case in stmt.cases:
            for pattern in case.patterns:
                self._line(f"case {self._expr(pattern)}:")
            self.indent += 1
            for s in case.body:
                self._emit_stmt(s)
            if case.body and not self._is_terminal_stmt(case.body[-1]):
                self._line("break;")
            self.indent -= 1
        if stmt.default:
            self._line("default:")
            self.indent += 1
            for s in stmt.default:
                self._emit_stmt(s)
            if stmt.default and not self._is_terminal_stmt(stmt.default[-1]):
                self._line("break;")
            self.indent -= 1
        self.indent -= 1
        self._line("}")

    def _emit_for_range(self, stmt: ForRange) -> None:
        self._emit_hoisted_vars(stmt)
        iter_expr = self._expr(stmt.iterable)
        iter_type = stmt.iterable.typ
        # Use fallback empty collection for Optional types (works whether promoted or not)
        if isinstance(iter_type, Optional):
            inner = iter_type.inner
            if isinstance(inner, Slice):
                elem_type = self._type(inner.element)
                iter_expr = f"({iter_expr} ?? <{elem_type}>[])"
            else:
                iter_expr = f"({iter_expr} ?? [])"
            iter_type = inner
        is_string = isinstance(iter_type, Primitive) and iter_type.kind == "string"
        index = stmt.index
        value = stmt.value
        body = stmt.body
        if value is not None and index is not None:
            idx = _safe_name(index)
            val = _safe_name(value)
            val_hoisted = value in self._hoisted_vars
            if is_string:
                self._line(f"for (int {idx} = 0; {idx} < {iter_expr}.length; {idx}++) {{")
                self.indent += 1
                if val_hoisted:
                    self._line(f"{val} = {iter_expr}[{idx}];")
                else:
                    self._line(f"var {val} = {iter_expr}[{idx}];")
            else:
                self._line(f"for (int {idx} = 0; {idx} < {iter_expr}.length; {idx}++) {{")
                self.indent += 1
                elem_type = self._element_type(iter_type)
                if val_hoisted:
                    self._line(f"{val} = {iter_expr}[{idx}];")
                else:
                    self._line(f"{elem_type} {val} = {iter_expr}[{idx}];")
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        elif value is not None:
            val = _safe_name(value)
            is_hoisted = value in self._hoisted_vars
            if is_string:
                self._loop_temp_counter += 1
                temp_var = f"_c{self._loop_temp_counter}"
                self._line(f"for (final {temp_var} in {iter_expr}.split('')) {{")
                self.indent += 1
                if is_hoisted:
                    self._line(f"{val} = {temp_var};")
                else:
                    self._line(f"var {val} = {temp_var};")
            else:
                elem_type = self._element_type(iter_type)
                if is_hoisted:
                    self._loop_temp_counter += 1
                    temp_var = f"_e{self._loop_temp_counter}"
                    self._line(f"for (final {temp_var} in {iter_expr}) {{")
                    self.indent += 1
                    self._line(f"{val} = {temp_var};")
                else:
                    self._line(f"for (final {val} in {iter_expr}) {{")
                    self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        elif index is not None:
            idx = _safe_name(index)
            self._line(f"for (int {idx} = 0; {idx} < {iter_expr}.length; {idx}++) {{")
            self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        else:
            # For strings, use .codeUnits since String is not Iterable in Dart
            if is_string:
                self._line(f"for (final _ in {iter_expr}.codeUnits) {{")
            else:
                self._line(f"for (final _ in {iter_expr}) {{")
            self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")

    def _emit_for_classic(self, stmt: ForClassic) -> None:
        self._emit_hoisted_vars(stmt)
        init_str = self._stmt_inline(stmt.init) if stmt.init else ""
        cond_str = self._expr(stmt.cond) if stmt.cond else ""
        post_str = self._stmt_inline(stmt.post) if stmt.post else ""
        self._line(f"for ({init_str}; {cond_str}; {post_str}) {{")
        self.indent += 1
        for s in stmt.body:
            self._emit_stmt(s)
        self.indent -= 1
        self._line("}")

    def _stmt_inline(self, stmt: Stmt) -> str:
        match stmt:
            case VarDecl(name=name, typ=typ, value=value):
                var_name = _safe_name(name)
                # For Optional types initialized to null in inline context, use inner type
                if isinstance(typ, Optional) and (value is None or isinstance(value, NilLit)):
                    inner_type = self._type(typ.inner)
                    return f"late {inner_type} {var_name}"
                dart_type = self._type(typ)
                if value:
                    return f"{dart_type} {var_name} = {self._expr(value)}"
                return f"{dart_type} {var_name}"
            case Assign(target=target, value=value):
                if isinstance(value, BinaryOp) and value.op == "+":
                    if isinstance(value.right, IntLit) and value.right.value == 1:
                        if isinstance(target, VarLV) and isinstance(value.left, Var):
                            if target.name == value.left.name:
                                return f"{_safe_name(target.name)}++"
                return f"{self._lvalue(target)} = {self._expr(value)}"
            case OpAssign(target=target, op=op, value=value):
                return f"{self._lvalue(target)} {op}= {self._expr(value)}"
            case _:
                return ""

    def _emit_try_catch(self, stmt: TryCatch) -> None:
        self._emit_hoisted_vars(stmt)
        self._line("try {")
        self.indent += 1
        for s in stmt.body:
            self._emit_stmt(s)
        self.indent -= 1
        exc_type = stmt.catch_type.name if isinstance(stmt.catch_type, StructRef) else "Exception"
        if stmt.catch_var_unused or not stmt.catch_var:
            self._line(f"}} on {exc_type} {{")
        else:
            var = _safe_name(stmt.catch_var)
            self._line(f"}} on {exc_type} catch ({var}) {{")
        self.indent += 1
        for s in stmt.catch_body:
            self._emit_stmt(s)
        if stmt.reraise:
            self._line("rethrow;")
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
                return "null"
            case Var(name=name):
                if name in self._type_switch_binding_rename:
                    return self._type_switch_binding_rename[name]
                if name == self.receiver_name:
                    return "this"
                return _safe_name(name)
            case FieldAccess(obj=obj, field=field):
                obj_str = self._expr(obj)
                obj_type = obj.typ
                # Use null assertion for Optional types
                if isinstance(obj_type, Optional):
                    obj_str = f"{obj_str}!"
                    obj_type = obj_type.inner
                # Handle tuple field access (F0, F1 -> $1, $2)
                if isinstance(obj_type, Tuple) and field.startswith("F") and field[1:].isdigit():
                    idx = int(field[1:]) + 1
                    return f"{obj_str}.${idx}"
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
                if isinstance(obj_type, Tuple):
                    if isinstance(index, IntLit):
                        return f"{obj_str}.${index.value + 1}"
                    return f"{obj_str}.${idx_str}"
                return f"{obj_str}[{idx_str}]"
            case SliceExpr(obj=obj, low=low, high=high):
                return self._slice_expr(obj, low, high)
            case ParseInt(string=s, base=b):
                return f"int.parse({self._expr(s)}, radix: {self._expr(b)})"
            case IntToStr(value=v):
                return f"{self._expr(v)}.toString()"
            case CharClassify(kind=kind, char=char):
                char_str = self._expr(char)
                # Dart doesn't have built-in char classification, use RegExp
                regex_map = {
                    "digit": r"RegExp(r'^\d+$')",
                    "alpha": r"RegExp(r'^[a-zA-Z]+$')",
                    "alnum": r"RegExp(r'^[a-zA-Z0-9]+$')",
                    "space": r"RegExp(r'^\s+$')",
                    "upper": r"RegExp(r'^[A-Z]+$')",
                    "lower": r"RegExp(r'^[a-z]+$')",
                }
                return f"({char_str}.isNotEmpty && {regex_map[kind]}.hasMatch({char_str}))"
            case TrimChars(string=s, chars=chars, mode=mode):
                s_str = self._expr(s)
                # Dart's built-in trim removes ALL whitespace (space, tab, newline, etc.)
                # Only use built-in if chars is empty (meaning trim all whitespace)
                # NOT when chars is specified (even if it's just space/tab), since that
                # would incorrectly trim newlines too
                if isinstance(chars, StringLit) and not chars.value:
                    if mode == "both":
                        return f"{s_str}.trim()"
                    elif mode == "left":
                        return f"{s_str}.trimLeft()"
                    else:
                        return f"{s_str}.trimRight()"
                # Custom trim chars - use helper functions
                chars_str = self._expr(chars)
                if mode == "left":
                    return f"_trimLeft({s_str}, {chars_str})"
                elif mode == "right":
                    return f"_trimRight({s_str}, {chars_str})"
                else:
                    return f"_trimBoth({s_str}, {chars_str})"
            case Call(func=func, args=args):
                return self._call(func, args)
            case MethodCall(obj=obj, method=method, args=args, receiver_type=receiver_type):
                return self._method_call(obj, method, args, receiver_type)
            case StaticCall(on_type=on_type, method=method, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                type_name = self._type_name_for_check(on_type)
                return f"{type_name}.{_safe_name(method)}({args_str})"
            case Truthy(expr=e):
                inner_str = self._expr(e)
                inner_type = e.typ
                if _is_string_type(inner_type):
                    return f"({inner_str}.isNotEmpty)"
                if isinstance(inner_type, (Slice, Map, Set)):
                    return f"({inner_str}.isNotEmpty)"
                if isinstance(inner_type, Optional) and isinstance(inner_type.inner, (Slice, Map, Set)):
                    # Use null-safe access - works whether Dart promoted the variable or not
                    return f"({inner_str}?.isNotEmpty ?? false)"
                if isinstance(inner_type, Optional) and isinstance(inner_type.inner, Primitive) and inner_type.inner.kind == "string":
                    return f"({inner_str}?.isNotEmpty ?? false)"
                if isinstance(inner_type, Primitive) and inner_type.kind == "int":
                    return f"({inner_str} != 0)"
                return f"({inner_str} != null)"
            case BinaryOp(op="in", left=left, right=right):
                return self._containment_check(left, right, negated=False)
            case BinaryOp(op="not in", left=left, right=right):
                return self._containment_check(left, right, negated=True)
            case BinaryOp(op=op, left=left, right=right):
                left_str = self._expr(left)
                right_str = self._expr(right)
                dart_op = _binary_op(op)
                # Handle string comparisons - Dart doesn't support >, <, >=, <= on strings
                left_type = left.typ
                right_type = right.typ
                if (op in (">=", "<=", ">", "<") and
                    isinstance(left_type, Primitive) and left_type.kind == "string" and
                    isinstance(right_type, Primitive) and right_type.kind == "string"):
                    # Use compareTo for string comparisons
                    compare_val = "0"
                    if op == ">=":
                        return f"({left_str}.compareTo({right_str}) >= 0)"
                    if op == "<=":
                        return f"({left_str}.compareTo({right_str}) <= 0)"
                    if op == ">":
                        return f"({left_str}.compareTo({right_str}) > 0)"
                    if op == "<":
                        return f"({left_str}.compareTo({right_str}) < 0)"
                # Add parens around || when inside && to preserve precedence
                if dart_op == "&&":
                    if isinstance(left, BinaryOp) and left.op == "||":
                        left_str = f"({left_str})"
                    if isinstance(right, BinaryOp) and right.op == "||":
                        right_str = f"({right_str})"
                return f"{left_str} {dart_op} {right_str}"
            case UnaryOp(op="&", operand=operand):
                return self._expr(operand)
            case UnaryOp(op="*", operand=operand):
                return self._expr(operand)
            case UnaryOp(op="!", operand=operand):
                operand_type = operand.typ
                operand_str = self._expr(operand)
                # Convert Python truthiness to Dart explicit boolean checks
                if isinstance(operand_type, Primitive):
                    if operand_type.kind == "int":
                        return f"({operand_str} == 0)"
                    if operand_type.kind == "string":
                        return f"({operand_str}.isEmpty)"
                    if operand_type.kind == "bool":
                        return f"!({operand_str})"
                if isinstance(operand_type, (InterfaceRef, StructRef, Pointer)):
                    return f"({operand_str} == null)"
                if isinstance(operand_type, Slice):
                    return f"({operand_str}.isEmpty)"
                if isinstance(operand_type, Map):
                    return f"({operand_str}.isEmpty)"
                return f"!({operand_str})"
            case UnaryOp(op=op, operand=operand):
                return f"{op}{self._expr(operand)}"
            case Ternary(cond=cond, then_expr=then_expr, else_expr=else_expr):
                else_str = self._expr(else_expr)
                if isinstance(else_expr, NilLit):
                    if isinstance(then_expr.typ, Slice):
                        elem = self._type(then_expr.typ.element)
                        else_str = f"<{elem}>[]"
                    # Otherwise just use null - variable will be declared nullable
                return f"({self._expr(cond)} ? {self._expr(then_expr)} : {else_str})"
            case Cast(expr=inner, to_type=to_type):
                return self._cast(inner, to_type)
            case TypeAssert(expr=inner, asserted=asserted):
                type_name = self._type(asserted)
                return f"({self._expr(inner)} as {type_name})"
            case IsType(expr=inner, tested_type=tested_type):
                type_name = self._type_name_for_check(tested_type)
                return f"({self._expr(inner)} is {type_name})"
            case IsNil(expr=inner, negated=negated):
                inner_type = inner.typ
                # For non-nullable list types, check emptiness instead of null
                if isinstance(inner_type, (Slice, Map, Set)):
                    inner_str = self._expr(inner)
                    if negated:
                        return f"({inner_str}.isNotEmpty)"
                    return f"({inner_str}.isEmpty)"
                if negated:
                    return f"{self._expr(inner)} != null"
                return f"{self._expr(inner)} == null"
            case Len(expr=inner):
                inner_str = self._expr(inner)
                inner_type = inner.typ
                # Add ! for Optional types since Dart can't promote instance fields
                if isinstance(inner_type, Optional):
                    inner_str = f"{inner_str}!"
                return f"{inner_str}.length"
            case MakeSlice(element_type=element_type, length=length, capacity=capacity):
                elem_type = self._type(element_type)
                if length:
                    return f"List<{elem_type}>.filled({self._expr(length)}, {self._default_value(element_type)})"
                return f"<{elem_type}>[]"
            case MakeMap(key_type=key_type, value_type=value_type):
                kt = self._type(key_type)
                vt = self._type(value_type)
                return f"<{kt}, {vt}>{{}}"
            case SliceLit(elements=elements, element_type=element_type):
                elem_type = self._type(element_type)
                if not elements:
                    return f"<{elem_type}>[]"
                elems = ", ".join(self._expr(e) for e in elements)
                return f"<{elem_type}>[{elems}]"
            case MapLit(entries=entries, key_type=key_type, value_type=value_type):
                kt = self._type(key_type)
                vt = self._type(value_type)
                if not entries:
                    return f"<{kt}, {vt}>{{}}"
                pairs = ", ".join(f"{self._expr(k)}: {self._expr(v)}" for k, v in entries)
                return f"<{kt}, {vt}>{{{pairs}}}"
            case SetLit(elements=elements, element_type=element_type):
                elem_type = self._type(element_type)
                if not elements:
                    return f"<{elem_type}>{{}}"
                elems = ", ".join(self._expr(e) for e in elements)
                return f"<{elem_type}>{{{elems}}}"
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
                # Dart doesn't have char literals; use string or code unit
                escaped = escape_string(value)
                return f'"{escaped}"'
            case CharAt(string=s, index=index):
                s_str = self._expr(s)
                idx_str = self._expr(index)
                return f"{s_str}[{idx_str}]"
            case CharLen(string=s):
                s_str = self._expr(s)
                return f"{s_str}.length"
            case Substring(string=s, low=low, high=high):
                s_str = self._expr(s)
                # Use safe substring that clamps indices like Python does
                if low and high:
                    return f"_safeSubstring({s_str}, {self._expr(low)}, {self._expr(high)})"
                elif low:
                    return f"{s_str}.substring({self._expr(low)})"
                elif high:
                    return f"_safeSubstring({s_str}, 0, {self._expr(high)})"
                return s_str
            case LastElement(sequence=seq):
                seq_str = self._expr(seq)
                return f"{seq_str}.last"
            case SliceConvert(source=source, target_element_type=target_elem):
                # Dart uses covariant generics for List, no conversion needed
                return self._expr(source)
            case SentinelToOptional(expr=e, sentinel=sentinel):
                e_str = self._expr(e)
                sentinel_str = self._expr(sentinel)
                return f"({e_str} == {sentinel_str} ? null : {e_str})"
            case Args():
                # Dart: command-line args passed to main, need import 'dart:io'
                return "Platform.executableArguments"
            case GetEnv(name=name, default=default):
                name_str = self._expr(name)
                if default:
                    default_str = self._expr(default)
                    return f"(Platform.environment[{name_str}] ?? {default_str})"
                return f"Platform.environment[{name_str}]"
            case ReadLine():
                return "stdin.readLineSync() ?? ''"
            case ReadAll():
                # Read all from stdin
                return "stdin.readAsStringSync()"
            case ListComp(element=element, target=target, iterable=iterable, condition=condition):
                iter_str = self._expr(iterable)
                elem_str = self._expr(element)
                var = _safe_name(target)
                if condition:
                    cond_str = self._expr(condition)
                    return f"{iter_str}.where(({var}) => {cond_str}).map(({var}) => {elem_str}).toList()"
                return f"{iter_str}.map(({var}) => {elem_str}).toList()"
            case SetComp(element=element, target=target, iterable=iterable, condition=condition):
                iter_str = self._expr(iterable)
                elem_str = self._expr(element)
                var = _safe_name(target)
                if condition:
                    cond_str = self._expr(condition)
                    return f"{iter_str}.where(({var}) => {cond_str}).map(({var}) => {elem_str}).toSet()"
                return f"{iter_str}.map(({var}) => {elem_str}).toSet()"
            case DictComp(key=key, value=value, target=target, iterable=iterable, condition=condition):
                iter_str = self._expr(iterable)
                key_str = self._expr(key)
                val_str = self._expr(value)
                var = _safe_name(target)
                if condition:
                    cond_str = self._expr(condition)
                    return f"Map.fromEntries({iter_str}.where(({var}) => {cond_str}).map(({var}) => MapEntry({key_str}, {val_str})))"
                return f"Map.fromEntries({iter_str}.map(({var}) => MapEntry({key_str}, {val_str})))"
            case _:
                return "null /* TODO: unknown expression */"

    def _call(self, func: str, args: list[Expr]) -> str:
        # Don't add ! for Optional args - Dart's flow analysis handles promotion
        # for locals/params after null checks, and we use null-safe patterns elsewhere
        arg_parts: list[str] = []
        for a in args:
            arg_parts.append(self._expr(a))
        args_str = ", ".join(arg_parts)
        if func == "int" and len(args) == 2:
            return f"int.parse({self._expr(args[0])}, radix: {self._expr(args[1])})"
        if func == "str":
            if args and isinstance(args[0].typ, Slice):
                elem_type = args[0].typ.element
                if isinstance(elem_type, Primitive) and elem_type.kind == "byte":
                    return f"String.fromCharCodes({self._expr(args[0])})"
            return f"({self._expr(args[0])}).toString()"
        if func == "len":
            arg = self._expr(args[0])
            return f"{arg}.length"
        if func == "range":
            if len(args) == 1:
                return f"List.generate({self._expr(args[0])}, (i) => i)"
            elif len(args) == 2:
                start = self._expr(args[0])
                stop = self._expr(args[1])
                return f"List.generate({stop} - {start}, (i) => {start} + i)"
            else:
                start = self._expr(args[0])
                stop = self._expr(args[1])
                step = self._expr(args[2])
                return f"_range({start}, {stop}, {step})"
        if func == "ord":
            return f"({self._expr(args[0])}).codeUnitAt(0)"
        if func == "chr":
            return f"String.fromCharCode({self._expr(args[0])})"
        if func == "abs":
            return f"({self._expr(args[0])}).abs()"
        if func == "min":
            if len(args) == 2:
                return f"_min({args_str})"
            return f"[{args_str}].reduce((a, b) => a < b ? a : b)"
        if func == "max":
            if len(args) == 2:
                return f"_max({args_str})"
            return f"[{args_str}].reduce((a, b) => a > b ? a : b)"
        if func in ("_intPtr", "_int_ptr"):
            return self._expr(args[0])
        if func in self._func_params:
            return f"{_safe_name(func)}({args_str})"
        return f"{_safe_name(func)}({args_str})"

    def _method_call(self, obj: Expr, method: str, args: list[Expr], receiver_type: Type) -> str:
        # Don't add ! for Optional args - Dart's flow analysis handles promotion
        # for locals/params after null checks, and we use null-safe patterns elsewhere
        arg_parts: list[str] = []
        for a in args:
            arg_parts.append(self._expr(a))
        args_str = ", ".join(arg_parts)
        obj_str = self._expr(obj)
        # Use null assertion for Optional receiver types
        if isinstance(receiver_type, Optional):
            obj_str = f"{obj_str}!"
            receiver_type = receiver_type.inner
        if isinstance(receiver_type, Slice):
            if method == "append" and args:
                return f"{obj_str}.add({args_str})"
            if method == "pop":
                if args:
                    idx = self._expr(args[0])
                    return f"{obj_str}.removeAt({idx})"
                return f"{obj_str}.removeLast()"
            if method == "copy":
                elem_type = self._type(receiver_type.element)
                return f"List<{elem_type}>.from({obj_str})"
            if method == "decode":
                elem = receiver_type.element
                if isinstance(elem, Primitive) and elem.kind == "byte":
                    # Use utf8.decode with allowMalformed to replace invalid UTF-8 with U+FFFD
                    # This matches Python's bytes.decode("utf-8", errors="replace")
                    return f"utf8.decode({obj_str}, allowMalformed: true)"
        if isinstance(receiver_type, Primitive) and receiver_type.kind == "string":
            if method == "startswith":
                if len(args) == 2:
                    prefix = self._expr(args[0])
                    pos = self._expr(args[1])
                    return f"({obj_str}.indexOf({prefix}, {pos}) == {pos})"
                return f"{obj_str}.startsWith({args_str})"
            if method == "endswith":
                if args and isinstance(args[0], TupleLit):
                    checks = [f"{obj_str}.endsWith({self._expr(e)})" for e in args[0].elements]
                    return "(" + " || ".join(checks) + ")"
                return f"{obj_str}.endsWith({args_str})"
            if method == "find":
                return f"{obj_str}.indexOf({args_str})"
            if method == "rfind":
                return f"{obj_str}.lastIndexOf({args_str})"
            if method == "replace":
                return f"{obj_str}.replaceAll({args_str})"
            if method == "split":
                return f"{obj_str}.split({args_str})"
            if method == "join":
                return f"{args_str}.join({obj_str})"
            if method == "lower":
                return f"{obj_str}.toLowerCase()"
            if method == "upper":
                return f"{obj_str}.toUpperCase()"
        if isinstance(receiver_type, Map):
            if method == "get" and len(args) == 2:
                key = self._expr(args[0])
                default = self._expr(args[1])
                return f"({obj_str}[{key}] ?? {default})"
        if method == "append":
            return f"{obj_str}.add({args_str})"
        if method == "extend":
            return f"{obj_str}.addAll({args_str})"
        if method == "remove":
            return f"{obj_str}.remove({args_str})"
        if method == "clear":
            return f"{obj_str}.clear()"
        if method == "insert":
            return f"{obj_str}.insert({args_str})"
        if method == "endswith":
            if args and isinstance(args[0], TupleLit):
                checks = [f"{obj_str}.endsWith({self._expr(e)})" for e in args[0].elements]
                return "(" + " || ".join(checks) + ")"
            return f"{obj_str}.endsWith({args_str})"
        if method == "startswith":
            return f"{obj_str}.startsWith({args_str})"
        if method == "join":
            return f"{args_str}.join({obj_str})"
        return f"{obj_str}.{_safe_name(method)}({args_str})"

    def _slice_expr(self, obj: Expr, low: Expr | None, high: Expr | None) -> str:
        obj_str = self._expr(obj)
        if isinstance(obj.typ, Primitive) and obj.typ.kind == "string":
            # Use safe substring to clamp indices like Python slice semantics
            if low and high:
                lo = self._expr(low)
                hi = self._expr(high)
                return f"_safeSubstring({obj_str}, {lo}, {hi})"
            elif low:
                return f"{obj_str}.substring({self._expr(low)})"
            elif high:
                return f"_safeSubstring({obj_str}, 0, {self._expr(high)})"
            return obj_str
        if low and high:
            lo = self._expr(low)
            hi = self._expr(high)
            return f"{obj_str}.sublist({lo}, {hi})"
        elif low:
            lo = self._expr(low)
            return f"{obj_str}.sublist({lo})"
        elif high:
            return f"{obj_str}.sublist(0, {self._expr(high)})"
        # Full copy - need to preserve element type
        if isinstance(obj.typ, Slice):
            elem_type = self._type(obj.typ.element)
            return f"List<{elem_type}>.from({obj_str})"
        return f"List.from({obj_str})"

    def _containment_check(self, item: Expr, container: Expr, negated: bool) -> str:
        item_str = self._expr(item)
        container_str = self._expr(container)
        container_type = container.typ
        neg = "!" if negated else ""
        if isinstance(container_type, Set):
            return f"{neg}{container_str}.contains({item_str})"
        if isinstance(container_type, Map):
            return f"{neg}{container_str}.containsKey({item_str})"
        if isinstance(container_type, Primitive) and container_type.kind == "string":
            return f"{neg}{container_str}.contains({item_str})"
        return f"{neg}{container_str}.contains({item_str})"

    def _cast(self, inner: Expr, to_type: Type) -> str:
        inner_str = self._expr(inner)
        dart_type = self._type(to_type)
        inner_type = inner.typ
        if isinstance(to_type, Primitive):
            if to_type.kind == "int":
                if isinstance(inner_type, Primitive) and inner_type.kind == "float":
                    return f"({inner_str}).toInt()"
                # When casting from Index of a string to int, need codeUnitAt
                # because Dart's string[i] returns String, not int
                if isinstance(inner, Index):
                    obj_type = inner.obj.typ
                    if isinstance(obj_type, Primitive) and obj_type.kind == "string":
                        obj_str = self._expr(inner.obj)
                        idx_str = self._expr(inner.index)
                        return f"{obj_str}.codeUnitAt({idx_str})"
                # When inner is a string (single char), use codeUnitAt(0)
                if isinstance(inner_type, Primitive) and inner_type.kind == "string":
                    return f"({inner_str}).codeUnitAt(0)"
                return f"({inner_str} as int)"
            if to_type.kind == "float":
                if isinstance(inner_type, Primitive) and inner_type.kind == "int":
                    return f"({inner_str}).toDouble()"
                return f"({inner_str} as double)"
            if to_type.kind == "string":
                if isinstance(inner_type, Slice):
                    elem = inner_type.element
                    if isinstance(elem, Primitive) and elem.kind == "byte":
                        # Use utf8.decode with allowMalformed to replace invalid UTF-8 with U+FFFD
                        # This matches Python's bytes.decode("utf-8", errors="replace")
                        return f"utf8.decode({inner_str}, allowMalformed: true)"
                if isinstance(inner_type, Primitive) and inner_type.kind == "rune":
                    return f"String.fromCharCode({inner_str})"
                return f"({inner_str}).toString()"
            if to_type.kind == "rune":
                # Only call codeUnitAt if inner is a string
                if isinstance(inner_type, Primitive) and inner_type.kind == "string":
                    return f"({inner_str}).codeUnitAt(0)"
                # If already an int/rune, just use it directly
                return inner_str
        # String to bytes conversion (UTF-8 encoding)
        if isinstance(to_type, Slice) and isinstance(to_type.element, Primitive) and to_type.element.kind == "byte":
            if isinstance(inner_type, Primitive) and inner_type.kind == "string":
                # Use utf8.encode for proper UTF-8 encoding, matching Python's str.encode("utf-8")
                return f"utf8.encode({inner_str})"
        return f"({inner_str} as {dart_type})"

    def _format_string(self, template: str, args: list[Expr]) -> str:
        # Escape the template FIRST (before adding interpolations),
        # so we don't escape the ${} we intentionally add
        escaped_template = escape_string(template)
        result = escaped_template
        # Handle {0}, {1} style placeholders
        for i, arg in enumerate(args):
            if isinstance(arg, StringLit):
                val = arg.value.replace("\\", "\\\\").replace("$", r"\$").replace('"', r'\"')
                result = result.replace(f"{{{i}}}", val, 1)
            else:
                result = result.replace(f"{{{i}}}", f"${{{self._expr(arg)}}}", 1)
        # Handle %v placeholders
        arg_idx = 0
        while "%v" in result:
            if arg_idx >= len(args):
                break
            arg = args[arg_idx]
            arg_idx += 1
            if isinstance(arg, StringLit):
                val = arg.value.replace("\\", "\\\\").replace("$", r"\$").replace('"', r'\"')
                result = result.replace("%v", val, 1)
            else:
                result = result.replace("%v", f"${{{self._expr(arg)}}}", 1)
        return f'"{result}"'

    def _struct_lit(self, struct_name: str, fields: dict[str, Expr], embedded_value: Expr | None) -> str:
        safe_name = _safe_pascal(struct_name)
        field_info = self.struct_fields.get(struct_name, [])
        if field_info:
            ordered_args = []
            for field_name, field_type in field_info:
                if field_name in fields:
                    field_val = fields[field_name]
                    if isinstance(field_val, NilLit) and isinstance(field_type, Slice):
                        elem = self._type(field_type.element)
                        ordered_args.append(f"<{elem}>[]")
                    elif isinstance(field_val, NilLit) and not isinstance(field_type, Optional):
                        # Null for non-Optional field - cast to dynamic for Dart null safety
                        ordered_args.append("null as dynamic")
                    else:
                        ordered_args.append(self._expr(field_val))
                else:
                    ordered_args.append(self._default_value(field_type))
            return f"{safe_name}({', '.join(ordered_args)})"
        elif embedded_value is not None:
            if isinstance(embedded_value, StructLit):
                parent_args = ", ".join(self._expr(v) for v in embedded_value.fields.values())
                return f"{safe_name}({parent_args})"
            return f"{safe_name}({self._expr(embedded_value)})"
        elif not fields:
            return f"{safe_name}()"
        else:
            args = ", ".join(self._expr(v) for v in fields.values())
            return f"{safe_name}({args})"

    def _lvalue(self, lv: LValue) -> str:
        match lv:
            case VarLV(name=name):
                if name == self.receiver_name:
                    return "this"
                return _safe_name(name)
            case FieldLV(obj=obj, field=field):
                obj_str = self._expr(obj)
                # Use null assertion for Optional types
                if isinstance(obj.typ, Optional):
                    obj_str = f"{obj_str}!"
                return f"{obj_str}.{_safe_name(field)}"
            case IndexLV(obj=obj, index=index):
                return f"{self._expr(obj)}[{self._expr(index)}]"
            case DerefLV(ptr=ptr):
                return self._expr(ptr)
            case _:
                return "null /* lvalue: unknown */"

    def _type(self, typ: Type) -> str:
        match typ:
            case Primitive(kind=kind):
                return _primitive_type(kind)
            case Slice(element=element):
                elem = self._type(element)
                return f"List<{elem}>"
            case Array(element=element, size=size):
                return f"List<{self._type(element)}>"
            case Map(key=key, value=value):
                kt = self._type(key)
                vt = self._type(value)
                return f"Map<{kt}, {vt}>"
            case Set(element=element):
                et = self._type(element)
                return f"Set<{et}>"
            case Tuple(elements=elements):
                types = ", ".join(self._type(t) for t in elements)
                return f"({types})"
            case Pointer(target=target):
                return self._type(target)
            case Optional(inner=inner):
                inner_type = self._type(inner)
                return f"{inner_type}?"
            case StructRef(name=name):
                return _safe_pascal(name)
            case InterfaceRef(name=name):
                if name == "any":
                    return "dynamic"
                return _safe_pascal(name)
            case Union(name=name):
                if name:
                    return _safe_pascal(name)
                return "dynamic"
            case FuncType(params=params, ret=ret):
                if ret == Primitive("void"):
                    if not params:
                        return "void Function()"
                    param_types = ", ".join(self._type(p) for p in params)
                    return f"void Function({param_types})"
                if not params:
                    return f"{self._type(ret)} Function()"
                param_types = ", ".join(self._type(p) for p in params)
                return f"{self._type(ret)} Function({param_types})"
            case _:
                return "dynamic"

    def _type_name_for_check(self, typ: Type) -> str:
        match typ:
            case StructRef(name=name):
                return _safe_pascal(name)
            case InterfaceRef(name=name):
                return _safe_pascal(name)
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
                return "dynamic"

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
                elem = self._type(typ.element)
                return f"<{elem}>[]"
            case Tuple(elements=elements):
                defaults = ", ".join(self._default_value(t) for t in elements)
                return f"({defaults})"
            case Optional():
                return "null"
            case Map():
                return "{}"
            case Set():
                return "{}"
            case _:
                # Cast null to dynamic for non-Optional types to bypass Dart null safety
                return "null as dynamic"

    def _emit_helpers(self) -> None:
        """Emit helper functions needed by generated code."""
        self._line("// Helper functions")
        self._line("int _min(int a, int b) => a < b ? a : b;")
        self._line("int _max(int a, int b) => a > b ? a : b;")
        self._line("")
        self._line("// Safe substring that clamps indices like Python slice semantics")
        self._line("String _safeSubstring(String s, int start, int end) {")
        self.indent += 1
        self._line("if (start < 0) start = 0;")
        self._line("if (end > s.length) end = s.length;")
        self._line("if (start >= end) return '';")
        self._line("return s.substring(start, end);")
        self.indent -= 1
        self._line("}")
        self._line("")
        self._line("List<int> _range(int start, int stop, int step) {")
        self.indent += 1
        self._line("final result = <int>[];")
        self._line("if (step > 0) {")
        self.indent += 1
        self._line("for (var i = start; i < stop; i += step) result.add(i);")
        self.indent -= 1
        self._line("} else {")
        self.indent += 1
        self._line("for (var i = start; i > stop; i += step) result.add(i);")
        self.indent -= 1
        self._line("}")
        self._line("return result;")
        self.indent -= 1
        self._line("}")
        self._line("")
        self._line("String _trimLeft(String s, String chars) {")
        self.indent += 1
        self._line("int i = 0;")
        self._line("while (i < s.length && chars.contains(s[i])) i++;")
        self._line("return s.substring(i);")
        self.indent -= 1
        self._line("}")
        self._line("")
        self._line("String _trimRight(String s, String chars) {")
        self.indent += 1
        self._line("int i = s.length;")
        self._line("while (i > 0 && chars.contains(s[i - 1])) i--;")
        self._line("return s.substring(0, i);")
        self.indent -= 1
        self._line("}")
        self._line("")
        self._line("String _trimBoth(String s, String chars) {")
        self.indent += 1
        self._line("return _trimRight(_trimLeft(s, chars), chars);")
        self.indent -= 1
        self._line("}")


def _primitive_type(kind: str) -> str:
    match kind:
        case "string":
            return "String"
        case "int":
            return "int"
        case "float":
            return "double"
        case "bool":
            return "bool"
        case "byte":
            return "int"
        case "rune":
            return "int"
        case "void":
            return "void"
        case _:
            return "dynamic"


def _binary_op(op: str) -> str:
    match op:
        case "&&":
            return "&&"
        case "||":
            return "||"
        case _:
            return op


def _is_string_type(typ: Type) -> bool:
    return isinstance(typ, Primitive) and typ.kind in ("string", "rune")
