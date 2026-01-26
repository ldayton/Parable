"""Scope analysis and variable hoisting for Go transpiler."""

from __future__ import annotations

import ast
from collections.abc import Callable
from typing import TYPE_CHECKING

from .go_types import ScopeInfo, VarInfo

if TYPE_CHECKING:
    from .go_types import EmissionContext, FuncInfo, SymbolTable


class ScopeAnalysisMixin:
    """Mixin providing scope analysis and variable hoisting for Go transpiler."""

    # Instance attributes (set by main class)
    symbols: SymbolTable
    _ctx: EmissionContext
    current_method: str | None
    current_func_info: FuncInfo | None
    indent: int

    # ========== Scope-Aware Variable Declaration ==========

    def _new_scope(self, parent: int) -> int:
        """Create a new scope as a child of parent."""
        scope_id = self._ctx.next_scope_id
        self._ctx.next_scope_id += 1
        parent_depth = self._ctx.scope_tree[parent].depth if parent in self._ctx.scope_tree else -1
        self._ctx.scope_tree[scope_id] = ScopeInfo(scope_id, parent, parent_depth + 1)
        return scope_id

    def _is_ancestor(self, ancestor: int, descendant: int) -> bool:
        """True if ancestor is a proper ancestor of descendant."""
        current = self._ctx.scope_tree[descendant].parent
        while current is not None:
            if current == ancestor:
                return True
            current = self._ctx.scope_tree[current].parent
        return False

    def _is_ancestor_or_equal(self, ancestor: int, descendant: int) -> bool:
        """True if ancestor is an ancestor of or equal to descendant."""
        return ancestor == descendant or self._is_ancestor(ancestor, descendant)

    def _compute_lca(self, scope_ids: set[int]) -> int:
        """Compute lowest common ancestor of a set of scopes."""
        if len(scope_ids) == 1:
            return next(iter(scope_ids))

        def ancestors(s: int) -> set[int]:
            result = {s}
            current = self._ctx.scope_tree[s].parent
            while current is not None:
                result.add(current)
                current = self._ctx.scope_tree[current].parent
            return result

        common = ancestors(next(iter(scope_ids)))
        for s in scope_ids:
            common &= ancestors(s)
        # Return deepest common ancestor
        return max(common, key=lambda s: self._ctx.scope_tree[s].depth)

    def _needs_hoisting(self, var_info: VarInfo) -> tuple[bool, int | None]:
        """Determine if a variable needs hoisting and to which scope."""
        if not var_info.assign_scopes:
            return (False, None)
        all_scopes = var_info.assign_scopes | var_info.read_scopes
        if not all_scopes:
            return (False, None)
        lca = self._compute_lca(all_scopes)
        # Case 1: Assignments in sibling/divergent branches (e.g., if/else)
        # Must hoist if LCA is not one of the assignment scopes
        if lca not in var_info.assign_scopes:
            return (True, lca)
        # Case 2: Assignment in inner scope, read in outer scope
        for assign_scope in var_info.assign_scopes:
            for read_scope in var_info.read_scopes:
                if not self._is_ancestor_or_equal(assign_scope, read_scope):
                    return (True, lca)
        # Case 3: Multiple assignments where inner would shadow outer
        if len(var_info.assign_scopes) > 1:
            min_scope = min(var_info.assign_scopes, key=lambda s: self._ctx.scope_tree[s].depth)
            for scope in var_info.assign_scopes:
                if scope != min_scope and not self._is_ancestor(min_scope, scope):
                    return (True, lca)
        return (False, None)

    def _record_var_assign(self, var: str, scope_id: int, value: ast.expr | None):
        """Record a variable assignment at a scope."""
        if var not in self._ctx.var_usage:
            self._ctx.var_usage[var] = VarInfo(var, "")
        self._ctx.var_usage[var].assign_scopes.add(scope_id)
        # Infer type from first assignment
        if not self._ctx.var_usage[var].go_type and value:
            self._ctx.var_usage[var].first_value = value

    def _record_var_read(self, var: str, scope_id: int):
        """Record a variable read at a scope."""
        if var not in self._ctx.var_usage:
            self._ctx.var_usage[var] = VarInfo(var, "")
        self._ctx.var_usage[var].read_scopes.add(scope_id)

    def _collect_var_scopes(self, stmts: list[ast.stmt], scope_id: int):
        """Collect variable assignment/read scopes recursively."""
        for stmt in stmts:
            # Store scope mapping for emission phase
            self._ctx.scope_id_map[id(stmt)] = scope_id
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        # For tuple-returning function calls, collect synthetic vars
                        if isinstance(stmt.value, ast.Call):
                            ret_info = self._get_return_type_info(stmt.value)
                            if ret_info and len(ret_info) > 1:
                                var_name = self._to_go_var(target.id)
                                for i, elem_type in enumerate(ret_info):
                                    synth_name = f"{var_name}{i}"
                                    self._record_var_assign(synth_name, scope_id, None)
                                    self._ctx.var_types[synth_name] = elem_type
                                continue
                        var_name = self._to_go_var(target.id)
                        self._record_var_assign(var_name, scope_id, stmt.value)
                        # Infer type while we have context
                        expr_type = self._infer_type_from_expr(stmt.value)
                        if expr_type and expr_type not in ("interface{}", "[]interface{}"):
                            if var_name not in self._ctx.var_types or self._ctx.var_types[
                                var_name
                            ] in (
                                "interface{}",
                                "[]interface{}",
                            ):
                                self._ctx.var_types[var_name] = expr_type
                    # Tuple targets use := (handled separately)
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                var_name = self._to_go_var(stmt.target.id)
                self._record_var_assign(var_name, scope_id, stmt.value)
            elif isinstance(stmt, ast.If):
                # Check for isinstance pattern to narrow type during collection
                isinstance_info = self._detect_isinstance_if(stmt.test)
                then_scope = self._new_scope(parent=scope_id)
                if isinstance_info:
                    var_py, type_name = isinstance_info
                    var_go = self._to_go_var(var_py)
                    old_type = self._ctx.var_types.get(var_go)
                    self._ctx.var_types[var_go] = f"*{type_name}"
                    self._collect_var_scopes(stmt.body, then_scope)
                    if old_type is not None:
                        self._ctx.var_types[var_go] = old_type
                    else:
                        self._ctx.var_types.pop(var_go, None)
                else:
                    self._collect_var_scopes(stmt.body, then_scope)
                if stmt.orelse:
                    else_scope = self._new_scope(parent=scope_id)
                    self._collect_var_scopes(stmt.orelse, else_scope)
            elif isinstance(stmt, ast.While):
                body_scope = self._new_scope(parent=scope_id)
                self._collect_var_scopes(stmt.body, body_scope)
            elif isinstance(stmt, ast.For):
                # Loop var handled by range syntax, just recurse
                body_scope = self._new_scope(parent=scope_id)
                self._collect_var_scopes(stmt.body, body_scope)
            elif isinstance(stmt, ast.With):
                # Collect with-item variables
                for item in stmt.items:
                    if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                        var_name = self._to_go_var(item.optional_vars.id)
                        self._record_var_assign(var_name, scope_id, None)
                body_scope = self._new_scope(parent=scope_id)
                self._collect_var_scopes(stmt.body, body_scope)
            elif isinstance(stmt, ast.Try):
                body_scope = self._new_scope(parent=scope_id)
                self._collect_var_scopes(stmt.body, body_scope)
                # Track exception handler variable names to exclude from read collection
                # (Go uses recover() pattern, not exception variables)
                except_vars: set[str] = set()
                for handler in stmt.handlers:
                    handler_scope = self._new_scope(parent=scope_id)
                    if handler.name:
                        var_name = self._to_go_var(handler.name)
                        except_vars.add(var_name)
                        # Don't record the exception variable - Go uses recover() pattern
                    self._collect_var_scopes(handler.body, handler_scope)
                # Remove exception vars from read tracking (they become 'r' in Go)
                for var in except_vars:
                    if var in self._ctx.var_usage:
                        self._ctx.var_usage[var].read_scopes.clear()
                        self._ctx.var_usage[var].assign_scopes.clear()
                if stmt.orelse:
                    else_scope = self._new_scope(parent=scope_id)
                    self._collect_var_scopes(stmt.orelse, else_scope)
                if stmt.finalbody:
                    finally_scope = self._new_scope(parent=scope_id)
                    self._collect_var_scopes(stmt.finalbody, finally_scope)
            # Collect reads from all expressions in this statement
            self._collect_reads_in_scope(stmt, scope_id)

    def _collect_reads_in_scope(self, node: ast.AST, scope_id: int):
        """Collect variable reads from any AST node."""
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            var_name = self._to_go_var(node.id)
            self._record_var_read(var_name, scope_id)
        # Handle tuple element access: result[0] -> result0
        elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int):
                var_name = self._to_go_var(node.value.id)
                self._record_var_read(f"{var_name}{node.slice.value}", scope_id)
        for child in ast.iter_child_nodes(node):
            self._collect_reads_in_scope(child, scope_id)

    def _compute_hoisting(self):
        """Determine which vars need hoisting vs inline :="""
        # Collect all reads first to filter unused vars
        reads: set[str] = set()
        for var, info in self._ctx.var_usage.items():
            if info.read_scopes:
                reads.add(var)
        # Collect append types and nullable vars for type inference
        # (These require the full statement list, so we reuse existing methods)
        for var, info in self._ctx.var_usage.items():
            if var not in reads:
                continue  # Skip unused vars
            needs_hoist, hoist_scope = self._needs_hoisting(info)
            if needs_hoist and hoist_scope is not None:
                self._ctx.hoisted_vars[var] = hoist_scope

    def _exclude_assign_check_return_vars(self, stmts: list[ast.stmt]):
        """Remove vars from hoisting that are only used in assign-check-return patterns."""
        consumed_vars: set[str] = set()
        self._scan_assign_check_return_vars(stmts, consumed_vars)
        for var in consumed_vars:
            if var in self._ctx.hoisted_vars:
                del self._ctx.hoisted_vars[var]
            if var in self._ctx.var_usage:
                del self._ctx.var_usage[var]
            # Also clear var_types so pattern detection works during emission
            if var in self._ctx.var_types:
                del self._ctx.var_types[var]

    def _scan_assign_check_return_vars(self, stmts: list[ast.stmt], consumed: set[str]):
        """Recursively scan for vars consumed by assign-check-return patterns."""
        i = 0
        while i < len(stmts):
            stmt = stmts[i]
            # Check for the pattern: result = self.method(); if result: return result
            # Use a looser check that doesn't require the var type to be "Node"
            match = self._detect_assign_check_return_loose(stmts, i)
            if match:
                go_var = match
                consumed.add(go_var)
                i += 2  # Skip both statements
                continue
            # Recurse into nested blocks
            if isinstance(stmt, ast.If):
                self._scan_assign_check_return_vars(stmt.body, consumed)
                if stmt.orelse:
                    self._scan_assign_check_return_vars(stmt.orelse, consumed)
            elif isinstance(stmt, ast.While):
                self._scan_assign_check_return_vars(stmt.body, consumed)
            elif isinstance(stmt, ast.For):
                self._scan_assign_check_return_vars(stmt.body, consumed)
            elif isinstance(stmt, ast.Try):
                self._scan_assign_check_return_vars(stmt.body, consumed)
                for handler in stmt.handlers:
                    self._scan_assign_check_return_vars(handler.body, consumed)
            i += 1

    def _detect_assign_check_return_loose(self, stmts: list[ast.stmt], idx: int) -> str | None:
        """Looser version of _detect_assign_check_return for pre-scan.

        Returns the Go variable name if pattern matches, None otherwise.
        Doesn't require var_types to be populated.
        """
        if idx + 1 >= len(stmts):
            return None
        # First statement must be: result = self.method()
        assign = stmts[idx]
        if not isinstance(assign, ast.Assign):
            return None
        if len(assign.targets) != 1:
            return None
        target = assign.targets[0]
        if not isinstance(target, ast.Name):
            return None
        var_name = target.id
        # RHS must be a method call
        if not isinstance(assign.value, ast.Call):
            return None
        call = assign.value
        if not isinstance(call.func, ast.Attribute):
            return None
        if not isinstance(call.func.value, ast.Name) or call.func.value.id != "self":
            return None
        method_name = call.func.attr
        # Check if this method returns a concrete pointer type
        return_type = self._get_method_return_type(method_name)
        if not return_type or not return_type.startswith("*"):
            return None
        # Second statement must be: if result: return result
        if_stmt = stmts[idx + 1]
        if not isinstance(if_stmt, ast.If):
            return None
        # Test must be just the variable name (truthy check)
        test_var_name = None
        if isinstance(if_stmt.test, ast.Name):
            test_var_name = if_stmt.test.id
        elif isinstance(if_stmt.test, ast.Compare):
            cmp = if_stmt.test
            if (
                isinstance(cmp.left, ast.Name)
                and len(cmp.ops) == 1
                and isinstance(cmp.ops[0], ast.IsNot)
                and len(cmp.comparators) == 1
                and isinstance(cmp.comparators[0], ast.Constant)
                and cmp.comparators[0].value is None
            ):
                test_var_name = cmp.left.id
        if test_var_name != var_name:
            return None
        # Body must be: return result
        if len(if_stmt.body) != 1:
            return None
        ret = if_stmt.body[0]
        if not isinstance(ret, ast.Return):
            return None
        if not isinstance(ret.value, ast.Name) or ret.value.id != var_name:
            return None
        # No else branch
        if if_stmt.orelse:
            return None
        go_var = self._to_go_var(var_name)
        return go_var

    def _populate_var_types_from_usage(self, stmts: list[ast.stmt]):
        """Populate var_types for all variables based on usage patterns."""
        append_types = self._collect_append_element_types(stmts)
        nullable_node_vars = self._collect_nullable_node_vars(stmts)
        nullable_string_vars = self._collect_nullable_string_vars(stmts)
        multi_node_vars = self._collect_multi_node_type_vars(stmts)
        for var, _info in self._ctx.var_usage.items():
            go_type = self._ctx.var_types.get(var)
            # Check append() calls for element type
            if var in append_types:
                elem_type = append_types[var]
                if elem_type and (
                    not go_type or go_type in ("interface{}", "[]interface{}", "[]string")
                ):
                    self._ctx.var_types[var] = f"[]{elem_type}"
                    continue
            # Check if var is None-initialized but later assigned Node types
            if var in nullable_node_vars:
                if not go_type or go_type == "interface{}":
                    self._ctx.var_types[var] = "Node"
                    continue
            # Check if var is None-initialized but later assigned string types
            if var in nullable_string_vars:
                if not go_type or go_type == "interface{}":
                    self._ctx.var_types[var] = "string"
                    continue
            # Check if var is assigned multiple different concrete Node types
            if var in multi_node_vars:
                if go_type and go_type.startswith("*") and go_type[1:] in self.symbols.classes:
                    if self.symbols.classes[go_type[1:]].is_node:
                        self._ctx.var_types[var] = "Node"
                        continue
            # Infer from name if no specific type
            if not go_type or go_type in ("interface{}", "[]interface{}"):
                name_type = self._infer_var_type_from_name(var)
                if name_type:
                    self._ctx.var_types[var] = name_type

    def _predeclare_all_locals(self, stmts: list[ast.stmt]):
        """Pre-declare ALL local variables at function top (C-style).

        This completely avoids Go's block-scoping issues by declaring all
        variables upfront. Assignments then use = instead of :=.
        """
        # Collect all variable assignments recursively
        assignments: dict[str, ast.expr | None] = {}  # var name -> first value (for type inference)
        self._collect_all_assignments(stmts, assignments)
        # Collect all variable reads to filter out unused vars
        reads: set[str] = set()
        self._collect_all_reads(stmts, reads)
        # Collect element types from append() calls for better list type inference
        append_types = self._collect_append_element_types(stmts)
        # Collect variables that are None-initialized but later assigned Node types
        nullable_node_vars = self._collect_nullable_node_vars(stmts)
        # Collect variables that are None-initialized but later assigned string types
        nullable_string_vars = self._collect_nullable_string_vars(stmts)
        # Collect variables assigned multiple different concrete Node types
        multi_node_vars = self._collect_multi_node_type_vars(stmts)
        # Emit var declarations for all collected variables that are actually read
        for var_name, first_value in assignments.items():
            if var_name not in self._ctx.declared_vars and var_name in reads:
                # Try to get type from var_types first (from annotations, etc.)
                go_type = self._ctx.var_types.get(var_name)
                # But always try to infer from expression for more specific types
                if first_value is not None:
                    expr_type = self._infer_type_from_expr(first_value)
                    # Prefer expression type if it's more specific than var_types
                    if expr_type and expr_type not in ("interface{}", "[]interface{}"):
                        if not go_type or go_type in (
                            "interface{}",
                            "[]interface{}",
                            "map[string]interface{}",
                        ):
                            go_type = expr_type
                # Check append() calls for element type - this is more reliable than name heuristics
                if var_name in append_types:
                    elem_type = append_types[var_name]
                    if elem_type and (
                        not go_type or go_type in ("interface{}", "[]interface{}", "[]string")
                    ):
                        go_type = f"[]{elem_type}"
                # Check if var is None-initialized but later assigned Node types
                if var_name in nullable_node_vars:
                    if not go_type or go_type == "interface{}":
                        go_type = "Node"
                # Check if var is None-initialized but later assigned string types
                if var_name in nullable_string_vars:
                    if not go_type or go_type == "interface{}":
                        go_type = "string"
                # Check if var is assigned multiple different concrete Node types
                if var_name in multi_node_vars:
                    if go_type and go_type.startswith("*") and go_type[1:] in self.symbols.classes:
                        if self.symbols.classes[go_type[1:]].is_node:
                            go_type = "Node"
                if not go_type or go_type in ("interface{}", "[]interface{}"):
                    # Try harder - check if it's a known pattern
                    go_type = self._infer_var_type_from_name(var_name) or go_type or "interface{}"
                # Special case: 'results' (plural) in a method that returns []Node
                # Don't apply to 'result' (singular) which may be a single Node
                if var_name.lower() == "results" and self.current_method:
                    method_ret = self._get_current_method_return_type()
                    if method_ret == "[]Node":
                        go_type = method_ret
                # Special case: if expr says byte but name says string, prefer string
                # (handles cases like `direction = value[i]` used in string concatenation)
                if go_type == "byte":
                    name_type = self._infer_var_type_from_name(var_name)
                    if name_type == "string":
                        go_type = "string"
                self.emit(f"var {var_name} {go_type}")
                # Suppress unused variable warning immediately
                self.emit(f"_ = {var_name}")
                self._ctx.declared_vars.add(var_name)
                self._ctx.var_types[var_name] = go_type

    def _get_current_method_return_type(self) -> str:
        """Get the return type of the current method being emitted."""
        if hasattr(self, "current_func_info") and self.current_func_info:
            return self.current_func_info.return_type or ""
        return ""

    def _collect_all_assignments(
        self, stmts: list[ast.stmt], assignments: dict[str, ast.expr | None]
    ):
        """Recursively collect all variable assignments in a statement list."""
        for stmt in stmts:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        # For tuple-returning function calls, collect synthetic vars
                        if isinstance(stmt.value, ast.Call):
                            ret_info = self._get_return_type_info(stmt.value)
                            if ret_info and len(ret_info) > 1:
                                var_name = self._to_go_var(target.id)
                                for i, elem_type in enumerate(ret_info):
                                    synth_name = f"{var_name}{i}"
                                    if synth_name not in assignments:
                                        assignments[synth_name] = None
                                        # Store type for pre-declaration
                                        self._ctx.var_types[synth_name] = elem_type
                                continue
                        var_name = self._to_go_var(target.id)
                        if var_name not in assignments:
                            assignments[var_name] = stmt.value
                            # Infer type now while we have isinstance context
                            expr_type = self._infer_type_from_expr(stmt.value)
                            if expr_type and expr_type not in ("interface{}", "[]interface{}"):
                                if var_name not in self._ctx.var_types or self._ctx.var_types[
                                    var_name
                                ] in (
                                    "interface{}",
                                    "[]interface{}",
                                ):
                                    self._ctx.var_types[var_name] = expr_type
                    elif isinstance(target, ast.Tuple):
                        # Don't pre-declare tuple unpacking targets
                        # The unpacking statement itself uses := which declares them
                        pass
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                var_name = self._to_go_var(stmt.target.id)
                if var_name not in assignments:
                    assignments[var_name] = stmt.value
            elif isinstance(stmt, ast.For):
                # Don't pre-declare loop variables - for statement handles that
                # Just recurse into body
                self._collect_all_assignments(stmt.body, assignments)
            elif isinstance(stmt, ast.While):
                self._collect_all_assignments(stmt.body, assignments)
            elif isinstance(stmt, ast.If):
                # Check for isinstance pattern to narrow type during collection
                isinstance_info = self._detect_isinstance_if(stmt.test)
                if isinstance_info:
                    var_py, type_name = isinstance_info
                    var_go = self._to_go_var(var_py)
                    old_type = self._ctx.var_types.get(var_go)
                    self._ctx.var_types[var_go] = f"*{type_name}"
                    self._collect_all_assignments(stmt.body, assignments)
                    # Restore original type
                    if old_type is not None:
                        self._ctx.var_types[var_go] = old_type
                    else:
                        self._ctx.var_types.pop(var_go, None)
                else:
                    self._collect_all_assignments(stmt.body, assignments)
                if stmt.orelse:
                    self._collect_all_assignments(stmt.orelse, assignments)
            elif isinstance(stmt, ast.With):
                # Collect with-item variables
                for item in stmt.items:
                    if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                        var_name = self._to_go_var(item.optional_vars.id)
                        if var_name not in assignments:
                            assignments[var_name] = None
                self._collect_all_assignments(stmt.body, assignments)
            elif isinstance(stmt, ast.Try):
                self._collect_all_assignments(stmt.body, assignments)
                for handler in stmt.handlers:
                    if handler.name:
                        var_name = self._to_go_var(handler.name)
                        if var_name not in assignments:
                            assignments[var_name] = None
                    self._collect_all_assignments(handler.body, assignments)
                self._collect_all_assignments(stmt.orelse, assignments)
                self._collect_all_assignments(stmt.finalbody, assignments)

    def _collect_all_reads(self, stmts: list[ast.stmt], reads: set[str]):
        """Recursively collect all variable reads in a statement list."""
        for stmt in stmts:
            self._collect_reads_in_node(stmt, reads)

    def _collect_reads_in_node(self, node: ast.AST, reads: set[str]):
        """Collect variable reads from any AST node."""
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            var_name = self._to_go_var(node.id)
            reads.add(var_name)
        # Handle tuple element access: result[0] -> result0
        elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int):
                var_name = self._to_go_var(node.value.id)
                reads.add(f"{var_name}{node.slice.value}")
        for child in ast.iter_child_nodes(node):
            self._collect_reads_in_node(child, reads)

    def _collect_append_element_types(self, stmts: list[ast.stmt]) -> dict[str, str]:
        """Collect element types from append() calls to infer list types."""
        result: dict[str, str] = {}
        self._collect_appends_recursive(stmts, result)
        return result

    def _collect_appends_recursive(self, stmts: list[ast.stmt], result: dict[str, str]):
        """Recursively find append calls and infer element types."""
        for stmt in stmts:
            # Look for: var.append(value)
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                if (
                    isinstance(call.func, ast.Attribute)
                    and call.func.attr == "append"
                    and isinstance(call.func.value, ast.Name)
                    and call.args
                ):
                    var_name = self._to_go_var(call.func.value.id)
                    # Infer element type from the argument
                    elem_type = self._infer_append_element_type(call.args[0])
                    if elem_type and var_name not in result:
                        result[var_name] = elem_type
            # Recurse into control flow
            if isinstance(stmt, ast.If):
                self._collect_appends_recursive(stmt.body, result)
                self._collect_appends_recursive(stmt.orelse, result)
            elif isinstance(stmt, ast.For):
                self._collect_appends_recursive(stmt.body, result)
            elif isinstance(stmt, ast.While):
                self._collect_appends_recursive(stmt.body, result)
            elif isinstance(stmt, ast.Try):
                self._collect_appends_recursive(stmt.body, result)
                for handler in stmt.handlers:
                    self._collect_appends_recursive(handler.body, result)
            elif isinstance(stmt, ast.With):
                self._collect_appends_recursive(stmt.body, result)

    def _infer_append_element_type(self, node: ast.expr) -> str:
        """Infer the Go type of an element being appended.

        Returns 'Node' for Node subtypes since []Node is the common interface type
        used in function signatures, even when appending concrete types like *Word.
        """
        # Variable reference - check var_types or infer from name
        if isinstance(node, ast.Name):
            var_name = self._to_go_var(node.id)
            if var_name in self._ctx.var_types:
                vtype = self._ctx.var_types[var_name]
                # Convert concrete Node types to Node interface for slice compatibility
                if vtype.startswith("*") and vtype[1:] in self.symbols.classes:
                    if self.symbols.classes[vtype[1:]].is_node:
                        return "Node"
                return vtype
            # Common patterns - return Node for AST node types
            if node.id in (
                "word",
                "w",
                "redirect",
                "redir",
                "cmd",
                "command",
                "node",
                "n",
                "result",
                "elem",
                "item",
                "part",
            ):
                return "Node"
        # Method call that returns a known type
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                method = node.func.attr
                # Parse methods that return Node types
                if method.startswith("parse") or method.startswith("Parse"):
                    return "Node"
                if method in ("_Advance", "_advance", "Advance", "advance"):
                    return "string"
            # Constructor call for a Node class
            elif isinstance(node.func, ast.Name):
                if node.func.id in self.symbols.classes:
                    if self.symbols.classes[node.func.id].is_node:
                        return "Node"
        # String literal
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return "string"
        return ""

    def _collect_nullable_typed_vars(
        self, stmts: list[ast.stmt], type_checker: Callable[[ast.expr], bool]
    ) -> set[str]:
        """Collect variables first assigned None then later assigned a typed value."""
        none_vars: set[str] = set()
        self._collect_none_assigned_vars(stmts, none_vars)
        result: set[str] = set()
        self._collect_typed_assigned_vars(stmts, none_vars, result, type_checker)
        return result

    def _collect_nullable_node_vars(self, stmts: list[ast.stmt]) -> set[str]:
        """Collect variables first assigned None but later assigned Nodes."""
        return self._collect_nullable_typed_vars(stmts, self._is_node_returning_expr)

    def _collect_nullable_string_vars(self, stmts: list[ast.stmt]) -> set[str]:
        """Collect variables first assigned None but later assigned strings."""
        return self._collect_nullable_typed_vars(stmts, self._is_string_returning_expr)

    def _collect_typed_assigned_vars(
        self,
        stmts: list[ast.stmt],
        candidates: set[str],
        result: set[str],
        type_checker: Callable[[ast.expr], bool],
    ):
        """Find candidate vars later assigned values matching type_checker."""
        for stmt in stmts:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        var_name = self._to_go_var(target.id)
                        if var_name in candidates and type_checker(stmt.value):
                            result.add(var_name)
            # Recurse into control flow
            if isinstance(stmt, ast.If):
                self._collect_typed_assigned_vars(stmt.body, candidates, result, type_checker)
                self._collect_typed_assigned_vars(stmt.orelse, candidates, result, type_checker)
            elif isinstance(stmt, ast.For):
                self._collect_typed_assigned_vars(stmt.body, candidates, result, type_checker)
            elif isinstance(stmt, ast.While):
                self._collect_typed_assigned_vars(stmt.body, candidates, result, type_checker)
            elif isinstance(stmt, ast.Try):
                self._collect_typed_assigned_vars(stmt.body, candidates, result, type_checker)
                for handler in stmt.handlers:
                    self._collect_typed_assigned_vars(
                        handler.body, candidates, result, type_checker
                    )
            elif isinstance(stmt, ast.With):
                self._collect_typed_assigned_vars(stmt.body, candidates, result, type_checker)

    def _is_string_returning_expr(self, node: ast.expr) -> bool:
        """Check if an expression returns a string type."""
        # String literals
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return True
        # Variable reference - check if we know its type
        if isinstance(node, ast.Name):
            var_type = self._ctx.var_types.get(self._to_go_var(node.id), "")
            return var_type == "string"
        # JoinedStr (f-string)
        if isinstance(node, ast.JoinedStr):
            return True
        # String methods
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            method = node.func.attr
            if method in ("join", "strip", "lstrip", "rstrip", "lower", "upper", "replace"):
                return True
        return False

    def _collect_none_assigned_vars(self, stmts: list[ast.stmt], result: set[str]):
        """Find variables first assigned None."""
        for stmt in stmts:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        if isinstance(stmt.value, ast.Constant) and stmt.value.value is None:
                            result.add(self._to_go_var(target.id))
            # Recurse into control flow
            if isinstance(stmt, ast.If):
                self._collect_none_assigned_vars(stmt.body, result)
                self._collect_none_assigned_vars(stmt.orelse, result)
            elif isinstance(stmt, ast.For):
                self._collect_none_assigned_vars(stmt.body, result)
            elif isinstance(stmt, ast.While):
                self._collect_none_assigned_vars(stmt.body, result)
            elif isinstance(stmt, ast.Try):
                self._collect_none_assigned_vars(stmt.body, result)
                for handler in stmt.handlers:
                    self._collect_none_assigned_vars(handler.body, result)
            elif isinstance(stmt, ast.With):
                self._collect_none_assigned_vars(stmt.body, result)

    def _is_node_returning_expr(self, node: ast.expr) -> bool:
        """Check if an expression returns a Node type."""
        # Method calls to parse_* methods return Node
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            method = node.func.attr
            # Parse methods return Node types
            if method.startswith("parse") or method.startswith("_parse"):
                return True
            if method.startswith("Parse") or method.startswith("_Parse"):
                return True
            # Check if method is in class and returns Node
            class_name = self._infer_object_class(node.func.value)
            if class_name:
                class_info = self.symbols.classes.get(class_name)
                if class_info and method in class_info.methods:
                    ret_type = class_info.methods[method].return_type or ""
                    if ret_type == "Node" or ret_type.endswith("| None") and "Node" in ret_type:
                        return True
                    # Check if return type is a Node subclass
                    if ret_type.startswith("*") and ret_type[1:] in self.symbols.classes:
                        if self.symbols.classes[ret_type[1:]].is_node:
                            return True
        # Node constructor
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in self.symbols.classes:
                if self.symbols.classes[node.func.id].is_node:
                    return True
        return False

    def _collect_multi_node_type_vars(self, stmts: list[ast.stmt]) -> set[str]:
        """Collect variables assigned multiple different concrete Node types.

        Pattern:
            result = self.parse_brace_group()  # *BraceGroup
            if cond:
                result = self.parse_subshell()  # *Subshell

        These should be typed as Node, not the first concrete type.
        """
        # Collect all Node types assigned to each variable
        var_node_types: dict[str, set[str]] = {}
        self._collect_var_node_types(stmts, var_node_types)
        # Variables with multiple different Node types should be typed as Node
        result: set[str] = set()
        for var_name, types in var_node_types.items():
            if len(types) > 1:
                result.add(var_name)
        return result

    def _collect_var_node_types(self, stmts: list[ast.stmt], result: dict[str, set[str]]):
        """Collect the concrete Node types assigned to each variable."""
        for stmt in stmts:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        var_name = self._to_go_var(target.id)
                        node_type = self._get_concrete_node_type(stmt.value)
                        if node_type:
                            if var_name not in result:
                                result[var_name] = set()
                            result[var_name].add(node_type)
            # Recurse into control flow
            if isinstance(stmt, ast.If):
                self._collect_var_node_types(stmt.body, result)
                self._collect_var_node_types(stmt.orelse, result)
            elif isinstance(stmt, ast.For):
                self._collect_var_node_types(stmt.body, result)
            elif isinstance(stmt, ast.While):
                self._collect_var_node_types(stmt.body, result)
            elif isinstance(stmt, ast.Try):
                self._collect_var_node_types(stmt.body, result)
                for handler in stmt.handlers:
                    self._collect_var_node_types(handler.body, result)
            elif isinstance(stmt, ast.With):
                self._collect_var_node_types(stmt.body, result)

    def _get_concrete_node_type(self, node: ast.expr) -> str:
        """Get the concrete Node type from an expression, or empty string if not a Node."""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                method = node.func.attr
                class_name = self._infer_object_class(node.func.value)
                if class_name:
                    class_info = self.symbols.classes.get(class_name)
                    if class_info and method in class_info.methods:
                        ret_type = class_info.methods[method].return_type or ""
                        # Return concrete Node types (e.g., *BraceGroup, *Subshell)
                        if ret_type.startswith("*") and ret_type[1:] in self.symbols.classes:
                            if self.symbols.classes[ret_type[1:]].is_node:
                                return ret_type
                        # Return "Node" for methods that return Node interface
                        if ret_type == "Node":
                            return "Node"
            elif isinstance(node.func, ast.Name):
                # Node constructor
                if node.func.id in self.symbols.classes:
                    if self.symbols.classes[node.func.id].is_node:
                        return "*" + node.func.id
        return ""

    def _infer_var_type_from_name(self, var_name: str) -> str:
        """Infer type from common variable naming patterns."""
        name_lower = var_name.lower()
        # Boolean patterns
        if name_lower.startswith(("is", "has", "was", "can", "should", "in_", "at_")):
            return "bool"
        if name_lower in ("ok", "found", "done", "valid", "exists", "passnext", "wasdollar"):
            return "bool"
        # Integer patterns
        if name_lower in (
            "i",
            "j",
            "k",
            "n",
            "idx",
            "index",
            "count",
            "depth",
            "len",
            "length",
            "start",
            "end",
            "pos",
            "offset",
            "size",
            "num",
            "line",
            "col",
            "flags",
            "state",
            "ctx",
            "mode",
        ):
            return "int"
        if name_lower.endswith(
            ("count", "depth", "pos", "idx", "index", "len", "size", "flags", "state")
        ):
            return "int"
        if "dolbrace" in name_lower:
            return "int"
        # Token patterns
        if name_lower in ("tok", "token", "savedlast"):
            return "*Token"
        if name_lower.endswith("token") or name_lower.endswith("tok"):
            return "*Token"
        # String patterns (be careful not to include names that could be slices like "result")
        if name_lower in (
            "s",
            "ch",
            "char",
            "name",
            "text",
            "value",
            "content",
            "nested",
            "arg",
            "inner",
            "escaped",
            "afterbrace",
            "opstart",
            "rest",
            "ansistr",
            "expanded",
            "resultstr",
            "leadingws",
            "normalizedws",
            "stripped",
            "direction",
            "rawcontent",
            "rawstripped",
            "spaced",
            "prefix",
            "suffix",
            "originner",
            "closing",
            "finaloutput",
            "formatted",
            "leftsexp",
            "rightsexp",
            "fdtarget",
            "outval",
            "raw",
            "targetval",
        ):
            return "string"
        if name_lower.endswith(("str", "text", "name", "char", "content", "sexp")):
            return "string"
        # Byte patterns - single character variables from string subscripts
        if name_lower in ("byteval", "firstchar", "ctrlchar"):
            return "byte"
        # Node list patterns
        if name_lower in ("parts", "elements", "children", "nodes"):
            return "[]Node"
        if name_lower.endswith("parts") or name_lower.endswith("nodes"):
            return "[]Node"
        # String list patterns
        if name_lower in ("chars", "lines", "words"):
            return "[]string"
        if name_lower.endswith("chars") or name_lower.endswith("lines"):
            return "[]string"
        # Int list patterns (positions, indices)
        if name_lower.endswith("positions"):
            return "[]int"
        # Segment list patterns (slices of nodes)
        if name_lower == "segments":
            return "[][]Node"
        # Segment variable (slice of nodes)
        if name_lower == "seg":
            return "[]Node"
        # Node patterns (nullable in Python, but Node in Go since nil is valid)
        if name_lower in ("iftrue", "iffalse"):
            return "Node"
        return ""
