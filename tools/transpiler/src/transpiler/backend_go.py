"""GoBackend: IR -> Go code.

Pure syntax emission - no analysis. All type information comes from IR.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .ir import (
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
        self._declared_vars: set[str] = set()  # Track declared local variables

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
        self._line('"strings"')
        self.indent -= 1
        self._line(")")
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

    def _emit_struct(self, struct: Struct) -> None:
        """Emit struct definition."""
        self._line(f"type {struct.name} struct {{")
        self.indent += 1
        for field in struct.fields:
            go_type = self._type_to_go(field.typ)
            go_name = self._to_pascal(field.name)
            self._line(f"{go_name} {go_type}")
        self.indent -= 1
        self._line("}")
        self._line("")
        # Emit methods
        for method in struct.methods:
            self._emit_function(method)

    def _emit_function(self, func: Function) -> None:
        """Emit function or method definition."""
        # Reset declared vars for new function scope
        self._declared_vars = set()
        # Add parameters to declared vars
        param_names = {self._to_camel(p.name) for p in func.params}
        for p in func.params:
            self._declared_vars.add(self._to_camel(p.name))
        params = ", ".join(
            f"{self._to_camel(p.name)} {self._type_to_go(p.typ)}" for p in func.params
        )
        ret = self._type_to_go(func.ret) if func.ret != VOID else ""
        if func.receiver:
            # Use first letter of receiver name, but avoid collision with params
            recv_name = func.receiver.name[0].lower()
            if recv_name in param_names:
                # Collision - use full receiver type name's first letter instead
                recv_type_name = self._type_to_go(func.receiver.typ).lstrip("*")
                recv_name = recv_type_name[0].lower() + "0"
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
        if stmt.value:
            val = self._emit_expr(stmt.value)
            self._line(f"var {name} {go_type} = {val}")
        else:
            self._line(f"var {name} {go_type}")

    def _emit_stmt_Assign(self, stmt: Assign) -> None:
        target = self._emit_lvalue(stmt.target)
        value = self._emit_expr(stmt.value)
        # For simple variable assignments, use := for first declaration
        if isinstance(stmt.target, VarLV):
            var_name = self._to_camel(stmt.target.name)
            if var_name not in self._declared_vars:
                self._declared_vars.add(var_name)
                self._line(f"{target} := {value}")
                return
        self._line(f"{target} = {value}")

    def _emit_stmt_OpAssign(self, stmt: OpAssign) -> None:
        target = self._emit_lvalue(stmt.target)
        value = self._emit_expr(stmt.value)
        self._line(f"{target} {stmt.op}= {value}")

    def _emit_stmt_ExprStmt(self, stmt: ExprStmt) -> None:
        # Special handling for append - needs to be an assignment in Go
        if isinstance(stmt.expr, MethodCall) and stmt.expr.method == "append" and stmt.expr.args:
            obj = self._emit_expr(stmt.expr.obj)
            arg = self._emit_expr(stmt.expr.args[0])
            self._line(f"{obj} = append({obj}, {arg})")
            return
        expr = self._emit_expr(stmt.expr)
        # Filter out placeholder expressions (after camelCase conversion)
        if expr and not expr.startswith(("skip", "pass", "localFunc", "unknown")):
            self._line(expr)

    def _emit_stmt_Return(self, stmt: Return) -> None:
        if stmt.value:
            val = self._emit_expr(stmt.value)
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
            return f"{self._emit_lvalue(stmt.target)} = {self._emit_expr(stmt.value)}"
        if isinstance(stmt, OpAssign):
            return f"{self._emit_lvalue(stmt.target)} {stmt.op}= {self._emit_expr(stmt.value)}"
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

    def _emit_stmt_Raise(self, stmt: Raise) -> None:
        msg = self._emit_expr(stmt.message)
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
        # Handle tuple indexing on struct types (stack entries)
        # Pattern: stack[i][0] -> stack[i].Single, stack[i][1] -> stack[i].Double
        if isinstance(expr.index, IntLit) and expr.index.value in (0, 1):
            # Check if we're indexing into a stack entry (another Index on "stack")
            if isinstance(expr.obj, Index):
                inner_obj = self._emit_expr(expr.obj.obj)
                if "stack" in inner_obj.lower() or "Stack" in inner_obj:
                    inner_idx = self._emit_expr(expr.obj.index)
                    field = "Single" if expr.index.value == 0 else "Double"
                    return f"{inner_obj}[{inner_idx}].{field}"
        return f"{obj}[{idx}]"

    def _emit_expr_SliceExpr(self, expr: SliceExpr) -> str:
        obj = self._emit_expr(expr.obj)
        low = self._emit_expr(expr.low) if expr.low else ""
        high = self._emit_expr(expr.high) if expr.high else ""
        return f"{obj}[{low}:{high}]"

    def _emit_expr_Call(self, expr: Call) -> str:
        func = self._to_pascal(expr.func)
        args = ", ".join(self._emit_expr(a) for a in expr.args)
        return f"{func}({args})"

    def _emit_expr_MethodCall(self, expr: MethodCall) -> str:
        obj = self._emit_expr(expr.obj)
        method = expr.method  # Keep original for special cases
        # Handle Python list methods specially - only for slice types
        if isinstance(expr.receiver_type, Slice):
            if method == "append" and expr.args:
                arg = self._emit_expr(expr.args[0])
                return f"append({obj}, {arg})"
            if method == "pop" and not expr.args:
                return f"{obj}[len({obj})-1]"
            if method == "copy":
                # Slice copy: append([]T{}, slice...)
                return f"append({obj}[:0:0], {obj}...)"
        method = self._to_pascal(method)
        args = ", ".join(self._emit_expr(a) for a in expr.args)
        return f"{obj}.{method}({args})"

    def _emit_expr_StaticCall(self, expr: StaticCall) -> str:
        on_type = self._type_to_go(expr.on_type)
        method = self._to_pascal(expr.method)
        args = ", ".join(self._emit_expr(a) for a in expr.args)
        return f"{on_type}.{method}({args})"

    def _emit_expr_BinaryOp(self, expr: BinaryOp) -> str:
        left = self._emit_expr(expr.left)
        right = self._emit_expr(expr.right)
        # Handle 'in' and 'not in' operators
        if expr.op == "in":
            return f"strings.Contains({right}, {left})"
        if expr.op == "not in":
            return f"!strings.Contains({right}, {left})"
        return f"({left} {expr.op} {right})"

    def _emit_expr_UnaryOp(self, expr: UnaryOp) -> str:
        operand = self._emit_expr(expr.operand)
        return f"{expr.op}{operand}"

    def _emit_expr_Ternary(self, expr: Ternary) -> str:
        # Go doesn't have ternary, emit as IIFE
        cond = self._emit_expr(expr.cond)
        then_expr = self._emit_expr(expr.then_expr)
        else_expr = self._emit_expr(expr.else_expr)
        go_type = self._type_to_go(expr.typ)
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
        elem_type = self._type_to_go(expr.element_type)
        elements = ", ".join(self._emit_expr(e) for e in expr.elements)
        return f"[]{elem_type}{{{elements}}}"

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
        return f"&{expr.struct_name}{{{fields}}}"

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
        return f"({parts})"

    def _emit_expr_StringFormat(self, expr: StringFormat) -> str:
        args = ", ".join(self._emit_expr(a) for a in expr.args)
        # Escape special characters in template
        escaped = (
            expr.template.replace("\\", "\\\\")
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
            parts = ", ".join(self._type_to_go(e) for e in typ.elements)
            return f"({parts})"
        if isinstance(typ, Pointer):
            return f"*{self._type_to_go(typ.target)}"
        if isinstance(typ, Optional):
            # Go uses nil for optionals on pointer types
            inner = self._type_to_go(typ.inner)
            if inner.startswith("*"):
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
            return typ.name  # Interface type
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
        result = "".join(p.capitalize() for p in parts)
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
        # All-caps names (constants) should use PascalCase in Go
        if name.isupper():
            return "".join(p.capitalize() for p in parts)
        result = parts[0] + "".join(p.capitalize() for p in parts[1:])
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
