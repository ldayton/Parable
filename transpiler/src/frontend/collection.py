"""Collection utilities extracted from frontend.py."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from .ast_compat import ASTNode, dict_walk, is_type, node_type
from . import type_inference
from ..ir import (
    BOOL,
    BYTE,
    FLOAT,
    INT,
    VOID,
    FieldInfo,
    FuncInfo,
    InterfaceRef,
    Map,
    Optional,
    ParamInfo,
    Pointer,
    Set,
    Slice,
    STRING,
    StructRef,
    StructInfo,
    Tuple,
)
from ..type_overrides import (
    FIELD_TYPE_OVERRIDES,
    MODULE_CONSTANTS,
    PARAM_TYPE_OVERRIDES,
    RETURN_TYPE_OVERRIDES,
)

if TYPE_CHECKING:
    from .. import ir
    from ..ir import SymbolTable, Type


@dataclass
class CollectionCallbacks:
    """Callbacks for collection phase that need lowering/type conversion."""

    annotation_to_str: Callable[[ASTNode | None], str]
    py_type_to_ir: Callable[[str, bool], "Type"]
    py_return_type_to_ir: Callable[[str], "Type"]
    lower_expr: Callable[[ASTNode], "ir.Expr"]
    infer_type_from_value: Callable[[ASTNode, dict[str, str]], "Type"] | None = None
    extract_struct_name: Callable[["Type"], str | None] | None = None
    infer_container_type_from_ast: Callable[[ASTNode, dict[str, "Type"]], "Type"] | None = None
    is_len_call: Callable[[ASTNode], bool] | None = None
    is_kind_check: Callable[[ASTNode], tuple[str, str] | None] | None = None
    infer_call_return_type: Callable[[ASTNode], "Type"] | None = None
    infer_iterable_type: Callable[[ASTNode, dict[str, "Type"]], "Type"] | None = None
    infer_element_type_from_append_arg: Callable[[ASTNode, dict[str, "Type"]], "Type"] | None = (
        None
    )


def is_exception_subclass(name: str, symbols: SymbolTable) -> bool:
    """Check if a class is an Exception subclass (directly or transitively)."""
    if name == "Exception":
        return True
    info = symbols.structs.get(name)
    if not info:
        return False
    return any(is_exception_subclass(base, symbols) for base in info.bases)


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


def mark_node_subclasses(symbols: SymbolTable, node_types: set[str]) -> None:
    """Pass 2: Mark classes that inherit from Node."""
    for name, info in symbols.structs.items():
        info.is_node = type_inference.is_node_subclass(name, symbols)
        if info.is_node:
            node_types.add(name)


def mark_exception_subclasses(symbols: SymbolTable) -> None:
    """Pass 2b: Mark classes that inherit from Exception."""
    for name, info in symbols.structs.items():
        info.is_exception = is_exception_subclass(name, symbols)


def build_kind_mapping(
    symbols: SymbolTable,
    kind_to_struct: dict[str, str],
    kind_to_class: dict[str, str],
) -> None:
    """Build kind -> struct/class mappings from const_fields["kind"] values."""
    for name, info in symbols.structs.items():
        if "kind" in info.const_fields:
            kind_value = info.const_fields["kind"]
            kind_to_struct[kind_value] = name
            kind_to_class[kind_value] = name


def collect_constants(tree: ASTNode, symbols: SymbolTable) -> None:
    """Pass 5: Collect module-level and class-level constants."""
    # First, register overridden constants from type_overrides
    for const_name, (const_type, _) in MODULE_CONSTANTS.items():
        symbols.constants[const_name] = const_type
    for node in tree.get("body", []):
        if is_type(node, ["Assign"]) and len(node.get("targets", [])) == 1:
            target = node.get("targets", [])[0]
            if is_type(target, ["Name"]) and target.get("id", "").isupper():
                # Skip if already registered via MODULE_CONSTANTS
                if target.get("id") in MODULE_CONSTANTS:
                    continue
                # All-caps name = constant
                value = node.get("value", {})
                if is_type(value, ["Constant"]) and isinstance(value.get("value"), int):
                    symbols.constants[target.get("id")] = INT
                # Set literal constants (e.g., ASSIGNMENT_BUILTINS = {"alias", ...})
                elif is_type(value, ["Set"]):
                    symbols.constants[target.get("id")] = Set(STRING)
                # Dict literal constants (e.g., ANSI_C_ESCAPES = {"a": 0x07, ...})
                elif is_type(value, ["Dict"]):
                    symbols.constants[target.get("id")] = Map(STRING, INT)
        # Collect class-level constants (e.g., TokenType.EOF = 0)
        elif is_type(node, ["ClassDef"]):
            for stmt in node.get("body", []):
                if is_type(stmt, ["Assign"]) and len(stmt.get("targets", [])) == 1:
                    target = stmt.get("targets", [])[0]
                    if is_type(target, ["Name"]) and target.get("id", "").isupper():
                        value = stmt.get("value", {})
                        if is_type(value, ["Constant"]) and isinstance(value.get("value"), int):
                            # Store as ClassName_CONST_NAME
                            const_name = f"{node.get('name')}_{target.get('id')}"
                            symbols.constants[const_name] = INT


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
        # Check for overrides first (takes precedence)
        override_key = (node.get("name"), arg.get("arg"))
        if override_key in PARAM_TYPE_OVERRIDES:
            typ = PARAM_TYPE_OVERRIDES[override_key]
        # Auto-wrap mutated slice params with Pointer
        elif arg.get("arg") in mutated_params and isinstance(typ, Slice):
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


def collect_signatures(
    tree: ASTNode,
    symbols: SymbolTable,
    callbacks: CollectionCallbacks,
) -> None:
    """Pass 3: Collect function and method signatures."""
    for node in tree.get("body", []):
        if is_type(node, ["FunctionDef"]):
            symbols.functions[node.get("name")] = extract_func_info(node, callbacks)
        elif is_type(node, ["ClassDef"]):
            collect_class_methods(node, symbols, callbacks)


def collect_init_fields(
    init: ASTNode,
    info: StructInfo,
    callbacks: CollectionCallbacks,
) -> None:
    """Collect fields assigned in __init__."""
    param_types: dict[str, str] = {}
    # Record __init__ parameter order (excluding self) for constructor calls
    args = init.get("args", {})
    args_list = args.get("args", [])
    for arg in args_list:
        if arg.get("arg") != "self":
            info.init_params.append(arg.get("arg"))
            if arg.get("annotation"):
                param_types[arg.get("arg")] = callbacks.annotation_to_str(arg.get("annotation"))
    # Track whether __init__ has computed initializations
    has_computed_init = False
    for stmt in dict_walk(init):
        if is_type(stmt, ["AnnAssign"]):
            target = stmt.get("target", {})
            if (
                is_type(target, ["Attribute"])
                and is_type(target.get("value"), ["Name"])
                and target.get("value", {}).get("id") == "self"
            ):
                field_name = target.get("attr")
                if field_name not in info.fields:
                    py_type = callbacks.annotation_to_str(stmt.get("annotation"))
                    typ = callbacks.py_type_to_ir(py_type, True)  # concrete_nodes=True
                    # Apply field type overrides (keep for compatibility)
                    override_key = (info.name, field_name)
                    if override_key in FIELD_TYPE_OVERRIDES:
                        typ = FIELD_TYPE_OVERRIDES[override_key]
                    info.fields[field_name] = FieldInfo(
                        name=field_name, typ=typ, py_name=field_name
                    )
                # Check if value is computed (not just a param reference)
                value = stmt.get("value")
                if value is not None:
                    if not (is_type(value, ["Name"]) and value.get("id") in info.init_params):
                        has_computed_init = True
        elif is_type(stmt, ["Assign"]):
            for target in stmt.get("targets", []):
                if (
                    is_type(target, ["Attribute"])
                    and is_type(target.get("value"), ["Name"])
                    and target.get("value", {}).get("id") == "self"
                ):
                    field_name = target.get("attr")
                    value = stmt.get("value", {})
                    # Track param-to-field mapping: self.field = param
                    is_simple_param = (
                        is_type(value, ["Name"]) and value.get("id") in info.init_params
                    )
                    # Track constant string assignments: self.kind = "operator"
                    is_const_str = is_type(value, ["Constant"]) and isinstance(
                        value.get("value"), str
                    )
                    if is_simple_param:
                        info.param_to_field[value.get("id")] = field_name
                    elif is_const_str:
                        info.const_fields[field_name] = value.get("value")
                    else:
                        # Computed initialization - need constructor
                        has_computed_init = True
                    if field_name not in info.fields:
                        assert callbacks.infer_type_from_value is not None
                        typ = callbacks.infer_type_from_value(value, param_types)
                        # Apply field type overrides
                        override_key = (info.name, field_name)
                        if override_key in FIELD_TYPE_OVERRIDES:
                            typ = FIELD_TYPE_OVERRIDES[override_key]
                        info.fields[field_name] = FieldInfo(
                            name=field_name, typ=typ, py_name=field_name
                        )
    # Flag if constructor is needed - only for structs that critically need it
    # (Parser, Lexer need computed Length, nested constructors, back-references)
    NEEDS_CONSTRUCTOR = {"Parser", "Lexer", "ContextStack", "QuoteState", "ParseContext"}
    if has_computed_init and info.name in NEEDS_CONSTRUCTOR:
        info.needs_constructor = True


def collect_class_fields(
    node: ASTNode,
    symbols: SymbolTable,
    callbacks: CollectionCallbacks,
) -> None:
    """Collect fields from class body and __init__."""
    info = symbols.structs[node.get("name")]
    # Collect class-level annotations
    for stmt in node.get("body", []):
        if is_type(stmt, ["AnnAssign"]) and is_type(stmt.get("target"), ["Name"]):
            target = stmt.get("target", {})
            field_name = target.get("id")
            py_type = callbacks.annotation_to_str(stmt.get("annotation"))
            typ = callbacks.py_type_to_ir(py_type, False)
            # Apply field type overrides
            override_key = (info.name, field_name)
            if override_key in FIELD_TYPE_OVERRIDES:
                typ = FIELD_TYPE_OVERRIDES[override_key]
            info.fields[field_name] = FieldInfo(name=field_name, typ=typ, py_name=field_name)
    # Collect fields from __init__
    for stmt in node.get("body", []):
        if is_type(stmt, ["FunctionDef"]) and stmt.get("name") == "__init__":
            collect_init_fields(stmt, info, callbacks)
    # Exception classes always need constructors for panic(NewXxx(...)) pattern
    if info.is_exception:
        info.needs_constructor = True


def collect_fields(
    tree: ASTNode,
    symbols: SymbolTable,
    callbacks: CollectionCallbacks,
) -> None:
    """Pass 4: Collect struct fields from class definitions."""
    for node in tree.get("body", []):
        if is_type(node, ["ClassDef"]):
            collect_class_fields(node, symbols, callbacks)


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
                        left_type = infer_branch_expr_type(value.get("left"), var_types, branch_vars)
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
    symbols: SymbolTable,
    current_class_name: str,
    current_func_info: "FuncInfo | None",
    callbacks: CollectionCallbacks,
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
                assert callbacks.extract_struct_name is not None
                struct_name = callbacks.extract_struct_name(obj_type)
                if struct_name and struct_name in symbols.structs:
                    field_info = symbols.structs[struct_name].fields.get(arg.get("attr"))
                    if field_info:
                        return field_info.typ
    # Subscript: container[i] -> infer element type from container
    if is_type(arg, ["Subscript"]):
        assert callbacks.infer_container_type_from_ast is not None
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
                    elt, var_types, symbols, current_class_name, current_func_info, callbacks
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
                return InterfaceRef("Node")
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
            assert callbacks.extract_struct_name is not None
            struct_name = callbacks.extract_struct_name(obj_type)
            if struct_name and struct_name in symbols.structs:
                method_info = symbols.structs[struct_name].methods.get(method_name)
                if method_info:
                    return method_info.return_type
    return InterfaceRef("any")


def collect_var_types(
    stmts: list[ASTNode],
    symbols: SymbolTable,
    current_class_name: str,
    current_func_info: "FuncInfo | None",
    node_types: set[str],
    callbacks: CollectionCallbacks,
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
            all_node = all(
                t == InterfaceRef("Node")
                or t == StructRef("Node")
                or (
                    isinstance(t, Pointer)
                    and isinstance(t.target, StructRef)
                    and t.target.name in node_types
                )
                for t in unique_types
            )
            if all_node:
                vars_concrete_type[var_name] = InterfaceRef("Node")
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
                    assert callbacks.infer_iterable_type is not None
                    iterable_type = callbacks.infer_iterable_type(iter_node, var_types)
                    if isinstance(iterable_type, Slice):
                        var_types[loop_var] = iterable_type.element
            elif is_type(target, ["Tuple"]) and len(target.get("elts", [])) == 2:
                elts = target.get("elts", [])
                if is_type(elts[1], ["Name"]):
                    loop_var = elts[1].get("id")
                    assert callbacks.infer_iterable_type is not None
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
                        assert callbacks.is_len_call is not None
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
                elif is_type(value, ["Attribute"]):
                    # Look up field type using local var_types (not self._type_ctx)
                    attr_node = value
                    field_name = attr_node.get("attr")
                    obj_type: "Type" = InterfaceRef("any")
                    attr_value = attr_node.get("value", {})
                    if is_type(attr_value, ["Name"]):
                        obj_name = attr_value.get("id")
                        if obj_name == "self" and current_class_name:
                            obj_type = Pointer(StructRef(current_class_name))
                        elif obj_name in var_types:
                            obj_type = var_types[obj_name]
                    assert callbacks.extract_struct_name is not None
                    struct_name = callbacks.extract_struct_name(obj_type)
                    if struct_name and struct_name in symbols.structs:
                        field_info = symbols.structs[struct_name].fields.get(field_name)
                        if field_info:
                            var_types[var_name] = field_info.typ
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
                                assert callbacks.extract_struct_name is not None
                                struct_name = callbacks.extract_struct_name(obj_type)
                                if struct_name and struct_name in symbols.structs:
                                    field_info = symbols.structs[struct_name].fields.get(attr.get("attr"))
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
                    assert callbacks.extract_struct_name is not None
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
                assert callbacks.infer_call_return_type is not None
                ret_type = callbacks.infer_call_return_type(value)
                if isinstance(ret_type, Tuple):
                    for i, elt in enumerate(target.get("elts", [])):
                        if is_type(elt, ["Name"]) and i < len(ret_type.elements):
                            var_types[elt.get("id")] = ret_type.elements[i]
            # Handle single var = tuple-returning func (will be expanded to synthetic vars)
            elif is_type(target, ["Name"]) and is_type(value, ["Call"]):
                assert callbacks.infer_call_return_type is not None
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
                    assert callbacks.infer_element_type_from_append_arg is not None
                    elem_type = callbacks.infer_element_type_from_append_arg(
                        call_args[0], var_types
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
            assert callbacks.is_kind_check is not None
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
            elif concrete_type == InterfaceRef("Node"):
                # Node with None -> use Node interface (nilable in Go)
                var_types[var_name] = InterfaceRef("Node")
            else:
                # Other types -> use Optional (pointer)
                var_types[var_name] = Optional(concrete_type)
    # Seventh pass: variables with multiple Node types (not assigned None)
    # These are variables assigned different Node subtypes in branches or sequentially
    # The unified Node type takes precedence over any single assignment's type
    for var_name, concrete_type in vars_concrete_type.items():
        if var_name not in vars_assigned_none and concrete_type == InterfaceRef("Node"):
            var_types[var_name] = InterfaceRef("Node")
    return var_types, tuple_vars, sentinel_ints, list_element_unions
