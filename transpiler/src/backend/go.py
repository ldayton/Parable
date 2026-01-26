"""GoBackend: IR -> Go code.

Pure syntax emission - no analysis. All type information comes from IR.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

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
    StringSlice,
    Struct,
    StructLit,
    StructRef,
    Ternary,
    TryCatch,
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

if TYPE_CHECKING:
    pass

# Go reserved words that need renaming
GO_RESERVED = {
    "break", "case", "chan", "const", "continue", "default", "defer", "else",
    "fallthrough", "for", "func", "go", "goto", "if", "import", "interface",
    "map", "package", "range", "return", "select", "struct", "switch", "type", "var",
}


class GoBackend:
    """Emit Go code from IR Module."""

    def __init__(self) -> None:
        self.output: list[str] = []
        self.indent = 0
        self._receiver_name: str = ""  # Current method receiver name
        self._tuple_vars: dict[str, Tuple] = {}  # Track tuple-typed variables
        self._hoisted_in_try: set[str] = set()  # Variables hoisted from try blocks

    def emit(self, module: Module) -> str:
        """Emit Go code from IR Module."""
        self.output = []
        self._emit_header(module)
        self._emit_constants(module.constants)
        for struct in module.structs:
            self._emit_struct(struct)
        for func in module.functions:
            self._emit_function(func)
        return "\n".join(self.output)

    def _emit_constants(self, constants: list[Constant]) -> None:
        """Emit module-level constants."""
        if not constants:
            return
        self._line("const (")
        self.indent += 1
        for const in constants:
            name = self._to_pascal(const.name)
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
        self._line('"strconv"')
        self._line('"strings"')
        self._line('"unicode"')
        self.indent -= 1
        self._line(")")
        self._line("")
        self._line("var _ = strings.Compare // ensure import is used")
        self._line("")
        # Emit helper type aliases
        self._line("// quoteStackEntry holds pushed quote state (single, double)")
        self._line("type quoteStackEntry struct {")
        self.indent += 1
        self._line("Single bool")
        self._line("Double bool")
        self.indent -= 1
        self._line("}")
        self._line("")
        # Emit string character classification helpers
        self._emit_string_helpers()

    def _emit_string_helpers(self) -> None:
        """Emit helper functions for Python string methods."""
        helpers = '''
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
'''
        for line in helpers.strip().split('\n'):
            self._line_raw(line)
        self._line("")

    def _emit_struct(self, struct: Struct) -> None:
        """Emit struct definition."""
        # Emit Node as an interface (it's the abstract base for AST nodes)
        if struct.name == "Node":
            self._line(f"type {struct.name} interface {{")
            self.indent += 1
            self._line("isNode()")  # Marker method for type safety
            self.indent -= 1
            self._line("}")
            self._line("")
            return
        self._line(f"type {struct.name} struct {{")
        self.indent += 1
        for field in struct.fields:
            go_type = self._type_to_go(field.typ)
            go_name = self._to_pascal(field.name)
            self._line(f"{go_name} {go_type}")
        self.indent -= 1
        self._line("}")
        self._line("")
        # If struct implements Node, emit the marker method
        if "Node" in struct.implements:
            self._line(f"func (self *{struct.name}) isNode() {{}}")
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
        params = ", ".join(
            f"{self._to_camel(p.name)} {self._type_to_go(p.typ)}" for p in func.params
        )
        ret = self._return_type_to_go(func.ret) if func.ret != VOID else ""
        if func.receiver:
            # Use the receiver name from IR directly (converted to camelCase)
            recv_name = self._to_camel(func.receiver.name)
            self._receiver_name = recv_name
            recv_type = self._type_to_go(func.receiver.typ)
            if func.receiver.pointer:
                recv_type = "*" + recv_type.lstrip("*")
            self._line(f"func ({recv_name} {recv_type}) {self._to_pascal(func.name)}({params}) {ret} {{")
        else:
            self._receiver_name = ""
            name = self._to_pascal(func.name)
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
        method = f"_emit_stmt_{type(stmt).__name__}"
        if hasattr(self, method):
            getattr(self, method)(stmt)
        else:
            self._line(f"// TODO: {type(stmt).__name__}")

    def _emit_stmt_VarDecl(self, stmt: VarDecl) -> None:
        go_type = self._type_to_go(stmt.typ)
        name = self._to_camel(stmt.name)
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
                self._line(f"var {name} {go_type} = func() {go_type} {{ {tmp_vars} := {call_expr}; return {go_type}{{{field_vals}}} }}()")
                return
        if stmt.value:
            val = self._emit_expr(stmt.value)
            # Use short declaration for simple types, explicit var for complex types
            if isinstance(stmt.typ, (Tuple, Slice, Map, Set)) and not isinstance(stmt.value, (SliceLit, MapLit, SetLit, MakeSlice, MakeMap)):
                self._line(f"var {name} {go_type} = {val}")
            else:
                self._line(f"{name} := {val}")
        else:
            self._line(f"var {name} {go_type}")

    def _emit_stmt_Assign(self, stmt: Assign) -> None:
        target = self._emit_lvalue(stmt.target)
        value = self._emit_expr(stmt.value)
        if getattr(stmt, 'is_declaration', False):
            # Check if this var was hoisted - use = instead of :=
            if isinstance(stmt.target, VarLV) and stmt.target.name in self._hoisted_in_try:
                self._line(f"{target} = {value}")
            else:
                self._line(f"{target} := {value}")
        else:
            self._line(f"{target} = {value}")

    def _emit_stmt_TupleAssign(self, stmt: TupleAssign) -> None:
        """Emit tuple unpacking: a, b := func()"""
        targets = []
        for t in stmt.targets:
            if isinstance(t, VarLV):
                if t.name == "_":
                    targets.append("_")
                else:
                    targets.append(self._to_camel(t.name))
            else:
                targets.append(self._emit_lvalue(t))
        target_str = ", ".join(targets)
        value = self._emit_expr(stmt.value)
        if getattr(stmt, 'is_declaration', False):
            # Check if ANY target was hoisted - use = instead of :=
            any_hoisted = any(
                isinstance(t, VarLV) and t.name in self._hoisted_in_try
                for t in stmt.targets
            )
            if any_hoisted:
                self._line(f"{target_str} = {value}")
            else:
                self._line(f"{target_str} := {value}")
        else:
            self._line(f"{target_str} = {value}")

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
            arg_type = stmt.expr.args[0].typ if hasattr(stmt.expr.args[0], 'typ') else None
            recv_type = stmt.expr.receiver_type

            def needs_deref(arg_type, elem_type):
                """Check if pointer arg needs dereference when appending to slice."""
                if not isinstance(arg_type, Pointer) or not isinstance(arg_type.target, StructRef):
                    return False
                if isinstance(elem_type, StructRef) and arg_type.target.name == elem_type.name:
                    return True
                if isinstance(elem_type, Interface) and arg_type.target.name == elem_type.name:
                    return True
                return False

            def needs_byte_cast(arg_type, elem_type):
                """Check if int arg needs cast to byte when appending to []byte."""
                return arg_type == INT and elem_type == BYTE

            def needs_string_cast(arg_type, elem_type):
                """Check if rune arg needs cast to string when appending to []string or []any."""
                if arg_type != RUNE:
                    return False
                if elem_type == STRING:
                    return True
                # Rune appended to []interface{} also needs conversion (common pattern)
                if isinstance(elem_type, Interface) and elem_type.name == "any":
                    return True
                return False

            # Handle pointer-to-slice receiver
            if isinstance(recv_type, Pointer) and isinstance(recv_type.target, Slice):
                elem_type = recv_type.target.element
                if needs_deref(arg_type, elem_type):
                    self._line(f"*{obj} = append(*{obj}, *{arg})")
                elif needs_byte_cast(arg_type, elem_type):
                    self._line(f"*{obj} = append(*{obj}, byte({arg}))")
                elif needs_string_cast(arg_type, elem_type):
                    self._line(f"*{obj} = append(*{obj}, string({arg}))")
                else:
                    self._line(f"*{obj} = append(*{obj}, {arg})")
            # Handle regular slice receiver
            elif isinstance(recv_type, Slice):
                elem_type = recv_type.element
                if needs_deref(arg_type, elem_type):
                    self._line(f"{obj} = append({obj}, *{arg})")
                elif needs_byte_cast(arg_type, elem_type):
                    self._line(f"{obj} = append({obj}, byte({arg}))")
                elif needs_string_cast(arg_type, elem_type):
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
            if isinstance(stmt.expr.receiver_type, Pointer) and isinstance(stmt.expr.receiver_type.target, Slice):
                self._line(f"*{obj} = append(*{obj}, {arg}...)")
            else:
                self._line(f"{obj} = append({obj}, {arg}...)")
            return
        expr = self._emit_expr(stmt.expr)
        # Filter out placeholder expressions (after camelCase conversion)
        if expr and not expr.startswith(("skip", "pass", "localFunc", "unknown")):
            self._line(expr)

    def _emit_stmt_Return(self, stmt: Return) -> None:
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
                ret_type = getattr(self, '_current_return_type', None)
                val_type = getattr(stmt.value, 'typ', None)
                if (isinstance(ret_type, Optional) and
                    val_type and not isinstance(val_type, (Optional, Pointer)) and
                    not isinstance(stmt.value, NilLit)):
                    val = f"&{val}"
                self._line(f"return {val}")
        else:
            self._line("return")

    def _emit_stmt_If(self, stmt: If) -> None:
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
        cond = self._emit_expr(stmt.cond)
        self._line(f"for {cond} {{")
        self.indent += 1
        for s in stmt.body:
            self._emit_stmt(s)
        self.indent -= 1
        self._line("}")

    def _emit_stmt_ForRange(self, stmt: ForRange) -> None:
        iterable = self._emit_expr(stmt.iterable)
        idx = stmt.index if stmt.index else "_"
        val = stmt.value if stmt.value else "_"
        idx_go = self._to_camel(idx) if idx != "_" else "_"
        val_go = self._to_camel(val) if val != "_" else "_"
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
            name = self._to_camel(stmt.name)
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
        self._line("{")
        self.indent += 1
        for s in stmt.body:
            self._emit_stmt(s)
        self.indent -= 1
        self._line("}")

    def _emit_stmt_TryCatch(self, stmt: TryCatch) -> None:
        # Emit hoisted variable declarations before the IIFE
        hoisted_vars = getattr(stmt, 'hoisted_vars', [])
        for name, typ in hoisted_vars:
            type_str = self._type_to_go(typ) if typ else "interface{}"
            go_name = self._to_camel(name)
            self._line(f"var {go_name} {type_str}")
            self._hoisted_in_try.add(name)

        # Go uses defer/recover pattern
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
        msg = self._emit_expr(stmt.message)
        # Include position in panic if available (non-zero/non-literal-0)
        pos = self._emit_expr(stmt.pos)
        if pos != "0":
            self._line(f'panic(fmt.Sprintf("%s at position %d", {msg}, {pos}))')
        else:
            self._line(f'panic({msg})')

    def _emit_stmt_SoftFail(self, stmt: SoftFail) -> None:
        self._line("return nil")

    def _emit_stmt_TypeSwitch(self, stmt: TypeSwitch) -> None:
        expr = self._emit_expr(stmt.expr)
        binding = self._to_camel(stmt.binding)
        self._line(f"switch {binding} := {expr}.(type) {{")
        for case in stmt.cases:
            go_type = self._type_to_go(case.typ)
            self._line(f"case {go_type}:")
            self.indent += 1
            for s in case.body:
                self._emit_stmt(s)
            self.indent -= 1
        if stmt.default:
            self._line("default:")
            self.indent += 1
            for s in stmt.default:
                self._emit_stmt(s)
            self.indent -= 1
        self._line("}")

    def _emit_stmt_Match(self, stmt: Match) -> None:
        expr = self._emit_expr(stmt.expr)
        self._line(f"switch {expr} {{")
        for case in stmt.cases:
            patterns = ", ".join(self._emit_expr(p) for p in case.patterns)
            self._line(f"case {patterns}:")
            self.indent += 1
            for s in case.body:
                self._emit_stmt(s)
            self.indent -= 1
        if stmt.default:
            self._line("default:")
            self.indent += 1
            for s in stmt.default:
                self._emit_stmt(s)
            self.indent -= 1
        self._line("}")

    # ============================================================
    # EXPRESSION EMISSION
    # ============================================================

    def _emit_expr(self, expr: Expr) -> str:
        """Emit an expression and return Go code string."""
        method = f"_emit_expr_{type(expr).__name__}"
        if hasattr(self, method):
            return getattr(self, method)(expr)
        return f"/* TODO: {type(expr).__name__} */"

    def _emit_expr_IntLit(self, expr: IntLit) -> str:
        return str(expr.value)

    def _emit_expr_FloatLit(self, expr: FloatLit) -> str:
        return str(expr.value)

    def _emit_expr_StringLit(self, expr: StringLit) -> str:
        escaped = (
            expr.value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\t", "\\t")
            .replace("\r", "\\r")
        )
        return f'"{escaped}"'

    def _emit_expr_BoolLit(self, expr: BoolLit) -> str:
        return "true" if expr.value else "false"

    def _emit_expr_NilLit(self, expr: NilLit) -> str:
        return "nil"

    def _emit_expr_Var(self, expr: Var) -> str:
        if expr.name == "self":
            return self._receiver_name if self._receiver_name else "self"
        return self._to_camel(expr.name)

    def _emit_expr_FieldAccess(self, expr: FieldAccess) -> str:
        obj = self._emit_expr(expr.obj)
        field = self._to_pascal(expr.field)
        return f"{obj}.{field}"

    def _emit_expr_Index(self, expr: Index) -> str:
        obj = self._emit_expr(expr.obj)
        idx = self._emit_expr(expr.index)
        # Handle tuple indexing - use field access for tuple types
        if isinstance(expr.index, IntLit):
            # Check if indexing into a known tuple variable
            if isinstance(expr.obj, Var):
                var_name = self._to_camel(expr.obj.name)
                if var_name in self._tuple_vars:
                    return f"{obj}.F{expr.index.value}"
            # Check if indexing into a tuple type (struct with F0, F1, etc.)
            if hasattr(expr, 'obj_type') and isinstance(expr.obj_type, Tuple):
                return f"{obj}.F{expr.index.value}"
            # Handle stack entry pattern: stack[i][0] -> stack[i].Single
            if expr.index.value in (0, 1) and isinstance(expr.obj, Index):
                inner_obj = self._emit_expr(expr.obj.obj)
                if "stack" in inner_obj.lower() or "Stack" in inner_obj:
                    inner_idx = self._emit_expr(expr.obj.index)
                    field = "Single" if expr.index.value == 0 else "Double"
                    return f"{inner_obj}[{inner_idx}].{field}"
        result = f"{obj}[{idx}]"
        # In Go, indexing a string returns byte, cast to int if needed
        obj_type = getattr(expr.obj, 'typ', None)
        if obj_type == STRING and expr.typ == INT:
            result = f"int({result})"
        return result

    def _emit_expr_SliceExpr(self, expr: SliceExpr) -> str:
        obj = self._emit_expr(expr.obj)
        low = self._emit_expr(expr.low) if expr.low else ""
        high = self._emit_expr(expr.high) if expr.high else ""
        return f"{obj}[{low}:{high}]"

    def _emit_expr_Call(self, expr: Call) -> str:
        # Go builtins and our helpers stay as-is
        if expr.func in ("append", "cap", "close", "copy", "delete", "panic", "recover", "print", "println", "_parseInt"):
            func = expr.func
        else:
            func = self._to_pascal(expr.func)
        args = ", ".join(self._emit_expr(a) for a in expr.args)
        return f"{func}({args})"

    def _emit_expr_MethodCall(self, expr: MethodCall) -> str:
        obj = self._emit_expr(expr.obj)
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
                arg_type = expr.args[0].typ if hasattr(expr.args[0], 'typ') else None
                elem_type = expr.receiver_type.element
                needs_deref = False
                if isinstance(arg_type, Pointer) and isinstance(arg_type.target, StructRef):
                    # Check if element is StructRef with same name
                    if isinstance(elem_type, StructRef) and arg_type.target.name == elem_type.name:
                        needs_deref = True
                    # Or element is Interface with same name (Node interface)
                    elif isinstance(elem_type, Interface) and arg_type.target.name == elem_type.name:
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
        # Handle Python string character classification methods (always, type inference may be imprecise)
        if method == "isalnum":
            return f"_strIsAlnum({obj})"
        if method == "isalpha":
            return f"_strIsAlpha({obj})"
        if method == "isdigit":
            return f"_strIsDigit({obj})"
        if method == "isspace":
            return f"_strIsSpace({obj})"
        if method == "isupper":
            return f"_strIsUpper({obj})"
        if method == "islower":
            return f"_strIsLower({obj})"
        # Handle Python string methods that map to strings package
        if method == "startswith" and expr.args:
            arg = self._emit_expr(expr.args[0])
            return f"strings.HasPrefix({obj}, {arg})"
        if method == "endswith" and expr.args:
            arg = self._emit_expr(expr.args[0])
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
            return f"strings.TrimLeft({obj}, \" \\t\\n\\r\")"
        if method == "rstrip":
            if expr.args:
                arg = self._emit_expr(expr.args[0])
                return f"strings.TrimRight({obj}, {arg})"
            return f"strings.TrimRight({obj}, \" \\t\\n\\r\")"
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
        method = self._to_pascal(method)
        args = ", ".join(self._emit_expr(a) for a in expr.args)
        return f"{obj}.{method}({args})"

    def _emit_expr_StaticCall(self, expr: StaticCall) -> str:
        on_type = self._type_to_go(expr.on_type)
        method = self._to_pascal(expr.method)
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
        left = self._emit_expr(expr.left)
        right = self._emit_expr(expr.right)
        # Handle 'in' and 'not in' operators
        if expr.op == "in":
            return f"strings.Contains({right}, {left})"
        if expr.op == "not in":
            return f"!strings.Contains({right}, {left})"
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
        operand = self._emit_expr(expr.operand)
        # Wrap complex operands in parens for ! operator
        if expr.op == "!" and isinstance(expr.operand, (BinaryOp, UnaryOp, IsNil)):
            return f"{expr.op}({operand})"
        return f"{expr.op}{operand}"

    def _emit_expr_Ternary(self, expr: Ternary) -> str:
        # Go doesn't have ternary, emit as IIFE
        cond = self._emit_expr(expr.cond)
        then_expr = self._emit_expr(expr.then_expr)
        else_expr = self._emit_expr(expr.else_expr)
        # When ternary type is any but both branches have same concrete type, use that
        result_type = expr.typ
        if isinstance(result_type, Interface) and result_type.name == "any":
            then_type = getattr(expr.then_expr, 'typ', None)
            else_type = getattr(expr.else_expr, 'typ', None)
            if then_type is not None and then_type == else_type:
                result_type = then_type
        go_type = self._type_to_go(result_type)
        return f"func() {go_type} {{ if {cond} {{ return {then_expr} }} else {{ return {else_expr} }} }}()"

    def _emit_expr_Cast(self, expr: Cast) -> str:
        inner = self._emit_expr(expr.expr)
        to_type = self._type_to_go(expr.to_type)
        return f"{to_type}({inner})"

    def _emit_expr_TypeAssert(self, expr: TypeAssert) -> str:
        inner = self._emit_expr(expr.expr)
        asserted = self._type_to_go(expr.asserted)
        return f"{inner}.({asserted})"

    def _emit_expr_IsType(self, expr: IsType) -> str:
        inner = self._emit_expr(expr.expr)
        tested = self._type_to_go(expr.tested_type)
        return f"func() bool {{ _, ok := {inner}.({tested}); return ok }}()"

    def _emit_expr_IsNil(self, expr: IsNil) -> str:
        inner = self._emit_expr(expr.expr)
        if expr.negated:
            return f"{inner} != nil"
        return f"{inner} == nil"

    def _emit_expr_Len(self, expr: Len) -> str:
        inner = self._emit_expr(expr.expr)
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
        elem_type = expr.element_type
        # Empty slices with any type default to []string (common pattern in string-heavy code)
        if not expr.elements and isinstance(elem_type, Interface) and elem_type.name == "any":
            return "[]string{}"
        go_elem = self._type_to_go(elem_type)
        elements = ", ".join(self._emit_expr(e) for e in expr.elements)
        return f"[]{go_elem}{{{elements}}}"

    def _emit_expr_MapLit(self, expr: MapLit) -> str:
        key_type = self._type_to_go(expr.key_type)
        val_type = self._type_to_go(expr.value_type)
        entries = ", ".join(
            f"{self._emit_expr(k)}: {self._emit_expr(v)}" for k, v in expr.entries
        )
        return f"map[{key_type}]{val_type}{{{entries}}}"

    def _emit_expr_SetLit(self, expr: SetLit) -> str:
        elem_type = self._type_to_go(expr.element_type)
        elements = ", ".join(f"{self._emit_expr(e)}: {{}}" for e in expr.elements)
        return f"map[{elem_type}]struct{{}}{{{elements}}}"

    def _emit_expr_StructLit(self, expr: StructLit) -> str:
        fields = ", ".join(
            f"{self._to_pascal(k)}: {self._emit_expr(v)}" for k, v in expr.fields.items()
        )
        lit = f"{expr.struct_name}{{{fields}}}"
        if isinstance(expr.typ, Pointer):
            return f"&{lit}"
        return lit

    def _emit_expr_TupleLit(self, expr: TupleLit) -> str:
        """Emit tuple literal as anonymous struct."""
        # For 2-element tuples commonly used in quoteStackEntry, emit as struct{A, B type}{}
        elements = ", ".join(self._emit_expr(e) for e in expr.elements)
        if len(expr.elements) == 2:
            # Common pattern: struct{Single, Double bool}{val1, val2}
            return f"struct{{Single, Double bool}}{{{elements}}}"
        # Fallback: use numbered fields
        fields = ", ".join(f"F{i}: {self._emit_expr(e)}" for i, e in enumerate(expr.elements))
        return f"struct{{}}{{{fields}}}"

    def _emit_expr_StringConcat(self, expr: StringConcat) -> str:
        parts = " + ".join(self._emit_expr(p) for p in expr.parts)
        return parts

    def _emit_expr_StringFormat(self, expr: StringFormat) -> str:
        args = ", ".join(self._emit_expr(a) for a in expr.args)
        # Convert Python-style {0}, {1} placeholders to Go-style %v
        import re
        template = expr.template
        template = re.sub(r'\{(\d+)\}', '%v', template)
        # Escape special characters in template
        escaped = (
            template.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\t", "\\t")
            .replace("\r", "\\r")
        )
        if args:
            return f'fmt.Sprintf("{escaped}", {args})'
        return f'"{escaped}"'

    # ============================================================
    # LVALUE EMISSION
    # ============================================================

    def _emit_lvalue(self, lv: LValue) -> str:
        """Emit an lvalue and return Go code string."""
        if isinstance(lv, VarLV):
            return self._to_camel(lv.name)
        if isinstance(lv, FieldLV):
            obj = self._emit_expr(lv.obj)
            field = self._to_pascal(lv.field)
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
            if isinstance(typ.inner, Interface):
                return inner
            return f"*{inner}"
        if isinstance(typ, StructRef):
            return typ.name
        if isinstance(typ, Interface):
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

    # ============================================================
    # NAME CONVERSION
    # ============================================================

    def _to_pascal(self, name: str) -> str:
        """Convert snake_case to PascalCase. Private methods (underscore prefix) become unexported."""
        is_private = name.startswith("_")
        if is_private:
            name = name[1:]
        parts = name.split("_")
        # Use upper on first char only (not capitalize which lowercases rest)
        result = "".join((p[0].upper() + p[1:]) if p else "" for p in parts)
        if is_private:
            # Make first letter lowercase for unexported (private) names
            return result[0].lower() + result[1:] if result else result
        return result

    def _to_camel(self, name: str) -> str:
        """Convert snake_case to camelCase."""
        if name == "self":
            return name
        if name.startswith("_"):
            name = name[1:]
        parts = name.split("_")
        if not parts:
            return name
        # Use upper on first char only (not capitalize which lowercases rest)
        def upper_first(s: str) -> str:
            return (s[0].upper() + s[1:]) if s else ""
        # All-caps names (constants) should use PascalCase in Go
        if name.isupper():
            return "".join(upper_first(p) for p in parts)
        result = parts[0] + "".join(upper_first(p) for p in parts[1:])
        # Handle Go reserved words
        if result in GO_RESERVED:
            return result + "_"
        return result

    # ============================================================
    # OUTPUT HELPERS
    # ============================================================

    def _line(self, text: str) -> None:
        """Emit a line with current indentation."""
        self.output.append("\t" * self.indent + text)

    def _line_raw(self, text: str) -> None:
        """Emit text without newline (for continuations)."""
        self.output.append("\t" * self.indent + text)
