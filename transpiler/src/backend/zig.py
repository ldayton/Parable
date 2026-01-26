"""Zig backend: IR → Zig code."""

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


class ZigBackend:
    """Emit Zig code from IR."""

    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self.receiver_name: str | None = None
        self.current_struct: str = ""
        self.var_types: dict[str, Type] = {}  # Track declared variable types

    def emit(self, module: Module) -> str:
        """Emit Zig code from IR Module."""
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
        self._line("const std = @import(\"std\");")
        self._line("const mem = std.mem;")
        self._line("const Allocator = std.mem.Allocator;")
        self._line("const ArrayList = std.ArrayList;")
        self._line("")
        self._line("var gpa = std.heap.GeneralPurposeAllocator(.{}){};")
        self._line("const allocator = gpa.allocator();")
        self._line("")
        if module.constants:
            for const in module.constants:
                self._emit_constant(const)
            self._line("")
        for struct in module.structs:
            self._emit_struct(struct)
        for func in module.functions:
            self._emit_function(func)

    def _emit_constant(self, const: Constant) -> None:
        typ = self._type(const.typ)
        val = self._expr(const.value)
        self._line(f"pub const {const.name}: {typ} = {val};")

    def _emit_struct(self, struct: Struct) -> None:
        self.current_struct = struct.name
        self._line(f"pub const {struct.name} = struct {{")
        self.indent += 1
        for fld in struct.fields:
            self._emit_field(fld)
        if struct.fields and struct.methods:
            self._line("")
        for i, method in enumerate(struct.methods):
            if i > 0:
                self._line("")
            self._emit_method(method)
        self.indent -= 1
        self._line("};")
        self._line("")
        self.current_struct = ""

    def _emit_field(self, fld: Field) -> None:
        typ = self._type(fld.typ)
        self._line(f"{to_snake(fld.name)}: {typ},")

    def _emit_function(self, func: Function) -> None:
        self.var_types = {}  # Reset variable tracking for each function
        params = self._params(func.params)
        ret = self._type(func.ret)
        name = to_snake(func.name)
        pub = "pub " if not name.startswith("_") else ""
        if ret == "void":
            self._line(f"{pub}fn {name}({params}) void {{")
        else:
            self._line(f"{pub}fn {name}({params}) {ret} {{")
        self.indent += 1
        if not func.body:
            self._line("@panic(\"todo\");")
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")
        self._line("")

    def _emit_method(self, func: Function) -> None:
        self.var_types = {}  # Reset variable tracking for each method
        params = self._method_params(func.params, func.receiver)
        ret = self._type(func.ret)
        name = to_snake(func.name)
        pub = "pub " if not name.startswith("_") else ""
        if func.receiver:
            self.receiver_name = func.receiver.name
        if ret == "void":
            self._line(f"{pub}fn {name}({params}) void {{")
        else:
            self._line(f"{pub}fn {name}({params}) {ret} {{")
        self.indent += 1
        if not func.body:
            self._line("@panic(\"todo\");")
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")
        self.receiver_name = None

    def _params(self, params: list) -> str:
        parts = []
        for p in params:
            typ = self._type(p.typ)
            parts.append(f"{to_snake(p.name)}: {typ}")
        return ", ".join(parts)

    def _method_params(self, params: list, receiver: Receiver | None) -> str:
        parts = []
        if receiver:
            if receiver.mutable:
                parts.append(f"self: *{receiver.typ.name}")
            else:
                parts.append(f"self: *const {receiver.typ.name}")
        for p in params:
            typ = self._type(p.typ)
            parts.append(f"{to_snake(p.name)}: {typ}")
        return ", ".join(parts)

    def _emit_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDecl(name=name, typ=typ, value=value):
                zig_type = self._type(typ)
                self.var_types[name] = typ  # Track variable type
                keyword = "var" if getattr(stmt, 'is_reassigned', False) else "const"
                if value is not None:
                    val = self._expr(value)
                    # Omit type when it can be inferred (simple expressions)
                    if _can_infer_type(value):
                        self._line(f"{keyword} {to_snake(name)} = {val};")
                    else:
                        self._line(f"{keyword} {to_snake(name)}: {zig_type} = {val};")
                else:
                    default = self._default_value(typ)
                    self._line(f"{keyword} {to_snake(name)}: {zig_type} = {default};")
            case Assign(target=target, value=value):
                lv = self._lvalue(target)
                # Detect x = x + 1 -> x += 1 or x = x - 1 -> x -= 1
                if isinstance(target, VarLV) and isinstance(value, BinaryOp):
                    if isinstance(value.left, Var) and value.left.name == target.name:
                        if value.op == "+" and isinstance(value.right, IntLit) and value.right.value == 1:
                            self._line(f"{lv} += 1;")
                            return
                        if value.op == "-" and isinstance(value.right, IntLit) and value.right.value == 1:
                            self._line(f"{lv} -= 1;")
                            return
                        # General case: x = x op y -> x op= y
                        if value.op in ("+", "-", "*", "/"):
                            self._line(f"{lv} {value.op}= {self._expr(value.right)};")
                            return
                val = self._expr(value)
                self._line(f"{lv} = {val};")
            case OpAssign(target=target, op=op, value=value):
                lv = self._lvalue(target)
                val = self._expr(value)
                self._line(f"{lv} {op}= {val};")
            case ExprStmt(expr=expr):
                e = self._expr(expr)
                # Zig requires discarding unused values, but not for void
                if _is_void_expr(expr):
                    self._line(f"{e};")
                elif not e.endswith(";"):
                    self._line(f"_ = {e};")
            case Return(value=value):
                if value is not None:
                    self._line(f"return {self._expr(value)};")
                else:
                    self._line("return;")
            case If(cond=cond, then_body=then_body, else_body=else_body, init=init):
                if init is not None:
                    self._emit_stmt(init)
                self._line(f"if ({self._expr(cond)}) {{")
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
                self._emit_type_switch(expr, binding, cases, default)
            case Match(expr=expr, cases=cases, default=default):
                self._emit_match(expr, cases, default)
            case ForRange(index=index, value=value, iterable=iterable, body=body):
                self._emit_for_range(index, value, iterable, body)
            case ForClassic(init=init, cond=cond, post=post, body=body):
                self._emit_for_classic(init, cond, post, body)
            case While(cond=cond, body=body):
                self._line(f"while ({self._expr(cond)}) {{")
                self.indent += 1
                for s in body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("}")
            case Break(label=label):
                if label:
                    self._line(f"break :{label};")
                else:
                    self._line("break;")
            case Continue(label=label):
                if label:
                    self._line(f"continue :{label};")
                else:
                    self._line("continue;")
            case Block(body=body):
                self._line("{")
                self.indent += 1
                for s in body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("}")
            case TryCatch(body=body, catch_var=catch_var, catch_body=catch_body, reraise=reraise):
                self._emit_try_catch(body, catch_var, catch_body, reraise)
            case Raise(error_type=error_type, message=message, pos=pos):
                msg = self._expr(message)
                self._line(f"@panic({msg});")
            case SoftFail():
                self._line("return null;")
            case _:
                self._line(f"// TODO: {type(stmt).__name__}")

    def _emit_type_switch(
        self, expr: Expr, binding: str, cases: list[TypeCase], default: list[Stmt]
    ) -> None:
        var = self._expr(expr)
        self._line(f"// type switch on {var}")
        self._line(f"const {to_snake(binding)} = {var};")
        # Zig doesn't have runtime type switching like Go, emit as if-else chain
        for i, case in enumerate(cases):
            type_name = self._type_name_for_check(case.typ)
            keyword = "if" if i == 0 else "} else if"
            self._line(f"{keyword} (@TypeOf({var}) == {type_name}) {{")
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
        expr_str = self._expr(expr)
        # Check if matching on strings - Zig can't switch on strings, use if-else
        is_string_match = _is_string_type(expr.typ) if hasattr(expr, 'typ') else False
        if is_string_match:
            self._emit_string_match(expr_str, cases, default)
        else:
            self._line(f"switch ({expr_str}) {{")
            self.indent += 1
            for case in cases:
                patterns = ", ".join(self._expr(p) for p in case.patterns)
                self._line(f"{patterns} => {{")
                self.indent += 1
                for s in case.body:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("},")
            if default:
                self._line("else => {")
                self.indent += 1
                for s in default:
                    self._emit_stmt(s)
                self.indent -= 1
                self._line("},")
            self.indent -= 1
            self._line("}")

    def _emit_string_match(self, expr_str: str, cases: list, default: list[Stmt]) -> None:
        """Emit string matching as if-else chain using mem.eql."""
        for i, case in enumerate(cases):
            # Build condition: check all patterns with OR
            conditions = []
            for p in case.patterns:
                pat_str = self._expr(p)
                conditions.append(f"mem.eql(u8, {expr_str}, {pat_str})")
            cond = " or ".join(conditions)
            keyword = "if" if i == 0 else "} else if"
            self._line(f"{keyword} ({cond}) {{")
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
        # ArrayList needs .items to iterate
        if isinstance(iterable.typ, Slice):
            iter_expr = f"{iter_expr}.items"
        if value is not None and index is not None:
            # Zig for with index requires manual tracking or enumeration
            self._line(f"for ({iter_expr}, 0..) |{to_snake(value)}, {to_snake(index)}| {{")
        elif value is not None:
            self._line(f"for ({iter_expr}) |{to_snake(value)}| {{")
        elif index is not None:
            self._line(f"for ({iter_expr}, 0..) |_, {to_snake(index)}| {{")
        else:
            self._line(f"for ({iter_expr}) |_| {{")
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
        # Zig doesn't have C-style for loops, convert to while
        if init is not None:
            self._emit_stmt(init)
        cond_str = self._expr(cond) if cond else "true"
        self._line(f"while ({cond_str}) {{")
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
    ) -> None:
        # Zig uses error unions - wrap in a block and handle errors inline
        # This is a simplified approach; full error handling would need function signatures
        if catch_body:
            # Emit body directly, catch is handled at call sites with 'catch'
            self._line("// Note: error handling simplified - Zig uses error unions")
            for s in body:
                self._emit_stmt(s)
        else:
            for s in body:
                self._emit_stmt(s)

    def _expr(self, expr: Expr) -> str:
        match expr:
            case IntLit(value=value):
                # Use character literals for common ASCII values
                if value == 32:
                    return "' '"
                if value == 10:
                    return "'\\n'"
                if value == 9:
                    return "'\\t'"
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
                    return "self"
                if name.isupper():
                    return name
                return to_snake(name)
            case FieldAccess(obj=obj, field=field):
                obj_str = self._expr(obj)
                # Unwrap optional with .? before field access
                # Check both the expression type and tracked variable type
                is_optional = isinstance(obj.typ, Optional)
                if isinstance(obj, Var) and obj.name in self.var_types:
                    is_optional = isinstance(self.var_types[obj.name], Optional)
                if is_optional:
                    obj_str = f"{obj_str}.?"
                return f"{obj_str}.{to_snake(field)}"
            case Index(obj=obj, index=index):
                # Check if indexing a tuple - use field access instead
                if isinstance(obj.typ, Tuple) and isinstance(index, IntLit):
                    return f"{self._expr(obj)}.f{index.value}"
                # For ArrayList, use .items for indexing
                obj_str = self._expr(obj)
                if isinstance(obj.typ, Slice):
                    obj_str = f"{obj_str}.items"
                # Cast index to usize if it's an integer expression
                idx_str = self._expr(index)
                if _needs_usize_cast(index):
                    idx_str = f"@intCast({idx_str})"
                return f"{obj_str}[{idx_str}]"
            case SliceExpr(obj=obj, low=low, high=high):
                return self._slice_expr(obj, low, high)
            case Call(func=func, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                return f"{to_snake(func)}({args_str})"
            case MethodCall(obj=obj, method=method, args=args, receiver_type=receiver_type):
                return self._method_call(obj, method, args, receiver_type)
            case StaticCall(on_type=on_type, method=method, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                type_name = self._type_name_for_check(on_type)
                return f"{type_name}.{to_snake(method)}({args_str})"
            case BinaryOp(op=op, left=left, right=right):
                zig_op = _binary_op(op)
                # String comparison needs mem.eql
                if zig_op == "==" and _is_string_type(left.typ):
                    return f"mem.eql(u8, {self._expr(left)}, {self._expr(right)})"
                if zig_op == "!=" and _is_string_type(left.typ):
                    return f"!mem.eql(u8, {self._expr(left)}, {self._expr(right)})"
                # Add parens only for compound expressions or low-precedence ops
                left_str = self._expr(left)
                right_str = self._expr(right)
                # Cast int to usize when comparing with .len (but not literals)
                if _is_len_expr(right) and _is_int_type(left.typ) and not isinstance(left, IntLit):
                    left_str = f"@intCast({left_str})"
                elif _is_len_expr(left) and _is_int_type(right.typ) and not isinstance(right, IntLit):
                    right_str = f"@intCast({right_str})"
                if _needs_parens(left):
                    left_str = f"({left_str})"
                if _needs_parens(right):
                    right_str = f"({right_str})"
                return f"{left_str} {zig_op} {right_str}"
            case UnaryOp(op=op, operand=operand):
                zig_op = "!" if op == "!" else op
                return f"{zig_op}{self._expr(operand)}"
            case Ternary(cond=cond, then_expr=then_expr, else_expr=else_expr):
                # Zig has if expressions
                return f"if ({self._expr(cond)}) {self._expr(then_expr)} else {self._expr(else_expr)}"
            case Cast(expr=inner, to_type=to_type):
                return self._cast(inner, to_type)
            case TypeAssert(expr=inner, asserted=asserted, safe=safe):
                # Zig doesn't have dynamic type assertions
                return self._expr(inner)
            case IsType(expr=inner, tested_type=tested_type):
                type_name = self._type_name_for_check(tested_type)
                return f"@TypeOf({self._expr(inner)}) == {type_name}"
            case IsNil(expr=inner, negated=negated):
                if negated:
                    return f"{self._expr(inner)} != null"
                return f"{self._expr(inner)} == null"
            case Len(expr=inner):
                inner_str = self._expr(inner)
                # ArrayList uses .items.len
                if isinstance(inner.typ, Slice):
                    return f"{inner_str}.items.len"
                return f"{inner_str}.len"
            case MakeSlice(element_type=element_type, length=length, capacity=capacity):
                typ = self._type(element_type)
                if capacity:
                    cap_str = self._expr(capacity)
                    if _needs_usize_cast(capacity):
                        cap_str = f"@intCast({cap_str})"
                    return f"ArrayList({typ}).initCapacity(allocator, {cap_str}) catch unreachable"
                if length:
                    len_str = self._expr(length)
                    if _needs_usize_cast(length):
                        len_str = f"@intCast({len_str})"
                    return f"ArrayList({typ}).initCapacity(allocator, {len_str}) catch unreachable"
                return f"ArrayList({typ}).init(allocator)"
            case MakeMap(key_type=key_type, value_type=value_type):
                kt = self._type(key_type)
                vt = self._type(value_type)
                if kt == "[]const u8":
                    return f"std.StringHashMap({vt}).init(allocator)"
                return f"std.AutoHashMap({kt}, {vt}).init(allocator)"
            case SliceLit(elements=elements, element_type=element_type):
                typ = self._type(element_type)
                if not elements:
                    return f"ArrayList({typ}).init(allocator)"
                # For non-empty literals, init and add elements would be verbose
                # Just return an empty ArrayList for now
                return f"ArrayList({typ}).init(allocator)"
            case MapLit(entries=entries, key_type=key_type, value_type=value_type):
                kt = self._type(key_type)
                vt = self._type(value_type)
                map_type = f"std.StringHashMap({vt})" if kt == "[]const u8" else f"std.AutoHashMap({kt}, {vt})"
                if not entries:
                    return f"{map_type}.init(allocator)"
                # Use block expression to populate map
                puts = " ".join(f"m.put({self._expr(k)}, {self._expr(v)}) catch unreachable;" for k, v in entries)
                return f"blk: {{ var m = {map_type}.init(allocator); {puts} break :blk m; }}"
            case SetLit(elements=elements, element_type=element_type):
                et = self._type(element_type)
                set_type = f"std.StringHashMap(void)" if et == "[]const u8" else f"std.AutoHashMap({et}, void)"
                if not elements:
                    return f"{set_type}.init(allocator)"
                # Use block expression to populate set
                puts = " ".join(f"s.put({self._expr(e)}, {{}}) catch unreachable;" for e in elements)
                return f"blk: {{ var s = {set_type}.init(allocator); {puts} break :blk s; }}"
            case StructLit(struct_name=struct_name, fields=fields):
                if not fields:
                    return f"{struct_name}{{}}"
                args = ", ".join(f".{to_snake(k)} = {self._expr(v)}" for k, v in fields.items())
                return f"{struct_name}{{ {args} }}"
            case TupleLit(elements=elements):
                # Use named fields f0, f1, etc. to match the struct type
                parts = ", ".join(f".f{i} = {self._expr(e)}" for i, e in enumerate(elements))
                return f".{{ {parts} }}"
            case StringConcat(parts=parts):
                if len(parts) == 1:
                    return self._expr(parts[0])
                # Zig uses ++ for array/slice concat
                return " ++ ".join(self._expr(p) for p in parts)
            case StringFormat(template=template, args=args):
                return self._format_string(template, args)
            case _:
                return f"undefined // TODO: {type(expr).__name__}"

    def _method_call(self, obj: Expr, method: str, args: list[Expr], receiver_type: Type) -> str:
        args_str = ", ".join(self._expr(a) for a in args)
        obj_str = self._expr(obj)
        # Handle ArrayList methods
        if isinstance(receiver_type, Slice):
            if method == "append" and args:
                return f"{obj_str}.append({args_str}) catch unreachable"
            if method == "pop" and not args:
                return f"{obj_str}.pop()"
        return f"{obj_str}.{to_snake(method)}({args_str})"

    def _slice_expr(self, obj: Expr, low: Expr | None, high: Expr | None) -> str:
        obj_str = self._expr(obj)
        # Cast indices to usize
        low_str = f"@intCast({self._expr(low)})" if low and _needs_usize_cast(low) else (self._expr(low) if low else "0")
        high_str = f"@intCast({self._expr(high)})" if high and _needs_usize_cast(high) else (self._expr(high) if high else None)
        if high_str:
            return f"{obj_str}[{low_str}..{high_str}]"
        else:
            return f"{obj_str}[{low_str}..]"

    def _cast(self, inner: Expr, to_type: Type) -> str:
        inner_str = self._expr(inner)
        zig_type = self._type(to_type)
        # Zig uses @intCast, @floatFromInt, etc.
        if isinstance(to_type, Primitive):
            if to_type.kind == "int":
                return f"@intCast({inner_str})"
            if to_type.kind == "float":
                # Int to float uses @floatFromInt
                if hasattr(inner, 'typ') and isinstance(inner.typ, Primitive) and inner.typ.kind == "int":
                    return f"@floatFromInt({inner_str})"
                return f"@floatCast({inner_str})"
            if to_type.kind == "byte":
                return f"@intCast({inner_str})"
        return f"@as({zig_type}, {inner_str})"

    def _format_string(self, template: str, args: list[Expr]) -> str:
        # Convert {0}, {1}, etc. and %v to {} for Zig
        import re
        result = re.sub(r'\{\d+\}', '{}', template)
        result = result.replace("%v", "{}").replace("%%", "%")
        escaped = result.replace("\\", "\\\\").replace('"', '\\"')
        args_str = ", ".join(self._expr(a) for a in args)
        if args_str:
            return f'std.fmt.allocPrint(allocator, "{escaped}", .{{ {args_str} }}) catch unreachable'
        return f'"{escaped}"'

    def _lvalue(self, lv: LValue) -> str:
        match lv:
            case VarLV(name=name):
                if name == self.receiver_name:
                    return "self"
                return to_snake(name)
            case FieldLV(obj=obj, field=field):
                return f"{self._expr(obj)}.{to_snake(field)}"
            case IndexLV(obj=obj, index=index):
                obj_str = self._expr(obj)
                # ArrayList needs .items for indexing
                if isinstance(obj.typ, Slice):
                    obj_str = f"{obj_str}.items"
                idx_str = self._expr(index)
                if _needs_usize_cast(index):
                    idx_str = f"@intCast({idx_str})"
                return f"{obj_str}[{idx_str}]"
            case DerefLV(ptr=ptr):
                return f"{self._expr(ptr)}.*"
            case _:
                return f"undefined // lvalue: {type(lv).__name__}"

    def _type(self, typ: Type) -> str:
        match typ:
            case Primitive(kind=kind):
                return _primitive_type(kind)
            case Slice(element=element):
                # Use ArrayList for mutable slices
                return f"ArrayList({self._type(element)})"
            case Array(element=element, size=size):
                return f"[{size}]{self._type(element)}"
            case Map(key=key, value=value):
                kt = self._type(key)
                vt = self._type(value)
                if kt == "[]const u8":
                    return f"std.StringHashMap({vt})"
                return f"std.AutoHashMap({kt}, {vt})"
            case Set(element=element):
                et = self._type(element)
                if et == "[]const u8":
                    return "std.StringHashMap(void)"
                return f"std.AutoHashMap({et}, void)"
            case Tuple(elements=elements):
                # Use f0, f1, etc. as field names for tuple structs
                parts = ", ".join(f"f{i}: {self._type(e)}" for i, e in enumerate(elements))
                return f"struct {{ {parts} }}"
            case Pointer(target=target):
                return f"*{self._type(target)}"
            case Optional(inner=inner):
                return f"?{self._type(inner)}"
            case StructRef(name=name):
                return name
            case Interface(name=name):
                if name == "any":
                    return "*anyopaque"
                return name
            case Union(name=name, variants=variants):
                if name:
                    return name
                if variants:
                    # Generate anonymous tagged union
                    fields = ", ".join(f"v{i}: {self._type(v)}" for i, v in enumerate(variants))
                    return f"union(enum) {{ {fields} }}"
                return "anytype"
            case FuncType(params=params, ret=ret):
                params_str = ", ".join(self._type(p) for p in params)
                ret_str = self._type(ret)
                return f"*const fn({params_str}) {ret_str}"
            case StringSlice():
                return "[]const u8"
            case _:
                return "*anyopaque"

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
                return "&[_]{}"
            case Optional():
                return "null"
            case _:
                return "undefined"


def _primitive_type(kind: str) -> str:
    match kind:
        case "string":
            return "[]const u8"
        case "int":
            return "i64"
        case "float":
            return "f64"
        case "bool":
            return "bool"
        case "byte":
            return "u8"
        case "rune":
            return "u21"  # Unicode code point
        case "void":
            return "void"
        case _:
            return "*anyopaque"


def _binary_op(op: str) -> str:
    match op:
        case "&&":
            return "and"
        case "||":
            return "or"
        case _:
            return op


def _is_string_type(typ: Type) -> bool:
    if isinstance(typ, Primitive) and typ.kind == "string":
        return True
    if isinstance(typ, StringSlice):
        return True
    return False


def _string_literal(value: str) -> str:
    return f'"{escape_string(value)}"'


def _is_void_expr(expr: Expr) -> bool:
    """Check if expression has void return type."""
    if hasattr(expr, "typ"):
        typ = expr.typ
        if isinstance(typ, Primitive) and typ.kind == "void":
            return True
    return False


def _needs_parens(expr: Expr) -> bool:
    """Check if expression needs parentheses when used as operand."""
    # Compound binary ops with lower precedence need parens
    if isinstance(expr, BinaryOp):
        return expr.op in ("&&", "||", "and", "or")
    return False


def _needs_usize_cast(expr: Expr) -> bool:
    """Check if expression needs @intCast to usize for indexing."""
    # Integer literals don't need cast (Zig infers)
    if isinstance(expr, IntLit):
        return False
    # Variables and expressions with int type need cast
    if hasattr(expr, "typ") and isinstance(expr.typ, Primitive):
        return expr.typ.kind == "int"
    return False


def _is_len_expr(expr: Expr) -> bool:
    """Check if expression is a .len access (returns usize)."""
    return isinstance(expr, Len)


def _is_int_type(typ: Type) -> bool:
    """Check if type is an integer type."""
    return isinstance(typ, Primitive) and typ.kind == "int"


def _can_infer_type(expr: Expr) -> bool:
    """Check if Zig can infer the type from this expression."""
    # Function/method calls - Zig knows the return type
    if isinstance(expr, (Call, MethodCall, StaticCall)):
        return True
    # Field access - type is known from struct definition
    if isinstance(expr, FieldAccess):
        return True
    # Index into tuple - type is known
    if isinstance(expr, Index):
        return True
    # Struct literals with explicit type name
    if isinstance(expr, StructLit):
        return True
    return False
