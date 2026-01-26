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


@dataclass
class FunctionAnalysis:
    """Analysis results for a single function/method body."""

    var_types: dict[str, str] = field(default_factory=dict)
    hoisted_vars: dict[str, int] = field(default_factory=dict)
    declared_vars: set[str] = field(default_factory=set)
    scope_tree: dict[int, ScopeInfo] = field(default_factory=dict)
    var_usage: dict[str, VarInfo] = field(default_factory=dict)
    returned_vars: set[str] = field(default_factory=set)
    byte_vars: set[str] = field(default_factory=set)
    tuple_vars: dict[str, list[str]] = field(default_factory=dict)
    tuple_func_vars: dict[str, str] = field(default_factory=dict)
    var_assign_sources: dict[str, str] = field(default_factory=dict)
    scope_id_map: dict[int, int] = field(default_factory=dict)
    next_scope_id: int = 1


@dataclass
class EmissionContext:
    """Mutable context passed through emission methods."""

    analysis: FunctionAnalysis
    symbols: SymbolTable
    current_class: str | None = None
    current_method: str | None = None
    current_func_info: FuncInfo | None = None
    current_return_type: str = ""
    indent: int = 0
    emitted_hoisted: set[str] = field(default_factory=set)

    @property
    def var_types(self) -> dict[str, str]:
        return self.analysis.var_types

    @property
    def declared_vars(self) -> set[str]:
        return self.analysis.declared_vars

    @property
    def scope_tree(self) -> dict[int, ScopeInfo]:
        return self.analysis.scope_tree

    @property
    def var_usage(self) -> dict[str, VarInfo]:
        return self.analysis.var_usage

    @property
    def hoisted_vars(self) -> dict[str, int]:
        return self.analysis.hoisted_vars

    @property
    def scope_id_map(self) -> dict[int, int]:
        return self.analysis.scope_id_map

    @property
    def returned_vars(self) -> set[str]:
        return self.analysis.returned_vars

    @property
    def byte_vars(self) -> set[str]:
        return self.analysis.byte_vars

    @property
    def tuple_vars(self) -> dict[str, list[str]]:
        return self.analysis.tuple_vars

    @property
    def tuple_func_vars(self) -> dict[str, str]:
        return self.analysis.tuple_func_vars

    @property
    def var_assign_sources(self) -> dict[str, str]:
        return self.analysis.var_assign_sources

    @property
    def next_scope_id(self) -> int:
        return self.analysis.next_scope_id

    @next_scope_id.setter
    def next_scope_id(self, value: int) -> None:
        self.analysis.next_scope_id = value


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
