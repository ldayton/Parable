"""Collection utilities extracted from frontend.py."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

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

    annotation_to_str: Callable[[ast.expr | None], str]
    py_type_to_ir: Callable[[str, bool], "Type"]
    py_return_type_to_ir: Callable[[str], "Type"]
    lower_expr: Callable[[ast.expr], "ir.Expr"]
    infer_type_from_value: Callable[[ast.expr, dict[str, str]], "Type"] | None = None
    extract_struct_name: Callable[["Type"], str | None] | None = None
    infer_container_type_from_ast: Callable[[ast.expr, dict[str, "Type"]], "Type"] | None = None
    is_len_call: Callable[[ast.expr], bool] | None = None
    is_kind_check: Callable[[ast.expr], tuple[str, str] | None] | None = None
    infer_call_return_type: Callable[[ast.Call], "Type"] | None = None
    infer_iterable_type: Callable[[ast.expr, dict[str, "Type"]], "Type"] | None = None
    infer_element_type_from_append_arg: Callable[[ast.expr, dict[str, "Type"]], "Type"] | None = (
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


def detect_mutated_params(node: ast.FunctionDef) -> set[str]:
    """Detect which parameters are mutated in the function body."""
    mutated = set()
    param_names = {a.arg for a in node.args.args if a.arg != "self"}
    for stmt in ast.walk(node):
        # param.append(...), param.extend(...), param.clear(), param.pop()
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
            if isinstance(call.func, ast.Attribute):
                if call.func.attr in ("append", "extend", "clear", "pop"):
                    if isinstance(call.func.value, ast.Name) and call.func.value.id in param_names:
                        mutated.add(call.func.value.id)
        # param[i] = ...
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Subscript):
                    if isinstance(target.value, ast.Name) and target.value.id in param_names:
                        mutated.add(target.value.id)
    return mutated


def get_base_name(base: ast.expr) -> str:
    """Extract base class name from AST node."""
    if isinstance(base, ast.Name):
        return base.id
    if isinstance(base, ast.Attribute):
        return base.attr
    return ""


def collect_class_names(tree: ast.Module, symbols: SymbolTable) -> None:
    """Pass 1: Collect all class names and their bases."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = [get_base_name(b) for b in node.bases]
            symbols.structs[node.name] = StructInfo(name=node.name, bases=bases)


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


def collect_constants(tree: ast.Module, symbols: SymbolTable) -> None:
    """Pass 5: Collect module-level and class-level constants."""
    # First, register overridden constants from type_overrides
    for const_name, (const_type, _) in MODULE_CONSTANTS.items():
        symbols.constants[const_name] = const_type
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id.isupper():
                # Skip if already registered via MODULE_CONSTANTS
                if target.id in MODULE_CONSTANTS:
                    continue
                # All-caps name = constant
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, int):
                    symbols.constants[target.id] = INT
                # Set literal constants (e.g., ASSIGNMENT_BUILTINS = {"alias", ...})
                elif isinstance(node.value, ast.Set):
                    symbols.constants[target.id] = Set(STRING)
                # Dict literal constants (e.g., ANSI_C_ESCAPES = {"a": 0x07, ...})
                elif isinstance(node.value, ast.Dict):
                    symbols.constants[target.id] = Map(STRING, INT)
        # Collect class-level constants (e.g., TokenType.EOF = 0)
        elif isinstance(node, ast.ClassDef):
            for stmt in node.body:
                if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                    target = stmt.targets[0]
                    if isinstance(target, ast.Name) and target.id.isupper():
                        if isinstance(stmt.value, ast.Constant) and isinstance(
                            stmt.value.value, int
                        ):
                            # Store as ClassName_CONST_NAME
                            const_name = f"{node.name}_{target.id}"
                            symbols.constants[const_name] = INT


def extract_func_info(
    node: ast.FunctionDef,
    callbacks: CollectionCallbacks,
    is_method: bool = False,
) -> FuncInfo:
    """Extract function signature information."""
    mutated_params = detect_mutated_params(node)
    params = []
    non_self_args = [a for a in node.args.args if a.arg != "self"]
    n_params = len(non_self_args)
    n_defaults = len(node.args.defaults) if node.args.defaults else 0
    for i, arg in enumerate(non_self_args):
        py_type = callbacks.annotation_to_str(arg.annotation) if arg.annotation else ""
        typ = callbacks.py_type_to_ir(py_type, False) if py_type else InterfaceRef("any")
        # Check for overrides first (takes precedence)
        override_key = (node.name, arg.arg)
        if override_key in PARAM_TYPE_OVERRIDES:
            typ = PARAM_TYPE_OVERRIDES[override_key]
        # Auto-wrap mutated slice params with Pointer
        elif arg.arg in mutated_params and isinstance(typ, Slice):
            typ = Pointer(typ)
        has_default = False
        default_value = None
        # Check if this param has a default
        if i >= n_params - n_defaults:
            has_default = True
            default_idx = i - (n_params - n_defaults)
            if node.args.defaults and default_idx < len(node.args.defaults):
                default_value = callbacks.lower_expr(node.args.defaults[default_idx])
        params.append(
            ParamInfo(name=arg.arg, typ=typ, has_default=has_default, default_value=default_value)
        )
    return_type = VOID
    if node.returns:
        py_return = callbacks.annotation_to_str(node.returns)
        return_type = callbacks.py_return_type_to_ir(py_return)
    # Apply return type overrides
    if node.name in RETURN_TYPE_OVERRIDES:
        return_type = RETURN_TYPE_OVERRIDES[node.name]
    return FuncInfo(
        name=node.name,
        params=params,
        return_type=return_type,
        is_method=is_method,
    )


def collect_class_methods(
    node: ast.ClassDef,
    symbols: SymbolTable,
    callbacks: CollectionCallbacks,
) -> None:
    """Collect method signatures for a class."""
    info = symbols.structs[node.name]
    for stmt in node.body:
        if isinstance(stmt, ast.FunctionDef):
            func_info = extract_func_info(stmt, callbacks, is_method=True)
            func_info.is_method = True
            func_info.receiver_type = node.name
            info.methods[stmt.name] = func_info


def collect_signatures(
    tree: ast.Module,
    symbols: SymbolTable,
    callbacks: CollectionCallbacks,
) -> None:
    """Pass 3: Collect function and method signatures."""
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            symbols.functions[node.name] = extract_func_info(node, callbacks)
        elif isinstance(node, ast.ClassDef):
            collect_class_methods(node, symbols, callbacks)


def collect_init_fields(
    init: ast.FunctionDef,
    info: StructInfo,
    callbacks: CollectionCallbacks,
) -> None:
    """Collect fields assigned in __init__."""
    param_types: dict[str, str] = {}
    # Record __init__ parameter order (excluding self) for constructor calls
    for arg in init.args.args:
        if arg.arg != "self":
            info.init_params.append(arg.arg)
            if arg.annotation:
                param_types[arg.arg] = callbacks.annotation_to_str(arg.annotation)
    # Track whether __init__ has computed initializations
    has_computed_init = False
    for stmt in ast.walk(init):
        if isinstance(stmt, ast.AnnAssign):
            if (
                isinstance(stmt.target, ast.Attribute)
                and isinstance(stmt.target.value, ast.Name)
                and stmt.target.value.id == "self"
            ):
                field_name = stmt.target.attr
                if field_name not in info.fields:
                    py_type = callbacks.annotation_to_str(stmt.annotation)
                    typ = callbacks.py_type_to_ir(py_type, True)  # concrete_nodes=True
                    # Apply field type overrides (keep for compatibility)
                    override_key = (info.name, field_name)
                    if override_key in FIELD_TYPE_OVERRIDES:
                        typ = FIELD_TYPE_OVERRIDES[override_key]
                    info.fields[field_name] = FieldInfo(
                        name=field_name, typ=typ, py_name=field_name
                    )
                # Check if value is computed (not just a param reference)
                if stmt.value is not None:
                    if not (isinstance(stmt.value, ast.Name) and stmt.value.id in info.init_params):
                        has_computed_init = True
        elif isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    field_name = target.attr
                    # Track param-to-field mapping: self.field = param
                    is_simple_param = (
                        isinstance(stmt.value, ast.Name) and stmt.value.id in info.init_params
                    )
                    # Track constant string assignments: self.kind = "operator"
                    is_const_str = isinstance(stmt.value, ast.Constant) and isinstance(
                        stmt.value.value, str
                    )
                    if is_simple_param:
                        info.param_to_field[stmt.value.id] = field_name
                    elif is_const_str:
                        info.const_fields[field_name] = stmt.value.value
                    else:
                        # Computed initialization - need constructor
                        has_computed_init = True
                    if field_name not in info.fields:
                        assert callbacks.infer_type_from_value is not None
                        typ = callbacks.infer_type_from_value(stmt.value, param_types)
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
    node: ast.ClassDef,
    symbols: SymbolTable,
    callbacks: CollectionCallbacks,
) -> None:
    """Collect fields from class body and __init__."""
    info = symbols.structs[node.name]
    # Collect class-level annotations
    for stmt in node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            field_name = stmt.target.id
            py_type = callbacks.annotation_to_str(stmt.annotation)
            typ = callbacks.py_type_to_ir(py_type, False)
            # Apply field type overrides
            override_key = (info.name, field_name)
            if override_key in FIELD_TYPE_OVERRIDES:
                typ = FIELD_TYPE_OVERRIDES[override_key]
            info.fields[field_name] = FieldInfo(name=field_name, typ=typ, py_name=field_name)
    # Collect fields from __init__
    for stmt in node.body:
        if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
            collect_init_fields(stmt, info, callbacks)
    # Exception classes always need constructors for panic(NewXxx(...)) pattern
    if info.is_exception:
        info.needs_constructor = True


def collect_fields(
    tree: ast.Module,
    symbols: SymbolTable,
    callbacks: CollectionCallbacks,
) -> None:
    """Pass 4: Collect struct fields from class definitions."""
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
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
    node: ast.expr,
    var_types: dict[str, "Type"],
    branch_vars: dict[str, "Type"],
) -> "Type":
    """Infer type of expression during branch analysis."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return STRING
        if isinstance(node.value, int) and not isinstance(node.value, bool):
            return INT
        if isinstance(node.value, bool):
            return BOOL
    if isinstance(node, ast.Name):
        if node.id in branch_vars:
            return branch_vars[node.id]
        if node.id in var_types:
            return var_types[node.id]
    if isinstance(node, ast.BinOp):
        left = infer_branch_expr_type(node.left, var_types, branch_vars)
        right = infer_branch_expr_type(node.right, var_types, branch_vars)
        if left == STRING or right == STRING:
            return STRING
        if left == INT or right == INT:
            return INT
    return InterfaceRef("any")


def collect_branch_var_types(
    stmts: list[ast.stmt],
    var_types: dict[str, "Type"],
) -> dict[str, "Type"]:
    """Collect variable types assigned in a list of statements (for branch analysis)."""
    branch_vars: dict[str, "Type"] = {}
    # Walk entire subtree to find all assignments (may be nested in for/while/etc)
    for stmt in ast.walk(ast.Module(body=stmts, type_ignores=[])):
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            target = stmt.targets[0]
            if isinstance(target, ast.Name):
                var_name = target.id
                # Infer type from value
                if isinstance(stmt.value, ast.Constant):
                    if isinstance(stmt.value.value, str):
                        branch_vars[var_name] = STRING
                    elif isinstance(stmt.value.value, int) and not isinstance(
                        stmt.value.value, bool
                    ):
                        branch_vars[var_name] = INT
                    elif isinstance(stmt.value.value, bool):
                        branch_vars[var_name] = BOOL
                elif isinstance(stmt.value, ast.BinOp):
                    # String concatenation -> STRING
                    if isinstance(stmt.value.op, ast.Add):
                        left_type = infer_branch_expr_type(stmt.value.left, var_types, branch_vars)
                        right_type = infer_branch_expr_type(
                            stmt.value.right, var_types, branch_vars
                        )
                        if left_type == STRING or right_type == STRING:
                            branch_vars[var_name] = STRING
                        elif left_type == INT or right_type == INT:
                            branch_vars[var_name] = INT
                elif isinstance(stmt.value, ast.Name):
                    # Assign from another variable
                    if stmt.value.id in var_types:
                        branch_vars[var_name] = var_types[stmt.value.id]
                    elif stmt.value.id in branch_vars:
                        branch_vars[var_name] = branch_vars[stmt.value.id]
                # Method calls (e.g., x.to_sexp() returns STRING)
                elif isinstance(stmt.value, ast.Call) and isinstance(
                    stmt.value.func, ast.Attribute
                ):
                    method = stmt.value.func.attr
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
    arg: ast.expr,
    var_types: dict[str, "Type"],
    symbols: SymbolTable,
    current_class_name: str,
    current_func_info: "FuncInfo | None",
    callbacks: CollectionCallbacks,
) -> "Type":
    """Infer slice element type from what's being appended."""
    # Constant literals
    if isinstance(arg, ast.Constant):
        if isinstance(arg.value, bool):
            return BOOL
        if isinstance(arg.value, int):
            return INT
        if isinstance(arg.value, str):
            return STRING
        if isinstance(arg.value, float):
            return FLOAT
    # Variable reference with known type (e.g., loop variable)
    if isinstance(arg, ast.Name):
        if arg.id in var_types:
            return var_types[arg.id]
        # Check function parameters
        if current_func_info:
            for p in current_func_info.params:
                if p.name == arg.id:
                    return p.typ
    # Field access: self.field or obj.field
    if isinstance(arg, ast.Attribute):
        if isinstance(arg.value, ast.Name):
            if arg.value.id == "self" and current_class_name:
                struct_info = symbols.structs.get(current_class_name)
                if struct_info:
                    field_info = struct_info.fields.get(arg.attr)
                    if field_info:
                        return field_info.typ
            elif arg.value.id in var_types:
                obj_type = var_types[arg.value.id]
                assert callbacks.extract_struct_name is not None
                struct_name = callbacks.extract_struct_name(obj_type)
                if struct_name and struct_name in symbols.structs:
                    field_info = symbols.structs[struct_name].fields.get(arg.attr)
                    if field_info:
                        return field_info.typ
    # Subscript: container[i] -> infer element type from container
    if isinstance(arg, ast.Subscript):
        assert callbacks.infer_container_type_from_ast is not None
        container_type = callbacks.infer_container_type_from_ast(arg.value, var_types)
        if container_type == STRING:
            return STRING  # string[i] in Python returns a string
        if isinstance(container_type, Slice):
            return container_type.element
    # Tuple literal: (a, b, ...) -> Tuple(type(a), type(b), ...)
    if isinstance(arg, ast.Tuple):
        elem_types = []
        for elt in arg.elts:
            elem_types.append(
                infer_element_type_from_append_arg(
                    elt, var_types, symbols, current_class_name, current_func_info, callbacks
                )
            )
        return Tuple(tuple(elem_types))
    # Method calls
    if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute):
        method = arg.func.attr
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
            if isinstance(arg.func.value, ast.Name):
                var = arg.func.value.id
                if var == "ctx":
                    return Pointer(StructRef("ParseContext"))
    # Function/constructor calls
    if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name):
        func_name = arg.func.id
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
    if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute):
        method_name = arg.func.attr
        # Handle self.method() calls directly using current class name
        # (can't use _infer_expr_type_from_ast here - _type_ctx not set yet)
        if isinstance(arg.func.value, ast.Name) and arg.func.value.id == "self":
            if current_class_name and current_class_name in symbols.structs:
                method_info = symbols.structs[current_class_name].methods.get(method_name)
                if method_info:
                    return method_info.return_type
        # Handle other obj.method() calls via var_types lookup
        elif isinstance(arg.func.value, ast.Name) and arg.func.value.id in var_types:
            obj_type = var_types[arg.func.value.id]
            assert callbacks.extract_struct_name is not None
            struct_name = callbacks.extract_struct_name(obj_type)
            if struct_name and struct_name in symbols.structs:
                method_info = symbols.structs[struct_name].methods.get(method_name)
                if method_info:
                    return method_info.return_type
    return InterfaceRef("any")


def collect_var_types(
    stmts: list[ast.stmt],
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
    for stmt in ast.walk(ast.Module(body=stmts, type_ignores=[])):
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            target = stmt.targets[0]
            if isinstance(target, ast.Name):
                var_name = target.id
                if var_name not in vars_all_types:
                    vars_all_types[var_name] = []
                # Check if assigning None
                if isinstance(stmt.value, ast.Constant) and stmt.value.value is None:
                    vars_assigned_none.add(var_name)
                # Check if assigning typed value
                elif isinstance(stmt.value, ast.Constant):
                    if isinstance(stmt.value.value, int) and not isinstance(stmt.value.value, bool):
                        vars_all_types[var_name].append(INT)
                    elif isinstance(stmt.value.value, str):
                        vars_all_types[var_name].append(STRING)
                elif isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name):
                    # int(...) call
                    if stmt.value.func.id == "int":
                        vars_all_types[var_name].append(INT)
                    elif stmt.value.func.id == "str":
                        vars_all_types[var_name].append(STRING)
                # String method calls: x = "".join(...), etc.
                elif isinstance(stmt.value, ast.Call) and isinstance(
                    stmt.value.func, ast.Attribute
                ):
                    method = stmt.value.func.attr
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
                        isinstance(stmt.value.func.value, ast.Name)
                        and stmt.value.func.value.id == "self"
                    ):
                        if current_class_name and current_class_name in symbols.structs:
                            method_info = symbols.structs[current_class_name].methods.get(method)
                            if method_info:
                                vars_all_types[var_name].append(method_info.return_type)
                # Assignment from known variable: varfd = varname
                elif isinstance(stmt.value, ast.Name):
                    if stmt.value.id in vars_all_types and vars_all_types[stmt.value.id]:
                        vars_all_types[var_name].extend(vars_all_types[stmt.value.id])
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
    for stmt in ast.walk(ast.Module(body=stmts, type_ignores=[])):
        if isinstance(stmt, ast.For):
            if isinstance(stmt.target, ast.Name):
                loop_var = stmt.target.id
                # Check for range() call - loop variable is INT
                if (
                    isinstance(stmt.iter, ast.Call)
                    and isinstance(stmt.iter.func, ast.Name)
                    and stmt.iter.func.id == "range"
                ):
                    var_types[loop_var] = INT
                else:
                    assert callbacks.infer_iterable_type is not None
                    iterable_type = callbacks.infer_iterable_type(stmt.iter, var_types)
                    if isinstance(iterable_type, Slice):
                        var_types[loop_var] = iterable_type.element
            elif isinstance(stmt.target, ast.Tuple) and len(stmt.target.elts) == 2:
                if isinstance(stmt.target.elts[1], ast.Name):
                    loop_var = stmt.target.elts[1].id
                    assert callbacks.infer_iterable_type is not None
                    iterable_type = callbacks.infer_iterable_type(stmt.iter, var_types)
                    if isinstance(iterable_type, Slice):
                        var_types[loop_var] = iterable_type.element
    # Second pass: infer variable types from assignments (runs first to populate var_types)
    for stmt in ast.walk(ast.Module(body=stmts, type_ignores=[])):
        # Infer from annotated assignments
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            py_type = callbacks.annotation_to_str(stmt.annotation)
            typ = callbacks.py_type_to_ir(py_type, False)
            # int | None = None uses -1 sentinel, so track as INT not Optional
            if (
                isinstance(typ, Optional)
                and typ.inner == INT
                and stmt.value
                and isinstance(stmt.value, ast.Constant)
                and stmt.value.value is None
            ):
                var_types[stmt.target.id] = INT
                sentinel_ints.add(stmt.target.id)
            else:
                var_types[stmt.target.id] = typ
        # Infer from return statements: if returning var and return type is known
        if isinstance(stmt, ast.Return) and stmt.value:
            if isinstance(stmt.value, ast.Name):
                var_name = stmt.value.id
                if current_func_info and isinstance(current_func_info.return_type, Slice):
                    var_types[var_name] = current_func_info.return_type
        # Infer from field assignments: self.field = var -> var has field's type
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            target = stmt.targets[0]
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                if target.value.id == "self" and isinstance(stmt.value, ast.Name):
                    var_name = stmt.value.id
                    field_name = target.attr
                    # Look up field type from current class
                    if current_class_name in symbols.structs:
                        struct_info = symbols.structs[current_class_name]
                        field_info = struct_info.fields.get(field_name)
                        if field_info:
                            var_types[var_name] = field_info.typ
            # Infer from method call assignments: var = self.method() -> var has method's return type
            if isinstance(target, ast.Name) and isinstance(stmt.value, ast.Call):
                var_name = target.id
                call = stmt.value
                if isinstance(call.func, ast.Attribute):
                    method_name = call.func.attr
                    # Get object type
                    if isinstance(call.func.value, ast.Name):
                        obj_name = call.func.value.id
                        if obj_name == "self" and current_class_name:
                            struct_info = symbols.structs.get(current_class_name)
                            if struct_info:
                                method_info = struct_info.methods.get(method_name)
                                if method_info:
                                    var_types[var_name] = method_info.return_type
            # Infer from literal assignments
            if isinstance(target, ast.Name):
                var_name = target.id
                if isinstance(stmt.value, ast.Constant):
                    if isinstance(stmt.value.value, bool):
                        var_types[var_name] = BOOL
                    elif isinstance(stmt.value.value, int):
                        var_types[var_name] = INT
                    elif isinstance(stmt.value.value, str):
                        var_types[var_name] = STRING
                elif isinstance(stmt.value, ast.Name):
                    if stmt.value.id in ("True", "False"):
                        var_types[var_name] = BOOL
                # Comparisons and bool ops always produce bool
                elif isinstance(stmt.value, (ast.Compare, ast.BoolOp)):
                    var_types[var_name] = BOOL
                # BinOp with arithmetic operators produce int
                elif isinstance(stmt.value, ast.BinOp):
                    if isinstance(stmt.value.op, (ast.Sub, ast.Mult, ast.FloorDiv, ast.Mod)):
                        var_types[var_name] = INT
                    elif isinstance(stmt.value.op, ast.Add):
                        # Could be int or string - check operands
                        assert callbacks.is_len_call is not None
                        if callbacks.is_len_call(stmt.value.left) or callbacks.is_len_call(
                            stmt.value.right
                        ):
                            var_types[var_name] = INT
                # Infer from list/dict literals - element type inferred later from appends
                elif isinstance(stmt.value, ast.List):
                    var_types[var_name] = Slice(InterfaceRef("any"))
                elif isinstance(stmt.value, ast.Dict):
                    var_types[var_name] = Map(STRING, InterfaceRef("any"))
                # Infer from field access: var = obj.field -> var has field's type
                elif isinstance(stmt.value, ast.Attribute):
                    # Look up field type using local var_types (not self._type_ctx)
                    attr_node = stmt.value
                    field_name = attr_node.attr
                    obj_type: "Type" = InterfaceRef("any")
                    if isinstance(attr_node.value, ast.Name):
                        obj_name = attr_node.value.id
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
                elif isinstance(stmt.value, ast.Subscript):
                    container_type: "Type" = InterfaceRef("any")
                    if isinstance(stmt.value.value, ast.Name):
                        container_name = stmt.value.value.id
                        if container_name in var_types:
                            container_type = var_types[container_name]
                    # Also handle field access: self.field[i]
                    elif isinstance(stmt.value.value, ast.Attribute):
                        attr = stmt.value.value
                        if isinstance(attr.value, ast.Name):
                            if attr.value.id == "self" and current_class_name:
                                struct_info = symbols.structs.get(current_class_name)
                                if struct_info:
                                    field_info = struct_info.fields.get(attr.attr)
                                    if field_info:
                                        container_type = field_info.typ
                            elif attr.value.id in var_types:
                                obj_type = var_types[attr.value.id]
                                assert callbacks.extract_struct_name is not None
                                struct_name = callbacks.extract_struct_name(obj_type)
                                if struct_name and struct_name in symbols.structs:
                                    field_info = symbols.structs[struct_name].fields.get(attr.attr)
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
                        if isinstance(stmt.value.slice, ast.Constant) and isinstance(
                            stmt.value.slice.value, int
                        ):
                            idx = stmt.value.slice.value
                            if 0 <= idx < len(container_type.elements):
                                var_types[var_name] = container_type.elements[idx]
                # Infer from method calls: var = obj.method() -> method return type
                elif isinstance(stmt.value, ast.Call) and isinstance(
                    stmt.value.func, ast.Attribute
                ):
                    method_name = stmt.value.func.attr
                    obj_type: "Type" = InterfaceRef("any")
                    if isinstance(stmt.value.func.value, ast.Name):
                        obj_name = stmt.value.func.value.id
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
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            target = stmt.targets[0]
            if isinstance(target, ast.Tuple) and isinstance(stmt.value, ast.Call):
                # Get return type of the called function/method
                assert callbacks.infer_call_return_type is not None
                ret_type = callbacks.infer_call_return_type(stmt.value)
                if isinstance(ret_type, Tuple):
                    for i, elt in enumerate(target.elts):
                        if isinstance(elt, ast.Name) and i < len(ret_type.elements):
                            var_types[elt.id] = ret_type.elements[i]
            # Handle single var = tuple-returning func (will be expanded to synthetic vars)
            elif isinstance(target, ast.Name) and isinstance(stmt.value, ast.Call):
                assert callbacks.infer_call_return_type is not None
                ret_type = callbacks.infer_call_return_type(stmt.value)
                if isinstance(ret_type, Tuple) and len(ret_type.elements) > 1:
                    base_name = target.id
                    synthetic_names = [f"{base_name}{i}" for i in range(len(ret_type.elements))]
                    tuple_vars[base_name] = synthetic_names
                    for i, elem_type in enumerate(ret_type.elements):
                        var_types[f"{base_name}{i}"] = elem_type
                # Handle constructor calls: var = ClassName()
                elif isinstance(stmt.value.func, ast.Name):
                    class_name = stmt.value.func.id
                    if class_name in symbols.structs:
                        var_types[target.id] = Pointer(StructRef(class_name))
                    # Handle free function calls: var = func()
                    elif class_name in symbols.functions:
                        var_types[target.id] = symbols.functions[class_name].return_type
                    # Handle builtin calls: bytearray(), list(), dict(), etc.
                    elif class_name == "bytearray":
                        var_types[target.id] = Slice(BYTE)
                    elif class_name == "list":
                        var_types[target.id] = Slice(InterfaceRef("any"))
                    elif class_name == "dict":
                        var_types[target.id] = Map(InterfaceRef("any"), InterfaceRef("any"))
    # Third pass: infer types from append() calls (after all variable types are collected)
    # Note: don't overwrite already-known specific slice types (e.g., bytearray -> []byte)
    for stmt in ast.walk(ast.Module(body=stmts, type_ignores=[])):
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
            if isinstance(call.func, ast.Attribute) and call.func.attr == "append":
                if isinstance(call.func.value, ast.Name) and call.args:
                    var_name = call.func.value.id
                    # Don't overwrite already-known specific slice types (e.g., bytearray)
                    # But DO infer if current type is generic Slice(any)
                    if var_name in var_types and isinstance(var_types[var_name], Slice):
                        current_elem = var_types[var_name].element
                        if current_elem != InterfaceRef("any"):
                            continue  # Skip - already has specific element type
                    assert callbacks.infer_element_type_from_append_arg is not None
                    elem_type = callbacks.infer_element_type_from_append_arg(
                        call.args[0], var_types
                    )
                    if elem_type != InterfaceRef("any"):
                        var_types[var_name] = Slice(elem_type)
    # Third-and-a-half pass: detect kind-guarded appends to track list element union types
    # Pattern: if/elif p.kind == "something": list_var.append(p)
    # This records that list_var contains items of struct type for "something"
    list_element_unions: dict[str, list[str]] = {}
    for stmt in ast.walk(ast.Module(body=stmts, type_ignores=[])):
        if isinstance(stmt, ast.If):
            # Check the test condition for kind checks
            assert callbacks.is_kind_check is not None
            kind_check = callbacks.is_kind_check(stmt.test)
            if kind_check:
                checked_var, struct_name = kind_check
                # Look for append calls in the body
                for body_stmt in stmt.body:
                    if isinstance(body_stmt, ast.Expr) and isinstance(body_stmt.value, ast.Call):
                        call = body_stmt.value
                        if (
                            isinstance(call.func, ast.Attribute)
                            and call.func.attr == "append"
                            and isinstance(call.func.value, ast.Name)
                            and call.args
                            and isinstance(call.args[0], ast.Name)
                            and call.args[0].id == checked_var
                        ):
                            list_var = call.func.value.id
                            if list_var not in list_element_unions:
                                list_element_unions[list_var] = []
                            if struct_name not in list_element_unions[list_var]:
                                list_element_unions[list_var].append(struct_name)
    # Fourth pass: re-run assignment type inference to propagate types through chains
    # This handles cases like: pair = cmds[0]; needs = pair[1]
    # where pair's type depends on cmds, and needs' type depends on pair
    for _ in range(2):  # Run a couple iterations to handle multi-step chains
        for stmt in ast.walk(ast.Module(body=stmts, type_ignores=[])):
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                target = stmt.targets[0]
                if isinstance(target, ast.Name):
                    var_name = target.id
                    if isinstance(stmt.value, ast.Subscript):
                        container_type: "Type" = InterfaceRef("any")
                        if isinstance(stmt.value.value, ast.Name):
                            container_name = stmt.value.value.id
                            if container_name in var_types:
                                container_type = var_types[container_name]
                        if isinstance(container_type, Slice):
                            var_types[var_name] = container_type.element
                        elif isinstance(container_type, Tuple):
                            if isinstance(stmt.value.slice, ast.Constant) and isinstance(
                                stmt.value.slice.value, int
                            ):
                                idx = stmt.value.slice.value
                                if 0 <= idx < len(container_type.elements):
                                    var_types[var_name] = container_type.elements[idx]
    # Fifth pass: unify types from if/else branches
    for stmt in ast.walk(ast.Module(body=stmts, type_ignores=[])):
        if isinstance(stmt, ast.If) and stmt.orelse:
            then_vars = collect_branch_var_types(stmt.body, var_types)
            else_vars = collect_branch_var_types(stmt.orelse, var_types)
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
