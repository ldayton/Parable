"""Collection utilities extracted from frontend.py."""
from __future__ import annotations

import ast
from typing import TYPE_CHECKING, Callable

from . import type_inference
from ..ir import INT, Map, Set, STRING, StructInfo
from ..type_overrides import MODULE_CONSTANTS

if TYPE_CHECKING:
    from ..ir import SymbolTable


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
                        if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, int):
                            # Store as ClassName_CONST_NAME
                            const_name = f"{node.name}_{target.id}"
                            symbols.constants[const_name] = INT
