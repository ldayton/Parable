"""Expression emission for Go transpiler."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from .go_overrides import TUPLE_ELEMENT_TYPES
from .go_type_system import TYPE_MAP

if TYPE_CHECKING:
    pass


class EmitExpressionsMixin:
    """Mixin for expression code emission."""

    # ========== Expression Emission ==========

    def visit_expr(self, node: ast.expr) -> str:
        """Convert a Python expression to Go code string."""
        method = f"visit_expr_{node.__class__.__name__}"
        if hasattr(self, method):
            return getattr(self, method)(node)
        raise NotImplementedError(f"Expression type {node.__class__.__name__}")

    def visit_expr_Constant(self, node: ast.Constant) -> str:
        """Convert constant literals."""
        if isinstance(node.value, bool):
            return "true" if node.value else "false"
        if isinstance(node.value, int):
            return str(node.value)
        if isinstance(node.value, str):
            value = node.value
            # Escape for Go string literal
            escaped = (
                value.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\t", "\\t")
                .replace("\r", "\\r")
            )
            # Escape control characters
            result = []
            for c in escaped:
                ord_c = ord(c)
                if ord_c < 32 or ord_c == 127:
                    result.append(f"\\x{ord_c:02x}")
                else:
                    result.append(c)
            return f'"{"".join(result)}"'
        if node.value is None:
            return "nil"
        if isinstance(node.value, bytes):
            # Convert bytes to []byte literal
            return "[]byte{" + ", ".join(str(b) for b in node.value) + "}"
        return repr(node.value)

    def visit_expr_Name(self, node: ast.Name) -> str:
        """Convert variable names."""
        mapping = {
            "True": "true",
            "False": "false",
            "None": "nil",
            "self": self._get_receiver_name(),
        }
        name = mapping.get(node.id, node.id)
        # Handle class name constants (e.g., TokenType.WORD)
        if name in self.symbols.classes:
            return name
        # Handle module-level constants (SCREAMING_CASE or _SCREAMING_CASE)
        if name.isupper() or (name.startswith("_") and name[1:].isupper()):
            go_name = name.lstrip("_")
            parts = go_name.split("_")
            return "".join(p.capitalize() for p in parts)
        # Convert to camelCase and handle reserved words
        result = self._to_go_var(name)
        # Rewrite variable references in type switch context
        if self._type_switch_var and result == self._type_switch_var[0]:
            return self._type_switch_var[1]
        return result

    def _get_receiver_name(self) -> str:
        """Get receiver name for current class context."""
        if self.current_class:
            return self.current_class[0].lower()
        return "self"

    def visit_expr_Attribute(self, node: ast.Attribute) -> str:
        """Convert attribute access."""
        attr_name = node.attr
        # Check for class constant access like DolbraceState.PARAM
        if isinstance(node.value, ast.Name):
            class_name = node.value.id
            if class_name in self.symbols.classes:
                class_info = self.symbols.classes[class_name]
                if attr_name in class_info.constants:
                    return f"{class_name}_{attr_name}"
        value = self.visit_expr(node.value)
        # Check if this is accessing a method that should be called (like node.kind -> node.Kind())
        if self._is_interface_method(node.value, attr_name):
            go_attr = self._to_go_func_name(attr_name)
            return f"{value}.{go_attr}()"
        attr = self._to_go_field_name(attr_name)
        # Check if accessing a union field with a type hint
        if isinstance(node.value, ast.Name) and node.value.id == "self" and self.current_class:
            union_key = (self.current_class, attr_name)
            if union_key in self.union_field_types:
                field_type = self.union_field_types[union_key]
                return f"{value}.{attr}.({field_type})"
        # Check if value needs type assertion for struct-specific field access
        value_type = self._get_expr_element_type(node.value)
        if value_type in ("interface{}", "Node"):
            type_assertion = self._get_type_for_field(attr_name, node.value)
            if type_assertion:
                return f"{value}.({type_assertion}).{attr}"
        return f"{value}.{attr}"

    def _get_expr_type(self, node: ast.expr) -> str:
        """Get the Go type of an expression."""
        # Variable reference
        if isinstance(node, ast.Name):
            var_name = self._to_go_var(node.id)
            return self.var_types.get(var_name, "")
        # Attribute access - look up field type in struct
        if isinstance(node, ast.Attribute):
            # self.x -> look up field type in current class
            if isinstance(node.value, ast.Name) and node.value.id == "self" and self.current_class:
                class_info = self.symbols.classes.get(self.current_class)
                if class_info and node.attr in class_info.fields:
                    return class_info.fields[node.attr].go_type or ""
            # obj.x -> look up field type in object's class
            obj_class = self._infer_object_class(node.value)
            if obj_class and obj_class in self.symbols.classes:
                class_info = self.symbols.classes[obj_class]
                if node.attr in class_info.fields:
                    return class_info.fields[node.attr].go_type or ""
        return ""

    def _get_expr_element_type(self, node: ast.expr) -> str:
        """Get the type that an expression evaluates to (for type assertion decisions)."""
        # Variable reference
        if isinstance(node, ast.Name):
            var_name = self._to_go_var(node.id)
            # If in type switch and this is the switched variable, use narrowed type
            if self._type_switch_var and var_name == self._type_switch_var[0]:
                return self._type_switch_type or ""
            return self.var_types.get(var_name, "")
        # Subscript on a slice - get the element type
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            var_name = self._to_go_var(node.value.id)
            var_type = self.var_types.get(var_name, "")
            if var_type.startswith("[]"):
                return var_type[2:]  # []Node -> Node
        # Attribute access - look up field type in struct
        if isinstance(node, ast.Attribute):
            # Get the class of the object being accessed
            obj_class = self._infer_object_class(node.value)
            if obj_class and obj_class in self.symbols.classes:
                class_info = self.symbols.classes[obj_class]
                if node.attr in class_info.fields:
                    return class_info.fields[node.attr].go_type or ""
        return ""

    def _get_type_for_field(
        self, field_name: str, value_node: ast.expr | None = None
    ) -> str | None:
        """Get the type assertion needed for a field access on interface{} or Node."""
        # Special case: .command field exists on both CommandSubstitution and ProcessSubstitution
        # Determine which type based on the assignment source tracked in var_assign_sources
        if field_name == "command" and value_node is not None:
            if isinstance(value_node, ast.Name):
                var_name = self._to_go_var(value_node.id)
                source = getattr(self, "var_assign_sources", {}).get(var_name, "")
                if source == "procsub_parts":
                    return "*ProcessSubstitution"
                elif source == "cmdsub_parts":
                    return "*CommandSubstitution"
        field_to_type = {
            "command": "*CommandSubstitution",
            "body": "*ProcessSubstitution",
            "elements": "*ArrayNode",
            "parts": "*Word",
            "words": "*Command",
            "redirects": "*Command",
            "op": "*Operator",
            "value": "*Word",  # For Target.Value where Target is Node
            "target": "*Redirect",  # For Redirect.Target
        }
        return field_to_type.get(field_name)

    def _find_method_owner(self, method_name: str) -> str | None:
        """Find which struct type owns a given method."""
        # Search all classes for this method
        for class_name, class_info in self.symbols.classes.items():
            if method_name in class_info.methods:
                if class_info.is_node:
                    return "*" + class_name
                return "*" + class_name
        return None

    def _is_interface_method(self, value: ast.expr, attr: str) -> bool:
        """Check if attribute is a method on an interface type."""
        # Node interface methods
        if attr in ("kind", "to_sexp"):
            # Check if value is self in a non-Node class (like ParseContext) - kind is a field there
            if isinstance(value, ast.Name) and value.id == "self":
                if self.current_class and not self.symbols.is_node_subclass(self.current_class):
                    return False  # It's a field access in a non-Node class
            # Check if value is likely a Node
            if isinstance(value, ast.Name):
                name = value.id
                if name in (
                    "node",
                    "n",
                    "child",
                    "elem",
                    "item",
                    "body",
                    "left",
                    "right",
                    "operand",
                ):
                    return True
            return True  # Assume it's a method if uncertain
        return False

    def _needs_node_assertion(self, value: ast.expr) -> bool:
        """Check if calling Node method on this expr needs a type assertion."""
        # If it's a variable with interface{} type, needs assertion
        if isinstance(value, ast.Name):
            var_name = self._to_go_var(value.id)
            var_type = self.var_types.get(var_name, "")
            # If type is interface{}, needs assertion
            if var_type == "interface{}":
                return True
        return False

    def _func_expects_string_param(self, func_name: str, param_index: int) -> bool:
        """Check if a function parameter expects string (for byte conversion)."""
        # Single-character helper functions that take string param at index 0
        char_funcs = {
            "_is_whitespace",
            "_is_whitespace_no_newline",
            "_is_metachar",
            "_is_hex_digit",
            "_is_octal_digit",
            "_get_ansi_escape",
            "_is_funsub_char",
            "_is_extglob_prefix",
            "_is_digit",
            "_is_special_param_unbraced",
            "_is_simple_param_op",
            "_is_escape_char_in_backtick",
        }
        if func_name in char_funcs and param_index == 0:
            return True
        return False

    def _fill_default_args(self, func_name: str, args: list[str]) -> list[str]:
        """Fill in default argument values for functions with optional params."""
        # Look up function info
        func_info = self.symbols.functions.get(func_name)
        if not func_info:
            # Check if it's a class constructor (__init__)
            class_info = self.symbols.classes.get(func_name)
            if class_info:
                if "__init__" in class_info.methods:
                    func_info = class_info.methods["__init__"]
                else:
                    # Check parent classes for inherited __init__
                    for base in class_info.bases:
                        base_info = self.symbols.classes.get(base)
                        if base_info and "__init__" in base_info.methods:
                            func_info = base_info.methods["__init__"]
                            break
            if not func_info:
                return args
        # Check if we need to add default values
        expected_params = len(func_info.params)
        provided_args = len(args)
        if provided_args >= expected_params:
            return args
        # Add defaults for missing args
        result = list(args)
        for i in range(provided_args, expected_params):
            param = func_info.params[i]
            if param.default is not None:
                default_val = self.visit_expr(param.default)
                # Convert nil to zero value based on parameter type
                if default_val == "nil":
                    default_val = self._nil_to_zero_value(param.go_type)
                result.append(default_val)
            else:
                # No default, can't fill in
                break
        return result

    def _merge_keyword_args(
        self, func_name: str, args: list[str], keywords: list[ast.keyword]
    ) -> list[str]:
        """Merge keyword arguments into positional argument list."""
        if not keywords:
            return args
        # Look up function info to get parameter names and positions
        func_info = self.symbols.functions.get(func_name)
        if not func_info:
            # Check if it's a class constructor
            class_info = self.symbols.classes.get(func_name)
            if class_info:
                if "__init__" in class_info.methods:
                    func_info = class_info.methods["__init__"]
                else:
                    # Check parent classes for inherited __init__
                    for base in class_info.bases:
                        base_info = self.symbols.classes.get(base)
                        if base_info and "__init__" in base_info.methods:
                            func_info = base_info.methods["__init__"]
                            break
            if not func_info:
                return args
        # Build param name to index mapping
        param_indices: dict[str, int] = {}
        for i, param in enumerate(func_info.params):
            param_indices[param.name] = i
        # Merge keyword args at correct positions
        result = list(args)
        for kw in keywords:
            if kw.arg is None:
                continue  # **kwargs not supported
            if kw.arg in param_indices:
                idx = param_indices[kw.arg]
                # Extend result list if needed, using zero values based on param type
                while len(result) <= idx:
                    fill_idx = len(result)
                    if fill_idx < len(func_info.params):
                        fill_type = func_info.params[fill_idx].go_type
                        result.append(self._nil_to_zero_value(fill_type))
                    else:
                        result.append("nil")
                result[idx] = self.visit_expr(kw.value)
        return result

    def _infer_object_class(self, node: ast.expr) -> str | None:
        """Infer the class name of an object expression."""
        if isinstance(node, ast.Attribute):
            # self._parser -> Parser, l._parser -> Parser
            attr = node.attr
            if attr.startswith("_"):
                attr = attr[1:]
            attr_pascal = self._snake_to_pascal(attr)
            if attr_pascal in self.symbols.classes:
                return attr_pascal
            # self.something -> might need to look up field type
            if isinstance(node.value, ast.Name) and node.value.id == "self":
                # Look up the field type in current class
                if self.current_class:
                    class_info = self.symbols.classes.get(self.current_class)
                    if class_info and node.attr in class_info.fields:
                        field_info = class_info.fields[node.attr]
                        field_type = field_info.py_type
                        # Extract class name from type like "Parser | None"
                        for word in field_type.replace("|", " ").split():
                            if word in self.symbols.classes:
                                return word
        # self -> current class
        if isinstance(node, ast.Name):
            if node.id == "self" and self.current_class:
                return self.current_class
            # Check local variable type
            var_name = self._to_go_var(node.id)
            var_type = self.var_types.get(var_name, "")
            # Extract class name from pointer type like "*Word"
            if var_type.startswith("*"):
                class_name = var_type[1:]
                if class_name in self.symbols.classes:
                    return class_name
            elif var_type in self.symbols.classes:
                return var_type
        # Subscript expression: parts[0] -> Node if parts is []Node
        if isinstance(node, ast.Subscript):
            elem_type = self._get_expr_element_type(node)
            if elem_type == "Node":
                return "Node"  # Special case - it's the Node interface
            if elem_type in self.symbols.classes:
                return elem_type
        # Constructor call: Word(...) -> Word
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            class_name = node.func.id
            if class_name in self.symbols.classes:
                return class_name
        return None

    def _merge_keyword_args_for_method(
        self, class_name: str, method: str, args: list[str], keywords: list[ast.keyword]
    ) -> list[str]:
        """Merge keyword arguments for a method call."""
        if not keywords:
            return args
        class_info = self.symbols.classes.get(class_name)
        if not class_info:
            return args
        # Try original name first, then camelCase, then PascalCase
        method_key = method
        if method_key not in class_info.methods:
            method_key = self._snake_to_camel(method)
        if method_key not in class_info.methods:
            method_key = self._snake_to_pascal(method)
        if method_key not in class_info.methods:
            return args
        func_info = class_info.methods[method_key]
        # Build param name to index mapping
        param_indices: dict[str, int] = {}
        for i, param in enumerate(func_info.params):
            param_indices[param.name] = i
        # Merge keyword args
        result = list(args)
        for kw in keywords:
            if kw.arg is None:
                continue
            if kw.arg in param_indices:
                idx = param_indices[kw.arg]
                while len(result) <= idx:
                    fill_idx = len(result)
                    if fill_idx < len(func_info.params):
                        fill_type = func_info.params[fill_idx].go_type
                        result.append(self._nil_to_zero_value(fill_type))
                    else:
                        result.append("nil")
                result[idx] = self.visit_expr(kw.value)
        return result

    def _fill_default_args_for_method(
        self, class_name: str, method: str, args: list[str]
    ) -> list[str]:
        """Fill in default argument values for a method call."""
        class_info = self.symbols.classes.get(class_name)
        if not class_info:
            return args
        # Try original name first, then camelCase, then PascalCase
        method_key = method
        if method_key not in class_info.methods:
            method_key = self._snake_to_camel(method)
        if method_key not in class_info.methods:
            method_key = self._snake_to_pascal(method)
        if method_key not in class_info.methods:
            return args
        func_info = class_info.methods[method_key]
        expected_params = len(func_info.params)
        provided_args = len(args)
        if provided_args >= expected_params:
            return args
        result = list(args)
        for i in range(provided_args, expected_params):
            param = func_info.params[i]
            if param.default is not None:
                default_val = self.visit_expr(param.default)
                if default_val == "nil":
                    default_val = self._nil_to_zero_value(param.go_type)
                result.append(default_val)
            else:
                break
        return result

    def _add_address_of_for_ptr_slice_params(
        self, class_name: str, method: str, args: list[str], orig_args: list[ast.expr]
    ) -> list[str]:
        """Add & when passing slice to pointer-to-slice parameter."""
        class_info = self.symbols.classes.get(class_name)
        if not class_info:
            return args
        # Try original name first, then camelCase, then PascalCase
        method_key = method
        if method_key not in class_info.methods:
            method_key = self._snake_to_camel(method)
        if method_key not in class_info.methods:
            method_key = self._snake_to_pascal(method)
        if method_key not in class_info.methods:
            return args
        func_info = class_info.methods[method_key]
        result = list(args)
        for i, arg_str in enumerate(result):
            if i >= len(func_info.params) or i >= len(orig_args):
                break
            param = func_info.params[i]
            param_type = param.go_type
            if not param_type or not param_type.startswith("*[]"):
                continue
            # Check if the argument is a slice variable (not already a pointer)
            if isinstance(orig_args[i], ast.Name):
                var_name = self._to_go_var(orig_args[i].id)
                arg_type = self.var_types.get(var_name, "")
                if arg_type and arg_type.startswith("[]") and not arg_type.startswith("[]*"):
                    result[i] = f"&{arg_str}"
        return result

    def visit_expr_Subscript(self, node: ast.Subscript) -> str:
        """Convert subscript access (indexing/slicing)."""
        # Check if accessing tuple variable element (cmdsub_result[0] -> cmdsubResult0)
        if isinstance(node.value, ast.Name) and isinstance(node.slice, ast.Constant):
            var_name = self._to_go_var(node.value.id)
            if var_name in self.tuple_vars and isinstance(node.slice.value, int):
                idx = node.slice.value
                elem_vars = self.tuple_vars[var_name]
                if 0 <= idx < len(elem_vars):
                    return elem_vars[idx]
        value = self.visit_expr(node.value)
        if isinstance(node.slice, ast.Slice):
            # Check if slicing a string - need rune-based slicing
            is_string_slice = self._is_string_slice(node)
            # For Lexer/Parser Source slices, use Source_runes directly
            is_source_slice = self._is_lexer_source_slice(node)
            # Compute len function based on type
            len_func = "_runeLen" if is_string_slice else "len"
            if is_source_slice:
                receiver = self.current_class[0].lower()
                len_func = f"len({receiver}.Source_runes)"
            # Handle negative indices (Python [:-1] -> Go [:len(x)-1])
            lower = ""
            upper = ""
            if node.slice.lower:
                if isinstance(node.slice.lower, ast.UnaryOp) and isinstance(
                    node.slice.lower.op, ast.USub
                ):
                    # Negative lower bound: -N -> len(x)-N
                    n = self.visit_expr(node.slice.lower.operand)
                    if is_source_slice:
                        lower = f"{len_func}-{n}"
                    elif is_string_slice:
                        lower = f"{len_func}({value})-{n}"
                    else:
                        lower = f"len({value})-{n}"
                elif (
                    isinstance(node.slice.lower, ast.Constant)
                    and isinstance(node.slice.lower.value, int)
                    and node.slice.lower.value < 0
                ):
                    # Negative constant lower bound
                    if is_source_slice:
                        lower = f"{len_func}{node.slice.lower.value}"
                    elif is_string_slice:
                        lower = f"{len_func}({value}){node.slice.lower.value}"
                    else:
                        lower = f"len({value}){node.slice.lower.value}"
                else:
                    lower = self.visit_expr(node.slice.lower)
            else:
                lower = "0"
            if node.slice.upper:
                if isinstance(node.slice.upper, ast.UnaryOp) and isinstance(
                    node.slice.upper.op, ast.USub
                ):
                    # Negative upper bound: -N -> len(x)-N
                    n = self.visit_expr(node.slice.upper.operand)
                    if is_source_slice:
                        upper = f"{len_func}-{n}"
                    elif is_string_slice:
                        upper = f"{len_func}({value})-{n}"
                    else:
                        upper = f"len({value})-{n}"
                elif (
                    isinstance(node.slice.upper, ast.Constant)
                    and isinstance(node.slice.upper.value, int)
                    and node.slice.upper.value < 0
                ):
                    # Negative constant upper bound
                    if is_source_slice:
                        upper = f"{len_func}{node.slice.upper.value}"
                    elif is_string_slice:
                        upper = f"{len_func}({value}){node.slice.upper.value}"
                    else:
                        upper = f"len({value}){node.slice.upper.value}"
                else:
                    upper = self.visit_expr(node.slice.upper)
            # Emit the slice
            if is_source_slice:
                receiver = self.current_class[0].lower()
                if upper:
                    return f"string({receiver}.Source_runes[{lower}:{upper}])"
                return f"string({receiver}.Source_runes[{lower}:])"
            if is_string_slice:
                if upper:
                    return f"_Substring({value}, {lower}, {upper})"
                return f"_Substring({value}, {lower}, {len_func}({value}))"
            if upper:
                return f"{value}[{lower}:{upper}]"
            return f"{value}[{lower}:]"
        index = self.visit_expr(node.slice)
        # Check if indexing a string - use rune-based access
        if self._is_string_subscript(node):
            # Check if this is self.source[i] in Lexer/Parser - use Source_runes
            if self._is_lexer_source_subscript(node):
                # Use pre-converted Source_runes for O(1) access
                receiver = self._get_receiver_name()
                return f"string({receiver}.Source_runes[{index}])"
            # General string indexing - use _runeAt helper
            return f"_runeAt({value}, {index})"
        # Check if indexing an interface{} variable (needs type assertion)
        if isinstance(node.value, ast.Name):
            var_name = self._to_go_var(node.value.id)
            var_type = self.var_types.get(var_name, "")
            if var_type == "interface{}":
                # Type assert to []interface{} then index
                base_expr = f"{value}.([]interface{{}})[{index}]"
                # Check if we know the element type from a tuple function
                # Only add assertion for slice types (for append contexts); simple types
                # are handled by the assignment handler
                if var_name in self.tuple_func_vars and isinstance(node.slice, ast.Constant):
                    func_name = self.tuple_func_vars[var_name]
                    idx = node.slice.value
                    if func_name in TUPLE_ELEMENT_TYPES:
                        elem_types = TUPLE_ELEMENT_TYPES[func_name]
                        if idx in elem_types:
                            elem_type = elem_types[idx]
                            # Only add type assertion for slice types (e.g., []string)
                            # Simple types like int are handled by assignment target type
                            if elem_type.startswith("[]"):
                                return f"{base_expr}.({elem_type})"
                return base_expr
        return f"{value}[{index}]"

    def visit_expr_BinOp(self, node: ast.BinOp) -> str:
        """Convert binary operations."""
        left = self.visit_expr(node.left)
        right = self.visit_expr(node.right)
        op = self._binop_to_go(node.op)
        # Handle floor division
        if isinstance(node.op, ast.FloorDiv):
            return f"{left} / {right}"  # Go int division is floor
        # Handle power
        if isinstance(node.op, ast.Pow):
            return f"int(math.Pow(float64({left}), float64({right})))"
        # Handle true division (Python / always returns float)
        if isinstance(node.op, ast.Div):
            return f"float64({left}) / float64({right})"
        # Width-rank auto-casting for mixed int/float arithmetic
        if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult)):
            left_type = self._infer_type_from_expr(node.left)
            right_type = self._infer_type_from_expr(node.right)
            if left_type == "float64" and right_type == "int":
                right = f"float64({right})"
            elif left_type == "int" and right_type == "float64":
                left = f"float64({left})"
        return f"{left} {op} {right}"

    def _binop_to_go(self, op: ast.operator) -> str:
        """Convert Python binary operator to Go."""
        ops = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.FloorDiv: "/",
            ast.Mod: "%",
            ast.LShift: "<<",
            ast.RShift: ">>",
            ast.BitOr: "|",
            ast.BitXor: "^",
            ast.BitAnd: "&",
        }
        return ops.get(type(op), "/* ? */")

    def visit_expr_UnaryOp(self, node: ast.UnaryOp) -> str:
        """Convert unary operations."""
        if isinstance(node.op, ast.Not):
            operand = self._emit_bool_expr(node.operand)
            return f"!({operand})"
        operand = self.visit_expr(node.operand)
        if isinstance(node.op, ast.USub):
            return f"-{operand}"
        if isinstance(node.op, ast.UAdd):
            return f"+{operand}"
        if isinstance(node.op, ast.Invert):
            return f"^{operand}"
        return f"/* TODO: UnaryOp */{operand}"

    def _emit_bool_expr(self, node: ast.expr) -> str:
        """Emit expression in boolean context, handling slice/map/string truthiness."""
        # Handle tuple element access (cmdsub_result[0] -> cmdsubResult0)
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name) and isinstance(node.slice, ast.Constant):
                var_name = self._to_go_var(node.value.id)
                if var_name in self.tuple_vars and isinstance(node.slice.value, int):
                    idx = node.slice.value
                    elem_vars = self.tuple_vars[var_name]
                    if 0 <= idx < len(elem_vars):
                        elem_var = elem_vars[idx]
                        elem_type = self.var_types.get(elem_var, "")
                        if elem_type == "Node" or elem_type.startswith("*"):
                            return f"{elem_var} != nil"
                        if elem_type.startswith("[]") or elem_type.startswith("map["):
                            return f"len({elem_var}) > 0"
                        if elem_type == "string":
                            return f"len({elem_var}) > 0"
        # If it's a simple Name that might be a slice/map/string, convert appropriately
        if isinstance(node, ast.Name):
            var_name = self._to_go_var(node.id)
            var_type = self.var_types.get(var_name, "")
            # Check if it's a Node type (interface, might be nil)
            if var_type == "Node" or var_type.startswith("*"):
                return f"{var_name} != nil"
            # Check if it's a slice or map type
            if var_type.startswith("[]") or var_type.startswith("map["):
                return f"len({var_name}) > 0"
            if var_type == "string":
                return f"len({var_name}) > 0"
            # Check if it's an int type (needs != 0 check)
            if var_type == "int":
                return f"{var_name} != 0"
            # Check by variable name heuristics for Node types
            if node.id.endswith(("_node", "Node", "_result")) or node.id in (
                "paramNode",
                "arithNode",
                "cmdNode",
                "node",
                "result",
            ):
                return f"{self.visit_expr(node)} != nil"
            # Check by variable name heuristics
            if node.id in ("redirects", "parts", "words", "commands", "args", "elts", "items"):
                return f"len({self.visit_expr(node)}) > 0"
            # String variable name heuristics
            if node.id in (
                "s",
                "name",
                "value",
                "text",
                "line",
                "word",
                "op",
                "delimiter",
                "param",
                "content",
                "nested",
                "arg",
                "inner",
                "trailing",
            ):
                return f"len({self.visit_expr(node)}) > 0"
        # If it's an attribute access that looks like a slice field
        if isinstance(node, ast.Attribute):
            if node.attr in ("redirects", "parts", "words", "commands", "args", "elts"):
                return f"len({self.visit_expr(node)}) > 0"
            # Optional Node fields need nil check
            if node.attr in ("else_body", "condition", "else_clause", "finally_clause", "body"):
                return f"{self.visit_expr(node)} != nil"
            # Look up field type from local variable's class
            if isinstance(node.value, ast.Name) and node.value.id != "self":
                var_name = self._to_go_var(node.value.id)
                var_type = self.var_types.get(var_name, "")
                if var_type.startswith("*"):
                    class_name = var_type[1:]
                    if class_name in self.symbols.classes:
                        class_info = self.symbols.classes[class_name]
                        if node.attr in class_info.fields:
                            field_type = class_info.fields[node.attr].go_type or ""
                            if field_type == "string":
                                return f"len({self.visit_expr(node)}) > 0"
                            if field_type.startswith("[]") or field_type.startswith("map["):
                                return f"len({self.visit_expr(node)}) > 0"
                            if field_type == "Node" or field_type.startswith("*"):
                                return f"{self.visit_expr(node)} != nil"
            # Look up field type from class
            if isinstance(node.value, ast.Name) and node.value.id == "self" and self.current_class:
                class_info = self.symbols.classes.get(self.current_class)
                if class_info and node.attr in class_info.fields:
                    field_type = class_info.fields[node.attr].go_type or ""
                    if field_type == "Node" or field_type.startswith("*"):
                        return f"{self.visit_expr(node)} != nil"
                    if field_type == "string":
                        return f'{self.visit_expr(node)} != ""'
                    if field_type.startswith("[]") or field_type.startswith("map["):
                        return f"len({self.visit_expr(node)}) > 0"
        # For UnaryOp Not, already handled above
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return f"!({self._emit_bool_expr(node.operand)})"
        # For bitwise AND, convert to != 0
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitAnd):
            return f"({self.visit_expr(node)}) != 0"
        # For getattr calls with bool default, add type assertion
        if self._is_getattr_call(node):
            # Check the default value (third argument)
            if len(node.args) >= 3:
                default = node.args[2]
                if isinstance(default, ast.Constant) and isinstance(default.value, bool):
                    return f"{self.visit_expr(node)}.(bool)"
        # For len() calls in boolean context, compare to 0
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "len":
            return f"{self.visit_expr(node)} > 0"
        # For string methods that return strings, check if non-empty
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            method = node.func.attr
            if method in (
                "strip",
                "lstrip",
                "rstrip",
                "lower",
                "upper",
                "replace",
                "peek",
                "Peek",
                "peek_word",
                "PeekWord",
            ):
                return f'{self.visit_expr(node)} != ""'
        # Default: just emit the expression
        return self.visit_expr(node)

    def visit_expr_Compare(self, node: ast.Compare) -> str:
        """Convert comparison operations."""
        result = self.visit_expr(node.left)
        for op, comparator in zip(node.ops, node.comparators, strict=True):
            # Handle 'in' operator
            if isinstance(op, ast.In):
                return self._emit_in_check(node.left, comparator, negated=False)
            if isinstance(op, ast.NotIn):
                return self._emit_in_check(node.left, comparator, negated=True)
            # Handle Node-typed field compared to None - use _isNilNode() to catch typed nils
            if (
                isinstance(op, ast.Is)
                and isinstance(comparator, ast.Constant)
                and comparator.value is None
            ):
                # Check for self.field of type Node
                if (
                    isinstance(node.left, ast.Attribute)
                    and isinstance(node.left.value, ast.Name)
                    and node.left.value.id == "self"
                    and self.current_class
                ):
                    class_info = self.symbols.classes.get(self.current_class)
                    if class_info and node.left.attr in class_info.fields:
                        field_type = class_info.fields[node.left.attr].go_type or ""
                        if field_type == "Node":
                            return f"_isNilNode({result})"
                # Check for local variable of type Node
                if isinstance(node.left, ast.Name):
                    var_name = self._to_go_var(node.left.id)
                    var_type = self.var_types.get(var_name, "")
                    if var_type == "Node":
                        return f"_isNilNode({result})"
            if (
                isinstance(op, ast.IsNot)
                and isinstance(comparator, ast.Constant)
                and comparator.value is None
            ):
                # Check for self.field of type Node
                if (
                    isinstance(node.left, ast.Attribute)
                    and isinstance(node.left.value, ast.Name)
                    and node.left.value.id == "self"
                    and self.current_class
                ):
                    class_info = self.symbols.classes.get(self.current_class)
                    if class_info and node.left.attr in class_info.fields:
                        field_type = class_info.fields[node.left.attr].go_type or ""
                        if field_type == "Node":
                            return f"!_isNilNode({result})"
                # Check for local variable of type Node
                if isinstance(node.left, ast.Name):
                    var_name = self._to_go_var(node.left.id)
                    var_type = self.var_types.get(var_name, "")
                    if var_type == "Node":
                        return f"!_isNilNode({result})"
            # Handle string subscript compared with single-char string
            right = self._emit_comparand(comparator, node.left)
            op_str = self._cmpop_to_go(op)
            result = f"{result} {op_str} {right}"
        return result

    def _emit_comparand(self, node: ast.expr, left: ast.expr) -> str:
        """Emit right side of comparison, handling byte vs string."""
        # Use rune literals for byte expressions (string subscripts or byte-typed variables)
        # But not for variables that could be strings from method calls
        if self._is_byte_expr(left) and not self._could_be_string_from_method(left):
            match node:
                case ast.Constant(value=str() as s) if len(s) == 1:
                    return self._char_to_rune_literal(s)
        # Handle comparison to None - use "" only for known string variables
        match node:
            case ast.Constant(value=None):
                match left:
                    case ast.Name(id=name):
                        var_name = self._to_go_var(name)
                        var_type = self.var_types.get(var_name, "")
                        if var_type == "int":
                            return "-1"
                        if var_type == "string":
                            return '""'
                        if name in (
                            "c",
                            "ch",
                            "eof_token",
                            "op",
                            "param",
                            "content",
                            "nested",
                            "arg",
                        ):
                            return '""'
                        if (
                            name.endswith("_pos")
                            or name.endswith("Pos")
                            or name in ("bracket_start_pos", "bracketStartPos")
                        ):
                            return "-1"
                    case ast.Attribute(value=ast.Name(id="self"), attr=attr) if self.current_class:
                        class_info = self.symbols.classes.get(self.current_class)
                        if class_info and attr in class_info.fields:
                            field_type = class_info.fields[attr].go_type or ""
                            if field_type == "string":
                                return '""'
                            if field_type == "int":
                                return "-1"
                    case ast.Attribute(attr=attr) if attr in ("_eof_token", "op", "arg", "param"):
                        return '""'
                    case ast.Call(func=ast.Attribute(attr=method) as func):
                        class_name = self._infer_object_class(func.value)
                        if class_name:
                            class_info = self.symbols.classes.get(class_name)
                            if class_info and method in class_info.methods:
                                ret_type = class_info.methods[method].return_type or ""
                                if ret_type == "string":
                                    return '""'
                                if ret_type == "int":
                                    return "-1"
        return self.visit_expr(node)

    def _is_getattr_call(self, node: ast.expr) -> bool:
        """Check if expression is a getattr() call."""
        match node:
            case ast.Call(func=ast.Name(id="getattr")):
                return True
        return False

    def _is_tuple_element_access(self, node: ast.expr) -> bool:
        """Check if expression is accessing a tuple element (subscript on interface{} var)."""
        match node:
            case ast.Subscript(value=ast.Name(id=name), slice=ast.Constant()):
                return self.var_types.get(self._to_go_var(name), "") == "interface{}"
        return False

    def _is_node_list_subscript(self, node: ast.expr) -> bool:
        """Check if expression is a subscript on a []Node field (returns Node)."""
        match node:
            case ast.Subscript(slice=ast.Slice()):
                return False  # Slice returns slice, not element
            case ast.Subscript(value=ast.Attribute(value=ast.Name(id=var_id), attr=attr)):
                var_name = self._to_go_var(var_id)
                var_type = self.var_types.get(var_name, "")
                if self._type_switch_var and var_name == self._type_switch_var[0]:
                    var_type = self._type_switch_type or ""
                if var_type.startswith("*"):
                    class_name = var_type[1:]
                    if class_name in self.symbols.classes:
                        class_info = self.symbols.classes[class_name]
                        if attr in class_info.fields:
                            field_type = class_info.fields[attr].go_type or ""
                            if field_type == "[]Node":
                                return True
        return False

    def _is_byte_expr(self, node: ast.expr) -> bool:
        """Check if expression evaluates to a byte/rune (e.g., rune slice subscript or byte variable)."""
        # Note: string subscripts are now converted to string() so they're not byte expressions
        match node:
            case ast.Subscript(value=ast.Name(id=name)):
                return self.var_types.get(self._to_go_var(name), "") == "[]rune"
            case ast.Name(id=name):
                return self.var_types.get(self._to_go_var(name), "") in ("byte", "rune")
        return False

    def _could_be_string_from_method(self, node: ast.expr) -> bool:
        """Check if a variable could be a string from method calls like advance/peek.
        Used to avoid treating such variables as runes even if typed from for-range."""
        match node:
            case ast.Name(id=name) if name in ("ch", "dch", "esc", "quote", "closing"):
                return True
        return False

    def _is_int_expr(self, node: ast.expr) -> bool:
        """Check if expression evaluates to an int."""
        match node:
            case ast.Constant(value=int()) if not isinstance(node.value, bool):
                return True
            case ast.Name(id=name) if self.var_types.get(self._to_go_var(name), "") == "int":
                return True
            case ast.Call(func=ast.Name(id="ord")):
                return True
            case ast.BinOp(op=ast.Add(), left=left, right=right):
                # Add can be string concat, so check operands
                if self._is_string_expr(left) or self._is_string_expr(right):
                    return False
                return self._is_int_expr(left) or self._is_int_expr(right)
            case ast.BinOp(
                op=ast.Sub() | ast.Mult() | ast.Div() | ast.FloorDiv() | ast.Mod() | ast.Pow(),
                left=left,
                right=right,
            ):
                return self._is_int_expr(left) or self._is_int_expr(right)
            case ast.BinOp(
                op=ast.BitOr() | ast.BitAnd() | ast.BitXor() | ast.LShift() | ast.RShift()
            ):
                return True
        return False

    def _is_string_expr(self, node: ast.expr) -> bool:
        """Check if expression evaluates to a string."""
        match node:
            case ast.Constant(value=str()):
                return True
            case ast.Name(id=name) if self.var_types.get(self._to_go_var(name), "") == "string":
                return True
            case ast.BinOp(op=ast.Add(), left=left, right=right):
                return self._is_string_expr(left) or self._is_string_expr(right)
            case ast.Subscript(slice=ast.Slice()) if self._is_string_subscript(node):
                return True
            case ast.Call(func=ast.Name(id="_substring")):
                return True
            case ast.Call(func=ast.Attribute(attr=method)) if method in (
                "join",
                "lower",
                "upper",
                "strip",
                "lstrip",
                "rstrip",
                "replace",
                "format",
                "decode",
                "encode",
            ):
                return True
        return False

    def _is_ord_of_byte(self, node: ast.expr) -> bool:
        """Check if node is ord() called on a byte expression or string subscript."""
        match node:
            case ast.Call(func=ast.Name(id="ord"), args=[arg]):
                if self._is_string_subscript(arg) or self._is_byte_expr(arg):
                    return True
                match arg:
                    case ast.Name(id=name) if self.var_types.get(self._to_go_var(name), "") in (
                        "byte",
                        "rune",
                    ):
                        return True
        return False

    def _extract_ord_arg(self, node: ast.Call) -> str:
        """Extract the argument from an ord() call, returning raw byte value for string subscripts."""
        if node.args:
            arg = node.args[0]
            # For string subscripts, return raw s[i] without string() wrapper
            if self._is_string_subscript(arg):
                value = self.visit_expr(arg.value)
                index = self.visit_expr(arg.slice)
                return f"{value}[{index}]"
            return self.visit_expr(arg)
        return "0"

    def _is_string_subscript(self, node: ast.expr) -> bool:
        """Check if node is a string subscript (e.g., s[i] or chars[i][j])."""
        if not isinstance(node, ast.Subscript):
            return False
        # Check for nested subscript: chars[i][j] where chars is []string
        # In this case chars[i] is a string, and chars[i][j] is a byte
        if isinstance(node.value, ast.Subscript):
            inner_var = node.value.value
            if isinstance(inner_var, ast.Name):
                var_name = self._to_go_var(inner_var.id)
                var_type = self.var_types.get(var_name, "")
                # If subscripting into a []string element, the result is a byte
                if var_type == "[]string":
                    return True
                # Heuristic: common names for string slices
                if inner_var.id in (
                    "chars",
                    "text_chars",
                    "name_chars",
                    "delimiter_chars",
                    "content_chars",
                    "pattern_chars",
                ):
                    return True
        # Check if the value being subscripted is likely a string
        # This is heuristic - we check if it's a Name that looks like a string var
        if isinstance(node.value, ast.Name):
            name = node.value.id
            # Check var_types first
            go_name = self._to_go_var(name)
            var_type = self.var_types.get(go_name, "")
            if var_type == "string":
                return True
            # Common string variable names
            if name in (
                "s",
                "text",
                "source",
                "inner",
                "value",
                "char",
                "c",
                "line",
                "name",
                "word",
                "op",
                "delimiter",
                "prefix",
                "suffix",
                "result_str",
                "inner_str",
                "outer_str",
            ):
                return True
            # Check if it ends with common string suffixes
            if name.endswith("_str") or name.endswith("text") or name.endswith("line"):
                return True
        # Check for self.source, self.text, etc.
        if isinstance(node.value, ast.Attribute):
            attr = node.value.attr
            if attr in (
                "source",
                "text",
                "value",
                "line",
                "inner",
                "name",
                "word",
                "pattern",
                "_arith_src",
            ):
                return True
        return False

    def _is_lexer_source_subscript(self, node: ast.Subscript) -> bool:
        """Check if node is self.source[i] access in Lexer/Parser context."""
        if not isinstance(node.value, ast.Attribute):
            return False
        if node.value.attr != "source":
            return False
        # Check if we're in a Lexer or Parser class
        if self.current_class in ("Lexer", "Parser"):
            return True
        return False

    def _is_string_slice(self, node: ast.Subscript) -> bool:
        """Check if node is a string slice (e.g., s[start:end])."""
        if not isinstance(node.slice, ast.Slice):
            return False
        # Check if the value being sliced is likely a string
        if isinstance(node.value, ast.Name):
            name = node.value.id
            go_name = self._to_go_var(name)
            var_type = self.var_types.get(go_name, "")
            if var_type == "string":
                return True
            # Common string variable names
            if name in (
                "s",
                "text",
                "source",
                "inner",
                "value",
                "line",
                "name",
                "word",
                "op",
                "delimiter",
                "prefix",
                "suffix",
            ):
                return True
        if isinstance(node.value, ast.Attribute):
            if node.value.attr in (
                "source",
                "text",
                "value",
                "line",
                "inner",
                "name",
                "word",
                "pattern",
                "_arith_src",
            ):
                return True
        return False

    def _is_lexer_source_slice(self, node: ast.Subscript) -> bool:
        """Check if node is self.source[start:end] in Lexer/Parser context."""
        if not isinstance(node.slice, ast.Slice):
            return False
        if not isinstance(node.value, ast.Attribute):
            return False
        if node.value.attr != "source":
            return False
        if self.current_class in ("Lexer", "Parser"):
            return True
        return False

    def _char_to_rune_literal(self, c: str) -> str:
        """Convert a single character to a Go rune literal."""
        if c == "\n":
            return "'\\n'"
        if c == "\t":
            return "'\\t'"
        if c == "\r":
            return "'\\r'"
        if c == "\\":
            return "'\\\\'"
        if c == "'":
            return "'\\''"
        if c == '"':
            return "'\"'"
        # Handle control characters and non-printable characters
        ord_c = ord(c)
        if ord_c < 32 or ord_c == 127:
            return f"'\\x{ord_c:02x}'"
        if ord_c > 127:
            return f"'\\u{ord_c:04x}'"
        return f"'{c}'"

    def _cmpop_to_go(self, op: ast.cmpop) -> str:
        """Convert Python comparison operator to Go."""
        ops = {
            ast.Eq: "==",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
            ast.Is: "==",
            ast.IsNot: "!=",
        }
        return ops.get(type(op), "/* ? */")

    def _emit_in_check(self, left: ast.expr, container: ast.expr, negated: bool) -> str:
        """Emit Go code for 'x in container' check."""
        left_expr = self.visit_expr(left)
        # String membership - literal string
        if isinstance(container, ast.Constant) and isinstance(container.value, str):
            container_expr = self.visit_expr(container)
            # If left is a byte expression, use ContainsRune
            if self._is_byte_expr(left):
                left_expr = f"rune({left_expr})"
                if negated:
                    return f"!strings.ContainsRune({container_expr}, {left_expr})"
                return f"strings.ContainsRune({container_expr}, {left_expr})"
            # For string left, use Contains
            if negated:
                return f"!strings.Contains({container_expr}, {left_expr})"
            return f"strings.Contains({container_expr}, {left_expr})"
        # String membership - variable with string type
        if isinstance(container, ast.Name):
            var_name = self._to_go_var(container.id)
            var_type = self.var_types.get(var_name, "")
            if var_type == "string":
                container_expr = self.visit_expr(container)
                # If left is a byte expression, use ContainsRune
                if self._is_byte_expr(left):
                    left_expr = f"rune({left_expr})"
                    if negated:
                        return f"!strings.ContainsRune({container_expr}, {left_expr})"
                    return f"strings.ContainsRune({container_expr}, {left_expr})"
                # For string left, use Contains
                if negated:
                    return f"!strings.Contains({container_expr}, {left_expr})"
                return f"strings.Contains({container_expr}, {left_expr})"
        # For other containers, use a helper or inline check
        container_expr = self.visit_expr(container)
        # Check if container is a set (map in Go) - either module-level or parameter
        if isinstance(container, ast.Name):
            name = container.id
            # Module-level sets are uppercase
            is_module_set = name.isupper() or (name.startswith("_") and name[1:].isupper())
            # Check if it's a parameter/variable typed as map[string]struct{}
            var_name = self._to_go_var(name)
            var_type = self.var_types.get(var_name, "")
            is_set_type = var_type.startswith("map[") and var_type.endswith("]struct{}")
            if is_module_set:
                # Module-level sets use map[string]bool - direct access works
                if negated:
                    return f"!{container_expr}[{left_expr}]"
                return f"{container_expr}[{left_expr}]"
            if is_set_type:
                # Parameter/variable sets use map[string]struct{} - need comma ok idiom
                # Create inline check: func() bool { _, ok := m[k]; return ok }()
                if negated:
                    return f"func() bool {{ _, ok := {container_expr}[{left_expr}]; return !ok }}()"
                return f"func() bool {{ _, ok := {container_expr}[{left_expr}]; return ok }}()"
        # Use _containsAny for interface{} slices, _contains for typed slices
        if "[]interface{}" in container_expr:
            func_name = "_containsAny"
        else:
            func_name = "_contains"
        if negated:
            return f"!{func_name}({container_expr}, {left_expr})"
        return f"{func_name}({container_expr}, {left_expr})"

    def visit_expr_BoolOp(self, node: ast.BoolOp) -> str:
        """Convert boolean operations (and/or)."""
        is_and = isinstance(node.op, ast.And)
        op = " && " if is_and else " || "
        # Check for isinstance(x, T) and x.attr pattern
        if is_and and len(node.values) >= 2:
            isinstance_info = self._detect_isinstance_call(node.values[0])
            if isinstance_info:
                var_name, type_name = isinstance_info
                # Check if subsequent operands access attributes on the same variable
                if self._subsequent_ops_use_var(node.values[1:], var_name):
                    return self._emit_isinstance_and_attr(var_name, type_name, node.values[1:])
        # Use _emit_bool_expr for each operand to handle truthiness conversions
        # Parenthesize nested BoolOps with different operators due to precedence
        # In Go, && has higher precedence than ||, so:
        # - Or inside And needs parentheses: a && (b || c)
        # - And inside Or does not: a || b && c is already correct
        values = []
        for v in node.values:
            expr = self._emit_bool_expr(v)
            # If this is an And and the value is an Or BoolOp, wrap in parentheses
            if is_and and isinstance(v, ast.BoolOp) and isinstance(v.op, ast.Or):
                expr = f"({expr})"
            values.append(expr)
        return op.join(values)

    def _detect_isinstance_call(self, node: ast.expr) -> tuple[str, str] | None:
        """Detect isinstance(var, Type) call. Returns (var_name, type_name) or None."""
        if not isinstance(node, ast.Call):
            return None
        if not isinstance(node.func, ast.Name) or node.func.id != "isinstance":
            return None
        if len(node.args) != 2:
            return None
        if not isinstance(node.args[0], ast.Name):
            return None
        if not isinstance(node.args[1], ast.Name):
            return None
        return (node.args[0].id, node.args[1].id)

    def _subsequent_ops_use_var(self, operands: list[ast.expr], var_name: str) -> bool:
        """Check if any operand accesses an attribute on the given variable."""
        for op in operands:
            if isinstance(op, ast.Attribute):
                if isinstance(op.value, ast.Name) and op.value.id == var_name:
                    return True
        return False

    def _emit_isinstance_and_attr(
        self, var_name: str, type_name: str, subsequent_ops: list[ast.expr]
    ) -> str:
        """Emit combined isinstance + attribute access pattern.

        Pattern: isinstance(x, T) and x.attr
        Go: func() bool { t, ok := x.(*T); return ok && t.Attr }()
        """
        go_var = self._to_go_var(var_name)
        # Emit subsequent conditions, replacing var access with casted variable
        casted_var = "t"
        conditions = ["ok"]
        for op in subsequent_ops:
            if (
                isinstance(op, ast.Attribute)
                and isinstance(op.value, ast.Name)
                and op.value.id == var_name
            ):
                # Replace x.attr with t.Attr
                go_attr = self._to_go_field_name(op.attr)
                conditions.append(f"{casted_var}.{go_attr}")
            else:
                # Other condition, emit as-is
                conditions.append(self._emit_bool_expr(op))
        return_expr = " && ".join(conditions)
        return (
            f"func() bool {{ {casted_var}, ok := {go_var}.(*{type_name}); return {return_expr} }}()"
        )

    def visit_expr_IfExp(self, node: ast.IfExp) -> str:
        """Convert ternary expression. Go doesn't have ternary, use helper func."""
        # Check for pattern: arr[idx] if idx < len(arr) else None
        # This requires lazy evaluation to avoid index-out-of-bounds panic
        if self._is_bounds_guarded_subscript(node):
            return self._emit_lazy_ternary(node)
        test = self._emit_bool_expr(node.test)
        body = self.visit_expr(node.body)
        orelse = self.visit_expr(node.orelse)
        # Check if we need to cast for Node interface compatibility
        body_type = self._infer_type_from_expr(node.body)
        orelse_type = self._infer_type_from_expr(node.orelse)
        # If one is Node and other is *SomeNodeSubclass, cast to Node
        if body_type == "Node" and orelse_type.startswith("*"):
            class_name = orelse_type[1:]
            if class_name in self.symbols.classes and self.symbols.classes[class_name].is_node:
                orelse = f"Node({orelse})"
        elif orelse_type == "Node" and body_type.startswith("*"):
            class_name = body_type[1:]
            if class_name in self.symbols.classes and self.symbols.classes[class_name].is_node:
                body = f"Node({body})"
        # Use an inline if helper function
        return f"_ternary({test}, {body}, {orelse})"

    def _is_bounds_guarded_subscript(self, node: ast.IfExp) -> bool:
        """Check if ternary is: arr[idx] if idx < len(arr) else None."""
        # Body must be subscript access
        if not isinstance(node.body, ast.Subscript):
            return False
        # Orelse must be None
        if not (isinstance(node.orelse, ast.Constant) and node.orelse.value is None):
            return False
        # Test must be Compare with single < operator
        if not isinstance(node.test, ast.Compare):
            return False
        if len(node.test.ops) != 1 or not isinstance(node.test.ops[0], ast.Lt):
            return False
        if len(node.test.comparators) != 1:
            return False
        # Right side of compare must be len(arr) where arr matches subscript value
        comparator = node.test.comparators[0]
        if not isinstance(comparator, ast.Call):
            return False
        if not (isinstance(comparator.func, ast.Name) and comparator.func.id == "len"):
            return False
        if len(comparator.args) != 1:
            return False
        # Check arr in len(arr) matches arr in arr[idx]
        len_arg = comparator.args[0]
        subscript_value = node.body.value
        if not self._ast_names_equal(len_arg, subscript_value):
            return False
        # Check idx in idx < len(arr) matches idx in arr[idx]
        left_idx = node.test.left
        subscript_idx = node.body.slice
        return self._ast_names_equal(left_idx, subscript_idx)

    def _ast_names_equal(self, a: ast.expr, b: ast.expr) -> bool:
        """Check if two AST nodes represent the same name/attribute."""
        if isinstance(a, ast.Name) and isinstance(b, ast.Name):
            return a.id == b.id
        if isinstance(a, ast.Attribute) and isinstance(b, ast.Attribute):
            return a.attr == b.attr and self._ast_names_equal(a.value, b.value)
        return False

    def _emit_lazy_ternary(self, node: ast.IfExp) -> str:
        """Emit IIFE for lazy evaluation of bounds-guarded subscript."""
        test = self._emit_bool_expr(node.test)
        body = self.visit_expr(node.body)
        body_type = self._infer_type_from_expr(node.body)
        return f"func() {body_type} {{ if {test} {{ return {body} }}; return nil }}()"

    def visit_expr_Call(self, node: ast.Call) -> str:
        """Convert function/method calls."""
        args = [self.visit_expr(a) for a in node.args]
        args_str = ", ".join(args)
        # Method call
        if isinstance(node.func, ast.Attribute):
            return self._emit_method_call(node)
        # Function call
        if isinstance(node.func, ast.Name):
            return self._emit_func_call(node)
        return f"{self.visit_expr(node.func)}({args_str})"

    def _emit_method_call(self, node: ast.Call) -> str:
        """Emit method call."""
        obj = self.visit_expr(node.func.value)
        method = node.func.attr
        args = [self.visit_expr(a) for a in node.args]
        # Handle keyword arguments and default values for class methods
        class_name = self._infer_object_class(node.func.value)
        if class_name:
            args = self._merge_keyword_args_for_method(class_name, method, args, node.keywords)
            args = self._fill_default_args_for_method(class_name, method, args)
            # Add & when passing slice to pointer-to-slice parameter
            args = self._add_address_of_for_ptr_slice_params(class_name, method, args, node.args)
        args_str = ", ".join(args)
        # Handle Node interface methods - may need type assertion
        if method in ("to_sexp", "kind"):
            # If obj might not be typed as Node, add assertion
            if self._needs_node_assertion(node.func.value):
                go_method = self._snake_to_pascal(method)
                return f"{obj}.(Node).{go_method}()"
        # Handle struct-specific methods called on Node-typed expressions
        obj_type = self._get_expr_element_type(node.func.value)
        if obj_type == "Node" and method not in ("to_sexp", "kind"):
            # Method is not on Node interface - need to find which struct has it
            struct_type = self._find_method_owner(method)
            if struct_type:
                go_method = self._to_go_func_name(method)
                return f"{obj}.({struct_type}).{go_method}({args_str})"
        # Handle Python string/list methods
        if method == "append":
            return self._emit_append(obj, args, node.args)
        method_map = {
            "startswith": lambda o, a: f"strings.HasPrefix({o}, {a[0]})",
            "endswith": lambda o, a: f"strings.HasSuffix({o}, {a[0]})",
            "strip": lambda o, a: f"strings.TrimSpace({o})",
            "lstrip": lambda o, a: f"strings.TrimLeft({o}, {a[0]})"
            if a
            else f'strings.TrimLeft({o}, " \\t\\n\\r\\x0b\\x0c")',
            "rstrip": lambda o, a: f"strings.TrimRight({o}, {a[0]})"
            if a
            else f'strings.TrimRight({o}, " \\t\\n\\r\\x0b\\x0c")',
            "find": lambda o, a: f"strings.Index({o}, {a[0]})",
            "rfind": lambda o, a: f"strings.LastIndex({o}, {a[0]})",
            "replace": lambda o, a: f"strings.ReplaceAll({o}, {a[0]}, {a[1]})",
            "join": self._emit_join,
            "lower": lambda o, a: f"strings.ToLower({o})",
            "upper": lambda o, a: f"strings.ToUpper({o})",
            "isalpha": self._emit_isalpha,
            "isdigit": self._emit_isdigit,
            "isalnum": self._emit_isalnum,
            "isspace": self._emit_isspace,
            "pop": self._emit_pop,
            "extend": self._emit_extend,
            "get": self._emit_dict_get,
            "encode": self._emit_encode,
            "decode": lambda o, a: f"string({o})",
        }
        if method in method_map:
            handler = method_map[method]
            if callable(handler):
                self._current_method_node = node
                result = handler(obj, args)
                self._current_method_node = None
                return result
        # Default: convert to Go method call
        go_method = self._to_go_func_name(method)
        return f"{obj}.{go_method}({args_str})"

    def _emit_append(
        self, obj: str, args: list[str], orig_args: list[ast.expr] | None = None
    ) -> str:
        """Emit append call - Go requires reassignment."""
        arg = args[0]
        obj_type = self.var_types.get(obj, "")
        # Handle pointer-to-slice types - dereference for append
        if obj_type.startswith("*[]"):
            elem_type = obj_type[3:]  # e.g., "*[]Node" -> "Node"
            # If appending interface{} to *[]Node, add type assertion
            if elem_type == "Node" and orig_args:
                arg_type = self._infer_type_from_expr(orig_args[0])
                if arg_type == "interface{}":
                    arg = f"{arg}.(Node)"
            # If appending a byte to a *[]string, convert
            if elem_type == "string":
                if orig_args and self._is_byte_expr(orig_args[0]):
                    arg = f"string({arg})"
            # If appending an int to *[]byte, convert to byte
            if elem_type == "byte" and orig_args:
                if self._is_int_expr(orig_args[0]):
                    arg = f"byte({arg})"
            return f"*{obj} = append(*{obj}, {arg})"
        # If appending interface{} to []Node, add type assertion
        if obj_type == "[]Node" and orig_args:
            arg_type = self._infer_type_from_expr(orig_args[0])
            if arg_type == "interface{}":
                arg = f"{arg}.(Node)"
        # If appending a byte to a string slice, convert
        if obj_type == "[]string":
            if orig_args and self._is_byte_expr(orig_args[0]):
                arg = f"string({arg})"
        # If appending to []byte
        elif obj_type == "[]byte":
            if orig_args and self._is_byte_expr(orig_args[0]):
                pass  # Already a byte, use as-is
            elif orig_args and self._is_ord_of_byte(orig_args[0]):
                # ord() of a byte - extract the byte directly
                arg = self._extract_ord_arg(orig_args[0])
            elif orig_args and self._is_int_expr(orig_args[0]):
                arg = f"byte({arg})"
            elif (
                orig_args
                and isinstance(orig_args[0], ast.Constant)
                and isinstance(orig_args[0].value, str)
            ):
                if len(orig_args[0].value) == 1:
                    arg = self._char_to_rune_literal(orig_args[0].value)
                else:
                    # Multi-character string - use spread operator
                    return f"{obj} = append({obj}, []byte({arg})...)"
            elif orig_args and isinstance(orig_args[0], ast.Name):
                # Variable - check its type
                var_name = self._to_go_var(orig_args[0].id)
                var_type = self.var_types.get(var_name, "")
                if var_type == "string":
                    # String variable appended to []byte - use spread
                    return f"{obj} = append({obj}, []byte({arg})...)"
            elif orig_args and self._is_string_expr(orig_args[0]):
                # String expression (concatenation, slice, etc) - use spread
                return f"{obj} = append({obj}, []byte({arg})...)"
        # If appending string char to []rune
        elif obj_type == "[]rune":
            # Check if arg is a string constant - convert to rune
            if (
                orig_args
                and isinstance(orig_args[0], ast.Constant)
                and isinstance(orig_args[0].value, str)
            ):
                if len(orig_args[0].value) == 1:
                    arg = self._char_to_rune_literal(orig_args[0].value)
        return f"{obj} = append({obj}, {arg})"

    def _emit_pop(self, obj: str, args: list[str]) -> str:
        """Emit pop call - returns last element and removes it.
        For slices: use _pop helper
        For objects with Pop() method (like QuoteState): call the method
        """
        # Check if this is an object with a Pop() method
        obj_type = self.var_types.get(obj, "")
        if obj_type in ("*QuoteState", "QuoteState"):
            return f"{obj}.Pop()"
        return f"_pop(&{obj})"

    def _emit_extend(self, obj: str, args: list[str]) -> str:
        """Emit extend call."""
        return f"{obj} = append({obj}, {args[0]}...)"

    def _emit_join(self, obj: str, args: list[str]) -> str:
        """Emit join call - strings.Join or string() for []rune or []byte."""
        list_arg = args[0]
        # Check if the list argument is a []rune or []byte variable
        list_type = self.var_types.get(list_arg, "")
        if list_type == "[]rune":
            # For []rune with empty separator, just convert to string
            if obj == '""':
                return f"string({list_arg})"
            # For non-empty separator, need to convert runes to strings first
            return f"strings.Join(_runesToStrings({list_arg}), {obj})"
        if list_type == "[]byte":
            # For []byte with empty separator, just convert to string
            if obj == '""':
                return f"string({list_arg})"
            # For non-empty separator, need to convert bytes to strings first
            return f"strings.Join(_bytesToStrings({list_arg}), {obj})"
        return f"strings.Join({list_arg}, {obj})"

    def _emit_encode(self, obj: str, args: list[str]) -> str:
        """Emit encode call - convert string to []byte."""
        # Check if the object is already a byte (from string subscript)
        if hasattr(self, "_current_method_node") and self._current_method_node:
            # _current_method_node is a Call, func is the Attribute, func.value is the object
            if isinstance(self._current_method_node.func, ast.Attribute):
                value_node = self._current_method_node.func.value
                if self._is_byte_expr(value_node):
                    # Already a byte, just wrap in slice for extend compatibility
                    return f"[]byte{{{obj}}}"
        return f"[]byte({obj})"

    def _emit_isalpha(self, obj: str, args: list[str]) -> str:
        """Emit isalpha check."""
        # Handle both string and byte/rune cases
        return f"unicode.IsLetter(_runeFromChar({obj}))"

    def _emit_isdigit(self, obj: str, args: list[str]) -> str:
        """Emit isdigit check - true if non-empty and all characters are digits."""
        return f"_strIsDigits({obj})"

    def _emit_isalnum(self, obj: str, args: list[str]) -> str:
        """Emit isalnum check."""
        return f"(unicode.IsLetter(_runeFromChar({obj})) || unicode.IsDigit(_runeFromChar({obj})))"

    def _emit_isspace(self, obj: str, args: list[str]) -> str:
        """Emit isspace check - true if non-empty and all whitespace."""
        return f'(len({obj}) > 0 && strings.TrimSpace({obj}) == "")'

    def _emit_dict_get(self, obj: str, args: list[str]) -> str:
        """Emit dict.get() call."""
        key = args[0]
        # Special case: ANSI_C_ESCAPES uses rune keys
        if obj in ("ANSICEscapes", "ANSI_C_ESCAPES", "AnsiCEscapes"):
            obj = "ANSICEscapes"  # Use the manually emitted name
            key = f"_strToRune({key})"
        if len(args) > 1:
            default = args[1]
            return f"_mapGet({obj}, {key}, {default})"
        return f"{obj}[{key}]"

    def _emit_func_call(self, node: ast.Call) -> str:
        """Emit function call."""
        name = node.func.id
        args = []
        for i, a in enumerate(node.args):
            arg_str = self.visit_expr(a)
            # Convert byte to string for functions that expect string parameters
            if self._func_expects_string_param(name, i) and self._is_byte_expr(a):
                arg_str = f"string({arg_str})"
            args.append(arg_str)
        # Handle keyword arguments
        args = self._merge_keyword_args(name, args, node.keywords)
        # Add default values for missing parameters
        args = self._fill_default_args(name, args)
        args_str = ", ".join(args)
        # Handle builtins
        builtin_map = {
            "len": lambda a: self._emit_len(node.args[0], a[0]),
            "str": lambda a: f"fmt.Sprint({a[0]})" if a else '""',
            "int": lambda a: f"_mustAtoi({a[0]})" if len(a) == 1 else f"_parseInt({a[0]}, {a[1]})",
            "bool": lambda a: f"({a[0]} != 0)" if a else "false",
            "ord": self._emit_ord,
            "chr": lambda a: f"string(rune({a[0]}))",
            "isinstance": self._emit_isinstance,
            "getattr": self._emit_getattr,
            "range": lambda a: "/* range */",
            "list": self._emit_list,
            "set": lambda a: f"_makeSet({a[0]})" if a else "make(map[interface{}]struct{})",
            "max": lambda a: f"_max({', '.join(a)})",
            "min": lambda a: f"_min({', '.join(a)})",
            "bytearray": lambda a: "[]byte{}",
        }
        if name in builtin_map:
            self._current_call_node = node
            result = builtin_map[name](args)
            self._current_call_node = None
            return result
        # Handle helper functions
        if name == "_substring":
            # Use helper function with bounds checking (Python slicing is safe)
            return f"_Substring({args[0]}, {args[1]}, {args[2]})"
        if name == "_sublist":
            return f"{args[0]}[{args[1]}:{args[2]}]"
        if name == "_repeat_str":
            return f"strings.Repeat({args[0]}, {args[1]})"
        if name == "_starts_with_at":
            return f"strings.HasPrefix({args[0]}[{args[1]}:], {args[2]})"
        # Handle local functions that are translated to helpers
        if name == "format_arith_val":
            return f"_FormatArithVal({args_str})"
        # Handle class constructors
        if name in self.symbols.classes:
            # Fix empty list types based on constructor parameter types
            class_info = self.symbols.classes[name]
            if "__init__" in class_info.methods:
                init_info = class_info.methods["__init__"]
                fixed_args = []
                for i, arg in enumerate(args):
                    if arg == "[]interface{}{}" and i < len(init_info.params):
                        param_type = init_info.params[i].go_type
                        if param_type and param_type.startswith("[]"):
                            arg = f"{param_type}{{}}"
                    fixed_args.append(arg)
                args_str = ", ".join(fixed_args)
            return f"New{name}({args_str})"
        # Default function call
        go_name = self._to_go_func_name(name)
        return f"{go_name}({args_str})"

    def _emit_list(self, args: list[str]) -> str:
        """Emit list() call - create a copy of a slice."""
        if not args:
            return "[]interface{}{}"
        # Try to infer the slice type from the argument
        if hasattr(self, "_current_call_node") and self._current_call_node:
            call_args = self._current_call_node.args
            if call_args:
                arg_type = self._infer_expr_type(call_args[0])
                if arg_type and arg_type.startswith("[]"):
                    return f"append({arg_type}{{}}, {args[0]}...)"
        return f"append([]interface{{}}{{}}, {args[0]}...)"

    def _emit_len(self, arg_node: ast.expr, arg_str: str) -> str:
        """Emit len() call - use _runeLen for strings, len() otherwise."""
        # Check if the argument is a string expression
        if self._is_string_expr(arg_node):
            # For Lexer/Parser Source, use len(Source_runes) for O(1) access
            if isinstance(arg_node, ast.Attribute):
                if arg_node.attr == "source" and self.current_class in ("Lexer", "Parser"):
                    receiver = self.current_class[0].lower()
                    return f"len({receiver}.Source_runes)"
            return f"_runeLen({arg_str})"
        return f"len({arg_str})"

    def _emit_ord(self, args: list[str]) -> str:
        """Emit ord() call - get code point of a character.

        Python's ord() always returns int, so we return int.
        """
        if not args:
            return "0"
        arg = args[0]
        # Check if the current call arg is already a byte/rune expression
        if hasattr(self, "_current_call_node") and self._current_call_node:
            call_args = self._current_call_node.args
            if call_args:
                # If it's a string subscript, emit as int(s[i]) directly
                # (bypass the string() conversion we normally do)
                if self._is_string_subscript(call_args[0]):
                    # Get raw subscript without string() wrapper
                    value = self.visit_expr(call_args[0].value)
                    index = self.visit_expr(call_args[0].slice)
                    return f"int({value}[{index}])"
                if self._is_byte_expr(call_args[0]):
                    return f"int({arg})"  # Already a byte, convert to int
            # Also check if it's a variable with byte type
            if call_args and isinstance(call_args[0], ast.Name):
                var_name = self._to_go_var(call_args[0].id)
                var_type = self.var_types.get(var_name, "")
                if var_type in ("byte", "rune"):
                    return f"int({arg})"  # Already a byte/rune, convert to int
        return f"int(rune({arg}[0]))"

    def _emit_isinstance(self, args: list[str]) -> str:
        """Emit isinstance check using type assertion."""
        if not hasattr(self, "_current_call_node") or not self._current_call_node:
            raise NotImplementedError("isinstance: no call node context")
        call_node = self._current_call_node
        if len(call_node.args) < 2:
            raise NotImplementedError("isinstance: need 2 args")
        obj = args[0]
        type_arg = call_node.args[1]
        # Extract type names from AST
        type_names: list[str] = []
        if isinstance(type_arg, ast.Name):
            type_names.append(type_arg.id)
        elif isinstance(type_arg, ast.Tuple):
            for elt in type_arg.elts:
                if isinstance(elt, ast.Name):
                    type_names.append(elt.id)
        if not type_names:
            raise NotImplementedError(f"isinstance: unsupported type pattern {ast.dump(type_arg)}")
        # Generate Go type assertion(s)
        if len(type_names) == 1:
            return f"func() bool {{ _, ok := {obj}.(*{type_names[0]}); return ok }}()"
        # Multiple types - check each in turn
        checks = []
        for i, tn in enumerate(type_names):
            var = f"ok{i + 1}"
            checks.append(f"_, {var} := {obj}.(*{tn})")
        return_expr = " || ".join(f"ok{i + 1}" for i in range(len(type_names)))
        return f"func() bool {{ {'; '.join(checks)}; return {return_expr} }}()"

    def _detect_isinstance_if(self, test: ast.expr) -> tuple[str, str] | None:
        """Detect if test is `isinstance(var, Type)`. Returns (var_name, type_name) or None."""
        if not isinstance(test, ast.Call):
            return None
        if not isinstance(test.func, ast.Name) or test.func.id != "isinstance":
            return None
        if len(test.args) != 2:
            return None
        var_arg, type_arg = test.args
        if not isinstance(var_arg, ast.Name):
            return None
        if not isinstance(type_arg, ast.Name):
            return None  # Only single type for now, not tuples
        return (var_arg.id, type_arg.id)

    def _collect_isinstance_chain(
        self, stmts: list[ast.stmt], start_idx: int
    ) -> list[tuple[ast.If, str, str]]:
        """Collect consecutive `if isinstance(same_var, T):` statements.
        Returns list of (stmt, var_name, type_name) tuples."""
        result: list[tuple[ast.If, str, str]] = []
        if start_idx >= len(stmts):
            return result
        first_stmt = stmts[start_idx]
        if not isinstance(first_stmt, ast.If):
            return result
        first_info = self._detect_isinstance_if(first_stmt.test)
        if not first_info:
            return result
        target_var = first_info[0]
        result.append((first_stmt, first_info[0], first_info[1]))
        # Look for more isinstance checks on the same variable
        for i in range(start_idx + 1, len(stmts)):
            stmt = stmts[i]
            if not isinstance(stmt, ast.If):
                break
            info = self._detect_isinstance_if(stmt.test)
            if not info or info[0] != target_var:
                break
            # Must not have elif/else - only simple if isinstance(...):
            if stmt.orelse:
                break
            result.append((stmt, info[0], info[1]))
        return result

    def _detect_assign_check_return(
        self, stmts: list[ast.stmt], idx: int
    ) -> tuple[str, ast.Call, str] | None:
        """Detect pattern: result = self.method(); if result: return result
        Returns (var_name, method_call, return_type) or None.
        This pattern causes typed-nil issues when method returns concrete type
        but variable is interface type."""
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
        # Variable should be interface type (Node) or untyped (for assign-check-return pattern)
        # The pattern transformation avoids typed-nil issues and unused variable issues
        go_var = self._to_go_var(var_name)
        var_type = self.var_types.get(go_var, "")
        # Accept if type is Node, empty (untyped), or interface{}
        if var_type not in ("Node", "", "interface{}"):
            return None
        # Second statement must be: if result: return result
        # OR: if result is not None: return result
        if_stmt = stmts[idx + 1]
        if not isinstance(if_stmt, ast.If):
            return None
        # Test must be just the variable name (truthy check)
        # OR a comparison: result is not None
        test_var_name = None
        if isinstance(if_stmt.test, ast.Name):
            test_var_name = if_stmt.test.id
        elif isinstance(if_stmt.test, ast.Compare):
            # Check for: result is not None
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
        # Body must be single return statement returning the same variable
        if len(if_stmt.body) != 1:
            return None
        ret = if_stmt.body[0]
        if not isinstance(ret, ast.Return) or not isinstance(ret.value, ast.Name):
            return None
        if ret.value.id != var_name:
            return None
        # Must not have else clause
        if if_stmt.orelse:
            return None
        return (var_name, call, return_type)

    def _get_method_return_type(self, method_name: str) -> str | None:
        """Get the return type of a method if it's a concrete pointer type."""
        # Parser methods that return concrete types
        parser_methods = {
            "parse_brace_group": "*BraceGroup",
            "parse_subshell": "*Subshell",
            "parse_if": "*If",
            "parse_while": "*While",
            "parse_until": "*Until",
            "parse_for": "*For",
            "parse_select": "*Select",
            "parse_case": "*Case",
            "parse_function": "*Function",
            "parse_coproc": "*Coproc",
            "parse_arithmetic_command": "*ArithmeticCommand",
            "parse_conditional_expr": "*ConditionalExpr",
            "parse_comment": "*Comment",
        }
        return parser_methods.get(method_name)

    def _emit_assign_check_return(self, var_name: str, method_call: ast.Call, return_type: str):
        """Emit pattern: if tmp := method(); tmp != nil { return tmp }
        This avoids typed-nil interface issues."""
        go_var = self._to_go_var(var_name)
        # Generate the method call expression
        call_expr = self.visit_expr(method_call)
        # Use a short temp variable name
        tmp_var = go_var[0].lower() + "Tmp"
        if tmp_var == go_var:
            tmp_var = go_var + "Tmp"
        self.emit(f"if {tmp_var} := {call_expr}; {tmp_var} != nil {{")
        self.indent += 1
        self.emit(f"return {tmp_var}")
        self.indent -= 1
        self.emit("}")

    def _emit_type_switch(self, var_name: str, cases: list[tuple[ast.If, str, str]]):
        """Emit Go type switch for isinstance chain."""
        go_var = self._to_go_var(var_name)
        # Use short switch variable name (e.g., node -> n)
        switch_var = go_var[0].lower()
        if switch_var == go_var:
            switch_var = go_var + "T"  # Avoid shadowing
        self.emit(f"switch {switch_var} := {go_var}.(type) {{")
        for stmt, _, type_name in cases:
            # Convert Python type name to Go type (e.g., str -> string)
            go_type = TYPE_MAP.get(type_name, type_name)
            # Primitives don't get * prefix, class types do
            if type_name in TYPE_MAP:
                case_type = go_type
            else:
                case_type = f"*{go_type}"
            self.emit(f"case {case_type}:")
            self.indent += 1
            # Set up type switch context for variable rewriting
            old_switch_var = self._type_switch_var
            old_switch_type = self._type_switch_type
            self._type_switch_var = (go_var, switch_var)
            self._type_switch_type = case_type
            # Track narrowed type for field access
            old_var_type = self.var_types.get(switch_var)
            self.var_types[switch_var] = case_type
            try:
                for s in stmt.body:
                    self._emit_stmt(s)
            except NotImplementedError:
                self.emit('panic("TODO: incomplete implementation")')
            # Restore context
            self._type_switch_var = old_switch_var
            self._type_switch_type = old_switch_type
            if old_var_type is not None:
                self.var_types[switch_var] = old_var_type
            else:
                self.var_types.pop(switch_var, None)
            self.indent -= 1
        # Check if the last isinstance has an else branch that doesn't contain more isinstance checks
        # This handles patterns like: if isinstance(body, str): ... else: body.to_sexp()
        last_stmt = cases[-1][0]
        if last_stmt.orelse and not self._else_contains_isinstance(last_stmt.orelse, cases[0][1]):
            self.emit("default:")
            self.indent += 1
            # In the default case, the switch variable still holds the value but with interface{} type
            old_switch_var = self._type_switch_var
            self._type_switch_var = (go_var, switch_var)
            try:
                for s in last_stmt.orelse:
                    self._emit_stmt(s)
            except NotImplementedError:
                self.emit('panic("TODO: incomplete implementation")')
            self._type_switch_var = old_switch_var
            self.indent -= 1
        self.emit("}")

    def _else_contains_isinstance(self, stmts: list[ast.stmt], var_name: str) -> bool:
        """Check if else branch contains isinstance checks on the same variable."""
        for stmt in stmts:
            if isinstance(stmt, ast.If):
                info = self._detect_isinstance_if(stmt.test)
                if info and info[0] == var_name:
                    return True
                # Recursively check elif/else branches
                if stmt.orelse and self._else_contains_isinstance(stmt.orelse, var_name):
                    return True
        return False

    def _emit_getattr(self, args: list[str]) -> str:
        """Emit getattr call."""
        obj = args[0]
        attr = args[1]
        if len(args) > 2:
            default = args[2]
            return f"_getattr({obj}, {attr}, {default})"
        return f"_getattr({obj}, {attr}, nil)"

    def visit_expr_List(self, node: ast.List) -> str:
        """Convert list literals."""
        if not node.elts:
            # Empty list - try to infer type from context, fallback to interface{}
            return "[]interface{}{}"
        # Infer element type from first element
        first = node.elts[0]
        elem_type = self._infer_literal_elem_type(first)
        elements = ", ".join(self.visit_expr(e) for e in node.elts)
        return f"[]{elem_type}{{{elements}}}"

    def _infer_literal_elem_type(self, node: ast.expr) -> str:
        """Infer Go type from a literal element."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return "string"
            if isinstance(node.value, int):
                return "int"
            if isinstance(node.value, bool):
                return "bool"
        # Handle string concatenation (BinOp with Add involving strings)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left_type = self._infer_literal_elem_type(node.left)
            right_type = self._infer_literal_elem_type(node.right)
            if left_type == "string" or right_type == "string":
                return "string"
        # Handle class constructor calls
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            class_name = node.func.id
            if class_name in self.symbols.classes:
                info = self.symbols.classes[class_name]
                if info.is_node:
                    return "Node"
                return "*" + class_name
        # Handle variable references - look up type
        if isinstance(node, ast.Name):
            var_name = self._to_go_var(node.id)
            var_type = self.var_types.get(var_name, "")
            if var_type and var_type != "interface{}":
                return var_type
        return "interface{}"

    def visit_expr_Dict(self, node: ast.Dict) -> str:
        """Convert dict literals."""
        if not node.keys:
            return "map[string]interface{}{}"
        pairs = []
        for k, v in zip(node.keys, node.values, strict=True):
            pairs.append(f"{self.visit_expr(k)}: {self.visit_expr(v)}")
        # Use map[string]string if all values are string constants
        if node.values and all(
            isinstance(v, ast.Constant) and isinstance(v.value, str) for v in node.values
        ):
            return "map[string]string{" + ", ".join(pairs) + "}"
        return "map[string]interface{}{" + ", ".join(pairs) + "}"

    def visit_expr_Tuple(self, node: ast.Tuple) -> str:
        """Convert tuple literals (as slices in Go)."""
        elements = ", ".join(self.visit_expr(e) for e in node.elts)
        return f"[]interface{{}}{{{elements}}}"

    def visit_expr_Set(self, node: ast.Set) -> str:
        """Convert set literals."""
        if not node.elts:
            return "make(map[interface{}]struct{})"
        # Check if all elements are string constants - use map[string] for type safety
        all_strings = all(
            isinstance(e, ast.Constant) and isinstance(e.value, str) for e in node.elts
        )
        key_type = "string" if all_strings else "interface{}"
        elements = ", ".join(f"{self.visit_expr(e)}: {{}}" for e in node.elts)
        return f"map[{key_type}]struct{{}}{{{elements}}}"

    def visit_expr_JoinedStr(self, node: ast.JoinedStr) -> str:
        """Convert f-strings to fmt.Sprintf."""
        format_parts = []
        args = []
        for part in node.values:
            if isinstance(part, ast.Constant):
                # Escape % for fmt.Sprintf
                format_parts.append(part.value.replace("%", "%%"))
            elif isinstance(part, ast.FormattedValue):
                format_parts.append("%v")
                args.append(self.visit_expr(part.value))
        format_str = "".join(format_parts).replace('"', '\\"').replace("\n", "\\n")
        if args:
            return f'fmt.Sprintf("{format_str}", {", ".join(args)})'
        return f'"{format_str}"'

    def visit_expr_Lambda(self, node: ast.Lambda) -> str:
        """Convert lambda expressions."""
        params = [self._to_go_var(a.arg) for a in node.args.args]
        params_str = ", ".join(f"{p} interface{{}}" for p in params)
        body = self.visit_expr(node.body)
        return f"func({params_str}) interface{{}} {{ return {body} }}"
