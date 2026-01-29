"""Lowering utilities extracted from frontend.py."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from .ast_compat import ASTNode, is_type, op_type

from ..ir import (
    BOOL,
    BYTE,
    FLOAT,
    INT,
    RUNE,
    STRING,
    VOID,
    InterfaceRef,
    Loc,
    Map,
    Optional,
    Pointer,
    Set,
    Slice,
    StringFormat,
    StructRef,
    Tuple,
)
from ..type_overrides import NODE_METHOD_TYPES, SENTINEL_INT_FIELDS, VAR_TYPE_OVERRIDES
from . import type_inference

if TYPE_CHECKING:
    from .. import ir
    from ..ir import FuncInfo, SymbolTable, Type
    from .context import FrontendContext, LoweringDispatch, TypeContext


def loc_from_node(node: ASTNode) -> Loc:
    """Create Loc from AST node."""
    lineno = node.get("lineno") if isinstance(node, dict) else None
    if lineno is not None:
        col = node.get("col_offset", 0)
        end_lineno = node.get("end_lineno", lineno) or lineno
        end_col = node.get("end_col_offset", col) or col
        return Loc(line=lineno, col=col, end_line=end_lineno, end_col=end_col)
    return Loc.unknown()


def make_default_value(typ: "Type", loc: Loc) -> "ir.Expr":
    """Create a default value expression for a given type."""
    from .. import ir
    from ..ir import (
        BOOL,
        FLOAT,
        INT,
        STRING,
        Map,
        Optional,
        Pointer,
        Primitive,
        Set,
        Slice,
        StructRef,
    )

    # Pointer and interface types use nil
    if isinstance(typ, (Pointer, Optional, InterfaceRef)):
        return ir.NilLit(typ=typ, loc=loc)
    # Primitive types use their zero values
    if isinstance(typ, Primitive):
        if typ.kind == "bool":
            return ir.BoolLit(value=False, typ=BOOL, loc=loc)
        if typ.kind == "int":
            return ir.IntLit(value=0, typ=INT, loc=loc)
        if typ.kind == "string":
            return ir.StringLit(value="", typ=STRING, loc=loc)
        if typ.kind == "float":
            return ir.FloatLit(value=0.0, typ=FLOAT, loc=loc)
    # Slice/Map/Set use nil (Go zero value)
    if isinstance(typ, (Slice, Map, Set)):
        return ir.NilLit(typ=typ, loc=loc)
    # StructRef uses nil (pointer to struct)
    if isinstance(typ, StructRef):
        return ir.NilLit(typ=Pointer(typ), loc=loc)
    # Fallback to nil
    return ir.NilLit(typ=typ, loc=loc)


def binop_to_str(op: ASTNode) -> str:
    """Convert AST binary operator to string."""
    return {
        "Add": "+",
        "Sub": "-",
        "Mult": "*",
        "Div": "/",
        "FloorDiv": "/",
        "Mod": "%",
        "Pow": "**",
        "LShift": "<<",
        "RShift": ">>",
        "BitOr": "|",
        "BitXor": "^",
        "BitAnd": "&",
    }.get(op_type(op), "+")


def cmpop_to_str(op: ASTNode) -> str:
    """Convert AST comparison operator to string."""
    return {
        "Eq": "==",
        "NotEq": "!=",
        "Lt": "<",
        "LtE": "<=",
        "Gt": ">",
        "GtE": ">=",
        "Is": "==",
        "IsNot": "!=",
        "In": "in",
        "NotIn": "not in",
    }.get(op_type(op), "==")


def unaryop_to_str(op: ASTNode) -> str:
    """Convert AST unary operator to string."""
    return {"Not": "!", "USub": "-", "UAdd": "+", "Invert": "~"}.get(op_type(op), "-")


# ============================================================
# TYPE NARROWING HELPERS
# ============================================================


def is_isinstance_call(node: ASTNode) -> tuple[str, str] | None:
    """Check if node is isinstance(var, Type). Returns (var_name, type_name) or None."""
    if not is_type(node, ["Call"]):
        return None
    func = node.get("func")
    if not is_type(func, ["Name"]) or func.get("id") != "isinstance":
        return None
    args = node.get("args", [])
    if len(args) != 2:
        return None
    if not is_type(args[0], ["Name"]):
        return None
    if not is_type(args[1], ["Name"]):
        return None
    return (args[0].get("id"), args[1].get("id"))


def is_kind_check(node: ASTNode, kind_to_class: dict[str, str]) -> tuple[str, str] | None:
    """Check if node is x.kind == "typename". Returns (var_name, class_name) or None."""
    if not is_type(node, ["Compare"]):
        return None
    ops = node.get("ops", [])
    comparators = node.get("comparators", [])
    if len(ops) != 1 or not is_type(ops[0], ["Eq"]):
        return None
    if len(comparators) != 1:
        return None
    # Check for x.kind on left side
    left = node.get("left")
    if not is_type(left, ["Attribute"]) or left.get("attr") != "kind":
        return None
    left_value = left.get("value")
    if not is_type(left_value, ["Name"]):
        return None
    var_name = left_value.get("id")
    # Check for string constant on right side
    comparator = comparators[0]
    if not is_type(comparator, ["Constant"]) or not isinstance(comparator.get("value"), str):
        return None
    kind_value = comparator.get("value")
    # Map kind string to class name
    if kind_value not in kind_to_class:
        return None
    return (var_name, kind_to_class[kind_value])


def extract_isinstance_or_chain(
    node: ASTNode, kind_to_class: dict[str, str]
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
    if is_type(node, ["BoolOp"]) and is_type(node.get("op"), ["Or"]):
        var_name: str | None = None
        type_names: list[str] = []
        for value in node.get("values", []):
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


def extract_isinstance_from_and(node: ASTNode) -> tuple[str, str] | None:
    """Extract isinstance(var, Type) from compound AND expression.
    Returns (var_name, type_name) or None if no isinstance found."""
    if not is_type(node, ["BoolOp"]):
        return None
    op = node.get("op")
    if not is_type(op, ["And"]):
        return None
    # Check each value in the AND chain for isinstance
    for value in node.get("values", []):
        result = is_isinstance_call(value)
        if result:
            return result
    return None


def extract_kind_check(
    node: ASTNode, kind_to_struct: dict[str, str], kind_source_vars: dict[str, str]
) -> tuple[str, str] | None:
    """Extract kind-based type narrowing from `kind == "value"` or `node.kind == "value"`.
    Returns (node_var_name, struct_name) or None if not a kind check."""
    # Match: kind == "value" where kind was previously assigned from node.kind
    ops = node.get("ops", [])
    if is_type(node, ["Compare"]) and len(ops) == 1 and is_type(ops[0], ["Eq"]):
        left = node.get("left")
        comparators = node.get("comparators", [])
        right = comparators[0] if comparators else {}
        # Check for var == "kind_value" pattern
        if (
            is_type(left, ["Name"])
            and is_type(right, ["Constant"])
            and isinstance(right.get("value"), str)
        ):
            kind_var = left.get("id")
            kind_value = right.get("value")
            if kind_value in kind_to_struct:
                # Look up which Node-typed variable this kind var came from
                if kind_var in kind_source_vars:
                    node_var = kind_source_vars[kind_var]
                    return (node_var, kind_to_struct[kind_value])
        # Check for node.kind == "value" pattern
        if (
            is_type(left, ["Attribute"])
            and left.get("attr") == "kind"
            and is_type(left.get("value"), ["Name"])
        ):
            node_var = left.get("value", {}).get("id")
            if is_type(right, ["Constant"]) and isinstance(right.get("value"), str):
                kind_value = right.get("value")
                if kind_value in kind_to_struct:
                    return (node_var, kind_to_struct[kind_value])
    return None


def extract_attr_kind_check(
    node: ASTNode, kind_to_struct: dict[str, str]
) -> tuple[tuple[str, ...], str] | None:
    """Extract kind check for attribute paths like `node.body.kind == "value"`.
    Returns (attr_path_tuple, struct_name) or None."""
    ops = node.get("ops", [])
    if is_type(node, ["Compare"]) and len(ops) == 1 and is_type(ops[0], ["Eq"]):
        left = node.get("left")
        comparators = node.get("comparators", [])
        right = comparators[0] if comparators else {}
        # Check for expr.kind == "value" pattern where expr is an attribute chain
        if (
            is_type(left, ["Attribute"])
            and left.get("attr") == "kind"
            and is_type(right, ["Constant"])
            and isinstance(right.get("value"), str)
        ):
            kind_value = right.get("value")
            if kind_value in kind_to_struct:
                # Extract the attribute path (e.g., node.body -> ("node", "body"))
                attr_path = get_attr_path(left.get("value"))
                if attr_path and len(attr_path) > 1:  # Only for chains, not simple vars
                    return (attr_path, kind_to_struct[kind_value])
    return None


def get_attr_path(node: ASTNode) -> tuple[str, ...] | None:
    """Extract attribute path as tuple (e.g., node.body -> ("node", "body"))."""
    if is_type(node, ["Name"]):
        return (node.get("id"),)
    elif is_type(node, ["Attribute"]) and is_type(node.get("value"), ["Name", "Attribute"]):
        base = get_attr_path(node.get("value"))
        if base:
            return base + (node.get("attr"),)
    return None


def resolve_type_name(
    name: str, type_map: dict[str, "ir.Type"], symbols: "ir.SymbolTable"
) -> "ir.Type":
    """Resolve a class name to an IR type (for isinstance checks)."""
    from ..ir import Pointer, StructRef

    # Handle primitive types
    if name in type_map:
        return type_map[name]
    if name in symbols.structs:
        return Pointer(StructRef(name))
    return InterfaceRef(name)


# ============================================================
# ARGUMENT HELPERS
# ============================================================


def convert_negative_index(
    idx_node: ASTNode,
    obj: "ir.Expr",
    parent: ASTNode,
    lower_expr: Callable[[ASTNode], "ir.Expr"],
) -> "ir.Expr":
    """Convert negative index -N to len(obj) - N."""
    from .. import ir

    # Check for -N pattern (UnaryOp with USub on positive int constant)
    if is_type(idx_node, ["UnaryOp"]) and is_type(idx_node.get("op"), ["USub"]):
        operand = idx_node.get("operand")
        if is_type(operand, ["Constant"]) and isinstance(operand.get("value"), int):
            n = operand.get("value")
            if n > 0:
                # len(obj) - N
                return ir.BinaryOp(
                    op="-",
                    left=ir.Len(expr=obj, typ=INT, loc=loc_from_node(parent)),
                    right=ir.IntLit(value=n, typ=INT, loc=loc_from_node(idx_node)),
                    typ=INT,
                    loc=loc_from_node(idx_node),
                )
    # Not a negative constant, lower normally
    return lower_expr(idx_node)


def merge_keyword_args(
    obj_type: "Type",
    method: str,
    args: list["ir.Expr"],
    node: ASTNode,
    symbols: "SymbolTable",
    lower_expr: Callable[[ASTNode], "ir.Expr"],
    extract_struct_name: Callable[["Type"], str | None],
) -> list["ir.Expr"]:
    """Merge keyword arguments into positional args at their proper positions."""
    keywords = node.get("keywords", [])
    if not keywords:
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
    for kw in keywords:
        kw_arg = kw.get("arg")
        if kw_arg and kw_arg in param_indices:
            idx = param_indices[kw_arg]
            # Extend list if necessary
            while len(result) <= idx:
                result.append(None)
            result[idx] = lower_expr(kw.get("value"))
    return result


def fill_default_args(
    obj_type: "Type",
    method: str,
    args: list["ir.Expr"],
    symbols: "SymbolTable",
    extract_struct_name: Callable[["Type"], str | None],
) -> list["ir.Expr"]:
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
    args: list["ir.Expr"],
    node: ASTNode,
    lower_expr: Callable[[ASTNode], "ir.Expr"],
) -> list["ir.Expr"]:
    """Merge keyword arguments into positional args at their proper positions for free functions."""
    keywords = node.get("keywords", [])
    if not keywords:
        return args
    # Build param name -> index map
    param_indices: dict[str, int] = {}
    for i, param in enumerate(func_info.params):
        param_indices[param.name] = i
    # Extend args list if needed and place keyword args
    result = list(args)
    for kw in keywords:
        kw_arg = kw.get("arg")
        if kw_arg and kw_arg in param_indices:
            idx = param_indices[kw_arg]
            # Extend list if necessary
            while len(result) <= idx:
                result.append(None)
            result[idx] = lower_expr(kw.get("value"))
    return result


def fill_default_args_for_func(func_info: "FuncInfo", args: list["ir.Expr"]) -> list["ir.Expr"]:
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
    args: list["ir.Expr"],
    orig_args: list[ASTNode],
    symbols: "SymbolTable",
    extract_struct_name: Callable[["Type"], str | None],
    infer_expr_type_from_ast: Callable[[ASTNode], "Type"],
) -> list["ir.Expr"]:
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
                result[i] = ir.UnaryOp(
                    op="&",
                    operand=arg,
                    typ=param_type,
                    loc=arg.loc if hasattr(arg, "loc") else Loc.unknown(),
                )
    return result


def deref_for_slice_params(
    obj_type: "Type",
    method: str,
    args: list["ir.Expr"],
    orig_args: list[ASTNode],
    symbols: "SymbolTable",
    extract_struct_name: Callable[["Type"], str | None],
    infer_expr_type_from_ast: Callable[[ASTNode], "Type"],
) -> list["ir.Expr"]:
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
                result[i] = ir.UnaryOp(
                    op="*",
                    operand=arg,
                    typ=inner_slice,
                    loc=arg.loc if hasattr(arg, "loc") else Loc.unknown(),
                )
    return result


def deref_for_func_slice_params(
    func_name: str,
    args: list["ir.Expr"],
    orig_args: list[ASTNode],
    symbols: "SymbolTable",
    infer_expr_type_from_ast: Callable[[ASTNode], "Type"],
) -> list["ir.Expr"]:
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
                result[i] = ir.UnaryOp(
                    op="*",
                    operand=arg,
                    typ=inner_slice,
                    loc=arg.loc if hasattr(arg, "loc") else Loc.unknown(),
                )
    return result


def coerce_args_to_node(func_info: "FuncInfo", args: list["ir.Expr"]) -> list["ir.Expr"]:
    """Add type assertions when passing interface{} to Node parameter."""
    from .. import ir

    result = list(args)
    for i, arg in enumerate(result):
        if i >= len(func_info.params):
            break
        param = func_info.params[i]
        param_type = param.typ
        # Check if param expects Node but arg is interface{}
        if isinstance(param_type, InterfaceRef) and param_type.name == "Node":
            arg_type = getattr(arg, "typ", None)
            # interface{} is represented as InterfaceRef("any")
            if arg_type == InterfaceRef("any"):
                result[i] = ir.TypeAssert(
                    expr=arg,
                    asserted=InterfaceRef("Node"),
                    safe=True,
                    typ=InterfaceRef("Node"),
                    loc=arg.loc if hasattr(arg, "loc") else Loc.unknown(),
                )
    return result


def is_pointer_to_slice(typ: "Type") -> bool:
    """Check if type is pointer-to-slice (Pointer(Slice) only, NOT Optional(Slice))."""
    if isinstance(typ, Pointer) and isinstance(typ.target, Slice):
        return True
    return False


def is_len_call(node: ASTNode) -> bool:
    """Check if node is a len() call."""
    if not is_type(node, ["Call"]):
        return False
    func = node.get("func")
    return is_type(func, ["Name"]) and func.get("id") == "len"


def get_inner_slice(typ: "Type") -> Slice | None:
    """Get the inner Slice from Pointer(Slice) only, NOT Optional(Slice)."""
    if isinstance(typ, Pointer) and isinstance(typ.target, Slice):
        return typ.target
    return None


def coerce_sentinel_to_ptr(
    obj_type: "Type",
    method: str,
    args: list["ir.Expr"],
    orig_args: list[ASTNode],
    symbols: "SymbolTable",
    sentinel_ints: set[str],
    extract_struct_name: Callable[["Type"], str | None],
) -> list["ir.Expr"]:
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
            if i < len(orig_args) and is_type(orig_args[i], ["Name"]):
                var_name = orig_args[i].get("id")
                if var_name in sentinel_ints:
                    # Wrap in _intPtr() call
                    result[i] = ir.Call(func="_intPtr", args=[arg], typ=param.typ, loc=arg.loc)
    return result


# ============================================================
# SIMPLE EXPRESSION LOWERING
# ============================================================


def lower_expr_Constant(node: ASTNode) -> "ir.Expr":
    """Lower Python constant to IR literal."""
    from .. import ir

    value = node.get("value")
    if isinstance(value, bool):
        return ir.BoolLit(value=value, typ=BOOL, loc=loc_from_node(node))
    if isinstance(value, int):
        return ir.IntLit(value=value, typ=INT, loc=loc_from_node(node))
    if isinstance(value, float):
        return ir.FloatLit(value=value, typ=FLOAT, loc=loc_from_node(node))
    if isinstance(value, str):
        return ir.StringLit(value=value, typ=STRING, loc=loc_from_node(node))
    if value is None:
        return ir.NilLit(typ=InterfaceRef("any"), loc=loc_from_node(node))
    return ir.Var(name=f"TODO_Constant_{type(value)}", typ=InterfaceRef("any"))


def lower_expr_Name(
    node: ASTNode,
    type_ctx: "TypeContext",
    symbols: "SymbolTable",
) -> "ir.Expr":
    """Lower Python name to IR variable."""
    from .. import ir

    node_id = node.get("id")
    if node_id == "True":
        return ir.BoolLit(value=True, typ=BOOL, loc=loc_from_node(node))
    if node_id == "False":
        return ir.BoolLit(value=False, typ=BOOL, loc=loc_from_node(node))
    if node_id == "None":
        return ir.NilLit(typ=InterfaceRef("any"), loc=loc_from_node(node))
    # Handle expanded tuple variables: result -> TupleLit(result0, result1)
    if node_id in type_ctx.tuple_vars:
        synthetic_names = type_ctx.tuple_vars[node_id]
        elements = []
        elem_types = []
        for syn_name in synthetic_names:
            typ = type_ctx.var_types.get(syn_name, InterfaceRef("any"))
            elements.append(ir.Var(name=syn_name, typ=typ, loc=loc_from_node(node)))
            elem_types.append(typ)
        return ir.TupleLit(elements=elements, typ=Tuple(tuple(elem_types)), loc=loc_from_node(node))
    # Look up variable type from context, or constants for module-level constants
    var_type = type_ctx.var_types.get(node_id)
    if var_type is None:
        var_type = symbols.constants.get(node_id, InterfaceRef("any"))
    return ir.Var(name=node_id, typ=var_type, loc=loc_from_node(node))


def lower_expr_Attribute(
    node: ASTNode,
    symbols: "SymbolTable",
    type_ctx: "TypeContext",
    current_class_name: str,
    node_field_types: dict[str, list[str]],
    lower_expr: Callable[[ASTNode], "ir.Expr"],
    is_node_interface_type: Callable[["Type | None"], bool],
) -> "ir.Expr":
    """Lower Python attribute access to IR field access."""
    from .. import ir

    node_value = node.get("value", {})
    node_attr = node.get("attr")
    # Check for class constant access (e.g., TokenType.EOF -> TokenType_EOF)
    if is_type(node_value, ["Name"]):
        class_name = node_value.get("id")
        const_name = f"{class_name}_{node_attr}"
        if const_name in symbols.constants:
            return ir.Var(name=const_name, typ=INT, loc=loc_from_node(node))
    obj = lower_expr(node_value)
    # If accessing field on a narrowed variable, wrap in TypeAssert
    if is_type(node_value, ["Name"]) and node_value.get("id") in type_ctx.narrowed_vars:
        var_type = type_ctx.var_types.get(node_value.get("id"))
        if var_type and isinstance(var_type, Pointer) and isinstance(var_type.target, StructRef):
            obj = ir.TypeAssert(
                expr=obj, asserted=var_type, safe=True, typ=var_type, loc=loc_from_node(node_value)
            )
    # Check if accessing a field on a Node-typed expression that isn't in the interface
    # Node interface only has Kind() method, so any other field needs a type assertion
    obj_type = getattr(obj, "typ", None)
    if is_node_interface_type(obj_type) and node_attr != "kind":
        # Look up which struct types have this field
        if node_attr in node_field_types:
            struct_names = node_field_types[node_attr]
            # If the variable is from a union type, prefer a struct from the union
            chosen_struct = struct_names[0]  # Default: first in NODE_FIELD_TYPES
            # Check if the object expression has a narrowed type from a kind check
            obj_attr_path = get_attr_path(node_value)
            if obj_attr_path and obj_attr_path in type_ctx.narrowed_attr_paths:
                narrowed_struct = type_ctx.narrowed_attr_paths[obj_attr_path]
                if narrowed_struct in struct_names:
                    chosen_struct = narrowed_struct
            elif is_type(node_value, ["Name"]):
                var_name = node_value.get("id")
                if var_name in type_ctx.union_types:
                    union_structs = type_ctx.union_types[var_name]
                    # Find intersection of union structs and field structs
                    for s in union_structs:
                        if s in struct_names:
                            chosen_struct = s
                            break
            asserted_type = Pointer(StructRef(chosen_struct))
            obj = ir.TypeAssert(
                expr=obj,
                asserted=asserted_type,
                safe=True,
                typ=asserted_type,
                loc=loc_from_node(node_value),
            )
    # Infer field type for self.field accesses
    field_type: "Type" = InterfaceRef("any")
    if is_type(node_value, ["Name"]) and node_value.get("id") == "self":
        if current_class_name in symbols.structs:
            struct_info = symbols.structs[current_class_name]
            field_info = struct_info.fields.get(node_attr)
            if field_info:
                field_type = field_info.typ
    # Also look up field type from the asserted struct type
    if isinstance(obj, ir.TypeAssert):
        asserted = obj.asserted
        if isinstance(asserted, Pointer) and isinstance(asserted.target, StructRef):
            struct_name = asserted.target.name
            if struct_name in symbols.structs:
                field_info = symbols.structs[struct_name].fields.get(node_attr)
                if field_info:
                    field_type = field_info.typ
    # Look up field type from object's type (for variables with known struct types)
    if field_type == InterfaceRef("any") and obj_type is not None:
        struct_name = None
        if isinstance(obj_type, Pointer) and isinstance(obj_type.target, StructRef):
            struct_name = obj_type.target.name
        elif isinstance(obj_type, StructRef):
            struct_name = obj_type.name
        if struct_name and struct_name in symbols.structs:
            field_info = symbols.structs[struct_name].fields.get(node_attr)
            if field_info:
                field_type = field_info.typ
    return ir.FieldAccess(obj=obj, field=node_attr, typ=field_type, loc=loc_from_node(node))


def lower_expr_Subscript(
    node: ASTNode,
    type_ctx: "TypeContext",
    lower_expr: Callable[[ASTNode], "ir.Expr"],
    convert_negative_index: Callable[[ASTNode, "ir.Expr", ASTNode], "ir.Expr"],
    infer_expr_type_from_ast: Callable[[ASTNode], "Type"],
) -> "ir.Expr":
    """Lower Python subscript access to IR index or slice expression."""
    from .. import ir

    node_value = node.get("value")
    node_slice = node.get("slice")
    # Check for tuple var indexing: cmdsub_result[0] -> cmdsub_result0
    if is_type(node_value, ["Name"]) and is_type(node_slice, ["Constant"]):
        var_name = node_value.get("id")
        slice_value = node_slice.get("value")
        if var_name in type_ctx.tuple_vars and isinstance(slice_value, int):
            idx = slice_value
            synthetic_names = type_ctx.tuple_vars[var_name]
            if 0 <= idx and idx < len(synthetic_names):
                syn_name = synthetic_names[idx]
                typ = type_ctx.var_types.get(syn_name, InterfaceRef("any"))
                return ir.Var(name=syn_name, typ=typ, loc=loc_from_node(node))
    obj = lower_expr(node_value)
    if is_type(node_slice, ["Slice"]):
        slice_lower = node_slice.get("lower")
        slice_upper = node_slice.get("upper")
        low = convert_negative_index(slice_lower, obj, node) if slice_lower else None
        high = convert_negative_index(slice_upper, obj, node) if slice_upper else None
        # Slicing preserves type - string slice is still string, slice of slice is still slice
        slice_type: "Type" = infer_expr_type_from_ast(node_value)
        if slice_type == InterfaceRef("any"):
            slice_type = obj.typ if hasattr(obj, "typ") else InterfaceRef("any")
        return ir.SliceExpr(obj=obj, low=low, high=high, typ=slice_type, loc=loc_from_node(node))
    idx = convert_negative_index(node_slice, obj, node)
    # Infer element type from slice type
    elem_type: "Type" = InterfaceRef("any")
    obj_type = getattr(obj, "typ", None)
    if isinstance(obj_type, Slice):
        elem_type = obj_type.element
    # Handle tuple indexing: tuple[0] -> tuple.F0 (as FieldAccess)
    if (
        isinstance(obj_type, Tuple)
        and is_type(node_slice, ["Constant"])
        and isinstance(node_slice.get("value"), int)
    ):
        field_idx = node_slice.get("value")
        if 0 <= field_idx and field_idx < len(obj_type.elements):
            elem_type = obj_type.elements[field_idx]
            return ir.FieldAccess(
                obj=obj, field=f"F{field_idx}", typ=elem_type, loc=loc_from_node(node)
            )
    index_expr = ir.Index(obj=obj, index=idx, typ=elem_type, loc=loc_from_node(node))
    # Check if indexing a string - if so, wrap with Cast to string
    # In Go, string[i] returns byte, but Python returns str
    # Check both AST inference and lowered expression type
    is_string = infer_expr_type_from_ast(node_value) == STRING
    if not is_string and hasattr(obj, "typ") and obj.typ == STRING:
        is_string = True
    if is_string:
        return ir.Cast(expr=index_expr, to_type=STRING, typ=STRING, loc=loc_from_node(node))
    return index_expr


# ============================================================
# OPERATOR EXPRESSION LOWERING
# ============================================================


def lower_expr_BinOp(
    node: ASTNode,
    lower_expr: Callable[[ASTNode], "ir.Expr"],
    infer_expr_type_from_ast: Callable[[ASTNode], "Type"],
) -> "ir.Expr":
    """Lower Python binary operation to IR."""
    from .. import ir

    left = lower_expr(node.get("left"))
    right = lower_expr(node.get("right"))
    op = binop_to_str(node.get("op"))
    # Infer result type based on operator
    node_op = node.get("op")
    result_type: "Type" = InterfaceRef("any")
    if is_type(node_op, ["BitAnd", "BitOr", "BitXor", "LShift", "RShift"]):
        result_type = INT
    elif is_type(node_op, ["Add", "Sub", "Mult", "FloorDiv", "Mod"]):
        left_type = infer_expr_type_from_ast(node.get("left"))
        right_type = infer_expr_type_from_ast(node.get("right"))
        # String concatenation
        if left_type == STRING or right_type == STRING:
            result_type = STRING
        elif left_type == INT or right_type == INT:
            result_type = INT
    return ir.BinaryOp(op=op, left=left, right=right, typ=result_type, loc=loc_from_node(node))


def get_sentinel_value(
    node: ASTNode,
    type_ctx: "TypeContext",
    current_class_name: str,
    sentinel_int_fields: dict[tuple[str, str], int],
) -> int | None:
    """Get the sentinel value for a sentinel int expression, or None if not a sentinel int."""
    # Local variable sentinel ints (always use -1)
    if is_type(node, ["Name"]) and node.get("id") in type_ctx.sentinel_ints:
        return -1
    # Field sentinel ints: self.field
    node_value = node.get("value") if is_type(node, ["Attribute"]) else None
    if (
        is_type(node, ["Attribute"])
        and is_type(node_value, ["Name"])
        and node_value.get("id") == "self"
    ):
        class_name = current_class_name
        field_name = node.get("attr")
        if (class_name, field_name) in sentinel_int_fields:
            return sentinel_int_fields[(class_name, field_name)]
    return None


def is_sentinel_int(
    node: ASTNode,
    type_ctx: "TypeContext",
    current_class_name: str,
    sentinel_int_fields: dict[tuple[str, str], int],
) -> bool:
    """Check if an expression is a sentinel int (uses a sentinel value for None)."""
    return get_sentinel_value(node, type_ctx, current_class_name, sentinel_int_fields) is not None


def lower_expr_Compare(
    node: ASTNode,
    lower_expr: Callable[[ASTNode], "ir.Expr"],
    infer_expr_type_from_ast: Callable[[ASTNode], "Type"],
    type_ctx: "TypeContext",
    current_class_name: str,
    sentinel_int_fields: dict[tuple[str, str], int],
) -> "ir.Expr":
    """Lower Python comparison to IR."""
    from .. import ir

    ops = node.get("ops", [])
    comparators = node.get("comparators", [])
    node_left = node.get("left")
    # Handle simple comparisons
    if len(ops) == 1 and len(comparators) == 1:
        left = lower_expr(node_left)
        right = lower_expr(comparators[0])
        op = cmpop_to_str(ops[0])
        # Special case for "is None" / "is not None"
        if (
            is_type(ops[0], ["Is"])
            and is_type(comparators[0], ["Constant"])
            and comparators[0].get("value") is None
        ):
            # For strings, compare to empty string; for bools, compare to false
            left_type = infer_expr_type_from_ast(node_left)
            if left_type == STRING:
                cmp_op = "=="
                return ir.BinaryOp(
                    op=cmp_op,
                    left=left,
                    right=ir.StringLit(value="", typ=STRING),
                    typ=BOOL,
                    loc=loc_from_node(node),
                )
            if left_type == BOOL:
                return ir.UnaryOp(op="!", operand=left, typ=BOOL, loc=loc_from_node(node))
            # For sentinel ints, compare to the sentinel value
            sentinel = get_sentinel_value(
                node_left, type_ctx, current_class_name, sentinel_int_fields
            )
            if sentinel is not None:
                return ir.BinaryOp(
                    op="==",
                    left=left,
                    right=ir.IntLit(value=sentinel, typ=INT),
                    typ=BOOL,
                    loc=loc_from_node(node),
                )
            return ir.IsNil(expr=left, negated=False, typ=BOOL, loc=loc_from_node(node))
        if (
            is_type(ops[0], ["IsNot"])
            and is_type(comparators[0], ["Constant"])
            and comparators[0].get("value") is None
        ):
            # For strings, compare to non-empty string; for bools, just use the bool itself
            left_type = infer_expr_type_from_ast(node_left)
            if left_type == STRING:
                cmp_op = "!="
                return ir.BinaryOp(
                    op=cmp_op,
                    left=left,
                    right=ir.StringLit(value="", typ=STRING),
                    typ=BOOL,
                    loc=loc_from_node(node),
                )
            if left_type == BOOL:
                return left  # bool is its own truthy value
            # For sentinel ints, compare to the sentinel value
            sentinel = get_sentinel_value(
                node_left, type_ctx, current_class_name, sentinel_int_fields
            )
            if sentinel is not None:
                return ir.BinaryOp(
                    op="!=",
                    left=left,
                    right=ir.IntLit(value=sentinel, typ=INT),
                    typ=BOOL,
                    loc=loc_from_node(node),
                )
            return ir.IsNil(expr=left, negated=True, typ=BOOL, loc=loc_from_node(node))
        # Handle "x in (a, b, c)" -> "x == a || x == b || x == c"
        if is_type(ops[0], ["In", "NotIn"]) and is_type(comparators[0], ["Tuple"]):
            negated = is_type(ops[0], ["NotIn"])
            cmp_op = "!=" if negated else "=="
            join_op = "&&" if negated else "||"
            elts = comparators[0].get("elts", [])
            if elts:
                result = ir.BinaryOp(
                    op=cmp_op,
                    left=left,
                    right=lower_expr(elts[0]),
                    typ=BOOL,
                    loc=loc_from_node(node),
                )
                for elt in elts[1:]:
                    cmp = ir.BinaryOp(
                        op=cmp_op,
                        left=left,
                        right=lower_expr(elt),
                        typ=BOOL,
                        loc=loc_from_node(node),
                    )
                    result = ir.BinaryOp(
                        op=join_op, left=result, right=cmp, typ=BOOL, loc=loc_from_node(node)
                    )
                return result
            return ir.BoolLit(value=not negated, typ=BOOL, loc=loc_from_node(node))
        # Handle string vs pointer/optional string comparison: dereference the pointer side
        left_type = infer_expr_type_from_ast(node_left)
        right_type = infer_expr_type_from_ast(comparators[0])
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
    prev = lower_expr(node_left)
    for op, comp in zip(ops, comparators):
        curr = lower_expr(comp)
        cmp = ir.BinaryOp(
            op=cmpop_to_str(op), left=prev, right=curr, typ=BOOL, loc=loc_from_node(node)
        )
        if result is None:
            result = cmp
        else:
            result = ir.BinaryOp(op="&&", left=result, right=cmp, typ=BOOL, loc=loc_from_node(node))
        prev = curr
    return result or ir.BoolLit(value=True, typ=BOOL)


def lower_expr_BoolOp(
    node: ASTNode,
    lower_expr_as_bool: Callable[[ASTNode], "ir.Expr"],
) -> "ir.Expr":
    """Lower Python boolean operation to IR."""
    from .. import ir

    node_op = node.get("op")
    values = node.get("values", [])
    op = "&&" if is_type(node_op, ["And"]) else "||"
    result = lower_expr_as_bool(values[0])
    for val in values[1:]:
        right = lower_expr_as_bool(val)
        result = ir.BinaryOp(op=op, left=result, right=right, typ=BOOL, loc=loc_from_node(node))
    return result


def lower_expr_UnaryOp(
    node: ASTNode,
    lower_expr: Callable[[ASTNode], "ir.Expr"],
    lower_expr_as_bool: Callable[[ASTNode], "ir.Expr"],
) -> "ir.Expr":
    """Lower Python unary operation to IR."""
    from .. import ir

    node_op = node.get("op")
    # For 'not' operator, convert operand to boolean first
    if is_type(node_op, ["Not"]):
        operand = lower_expr_as_bool(node.get("operand"))
        return ir.UnaryOp(op="!", operand=operand, typ=BOOL, loc=loc_from_node(node))
    operand = lower_expr(node.get("operand"))
    op = unaryop_to_str(node_op)
    return ir.UnaryOp(op=op, operand=operand, typ=InterfaceRef("any"), loc=loc_from_node(node))


# ============================================================
# COLLECTION EXPRESSION LOWERING
# ============================================================


def lower_expr_List(
    node: ASTNode,
    lower_expr: Callable[[ASTNode], "ir.Expr"],
    infer_expr_type_from_ast: Callable[[ASTNode], "Type"],
    expected_type_ctx: "Type | None",
    expected_type: "Type | None" = None,
) -> "ir.Expr":
    """Lower Python list literal to IR slice literal."""
    from .. import ir

    elements = [lower_expr(e) for e in node.get("elts", [])]
    # Prefer expected type when available (bidirectional type inference)
    element_type: "Type" = InterfaceRef("any")
    if expected_type is not None and isinstance(expected_type, Slice):
        element_type = expected_type.element
    elif expected_type_ctx is not None and isinstance(expected_type_ctx, Slice):
        element_type = expected_type_ctx.element
    elif node.get("elts"):
        # Fall back to inferring from first element
        elts = node.get("elts", [])
        element_type = infer_expr_type_from_ast(elts[0])
    return ir.SliceLit(
        element_type=element_type,
        elements=elements,
        typ=Slice(element_type),
        loc=loc_from_node(node),
    )


def lower_list_call_with_expected_type(
    node: ASTNode,
    lower_expr: Callable[[ASTNode], "ir.Expr"],
    expected_type: "Type | None",
) -> "ir.Expr":
    """Handle list(x) call with expected type context for covariant copies."""
    from .. import ir

    args = node.get("args", [])
    arg = lower_expr(args[0])
    source_type = arg.typ
    # Check if we need covariant conversion: []*Derived -> []Interface
    if (
        expected_type is not None
        and isinstance(expected_type, Slice)
        and isinstance(source_type, Slice)
    ):
        source_elem = source_type.element
        target_elem = expected_type.element
        # Unwrap pointer for comparison
        if isinstance(source_elem, Pointer):
            source_elem_unwrapped = source_elem.target
        else:
            source_elem_unwrapped = source_elem
        # Need conversion if: source is *Struct, target is interface/Node
        if (
            source_elem != target_elem
            and isinstance(source_elem_unwrapped, StructRef)
            and isinstance(target_elem, (InterfaceRef, StructRef))
        ):
            return ir.SliceConvert(
                source=arg,
                target_element_type=target_elem,
                typ=expected_type,
                loc=loc_from_node(node),
            )
    # Fall through to normal copy
    return ir.MethodCall(
        obj=arg,
        method="copy",
        args=[],
        receiver_type=source_type if isinstance(source_type, Slice) else Slice(InterfaceRef("any")),
        typ=source_type if isinstance(source_type, Slice) else Slice(InterfaceRef("any")),
        loc=loc_from_node(node),
    )


def lower_expr_Dict(
    node: ASTNode,
    lower_expr: Callable[[ASTNode], "ir.Expr"],
    infer_expr_type_from_ast: Callable[[ASTNode], "Type"],
) -> "ir.Expr":
    """Lower Python dict literal to IR map literal."""
    from .. import ir

    entries = []
    keys = node.get("keys", [])
    values = node.get("values", [])
    for k, v in zip(keys, values):
        if k is not None:
            entries.append((lower_expr(k), lower_expr(v)))
    # Infer key and value types from first entry if available
    key_type: "Type" = STRING
    value_type: "Type" = InterfaceRef("any")
    if values and values[0]:
        first_val = values[0]
        value_type = infer_expr_type_from_ast(first_val)
    return ir.MapLit(
        key_type=key_type,
        value_type=value_type,
        entries=entries,
        typ=Map(key_type, value_type),
        loc=loc_from_node(node),
    )


def lower_expr_JoinedStr(
    node: ASTNode,
    lower_expr: Callable[[ASTNode], "ir.Expr"],
) -> "ir.Expr":
    """Lower Python f-string to StringFormat IR node."""
    template_parts: list[str] = []
    args: list["ir.Expr"] = []
    for part in node.get("values", []):
        if is_type(part, ["Constant"]):
            # Escape % signs in literal parts for fmt.Sprintf
            template_parts.append(str(part.get("value", "")).replace("%", "%%"))
        elif is_type(part, ["FormattedValue"]):
            template_parts.append("%v")
            args.append(lower_expr(part.get("value")))
    template = "".join(template_parts)
    return StringFormat(template=template, args=args, typ=STRING, loc=loc_from_node(node))


def lower_expr_Tuple(
    node: ASTNode,
    lower_expr: Callable[[ASTNode], "ir.Expr"],
) -> "ir.Expr":
    """Lower Python tuple literal to TupleLit IR node."""
    from .. import ir

    elements = [lower_expr(e) for e in node.get("elts", [])]
    element_types = tuple(e.typ for e in elements)
    return ir.TupleLit(
        elements=elements, typ=Tuple(elements=element_types), loc=loc_from_node(node)
    )


def lower_expr_Set(
    node: ASTNode,
    lower_expr: Callable[[ASTNode], "ir.Expr"],
) -> "ir.Expr":
    """Lower Python set literal to SetLit IR node."""
    from .. import ir

    elements = [lower_expr(e) for e in node.get("elts", [])]
    # Infer element type from first element
    elem_type = getattr(elements[0], "typ", STRING) if elements else STRING
    return ir.SetLit(
        element_type=elem_type, elements=elements, typ=Set(elem_type), loc=loc_from_node(node)
    )


# ============================================================
# EXPRESSION DISPATCHER
# ============================================================


def lower_expr_as_bool(
    node: ASTNode,
    lower_expr: Callable[[ASTNode], "ir.Expr"],
    lower_expr_as_bool_self: Callable[[ASTNode], "ir.Expr"],
    infer_expr_type_from_ast: Callable[[ASTNode], "Type"],
    is_isinstance_call: Callable[[ASTNode], tuple[str, str] | None],
    resolve_type_name: Callable[[str], "Type"],
    type_ctx: "TypeContext",
    symbols: "SymbolTable",
) -> "ir.Expr":
    """Lower expression used in boolean context, adding truthy checks as needed."""
    from .. import ir

    # Already boolean expressions - lower directly
    if is_type(node, ["Compare"]):
        return lower_expr(node)
    if is_type(node, ["BoolOp"]):
        # For BoolOp, recursively lower operands as booleans
        node_op = node.get("op")
        op = "&&" if is_type(node_op, ["And"]) else "||"
        values = node.get("values", [])
        result = lower_expr_as_bool_self(values[0])
        # Track isinstance narrowing for AND chains
        narrowed_var: str | None = None
        narrowed_old_type: Type | None = None
        was_already_narrowed = False
        if is_type(node_op, ["And"]):
            isinstance_check = is_isinstance_call(values[0])
            if isinstance_check:
                var_name, type_name = isinstance_check
                narrowed_var = var_name
                narrowed_old_type = type_ctx.var_types.get(var_name)
                was_already_narrowed = var_name in type_ctx.narrowed_vars
                type_ctx.var_types[var_name] = resolve_type_name(type_name)
                type_ctx.narrowed_vars.add(var_name)
        for val in values[1:]:
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
    if is_type(node, ["UnaryOp"]) and is_type(node.get("op"), ["Not"]):
        operand = lower_expr_as_bool_self(node.get("operand"))
        return ir.UnaryOp(op="!", operand=operand, typ=BOOL, loc=loc_from_node(node))
    if is_type(node, ["Constant"]):
        if isinstance(node.get("value"), bool):
            return lower_expr(node)
    if is_type(node, ["Name"]) and node.get("id") in ("True", "False"):
        return lower_expr(node)
    if is_type(node, ["Call"]):
        # Calls that return bool are fine
        func = node.get("func")
        if is_type(func, ["Attribute"]):
            # Methods like .startswith(), .endswith(), .isdigit() return bool
            if func.get("attr") in (
                "startswith",
                "endswith",
                "isdigit",
                "isalpha",
                "isalnum",
                "isspace",
            ):
                return lower_expr(node)
            # Check if the method returns bool by looking up its return type
            method_return_type = infer_expr_type_from_ast(node)
            if method_return_type == BOOL:
                return lower_expr(node)
        elif is_type(func, ["Name"]):
            if func.get("id") in ("isinstance", "hasattr", "callable", "bool"):
                return lower_expr(node)
            # Check if the function returns bool by looking up its return type
            func_name = func.get("id")
            if func_name in symbols.functions:
                func_info = symbols.functions[func_name]
                if func_info.return_type == BOOL:
                    return lower_expr(node)
    # Non-boolean expression - needs truthy check
    expr = lower_expr(node)
    # Use the IR expression's type if available, otherwise infer from AST
    expr_type = (
        expr.typ
        if hasattr(expr, "typ") and expr.typ != InterfaceRef("any")
        else infer_expr_type_from_ast(node)
    )
    # Bool expressions don't need nil check
    if expr_type == BOOL:
        return expr
    # String truthy check: s != ""
    if expr_type == STRING:
        return ir.BinaryOp(
            op="!=",
            left=expr,
            right=ir.StringLit(value="", typ=STRING),
            typ=BOOL,
            loc=loc_from_node(node),
        )
    # Int truthy check: n != 0
    if expr_type == INT:
        return ir.BinaryOp(
            op="!=", left=expr, right=ir.IntLit(value=0, typ=INT), typ=BOOL, loc=loc_from_node(node)
        )
    # Slice/Map/Set truthy check: len(x) > 0
    if isinstance(expr_type, (Slice, Map, Set)):
        return ir.BinaryOp(
            op=">",
            left=ir.Len(expr=expr, typ=INT, loc=loc_from_node(node)),
            right=ir.IntLit(value=0, typ=INT),
            typ=BOOL,
            loc=loc_from_node(node),
        )
    # Optional(Slice) truthy check: len(x) > 0 (nil slice has len 0)
    if isinstance(expr_type, Optional) and isinstance(expr_type.inner, (Slice, Map, Set)):
        return ir.BinaryOp(
            op=">",
            left=ir.Len(expr=expr, typ=INT, loc=loc_from_node(node)),
            right=ir.IntLit(value=0, typ=INT),
            typ=BOOL,
            loc=loc_from_node(node),
        )
    # Interface truthy check: x != nil
    if isinstance(expr_type, InterfaceRef):
        return ir.IsNil(expr=expr, negated=True, typ=BOOL, loc=loc_from_node(node))
    # Pointer/Optional truthy check: x != nil
    if isinstance(expr_type, (Pointer, Optional)):
        return ir.IsNil(expr=expr, negated=True, typ=BOOL, loc=loc_from_node(node))
    # Check name that might be pointer or interface - use nil check
    if is_type(node, ["Name"]):
        # If type is interface, use nil check (interfaces are nilable)
        if isinstance(expr_type, InterfaceRef):
            return ir.IsNil(expr=expr, negated=True, typ=BOOL, loc=loc_from_node(node))
        # If type is a pointer, use nil check
        if isinstance(expr_type, (Pointer, Optional)):
            return ir.IsNil(expr=expr, negated=True, typ=BOOL, loc=loc_from_node(node))
        # Otherwise just return the expression (shouldn't reach here for valid types)
        return expr
    # For other expressions, assume it's a pointer check
    return ir.IsNil(expr=expr, negated=True, typ=BOOL, loc=loc_from_node(node))


def lower_expr_IfExp(
    node: ASTNode,
    lower_expr: Callable[[ASTNode], "ir.Expr"],
    lower_expr_as_bool: Callable[[ASTNode], "ir.Expr"],
    extract_attr_kind_check: Callable[[ASTNode], tuple[str, str] | None],
    type_ctx: "TypeContext",
) -> "ir.Expr":
    """Lower Python ternary (if-else expression) to Ternary IR node."""
    from .. import ir

    cond = lower_expr_as_bool(node.get("test"))
    # Check for attribute path kind narrowing in the condition
    # e.g., node.body.kind == "brace-group" narrows node.body to BraceGroup
    attr_kind_check = extract_attr_kind_check(node.get("test"))
    if attr_kind_check:
        attr_path, struct_name = attr_kind_check
        type_ctx.narrowed_attr_paths[attr_path] = struct_name
    then_expr = lower_expr(node.get("body"))
    # Clean up the narrowing after processing then branch
    if attr_kind_check:
        type_ctx.narrowed_attr_paths.pop(attr_kind_check[0])
    else_expr = lower_expr(node.get("orelse"))
    # Use type from lowered expressions (prefer then branch, fall back to else)
    result_type = getattr(then_expr, "typ", None)
    if result_type is None or result_type == InterfaceRef("any"):
        result_type = getattr(else_expr, "typ", None)
    if result_type is None:
        result_type = InterfaceRef("any")
    return ir.Ternary(
        cond=cond,
        then_expr=then_expr,
        else_expr=else_expr,
        typ=result_type,
        loc=loc_from_node(node),
    )


# ============================================================
# SIMPLE STATEMENT LOWERING
# ============================================================


def is_super_init_call(node: ASTNode) -> bool:
    """Check if expression is super().__init__(...)."""
    if not is_type(node, ["Call"]):
        return False
    func = node.get("func")
    if not is_type(func, ["Attribute"]):
        return False
    if func.get("attr") != "__init__":
        return False
    func_value = func.get("value")
    if not is_type(func_value, ["Call"]):
        return False
    func_value_func = func_value.get("func")
    if not is_type(func_value_func, ["Name"]):
        return False
    return func_value_func.get("id") == "super"


def lower_stmt_Expr(
    node: ASTNode,
    lower_expr: Callable[[ASTNode], "ir.Expr"],
) -> "ir.Stmt":
    """Lower expression statement."""
    from .. import ir

    # Skip docstrings
    value = node.get("value")
    if is_type(value, ["Constant"]) and isinstance(value.get("value"), str):
        return ir.ExprStmt(expr=ir.Var(name="_skip_docstring", typ=VOID))
    # Skip super().__init__() calls - handled by Go embedding
    if is_super_init_call(value):
        return ir.ExprStmt(expr=ir.Var(name="_skip_super_init", typ=VOID))
    return ir.ExprStmt(expr=lower_expr(value), loc=loc_from_node(node))


def lower_stmt_AugAssign(
    node: ASTNode,
    lower_lvalue: Callable[[ASTNode], "ir.LValue"],
    lower_expr: Callable[[ASTNode], "ir.Expr"],
) -> "ir.Stmt":
    """Lower augmented assignment (+=, -=, etc.)."""
    from .. import ir

    lval = lower_lvalue(node.get("target"))
    value = lower_expr(node.get("value"))
    op = binop_to_str(node.get("op"))
    return ir.OpAssign(target=lval, op=op, value=value, loc=loc_from_node(node))


def lower_stmt_While(
    node: ASTNode,
    lower_expr_as_bool: Callable[[ASTNode], "ir.Expr"],
    lower_stmts: Callable[[list[ASTNode]], list["ir.Stmt"]],
) -> "ir.Stmt":
    """Lower while loop."""
    from .. import ir

    cond = lower_expr_as_bool(node.get("test"))
    body = lower_stmts(node.get("body", []))
    return ir.While(cond=cond, body=body, loc=loc_from_node(node))


def lower_stmt_Break(node: ASTNode) -> "ir.Stmt":
    """Lower break statement."""
    from .. import ir

    return ir.Break(loc=loc_from_node(node))


def lower_stmt_Continue(node: ASTNode) -> "ir.Stmt":
    """Lower continue statement."""
    from .. import ir

    return ir.Continue(loc=loc_from_node(node))


def lower_stmt_Pass(node: ASTNode) -> "ir.Stmt":
    """Lower pass statement."""
    from .. import ir

    return ir.ExprStmt(expr=ir.Var(name="_pass", typ=VOID), loc=loc_from_node(node))


def lower_stmt_FunctionDef(node: ASTNode) -> "ir.Stmt":
    """Lower local function definition (placeholder)."""
    from .. import ir

    return ir.ExprStmt(expr=ir.Var(name=f"_local_func_{node.get('name')}", typ=VOID))


def lower_stmt_Return(
    node: ASTNode,
    ctx: "FrontendContext",
    lower_expr: Callable[[ASTNode], "ir.Expr"],
) -> "ir.Stmt":
    """Lower return statement."""
    from .. import ir

    node_value = node.get("value")
    value = lower_expr(node_value) if node_value else None
    # Apply type coercion based on function return type
    return_type = ctx.type_ctx.return_type
    if value and return_type:
        from_type = type_inference.synthesize_type(
            value, ctx.type_ctx, ctx.current_func_info, ctx.symbols, ctx.node_types
        )
        value = type_inference.coerce(
            value,
            from_type,
            return_type,
            ctx.type_ctx,
            ctx.current_func_info,
            ctx.symbols,
            ctx.node_types,
        )
    return ir.Return(value=value, loc=loc_from_node(node))


# ============================================================
# EXCEPTION STATEMENT LOWERING
# ============================================================


def lower_stmt_Raise(
    node: ASTNode,
    lower_expr: Callable[[ASTNode], "ir.Expr"],
    current_catch_var: str | None,
) -> "ir.Stmt":
    """Lower raise statement."""
    from .. import ir

    exc = node.get("exc")
    if exc:
        # Check if raising the catch variable (re-raise pattern)
        if is_type(exc, ["Name"]) and exc.get("id") == current_catch_var:
            return ir.Raise(
                error_type="Error",
                message=ir.StringLit(value="", typ=STRING),
                pos=ir.IntLit(value=0, typ=INT),
                reraise_var=current_catch_var,
                loc=loc_from_node(node),
            )
        # Extract error type and message from exception
        exc_func = exc.get("func")
        if is_type(exc, ["Call"]) and is_type(exc_func, ["Name"]):
            error_type = exc_func.get("id")
            exc_args = exc.get("args", [])
            msg = (
                lower_expr(exc_args[0])
                if exc_args
                else ir.StringLit(value="", typ=STRING)
            )
            # Check for pos kwarg
            pos = ir.IntLit(value=0, typ=INT)
            if len(exc_args) > 1:
                pos = lower_expr(exc_args[1])
            else:
                # Check kwargs for pos
                for kw in exc.get("keywords", []):
                    if kw.get("arg") == "pos":
                        pos = lower_expr(kw.get("value"))
                        break
            return ir.Raise(error_type=error_type, message=msg, pos=pos, loc=loc_from_node(node))
    return ir.Raise(
        error_type="Error",
        message=ir.StringLit(value="", typ=STRING),
        pos=ir.IntLit(value=0, typ=INT),
        loc=loc_from_node(node),
    )


# ============================================================
# COMPLEX EXPRESSION LOWERING (requires full context)
# ============================================================


def lower_expr_Call(
    node: ASTNode,
    ctx: "FrontendContext",
    dispatch: "LoweringDispatch",
) -> "ir.Expr":
    """Lower a Python function/method call to IR.

    Handles:
    - Method calls (encode, decode, append, pop, and general methods)
    - Free function calls (len, bool, list, int, str, ord, chr, max, min, isinstance)
    - Constructor calls (struct construction)
    - Regular function calls
    """
    from .. import ir

    node_args = node.get("args", [])
    args = [dispatch.lower_expr(a) for a in node_args]
    # Method call
    func = node.get("func")
    if is_type(func, ["Attribute"]):
        method = func.get("attr")
        func_value = func.get("value")
        # Handle chr(n).encode("utf-8") -> []byte(string(rune(n)))
        if method == "encode" and is_type(func_value, ["Call"]):
            inner_call = func_value
            inner_func = inner_call.get("func")
            if is_type(inner_func, ["Name"]) and inner_func.get("id") == "chr":
                # chr(n).encode("utf-8") -> cast to []byte
                chr_arg = dispatch.lower_expr(inner_call.get("args", [])[0])
                rune_cast = ir.Cast(expr=chr_arg, to_type=RUNE, typ=RUNE, loc=loc_from_node(node))
                str_cast = ir.Cast(
                    expr=rune_cast, to_type=STRING, typ=STRING, loc=loc_from_node(node)
                )
                return ir.Cast(
                    expr=str_cast, to_type=Slice(BYTE), typ=Slice(BYTE), loc=loc_from_node(node)
                )
        # Handle str.encode("utf-8") -> []byte(str)
        if method == "encode":
            obj = dispatch.lower_expr(func_value)
            return ir.Cast(expr=obj, to_type=Slice(BYTE), typ=Slice(BYTE), loc=loc_from_node(node))
        # Handle bytes.decode("utf-8") -> string(bytes)
        if method == "decode":
            obj = dispatch.lower_expr(func_value)
            return ir.Cast(expr=obj, to_type=STRING, typ=STRING, loc=loc_from_node(node))
        obj = dispatch.lower_expr(func_value)
        # Handle Python list methods that need special Go treatment
        if method == "append" and args:
            # Look up actual type of the object (might be pointer to slice for params)
            obj_type = dispatch.infer_expr_type_from_ast(func_value)
            # Check if appending to a byte slice - need to cast int to byte
            elem_type = None
            if isinstance(obj_type, Slice):
                elem_type = obj_type.element
            elif isinstance(obj_type, Pointer) and isinstance(obj_type.target, Slice):
                elem_type = obj_type.target.element
            # Coerce int to byte for byte slices (Python bytearray.append accepts int)
            coerced_args = args
            if elem_type == BYTE and len(args) == 1:
                arg = args[0]
                # Check if arg is int-typed (via AST inference or lowered type)
                arg_ast_type = dispatch.infer_expr_type_from_ast(node_args[0])
                if arg_ast_type == INT or (hasattr(arg, "typ") and arg.typ == INT):
                    coerced_args = [ir.Cast(expr=arg, to_type=BYTE, typ=BYTE, loc=arg.loc)]
            # list.append(x) -> append(list, x) in Go (handled via MethodCall for now)
            return ir.MethodCall(
                obj=obj,
                method="append",
                args=coerced_args,
                receiver_type=obj_type
                if obj_type != InterfaceRef("any")
                else Slice(InterfaceRef("any")),
                typ=VOID,
                loc=loc_from_node(node),
            )
        # Infer receiver type for proper method lookup
        obj_type = dispatch.infer_expr_type_from_ast(func_value)
        if method == "pop" and not args and isinstance(obj_type, Slice):
            # list.pop() -> return last element and shrink slice (only for slices)
            return ir.MethodCall(
                obj=obj,
                method="pop",
                args=[],
                receiver_type=obj_type,
                typ=obj_type.element,
                loc=loc_from_node(node),
            )
        # Check if calling a method on a Node-typed expression that needs type assertion
        # Do this early so we can use the asserted type for default arg lookup
        if type_inference.is_node_interface_type(obj_type) and method in NODE_METHOD_TYPES:
            struct_name = NODE_METHOD_TYPES[method]
            asserted_type = Pointer(StructRef(struct_name))
            obj = ir.TypeAssert(
                expr=obj,
                asserted=asserted_type,
                safe=True,
                typ=asserted_type,
                loc=loc_from_node(func_value),
            )
            # Use asserted type for subsequent lookups
            obj_type = asserted_type
        # Merge keyword arguments into args at proper positions
        args = dispatch.merge_keyword_args(obj_type, method, args, node)
        # Fill in default values for any remaining missing parameters
        args = dispatch.fill_default_args(obj_type, method, args)
        # Coerce sentinel ints to pointers for *int params
        args = dispatch.coerce_sentinel_to_ptr(obj_type, method, args, node_args)
        # Add & for pointer-to-slice params
        args = dispatch.add_address_of_for_ptr_params(obj_type, method, args, node_args)
        # Dereference * for slice params
        args = dispatch.deref_for_slice_params(obj_type, method, args, node_args)
        # Infer return type
        ret_type = type_inference.synthesize_method_return_type(
            obj_type, method, ctx.symbols, ctx.node_types
        )
        return ir.MethodCall(
            obj=obj,
            method=method,
            args=args,
            receiver_type=obj_type,
            typ=ret_type,
            loc=loc_from_node(node),
        )
    # Free function call
    if is_type(func, ["Name"]):
        func_name = func.get("id")
        # Check for len()
        if func_name == "len" and args:
            arg = args[0]
            arg_type = dispatch.infer_expr_type_from_ast(node_args[0])
            # Dereference Pointer(Slice) or Optional(Slice) for len()
            inner_slice = get_inner_slice(arg_type)
            if inner_slice is not None:
                arg = ir.UnaryOp(op="*", operand=arg, typ=inner_slice, loc=arg.loc)
            return ir.Len(expr=arg, typ=INT, loc=loc_from_node(node))
        # Check for bool() - convert to comparison
        if func_name == "bool" and args:
            # bool(x) -> x != 0 for ints, x != "" for strings, x != nil for pointers
            arg_type = dispatch.infer_expr_type_from_ast(node_args[0])
            if arg_type == INT:
                return ir.BinaryOp(
                    op="!=",
                    left=args[0],
                    right=ir.IntLit(value=0, typ=INT),
                    typ=BOOL,
                    loc=loc_from_node(node),
                )
            if arg_type == STRING:
                return ir.BinaryOp(
                    op="!=",
                    left=args[0],
                    right=ir.StringLit(value="", typ=STRING),
                    typ=BOOL,
                    loc=loc_from_node(node),
                )
            # Default: assume pointer/optional, check != nil
            return ir.IsNil(expr=args[0], negated=True, typ=BOOL, loc=loc_from_node(node))
        # Check for list() copy
        if func_name == "list" and args:
            # list(x) is a copy operation - preserve element type from source
            source_type = getattr(args[0], "typ", None)
            if isinstance(source_type, Slice):
                result_type = source_type
            else:
                result_type = Slice(InterfaceRef("any"))
            return ir.MethodCall(
                obj=args[0],
                method="copy",
                args=[],
                receiver_type=result_type,
                typ=result_type,
                loc=loc_from_node(node),
            )
        # Check for bytearray() constructor
        if func_name == "bytearray" and not args:
            return ir.MakeSlice(
                element_type=BYTE,
                length=None,
                capacity=None,
                typ=Slice(BYTE),
                loc=loc_from_node(node),
            )
        # Check for int(s, base) conversion
        if func_name == "int" and len(args) == 2:
            return ir.Call(func="_parseInt", args=args, typ=INT, loc=loc_from_node(node))
        # Check for int(s) - string to int conversion
        if func_name == "int" and len(args) == 1:
            arg_type = dispatch.infer_expr_type_from_ast(node_args[0])
            if arg_type == STRING:
                # String to int: use _parseInt with base 10
                return ir.Call(
                    func="_parseInt",
                    args=[args[0], ir.IntLit(value=10, typ=INT, loc=loc_from_node(node))],
                    typ=INT,
                    loc=loc_from_node(node),
                )
            else:
                # Already numeric: just cast to int
                return ir.Cast(expr=args[0], to_type=INT, typ=INT, loc=loc_from_node(node))
        # Check for str(n) - int to string conversion
        if func_name == "str" and len(args) == 1:
            arg_type = dispatch.infer_expr_type_from_ast(node_args[0])
            if arg_type == INT:
                return ir.Call(func="_intToStr", args=args, typ=STRING, loc=loc_from_node(node))
            # Handle *int or Optional[int] - dereference first
            if isinstance(arg_type, (Optional, Pointer)):
                inner = arg_type.inner if isinstance(arg_type, Optional) else arg_type.target
                if inner == INT:
                    deref_arg = ir.UnaryOp(
                        op="*", operand=args[0], typ=INT, loc=loc_from_node(node)
                    )
                    return ir.Call(
                        func="_intToStr", args=[deref_arg], typ=STRING, loc=loc_from_node(node)
                    )
            # Already string or convert via fmt
            return ir.Cast(expr=args[0], to_type=STRING, typ=STRING, loc=loc_from_node(node))
        # Check for ord(c) -> int(c[0]) (get Unicode code point)
        if func_name == "ord" and len(args) == 1:
            # ord(c) -> cast the first character to int
            # In Go: int(c[0]) for strings, int(c) for bytes/runes
            arg_type = dispatch.infer_expr_type_from_ast(node_args[0])
            if arg_type in (BYTE, RUNE):
                # Already a byte/rune: just cast to int
                return ir.Cast(expr=args[0], to_type=INT, typ=INT, loc=loc_from_node(node))
            else:
                # String or unknown: index to get first byte, then cast to int
                indexed = ir.Index(obj=args[0], index=ir.IntLit(value=0, typ=INT), typ=BYTE)
                return ir.Cast(expr=indexed, to_type=INT, typ=INT, loc=loc_from_node(node))
        # Check for chr(n) -> string(rune(n))
        if func_name == "chr" and len(args) == 1:
            rune_cast = ir.Cast(expr=args[0], to_type=RUNE, typ=RUNE, loc=loc_from_node(node))
            return ir.Cast(expr=rune_cast, to_type=STRING, typ=STRING, loc=loc_from_node(node))
        # Check for max(a, b) -> a > b ? a : b
        if func_name == "max" and len(args) == 2:
            cond = ir.BinaryOp(
                op=">", left=args[0], right=args[1], typ=BOOL, loc=loc_from_node(node)
            )
            return ir.Ternary(
                cond=cond, then_expr=args[0], else_expr=args[1], typ=INT, loc=loc_from_node(node)
            )
        # Check for min(a, b) -> a < b ? a : b
        if func_name == "min" and len(args) == 2:
            cond = ir.BinaryOp(
                op="<", left=args[0], right=args[1], typ=BOOL, loc=loc_from_node(node)
            )
            return ir.Ternary(
                cond=cond, then_expr=args[0], else_expr=args[1], typ=INT, loc=loc_from_node(node)
            )
        # Check for isinstance(x, Type) -> IsType expression
        if func_name == "isinstance" and len(node_args) == 2:
            expr = dispatch.lower_expr(node_args[0])
            if is_type(node_args[1], ["Name"]):
                type_name = node_args[1].get("id")
                tested_type = resolve_type_name(type_name, type_inference.TYPE_MAP, ctx.symbols)
                return ir.IsType(
                    expr=expr, tested_type=tested_type, typ=BOOL, loc=loc_from_node(node)
                )
        # Check for constructor calls (class names)
        if func_name in ctx.symbols.structs:
            struct_info = ctx.symbols.structs[func_name]
            # If struct needs constructor, call NewXxx instead of StructLit
            if struct_info.needs_constructor:
                # Build param name -> index map for keyword arg handling
                param_indices: dict[str, int] = {}
                for i, param_name in enumerate(struct_info.init_params):
                    param_indices[param_name] = i
                # Initialize args list with Nones
                n_params = len(struct_info.init_params)
                ctor_args: list[ir.Expr | None] = [None] * n_params
                # First, place positional args
                for i, arg_ast in enumerate(node_args):
                    if i < n_params:
                        param_name = struct_info.init_params[i]
                        field_name = struct_info.param_to_field.get(param_name, param_name)
                        field_info = struct_info.fields.get(field_name)
                        expected_type = field_info.typ if field_info else None
                        if isinstance(expected_type, Pointer) and isinstance(
                            expected_type.target, Slice
                        ):
                            expected_type = expected_type.target
                        if is_type(arg_ast, ["List"]):
                            ctor_args[i] = dispatch.lower_expr_List(arg_ast, expected_type)
                        elif (
                            is_type(arg_ast, ["Call"])
                            and is_type(arg_ast.get("func"), ["Name"])
                            and arg_ast.get("func").get("id") == "list"
                            and arg_ast.get("args")
                        ):
                            ctor_args[i] = lower_list_call_with_expected_type(
                                arg_ast, dispatch.lower_expr, expected_type
                            )
                        else:
                            ctor_args[i] = args[i]
                # Then, place keyword args in their proper positions
                for kw in node.get("keywords", []):
                    kw_arg = kw.get("arg")
                    if kw_arg and kw_arg in param_indices:
                        idx = param_indices[kw_arg]
                        param_name = struct_info.init_params[idx]
                        field_name = struct_info.param_to_field.get(param_name, param_name)
                        field_info = struct_info.fields.get(field_name)
                        expected_type = field_info.typ if field_info else None
                        if isinstance(expected_type, Pointer) and isinstance(
                            expected_type.target, Slice
                        ):
                            expected_type = expected_type.target
                        kw_value = kw.get("value")
                        if is_type(kw_value, ["List"]):
                            ctor_args[idx] = dispatch.lower_expr_List(kw_value, expected_type)
                        elif (
                            is_type(kw_value, ["Call"])
                            and is_type(kw_value.get("func"), ["Name"])
                            and kw_value.get("func").get("id") == "list"
                            and kw_value.get("args")
                        ):
                            ctor_args[idx] = lower_list_call_with_expected_type(
                                kw_value, dispatch.lower_expr, expected_type
                            )
                        else:
                            ctor_args[idx] = dispatch.lower_expr(kw_value)
                # Fill in default values for any remaining None slots
                for i in range(n_params):
                    if ctor_args[i] is None:
                        param_name = struct_info.init_params[i]
                        field_name = struct_info.param_to_field.get(param_name, param_name)
                        field_info = struct_info.fields.get(field_name)
                        field_type = field_info.typ if field_info else InterfaceRef("any")
                        ctor_args[i] = make_default_value(field_type, loc_from_node(node))
                return ir.Call(
                    func=f"New{func_name}",
                    args=ctor_args,  # type: ignore
                    typ=Pointer(StructRef(func_name)),
                    loc=loc_from_node(node),
                )
            # Simple struct: emit StructLit with fields mapped from positional and keyword args
            fields: dict[str, ir.Expr] = {}
            for i, arg_ast in enumerate(node_args):
                if i < len(struct_info.init_params):
                    param_name = struct_info.init_params[i]
                    # Map param name to actual field name (e.g., in_process_sub -> _in_process_sub)
                    field_name = struct_info.param_to_field.get(param_name, param_name)
                    # Look up field type for expected type context
                    field_info = struct_info.fields.get(field_name)
                    expected_type = field_info.typ if field_info else None
                    # Handle pointer-wrapped slice types
                    if isinstance(expected_type, Pointer) and isinstance(
                        expected_type.target, Slice
                    ):
                        expected_type = expected_type.target
                    # Re-lower list args with expected type context
                    if is_type(arg_ast, ["List"]):
                        fields[field_name] = dispatch.lower_expr_List(arg_ast, expected_type)
                    else:
                        fields[field_name] = args[i]
            # Handle keyword arguments for struct literals
            node_keywords = node.get("keywords", [])
            if node_keywords:
                for kw in node_keywords:
                    kw_arg = kw.get("arg")
                    if kw_arg:
                        # Map param name to field name (handle snake_case to PascalCase)
                        field_name = struct_info.param_to_field.get(kw_arg, kw_arg)
                        field_info = struct_info.fields.get(field_name)
                        expected_type = field_info.typ if field_info else None
                        if isinstance(expected_type, Pointer) and isinstance(
                            expected_type.target, Slice
                        ):
                            expected_type = expected_type.target
                        kw_value = kw.get("value")
                        if is_type(kw_value, ["List"]):
                            fields[field_name] = dispatch.lower_expr_List(kw_value, expected_type)
                        elif (
                            is_type(kw_value, ["Call"])
                            and is_type(kw_value.get("func"), ["Name"])
                            and kw_value.get("func").get("id") == "list"
                            and kw_value.get("args")
                        ):
                            fields[field_name] = lower_list_call_with_expected_type(
                                kw_value, dispatch.lower_expr, expected_type
                            )
                        else:
                            fields[field_name] = dispatch.lower_expr(kw_value)
            # Add constant field initializations from __init__
            for const_name, const_value in struct_info.const_fields.items():
                if const_name not in fields:
                    fields[const_name] = ir.StringLit(
                        value=const_value, typ=STRING, loc=loc_from_node(node)
                    )
            return ir.StructLit(
                struct_name=func_name,
                fields=fields,
                typ=Pointer(StructRef(func_name)),
                loc=loc_from_node(node),
            )
        # Look up function return type and fill default args from symbol table
        ret_type: "Type" = InterfaceRef("any")
        if func_name in ctx.symbols.functions:
            func_info = ctx.symbols.functions[func_name]
            ret_type = func_info.return_type
            # Merge keyword arguments into positional args
            args = dispatch.merge_keyword_args_for_func(func_info, args, node)
            # Fill in default arguments
            args = fill_default_args_for_func(func_info, args)
            # Dereference * for slice params
            args = dispatch.deref_for_func_slice_params(func_name, args, node_args)
            # Add type assertions for interface{} -> Node coercion
            args = coerce_args_to_node(func_info, args)
        return ir.Call(func=func_name, args=args, typ=ret_type, loc=loc_from_node(node))
    return ir.Var(name="TODO_Call", typ=InterfaceRef("any"))


def lower_stmt_Assign(
    node: ASTNode,
    ctx: "FrontendContext",
    dispatch: "LoweringDispatch",
) -> "ir.Stmt":
    """Lower a Python assignment statement to IR.

    Handles:
    - Simple assignments: x = value
    - Tuple-returning functions: x = func() -> x0, x1 = func()
    - List pop: var = list.pop() -> multiple statements
    - Tuple unpacking: a, b = func(), a, b = x, y, etc.
    - Sentinel ints: var = None -> var = -1
    - Multiple targets: a = b = value
    """
    from .. import ir
    from ..ir import Tuple as TupleType

    type_ctx = ctx.type_ctx
    node_targets = node.get("targets", [])
    node_value = node.get("value")
    # Check VAR_TYPE_OVERRIDES to set expected type before lowering
    if len(node_targets) == 1:
        target = node_targets[0]
        if is_type(target, ["Name"]):
            func_name = ctx.current_func_info.name if ctx.current_func_info else ""
            override_key = (func_name, target.get("id"))
            if override_key in VAR_TYPE_OVERRIDES:
                type_ctx.expected = VAR_TYPE_OVERRIDES[override_key]
        # For field assignments (self.field = value), use field type as expected
        elif is_type(target, ["Attribute"]) and is_type(target.get("value"), ["Name"]):
            target_value = target.get("value")
            if target_value.get("id") == "self" and ctx.current_class_name:
                struct_info = ctx.symbols.structs.get(ctx.current_class_name)
                if struct_info:
                    field_info = struct_info.fields.get(target.get("attr"))
                    if field_info:
                        type_ctx.expected = field_info.typ
    value = dispatch.lower_expr(node_value)
    type_ctx.expected = None  # Reset expected type
    if len(node_targets) == 1:
        target = node_targets[0]
        # Handle single var = tuple-returning func: x = func() -> x0, x1 := func()
        if is_type(target, ["Name"]) and is_type(node_value, ["Call"]):
            ret_type = type_inference.infer_call_return_type(
                node_value,
                ctx.symbols,
                ctx.type_ctx,
                ctx.current_func_info,
                ctx.current_class_name,
                ctx.node_types,
            )
            if isinstance(ret_type, TupleType) and len(ret_type.elements) > 1:
                # Generate synthetic variable names and track for later index access
                base_name = target.get("id")
                synthetic_names = [f"{base_name}{i}" for i in range(len(ret_type.elements))]
                type_ctx.tuple_vars[base_name] = synthetic_names
                # Also track types of synthetic vars
                for i, syn_name in enumerate(synthetic_names):
                    type_ctx.var_types[syn_name] = ret_type.elements[i]
                targets = []
                for i in range(len(ret_type.elements)):
                    targets.append(ir.VarLV(name=f"{base_name}{i}", loc=loc_from_node(target)))
                return ir.TupleAssign(targets=targets, value=value, loc=loc_from_node(node))
        # Handle simple pop: var = list.pop() -> var = list[len(list)-1]; list = list[:len(list)-1]
        if is_type(target, ["Name"]) and is_type(node_value, ["Call"]):
            node_value_func = node_value.get("func")
            if (
                is_type(node_value_func, ["Attribute"])
                and node_value_func.get("attr") == "pop"
                and not node_value.get("args")
            ):
                func_value = node_value_func.get("value")
                obj = dispatch.lower_expr(func_value)
                obj_type = dispatch.infer_expr_type_from_ast(func_value)
                if isinstance(obj_type, Slice):
                    obj_lval = dispatch.lower_lvalue(func_value)
                    lval = dispatch.lower_lvalue(target)
                    elem_type = obj_type.element
                    len_minus_1 = ir.BinaryOp(
                        op="-",
                        left=ir.Len(expr=obj, typ=INT),
                        right=ir.IntLit(value=1, typ=INT),
                        typ=INT,
                    )
                    block = ir.Block(
                        body=[
                            ir.Assign(
                                target=lval,
                                value=ir.Index(obj=obj, index=len_minus_1, typ=elem_type),
                            ),
                            ir.Assign(
                                target=obj_lval,
                                value=ir.SliceExpr(obj=obj, high=len_minus_1, typ=obj_type),
                            ),
                        ],
                        loc=loc_from_node(node),
                    )
                    block.no_scope = True  # Emit without braces
                    return block
        # Handle tuple unpacking: a, b = func() where func returns tuple
        target_elts = target.get("elts", [])
        if is_type(target, ["Tuple"]) and len(target_elts) == 2:
            # Special case for popping from stack with tuple unpacking
            node_value_func = node_value.get("func") if is_type(node_value, ["Call"]) else None
            if is_type(node_value, ["Call"]) and is_type(node_value_func, ["Attribute"]):
                if node_value_func.get("attr") == "pop":
                    # a, b = stack.pop() -> entry := stack[len(stack)-1]; stack = stack[:len(stack)-1]; a = entry.F0; b = entry.F1
                    func_value = node_value_func.get("value")
                    obj = dispatch.lower_expr(func_value)
                    obj_lval = dispatch.lower_lvalue(func_value)
                    lval0 = dispatch.lower_lvalue(target_elts[0])
                    lval1 = dispatch.lower_lvalue(target_elts[1])
                    len_minus_1 = ir.BinaryOp(
                        op="-",
                        left=ir.Len(expr=obj, typ=INT),
                        right=ir.IntLit(value=1, typ=INT),
                        typ=INT,
                    )
                    # Infer tuple element type from the list's type if available
                    entry_type: "Type" = Tuple((BOOL, BOOL))  # Default
                    if is_type(func_value, ["Name"]):
                        var_name = func_value.get("id")
                        if var_name in type_ctx.var_types:
                            list_type = type_ctx.var_types[var_name]
                            if isinstance(list_type, Slice) and isinstance(
                                list_type.element, Tuple
                            ):
                                entry_type = list_type.element
                    # Get field types from entry_type
                    f0_type = (
                        entry_type.elements[0]
                        if isinstance(entry_type, Tuple) and len(entry_type.elements) > 0
                        else BOOL
                    )
                    f1_type = (
                        entry_type.elements[1]
                        if isinstance(entry_type, Tuple) and len(entry_type.elements) > 1
                        else BOOL
                    )
                    entry_var = ir.Var(name="_entry", typ=entry_type)
                    return ir.Block(
                        body=[
                            ir.VarDecl(
                                name="_entry",
                                typ=entry_type,
                                value=ir.Index(obj=obj, index=len_minus_1, typ=entry_type),
                            ),
                            ir.Assign(
                                target=obj_lval,
                                value=ir.SliceExpr(
                                    obj=obj, high=len_minus_1, typ=InterfaceRef("any")
                                ),
                            ),
                            ir.Assign(
                                target=lval0,
                                value=ir.FieldAccess(obj=entry_var, field="F0", typ=f0_type),
                            ),
                            ir.Assign(
                                target=lval1,
                                value=ir.FieldAccess(obj=entry_var, field="F1", typ=f1_type),
                            ),
                        ],
                        loc=loc_from_node(node),
                    )
                else:
                    # General tuple unpacking: a, b = obj.method()
                    lval0 = dispatch.lower_lvalue(target_elts[0])
                    lval1 = dispatch.lower_lvalue(target_elts[1])
                    return ir.TupleAssign(
                        targets=[lval0, lval1], value=value, loc=loc_from_node(node)
                    )
            # General tuple unpacking for function calls: a, b = func()
            if is_type(node_value, ["Call"]):
                lval0 = dispatch.lower_lvalue(target_elts[0])
                lval1 = dispatch.lower_lvalue(target_elts[1])
                return ir.TupleAssign(targets=[lval0, lval1], value=value, loc=loc_from_node(node))
            # Tuple unpacking from index: a, b = list[idx] where list is []Tuple
            if is_type(node_value, ["Subscript"]):
                # Infer tuple element type from the list's type
                entry_type: "Type" = Tuple((InterfaceRef("any"), InterfaceRef("any")))  # Default
                node_value_value = node_value.get("value")
                if is_type(node_value_value, ["Name"]):
                    var_name = node_value_value.get("id")
                    if var_name in type_ctx.var_types:
                        list_type = type_ctx.var_types[var_name]
                        if isinstance(list_type, Slice) and isinstance(list_type.element, Tuple):
                            entry_type = list_type.element
                # Get field types from entry_type
                f0_type = (
                    entry_type.elements[0]
                    if isinstance(entry_type, Tuple) and len(entry_type.elements) > 0
                    else InterfaceRef("any")
                )
                f1_type = (
                    entry_type.elements[1]
                    if isinstance(entry_type, Tuple) and len(entry_type.elements) > 1
                    else InterfaceRef("any")
                )
                lval0 = dispatch.lower_lvalue(target_elts[0])
                lval1 = dispatch.lower_lvalue(target_elts[1])
                entry_var = ir.Var(name="_entry", typ=entry_type)
                # Update var_types for the targets
                if is_type(target_elts[0], ["Name"]):
                    type_ctx.var_types[target_elts[0].get("id")] = f0_type
                if is_type(target_elts[1], ["Name"]):
                    type_ctx.var_types[target_elts[1].get("id")] = f1_type
                return ir.Block(
                    body=[
                        ir.VarDecl(name="_entry", typ=entry_type, value=value),
                        ir.Assign(
                            target=lval0,
                            value=ir.FieldAccess(obj=entry_var, field="F0", typ=f0_type),
                        ),
                        ir.Assign(
                            target=lval1,
                            value=ir.FieldAccess(obj=entry_var, field="F1", typ=f1_type),
                        ),
                    ],
                    loc=loc_from_node(node),
                )
            # Tuple unpacking from tuple literal: a, b = x, y
            node_value_elts = node_value.get("elts", []) if is_type(node_value, ["Tuple"]) else []
            if is_type(node_value, ["Tuple"]) and len(node_value_elts) == 2:
                lval0 = dispatch.lower_lvalue(target_elts[0])
                lval1 = dispatch.lower_lvalue(target_elts[1])
                val0 = dispatch.lower_expr(node_value_elts[0])
                val1 = dispatch.lower_expr(node_value_elts[1])
                # Update var_types
                if is_type(target_elts[0], ["Name"]):
                    type_ctx.var_types[target_elts[0].get("id")] = type_inference.synthesize_type(
                        val0, type_ctx, ctx.current_func_info, ctx.symbols, ctx.node_types
                    )
                if is_type(target_elts[1], ["Name"]):
                    type_ctx.var_types[target_elts[1].get("id")] = type_inference.synthesize_type(
                        val1, type_ctx, ctx.current_func_info, ctx.symbols, ctx.node_types
                    )
                block = ir.Block(
                    body=[
                        ir.Assign(target=lval0, value=val0),
                        ir.Assign(target=lval1, value=val1),
                    ],
                    loc=loc_from_node(node),
                )
                block.no_scope = True  # Don't emit braces
                return block
        # Handle sentinel ints: var = None -> var = -1
        if isinstance(value, ir.NilLit) and is_sentinel_int(
            target, ctx.type_ctx, ctx.current_class_name, SENTINEL_INT_FIELDS
        ):
            value = ir.IntLit(value=-1, typ=INT, loc=loc_from_node(node))
        # Track variable type dynamically for later use in nested scopes
        # Apply VAR_TYPE_OVERRIDES first, then coerce
        if is_type(target, ["Name"]):
            func_name = ctx.current_func_info.name if ctx.current_func_info else ""
            target_id = target.get("id")
            override_key = (func_name, target_id)
            if override_key in VAR_TYPE_OVERRIDES:
                type_ctx.var_types[target_id] = VAR_TYPE_OVERRIDES[override_key]
        # Coerce value to target type if known
        target_id = target.get("id") if is_type(target, ["Name"]) else None
        if is_type(target, ["Name"]) and target_id in type_ctx.var_types:
            expected_type = type_ctx.var_types[target_id]
            from_type = type_inference.synthesize_type(
                value, type_ctx, ctx.current_func_info, ctx.symbols, ctx.node_types
            )
            value = type_inference.coerce(
                value,
                from_type,
                expected_type,
                type_ctx,
                ctx.current_func_info,
                ctx.symbols,
                ctx.node_types,
            )
        # Track variable type dynamically for later use in nested scopes
        if is_type(target, ["Name"]):
            target_id = target.get("id")
            # Check VAR_TYPE_OVERRIDES first
            func_name = ctx.current_func_info.name if ctx.current_func_info else ""
            override_key = (func_name, target_id)
            if override_key in VAR_TYPE_OVERRIDES:
                pass  # Already set above
            else:
                value_type = type_inference.synthesize_type(
                    value, type_ctx, ctx.current_func_info, ctx.symbols, ctx.node_types
                )
                # Update type if it's concrete (not any) and either:
                # - Variable not yet tracked, or
                # - Variable was RUNE from for-loop but now assigned STRING (from method call)
                current_type = type_ctx.var_types.get(target_id)
                if value_type != InterfaceRef("any"):
                    if current_type is None or (current_type == RUNE and value_type == STRING):
                        type_ctx.var_types[target_id] = value_type
        # Propagate narrowed status: if assigning from a narrowed var, target is also narrowed
        if is_type(target, ["Name"]) and is_type(node_value, ["Name"]):
            target_id = target.get("id")
            node_value_id = node_value.get("id")
            if node_value_id in type_ctx.narrowed_vars:
                type_ctx.narrowed_vars.add(target_id)
                # Also set the narrowed type for the target
                narrowed_type = type_ctx.var_types.get(node_value_id)
                if narrowed_type:
                    type_ctx.var_types[target_id] = narrowed_type
        # Track kind = node.kind assignments for kind-based type narrowing
        if is_type(target, ["Name"]) and is_type(node_value, ["Attribute"]):
            target_id = target.get("id")
            node_value_value = node_value.get("value")
            if node_value.get("attr") == "kind" and is_type(node_value_value, ["Name"]):
                type_ctx.kind_source_vars[target_id] = node_value_value.get("id")
        # Propagate list element union types: var = list[idx] where list has known element unions
        if is_type(target, ["Name"]) and is_type(node_value, ["Subscript"]):
            target_id = target.get("id")
            node_value_value = node_value.get("value")
            if is_type(node_value_value, ["Name"]):
                list_var = node_value_value.get("id")
                if list_var in type_ctx.list_element_unions:
                    type_ctx.union_types[target_id] = type_ctx.list_element_unions[list_var]
                    # Also reset var_types to Node so union_types logic is used for field access
                    type_ctx.var_types[target_id] = InterfaceRef("Node")
        lval = dispatch.lower_lvalue(target)
        assign = ir.Assign(target=lval, value=value, loc=loc_from_node(node))
        # Add declaration type if VAR_TYPE_OVERRIDE applies or if var_types has a unified Node type
        if is_type(target, ["Name"]):
            target_id = target.get("id")
            func_name = ctx.current_func_info.name if ctx.current_func_info else ""
            override_key = (func_name, target_id)
            if override_key in VAR_TYPE_OVERRIDES:
                assign.decl_typ = VAR_TYPE_OVERRIDES[override_key]
            elif target_id in type_ctx.var_types:
                # Use unified Node type from var_types for hoisted variables
                unified_type = type_ctx.var_types[target_id]
                if unified_type == InterfaceRef("Node"):
                    expr_type = type_inference.synthesize_type(
                        value, type_ctx, ctx.current_func_info, ctx.symbols, ctx.node_types
                    )
                    if unified_type != expr_type:
                        assign.decl_typ = unified_type
        return assign
    # Multiple targets: a = b = val -> emit assignment for each target
    stmts: list[ir.Stmt] = []
    for target in node_targets:
        lval = dispatch.lower_lvalue(target)
        stmts.append(ir.Assign(target=lval, value=value, loc=loc_from_node(node)))
        # Track variable type
        if is_type(target, ["Name"]):
            target_id = target.get("id")
            value_type = type_inference.synthesize_type(
                value, type_ctx, ctx.current_func_info, ctx.symbols, ctx.node_types
            )
            if value_type != InterfaceRef("any"):
                type_ctx.var_types[target_id] = value_type
    if len(stmts) == 1:
        return stmts[0]
    block = ir.Block(body=stmts, loc=loc_from_node(node))
    block.no_scope = True  # Don't emit braces
    return block


def lower_stmt_AnnAssign(
    node: ASTNode,
    ctx: "FrontendContext",
    dispatch: "LoweringDispatch",
) -> "ir.Stmt":
    """Lower a Python annotated assignment to IR."""
    from .. import ir

    node_annotation = node.get("annotation")
    node_value = node.get("value")
    node_target = node.get("target")
    py_type = dispatch.annotation_to_str(node_annotation)
    typ = type_inference.py_type_to_ir(py_type, ctx.symbols, ctx.node_types, False)
    type_ctx = ctx.type_ctx
    # Handle int | None = None -> use -1 as sentinel
    if (
        isinstance(typ, Optional)
        and typ.inner == INT
        and node_value
        and is_type(node_value, ["Constant"])
        and node_value.get("value") is None
    ):
        if is_type(node_target, ["Name"]):
            # Store as plain int with -1 sentinel
            return ir.VarDecl(
                name=node_target.get("id"),
                typ=INT,
                value=ir.IntLit(value=-1, typ=INT, loc=loc_from_node(node)),
                loc=loc_from_node(node),
            )
    # Determine expected type for lowering (use field type for field assignments)
    expected_type = typ
    if (
        is_type(node_target, ["Attribute"])
        and is_type(node_target.get("value"), ["Name"])
        and node_target.get("value").get("id") == "self"
        and ctx.current_class_name
    ):
        field_name = node_target.get("attr")
        struct_info = ctx.symbols.structs.get(ctx.current_class_name)
        if struct_info:
            field_info = struct_info.fields.get(field_name)
            if field_info:
                expected_type = field_info.typ
    if node_value:
        # For list values, pass expected type to get correct element type
        if is_type(node_value, ["List"]):
            value = dispatch.lower_expr_List(node_value, expected_type)
        else:
            value = dispatch.lower_expr(node_value)
        # Coerce value to expected type
        from_type = type_inference.synthesize_type(
            value, type_ctx, ctx.current_func_info, ctx.symbols, ctx.node_types
        )
        value = type_inference.coerce(
            value,
            from_type,
            expected_type,
            type_ctx,
            ctx.current_func_info,
            ctx.symbols,
            ctx.node_types,
        )
    else:
        value = None
    if is_type(node_target, ["Name"]):
        # Update type context with declared type (overrides any earlier inference)
        type_ctx.var_types[node_target.get("id")] = typ
        return ir.VarDecl(name=node_target.get("id"), typ=typ, value=value, loc=loc_from_node(node))
    # Attribute target - treat as assignment
    lval = dispatch.lower_lvalue(node_target)
    if value:
        # Handle sentinel ints for field assignments: self.field = None -> self.field = -1
        if isinstance(value, ir.NilLit) and is_sentinel_int(
            node_target, type_ctx, ctx.current_class_name, SENTINEL_INT_FIELDS
        ):
            value = ir.IntLit(value=-1, typ=INT, loc=loc_from_node(node))
        # For field assignments, coerce to the actual field type (from struct info)
        if (
            is_type(node_target, ["Attribute"])
            and is_type(node_target.get("value"), ["Name"])
            and node_target.get("value").get("id") == "self"
            and ctx.current_class_name
        ):
            field_name = node_target.get("attr")
            struct_info = ctx.symbols.structs.get(ctx.current_class_name)
            if struct_info:
                field_info = struct_info.fields.get(field_name)
                if field_info:
                    from_type = type_inference.synthesize_type(
                        value, type_ctx, ctx.current_func_info, ctx.symbols, ctx.node_types
                    )
                    value = type_inference.coerce(
                        value,
                        from_type,
                        field_info.typ,
                        type_ctx,
                        ctx.current_func_info,
                        ctx.symbols,
                        ctx.node_types,
                    )
        return ir.Assign(target=lval, value=value, loc=loc_from_node(node))
    return ir.ExprStmt(expr=ir.Var(name="_skip_ann", typ=VOID))


def collect_isinstance_chain(
    node: ASTNode,
    var_name: str,
    ctx: "FrontendContext",
    dispatch: "LoweringDispatch",
) -> tuple[list["ir.TypeCase"], list["ir.Stmt"]]:
    """Collect isinstance checks on same variable into TypeSwitch cases."""
    from .. import ir

    type_ctx = ctx.type_ctx
    cases: list[ir.TypeCase] = []
    current = node
    while True:
        # Check for single isinstance or isinstance-or-chain
        check = extract_isinstance_or_chain(current.get("test"), ctx.kind_to_class)
        if not check or check[0] != var_name:
            break
        _, type_names = check
        # Lower body once, generate case for each type
        # For or chains, duplicate the body for each type
        for type_name in type_names:
            typ = resolve_type_name(type_name, type_inference.TYPE_MAP, ctx.symbols)
            # Temporarily narrow the variable type for this branch
            old_type = type_ctx.var_types.get(var_name)
            type_ctx.var_types[var_name] = typ
            body = dispatch.lower_stmts(current.get("body", []))
            # Restore original type
            if old_type is not None:
                type_ctx.var_types[var_name] = old_type
            else:
                type_ctx.var_types.pop(var_name, None)
            cases.append(ir.TypeCase(typ=typ, body=body, loc=loc_from_node(current)))
        # Check for elif isinstance chain
        orelse = current.get("orelse", [])
        if len(orelse) == 1 and is_type(orelse[0], ["If"]):
            current = orelse[0]
        elif orelse:
            # Has else block - becomes default
            default = dispatch.lower_stmts(orelse)
            return cases, default
        else:
            return cases, []
    # Reached non-isinstance condition - treat rest as default
    if current != node:
        # Need to lower the remaining if statement
        current_orelse = current.get("orelse", [])
        default_if = ir.If(
            cond=dispatch.lower_expr_as_bool(current.get("test")),
            then_body=dispatch.lower_stmts(current.get("body", [])),
            else_body=dispatch.lower_stmts(current_orelse) if current_orelse else [],
            loc=loc_from_node(current),
        )
        return cases, [default_if]
    return [], []


def lower_stmt_If(
    node: ASTNode,
    ctx: "FrontendContext",
    dispatch: "LoweringDispatch",
) -> "ir.Stmt":
    """Lower a Python if statement to IR."""
    from .. import ir
    from ..ir import TypeSwitch

    type_ctx = ctx.type_ctx
    node_test = node.get("test")
    node_body = node.get("body", [])
    node_orelse = node.get("orelse", [])
    # Check for isinstance chain pattern (including 'or' patterns)
    isinstance_check = extract_isinstance_or_chain(node_test, ctx.kind_to_class)
    if isinstance_check:
        var_name, _ = isinstance_check
        # Try to collect full isinstance chain on same variable
        cases, default = collect_isinstance_chain(node, var_name, ctx, dispatch)
        if cases:
            var_expr = dispatch.lower_expr({"_type": "Name", "id": var_name})
            return TypeSwitch(
                expr=var_expr,
                binding=var_name,
                cases=cases,
                default=default,
                loc=loc_from_node(node),
            )
    # Fall back to regular If emission
    cond = dispatch.lower_expr_as_bool(node_test)
    # Check for isinstance in compound AND condition for type narrowing
    isinstance_in_and = extract_isinstance_from_and(node_test)
    # Check for kind-based type narrowing (kind == "value" or node.kind == "value")
    kind_check = extract_kind_check(node_test, ctx.kind_to_struct, ctx.type_ctx.kind_source_vars)
    narrowed_var = None
    old_type = None
    was_already_narrowed = False
    if isinstance_in_and:
        var_name, type_name = isinstance_in_and
        typ = resolve_type_name(type_name, type_inference.TYPE_MAP, ctx.symbols)
        narrowed_var = var_name
        old_type = type_ctx.var_types.get(var_name)
        was_already_narrowed = var_name in type_ctx.narrowed_vars
        type_ctx.var_types[var_name] = typ
        type_ctx.narrowed_vars.add(var_name)
    elif kind_check:
        var_name, struct_name = kind_check
        typ = Pointer(StructRef(struct_name))
        narrowed_var = var_name
        old_type = type_ctx.var_types.get(var_name)
        was_already_narrowed = var_name in type_ctx.narrowed_vars
        type_ctx.var_types[var_name] = typ
        type_ctx.narrowed_vars.add(var_name)
    then_body = dispatch.lower_stmts(node_body)
    # Restore narrowed type after processing body
    if narrowed_var is not None:
        if old_type is not None:
            type_ctx.var_types[narrowed_var] = old_type
        else:
            type_ctx.var_types.pop(narrowed_var, None)
        if not was_already_narrowed:
            type_ctx.narrowed_vars.discard(narrowed_var)
    else_body = dispatch.lower_stmts(node_orelse) if node_orelse else []
    return ir.If(cond=cond, then_body=then_body, else_body=else_body, loc=loc_from_node(node))


def lower_stmt_For(
    node: ASTNode,
    ctx: "FrontendContext",
    dispatch: "LoweringDispatch",
) -> "ir.Stmt":
    """Lower a Python for loop to IR."""
    from .. import ir

    type_ctx = ctx.type_ctx
    node_iter = node.get("iter")
    node_target = node.get("target")
    node_body = node.get("body", [])
    iterable = dispatch.lower_expr(node_iter)
    # Determine loop variable types based on iterable type
    iterable_type = dispatch.infer_expr_type_from_ast(node_iter)
    # Dereference Pointer(Slice) or Optional(Slice) for range
    inner_slice = get_inner_slice(iterable_type)
    if inner_slice is not None:
        iterable = ir.UnaryOp(op="*", operand=iterable, typ=inner_slice, loc=iterable.loc)
        iterable_type = inner_slice
    # Determine index and value names
    index = None
    value = None
    # Get element type for loop variable
    elem_type: "Type | None" = None
    if iterable_type == STRING:
        elem_type = RUNE
    elif isinstance(iterable_type, Slice):
        elem_type = iterable_type.element
    if is_type(node_target, ["Name"]):
        target_id = node_target.get("id")
        if target_id == "_":
            pass  # Discard
        else:
            value = target_id
            if elem_type:
                type_ctx.var_types[value] = elem_type
    elif is_type(node_target, ["Tuple"]):
        target_elts = node_target.get("elts", [])
        if len(target_elts) == 2:
            # Check if iterating over Slice(Tuple) - need tuple unpacking, not (index, value)
            if isinstance(elem_type, Tuple) and len(elem_type.elements) >= 2:
                # Generate: for _, _item := range iterable; a := _item.F0; b := _item.F1
                item_var = "_item"
                # Set types for unpacked variables
                unpack_vars: list[tuple[int, str]] = []
                for i, elt in enumerate(target_elts):
                    if is_type(elt, ["Name"]) and elt.get("id") != "_":
                        elt_id = elt.get("id")
                        unpack_vars.append((i, elt_id))
                        if i < len(elem_type.elements):
                            type_ctx.var_types[elt_id] = elem_type.elements[i]
                # Lower body after setting up types
                body = dispatch.lower_stmts(node_body)
                # Prepend unpacking assignments
                unpack_stmts: list[ir.Stmt] = []
                for i, var_name in unpack_vars:
                    field_type = (
                        elem_type.elements[i] if i < len(elem_type.elements) else InterfaceRef("any")
                    )
                    field_access = ir.FieldAccess(
                        obj=ir.Var(name=item_var, typ=elem_type, loc=loc_from_node(node)),
                        field=f"F{i}",
                        typ=field_type,
                        loc=loc_from_node(node),
                    )
                    unpack_stmts.append(
                        ir.Assign(
                            target=ir.VarLV(name=var_name),
                            value=field_access,
                            loc=loc_from_node(node),
                        )
                    )
                return ir.ForRange(
                    index=None,
                    value=item_var,
                    iterable=iterable,
                    body=unpack_stmts + body,
                    loc=loc_from_node(node),
                )
            # Otherwise treat as (index, value) iteration
            if is_type(target_elts[0], ["Name"]):
                elt0_id = target_elts[0].get("id")
                index = elt0_id if elt0_id != "_" else None
            if is_type(target_elts[1], ["Name"]):
                elt1_id = target_elts[1].get("id")
                value = elt1_id if elt1_id != "_" else None
                if elem_type and value:
                    type_ctx.var_types[value] = elem_type
    # Lower body after setting up loop variable types
    body = dispatch.lower_stmts(node_body)
    return ir.ForRange(
        index=index, value=value, iterable=iterable, body=body, loc=loc_from_node(node)
    )


def lower_stmt_Try(
    node: ASTNode,
    ctx: "FrontendContext",
    dispatch: "LoweringDispatch",
    set_catch_var: Callable[[str | None], str | None],
) -> "ir.Stmt":
    """Lower a Python try statement to IR."""
    from .. import ir

    body = dispatch.lower_stmts(node.get("body", []))
    catch_var = None
    catch_body: list[ir.Stmt] = []
    reraise = False
    handlers = node.get("handlers", [])
    if handlers:
        handler = handlers[0]
        catch_var = handler.get("name")
        handler_body = handler.get("body", [])
        # Set catch var context so raise e can be detected
        saved_catch_var = set_catch_var(catch_var)
        catch_body = dispatch.lower_stmts(handler_body)
        set_catch_var(saved_catch_var)
        # Check if handler re-raises (bare raise)
        for stmt in handler_body:
            if is_type(stmt, ["Raise"]) and stmt.get("exc") is None:
                reraise = True
    return ir.TryCatch(
        body=body,
        catch_var=catch_var,
        catch_body=catch_body,
        reraise=reraise,
        loc=loc_from_node(node),
    )


# ============================================================
# LVALUE LOWERING
# ============================================================


def lower_lvalue(
    node: ASTNode,
    lower_expr: Callable[[ASTNode], "ir.Expr"],
) -> "ir.LValue":
    """Lower an expression to an LValue."""
    from .. import ir

    if is_type(node, ["Name"]):
        return ir.VarLV(name=node.get("id"), loc=loc_from_node(node))
    if is_type(node, ["Attribute"]):
        obj = lower_expr(node.get("value"))
        return ir.FieldLV(obj=obj, field=node.get("attr"), loc=loc_from_node(node))
    if is_type(node, ["Subscript"]):
        obj = lower_expr(node.get("value"))
        idx = lower_expr(node.get("slice"))
        return ir.IndexLV(obj=obj, index=idx, loc=loc_from_node(node))
    return ir.VarLV(name="_unknown_lvalue", loc=loc_from_node(node))


# ============================================================
# DISPATCH TABLES
# ============================================================


def _lower_expr_Constant_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Expr":
    return lower_expr_Constant(node)


def _lower_expr_Name_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Expr":
    return lower_expr_Name(node, ctx.type_ctx, ctx.symbols)


def _lower_expr_Attribute_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Expr":
    from ..type_overrides import NODE_FIELD_TYPES

    return lower_expr_Attribute(
        node,
        ctx.symbols,
        ctx.type_ctx,
        ctx.current_class_name,
        NODE_FIELD_TYPES,
        d.lower_expr,
        type_inference.is_node_interface_type,
    )


def _lower_expr_Subscript_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Expr":
    return lower_expr_Subscript(
        node,
        ctx.type_ctx,
        d.lower_expr,
        lambda idx, obj, parent: convert_negative_index(idx, obj, parent, d.lower_expr),
        d.infer_expr_type_from_ast,
    )


def _lower_expr_BinOp_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Expr":
    return lower_expr_BinOp(node, d.lower_expr, d.infer_expr_type_from_ast)


def _lower_expr_Compare_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Expr":
    from ..type_overrides import SENTINEL_INT_FIELDS

    return lower_expr_Compare(
        node,
        d.lower_expr,
        d.infer_expr_type_from_ast,
        ctx.type_ctx,
        ctx.current_class_name,
        SENTINEL_INT_FIELDS,
    )


def _lower_expr_BoolOp_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Expr":
    return lower_expr_BoolOp(node, d.lower_expr_as_bool)


def _lower_expr_UnaryOp_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Expr":
    return lower_expr_UnaryOp(node, d.lower_expr, d.lower_expr_as_bool)


def _lower_expr_IfExp_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Expr":
    return lower_expr_IfExp(
        node,
        d.lower_expr,
        d.lower_expr_as_bool,
        lambda n: extract_attr_kind_check(n, ctx.kind_to_struct),
        ctx.type_ctx,
    )


def _lower_expr_List_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Expr":
    return lower_expr_List(
        node, d.lower_expr, d.infer_expr_type_from_ast, ctx.type_ctx.expected, None
    )


def _lower_expr_Dict_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Expr":
    return lower_expr_Dict(node, d.lower_expr, d.infer_expr_type_from_ast)


def _lower_expr_JoinedStr_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Expr":
    return lower_expr_JoinedStr(node, d.lower_expr)


def _lower_expr_Tuple_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Expr":
    return lower_expr_Tuple(node, d.lower_expr)


def _lower_expr_Set_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Expr":
    return lower_expr_Set(node, d.lower_expr)


EXPR_HANDLERS: dict[
    str, Callable[[ASTNode, "FrontendContext", "LoweringDispatch"], "ir.Expr"]
] = {
    "Constant": _lower_expr_Constant_dispatch,
    "Name": _lower_expr_Name_dispatch,
    "Attribute": _lower_expr_Attribute_dispatch,
    "Subscript": _lower_expr_Subscript_dispatch,
    "BinOp": _lower_expr_BinOp_dispatch,
    "Compare": _lower_expr_Compare_dispatch,
    "BoolOp": _lower_expr_BoolOp_dispatch,
    "UnaryOp": _lower_expr_UnaryOp_dispatch,
    "Call": lower_expr_Call,  # Already has (node, ctx, dispatch) signature
    "IfExp": _lower_expr_IfExp_dispatch,
    "List": _lower_expr_List_dispatch,
    "Dict": _lower_expr_Dict_dispatch,
    "JoinedStr": _lower_expr_JoinedStr_dispatch,
    "Tuple": _lower_expr_Tuple_dispatch,
    "Set": _lower_expr_Set_dispatch,
}


def lower_expr(node: ASTNode, ctx: "FrontendContext", dispatch: "LoweringDispatch") -> "ir.Expr":
    """Lower a Python expression to IR using dispatch table."""
    from .. import ir

    handler = EXPR_HANDLERS.get(node.get("_type"))
    if handler:
        return handler(node, ctx, dispatch)
    return ir.Var(name=f"TODO_{node.get('_type', 'unknown')}", typ=InterfaceRef("any"))


def _lower_stmt_Expr_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Stmt":
    return lower_stmt_Expr(node, d.lower_expr)


def _lower_stmt_AugAssign_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Stmt":
    return lower_stmt_AugAssign(node, d.lower_lvalue, d.lower_expr)


def _lower_stmt_Return_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Stmt":
    return lower_stmt_Return(node, ctx, d.lower_expr)


def _lower_stmt_While_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Stmt":
    return lower_stmt_While(node, d.lower_expr_as_bool, d.lower_stmts)


def _lower_stmt_Break_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Stmt":
    return lower_stmt_Break(node)


def _lower_stmt_Continue_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Stmt":
    return lower_stmt_Continue(node)


def _lower_stmt_Pass_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Stmt":
    return lower_stmt_Pass(node)


def _lower_stmt_Raise_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Stmt":
    return lower_stmt_Raise(node, d.lower_expr, ctx.current_catch_var)


def _lower_stmt_FunctionDef_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Stmt":
    return lower_stmt_FunctionDef(node)


def _lower_stmt_Try_dispatch(
    node: ASTNode, ctx: "FrontendContext", d: "LoweringDispatch"
) -> "ir.Stmt":
    return lower_stmt_Try(node, ctx, d, d.set_catch_var)


STMT_HANDLERS: dict[
    str, Callable[[ASTNode, "FrontendContext", "LoweringDispatch"], "ir.Stmt"]
] = {
    "Expr": _lower_stmt_Expr_dispatch,
    "Assign": lower_stmt_Assign,  # Already has (node, ctx, dispatch) signature
    "AnnAssign": lower_stmt_AnnAssign,  # Already has (node, ctx, dispatch) signature
    "AugAssign": _lower_stmt_AugAssign_dispatch,
    "Return": _lower_stmt_Return_dispatch,
    "If": lower_stmt_If,  # Already has (node, ctx, dispatch) signature
    "While": _lower_stmt_While_dispatch,
    "For": lower_stmt_For,  # Already has (node, ctx, dispatch) signature
    "Break": _lower_stmt_Break_dispatch,
    "Continue": _lower_stmt_Continue_dispatch,
    "Pass": _lower_stmt_Pass_dispatch,
    "Raise": _lower_stmt_Raise_dispatch,
    "Try": _lower_stmt_Try_dispatch,
    "FunctionDef": _lower_stmt_FunctionDef_dispatch,
}


def lower_stmt(node: ASTNode, ctx: "FrontendContext", dispatch: "LoweringDispatch") -> "ir.Stmt":
    """Lower a Python statement to IR using dispatch table."""
    from .. import ir

    handler = STMT_HANDLERS.get(node.get("_type"))
    if handler:
        return handler(node, ctx, dispatch)
    return ir.ExprStmt(expr=ir.Var(name=f"TODO_{node.get('_type', 'unknown')}", typ=InterfaceRef("any")))


def lower_stmts(
    stmts: list[ASTNode], ctx: "FrontendContext", dispatch: "LoweringDispatch"
) -> list["ir.Stmt"]:
    """Lower a list of Python statements to IR."""
    return [lower_stmt(s, ctx, dispatch) for s in stmts]
