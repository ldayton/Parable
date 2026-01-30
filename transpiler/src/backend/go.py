"""GoBackend: IR -> Go code.

Pure syntax emission - no analysis. All type information comes from IR.

COMPENSATIONS FOR EARLIER STAGE DEFICIENCIES
============================================

Frontend deficiencies (should be fixed in frontend.py):
- _extract_type_suffix checks hardcoded prefixes "Arith", "Cond" for type switch
  binding names - frontend should emit type-agnostic IR for narrowed bindings
- _runeAt, _runeLen, _Substring helpers exist because frontend emits string
  indexing as Index nodes without distinguishing byte vs character semantics.
  Frontend should emit distinct IR for character-based string operations.
- ExprStmt filters expressions starting with "skip", "pass", "localFunc" -
  frontend emits these markers that should be handled before backend.

Middleend deficiencies (should be fixed in middleend.py):
- _infer_tuple_element_type scans return statements to infer hoisted variable
  types - middleend should annotate hoisted_vars with complete type information
  instead of leaving typ=None for some variables.

UNCOMPENSATED DEFICIENCIES (non-idiomatic output)
=================================================

The dominant issue is string vs []rune representation. Python strings are
character sequences; Go strings are byte sequences. The backend defensively
emits _runeAt/_runeLen/_Substring helpers for ALL string operations (~540
call sites), but idiomatic Go would:
  1. Analyze string usage patterns in frontend/middleend
  2. Type variables as []rune when indexed by character (e.g., lexer source)
  3. Convert once at scope entry: `runes := []rune(source)`
  4. Then use direct indexing: `runes[i]` instead of `_runeAt(source, i)`
This would eliminate most helper calls and enable standard Go range iteration.
Downstream consequences of this missing analysis:
  - ~100 while-style loops (`for i < n`) instead of `for i, c := range runes`
  - ~60 helper predicates take string instead of rune: `isHexDigit(string)`
    should be `isHexDigit(rune)` with direct comparisons like `c >= '0'`

Frontend deficiencies (should be fixed in frontend.py):
- Helper function indirection: `_parseInt(x, 10)` helper instead of inline
  error-ignoring pattern, `_intPtr(fd)` instead of inline pointer creation.
  (~15 call sites)
- Range() helper allocates slices: `for _, i := range Range(n)` instead of
  `for i := 0; i < n; i++`. Frontend should emit ForClassic IR. (~11 sites)
- IIFE for ternary: `func() T { if c { return a } else { return b } }()`.
  Frontend could emit Ternary with a flag indicating if/else expansion is
  acceptable, or middleend could lift to variable assignment. (~30 sites)
- Factory functions assign field-by-field (`self := &T{}; self.X = v; ...`)
  instead of struct literals (`&T{X: v, ...}`). Frontend should emit
  StructLit with all fields when translating __init__ methods. (~7 factories)

Middleend deficiencies (should be fixed in middleend.py):
- _isNilInterfaceRef() uses reflection for interface nil checks (~92 sites).
  Middleend could track when expressions are definitely interface{} vs typed
  nil pointers, allowing direct `== nil` comparison in simple cases.

"""

from __future__ import annotations

from re import sub as re_sub

from src.backend.util import GO_RESERVED, escape_string, go_to_camel, go_to_pascal
from src.ir import (
    BOOL,
    BYTE,
    FLOAT,
    INT,
    RUNE,
    STRING,
    VOID,
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
    Function,
    FuncType,
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
    Truthy,
    TupleAssign,
    TupleLit,
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


def _needs_deref(arg_type: Type, elem_type: Type) -> bool:
    """Check if pointer arg needs dereference when appending to slice."""
    if not isinstance(arg_type, Pointer) or not isinstance(arg_type.target, StructRef):
        return False
    if isinstance(elem_type, StructRef) and arg_type.target.name == elem_type.name:
        return True
    if isinstance(elem_type, InterfaceRef) and arg_type.target.name == elem_type.name:
        return True
    return False


def _needs_byte_cast(arg_type: Type, elem_type: Type) -> bool:
    """Check if int arg needs cast to byte when appending to []byte."""
    return arg_type == INT and elem_type == BYTE


def _needs_string_cast(arg_type: Type, elem_type: Type) -> bool:
    """Check if rune arg needs cast to string when appending to []string or []any."""
    if arg_type != RUNE:
        return False
    if elem_type == STRING:
        return True
    # Rune appended to []interface{} also needs conversion (common pattern)
    if isinstance(elem_type, InterfaceRef) and elem_type.name == "any":
        return True
    return False


_NODE_METHODS: set[str] = {"ToSexp", "GetKind", "to_sexp", "get_kind"}


def _check_uses_node_methods_expr(expr: Expr | None, binding: str) -> bool:
    """Check if expr uses Node interface methods on the binding variable."""
    if expr is None:
        return False
    if isinstance(expr, MethodCall):
        if isinstance(expr.obj, Var) and expr.obj.name == binding:
            if expr.method in _NODE_METHODS:
                return True
        if _check_uses_node_methods_expr(expr.obj, binding):
            return True
        for arg in expr.args:
            if _check_uses_node_methods_expr(arg, binding):
                return True
    if isinstance(expr, BinaryOp):
        return _check_uses_node_methods_expr(expr.left, binding) or _check_uses_node_methods_expr(expr.right, binding)
    if isinstance(expr, UnaryOp):
        return _check_uses_node_methods_expr(expr.operand, binding)
    if isinstance(expr, Ternary):
        return _check_uses_node_methods_expr(expr.cond, binding) or _check_uses_node_methods_expr(expr.then_expr, binding) or _check_uses_node_methods_expr(expr.else_expr, binding)
    if isinstance(expr, (Cast, TypeAssert, IsNil, IsType)):
        return _check_uses_node_methods_expr(expr.expr, binding)
    if isinstance(expr, Index):
        return _check_uses_node_methods_expr(expr.obj, binding) or _check_uses_node_methods_expr(expr.index, binding)
    if isinstance(expr, FieldAccess):
        return _check_uses_node_methods_expr(expr.obj, binding)
    if isinstance(expr, Call):
        for arg in expr.args:
            if _check_uses_node_methods_expr(arg, binding):
                return True
    if isinstance(expr, StringConcat):
        for part in expr.parts:
            if _check_uses_node_methods_expr(part, binding):
                return True
    return False


def _check_uses_node_methods_stmt(stmt: Stmt, binding: str) -> bool:
    """Check if stmt uses Node interface methods on the binding variable."""
    if isinstance(stmt, (Assign, OpAssign)):
        return _check_uses_node_methods_expr(stmt.value, binding)
    if isinstance(stmt, ExprStmt):
        return _check_uses_node_methods_expr(stmt.expr, binding)
    if isinstance(stmt, Return) and stmt.value:
        return _check_uses_node_methods_expr(stmt.value, binding)
    if isinstance(stmt, If):
        if _check_uses_node_methods_expr(stmt.cond, binding):
            return True
        for s in stmt.then_body + stmt.else_body:
            if _check_uses_node_methods_stmt(s, binding):
                return True
    return False


def _scan_for_return_position(stmts: list[Stmt], var_name: str) -> int | None:
    """Scan statements for return position of a variable in a tuple literal."""
    for s in stmts:
        if isinstance(s, Return) and s.value and isinstance(s.value, TupleLit):
            for i, elem in enumerate(s.value.elements):
                if isinstance(elem, Var) and elem.name == var_name:
                    return i
        elif isinstance(s, If):
            pos = _scan_for_return_position(s.then_body, var_name)
            if pos is not None:
                return pos
            pos = _scan_for_return_position(s.else_body, var_name)
            if pos is not None:
                return pos
    return None


class GoBackend:
    """Emit Go code from IR Module."""

    def __init__(self) -> None:
        self.output: list[str] = []
        self.indent = 0
        self._receiver_name: str = ""  # Current method receiver name
        self._tuple_vars: dict[str, Tuple] = {}  # Track tuple-typed variables
        self._hoisted_in_try: set[str] = set()  # Variables hoisted from try blocks
        self._type_switch_binding_rename: dict[str, str] = {}  # Maps binding name to narrowed name
        self._named_returns: list[str] | None = None  # Named return param names (when needed)
        self._in_catch_body: bool = False  # Whether we're inside a TryCatch catch body
        self._current_return_type: Type = VOID  # Current function's return type

    def emit(self, module: Module) -> str:
        """Emit Go code from IR Module."""
        self.output = []
        self._emit_header(module)
        self._emit_constants(module.constants)
        for iface in module.interfaces:
            self._emit_interface_def(iface)
        for struct in module.structs:
            self._emit_struct(struct)
        for func in module.functions:
            if func.name in ("_repeat_str", "_sublist"):
                continue
            self._emit_function(func)
        return "\n".join(self.output)

    def _emit_constants(self, constants: list[Constant]) -> None:
        """Emit module-level constants."""
        if not constants:
            return
        # Separate constants into true constants (int/string/bool) and var constants (sets/maps)
        true_consts = [c for c in constants if not isinstance(c.typ, (Set, Map))]
        var_consts = [c for c in constants if isinstance(c.typ, (Set, Map))]
        if true_consts:
            self._line("const (")
            self.indent += 1
            for const in true_consts:
                name = go_to_pascal(const.name)
                value = self._emit_expr(const.value)
                self._line(f"{name} = {value}")
            self.indent -= 1
            self._line(")")
            self._line("")
        if var_consts:
            self._line("var (")
            self.indent += 1
            for const in var_consts:
                name = go_to_pascal(const.name)
                value = self._emit_expr(const.value)
                self._line(f"{name} = {value}")
            self.indent -= 1
            self._line(")")
            self._line("")

    def _emit_header(self, module: Module) -> None:
        """Emit package declaration and imports."""
        self._line(f"package {module.name}")
        self._line("")
        self._line("import (")
        self.indent += 1
        self._line('"fmt"')
        self._line('"reflect"')
        self._line('"strconv"')
        self._line('"strings"')
        self._line('"unicode"')
        self._line('"unicode/utf8"')
        self.indent -= 1
        self._line(")")
        self._line("")
        self._line("var _ = strings.Compare // ensure import is used")
        self._line("")
        # Emit string character classification helpers
        self._emit_string_helpers()

    def _emit_string_helpers(self) -> None:
        """Emit helper functions for Python string methods."""
        helpers = """
func _strIsAlnum(s string) bool {
	for _, r := range s {
		if !unicode.IsLetter(r) && !unicode.IsDigit(r) {
			return false
		}
	}
	return len(s) > 0
}

func _strIsAlpha(s string) bool {
	for _, r := range s {
		if !unicode.IsLetter(r) {
			return false
		}
	}
	return len(s) > 0
}

func _strIsDigit(s string) bool {
	for _, r := range s {
		if !unicode.IsDigit(r) {
			return false
		}
	}
	return len(s) > 0
}

func _strIsSpace(s string) bool {
	for _, r := range s {
		if !unicode.IsSpace(r) {
			return false
		}
	}
	return len(s) > 0
}

func _strIsUpper(s string) bool {
	for _, r := range s {
		if !unicode.IsUpper(r) {
			return false
		}
	}
	return len(s) > 0
}

func _strIsLower(s string) bool {
	for _, r := range s {
		if !unicode.IsLower(r) {
			return false
		}
	}
	return len(s) > 0
}

// _intPtr converts a sentinel int (-1 = nil) to *int
func _intPtr(val int) *int {
	if val == -1 {
		return nil
	}
	return &val
}

// Range generates a slice of integers similar to Python's range()
// Range(end) -> [0, 1, ..., end-1]
// Range(start, end) -> [start, start+1, ..., end-1]
// Range(start, end, step) -> [start, start+step, ..., last < end]
func Range(args ...int) []int {
	var start, end, step int
	switch len(args) {
	case 1:
		start, end, step = 0, args[0], 1
	case 2:
		start, end, step = args[0], args[1], 1
	case 3:
		start, end, step = args[0], args[1], args[2]
	default:
		return nil
	}
	if step == 0 {
		return nil
	}
	var result []int
	if step > 0 {
		for i := start; i < end; i += step {
			result = append(result, i)
		}
	} else {
		for i := start; i > end; i += step {
			result = append(result, i)
		}
	}
	return result
}

func _parseInt(s string, base int) int {
	n, _ := strconv.ParseInt(s, base, 64)
	return int(n)
}

// _mapGet returns the value for key from map m, or defaultVal if not found
func _mapGet[K comparable, V any](m map[K]V, key K, defaultVal V) V {
	if v, ok := m[key]; ok {
		return v
	}
	return defaultVal
}

// _mapHas returns true if key exists in map m
func _mapHas[K comparable, V any](m map[K]V, key K) bool {
	_, ok := m[key]
	return ok
}

// _isNilInterface checks if an interface value is nil.
// In Go, an interface is nil only when both type and value are nil.
// This handles the case where interface contains a typed nil pointer.
func _isNilInterfaceRef(i interface{}) bool {
	if i == nil {
		return true
	}
	v := reflect.ValueOf(i)
	return v.Kind() == reflect.Ptr && v.IsNil()
}

// _runeAt returns the character (as string) at rune index i in string s.
// Python s[i] on a string returns the i-th character, not byte.
func _runeAt(s string, i int) string {
	if i < 0 {
		return ""
	}
	for byteOffset, runeIdx := 0, 0; byteOffset < len(s); runeIdx++ {
		r, size := utf8.DecodeRuneInString(s[byteOffset:])
		if runeIdx == i {
			return string(r)
		}
		byteOffset += size
	}
	return ""
}

// _runeLen returns the number of runes (characters) in string s.
// Python len(s) on a string returns character count, not byte count.
func _runeLen(s string) int {
	return utf8.RuneCountInString(s)
}

// _Substring returns s[start:end] using rune (character) indices.
// Python s[start:end] uses character indices, not byte indices.
func _Substring(s string, start int, end int) string {
	if start < 0 {
		start = 0
	}
	byteStart, byteEnd := -1, len(s)
	runeIdx := 0
	for byteOffset := 0; byteOffset < len(s); {
		if runeIdx == start {
			byteStart = byteOffset
		}
		if runeIdx == end {
			byteEnd = byteOffset
			break
		}
		_, size := utf8.DecodeRuneInString(s[byteOffset:])
		byteOffset += size
		runeIdx++
	}
	if byteStart < 0 || byteStart >= byteEnd {
		return ""
	}
	return s[byteStart:byteEnd]
}
"""
        for line in helpers.strip().split("\n"):
            self._line_raw(line)
        self._line("")

    def _emit_interface_def(self, iface: InterfaceDef) -> None:
        """Emit interface definition."""
        self._line(f"type {iface.name} interface {{")
        self.indent += 1
        for method in iface.methods:
            params = ", ".join(self._type_to_go(p.typ) for p in method.params)
            ret = self._type_to_go(method.ret) if method.ret != VOID else ""
            if ret:
                self._line(f"{method.name}({params}) {ret}")
            else:
                self._line(f"{method.name}({params})")
        self.indent -= 1
        self._line("}")
        self._line("")

    def _emit_struct(self, struct: Struct) -> None:
        """Emit struct definition."""
        self._line(f"type {struct.name} struct {{")
        self.indent += 1
        # Emit embedded type for exception inheritance
        if struct.embedded_type:
            self._line(struct.embedded_type)
        for field in struct.fields:
            go_type = self._type_to_go(field.typ)
            go_name = go_to_pascal(field.name)
            self._line(f"{go_name} {go_type}")
        self.indent -= 1
        self._line("}")
        self._line("")
        # Emit Error() method for exceptions (Go error interface)
        if struct.is_exception:
            if not struct.embedded_type:
                # Root exception - emit Error() calling formatMessage()
                self._line(f"func (self *{struct.name}) Error() string {{")
                self.indent += 1
                self._line("return self.formatMessage()")
                self.indent -= 1
                self._line("}")
                self._line("")
            # Exceptions with embedded_type inherit Error() from parent
        # If struct implements Node interface, emit the interface methods
        if "Node" in struct.implements:
            # GetKind getter for the Kind field
            self._line(f"func (self *{struct.name}) GetKind() string {{ return self.Kind }}")
            self._line("")
        # Emit methods
        for method in struct.methods:
            self._emit_function(method)

    def _emit_function(self, func: Function) -> None:
        """Emit function or method definition."""
        # Reset tracking for new function scope
        self._tuple_vars = {}
        self._hoisted_in_try = set()
        self._current_return_type = func.ret
        self._named_returns = None
        self._in_catch_body = False
        params = ", ".join(f"{go_to_camel(p.name)} {self._type_to_go(p.typ)}" for p in func.params)
        # Check if we need named return parameters (for TryCatch with catch-body returns)
        needs_named_returns = func.needs_named_returns
        if needs_named_returns and func.ret != VOID:
            ret = self._named_return_type_to_go(func.ret)
        else:
            ret = self._return_type_to_go(func.ret) if func.ret != VOID else ""
        if func.receiver:
            # Use the receiver name from IR directly (converted to camelCase)
            recv_name = go_to_camel(func.receiver.name)
            self._receiver_name = recv_name
            recv_type = self._type_to_go(func.receiver.typ)
            if func.receiver.pointer:
                recv_type = "*" + recv_type.lstrip("*")
            self._line(
                f"func ({recv_name} {recv_type}) {go_to_pascal(func.name)}({params}) {ret} {{"
            )
        else:
            self._receiver_name = ""
            name = go_to_pascal(func.name)
            if ret:
                self._line(f"func {name}({params}) {ret} {{")
            else:
                self._line(f"func {name}({params}) {{")
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
            self._emit_stmt_Break(stmt)
        elif isinstance(stmt, Continue):
            self._emit_stmt_Continue(stmt)
        elif isinstance(stmt, Block):
            self._emit_stmt_Block(stmt)
        elif isinstance(stmt, TryCatch):
            self._emit_stmt_TryCatch(stmt)
        elif isinstance(stmt, Raise):
            self._emit_stmt_Raise(stmt)
        elif isinstance(stmt, SoftFail):
            self._emit_stmt_SoftFail(stmt)
        elif isinstance(stmt, TypeSwitch):
            self._emit_stmt_TypeSwitch(stmt)
        elif isinstance(stmt, Match):
            self._emit_stmt_Match(stmt)
        elif isinstance(stmt, NoOp):
            pass  # No output for NoOp
        else:
            self._line("// TODO: unknown statement")

    def _emit_stmt_VarDecl(self, stmt: VarDecl) -> None:
        go_type = self._type_to_go(stmt.typ)
        name = go_to_camel(stmt.name)
        # Track tuple vars for later tuple indexing
        if isinstance(stmt.typ, Tuple):
            self._tuple_vars[name] = stmt.typ
            # For function calls returning tuples, wrap in IIFE to convert
            # multiple return values to struct
            if stmt.value and isinstance(stmt.value, (Call, MethodCall)):
                call_expr = self._emit_expr(stmt.value)
                n = len(stmt.typ.elements)
                tmp_vars = ", ".join(f"_t{i}" for i in range(n))
                field_vals = ", ".join(f"_t{i}" for i in range(n))
                self._line(
                    f"var {name} {go_type} = func() {go_type} {{ {tmp_vars} := {call_expr}; return {go_type}{{{field_vals}}} }}()"
                )
                return
        if stmt.value:
            # nil assignments need explicit var type (Go's nil is untyped)
            if isinstance(stmt.value, NilLit):
                self._line(f"var {name} {go_type}")
                return
            val = self._emit_expr(stmt.value)
            # Use short declaration for simple types, explicit var for complex types
            if isinstance(stmt.typ, (Tuple, Slice, Map, Set)) and not isinstance(
                stmt.value, (SliceLit, MapLit, SetLit, MakeSlice, MakeMap)
            ):
                self._line(f"var {name} {go_type} = {val}")
            else:
                self._line(f"{name} := {val}")
        else:
            self._line(f"var {name} {go_type}")

    def _emit_stmt_Assign(self, stmt: Assign) -> None:
        target = self._emit_lvalue(stmt.target)
        if stmt.is_declaration:
            # Check if this var was hoisted - use = instead of :=
            is_hoisted = isinstance(stmt.target, VarLV) and stmt.target.name in self._hoisted_in_try
            # Check if there's a declaration type override
            decl_typ = stmt.decl_typ
            # nil assignments need explicit var type (Go's nil is untyped)
            if isinstance(stmt.value, NilLit):
                if is_hoisted:
                    # Variable was hoisted, just assign nil
                    self._line(f"{target} = nil")
                    return
                var_type = decl_typ if decl_typ is not None else stmt.value.typ
                if var_type:
                    go_type = self._type_to_go(var_type)
                    self._line(f"var {target} {go_type}")
                    return
            value = self._emit_expr(stmt.value)
            if is_hoisted:
                self._line(f"{target} = {value}")
            elif decl_typ:
                # Use explicit var declaration with override type
                go_type = self._type_to_go(decl_typ)
                self._line(f"var {target} {go_type} = {value}")
            else:
                self._line(f"{target} := {value}")
        else:
            value = self._emit_expr(stmt.value)
            self._line(f"{target} = {value}")

    def _emit_stmt_TupleAssign(self, stmt: TupleAssign) -> None:
        """Emit tuple unpacking: a, b := func()"""
        # Special case: a, b = slice.pop() - Go slices don't have pop()
        if isinstance(stmt.value, MethodCall) and stmt.value.method == "pop":
            self._emit_tuple_pop(stmt)
            return
        targets = []
        unused_indices = stmt.unused_indices
        for i, t in enumerate(stmt.targets):
            if i in unused_indices:
                targets.append("_")
            elif isinstance(t, VarLV):
                if t.name == "_":
                    targets.append("_")
                else:
                    targets.append(go_to_camel(t.name))
            else:
                targets.append(self._emit_lvalue(t))
        target_str = ", ".join(targets)
        value = self._emit_expr(stmt.value)
        is_decl = stmt.is_declaration
        new_targets = stmt.new_targets
        # Check if ANY target was hoisted - those use = instead of :=
        any_hoisted = any(
            isinstance(t, VarLV) and t.name in self._hoisted_in_try for t in stmt.targets
        )
        # Go's := handles mixed declarations - if ANY target is new (and not hoisted), use :=
        has_new_unhoisted = any(
            isinstance(t, VarLV) and t.name in new_targets and t.name not in self._hoisted_in_try
            for t in stmt.targets
        )
        if is_decl and not any_hoisted:
            self._line(f"{target_str} := {value}")
        elif has_new_unhoisted:
            # Mixed case: some new, some existing - Go's := handles this
            self._line(f"{target_str} := {value}")
        else:
            self._line(f"{target_str} = {value}")

    def _emit_tuple_pop(self, stmt: TupleAssign) -> None:
        """Emit tuple unpacking from slice.pop(): a, b = slice.pop()

        Go slices don't have pop(), so expand to:
            _entry := slice[len(slice)-1]
            slice = slice[:len(slice)-1]
            a, b = _entry.F0, _entry.F1
        """
        mc = stmt.value
        if not isinstance(mc, MethodCall):
            return
        obj = self._emit_expr(mc.obj)
        obj_lv = self._emit_lvalue_from_expr(mc.obj)
        # Emit: _entry := slice[len(slice)-1]
        self._line(f"_entry := {obj}[len({obj})-1]")
        # Emit: slice = slice[:len(slice)-1]
        self._line(f"{obj_lv} = {obj}[:len({obj})-1]")
        # Emit tuple field assignments
        targets = []
        for i, t in enumerate(stmt.targets):
            if isinstance(t, VarLV) and t.name == "_":
                targets.append("_")
            elif isinstance(t, VarLV):
                targets.append(go_to_camel(t.name))
            else:
                targets.append(self._emit_lvalue(t))
        if len(targets) == 2:
            self._line(f"{targets[0]}, {targets[1]} = _entry.F0, _entry.F1")
        else:
            for i, target in enumerate(targets):
                self._line(f"{target} = _entry.F{i}")

    def _emit_lvalue_from_expr(self, expr: Expr) -> str:
        """Convert an expression to its lvalue form for assignment."""
        if isinstance(expr, Var):
            if expr.name == self._receiver_name:
                return self._receiver_name
            return go_to_camel(expr.name)
        if isinstance(expr, FieldAccess):
            obj = self._emit_expr(expr.obj)
            return f"{obj}.{go_to_pascal(expr.field)}"
        return self._emit_expr(expr)

    def _emit_stmt_OpAssign(self, stmt: OpAssign) -> None:
        target = self._emit_lvalue(stmt.target)
        # Convert += 1 to ++ and -= 1 to --
        if isinstance(stmt.value, IntLit) and stmt.value.value == 1:
            if stmt.op == "+":
                self._line(f"{target}++")
                return
            if stmt.op == "-":
                self._line(f"{target}--")
                return
        value = self._emit_expr(stmt.value)
        self._line(f"{target} {stmt.op}= {value}")

    def _emit_stmt_ExprStmt(self, stmt: ExprStmt) -> None:
        # Special handling for append - needs to be an assignment in Go
        if isinstance(stmt.expr, MethodCall) and stmt.expr.method == "append" and stmt.expr.args:
            obj = self._emit_expr(stmt.expr.obj)
            arg = self._emit_expr(stmt.expr.args[0])
            arg_type = stmt.expr.args[0].typ
            recv_type = stmt.expr.receiver_type
            # Handle pointer-to-slice receiver
            if isinstance(recv_type, Pointer) and isinstance(recv_type.target, Slice):
                elem_type = recv_type.target.element
                if _needs_deref(arg_type, elem_type):
                    self._line(f"*{obj} = append(*{obj}, *{arg})")
                elif _needs_byte_cast(arg_type, elem_type):
                    self._line(f"*{obj} = append(*{obj}, byte({arg}))")
                elif _needs_string_cast(arg_type, elem_type):
                    self._line(f"*{obj} = append(*{obj}, string({arg}))")
                else:
                    self._line(f"*{obj} = append(*{obj}, {arg})")
            # Handle regular slice receiver
            elif isinstance(recv_type, Slice):
                elem_type = recv_type.element
                if _needs_deref(arg_type, elem_type):
                    self._line(f"{obj} = append({obj}, *{arg})")
                elif _needs_byte_cast(arg_type, elem_type):
                    self._line(f"{obj} = append({obj}, byte({arg}))")
                elif _needs_string_cast(arg_type, elem_type):
                    self._line(f"{obj} = append({obj}, string({arg}))")
                else:
                    self._line(f"{obj} = append({obj}, {arg})")
            else:
                self._line(f"{obj} = append({obj}, {arg})")
            return
        # Special handling for extend - needs to be an assignment in Go
        if isinstance(stmt.expr, MethodCall) and stmt.expr.method == "extend" and stmt.expr.args:
            obj = self._emit_expr(stmt.expr.obj)
            arg = self._emit_expr(stmt.expr.args[0])
            # Check if receiver is a pointer to slice - need to dereference
            if isinstance(stmt.expr.receiver_type, Pointer) and isinstance(
                stmt.expr.receiver_type.target, Slice
            ):
                self._line(f"*{obj} = append(*{obj}, {arg}...)")
            else:
                self._line(f"{obj} = append({obj}, {arg}...)")
            return
        # Special handling for pop() as statement - truncates the slice
        # Only handle if receiver is a slice type (not a struct with a Pop method)
        if isinstance(stmt.expr, MethodCall) and stmt.expr.method == "pop" and not stmt.expr.args:
            recv_type = stmt.expr.receiver_type
            # Check if receiver is a pointer to slice
            if isinstance(recv_type, Pointer) and isinstance(recv_type.target, Slice):
                obj = self._emit_expr(stmt.expr.obj)
                self._line(f"*{obj} = (*{obj})[:len(*{obj})-1]")
                return
            elif isinstance(recv_type, Slice):
                obj = self._emit_expr(stmt.expr.obj)
                self._line(f"{obj} = {obj}[:len({obj})-1]")
                return
            # For other types (like structs with Pop method), fall through to normal handling
        expr = self._emit_expr(stmt.expr)
        if expr:
            self._line(expr)

    def _emit_stmt_Return(self, stmt: Return) -> None:
        # When inside a catch body with named returns, assign to named returns instead of returning
        # (defer functions can't return values)
        if self._in_catch_body and self._named_returns:
            if stmt.value:
                if isinstance(stmt.value, TupleLit):
                    # Assign each element to corresponding named return
                    for i, elem in enumerate(stmt.value.elements):
                        if i < len(self._named_returns):
                            val = self._emit_expr(elem)
                            self._line(f"{self._named_returns[i]} = {val}")
                else:
                    # Single return value
                    val = self._emit_expr(stmt.value)
                    self._line(f"{self._named_returns[0]} = {val}")
            # Don't emit 'return' - let the defer finish naturally
            # The named returns will be used when the outer function returns
            return
        if stmt.value:
            # For TupleLit, emit as multiple return values, not a struct
            if isinstance(stmt.value, TupleLit):
                vals = ", ".join(self._emit_expr(e) for e in stmt.value.elements)
                self._line(f"return {vals}")
            # For Ternary, expand to idiomatic if-else return
            elif isinstance(stmt.value, Ternary):
                cond = self._emit_expr(stmt.value.cond)
                then_val = self._emit_expr(stmt.value.then_expr)
                else_val = self._emit_expr(stmt.value.else_expr)
                self._line(f"if {cond} {{")
                self.indent += 1
                self._line(f"return {then_val}")
                self.indent -= 1
                self._line("}")
                self._line(f"return {else_val}")
            else:
                val = self._emit_expr(stmt.value)
                # If function returns Optional (pointer) but value is a non-pointer type, add &
                ret_type = self._current_return_type
                val_type = stmt.value.typ
                if (
                    isinstance(ret_type, Optional)
                    and val_type
                    and not isinstance(val_type, (Optional, Pointer))
                    and not isinstance(stmt.value, NilLit)
                ):
                    val = f"&{val}"
                self._line(f"return {val}")
        else:
            self._line("return")

    def _emit_stmt_If(self, stmt: If) -> None:
        # Emit hoisted variable declarations before the if
        hoisted_vars = stmt.hoisted_vars
        for name, typ in hoisted_vars:
            type_str = self._type_to_go(typ) if typ else "interface{}"
            # If type is interface{} but function returns a tuple, try to infer
            # position-based type (only for tuple returns where vars are in specific positions)
            if type_str == "interface{}" and self._current_return_type:
                if isinstance(self._current_return_type, Tuple):
                    # For tuple returns, check if variable is returned in a known position
                    # Common pattern: return node, text -> text is second element (string)
                    ret_type = self._infer_tuple_element_type(name, stmt, self._current_return_type)
                    if ret_type:
                        type_str = self._type_to_go(ret_type)
                # Don't override interface{} with non-tuple return type - the var might not
                # be related to the return value at all
            go_name = go_to_camel(name)
            self._line(f"var {go_name} {type_str}")
            self._hoisted_in_try.add(name)

        cond = self._emit_expr(stmt.cond)
        self._line(f"if {cond} {{")
        self.indent += 1
        for s in stmt.then_body:
            self._emit_stmt(s)
        self.indent -= 1
        if stmt.else_body:
            # Check if else body is a single If (elif chain)
            if len(stmt.else_body) == 1 and isinstance(stmt.else_body[0], If):
                self._line_raw("} else ")
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
        """Emit if statement without leading newline (for else if chains)."""
        cond = self._emit_expr(stmt.cond)
        self.output[-1] += f"if {cond} {{"
        self.indent += 1
        for s in stmt.then_body:
            self._emit_stmt(s)
        self.indent -= 1
        if stmt.else_body:
            if len(stmt.else_body) == 1 and isinstance(stmt.else_body[0], If):
                self._line_raw("} else ")
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
        # Emit hoisted variable declarations before the loop
        hoisted_vars = stmt.hoisted_vars
        for name, typ in hoisted_vars:
            go_name = go_to_camel(name)
            if typ is not None:
                go_type = self._type_to_go(typ)
                self._line(f"var {go_name} {go_type}")
            else:
                self._line(f"var {go_name} interface{{}}")
            # Track hoisted variables to use = instead of := for subsequent assignments
            self._hoisted_in_try.add(name)
        cond = self._emit_expr(stmt.cond)
        self._line(f"for {cond} {{")
        self.indent += 1
        for s in stmt.body:
            self._emit_stmt(s)
        self.indent -= 1
        self._line("}")

    def _emit_stmt_ForRange(self, stmt: ForRange) -> None:
        # Emit hoisted variable declarations before the for loop
        hoisted_vars = stmt.hoisted_vars
        for name, typ in hoisted_vars:
            type_str = self._type_to_go(typ) if typ else "interface{}"
            go_name = go_to_camel(name)
            self._line(f"var {go_name} {type_str}")
            self._hoisted_in_try.add(name)
        iterable = self._emit_expr(stmt.iterable)
        idx = stmt.index if stmt.index else "_"
        val = stmt.value if stmt.value else "_"
        idx_go = go_to_camel(idx) if idx != "_" else "_"
        val_go = go_to_camel(val) if val != "_" else "_"
        if idx == "_" and val == "_":
            self._line(f"for range {iterable} {{")
        elif idx == "_":
            self._line(f"for _, {val_go} := range {iterable} {{")
        else:
            self._line(f"for {idx_go}, {val_go} := range {iterable} {{")
        self.indent += 1
        for s in stmt.body:
            self._emit_stmt(s)
        self.indent -= 1
        self._line("}")

    def _emit_stmt_ForClassic(self, stmt: ForClassic) -> None:
        init = self._emit_stmt_inline(stmt.init) if stmt.init else ""
        cond = self._emit_expr(stmt.cond) if stmt.cond else ""
        post = self._emit_stmt_inline(stmt.post) if stmt.post else ""
        self._line(f"for {init}; {cond}; {post} {{")
        self.indent += 1
        for s in stmt.body:
            self._emit_stmt(s)
        self.indent -= 1
        self._line("}")

    def _emit_stmt_inline(self, stmt: Stmt) -> str:
        """Emit statement as inline string (for for loop parts)."""
        if isinstance(stmt, VarDecl):
            name = go_to_camel(stmt.name)
            if stmt.value:
                val = self._emit_expr(stmt.value)
                return f"{name} := {val}"
            return f"var {name} {self._type_to_go(stmt.typ)}"
        if isinstance(stmt, Assign):
            target = self._emit_lvalue(stmt.target)
            return f"{target} = {self._emit_expr(stmt.value)}"
        if isinstance(stmt, OpAssign):
            target = self._emit_lvalue(stmt.target)
            # Emit i++ / i-- for idiomatic Go
            if isinstance(stmt.value, IntLit) and stmt.value.value == 1:
                if stmt.op == "+":
                    return f"{target}++"
                if stmt.op == "-":
                    return f"{target}--"
            return f"{target} {stmt.op}= {self._emit_expr(stmt.value)}"
        return ""

    def _emit_stmt_Break(self, stmt: Break) -> None:
        if stmt.label:
            self._line(f"break {stmt.label}")
        else:
            self._line("break")

    def _emit_stmt_Continue(self, stmt: Continue) -> None:
        if stmt.label:
            self._line(f"continue {stmt.label}")
        else:
            self._line("continue")

    def _emit_stmt_Block(self, stmt: Block) -> None:
        # Check if this block should emit without braces (for statement sequences)
        no_scope = stmt.no_scope
        if not no_scope:
            self._line("{")
            self.indent += 1
        for s in stmt.body:
            self._emit_stmt(s)
        if not no_scope:
            self.indent -= 1
            self._line("}")

    def _emit_stmt_TryCatch(self, stmt: TryCatch) -> None:
        # Emit hoisted variable declarations before the try/catch
        hoisted_vars = stmt.hoisted_vars
        for name, typ in hoisted_vars:
            type_str = self._type_to_go(typ) if typ else "interface{}"
            go_name = go_to_camel(name)
            self._line(f"var {go_name} {type_str}")
            self._hoisted_in_try.add(name)
        has_returns = stmt.has_returns
        has_catch_returns = stmt.has_catch_returns
        if has_returns:
            # When try/catch contains return statements, don't wrap in IIFE
            # Return statements will return from the enclosing function
            self._line("defer func() {")
            self.indent += 1
            if stmt.catch_var:
                self._line(f"if {stmt.catch_var} := recover(); {stmt.catch_var} != nil {{")
            else:
                self._line("if r := recover(); r != nil {")
            self.indent += 1
            # Track that we're in catch body (for return transformation)
            if has_catch_returns and self._named_returns:
                self._in_catch_body = True
            for s in stmt.catch_body:
                self._emit_stmt(s)
            self._in_catch_body = False
            if stmt.reraise:
                self._line("panic(r)")
            self.indent -= 1
            self._line("}")
            self.indent -= 1
            self._line("}()")
            for s in stmt.body:
                self._emit_stmt(s)
        else:
            # Standard IIFE pattern when no returns
            self._line("func() {")
            self.indent += 1
            self._line("defer func() {")
            self.indent += 1
            if stmt.catch_var:
                self._line(f"if {stmt.catch_var} := recover(); {stmt.catch_var} != nil {{")
            else:
                self._line("if r := recover(); r != nil {")
            self.indent += 1
            for s in stmt.catch_body:
                self._emit_stmt(s)
            if stmt.reraise:
                self._line("panic(r)")
            self.indent -= 1
            self._line("}")
            self.indent -= 1
            self._line("}()")
            for s in stmt.body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}()")
        # Keep hoisted vars tracked - they remain in scope for the rest of the function

    def _emit_stmt_Raise(self, stmt: Raise) -> None:
        # Re-raise caught exception
        if stmt.reraise_var:
            self._line(f"panic({stmt.reraise_var})")
            return
        msg = self._emit_expr(stmt.message)
        pos = self._emit_expr(stmt.pos)
        if stmt.error_type == "ParseError":
            self._line(f"panic(NewParseError({msg}, {pos}, 0))")
        elif stmt.error_type == "MatchedPairError":
            self._line(f"panic(NewMatchedPairError({msg}, {pos}, 0))")
        else:
            # Fallback for other error types
            if pos != "0":
                self._line(f'panic(fmt.Sprintf("%s at position %d", {msg}, {pos}))')
            else:
                self._line(f"panic({msg})")

    def _emit_stmt_SoftFail(self, stmt: SoftFail) -> None:
        self._line("return nil")

    def _uses_node_methods(self, stmts: list[Stmt], binding: str) -> bool:
        """Check if binding variable is used with Node interface methods in statements."""
        for stmt in stmts:
            if _check_uses_node_methods_stmt(stmt, binding):
                return True
        return False

    def _emit_stmt_TypeSwitch(self, stmt: TypeSwitch) -> None:
        # Emit hoisted variable declarations before the switch
        hoisted_vars = stmt.hoisted_vars
        for name, typ in hoisted_vars:
            type_str = self._type_to_go(typ) if typ else "interface{}"
            go_name = go_to_camel(name)
            self._line(f"var {go_name} {type_str}")
            self._hoisted_in_try.add(name)
        # Special case: single case with default that's just a break.
        # Emit as type assertion if/else to avoid break-in-switch bug
        # (break inside switch default only exits switch, not enclosing loop).
        if (
            len(stmt.cases) == 1
            and len(stmt.default) == 1
            and isinstance(stmt.default[0], Break)
            and stmt.default[0].label is None
        ):
            self._emit_type_switch_as_assertion(stmt)
            return
        expr = self._emit_expr(stmt.expr)
        binding_unused = stmt.binding_unused
        binding_reassigned = stmt.binding_reassigned
        # If binding is unused or reassigned, emit without binding to avoid Go errors
        if binding_unused or binding_reassigned:
            self._line(f"switch {expr}.(type) {{")
        else:
            binding = go_to_camel(stmt.binding)
            self._line(f"switch {binding} := {expr}.(type) {{")
        for case in stmt.cases:
            go_type = self._type_to_go(case.typ)
            self._line(f"case {go_type}:")
            self.indent += 1
            # Save hoisted vars state - case bodies have their own scope
            saved_hoisted = set(self._hoisted_in_try)
            # When binding_reassigned, emit explicit type assertion with a different name
            # so reads use the narrowed type but writes go to the outer variable
            if binding_reassigned and not binding_unused:
                binding = go_to_camel(stmt.binding)
                # Create narrowed name by capitalizing first letter after binding
                narrowed_name = f"{binding}{self._extract_type_suffix(go_type)}"
                self._line(f"{narrowed_name} := {expr}.({go_type})")
                # Set up renaming context for this case body
                self._type_switch_binding_rename[stmt.binding] = narrowed_name
                for s in case.body:
                    self._emit_stmt(s)
                # Clear renaming context
                self._type_switch_binding_rename.pop(stmt.binding)
            else:
                for s in case.body:
                    self._emit_stmt(s)
            # Restore hoisted vars state - variables hoisted inside case don't leak out
            self._hoisted_in_try = saved_hoisted
            self.indent -= 1
        if stmt.default:
            self._line("default:")
            self.indent += 1
            # Save hoisted vars state - default case has its own scope
            saved_hoisted = set(self._hoisted_in_try)
            # In default case, binding has type interface{} - assert back to original type
            needs_node_assertion = False
            if not binding_unused and not binding_reassigned:
                binding = go_to_camel(stmt.binding)
                expr_typ = stmt.expr.typ
                if expr_typ:
                    type_str = self._type_to_go(expr_typ)
                    if type_str not in ("interface{}", "any"):
                        # Use = not := since binding is already declared by the switch
                        self._line(f"{binding} = {binding}.({type_str})")
                    elif self._uses_node_methods(stmt.default, stmt.binding):
                        # Need to assert to Node, but must use a new scope for shadowing
                        needs_node_assertion = True
            if needs_node_assertion:
                # Wrap in block to allow := shadowing
                binding = go_to_camel(stmt.binding)
                self._line("{")
                self.indent += 1
                self._line(f"{binding} := {binding}.(Node)")
                for s in stmt.default:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("}")
            else:
                for s in stmt.default:
                    self._emit_stmt(s)
            # Restore hoisted vars state
            self._hoisted_in_try = saved_hoisted
            self.indent -= 1
        self._line("}")

    def _emit_type_switch_as_assertion(self, stmt: TypeSwitch) -> None:
        """Emit a single-case TypeSwitch as if/else with type assertion.
        Used when default is just a break, to avoid break-in-switch bug."""
        case = stmt.cases[0]
        go_type = self._type_to_go(case.typ)
        expr = self._emit_expr(stmt.expr)
        binding = go_to_camel(stmt.binding)
        # Use a different binding name to avoid shadowing issues when the body
        # reassigns the original variable. Add a type suffix.
        narrowed_binding = binding + self._extract_type_suffix(go_type)
        self._line(f"if {narrowed_binding}, ok := {expr}.({go_type}); ok {{")
        self.indent += 1
        # Set up renaming context so references to binding use narrowed_binding
        self._type_switch_binding_rename[stmt.binding] = narrowed_binding
        for s in case.body:
            self._emit_stmt(s)
        self._type_switch_binding_rename.pop(stmt.binding)
        self.indent -= 1
        self._line("} else {")
        self.indent += 1
        for s in stmt.default:
            self._emit_stmt(s)
        self.indent -= 1
        self._line("}")

    def _extract_type_suffix(self, go_type: str) -> str:
        """Extract a suffix from a Go type for naming, e.g., '*ArithVar' -> 'Var'."""
        # Remove pointer prefix
        name = go_type.lstrip("*")
        # For types like 'ArithVar', extract 'Var' (after common prefixes)
        for prefix in ("Arith", "Cond", ""):
            if name.startswith(prefix) and len(name) > len(prefix):
                return name[len(prefix) :]
        return name

    def _emit_stmt_Match(self, stmt: Match) -> None:
        # Emit hoisted variable declarations before the switch
        hoisted_vars = stmt.hoisted_vars
        for name, typ in hoisted_vars:
            type_str = self._type_to_go(typ) if typ else "interface{}"
            go_name = go_to_camel(name)
            self._line(f"var {go_name} {type_str}")
            self._hoisted_in_try.add(name)
        expr = self._emit_expr(stmt.expr)
        self._line(f"switch {expr} {{")
        for case in stmt.cases:
            patterns = ", ".join(self._emit_expr(p) for p in case.patterns)
            self._line(f"case {patterns}:")
            self.indent += 1
            # Save hoisted vars state - case bodies have their own scope
            saved_hoisted = set(self._hoisted_in_try)
            for s in case.body:
                self._emit_stmt(s)
            # Restore hoisted vars state
            self._hoisted_in_try = saved_hoisted
            self.indent -= 1
        if stmt.default:
            self._line("default:")
            self.indent += 1
            # Save hoisted vars state
            saved_hoisted = set(self._hoisted_in_try)
            for s in stmt.default:
                self._emit_stmt(s)
            # Restore hoisted vars state
            self._hoisted_in_try = saved_hoisted
            self.indent -= 1
        self._line("}")

    # ============================================================
    # EXPRESSION EMISSION
    # ============================================================

    def _emit_expr(self, expr: Expr) -> str:
        """Emit an expression and return Go code string."""
        if isinstance(expr, IntLit):
            return self._emit_expr_IntLit(expr)
        if isinstance(expr, FloatLit):
            return self._emit_expr_FloatLit(expr)
        if isinstance(expr, StringLit):
            return self._emit_expr_StringLit(expr)
        if isinstance(expr, BoolLit):
            return self._emit_expr_BoolLit(expr)
        if isinstance(expr, NilLit):
            return self._emit_expr_NilLit(expr)
        if isinstance(expr, Var):
            return self._emit_expr_Var(expr)
        if isinstance(expr, FieldAccess):
            return self._emit_expr_FieldAccess(expr)
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
        return "/* TODO: unknown expression */"

    def _emit_expr_IntLit(self, expr: IntLit) -> str:
        return str(expr.value)

    def _emit_expr_FloatLit(self, expr: FloatLit) -> str:
        return str(expr.value)

    def _emit_expr_StringLit(self, expr: StringLit) -> str:
        return f'"{escape_string(expr.value)}"'

    def _emit_expr_BoolLit(self, expr: BoolLit) -> str:
        return "true" if expr.value else "false"

    def _emit_expr_NilLit(self, expr: NilLit) -> str:
        return "nil"

    def _emit_expr_Var(self, expr: Var) -> str:
        if expr.name == "self":
            return self._receiver_name if self._receiver_name else "self"
        # Check for type switch binding rename (reads use narrowed name)
        if expr.name in self._type_switch_binding_rename:
            return self._type_switch_binding_rename[expr.name]
        return go_to_camel(expr.name)

    def _emit_expr_FieldAccess(self, expr: FieldAccess) -> str:
        obj = self._emit_expr(expr.obj)
        field = go_to_pascal(expr.field)
        # Interface fields must be accessed via getter methods
        obj_type = expr.obj.typ
        is_node_type = (isinstance(obj_type, InterfaceRef) and obj_type.name == "Node") or (
            isinstance(obj_type, StructRef) and obj_type.name == "Node"
        )
        if is_node_type and expr.field == "kind":
            return f"{obj}.GetKind()"
        return f"{obj}.{field}"

    def _emit_expr_Index(self, expr: Index) -> str:
        obj = self._emit_expr(expr.obj)
        idx = self._emit_expr(expr.index)
        # Handle tuple indexing - use field access for tuple types
        if isinstance(expr.index, IntLit):
            # Check if indexing into a known tuple variable
            if isinstance(expr.obj, Var):
                var_name = go_to_camel(expr.obj.name)
                if var_name in self._tuple_vars:
                    return f"{obj}.F{expr.index.value}"
            # Check if indexing into a tuple type (struct with F0, F1, etc.)
            if isinstance(expr.obj.typ, Tuple):
                return f"{obj}.F{expr.index.value}"
        obj_type = expr.obj.typ
        # String indexing: use _runeAt when result is used as character/string,
        # but keep byte indexing when result is used as byte/int (e.g., for ord())
        if obj_type == STRING:
            # If result type is BYTE or expr is being cast to int, use byte indexing
            result_type = expr.typ
            if result_type == BYTE or result_type == INT:
                # Byte-based indexing for byte operations
                return f"{obj}[{idx}]"
            # Character-based indexing for string operations
            return f"_runeAt({obj}, {idx})"
        return f"{obj}[{idx}]"

    def _emit_expr_SliceExpr(self, expr: SliceExpr) -> str:
        obj = self._emit_expr(expr.obj)
        obj_type = expr.obj.typ
        # Use rune-based slicing for strings (Python s[a:b] uses character indices)
        if obj_type == STRING:
            low = self._emit_expr(expr.low) if expr.low else "0"
            high = self._emit_expr(expr.high) if expr.high else f"_runeLen({obj})"
            return f"_Substring({obj}, {low}, {high})"
        low = self._emit_expr(expr.low) if expr.low else ""
        high = self._emit_expr(expr.high) if expr.high else ""
        return f"{obj}[{low}:{high}]"

    def _emit_expr_SliceConvert(self, expr: "SliceConvert") -> str:
        """Emit slice covariant conversion as IIFE with explicit loop."""
        source = self._emit_expr(expr.source)
        target_elem = self._type_to_go(expr.target_element_type)
        # func() []T { r := make([]T, len(src)); for i, v := range src { r[i] = v }; return r }()
        return f"func() []{target_elem} {{ _r := make([]{target_elem}, len({source})); for _i, _v := range {source} {{ _r[_i] = _v }}; return _r }}()"

    def _emit_expr_Call(self, expr: Call) -> str:
        # _repeat_str(s, n) → strings.Repeat(s, n)
        if expr.func == "_repeat_str" and len(expr.args) == 2:
            s = self._emit_expr(expr.args[0])
            n = self._emit_expr(expr.args[1])
            return f"strings.Repeat({s}, {n})"
        # _sublist(lst, a, b) → lst[a:b]
        if expr.func == "_sublist" and len(expr.args) == 3:
            lst = self._emit_expr(expr.args[0])
            start = self._emit_expr(expr.args[1])
            end = self._emit_expr(expr.args[2])
            return f"{lst}[{start}:{end}]"
        # Go builtins and our helpers stay as-is
        if expr.func in (
            "append",
            "cap",
            "close",
            "copy",
            "delete",
            "panic",
            "recover",
            "print",
            "println",
            "_intPtr",
        ):
            func = expr.func
        # Known function parameter names that are called as functions - keep lowercase
        elif expr.func in ("parsefn",):
            func = expr.func
        else:
            func = go_to_pascal(expr.func)
        args = ", ".join(self._emit_expr(a) for a in expr.args)
        return f"{func}({args})"

    def _emit_expr_MethodCall(self, expr: MethodCall) -> str:
        obj = self._emit_expr(expr.obj)
        # Wrap pointer struct literals in parentheses for method calls
        # &StructName{...}.Method() needs to be (&StructName{...}).Method()
        if isinstance(expr.obj, StructLit) and isinstance(expr.obj.typ, Pointer):
            obj = f"({obj})"
        method = expr.method  # Keep original for special cases
        # Handle Python string.join() -> strings.Join(seq, sep)
        if method == "join" and expr.args:
            seq = self._emit_expr(expr.args[0])
            return f"strings.Join({seq}, {obj})"
        # Handle Python list methods specially - only for slice types
        if isinstance(expr.receiver_type, Slice):
            if method == "append" and expr.args:
                arg = self._emit_expr(expr.args[0])
                # If appending pointer to slice of values/interfaces, dereference
                arg_type = expr.args[0].typ
                elem_type = expr.receiver_type.element
                needs_deref = False
                if isinstance(arg_type, Pointer) and isinstance(arg_type.target, StructRef):
                    # Check if element is StructRef with same name
                    if isinstance(elem_type, StructRef) and arg_type.target.name == elem_type.name:
                        needs_deref = True
                    # Or element is Interface with same name (Node interface)
                    elif (
                        isinstance(elem_type, InterfaceRef)
                        and arg_type.target.name == elem_type.name
                    ):
                        needs_deref = True
                if needs_deref:
                    return f"append({obj}, *{arg})"
                return f"append({obj}, {arg})"
            if method == "extend" and expr.args:
                # list.extend(other) -> append(list, other...)
                arg = self._emit_expr(expr.args[0])
                return f"append({obj}, {arg}...)"
            if method == "pop" and not expr.args:
                return f"{obj}[len({obj})-1]"
            if method == "copy":
                # Slice copy: append([]T{}, slice...)
                return f"append({obj}[:0:0], {obj}...)"
        # Handle Python string methods that map to strings package
        if method == "startswith" and expr.args:
            # Handle tuple argument: s.startswith((" ", "\n")) -> HasPrefix(s," ")||HasPrefix(s,"\n")
            arg_node = expr.args[0]
            if isinstance(arg_node, TupleLit):
                parts = [
                    f"strings.HasPrefix({obj}, {self._emit_expr(e)})" for e in arg_node.elements
                ]
                return " || ".join(parts)
            arg = self._emit_expr(arg_node)
            # Handle position argument: s.startswith(prefix, pos) -> strings.HasPrefix(s[pos:], prefix)
            if len(expr.args) >= 2:
                pos = self._emit_expr(expr.args[1])
                return f"strings.HasPrefix({obj}[{pos}:], {arg})"
            return f"strings.HasPrefix({obj}, {arg})"
        if method == "endswith" and expr.args:
            # Handle tuple argument: s.endswith((" ", "\n")) -> HasSuffix(s," ")||HasSuffix(s,"\n")
            arg_node = expr.args[0]
            if isinstance(arg_node, TupleLit):
                parts = [
                    f"strings.HasSuffix({obj}, {self._emit_expr(e)})" for e in arg_node.elements
                ]
                return " || ".join(parts)
            arg = self._emit_expr(arg_node)
            return f"strings.HasSuffix({obj}, {arg})"
        if method == "replace" and len(expr.args) >= 2:
            old = self._emit_expr(expr.args[0])
            new = self._emit_expr(expr.args[1])
            # Python's replace replaces all occurrences by default
            return f"strings.ReplaceAll({obj}, {old}, {new})"
        if method == "lower":
            return f"strings.ToLower({obj})"
        if method == "upper":
            return f"strings.ToUpper({obj})"
        if method == "strip":
            return f"strings.TrimSpace({obj})"
        if method == "lstrip":
            if expr.args:
                arg = self._emit_expr(expr.args[0])
                return f"strings.TrimLeft({obj}, {arg})"
            return f'strings.TrimLeft({obj}, " \\t\\n\\r")'
        if method == "rstrip":
            if expr.args:
                arg = self._emit_expr(expr.args[0])
                return f"strings.TrimRight({obj}, {arg})"
            return f'strings.TrimRight({obj}, " \\t\\n\\r")'
        if method == "split":
            if expr.args:
                arg = self._emit_expr(expr.args[0])
                return f"strings.Split({obj}, {arg})"
            return f"strings.Fields({obj})"
        if method == "count" and expr.args:
            arg = self._emit_expr(expr.args[0])
            return f"strings.Count({obj}, {arg})"
        if method == "find" and expr.args:
            arg = self._emit_expr(expr.args[0])
            return f"strings.Index({obj}, {arg})"
        if method == "rfind" and expr.args:
            arg = self._emit_expr(expr.args[0])
            return f"strings.LastIndex({obj}, {arg})"
        # Handle dict.get(key, default) -> _mapGet(dict, key, default) or direct index
        if method == "get" and isinstance(expr.receiver_type, Map) and len(expr.args) >= 1:
            key = self._emit_expr(expr.args[0])
            if len(expr.args) >= 2:
                default = self._emit_expr(expr.args[1])
                return f"_mapGet({obj}, {key}, {default})"
            return f"{obj}[{key}]"
        method = go_to_pascal(method)
        args = ", ".join(self._emit_expr(a) for a in expr.args)
        return f"{obj}.{method}({args})"

    def _emit_expr_StaticCall(self, expr: StaticCall) -> str:
        on_type = self._type_to_go(expr.on_type)
        method = go_to_pascal(expr.method)
        args = ", ".join(self._emit_expr(a) for a in expr.args)
        return f"{on_type}.{method}({args})"

    def _emit_expr_BinaryOp(self, expr: BinaryOp) -> str:
        # Handle single-char string comparisons with runes
        # In Go, for-range over string yields runes, so "'" must become '\''
        if expr.op in ("==", "!="):
            left_is_rune = isinstance(expr.left, Var) and expr.left.typ == RUNE
            right_is_rune = isinstance(expr.right, Var) and expr.right.typ == RUNE
            left_str = self._emit_expr(expr.left)
            right_str = self._emit_expr(expr.right)
            if left_is_rune and isinstance(expr.right, StringLit) and len(expr.right.value) == 1:
                right_str = self._emit_rune_literal(expr.right.value)
            elif right_is_rune and isinstance(expr.left, StringLit) and len(expr.left.value) == 1:
                left_str = self._emit_rune_literal(expr.left.value)
            return f"{left_str} {expr.op} {right_str}"
        # Handle comparisons with optional (pointer) types - dereference the pointer
        # Pattern: x > 0 where x is *int needs to become *x > 0
        if expr.op in ("<", ">", "<=", ">="):
            left_type = expr.left.typ
            right_type = expr.right.typ
            left_str = self._emit_expr(expr.left)
            right_str = self._emit_expr(expr.right)
            # Dereference left if it's a pointer/optional to a primitive
            left_inner = left_type.target if isinstance(left_type, Pointer) else (left_type.inner if isinstance(left_type, Optional) else None)
            if left_inner in (INT, FLOAT):
                left_str = f"*{left_str}"
            # Dereference right if it's a pointer/optional to a primitive
            right_inner = right_type.target if isinstance(right_type, Pointer) else (right_type.inner if isinstance(right_type, Optional) else None)
            if right_inner in (INT, FLOAT):
                right_str = f"*{right_str}"
            return f"{left_str} {expr.op} {right_str}"
        left = self._emit_expr(expr.left)
        right = self._emit_expr(expr.right)
        # Handle 'in' and 'not in' operators
        if expr.op == "in":
            right_type = expr.right.typ
            if isinstance(right_type, (Set, Map)):
                return f"_mapHas({right}, {left})"
            return f"strings.Contains({right}, {left})"
        if expr.op == "not in":
            right_type = expr.right.typ
            if isinstance(right_type, (Set, Map)):
                return f"!_mapHas({right}, {left})"
            return f"!strings.Contains({right}, {left})"
        # Handle operator precedence: && binds tighter than ||
        # So a || expression nested inside && needs parentheses
        if expr.op == "&&":
            if isinstance(expr.left, BinaryOp) and expr.left.op == "||":
                left = f"({left})"
            if isinstance(expr.right, BinaryOp) and expr.right.op == "||":
                right = f"({right})"
        # Don't wrap comparison, logical, or simple arithmetic in parens
        # Go handles precedence well and parens around conditions look unidiomatic
        if expr.op in ("&&", "||", "==", "!=", "<", ">", "<=", ">=", "+", "-", "*"):
            return f"{left} {expr.op} {right}"
        return f"({left} {expr.op} {right})"

    def _emit_rune_literal(self, char: str) -> str:
        """Emit a single character as a Go rune literal."""
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
        # Control characters and special bytes
        if ord(char) < 32 or ord(char) > 126:
            return f"'\\x{ord(char):02x}'"
        return f"'{char}'"

    def _emit_expr_UnaryOp(self, expr: UnaryOp) -> str:
        # Map Python's bitwise NOT (~) to Go's XOR (^)
        op = "^" if expr.op == "~" else expr.op
        # Handle negated endswith/startswith with tuple: apply De Morgan's law
        # not x.endswith((" ", "\n")) -> !HasSuffix(x," ") && !HasSuffix(x,"\n")
        if op == "!" and isinstance(expr.operand, MethodCall):
            method = expr.operand.method
            if method in ("endswith", "startswith") and expr.operand.args:
                arg_node = expr.operand.args[0]
                if isinstance(arg_node, TupleLit):
                    obj = self._emit_expr(expr.operand.obj)
                    func = "strings.HasSuffix" if method == "endswith" else "strings.HasPrefix"
                    parts = [f"!{func}({obj}, {self._emit_expr(e)})" for e in arg_node.elements]
                    return " && ".join(parts)
        # Simplify negated comparisons to avoid double negatives
        if op == "!" and isinstance(expr.operand, BinaryOp):
            inner = expr.operand
            # !(x != "") -> x == ""
            if inner.op == "!=" and isinstance(inner.right, StringLit) and inner.right.value == "":
                return f'{self._emit_expr(inner.left)} == ""'
            # !(len(x) > 0) -> len(x) == 0
            if (
                inner.op == ">"
                and isinstance(inner.left, Len)
                and isinstance(inner.right, IntLit)
                and inner.right.value == 0
            ):
                return f"len({self._emit_expr(inner.left.expr)}) == 0"
            # !((x & Y) != 0) -> (x & Y) == 0
            if inner.op == "!=" and isinstance(inner.right, IntLit) and inner.right.value == 0:
                return f"({self._emit_expr(inner.left)}) == 0"
        # Remove double negation: !!x -> x
        if op == "!" and isinstance(expr.operand, UnaryOp) and expr.operand.op == "!":
            return self._emit_expr(expr.operand.operand)
        # Remove double negation with IsNil: !(!_isNilInterfaceRef(x)) -> _isNilInterfaceRef(x)
        if op == "!" and isinstance(expr.operand, IsNil) and expr.operand.negated:
            inner = self._emit_expr(expr.operand.expr)
            expr_type = expr.operand.expr.typ
            if isinstance(expr_type, InterfaceRef):
                return f"_isNilInterfaceRef({inner})"
            return f"{inner} == nil"
        operand = self._emit_expr(expr.operand)
        # Wrap complex operands in parens for ! operator
        if op == "!" and isinstance(expr.operand, (BinaryOp, UnaryOp, IsNil)):
            return f"{op}({operand})"
        return f"{op}{operand}"

    def _emit_expr_Ternary(self, expr: Ternary) -> str:
        # Go doesn't have ternary, emit as IIFE
        cond = self._emit_expr(expr.cond)
        then_expr = self._emit_expr(expr.then_expr)
        else_expr = self._emit_expr(expr.else_expr)
        # When ternary type is any but both branches have same concrete type, use that
        result_type = expr.typ
        if isinstance(result_type, InterfaceRef) and result_type.name == "any":
            then_type = expr.then_expr.typ
            else_type = expr.else_expr.typ
            if then_type == else_type:
                result_type = then_type
        go_type = self._type_to_go(result_type)
        return f"func() {go_type} {{ if {cond} {{ return {then_expr} }} else {{ return {else_expr} }} }}()"

    def _emit_expr_Cast(self, expr: Cast) -> str:
        inner = self._emit_expr(expr.expr)
        to_type = self._type_to_go(expr.to_type)
        # Skip redundant string() wrapper around _runeAt (which already returns string)
        if to_type == "string" and isinstance(expr.expr, Index):
            obj_type = expr.expr.obj.typ
            if obj_type == STRING:
                # _runeAt already returns string, no wrapper needed
                return inner
        return f"{to_type}({inner})"

    def _emit_expr_TypeAssert(self, expr: TypeAssert) -> str:
        inner = self._emit_expr(expr.expr)
        # In Go, you can only type-assert FROM an interface, not from a concrete type
        # If inner is a concrete struct pointer and we're asserting TO an interface,
        # skip the assertion (Go implicitly converts concrete types to interfaces)
        inner_type = expr.expr.typ
        is_concrete = isinstance(inner_type, Pointer) and isinstance(inner_type.target, StructRef)
        asserting_to_interface = isinstance(expr.asserted, InterfaceRef)
        if is_concrete and asserting_to_interface:
            # Concrete struct pointer to interface - no assertion needed
            return inner
        asserted = self._type_to_go(expr.asserted)
        return f"{inner}.({asserted})"

    def _emit_expr_IsType(self, expr: IsType) -> str:
        inner = self._emit_expr(expr.expr)
        tested = self._type_to_go(expr.tested_type)
        return f"func() bool {{ _, ok := {inner}.({tested}); return ok }}()"

    def _emit_expr_IsNil(self, expr: IsNil) -> str:
        inner = self._emit_expr(expr.expr)
        # Check if the expression type is an interface type
        # In Go, interface nil check requires reflection when interface might
        # contain a typed nil pointer (e.g., var x SomeInterface = (*Impl)(nil))
        expr_type = expr.expr.typ
        is_interface = isinstance(expr_type, InterfaceRef)
        if is_interface:
            # Use helper function that handles typed nil pointers
            if expr.negated:
                return f"!_isNilInterfaceRef({inner})"
            return f"_isNilInterfaceRef({inner})"
        if expr.negated:
            return f"{inner} != nil"
        return f"{inner} == nil"

    def _emit_expr_Truthy(self, expr: Truthy) -> str:
        inner = self._emit_expr(expr.expr)
        inner_type = expr.expr.typ
        if inner_type == STRING:
            return f"(len({inner}) > 0)"
        if inner_type == INT:
            # Wrap binary ops in parens for correct precedence with !=
            if isinstance(expr.expr, BinaryOp):
                return f"(({inner}) != 0)"
            return f"({inner} != 0)"
        if isinstance(inner_type, (Slice, Map, Set)):
            return f"(len({inner}) > 0)"
        if isinstance(inner_type, Optional) and isinstance(inner_type.inner, (Slice, Map, Set)):
            return f"(len({inner}) > 0)"
        return f"({inner} != nil)"

    def _emit_expr_CharClassify(self, expr: CharClassify) -> str:
        char = self._emit_expr(expr.char)
        char_type = expr.char.typ
        is_rune = isinstance(char_type, Primitive) and char_type.kind == "rune"
        unicode_map = {
            "digit": "IsDigit",
            "alpha": "IsLetter",
            "alnum": ("IsLetter", "IsDigit"),  # needs both
            "space": "IsSpace",
            "upper": "IsUpper",
            "lower": "IsLower",
        }
        helper_map = {
            "digit": "_strIsDigit",
            "alpha": "_strIsAlpha",
            "alnum": "_strIsAlnum",
            "space": "_strIsSpace",
            "upper": "_strIsUpper",
            "lower": "_strIsLower",
        }
        kind = expr.kind
        if is_rune:
            if kind == "alnum":
                return f"(unicode.IsLetter({char}) || unicode.IsDigit({char}))"
            return f"unicode.{unicode_map[kind]}({char})"
        # String: use helper that iterates
        return f"{helper_map[kind]}({char})"

    def _emit_expr_Len(self, expr: Len) -> str:
        inner = self._emit_expr(expr.expr)
        # Use rune-based length for strings (Python len() counts characters, not bytes)
        inner_type = expr.expr.typ
        if inner_type == STRING:
            return f"_runeLen({inner})"
        return f"len({inner})"

    def _emit_expr_MakeSlice(self, expr: MakeSlice) -> str:
        elem_type = self._type_to_go(expr.element_type)
        if expr.length and expr.capacity:
            length = self._emit_expr(expr.length)
            cap = self._emit_expr(expr.capacity)
            return f"make([]{elem_type}, {length}, {cap})"
        if expr.length:
            length = self._emit_expr(expr.length)
            return f"make([]{elem_type}, {length})"
        return f"make([]{elem_type}, 0)"

    def _emit_expr_MakeMap(self, expr: MakeMap) -> str:
        key_type = self._type_to_go(expr.key_type)
        val_type = self._type_to_go(expr.value_type)
        return f"make(map[{key_type}]{val_type})"

    def _emit_expr_SliceLit(self, expr: SliceLit) -> str:
        go_elem = self._type_to_go(expr.element_type)
        elements = ", ".join(self._emit_expr(e) for e in expr.elements)
        return f"[]{go_elem}{{{elements}}}"

    def _emit_expr_MapLit(self, expr: MapLit) -> str:
        key_type = self._type_to_go(expr.key_type)
        val_type = self._type_to_go(expr.value_type)
        entries = ", ".join(f"{self._emit_expr(k)}: {self._emit_expr(v)}" for k, v in expr.entries)
        return f"map[{key_type}]{val_type}{{{entries}}}"

    def _emit_expr_SetLit(self, expr: SetLit) -> str:
        elem_type = self._type_to_go(expr.element_type)
        elements = ", ".join(f"{self._emit_expr(e)}: {{}}" for e in expr.elements)
        return f"map[{elem_type}]struct{{}}{{{elements}}}"

    def _emit_expr_StructLit(self, expr: StructLit) -> str:
        parts = []
        # Handle embedded struct for exception inheritance
        if expr.embedded_value is not None:
            parts.append(self._emit_expr(expr.embedded_value))
        # Add named fields
        for k, v in expr.fields.items():
            parts.append(f"{go_to_pascal(k)}: {self._emit_expr(v)}")
        fields = ", ".join(parts)
        lit = f"{expr.struct_name}{{{fields}}}"
        if isinstance(expr.typ, Pointer):
            return f"&{lit}"
        return lit

    def _emit_expr_TupleLit(self, expr: TupleLit) -> str:
        """Emit tuple literal as anonymous struct."""
        # Use typed fields from Tuple type if available
        if isinstance(expr.typ, Tuple) and expr.typ.elements:
            types = [self._type_to_go(t) for t in expr.typ.elements]
            # Go anonymous struct fields use semicolons as separators
            fields = "; ".join(f"F{i} {t}" for i, t in enumerate(types))
            vals = ", ".join(self._emit_expr(e) for e in expr.elements)
            return f"struct{{{fields}}}{{{vals}}}"
        # Fallback: use numbered fields (shouldn't happen with proper frontend)
        elements = ", ".join(self._emit_expr(e) for e in expr.elements)
        if len(expr.elements) == 2:
            return f"struct{{F0 interface{{}}; F1 interface{{}}}}{{{elements}}}"
        fields = ", ".join(f"F{i}: {self._emit_expr(e)}" for i, e in enumerate(expr.elements))
        return f"struct{{}}{{{fields}}}"

    def _emit_expr_StringConcat(self, expr: StringConcat) -> str:
        parts = " + ".join(self._emit_expr(p) for p in expr.parts)
        return parts

    def _emit_expr_StringFormat(self, expr: StringFormat) -> str:
        args = ", ".join(self._emit_expr(a) for a in expr.args)
        # Convert Python-style {0}, {1} placeholders to Go-style %v
        template = re_sub(r"\{(\d+)\}", "%v", expr.template)
        escaped = escape_string(template)
        if args:
            return f'fmt.Sprintf("{escaped}", {args})'
        return f'"{escaped}"'

    def _emit_expr_ParseInt(self, expr: ParseInt) -> str:
        # Go's strconv.ParseInt returns (int64, error), so use helper to handle error
        return f"_parseInt({self._emit_expr(expr.string)}, {self._emit_expr(expr.base)})"

    def _emit_expr_IntToStr(self, expr: IntToStr) -> str:
        return f"strconv.Itoa({self._emit_expr(expr.value)})"

    # ============================================================
    # LVALUE EMISSION
    # ============================================================

    def _emit_lvalue(self, lv: LValue) -> str:
        """Emit an lvalue and return Go code string."""
        if isinstance(lv, VarLV):
            return go_to_camel(lv.name)
        if isinstance(lv, FieldLV):
            obj = self._emit_expr(lv.obj)
            field = go_to_pascal(lv.field)
            return f"{obj}.{field}"
        if isinstance(lv, IndexLV):
            obj = self._emit_expr(lv.obj)
            idx = self._emit_expr(lv.index)
            return f"{obj}[{idx}]"
        if isinstance(lv, DerefLV):
            ptr = self._emit_expr(lv.ptr)
            return f"*{ptr}"
        return "/* unknown lvalue */"

    # ============================================================
    # TYPE EMISSION
    # ============================================================

    def _return_type_to_go(self, typ: Type) -> str:
        """Convert IR Type to Go return type string (handles tuples specially)."""
        if isinstance(typ, Tuple):
            # Use Go's multiple return value syntax for function returns
            types = ", ".join(self._type_to_go(e) for e in typ.elements)
            return f"({types})"
        return self._type_to_go(typ)

    def _named_return_type_to_go(self, typ: Type) -> str:
        """Convert IR Type to Go named return type string (for defer/recover pattern)."""
        if isinstance(typ, Tuple):
            # Generate named returns: (result0 Type0, result1 Type1, ...)
            parts = []
            names = []
            for i, e in enumerate(typ.elements):
                name = f"result{i}"
                names.append(name)
                parts.append(f"{name} {self._type_to_go(e)}")
            self._named_returns = names
            return f"({', '.join(parts)})"
        # Single return: (result Type)
        name = "result"
        self._named_returns = [name]
        return f"({name} {self._type_to_go(typ)})"

    def _type_to_go(self, typ: Type) -> str:
        """Convert IR Type to Go type string."""
        if isinstance(typ, Primitive):
            return {
                "string": "string",
                "int": "int",
                "bool": "bool",
                "float": "float64",
                "byte": "byte",
                "rune": "rune",
                "void": "",
            }.get(typ.kind, "interface{}")
        if isinstance(typ, Slice):
            return f"[]{self._type_to_go(typ.element)}"
        if isinstance(typ, Array):
            return f"[{typ.size}]{self._type_to_go(typ.element)}"
        if isinstance(typ, Map):
            return f"map[{self._type_to_go(typ.key)}]{self._type_to_go(typ.value)}"
        if isinstance(typ, Set):
            return f"map[{self._type_to_go(typ.element)}]struct{{}}"
        if isinstance(typ, Tuple):
            # Go doesn't have tuple types for variables; use struct for storage
            fields = "; ".join(f"F{i} {self._type_to_go(e)}" for i, e in enumerate(typ.elements))
            return f"struct{{ {fields} }}"
        if isinstance(typ, Pointer):
            return f"*{self._type_to_go(typ.target)}"
        if isinstance(typ, Optional):
            # Go uses nil for optionals - interfaces and pointers can already be nil
            inner = self._type_to_go(typ.inner)
            if inner.startswith("*"):
                return inner
            # Interface types can already be nil, don't wrap in pointer
            if isinstance(typ.inner, InterfaceRef):
                return inner
            # Slice types can already be nil, don't wrap in pointer
            if isinstance(typ.inner, Slice):
                return inner
            return f"*{inner}"
        if isinstance(typ, StructRef):
            return typ.name
        if isinstance(typ, InterfaceRef):
            if typ.name == "any":
                return "interface{}"
            if typ.name == "None":
                return ""  # void return
            return typ.name
        if isinstance(typ, Union):
            # Go uses interface{} for union types (or a custom interface if named)
            return typ.name if typ.name else "interface{}"
        if isinstance(typ, FuncType):
            params = ", ".join(self._type_to_go(p) for p in typ.params)
            ret = self._type_to_go(typ.ret)
            if ret:
                return f"func({params}) {ret}"
            return f"func({params})"
        if isinstance(typ, StringSlice):
            return "string"
        return "interface{}"

    def _infer_tuple_element_type(self, var_name: str, stmt: If, ret_type: Tuple) -> Type | None:
        """Infer which tuple element a variable corresponds to by scanning returns."""
        pos = _scan_for_return_position(stmt.then_body, var_name)
        if pos is None:
            pos = _scan_for_return_position(stmt.else_body, var_name)
        if pos is not None and pos < len(ret_type.elements):
            return ret_type.elements[pos]
        return None

    # ============================================================
    # OUTPUT HELPERS
    # ============================================================

    def _line(self, text: str) -> None:
        """Emit a line with current indentation."""
        self.output.append("\t" * self.indent + text)

    def _line_raw(self, text: str) -> None:
        """Emit text without newline (for continuations)."""
        self.output.append("\t" * self.indent + text)
