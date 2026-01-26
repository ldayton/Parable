"""Statement emission for Go transpiler."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from .go_overrides import TUPLE_ELEMENT_TYPES, UNION_FIELDS
from .go_type_system import KIND_TO_TYPE

if TYPE_CHECKING:
    from .go_types import FuncInfo, SymbolTable


class EmitStatementsMixin:
    """Mixin for statement code emission."""

    # Type hints for attributes from GoTranspiler
    symbols: SymbolTable
    current_class: str | None
    current_method: str | None
    current_func_info: FuncInfo | None
    current_return_type: str
    indent: int
    declared_vars: set[str]
    byte_vars: set[str]
    tuple_vars: dict[str, list[str]]
    tuple_func_vars: dict[str, str]
    var_types: dict[str, str]
    var_assign_sources: dict[str, str]
    union_field_types: dict[tuple[str, str], str]
    returned_vars: set[str]
    _type_switch_var: tuple[str, str] | None
    _type_switch_type: str | None

    # Type hints for methods from other mixins
    def emit(self, text: str) -> None: ...
    def emit_raw(self, text: str) -> None: ...
    def visit_expr(self, node: ast.expr) -> str: ...
    def _to_go_var(self, name: str) -> str: ...
    def _to_go_func_name(self, name: str) -> str: ...
    def _to_go_field_name(self, name: str) -> str: ...
    def _to_go_type(self, py_type: str) -> str: ...
    def _py_type_to_go(self, py_type: str, concrete_nodes: bool = False) -> str: ...
    def _emit_bool_expr(self, node: ast.expr) -> str: ...
    def _infer_type_from_expr(self, node: ast.expr) -> str: ...
    def _infer_object_class(self, node: ast.expr) -> str: ...
    def _nil_to_zero_value(self, go_type: str | None) -> str: ...
    def _get_return_type_info(self, node: ast.Call) -> list[str] | None: ...
    def _is_string_subscript(self, node: ast.Subscript) -> bool: ...
    def _is_byte_expr(self, node: ast.expr) -> bool: ...
    def _is_getattr_call(self, node: ast.expr) -> bool: ...
    def _is_tuple_element_access(self, node: ast.expr) -> bool: ...
    def _is_node_list_subscript(self, node: ast.expr) -> bool: ...
    def _get_type_for_field(self, field_name: str) -> str: ...
    def _binop_to_go(self, op: ast.operator) -> str: ...
    def _annotation_to_str(self, ann: ast.expr) -> str: ...
    def _emit_stmts_with_patterns(self, stmts: list[ast.stmt]) -> None: ...
    def _infer_single_type_from_expr(self, node: ast.expr) -> str: ...

    # Methods that always use := for assignment (to avoid scope shadowing issues)
    FORCE_NEW_LOCAL_METHODS = {
        "_parse_matched_pair",
        "_ParseMatchedPair",
        "_collect_param_argument",
        "_CollectParamArgument",
    }

    def _emit_stmt(self, stmt: ast.stmt):
        """Emit a single statement."""
        method = f"_emit_stmt_{stmt.__class__.__name__}"
        if hasattr(self, method):
            getattr(self, method)(stmt)
        else:
            raise NotImplementedError(f"Statement type {stmt.__class__.__name__}")

    def _emit_stmt_Expr(self, stmt: ast.Expr):
        """Emit expression statement."""
        # Skip docstrings
        if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
            return
        expr = self.visit_expr(stmt.value)
        # Handle append which needs to be a statement
        if "= append(" in expr:
            self.emit(expr)
        else:
            self.emit(expr)

    def _emit_stmt_Assign(self, stmt: ast.Assign):
        """Emit assignment statement."""
        if len(stmt.targets) == 1:
            target = stmt.targets[0]
            # Handle tuple unpacking: a, b = x, y
            if isinstance(target, ast.Tuple):
                self._emit_tuple_unpack(target, stmt.value)
                return
            # Check if RHS is a tuple-returning function call assigned to single var
            if isinstance(target, ast.Name) and isinstance(stmt.value, ast.Call):
                ret_info = self._get_return_type_info(stmt.value)
                if ret_info and len(ret_info) > 1:
                    target_str = self.visit_expr(target)
                    # Generate synthetic variable names for tuple elements
                    elem_vars = [f"{target_str}{i}" for i in range(len(ret_info))]
                    # Check which vars are actually used later (to avoid declaring unused ones)
                    # If the base variable is returned, we need all synthetic vars declared
                    need_all = target_str in self.returned_vars
                    used_vars = []
                    for v in elem_vars:
                        if v in self.declared_vars or need_all:
                            used_vars.append(v)  # Already declared or returned means it's used
                        else:
                            used_vars.append("_")  # Not declared means unused, use blank identifier
                    # Check if all used elem_vars are already declared (redeclaration)
                    non_blank = [v for v in used_vars if v != "_"]
                    all_declared = all(v in self.declared_vars for v in non_blank)
                    for i, v in enumerate(elem_vars):
                        if v != "_" and used_vars[i] != "_":
                            self.declared_vars.add(v)
                            self.var_types[v] = ret_info[i]
                    self.tuple_vars[target_str] = elem_vars
                    call_str = self.visit_expr(stmt.value)
                    op = "=" if all_declared else ":="
                    self.emit(f"{', '.join(used_vars)} {op} {call_str}")
                    return
            target_str = self.visit_expr(target)
            # If in type switch context and assigning to the switched variable,
            # assign to the original variable (not the narrowed one)
            if isinstance(target, ast.Name) and self._type_switch_var:
                orig_var, narrowed_var = self._type_switch_var
                if target_str == narrowed_var:
                    target_str = orig_var
            # Check if this is a new variable (local name, not attribute)
            if isinstance(target, ast.Name):
                if target_str not in self.declared_vars:
                    self.declared_vars.add(target_str)
                    # Use inferred type for empty list initialization
                    if isinstance(stmt.value, ast.List) and not stmt.value.elts:
                        if target_str in self.var_types:
                            go_type = self.var_types[target_str]
                            self.emit(f"{target_str} := {go_type}{{}}")
                            return
                    value = self.visit_expr(stmt.value)
                    # Track if this variable holds a byte (from string subscript)
                    if self._is_string_char_subscript(stmt.value):
                        self.byte_vars.add(target_str)
                    # Track if assigned from a tuple-returning function
                    self._track_tuple_func_assignment(target_str, stmt.value)
                    # Track assignment source for procsub/cmdsub type inference
                    self._track_assign_source(target_str, stmt.value)
                    # Track type for subsequent accesses (e.g., subscript on interface{})
                    if target_str not in self.var_types:
                        inferred_type = self._infer_type_from_expr(stmt.value)
                        if inferred_type:
                            self.var_types[target_str] = inferred_type
                    # Add type assertion for tuple element access (inline declaration)
                    target_type = self.var_types.get(target_str, "")
                    if (
                        target_type
                        and target_type != "interface{}"
                        and self._is_tuple_element_access(stmt.value)
                    ):
                        value = f"{value}.({target_type})"
                    self.emit(f"{target_str} := {value}")
                    return
            # Use inferred type for empty list assignment to typed variables
            if isinstance(stmt.value, ast.List) and not stmt.value.elts:
                if target_str in self.var_types:
                    go_type = self.var_types[target_str]
                    self.emit(f"{target_str} = {go_type}{{}}")
                    return
            value = self.visit_expr(stmt.value)
            # Track if this variable holds a byte (from string subscript)
            if isinstance(target, ast.Name) and self._is_string_char_subscript(stmt.value):
                self.byte_vars.add(target_str)
            # Track assignment source for procsub/cmdsub type inference
            if isinstance(target, ast.Name):
                self._track_assign_source(target_str, stmt.value)
            # Convert nil to -1 if assigning to int field (self.x = None)
            if (
                isinstance(target, ast.Attribute)
                and isinstance(stmt.value, ast.Constant)
                and stmt.value.value is None
            ):
                if (
                    isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                    and self.current_class
                ):
                    class_info = self.symbols.classes.get(self.current_class)
                    if class_info and target.attr in class_info.fields:
                        field_type = class_info.fields[target.attr].go_type or ""
                        if field_type == "int":
                            value = "-1"
            # Convert byte to string if assigning to string-typed variable
            if isinstance(target, ast.Name):
                target_type = self.var_types.get(target_str, "")
                if target_type == "string" and self._is_byte_expr(stmt.value):
                    value = f"string({value})"
                # Convert nil to -1 if assigning to int variable
                if (
                    target_type == "int"
                    and isinstance(stmt.value, ast.Constant)
                    and stmt.value.value is None
                ):
                    value = "-1"
                # Convert nil to "" if assigning to string variable
                if (
                    target_type == "string"
                    and isinstance(stmt.value, ast.Constant)
                    and stmt.value.value is None
                ):
                    value = '""'
                # Add type assertion for getattr calls when target has known type
                if (
                    target_type
                    and target_type != "interface{}"
                    and self._is_getattr_call(stmt.value)
                ):
                    value = f"{value}.({target_type})"
                # Add type assertion for tuple element access when target has known type
                if (
                    target_type
                    and target_type != "interface{}"
                    and self._is_tuple_element_access(stmt.value)
                ):
                    value = f"{value}.({target_type})"
                # Add type assertion for subscript on []Node when target is concrete ptr type
                if (
                    target_type
                    and target_type.startswith("*")
                    and self._is_node_list_subscript(stmt.value)
                ):
                    value = f"{value}.({target_type})"
            # For method calls to certain patterns, use := to create new local (avoids scope issues)
            # This handles cases where same var name is used in sibling if blocks
            # But skip this if the variable was already pre-declared
            if isinstance(target, ast.Name) and isinstance(stmt.value, ast.Call):
                if target_str not in self.declared_vars:  # Not a pre-declared variable
                    # Only do this for known method calls that return strings (like _parse_matched_pair)
                    if isinstance(stmt.value.func, ast.Attribute):
                        method = stmt.value.func.attr
                        if method in (
                            "_parse_matched_pair",
                            "_ParseMatchedPair",
                            "_collect_param_argument",
                            "_CollectParamArgument",
                        ):
                            self.declared_vars.add(target_str)
                            self.emit(f"{target_str} := {value}")
                            return
            # Track if assigned from a tuple-returning function
            if isinstance(target, ast.Name):
                self._track_tuple_func_assignment(target_str, stmt.value)
            self.emit(f"{target_str} = {value}")
        else:
            # Multiple assignment targets: a = b = value
            # In Go, assign to each target
            value = self.visit_expr(stmt.value)
            for target in stmt.targets:
                target_str = self.visit_expr(target)
                if isinstance(target, ast.Name) and target_str not in self.declared_vars:
                    self.declared_vars.add(target_str)
                    self.emit(f"{target_str} := {value}")
                else:
                    self.emit(f"{target_str} = {value}")

    def _emit_tuple_unpack(self, target: ast.Tuple, value: ast.expr):
        """Emit tuple unpacking: a, b = x, y"""
        target_names = []
        for elt in target.elts:
            # Handle Python's discard pattern: _, x = func()
            if isinstance(elt, ast.Name) and elt.id == "_":
                target_names.append("_")
            else:
                name = self.visit_expr(elt)
                target_names.append(name)
                if isinstance(elt, ast.Name):
                    camel = self._to_go_var(elt.id)
                    self.declared_vars.add(camel)
        # Handle value side
        if isinstance(value, ast.Tuple):
            # a, b = x, y - for tuple literals, check if vars exist
            value_exprs = [self.visit_expr(v) for v in value.elts]
            self.emit(f"{', '.join(target_names)} := {', '.join(value_exprs)}")
        elif isinstance(value, ast.Call):
            # a, b = func() - always use := for function calls returning multiple values
            # This ensures fresh local variables are created in the current scope
            value_expr = self.visit_expr(value)
            self.emit(f"{', '.join(target_names)} := {value_expr}")
            # Suppress unused variable warnings for non-blank tuple elements
            for name in target_names:
                if name != "_":
                    self.emit(f"_ = {name}")
        else:
            # Other cases - need to unpack at runtime
            raise NotImplementedError(f"Tuple unpacking from {type(value).__name__}")

    def _emit_stmt_AnnAssign(self, stmt: ast.AnnAssign):
        """Emit annotated assignment."""
        if stmt.value:
            target = self.visit_expr(stmt.target)
            py_type = self._annotation_to_str(stmt.annotation)
            # Handle None assignment to optional types (int | None, etc.)
            if isinstance(stmt.value, ast.Constant) and stmt.value.value is None:
                if " | None" in py_type:
                    # Extract base type
                    base_type = py_type.split("|")[0].strip()
                    go_base = self._py_type_to_go(base_type)
                    # Use sentinel values for nullable primitives
                    if go_base == "int":
                        # Use -1 as sentinel for nullable int (positions are never negative)
                        if isinstance(stmt.target, ast.Name):
                            if target not in self.declared_vars:
                                self.declared_vars.add(target)
                                self.emit(f"{target} := -1")
                            else:
                                self.emit(f"{target} = -1")
                            self.var_types[target] = "int"
                            return
            # Use type annotation to determine the Go type for empty lists
            if isinstance(stmt.value, ast.List) and not stmt.value.elts:
                go_type = self._py_type_to_go(py_type)
                if go_type and go_type.startswith("["):
                    value = f"{go_type}{{}}"
                    # Store type for later use in append inference
                    if isinstance(stmt.target, ast.Name):
                        self.var_types[target] = go_type
                else:
                    value = self.visit_expr(stmt.value)
            else:
                value = self.visit_expr(stmt.value)
            # Use := for first declaration, = for reassignment
            if isinstance(stmt.target, ast.Name) and target not in self.declared_vars:
                self.declared_vars.add(target)
                self.emit(f"{target} := {value}")
            else:
                self.emit(f"{target} = {value}")

    def _emit_stmt_AugAssign(self, stmt: ast.AugAssign):
        """Emit augmented assignment (+=, -=, etc.)."""
        target = self.visit_expr(stmt.target)
        op = self._binop_to_go(stmt.op)
        value = self.visit_expr(stmt.value)
        self.emit(f"{target} {op}= {value}")

    def _emit_stmt_Return(self, stmt: ast.Return):
        """Emit return statement."""
        if stmt.value:
            # Handle tuple return type (multiple return values)
            if self.current_return_type.startswith("(") and isinstance(stmt.value, ast.Tuple):
                values = [
                    self._emit_tuple_return_element(e, i) for i, e in enumerate(stmt.value.elts)
                ]
                self.emit(f"return {', '.join(values)}")
                return
            # Check for None return - convert to zero value based on return type
            if isinstance(stmt.value, ast.Constant) and stmt.value.value is None:
                # Special handling for tuple return types
                if self.current_return_type.startswith("("):
                    inner = self.current_return_type[1:-1]
                    parts = [p.strip() for p in inner.split(",")]
                    zero_values = [self._nil_to_zero_value(p) for p in parts]
                    value = ", ".join(zero_values)
                else:
                    value = self._nil_to_zero_value(self.current_return_type)
            # Check for single-char string subscript (byte) being returned as string
            elif self.current_return_type == "string" and self._is_string_char_subscript(
                stmt.value
            ):
                value = f"string({self.visit_expr(stmt.value)})"
            # Check for byte variable being returned as string
            elif self.current_return_type == "string" and self._is_byte_variable(stmt.value):
                value = f"string({self.visit_expr(stmt.value)})"
            # Check for interface field being returned as concrete pointer type
            elif self.current_return_type.startswith("*") and self._is_interface_field(stmt.value):
                value = f"{self.visit_expr(stmt.value)}.({self.current_return_type})"
            # Check for []Node subscript being returned as concrete pointer type
            elif self.current_return_type.startswith("*") and self._is_node_list_subscript(
                stmt.value
            ):
                value = f"{self.visit_expr(stmt.value)}.({self.current_return_type})"
            # Check for attribute access returning Node when we need concrete type
            elif self.current_return_type.startswith("*") and self._is_node_field_access(
                stmt.value
            ):
                value = f"{self.visit_expr(stmt.value)}.({self.current_return_type})"
            # Check for returning a tuple variable (passthrough pattern)
            elif isinstance(stmt.value, ast.Name):
                var_name = self._to_go_var(stmt.value.id)
                if var_name in self.tuple_vars:
                    elem_vars = self.tuple_vars[var_name]
                    self.emit(f"return {', '.join(elem_vars)}")
                    return
                # Use visit_expr to handle type switch variable rewriting
                value = self.visit_expr(stmt.value)
            else:
                value = self.visit_expr(stmt.value)
            self.emit(f"return {value}")
        else:
            self.emit("return")

    def _emit_tuple_return_element(self, node: ast.expr, index: int) -> str:
        """Emit a single element of a tuple return, with type conversion if needed."""
        # Get the expected type for this position from the return type
        if self.current_return_type.startswith("("):
            inner = self.current_return_type[1:-1]
            parts = [p.strip() for p in inner.split(",")]
            expected_type = parts[index] if index < len(parts) else ""
        else:
            expected_type = ""
        # Convert None to appropriate zero value
        if isinstance(node, ast.Constant) and node.value is None:
            return self._nil_to_zero_value(expected_type)
        # Convert empty list to typed empty slice
        if isinstance(node, ast.List) and not node.elts:
            if expected_type.startswith("[]"):
                return f"{expected_type}{{}}"
        return self.visit_expr(node)

    def _is_string_char_subscript(self, node: ast.expr) -> bool:
        """Check if node is a single-character string subscript (returns byte in Go)."""
        if not isinstance(node, ast.Subscript):
            return False
        # Must be single index, not slice
        if isinstance(node.slice, ast.Slice):
            return False
        # Check if the value being subscripted is a known string attribute
        if isinstance(node.value, ast.Attribute):
            # Common string fields: source, Source
            if node.value.attr.lower() == "source":
                return True
        # Also handle local variables that are strings
        if isinstance(node.value, ast.Name):
            name = node.value.id
            if name in ("source", "s", "text", "line"):
                return True
        return False

    def _track_tuple_func_assignment(self, var_name: str, value: ast.expr):
        """Track if a variable is assigned from a known tuple-returning function."""
        if not isinstance(value, ast.Call):
            return
        func_name = None
        if isinstance(value.func, ast.Name):
            func_name = value.func.id
        elif isinstance(value.func, ast.Attribute):
            func_name = value.func.attr
        if func_name:
            go_func_name = self._to_go_func_name(func_name)
            if go_func_name in TUPLE_ELEMENT_TYPES:
                self.tuple_func_vars[var_name] = go_func_name

    def _track_assign_source(self, var_name: str, value: ast.expr):
        """Track assignment source for procsub/cmdsub type inference."""
        if isinstance(value, ast.Subscript) and isinstance(value.value, ast.Name):
            source_name = value.value.id
            if source_name in ("procsub_parts", "cmdsub_parts"):
                self.var_assign_sources[var_name] = source_name

    def _is_byte_variable(self, node: ast.expr) -> bool:
        """Check if node is a variable known to hold a byte."""
        if not isinstance(node, ast.Name):
            return False
        go_name = self._to_go_var(node.id)
        return go_name in self.byte_vars

    def _is_interface_field(self, node: ast.expr) -> bool:
        """Check if node is an attribute access on a struct field typed as Node/interface{}."""
        if not isinstance(node, ast.Attribute):
            return False
        # Look up the field type from the receiver's class
        if isinstance(node.value, ast.Name):
            var_name = self._to_go_var(node.value.id)
            var_type = self.var_types.get(var_name, "")
            # Strip pointer prefix to get class name
            class_name = var_type.lstrip("*")
            if class_name in self.symbols.classes:
                class_info = self.symbols.classes[class_name]
                if node.attr in class_info.fields:
                    field_type = class_info.fields[node.attr].go_type or ""
                    return field_type in ("Node", "interface{}")
        return False

    def _is_node_field_access(self, node: ast.expr) -> bool:
        """Check if node is an attribute access that returns Node."""
        if not isinstance(node, ast.Attribute):
            return False
        # Check if the field type is Node
        field_type = self._get_field_type_from_attr(node)
        return field_type in ("Node", "interface{}")

    def _get_field_type_from_attr(self, node: ast.Attribute) -> str:
        """Get the field type from an attribute access expression."""
        if isinstance(node.value, ast.Name):
            var_name = self._to_go_var(node.value.id)
            var_type = self.var_types.get(var_name, "")
            class_name = var_type.lstrip("*")
            if class_name in self.symbols.classes:
                class_info = self.symbols.classes[class_name]
                if node.attr in class_info.fields:
                    return class_info.fields[node.attr].go_type or ""
        # For more complex expressions, try to infer the type
        field_name = node.attr
        type_assertion = self._get_type_for_field(field_name)
        if type_assertion:
            # The field needs a type assertion, meaning it's probably Node
            class_name = type_assertion.lstrip("*")
            if class_name in self.symbols.classes:
                class_info = self.symbols.classes[class_name]
                if field_name in class_info.fields:
                    return class_info.fields[field_name].go_type or ""
        return ""

    def _emit_stmt_If(self, stmt: ast.If):
        """Emit if statement."""
        # Pre-declare variables assigned across if/elif/else branches to avoid Go scoping issues
        self._predeclare_if_chain_vars(stmt)
        self._emit_if_chain(stmt, is_first=True)

    def _predeclare_if_chain_vars(self, stmt: ast.If):
        """Pre-declare variables that are assigned in multiple if/elif/else branches."""
        # Collect assignments from all branches with their types
        branch_vars: list[dict[str, str]] = []
        self._collect_if_chain_assignments(stmt, branch_vars)
        if len(branch_vars) < 2:
            return  # No elif/else, no scoping issue
        # Find all variables across branches
        all_vars: dict[str, str] = {}
        for vars in branch_vars:
            for var, go_type in vars.items():
                if var not in all_vars:
                    all_vars[var] = go_type
        # Pre-declare variables that are new (not already declared)
        for var, go_type in all_vars.items():
            if var not in self.declared_vars:
                # Use known type from var_types if available, else inferred type
                actual_type = self.var_types.get(var, go_type)
                self.emit(f"var {var} {actual_type}")
                self.declared_vars.add(var)

    def _collect_if_chain_assignments(self, stmt: ast.If, branch_vars: list[dict[str, str]]):
        """Collect variable assignments from if/elif/else branches."""
        # Collect from if body
        if_vars = self._collect_branch_assignments(stmt.body)
        branch_vars.append(if_vars)
        # Process orelse
        if stmt.orelse:
            if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                # elif chain - recurse
                self._collect_if_chain_assignments(stmt.orelse[0], branch_vars)
            else:
                # else branch
                else_vars = self._collect_branch_assignments(stmt.orelse)
                branch_vars.append(else_vars)

    def _collect_branch_assignments(self, stmts: list[ast.stmt]) -> dict[str, str]:
        """Collect variable names and inferred types assigned in a list of statements (recursive)."""
        vars: dict[str, str] = {}
        for s in stmts:
            if isinstance(s, ast.Assign):
                for target in s.targets:
                    if isinstance(target, ast.Name):
                        # For tuple-returning functions, only collect vars that are predeclared
                        # (i.e., actually used) - unused ones will use _ in the assignment
                        if isinstance(s.value, ast.Call):
                            ret_info = self._get_return_type_info(s.value)
                            if ret_info and len(ret_info) > 1:
                                go_name = self._to_go_var(target.id)
                                for i, elem_type in enumerate(ret_info):
                                    synth_name = f"{go_name}{i}"
                                    # Only collect if already predeclared (actually used)
                                    if synth_name in self.declared_vars:
                                        vars[synth_name] = elem_type
                                continue
                            # Skip assignments from methods that force := usage
                            if isinstance(s.value.func, ast.Attribute):
                                if s.value.func.attr in self.FORCE_NEW_LOCAL_METHODS:
                                    continue
                        go_name = self._to_go_var(target.id)
                        # Use single-type inference to avoid tuple types
                        go_type = self._infer_single_type_from_expr(s.value)
                        vars[go_name] = go_type
                    elif isinstance(target, ast.Tuple):
                        # Skip tuple unpacking - it uses := which creates fresh locals
                        # Pre-declaring these would cause "declared and not used" errors
                        pass
            elif isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name):
                go_name = self._to_go_var(s.target.id)
                try:
                    py_type = ast.unparse(s.annotation)
                    go_type = self._py_type_to_go(py_type)
                except Exception:
                    go_type = "interface{}"
                vars[go_name] = go_type
            # Recursively collect from nested if statements
            elif isinstance(s, ast.If):
                nested = self._collect_branch_assignments(s.body)
                vars.update(nested)
                if s.orelse:
                    nested = self._collect_branch_assignments(s.orelse)
                    vars.update(nested)
            # Recursively collect from loops
            elif isinstance(s, (ast.For, ast.While)):
                nested = self._collect_branch_assignments(s.body)
                vars.update(nested)
        return vars

    def _detect_union_discriminator(self, test: ast.expr) -> tuple[str, str, str] | None:
        """Detect if test is a union field discriminator comparison (var == nil).
        Returns (receiver, field, discriminator_var) if found, None otherwise."""
        # Look for pattern: discriminatorVar == nil
        if not isinstance(test, ast.Compare):
            return None
        if len(test.ops) != 1 or not isinstance(test.ops[0], (ast.Eq, ast.Is)):
            return None
        if len(test.comparators) != 1:
            return None
        # Check if comparing to None/nil
        comp = test.comparators[0]
        if not (isinstance(comp, ast.Constant) and comp.value is None):
            return None
        # Check if left side is a discriminator variable
        if not isinstance(test.left, ast.Name):
            return None
        disc_var = self._to_go_var(test.left.id)
        # Check if this discriminator matches any union field
        for (receiver_type, field_name), (expected_disc, _, _) in UNION_FIELDS.items():
            if disc_var == expected_disc:
                return (receiver_type, field_name, disc_var)
        return None

    def _detect_kind_check(self, test: ast.expr) -> tuple[str, str] | None:
        """Detect `var.kind == "literal"` or `var is not None and var.kind == "literal"`.
        Returns (var_name, kind_literal) or None."""
        # Handle compound: `var is not None and var.kind == "literal"`
        # Go type assertion handles nil check implicitly, so we can emit just the assertion
        if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.And):
            for value in test.values:
                result = self._detect_simple_kind_check(value)
                if result:
                    return result
            return None
        return self._detect_simple_kind_check(test)

    def _detect_simple_kind_check(self, test: ast.expr) -> tuple[str, str] | None:
        """Detect simple `var.kind == "literal"`. Returns (var_name, kind_literal) or None."""
        if not isinstance(test, ast.Compare):
            return None
        if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
            return None
        if not isinstance(test.left, ast.Attribute) or test.left.attr != "kind":
            return None
        if not isinstance(test.left.value, ast.Name):
            return None
        comp = test.comparators[0]
        if not isinstance(comp, ast.Constant) or not isinstance(comp.value, str):
            return None
        if comp.value not in KIND_TO_TYPE:
            return None
        return (test.left.value.id, comp.value)

    def _emit_kind_type_narrowing(self, stmt: ast.If, kind_info: tuple[str, str], is_first: bool):
        """Emit kind-based type narrowing as Go type assertion."""
        var_name, kind_literal = kind_info
        type_name = KIND_TO_TYPE[kind_literal]
        go_var = self._to_go_var(var_name)
        narrowed_var = go_var[0].lower()
        if narrowed_var == go_var:
            narrowed_var = go_var + "T"
        if is_first:
            self.emit(f"if {narrowed_var}, ok := {go_var}.(*{type_name}); ok {{")
        else:
            self.emit_raw(
                "\t" * self.indent
                + f"}} else if {narrowed_var}, ok := {go_var}.(*{type_name}); ok {{"
            )
        self.indent += 1
        # Set type narrowing context (reuses existing _type_switch_var mechanism)
        old_switch_var = self._type_switch_var
        old_switch_type = self._type_switch_type
        self._type_switch_var = (go_var, narrowed_var)
        self._type_switch_type = f"*{type_name}"
        try:
            for s in stmt.body:
                self._emit_stmt(s)
        except NotImplementedError:
            self.emit('panic("TODO")')
        # Restore context
        self._type_switch_var = old_switch_var
        self._type_switch_type = old_switch_type
        self.indent -= 1
        # Handle elif/else chains
        if stmt.orelse:
            if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                self._emit_if_chain(stmt.orelse[0], is_first=False)
            else:
                self.emit_raw("\t" * self.indent + "} else {")
                self.indent += 1
                for s in stmt.orelse:
                    self._emit_stmt(s)
                self.indent -= 1
                self.emit("}")
        else:
            self.emit("}")

    def _emit_if_chain(self, stmt: ast.If, is_first: bool):
        """Emit if/elif/else chain."""
        # Check for kind-based type narrowing
        kind_info = self._detect_kind_check(stmt.test)
        if kind_info:
            return self._emit_kind_type_narrowing(stmt, kind_info, is_first)
        test = self._emit_bool_expr(stmt.test)
        # Check for union field discriminator pattern
        union_info = self._detect_union_discriminator(stmt.test)
        union_key = None
        if union_info:
            receiver_type, field_name, disc_var = union_info
            _, nil_type, non_nil_type = UNION_FIELDS[(receiver_type, field_name)]
            union_key = (receiver_type, field_name)
        if is_first:
            self.emit(f"if {test} {{")
        else:
            self.emit_raw("\t" * self.indent + f"}} else if {test} {{")
        self.indent += 1
        # Set union field type for body (nil branch = string for discriminator == nil)
        if union_key:
            self.union_field_types[union_key] = nil_type
        self._emit_stmts_with_patterns(stmt.body)
        # Clear union field type after body
        if union_key:
            del self.union_field_types[union_key]
        self.indent -= 1
        if stmt.orelse:
            if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                # elif - continue chain
                self._emit_if_chain(stmt.orelse[0], is_first=False)
            else:
                # else - set non-nil type
                self.emit_raw("\t" * self.indent + "} else {")
                self.indent += 1
                if union_key:
                    self.union_field_types[union_key] = non_nil_type
                self._emit_stmts_with_patterns(stmt.orelse)
                if union_key:
                    del self.union_field_types[union_key]
                self.indent -= 1
                self.emit("}")
        else:
            self.emit("}")

    def _emit_stmt_While(self, stmt: ast.While):
        """Emit while loop."""
        test = self._emit_bool_expr(stmt.test)
        self.emit(f"for {test} {{")
        self.indent += 1
        try:
            for s in stmt.body:
                self._emit_stmt(s)
        except NotImplementedError:
            self.emit('panic("TODO: incomplete implementation")')
        self.indent -= 1
        self.emit("}")

    def _emit_stmt_For(self, stmt: ast.For):
        """Emit for loop."""
        # Check for `for _ in x:` (discard loop variable) before visiting
        is_discard = isinstance(stmt.target, ast.Name) and stmt.target.id == "_"
        target = self.visit_expr(stmt.target) if not is_discard else "_"
        # Handle range()
        if isinstance(stmt.iter, ast.Call) and isinstance(stmt.iter.func, ast.Name):
            if stmt.iter.func.id == "range":
                self._emit_range_for(stmt, target, is_discard)
                return
        # Standard for-each
        iter_expr = self.visit_expr(stmt.iter)
        # Track loop variable type from iterable's element type
        if not is_discard and isinstance(stmt.target, ast.Name):
            elem_type = self._get_iter_element_type(stmt.iter)
            if elem_type:
                self.var_types[target] = elem_type
        # Handle `for _ in x:` (discard loop variable)
        if is_discard:
            self.emit(f"for range {iter_expr} {{")
        else:
            self.emit(f"for _, {target} := range {iter_expr} {{")
        self.indent += 1
        try:
            for s in stmt.body:
                self._emit_stmt(s)
        except NotImplementedError:
            self.emit('panic("TODO: incomplete implementation")')
        self.indent -= 1
        self.emit("}")

    def _get_iter_element_type(self, node: ast.expr) -> str:
        """Get the element type for iterating over an expression."""
        if isinstance(node, ast.Name):
            var_name = self._to_go_var(node.id)
            var_type = self.var_types.get(var_name, "")
            if var_type.startswith("[]"):
                return var_type[2:]  # []interface{} -> interface{}
            if var_type == "string":
                return "rune"
        return ""

    def _emit_range_for(self, stmt: ast.For, target: str, is_discard: bool = False):
        """Emit for loop over range()."""
        args = stmt.iter.args
        # For discarded loop variable, use anonymous loop
        if is_discard:
            end = self.visit_expr(args[0]) if args else "0"
            self.emit(f"for _i := 0; _i < {end}; _i++ {{")
        elif len(args) == 1:
            end = self.visit_expr(args[0])
            self.emit(f"for {target} := 0; {target} < {end}; {target}++ {{")
        elif len(args) == 2:
            start = self.visit_expr(args[0])
            end = self.visit_expr(args[1])
            self.emit(f"for {target} := {start}; {target} < {end}; {target}++ {{")
        else:
            start = self.visit_expr(args[0])
            end = self.visit_expr(args[1])
            step = self.visit_expr(args[2])
            # Check for negative step
            if isinstance(args[2], ast.UnaryOp) and isinstance(args[2].op, ast.USub):
                self.emit(f"for {target} := {start}; {target} > {end}; {target} += {step} {{")
            else:
                self.emit(f"for {target} := {start}; {target} < {end}; {target} += {step} {{")
        self.indent += 1
        try:
            for s in stmt.body:
                self._emit_stmt(s)
        except NotImplementedError:
            self.emit('panic("TODO: incomplete implementation")')
        self.indent -= 1
        self.emit("}")

    def _emit_stmt_Break(self, stmt: ast.Break):
        """Emit break statement."""
        self.emit("break")

    def _emit_stmt_Continue(self, stmt: ast.Continue):
        """Emit continue statement."""
        self.emit("continue")

    def _emit_stmt_Pass(self, stmt: ast.Pass):
        """Emit pass (no-op in Go)."""
        pass  # Go doesn't need explicit pass

    def _emit_stmt_FunctionDef(self, stmt: ast.FunctionDef):
        """Skip local function definitions - they need to be inlined or helper funcs."""
        # Local functions like format_arith_val are converted to helper functions
        pass

    def _emit_stmt_Raise(self, stmt: ast.Raise):
        """Emit raise as panic."""
        if stmt.exc:
            exc = self.visit_expr(stmt.exc)
            self.emit(f"panic({exc})")
        else:
            self.emit("panic(nil)")

    def _has_return_in_block(self, stmts: list[ast.stmt]) -> bool:
        """Check if a block contains return statements (complex try/except pattern)."""
        for s in stmts:
            if isinstance(s, ast.Return):
                return True
            if isinstance(s, ast.If):
                if self._has_return_in_block(s.body) or self._has_return_in_block(s.orelse):
                    return True
            if isinstance(s, (ast.For, ast.While)):
                if self._has_return_in_block(s.body):
                    return True
        return False

    def _is_try_assign_except_return(self, stmt: ast.Try) -> bool:
        """Check if this is a 'try: x = call() except: return fallback' pattern."""
        # Must have exactly one statement in try body that's an assignment
        if len(stmt.body) != 1:
            return False
        if not isinstance(stmt.body[0], ast.Assign):
            return False
        assign = stmt.body[0]
        # Must assign to a single name
        if len(assign.targets) != 1 or not isinstance(assign.targets[0], ast.Name):
            return False
        # Must have exactly one handler
        if len(stmt.handlers) != 1:
            return False
        handler = stmt.handlers[0]
        # Handler must end with a return statement
        if not handler.body or not isinstance(handler.body[-1], ast.Return):
            return False
        return True

    def _emit_try_assign_except_return(self, stmt: ast.Try):
        """Emit 'try: x = call() except: cleanup; return fallback' pattern.

        Generates:
            var x Type
            parseOk := true
            func() {
                defer func() { if r := recover(); r != nil { parseOk = false } }()
                x = call()
            }()
            if !parseOk { cleanup; return fallback }
        """
        assign = stmt.body[0]
        var_name = self._to_go_var(assign.targets[0].id)
        handler = stmt.handlers[0]
        # Get the return statement (last in handler)
        return_stmt = handler.body[-1]
        # Get cleanup statements (all but the return)
        cleanup_stmts = handler.body[:-1]
        # Pre-declare the variable with its type (infer from call if possible)
        # Skip if already declared (e.g., by _predeclare_all_locals)
        if var_name not in self.declared_vars:
            var_type = self._infer_call_return_type(assign.value)
            if var_type:
                self.emit(f"var {var_name} {var_type}")
            else:
                self.emit(f"var {var_name} interface{{}}")
            self.declared_vars.add(var_name)
        # Emit the success flag
        self.emit("parseOk := true")
        self.declared_vars.add("parseOk")
        # Emit IIFE with defer/recover
        self.emit("func() {")
        self.indent += 1
        self.emit("defer func() {")
        self.indent += 1
        self.emit("if r := recover(); r != nil {")
        self.indent += 1
        self.emit("parseOk = false")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}()")
        # Emit the assignment
        call_expr = self.visit_expr(assign.value)
        self.emit(f"{var_name} = {call_expr}")
        self.indent -= 1
        self.emit("}()")
        # Emit the error check and fallback
        self.emit("if !parseOk {")
        self.indent += 1
        for s in cleanup_stmts:
            self._emit_stmt(s)
        self._emit_stmt(return_stmt)
        self.indent -= 1
        self.emit("}")

    def _infer_call_return_type(self, node: ast.expr) -> str | None:
        """Infer the return type of a function call."""
        if not isinstance(node, ast.Call):
            return None
        func_name = None
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
        if not func_name:
            return None
        go_func_name = self._to_go_func_name(func_name)
        # Check if it's a known method
        if go_func_name in TUPLE_ELEMENT_TYPES:
            # Returns first element type for tuple-returning funcs
            return TUPLE_ELEMENT_TYPES[go_func_name][0]
        # Common return types for parser methods
        if "parse" in func_name.lower() or "Parse" in go_func_name:
            return "Node"
        return None

    def _emit_stmt_Try(self, stmt: ast.Try):
        """Emit try/except as defer/recover pattern."""
        # We'll wrap the try block in an immediately-invoked function with defer/recover
        # Pattern: func() { defer func() { if r := recover(); r != nil { handler } }(); body }()
        if not stmt.handlers:
            # No handlers, just emit body
            for s in stmt.body:
                self._emit_stmt(s)
            return
        # Check for "try assign, except return fallback" pattern:
        # try: result = call() except Error: cleanup; return fallback
        if self._is_try_assign_except_return(stmt):
            self._emit_try_assign_except_return(stmt)
            return
        # Check for complex patterns (return statements inside try) - skip these
        if self._has_return_in_block(stmt.body) or self._has_return_in_block(stmt.handlers[0].body):
            raise NotImplementedError("try/except with return")
        # Single handler expected (all our cases)
        handler = stmt.handlers[0]
        # Determine the pattern based on handler body
        is_reraise = False
        handler_stmts = []
        for h in handler.body:
            if isinstance(h, ast.Raise):
                is_reraise = True
            elif isinstance(h, ast.Pass):
                pass  # Silent pass - no handler statements
            else:
                handler_stmts.append(h)
        # Start the IIFE
        self.emit("func() {")
        self.indent += 1
        # Emit the defer/recover
        self.emit("defer func() {")
        self.indent += 1
        self.emit("if r := recover(); r != nil {")
        self.indent += 1
        # Emit handler statements (cleanup before re-raise, or fallback assignment)
        for h in handler_stmts:
            self._emit_stmt(h)
        if is_reraise:
            self.emit("panic(r)")
        # If silent pass, we just swallow the panic (no action needed)
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}()")
        # Emit try body
        for s in stmt.body:
            self._emit_stmt(s)
        self.indent -= 1
        self.emit("}()")
