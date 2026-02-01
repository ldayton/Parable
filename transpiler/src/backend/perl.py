"""Perl backend: IR → Perl 5.36+ code."""

from __future__ import annotations

from src.backend.util import escape_string, to_snake
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


_PERL_RESERVED = frozenset(
    {
        "abs",
        "accept",
        "alarm",
        "and",
        "atan2",
        "bind",
        "binmode",
        "bless",
        "caller",
        "chdir",
        "chmod",
        "chomp",
        "chop",
        "chown",
        "chr",
        "chroot",
        "close",
        "closedir",
        "cmp",
        "connect",
        "continue",
        "cos",
        "crypt",
        "dbmclose",
        "dbmopen",
        "defined",
        "delete",
        "die",
        "do",
        "dump",
        "each",
        "else",
        "elsif",
        "endgrent",
        "endhostent",
        "endnetent",
        "endprotoent",
        "endpwent",
        "endservent",
        "eof",
        "eq",
        "eval",
        "exec",
        "exists",
        "exit",
        "exp",
        "fcntl",
        "fileno",
        "flock",
        "for",
        "foreach",
        "fork",
        "format",
        "formline",
        "ge",
        "getc",
        "getgrent",
        "getgrgid",
        "getgrnam",
        "gethostbyaddr",
        "gethostbyname",
        "gethostent",
        "getlogin",
        "getnetbyaddr",
        "getnetbyname",
        "getnetent",
        "getpeername",
        "getpgrp",
        "getppid",
        "getpriority",
        "getprotobyname",
        "getprotobynumber",
        "getprotoent",
        "getpwent",
        "getpwnam",
        "getpwuid",
        "getservbyname",
        "getservbyport",
        "getservent",
        "getsockname",
        "getsockopt",
        "glob",
        "gmtime",
        "goto",
        "grep",
        "gt",
        "hex",
        "if",
        "import",
        "index",
        "int",
        "ioctl",
        "join",
        "keys",
        "kill",
        "last",
        "lc",
        "lcfirst",
        "le",
        "length",
        "link",
        "listen",
        "local",
        "localtime",
        "lock",
        "log",
        "lstat",
        "lt",
        "m",
        "map",
        "mkdir",
        "msgctl",
        "msgget",
        "msgrcv",
        "msgsnd",
        "my",
        "ne",
        "next",
        "no",
        "not",
        "oct",
        "open",
        "opendir",
        "or",
        "ord",
        "our",
        "pack",
        "package",
        "pipe",
        "pop",
        "pos",
        "print",
        "printf",
        "prototype",
        "push",
        "q",
        "qq",
        "qr",
        "quotemeta",
        "qw",
        "qx",
        "rand",
        "read",
        "readdir",
        "readline",
        "readlink",
        "readpipe",
        "recv",
        "redo",
        "ref",
        "rename",
        "require",
        "reset",
        "return",
        "reverse",
        "rewinddir",
        "rindex",
        "rmdir",
        "s",
        "say",
        "scalar",
        "seek",
        "seekdir",
        "select",
        "semctl",
        "semget",
        "semop",
        "send",
        "setgrent",
        "sethostent",
        "setnetent",
        "setpgrp",
        "setpriority",
        "setprotoent",
        "setpwent",
        "setservent",
        "setsockopt",
        "shift",
        "shmctl",
        "shmget",
        "shmread",
        "shmwrite",
        "shutdown",
        "sin",
        "sleep",
        "socket",
        "socketpair",
        "sort",
        "splice",
        "split",
        "sprintf",
        "sqrt",
        "srand",
        "stat",
        "state",
        "study",
        "sub",
        "substr",
        "symlink",
        "syscall",
        "sysopen",
        "sysread",
        "sysseek",
        "system",
        "syswrite",
        "tell",
        "telldir",
        "tie",
        "tied",
        "time",
        "times",
        "tr",
        "truncate",
        "uc",
        "ucfirst",
        "umask",
        "undef",
        "unless",
        "unlink",
        "unpack",
        "unshift",
        "untie",
        "until",
        "use",
        "utime",
        "values",
        "vec",
        "wait",
        "waitpid",
        "wantarray",
        "warn",
        "when",
        "while",
        "write",
        "xor",
    }
)


def _safe_name(name: str) -> str:
    """Rename variables that conflict with Perl reserved words."""
    if name == "_":
        return "_unused"
    name = to_snake(name)
    if not name:
        return "_unused"
    if name in _PERL_RESERVED:
        return name + "_"
    return name


def _is_string_type(typ: Type) -> bool:
    """Check if type is a string type."""
    return isinstance(typ, Primitive) and typ.kind == "string"


class PerlBackend:
    """Emit Perl code from IR."""

    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self.receiver_name: str | None = None
        self.current_package: str | None = None
        self.constants: set[str] = set()
        self._hoisted_vars: set[str] = set()
        self._func_params: set[str] = set()  # Parameters with FuncType
        self.struct_fields: dict[str, list[tuple[str, Type]]] = {}  # Struct field info
        self._in_try_with_return: bool = False  # Flag for return-from-eval workaround

    def emit(self, module: Module) -> str:
        """Emit Perl code from IR Module."""
        self.indent = 0
        self.lines = []
        self.constants = set()
        self._hoisted_vars = set()
        for const in module.constants:
            self.constants.add(const.name)
        self._emit_module(module)
        return "\n".join(self.lines)

    def _line(self, text: str = "") -> None:
        if text:
            self.lines.append("    " * self.indent + text)
        else:
            self.lines.append("")

    def _emit_hoisted_vars(
        self, stmt: If | While | ForRange | ForClassic | TryCatch | Match | TypeSwitch
    ) -> None:
        """Emit declarations for hoisted variables before a control flow construct."""
        hoisted_vars = stmt.hoisted_vars
        for name, typ in hoisted_vars:
            var_name = _safe_name(name)
            default = self._zero_value(typ) if typ else "undef"
            self._line(f"my ${var_name} = {default};")
            self._hoisted_vars.add(name)

    def _collect_undeclared_assigns(self, stmts: list[Stmt]) -> set[str]:
        """Find variables that need pre-declaration at function scope.

        In Perl, declarations inside control flow blocks (if/while/for) are block-scoped,
        not visible to sibling blocks. We need to pre-declare vars that:
        1. Have is_declaration=False assignments anywhere (these are never declared)
        2. Are assigned in TupleAssign where another target is hoisted (can't mix my/non-my)
        3. Are declared inside control flow AND declared at top level (the inner hoisting
           will cause the outer declaration to skip `my`)

        We exclude vars declared ONLY at the top level (VarDecl or Assign with is_declaration=True
        not inside any control flow) since those ARE visible throughout.
        """
        # Collect top-level declarations (visible throughout function)
        top_level_declared: set[str] = set()
        for stmt in stmts:
            match stmt:
                case VarDecl(name=name):
                    top_level_declared.add(name)
                case Assign(target=VarLV(name=name)) if stmt.is_declaration:
                    top_level_declared.add(name)
                case TupleAssign(targets=targets) if stmt.is_declaration:
                    for t in targets:
                        if isinstance(t, VarLV):
                            top_level_declared.add(t.name)
        # Collect all vars that need pre-declaration
        needs_predecl: set[str] = set()
        declared_in_control_flow: set[str] = set()
        self._collect_undeclared_info(stmts, needs_predecl, declared_in_control_flow, False)
        # Vars declared both inside control flow AND at top level need pre-declaration
        # because the inner hoisting will prevent the outer `my`
        needs_predecl.update(top_level_declared & declared_in_control_flow)
        # Exclude top-level-only declarations
        return needs_predecl - (top_level_declared - declared_in_control_flow)

    def _collect_undeclared_info(
        self,
        stmts: list[Stmt],
        needs_predecl: set[str],
        declared_in_cf: set[str],
        in_control_flow: bool,
    ) -> None:
        """Collect vars needing pre-declaration recursively.

        Args:
            stmts: Statements to analyze
            needs_predecl: Set to add undeclared variable names to
            declared_in_cf: Set to add vars declared inside control flow
            in_control_flow: True if we're inside a control flow block
        """
        for stmt in stmts:
            match stmt:
                case Assign(target=VarLV(name=name)) if not stmt.is_declaration:
                    needs_predecl.add(name)
                case Assign(target=VarLV(name=name)) if stmt.is_declaration and in_control_flow:
                    declared_in_cf.add(name)
                    needs_predecl.add(name)
                case TupleAssign(targets=targets):
                    for t in targets:
                        if isinstance(t, VarLV):
                            needs_predecl.add(t.name)
                            if in_control_flow and stmt.is_declaration:
                                declared_in_cf.add(t.name)
                case If(then_body=then_body, else_body=else_body, init=init):
                    if init:
                        self._collect_undeclared_info([init], needs_predecl, declared_in_cf, True)
                    self._collect_undeclared_info(then_body, needs_predecl, declared_in_cf, True)
                    self._collect_undeclared_info(else_body, needs_predecl, declared_in_cf, True)
                case While(body=body):
                    self._collect_undeclared_info(body, needs_predecl, declared_in_cf, True)
                case ForRange(body=body):
                    self._collect_undeclared_info(body, needs_predecl, declared_in_cf, True)
                case ForClassic(body=body, init=init):
                    if init:
                        self._collect_undeclared_info([init], needs_predecl, declared_in_cf, True)
                    self._collect_undeclared_info(body, needs_predecl, declared_in_cf, True)
                case TryCatch(body=body, catch_body=catch_body):
                    self._collect_undeclared_info(body, needs_predecl, declared_in_cf, True)
                    self._collect_undeclared_info(catch_body, needs_predecl, declared_in_cf, True)
                case Match(cases=cases, default=default):
                    for case in cases:
                        self._collect_undeclared_info(case.body, needs_predecl, declared_in_cf, True)
                    self._collect_undeclared_info(default, needs_predecl, declared_in_cf, True)
                case TypeSwitch(cases=cases, default=default):
                    for case in cases:
                        self._collect_undeclared_info(case.body, needs_predecl, declared_in_cf, True)
                    self._collect_undeclared_info(default, needs_predecl, declared_in_cf, True)
                case Block(body=body):
                    self._collect_undeclared_info(body, needs_predecl, declared_in_cf, in_control_flow)

    def _body_has_return(self, stmts: list[Stmt]) -> bool:
        """Check if the body contains any Return statements (recursively)."""
        for stmt in stmts:
            if isinstance(stmt, Return):
                return True
            match stmt:
                case If(then_body=then_body, else_body=else_body):
                    if self._body_has_return(then_body) or self._body_has_return(else_body):
                        return True
                case While(body=body) | ForRange(body=body) | ForClassic(body=body):
                    if self._body_has_return(body):
                        return True
                case Match(cases=cases, default=default):
                    for case in cases:
                        if self._body_has_return(case.body):
                            return True
                    if self._body_has_return(default):
                        return True
                case TypeSwitch(cases=cases, default=default):
                    for case in cases:
                        if self._body_has_return(case.body):
                            return True
                    if self._body_has_return(default):
                        return True
                case Block(body=body):
                    if self._body_has_return(body):
                        return True
                case TryCatch(body=body, catch_body=catch_body):
                    # Don't recurse into nested try-catch; they'll handle their own returns
                    pass
        return False

    def _emit_module(self, module: Module) -> None:
        self._line("use strict;")
        self._line("use warnings;")
        self._line("use feature 'signatures';")
        self._line("no warnings 'experimental::signatures';")
        need_blank = True
        if module.constants:
            self._line()
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
        if module.structs and module.functions:
            self._line()
            self._line("package main;")
            need_blank = True
        for func in module.functions:
            if need_blank:
                self._line()
            self._emit_function(func)
            need_blank = True
        self._line()
        self._line("1;")

    def _emit_constant(self, const: Constant) -> None:
        name = const.name.upper()
        val = self._expr(const.value)
        self._line(f"use constant {name} => {val};")

    def _emit_interface(self, iface: InterfaceDef) -> None:
        # Perl uses duck typing, interfaces are documentation only
        self._line(f"# Interface: {iface.name}")
        for method in iface.methods:
            params = ", ".join(_safe_name(p.name) for p in method.params)
            self._line(f"#   {method.name}({params})")

    def _emit_struct(self, struct: Struct) -> None:
        is_empty = not struct.fields and not struct.methods and not struct.doc
        if is_empty and not struct.is_exception and not struct.implements:
            return
        # Track struct fields for proper StructLit emission
        self.struct_fields[struct.name] = [(f.name, f.typ) for f in struct.fields]
        self._line(f"package {struct.name};")
        self.current_package = struct.name
        if struct.is_exception:
            self._line("use parent -norequire, 'Exception';")
        if struct.doc:
            self._line(f"# {struct.doc}")
        if struct.fields:
            self._line()
            self._emit_constructor(struct)
            self._line()
            for fld in struct.fields:
                self._emit_accessor(fld)
        for i, method in enumerate(struct.methods):
            self._line()
            self._emit_method(method)
        self._line()
        self._line("1;")
        self.current_package = None

    def _emit_constructor(self, struct: Struct) -> None:
        params = ", ".join(f"${_safe_name(f.name)}=undef" for f in struct.fields)
        if params:
            self._line(f"sub new ($class, {params}) {{")
        else:
            self._line("sub new ($class) {")
        self.indent += 1
        field_inits = ", ".join(f"{_safe_name(f.name)} => ${_safe_name(f.name)}" for f in struct.fields)
        if field_inits:
            self._line(f"return bless {{ {field_inits} }}, $class;")
        else:
            self._line("return bless {}, $class;")
        self.indent -= 1
        self._line("}")

    def _emit_accessor(self, fld: Field) -> None:
        name = _safe_name(fld.name)
        self._line(f"sub {name} ($self) {{ $self->{{{name}}} }}")

    def _emit_function(self, func: Function) -> None:
        self._hoisted_vars = set()
        self._func_params = {p.name for p in func.params if isinstance(p.typ, FuncType)}
        params = self._params(func.params)
        param_names = {p.name for p in func.params}
        self._line(f"sub {_safe_name(func.name)} ({params}) {{")
        self.indent += 1
        if func.doc:
            self._line(f"# {func.doc}")
        # Pre-declare vars that need it, excluding function parameters
        for name in sorted(self._collect_undeclared_assigns(func.body) - param_names):
            self._line(f"my ${_safe_name(name)};")
            self._hoisted_vars.add(name)
        if _is_empty_body(func.body):
            self._line("return;")
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")

    def _emit_method(self, func: Function) -> None:
        self._hoisted_vars = set()
        self._func_params = {p.name for p in func.params if isinstance(p.typ, FuncType)}
        params = self._params(func.params, with_self=True)
        param_names = {p.name for p in func.params}
        self._line(f"sub {_safe_name(func.name)} ({params}) {{")
        self.indent += 1
        if func.doc:
            self._line(f"# {func.doc}")
        if func.receiver:
            self.receiver_name = func.receiver.name
        # Pre-declare vars that need it, excluding function parameters
        for name in sorted(self._collect_undeclared_assigns(func.body) - param_names):
            self._line(f"my ${_safe_name(name)};")
            self._hoisted_vars.add(name)
        if _is_empty_body(func.body):
            self._line("return;")
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.receiver_name = None
        self.indent -= 1
        self._line("}")

    def _params(self, params: list[Param], with_self: bool = False) -> str:
        parts = []
        if with_self:
            parts.append("$self")
        for p in params:
            parts.append(f"${_safe_name(p.name)}")
        return ", ".join(parts)

    def _emit_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDecl(name=name, value=value):
                safe = _safe_name(name)
                if value is not None:
                    val = self._expr(value)
                    self._line(f"my ${safe} = {val};")
                else:
                    self._line(f"my ${safe};")
            case Assign(target=target, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                target_name = target.name if isinstance(target, VarLV) else None
                is_hoisted = target_name and target_name in self._hoisted_vars
                if stmt.is_declaration and not is_hoisted:
                    self._line(f"my {lv} = {val};")
                else:
                    self._line(f"{lv} = {val};")
            case TupleAssign(targets=targets, value=value):
                lvalues = ", ".join(self._lvalue(t) for t in targets)
                val = self._expr(value)
                any_hoisted = any(
                    isinstance(t, VarLV) and t.name in self._hoisted_vars for t in targets
                )
                if stmt.is_declaration and not any_hoisted:
                    self._line(f"my ({lvalues}) = @{{{val}}};")
                else:
                    self._line(f"({lvalues}) = @{{{val}}};")
            case OpAssign(target=target, op=op, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                perl_op = "." if op == "+" and _is_string_type(stmt.value.typ) else op
                self._line(f"{lv} {perl_op}= {val};")
            case NoOp():
                pass
            case ExprStmt(expr=expr):
                self._line(f"{self._expr(expr)};")
            case Return(value=value):
                if self._in_try_with_return:
                    # Inside eval{} - can't use return, use flag pattern instead
                    if value is not None:
                        self._line(f"$_try_result = {self._expr(value)};")
                    self._line("$_try_returned = 1;")
                    self._line("last TRYBLOCK;")  # Exit the labeled for loop
                elif value is not None:
                    self._line(f"return {self._expr(value)};")
                else:
                    self._line("return;")
            case If(cond=cond, then_body=then_body, else_body=else_body, init=init):
                self._emit_hoisted_vars(stmt)
                if init is not None:
                    self._emit_stmt(init)
                self._line(f"if ({self._expr(cond)}) {{")
                self.indent += 1
                if _is_empty_body(then_body):
                    pass  # Empty block is valid in Perl
                for s in then_body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._emit_else_body(else_body)
                self._line("}")
            case TypeSwitch(expr=expr, binding=binding, cases=cases, default=default):
                self._emit_hoisted_vars(stmt)
                self._emit_type_switch(expr, binding, cases, default)
            case Match(expr=expr, cases=cases, default=default):
                self._emit_hoisted_vars(stmt)
                self._emit_match(expr, cases, default)
            case ForRange(index=index, value=value, iterable=iterable, body=body):
                self._emit_hoisted_vars(stmt)
                self._emit_for_range(index, value, iterable, body)
            case ForClassic(init=init, cond=cond, post=post, body=body):
                self._emit_hoisted_vars(stmt)
                self._emit_for_classic(init, cond, post, body)
            case While(cond=cond, body=body):
                self._emit_hoisted_vars(stmt)
                self._line(f"while ({self._expr(cond)}) {{")
                self.indent += 1
                for s in body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("}")
            case Break(label=_):
                self._line("last;")
            case Continue(label=_):
                self._line("next;")
            case Block(body=body):
                for s in body:
                    self._emit_stmt(s)
            case TryCatch(body=body, catch_var=catch_var, catch_type=catch_type, catch_body=catch_body, reraise=reraise):
                self._emit_hoisted_vars(stmt)
                self._emit_try_catch(body, catch_var, catch_type, catch_body, reraise)
            case Raise(error_type=error_type, message=message, pos=pos, reraise_var=reraise_var):
                if reraise_var:
                    self._line(f"die ${reraise_var};")
                else:
                    msg = self._expr(message)
                    self._line(f"die {msg};")
            case SoftFail():
                self._line("return undef;")
            case _:
                raise NotImplementedError("Unknown statement")

    def _emit_type_switch(
        self, expr: Expr, binding: str, cases: list[TypeCase], default: list[Stmt]
    ) -> None:
        var = self._expr(expr)
        safe_binding = _safe_name(binding)
        for i, case in enumerate(cases):
            keyword = "if" if i == 0 else "} elsif"
            type_name = self._type_name_for_check(case.typ)
            self._line(f"{keyword} (ref({var}) eq '{type_name}') {{")
            self.indent += 1
            self._line(f"my ${safe_binding} = {var};")
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

    def _emit_match(self, expr: Expr, cases: list[MatchCase], default: list[Stmt]) -> None:
        expr_str = self._expr(expr)
        for i, case in enumerate(cases):
            patterns = " || ".join(f"{expr_str} eq {self._expr(p)}" for p in case.patterns)
            keyword = "if" if i == 0 else "} elsif"
            self._line(f"{keyword} ({patterns}) {{")
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

    def _emit_for_range(
        self,
        index: str | None,
        value: str | None,
        iterable: Expr,
        body: list[Stmt],
    ) -> None:
        iter_expr = self._expr(iterable)
        is_string = _is_string_type(iterable.typ)
        if isinstance(iterable.typ, Optional) or isinstance(iterable, FieldAccess):
            iter_expr = f"({iter_expr} // [])"
        idx = _safe_name(index) if index else None
        val = _safe_name(value) if value else None
        if is_string:
            if idx is not None and val is not None:
                tmp = "_chars"
                self._line(f"my @{tmp} = split(//, {iter_expr});")
                self._line(f"for my ${idx} (0 .. $#{tmp}) {{")
                self.indent += 1
                self._line(f"my ${val} = ${tmp}[${idx}];")
            elif val is not None:
                self._line(f"for my ${val} (split(//, {iter_expr})) {{")
                self.indent += 1
            elif idx is not None:
                self._line(f"for my ${idx} (0 .. length({iter_expr}) - 1) {{")
                self.indent += 1
            else:
                self._line(f"for (split(//, {iter_expr})) {{")
                self.indent += 1
        elif idx is not None and val is not None:
            self._line(f"for my ${idx} (0 .. $#{{{iter_expr}}}) {{")
            self.indent += 1
            self._line(f"my ${val} = {iter_expr}->[${idx}];")
        elif val is not None:
            self._line(f"for my ${val} (@{{{iter_expr}}}) {{")
            self.indent += 1
        elif idx is not None:
            self._line(f"for my ${idx} (0 .. $#{{{iter_expr}}}) {{")
            self.indent += 1
        else:
            self._line(f"for (@{{{iter_expr}}}) {{")
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
        if (range_info := _extract_range_pattern(init, cond, post)) is not None:
            var_name, iterable_expr = range_info
            iter_str = self._expr(iterable_expr)
            self._line(f"for my ${_safe_name(var_name)} (0 .. scalar(@{{{iter_str}}}) - 1) {{")
            self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
            return
        init_str = self._stmt_inline(init) if init else ""
        cond_str = self._expr(cond) if cond else "1"
        post_str = self._stmt_inline(post) if post else ""
        self._line(f"for ({init_str}; {cond_str}; {post_str}) {{")
        self.indent += 1
        for s in body:
            self._emit_stmt(s)
        self.indent -= 1
        self._line("}")

    def _stmt_inline(self, stmt: Stmt) -> str:
        match stmt:
            case VarDecl(name=name, value=value):
                if value is not None:
                    return f"my ${_safe_name(name)} = {self._expr(value)}"
                return f"my ${_safe_name(name)}"
            case Assign(target=target, value=value):
                return f"{self._lvalue(target)} = {self._expr(value)}"
            case OpAssign(target=target, op=op, value=value):
                return f"{self._lvalue(target)} {op}= {self._expr(value)}"
            case ExprStmt(expr=expr):
                return self._expr(expr)
            case _:
                raise NotImplementedError("Cannot inline")

    def _emit_try_catch(
        self,
        body: list[Stmt],
        catch_var: str | None,
        catch_type: Type | None,
        catch_body: list[Stmt],
        reraise: bool,
    ) -> None:
        has_return = self._body_has_return(body)
        if has_return:
            self._line("my $_try_result;")
            self._line("my $_try_returned = 0;")
        self._line("eval {")
        self.indent += 1
        if has_return:
            # Wrap in labeled loop so 'last' can exit when returning
            self._line("TRYBLOCK: for (1) {")
            self.indent += 1
            self._in_try_with_return = True
        for s in body:
            self._emit_stmt(s)
        if has_return:
            self._in_try_with_return = False
            self.indent -= 1
            self._line("}")
        self.indent -= 1
        self._line("};")
        var = _safe_name(catch_var) if catch_var else "_e"
        self._line(f"if (my ${var} = $@) {{")
        self.indent += 1
        for s in catch_body:
            self._emit_stmt(s)
        if reraise:
            self._line(f"die ${var};")
        self.indent -= 1
        self._line("}")
        if has_return:
            self._line("return $_try_result if $_try_returned;")

    def _emit_else_body(self, else_body: list[Stmt]) -> None:
        """Emit else body, converting single-If else to elsif chains."""
        if _is_empty_body(else_body):
            return
        if len(else_body) == 1 and isinstance(else_body[0], If):
            elif_stmt = else_body[0]
            if elif_stmt.init is not None:
                self._line("} else {")
                self.indent += 1
                self._emit_stmt(elif_stmt.init)
                self._line(f"if ({self._expr(elif_stmt.cond)}) {{")
                self.indent += 1
                for s in elif_stmt.then_body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._emit_else_body(elif_stmt.else_body)
                self._line("}")
                self.indent -= 1
            else:
                self._line(f"}} elsif ({self._expr(elif_stmt.cond)}) {{")
                self.indent += 1
                for s in elif_stmt.then_body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._emit_else_body(elif_stmt.else_body)
        else:
            self._line("} else {")
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
            case BoolLit(value=value):
                return "1" if value else "0"
            case NilLit():
                return "undef"
            case Var(name=name):
                if name == self.receiver_name:
                    return "$self"
                if name in self.constants:
                    const_call = name.upper() + "()"
                    if self.current_package is not None:
                        return f"main::{const_call}"
                    return const_call
                return f"${_safe_name(name)}"
            case FieldAccess(obj=obj, field=field):
                if field.startswith("F") and field[1:].isdigit():
                    return f"{self._expr(obj)}->[{field[1:]}]"
                return f"{self._expr(obj)}->{{{_safe_name(field)}}}"
            case FuncRef(name=name, obj=obj):
                if obj is not None:
                    return f"sub {{ {self._expr(obj)}->{_safe_name(name)}(@_) }}"
                return f"\\&{_safe_name(name)}"
            case Index(obj=obj, index=index):
                obj_type = obj.typ
                if isinstance(obj_type, Map):
                    return f"{self._expr(obj)}->{{{self._expr(index)}}}"
                if _is_string_type(obj_type):
                    return f"substr({self._expr(obj)}, {self._expr(index)}, 1)"
                if neg_idx := self._negative_index(obj, index):
                    return f"{self._expr(obj)}->[{neg_idx}]"
                return f"{self._expr(obj)}->[{self._expr(index)}]"
            case SliceExpr(obj=obj, low=low, high=high):
                return self._slice_expr(obj, low, high)
            case ParseInt(string=s, base=b):
                base_val = self._expr(b)
                if base_val == "10":
                    return f"int({self._expr(s)})"
                if base_val == "8":
                    return f"oct({self._expr(s)})"
                if base_val == "16":
                    return f"hex({self._expr(s)})"
                return f"int({self._expr(s)})"
            case IntToStr(value=v):
                return f'"{self._expr(v)}"'
            case CharClassify(kind=kind, char=char):
                char_expr = self._expr(char)
                method_map = {
                    "digit": f"({char_expr} =~ /^\\d$/)",
                    "alpha": f"({char_expr} =~ /^[a-zA-Z]$/)",
                    "alnum": f"({char_expr} =~ /^[a-zA-Z0-9]$/)",
                    "space": f"({char_expr} =~ /^\\s$/)",
                    "upper": f"({char_expr} =~ /^[A-Z]$/)",
                    "lower": f"({char_expr} =~ /^[a-z]$/)",
                }
                return method_map[kind]
            case TrimChars(string=s, chars=chars, mode=mode):
                s_expr = self._expr(s)
                if isinstance(chars, StringLit) and chars.value == " \t\n\r":
                    if mode == "left":
                        return f"({s_expr} =~ s/^\\s+//r)"
                    elif mode == "right":
                        return f"({s_expr} =~ s/\\s+$//r)"
                    else:
                        return f"({s_expr} =~ s/^\\s+|\\s+$//gr)"
                chars_expr = self._expr(chars)
                if mode == "left":
                    return f"({s_expr} =~ s/^[{chars_expr}]+//r)"
                elif mode == "right":
                    return f"({s_expr} =~ s/[{chars_expr}]+$//r)"
                else:
                    return f"({s_expr} =~ s/^[{chars_expr}]+|[{chars_expr}]+$//gr)"
            case Call(func=func, args=args):
                # _intPtr is a no-op in Perl (pointers are transparent)
                if func == "_intPtr" and args:
                    return self._expr(args[0])
                args_str = ", ".join(self._expr(a) for a in args)
                safe_func = _safe_name(func)
                # Function parameters need to be called via reference
                if func in self._func_params:
                    return f"${safe_func}->({args_str})"
                if self.current_package is not None:
                    return f"main::{safe_func}({args_str})"
                return f"{safe_func}({args_str})"
            case MethodCall(obj=obj, method=method, args=args, receiver_type=receiver_type):
                args_str = ", ".join(self._expr(a) for a in args)
                obj_str = self._expr(obj)
                if isinstance(obj, (BinaryOp, UnaryOp, Ternary)):
                    obj_str = f"({obj_str})"
                # Unwrap Pointer/Optional to get inner type for slice checks
                inner_type = receiver_type
                if isinstance(inner_type, Pointer):
                    inner_type = inner_type.target
                if isinstance(inner_type, Optional):
                    inner_type = inner_type.inner
                if isinstance(inner_type, Slice):
                    if method == "append":
                        return f"push(@{{{obj_str}}}, {args_str})"
                    if method == "extend":
                        return f"push(@{{{obj_str}}}, @{{{args_str}}})"
                    if method == "pop":
                        return f"pop(@{{{obj_str}}})"
                    if method == "copy":
                        return f"[@{{{obj_str}}}]"
                if isinstance(inner_type, Map):
                    if method == "get":
                        key = self._expr(args[0])
                        if len(args) == 2:
                            default = self._expr(args[1])
                            return f"({obj_str}->{{{key}}} // {default})"
                        return f"{obj_str}->{{{key}}}"
                if _is_string_type(inner_type):
                    if method == "join":
                        return f"join({obj_str}, @{{{args_str}}})"
                    if method == "find":
                        return f"index({obj_str}, {args_str})"
                    if method == "rfind":
                        return f"rindex({obj_str}, {args_str})"
                    if method == "startswith":
                        return f"(index({obj_str}, {args_str}) == 0)"
                    if method == "endswith":
                        return f"(substr({obj_str}, -length({args_str})) eq {args_str})"
                    if method == "split":
                        return f"[split({args_str}, {obj_str})]"
                    if method == "upper":
                        return f"uc({obj_str})"
                    if method == "lower":
                        return f"lc({obj_str})"
                    if method == "replace":
                        # For regex patterns, extract raw values, don't use quoted literals
                        if isinstance(args[0], StringLit):
                            old_val = _escape_perl_regex(args[0].value)
                        else:
                            # Non-literal: use expression but strip surrounding quotes if present
                            old_val = self._expr(args[0])
                        if isinstance(args[1], StringLit):
                            new_val = _escape_perl_replacement(args[1].value)
                        else:
                            new_val = self._expr(args[1])
                        return f"({obj_str} =~ s/{old_val}/{new_val}/gr)"
                # Fallback: if type is unknown but method is a common string method, treat as string
                if method in ("endswith", "startswith", "find", "rfind", "upper", "lower", "split"):
                    if method == "endswith":
                        return f"(substr({obj_str}, -length({args_str})) eq {args_str})"
                    if method == "startswith":
                        return f"(index({obj_str}, {args_str}) == 0)"
                    if method == "find":
                        return f"index({obj_str}, {args_str})"
                    if method == "rfind":
                        return f"rindex({obj_str}, {args_str})"
                    if method == "upper":
                        return f"uc({obj_str})"
                    if method == "lower":
                        return f"lc({obj_str})"
                    if method == "split":
                        return f"[split({args_str}, {obj_str})]"
                if method == "replace" and len(args) == 2:
                    # Fallback for replace with unknown type
                    if isinstance(args[0], StringLit):
                        old_val = _escape_perl_regex(args[0].value)
                    else:
                        old_val = self._expr(args[0])
                    if isinstance(args[1], StringLit):
                        new_val = _escape_perl_replacement(args[1].value)
                    else:
                        new_val = self._expr(args[1])
                    return f"({obj_str} =~ s/{old_val}/{new_val}/gr)"
                pl_method = _method_name(method, receiver_type)
                if args_str:
                    return f"{obj_str}->{pl_method}({args_str})"
                return f"{obj_str}->{pl_method}()"
            case StaticCall(on_type=on_type, method=method, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                type_name = self._type_name_for_check(on_type)
                return f"{type_name}->{_safe_name(method)}({args_str})"
            case Truthy(expr=e):
                inner_type = e.typ
                if isinstance(inner_type, (Slice, Map, Set)):
                    if isinstance(inner_type, Map):
                        return f"(scalar(keys %{{({self._expr(e)} // {{}})}}) > 0)"
                    return f"(scalar(@{{({self._expr(e)} // [])}}) > 0)"
                if isinstance(inner_type, Optional):
                    wrapped = inner_type.inner
                    if isinstance(wrapped, (Slice, Map, Set)):
                        if isinstance(wrapped, Map):
                            return f"(scalar(keys %{{({self._expr(e)} // {{}})}}) > 0)"
                        return f"(scalar(@{{({self._expr(e)} // [])}}) > 0)"
                    return f"defined({self._expr(e)})"
                if isinstance(inner_type, Pointer):
                    return f"defined({self._expr(e)})"
                if inner_type == Primitive(kind="string"):
                    return f"(length({self._expr(e)}) > 0)"
                return f"({self._expr(e)} ? 1 : 0)"
            case BinaryOp(op=op, left=left, right=right):
                if op == "in":
                    return self._containment_check(left, right, negated=False)
                if op == "not in":
                    return self._containment_check(left, right, negated=True)
                pl_op = _binary_op(op, left.typ, right.typ)
                left_str = self._maybe_paren(left, op, is_left=True)
                right_str = self._maybe_paren(right, op, is_left=False)
                return f"{left_str} {pl_op} {right_str}"
            case UnaryOp(op=op, operand=operand):
                pl_op = _unary_op(op)
                if op == "!" and isinstance(operand, BinaryOp):
                    return f"{pl_op}({self._expr(operand)})"
                return f"{pl_op}{self._expr(operand)}"
            case Ternary(cond=cond, then_expr=then_expr, else_expr=else_expr):
                return f"({self._cond_expr(cond)} ? {self._expr(then_expr)} : {self._expr(else_expr)})"
            case Cast(expr=inner, to_type=to_type):
                if to_type == Primitive(kind="string") and isinstance(inner.typ, Slice):
                    return f'pack("C*", @{{{self._expr(inner)}}})'
                if to_type == Primitive(kind="string") and inner.typ == Primitive(kind="rune"):
                    return f"chr({self._expr(inner)})"
                if isinstance(to_type, Slice) and to_type.element == Primitive(kind="byte"):
                    return f"[unpack('C*', {self._expr(inner)})]"
                if to_type == Primitive(kind="int") and inner.typ in (
                    Primitive(kind="string"),
                    Primitive(kind="byte"),
                    Primitive(kind="rune"),
                ):
                    return f"ord({self._expr(inner)})"
                return self._expr(inner)
            case TypeAssert(expr=inner):
                return self._expr(inner)
            case IsType(expr=inner, tested_type=tested_type):
                type_name = self._type_name_for_check(tested_type)
                return f"(ref({self._expr(inner)}) eq '{type_name}')"
            case IsNil(expr=inner, negated=negated):
                if negated:
                    return f"defined({self._expr(inner)})"
                return f"!defined({self._expr(inner)})"
            case Len(expr=inner):
                inner_type = inner.typ
                if isinstance(inner_type, Map):
                    return f"scalar(keys %{{{self._expr(inner)}}})"
                if isinstance(inner_type, Primitive) and inner_type.kind == "string":
                    return f"length({self._expr(inner)})"
                return f"scalar(@{{{self._expr(inner)}}})"
            case MakeSlice(element_type=element_type, length=length):
                if length is not None:
                    zero = self._zero_value(element_type)
                    return f"[({zero}) x {self._expr(length)}]"
                return "[]"
            case MakeMap():
                return "{}"
            case SliceLit(elements=elements):
                elems = ", ".join(self._expr(e) for e in elements)
                return f"[{elems}]"
            case MapLit(entries=entries):
                if not entries:
                    return "{}"
                pairs = ", ".join(f"{self._expr(k)} => {self._expr(v)}" for k, v in entries)
                return f"{{{pairs}}}"
            case SetLit(elements=elements):
                if not elements:
                    return "{}"
                pairs = ", ".join(f"{self._expr(e)} => 1" for e in elements)
                return f"{{{pairs}}}"
            case StructLit(struct_name=struct_name, fields=fields):
                # Use struct field order, fill in missing fields with undef
                field_info = self.struct_fields.get(struct_name, [])
                if field_info:
                    ordered_args = []
                    for field_name, field_type in field_info:
                        if field_name in fields:
                            field_val = fields[field_name]
                            if isinstance(field_val, NilLit) and isinstance(field_type, Slice):
                                ordered_args.append("[]")
                            else:
                                ordered_args.append(self._expr(field_val))
                        else:
                            ordered_args.append(self._zero_value(field_type))
                    return f"{struct_name}->new({', '.join(ordered_args)})"
                elif not fields:
                    return f"{struct_name}->new()"
                args = ", ".join(f"{self._expr(v)}" for v in fields.values())
                return f"{struct_name}->new({args})"
            case TupleLit(elements=elements):
                elems = ", ".join(self._expr(e) for e in elements)
                return f"[{elems}]"
            case StringConcat(parts=parts):
                return " . ".join(self._expr(p) for p in parts)
            case StringFormat(template=template, args=args):
                return self._format_string(template, args)
            case SliceConvert(source=source):
                return self._expr(source)
            case _:
                raise NotImplementedError("Unknown expression")

    def _containment_check(self, item: Expr, container: Expr, negated: bool) -> str:
        """Generate containment check: `x in y` or `x not in y`."""
        item_str = self._expr(item)
        container_str = self._expr(container)
        container_type = container.typ
        neg = "!" if negated else ""
        if isinstance(container_type, (Set, Map)):
            return f"{neg}exists({container_str}->{{{item_str}}})"
        if isinstance(container_type, Primitive) and container_type.kind == "string":
            if negated:
                return f"(index({container_str}, {item_str}) < 0)"
            return f"(index({container_str}, {item_str}) >= 0)"
        # For arrays, use grep
        if negated:
            return f"(!grep {{ $_ eq {item_str} }} @{{{container_str}}})"
        return f"(grep {{ $_ eq {item_str} }} @{{{container_str}}})"

    def _slice_expr(self, obj: Expr, low: Expr | None, high: Expr | None) -> str:
        obj_str = self._expr(obj)
        obj_type = obj.typ
        if isinstance(obj_type, Primitive) and obj_type.kind == "string":
            low_str = self._expr(low) if low else "0"
            if high:
                high_str = self._expr(high)
                return f"substr({obj_str}, {low_str}, {high_str} - {low_str})"
            return f"substr({obj_str}, {low_str})"
        low_str = self._expr(low) if low else "0"
        if high:
            high_str = self._expr(high)
            return f"[@{{{obj_str}}}[{low_str} .. {high_str} - 1]]"
        return f"[@{{{obj_str}}}[{low_str} .. $#{{{obj_str}}}]]"

    def _containment_check(self, item: Expr, container: Expr, negated: bool) -> str:
        """Emit containment check for 'in' / 'not in' operators."""
        item_str = self._expr(item)
        container_str = self._expr(container)
        container_type = container.typ
        neg = "!" if negated else ""
        if isinstance(container_type, Set):
            return f"{neg}exists({container_str}->{{{item_str}}})"
        if isinstance(container_type, Map):
            return f"{neg}exists({container_str}->{{{item_str}}})"
        if isinstance(container_type, Primitive) and container_type.kind == "string":
            if negated:
                return f"(index({container_str}, {item_str}) == -1)"
            return f"(index({container_str}, {item_str}) >= 0)"
        if negated:
            return f"(!grep {{ $_ eq {item_str} }} @{{{container_str}}})"
        return f"(grep {{ $_ eq {item_str} }} @{{{container_str}}})"

    def _negative_index(self, obj: Expr, index: Expr) -> str | None:
        """Detect len(obj) - N and return -N as string, or None if no match."""
        if not isinstance(index, BinaryOp) or index.op != "-":
            return None
        if not isinstance(index.left, Len) or not isinstance(index.right, IntLit):
            return None
        if self._expr(index.left.expr) != self._expr(obj):
            return None
        return f"-{index.right.value}"

    def _format_string(self, template: str, args: list[Expr]) -> str:
        result = template
        for i in range(len(args)):
            result = result.replace(f"{{{i}}}", "%s", 1)
        while "%v" in result:
            result = result.replace("%v", "%s", 1)
        args_str = ", ".join(self._expr(a) for a in args)
        result = result.replace('"', '\\"')
        return f'sprintf("{result}", {args_str})'

    def _lvalue(self, lv: LValue) -> str:
        match lv:
            case VarLV(name=name):
                if name == self.receiver_name:
                    return "$self"
                return f"${_safe_name(name)}"
            case FieldLV(obj=obj, field=field):
                return f"{self._expr(obj)}->{{{_safe_name(field)}}}"
            case IndexLV(obj=obj, index=index):
                obj_type = obj.typ
                if isinstance(obj_type, Map):
                    return f"{self._expr(obj)}->{{{self._expr(index)}}}"
                if neg_idx := self._negative_index(obj, index):
                    return f"{self._expr(obj)}->[{neg_idx}]"
                return f"{self._expr(obj)}->[{self._expr(index)}]"
            case DerefLV(ptr=ptr):
                return self._expr(ptr)
            case _:
                raise NotImplementedError("Unknown lvalue")

    def _type(self, typ: Type) -> str:
        """Type representation (for documentation, Perl is untyped)."""
        match typ:
            case Primitive(kind=kind):
                return kind
            case Slice(element=element):
                return "arrayref"
            case Array(element=element, size=size):
                return "arrayref"
            case Map(key=key, value=value):
                return "hashref"
            case Set(element=element):
                return "hashref"
            case Tuple(elements=elements):
                return "arrayref"
            case Pointer(target=target):
                return self._type(target)
            case Optional(inner=inner):
                return self._type(inner)
            case StructRef(name=name):
                return name
            case InterfaceRef(name=name):
                return name
            case Union(name=name, variants=variants):
                if name:
                    return name
                return "scalar"
            case FuncType(params=params, ret=ret):
                return "coderef"
            case _:
                return "scalar"

    def _type_name_for_check(self, typ: Type) -> str:
        match typ:
            case StructRef(name=name):
                return name
            case InterfaceRef(name=name):
                return name
            case _:
                return self._type(typ)

    def _zero_value(self, typ: Type) -> str:
        match typ:
            case Primitive(kind="int") | Primitive(kind="byte"):
                return "0"
            case Primitive(kind="float"):
                return "0.0"
            case Primitive(kind="bool"):
                return "0"
            case Primitive(kind="string"):
                return '""'
            case _:
                return "undef"

    def _cond_expr(self, expr: Expr) -> str:
        """Emit a condition expression, wrapping in parens only if needed for ternary."""
        match expr:
            case BinaryOp(op=op) if op in ("and", "or", "&&", "||"):
                return f"({self._expr(expr)})"
            case _:
                return self._expr(expr)

    def _maybe_paren(self, expr: Expr, parent_op: str, is_left: bool) -> str:
        """Wrap expression in parens if needed for operator precedence."""
        match expr:
            case BinaryOp(op=child_op):
                if _needs_parens(child_op, parent_op, is_left):
                    return f"({self._expr(expr)})"
            case Ternary():
                return f"({self._expr(expr)})"
        return self._expr(expr)


def _method_name(method: str, receiver_type: Type) -> str:
    """Convert method name for Perl idioms."""
    if isinstance(receiver_type, Slice):
        if method == "append":
            return "push"
    return _safe_name(method)


def _binary_op(op: str, left_type: Type, right_type: Type | None = None) -> str:
    """Convert binary operator, using string operators for string types."""
    is_string = _is_string_type(left_type) or (right_type is not None and _is_string_type(right_type))
    match op:
        case "and" | "&&":
            return "&&"
        case "or" | "||":
            return "||"
        case "==" if is_string:
            return "eq"
        case "!=" if is_string:
            return "ne"
        case "<" if is_string:
            return "lt"
        case ">" if is_string:
            return "gt"
        case "<=" if is_string:
            return "le"
        case ">=" if is_string:
            return "ge"
        case "+":
            if is_string:
                return "."
            return "+"
        case _:
            return op


def _unary_op(op: str) -> str:
    match op:
        case "!":
            return "!"
        case "&" | "*":
            return ""
        case _:
            return op


_PRECEDENCE = {
    "or": 1,
    "||": 1,
    "and": 2,
    "&&": 2,
    "eq": 3,
    "ne": 3,
    "lt": 3,
    "gt": 3,
    "le": 3,
    "ge": 3,
    "==": 3,
    "!=": 3,
    "<": 3,
    ">": 3,
    "<=": 3,
    ">=": 3,
    ".": 4,
    "+": 4,
    "-": 4,
    "*": 5,
    "/": 5,
    "%": 5,
}


def _needs_parens(child_op: str, parent_op: str, is_left: bool) -> bool:
    """Determine if a child binary op needs parens inside a parent binary op."""
    child_prec = _PRECEDENCE.get(child_op, 0)
    parent_prec = _PRECEDENCE.get(parent_op, 0)
    if child_prec < parent_prec:
        return True
    if child_prec == parent_prec and not is_left:
        return child_op in ("==", "!=", "<", ">", "<=", ">=", "eq", "ne", "lt", "gt", "le", "ge")
    return False


def _escape_perl_string(value: str) -> str:
    """Escape a string for Perl double-quoted literal."""
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
        .replace("\r", "\\r")
        .replace("$", "\\$")
        .replace("@", "\\@")
    )


def _escape_perl_regex(s: str) -> str:
    """Escape special regex metacharacters for Perl s/// pattern."""
    # Escape: . ^ $ * + ? { } [ ] \ | ( ) /
    result = []
    for ch in s:
        if ch in r".^$*+?{}[]\|()/":
            result.append("\\" + ch)
        elif ch == "\n":
            result.append("\\n")
        elif ch == "\t":
            result.append("\\t")
        elif ch == "\r":
            result.append("\\r")
        elif ord(ch) < 32 or ord(ch) > 126:
            # Use \x{XX} for control chars and non-ASCII
            result.append(f"\\x{{{ord(ch):02x}}}")
        else:
            result.append(ch)
    return "".join(result)


def _escape_perl_replacement(s: str) -> str:
    """Escape special chars in Perl s/// replacement string."""
    # In replacement, $ \ and / are special
    result = []
    for ch in s:
        if ch == "\\":
            result.append("\\\\")
        elif ch == "$":
            result.append("\\$")
        elif ch == "/":
            result.append("\\/")
        elif ch == "\n":
            result.append("\\n")
        elif ch == "\t":
            result.append("\\t")
        elif ch == "\r":
            result.append("\\r")
        elif ord(ch) < 32 or ord(ch) > 126:
            # Use \x{XX} for control chars and non-ASCII
            result.append(f"\\x{{{ord(ch):02x}}}")
        else:
            result.append(ch)
    return "".join(result)


def _string_literal(value: str) -> str:
    return f'"{_escape_perl_string(value)}"'


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
    if not isinstance(cond.right, Len):
        return None
    iterable_expr = cond.right.expr
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
    return (var_name, iterable_expr)
