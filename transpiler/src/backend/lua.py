"""Lua backend: IR → Lua code.

Targets Lua 5.4+ with backwards compatibility to 5.1.
Key differences from other backends:
- 1-based indexing (arrays and strings)
- Classes via metatables
- No continue statement in 5.1 (use repeat/until pattern)
- Ternary via cond and a or b (caveat with falsy then-values)
"""

from __future__ import annotations

from src.backend.util import escape_string, to_snake, to_screaming_snake
from src.ir import (
    Array,
    Assign,
    BinaryOp,
    Block,
    BoolLit,
    Break,
    Call,
    Cast,
    CharClassify,
    CharLit,
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
    Struct,
    StructLit,
    StructRef,
    Ternary,
    TrimChars,
    TryCatch,
    Tuple,
    TupleAssign,
    Truthy,
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


def _is_empty_body(body: list[Stmt]) -> bool:
    """Check if body is empty or contains only NoOp statements."""
    return not body or all(isinstance(s, NoOp) for s in body)


_LUA_RESERVED = frozenset(
    {
        "and",
        "break",
        "do",
        "else",
        "elseif",
        "end",
        "false",
        "for",
        "function",
        "goto",
        "if",
        "in",
        "local",
        "nil",
        "not",
        "or",
        "repeat",
        "return",
        "then",
        "true",
        "until",
        "while",
        # Common globals to avoid shadowing
        "arg",  # Command-line arguments table
        "type",
        "error",
        "pairs",
        "ipairs",
        "next",
        "string",
        "table",
        "math",
        "io",
        "os",
        "require",
        "pcall",
        "xpcall",
        "setmetatable",
        "getmetatable",
        "tonumber",
        "tostring",
    }
)


def _safe_name(name: str) -> str:
    """Rename variables that conflict with Lua reserved words."""
    if name == "_":
        return "_"  # Lua uses _ for ignored values
    name = to_snake(name)
    if not name:
        return "_"  # Fallback for empty names
    if name in _LUA_RESERVED:
        return name + "_"
    return name


def _is_constant(name: str) -> bool:
    """Check if name looks like a constant (SCREAMING_SNAKE_CASE)."""
    return name.isupper() or (name.replace("_", "").isupper() and "_" in name)


def _safe_type_name(name: str) -> str:
    """Ensure type name is valid (starts with uppercase)."""
    if name and name[0].islower():
        return name[0].upper() + name[1:]
    return name


class LuaBackend:
    """Emit Lua code from IR."""

    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self.receiver_name: str | None = None
        self.struct_fields: dict[str, list[str]] = {}  # struct name -> [field_names]
        self._has_continue = False  # Track if we need continue helper
        self._needs_table_slice = False
        self._needs_string_split = False
        self._needs_set_contains = False
        self._needs_string_find = False
        self._hoisted_vars: set[str] = set()  # Variables already declared via hoisting

    def emit(self, module: Module) -> str:
        """Emit Lua code from IR Module."""
        self.indent = 0
        self.lines = []
        self.struct_fields = {}
        self._has_continue = False
        self._needs_table_slice = False
        self._needs_string_split = False
        self._needs_set_contains = False
        self._needs_string_find = False
        self._hoisted_vars = set()
        # First pass to collect struct field info
        for struct in module.structs:
            self.struct_fields[struct.name] = [f.name for f in struct.fields]
        # Scan for continue statements
        self._scan_for_continue(module)
        self._emit_module(module)
        return "\n".join(self.lines)

    def _scan_for_continue(self, module: Module) -> None:
        """Scan module for continue statements."""
        for func in module.functions:
            if self._body_has_continue(func.body):
                self._has_continue = True
                return
        for struct in module.structs:
            for method in struct.methods:
                if self._body_has_continue(method.body):
                    self._has_continue = True
                    return

    def _body_has_continue(self, body: list[Stmt]) -> bool:
        """Check if body contains any continue statements (including nested)."""
        for stmt in body:
            if isinstance(stmt, Continue):
                return True
            if isinstance(stmt, If):
                if self._body_has_continue(stmt.then_body) or self._body_has_continue(
                    stmt.else_body
                ):
                    return True
            elif isinstance(stmt, While):
                if self._body_has_continue(stmt.body):
                    return True
            elif isinstance(stmt, ForRange):
                if self._body_has_continue(stmt.body):
                    return True
            elif isinstance(stmt, ForClassic):
                if self._body_has_continue(stmt.body):
                    return True
            elif isinstance(stmt, Block):
                if self._body_has_continue(stmt.body):
                    return True
            elif isinstance(stmt, TryCatch):
                if self._body_has_continue(stmt.body) or self._body_has_continue(
                    stmt.catch_body
                ):
                    return True
            elif isinstance(stmt, Match):
                for case in stmt.cases:
                    if self._body_has_continue(case.body):
                        return True
                if self._body_has_continue(stmt.default):
                    return True
        return False

    def _body_has_direct_continue(self, body: list[Stmt]) -> bool:
        """Check if body contains continue statements NOT inside nested loops."""
        for stmt in body:
            if isinstance(stmt, Continue):
                return True
            if isinstance(stmt, If):
                if self._body_has_direct_continue(
                    stmt.then_body
                ) or self._body_has_direct_continue(stmt.else_body):
                    return True
            elif isinstance(stmt, Block):
                if self._body_has_direct_continue(stmt.body):
                    return True
            elif isinstance(stmt, TryCatch):
                if self._body_has_direct_continue(
                    stmt.body
                ) or self._body_has_direct_continue(stmt.catch_body):
                    return True
            elif isinstance(stmt, Match):
                for case in stmt.cases:
                    if self._body_has_direct_continue(case.body):
                        return True
                if self._body_has_direct_continue(stmt.default):
                    return True
            elif isinstance(stmt, TypeSwitch):
                for case in stmt.cases:
                    if self._body_has_direct_continue(case.body):
                        return True
                if self._body_has_direct_continue(stmt.default):
                    return True
            # Skip While, ForRange, ForClassic - continues inside those are handled by those loops
            elif isinstance(stmt, TypeSwitch):
                for case in stmt.cases:
                    if self._body_has_continue(case.body):
                        return True
                if self._body_has_continue(stmt.default):
                    return True
        return False

    def _body_has_return(self, body: list[Stmt]) -> bool:
        """Check if body contains any return statements."""
        for stmt in body:
            if isinstance(stmt, Return) and stmt.value is not None:
                return True
            if isinstance(stmt, If):
                if self._body_has_return(stmt.then_body) or self._body_has_return(
                    stmt.else_body
                ):
                    return True
            elif isinstance(stmt, (While, ForRange)):
                if self._body_has_return(stmt.body):
                    return True
            elif isinstance(stmt, ForClassic):
                if self._body_has_return(stmt.body):
                    return True
            elif isinstance(stmt, Block):
                if self._body_has_return(stmt.body):
                    return True
            elif isinstance(stmt, TryCatch):
                if self._body_has_return(stmt.body) or self._body_has_return(
                    stmt.catch_body
                ):
                    return True
            elif isinstance(stmt, Match):
                for case in stmt.cases:
                    if self._body_has_return(case.body):
                        return True
                if self._body_has_return(stmt.default):
                    return True
            elif isinstance(stmt, TypeSwitch):
                for case in stmt.cases:
                    if self._body_has_return(case.body):
                        return True
                if self._body_has_return(stmt.default):
                    return True
        return False

    def _collect_assigned_vars(self, stmts: list[Stmt]) -> set[str]:
        """Collect all variable names assigned in statements (for hoisting)."""
        result: set[str] = set()
        for stmt in stmts:
            match stmt:
                case VarDecl(name=name):
                    result.add(name)
                case Assign(target=VarLV(name=name)):
                    result.add(name)
                case TupleAssign(new_targets=new_targets):
                    result.update(new_targets)
                case If(init=init, then_body=then_body, else_body=else_body):
                    if init and isinstance(init, VarDecl):
                        result.add(init.name)
                    result.update(self._collect_assigned_vars(then_body))
                    result.update(self._collect_assigned_vars(else_body))
                case ForRange(index=index, value=value, body=body):
                    if index:
                        result.add(index)
                    if value:
                        result.add(value)
                    result.update(self._collect_assigned_vars(body))
                case ForClassic(init=init, body=body):
                    if init:
                        result.update(self._collect_assigned_vars([init]))
                    result.update(self._collect_assigned_vars(body))
                case While(body=body):
                    result.update(self._collect_assigned_vars(body))
                case Block(body=body):
                    result.update(self._collect_assigned_vars(body))
                case TryCatch(body=body, catch_var=catch_var, catch_body=catch_body):
                    result.update(self._collect_assigned_vars(body))
                    if catch_var:
                        result.add(catch_var)
                    result.update(self._collect_assigned_vars(catch_body))
                case Match(cases=cases, default=default):
                    for case in cases:
                        result.update(self._collect_assigned_vars(case.body))
                    result.update(self._collect_assigned_vars(default))
                case TypeSwitch(binding=binding, cases=cases, default=default):
                    if binding:
                        result.add(binding)
                    for case in cases:
                        result.update(self._collect_assigned_vars(case.body))
                    result.update(self._collect_assigned_vars(default))
        return result

    def _line(self, text: str = "") -> None:
        if text:
            self.lines.append("  " * self.indent + text)
        else:
            self.lines.append("")

    def _emit_module(self, module: Module) -> None:
        self._line("-- Generated Lua code")
        self._line()
        self._emit_preamble()
        need_blank = True
        if module.constants:
            for const in module.constants:
                self._emit_constant(const)
            need_blank = True
        for iface in module.interfaces:
            if need_blank:
                self._line()
            self._emit_interface(iface)
            need_blank = True
        for struct in module.structs:
            if need_blank:
                self._line()
            self._emit_struct(struct)
            need_blank = True
        for func in module.functions:
            if need_blank:
                self._line()
            self._emit_function(func)
            need_blank = True

    def _emit_preamble(self) -> None:
        """Emit helper functions needed by generated code."""
        # Table slice helper
        self._line("local function _table_slice(t, i, j)")
        self.indent += 1
        self._line("local result = {}")
        self._line("j = j or #t")
        self._line("for k = i, j do")
        self.indent += 1
        self._line("result[#result + 1] = t[k]")
        self.indent -= 1
        self._line("end")
        self._line("return result")
        self.indent -= 1
        self._line("end")
        self._line()
        # String split helper
        self._line("local function _string_split(s, sep)")
        self.indent += 1
        self._line("if sep == '' then")
        self.indent += 1
        self._line("local result = {}")
        self._line("for i = 1, #s do")
        self.indent += 1
        self._line("result[i] = s:sub(i, i)")
        self.indent -= 1
        self._line("end")
        self._line("return result")
        self.indent -= 1
        self._line("end")
        self._line("local result = {}")
        self._line("local pattern = '([^' .. sep .. ']+)'")
        self._line("for part in string.gmatch(s, pattern) do")
        self.indent += 1
        self._line("result[#result + 1] = part")
        self.indent -= 1
        self._line("end")
        self._line("return result")
        self.indent -= 1
        self._line("end")
        self._line()
        # Set contains helper
        self._line("local function _set_contains(s, v)")
        self.indent += 1
        self._line("return s[v] == true")
        self.indent -= 1
        self._line("end")
        self._line()
        # Set add helper
        self._line("local function _set_add(s, v)")
        self.indent += 1
        self._line("s[v] = true")
        self.indent -= 1
        self._line("end")
        self._line()
        # String find helper (returns 0-based index or -1)
        self._line("local function _string_find(s, sub, start)")
        self.indent += 1
        self._line("start = start or 0")
        self._line("local pos = string.find(s, sub, start + 1, true)")
        self._line("if pos then return pos - 1 else return -1 end")
        self.indent -= 1
        self._line("end")
        self._line()
        # String rfind helper (returns 0-based index or -1)
        self._line("local function _string_rfind(s, sub)")
        self.indent += 1
        self._line("local last = -1")
        self._line("local start = 1")
        self._line("while true do")
        self.indent += 1
        self._line("local pos = string.find(s, sub, start, true)")
        self._line("if not pos then break end")
        self._line("last = pos - 1")
        self._line("start = pos + 1")
        self.indent -= 1
        self._line("end")
        self._line("return last")
        self.indent -= 1
        self._line("end")
        self._line()
        # Range helper for range() calls
        self._line("local function _range(start, stop, step)")
        self.indent += 1
        self._line("if stop == nil then stop = start; start = 0 end")
        self._line("step = step or 1")
        self._line("local result = {}")
        self._line("if step > 0 then")
        self.indent += 1
        self._line("for i = start, stop - 1, step do")
        self.indent += 1
        self._line("result[#result + 1] = i")
        self.indent -= 1
        self._line("end")
        self.indent -= 1
        self._line("else")
        self.indent += 1
        self._line("for i = start, stop + 1, step do")
        self.indent += 1
        self._line("result[#result + 1] = i")
        self.indent -= 1
        self._line("end")
        self.indent -= 1
        self._line("end")
        self._line("return result")
        self.indent -= 1
        self._line("end")
        self._line()
        # Map get with default
        self._line("local function _map_get(m, key, default)")
        self.indent += 1
        self._line("local v = m[key]")
        self._line("if v == nil then return default else return v end")
        self.indent -= 1
        self._line("end")
        self._line()
        # Bytes to string helper (for decode())
        self._line("local function _bytes_to_string(bytes)")
        self.indent += 1
        self._line("local chars = {}")
        self._line("for i, b in ipairs(bytes) do")
        self.indent += 1
        self._line("chars[i] = string.char(b)")
        self.indent -= 1
        self._line("end")
        self._line("return table.concat(chars, '')")
        self.indent -= 1
        self._line("end")

    def _emit_constant(self, const: Constant) -> None:
        name = to_screaming_snake(const.name)
        val = self._expr(const.value)
        self._line(f"{name} = {val}")

    def _emit_interface(self, iface: InterfaceDef) -> None:
        # Lua doesn't have interfaces, emit as comment
        self._line(f"-- Interface: {iface.name}")
        for method in iface.methods:
            params = ", ".join(_safe_name(p.name) for p in method.params)
            self._line(f"--   {_safe_name(method.name)}({params})")

    def _emit_struct(self, struct: Struct) -> None:
        is_empty = not struct.fields and not struct.methods and not struct.doc
        if is_empty and not struct.is_exception and not struct.implements:
            return
        name = _safe_type_name(struct.name)
        self._line(f"{name} = {{}}")
        self._line(f"{name}.__index = {name}")
        self._line()
        # Constructor
        if struct.fields or struct.is_exception:
            self._emit_constructor(struct)
        # Methods
        for method in struct.methods:
            self._line()
            self._emit_method(method, name)

    def _emit_constructor(self, struct: Struct) -> None:
        name = _safe_type_name(struct.name)
        # Build parameter list with defaults
        params = []
        for f in struct.fields:
            params.append(_safe_name(f.name))
        params_str = ", ".join(params)
        self._line(f"function {name}:new({params_str})")
        self.indent += 1
        self._line(f"local self = setmetatable({{}}, {name})")
        for f in struct.fields:
            fname = _safe_name(f.name)
            if f.default is not None:
                default = self._expr(f.default)
                self._line(f"if {fname} == nil then {fname} = {default} end")
            else:
                default = self._zero_value(f.typ)
                self._line(f"if {fname} == nil then {fname} = {default} end")
            self._line(f"self.{fname} = {fname}")
        self._line("return self")
        self.indent -= 1
        self._line("end")

    def _emit_function(self, func: Function) -> None:
        saved_hoisted = self._hoisted_vars
        # Collect all variables and pre-declare them at function start
        all_vars = self._collect_assigned_vars(func.body)
        param_names = {p.name for p in func.params}
        local_vars = all_vars - param_names - {"_"}  # Exclude params and _
        self._hoisted_vars = set(local_vars)  # Mark all as already declared
        params = self._params(func.params)
        self._line(f"function {_safe_name(func.name)}({params})")
        self.indent += 1
        if func.doc:
            self._line(f"-- {func.doc}")
        # Emit hoisted locals at function start
        if local_vars:
            self._line(f"local {', '.join(_safe_name(v) for v in sorted(local_vars))}")
        if _is_empty_body(func.body):
            self._line("-- empty function")
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("end")
        self._hoisted_vars = saved_hoisted

    def _emit_method(self, func: Function, struct_name: str) -> None:
        saved_hoisted = self._hoisted_vars
        # Collect all variables and pre-declare them at function start
        all_vars = self._collect_assigned_vars(func.body)
        param_names = {p.name for p in func.params}
        if func.receiver:
            param_names.add(func.receiver.name)
        local_vars = all_vars - param_names - {"_"}  # Exclude params, receiver, and _
        self._hoisted_vars = set(local_vars)  # Mark all as already declared
        params = self._params(func.params)
        self._line(f"function {struct_name}:{_safe_name(func.name)}({params})")
        self.indent += 1
        if func.doc:
            self._line(f"-- {func.doc}")
        if func.receiver:
            self.receiver_name = func.receiver.name
        # Emit hoisted locals at function start
        if local_vars:
            self._line(f"local {', '.join(_safe_name(v) for v in sorted(local_vars))}")
        if _is_empty_body(func.body):
            self._line("-- empty method")
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.receiver_name = None
        self.indent -= 1
        self._line("end")
        self._hoisted_vars = saved_hoisted

    def _params(self, params: list[Param]) -> str:
        parts = []
        for p in params:
            parts.append(_safe_name(p.name))
        return ", ".join(parts)

    def _emit_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDecl(name=name, value=value):
                safe = _safe_name(name)
                if value is not None:
                    val = self._expr(value)
                    self._line(f"{safe} = {val}")
            case Assign(target=target, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                self._line(f"{lv} = {val}")
            case TupleAssign(targets=targets, value=value):
                lvalues = ", ".join(self._lvalue(t) for t in targets)
                val = self._expr(value)
                self._line(f"{lvalues} = table.unpack({val})")
            case OpAssign(target=target, op=op, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                # String concatenation: += on strings becomes .. in Lua
                if op == "+" and self._is_string_type(value.typ):
                    self._line(f"{lv} = {lv} .. {val}")
                else:
                    lua_op = _op_assign_op(op)
                    self._line(f"{lv} = {lv} {lua_op} {val}")
            case NoOp():
                pass
            case ExprStmt(expr=expr):
                e = self._expr(expr)
                # Prefix with ; if expr starts with ( to prevent Lua parsing ambiguity
                if e.startswith("("):
                    self._line(";" + e)
                else:
                    self._line(e)
            case Return(value=value):
                if value is not None:
                    self._line(f"return {self._expr(value)}")
                else:
                    self._line("return")
            case If(
                cond=cond,
                then_body=then_body,
                else_body=else_body,
                init=init,
            ):
                if init is not None:
                    self._emit_stmt(init)
                self._line(f"if {self._expr(cond)} then")
                self.indent += 1
                if _is_empty_body(then_body):
                    self._line("-- empty then")
                for s in then_body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._emit_else_body(else_body)
                self._line("end")
            case TypeSwitch(
                expr=expr,
                binding=binding,
                cases=cases,
                default=default,
            ):
                self._emit_type_switch(expr, binding, cases, default)
            case Match(expr=expr, cases=cases, default=default):
                self._emit_match(expr, cases, default)
            case ForRange(
                index=index,
                value=value,
                iterable=iterable,
                body=body,
            ):
                self._emit_for_range(index, value, iterable, body)
            case ForClassic(init=init, cond=cond, post=post, body=body):
                self._emit_for_classic(init, cond, post, body)
            case While(cond=cond, body=body):
                has_continue = self._body_has_direct_continue(body)
                self._line(f"while {self._expr(cond)} do")
                self.indent += 1
                if _is_empty_body(body):
                    self._line("-- empty while")
                for s in body:
                    self._emit_stmt(s)
                if has_continue:
                    self._line("::continue::")
                self.indent -= 1
                self._line("end")
            case Break(label=_):
                self._line("break")
            case Continue(label=_):
                # Lua 5.1 doesn't have continue - use goto in 5.2+ or repeat/until pattern
                # We use goto for simplicity (requires Lua 5.2+)
                self._line("goto continue")
            case Block(body=body):
                # Don't emit do/end - Lua's do/end creates a scope boundary
                # but IR Block is just grouping, not a scope boundary
                for s in body:
                    self._emit_stmt(s)
            case TryCatch(
                body=body,
                catch_var=catch_var,
                catch_type=catch_type,
                catch_body=catch_body,
                reraise=reraise,
            ):
                self._emit_try_catch(body, catch_var, catch_type, catch_body, reraise)
            case Raise(
                error_type=error_type,
                message=message,
                pos=pos,
                reraise_var=reraise_var,
            ):
                if reraise_var:
                    self._line(f"error({reraise_var})")
                else:
                    msg = self._expr(message)
                    if pos is not None:
                        pos_expr = self._expr(pos)
                        self._line(f"error({{{error_type} = true, message = {msg}, pos = {pos_expr}}})")
                    else:
                        self._line(f"error({{{error_type} = true, message = {msg}}})")
            case SoftFail():
                self._line("return nil")
            case Print(value=value, newline=newline, stderr=stderr):
                val = self._expr(value)
                if stderr:
                    self._line(f"io.stderr:write({val})")
                    if newline:
                        self._line("io.stderr:write('\\n')")
                elif newline:
                    self._line(f"print({val})")
                else:
                    self._line(f"io.write({val})")
            case _:
                raise NotImplementedError("Unknown statement")

    def _emit_type_switch(
        self, expr: Expr, binding: str, cases: list[TypeCase], default: list[Stmt]
    ) -> None:
        var = self._expr(expr)
        safe_binding = _safe_name(binding)
        # Lua doesn't have type switch, use if/elseif chain with type checks
        for i, case in enumerate(cases):
            keyword = "if" if i == 0 else "elseif"
            type_check = self._type_check(var, case.typ)
            self._line(f"{keyword} {type_check} then")
            self.indent += 1
            self._line(f"local {safe_binding} = {var}")
            if _is_empty_body(case.body):
                self._line("-- empty case")
            for s in case.body:
                self._emit_stmt(s)
            self.indent -= 1
        if default:
            self._line("else")
            self.indent += 1
            for s in default:
                self._emit_stmt(s)
            self.indent -= 1
        self._line("end")

    def _type_check(self, var: str, typ: Type) -> str:
        """Generate type check expression."""
        match typ:
            case Primitive(kind="string"):
                return f"type({var}) == 'string'"
            case Primitive(kind="int") | Primitive(kind="float") | Primitive(
                kind="byte"
            ):
                return f"type({var}) == 'number'"
            case Primitive(kind="bool"):
                return f"type({var}) == 'boolean'"
            case StructRef(name=name):
                type_name = _safe_type_name(name)
                return f"(type({var}) == 'table' and getmetatable({var}) == {type_name})"
            case InterfaceRef(name=name):
                type_name = _safe_type_name(name)
                return f"(type({var}) == 'table' and getmetatable({var}) == {type_name})"
            case Pointer(target=target):
                return self._type_check(var, target)
            case Optional(inner=inner):
                return self._type_check(var, inner)
            case Union(name=name):
                type_name = _safe_type_name(name)
                return f"(type({var}) == 'table' and getmetatable({var}) == {type_name})"
            case Struct(name=name):
                type_name = _safe_type_name(name)
                return f"(type({var}) == 'table' and getmetatable({var}) == {type_name})"
            case _:
                return f"type({var}) == 'table'"

    def _emit_match(
        self, expr: Expr, cases: list[MatchCase], default: list[Stmt]
    ) -> None:
        var = self._expr(expr)
        # Use local variable to avoid re-evaluating expression
        self._line(f"local _match_val = {var}")
        for i, case in enumerate(cases):
            keyword = "if" if i == 0 else "elseif"
            patterns = " or ".join(
                f"_match_val == {self._expr(p)}" for p in case.patterns
            )
            self._line(f"{keyword} {patterns} then")
            self.indent += 1
            if _is_empty_body(case.body):
                self._line("-- empty case")
            for s in case.body:
                self._emit_stmt(s)
            self.indent -= 1
        if default:
            self._line("else")
            self.indent += 1
            for s in default:
                self._emit_stmt(s)
            self.indent -= 1
        self._line("end")

    def _emit_for_range(
        self,
        index: str | None,
        value: str | None,
        iterable: Expr,
        body: list[Stmt],
    ) -> None:
        # Unwrap enumerate() call if present
        actual_iterable = iterable
        if isinstance(iterable, Call) and iterable.func == "enumerate":
            actual_iterable = iterable.args[0]
        iter_expr = self._expr(actual_iterable)
        iter_type = actual_iterable.typ
        is_string = isinstance(iter_type, Primitive) and iter_type.kind == "string"
        has_continue = self._body_has_direct_continue(body)
        idx = _safe_name(index) if index else "_"
        val = _safe_name(value) if value else "_"
        if is_string:
            # Iterate over string characters
            self._line(f"for {idx} = 1, #{iter_expr} do")
            self.indent += 1
            if value:
                self._line(f"local {val} = string.sub({iter_expr}, {idx}, {idx})")
            if index:
                # Convert to 0-based index
                self._line(f"{idx} = {idx} - 1")
        else:
            # Use ipairs for arrays/slices
            self._line(f"for {idx}, {val} in ipairs({iter_expr}) do")
            self.indent += 1
            if index:
                # Convert to 0-based index
                self._line(f"{idx} = {idx} - 1")
        if _is_empty_body(body):
            self._line("-- empty for")
        for s in body:
            self._emit_stmt(s)
        if has_continue:
            self._line("::continue::")
        self.indent -= 1
        self._line("end")

    def _emit_for_classic(
        self,
        init: Stmt | None,
        cond: Expr | None,
        post: Stmt | None,
        body: list[Stmt],
    ) -> None:
        # Try to detect simple range pattern: for i = 0; i < n; i++
        if (range_info := _extract_range_pattern(init, cond, post)) is not None:
            var_name, limit_expr = range_info
            limit = self._expr(limit_expr)
            has_continue = self._body_has_direct_continue(body)
            self._line(f"for {_safe_name(var_name)} = 0, {limit} - 1 do")
            self.indent += 1
            if _is_empty_body(body):
                self._line("-- empty for")
            for s in body:
                self._emit_stmt(s)
            if has_continue:
                self._line("::continue::")
            self.indent -= 1
            self._line("end")
            return
        # General case: use while loop
        if init is not None:
            self._emit_stmt(init)
        cond_str = self._expr(cond) if cond else "true"
        has_continue = self._body_has_direct_continue(body)
        self._line(f"while {cond_str} do")
        self.indent += 1
        if _is_empty_body(body) and post is None:
            self._line("-- empty while")
        for s in body:
            self._emit_stmt(s)
        if has_continue:
            self._line("::continue::")
        if post is not None:
            self._emit_stmt(post)
        self.indent -= 1
        self._line("end")

    def _emit_try_catch(
        self,
        body: list[Stmt],
        catch_var: str | None,
        catch_type: Type | None,
        catch_body: list[Stmt],
        reraise: bool,
    ) -> None:
        var = _safe_name(catch_var) if catch_var else "_err"
        has_return = self._body_has_return(body)
        self._line("local _ok, _err = pcall(function()")
        self.indent += 1
        if _is_empty_body(body):
            self._line("-- empty try")
        for s in body:
            self._emit_stmt(s)
        self.indent -= 1
        self._line("end)")
        self._line("if not _ok then")
        self.indent += 1
        if catch_var:
            self._line(f"local {var} = _err")
        if _is_empty_body(catch_body) and not reraise:
            self._line("-- empty catch")
        for s in catch_body:
            self._emit_stmt(s)
        if reraise:
            self._line("error(_err)")
        self.indent -= 1
        self._line("end")
        # If try body has return statements, propagate the return value on success
        if has_return:
            self._line("if _ok then return _err end")

    def _emit_else_body(self, else_body: list[Stmt]) -> None:
        """Emit else body, converting single-If else to elseif chains."""
        if _is_empty_body(else_body):
            return
        if len(else_body) == 1 and isinstance(else_body[0], If):
            elif_stmt = else_body[0]
            if elif_stmt.init is not None:
                self._line("else")
                self.indent += 1
                self._emit_stmt(elif_stmt.init)
                self._line(f"if {self._expr(elif_stmt.cond)} then")
                self.indent += 1
                if _is_empty_body(elif_stmt.then_body):
                    self._line("-- empty then")
                for s in elif_stmt.then_body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._emit_else_body(elif_stmt.else_body)
                self._line("end")
                self.indent -= 1
            else:
                self._line(f"elseif {self._expr(elif_stmt.cond)} then")
                self.indent += 1
                if _is_empty_body(elif_stmt.then_body):
                    self._line("-- empty then")
                for s in elif_stmt.then_body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._emit_else_body(elif_stmt.else_body)
        else:
            self._line("else")
            self.indent += 1
            for s in else_body:
                self._emit_stmt(s)
            self.indent -= 1

    def _expr(self, expr: Expr) -> str:
        match expr:
            case IntLit(value=value):
                return str(value)
            case FloatLit(value=value):
                return str(value)
            case StringLit(value=value):
                return _string_literal(value)
            case CharLit(value=value):
                return _string_literal(value)
            case BoolLit(value=value):
                return "true" if value else "false"
            case NilLit():
                return "nil"
            case Var(name=name):
                if name == self.receiver_name:
                    return "self"
                if _is_constant(name):
                    return to_screaming_snake(name)
                if "_" in name and name[0].isupper():
                    return to_screaming_snake(name)
                return _safe_name(name)
            case FieldAccess(obj=obj, field=field):
                if field.startswith("F") and field[1:].isdigit():
                    # Tuple field access - adjust for 1-based indexing
                    idx = int(field[1:]) + 1
                    return f"{self._expr(obj)}[{idx}]"
                return f"{self._expr(obj)}.{_safe_name(field)}"
            case FuncRef(name=name, obj=obj):
                if obj is not None:
                    return f"function(...) return {self._expr(obj)}:{_safe_name(name)}(...) end"
                return _safe_name(name)
            case Index(obj=obj, index=index):
                obj_str = self._expr(obj)
                idx_str = self._expr(index)
                obj_type = obj.typ
                # Lua is 1-based, so add 1 to index
                if isinstance(obj_type, Primitive) and obj_type.kind == "string":
                    # String indexing returns character
                    return f"string.sub({obj_str}, {idx_str} + 1, {idx_str} + 1)"
                if isinstance(obj_type, (Slice, Array)):
                    return f"{obj_str}[{idx_str} + 1]"
                # Map access doesn't need adjustment
                return f"{obj_str}[{idx_str}]"
            case SliceExpr(obj=obj, low=low, high=high):
                return self._slice_expr(obj, low, high)
            case ParseInt(string=s, base=b):
                base_val = self._expr(b)
                if base_val == "10":
                    return f"tonumber({self._expr(s)})"
                return f"tonumber({self._expr(s)}, {base_val})"
            case IntToStr(value=v):
                return f"tostring({self._expr(v)})"
            case CharClassify(kind=kind, char=char):
                char_expr = self._expr(char)
                pattern_map = {
                    "digit": "%d",
                    "alpha": "%a",
                    "alnum": "%w",
                    "space": "%s",
                    "upper": "%u",
                    "lower": "%l",
                }
                pattern = pattern_map[kind]
                # Python's isdigit/isalpha/etc check ALL chars, so use + not single char
                return f"(string.match({char_expr}, '^{pattern}+$') ~= nil)"
            case TrimChars(string=s, chars=chars, mode=mode):
                s_str = self._expr(s)
                chars_str = self._expr(chars)
                if mode == "left":
                    return f"(string.gsub({s_str}, '^[' .. {chars_str} .. ']+', ''))"
                elif mode == "right":
                    return f"(string.gsub({s_str}, '[' .. {chars_str} .. ']+$', ''))"
                else:
                    return f"(string.gsub((string.gsub({s_str}, '^[' .. {chars_str} .. ']+', '')), '[' .. {chars_str} .. ']+$', ''))"
            case Call(func="_intPtr", args=[arg]):
                val = self._expr(arg)
                return f"(({val}) == -1 and nil or ({val}))"
            case Call(func=func, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                if func == "range":
                    return f"_range({args_str})"
                return f"{_safe_name(func)}({args_str})"
            case MethodCall(
                obj=obj, method=method, args=args, receiver_type=receiver_type
            ):
                return self._method_call(obj, method, args, receiver_type)
            case StaticCall(on_type=on_type, method=method, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                type_name = self._type_name_for_check(on_type)
                return f"{type_name}.{_safe_name(method)}({args_str})"
            case Truthy(expr=e):
                inner_type = e.typ
                expr_str = self._expr(e)
                # In Lua, only nil and false are falsy
                if isinstance(inner_type, (Slice, Map)):
                    return f"(#({expr_str}) > 0)"
                if isinstance(inner_type, Set):
                    return f"(next({expr_str}) ~= nil)"
                if isinstance(inner_type, Optional):
                    inner = inner_type.inner
                    if isinstance(inner, (Slice, Map)):
                        return f"({expr_str} ~= nil and #({expr_str}) > 0)"
                    if isinstance(inner, Set):
                        return f"({expr_str} ~= nil and next({expr_str}) ~= nil)"
                    return f"({expr_str} ~= nil)"
                if isinstance(inner_type, Pointer):
                    return f"({expr_str} ~= nil)"
                if inner_type == Primitive(kind="string"):
                    return f"({expr_str} ~= nil and #({expr_str}) > 0)"
                if inner_type == Primitive(kind="int"):
                    return f"({expr_str} ~= 0)"
                if isinstance(e, Len):
                    return f"({expr_str} > 0)"
                if isinstance(e, BinaryOp) and e.typ == Primitive(kind="int"):
                    return f"(({expr_str}) ~= 0)"
                # Default: check not nil and not false
                return f"({expr_str} ~= nil and {expr_str} ~= false)"
            case BinaryOp(op=op, left=left, right=right):
                if op == "in":
                    return self._containment_check(left, right, negated=False)
                if op == "not in":
                    return self._containment_check(left, right, negated=True)
                # String concatenation: + on strings becomes .. in Lua
                if op == "+" and (
                    self._is_string_type(left.typ) or self._is_string_type(right.typ)
                ):
                    left_str = self._maybe_paren(left, "..", is_left=True)
                    right_str = self._maybe_paren(right, "..", is_left=False)
                    return f"{left_str} .. {right_str}"
                lua_op = _binary_op(op)
                left_str = self._maybe_paren(left, op, is_left=True)
                right_str = self._maybe_paren(right, op, is_left=False)
                return f"{left_str} {lua_op} {right_str}"
            case UnaryOp(op=op, operand=operand):
                lua_op = _unary_op(op)
                if op == "!" and isinstance(operand, BinaryOp):
                    return f"{lua_op}({self._expr(operand)})"
                if op == "!" and isinstance(operand, Truthy):
                    inner = operand.expr
                    if inner.typ == Primitive(kind="int"):
                        inner_str = self._expr(inner)
                        if isinstance(inner, BinaryOp):
                            return f"(({inner_str}) == 0)"
                        return f"({inner_str} == 0)"
                return f"{lua_op}{self._expr(operand)}"
            case Ternary(cond=cond, then_expr=then_expr, else_expr=else_expr):
                # Lua ternary: cond and a or b (fails if a is false/nil)
                # For safety, use function wrapper
                cond_str = self._expr(cond)
                then_str = self._expr(then_expr)
                else_str = self._expr(else_expr)
                # Check if then_expr could be falsy (boolean false or nil)
                if self._could_be_falsy(then_expr):
                    return f"(function() if {cond_str} then return {then_str} else return {else_str} end end)()"
                return f"({cond_str} and {then_str} or {else_str})"
            case Cast(expr=inner, to_type=to_type):
                if to_type == Primitive(kind="string") and isinstance(inner.typ, Slice):
                    # byte slice to string
                    return f"_bytes_to_string({self._expr(inner)})"
                if to_type == Primitive(kind="string") and inner.typ == Primitive(
                    kind="rune"
                ):
                    # Use utf8.char for Unicode codepoints (Lua 5.3+)
                    return f"utf8.char({self._expr(inner)})"
                if isinstance(to_type, Slice) and to_type.element == Primitive(
                    kind="byte"
                ):
                    # string to byte slice
                    return f"({{string.byte({self._expr(inner)}, 1, -1)}})"
                if to_type == Primitive(kind="int") and inner.typ in (
                    Primitive(kind="string"),
                    Primitive(kind="byte"),
                    Primitive(kind="rune"),
                ):
                    return f"string.byte({self._expr(inner)})"
                return self._expr(inner)
            case TypeAssert(expr=inner):
                return self._expr(inner)
            case IsType(expr=inner, tested_type=tested_type):
                inner_str = self._expr(inner)
                return self._type_check(inner_str, tested_type)
            case IsNil(expr=inner, negated=negated):
                if negated:
                    return f"({self._expr(inner)} ~= nil)"
                return f"({self._expr(inner)} == nil)"
            case Len(expr=inner):
                return f"#{self._expr(inner)}"
            case MakeSlice(element_type=element_type, length=length):
                if length is not None:
                    zero = self._zero_value(element_type)
                    return f"(function() local t = {{}}; for i = 1, {self._expr(length)} do t[i] = {zero} end; return t end)()"
                return "{}"
            case MakeMap():
                return "{}"
            case SliceLit(elements=elements):
                elems = ", ".join(self._expr(e) for e in elements)
                return f"{{{elems}}}"
            case MapLit(entries=entries):
                if not entries:
                    return "{}"
                pairs = ", ".join(
                    f"[{self._expr(k)}] = {self._expr(v)}" for k, v in entries
                )
                return f"{{{pairs}}}"
            case SetLit(elements=elements):
                if not elements:
                    return "{}"
                pairs = ", ".join(f"[{self._expr(e)}] = true" for e in elements)
                return f"{{{pairs}}}"
            case StructLit(struct_name=struct_name, fields=fields):
                type_name = _safe_type_name(struct_name)
                # Get field order from struct definition
                field_order = self.struct_fields.get(struct_name, [])
                args_list = []
                for fname in field_order:
                    if fname in fields:
                        args_list.append(self._expr(fields[fname]))
                    else:
                        args_list.append("nil")
                args = ", ".join(args_list)
                return f"{type_name}:new({args})"
            case TupleLit(elements=elements):
                elems = ", ".join(self._expr(e) for e in elements)
                return f"{{{elems}}}"
            case StringConcat(parts=parts):
                return " .. ".join(self._expr(p) for p in parts)
            case StringFormat(template=template, args=args):
                return self._format_string(template, args)
            case SliceConvert(source=source):
                return self._expr(source)
            case _:
                raise NotImplementedError("Unknown expression")

    def _could_be_falsy(self, expr: Expr) -> bool:
        """Check if expression could evaluate to false or nil."""
        if isinstance(expr, BoolLit) and not expr.value:
            return True
        if isinstance(expr, NilLit):
            return True
        if isinstance(expr.typ, Optional):
            return True
        if isinstance(expr.typ, Primitive) and expr.typ.kind == "bool":
            return True
        return False

    def _is_string_type(self, typ: Type) -> bool:
        """Check if type is a string type."""
        if isinstance(typ, Primitive) and typ.kind == "string":
            return True
        if isinstance(typ, Optional):
            return self._is_string_type(typ.inner)
        return False

    def _containment_check(self, item: Expr, container: Expr, negated: bool) -> str:
        """Generate containment check: `x in y` or `x not in y`."""
        item_str = self._expr(item)
        container_str = self._expr(container)
        container_type = container.typ
        neg = "not " if negated else ""
        if isinstance(container_type, Set):
            return f"{neg}_set_contains({container_str}, {item_str})"
        if isinstance(container_type, Map):
            return f"({neg}({container_str}[{item_str}] ~= nil))"
        if isinstance(container_type, Primitive) and container_type.kind == "string":
            return f"({neg}(string.find({container_str}, {item_str}, 1, true) ~= nil))"
        # Array/Slice - need to search
        return f"({neg}(function() for _, v in ipairs({container_str}) do if v == {item_str} then return true end end return false end)())"

    def _method_call(
        self, obj: Expr, method: str, args: list[Expr], receiver_type: Type
    ) -> str:
        """Handle method calls with proper Lua idioms."""
        obj_str = self._expr(obj)
        args_str = ", ".join(self._expr(a) for a in args)
        # Unwrap Pointer and Optional types
        inner_type = receiver_type
        if isinstance(inner_type, Pointer):
            inner_type = inner_type.target
        if isinstance(inner_type, Optional):
            inner_type = inner_type.inner
        # String methods
        if isinstance(inner_type, Primitive) and inner_type.kind == "string":
            if method == "join" and len(args) == 1:
                # "sep".join(arr) -> table.concat(arr, sep)
                return f"table.concat({self._expr(args[0])}, {obj_str})"
            if method == "split" and len(args) == 1:
                return f"_string_split({obj_str}, {self._expr(args[0])})"
            if method == "lower":
                return f"string.lower({obj_str})"
            if method == "upper":
                return f"string.upper({obj_str})"
            if method == "find":
                if len(args) == 1:
                    return f"_string_find({obj_str}, {self._expr(args[0])})"
                return f"_string_find({obj_str}, {self._expr(args[0])}, {self._expr(args[1])})"
            if method == "rfind":
                return f"_string_rfind({obj_str}, {self._expr(args[0])})"
            if method == "startswith":
                prefix = self._expr(args[0])
                if len(args) == 2:
                    pos = self._expr(args[1])
                    return f"(string.sub({obj_str}, {pos} + 1, {pos} + #{prefix}) == {prefix})"
                return f"(string.sub({obj_str}, 1, #{prefix}) == {prefix})"
            if method == "endswith":
                arg = args[0]
                # Handle tuple argument: s.endswith(("a", "b")) -> s ends with a or b
                if isinstance(arg, TupleLit):
                    checks = []
                    for elem in arg.elements:
                        suffix = self._expr(elem)
                        checks.append(f"string.sub({obj_str}, -#{suffix}) == {suffix}")
                    return f"({' or '.join(checks)})"
                suffix = self._expr(arg)
                return f"(string.sub({obj_str}, -#{suffix}) == {suffix})"
            if method == "replace":
                old = self._expr(args[0])
                new = self._expr(args[1])
                # Use gsub with plain pattern
                return f"(string.gsub({obj_str}, {old}, {new}))"
        # Slice methods
        if isinstance(inner_type, Slice):
            if method == "append":
                return f"(function() table.insert({obj_str}, {args_str}); return {obj_str} end)()"
            if method == "extend":
                return f"(function() for _, v in ipairs({self._expr(args[0])}) do table.insert({obj_str}, v) end; return {obj_str} end)()"
            if method == "copy":
                return f"(function() local t = {{}}; for i, v in ipairs({obj_str}) do t[i] = v end; return t end)()"
            if method == "pop":
                if len(args) == 1 and isinstance(args[0], IntLit) and args[0].value == 0:
                    return f"table.remove({obj_str}, 1)"
                if len(args) == 0:
                    return f"table.remove({obj_str})"
                return f"table.remove({obj_str}, {self._expr(args[0])} + 1)"
        # Map methods
        if isinstance(inner_type, Map):
            if method == "get":
                key = self._expr(args[0])
                if len(args) == 2:
                    default = self._expr(args[1])
                    return f"_map_get({obj_str}, {key}, {default})"
                return f"{obj_str}[{key}]"
        # Set methods
        if isinstance(inner_type, Set):
            if method == "add":
                return f"_set_add({obj_str}, {args_str})"
            if method == "contains":
                return f"_set_contains({obj_str}, {args_str})"
        # Fallback for string methods when type isn't known
        if method == "endswith" and len(args) == 1:
            arg = args[0]
            # Handle tuple argument: s.endswith(("a", "b")) -> s ends with a or b
            if isinstance(arg, TupleLit):
                checks = []
                for elem in arg.elements:
                    suffix = self._expr(elem)
                    checks.append(f"string.sub({obj_str}, -#{suffix}) == {suffix}")
                return f"({' or '.join(checks)})"
            suffix = self._expr(arg)
            return f"(string.sub({obj_str}, -#{suffix}) == {suffix})"
        if method == "startswith" and len(args) >= 1:
            prefix = self._expr(args[0])
            if len(args) == 2:
                pos = self._expr(args[1])
                return f"(string.sub({obj_str}, {pos} + 1, {pos} + #{prefix}) == {prefix})"
            return f"(string.sub({obj_str}, 1, #{prefix}) == {prefix})"
        if method == "lower":
            return f"string.lower({obj_str})"
        if method == "upper":
            return f"string.upper({obj_str})"
        if method == "split" and len(args) == 1:
            return f"_string_split({obj_str}, {self._expr(args[0])})"
        if method == "isdigit":
            return f"(string.match({obj_str}, '^%d+$') ~= nil)"
        if method == "isspace":
            return f"(string.match({obj_str}, '^%s+$') ~= nil)"
        if method == "isalnum":
            return f"(string.match({obj_str}, '^%w+$') ~= nil)"
        if method == "rstrip":
            if len(args) == 0:
                return f"(string.gsub({obj_str}, '%s+$', ''))"
            chars = self._expr(args[0])
            return f"(string.gsub({obj_str}, '[' .. {chars} .. ']+$', ''))"
        if method == "lstrip":
            if len(args) == 0:
                return f"(string.gsub({obj_str}, '^%s+', ''))"
            chars = self._expr(args[0])
            return f"(string.gsub({obj_str}, '^[' .. {chars} .. ']+', ''))"
        if method == "strip":
            if len(args) == 0:
                return f"(string.gsub((string.gsub({obj_str}, '^%s+', '')), '%s+$', ''))"
            chars = self._expr(args[0])
            return f"(string.gsub((string.gsub({obj_str}, '^[' .. {chars} .. ']+', '')), '[' .. {chars} .. ']+$', ''))"
        if method == "replace" and len(args) == 2:
            old = self._expr(args[0])
            new = self._expr(args[1])
            return f"(string.gsub({obj_str}, {old}, {new}))"
        if method == "find" and len(args) >= 1:
            if len(args) == 1:
                return f"_string_find({obj_str}, {self._expr(args[0])})"
            return f"_string_find({obj_str}, {self._expr(args[0])}, {self._expr(args[1])})"
        if method == "rfind" and len(args) >= 1:
            return f"_string_rfind({obj_str}, {self._expr(args[0])})"
        if method == "append" and len(args) == 1:
            return f"(function() table.insert({obj_str}, {args_str}); return {obj_str} end)()"
        if method == "join" and len(args) == 1:
            # "sep".join(arr) -> table.concat(arr, sep)
            return f"table.concat({self._expr(args[0])}, {obj_str})"
        # Default: method call syntax
        if isinstance(obj, (BinaryOp, UnaryOp, Ternary)):
            obj_str = f"({obj_str})"
        if args_str:
            return f"{obj_str}:{_safe_name(method)}({args_str})"
        return f"{obj_str}:{_safe_name(method)}()"

    def _slice_expr(self, obj: Expr, low: Expr | None, high: Expr | None) -> str:
        obj_str = self._expr(obj)
        obj_type = obj.typ
        is_string = isinstance(obj_type, Primitive) and obj_type.kind == "string"
        # Adjust for 1-based indexing
        if low:
            low_str = f"({self._expr(low)}) + 1"
        else:
            low_str = "1"
        if high:
            high_str = self._expr(high)
        else:
            high_str = f"#{obj_str}"
        if is_string:
            return f"string.sub({obj_str}, {low_str}, {high_str})"
        return f"_table_slice({obj_str}, {low_str}, {high_str})"

    def _format_string(self, template: str, args: list[Expr]) -> str:
        # Use string.format with %s placeholders
        result = template
        format_parts = []
        arg_idx = 0
        # Handle {i} placeholders
        for i in range(len(args)):
            placeholder = f"{{{i}}}"
            if placeholder in result:
                result = result.replace(placeholder, "%s", 1)
                format_parts.append(self._expr(args[i]))
                arg_idx = i + 1
        # Handle %v placeholders
        while "%v" in result:
            result = result.replace("%v", "%s", 1)
            if arg_idx < len(args):
                format_parts.append(self._expr(args[arg_idx]))
                arg_idx += 1
        # Escape any remaining % signs
        result = result.replace("%", "%%").replace("%%s", "%s")
        # Escape special characters for Lua string
        result = result.replace("\\", "\\\\")
        result = result.replace('"', '\\"')
        result = result.replace("\n", "\\n")
        result = result.replace("\t", "\\t")
        result = result.replace("\r", "\\r")
        if format_parts:
            args_str = ", ".join(format_parts)
            return f'string.format("{result}", {args_str})'
        return f'"{result}"'

    def _lvalue(self, lv: LValue) -> str:
        match lv:
            case VarLV(name=name):
                if name == self.receiver_name:
                    return "self"
                return _safe_name(name)
            case FieldLV(obj=obj, field=field):
                return f"{self._expr(obj)}.{_safe_name(field)}"
            case IndexLV(obj=obj, index=index):
                obj_str = self._expr(obj)
                idx_str = self._expr(index)
                obj_type = obj.typ
                # Adjust for 1-based indexing on arrays/slices
                if isinstance(obj_type, (Slice, Array)):
                    return f"{obj_str}[{idx_str} + 1]"
                if isinstance(obj_type, Primitive) and obj_type.kind == "string":
                    return f"{obj_str}[{idx_str} + 1]"
                return f"{obj_str}[{idx_str}]"
            case DerefLV(ptr=ptr):
                return self._expr(ptr)
            case _:
                raise NotImplementedError("Unknown lvalue")

    def _type_name_for_check(self, typ: Type) -> str:
        match typ:
            case StructRef(name=name):
                return _safe_type_name(name)
            case InterfaceRef(name=name):
                return _safe_type_name(name)
            case Primitive(kind="string"):
                return "string"
            case Primitive(kind="int"):
                return "number"
            case Primitive(kind="float"):
                return "number"
            case Primitive(kind="bool"):
                return "boolean"
            case _:
                return "table"

    def _zero_value(self, typ: Type) -> str:
        match typ:
            case Primitive(kind="int") | Primitive(kind="byte"):
                return "0"
            case Primitive(kind="float"):
                return "0.0"
            case Primitive(kind="bool"):
                return "false"
            case Primitive(kind="string"):
                return '""'
            case Slice():
                return "{}"
            case Map():
                return "{}"
            case Set():
                return "{}"
            case _:
                return "nil"

    def _maybe_paren(self, expr: Expr, parent_op: str, is_left: bool) -> str:
        """Wrap expression in parens if needed for operator precedence."""
        match expr:
            case BinaryOp(op=child_op):
                if _needs_parens(child_op, parent_op, is_left):
                    return f"({self._expr(expr)})"
            case Ternary():
                return f"({self._expr(expr)})"
        return self._expr(expr)


def _binary_op(op: str) -> str:
    match op:
        case "and" | "&&":
            return "and"
        case "or" | "||":
            return "or"
        case "!=":
            return "~="
        case "//":
            return "//"  # Lua 5.3+ has floor division
        case "**":
            return "^"  # Lua exponentiation
        case _:
            return op


def _unary_op(op: str) -> str:
    match op:
        case "!":
            return "not "
        case "&" | "*":
            return ""
        case _:
            return op


def _op_assign_op(op: str) -> str:
    """Convert compound assignment operator to binary operator."""
    return op


_PRECEDENCE = {
    "or": 1,
    "||": 1,
    "and": 2,
    "&&": 2,
    "==": 3,
    "~=": 3,
    "!=": 3,
    "<": 3,
    ">": 3,
    "<=": 3,
    ">=": 3,
    "|": 4,
    "~": 5,  # bitwise xor in Lua is ~
    "&": 6,
    "<<": 7,
    ">>": 7,
    "..": 8,
    "+": 9,
    "-": 9,
    "*": 10,
    "/": 10,
    "//": 10,
    "%": 10,
    "^": 11,  # exponentiation (right-associative)
    "**": 11,  # Python exponentiation, maps to ^
}


def _needs_parens(child_op: str, parent_op: str, is_left: bool) -> bool:
    """Determine if a child binary op needs parens inside a parent binary op."""
    child_prec = _PRECEDENCE.get(child_op, 0)
    parent_prec = _PRECEDENCE.get(parent_op, 0)
    if child_prec < parent_prec:
        return True
    if child_prec == parent_prec and not is_left:
        return child_op in ("==", "~=", "<", ">", "<=", ">=")
    return False


def _escape_lua_string(value: str) -> str:
    """Escape a string for Lua (uses \\u{XXXX} syntax for control chars)."""
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
        .replace("\r", "\\r")
        .replace("\x01", "\\u{0001}")
        .replace("\x7f", "\\u{007f}")
    )


def _string_literal(value: str) -> str:
    return f'"{_escape_lua_string(value)}"'


def _extract_range_pattern(
    init: Stmt | None, cond: Expr | None, post: Stmt | None
) -> tuple[str, Expr] | None:
    """Extract simple range iteration pattern: for i := 0; i < len(x); i++."""
    if init is None or cond is None or post is None:
        return None
    if not isinstance(init, VarDecl):
        return None
    if not isinstance(init.value, IntLit) or init.value.value != 0:
        return None
    var_name = init.name
    if not isinstance(cond, BinaryOp) or cond.op != "<":
        return None
    if not isinstance(cond.left, Var) or cond.left.name != var_name:
        return None
    limit_expr = cond.right
    if isinstance(post, OpAssign):
        if post.op != "+" or not isinstance(post.target, VarLV):
            return None
        if post.target.name != var_name:
            return None
        if not isinstance(post.value, IntLit) or post.value.value != 1:
            return None
    elif isinstance(post, Assign):
        if not isinstance(post.target, VarLV) or post.target.name != var_name:
            return None
        if not isinstance(post.value, BinaryOp) or post.value.op != "+":
            return None
        if not isinstance(post.value.left, Var) or post.value.left.name != var_name:
            return None
        if not isinstance(post.value.right, IntLit) or post.value.right.value != 1:
            return None
    else:
        return None
    return (var_name, limit_expr)
