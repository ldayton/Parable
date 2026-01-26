"""Rust backend: IR → Rust code."""

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
    Interface,
    InterfaceDef,
    IsNil,
    IsType,
    Len,
    LValue,
    MakeMap,
    MakeSlice,
    Map,
    MapLit,
    Match,
    MethodCall,
    Module,
    NilLit,
    OpAssign,
    Optional,
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


class RustBackend:
    """Emit Rust code from IR."""

    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self.receiver_name: str | None = None
        self.current_func_ret: Type | None = None

    def emit(self, module: Module) -> str:
        """Emit Rust code from IR Module."""
        self.indent = 0
        self.lines = []
        self._emit_module(module)
        return "\n".join(self.lines)

    def _line(self, text: str = "") -> None:
        if text:
            self.lines.append("    " * self.indent + text)
        else:
            self.lines.append("")

    def _emit_module(self, module: Module) -> None:
        self._line("#![allow(dead_code)]")
        self._line()
        self._line("use std::collections::{HashMap, HashSet};")
        need_blank = True
        if module.constants:
            self._line()
            for const in module.constants:
                self._emit_constant(const)
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

    def _emit_constant(self, const: Constant) -> None:
        typ = self._type(const.typ)
        val = self._expr(const.value)
        self._line(f"const {const.name}: {typ} = {val};")

    def _emit_interface(self, iface: InterfaceDef) -> None:
        self._line(f"trait {iface.name} {{")
        self.indent += 1
        for method in iface.methods:
            params = self._trait_params(method.params)
            ret = self._type(method.ret)
            if ret == "()":
                self._line(f"fn {to_snake(method.name)}({params});")
            else:
                self._line(f"fn {to_snake(method.name)}({params}) -> {ret};")
        self.indent -= 1
        self._line("}")

    def _emit_struct(self, struct: Struct) -> None:
        # Add common derives for structs
        self._line("#[derive(Clone, Default)]")
        self._line(f"struct {struct.name} {{")
        self.indent += 1
        for fld in struct.fields:
            self._emit_field(fld)
        self.indent -= 1
        self._line("}")
        if struct.methods:
            self._line()
            self._line(f"impl {struct.name} {{")
            self.indent += 1
            for i, method in enumerate(struct.methods):
                if i > 0:
                    self._line()
                self._emit_method(method)
            self.indent -= 1
            self._line("}")

    def _emit_field(self, fld: Field) -> None:
        typ = self._type(fld.typ)
        self._line(f"{to_snake(fld.name)}: {typ},")

    def _emit_function(self, func: Function) -> None:
        params = self._params(func.params)
        ret = self._type(func.ret)
        name = to_snake(func.name)
        self.current_func_ret = func.ret
        if ret == "()":
            self._line(f"fn {name}({params}) {{")
        else:
            self._line(f"fn {name}({params}) -> {ret} {{")
        self.indent += 1
        if not func.body:
            self._line("todo!()")
        self._emit_body(func.body)
        self.indent -= 1
        self._line("}")
        self.current_func_ret = None

    def _emit_method(self, func: Function) -> None:
        params = self._method_params(func.params, func.receiver)
        ret = self._type(func.ret)
        name = to_snake(func.name)
        if func.receiver:
            self.receiver_name = func.receiver.name
        self.current_func_ret = func.ret
        if ret == "()":
            self._line(f"fn {name}({params}) {{")
        else:
            self._line(f"fn {name}({params}) -> {ret} {{")
        self.indent += 1
        if not func.body:
            self._line("todo!()")
        self._emit_body(func.body)
        self.indent -= 1
        self._line("}")
        self.receiver_name = None
        self.current_func_ret = None

    def _params(self, params: list) -> str:
        parts = []
        for p in params:
            typ = self._type(p.typ)
            mut = "mut " if getattr(p, 'is_modified', False) else ""
            prefix = "_" if getattr(p, 'is_unused', False) else ""
            parts.append(f"{mut}{prefix}{to_snake(p.name)}: {typ}")
        return ", ".join(parts)

    def _method_params(self, params: list, receiver: Receiver | None) -> str:
        parts = []
        if receiver:
            if receiver.mutable:
                parts.append("&mut self")
            else:
                parts.append("&self")
        for p in params:
            typ = self._type(p.typ)
            prefix = "_" if getattr(p, 'is_unused', False) else ""
            parts.append(f"{prefix}{to_snake(p.name)}: {typ}")
        return ", ".join(parts)

    def _trait_params(self, params: list) -> str:
        parts = ["&self"]
        for p in params:
            typ = self._type(p.typ)
            parts.append(f"{to_snake(p.name)}: {typ}")
        return ", ".join(parts)

    def _emit_stmts(self, body: list[Stmt]) -> None:
        """Emit statements with tuple destructuring optimization."""
        i = 0
        while i < len(body):
            # Try to emit tuple destructuring for pattern: let x = tuple; let a = x.0; let b = x.1;
            consumed = self._try_emit_tuple_destructure(body, i)
            if consumed > 0:
                i += consumed
                continue
            self._emit_stmt(body[i])
            i += 1

    def _emit_body(self, body: list[Stmt]) -> None:
        """Emit function body, using expression return for tail position."""
        i = 0
        while i < len(body):
            stmt = body[i]
            is_last = i == len(body) - 1
            # Try to emit tuple destructuring for pattern: let x = tuple; let a = x.0; let b = x.1;
            consumed = self._try_emit_tuple_destructure(body, i)
            if consumed > 0:
                i += consumed
                continue
            # Use expression return for final Return statement
            if is_last and isinstance(stmt, Return) and stmt.value is not None:
                val_expr = self._expr(stmt.value)
                # Wrap in Some() if returning non-Optional value in Optional function
                if (isinstance(self.current_func_ret, Optional) and
                    hasattr(stmt.value, 'typ') and not isinstance(stmt.value.typ, Optional)):
                    val_expr = f"Some({val_expr}.clone())"
                self._line(val_expr)
            else:
                self._emit_stmt(stmt)
            i += 1

    def _try_emit_tuple_destructure(self, body: list[Stmt], start: int) -> int:
        """Try to emit tuple destructuring. Returns number of statements consumed, or 0."""
        if start >= len(body):
            return 0
        first = body[start]
        # Pattern: let result: (A, B) = expr; let a = result.0; let b = result.1;
        if not isinstance(first, VarDecl):
            return 0
        if not isinstance(first.typ, Tuple):
            return 0
        tuple_var = first.name
        tuple_len = len(first.typ.elements)
        # Look for consecutive Index accesses on this tuple var
        bindings = []
        for j in range(tuple_len):
            idx = start + 1 + j
            if idx >= len(body):
                return 0
            stmt = body[idx]
            if not isinstance(stmt, VarDecl):
                return 0
            if not isinstance(stmt.value, Index):
                return 0
            if not isinstance(stmt.value.obj, Var):
                return 0
            if stmt.value.obj.name != tuple_var:
                return 0
            if not isinstance(stmt.value.index, IntLit):
                return 0
            if stmt.value.index.value != j:
                return 0
            bindings.append((stmt.name, getattr(stmt, 'is_reassigned', False)))
        # All checks passed - emit destructuring
        muts = ["mut " if is_reassigned else "" for _, is_reassigned in bindings]
        names = [to_snake(name) for name, _ in bindings]
        binding_str = ", ".join(f"{m}{n}" for m, n in zip(muts, names))
        val_expr = self._expr(first.value)
        self._line(f"let ({binding_str}) = {val_expr};")
        return 1 + tuple_len  # consumed: tuple decl + all index accesses

    def _emit_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDecl(name=name, typ=typ, value=value, mutable=mutable):
                rust_type = self._type(typ)
                # When initial value is unused, first assignment is initialization, not mutation
                # So mut is only needed if assigned more than once after that
                initial_unused = getattr(stmt, 'initial_value_unused', False)
                if initial_unused:
                    needs_mut = getattr(stmt, 'assignment_count', 0) > 1
                else:
                    needs_mut = getattr(stmt, 'is_reassigned', False)
                mut = "mut " if needs_mut else ""
                if initial_unused:
                    self._line(f"let {mut}{to_snake(name)}: {rust_type};")
                elif value is not None:
                    val = self._expr(value)
                    self._line(f"let {mut}{to_snake(name)}: {rust_type} = {val};")
                else:
                    default = self._default_value(typ)
                    self._line(f"let {mut}{to_snake(name)}: {rust_type} = {default};")
            case Assign(target=target, value=value):
                lv = self._lvalue(target)
                # Detect x = x + y pattern and emit x += y
                if isinstance(value, BinaryOp) and value.op in ("+", "-", "*", "/", "%"):
                    if isinstance(target, VarLV) and isinstance(value.left, Var):
                        if target.name == value.left.name:
                            val = self._expr(value.right)
                            self._line(f"{lv} {value.op}= {val};")
                            return
                val = self._expr(value)
                self._line(f"{lv} = {val};")
            case TupleAssign(targets=targets, value=value):
                lvalues = ", ".join(self._lvalue(t) for t in targets)
                val = self._expr(value)
                if getattr(stmt, 'is_declaration', False):
                    self._line(f"let ({lvalues}) = {val};")
                else:
                    self._line(f"({lvalues}) = {val};")
            case OpAssign(target=target, op=op, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                self._line(f"{lv} {op}= {val};")
            case ExprStmt(expr=expr):
                e = self._expr(expr)
                self._line(f"{e};")
            case Return(value=value):
                if value is not None:
                    val_expr = self._expr(value)
                    # Wrap in Some() if returning non-Optional value in Optional function
                    if (isinstance(self.current_func_ret, Optional) and
                        hasattr(value, 'typ') and not isinstance(value.typ, Optional)):
                        val_expr = f"Some({val_expr}.clone())"
                    self._line(f"return {val_expr};")
                else:
                    self._line("return;")
            case If(cond=cond, then_body=then_body, else_body=else_body, init=init):
                if init is not None:
                    self._emit_stmt(init)
                self._line(f"if {self._expr(cond)} {{")
                self.indent += 1
                self._emit_stmts(then_body)
                self.indent -= 1
                if else_body:
                    self._line("} else {")
                    self.indent += 1
                    self._emit_stmts(else_body)
                    self.indent -= 1
                self._line("}")
            case TypeSwitch(expr=expr, binding=binding, cases=cases, default=default):
                self._emit_type_switch(expr, binding, cases, default)
            case Match(expr=expr, cases=cases, default=default):
                self._emit_match(expr, cases, default)
            case ForRange(index=index, value=value, iterable=iterable, body=body):
                self._emit_for_range(index, value, iterable, body)
            case ForClassic(init=init, cond=cond, post=post, body=body):
                self._emit_for_classic(init, cond, post, body)
            case While(cond=cond, body=body):
                self._line(f"while {self._expr(cond)} {{")
                self.indent += 1
                self._emit_stmts(body)
                self.indent -= 1
                self._line("}")
            case Break(label=label):
                if label:
                    self._line(f"break '{label};")
                else:
                    self._line("break;")
            case Continue(label=label):
                if label:
                    self._line(f"continue '{label};")
                else:
                    self._line("continue;")
            case Block(body=body):
                self._line("{")
                self.indent += 1
                self._emit_stmts(body)
                self.indent -= 1
                self._line("}")
            case TryCatch(body=body, catch_var=catch_var, catch_body=catch_body, reraise=reraise):
                catch_var_unused = getattr(stmt, 'catch_var_unused', False)
                self._emit_try_catch(body, catch_var, catch_body, reraise, catch_var_unused)
            case Raise(error_type=error_type, message=message, pos=pos):
                # For string literals, emit panic!("message") directly
                if isinstance(message, StringLit):
                    escaped = message.value.replace("\\", "\\\\").replace('"', '\\"')
                    self._line(f'panic!("{escaped}");')
                else:
                    msg = self._expr(message)
                    self._line(f'panic!("{{}}", {msg});')
            case SoftFail():
                self._line("return None;")
            case _:
                raise NotImplementedError(f"Unknown statement: {type(stmt).__name__}")

    def _emit_type_switch(
        self, expr: Expr, binding: str, cases: list[TypeCase], default: list[Stmt]
    ) -> None:
        var = self._expr(expr)
        self._line(f"// type switch on {var}")
        for i, case in enumerate(cases):
            type_name = self._type_name_for_check(case.typ)
            keyword = "if" if i == 0 else "} else if"
            self._line(f"{keyword} let Some({to_snake(binding)}) = {var}.downcast_ref::<{type_name}>() {{")
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

    def _emit_match(self, expr: Expr, cases: list, default: list[Stmt]) -> None:
        # For String types, match against .as_str() to enable literal patterns
        expr_str = self._expr(expr)
        if hasattr(expr, 'typ') and isinstance(expr.typ, Primitive) and expr.typ.kind == "string":
            expr_str = f"{expr_str}.as_str()"
        self._line(f"match {expr_str} {{")
        self.indent += 1
        for case in cases:
            patterns = " | ".join(self._match_pattern(p) for p in case.patterns)
            # Use expression syntax for single-return match arms
            if self._is_single_return(case.body):
                val = self._expr(case.body[0].value)
                self._line(f"{patterns} => {val},")
            else:
                self._line(f"{patterns} => {{")
                self.indent += 1
                self._emit_body(case.body)
                self.indent -= 1
                self._line("}")
        if default:
            if self._is_single_return(default):
                val = self._expr(default[0].value)
                self._line(f"_ => {val},")
            else:
                self._line("_ => {")
                self.indent += 1
                self._emit_body(default)
                self.indent -= 1
                self._line("}")
        self.indent -= 1
        self._line("}")

    def _is_single_return(self, body: list[Stmt]) -> bool:
        """Check if body is a single Return statement with a value."""
        return len(body) == 1 and isinstance(body[0], Return) and body[0].value is not None

    def _match_pattern(self, p: Expr) -> str:
        """Emit a match pattern (string literals without .to_string())."""
        if isinstance(p, StringLit):
            escaped = p.value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        return self._expr(p)

    def _emit_for_range(
        self,
        index: str | None,
        value: str | None,
        iterable: Expr,
        body: list[Stmt],
    ) -> None:
        iter_expr = self._expr(iterable)
        if index is not None and value is not None:
            self._line(f"for ({to_snake(index)}, {to_snake(value)}) in {iter_expr}.iter().enumerate() {{")
        elif value is not None:
            self._line(f"for {to_snake(value)} in {iter_expr}.iter() {{")
        elif index is not None:
            self._line(f"for {to_snake(index)} in 0..{iter_expr}.len() {{")
        else:
            self._line(f"for _ in {iter_expr}.iter() {{")
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
        if init is not None:
            self._emit_stmt(init)
        cond_str = self._expr(cond) if cond else "true"
        self._line(f"while {cond_str} {{")
        self.indent += 1
        for s in body:
            self._emit_stmt(s)
        if post is not None:
            self._emit_stmt(post)
        self.indent -= 1
        self._line("}")

    def _emit_try_catch(
        self,
        body: list[Stmt],
        catch_var: str | None,
        catch_body: list[Stmt],
        reraise: bool,
        catch_var_unused: bool = False,
    ) -> None:
        self._line("let _result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {")
        self.indent += 1
        for s in body:
            self._emit_stmt(s)
        self.indent -= 1
        self._line("}));")
        if catch_var:
            prefix = "_" if catch_var_unused else ""
            var = f"{prefix}{to_snake(catch_var)}"
        else:
            var = "_e"
        self._line(f"if let Err({var}) = _result {{")
        self.indent += 1
        for s in catch_body:
            self._emit_stmt(s)
        if reraise:
            self._line(f"std::panic::resume_unwind({var});")
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
                return "None"
            case Var(name=name):
                if name == self.receiver_name:
                    return "self"
                # Don't snake_case constants (all caps)
                if name.isupper():
                    return name
                return to_snake(name)
            case FieldAccess(obj=obj, field=field):
                obj_expr = self._expr(obj)
                # Unwrap if accessing field on an Optional variable
                if isinstance(obj, Var) and isinstance(obj.typ, Optional):
                    obj_expr = f"{obj_expr}.as_ref().unwrap()"
                field_access = f"{obj_expr}.{to_snake(field)}"
                # Clone String fields accessed from references
                if (isinstance(obj, Var) and isinstance(obj.typ, Optional) and
                    hasattr(expr, 'typ') and isinstance(expr.typ, Primitive) and expr.typ.kind == "string"):
                    field_access = f"{field_access}.clone()"
                return field_access
            case Index(obj=obj, index=index):
                # Tuple indexing uses .0, .1 syntax in Rust
                if hasattr(expr, 'obj_type') and isinstance(expr.obj_type, Tuple):
                    return f"{self._expr(obj)}.{index.value}"
                if isinstance(index, IntLit) and hasattr(obj, 'typ') and isinstance(obj.typ, Tuple):
                    return f"{self._expr(obj)}.{index.value}"
                # String indexing returns byte as i64
                if hasattr(obj, 'typ') and isinstance(obj.typ, Primitive) and obj.typ.kind == "string":
                    idx_expr = self._expr(index)
                    if isinstance(index, IntLit):
                        return f"{self._expr(obj)}.as_bytes()[{idx_expr}] as i64"
                    return f"{self._expr(obj)}.as_bytes()[{idx_expr} as usize] as i64"
                # Cast index to usize for array/slice indexing
                idx_expr = self._expr(index)
                if isinstance(index, IntLit):
                    return f"{self._expr(obj)}[{idx_expr}]"
                return f"{self._expr(obj)}[{idx_expr} as usize]"
            case SliceExpr(obj=obj, low=low, high=high):
                return self._slice_expr(obj, low, high)
            case Call(func=func, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                return f"{to_snake(func)}({args_str})"
            case MethodCall(obj=obj, method=method, args=args, receiver_type=receiver_type):
                return self._method_call(obj, method, args, receiver_type)
            case StaticCall(on_type=on_type, method=method, args=args):
                type_name = self._type_name_for_check(on_type)
                # Map common static methods to Rust equivalents
                rust_method = to_snake(method)
                if rust_method == "empty" and not args:
                    rust_method = "default"
                args_str = ", ".join(self._expr(a) for a in args)
                return f"{type_name}::{rust_method}({args_str})"
            case BinaryOp(op=op, left=left, right=right):
                # Idiomatic: len(x) > 0 → !x.is_empty(), len(x) == 0 → x.is_empty()
                if isinstance(left, Len) and isinstance(right, IntLit) and right.value == 0:
                    inner = self._expr(left.expr)
                    if op == ">":
                        return f"!{inner}.is_empty()"
                    elif op == "==":
                        return f"{inner}.is_empty()"
                    elif op == "!=":
                        return f"!{inner}.is_empty()"
                    elif op == "<=":
                        return f"{inner}.is_empty()"
                rust_op = _binary_op(op)
                left_str = self._expr(left)
                # For string equality comparisons, use bare &str literal (no .to_string())
                if op in ("==", "!=") and isinstance(right, StringLit):
                    right_str = _string_literal_bare(right.value)
                else:
                    right_str = self._expr(right)
                # Minimal parenthesization - Rust handles operator precedence correctly
                return f"{left_str} {rust_op} {right_str}"
            case UnaryOp(op=op, operand=operand):
                return f"{op}{self._expr(operand)}"
            case Ternary(cond=cond, then_expr=then_expr, else_expr=else_expr):
                return f"if {self._expr(cond)} {{ {self._expr(then_expr)} }} else {{ {self._expr(else_expr)} }}"
            case Cast(expr=inner, to_type=to_type):
                return f"{self._expr(inner)} as {self._type(to_type)}"
            case TypeAssert(expr=inner, asserted=asserted, safe=safe):
                type_name = self._type_name_for_check(asserted)
                if safe:
                    return f"{self._expr(inner)}.downcast_ref::<{type_name}>()"
                return f"{self._expr(inner)}.downcast_ref::<{type_name}>().unwrap()"
            case IsType(expr=inner, tested_type=tested_type):
                type_name = self._type_name_for_check(tested_type)
                return f"{self._expr(inner)}.downcast_ref::<{type_name}>().is_some()"
            case IsNil(expr=inner, negated=negated):
                if negated:
                    return f"{self._expr(inner)}.is_some()"
                return f"{self._expr(inner)}.is_none()"
            case Len(expr=inner):
                # Cast len() to i64 to match our integer type
                return f"({self._expr(inner)}.len() as i64)"
            case MakeSlice(element_type=element_type, length=length):
                typ = self._type(element_type)
                if length is not None:
                    default = self._default_value(element_type)
                    len_expr = self._expr(length)
                    if isinstance(length, IntLit):
                        return f"vec![{default}; {len_expr}]"
                    return f"vec![{default}; {len_expr} as usize]"
                return f"Vec::<{typ}>::new()"
            case MakeMap(key_type=key_type, value_type=value_type):
                kt = self._type(key_type)
                vt = self._type(value_type)
                return f"HashMap::<{kt}, {vt}>::new()"
            case SliceLit(elements=elements):
                if not elements:
                    return "vec![]"
                elems = ", ".join(self._expr(e) for e in elements)
                return f"vec![{elems}]"
            case MapLit(entries=entries, key_type=key_type, value_type=value_type):
                if not entries:
                    kt = self._type(key_type)
                    vt = self._type(value_type)
                    return f"HashMap::<{kt}, {vt}>::new()"
                pairs = ", ".join(
                    f"({self._expr(k)}, {self._expr(v)})" for k, v in entries
                )
                return f"HashMap::from([{pairs}])"
            case SetLit(elements=elements, element_type=element_type):
                if not elements:
                    et = self._type(element_type)
                    return f"HashSet::<{et}>::new()"
                elems = ", ".join(self._expr(e) for e in elements)
                return f"HashSet::from([{elems}])"
            case StructLit(struct_name=struct_name, fields=fields):
                if not fields:
                    return f"{struct_name}::default()"
                # Use field init shorthand when field name matches variable name
                parts = []
                for k, v in fields.items():
                    field_name = to_snake(k)
                    val_str = self._expr(v)
                    if isinstance(v, Var) and to_snake(v.name) == field_name:
                        parts.append(field_name)
                    else:
                        parts.append(f"{field_name}: {val_str}")
                return f"{struct_name} {{ {', '.join(parts)} }}"
            case TupleLit(elements=elements):
                elems = ", ".join(self._expr(e) for e in elements)
                return f"({elems})"
            case StringConcat(parts=parts):
                if len(parts) == 1:
                    return self._expr(parts[0])
                # In Rust, String + &str works, so first part is String, rest are &str
                result_parts = []
                for i, p in enumerate(parts):
                    if i == 0:
                        result_parts.append(self._expr(p))
                    elif isinstance(p, StringLit):
                        # String literals can be &str directly
                        result_parts.append(_string_literal_bare(p.value))
                    else:
                        # Other String expressions need & to become &str
                        result_parts.append(f"&{self._expr(p)}")
                return " + ".join(result_parts)
            case StringFormat(template=template, args=args):
                return self._format_string(template, args)
            case _:
                raise NotImplementedError(f"Unknown expression: {type(expr).__name__}")

    def _method_call(self, obj: Expr, method: str, args: list[Expr], receiver_type: Type) -> str:
        args_str = ", ".join(self._expr(a) for a in args)
        # Handle slice methods
        if isinstance(receiver_type, Slice):
            if method == "append" and args:
                return f"{self._expr(obj)}.push({args_str})"
            if method == "pop" and not args:
                return f"{self._expr(obj)}.pop().unwrap()"
        return f"{self._expr(obj)}.{to_snake(method)}({args_str})"

    def _slice_expr(self, obj: Expr, low: Expr | None, high: Expr | None) -> str:
        obj_str = self._expr(obj)
        # Use .to_string() for String types, .to_vec() for slices
        is_string = hasattr(obj, 'typ') and isinstance(obj.typ, Primitive) and obj.typ.kind == "string"
        convert = ".to_string()" if is_string else ".to_vec()"
        # Cast indices to usize
        low_str = f"({self._expr(low)} as usize)" if low and not isinstance(low, IntLit) else (self._expr(low) if low else None)
        high_str = f"({self._expr(high)} as usize)" if high and not isinstance(high, IntLit) else (self._expr(high) if high else None)
        if low_str and high_str:
            return f"{obj_str}[{low_str}..{high_str}]{convert}"
        elif low_str:
            return f"{obj_str}[{low_str}..]{convert}"
        elif high_str:
            return f"{obj_str}[..{high_str}]{convert}"
        return f"{obj_str}.clone()"

    def _format_string(self, template: str, args: list[Expr]) -> str:
        # Convert {0}, {1} to {} for Rust format!
        result = template
        for i in range(len(args)):
            result = result.replace(f"{{{i}}}", "{}", 1)
        escaped = result.replace("\\", "\\\\").replace('"', '\\"')
        args_str = ", ".join(self._expr(a) for a in args)
        if args_str:
            return f'format!("{escaped}", {args_str})'
        return f'"{escaped}".to_string()'

    def _lvalue(self, lv: LValue) -> str:
        match lv:
            case VarLV(name=name):
                if name == self.receiver_name:
                    return "self"
                return to_snake(name)
            case FieldLV(obj=obj, field=field):
                return f"{self._expr(obj)}.{to_snake(field)}"
            case IndexLV(obj=obj, index=index):
                idx_expr = self._expr(index)
                if isinstance(index, IntLit):
                    return f"{self._expr(obj)}[{idx_expr}]"
                return f"{self._expr(obj)}[{idx_expr} as usize]"
            case DerefLV(ptr=ptr):
                return f"*{self._expr(ptr)}"
            case _:
                raise NotImplementedError(f"Unknown lvalue: {type(lv).__name__}")

    def _type(self, typ: Type) -> str:
        match typ:
            case Primitive(kind=kind):
                return _primitive_type(kind)
            case Slice(element=element):
                return f"Vec<{self._type(element)}>"
            case Array(element=element, size=size):
                return f"[{self._type(element)}; {size}]"
            case Map(key=key, value=value):
                return f"HashMap<{self._type(key)}, {self._type(value)}>"
            case Set(element=element):
                return f"HashSet<{self._type(element)}>"
            case Tuple(elements=elements):
                parts = ", ".join(self._type(e) for e in elements)
                return f"({parts})"
            case Pointer(target=target):
                return f"Box<{self._type(target)}>"
            case Optional(inner=inner):
                return f"Option<{self._type(inner)}>"
            case StructRef(name=name):
                return name
            case Interface(name=name):
                if name == "any":
                    return "Box<dyn std::any::Any>"
                return f"Box<dyn {name}>"
            case Union(name=name, variants=variants):
                if name:
                    return name
                parts = ", ".join(self._type(v) for v in variants)
                return f"({parts})"
            case FuncType(params=params, ret=ret):
                params_str = ", ".join(self._type(p) for p in params)
                ret_str = self._type(ret)
                return f"fn({params_str}) -> {ret_str}"
            case StringSlice():
                return "&str"
            case _:
                raise NotImplementedError(f"Unknown type: {type(typ).__name__}")

    def _type_name_for_check(self, typ: Type) -> str:
        match typ:
            case StructRef(name=name):
                return name
            case Interface(name=name):
                return name
            case Pointer(target=target):
                return self._type_name_for_check(target)
            case _:
                return self._type(typ)

    def _default_value(self, typ: Type) -> str:
        match typ:
            case Primitive(kind="string"):
                return 'String::new()'
            case Primitive(kind="int"):
                return "0"
            case Primitive(kind="float"):
                return "0.0"
            case Primitive(kind="bool"):
                return "false"
            case Primitive(kind="byte"):
                return "0"
            case Primitive(kind="rune"):
                return "'\\0'"
            case Slice():
                return "Vec::new()"
            case Map():
                return "HashMap::new()"
            case Set():
                return "HashSet::new()"
            case Optional():
                return "None"
            case _:
                return "Default::default()"


def _primitive_type(kind: str) -> str:
    match kind:
        case "string":
            return "String"
        case "int":
            return "i64"
        case "float":
            return "f64"
        case "bool":
            return "bool"
        case "byte":
            return "u8"
        case "rune":
            return "char"
        case "void":
            return "()"
        case _:
            raise NotImplementedError(f"Unknown primitive: {kind}")


def _binary_op(op: str) -> str:
    match op:
        case "&&":
            return "&&"
        case "||":
            return "||"
        case _:
            return op


def _string_literal(value: str) -> str:
    return f'"{escape_string(value)}".to_string()'


def _string_literal_bare(value: str) -> str:
    """String literal without .to_string() - for comparisons with &str."""
    return f'"{escape_string(value)}"'
