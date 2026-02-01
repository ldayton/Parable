"""Phase 5: Function and method signature collection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .ast_compat import ASTNode, dict_walk, is_type
from .collection import CollectionCallbacks
from ..ir import (
    FuncInfo,
    InterfaceRef,
    ParamInfo,
    Pointer,
    Slice,
    VOID,
)
from ..type_overrides import RETURN_TYPE_OVERRIDES

if TYPE_CHECKING:
    from ..ir import SymbolTable


def detect_mutated_params(node: ASTNode) -> set[str]:
    """Detect which parameters are mutated in the function body."""
    mutated = set()
    args = node.get("args", {})
    args_list = args.get("args", [])
    param_names = {a.get("arg") for a in args_list if a.get("arg") != "self"}
    for stmt in dict_walk(node):
        # param.append(...), param.extend(...), param.clear(), param.pop()
        if is_type(stmt, ["Expr"]) and is_type(stmt.get("value"), ["Call"]):
            call = stmt.get("value")
            if is_type(call.get("func"), ["Attribute"]):
                func = call.get("func")
                if func.get("attr") in ("append", "extend", "clear", "pop"):
                    if is_type(func.get("value"), ["Name"]) and func.get("value", {}).get("id") in param_names:
                        mutated.add(func.get("value", {}).get("id"))
        # param[i] = ...
        if is_type(stmt, ["Assign"]):
            for target in stmt.get("targets", []):
                if is_type(target, ["Subscript"]):
                    if is_type(target.get("value"), ["Name"]) and target.get("value", {}).get("id") in param_names:
                        mutated.add(target.get("value", {}).get("id"))
    return mutated


def extract_func_info(
    node: ASTNode,
    callbacks: CollectionCallbacks,
    is_method: bool = False,
) -> FuncInfo:
    """Extract function signature information."""
    mutated_params = detect_mutated_params(node)
    params = []
    args = node.get("args", {})
    args_list = args.get("args", [])
    defaults = args.get("defaults", [])
    non_self_args = [a for a in args_list if a.get("arg") != "self"]
    n_params = len(non_self_args)
    n_defaults = len(defaults) if defaults else 0
    for i, arg in enumerate(non_self_args):
        annotation = arg.get("annotation")
        py_type = callbacks.annotation_to_str(annotation) if annotation else ""
        typ = callbacks.py_type_to_ir(py_type, False) if py_type else InterfaceRef("any")
        # Auto-wrap mutated slice params with Pointer
        if arg.get("arg") in mutated_params and isinstance(typ, Slice):
            typ = Pointer(typ)
        has_default = False
        default_value = None
        # Check if this param has a default
        if i >= n_params - n_defaults:
            has_default = True
            default_idx = i - (n_params - n_defaults)
            if defaults and default_idx < len(defaults):
                default_value = callbacks.lower_expr(defaults[default_idx])
        params.append(
            ParamInfo(name=arg.get("arg"), typ=typ, has_default=has_default, default_value=default_value)
        )
    return_type = VOID
    returns = node.get("returns")
    if returns:
        py_return = callbacks.annotation_to_str(returns)
        return_type = callbacks.py_return_type_to_ir(py_return)
    # Apply return type overrides
    if node.get("name") in RETURN_TYPE_OVERRIDES:
        return_type = RETURN_TYPE_OVERRIDES[node.get("name")]
    return FuncInfo(
        name=node.get("name"),
        params=params,
        return_type=return_type,
        is_method=is_method,
    )


def collect_class_methods(
    node: ASTNode,
    symbols: SymbolTable,
    callbacks: CollectionCallbacks,
) -> None:
    """Collect method signatures for a class."""
    info = symbols.structs[node.get("name")]
    for stmt in node.get("body", []):
        if is_type(stmt, ["FunctionDef"]):
            func_info = extract_func_info(stmt, callbacks, is_method=True)
            func_info.is_method = True
            func_info.receiver_type = node.get("name")
            info.methods[stmt.get("name")] = func_info
    # Build method-to-struct mapping for Node subclasses
    if info.is_node:
        excluded_methods = {"to_sexp", "kind", "__init__", "__repr__", "ToSexp", "GetKind"}
        for method_name in info.methods:
            if method_name not in excluded_methods:
                symbols.method_to_structs[method_name] = info.name


def collect_signatures(
    tree: ASTNode,
    symbols: SymbolTable,
    callbacks: CollectionCallbacks,
) -> None:
    """Pass 5: Collect function and method signatures."""
    for node in tree.get("body", []):
        if is_type(node, ["FunctionDef"]):
            symbols.functions[node.get("name")] = extract_func_info(node, callbacks)
        elif is_type(node, ["ClassDef"]):
            collect_class_methods(node, symbols, callbacks)
