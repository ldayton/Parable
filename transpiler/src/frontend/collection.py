"""Collection utilities extracted from frontend.py."""
from __future__ import annotations

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..ir import StructInfo, SymbolTable


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
