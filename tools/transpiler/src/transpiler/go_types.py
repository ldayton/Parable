"""Type definitions for Go transpiler."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field


@dataclass
class ScopeInfo:
    """Information about a scope in the scope tree."""

    id: int
    parent: int | None  # None for function scope (root)
    depth: int  # 0 for function scope


@dataclass
class VarInfo:
    """Information about a variable's usage across scopes."""

    name: str
    go_type: str
    assign_scopes: set[int] = field(default_factory=set)  # All scope IDs where assigned
    read_scopes: set[int] = field(default_factory=set)  # Scope IDs where read
    first_value: ast.expr | None = None  # First assigned value (for type inference)


@dataclass
class FieldInfo:
    """Information about a struct field."""

    name: str
    py_type: str  # Original Python type annotation
    go_type: str  # Resolved Go type


@dataclass
class ParamInfo:
    """Information about a function parameter."""

    name: str
    py_type: str
    go_type: str
    default: ast.expr | None = None


@dataclass
class FuncInfo:
    """Information about a function or method."""

    name: str
    params: list[ParamInfo]
    return_type: str  # Go type
    is_method: bool = False
    receiver_type: str = ""  # For methods, the type that owns this method


@dataclass
class ClassInfo:
    """Information about a class/struct."""

    name: str
    bases: list[str]
    fields: dict[str, FieldInfo] = field(default_factory=dict)
    methods: dict[str, FuncInfo] = field(default_factory=dict)
    is_node: bool = False  # True if this is a Node subclass
    constants: dict[str, int | str] = field(default_factory=dict)  # Class-level constants


class SymbolTable:
    """Symbol table for type resolution."""

    def __init__(self):
        self.classes: dict[str, ClassInfo] = {}
        self.functions: dict[str, FuncInfo] = {}
        self.constants: dict[str, str] = {}  # name -> Go type

    def is_node_subclass(self, class_name: str) -> bool:
        """Check if a class is a Node subclass (directly or transitively)."""
        if class_name == "Node":
            return True
        info = self.classes.get(class_name)
        if not info:
            return False
        for base in info.bases:
            if self.is_node_subclass(base):
                return True
        return False
