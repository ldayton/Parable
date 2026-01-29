"""Lowering utilities extracted from frontend.py."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from ..ir import BOOL, FLOAT, INT, STRING, VOID, Interface, Loc, Map, Optional, Pointer, Set, Slice, StringFormat, StructRef, Tuple

if TYPE_CHECKING:
    from .. import ir
    from ..ir import FuncInfo, SymbolTable, Type
    from .context import TypeContext


@dataclass
class LoweringDispatch:
    """Callbacks for mutual recursion during lowering."""
    lower_expr: Callable[[ast.expr], "ir.Expr"]
    lower_stmt: Callable[[ast.stmt], "ir.Stmt"]
    lower_stmts: Callable[[list[ast.stmt]], list["ir.Stmt"]]
    lower_lvalue: Callable[[ast.expr], "ir.LValue"]
    lower_expr_as_bool: Callable[[ast.expr], "ir.Expr"]


def loc_from_node(node: ast.AST) -> Loc:
    """Create Loc from AST node."""
    if hasattr(node, "lineno"):
        return Loc(
            line=node.lineno,
            col=node.col_offset,
            end_line=getattr(node, "end_lineno", node.lineno) or node.lineno,
            end_col=getattr(node, "end_col_offset", node.col_offset) or node.col_offset,
        )
    return Loc.unknown()


def binop_to_str(op: ast.operator) -> str:
    """Convert AST binary operator to string."""
    return {
        ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
        ast.FloorDiv: "/", ast.Mod: "%", ast.Pow: "**",
        ast.LShift: "<<", ast.RShift: ">>",
        ast.BitOr: "|", ast.BitXor: "^", ast.BitAnd: "&",
    }.get(type(op), "+")


def cmpop_to_str(op: ast.cmpop) -> str:
    """Convert AST comparison operator to string."""
    return {
        ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=",
        ast.Gt: ">", ast.GtE: ">=", ast.Is: "==", ast.IsNot: "!=",
        ast.In: "in", ast.NotIn: "not in",
    }.get(type(op), "==")


def unaryop_to_str(op: ast.unaryop) -> str:
    """Convert AST unary operator to string."""
    return {ast.Not: "!", ast.USub: "-", ast.UAdd: "+", ast.Invert: "~"}.get(type(op), "-")


# ============================================================
# TYPE NARROWING HELPERS
# ============================================================


def is_isinstance_call(node: ast.expr) -> tuple[str, str] | None:
    """Check if node is isinstance(var, Type). Returns (var_name, type_name) or None."""
    if not isinstance(node, ast.Call):
        return None
    if not isinstance(node.func, ast.Name) or node.func.id != "isinstance":
        return None
    if len(node.args) != 2:
        return None
    if not isinstance(node.args[0], ast.Name):
        return None
    if not isinstance(node.args[1], ast.Name):
        return None
    return (node.args[0].id, node.args[1].id)


def is_kind_check(node: ast.expr, kind_to_class: dict[str, str]) -> tuple[str, str] | None:
    """Check if node is x.kind == "typename". Returns (var_name, class_name) or None."""
    if not isinstance(node, ast.Compare):
        return None
    if len(node.ops) != 1 or not isinstance(node.ops[0], ast.Eq):
        return None
    if len(node.comparators) != 1:
        return None
    # Check for x.kind on left side
    if not isinstance(node.left, ast.Attribute) or node.left.attr != "kind":
        return None
    if not isinstance(node.left.value, ast.Name):
        return None
    var_name = node.left.value.id
    # Check for string constant on right side
    comparator = node.comparators[0]
    if not isinstance(comparator, ast.Constant) or not isinstance(comparator.value, str):
        return None
    kind_value = comparator.value
    # Map kind string to class name
    if kind_value not in kind_to_class:
        return None
    return (var_name, kind_to_class[kind_value])


def extract_isinstance_or_chain(
    node: ast.expr, kind_to_class: dict[str, str]
) -> tuple[str, list[str]] | None:
    """Extract isinstance/kind checks from expression. Returns (var_name, [type_names]) or None."""
    # Handle simple isinstance call
    simple = is_isinstance_call(node)
    if simple:
        return (simple[0], [simple[1]])
    # Handle x.kind == "typename" pattern
    kind_check = is_kind_check(node, kind_to_class)
    if kind_check:
        return (kind_check[0], [kind_check[1]])
    # Handle isinstance(x, A) or isinstance(x, B) or ...
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
        var_name: str | None = None
        type_names: list[str] = []
        for value in node.values:
            check = is_isinstance_call(value) or is_kind_check(value, kind_to_class)
            if not check:
                return None  # Not all are isinstance/kind calls
            if var_name is None:
                var_name = check[0]
            elif var_name != check[0]:
                return None  # Different variables
            type_names.append(check[1])
        if var_name and type_names:
            return (var_name, type_names)
    return None


def extract_isinstance_from_and(node: ast.expr) -> tuple[str, str] | None:
    """Extract isinstance(var, Type) from compound AND expression.
    Returns (var_name, type_name) or None if no isinstance found."""
    if not isinstance(node, ast.BoolOp) or not isinstance(node.op, ast.And):
        return None
    # Check each value in the AND chain for isinstance
    for value in node.values:
        result = is_isinstance_call(value)
        if result:
            return result
    return None


def extract_kind_check(
    node: ast.expr, kind_to_struct: dict[str, str], kind_source_vars: dict[str, str]
) -> tuple[str, str] | None:
    """Extract kind-based type narrowing from `kind == "value"` or `node.kind == "value"`.
    Returns (node_var_name, struct_name) or None if not a kind check."""
    # Match: kind == "value" where kind was previously assigned from node.kind
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq):
        left = node.left
        right = node.comparators[0]
        # Check for var == "kind_value" pattern
        if isinstance(left, ast.Name) and isinstance(right, ast.Constant) and isinstance(right.value, str):
            kind_var = left.id
            kind_value = right.value
            if kind_value in kind_to_struct:
                # Look up which Node-typed variable this kind var came from
                if kind_var in kind_source_vars:
                    node_var = kind_source_vars[kind_var]
                    return (node_var, kind_to_struct[kind_value])
        # Check for node.kind == "value" pattern
        if isinstance(left, ast.Attribute) and left.attr == "kind" and isinstance(left.value, ast.Name):
            node_var = left.value.id
            if isinstance(right, ast.Constant) and isinstance(right.value, str):
                kind_value = right.value
                if kind_value in kind_to_struct:
                    return (node_var, kind_to_struct[kind_value])
    return None


def extract_attr_kind_check(
    node: ast.expr, kind_to_struct: dict[str, str]
) -> tuple[tuple[str, ...], str] | None:
    """Extract kind check for attribute paths like `node.body.kind == "value"`.
    Returns (attr_path_tuple, struct_name) or None."""
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq):
        left = node.left
        right = node.comparators[0]
        # Check for expr.kind == "value" pattern where expr is an attribute chain
        if (isinstance(left, ast.Attribute) and left.attr == "kind"
            and isinstance(right, ast.Constant) and isinstance(right.value, str)):
            kind_value = right.value
            if kind_value in kind_to_struct:
                # Extract the attribute path (e.g., node.body -> ("node", "body"))
                attr_path = get_attr_path(left.value)
                if attr_path and len(attr_path) > 1:  # Only for chains, not simple vars
                    return (attr_path, kind_to_struct[kind_value])
    return None


def get_attr_path(node: ast.expr) -> tuple[str, ...] | None:
    """Extract attribute path as tuple (e.g., node.body -> ("node", "body"))."""
    if isinstance(node, ast.Name):
        return (node.id,)
    elif isinstance(node, ast.Attribute) and isinstance(node.value, (ast.Name, ast.Attribute)):
        base = get_attr_path(node.value)
        if base:
            return base + (node.attr,)
    return None


def resolve_type_name(
    name: str, type_map: dict[str, "ir.Type"], symbols: "ir.SymbolTable"
) -> "ir.Type":
    """Resolve a class name to an IR type (for isinstance checks)."""
    from ..ir import Interface, Pointer, StructRef
    # Handle primitive types
    if name in type_map:
        return type_map[name]
    if name in symbols.structs:
        return Pointer(StructRef(name))
    return Interface(name)


# ============================================================
# ARGUMENT HELPERS
# ============================================================


def convert_negative_index(
    idx_node: ast.expr,
    obj: "ir.Expr",
    parent: ast.AST,
    lower_expr: Callable[[ast.expr], "ir.Expr"],
) -> "ir.Expr":
    """Convert negative index -N to len(obj) - N."""
    from .. import ir
    # Check for -N pattern (UnaryOp with USub on positive int constant)
    if isinstance(idx_node, ast.UnaryOp) and isinstance(idx_node.op, ast.USub):
        if isinstance(idx_node.operand, ast.Constant) and isinstance(idx_node.operand.value, int):
            n = idx_node.operand.value
            if n > 0:
                # len(obj) - N
                return ir.BinaryOp(
                    op="-",
                    left=ir.Len(expr=obj, typ=INT, loc=loc_from_node(parent)),
                    right=ir.IntLit(value=n, typ=INT, loc=loc_from_node(idx_node)),
                    typ=INT,
                    loc=loc_from_node(idx_node)
                )
    # Not a negative constant, lower normally
    return lower_expr(idx_node)


def merge_keyword_args(
    obj_type: "Type",
    method: str,
    args: list,
    node: ast.Call,
    symbols: "SymbolTable",
    lower_expr: Callable[[ast.expr], "ir.Expr"],
    extract_struct_name: Callable[["Type"], str | None],
) -> list:
    """Merge keyword arguments into positional args at their proper positions."""
    if not node.keywords:
        return args
    struct_name = extract_struct_name(obj_type)
    if not struct_name or struct_name not in symbols.structs:
        return args
    method_info = symbols.structs[struct_name].methods.get(method)
    if not method_info:
        return args
    # Build param name -> index map
    param_indices: dict[str, int] = {}
    for i, param in enumerate(method_info.params):
        param_indices[param.name] = i
    # Extend args list if needed
    result = list(args)
    for kw in node.keywords:
        if kw.arg and kw.arg in param_indices:
            idx = param_indices[kw.arg]
            # Extend list if necessary
            while len(result) <= idx:
                result.append(None)
            result[idx] = lower_expr(kw.value)
    return result


def fill_default_args(
    obj_type: "Type",
    method: str,
    args: list,
    symbols: "SymbolTable",
    extract_struct_name: Callable[["Type"], str | None],
) -> list:
    """Fill in missing arguments with default values for methods with optional params."""
    struct_name = extract_struct_name(obj_type)
    method_info = None
    if struct_name and struct_name in symbols.structs:
        method_info = symbols.structs[struct_name].methods.get(method)
    # If struct lookup failed, search all structs for this method (for union-typed receivers)
    if not method_info:
        for s_name, s_info in symbols.structs.items():
            if method in s_info.methods:
                method_info = s_info.methods[method]
                break
    if not method_info:
        return args
    n_expected = len(method_info.params)
    # Extend to full length if needed
    result = list(args)
    while len(result) < n_expected:
        result.append(None)
    # Fill in None slots with defaults
    for i, arg in enumerate(result):
        if arg is None and i < n_expected:
            param = method_info.params[i]
            if param.has_default and param.default_value is not None:
                result[i] = param.default_value
    return result


def merge_keyword_args_for_func(
    func_info: "FuncInfo",
    args: list,
    node: ast.Call,
    lower_expr: Callable[[ast.expr], "ir.Expr"],
) -> list:
    """Merge keyword arguments into positional args at their proper positions for free functions."""
    if not node.keywords:
        return args
    # Build param name -> index map
    param_indices: dict[str, int] = {}
    for i, param in enumerate(func_info.params):
        param_indices[param.name] = i
    # Extend args list if needed and place keyword args
    result = list(args)
    for kw in node.keywords:
        if kw.arg and kw.arg in param_indices:
            idx = param_indices[kw.arg]
            # Extend list if necessary
            while len(result) <= idx:
                result.append(None)
            result[idx] = lower_expr(kw.value)
    return result


def fill_default_args_for_func(func_info: "FuncInfo", args: list) -> list:
    """Fill in missing arguments with default values for free functions with optional params."""
    n_expected = len(func_info.params)
    if len(args) >= n_expected:
        return args
    # Extend to full length if needed
    result = list(args)
    while len(result) < n_expected:
        result.append(None)
    # Fill in None slots with defaults
    for i, arg in enumerate(result):
        if arg is None and i < n_expected:
            param = func_info.params[i]
            if param.has_default and param.default_value is not None:
                result[i] = param.default_value
    return result


def add_address_of_for_ptr_params(
    obj_type: "Type",
    method: str,
    args: list,
    orig_args: list[ast.expr],
    symbols: "SymbolTable",
    extract_struct_name: Callable[["Type"], str | None],
    infer_expr_type_from_ast: Callable[[ast.expr], "Type"],
) -> list:
    """Add & when passing slice to pointer-to-slice parameter."""
    from .. import ir
    struct_name = extract_struct_name(obj_type)
    if not struct_name or struct_name not in symbols.structs:
        return args
    method_info = symbols.structs[struct_name].methods.get(method)
    if not method_info:
        return args
    result = list(args)
    for i, arg in enumerate(result):
        if i >= len(method_info.params) or i >= len(orig_args):
            break
        param = method_info.params[i]
        param_type = param.typ
        # Check if param expects pointer to slice but arg is slice
        if isinstance(param_type, Pointer) and isinstance(param_type.target, Slice):
            # Infer arg type from AST
            arg_type = infer_expr_type_from_ast(orig_args[i])
            if isinstance(arg_type, Slice) and not isinstance(arg_type, Pointer):
                # Wrap with address-of
                result[i] = ir.UnaryOp(op="&", operand=arg, typ=param_type, loc=arg.loc if hasattr(arg, 'loc') else Loc.unknown())
    return result


def deref_for_slice_params(
    obj_type: "Type",
    method: str,
    args: list,
    orig_args: list[ast.expr],
    symbols: "SymbolTable",
    extract_struct_name: Callable[["Type"], str | None],
    infer_expr_type_from_ast: Callable[[ast.expr], "Type"],
) -> list:
    """Dereference * when passing pointer-to-slice to slice parameter."""
    from .. import ir
    struct_name = extract_struct_name(obj_type)
    if not struct_name or struct_name not in symbols.structs:
        return args
    method_info = symbols.structs[struct_name].methods.get(method)
    if not method_info:
        return args
    result = list(args)
    for i, arg in enumerate(result):
        if i >= len(method_info.params) or i >= len(orig_args):
            break
        param = method_info.params[i]
        param_type = param.typ
        # Check if param expects slice but arg is pointer/optional to slice
        if isinstance(param_type, Slice) and not isinstance(param_type, Pointer):
            arg_type = infer_expr_type_from_ast(orig_args[i])
            inner_slice = get_inner_slice(arg_type)
            if inner_slice is not None:
                result[i] = ir.UnaryOp(op="*", operand=arg, typ=inner_slice, loc=arg.loc if hasattr(arg, 'loc') else Loc.unknown())
    return result


def deref_for_func_slice_params(
    func_name: str,
    args: list,
    orig_args: list[ast.expr],
    symbols: "SymbolTable",
    infer_expr_type_from_ast: Callable[[ast.expr], "Type"],
) -> list:
    """Dereference * when passing pointer-to-slice to slice parameter for free functions."""
    from .. import ir
    if func_name not in symbols.functions:
        return args
    func_info = symbols.functions[func_name]
    result = list(args)
    for i, arg in enumerate(result):
        if i >= len(func_info.params) or i >= len(orig_args):
            break
        param = func_info.params[i]
        param_type = param.typ
        # Check if param expects slice but arg is pointer/optional to slice
        if isinstance(param_type, Slice) and not isinstance(param_type, Pointer):
            arg_type = infer_expr_type_from_ast(orig_args[i])
            inner_slice = get_inner_slice(arg_type)
            if inner_slice is not None:
                result[i] = ir.UnaryOp(op="*", operand=arg, typ=inner_slice, loc=arg.loc if hasattr(arg, 'loc') else Loc.unknown())
    return result


def coerce_args_to_node(func_info: "FuncInfo", args: list) -> list:
    """Add type assertions when passing interface{} to Node parameter."""
    from .. import ir
    from ..ir import Interface
    result = list(args)
    for i, arg in enumerate(result):
        if i >= len(func_info.params):
            break
        param = func_info.params[i]
        param_type = param.typ
        # Check if param expects Node but arg is interface{}
        if isinstance(param_type, Interface) and param_type.name == "Node":
            arg_type = getattr(arg, 'typ', None)
            # interface{} is represented as Interface("any")
            if arg_type == Interface("any"):
                result[i] = ir.TypeAssert(
                    expr=arg, asserted=Interface("Node"), safe=True,
                    typ=Interface("Node"), loc=arg.loc if hasattr(arg, 'loc') else Loc.unknown()
                )
    return result


def is_pointer_to_slice(typ: "Type") -> bool:
    """Check if type is pointer-to-slice (Pointer(Slice) only, NOT Optional(Slice))."""
    if isinstance(typ, Pointer) and isinstance(typ.target, Slice):
        return True
    return False


def is_len_call(node: ast.expr) -> bool:
    """Check if node is a len() call."""
    return (isinstance(node, ast.Call) and
            isinstance(node.func, ast.Name) and
            node.func.id == "len")


def get_inner_slice(typ: "Type") -> Slice | None:
    """Get the inner Slice from Pointer(Slice) only, NOT Optional(Slice)."""
    if isinstance(typ, Pointer) and isinstance(typ.target, Slice):
        return typ.target
    return None


def coerce_sentinel_to_ptr(
    obj_type: "Type",
    method: str,
    args: list,
    orig_args: list,
    symbols: "SymbolTable",
    sentinel_ints: set[str],
    extract_struct_name: Callable[["Type"], str | None],
) -> list:
    """Wrap sentinel ints with _intPtr() when passing to Optional(int) params."""
    from .. import ir
    struct_name = extract_struct_name(obj_type)
    if not struct_name or struct_name not in symbols.structs:
        return args
    method_info = symbols.structs[struct_name].methods.get(method)
    if not method_info:
        return args
    result = list(args)
    for i, (arg, param) in enumerate(zip(result, method_info.params)):
        if arg is None:
            continue
        # Check if parameter expects *int and argument is a sentinel int variable
        if isinstance(param.typ, Optional) and param.typ.inner == INT:
            if i < len(orig_args) and isinstance(orig_args[i], ast.Name):
                var_name = orig_args[i].id
                if var_name in sentinel_ints:
                    # Wrap in _intPtr() call
                    result[i] = ir.Call(func="_intPtr", args=[arg], typ=param.typ, loc=arg.loc)
    return result


# ============================================================
# SIMPLE EXPRESSION LOWERING
# ============================================================


def lower_expr_Constant(node: ast.Constant) -> "ir.Expr":
    """Lower Python constant to IR literal."""
    from .. import ir
    if isinstance(node.value, bool):
        return ir.BoolLit(value=node.value, typ=BOOL, loc=loc_from_node(node))
    if isinstance(node.value, int):
        return ir.IntLit(value=node.value, typ=INT, loc=loc_from_node(node))
    if isinstance(node.value, float):
        return ir.FloatLit(value=node.value, typ=FLOAT, loc=loc_from_node(node))
    if isinstance(node.value, str):
        return ir.StringLit(value=node.value, typ=STRING, loc=loc_from_node(node))
    if node.value is None:
        return ir.NilLit(typ=Interface("any"), loc=loc_from_node(node))
    return ir.Var(name=f"TODO_Constant_{type(node.value)}", typ=Interface("any"))


def lower_expr_Name(
    node: ast.Name,
    type_ctx: "TypeContext",
    symbols: "SymbolTable",
) -> "ir.Expr":
    """Lower Python name to IR variable."""
    from .. import ir
    if node.id == "True":
        return ir.BoolLit(value=True, typ=BOOL, loc=loc_from_node(node))
    if node.id == "False":
        return ir.BoolLit(value=False, typ=BOOL, loc=loc_from_node(node))
    if node.id == "None":
        return ir.NilLit(typ=Interface("any"), loc=loc_from_node(node))
    # Handle expanded tuple variables: result -> TupleLit(result0, result1)
    if node.id in type_ctx.tuple_vars:
        synthetic_names = type_ctx.tuple_vars[node.id]
        elements = []
        elem_types = []
        for syn_name in synthetic_names:
            typ = type_ctx.var_types.get(syn_name, Interface("any"))
            elements.append(ir.Var(name=syn_name, typ=typ, loc=loc_from_node(node)))
            elem_types.append(typ)
        return ir.TupleLit(
            elements=elements,
            typ=Tuple(tuple(elem_types)),
            loc=loc_from_node(node)
        )
    # Look up variable type from context, or constants for module-level constants
    var_type = type_ctx.var_types.get(node.id)
    if var_type is None:
        var_type = symbols.constants.get(node.id, Interface("any"))
    return ir.Var(name=node.id, typ=var_type, loc=loc_from_node(node))


def lower_expr_Attribute(
    node: ast.Attribute,
    symbols: "SymbolTable",
    type_ctx: "TypeContext",
    current_class_name: str,
    node_field_types: dict[str, list[str]],
    lower_expr: Callable[[ast.expr], "ir.Expr"],
    is_node_interface_type: Callable[["Type | None"], bool],
) -> "ir.Expr":
    """Lower Python attribute access to IR field access."""
    from .. import ir
    # Check for class constant access (e.g., TokenType.EOF -> TokenType_EOF)
    if isinstance(node.value, ast.Name):
        class_name = node.value.id
        const_name = f"{class_name}_{node.attr}"
        if const_name in symbols.constants:
            return ir.Var(name=const_name, typ=INT, loc=loc_from_node(node))
    obj = lower_expr(node.value)
    # If accessing field on a narrowed variable, wrap in TypeAssert
    if isinstance(node.value, ast.Name) and node.value.id in type_ctx.narrowed_vars:
        var_type = type_ctx.var_types.get(node.value.id)
        if var_type and isinstance(var_type, Pointer) and isinstance(var_type.target, StructRef):
            obj = ir.TypeAssert(
                expr=obj, asserted=var_type, safe=True,
                typ=var_type, loc=loc_from_node(node.value)
            )
    # Check if accessing a field on a Node-typed expression that isn't in the interface
    # Node interface only has Kind() method, so any other field needs a type assertion
    obj_type = getattr(obj, 'typ', None)
    if is_node_interface_type(obj_type) and node.attr != "kind":
        # Look up which struct types have this field
        if node.attr in node_field_types:
            struct_names = node_field_types[node.attr]
            # If the variable is from a union type, prefer a struct from the union
            chosen_struct = struct_names[0]  # Default: first in NODE_FIELD_TYPES
            # Check if the object expression has a narrowed type from a kind check
            obj_attr_path = get_attr_path(node.value)
            if obj_attr_path and obj_attr_path in type_ctx.narrowed_attr_paths:
                narrowed_struct = type_ctx.narrowed_attr_paths[obj_attr_path]
                if narrowed_struct in struct_names:
                    chosen_struct = narrowed_struct
            elif isinstance(node.value, ast.Name):
                var_name = node.value.id
                if var_name in type_ctx.union_types:
                    union_structs = type_ctx.union_types[var_name]
                    # Find intersection of union structs and field structs
                    for s in union_structs:
                        if s in struct_names:
                            chosen_struct = s
                            break
            asserted_type = Pointer(StructRef(chosen_struct))
            obj = ir.TypeAssert(
                expr=obj, asserted=asserted_type, safe=True,
                typ=asserted_type, loc=loc_from_node(node.value)
            )
    # Infer field type for self.field accesses
    field_type: "Type" = Interface("any")
    if isinstance(node.value, ast.Name) and node.value.id == "self":
        if current_class_name in symbols.structs:
            struct_info = symbols.structs[current_class_name]
            field_info = struct_info.fields.get(node.attr)
            if field_info:
                field_type = field_info.typ
    # Also look up field type from the asserted struct type
    if isinstance(obj, ir.TypeAssert):
        asserted = obj.asserted
        if isinstance(asserted, Pointer) and isinstance(asserted.target, StructRef):
            struct_name = asserted.target.name
            if struct_name in symbols.structs:
                field_info = symbols.structs[struct_name].fields.get(node.attr)
                if field_info:
                    field_type = field_info.typ
    # Look up field type from object's type (for variables with known struct types)
    if field_type == Interface("any") and obj_type is not None:
        struct_name = None
        if isinstance(obj_type, Pointer) and isinstance(obj_type.target, StructRef):
            struct_name = obj_type.target.name
        elif isinstance(obj_type, StructRef):
            struct_name = obj_type.name
        if struct_name and struct_name in symbols.structs:
            field_info = symbols.structs[struct_name].fields.get(node.attr)
            if field_info:
                field_type = field_info.typ
    return ir.FieldAccess(
        obj=obj, field=node.attr, typ=field_type, loc=loc_from_node(node)
    )


def lower_expr_Subscript(
    node: ast.Subscript,
    type_ctx: "TypeContext",
    lower_expr: Callable[[ast.expr], "ir.Expr"],
    convert_negative_index: Callable[[ast.expr, "ir.Expr", ast.AST], "ir.Expr"],
    infer_expr_type_from_ast: Callable[[ast.expr], "Type"],
) -> "ir.Expr":
    """Lower Python subscript access to IR index or slice expression."""
    from .. import ir
    # Check for tuple var indexing: cmdsub_result[0] -> cmdsub_result0
    if isinstance(node.value, ast.Name) and isinstance(node.slice, ast.Constant):
        var_name = node.value.id
        if var_name in type_ctx.tuple_vars and isinstance(node.slice.value, int):
            idx = node.slice.value
            synthetic_names = type_ctx.tuple_vars[var_name]
            if 0 <= idx < len(synthetic_names):
                syn_name = synthetic_names[idx]
                typ = type_ctx.var_types.get(syn_name, Interface("any"))
                return ir.Var(name=syn_name, typ=typ, loc=loc_from_node(node))
    obj = lower_expr(node.value)
    if isinstance(node.slice, ast.Slice):
        low = convert_negative_index(node.slice.lower, obj, node) if node.slice.lower else None
        high = convert_negative_index(node.slice.upper, obj, node) if node.slice.upper else None
        # Slicing preserves type - string slice is still string, slice of slice is still slice
        slice_type: "Type" = infer_expr_type_from_ast(node.value)
        if slice_type == Interface("any"):
            slice_type = obj.typ if hasattr(obj, 'typ') else Interface("any")
        return ir.SliceExpr(
            obj=obj, low=low, high=high, typ=slice_type, loc=loc_from_node(node)
        )
    idx = convert_negative_index(node.slice, obj, node)
    # Infer element type from slice type
    elem_type: "Type" = Interface("any")
    obj_type = getattr(obj, 'typ', None)
    if isinstance(obj_type, Slice):
        elem_type = obj_type.element
    # Handle tuple indexing: tuple[0] -> tuple.F0 (as FieldAccess)
    if isinstance(obj_type, Tuple) and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int):
        field_idx = node.slice.value
        if 0 <= field_idx < len(obj_type.elements):
            elem_type = obj_type.elements[field_idx]
            return ir.FieldAccess(obj=obj, field=f"F{field_idx}", typ=elem_type, loc=loc_from_node(node))
    index_expr = ir.Index(obj=obj, index=idx, typ=elem_type, loc=loc_from_node(node))
    # Check if indexing a string - if so, wrap with Cast to string
    # In Go, string[i] returns byte, but Python returns str
    # Check both AST inference and lowered expression type
    is_string = infer_expr_type_from_ast(node.value) == STRING
    if not is_string and hasattr(obj, 'typ') and obj.typ == STRING:
        is_string = True
    if is_string:
        return ir.Cast(expr=index_expr, to_type=STRING, typ=STRING, loc=loc_from_node(node))
    return index_expr


# ============================================================
# OPERATOR EXPRESSION LOWERING
# ============================================================


def lower_expr_BinOp(
    node: ast.BinOp,
    lower_expr: Callable[[ast.expr], "ir.Expr"],
    infer_expr_type_from_ast: Callable[[ast.expr], "Type"],
) -> "ir.Expr":
    """Lower Python binary operation to IR."""
    from .. import ir
    left = lower_expr(node.left)
    right = lower_expr(node.right)
    op = binop_to_str(node.op)
    # Infer result type based on operator
    result_type: "Type" = Interface("any")
    if isinstance(node.op, (ast.BitAnd, ast.BitOr, ast.BitXor, ast.LShift, ast.RShift)):
        result_type = INT
    elif isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.FloorDiv, ast.Mod)):
        left_type = infer_expr_type_from_ast(node.left)
        right_type = infer_expr_type_from_ast(node.right)
        # String concatenation
        if left_type == STRING or right_type == STRING:
            result_type = STRING
        elif left_type == INT or right_type == INT:
            result_type = INT
    return ir.BinaryOp(op=op, left=left, right=right, typ=result_type, loc=loc_from_node(node))


def get_sentinel_value(
    node: ast.expr,
    type_ctx: "TypeContext",
    current_class_name: str,
    sentinel_int_fields: dict[tuple[str, str], int],
) -> int | None:
    """Get the sentinel value for a sentinel int expression, or None if not a sentinel int."""
    # Local variable sentinel ints (always use -1)
    if isinstance(node, ast.Name) and node.id in type_ctx.sentinel_ints:
        return -1
    # Field sentinel ints: self.field
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
        class_name = current_class_name
        field_name = node.attr
        if (class_name, field_name) in sentinel_int_fields:
            return sentinel_int_fields[(class_name, field_name)]
    return None


def is_sentinel_int(
    node: ast.expr,
    type_ctx: "TypeContext",
    current_class_name: str,
    sentinel_int_fields: dict[tuple[str, str], int],
) -> bool:
    """Check if an expression is a sentinel int (uses a sentinel value for None)."""
    return get_sentinel_value(node, type_ctx, current_class_name, sentinel_int_fields) is not None


def lower_expr_Compare(
    node: ast.Compare,
    lower_expr: Callable[[ast.expr], "ir.Expr"],
    infer_expr_type_from_ast: Callable[[ast.expr], "Type"],
    type_ctx: "TypeContext",
    current_class_name: str,
    sentinel_int_fields: dict[tuple[str, str], int],
) -> "ir.Expr":
    """Lower Python comparison to IR."""
    from .. import ir
    # Handle simple comparisons
    if len(node.ops) == 1 and len(node.comparators) == 1:
        left = lower_expr(node.left)
        right = lower_expr(node.comparators[0])
        op = cmpop_to_str(node.ops[0])
        # Special case for "is None" / "is not None"
        if isinstance(node.ops[0], ast.Is) and isinstance(node.comparators[0], ast.Constant) and node.comparators[0].value is None:
            # For strings, compare to empty string; for bools, compare to false
            left_type = infer_expr_type_from_ast(node.left)
            if left_type == STRING:
                cmp_op = "=="
                return ir.BinaryOp(op=cmp_op, left=left, right=ir.StringLit(value="", typ=STRING), typ=BOOL, loc=loc_from_node(node))
            if left_type == BOOL:
                return ir.UnaryOp(op="!", operand=left, typ=BOOL, loc=loc_from_node(node))
            # For sentinel ints, compare to the sentinel value
            sentinel = get_sentinel_value(node.left, type_ctx, current_class_name, sentinel_int_fields)
            if sentinel is not None:
                return ir.BinaryOp(op="==", left=left, right=ir.IntLit(value=sentinel, typ=INT), typ=BOOL, loc=loc_from_node(node))
            return ir.IsNil(expr=left, negated=False, typ=BOOL, loc=loc_from_node(node))
        if isinstance(node.ops[0], ast.IsNot) and isinstance(node.comparators[0], ast.Constant) and node.comparators[0].value is None:
            # For strings, compare to non-empty string; for bools, just use the bool itself
            left_type = infer_expr_type_from_ast(node.left)
            if left_type == STRING:
                cmp_op = "!="
                return ir.BinaryOp(op=cmp_op, left=left, right=ir.StringLit(value="", typ=STRING), typ=BOOL, loc=loc_from_node(node))
            if left_type == BOOL:
                return left  # bool is its own truthy value
            # For sentinel ints, compare to the sentinel value
            sentinel = get_sentinel_value(node.left, type_ctx, current_class_name, sentinel_int_fields)
            if sentinel is not None:
                return ir.BinaryOp(op="!=", left=left, right=ir.IntLit(value=sentinel, typ=INT), typ=BOOL, loc=loc_from_node(node))
            return ir.IsNil(expr=left, negated=True, typ=BOOL, loc=loc_from_node(node))
        # Handle "x in (a, b, c)" -> "x == a || x == b || x == c"
        if isinstance(node.ops[0], (ast.In, ast.NotIn)) and isinstance(node.comparators[0], ast.Tuple):
            negated = isinstance(node.ops[0], ast.NotIn)
            cmp_op = "!=" if negated else "=="
            join_op = "&&" if negated else "||"
            elts = node.comparators[0].elts
            if elts:
                result = ir.BinaryOp(op=cmp_op, left=left, right=lower_expr(elts[0]), typ=BOOL, loc=loc_from_node(node))
                for elt in elts[1:]:
                    cmp = ir.BinaryOp(op=cmp_op, left=left, right=lower_expr(elt), typ=BOOL, loc=loc_from_node(node))
                    result = ir.BinaryOp(op=join_op, left=result, right=cmp, typ=BOOL, loc=loc_from_node(node))
                return result
            return ir.BoolLit(value=not negated, typ=BOOL, loc=loc_from_node(node))
        # Handle string vs pointer/optional string comparison: dereference the pointer side
        left_type = infer_expr_type_from_ast(node.left)
        right_type = infer_expr_type_from_ast(node.comparators[0])
        if left_type == STRING and isinstance(right_type, (Optional, Pointer)):
            inner = right_type.inner if isinstance(right_type, Optional) else right_type.target
            if inner == STRING:
                right = ir.UnaryOp(op="*", operand=right, typ=STRING, loc=loc_from_node(node))
        elif right_type == STRING and isinstance(left_type, (Optional, Pointer)):
            inner = left_type.inner if isinstance(left_type, Optional) else left_type.target
            if inner == STRING:
                left = ir.UnaryOp(op="*", operand=left, typ=STRING, loc=loc_from_node(node))
        # Handle int vs pointer/optional int comparison: dereference the pointer side
        elif left_type == INT and isinstance(right_type, (Optional, Pointer)):
            inner = right_type.inner if isinstance(right_type, Optional) else right_type.target
            if inner == INT:
                right = ir.UnaryOp(op="*", operand=right, typ=INT, loc=loc_from_node(node))
        elif right_type == INT and isinstance(left_type, (Optional, Pointer)):
            inner = left_type.inner if isinstance(left_type, Optional) else left_type.target
            if inner == INT:
                left = ir.UnaryOp(op="*", operand=left, typ=INT, loc=loc_from_node(node))
        return ir.BinaryOp(op=op, left=left, right=right, typ=BOOL, loc=loc_from_node(node))
    # Chain comparisons - convert to AND of pairwise comparisons
    result = None
    prev = lower_expr(node.left)
    for op, comp in zip(node.ops, node.comparators):
        curr = lower_expr(comp)
        cmp = ir.BinaryOp(op=cmpop_to_str(op), left=prev, right=curr, typ=BOOL, loc=loc_from_node(node))
        if result is None:
            result = cmp
        else:
            result = ir.BinaryOp(op="&&", left=result, right=cmp, typ=BOOL, loc=loc_from_node(node))
        prev = curr
    return result or ir.BoolLit(value=True, typ=BOOL)


def lower_expr_BoolOp(
    node: ast.BoolOp,
    lower_expr_as_bool: Callable[[ast.expr], "ir.Expr"],
) -> "ir.Expr":
    """Lower Python boolean operation to IR."""
    from .. import ir
    op = "&&" if isinstance(node.op, ast.And) else "||"
    result = lower_expr_as_bool(node.values[0])
    for val in node.values[1:]:
        right = lower_expr_as_bool(val)
        result = ir.BinaryOp(op=op, left=result, right=right, typ=BOOL, loc=loc_from_node(node))
    return result


def lower_expr_UnaryOp(
    node: ast.UnaryOp,
    lower_expr: Callable[[ast.expr], "ir.Expr"],
    lower_expr_as_bool: Callable[[ast.expr], "ir.Expr"],
) -> "ir.Expr":
    """Lower Python unary operation to IR."""
    from .. import ir
    # For 'not' operator, convert operand to boolean first
    if isinstance(node.op, ast.Not):
        operand = lower_expr_as_bool(node.operand)
        return ir.UnaryOp(op="!", operand=operand, typ=BOOL, loc=loc_from_node(node))
    operand = lower_expr(node.operand)
    op = unaryop_to_str(node.op)
    return ir.UnaryOp(op=op, operand=operand, typ=Interface("any"), loc=loc_from_node(node))


# ============================================================
# COLLECTION EXPRESSION LOWERING
# ============================================================


def lower_expr_List(
    node: ast.List,
    lower_expr: Callable[[ast.expr], "ir.Expr"],
    infer_expr_type_from_ast: Callable[[ast.expr], "Type"],
    expected_type_ctx: "Type | None",
    expected_type: "Type | None" = None,
) -> "ir.Expr":
    """Lower Python list literal to IR slice literal."""
    from .. import ir
    elements = [lower_expr(e) for e in node.elts]
    # Prefer expected type when available (bidirectional type inference)
    element_type: "Type" = Interface("any")
    if expected_type is not None and isinstance(expected_type, Slice):
        element_type = expected_type.element
    elif expected_type_ctx is not None and isinstance(expected_type_ctx, Slice):
        element_type = expected_type_ctx.element
    elif node.elts:
        # Fall back to inferring from first element
        element_type = infer_expr_type_from_ast(node.elts[0])
    return ir.SliceLit(
        element_type=element_type, elements=elements,
        typ=Slice(element_type), loc=loc_from_node(node)
    )


def lower_list_call_with_expected_type(
    node: ast.Call,
    lower_expr: Callable[[ast.expr], "ir.Expr"],
    expected_type: "Type | None",
) -> "ir.Expr":
    """Handle list(x) call with expected type context for covariant copies."""
    from .. import ir
    arg = lower_expr(node.args[0])
    source_type = arg.typ
    # Check if we need covariant conversion: []*Derived -> []Interface
    if (expected_type is not None and isinstance(expected_type, Slice) and
        isinstance(source_type, Slice)):
        source_elem = source_type.element
        target_elem = expected_type.element
        # Unwrap pointer for comparison
        if isinstance(source_elem, Pointer):
            source_elem_unwrapped = source_elem.target
        else:
            source_elem_unwrapped = source_elem
        # Need conversion if: source is *Struct, target is interface/Node
        if (source_elem != target_elem and
            isinstance(source_elem_unwrapped, StructRef) and
            isinstance(target_elem, (Interface, StructRef))):
            return ir.SliceConvert(
                source=arg,
                target_element_type=target_elem,
                typ=expected_type,
                loc=loc_from_node(node)
            )
    # Fall through to normal copy
    return ir.MethodCall(
        obj=arg, method="copy", args=[],
        receiver_type=source_type if isinstance(source_type, Slice) else Slice(Interface("any")),
        typ=source_type if isinstance(source_type, Slice) else Slice(Interface("any")),
        loc=loc_from_node(node)
    )


def lower_expr_Dict(
    node: ast.Dict,
    lower_expr: Callable[[ast.expr], "ir.Expr"],
    infer_expr_type_from_ast: Callable[[ast.expr], "Type"],
) -> "ir.Expr":
    """Lower Python dict literal to IR map literal."""
    from .. import ir
    entries = []
    for k, v in zip(node.keys, node.values):
        if k is not None:
            entries.append((lower_expr(k), lower_expr(v)))
    # Infer key and value types from first entry if available
    key_type: "Type" = STRING
    value_type: "Type" = Interface("any")
    if node.values and node.values[0]:
        first_val = node.values[0]
        value_type = infer_expr_type_from_ast(first_val)
    return ir.MapLit(
        key_type=key_type, value_type=value_type, entries=entries,
        typ=Map(key_type, value_type), loc=loc_from_node(node)
    )


def lower_expr_JoinedStr(
    node: ast.JoinedStr,
    lower_expr: Callable[[ast.expr], "ir.Expr"],
) -> "ir.Expr":
    """Lower Python f-string to StringFormat IR node."""
    template_parts: list[str] = []
    args: list["ir.Expr"] = []
    for part in node.values:
        if isinstance(part, ast.Constant):
            # Escape % signs in literal parts for fmt.Sprintf
            template_parts.append(str(part.value).replace("%", "%%"))
        elif isinstance(part, ast.FormattedValue):
            template_parts.append("%v")
            args.append(lower_expr(part.value))
    template = "".join(template_parts)
    return StringFormat(template=template, args=args, typ=STRING, loc=loc_from_node(node))


def lower_expr_Tuple(
    node: ast.Tuple,
    lower_expr: Callable[[ast.expr], "ir.Expr"],
) -> "ir.Expr":
    """Lower Python tuple literal to TupleLit IR node."""
    from .. import ir
    elements = [lower_expr(e) for e in node.elts]
    element_types = tuple(e.typ for e in elements)
    return ir.TupleLit(elements=elements, typ=Tuple(elements=element_types), loc=loc_from_node(node))


def lower_expr_Set(
    node: ast.Set,
    lower_expr: Callable[[ast.expr], "ir.Expr"],
) -> "ir.Expr":
    """Lower Python set literal to SetLit IR node."""
    from .. import ir
    elements = [lower_expr(e) for e in node.elts]
    # Infer element type from first element
    elem_type = getattr(elements[0], 'typ', STRING) if elements else STRING
    return ir.SetLit(element_type=elem_type, elements=elements, typ=Set(elem_type), loc=loc_from_node(node))


# ============================================================
# EXPRESSION DISPATCHER
# ============================================================


def lower_expr_as_bool(
    node: ast.expr,
    lower_expr: Callable[[ast.expr], "ir.Expr"],
    lower_expr_as_bool_self: Callable[[ast.expr], "ir.Expr"],
    infer_expr_type_from_ast: Callable[[ast.expr], "Type"],
    is_isinstance_call: Callable[[ast.expr], tuple[str, str] | None],
    resolve_type_name: Callable[[str], "Type"],
    type_ctx: "TypeContext",
    symbols: "SymbolTable",
) -> "ir.Expr":
    """Lower expression used in boolean context, adding truthy checks as needed."""
    from .. import ir
    # Already boolean expressions - lower directly
    if isinstance(node, ast.Compare):
        return lower_expr(node)
    if isinstance(node, ast.BoolOp):
        # For BoolOp, recursively lower operands as booleans
        op = "&&" if isinstance(node.op, ast.And) else "||"
        result = lower_expr_as_bool_self(node.values[0])
        # Track isinstance narrowing for AND chains
        narrowed_var: str | None = None
        narrowed_old_type: Type | None = None
        was_already_narrowed = False
        if isinstance(node.op, ast.And):
            isinstance_check = is_isinstance_call(node.values[0])
            if isinstance_check:
                var_name, type_name = isinstance_check
                narrowed_var = var_name
                narrowed_old_type = type_ctx.var_types.get(var_name)
                was_already_narrowed = var_name in type_ctx.narrowed_vars
                type_ctx.var_types[var_name] = resolve_type_name(type_name)
                type_ctx.narrowed_vars.add(var_name)
        for val in node.values[1:]:
            right = lower_expr_as_bool_self(val)
            result = ir.BinaryOp(op=op, left=result, right=right, typ=BOOL, loc=loc_from_node(node))
        # Restore narrowed type and tracking
        if narrowed_var is not None:
            if narrowed_old_type is not None:
                type_ctx.var_types[narrowed_var] = narrowed_old_type
            else:
                type_ctx.var_types.pop(narrowed_var, None)
            if not was_already_narrowed:
                type_ctx.narrowed_vars.discard(narrowed_var)
        return result
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        operand = lower_expr_as_bool_self(node.operand)
        return ir.UnaryOp(op="!", operand=operand, typ=BOOL, loc=loc_from_node(node))
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return lower_expr(node)
    if isinstance(node, ast.Name) and node.id in ("True", "False"):
        return lower_expr(node)
    if isinstance(node, ast.Call):
        # Calls that return bool are fine
        if isinstance(node.func, ast.Attribute):
            # Methods like .startswith(), .endswith(), .isdigit() return bool
            if node.func.attr in ("startswith", "endswith", "isdigit", "isalpha", "isalnum", "isspace"):
                return lower_expr(node)
            # Check if the method returns bool by looking up its return type
            method_return_type = infer_expr_type_from_ast(node)
            if method_return_type == BOOL:
                return lower_expr(node)
        elif isinstance(node.func, ast.Name):
            if node.func.id in ("isinstance", "hasattr", "callable", "bool"):
                return lower_expr(node)
            # Check if the function returns bool by looking up its return type
            func_name = node.func.id
            if func_name in symbols.functions:
                func_info = symbols.functions[func_name]
                if func_info.return_type == BOOL:
                    return lower_expr(node)
    # Non-boolean expression - needs truthy check
    expr = lower_expr(node)
    # Use the IR expression's type if available, otherwise infer from AST
    expr_type = expr.typ if hasattr(expr, 'typ') and expr.typ != Interface("any") else infer_expr_type_from_ast(node)
    # Bool expressions don't need nil check
    if expr_type == BOOL:
        return expr
    # String truthy check: s != ""
    if expr_type == STRING:
        return ir.BinaryOp(op="!=", left=expr, right=ir.StringLit(value="", typ=STRING), typ=BOOL, loc=loc_from_node(node))
    # Int truthy check: n != 0
    if expr_type == INT:
        return ir.BinaryOp(op="!=", left=expr, right=ir.IntLit(value=0, typ=INT), typ=BOOL, loc=loc_from_node(node))
    # Slice/Map/Set truthy check: len(x) > 0
    if isinstance(expr_type, (Slice, Map, Set)):
        return ir.BinaryOp(op=">", left=ir.Len(expr=expr, typ=INT, loc=loc_from_node(node)), right=ir.IntLit(value=0, typ=INT), typ=BOOL, loc=loc_from_node(node))
    # Optional(Slice) truthy check: len(x) > 0 (nil slice has len 0)
    if isinstance(expr_type, Optional) and isinstance(expr_type.inner, (Slice, Map, Set)):
        return ir.BinaryOp(op=">", left=ir.Len(expr=expr, typ=INT, loc=loc_from_node(node)), right=ir.IntLit(value=0, typ=INT), typ=BOOL, loc=loc_from_node(node))
    # Interface truthy check: x != nil
    if isinstance(expr_type, Interface):
        return ir.IsNil(expr=expr, negated=True, typ=BOOL, loc=loc_from_node(node))
    # Pointer/Optional truthy check: x != nil
    if isinstance(expr_type, (Pointer, Optional)):
        return ir.IsNil(expr=expr, negated=True, typ=BOOL, loc=loc_from_node(node))
    # Check name that might be pointer or interface - use nil check
    if isinstance(node, ast.Name):
        # If type is interface, use nil check (interfaces are nilable)
        if isinstance(expr_type, Interface):
            return ir.IsNil(expr=expr, negated=True, typ=BOOL, loc=loc_from_node(node))
        # If type is a pointer, use nil check
        if isinstance(expr_type, (Pointer, Optional)):
            return ir.IsNil(expr=expr, negated=True, typ=BOOL, loc=loc_from_node(node))
        # Otherwise just return the expression (shouldn't reach here for valid types)
        return expr
    # For other expressions, assume it's a pointer check
    return ir.IsNil(expr=expr, negated=True, typ=BOOL, loc=loc_from_node(node))


def lower_expr_IfExp(
    node: ast.IfExp,
    lower_expr: Callable[[ast.expr], "ir.Expr"],
    lower_expr_as_bool: Callable[[ast.expr], "ir.Expr"],
    extract_attr_kind_check: Callable[[ast.expr], tuple[str, str] | None],
    type_ctx: "TypeContext",
) -> "ir.Expr":
    """Lower Python ternary (if-else expression) to Ternary IR node."""
    from .. import ir
    cond = lower_expr_as_bool(node.test)
    # Check for attribute path kind narrowing in the condition
    # e.g., node.body.kind == "brace-group" narrows node.body to BraceGroup
    attr_kind_check = extract_attr_kind_check(node.test)
    if attr_kind_check:
        attr_path, struct_name = attr_kind_check
        type_ctx.narrowed_attr_paths[attr_path] = struct_name
    then_expr = lower_expr(node.body)
    # Clean up the narrowing after processing then branch
    if attr_kind_check:
        del type_ctx.narrowed_attr_paths[attr_kind_check[0]]
    else_expr = lower_expr(node.orelse)
    # Use type from lowered expressions (prefer then branch, fall back to else)
    result_type = getattr(then_expr, 'typ', None)
    if result_type is None or result_type == Interface("any"):
        result_type = getattr(else_expr, 'typ', None)
    if result_type is None:
        result_type = Interface("any")
    return ir.Ternary(
        cond=cond, then_expr=then_expr, else_expr=else_expr,
        typ=result_type, loc=loc_from_node(node)
    )


# ============================================================
# SIMPLE STATEMENT LOWERING
# ============================================================


def is_super_init_call(node: ast.expr) -> bool:
    """Check if expression is super().__init__(...)."""
    if not isinstance(node, ast.Call):
        return False
    if not isinstance(node.func, ast.Attribute):
        return False
    if node.func.attr != "__init__":
        return False
    if not isinstance(node.func.value, ast.Call):
        return False
    if not isinstance(node.func.value.func, ast.Name):
        return False
    return node.func.value.func.id == "super"


def lower_stmt_Expr(
    node: ast.Expr,
    lower_expr: Callable[[ast.expr], "ir.Expr"],
) -> "ir.Stmt":
    """Lower expression statement."""
    from .. import ir
    # Skip docstrings
    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
        return ir.ExprStmt(expr=ir.Var(name="_skip_docstring", typ=VOID))
    # Skip super().__init__() calls - handled by Go embedding
    if is_super_init_call(node.value):
        return ir.ExprStmt(expr=ir.Var(name="_skip_super_init", typ=VOID))
    return ir.ExprStmt(expr=lower_expr(node.value), loc=loc_from_node(node))


def lower_stmt_AugAssign(
    node: ast.AugAssign,
    lower_lvalue: Callable[[ast.expr], "ir.LValue"],
    lower_expr: Callable[[ast.expr], "ir.Expr"],
) -> "ir.Stmt":
    """Lower augmented assignment (+=, -=, etc.)."""
    from .. import ir
    lval = lower_lvalue(node.target)
    value = lower_expr(node.value)
    op = binop_to_str(node.op)
    return ir.OpAssign(target=lval, op=op, value=value, loc=loc_from_node(node))


def lower_stmt_While(
    node: ast.While,
    lower_expr_as_bool: Callable[[ast.expr], "ir.Expr"],
    lower_stmts: Callable[[list[ast.stmt]], list["ir.Stmt"]],
) -> "ir.Stmt":
    """Lower while loop."""
    from .. import ir
    cond = lower_expr_as_bool(node.test)
    body = lower_stmts(node.body)
    return ir.While(cond=cond, body=body, loc=loc_from_node(node))


def lower_stmt_Break(node: ast.Break) -> "ir.Stmt":
    """Lower break statement."""
    from .. import ir
    return ir.Break(loc=loc_from_node(node))


def lower_stmt_Continue(node: ast.Continue) -> "ir.Stmt":
    """Lower continue statement."""
    from .. import ir
    return ir.Continue(loc=loc_from_node(node))


def lower_stmt_Pass(node: ast.Pass) -> "ir.Stmt":
    """Lower pass statement."""
    from .. import ir
    return ir.ExprStmt(expr=ir.Var(name="_pass", typ=VOID), loc=loc_from_node(node))


def lower_stmt_FunctionDef(node: ast.FunctionDef) -> "ir.Stmt":
    """Lower local function definition (placeholder)."""
    from .. import ir
    return ir.ExprStmt(expr=ir.Var(name=f"_local_func_{node.name}", typ=VOID))


def lower_stmt_Return(
    node: ast.Return,
    lower_expr: Callable[[ast.expr], "ir.Expr"],
    synthesize_type: Callable[["ir.Expr"], "Type"],
    coerce: Callable[["ir.Expr", "Type", "Type"], "ir.Expr"],
    return_type: "Type | None",
) -> "ir.Stmt":
    """Lower return statement."""
    from .. import ir
    value = lower_expr(node.value) if node.value else None
    # Apply type coercion based on function return type
    if value and return_type:
        from_type = synthesize_type(value)
        value = coerce(value, from_type, return_type)
    return ir.Return(value=value, loc=loc_from_node(node))


# ============================================================
# EXCEPTION STATEMENT LOWERING
# ============================================================


def lower_stmt_Raise(
    node: ast.Raise,
    lower_expr: Callable[[ast.expr], "ir.Expr"],
    current_catch_var: str | None,
) -> "ir.Stmt":
    """Lower raise statement."""
    from .. import ir
    if node.exc:
        # Check if raising the catch variable (re-raise pattern)
        if isinstance(node.exc, ast.Name) and node.exc.id == current_catch_var:
            return ir.Raise(
                error_type="Error",
                message=ir.StringLit(value="", typ=STRING),
                pos=ir.IntLit(value=0, typ=INT),
                reraise_var=current_catch_var,
                loc=loc_from_node(node),
            )
        # Extract error type and message from exception
        if isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
            error_type = node.exc.func.id
            msg = lower_expr(node.exc.args[0]) if node.exc.args else ir.StringLit(value="", typ=STRING)
            # Check for pos kwarg
            pos = ir.IntLit(value=0, typ=INT)
            if len(node.exc.args) > 1:
                pos = lower_expr(node.exc.args[1])
            else:
                # Check kwargs for pos
                for kw in node.exc.keywords:
                    if kw.arg == "pos":
                        pos = lower_expr(kw.value)
                        break
            return ir.Raise(error_type=error_type, message=msg, pos=pos, loc=loc_from_node(node))
    return ir.Raise(error_type="Error", message=ir.StringLit(value="", typ=STRING), pos=ir.IntLit(value=0, typ=INT), loc=loc_from_node(node))
