"""PHP backend: IR → PHP 8.1+ code."""

from __future__ import annotations

from src.backend.util import to_camel, to_pascal, to_screaming_snake
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

_PHP_RESERVED = frozenset(
    {
        "abstract",
        "and",
        "array",
        "as",
        "break",
        "callable",
        "case",
        "catch",
        "class",
        "clone",
        "const",
        "continue",
        "declare",
        "default",
        "die",
        "do",
        "echo",
        "else",
        "elseif",
        "empty",
        "enddeclare",
        "endfor",
        "endforeach",
        "endif",
        "endswitch",
        "endwhile",
        "eval",
        "exit",
        "extends",
        "final",
        "finally",
        "fn",
        "for",
        "foreach",
        "function",
        "global",
        "goto",
        "if",
        "implements",
        "include",
        "include_once",
        "instanceof",
        "insteadof",
        "interface",
        "isset",
        "list",
        "match",
        "namespace",
        "new",
        "or",
        "print",
        "private",
        "protected",
        "public",
        "readonly",
        "require",
        "require_once",
        "return",
        "static",
        "switch",
        "throw",
        "trait",
        "try",
        "unset",
        "use",
        "var",
        "while",
        "xor",
        "yield",
        "__CLASS__",
        "__DIR__",
        "__FILE__",
        "__FUNCTION__",
        "__LINE__",
        "__METHOD__",
        "__NAMESPACE__",
        "__TRAIT__",
        # Built-in classes that cannot be redeclared
        "exception",
        "error",
        "parseerror",
        "typeerror",
        "argumentcounterror",
        "arithmeticerror",
        "assertionerror",
        "divisionbyzeroerror",
        "compileerror",
        "throwable",
        "iterator",
        "iteratoraggregate",
        "traversable",
        "arrayaccess",
        "serializable",
        "countable",
        "stringable",
        "closure",
        "generator",
        "stdclass",
    }
)


def _safe_name(name: str) -> str:
    """Escape PHP reserved words with _ suffix."""
    result = to_camel(name)
    if result in _PHP_RESERVED:
        return result + "_"
    return result


def _safe_pascal(name: str) -> str:
    """Convert to PascalCase and escape reserved words."""
    result = to_pascal(name)
    if result.lower() in _PHP_RESERVED:
        return result + "_"
    return result


class PhpBackend:
    """Emit PHP 8.1+ code from IR."""

    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self.receiver_name: str | None = None
        self.current_class: str = ""
        self.struct_fields: dict[str, list[tuple[str, Type]]] = {}
        self._hoisted_vars: set[str] = set()
        self._module_name: str = ""
        self._callable_params: set[str] = set()

    def emit(self, module: Module) -> str:
        """Emit PHP code from IR Module."""
        self.indent = 0
        self.lines = []
        self.struct_fields = {}
        self._hoisted_vars = set()
        self._module_name = module.name
        self._collect_struct_fields(module)
        self._emit_module(module)
        return "\n".join(self.lines)

    def _collect_struct_fields(self, module: Module) -> None:
        """Collect field information for all structs."""
        for struct in module.structs:
            self.struct_fields[struct.name] = [(f.name, f.typ) for f in struct.fields]

    def _line(self, text: str = "") -> None:
        if text:
            self.lines.append("    " * self.indent + text)
        else:
            self.lines.append("")

    def _emit_module(self, module: Module) -> None:
        self._line("<?php")
        self._line("")
        self._line("declare(strict_types=1);")
        self._line("")
        if module.constants:
            for const in module.constants:
                self._emit_constant(const)
            self._line("")
        for iface in module.interfaces:
            self._emit_interface(iface)
            self._line("")
        for struct in module.structs:
            self._emit_struct(struct)
            self._line("")
        for func in module.functions:
            self._emit_function(func)
            self._line("")

    def _emit_constant(self, const: Constant) -> None:
        val = self._expr(const.value)
        name = to_screaming_snake(const.name)
        self._line(f"const {name} = {val};")

    def _emit_interface(self, iface: InterfaceDef) -> None:
        self._line(f"interface {_safe_pascal(iface.name)}")
        self._line("{")
        self.indent += 1
        for method in iface.methods:
            params = self._params(method.params)
            ret = self._type(method.ret)
            name = _safe_name(method.name)
            self._line(f"public function {name}({params}): {ret};")
        self.indent -= 1
        self._line("}")

    def _emit_struct(self, struct: Struct) -> None:
        class_name = _safe_pascal(struct.name)
        self.current_class = struct.name
        extends_clause = ""
        if struct.is_exception:
            parent = _safe_pascal(struct.embedded_type) if struct.embedded_type else "Exception"
            extends_clause = f" extends {parent}"
        elif struct.implements:
            impl_names = ", ".join(_safe_pascal(i) for i in struct.implements)
            extends_clause = f" implements {impl_names}"
        self._line(f"class {class_name}{extends_clause}")
        self._line("{")
        self.indent += 1
        # Skip 'message' field for exceptions since it's inherited from Exception
        fields_to_emit = [f for f in struct.fields if not (struct.is_exception and f.name == "message")]
        for fld in fields_to_emit:
            self._emit_field(fld)
        # Generate constructor for structs with fields, or exception subclasses that need to call parent
        if struct.fields or (struct.is_exception and struct.embedded_type):
            self._line("")
            self._emit_constructor(struct)
        for method in struct.methods:
            self._line("")
            self._emit_method(method)
        self.indent -= 1
        self._line("}")
        self.current_class = ""

    def _emit_field(self, fld: Field) -> None:
        typ = self._param_type(fld.typ)
        name = _safe_name(fld.name)
        self._line(f"public {typ} ${name};")

    def _emit_constructor(self, struct: Struct) -> None:
        class_name = struct.name
        # Handle exception subclasses with no fields - just call parent with message
        if not struct.fields:
            if struct.is_exception and struct.embedded_type:
                self._line("public function __construct(string $message)")
                self._line("{")
                self.indent += 1
                self._line("parent::__construct($message, 0, 0);")
                self.indent -= 1
                self._line("}")
            return
        param_parts = []
        for f in struct.fields:
            typ = self._param_type(f.typ)
            name = _safe_name(f.name)
            if f.default is not None:
                default_val = self._expr(f.default)
                param_parts.append(f"{typ} ${name} = {default_val}")
            elif isinstance(f.typ, Optional):
                param_parts.append(f"{typ} ${name} = null")
            elif struct.is_exception and name in ("pos", "line"):
                # Exception pos/line fields default to 0
                param_parts.append(f"{typ} ${name} = 0")
            else:
                param_parts.append(f"{typ} ${name}")
        params = ", ".join(param_parts)
        self._line(f"public function __construct({params})")
        self._line("{")
        self.indent += 1
        for f in struct.fields:
            param_name = _safe_name(f.name)
            if struct.is_exception and f.name == "message":
                self._line(f"parent::__construct(${param_name});")
            elif isinstance(f.typ, Slice):
                self._line(f"$this->{param_name} = ${param_name} ?? [];")
            else:
                self._line(f"$this->{param_name} = ${param_name};")
        self.indent -= 1
        self._line("}")

    def _emit_function(self, func: Function) -> None:
        self._hoisted_vars = set()
        self._callable_params = {p.name for p in func.params if isinstance(p.typ, FuncType)}
        params = self._params(func.params)
        ret = self._param_type(func.ret)
        name = _safe_name(func.name)
        self._line(f"function {name}({params}): {ret}")
        self._line("{")
        self.indent += 1
        if not func.body:
            self._line('throw new Exception("Not implemented");')
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")
        self._callable_params = set()

    def _emit_method(self, func: Function) -> None:
        self._hoisted_vars = set()
        self._callable_params = {p.name for p in func.params if isinstance(p.typ, FuncType)}
        params = self._params(func.params)
        ret = self._param_type(func.ret)
        name = _safe_name(func.name)
        if func.receiver:
            self.receiver_name = func.receiver.name
        self._line(f"public function {name}({params}): {ret}")
        self._line("{")
        self.indent += 1
        if not func.body:
            self._line('throw new Exception("Not implemented");')
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")
        self.receiver_name = None
        self._callable_params = set()

    def _params(self, params: list[Param]) -> str:
        parts = []
        for p in params:
            typ = self._param_type(p.typ)
            parts.append(f"{typ} ${_safe_name(p.name)}")
        return ", ".join(parts)

    def _emit_hoisted_vars(
        self, stmt: If | While | ForRange | ForClassic | TryCatch | Match | TypeSwitch
    ) -> None:
        hoisted_vars = stmt.hoisted_vars
        for name, typ in hoisted_vars:
            var_name = _safe_name(name)
            default = self._default_value(typ) if typ else "null"
            self._line(f"${var_name} = {default};")
            self._hoisted_vars.add(name)

    def _emit_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDecl(name=name, typ=typ, value=value):
                var_name = _safe_name(name)
                if value is not None:
                    val = self._expr(value)
                    self._line(f"${var_name} = {val};")
                else:
                    default = self._default_value(typ)
                    self._line(f"${var_name} = {default};")
            case Assign(target=target, value=value):
                val = self._expr(value)
                lv = self._lvalue(target)
                self._line(f"{lv} = {val};")
            case OpAssign(target=target, op=op, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                # String concatenation: += on strings becomes .= in PHP
                php_op = "." if op == "+" and _is_string_type(value.typ) else op
                self._line(f"{lv} {php_op}= {val};")
            case TupleAssign(targets=targets, value=value):
                self._emit_tuple_assign(stmt)
            case NoOp():
                pass
            case ExprStmt(expr=expr):
                e = self._expr(expr)
                self._line(f"{e};")
            case Return(value=value):
                if value is not None:
                    self._line(f"return {self._expr(value)};")
                else:
                    self._line("return;")
            case If(cond=cond, then_body=then_body, else_body=else_body, init=init):
                self._emit_hoisted_vars(stmt)
                if init is not None:
                    self._emit_stmt(init)
                self._line(f"if ({self._expr(cond)})")
                self._line("{")
                self.indent += 1
                for s in then_body:
                    self._emit_stmt(s)
                self.indent -= 1
                if else_body:
                    self._line("}")
                    self._line("else")
                    self._line("{")
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
                self._line(f"while ({self._expr(cond)})")
                self._line("{")
                self.indent += 1
                for s in body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("}")
            case Break(label=label):
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
                    self._line(f"throw ${reraise_var};")
                else:
                    msg = self._expr(message)
                    exc_type = _safe_pascal(error_type)
                    self._line(f"throw new {exc_type}({msg});")
            case SoftFail():
                self._line("return null;")
            case _:
                self._line("// TODO: unknown statement")

    def _emit_tuple_assign(self, stmt: TupleAssign) -> None:
        value = stmt.value
        targets = stmt.targets
        val_str = self._expr(value)
        lv_strs = [self._lvalue(t) for t in targets]
        self._line(f"[{', '.join(lv_strs)}] = {val_str};")

    def _emit_type_switch(self, stmt: TypeSwitch) -> None:
        self._emit_hoisted_vars(stmt)
        var = self._expr(stmt.expr)
        binding = _safe_name(stmt.binding)
        cases = stmt.cases
        default = stmt.default
        shadows = isinstance(stmt.expr, Var) and _safe_name(stmt.expr.name) == binding
        first = True
        for case in cases:
            type_name = self._type_name_for_check(case.typ)
            keyword = "if" if first else "elseif"
            first = False
            self._line(f"{keyword} ({var} instanceof {type_name})")
            self._line("{")
            self.indent += 1
            if not shadows:
                self._line(f"${binding} = {var};")
            for s in case.body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        if default:
            self._line("else")
            self._line("{")
            self.indent += 1
            for s in default:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")

    def _emit_match(self, stmt: Match) -> None:
        self._emit_hoisted_vars(stmt)
        expr_str = self._expr(stmt.expr)
        self._line(f"switch ({expr_str})")
        self._line("{")
        self.indent += 1
        for case in stmt.cases:
            for pattern in case.patterns:
                self._line(f"case {self._expr(pattern)}:")
            self.indent += 1
            for s in case.body:
                self._emit_stmt(s)
            if case.body and not isinstance(case.body[-1], Return):
                self._line("break;")
            self.indent -= 1
        if stmt.default:
            self._line("default:")
            self.indent += 1
            for s in stmt.default:
                self._emit_stmt(s)
            self.indent -= 1
        self.indent -= 1
        self._line("}")

    def _emit_for_range(self, stmt: ForRange) -> None:
        self._emit_hoisted_vars(stmt)
        iter_expr = self._expr(stmt.iterable)
        iter_type = stmt.iterable.typ
        is_string = isinstance(iter_type, Primitive) and iter_type.kind == "string"
        index = stmt.index
        value = stmt.value
        body = stmt.body
        if value is not None and index is not None:
            idx = _safe_name(index)
            val = _safe_name(value)
            if is_string:
                self._line(f"for (${idx} = 0; ${idx} < mb_strlen({iter_expr}); ${idx}++)")
                self._line("{")
                self.indent += 1
                self._line(f"${val} = mb_substr({iter_expr}, ${idx}, 1);")
            else:
                self._line(f"foreach ({iter_expr} as ${idx} => ${val})")
                self._line("{")
                self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        elif value is not None:
            val = _safe_name(value)
            if is_string:
                self._line(f"foreach (mb_str_split({iter_expr}) as ${val})")
            else:
                self._line(f"foreach ({iter_expr} as ${val})")
            self._line("{")
            self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        elif index is not None:
            idx = _safe_name(index)
            if is_string:
                self._line(f"for (${idx} = 0; ${idx} < mb_strlen({iter_expr}); ${idx}++)")
            else:
                self._line(f"for (${idx} = 0; ${idx} < count({iter_expr}); ${idx}++)")
            self._line("{")
            self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        else:
            if is_string:
                self._line(f"foreach (mb_str_split({iter_expr}) as $_)")
            else:
                self._line(f"foreach ({iter_expr} as $_)")
            self._line("{")
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
        self._line(f"for ({init_str}; {cond_str}; {post_str})")
        self._line("{")
        self.indent += 1
        for s in stmt.body:
            self._emit_stmt(s)
        self.indent -= 1
        self._line("}")

    def _stmt_inline(self, stmt: Stmt) -> str:
        match stmt:
            case VarDecl(name=name, typ=typ, value=value):
                var_name = _safe_name(name)
                if value:
                    return f"${var_name} = {self._expr(value)}"
                return f"${var_name} = {self._default_value(typ)}"
            case Assign(target=target, value=value):
                if isinstance(value, BinaryOp) and value.op == "+":
                    if isinstance(value.right, IntLit) and value.right.value == 1:
                        if isinstance(target, VarLV) and isinstance(value.left, Var):
                            if target.name == value.left.name:
                                return f"${_safe_name(target.name)}++"
                return f"{self._lvalue(target)} = {self._expr(value)}"
            case OpAssign(target=target, op=op, value=value):
                php_op = "." if op == "+" and _is_string_type(value.typ) else op
                return f"{self._lvalue(target)} {php_op}= {self._expr(value)}"
            case _:
                return ""

    def _emit_try_catch(self, stmt: TryCatch) -> None:
        self._emit_hoisted_vars(stmt)
        self._line("try")
        self._line("{")
        self.indent += 1
        for s in stmt.body:
            self._emit_stmt(s)
        self.indent -= 1
        var = _safe_name(stmt.catch_var) if stmt.catch_var else "ex"
        exc_type = _safe_pascal(stmt.catch_type.name) if isinstance(stmt.catch_type, StructRef) else "Exception"
        self._line(f"}} catch ({exc_type} ${var})")
        self._line("{")
        self.indent += 1
        for s in stmt.catch_body:
            self._emit_stmt(s)
        if stmt.reraise:
            self._line(f"throw ${var};")
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
                return f'"{_escape_php_string(value)}"'
            case BoolLit(value=value):
                return "true" if value else "false"
            case NilLit():
                return "null"
            case Var(name=name):
                if name == self.receiver_name:
                    return "$this"
                if name.isupper() or (name[0].isupper() and "_" in name and name.split("_", 1)[1].isupper()):
                    return to_screaming_snake(name)
                return "$" + _safe_name(name)
            case FieldAccess(obj=obj, field=field):
                obj_str = self._expr(obj)
                obj_type = obj.typ
                if isinstance(obj_type, Pointer):
                    obj_type = obj_type.target
                if field.startswith("F") and field[1:].isdigit():
                    return f"{obj_str}[{field[1:]}]"
                return f"{obj_str}->{_safe_name(field)}"
            case FuncRef(name=name, obj=obj):
                if obj is not None:
                    obj_str = self._expr(obj)
                    return f"[{obj_str}, '{_safe_name(name)}']"
                return f"'{_safe_name(name)}'"
            case Index(obj=obj, index=index):
                obj_str = self._expr(obj)
                idx_str = self._expr(index)
                obj_type = obj.typ
                if isinstance(obj_type, Primitive) and obj_type.kind == "string":
                    return f"mb_substr({obj_str}, {idx_str}, 1)"
                return f"{obj_str}[{idx_str}]"
            case SliceExpr(obj=obj, low=low, high=high):
                return self._slice_expr(obj, low, high)
            case ParseInt(string=s, base=b):
                return f"intval({self._expr(s)}, {self._expr(b)})"
            case IntToStr(value=v):
                return f"strval({self._expr(v)})"
            case CharClassify(kind=kind, char=char):
                char_str = self._expr(char)
                method_map = {
                    "digit": "ctype_digit",
                    "alpha": "ctype_alpha",
                    "alnum": "ctype_alnum",
                    "space": "ctype_space",
                    "upper": "ctype_upper",
                    "lower": "ctype_lower",
                }
                method = method_map[kind]
                return f"{method}({char_str})"
            case TrimChars(string=s, chars=chars, mode=mode):
                s_str = self._expr(s)
                chars_str = self._expr(chars)
                if mode == "left":
                    return f"ltrim({s_str}, {chars_str})"
                elif mode == "right":
                    return f"rtrim({s_str}, {chars_str})"
                else:
                    return f"trim({s_str}, {chars_str})"
            case Call(func=func, args=args):
                return self._call(func, args)
            case MethodCall(obj=obj, method=method, args=args, receiver_type=receiver_type):
                return self._method_call(obj, method, args, receiver_type)
            case StaticCall(on_type=on_type, method=method, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                type_name = self._type_name_for_check(on_type)
                return f"{type_name}::{_safe_name(method)}({args_str})"
            case Truthy(expr=e):
                inner_str = self._expr(e)
                inner_type = e.typ
                if _is_string_type(inner_type):
                    return f"({inner_str} !== '')"
                if isinstance(inner_type, (Slice, Map, Set)):
                    return f"(count({inner_str}) > 0)"
                if isinstance(inner_type, Primitive) and inner_type.kind == "int":
                    return f"({inner_str} !== 0)"
                return f"({inner_str} !== null)"
            case BinaryOp(op="in", left=left, right=right):
                return self._containment_check(left, right, negated=False)
            case BinaryOp(op="not in", left=left, right=right):
                return self._containment_check(left, right, negated=True)
            case BinaryOp(op=op, left=left, right=right):
                # String concatenation: + on strings becomes . in PHP
                if op == "+" and (_is_string_type(left.typ) or _is_string_type(right.typ)):
                    left_str = self._maybe_paren(left, ".", is_left=True)
                    right_str = self._maybe_paren(right, ".", is_left=False)
                    return f"{left_str} . {right_str}"
                php_op = _binary_op(op, left.typ)
                left_str = self._maybe_paren(left, php_op, is_left=True)
                right_str = self._maybe_paren(right, php_op, is_left=False)
                result = f"{left_str} {php_op} {right_str}"
                if op in ("&", "|", "^") or (isinstance(left, BinaryOp) and left.op in ("&", "|", "^")):
                    return f"({result})"
                return result
            case UnaryOp(op="&", operand=operand):
                return self._expr(operand)
            case UnaryOp(op="*", operand=operand):
                return self._expr(operand)
            case UnaryOp(op="!", operand=operand):
                operand_type = operand.typ
                if isinstance(operand_type, Primitive) and operand_type.kind == "int":
                    return f"({self._expr(operand)} === 0)"
                if isinstance(operand_type, (InterfaceRef, StructRef, Pointer)):
                    return f"({self._expr(operand)} === null)"
                return f"!{self._expr(operand)}"
            case UnaryOp(op=op, operand=operand):
                return f"{op}{self._expr(operand)}"
            case Ternary(cond=cond, then_expr=then_expr, else_expr=else_expr):
                return f"({self._expr(cond)} ? {self._expr(then_expr)} : {self._expr(else_expr)})"
            case Cast(expr=inner, to_type=to_type):
                return self._cast(inner, to_type)
            case TypeAssert(expr=inner, asserted=asserted):
                return self._expr(inner)
            case IsType(expr=inner, tested_type=tested_type):
                type_name = self._type_name_for_check(tested_type)
                return f"({self._expr(inner)} instanceof {type_name})"
            case IsNil(expr=inner, negated=negated):
                if negated:
                    return f"{self._expr(inner)} !== null"
                return f"{self._expr(inner)} === null"
            case Len(expr=inner):
                inner_str = self._expr(inner)
                if isinstance(inner.typ, Primitive) and inner.typ.kind == "string":
                    return f"mb_strlen({inner_str})"
                return f"count({inner_str})"
            case MakeSlice(element_type=element_type, length=length, capacity=capacity):
                return "[]"
            case MakeMap(key_type=key_type, value_type=value_type):
                return "[]"
            case SliceLit(elements=elements, element_type=element_type):
                if not elements:
                    return "[]"
                elems = ", ".join(self._expr(e) for e in elements)
                return f"[{elems}]"
            case MapLit(entries=entries, key_type=key_type, value_type=value_type):
                if not entries:
                    return "[]"
                pairs = ", ".join(f"{self._expr(k)} => {self._expr(v)}" for k, v in entries)
                return f"[{pairs}]"
            case SetLit(elements=elements, element_type=element_type):
                if not elements:
                    return "[]"
                elems = ", ".join(f"{self._expr(e)} => true" for e in elements)
                return f"[{elems}]"
            case StructLit(struct_name=struct_name, fields=fields, embedded_value=embedded_value):
                return self._struct_lit(struct_name, fields, embedded_value)
            case TupleLit(elements=elements):
                elems = ", ".join(self._expr(e) for e in elements)
                return f"[{elems}]"
            case StringConcat(parts=parts):
                return " . ".join(self._expr(p) for p in parts)
            case StringFormat(template=template, args=args):
                return self._format_string(template, args)
            case _:
                return "null /* TODO: unknown expression */"

    def _call(self, func: str, args: list[Expr]) -> str:
        args_str = ", ".join(self._expr(a) for a in args)
        if func == "_intPtr" and len(args) == 1:
            return self._expr(args[0])
        if func == "int" and len(args) == 2:
            return f"intval({args_str})"
        if func == "str":
            return f"strval({self._expr(args[0])})"
        if func == "len":
            arg = self._expr(args[0])
            arg_type = args[0].typ
            if isinstance(arg_type, Primitive) and arg_type.kind == "string":
                return f"mb_strlen({arg})"
            return f"count({arg})"
        if func == "range":
            if len(args) == 1:
                return f"range(0, {self._expr(args[0])} - 1)"
            elif len(args) == 2:
                return f"range({self._expr(args[0])}, {self._expr(args[1])} - 1)"
            else:
                return f"range({self._expr(args[0])}, {self._expr(args[1])} - 1, {self._expr(args[2])})"
        if func == "ord":
            return f"mb_ord({self._expr(args[0])})"
        if func == "chr":
            return f"mb_chr({self._expr(args[0])})"
        if func == "abs":
            return f"abs({args_str})"
        if func == "min":
            return f"min({args_str})"
        if func == "max":
            return f"max({args_str})"
        safe_func = _safe_name(func)
        if func in self._callable_params:
            return f"${safe_func}({args_str})"
        return f"{safe_func}({args_str})"

    def _method_call(self, obj: Expr, method: str, args: list[Expr], receiver_type: Type) -> str:
        args_str = ", ".join(self._expr(a) for a in args)
        obj_str = self._expr(obj)
        if isinstance(receiver_type, Slice):
            if method == "append" and args:
                return f"array_push({obj_str}, {args_str})"
            if method == "pop":
                if not args:
                    return f"array_pop({obj_str})"
                idx = self._expr(args[0])
                if idx == "0":
                    return f"array_shift({obj_str})"
                return f"array_splice({obj_str}, {idx}, 1)[0]"
            if method == "copy":
                return obj_str
        if isinstance(receiver_type, Primitive) and receiver_type.kind == "string":
            if method == "startswith":
                if len(args) == 1:
                    return f"str_starts_with({obj_str}, {args_str})"
                else:
                    prefix = self._expr(args[0])
                    offset = self._expr(args[1])
                    return f"str_starts_with(mb_substr({obj_str}, {offset}), {prefix})"
            if method == "endswith":
                if args and isinstance(args[0], TupleLit):
                    checks = " || ".join(f"str_ends_with({obj_str}, {self._expr(e)})" for e in args[0].elements)
                    return f"({checks})"
                return f"str_ends_with({obj_str}, {args_str})"
            if method == "find":
                return f"mb_strpos({obj_str}, {args_str})"
            if method == "rfind":
                return f"mb_strrpos({obj_str}, {args_str})"
            if method == "replace":
                return f"str_replace({self._expr(args[0])}, {self._expr(args[1])}, {obj_str})"
            if method == "split":
                return f"explode({args_str}, {obj_str})"
            if method == "join":
                return f"implode({obj_str}, {args_str})"
            if method == "lower":
                return f"mb_strtolower({obj_str})"
            if method == "upper":
                return f"mb_strtoupper({obj_str})"
        if isinstance(receiver_type, Map):
            if method == "get" and len(args) == 2:
                key = self._expr(args[0])
                default = self._expr(args[1])
                return f"({obj_str}[{key}] ?? {default})"
        if method == "append":
            return f"array_push({obj_str}, {args_str})"
        if method == "extend":
            arg_type = args[0].typ if args else None
            if isinstance(arg_type, Slice):
                elem_type = arg_type.element
                if isinstance(elem_type, Primitive) and elem_type.kind == "byte":
                    return f"array_push({obj_str}, ...str_split({args_str}))"
                return f"array_push({obj_str}, ...{args_str})"
            return f"array_push({obj_str}, {args_str})"
        if method == "remove":
            return f"array_splice({obj_str}, array_search({args_str}, {obj_str}), 1)"
        if method == "clear":
            return f"{obj_str} = []"
        if method == "insert":
            return f"array_splice({obj_str}, {self._expr(args[0])}, 0, [{self._expr(args[1])}])"
        # Fallback string methods (when receiver type isn't detected)
        if method == "endswith":
            if args and isinstance(args[0], TupleLit):
                checks = " || ".join(f"str_ends_with({obj_str}, {self._expr(e)})" for e in args[0].elements)
                return f"({checks})"
            return f"str_ends_with({obj_str}, {args_str})"
        if method == "startswith":
            return f"str_starts_with({obj_str}, {args_str})"
        if method == "find":
            return f"mb_strpos({obj_str}, {args_str})"
        if method == "rfind":
            return f"mb_strrpos({obj_str}, {args_str})"
        if method == "replace":
            return f"str_replace({self._expr(args[0])}, {self._expr(args[1])}, {obj_str})"
        if method == "split":
            return f"explode({args_str}, {obj_str})"
        if method == "join":
            return f"implode({obj_str}, {args_str})"
        if method == "lower":
            return f"mb_strtolower({obj_str})"
        if method == "upper":
            return f"mb_strtoupper({obj_str})"
        return f"{obj_str}->{_safe_name(method)}({args_str})"

    def _slice_expr(self, obj: Expr, low: Expr | None, high: Expr | None) -> str:
        obj_str = self._expr(obj)
        if isinstance(obj.typ, Primitive) and obj.typ.kind == "string":
            if low and high:
                lo = self._expr(low)
                hi = self._expr(high)
                return f"mb_substr({obj_str}, {lo}, {hi} - {lo})"
            elif low:
                return f"mb_substr({obj_str}, {self._expr(low)})"
            elif high:
                return f"mb_substr({obj_str}, 0, {self._expr(high)})"
            return obj_str
        if low and high:
            lo = self._expr(low)
            hi = self._expr(high)
            return f"array_slice({obj_str}, {lo}, {hi} - {lo})"
        elif low:
            return f"array_slice({obj_str}, {self._expr(low)})"
        elif high:
            return f"array_slice({obj_str}, 0, {self._expr(high)})"
        return obj_str

    def _containment_check(self, item: Expr, container: Expr, negated: bool) -> str:
        item_str = self._expr(item)
        container_str = self._expr(container)
        container_type = container.typ
        neg = "!" if negated else ""
        if isinstance(container_type, Set):
            return f"{neg}isset({container_str}[{item_str}])"
        if isinstance(container_type, Map):
            return f"{neg}array_key_exists({item_str}, {container_str})"
        if isinstance(container_type, Primitive) and container_type.kind == "string":
            return f"({neg}str_contains({container_str}, {item_str}))"
        return f"{neg}in_array({item_str}, {container_str}, true)"

    def _cast(self, inner: Expr, to_type: Type) -> str:
        inner_str = self._expr(inner)
        if isinstance(to_type, Primitive):
            if to_type.kind == "int":
                return f"(int)({inner_str})"
            if to_type.kind == "float":
                return f"(float)({inner_str})"
            if to_type.kind == "bool":
                return f"(bool)({inner_str})"
            if to_type.kind == "string":
                inner_type = inner.typ
                if isinstance(inner_type, Slice):
                    elem = inner_type.element
                    if isinstance(elem, Primitive) and elem.kind == "byte":
                        return f"implode('', {inner_str})"
                return f"(string)({inner_str})"
        return inner_str

    def _format_string(self, template: str, args: list[Expr]) -> str:
        from re import sub as re_sub
        result = re_sub(r"\{(\d+)\}", r"%s", template)
        result = result.replace("%v", "%s")
        escaped = _escape_php_string(result)
        args_str = ", ".join(self._expr(a) for a in args)
        if args_str:
            return f'sprintf("{escaped}", {args_str})'
        return f'"{escaped}"'

    def _struct_lit(self, struct_name: str, fields: dict[str, Expr], embedded_value: Expr | None) -> str:
        field_info = self.struct_fields.get(struct_name, [])
        safe_name = _safe_pascal(struct_name)
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

    def _lvalue(self, lv: LValue) -> str:
        match lv:
            case VarLV(name=name):
                if name == self.receiver_name:
                    return "$this"
                return "$" + _safe_name(name)
            case FieldLV(obj=obj, field=field):
                return f"{self._expr(obj)}->{_safe_name(field)}"
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
                return "array"
            case Array(element=element, size=size):
                return "array"
            case Map(key=key, value=value):
                return "array"
            case Set(element=element):
                return "array"
            case Tuple(elements=elements):
                return "array"
            case Pointer(target=target):
                return self._type(target)
            case Optional(inner=inner):
                inner_type = self._type(inner)
                return f"?{inner_type}"
            case StructRef(name=name):
                return _safe_pascal(name)
            case InterfaceRef(name=name):
                if name == "any":
                    return "mixed"
                return _safe_pascal(name)
            case Union(name=name):
                if name:
                    return _safe_pascal(name)
                return "mixed"
            case FuncType(params=params, ret=ret):
                return "callable"
            case _:
                return "mixed"

    def _param_type(self, typ: Type) -> str:
        """Return type hint for parameters, making struct/interface/slice types nullable."""
        match typ:
            case StructRef(name=name):
                return f"?{_safe_pascal(name)}"
            case InterfaceRef(name=name):
                if name == "any":
                    return "mixed"
                return f"?{_safe_pascal(name)}"
            case Pointer(target=target):
                return self._param_type(target)
            case Slice():
                return "?array"
            case _:
                return self._type(typ)

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
                return '""'
            case Slice():
                return "[]"
            case Map():
                return "[]"
            case Set():
                return "[]"
            case Optional():
                return "null"
            case _:
                return "null"

    def _maybe_paren(self, expr: Expr, parent_op: str, is_left: bool) -> str:
        """Wrap expression in parens if needed for operator precedence."""
        match expr:
            case BinaryOp(op=child_op):
                if _needs_parens(child_op, parent_op, is_left):
                    return f"({self._expr(expr)})"
            case Ternary():
                return f"({self._expr(expr)})"
        return self._expr(expr)


def _primitive_type(kind: str) -> str:
    match kind:
        case "string":
            return "string"
        case "int":
            return "int"
        case "float":
            return "float"
        case "bool":
            return "bool"
        case "byte":
            return "int"
        case "rune":
            return "string"
        case "void":
            return "void"
        case _:
            return "mixed"


def _binary_op(op: str, left_type: Type) -> str:
    is_string = _is_string_type(left_type)
    match op:
        case "&&":
            return "&&"
        case "||":
            return "||"
        case "==":
            return "==="
        case "!=":
            return "!=="
        case "+":
            if is_string:
                return "."
            return "+"
        case _:
            return op


def _escape_php_string(value: str) -> str:
    """Escape a string for PHP double-quoted literal."""
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
        .replace("\r", "\\r")
        .replace("$", "\\$")
    )


def _is_string_type(typ: Type) -> bool:
    return isinstance(typ, Primitive) and typ.kind in ("string", "rune")


# PHP operator precedence (higher number = tighter binding)
_PRECEDENCE = {
    "or": 1,
    "||": 2,
    "and": 3,
    "&&": 4,
    "|": 5,
    "^": 6,
    "&": 7,
    "==": 8,
    "===": 8,
    "!=": 8,
    "!==": 8,
    "<": 9,
    ">": 9,
    "<=": 9,
    ">=": 9,
    "+": 11,
    "-": 11,
    ".": 11,
    "*": 12,
    "/": 12,
    "%": 12,
    "//": 12,
}


def _needs_parens(child_op: str, parent_op: str, is_left: bool) -> bool:
    """Determine if a child binary op needs parens inside a parent binary op."""
    child_prec = _PRECEDENCE.get(child_op, 0)
    parent_prec = _PRECEDENCE.get(parent_op, 0)
    if child_prec < parent_prec:
        return True
    if child_prec == parent_prec and not is_left:
        return child_op in ("==", "===", "!=", "!==", "<", ">", "<=", ">=")
    return False
