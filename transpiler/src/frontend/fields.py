"""Phase 6: Field type collection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .ast_compat import ASTNode, dict_walk, is_type
from .collection import CollectionCallbacks
from ..ir import FieldInfo

if TYPE_CHECKING:
    from ..ir import StructInfo, SymbolTable


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
            typ = callbacks.py_type_to_ir(py_type, True)  # concrete_nodes=True for struct fields
            info.fields[field_name] = FieldInfo(name=field_name, typ=typ, py_name=field_name)
    # Collect fields from __init__
    for stmt in node.get("body", []):
        if is_type(stmt, ["FunctionDef"]) and stmt.get("name") == "__init__":
            collect_init_fields(stmt, info, callbacks)
    # Exception classes always need constructors for panic(NewXxx(...)) pattern
    if info.is_exception:
        info.needs_constructor = True
    # Build field-to-structs mapping for Node subclasses
    if info.is_node:
        for field_name in info.fields:
            if field_name not in symbols.field_to_structs:
                symbols.field_to_structs[field_name] = []
            if info.name not in symbols.field_to_structs[field_name]:
                symbols.field_to_structs[field_name].append(info.name)


def collect_fields(
    tree: ASTNode,
    symbols: SymbolTable,
    callbacks: CollectionCallbacks,
) -> None:
    """Pass 6: Collect struct fields from class definitions."""
    for node in tree.get("body", []):
        if is_type(node, ["ClassDef"]):
            collect_class_fields(node, symbols, callbacks)
