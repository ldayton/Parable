"""Collection utilities extracted from frontend.py."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from .ast_compat import ASTNode, is_type
from ..ir import (
    INT,
    Map,
    Set,
    STRING,
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
    for node in tree.get("body", []):
        if is_type(node, ["Assign"]) and len(node.get("targets", [])) == 1:
            target = node.get("targets", [])[0]
            if is_type(target, ["Name"]) and target.get("id", "").isupper():
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
