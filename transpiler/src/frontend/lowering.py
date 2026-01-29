"""Lowering utilities extracted from frontend.py."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from ..ir import BOOL, FLOAT, INT, STRING, Interface, Loc, Optional, Pointer, Slice, Tuple

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
