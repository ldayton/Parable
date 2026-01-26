"""Symbol collection passes for Go transpiler."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from .go_overrides import FIELD_TYPE_OVERRIDES, PARAM_TYPE_OVERRIDES, RETURN_TYPE_OVERRIDES
from .go_types import ClassInfo, FieldInfo, FuncInfo, ParamInfo

if TYPE_CHECKING:
    from .go_types import SymbolTable


class SymbolsMixin:
    """Mixin providing symbol collection methods for Go transpiler."""

    # These are expected to be set by the main class
    symbols: "SymbolTable"

    # These methods are expected from TypeSystemMixin
    def _annotation_to_str(self, node: ast.expr | None) -> str: ...
    def _py_type_to_go(self, py_type: str, concrete_nodes: bool = False) -> str: ...
    def _py_return_type_to_go(self, py_type: str) -> str: ...
    def _infer_type(self, node: ast.expr, param_types: dict[str, str]) -> str: ...

    def _collect_symbols(self, tree: ast.Module):
        """Collect all type information in multiple passes."""
        # Pass 1: Collect class names and inheritance
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [self._get_base_name(b) for b in node.bases]
                self.symbols.classes[node.name] = ClassInfo(
                    name=node.name, bases=bases, fields={}, methods={}
                )
        # Mark Node subclasses
        for name, info in self.symbols.classes.items():
            info.is_node = self.symbols.is_node_subclass(name)
        # Pass 2: Collect function signatures
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                self.symbols.functions[node.name] = self._extract_func_info(node)
            elif isinstance(node, ast.ClassDef):
                self._collect_class_methods(node)
        # Pass 3: Collect struct fields from __init__
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                self._collect_class_fields(node)

    def _get_base_name(self, base: ast.expr) -> str:
        """Extract base class name from AST node."""
        if isinstance(base, ast.Name):
            return base.id
        if isinstance(base, ast.Attribute):
            return base.attr
        return ""

    def _collect_class_methods(self, node: ast.ClassDef):
        """Collect method signatures for a class."""
        class_info = self.symbols.classes[node.name]
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef):
                func_info = self._extract_func_info(stmt, is_method=True)
                func_info.receiver_type = node.name
                class_info.methods[stmt.name] = func_info

    def _collect_class_fields(self, node: ast.ClassDef):
        """Collect struct fields from class definition and __init__."""
        class_info = self.symbols.classes[node.name]
        # Collect class-level annotations
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                py_type = self._annotation_to_str(stmt.annotation)
                go_type = self._py_type_to_go(py_type)
                class_info.fields[stmt.target.id] = FieldInfo(
                    name=stmt.target.id, py_type=py_type, go_type=go_type
                )
        # Collect class-level constant assignments (for enum-like classes)
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and isinstance(stmt.value, ast.Constant):
                        # This is a class-level constant
                        class_info.constants[target.id] = stmt.value.value
        # Collect fields from __init__ assignments
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                self._collect_init_fields(stmt, class_info)

    def _collect_init_fields(self, init: ast.FunctionDef, class_info: ClassInfo):
        """Collect fields assigned in __init__."""
        param_types: dict[str, str] = {}
        for arg in init.args.args:
            if arg.arg != "self" and arg.annotation:
                param_types[arg.arg] = self._annotation_to_str(arg.annotation)
        for stmt in ast.walk(init):
            # Handle regular assignment: self.x = value
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                    ):
                        field_name = target.attr
                        if field_name not in class_info.fields:
                            go_type = self._infer_type(stmt.value, param_types)
                            class_info.fields[field_name] = FieldInfo(
                                name=field_name, py_type="", go_type=go_type
                            )
            # Handle annotated assignment: self.x: Type = value
            elif isinstance(stmt, ast.AnnAssign):
                if (
                    isinstance(stmt.target, ast.Attribute)
                    and isinstance(stmt.target.value, ast.Name)
                    and stmt.target.value.id == "self"
                ):
                    field_name = stmt.target.attr
                    if field_name not in class_info.fields:
                        py_type = self._annotation_to_str(stmt.annotation)
                        go_type = self._py_type_to_go(py_type)
                        # Apply field type overrides
                        override_key = (class_info.name, field_name)
                        if override_key in FIELD_TYPE_OVERRIDES:
                            go_type = FIELD_TYPE_OVERRIDES[override_key]
                        class_info.fields[field_name] = FieldInfo(
                            name=field_name, py_type=py_type, go_type=go_type
                        )

    def _extract_func_info(self, node: ast.FunctionDef, is_method: bool = False) -> FuncInfo:
        """Extract function signature information."""
        params = []
        for arg in node.args.args:
            if arg.arg == "self":
                continue
            py_type = self._annotation_to_str(arg.annotation) if arg.annotation else ""
            go_type = self._py_type_to_go(py_type) if py_type else "interface{}"
            # Check for overrides
            override_key = (node.name, arg.arg)
            if override_key in PARAM_TYPE_OVERRIDES:
                go_type = PARAM_TYPE_OVERRIDES[override_key]
            params.append(ParamInfo(name=arg.arg, py_type=py_type, go_type=go_type))
        # Handle defaults
        defaults = node.args.defaults
        if defaults:
            offset = len(params) - len(defaults)
            for i, default in enumerate(defaults):
                params[offset + i].default = default
        return_type = ""
        if node.returns:
            py_return = self._annotation_to_str(node.returns)
            return_type = self._py_return_type_to_go(py_return)
        # Apply return type overrides
        if node.name in RETURN_TYPE_OVERRIDES:
            return_type = RETURN_TYPE_OVERRIDES[node.name]
        return FuncInfo(
            name=node.name,
            params=params,
            return_type=return_type,
            is_method=is_method,
        )
