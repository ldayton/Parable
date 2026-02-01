"""Type inference utilities (Phase 8).

Consolidates all type inference logic:
- Core type conversion (from type_inference.py)
- Pre-scan variable type collection (from collection.py)
- Type narrowing helpers (from lowering.py)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from .ast_compat import ASTNode, dict_walk, is_type
from ..ir import (
    BOOL,
    BYTE,
    FLOAT,
    INT,
    RUNE,
    FuncInfo,
    InterfaceRef,
    Map,
    Optional,
    Pointer,
    Set,
    Slice,
    STRING,
    StructRef,
    Tuple,
)

if TYPE_CHECKING:
    from ..ir import SymbolTable, Type

# Re-export everything from type_inference.py
from .type_inference import (
    TYPE_MAP,
    coerce,
    extract_struct_name,
    extract_union_struct_names,
    infer_call_return_type,
    infer_container_type_from_ast,
    infer_expr_type_from_ast,
    infer_iterable_type,
    infer_type_from_value,
    is_node_interface_type,
    is_node_subtype,
    parse_callable_type,
    py_return_type_to_ir,
    py_type_to_ir,
    split_type_args,
    split_union_types,
    synthesize_field_type,
    synthesize_index_type,
    synthesize_method_return_type,
    synthesize_type,
)

__all__ = [
    # From type_inference.py
    "TYPE_MAP",
    "coerce",
    "extract_struct_name",
    "extract_union_struct_names",
    "infer_call_return_type",
    "infer_container_type_from_ast",
    "infer_expr_type_from_ast",
    "infer_iterable_type",
    "infer_type_from_value",
    "is_node_interface_type",
    "is_node_subtype",
    "parse_callable_type",
    "py_return_type_to_ir",
    "py_type_to_ir",
    "split_type_args",
    "split_union_types",
    "synthesize_field_type",
    "synthesize_index_type",
    "synthesize_method_return_type",
    "synthesize_type",
    # Type narrowing helpers (moved from lowering.py)
    "is_isinstance_call",
    "is_kind_check",
    "extract_isinstance_or_chain",
    "extract_isinstance_from_and",
    "extract_kind_check",
    "extract_attr_kind_check",
    "get_attr_path",
    # Pre-scan type collection (moved from collection.py)
    "collect_var_types",
    "compute_expr_types",
    "unify_branch_types",
    "collect_branch_var_types",
    "infer_branch_expr_type",
    "infer_element_type_from_append_arg",
    "InferenceCallbacks",
]


# ============================================================
# TYPE NARROWING HELPERS (moved from lowering.py)
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


# ============================================================
# PRE-SCAN TYPE COLLECTION (moved from collection.py)
# ============================================================


from dataclasses import dataclass


@dataclass
class InferenceCallbacks:
    """Callbacks for type inference that need access to other frontend components."""

    annotation_to_str: Callable[[ASTNode | None], str]
    py_type_to_ir: Callable[[str, bool], "Type"]
    extract_struct_name: Callable[["Type"], str | None]
    infer_container_type_from_ast: Callable[[ASTNode, dict[str, "Type"]], "Type"]
    is_len_call: Callable[[ASTNode], bool]
    is_kind_check: Callable[[ASTNode], tuple[str, str] | None]
    infer_call_return_type: Callable[[ASTNode], "Type"]
    infer_iterable_type: Callable[[ASTNode, dict[str, "Type"]], "Type"]


def infer_attr_chain_type(
    node: ASTNode,
    var_types: dict[str, "Type"],
    symbols: "SymbolTable",
    current_class_name: str,
) -> "Type":
    """Recursively infer type of chained attribute access like self.target.value."""
    if is_type(node, ["Name"]):
        name_id = node.get("id")
        if name_id == "self" and current_class_name:
            return Pointer(StructRef(current_class_name))
        if name_id in var_types:
            return var_types[name_id]
        return InterfaceRef("any")
    if is_type(node, ["Attribute"]):
        obj_type = infer_attr_chain_type(
            node.get("value", {}), var_types, symbols, current_class_name
        )
        struct_name = extract_struct_name(obj_type)
        if struct_name and struct_name in symbols.structs:
            field_info = symbols.structs[struct_name].fields.get(node.get("attr"))
            if field_info:
                return field_info.typ
        return InterfaceRef("any")
    return InterfaceRef("any")


def unify_branch_types(
    then_vars: dict[str, "Type"],
    else_vars: dict[str, "Type"],
) -> dict[str, "Type"]:
    """Unify variable types from if/else branches."""
    unified: dict[str, "Type"] = {}
    for var in set(then_vars) | set(else_vars):
        t1, t2 = then_vars.get(var), else_vars.get(var)
        if t1 == t2 and t1 is not None:
            unified[var] = t1
        elif t1 is not None and t2 is None:
            unified[var] = t1
        elif t2 is not None and t1 is None:
            unified[var] = t2
    return unified


def infer_branch_expr_type(
    node: ASTNode,
    var_types: dict[str, "Type"],
    branch_vars: dict[str, "Type"],
) -> "Type":
    """Infer type of expression during branch analysis."""
    if is_type(node, ["Constant"]):
        value = node.get("value")
        if isinstance(value, str):
            return STRING
        if isinstance(value, int) and not isinstance(value, bool):
            return INT
        if isinstance(value, bool):
            return BOOL
    if is_type(node, ["Name"]):
        node_id = node.get("id")
        if node_id in branch_vars:
            return branch_vars[node_id]
        if node_id in var_types:
            return var_types[node_id]
    if is_type(node, ["BinOp"]):
        left = infer_branch_expr_type(node.get("left"), var_types, branch_vars)
        right = infer_branch_expr_type(node.get("right"), var_types, branch_vars)
        if left == STRING or right == STRING:
            return STRING
        if left == INT or right == INT:
            return INT
    return InterfaceRef("any")


def collect_branch_var_types(
    stmts: list[ASTNode],
    var_types: dict[str, "Type"],
) -> dict[str, "Type"]:
    """Collect variable types assigned in a list of statements (for branch analysis)."""
    branch_vars: dict[str, "Type"] = {}
    # Walk entire subtree to find all assignments (may be nested in for/while/etc)
    for stmt in dict_walk({"_type": "Module", "body": stmts}):
        if is_type(stmt, ["Assign"]) and len(stmt.get("targets", [])) == 1:
            target = stmt.get("targets", [])[0]
            if is_type(target, ["Name"]):
                var_name = target.get("id")
                value = stmt.get("value", {})
                # Infer type from value
                if is_type(value, ["Constant"]):
                    v = value.get("value")
                    if isinstance(v, str):
                        branch_vars[var_name] = STRING
                    elif isinstance(v, int) and not isinstance(v, bool):
                        branch_vars[var_name] = INT
                    elif isinstance(v, bool):
                        branch_vars[var_name] = BOOL
                elif is_type(value, ["BinOp"]):
                    # String concatenation -> STRING
                    op = value.get("op", {})
                    if op.get("_type") == "Add":
                        left_type = infer_branch_expr_type(
                            value.get("left"), var_types, branch_vars
                        )
                        right_type = infer_branch_expr_type(
                            value.get("right"), var_types, branch_vars
                        )
                        if left_type == STRING or right_type == STRING:
                            branch_vars[var_name] = STRING
                        elif left_type == INT or right_type == INT:
                            branch_vars[var_name] = INT
                elif is_type(value, ["Name"]):
                    # Assign from another variable
                    value_id = value.get("id")
                    if value_id in var_types:
                        branch_vars[var_name] = var_types[value_id]
                    elif value_id in branch_vars:
                        branch_vars[var_name] = branch_vars[value_id]
                # Method calls (e.g., x.to_sexp() returns STRING)
                elif is_type(value, ["Call"]) and is_type(value.get("func"), ["Attribute"]):
                    method = value.get("func", {}).get("attr")
                    if method in (
                        "to_sexp",
                        "format",
                        "strip",
                        "lower",
                        "upper",
                        "replace",
                        "join",
                    ):
                        branch_vars[var_name] = STRING
    return branch_vars


def infer_element_type_from_append_arg(
    arg: ASTNode,
    var_types: dict[str, "Type"],
    symbols: "SymbolTable",
    current_class_name: str,
    current_func_info: FuncInfo | None,
    callbacks: InferenceCallbacks,
    hierarchy_root: str | None = None,
) -> "Type":
    """Infer slice element type from what's being appended."""
    # Constant literals
    if is_type(arg, ["Constant"]):
        value = arg.get("value")
        if isinstance(value, bool):
            return BOOL
        if isinstance(value, int):
            return INT
        if isinstance(value, str):
            return STRING
        if isinstance(value, float):
            return FLOAT
    # Variable reference with known type (e.g., loop variable)
    if is_type(arg, ["Name"]):
        arg_id = arg.get("id")
        if arg_id in var_types:
            return var_types[arg_id]
        # Check function parameters
        if current_func_info:
            for p in current_func_info.params:
                if p.name == arg_id:
                    return p.typ
    # Field access: self.field or obj.field
    if is_type(arg, ["Attribute"]):
        arg_value = arg.get("value", {})
        if is_type(arg_value, ["Name"]):
            if arg_value.get("id") == "self" and current_class_name:
                struct_info = symbols.structs.get(current_class_name)
                if struct_info:
                    field_info = struct_info.fields.get(arg.get("attr"))
                    if field_info:
                        return field_info.typ
            elif arg_value.get("id") in var_types:
                obj_type = var_types[arg_value.get("id")]
                struct_name = callbacks.extract_struct_name(obj_type)
                if struct_name and struct_name in symbols.structs:
                    field_info = symbols.structs[struct_name].fields.get(arg.get("attr"))
                    if field_info:
                        return field_info.typ
    # Subscript: container[i] -> infer element type from container
    if is_type(arg, ["Subscript"]):
        container_type = callbacks.infer_container_type_from_ast(arg.get("value"), var_types)
        if container_type == STRING:
            return STRING  # string[i] in Python returns a string
        if isinstance(container_type, Slice):
            return container_type.element
    # Tuple literal: (a, b, ...) -> Tuple(type(a), type(b), ...)
    if is_type(arg, ["Tuple"]):
        elem_types = []
        for elt in arg.get("elts", []):
            elem_types.append(
                infer_element_type_from_append_arg(
                    elt, var_types, symbols, current_class_name, current_func_info, callbacks, hierarchy_root
                )
            )
        return Tuple(tuple(elem_types))
    # Method calls
    if is_type(arg, ["Call"]) and is_type(arg.get("func"), ["Attribute"]):
        func = arg.get("func", {})
        method = func.get("attr")
        # String methods that return string
        if method in (
            "strip",
            "lstrip",
            "rstrip",
            "lower",
            "upper",
            "replace",
            "join",
            "format",
            "to_sexp",
        ):
            return STRING
        # .Copy() returns same type
        if method == "Copy":
            # x.Copy() where x is ctx -> *ParseContext
            func_value = func.get("value", {})
            if is_type(func_value, ["Name"]):
                var = func_value.get("id")
                if var == "ctx":
                    return Pointer(StructRef("ParseContext"))
    # Function/constructor calls
    if is_type(arg, ["Call"]) and is_type(arg.get("func"), ["Name"]):
        func_name = arg.get("func", {}).get("id")
        # String conversion functions
        if func_name in ("str", "string", "substring", "chr"):
            return STRING
        # Constructor calls
        if func_name in symbols.structs:
            info = symbols.structs[func_name]
            if info.is_node:
                return InterfaceRef(hierarchy_root) if hierarchy_root else InterfaceRef("any")
            return Pointer(StructRef(func_name))
        # Function return types
        if func_name in symbols.functions:
            return symbols.functions[func_name].return_type
    # Method calls: obj.method() -> look up method return type
    if is_type(arg, ["Call"]) and is_type(arg.get("func"), ["Attribute"]):
        func = arg.get("func", {})
        method_name = func.get("attr")
        func_value = func.get("value", {})
        # Handle self.method() calls directly using current class name
        # (can't use _infer_expr_type_from_ast here - _type_ctx not set yet)
        if is_type(func_value, ["Name"]) and func_value.get("id") == "self":
            if current_class_name and current_class_name in symbols.structs:
                method_info = symbols.structs[current_class_name].methods.get(method_name)
                if method_info:
                    return method_info.return_type
        # Handle other obj.method() calls via var_types lookup
        elif is_type(func_value, ["Name"]) and func_value.get("id") in var_types:
            obj_type = var_types[func_value.get("id")]
            struct_name = callbacks.extract_struct_name(obj_type)
            if struct_name and struct_name in symbols.structs:
                method_info = symbols.structs[struct_name].methods.get(method_name)
                if method_info:
                    return method_info.return_type
    return InterfaceRef("any")


def collect_var_types(
    stmts: list[ASTNode],
    symbols: "SymbolTable",
    current_class_name: str,
    current_func_info: FuncInfo | None,
    node_types: set[str],
    callbacks: InferenceCallbacks,
    hierarchy_root: str | None = None,
) -> tuple[dict[str, "Type"], dict[str, list[str]], set[str], dict[str, list[str]]]:
    """Pre-scan function body to collect variable types, tuple var mappings, and sentinel ints."""
    var_types: dict[str, "Type"] = {}
    tuple_vars: dict[str, list[str]] = {}
    sentinel_ints: set[str] = set()
    # Track variables assigned None and their concrete types (for Optional inference)
    vars_assigned_none: set[str] = set()
    vars_all_types: dict[str, list["Type"]] = {}  # Track all types assigned to each var
    # Preliminary pass: find variables assigned both None and typed values
    for stmt in dict_walk({"_type": "Module", "body": stmts}):
        if is_type(stmt, ["Assign"]) and len(stmt.get("targets", [])) == 1:
            target = stmt.get("targets", [])[0]
            if is_type(target, ["Name"]):
                var_name = target.get("id")
                if var_name not in vars_all_types:
                    vars_all_types[var_name] = []
                value = stmt.get("value", {})
                # Check if assigning None
                if is_type(value, ["Constant"]) and value.get("value") is None:
                    vars_assigned_none.add(var_name)
                # Check if assigning typed value
                elif is_type(value, ["Constant"]):
                    v = value.get("value")
                    if isinstance(v, int) and not isinstance(v, bool):
                        vars_all_types[var_name].append(INT)
                    elif isinstance(v, str):
                        vars_all_types[var_name].append(STRING)
                elif is_type(value, ["Call"]) and is_type(value.get("func"), ["Name"]):
                    # int(...) call
                    func_id = value.get("func", {}).get("id")
                    if func_id == "int":
                        vars_all_types[var_name].append(INT)
                    elif func_id == "str":
                        vars_all_types[var_name].append(STRING)
                # String method calls: x = "".join(...), etc.
                elif is_type(value, ["Call"]) and is_type(value.get("func"), ["Attribute"]):
                    func = value.get("func", {})
                    method = func.get("attr")
                    if method in (
                        "join",
                        "strip",
                        "lstrip",
                        "rstrip",
                        "lower",
                        "upper",
                        "replace",
                        "format",
                    ):
                        vars_all_types[var_name].append(STRING)
                    # self.method() calls - check return type
                    elif (
                        is_type(func.get("value"), ["Name"])
                        and func.get("value", {}).get("id") == "self"
                    ):
                        if current_class_name and current_class_name in symbols.structs:
                            method_info = symbols.structs[current_class_name].methods.get(method)
                            if method_info:
                                vars_all_types[var_name].append(method_info.return_type)
                # Assignment from known variable: varfd = varname
                elif is_type(value, ["Name"]):
                    value_id = value.get("id")
                    if value_id in vars_all_types and vars_all_types[value_id]:
                        vars_all_types[var_name].extend(vars_all_types[value_id])
    # Unify types for each variable
    vars_concrete_type: dict[str, "Type"] = {}
    for var_name, types in vars_all_types.items():
        if not types:
            continue
        # Deduplicate types
        unique_types = list(set(types))
        if len(unique_types) == 1:
            vars_concrete_type[var_name] = unique_types[0]
        else:
            # Multiple types - check if all are Node-related
            hierarchy_root_iface = InterfaceRef(hierarchy_root) if hierarchy_root else None
            hierarchy_root_struct = StructRef(hierarchy_root) if hierarchy_root else None
            all_node = hierarchy_root and all(
                t == hierarchy_root_iface
                or t == hierarchy_root_struct
                or (
                    isinstance(t, Pointer)
                    and isinstance(t.target, StructRef)
                    and t.target.name in node_types
                )
                for t in unique_types
            )
            if all_node and hierarchy_root:
                vars_concrete_type[var_name] = InterfaceRef(hierarchy_root)
            # Otherwise, no unified type (will fall back to default inference)
    # First pass: collect For loop variable types (needed for append inference)
    for stmt in dict_walk({"_type": "Module", "body": stmts}):
        if is_type(stmt, ["For"]):
            target = stmt.get("target", {})
            if is_type(target, ["Name"]):
                loop_var = target.get("id")
                iter_node = stmt.get("iter", {})
                # Check for range() call - loop variable is INT
                if (
                    is_type(iter_node, ["Call"])
                    and is_type(iter_node.get("func"), ["Name"])
                    and iter_node.get("func", {}).get("id") == "range"
                ):
                    var_types[loop_var] = INT
                else:
                    iterable_type = callbacks.infer_iterable_type(iter_node, var_types)
                    if iterable_type == STRING:
                        # Iterating over a string gives runes (single characters)
                        var_types[loop_var] = RUNE
                    elif isinstance(iterable_type, Slice):
                        var_types[loop_var] = iterable_type.element
            elif is_type(target, ["Tuple"]) and len(target.get("elts", [])) == 2:
                elts = target.get("elts", [])
                if is_type(elts[1], ["Name"]):
                    loop_var = elts[1].get("id")
                    iterable_type = callbacks.infer_iterable_type(stmt.get("iter"), var_types)
                    if isinstance(iterable_type, Slice):
                        var_types[loop_var] = iterable_type.element
    # Second pass: infer variable types from assignments (runs first to populate var_types)
    for stmt in dict_walk({"_type": "Module", "body": stmts}):
        # Infer from annotated assignments
        if is_type(stmt, ["AnnAssign"]) and is_type(stmt.get("target"), ["Name"]):
            target = stmt.get("target", {})
            py_type = callbacks.annotation_to_str(stmt.get("annotation"))
            typ = callbacks.py_type_to_ir(py_type, False)
            value = stmt.get("value", {})
            # int | None = None uses -1 sentinel, so track as INT not Optional
            if (
                isinstance(typ, Optional)
                and typ.inner == INT
                and value
                and is_type(value, ["Constant"])
                and value.get("value") is None
            ):
                var_types[target.get("id")] = INT
                sentinel_ints.add(target.get("id"))
            else:
                var_types[target.get("id")] = typ
        # Infer from return statements: if returning var and return type is known
        if is_type(stmt, ["Return"]) and stmt.get("value"):
            value = stmt.get("value", {})
            if is_type(value, ["Name"]):
                var_name = value.get("id")
                if current_func_info and isinstance(current_func_info.return_type, Slice):
                    var_types[var_name] = current_func_info.return_type
        # Infer from field assignments: self.field = var -> var has field's type
        if is_type(stmt, ["Assign"]) and len(stmt.get("targets", [])) == 1:
            target = stmt.get("targets", [])[0]
            value = stmt.get("value", {})
            if is_type(target, ["Attribute"]) and is_type(target.get("value"), ["Name"]):
                if target.get("value", {}).get("id") == "self" and is_type(value, ["Name"]):
                    var_name = value.get("id")
                    field_name = target.get("attr")
                    # Look up field type from current class
                    if current_class_name in symbols.structs:
                        struct_info = symbols.structs[current_class_name]
                        field_info = struct_info.fields.get(field_name)
                        if field_info:
                            var_types[var_name] = field_info.typ
            # Infer from method call assignments: var = self.method() -> var has method's return type
            if is_type(target, ["Name"]) and is_type(value, ["Call"]):
                var_name = target.get("id")
                call = value
                if is_type(call.get("func"), ["Attribute"]):
                    func = call.get("func", {})
                    method_name = func.get("attr")
                    # Get object type
                    if is_type(func.get("value"), ["Name"]):
                        obj_name = func.get("value", {}).get("id")
                        if obj_name == "self" and current_class_name:
                            struct_info = symbols.structs.get(current_class_name)
                            if struct_info:
                                method_info = struct_info.methods.get(method_name)
                                if method_info:
                                    var_types[var_name] = method_info.return_type
            # Infer from literal assignments
            if is_type(target, ["Name"]):
                var_name = target.get("id")
                if is_type(value, ["Constant"]):
                    v = value.get("value")
                    if isinstance(v, bool):
                        var_types[var_name] = BOOL
                    elif isinstance(v, int):
                        var_types[var_name] = INT
                    elif isinstance(v, str):
                        var_types[var_name] = STRING
                elif is_type(value, ["Name"]):
                    if value.get("id") in ("True", "False"):
                        var_types[var_name] = BOOL
                # Comparisons and bool ops always produce bool
                elif is_type(value, ["Compare", "BoolOp"]):
                    var_types[var_name] = BOOL
                # BinOp with arithmetic operators produce int
                elif is_type(value, ["BinOp"]):
                    op = value.get("op", {})
                    op_t = op.get("_type")
                    if op_t in ("Sub", "Mult", "FloorDiv", "Mod"):
                        var_types[var_name] = INT
                    elif op_t == "Add":
                        # Could be int or string - check operands
                        if callbacks.is_len_call(value.get("left")) or callbacks.is_len_call(
                            value.get("right")
                        ):
                            var_types[var_name] = INT
                # Infer from list/dict literals - element type inferred later from appends
                elif is_type(value, ["List"]):
                    var_types[var_name] = Slice(InterfaceRef("any"))
                elif is_type(value, ["Dict"]):
                    var_types[var_name] = Map(STRING, InterfaceRef("any"))
                # Infer from field access: var = obj.field -> var has field's type
                # Handles chained access like self.target.value
                elif is_type(value, ["Attribute"]):
                    field_type = infer_attr_chain_type(
                        value, var_types, symbols, current_class_name
                    )
                    if field_type != InterfaceRef("any"):
                        var_types[var_name] = field_type
                # Infer from subscript/slice: var = container[...] -> element type
                elif is_type(value, ["Subscript"]):
                    container_type: "Type" = InterfaceRef("any")
                    subscript_value = value.get("value", {})
                    if is_type(subscript_value, ["Name"]):
                        container_name = subscript_value.get("id")
                        if container_name in var_types:
                            container_type = var_types[container_name]
                    # Also handle field access: self.field[i]
                    elif is_type(subscript_value, ["Attribute"]):
                        attr = subscript_value
                        attr_value = attr.get("value", {})
                        if is_type(attr_value, ["Name"]):
                            if attr_value.get("id") == "self" and current_class_name:
                                struct_info = symbols.structs.get(current_class_name)
                                if struct_info:
                                    field_info = struct_info.fields.get(attr.get("attr"))
                                    if field_info:
                                        container_type = field_info.typ
                            elif attr_value.get("id") in var_types:
                                obj_type = var_types[attr_value.get("id")]
                                struct_name = callbacks.extract_struct_name(obj_type)
                                if struct_name and struct_name in symbols.structs:
                                    field_info = symbols.structs[struct_name].fields.get(
                                        attr.get("attr")
                                    )
                                    if field_info:
                                        container_type = field_info.typ
                    if container_type == STRING:
                        var_types[var_name] = STRING
                    elif isinstance(container_type, Slice):
                        # Indexing a slice gives the element type
                        var_types[var_name] = container_type.element
                    elif isinstance(container_type, Map):
                        # Indexing a map gives the value type
                        var_types[var_name] = container_type.value
                    elif isinstance(container_type, Tuple):
                        # Indexing a tuple with constant gives element type
                        slice_node = value.get("slice", {})
                        if is_type(slice_node, ["Constant"]) and isinstance(
                            slice_node.get("value"), int
                        ):
                            idx = slice_node.get("value")
                            if 0 <= idx and idx < len(container_type.elements):
                                var_types[var_name] = container_type.elements[idx]
                # Infer from method calls: var = obj.method() -> method return type
                elif is_type(value, ["Call"]) and is_type(value.get("func"), ["Attribute"]):
                    func = value.get("func", {})
                    method_name = func.get("attr")
                    obj_type: "Type" = InterfaceRef("any")
                    func_value = func.get("value", {})
                    # Handle string literal method calls: "".join(...), " ".join(...), etc.
                    if is_type(func_value, ["Constant"]) and isinstance(
                        func_value.get("value"), str
                    ):
                        if method_name in (
                            "join",
                            "replace",
                            "lower",
                            "upper",
                            "strip",
                            "lstrip",
                            "rstrip",
                            "format",
                        ):
                            var_types[var_name] = STRING
                            continue
                    if is_type(func_value, ["Name"]):
                        obj_name = func_value.get("id")
                        if obj_name == "self" and current_class_name:
                            obj_type = Pointer(StructRef(current_class_name))
                        elif obj_name in var_types:
                            obj_type = var_types[obj_name]
                        # Handle known string functions
                        elif obj_name == "strings" and method_name in (
                            "Join",
                            "Replace",
                            "ToLower",
                            "ToUpper",
                            "Trim",
                            "TrimSpace",
                        ):
                            var_types[var_name] = STRING
                            continue
                    struct_name = callbacks.extract_struct_name(obj_type)
                    if struct_name and struct_name in symbols.structs:
                        method_info = symbols.structs[struct_name].methods.get(method_name)
                        if method_info:
                            var_types[var_name] = method_info.return_type
        # Handle tuple unpacking: a, b = func() where func returns tuple
        if is_type(stmt, ["Assign"]) and len(stmt.get("targets", [])) == 1:
            target = stmt.get("targets", [])[0]
            value = stmt.get("value", {})
            if is_type(target, ["Tuple"]) and is_type(value, ["Call"]):
                # Get return type of the called function/method
                ret_type = callbacks.infer_call_return_type(value)
                if isinstance(ret_type, Tuple):
                    for i, elt in enumerate(target.get("elts", [])):
                        if is_type(elt, ["Name"]) and i < len(ret_type.elements):
                            var_types[elt.get("id")] = ret_type.elements[i]
            # Handle single var = tuple-returning func (will be expanded to synthetic vars)
            elif is_type(target, ["Name"]) and is_type(value, ["Call"]):
                ret_type = callbacks.infer_call_return_type(value)
                if isinstance(ret_type, Tuple) and len(ret_type.elements) > 1:
                    base_name = target.get("id")
                    synthetic_names = [f"{base_name}{i}" for i in range(len(ret_type.elements))]
                    tuple_vars[base_name] = synthetic_names
                    for i, elem_type in enumerate(ret_type.elements):
                        var_types[f"{base_name}{i}"] = elem_type
                # Handle constructor calls: var = ClassName()
                func = value.get("func", {})
                if is_type(func, ["Name"]):
                    class_name = func.get("id")
                    if class_name in symbols.structs:
                        var_types[target.get("id")] = Pointer(StructRef(class_name))
                    # Handle free function calls: var = func()
                    elif class_name in symbols.functions:
                        var_types[target.get("id")] = symbols.functions[class_name].return_type
                    # Handle builtin calls: bytearray(), list(), dict(), etc.
                    elif class_name == "bytearray":
                        var_types[target.get("id")] = Slice(BYTE)
                    elif class_name == "list":
                        var_types[target.get("id")] = Slice(InterfaceRef("any"))
                    elif class_name == "dict":
                        var_types[target.get("id")] = Map(InterfaceRef("any"), InterfaceRef("any"))
    # Third pass: infer types from append() calls (after all variable types are collected)
    # Note: don't overwrite already-known specific slice types (e.g., bytearray -> []byte)
    for stmt in dict_walk({"_type": "Module", "body": stmts}):
        if is_type(stmt, ["Expr"]) and is_type(stmt.get("value"), ["Call"]):
            call = stmt.get("value", {})
            func = call.get("func", {})
            if is_type(func, ["Attribute"]) and func.get("attr") == "append":
                func_value = func.get("value", {})
                call_args = call.get("args", [])
                if is_type(func_value, ["Name"]) and call_args:
                    var_name = func_value.get("id")
                    # Don't overwrite already-known specific slice types (e.g., bytearray)
                    # But DO infer if current type is generic Slice(any)
                    if var_name in var_types and isinstance(var_types[var_name], Slice):
                        current_elem = var_types[var_name].element
                        if current_elem != InterfaceRef("any"):
                            continue  # Skip - already has specific element type
                    elem_type = infer_element_type_from_append_arg(
                        call_args[0],
                        var_types,
                        symbols,
                        current_class_name,
                        current_func_info,
                        callbacks,
                        hierarchy_root,
                    )
                    if elem_type != InterfaceRef("any"):
                        var_types[var_name] = Slice(elem_type)
    # Third-and-a-half pass: detect kind-guarded appends to track list element union types
    # Pattern: if/elif p.kind == "something": list_var.append(p)
    # This records that list_var contains items of struct type for "something"
    list_element_unions: dict[str, list[str]] = {}
    for stmt in dict_walk({"_type": "Module", "body": stmts}):
        if is_type(stmt, ["If"]):
            # Check the test condition for kind checks
            kind_check = callbacks.is_kind_check(stmt.get("test"))
            if kind_check:
                checked_var, struct_name = kind_check
                # Look for append calls in the body
                for body_stmt in stmt.get("body", []):
                    if is_type(body_stmt, ["Expr"]) and is_type(body_stmt.get("value"), ["Call"]):
                        call = body_stmt.get("value", {})
                        func = call.get("func", {})
                        call_args = call.get("args", [])
                        if (
                            is_type(func, ["Attribute"])
                            and func.get("attr") == "append"
                            and is_type(func.get("value"), ["Name"])
                            and call_args
                            and is_type(call_args[0], ["Name"])
                            and call_args[0].get("id") == checked_var
                        ):
                            list_var = func.get("value", {}).get("id")
                            if list_var not in list_element_unions:
                                list_element_unions[list_var] = []
                            if struct_name not in list_element_unions[list_var]:
                                list_element_unions[list_var].append(struct_name)
    # Fourth pass: re-run assignment type inference to propagate types through chains
    # This handles cases like: pair = cmds[0]; needs = pair[1]
    # where pair's type depends on cmds, and needs' type depends on pair
    for _ in range(2):  # Run a couple iterations to handle multi-step chains
        for stmt in dict_walk({"_type": "Module", "body": stmts}):
            if is_type(stmt, ["Assign"]) and len(stmt.get("targets", [])) == 1:
                target = stmt.get("targets", [])[0]
                if is_type(target, ["Name"]):
                    var_name = target.get("id")
                    value = stmt.get("value", {})
                    if is_type(value, ["Subscript"]):
                        container_type: "Type" = InterfaceRef("any")
                        subscript_value = value.get("value", {})
                        if is_type(subscript_value, ["Name"]):
                            container_name = subscript_value.get("id")
                            if container_name in var_types:
                                container_type = var_types[container_name]
                        if isinstance(container_type, Slice):
                            var_types[var_name] = container_type.element
                        elif isinstance(container_type, Tuple):
                            slice_node = value.get("slice", {})
                            if is_type(slice_node, ["Constant"]) and isinstance(
                                slice_node.get("value"), int
                            ):
                                idx = slice_node.get("value")
                                if 0 <= idx and idx < len(container_type.elements):
                                    var_types[var_name] = container_type.elements[idx]
    # Fourth-and-a-half pass: re-process For loops now that assignments are typed
    # This catches cases like: for c in base[1:]: where base was typed in the second pass
    for stmt in dict_walk({"_type": "Module", "body": stmts}):
        if is_type(stmt, ["For"]):
            target = stmt.get("target", {})
            if is_type(target, ["Name"]):
                loop_var = target.get("id")
                # Skip if already typed (from First pass)
                if loop_var in var_types:
                    continue
                iter_node = stmt.get("iter", {})
                # Check for range() call - loop variable is INT
                if (
                    is_type(iter_node, ["Call"])
                    and is_type(iter_node.get("func"), ["Name"])
                    and iter_node.get("func", {}).get("id") == "range"
                ):
                    var_types[loop_var] = INT
                else:
                    iterable_type = callbacks.infer_iterable_type(iter_node, var_types)
                    if iterable_type == STRING:
                        var_types[loop_var] = RUNE
                    elif isinstance(iterable_type, Slice):
                        var_types[loop_var] = iterable_type.element
    # Fifth pass: unify types from if/else branches
    for stmt in dict_walk({"_type": "Module", "body": stmts}):
        if is_type(stmt, ["If"]) and stmt.get("orelse"):
            then_vars = collect_branch_var_types(stmt.get("body", []), var_types)
            else_vars = collect_branch_var_types(stmt.get("orelse", []), var_types)
            unified = unify_branch_types(then_vars, else_vars)
            for var, typ in unified.items():
                # Only update if not already set or currently generic
                if var not in var_types or var_types[var] == InterfaceRef("any"):
                    var_types[var] = typ
    # Sixth pass: variables assigned both None and typed value
    # For strings, use empty string as sentinel (not pointer)
    # For ints, use -1 as sentinel (simpler than pointers)
    for var_name in vars_assigned_none:
        if var_name in vars_concrete_type:
            concrete_type = vars_concrete_type[var_name]
            if concrete_type == STRING:
                # String with None -> just use string (empty = None)
                var_types[var_name] = STRING
            elif concrete_type == INT:
                # Int with None -> use sentinel (-1 = None)
                var_types[var_name] = INT
                sentinel_ints.add(var_name)
            elif hierarchy_root and concrete_type == InterfaceRef(hierarchy_root):
                # Node with None -> use Node interface (nilable in Go)
                var_types[var_name] = InterfaceRef(hierarchy_root)
            else:
                # Other types -> use Optional (pointer)
                var_types[var_name] = Optional(concrete_type)
    # Seventh pass: variables with multiple Node types (not assigned None)
    # These are variables assigned different Node subtypes in branches or sequentially
    # The unified Node type takes precedence over any single assignment's type
    hierarchy_root_iface = InterfaceRef(hierarchy_root) if hierarchy_root else None
    for var_name, concrete_type in vars_concrete_type.items():
        if var_name not in vars_assigned_none and hierarchy_root_iface and concrete_type == hierarchy_root_iface:
            var_types[var_name] = hierarchy_root_iface
    return var_types, tuple_vars, sentinel_ints, list_element_unions


@dataclass
class _ExprTypeCtx:
    """Context for compute_expr_types traversal."""

    symbols: "SymbolTable"
    current_class_name: str
    current_func_info: FuncInfo | None
    node_types: set[str]
    kind_to_struct: dict[str, str]
    kind_source_vars: dict[str, str]  # Maps kind var -> source node var
    narrowed_attr_paths: dict[tuple[str, ...], str]  # Maps attr path -> struct name


_EXPR_NODE_TYPES = frozenset(
    {
        "Constant",
        "Name",
        "Attribute",
        "Subscript",
        "Call",
        "BinOp",
        "Compare",
        "BoolOp",
        "UnaryOp",
        "IfExp",
        "List",
        "Dict",
        "Set",
        "Tuple",
        "JoinedStr",
        "FormattedValue",
    }
)


def _compute_expr_in_stmt(
    stmt: ASTNode, local_var_types: dict[str, "Type"], ctx: _ExprTypeCtx
) -> None:
    """Compute types for all expressions in a single statement."""
    from .context import TypeContext

    type_ctx = TypeContext(
        var_types=local_var_types,
        kind_source_vars=ctx.kind_source_vars,
        narrowed_attr_paths=ctx.narrowed_attr_paths,
    )
    for subnode in dict_walk(stmt):
        node_t = subnode.get("_type") if isinstance(subnode, dict) else None
        if node_t in _EXPR_NODE_TYPES:
            typ = infer_expr_type_from_ast(
                subnode,
                type_ctx,
                ctx.symbols,
                ctx.current_func_info,
                ctx.current_class_name,
                ctx.node_types,
            )
            subnode["_expr_type"] = typ


def _track_kind_sources(stmt: ASTNode, ctx: _ExprTypeCtx) -> None:
    """Track 'kind = node.kind' assignments for aliased kind checks."""
    if not is_type(stmt, ["Assign"]):
        return
    targets = stmt.get("targets", [])
    if len(targets) != 1:
        return
    target = targets[0]
    value = stmt.get("value", {})
    if (
        is_type(target, ["Name"])
        and is_type(value, ["Attribute"])
        and value.get("attr") == "kind"
        and is_type(value.get("value"), ["Name"])
    ):
        ctx.kind_source_vars[target.get("id")] = value.get("value", {}).get("id")


def _process_expr_stmts(
    stmt_list: list[ASTNode], local_var_types: dict[str, "Type"], ctx: _ExprTypeCtx
) -> None:
    """Process statements in order with local var_types context."""
    for stmt in stmt_list:
        stmt_type = stmt.get("_type") if isinstance(stmt, dict) else None
        # Track kind source vars before processing
        _track_kind_sources(stmt, ctx)
        if stmt_type == "If":
            _process_expr_if(stmt, local_var_types, ctx)
        elif stmt_type in ("For", "While", "With"):
            _compute_expr_in_stmt(stmt, local_var_types, ctx)
            _process_expr_stmts(stmt.get("body", []), local_var_types, ctx)
            _process_expr_stmts(stmt.get("orelse", []), local_var_types, ctx)
        elif stmt_type == "Try":
            _compute_expr_in_stmt(stmt, local_var_types, ctx)
            _process_expr_stmts(stmt.get("body", []), local_var_types, ctx)
            for handler in stmt.get("handlers", []):
                _process_expr_stmts(handler.get("body", []), local_var_types, ctx)
            _process_expr_stmts(stmt.get("orelse", []), local_var_types, ctx)
            _process_expr_stmts(stmt.get("finalbody", []), local_var_types, ctx)
        else:
            _compute_expr_in_stmt(stmt, local_var_types, ctx)


def _process_expr_if(stmt: ASTNode, local_var_types: dict[str, "Type"], ctx: _ExprTypeCtx) -> None:
    """Process if statement with type narrowing for isinstance/kind checks."""
    test = stmt.get("test", {})
    body = stmt.get("body", [])
    orelse = stmt.get("orelse", [])
    # Compute types in test expression first
    _compute_expr_in_stmt({"_type": "Expr", "value": test}, local_var_types, ctx)
    # Check for isinstance narrowing
    narrowing = extract_isinstance_or_chain(test, {})
    if narrowing:
        narrowed_var, type_names = narrowing
        if len(type_names) == 1 and narrowed_var in local_var_types:
            # Create copy with narrowed type for then-branch
            then_var_types = local_var_types.copy()
            type_name = type_names[0]
            if type_name in ctx.symbols.structs:
                then_var_types[narrowed_var] = Pointer(StructRef(type_name))
            elif type_name == "str":
                then_var_types[narrowed_var] = STRING
            elif type_name == "int":
                then_var_types[narrowed_var] = INT
            elif type_name == "bool":
                then_var_types[narrowed_var] = BOOL
            _process_expr_stmts(body, then_var_types, ctx)
            _process_expr_stmts(orelse, local_var_types, ctx)
            return
    # Check for kind check narrowing (x.kind == "value" or aliased kind == "value")
    kind_check = extract_kind_check(test, ctx.kind_to_struct, ctx.kind_source_vars)
    if kind_check:
        narrowed_var, struct_name = kind_check
        then_var_types = local_var_types.copy()
        then_var_types[narrowed_var] = Pointer(StructRef(struct_name))
        _process_expr_stmts(body, then_var_types, ctx)
        _process_expr_stmts(orelse, local_var_types, ctx)
        return
    # Check for attribute path narrowing (node.body.kind == "value")
    attr_kind_check = extract_attr_kind_check(test, ctx.kind_to_struct)
    if attr_kind_check:
        attr_path, struct_name = attr_kind_check
        ctx.narrowed_attr_paths[attr_path] = struct_name
        _process_expr_stmts(body, local_var_types, ctx)
        ctx.narrowed_attr_paths.pop(attr_path, None)
        _process_expr_stmts(orelse, local_var_types, ctx)
        return
    # No narrowing - use same var_types for both branches
    _process_expr_stmts(body, local_var_types, ctx)
    _process_expr_stmts(orelse, local_var_types, ctx)


def compute_expr_types(
    stmts: list[ASTNode],
    var_types: dict[str, "Type"],
    symbols: "SymbolTable",
    current_class_name: str,
    current_func_info: FuncInfo | None,
    node_types: set[str],
    kind_to_struct: dict[str, str] | None = None,
) -> None:
    """Compute types for all expressions in statements.

    Stores computed type directly in each AST node as '_expr_type' field.
    Processes statements in order, handling isinstance/kind narrowing in if-blocks.
    """
    if kind_to_struct is None:
        kind_to_struct = {}
    ctx = _ExprTypeCtx(
        symbols=symbols,
        current_class_name=current_class_name,
        current_func_info=current_func_info,
        node_types=node_types,
        kind_to_struct=kind_to_struct,
        kind_source_vars={},
        narrowed_attr_paths={},
    )
    _process_expr_stmts(stmts, var_types, ctx)
