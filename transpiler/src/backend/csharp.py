"""C# backend: IR → C# code."""

from __future__ import annotations

from src.backend.util import escape_string, to_camel, to_pascal, to_screaming_snake
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

# C# reserved words that need escaping with @
_CSHARP_RESERVED = frozenset(
    {
        "abstract",
        "as",
        "base",
        "bool",
        "break",
        "byte",
        "case",
        "catch",
        "char",
        "checked",
        "class",
        "const",
        "continue",
        "decimal",
        "default",
        "delegate",
        "do",
        "double",
        "else",
        "enum",
        "event",
        "explicit",
        "extern",
        "false",
        "finally",
        "fixed",
        "float",
        "for",
        "foreach",
        "goto",
        "if",
        "implicit",
        "in",
        "int",
        "interface",
        "internal",
        "is",
        "lock",
        "long",
        "namespace",
        "new",
        "null",
        "object",
        "operator",
        "out",
        "override",
        "params",
        "private",
        "protected",
        "public",
        "readonly",
        "ref",
        "return",
        "sbyte",
        "sealed",
        "short",
        "sizeof",
        "stackalloc",
        "static",
        "string",
        "struct",
        "switch",
        "this",
        "throw",
        "true",
        "try",
        "typeof",
        "uint",
        "ulong",
        "unchecked",
        "unsafe",
        "ushort",
        "using",
        "virtual",
        "void",
        "volatile",
        "while",
    }
)


def _safe_name(name: str) -> str:
    """Escape C# reserved words with @ prefix."""
    result = to_camel(name)
    if result in _CSHARP_RESERVED:
        return "@" + result
    return result


def _to_pascal_preserve(name: str) -> str:
    """Convert to PascalCase, preserving already-capitalized segments and leading underscore."""
    prefix = ""
    if name.startswith("_"):
        prefix = "_"
        name = name[1:]
    if "_" not in name:
        # Already camelCase or PascalCase - just uppercase first letter
        return prefix + (name[0].upper() + name[1:] if name else name)
    # snake_case - capitalize each segment
    parts = name.split("_")
    return prefix + "".join(p[0].upper() + p[1:] if p else "" for p in parts)


def _safe_pascal(name: str) -> str:
    """Convert to PascalCase and escape reserved words."""
    result = _to_pascal_preserve(name)
    if result in _CSHARP_RESERVED:
        return "@" + result
    return result


class CSharpBackend:
    """Emit C# code from IR."""

    def __init__(self) -> None:
        self.indent = 0
        self.lines: list[str] = []
        self.receiver_name: str | None = None
        self.current_class: str = ""
        self.struct_fields: dict[str, list[tuple[str, Type]]] = {}
        self._hoisted_vars: set[str] = set()
        self._declared_vars: set[str] = set()  # All variables declared in current function
        self._object_vars: set[str] = set()  # Variables declared with object type
        self._module_name: str = ""
        self._interface_names: set[str] = set()
        self.temp_counter = 0
        self._type_switch_binding_rename: dict[str, str] = {}
        self._loop_temp_counter = 0
        self._func_params: set[str] = set()

    def emit(self, module: Module) -> str:
        """Emit C# code from IR Module."""
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
            self.lines.append("    " * self.indent + text)
        else:
            self.lines.append("")

    def _emit_module(self, module: Module) -> None:
        self._line("using System;")
        self._line("using System.Collections.Generic;")
        self._line("using System.Linq;")
        self._line("")
        if module.constants:
            self._line("public static class Constants")
            self._line("{")
            self.indent += 1
            for const in module.constants:
                self._emit_constant(const)
            self.indent -= 1
            self._line("}")
            self._line("")
        for iface in module.interfaces:
            self._emit_interface(iface)
            self._line("")
        for struct in module.structs:
            self._emit_struct(struct)
            self._line("")
        if module.functions:
            self._emit_functions_class(module)

    def _emit_constant(self, const: Constant) -> None:
        typ = self._type(const.typ)
        val = self._expr(const.value)
        name = to_screaming_snake(const.name)
        # Only primitive types and strings can be const in C#
        if isinstance(const.typ, Primitive) and const.typ.kind in ("int", "float", "bool", "string"):
            self._line(f"public const {typ} {name} = {val};")
        else:
            self._line(f"public static readonly {typ} {name} = {val};")

    def _emit_interface(self, iface: InterfaceDef) -> None:
        self._line(f"public interface I{iface.name}")
        self._line("{")
        self.indent += 1
        # Emit interface fields as properties
        for fld in iface.fields:
            typ = self._type(fld.typ)
            name = _safe_pascal(fld.name)
            self._line(f"{typ} {name} {{ get; }}")
        for method in iface.methods:
            params = self._params(method.params)
            ret = self._type(method.ret)
            name = _safe_pascal(method.name)
            self._line(f"{ret} {name}({params});")
        self.indent -= 1
        self._line("}")

    def _emit_struct(self, struct: Struct) -> None:
        class_name = struct.name
        self.current_class = class_name
        extends_clause = ""
        if struct.is_exception:
            parent = struct.embedded_type or "Exception"
            extends_clause = f" : {parent}"
        elif struct.implements:
            impl_names = [f"I{n}" for n in struct.implements]
            extends_clause = f" : {', '.join(impl_names)}"
        self._line(f"public class {class_name}{extends_clause}")
        self._line("{")
        self.indent += 1
        for fld in struct.fields:
            self._emit_field(fld, struct.is_exception)
        if struct.fields:
            self._line("")
        self._emit_constructor(struct)
        for i, method in enumerate(struct.methods):
            self._line("")
            self._emit_method(method)
        self.indent -= 1
        self._line("}")
        self.current_class = ""

    def _emit_field(self, fld: Field, is_exception: bool = False) -> None:
        typ = self._type(fld.typ)
        name = _safe_pascal(fld.name)
        modifier = "new " if is_exception and name == "Message" else ""
        self._line(f"public {modifier}{typ} {name} {{ get; set; }}")

    def _emit_constructor(self, struct: Struct) -> None:
        class_name = struct.name
        if not struct.fields:
            if struct.is_exception and struct.embedded_type:
                # Child exception with no additional fields - pass all args to base
                self._line(f"public {class_name}(string message, int pos, int code) : base(message, pos, code) {{ }}")
            elif struct.is_exception:
                self._line(f"public {class_name}(string message) : base(message) {{ }}")
            return
        params = ", ".join(f"{self._type(f.typ)} {_safe_name(f.name)}" for f in struct.fields)
        if struct.is_exception and not struct.embedded_type:
            # Base exception class - needs to call Exception base
            self._line(f"public {class_name}({params}) : base(message)")
        else:
            self._line(f"public {class_name}({params})")
        self._line("{")
        self.indent += 1
        for f in struct.fields:
            param_name = _safe_name(f.name)
            prop_name = _safe_pascal(f.name)
            self._line(f"this.{prop_name} = {param_name};")
        self.indent -= 1
        self._line("}")

    def _emit_functions_class(self, module: Module) -> None:
        class_name = to_pascal(module.name) + "Functions"
        self._line(f"public static class {class_name}")
        self._line("{")
        self.indent += 1
        for i, func in enumerate(module.functions):
            if i > 0:
                self._line("")
            self._emit_function(func)
        self.indent -= 1
        self._line("}")

    def _emit_function(self, func: Function) -> None:
        self._hoisted_vars = set()
        self._declared_vars = {p.name for p in func.params}  # Track all declared vars
        self._object_vars = set()
        self._func_params = {p.name for p in func.params if isinstance(p.typ, FuncType)}
        params = self._params(func.params)
        ret = self._type(func.ret)
        name = _safe_pascal(func.name)
        # Special case: _substring needs clamping to match Python slice semantics
        if func.name == "_substring":
            self._line(f"public static {ret} {name}({params})")
            self._line("{")
            self.indent += 1
            self._line("int len = s.Length;")
            self._line("int clampedStart = Math.Max(0, Math.Min(start, len));")
            self._line("int clampedEnd = Math.Max(clampedStart, Math.Min(end, len));")
            self._line("return s.Substring(clampedStart, clampedEnd - clampedStart);")
            self.indent -= 1
            self._line("}")
            return
        self._line(f"public static {ret} {name}({params})")
        self._line("{")
        self.indent += 1
        if not func.body:
            self._line('throw new NotImplementedException();')
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")

    def _emit_method(self, func: Function) -> None:
        self._hoisted_vars = set()
        self._declared_vars = {p.name for p in func.params}  # Track all declared vars
        self._object_vars = set()
        self._func_params = {p.name for p in func.params if isinstance(p.typ, FuncType)}
        params = self._params(func.params)
        ret = self._type(func.ret)
        name = _safe_pascal(func.name)
        if func.receiver:
            self.receiver_name = func.receiver.name
        self._line(f"public {ret} {name}({params})")
        self._line("{")
        self.indent += 1
        if not func.body:
            self._line('throw new NotImplementedException();')
        for stmt in func.body:
            self._emit_stmt(stmt)
        self.indent -= 1
        self._line("}")
        self.receiver_name = None

    def _params(self, params: list[Param]) -> str:
        parts = []
        for p in params:
            typ = self._type(p.typ)
            parts.append(f"{typ} {_safe_name(p.name)}")
        return ", ".join(parts)

    def _emit_hoisted_vars(
        self, stmt: If | While | ForRange | ForClassic | TryCatch | Match | TypeSwitch
    ) -> None:
        hoisted_vars = stmt.hoisted_vars
        for name, typ in hoisted_vars:
            cs_type = self._type(typ) if typ else "object"
            var_name = _safe_name(name)
            default = self._default_value(typ) if typ else "null"
            self._line(f"{cs_type} {var_name} = {default};")
            self._hoisted_vars.add(name)
            self._declared_vars.add(name)
            if cs_type == "object":
                self._object_vars.add(name)

    def _emit_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDecl(name=name, typ=typ, value=value):
                cs_type = self._type(typ)
                var_name = _safe_name(name)
                self._declared_vars.add(name)
                if cs_type == "object":
                    self._object_vars.add(name)
                if value is not None:
                    val = self._expr(value)
                    self._line(f"{cs_type} {var_name} = {val};")
                else:
                    default = self._default_value(typ)
                    self._line(f"{cs_type} {var_name} = {default};")
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
                        # Prefer decl_typ (unified type from frontend) over value.typ
                        decl_type = stmt.decl_typ if stmt.decl_typ is not None else value.typ
                        cs_type = self._type(decl_type) if decl_type else "object"
                        self._line(f"{cs_type} {lv} = {val};")
                        if target_name:
                            self._declared_vars.add(target_name)
                            if cs_type == "object":
                                self._object_vars.add(target_name)
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
                saved_hoisted = self._hoisted_vars.copy()
                for s in then_body:
                    self._emit_stmt(s)
                self._hoisted_vars = saved_hoisted
                self.indent -= 1
                if else_body:
                    self._line("}")
                    self._line("else")
                    self._line("{")
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
                    self._line("throw;")
                else:
                    msg = self._expr(message)
                    pos_expr = self._expr(pos)
                    self._line(f"throw new {error_type}({msg}, {pos_expr}, 0);")
            case SoftFail():
                self._line("return null;")
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
            # C# supports tuple deconstruction - check if any target needs declaring
            decls = []
            for i, target in enumerate(targets):
                target_name = target.name if isinstance(target, VarLV) else f"_t{i}"
                is_hoisted = target_name in self._hoisted_vars
                is_new = is_decl or (target_name and target_name in new_targets)
                if is_hoisted or not is_new:
                    # Variable already exists, just use name
                    decls.append(_safe_name(target_name))
                else:
                    # New variable, need to declare with type
                    elem_type = value_type.elements[i] if i < len(value_type.elements) else None
                    cs_type = self._type(elem_type) if elem_type else "var"
                    decls.append(f"{cs_type} {_safe_name(target_name)}")
            self._line(f"({', '.join(decls)}) = {val_str};")
        else:
            # Fallback for non-tuple multi-returns
            val_str = self._expr(value)
            self._line(f"var _tuple = {val_str};")
            for i, target in enumerate(targets):
                lv = self._lvalue(target)
                target_name = target.name if isinstance(target, VarLV) else None
                is_hoisted = target_name and target_name in self._hoisted_vars
                if (is_decl or (target_name and target_name in new_targets)) and not is_hoisted:
                    self._line(f"var {lv} = _tuple.Item{i+1};")
                else:
                    self._line(f"{lv} = _tuple.Item{i+1};")

    def _emit_tuple_pop(self, stmt: TupleAssign) -> None:
        """Emit tuple unpacking from list.pop().

        C# List doesn't have pop() that returns the element, so expand to:
            _entry = list[list.Count - 1];
            list.RemoveAt(list.Count - 1);
            a = _entry.Item1;
            b = _entry.Item2;
        """
        mc = stmt.value
        if not isinstance(mc, MethodCall):
            return
        obj = self._expr(mc.obj)
        # Get the index (size-1 for pop())
        if mc.args:
            index = self._expr(mc.args[0])
        else:
            index = f"{obj}.Count - 1"
        # Get tuple type from the list's element type
        obj_type = mc.obj.typ if mc.obj else None
        elem_type = obj_type.element if isinstance(obj_type, Slice) else mc.typ
        tuple_type = self._type(elem_type) if elem_type else "object"
        # Emit: _entry = list[index]
        self.temp_counter += 1
        entry_var = f"_entry{self.temp_counter}"
        self._line(f"{tuple_type} {entry_var} = {obj}[{index}];")
        # Emit: list.RemoveAt(index)
        self._line(f"{obj}.RemoveAt({index});")
        # Emit field assignments
        is_decl = stmt.is_declaration
        new_targets = stmt.new_targets
        for i, target in enumerate(stmt.targets):
            lv = self._lvalue(target)
            target_name = target.name if isinstance(target, VarLV) else None
            is_hoisted = target_name and target_name in self._hoisted_vars
            if isinstance(elem_type, Tuple) and i < len(elem_type.elements):
                field_type = self._type(elem_type.elements[i])
            else:
                field_type = "object"
            if (is_decl or (target_name and target_name in new_targets)) and not is_hoisted:
                self._line(f"{field_type} {lv} = {entry_var}.Item{i + 1};")
            else:
                self._line(f"{lv} = {entry_var}.Item{i + 1};")

    def _is_terminal_stmt(self, stmt: Stmt) -> bool:
        """Check if a statement is a flow control terminator (no break needed after)."""
        return isinstance(stmt, (Return, Continue, Break, Raise))

    def _is_object_var(self, expr: Expr) -> bool:
        """Check if an expression is a variable declared with object type."""
        return isinstance(expr, Var) and expr.name in self._object_vars

    def _emit_type_switch(self, stmt: TypeSwitch) -> None:
        self._emit_hoisted_vars(stmt)
        var = self._expr(stmt.expr)
        binding = _safe_name(stmt.binding)
        cases = stmt.cases
        default = stmt.default
        self._line(f"switch ({var})")
        self._line("{")
        self.indent += 1
        for case in cases:
            type_name = self._type_name_for_check(case.typ)
            # Create unique narrowed name to avoid CS0136 variable shadowing
            narrowed_name = f"{binding}{type_name}"
            self._line(f"case {type_name} {narrowed_name}:")
            self.indent += 1
            # Track rename so Var references use narrowed name
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
        is_string = isinstance(iter_type, Primitive) and iter_type.kind == "string"
        index = stmt.index
        value = stmt.value
        body = stmt.body
        if value is not None and index is not None:
            idx = _safe_name(index)
            val = _safe_name(value)
            val_hoisted = value in self._hoisted_vars
            if is_string:
                self._line(f"for (int {idx} = 0; {idx} < {iter_expr}.Length; {idx}++)")
                self._line("{")
                self.indent += 1
                if val_hoisted:
                    self._line(f"{val} = {iter_expr}[{idx}].ToString();")
                else:
                    self._line(f"var {val} = {iter_expr}[{idx}].ToString();")
            else:
                self._line(f"for (int {idx} = 0; {idx} < {iter_expr}.Count; {idx}++)")
                self._line("{")
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
                self._line(f"foreach (var {temp_var} in {iter_expr})")
                self._line("{")
                self.indent += 1
                if is_hoisted:
                    self._line(f"{val} = {temp_var}.ToString();")
                else:
                    self._line(f"var {val} = {temp_var}.ToString();")
            else:
                elem_type = self._element_type(iter_type)
                # Use string for untyped list literals of strings
                if elem_type == "object":
                    elem_type = "string"
                if is_hoisted:
                    self._loop_temp_counter += 1
                    temp_var = f"_e{self._loop_temp_counter}"
                    self._line(f"foreach ({elem_type} {temp_var} in {iter_expr})")
                    self._line("{")
                    self.indent += 1
                    self._line(f"{val} = {temp_var};")
                else:
                    self._line(f"foreach ({elem_type} {val} in {iter_expr})")
                    self._line("{")
                    self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        elif index is not None:
            idx = _safe_name(index)
            if is_string:
                self._line(f"for (int {idx} = 0; {idx} < {iter_expr}.Length; {idx}++)")
            else:
                self._line(f"for (int {idx} = 0; {idx} < {iter_expr}.Count; {idx}++)")
            self._line("{")
            self.indent += 1
            for s in body:
                self._emit_stmt(s)
            self.indent -= 1
            self._line("}")
        else:
            if is_string:
                self._line(f"foreach (var _ in {iter_expr})")
            else:
                self._line(f"foreach (var _ in {iter_expr})")
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
                cs_type = self._type(typ)
                var_name = _safe_name(name)
                if cs_type == "object":
                    self._object_vars.add(name)
                if value:
                    return f"{cs_type} {var_name} = {self._expr(value)}"
                return f"{cs_type} {var_name}"
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
        self._line("try")
        self._line("{")
        self.indent += 1
        for s in stmt.body:
            self._emit_stmt(s)
        self.indent -= 1
        exc_type = stmt.catch_type.name if isinstance(stmt.catch_type, StructRef) else "Exception"
        if stmt.catch_var_unused or not stmt.catch_var:
            self._line(f"}} catch ({exc_type})")
        else:
            var = _safe_name(stmt.catch_var)
            self._line(f"}} catch ({exc_type} {var})")
        self._line("{")
        self.indent += 1
        for s in stmt.catch_body:
            self._emit_stmt(s)
        if stmt.reraise:
            self._line(f"throw;")
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
                if name.isupper() or (name[0].isupper() and "_" in name and name.split("_", 1)[1].isupper()):
                    return f"Constants.{to_screaming_snake(name)}"
                return _safe_name(name)
            case FieldAccess(obj=obj, field=field):
                obj_str = self._expr(obj)
                # Handle tuple field access (F0, F1 -> Item1, Item2)
                if isinstance(obj.typ, Tuple) and field.startswith("F") and field[1:].isdigit():
                    idx = int(field[1:]) + 1
                    return f"{obj_str}.Item{idx}"
                return f"{obj_str}.{_safe_pascal(field)}"
            case FuncRef(name=name, obj=obj):
                if obj is not None:
                    obj_str = self._expr(obj)
                    return f"{obj_str}.{_safe_pascal(name)}"
                return _safe_pascal(name)
            case Index(obj=obj, index=index):
                obj_str = self._expr(obj)
                idx_str = self._expr(index)
                obj_type = obj.typ
                if isinstance(obj_type, Tuple):
                    if isinstance(index, IntLit):
                        return f"{obj_str}.Item{index.value + 1}"
                    return f"{obj_str}.Item{idx_str}"
                if isinstance(obj_type, Map):
                    return f"{obj_str}[{idx_str}]"
                return f"{obj_str}[{idx_str}]"
            case SliceExpr(obj=obj, low=low, high=high):
                return self._slice_expr(obj, low, high)
            case ParseInt(string=s, base=b):
                return f"Convert.ToInt32({self._expr(s)}, {self._expr(b)})"
            case IntToStr(value=v):
                return f"{self._expr(v)}.ToString()"
            case CharClassify(kind=kind, char=char):
                method_map = {
                    "digit": "IsDigit",
                    "alpha": "IsLetter",
                    "alnum": "IsLetterOrDigit",
                    "space": "IsWhiteSpace",
                    "upper": "IsUpper",
                    "lower": "IsLower",
                }
                method = method_map[kind]
                char_str = self._expr(char)
                return f"({char_str}.Length > 0 && {char_str}.All(char.{method}))"
            case TrimChars(string=s, chars=chars, mode=mode):
                s_str = self._expr(s)
                if isinstance(chars, StringLit):
                    chars_arr = chars.value.replace("\\", "\\\\").replace("'", "\\'")
                    if mode == "both":
                        return f"{s_str}.Trim({self._expr(chars)}.ToCharArray())"
                    elif mode == "left":
                        return f"{s_str}.TrimStart({self._expr(chars)}.ToCharArray())"
                    else:
                        return f"{s_str}.TrimEnd({self._expr(chars)}.ToCharArray())"
                chars_str = self._expr(chars)
                if mode == "left":
                    return f"{s_str}.TrimStart({chars_str}.ToCharArray())"
                elif mode == "right":
                    return f"{s_str}.TrimEnd({chars_str}.ToCharArray())"
                else:
                    return f"{s_str}.Trim({chars_str}.ToCharArray())"
            case Call(func=func, args=args):
                return self._call(func, args)
            case MethodCall(obj=obj, method=method, args=args, receiver_type=receiver_type):
                return self._method_call(obj, method, args, receiver_type)
            case StaticCall(on_type=on_type, method=method, args=args):
                args_str = ", ".join(self._expr(a) for a in args)
                type_name = self._type_name_for_check(on_type)
                return f"{type_name}.{_safe_pascal(method)}({args_str})"
            case Truthy(expr=e):
                inner_str = self._expr(e)
                inner_type = e.typ
                if _is_string_type(inner_type):
                    return f"(!string.IsNullOrEmpty({inner_str}))"
                if isinstance(inner_type, (Slice, Map, Set)):
                    return f"({inner_str}.Count > 0)"
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
                cs_op = _binary_op(op)
                # Cast object-typed variables to string in string comparisons
                if cs_op in ("==", "!="):
                    if _is_string_type(left.typ) and self._is_object_var(right):
                        right_str = f"(string){right_str}"
                    elif _is_string_type(right.typ) and self._is_object_var(left):
                        left_str = f"(string){left_str}"
                if _is_string_type(left.typ):
                    if cs_op == "==":
                        return f"{left_str} == {right_str}"
                    if cs_op == "!=":
                        return f"{left_str} != {right_str}"
                    if cs_op == "<":
                        return f"string.Compare({left_str}, {right_str}) < 0"
                    if cs_op == "<=":
                        return f"string.Compare({left_str}, {right_str}) <= 0"
                    if cs_op == ">":
                        return f"string.Compare({left_str}, {right_str}) > 0"
                    if cs_op == ">=":
                        return f"string.Compare({left_str}, {right_str}) >= 0"
                # Wrap bitwise ops in parens to ensure correct precedence with comparisons
                if cs_op in ("&", "|", "^"):
                    return f"({left_str} {cs_op} {right_str})"
                # Add parens around || when inside && to preserve precedence
                if cs_op == "&&":
                    if isinstance(left, BinaryOp) and left.op == "||":
                        left_str = f"({left_str})"
                    if isinstance(right, BinaryOp) and right.op == "||":
                        right_str = f"({right_str})"
                return f"{left_str} {cs_op} {right_str}"
            case UnaryOp(op="&", operand=operand):
                return self._expr(operand)
            case UnaryOp(op="*", operand=operand):
                return self._expr(operand)
            case UnaryOp(op="!", operand=operand):
                operand_type = operand.typ
                operand_str = self._expr(operand)
                # Convert Python truthiness to C# explicit boolean checks
                if isinstance(operand_type, Primitive):
                    if operand_type.kind == "int":
                        return f"({operand_str} == 0)"
                    if operand_type.kind == "string":
                        return f"string.IsNullOrEmpty({operand_str})"
                    if operand_type.kind == "bool":
                        return f"!({operand_str})"
                if isinstance(operand_type, (InterfaceRef, StructRef, Pointer)):
                    return f"({operand_str} == null)"
                if isinstance(operand_type, Slice):
                    return f"({operand_str}.Count == 0)"
                if isinstance(operand_type, Map):
                    return f"({operand_str}.Count == 0)"
                # Fallback: wrap in parens and negate
                return f"!({operand_str})"
            case UnaryOp(op=op, operand=operand):
                return f"{op}{self._expr(operand)}"
            case Ternary(cond=cond, then_expr=then_expr, else_expr=else_expr):
                # When else is null but then is a list, use empty List instead
                else_str = self._expr(else_expr)
                if isinstance(else_expr, NilLit) and isinstance(then_expr.typ, Slice):
                    elem = self._type(then_expr.typ.element)
                    else_str = f"new List<{elem}>()"
                return f"({self._expr(cond)} ? {self._expr(then_expr)} : {else_str})"
            case Cast(expr=inner, to_type=to_type):
                return self._cast(inner, to_type)
            case TypeAssert(expr=inner, asserted=asserted):
                type_name = self._type(asserted)
                return f"(({type_name}){self._expr(inner)})"
            case IsType(expr=inner, tested_type=tested_type):
                type_name = self._type_name_for_check(tested_type)
                return f"({self._expr(inner)} is {type_name})"
            case IsNil(expr=inner, negated=negated):
                if negated:
                    return f"{self._expr(inner)} != null"
                return f"{self._expr(inner)} == null"
            case Len(expr=inner):
                inner_str = self._expr(inner)
                if isinstance(inner.typ, Primitive) and inner.typ.kind == "string":
                    return f"{inner_str}.Length"
                if isinstance(inner.typ, Array):
                    return f"{inner_str}.Length"
                return f"{inner_str}.Count"
            case MakeSlice(element_type=element_type, length=length, capacity=capacity):
                elem_type = self._type(element_type)
                if capacity:
                    return f"new List<{elem_type}>({self._expr(capacity)})"
                if length:
                    return f"new List<{elem_type}>({self._expr(length)})"
                return f"new List<{elem_type}>()"
            case MakeMap(key_type=key_type, value_type=value_type):
                kt = self._type(key_type)
                vt = self._type(value_type)
                return f"new Dictionary<{kt}, {vt}>()"
            case SliceLit(elements=elements, element_type=element_type):
                elem_type = self._type(element_type)
                if not elements:
                    return f"new List<{elem_type}>()"
                elems = ", ".join(self._expr(e) for e in elements)
                return f"new List<{elem_type}> {{ {elems} }}"
            case MapLit(entries=entries, key_type=key_type, value_type=value_type):
                kt = self._type(key_type)
                vt = self._type(value_type)
                if not entries:
                    return f"new Dictionary<{kt}, {vt}>()"
                pairs = ", ".join(f"{{ {self._expr(k)}, {self._expr(v)} }}" for k, v in entries)
                return f"new Dictionary<{kt}, {vt}> {{ {pairs} }}"
            case SetLit(elements=elements, element_type=element_type):
                elem_type = self._type(element_type)
                if not elements:
                    return f"new HashSet<{elem_type}>()"
                elems = ", ".join(self._expr(e) for e in elements)
                return f"new HashSet<{elem_type}> {{ {elems} }}"
            case StructLit(struct_name=struct_name, fields=fields, embedded_value=embedded_value):
                return self._struct_lit(struct_name, fields, embedded_value)
            case TupleLit(elements=elements):
                elems = ", ".join(self._expr(e) for e in elements)
                return f"({elems})"
            case StringConcat(parts=parts):
                return " + ".join(self._expr(p) for p in parts)
            case StringFormat(template=template, args=args):
                return self._format_string(template, args)
            case _:
                return "null /* TODO: unknown expression */"

    def _call(self, func: str, args: list[Expr]) -> str:
        args_str = ", ".join(self._expr(a) for a in args)
        if func == "int" and len(args) == 2:
            return f"Convert.ToInt64({args_str})"
        if func == "str":
            return f"({self._expr(args[0])}).ToString()"
        if func == "len":
            arg = self._expr(args[0])
            arg_type = args[0].typ
            if isinstance(arg_type, Primitive) and arg_type.kind == "string":
                return f"{arg}.Length"
            return f"{arg}.Count"
        if func == "range":
            if len(args) == 1:
                return f"Enumerable.Range(0, {self._expr(args[0])}).ToList()"
            elif len(args) == 2:
                start = self._expr(args[0])
                stop = self._expr(args[1])
                return f"Enumerable.Range({start}, {stop} - {start}).ToList()"
            else:
                start = self._expr(args[0])
                stop = self._expr(args[1])
                step = self._expr(args[2])
                step_arg = args[2]
                is_negative = (isinstance(step_arg, IntLit) and step_arg.value < 0) or (
                    isinstance(step_arg, UnaryOp) and step_arg.op == "-"
                )
                if is_negative:
                    return f"Enumerable.Range(0, ({start} - {stop} - 1) / (-({step})) + 1).Select(i => {start} + i * {step}).ToList()"
                return f"Enumerable.Range(0, ({stop} - {start} - 1) / {step} + 1).Select(i => {start} + i * {step}).ToList()"
        if func == "ord":
            return f"(int)({self._expr(args[0])}[0])"
        if func == "chr":
            return f"((char){self._expr(args[0])}).ToString()"
        if func == "abs":
            return f"Math.Abs({args_str})"
        if func == "min":
            return f"Math.Min({args_str})"
        if func == "max":
            return f"Math.Max({args_str})"
        # Pointer boxing not needed in C#
        if func in ("_intPtr", "_int_ptr"):
            return self._expr(args[0])
        # Function-typed parameters are called directly, not via ParableFunctions
        if func in self._func_params:
            return f"{_safe_name(func)}({args_str})"
        func_class = to_pascal(self._module_name) + "Functions"
        return f"{func_class}.{_safe_pascal(func)}({args_str})"

    def _method_call(self, obj: Expr, method: str, args: list[Expr], receiver_type: Type) -> str:
        args_str = ", ".join(self._expr(a) for a in args)
        obj_str = self._expr(obj)
        if isinstance(receiver_type, Slice):
            if method == "append" and args:
                return f"{obj_str}.Add({args_str})"
            if method == "pop":
                # Python pop() returns the removed element; C# RemoveAt is void
                # Use Func delegate with explicit type for the lambda
                elem_type = self._element_type(receiver_type)
                if args:
                    idx = self._expr(args[0])
                else:
                    idx = obj_str + ".Count - 1"
                body = obj_str + ".RemoveAt(" + idx + "); return _tmp;"
                return "((Func<" + elem_type + ", " + elem_type + ">)(_tmp => { " + body + " }))(" + obj_str + "[" + idx + "])"
            if method == "copy":
                return f"new List<{self._element_type(receiver_type)}>({obj_str})"
        if isinstance(receiver_type, Primitive) and receiver_type.kind == "string":
            if method == "startswith":
                if len(args) == 2:
                    prefix = self._expr(args[0])
                    pos = self._expr(args[1])
                    return f"({obj_str}.IndexOf({prefix}, {pos}) == {pos})"
                return f"{obj_str}.StartsWith({args_str})"
            if method == "endswith":
                # Handle tuple argument: str.endswith((" ", "\n")) -> multiple checks
                if args and isinstance(args[0], TupleLit):
                    checks = [f"{obj_str}.EndsWith({self._expr(e)})" for e in args[0].elements]
                    return "(" + " || ".join(checks) + ")"
                return f"{obj_str}.EndsWith({args_str})"
            if method == "find":
                return f"{obj_str}.IndexOf({args_str})"
            if method == "rfind":
                return f"{obj_str}.LastIndexOf({args_str})"
            if method == "replace":
                return f"{obj_str}.Replace({args_str})"
            if method == "split":
                return f"{obj_str}.Split({args_str}).ToList()"
            if method == "join":
                return f"string.Join({obj_str}, {args_str})"
            if method == "lower":
                return f"{obj_str}.ToLower()"
            if method == "upper":
                return f"{obj_str}.ToUpper()"
        if isinstance(receiver_type, Map):
            if method == "get" and len(args) == 2:
                key = self._expr(args[0])
                default = self._expr(args[1])
                return f"({obj_str}.TryGetValue({key}, out var _v) ? _v : {default})"
        if method == "append":
            return f"{obj_str}.Add({args_str})"
        if method == "extend":
            return f"{obj_str}.AddRange({args_str})"
        if method == "remove":
            return f"{obj_str}.Remove({args_str})"
        if method == "clear":
            return f"{obj_str}.Clear()"
        if method == "insert":
            return f"{obj_str}.Insert({args_str})"
        # Handle common methods that fall through when receiver type is unknown
        if method == "endswith":
            # Handle tuple argument: str.endswith((" ", "\n")) -> multiple checks
            if args and isinstance(args[0], TupleLit):
                checks = [f"{obj_str}.EndsWith({self._expr(e)})" for e in args[0].elements]
                return "(" + " || ".join(checks) + ")"
            return f"{obj_str}.EndsWith({args_str})"
        if method == "startswith":
            return f"{obj_str}.StartsWith({args_str})"
        if method == "join":
            # Python: sep.join(list) -> C#: string.Join(sep, list)
            return f"string.Join({obj_str}, {args_str})"
        # ToSexp needs cast when receiver is object (from type switch default)
        if method == "to_sexp":
            return f"((INode){obj_str}).ToSexp()"
        return f"{obj_str}.{_safe_pascal(method)}({args_str})"

    def _slice_expr(self, obj: Expr, low: Expr | None, high: Expr | None) -> str:
        obj_str = self._expr(obj)
        if isinstance(obj.typ, Primitive) and obj.typ.kind == "string":
            if low and high:
                lo = self._expr(low)
                hi = self._expr(high)
                return f"{obj_str}.Substring({lo}, {hi} - {lo})"
            elif low:
                return f"{obj_str}.Substring({self._expr(low)})"
            elif high:
                return f"{obj_str}.Substring(0, {self._expr(high)})"
            return obj_str
        if low and high:
            lo = self._expr(low)
            hi = self._expr(high)
            return f"{obj_str}.GetRange({lo}, {hi} - {lo})"
        elif low:
            lo = self._expr(low)
            return f"{obj_str}.GetRange({lo}, {obj_str}.Count - {lo})"
        elif high:
            return f"{obj_str}.GetRange(0, {self._expr(high)})"
        return f"new List<{self._element_type(obj.typ)}>({obj_str})"

    def _containment_check(self, item: Expr, container: Expr, negated: bool) -> str:
        item_str = self._expr(item)
        container_str = self._expr(container)
        container_type = container.typ
        neg = "!" if negated else ""
        if isinstance(container_type, Set):
            return f"{neg}{container_str}.Contains({item_str})"
        if isinstance(container_type, Map):
            return f"{neg}{container_str}.ContainsKey({item_str})"
        if isinstance(container_type, Primitive) and container_type.kind == "string":
            return f"{neg}{container_str}.Contains({item_str})"
        return f"{neg}{container_str}.Contains({item_str})"

    def _cast(self, inner: Expr, to_type: Type) -> str:
        inner_str = self._expr(inner)
        cs_type = self._type(to_type)
        inner_type = inner.typ
        if isinstance(to_type, Primitive):
            if to_type.kind == "int":
                return f"(int)({inner_str})"
            if to_type.kind == "float":
                return f"(double)({inner_str})"
            if to_type.kind == "byte":
                return f"(byte)({inner_str})"
            if to_type.kind == "string":
                return f"({inner_str}).ToString()"
            if to_type.kind == "rune":
                return f"(char)({inner_str})"
        # String to bytes conversion
        if isinstance(to_type, Slice) and isinstance(to_type.element, Primitive) and to_type.element.kind == "byte":
            if isinstance(inner_type, Primitive) and inner_type.kind == "string":
                return f"System.Text.Encoding.UTF8.GetBytes({inner_str}).ToList()"
        return f"(({cs_type}){inner_str})"

    def _format_string(self, template: str, args: list[Expr]) -> str:
        from re import sub as re_sub
        result = re_sub(r"\{(\d+)\}", r"{\1}", template)
        result = result.replace("%v", "{0}")
        escaped = escape_string(result)
        args_str = ", ".join(self._expr(a) for a in args)
        if args_str:
            return f'string.Format("{escaped}", {args_str})'
        return f'"{escaped}"'

    def _struct_lit(self, struct_name: str, fields: dict[str, Expr], embedded_value: Expr | None) -> str:
        field_info = self.struct_fields.get(struct_name, [])
        if field_info:
            ordered_args = []
            for field_name, field_type in field_info:
                if field_name in fields:
                    field_val = fields[field_name]
                    # Handle null for list fields - use empty List
                    if isinstance(field_val, NilLit) and isinstance(field_type, Slice):
                        elem = self._type(field_type.element)
                        ordered_args.append(f"new List<{elem}>()")
                    else:
                        ordered_args.append(self._expr(field_val))
                else:
                    ordered_args.append(self._default_value(field_type))
            return f"new {struct_name}({', '.join(ordered_args)})"
        elif embedded_value is not None:
            # Child exception class with no additional fields - forward parent args
            if isinstance(embedded_value, StructLit):
                parent_args = ", ".join(self._expr(v) for v in embedded_value.fields.values())
                return f"new {struct_name}({parent_args})"
            return f"new {struct_name}({self._expr(embedded_value)})"
        elif not fields:
            return f"new {struct_name}()"
        else:
            args = ", ".join(self._expr(v) for v in fields.values())
            return f"new {struct_name}({args})"

    def _lvalue(self, lv: LValue) -> str:
        match lv:
            case VarLV(name=name):
                if name == self.receiver_name:
                    return "this"
                return _safe_name(name)
            case FieldLV(obj=obj, field=field):
                return f"{self._expr(obj)}.{_safe_pascal(field)}"
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
                return f"{self._type(element)}[]"
            case Map(key=key, value=value):
                kt = self._type(key)
                vt = self._type(value)
                return f"Dictionary<{kt}, {vt}>"
            case Set(element=element):
                et = self._type(element)
                return f"HashSet<{et}>"
            case Tuple(elements=elements):
                types = ", ".join(self._type(t) for t in elements)
                return f"({types})"
            case Pointer(target=target):
                return self._type(target)
            case Optional(inner=inner):
                inner_type = self._type(inner)
                if isinstance(inner, Primitive) and inner.kind in ("int", "float", "bool", "byte", "rune"):
                    return f"{inner_type}?"
                return inner_type
            case StructRef(name=name):
                if name in self._interface_names:
                    return f"I{name}"
                return name
            case InterfaceRef(name=name):
                if name == "any":
                    return "object"
                return f"I{name}"
            case Union(name=name):
                if name:
                    return name
                return "object"
            case FuncType(params=params, ret=ret):
                if ret == Primitive("void"):
                    if not params:
                        return "Action"
                    param_types = ", ".join(self._type(p) for p in params)
                    return f"Action<{param_types}>"
                if not params:
                    return f"Func<{self._type(ret)}>"
                param_types = ", ".join(self._type(p) for p in params)
                return f"Func<{param_types}, {self._type(ret)}>"
            case _:
                return "object"

    def _type_name_for_check(self, typ: Type) -> str:
        match typ:
            case StructRef(name=name):
                if name in self._interface_names:
                    return f"I{name}"
                return name
            case InterfaceRef(name=name):
                return f"I{name}"
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
                return "object"

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
                return "'\\0'"
            case Slice():
                elem = self._type(typ.element)
                return f"new List<{elem}>()"
            case Tuple(elements=elements):
                defaults = ", ".join(self._default_value(t) for t in elements)
                return f"({defaults})"
            case Optional():
                return "null"
            case _:
                return "null"


def _primitive_type(kind: str) -> str:
    match kind:
        case "string":
            return "string"
        case "int":
            return "int"
        case "float":
            return "double"
        case "bool":
            return "bool"
        case "byte":
            return "byte"
        case "rune":
            return "char"
        case "void":
            return "void"
        case _:
            return "object"


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
