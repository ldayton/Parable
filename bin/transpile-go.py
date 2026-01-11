#!/usr/bin/env python3
"""Transpile parable.py's restricted Python subset to Go."""

import ast
import io
import sys
import tokenize
from pathlib import Path


class GoTranspiler(ast.NodeVisitor):
    def __init__(self):
        self.indent = 0
        self.output = []
        self.in_class_body = False
        self.in_method = False
        self.current_class = None
        self.class_names = set()
        self.node_classes = set()  # Classes that inherit from Node
        self.comments = {}
        self.last_line = 0
        # Track functions that can return errors (raise ParseError)
        self.error_functions = set()
        # Track declared variables in current scope
        self.declared_vars = set()
        # Track which variables have been assigned (for := vs =)
        self.assigned_vars = set()
        # First pass to collect class info
        self.collecting = True
        # Track struct fields inferred from __init__
        self.class_fields = {}  # class_name -> [(field_name, field_type)]

    def emit(self, text: str):
        self.output.append("\t" * self.indent + text)

    def emit_raw(self, text: str):
        self.output.append(text)

    def emit_comments_before(self, line: int):
        for comment_line in sorted(self.comments.keys()):
            if comment_line >= line:
                break
            if comment_line > self.last_line:
                comment = self.comments[comment_line].lstrip("# ").rstrip()
                self.emit(f"// {comment}")
        self.last_line = line

    def transpile(self, source: str) -> str:
        # Extract standalone comments
        lines = source.splitlines()
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                line_num, col = tok.start
                if lines[line_num - 1][:col].strip() == "":
                    self.comments[line_num] = tok.string
        tree = ast.parse(source)
        # First pass: collect class info and error-raising functions
        self.collecting = True
        self._collect_info(tree)
        self.collecting = False
        # Second pass: emit code
        self.visit(tree)
        return "\n".join(self.output)

    def _collect_info(self, tree: ast.Module):
        """First pass to collect class names and identify error-raising functions."""
        # First pass: collect all class names and node classes
        for stmt in tree.body:
            if isinstance(stmt, ast.ClassDef):
                self.class_names.add(stmt.name)
                for base in stmt.bases:
                    if isinstance(base, ast.Name) and base.id == "Node":
                        self.node_classes.add(stmt.name)
        # Second pass: collect field types (now we know all node classes)
        for stmt in tree.body:
            if isinstance(stmt, ast.ClassDef):
                # Collect fields from class body annotations and __init__
                fields = []
                for class_stmt in stmt.body:
                    if isinstance(class_stmt, ast.AnnAssign) and isinstance(class_stmt.target, ast.Name):
                        field_name = class_stmt.target.id
                        field_type = self._go_type(class_stmt.annotation)
                        if field_type:
                            fields.append((field_name, field_type))
                    elif isinstance(class_stmt, ast.FunctionDef) and class_stmt.name == "__init__":
                        # Infer fields from self.x = y assignments
                        for init_stmt in ast.walk(class_stmt):
                            if isinstance(init_stmt, ast.Assign):
                                target = init_stmt.targets[0]
                                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                                    if target.value.id == "self":
                                        field_name = target.attr
                                        # Try to infer type from argument annotation
                                        field_type = self._infer_field_type(init_stmt.value, class_stmt)
                                        if field_name not in [f[0] for f in fields]:
                                            fields.append((field_name, field_type))
                self.class_fields[stmt.name] = fields
            if isinstance(stmt, ast.FunctionDef):
                # Check if function raises ParseError or has "Raises:" in docstring
                for node in ast.walk(stmt):
                    if isinstance(node, ast.Raise):
                        self.error_functions.add(stmt.name)
                        break
                # Check docstring for "Raises:"
                if stmt.body and isinstance(stmt.body[0], ast.Expr):
                    if isinstance(stmt.body[0].value, ast.Constant):
                        docstring = stmt.body[0].value.value
                        if isinstance(docstring, str) and "Raises:" in docstring:
                            self.error_functions.add(stmt.name)

    def _infer_field_type(self, value: ast.expr, func: ast.FunctionDef) -> str:
        """Infer field type from assignment value."""
        # If value is a parameter name, check its annotation
        if isinstance(value, ast.Name):
            # Get non-self args with their indices
            non_self_args = [(i, a) for i, a in enumerate(func.args.args) if a.arg != "self"]
            for non_self_idx, (_, arg) in enumerate(non_self_args):
                if arg.arg == value.id and arg.annotation:
                    go_type = self._go_type(arg.annotation)
                    # Check if this arg has a None default (nullable)
                    if self._arg_has_none_default(func, non_self_idx):
                        if go_type == "int":
                            return "*int"
                        if go_type == "string":
                            return "*string"
                    return go_type
        # Infer type from literal values
        if isinstance(value, ast.Constant):
            if isinstance(value.value, int):
                return "int"
            if isinstance(value.value, str):
                return "string"
            if isinstance(value.value, bool):
                return "bool"
            if value.value is None:
                return "interface{}"
        # If value is a list literal or list()
        if isinstance(value, ast.List):
            return "[]interface{}"
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
            if value.func.id == "list":
                return "[]interface{}"
            if value.func.id == "bytearray":
                return "[]byte"
            if value.func.id == "len":
                return "int"
            if value.func.id == "set":
                return "map[interface{}]bool"
        # Default to interface{}
        return "interface{}"

    def _arg_has_none_default(self, func: ast.FunctionDef, arg_idx: int) -> bool:
        """Check if argument at index (excluding self) has a None default value."""
        args = func.args
        non_self_args = [a for a in args.args if a.arg != "self"]
        if arg_idx >= len(non_self_args):
            return False
        # Find the relative position in defaults
        num_defaults = len(args.defaults)
        first_default_idx = len(non_self_args) - num_defaults
        default_idx = arg_idx - first_default_idx
        if default_idx < 0 or default_idx >= num_defaults:
            return False
        default = args.defaults[default_idx]
        return isinstance(default, ast.Constant) and default.value is None

    def _go_type(self, annotation: ast.expr | None, param_name: str = "") -> str:
        """Convert Python type annotation to Go type."""
        if annotation is None:
            return ""
        if isinstance(annotation, ast.Name):
            mapping = {
                "str": "string",
                "int": "int",
                "bool": "bool",
                "list": "[]interface{}",
                "bytearray": "[]byte",
                "dict": "map[string]interface{}",
                "tuple": "[]interface{}",
                "None": "",
            }
            result = mapping.get(annotation.id, annotation.id)
            # For single-char parameters, use byte instead of string
            if result == "string" and param_name in ("c", "ch", "char", "byte_char"):
                return "byte"
            return result
        if isinstance(annotation, ast.Constant):
            # Forward reference like "CasePattern" or "Redirect | HereDoc"
            if isinstance(annotation.value, str):
                type_name = annotation.value
                # Handle union types in string form like "Redirect | HereDoc"
                if " | " in type_name:
                    parts = [p.strip() for p in type_name.split(" | ")]
                    # If any part is a Node subclass, return Node
                    if any(p in self.node_classes or p == "Node" for p in parts):
                        return "Node"
                    return parts[0]  # Return first type
                if type_name in self.node_classes or type_name == "Node":
                    return type_name
                return self._public_name(type_name)
            if annotation.value is None:
                return ""
        if isinstance(annotation, ast.Subscript):
            if isinstance(annotation.value, ast.Name):
                if annotation.value.id == "list":
                    elem_type = self._go_type(annotation.slice)
                    # If element type is a union or a Node subclass, use []Node
                    if not elem_type or elem_type in self.node_classes or elem_type == "Node":
                        return "[]Node"
                    if elem_type:
                        return f"[]{elem_type}"
                    return "[]interface{}"
                if annotation.value.id == "tuple":
                    return ""  # Go doesn't have tuples, handle case by case
        if isinstance(annotation, ast.BinOp):
            # Union type like Node | None or Redirect | HereDoc or int | None
            if isinstance(annotation.op, ast.BitOr):
                left_type = self._go_type(annotation.left)
                right_type = self._go_type(annotation.right)
                # If any part of the union is a Node subclass, return Node
                if left_type in self.node_classes or left_type == "Node":
                    return "Node"
                # T | None becomes *T (pointer for optional)
                if right_type == "" and left_type in ("int", "bool", "string"):
                    return f"*{left_type}"
                return left_type
        return ""

    def _safe_name(self, name: str) -> str:
        """Rename Go reserved words."""
        reserved = {
            "type": "typ",
            "func": "fn",
            "var": "variable",
            "range": "rng",
            "map": "mapping",
            "string": "str",
            "case": "caseVal",
            "select": "selectVal",
            "default": "defaultVal",
            "package": "pkg",
            "import": "imp",
            "return": "ret",
            "break": "brk",
            "continue": "cont",
            "for": "forVal",
            "if": "ifVal",
            "else": "elseVal",
            "switch": "switchVal",
            "go": "goVal",
            "chan": "chanVal",
            "defer": "deferVal",
            "interface": "iface",
            "struct": "structVal",
            "const": "constVal",
        }
        return reserved.get(name, name)

    def _public_name(self, name: str) -> str:
        """Convert to public Go name (PascalCase)."""
        if not name:
            return name
        # Handle leading underscore (private) - keep lowercase
        if name.startswith("_"):
            rest = name[1:]
            if rest:
                # Convert snake_case to camelCase
                parts = rest.split("_")
                return parts[0].lower() + "".join(p[0].upper() + p[1:] if p else "" for p in parts[1:])
            return name
        # If no underscores, just capitalize first letter (preserve existing case)
        if "_" not in name:
            return name[0].upper() + name[1:]
        # Convert snake_case to PascalCase
        parts = name.split("_")
        return "".join(p[0].upper() + p[1:] if p else "" for p in parts)

    def _func_name(self, name: str) -> str:
        """Convert Python function name to Go function name."""
        # Strip leading underscore for private functions
        if name.startswith("_"):
            name = name[1:]
            # Convert snake_case to camelCase (first letter lowercase for private)
            parts = name.split("_")
            return parts[0] + "".join(p.capitalize() for p in parts[1:] if p)
        # Public function: convert to PascalCase
        parts = name.split("_")
        return "".join(p.capitalize() for p in parts if p)

    def _method_name(self, name: str) -> str:
        """Convert Python method name to Go method name."""
        if name == "__init__":
            return ""  # Constructors are special
        if name == "to_sexp":
            return "ToSexp"
        # Private methods (starting with _) use camelCase
        if name.startswith("_"):
            name = name[1:]
            parts = name.split("_")
            return parts[0].lower() + "".join(p[0].upper() + p[1:] if p else "" for p in parts[1:])
        # Public methods use PascalCase
        parts = name.split("_")
        return "".join(p[0].upper() + p[1:] if p else "" for p in parts)

    def _receiver_name(self, class_name: str) -> str:
        """Get receiver variable name for a class."""
        # Use first letter lowercase
        return class_name[0].lower()

    def visit_Module(self, node: ast.Module):
        self.emit("package parable")
        self.emit("")
        self.emit('import (')
        self.indent += 1
        self.emit('"fmt"')
        self.emit('"reflect"')
        self.emit('"strings"')
        self.emit('"strconv"')
        self.emit('"unicode/utf8"')
        self.indent -= 1
        self.emit(")")
        self.emit("")
        # Emit Node interface
        self.emit("// Node is the interface for all AST nodes")
        self.emit("type Node interface {")
        self.indent += 1
        self.emit("ToSexp() string")
        self.emit("GetKind() string")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Emit helper functions
        self.emit("// Helper functions")
        self.emit("func toSet(items interface{}) map[interface{}]bool {")
        self.indent += 1
        self.emit("m := make(map[interface{}]bool)")
        self.emit("switch v := items.(type) {")
        self.emit("case []interface{}:")
        self.indent += 1
        self.emit("for _, item := range v { m[item] = true }")
        self.indent -= 1
        self.emit("case string:")
        self.indent += 1
        self.emit("for _, c := range v { m[string(c)] = true }")
        self.indent -= 1
        self.emit("}")
        self.emit("return m")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("func contains(set map[interface{}]bool, key interface{}) bool {")
        self.indent += 1
        self.emit("return set[key]")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("func substring(s string, start, end int) string {")
        self.indent += 1
        self.emit("if end > len(s) { end = len(s) }")
        self.emit("if start < 0 { start = 0 }")
        self.emit("return s[start:end]")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("func parseInt(s string, base int) int {")
        self.indent += 1
        self.emit("n, _ := strconv.ParseInt(s, base, 64)")
        self.emit("return int(n)")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("func toInt(v interface{}) int {")
        self.indent += 1
        self.emit("switch x := v.(type) {")
        self.emit("case int: return x")
        self.emit("case string: n, _ := strconv.Atoi(x); return n")
        self.emit("default: return 0")
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Suppress unused variable errors
        self.emit("var _ = substring")
        self.emit("var _ = parseInt")
        self.emit("var _ = toInt")
        self.emit("")
        # Helper for appending int to byte slice
        self.emit("func appendByte(slice []byte, val int) []byte {")
        self.indent += 1
        self.emit("return append(slice, byte(val))")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Helper for joining interface slice
        self.emit("func joinStrings(items []interface{}, sep string) string {")
        self.indent += 1
        self.emit("strs := make([]string, len(items))")
        self.emit("for i, item := range items {")
        self.indent += 1
        self.emit('strs[i] = fmt.Sprintf("%v", item)')
        self.indent -= 1
        self.emit("}")
        self.emit("return strings.Join(strs, sep)")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Helper for slicing a slice
        self.emit("func sublist(items []interface{}, start, end int) []interface{} {")
        self.indent += 1
        self.emit("if start < 0 { start = 0 }")
        self.emit("if end > len(items) { end = len(items) }")
        self.emit("return items[start:end]")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Helper for converting []Node to []interface{}
        self.emit("func toSlice(nodes []Node) []interface{} {")
        self.indent += 1
        self.emit("result := make([]interface{}, len(nodes))")
        self.emit("for i, n := range nodes { result[i] = n }")
        self.emit("return result")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Helper for slicing []Node
        self.emit("func sublistNodes(nodes []Node, start, end int) []Node {")
        self.indent += 1
        self.emit("if start < 0 { start = 0 }")
        self.emit("if end > len(nodes) { end = len(nodes) }")
        self.emit("return nodes[start:end]")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Helper for converting []interface{} to []Node
        self.emit("func toNodes(items []interface{}) []Node {")
        self.indent += 1
        self.emit("result := make([]Node, len(items))")
        self.emit("for i, item := range items { result[i] = item.(Node) }")
        self.emit("return result")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Character type helpers (use _h suffix to avoid conflicts with source functions)
        self.emit("func isAlpha_h(s string) bool {")
        self.indent += 1
        self.emit("for _, c := range s {")
        self.indent += 1
        self.emit("if !((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')) { return false }")
        self.indent -= 1
        self.emit("}")
        self.emit("return len(s) > 0")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("func isAlnum_h(s string) bool {")
        self.indent += 1
        self.emit("for _, c := range s {")
        self.indent += 1
        self.emit("if !((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9')) { return false }")
        self.indent -= 1
        self.emit("}")
        self.emit("return len(s) > 0")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("func isDigit_h(s string) bool {")
        self.indent += 1
        self.emit("for _, c := range s {")
        self.indent += 1
        self.emit("if !(c >= '0' && c <= '9') { return false }")
        self.indent -= 1
        self.emit("}")
        self.emit("return len(s) > 0")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("func isSpace_h(s string) bool {")
        self.indent += 1
        self.emit("for _, c := range s {")
        self.indent += 1
        self.emit("if !(c == ' ' || c == '\\t' || c == '\\n' || c == '\\r') { return false }")
        self.indent -= 1
        self.emit("}")
        self.emit("return len(s) > 0")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # getAttr helper
        self.emit("func getAttr(obj interface{}, attr string, defaultVal interface{}) interface{} {")
        self.indent += 1
        self.emit("// Simplified getattr - just return default for now")
        self.emit("return defaultVal")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Helper to convert byte to string
        self.emit("func byteToStr(b byte) string { return string([]byte{b}) }")
        self.emit("")
        # Helper for tuple-like access on []interface{} pairs
        self.emit("func pairFirst(p interface{}) Node {")
        self.indent += 1
        self.emit("if arr, ok := p.([]interface{}); ok && len(arr) > 0 {")
        self.indent += 1
        self.emit("if n, ok := arr[0].(Node); ok { return n }")
        self.indent -= 1
        self.emit("}")
        self.emit("return nil")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("func pairSecond(p interface{}) bool {")
        self.indent += 1
        self.emit("if arr, ok := p.([]interface{}); ok && len(arr) > 1 {")
        self.indent += 1
        self.emit("if b, ok := arr[1].(bool); ok { return b }")
        self.indent -= 1
        self.emit("}")
        self.emit("return false")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Helper to get Command field from any struct using reflect
        self.emit("func getCommand(n interface{}) Node {")
        self.indent += 1
        self.emit("v := reflect.ValueOf(n)")
        self.emit("if v.Kind() == reflect.Ptr { v = v.Elem() }")
        self.emit('f := v.FieldByName("Command")')
        self.emit("if f.IsValid() {")
        self.indent += 1
        self.emit("if cmd, ok := f.Interface().(Node); ok { return cmd }")
        self.indent -= 1
        self.emit("}")
        self.emit("return nil")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Helper for map.get(key, default)
        self.emit("func mapGet(m map[string]interface{}, key string, defaultVal interface{}) string {")
        self.indent += 1
        self.emit("if val, ok := m[key]; ok {")
        self.indent += 1
        self.emit("if s, ok := val.(string); ok { return s }")
        self.indent -= 1
        self.emit("}")
        self.emit("if s, ok := defaultVal.(string); ok { return s }")
        self.emit('return ""')
        self.indent -= 1
        self.emit("}")
        self.emit("")
        for stmt in node.body:
            self.emit_comments_before(stmt.lineno)
            self.visit(stmt)

    def visit_ClassDef(self, node: ast.ClassDef):
        # Skip the base Node class since we have a Node interface
        if node.name == "Node":
            return
        self.class_names.add(node.name)
        class_name = self._public_name(node.name)
        # Check if it inherits from Node
        is_node = node.name in self.node_classes
        is_exception = any(
            isinstance(b, ast.Name) and b.id == "Exception" for b in node.bases
        )
        # Get fields from collected info
        fields = self.class_fields.get(node.name, [])
        methods = [s for s in node.body if isinstance(s, ast.FunctionDef)]
        # Emit struct
        self.emit(f"type {class_name} struct {{")
        self.indent += 1
        for field_name, field_type in fields:
            go_field = self._public_name(field_name)
            self.emit(f"{go_field} {field_type}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # For ParseError, implement error interface
        if is_exception:
            recv = self._receiver_name(node.name)
            format_method = self._method_name("_format_message")
            self.emit(f"func ({recv} *{class_name}) Error() string {{")
            self.indent += 1
            self.emit(f"return {recv}.{format_method}()")
            self.indent -= 1
            self.emit("}")
            self.emit("")
        # For node classes, implement GetKind()
        if is_node:
            recv = self._receiver_name(node.name)
            self.emit(f"func ({recv} *{class_name}) GetKind() string {{")
            self.indent += 1
            self.emit(f"return {recv}.Kind")
            self.indent -= 1
            self.emit("}")
            self.emit("")
        # Emit constructor and methods
        old_class = self.current_class
        self.current_class = node.name
        self.in_class_body = True
        for method in methods:
            self.visit_FunctionDef(method)
        self.in_class_body = False
        self.current_class = old_class

    def _collect_local_vars(self, stmts: list) -> set:
        """Collect all variable names assigned in a list of statements."""
        names = set()
        for stmt in stmts:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
            elif isinstance(stmt, ast.AnnAssign):
                if isinstance(stmt.target, ast.Name) and stmt.value:
                    names.add(stmt.target.id)
            elif isinstance(stmt, ast.For):
                if isinstance(stmt.target, ast.Name):
                    names.add(stmt.target.id)
                names.update(self._collect_local_vars(stmt.body))
                names.update(self._collect_local_vars(stmt.orelse))
            elif isinstance(stmt, ast.While):
                names.update(self._collect_local_vars(stmt.body))
                names.update(self._collect_local_vars(stmt.orelse))
            elif isinstance(stmt, ast.If):
                names.update(self._collect_local_vars(stmt.body))
                names.update(self._collect_local_vars(stmt.orelse))
            elif isinstance(stmt, ast.Try):
                names.update(self._collect_local_vars(stmt.body))
                for handler in stmt.handlers:
                    names.update(self._collect_local_vars(handler.body))
                names.update(self._collect_local_vars(stmt.finalbody))
        return names

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Skip helper functions that are inlined
        if node.name in ("_substring", "_sublist", "_repeat_str"):
            return
        is_init = node.name == "__init__"
        method_name = self._method_name(node.name)
        # Get arguments (skip self for methods)
        args = [a for a in node.args.args if a.arg != "self"]
        # For constructors, emit a New function
        if is_init and self.current_class:
            class_name = self._public_name(self.current_class)
            # Build argument list, making nullable int args into pointers
            arg_parts = []
            defaults = node.args.defaults
            num_defaults = len(defaults)
            first_default_idx = len(args) - num_defaults
            for i, a in enumerate(args):
                go_type = self._go_type(a.annotation) or "interface{}"
                # Check if this arg has a None default
                default_idx = i - first_default_idx
                if default_idx >= 0 and default_idx < num_defaults:
                    default = defaults[default_idx]
                    if isinstance(default, ast.Constant) and default.value is None:
                        if go_type == "int":
                            go_type = "*int"
                        elif go_type == "string":
                            go_type = "*string"
                arg_parts.append(f"{self._safe_name(a.arg)} {go_type}")
            arg_list = ", ".join(arg_parts)
            self.emit(f"func New{class_name}({arg_list}) *{class_name} {{")
            self.indent += 1
            recv = self._receiver_name(self.current_class)
            self.emit(f"{recv} := &{class_name}{{}}")
            # Process body (skip super() calls, handle assignments to self.x)
            old_declared = self.declared_vars
            old_assigned = self.assigned_vars.copy()
            param_names = {a.arg for a in args}
            self.declared_vars = param_names.copy()
            self.assigned_vars = param_names.copy()  # Parameters already assigned
            for stmt in node.body:
                if self._is_super_call(stmt):
                    continue
                self.emit_comments_before(stmt.lineno)
                self._visit_init_stmt(stmt, recv)
            self.emit(f"return {recv}")
            self.declared_vars = old_declared
            self.assigned_vars = old_assigned
            self.indent -= 1
            self.emit("}")
            self.emit("")
            return
        # Regular method or function
        if self.in_class_body and self.current_class and not self.in_method:
            # Method with receiver
            class_name = self._public_name(self.current_class)
            recv = self._receiver_name(self.current_class)
            arg_list = ", ".join(
                f"{self._safe_name(a.arg)} {self._go_type(a.annotation, a.arg) or 'interface{}'}"
                for a in args
            )
            # Determine return type
            ret_type = self._go_type(node.returns) if node.returns else ""
            ret_str = f" {ret_type}" if ret_type else ""
            self.emit(f"func ({recv} *{class_name}) {method_name}({arg_list}){ret_str} {{")
        elif self.in_method:
            # Nested function - use anonymous function assigned to variable
            func_name = self._func_name(node.name)
            arg_list = ", ".join(
                f"{self._safe_name(a.arg)} {self._go_type(a.annotation, a.arg) or 'interface{}'}"
                for a in args
            )
            ret_type = self._go_type(node.returns) if node.returns else ""
            ret_str = f" {ret_type}" if ret_type else ""
            self.emit(f"{func_name} := func({arg_list}){ret_str} {{")
        else:
            # Top-level function
            func_name = self._func_name(node.name)
            arg_list = ", ".join(
                f"{self._safe_name(a.arg)} {self._go_type(a.annotation, a.arg) or 'interface{}'}"
                for a in args
            )
            ret_type = self._go_type(node.returns) if node.returns else ""
            # Check if function raises errors
            if node.name in self.error_functions:
                if ret_type:
                    ret_str = f" ({ret_type}, error)"
                else:
                    ret_str = " error"
            else:
                ret_str = f" {ret_type}" if ret_type else ""
            self.emit(f"func {func_name}({arg_list}){ret_str} {{")
        self.indent += 1
        old_in_method = self.in_method
        old_declared = self.declared_vars
        old_assigned = self.assigned_vars.copy() if hasattr(self, 'assigned_vars') else set()
        self.in_method = True
        param_names = {a.arg for a in args}
        self.declared_vars = param_names.copy()
        self.assigned_vars = param_names.copy()  # Parameters are already assigned
        # Handle default arguments
        self._emit_defaults(node)
        # Track variables that will be assigned in blocks but used later
        # These need outer-scope declaration for proper Go scoping
        self.block_reused_vars = self._find_reused_variables(node.body)
        # Emit body
        for stmt in node.body:
            self.emit_comments_before(stmt.lineno)
            self.visit(stmt)
        self.in_method = old_in_method
        self.declared_vars = old_declared
        self.assigned_vars = old_assigned
        self.indent -= 1
        self.emit("}")
        self.emit("")

    def _emit_defaults(self, node: ast.FunctionDef):
        """Emit default argument handling."""
        defaults = node.args.defaults
        if not defaults:
            return
        non_self_args = [a for a in node.args.args if a.arg != "self"]
        first_default_idx = len(non_self_args) - len(defaults)
        for i, default in enumerate(defaults):
            if isinstance(default, ast.Constant) and default.value is None:
                continue
            arg_name = self._safe_name(non_self_args[first_default_idx + i].arg)
            default_val = self.visit_expr(default)
            self.emit(f"if {arg_name} == nil {{ {arg_name} = {default_val} }}")

    def _find_reused_variables(self, body: list[ast.stmt]) -> dict[str, str]:
        """Find variables assigned in blocks that are used later, needing pre-declaration."""
        # Track where variables are assigned (inside blocks vs top level)
        block_assigned = set()  # Variables assigned inside for/if blocks
        all_assigned = set()  # All assigned variables
        all_used = set()  # All used variables

        def collect_names(node, in_block=False):
            """Recursively collect assigned and used variable names."""
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    all_assigned.add(node.id)
                    if in_block:
                        block_assigned.add(node.id)
                elif isinstance(node.ctx, ast.Load):
                    all_used.add(node.id)
            elif isinstance(node, ast.For):
                # For loop target is a block assignment
                if isinstance(node.target, ast.Name):
                    all_assigned.add(node.target.id)
                    block_assigned.add(node.target.id)
                elif isinstance(node.target, ast.Tuple):
                    for elt in node.target.elts:
                        if isinstance(elt, ast.Name):
                            all_assigned.add(elt.id)
                            block_assigned.add(elt.id)
                # Iter and body
                collect_names(node.iter, in_block)
                for stmt in node.body:
                    collect_names(stmt, in_block=True)
                for stmt in node.orelse:
                    collect_names(stmt, in_block=True)
            elif isinstance(node, ast.If):
                collect_names(node.test, in_block)
                for stmt in node.body:
                    collect_names(stmt, in_block=True)
                for stmt in node.orelse:
                    collect_names(stmt, in_block=True)
            elif isinstance(node, ast.While):
                collect_names(node.test, in_block)
                for stmt in node.body:
                    collect_names(stmt, in_block=True)
                for stmt in node.orelse:
                    collect_names(stmt, in_block=True)
            elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                for child in ast.iter_child_nodes(node):
                    collect_names(child, in_block)
            elif isinstance(node, (ast.Expr, ast.Return)):
                for child in ast.iter_child_nodes(node):
                    collect_names(child, in_block)
            elif isinstance(node, ast.Call):
                for child in ast.iter_child_nodes(node):
                    collect_names(child, in_block)
            elif isinstance(node, (ast.Attribute, ast.Subscript, ast.BinOp, ast.Compare,
                                   ast.BoolOp, ast.UnaryOp, ast.IfExp, ast.List, ast.Tuple)):
                for child in ast.iter_child_nodes(node):
                    collect_names(child, in_block)

        for stmt in body:
            collect_names(stmt, in_block=False)

        # Variables that need pre-declaration: assigned in block AND used somewhere
        needs_predecl = block_assigned & all_used

        # Infer types for these variables
        result = {}
        type_hints = {
            "cmd": "Node",
            "pair": "interface{}",
            "needs": "bool",
            # Note: inner, parts, items can be string or slice in different contexts
            # so we don't pre-declare them with a fixed type
            "parsed": "Node",
            "node": "Node",
            "words": "[]Node",
            "arg": "Node",
            "args": "[]Node",
            "part": "interface{}",
            "char": "byte",
            "text": "string",
            "name": "string",
            "value": "interface{}",
            "word": "Node",
            "redir": "Node",
            "rest": "string",
            "in_double": "bool",
            "in_single": "bool",
            "in_single_quote": "bool",
            "in_double_quote": "bool",
            "bs_count": "int",
            "simple": "int",
            "depth": "int",
            "start": "int",
            "end": "int",
            "count": "int",
            "hex_str": "string",
            "byte_val": "int",
            "codepoint": "int",
            "ctrl_char": "byte",
            "ctrl_val": "int",
            "oct_str": "string",
            "digit_count": "int",
            "escape_char": "byte",
            "brace_depth": "int",
            "effective_in_dquote": "bool",
            "ansi_str": "string",
            "expanded": "string",
            "esc_parts": "[]interface{}",
            "j": "int",
            "prev": "string",
            "direction": "byte",
            "formatted": "string",
            "prefix": "string",
            "last": "interface{}",
            "ch": "byte",
            "left": "[]interface{}",
            "right": "[]interface{}",
            "left_sexp": "string",
            "right_sexp": "string",
            "inner_parts": "[]interface{}",
            "inner_list": "Node",
            "op_name": "string",
            "fd_target": "string",
            "redirect_parts": "[]string",
            "word_parts": "[]string",
            "word_strs": "string",
            "init_val": "string",
            "cond_val": "string",
            "update_val": "string",
            "incr_val": "string",
        }
        # Skip pre-declaring variables that have context-dependent types
        # or are only used within their block
        skip_vars = {
            "i", "c", "n", "j", "w", "r",  # Loop variables
            "inner", "parts", "items", "result",  # Can be string or slice
            "arith_content",  # Context-dependent (prev is handled by multi-branch logic)
        }
        for var in needs_predecl:
            if var in skip_vars:
                continue  # Let these be declared naturally in loops
            if var in type_hints:
                result[var] = type_hints[var]
            else:
                result[var] = "interface{}"

        return result

    def _collect_assignments_in_block(self, body: list[ast.stmt]) -> set[str]:
        """Collect all variable names assigned in a block."""
        assigned = set()
        for stmt in body:
            for node in ast.walk(stmt):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    assigned.add(node.id)
                elif isinstance(node, ast.Tuple) and isinstance(node.ctx, ast.Store):
                    for elt in node.elts:
                        if isinstance(elt, ast.Name):
                            assigned.add(elt.id)
        return assigned

    def _is_super_call(self, stmt: ast.stmt) -> bool:
        """Check if statement is a super().__init__() call."""
        if not isinstance(stmt, ast.Expr):
            return False
        call = stmt.value
        if not isinstance(call, ast.Call):
            return False
        if not isinstance(call.func, ast.Attribute):
            return False
        if call.func.attr != "__init__":
            return False
        if not isinstance(call.func.value, ast.Call):
            return False
        if not isinstance(call.func.value.func, ast.Name):
            return False
        return call.func.value.func.id == "super"

    def _visit_init_stmt(self, stmt: ast.stmt, recv: str):
        """Visit a statement in __init__, converting self.x = y to receiver assignments."""
        if isinstance(stmt, ast.Assign):
            target = stmt.targets[0]
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                if target.value.id == "self":
                    field = self._public_name(target.attr)
                    value = self.visit_expr(stmt.value)
                    self.emit(f"{recv}.{field} = {value}")
                    return
        if isinstance(stmt, ast.If):
            # Skip "if x is None: x = []" patterns - nil slices work in Go
            if self._is_nil_list_init(stmt):
                return
            test = self.visit_expr(stmt.test)
            self.emit(f"if {test} {{")
            self.indent += 1
            for s in stmt.body:
                self._visit_init_stmt(s, recv)
            self.indent -= 1
            if stmt.orelse:
                self.emit("} else {")
                self.indent += 1
                for s in stmt.orelse:
                    self._visit_init_stmt(s, recv)
                self.indent -= 1
            self.emit("}")
            return
        # Default: visit normally
        self.visit(stmt)

    def _is_nil_list_init(self, stmt: ast.If) -> bool:
        """Check if statement is 'if x is None: x = []' pattern."""
        # Check if test is 'x is None'
        test = stmt.test
        if not isinstance(test, ast.Compare):
            return False
        if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Is):
            return False
        if not isinstance(test.comparators[0], ast.Constant) or test.comparators[0].value is not None:
            return False
        if not isinstance(test.left, ast.Name):
            return False
        param_name = test.left.id
        # Check if body is single assignment 'x = []'
        if len(stmt.body) != 1:
            return False
        body = stmt.body[0]
        if not isinstance(body, ast.Assign):
            return False
        if len(body.targets) != 1 or not isinstance(body.targets[0], ast.Name):
            return False
        if body.targets[0].id != param_name:
            return False
        # Check if value is empty list
        return isinstance(body.value, ast.List) and len(body.value.elts) == 0

    def visit_Return(self, node: ast.Return):
        if node.value:
            self.emit(f"return {self.visit_expr(node.value)}")
        else:
            self.emit("return")

    def visit_Assign(self, node: ast.Assign):
        target = node.targets[0]
        if isinstance(target, ast.Attribute):
            # self.x = y or obj.x = y
            obj = self.visit_expr(target.value)
            attr = self._public_name(target.attr)
            value = self.visit_expr(node.value)
            self.emit(f"{obj}.{attr} = {value}")
        elif isinstance(target, ast.Subscript):
            # x[i] = y
            self.emit(f"{self.visit_expr(target)} = {self.visit_expr(node.value)}")
        elif isinstance(target, ast.Name):
            var = self._safe_name(target.id)
            # Skip empty list assignment to pre-declared slice variables
            if (isinstance(node.value, ast.List) and len(node.value.elts) == 0
                and target.id in self.assigned_vars
                and hasattr(self, 'block_reused_vars')
                and target.id in self.block_reused_vars):
                # Variable already pre-declared with correct type, skip assignment
                return
            value = self.visit_expr(node.value)
            # Module-level assignments need var keyword
            if not self.in_method and not self.in_class_body:
                self.emit(f"var {var} = {value}")
            elif target.id not in self.assigned_vars:
                # First assignment to this variable - use :=
                self.assigned_vars.add(target.id)
                self.emit(f"{var} := {value}")
            else:
                self.emit(f"{var} = {value}")
        else:
            self.emit(f"// TODO: Assign {ast.dump(target)}")

    def visit_AnnAssign(self, node: ast.AnnAssign):
        # Skip class-level type annotations
        if self.in_class_body and not self.in_method:
            return
        if node.value:
            target = self.visit_expr(node.target)
            value = self.visit_expr(node.value)
            self.emit(f"{target} = {value}")

    def visit_AugAssign(self, node: ast.AugAssign):
        target = self.visit_expr(node.target)
        op = self._binop_str(node.op)
        value = self.visit_expr(node.value)
        self.emit(f"{target} {op}= {value}")

    def _binop_str(self, op: ast.operator) -> str:
        ops = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.FloorDiv: "/",  # Go integer division is floor
            ast.Mod: "%",
            ast.Pow: "**",  # Need math.Pow
            ast.LShift: "<<",
            ast.RShift: ">>",
            ast.BitOr: "|",
            ast.BitXor: "^",
            ast.BitAnd: "&",
        }
        return ops.get(type(op), "?")

    def visit_If(self, node: ast.If):
        all_branches = self._collect_all_branches(node)
        # First: Pre-declare variables assigned in multiple branches (if/elif/else)
        if len(all_branches) > 1:
            all_vars = {}
            for branch in all_branches:
                vars_in_branch = self._collect_first_assignments_with_types(branch)
                for var, var_type in vars_in_branch.items():
                    if var not in all_vars:
                        all_vars[var] = var_type
            branch_var_sets = [set(self._collect_first_assignments_with_types(b).keys()) for b in all_branches]
            for var, var_type in all_vars.items():
                count = sum(1 for s in branch_var_sets if var in s)
                if count >= 2 and var not in self.assigned_vars:
                    self.emit(f"var {self._safe_name(var)} {var_type}")
                    self.assigned_vars.add(var)
        # Second: Pre-declare variables assigned in this if that will be used later
        if hasattr(self, 'block_reused_vars'):
            vars_in_if = set()
            for branch in all_branches:
                vars_in_if.update(self._collect_assignments_in_block(branch))
            for var in vars_in_if:
                if var in self.block_reused_vars and var not in self.assigned_vars:
                    var_type = self.block_reused_vars[var]
                    self.emit(f"var {self._safe_name(var)} {var_type}")
                    self.assigned_vars.add(var)
        self._emit_if(node, is_elif=False)

    def _collect_all_branches(self, node: ast.If) -> list:
        """Collect all branches of an if-elif-else chain."""
        branches = [node.body]
        current = node
        while current.orelse:
            if len(current.orelse) == 1 and isinstance(current.orelse[0], ast.If):
                # elif branch
                current = current.orelse[0]
                branches.append(current.body)
            else:
                # else branch
                branches.append(current.orelse)
                break
        return branches

    def _collect_first_assignments_with_types(self, stmts: list) -> dict:
        """Collect variables first assigned with inferred types."""
        vars_with_types = {}
        for stmt in stmts:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id not in self.assigned_vars:
                        var_type = self._infer_expr_type(stmt.value)
                        vars_with_types[target.id] = var_type
            elif isinstance(stmt, ast.If):
                vars_with_types.update(self._collect_first_assignments_with_types(stmt.body))
                if stmt.orelse:
                    vars_with_types.update(self._collect_first_assignments_with_types(stmt.orelse))
        return vars_with_types

    def _infer_expr_type(self, node: ast.expr) -> str:
        """Infer Go type from expression."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, int):
                return "int"
            if isinstance(node.value, str):
                return "string"
            if isinstance(node.value, bool):
                return "bool"
        if isinstance(node, ast.BinOp):
            # Arithmetic ops usually return int
            if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.BitAnd, ast.BitOr)):
                return "int"
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in ("len", "parseInt", "int", "ord"):
                    return "int"
                if func_name in ("str", "joinStrings", "substring"):
                    return "string"
                # Functions that return int (based on name patterns)
                if "find" in func_name.lower() or "index" in func_name.lower() or "end" in func_name.lower():
                    return "int"
                # Functions that return string (based on name patterns)
                if "format" in func_name.lower() or "to_sexp" in func_name.lower():
                    return "string"
            # Method calls that return strings
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == "join":
                    return "string"
        # Subscript on a parts list is usually a Node
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name):
                if "parts" in node.value.id or "nodes" in node.value.id:
                    return "Node"
        return "interface{}"

    def _emit_if(self, node: ast.If, is_elif: bool):
        test = self.visit_expr(node.test)
        # Handle truthiness for non-boolean types in if conditions
        if isinstance(node.test, ast.Name):
            name = node.test.id
            if name in ("parsed", "node", "cmd", "tree"):
                test = f"({test} != nil)"
            elif name.endswith("_parts") or name in ("result", "parts", "items"):
                test = f"(len({test}) > 0)"
            elif "str" in name.lower() or name in ("inner", "value", "text"):
                test = f'({test} != "")'
        elif isinstance(node.test, ast.Attribute):
            # Handle self.redirects, s.Redirects, etc.
            attr = node.test.attr
            if attr in ("redirects", "words", "parts", "commands", "items", "args",
                        "init", "condition", "update", "in_words", "cases", "patterns"):
                test = f"(len({test}) > 0)"
            elif attr in ("command", "body", "target", "then_part", "else_part", "else_body", "then_body"):
                test = f"({test} != nil)"
        if is_elif:
            self.emit_raw("\t" * self.indent + f"}} else if {test} {{")
        else:
            self.emit(f"if {test} {{")
        self.indent += 1
        for stmt in node.body:
            self.emit_comments_before(stmt.lineno)
            self.visit(stmt)
        self.indent -= 1
        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                self._emit_if(node.orelse[0], is_elif=True)
            else:
                self.emit("} else {")
                self.indent += 1
                for stmt in node.orelse:
                    self.emit_comments_before(stmt.lineno)
                    self.visit(stmt)
                self.indent -= 1
                self.emit("}")
        else:
            self.emit("}")

    def visit_While(self, node: ast.While):
        # Pre-declare variables assigned in this loop that will be used later
        if hasattr(self, 'block_reused_vars'):
            vars_in_loop = self._collect_assignments_in_block(node.body)
            for var in vars_in_loop:
                if var in self.block_reused_vars and var not in self.assigned_vars:
                    var_type = self.block_reused_vars[var]
                    self.emit(f"var {self._safe_name(var)} {var_type}")
                    self.assigned_vars.add(var)
        test = self.visit_expr(node.test)
        self.emit(f"for {test} {{")
        self.indent += 1
        for stmt in node.body:
            self.emit_comments_before(stmt.lineno)
            self.visit(stmt)
        self.indent -= 1
        self.emit("}")

    def visit_For(self, node: ast.For):
        # Pre-declare variables assigned in this loop that will be used later
        if hasattr(self, 'block_reused_vars'):
            vars_in_loop = self._collect_assignments_in_block(node.body)
            for var in vars_in_loop:
                if var in self.block_reused_vars and var not in self.assigned_vars:
                    var_type = self.block_reused_vars[var]
                    self.emit(f"var {self._safe_name(var)} {var_type}")
                    self.assigned_vars.add(var)
        target = self.visit_expr(node.target)
        iter_expr = node.iter
        # Handle range() specially
        if (
            isinstance(iter_expr, ast.Call)
            and isinstance(iter_expr.func, ast.Name)
            and iter_expr.func.id == "range"
        ):
            args = iter_expr.args
            if len(args) == 1:
                end = self.visit_expr(args[0])
                self.emit(f"for {target} := 0; {target} < {end}; {target}++ {{")
            elif len(args) == 2:
                start = self.visit_expr(args[0])
                end = self.visit_expr(args[1])
                self.emit(f"for {target} := {start}; {target} < {end}; {target}++ {{")
            else:
                start, end, step = args
                start_val = self.visit_expr(start)
                end_val = self.visit_expr(end)
                step_val = self.visit_expr(step)
                # Check if step is negative
                is_negative = False
                if isinstance(step, ast.UnaryOp) and isinstance(step.op, ast.USub):
                    is_negative = True
                elif isinstance(step, ast.Constant) and step.value < 0:
                    is_negative = True
                if is_negative:
                    self.emit(f"for {target} := {start_val}; {target} > {end_val}; {target}-- {{")
                else:
                    self.emit(f"for {target} := {start_val}; {target} < {end_val}; {target} += {step_val} {{")
        else:
            iterable = self.visit_expr(iter_expr)
            self.emit(f"for _, {target} := range {iterable} {{")
        self.indent += 1
        for stmt in node.body:
            self.emit_comments_before(stmt.lineno)
            self.visit(stmt)
        self.indent -= 1
        self.emit("}")

    def visit_Expr(self, node: ast.Expr):
        # Skip docstrings
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return
        self.emit(f"{self.visit_expr(node.value)}")

    def visit_Pass(self, node: ast.Pass):
        pass

    def visit_Break(self, node: ast.Break):
        self.emit("break")

    def visit_Continue(self, node: ast.Continue):
        self.emit("continue")

    def visit_Raise(self, node: ast.Raise):
        if node.exc:
            exc = self.visit_expr(node.exc)
            self.emit(f"panic({exc})")
        else:
            self.emit("panic(nil)")

    def visit_Try(self, node: ast.Try):
        # Go doesn't have try/except, use defer/recover pattern
        # For now, emit the try body inline (simplified)
        self.emit("// try {")
        for stmt in node.body:
            self.emit_comments_before(stmt.lineno)
            self.visit(stmt)
        if node.handlers:
            self.emit("// } catch {")
            for handler in node.handlers:
                for stmt in handler.body:
                    self.emit_comments_before(stmt.lineno)
                    self.emit(f"// {self._stmt_to_go(stmt)}")
        self.emit("// }")

    def _stmt_to_go(self, stmt: ast.stmt) -> str:
        """Convert a statement to Go code string (for comments)."""
        if isinstance(stmt, ast.Return):
            if stmt.value:
                return f"return {self.visit_expr(stmt.value)}"
            return "return"
        return "..."

    # Expression visitors return strings
    def visit_expr(self, node: ast.expr) -> str:
        method = f"visit_expr_{node.__class__.__name__}"
        if hasattr(self, method):
            return getattr(self, method)(node)
        return f"/* TODO: {node.__class__.__name__} */"

    def visit_expr_Name(self, node: ast.Name) -> str:
        mapping = {
            "True": "true",
            "False": "false",
            "None": "nil",
            "self": self._receiver_name(self.current_class) if self.current_class else "self",
            "NotImplementedError": 'fmt.Errorf("not implemented")',
        }
        name = mapping.get(node.id)
        if name:
            return name
        return self._safe_name(node.id)

    def visit_expr_Constant(self, node: ast.Constant) -> str:
        if isinstance(node.value, str):
            escaped = (
                node.value.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\t", "\\t")
                .replace("\r", "\\r")
                .replace("\x00", "\\x00")
            )
            return f'"{escaped}"'
        if isinstance(node.value, bytes):
            return "[]byte{" + ", ".join(str(b) for b in node.value) + "}"
        if node.value is None:
            return "nil"
        if node.value is True:
            return "true"
        if node.value is False:
            return "false"
        return repr(node.value)

    def visit_expr_Attribute(self, node: ast.Attribute) -> str:
        value = self.visit_expr(node.value)
        attr = self._public_name(node.attr)
        # For .kind on a loop variable over Node slices, use GetKind() method
        if node.attr == "kind":
            return f"{value}.GetKind()"
        # For .command on Node types, use getCommand() helper
        if node.attr == "command" and isinstance(node.value, ast.Name):
            if node.value.id in ("node", "n", "cmdsub", "procsub"):
                return f"getCommand({value})"
        # For .words and .redirects on Node, need type assertion to *Command
        if node.attr in ("words", "redirects") and isinstance(node.value, ast.Name):
            if node.value.id in ("cmd", "node", "command"):
                return f"{value}.(*Command).{attr}"
        # For .op on Node (from subscript/type assertion), need type assertion to *Operator
        # But not if the object is already an Operator (like o.Op or self in Operator methods)
        if node.attr == "op":
            if isinstance(node.value, ast.Name) and node.value.id in ("o", "self", "r"):
                return f"{value}.{attr}"  # Already *Operator
            return f"{value}.(*Operator).{attr}"
        return f"{value}.{attr}"

    def visit_expr_Subscript(self, node: ast.Subscript) -> str:
        value = self.visit_expr(node.value)
        if isinstance(node.slice, ast.Slice):
            lower = self.visit_expr(node.slice.lower) if node.slice.lower else "0"
            upper = self.visit_expr(node.slice.upper) if node.slice.upper else ""
            if upper:
                return f"{value}[{lower}:{upper}]"
            return f"{value}[{lower}:]"
        idx = self.visit_expr(node.slice)
        result = f"{value}[{idx}]"
        # Add type assertion for interface slice access that should be Node
        if isinstance(node.value, ast.Name):
            var_name = node.value.id
            if "parts" in var_name or "nodes" in var_name or var_name in ("left", "right"):
                return f"{result}.(Node)"
            # Handle pair-like access (tuple unpacking simulation)
            if var_name in ("pair", "last_pair") and isinstance(node.slice, ast.Constant):
                if node.slice.value == 0:
                    return f"pairFirst({value})"
                elif node.slice.value == 1:
                    return f"pairSecond({value})"
        return result

    def visit_expr_Call(self, node: ast.Call) -> str:
        args = [self.visit_expr(a) for a in node.args]
        args_str = ", ".join(args)
        # Handle method calls
        if isinstance(node.func, ast.Attribute):
            obj = self.visit_expr(node.func.value)
            method = node.func.attr
            # Map Python methods to Go
            if method == "append":
                # Handle appending to byte arrays
                if len(node.args) == 1:
                    arg = node.args[0]
                    # If appending ord(x) to result, handle byte conversion
                    if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) and arg.func.id == "ord":
                        if len(arg.args) == 1:
                            ord_arg = arg.args[0]
                            inner_arg = self.visit_expr(ord_arg)
                            # If ord() of a subscript or simple var (byte), just use it
                            if isinstance(ord_arg, (ast.Subscript, ast.Name)):
                                return f"{obj} = append({obj}, {inner_arg})"
                    # If appending x.encode() where x is a subscript (already byte)
                    if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute):
                        if arg.func.attr == "encode" and isinstance(arg.func.value, ast.Subscript):
                            inner_arg = self.visit_expr(arg.func.value)
                            return f"{obj} = append({obj}, {inner_arg})"
                    # Cast int to byte when appending int variables to byte arrays
                    if isinstance(arg, ast.Name):
                        arg_name = arg.id
                        if "byte" in arg_name or arg_name in ("simple",):
                            return f"{obj} = append({obj}, byte({args_str}))"
                return f"{obj} = append({obj}, {args_str})"
            if method == "extend":
                # If extending with x.encode() where x is a subscript (single byte)
                if len(node.args) == 1:
                    arg = node.args[0]
                    if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute):
                        if arg.func.attr == "encode" and isinstance(arg.func.value, ast.Subscript):
                            inner_arg = self.visit_expr(arg.func.value)
                            return f"{obj} = append({obj}, {inner_arg})"
                return f"{obj} = append({obj}, {args_str}...)"
            if method == "startswith":
                if len(args) == 2:
                    # s.startswith(prefix, pos) -> strings.HasPrefix(s[pos:], prefix)
                    return f"strings.HasPrefix({obj}[{args[1]}:], {args[0]})"
                return f"strings.HasPrefix({obj}, {args_str})"
            if method == "endswith":
                if len(args) == 2:
                    # s.endswith(suffix, pos) -> strings.HasSuffix(s[:pos], suffix)
                    return f"strings.HasSuffix({obj}[:{args[1]}], {args[0]})"
                return f"strings.HasSuffix({obj}, {args_str})"
            if method == "find":
                return f"strings.Index({obj}, {args_str})"
            if method == "rfind":
                return f"strings.LastIndex({obj}, {args_str})"
            if method == "replace":
                return f"strings.ReplaceAll({obj}, {args_str})"
            if method == "strip":
                return f"strings.TrimSpace({obj})"
            if method == "lstrip":
                if args:
                    return f"strings.TrimLeft({obj}, {args_str})"
                return f"strings.TrimLeft({obj}, \" \\t\\n\")"
            if method == "rstrip":
                if args:
                    return f"strings.TrimRight({obj}, {args_str})"
                return f"strings.TrimRight({obj}, \" \\t\\n\")"
            if method == "lower":
                return f"strings.ToLower({obj})"
            if method == "upper":
                return f"strings.ToUpper({obj})"
            if method == "join":
                # Use joinStrings for interface slices (variables that could be []interface{})
                if len(node.args) == 1:
                    arg = node.args[0]
                    if isinstance(arg, ast.Name):
                        var_name = arg.id
                        if var_name in ("result", "normalized", "arith_content", "parts", "items"):
                            return f"joinStrings({args_str}, {obj})"
                    # Also use joinStrings for function calls like _sublist/sublist
                    if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name):
                        if arg.func.id in ("sublist", "_sublist"):
                            return f"joinStrings({args_str}, {obj})"
                return f"strings.Join({args_str}, {obj})"
            if method == "split":
                if args:
                    return f"strings.Split({obj}, {args_str})"
                return f"strings.Fields({obj})"
            if method == "isalpha":
                # If obj is a subscript (byte), convert to string
                if isinstance(node.func.value, ast.Subscript):
                    return f"isAlpha_h(string({obj}))"
                return f"isAlpha_h({obj})"
            if method == "isdigit":
                if isinstance(node.func.value, ast.Subscript):
                    return f"isDigit_h(string({obj}))"
                return f"isDigit_h({obj})"
            if method == "isalnum":
                if isinstance(node.func.value, ast.Subscript):
                    return f"isAlnum_h(string({obj}))"
                return f"isAlnum_h({obj})"
            if method == "isspace":
                if isinstance(node.func.value, ast.Subscript):
                    return f"isSpace_h(string({obj}))"
                return f"isSpace_h({obj})"
            if method == "encode":
                # If encoding a subscript (s[i]), it's already a byte
                if isinstance(node.func.value, ast.Subscript):
                    return obj
                return f"[]byte({obj})"
            if method == "decode":
                return f"string({obj})"
            if method == "get":
                if len(args) >= 2:
                    return f"mapGet({obj}, {args_str})"
                return f"{obj}[{args[0]}]"
            # Handle methods with default arguments
            if method == "parse_list":
                # def parse_list(self, at_start: bool = True) -> Node | None
                if len(args) == 0:
                    args.append("true")
                    args_str = ", ".join(args)
            # Method call
            go_method = self._method_name(method)
            return f"{obj}.{go_method}({args_str})"
        # Handle builtins
        if isinstance(node.func, ast.Name):
            name = node.func.id
            if name == "len":
                return f"len({args_str})"
            if name == "str":
                return f"fmt.Sprintf(\"%v\", {args_str})"
            if name == "int":
                if len(args) >= 2:
                    return f"parseInt({args_str})"
                return f"toInt({args_str})"
            if name == "ord":
                # If arg is a subscript (s[i]) or a simple name, just cast to int
                if len(node.args) == 1:
                    arg = node.args[0]
                    if isinstance(arg, ast.Subscript) or isinstance(arg, ast.Name):
                        return f"int({args_str})"
                return f"int([]rune({args_str})[0])"
            if name == "chr":
                return f"string(rune({args_str}))"
            if name == "isinstance":
                obj_expr = self.visit_expr(node.args[0])
                type_expr = node.args[1]
                if isinstance(type_expr, ast.Name):
                    type_name = self._public_name(type_expr.id)
                    return f"_, ok := {obj_expr}.(*{type_name}); ok"
                return f"/* isinstance TODO */"
            if name == "getattr":
                obj = self.visit_expr(node.args[0])
                attr = self.visit_expr(node.args[1])
                if len(args) >= 3:
                    default = self.visit_expr(node.args[2])
                    return f"getAttr({obj}, {attr}, {default})"
                return f"getAttr({obj}, {attr}, nil)"
            if name == "bytearray":
                return "[]byte{}"
            if name == "list":
                if args:
                    return f"toSlice({args_str})"
                return "[]interface{}{}"
            if name == "set":
                return f"toSet({args_str})"
            if name == "max":
                return f"max({args_str})"
            if name == "min":
                return f"min({args_str})"
            if name == "print":
                return f"fmt.Println({args_str})"
            # Check if it's a class constructor
            if name in self.class_names:
                go_name = self._public_name(name)
                # If constructing List with a []interface{} variable, wrap with toNodes
                if name == "List" and len(node.args) == 1:
                    arg = node.args[0]
                    if isinstance(arg, ast.Name) and arg.id in ("left", "right", "inner_parts", "parts"):
                        return f"New{go_name}(toNodes({args_str}))"
                # Word constructor has default parts=nil
                if name == "Word" and len(node.args) == 1:
                    return f"New{go_name}({args_str}, nil)"
                return f"New{go_name}({args_str})"
            # Handle functions with default arguments
            if name == "_format_cmdsub_node" or name == "format_cmdsub_node":
                # def _format_cmdsub_node(node: Node, indent: int = 0, in_procsub: bool = False)
                while len(args) < 3:
                    if len(args) == 1:
                        args.append("0")
                    elif len(args) == 2:
                        args.append("false")
                args_str = ", ".join(args)
            # Regular function call
            go_name = self._func_name(name)
            return f"{go_name}({args_str})"
        return f"{self.visit_expr(node.func)}({args_str})"

    def visit_expr_BinOp(self, node: ast.BinOp) -> str:
        left = self.visit_expr(node.left)
        right = self.visit_expr(node.right)
        op = self._binop_str(node.op)
        # String concatenation
        if isinstance(node.op, ast.Add):
            # If left is a byte (subscript on string) and right is a string, convert left
            if isinstance(node.left, ast.Name) and self._is_string_expr(node.right):
                # Variable that might be a byte (from subscript assignment)
                if node.left.id in ("direction", "ch", "c", "byte_char"):
                    return f"(byteToStr({left}) + {right})"
            # Check if likely string context
            if self._is_string_expr(node.left) or self._is_string_expr(node.right):
                return f"({left} + {right})"
        return f"({left} {op} {right})"

    def _is_string_expr(self, node: ast.expr) -> bool:
        """Check if expression is likely a string."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            return node.func.id == "str"
        return False

    def visit_expr_Compare(self, node: ast.Compare) -> str:
        result = self.visit_expr(node.left)
        # Check if left side is .op attribute or 'op' variable (which is a string, not byte)
        left_is_string = False
        if isinstance(node.left, ast.Attribute) and node.left.attr == "op":
            left_is_string = True
        elif isinstance(node.left, ast.Name) and node.left.id == "op":
            left_is_string = True
        for op, comparator in zip(node.ops, node.comparators, strict=True):
            op_str = self._cmpop_str(op)
            if isinstance(op, ast.In):
                # x in y -> contains(y, x)
                return f"contains({self.visit_expr(comparator)}, {result})"
            if isinstance(op, ast.NotIn):
                return f"!contains({self.visit_expr(comparator)}, {result})"
            # For .op comparisons, use string literals; otherwise use rune for single chars
            if left_is_string:
                cmp_expr = self._string_operand(comparator)
            else:
                cmp_expr = self._comparison_operand(comparator)
            result += f" {op_str} {cmp_expr}"
        return f"({result})"

    def _string_operand(self, node: ast.expr) -> str:
        """Convert operand for string comparison, always using string literals."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            # Escape special characters for Go string
            s = node.value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
            return f'"{s}"'
        return self.visit_expr(node)

    def _comparison_operand(self, node: ast.expr) -> str:
        """Convert operand for comparison, using rune literals for single chars."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if len(node.value) == 1:
                c = node.value
                if c == "'":
                    return "'\\''"
                if c == "\\":
                    return "'\\\\'"
                if c == "\n":
                    return "'\\n'"
                if c == "\t":
                    return "'\\t'"
                if c == "\r":
                    return "'\\r'"
                if c == "\x00":
                    return "'\\x00'"
                if c == "\x01":
                    return "'\\x01'"
                if c == "\x7f":
                    return "'\\x7f'"
                return f"'{c}'"
            # Empty string comparison: use len check instead
            if node.value == "":
                return '""'  # Keep as empty string, caller handles
        return self.visit_expr(node)

    def _cmpop_str(self, op: ast.cmpop) -> str:
        ops = {
            ast.Eq: "==",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
            ast.Is: "==",
            ast.IsNot: "!=",
            ast.In: "in",
            ast.NotIn: "not in",
        }
        return ops.get(type(op), "?")

    def visit_expr_BoolOp(self, node: ast.BoolOp) -> str:
        op = " && " if isinstance(node.op, ast.And) else " || "
        values = []
        for v in node.values:
            expr = self.visit_expr(v)
            # Handle truthiness for non-boolean types
            if isinstance(v, ast.Name):
                name = v.id
                # String-like variable names need != "" check
                if "str" in name.lower() or name in ("inner", "value", "text", "s", "prefix", "suffix", "expanded"):
                    expr = f'({expr} != "")'
                # Slice-like variable names need len() > 0 check
                elif name in ("normalized", "result", "parts", "items", "elements"):
                    expr = f"(len({expr}) > 0)"
                # Node-like variable names need != nil check
                elif name in ("parsed", "node", "cmd", "tree"):
                    expr = f"({expr} != nil)"
            values.append(expr)
        return f"({op.join(values)})"

    def visit_expr_UnaryOp(self, node: ast.UnaryOp) -> str:
        operand = self.visit_expr(node.operand)
        if isinstance(node.op, ast.Not):
            if isinstance(node.operand, ast.Name):
                name = node.operand.id
                # Slice-like variable names need len() == 0 check
                if name.endswith("_parts") or name in ("result", "parts", "items", "elements", "nodes", "cmdsub_parts", "procsub_parts"):
                    return f"(len({operand}) == 0)"
                # String-like variable names need == "" check
                if "str" in name.lower() or name in ("value", "text", "s", "inner", "prefix", "suffix"):
                    return f'({operand} == "")'
            return f"!({operand})"
        if isinstance(node.op, ast.USub):
            return f"-{operand}"
        if isinstance(node.op, ast.UAdd):
            return f"+{operand}"
        if isinstance(node.op, ast.Invert):
            return f"^{operand}"
        return f"/* UnaryOp */{operand}"

    def visit_expr_IfExp(self, node: ast.IfExp) -> str:
        # Go doesn't have ternary, need helper function
        test = self.visit_expr(node.test)
        body = self.visit_expr(node.body)
        orelse = self.visit_expr(node.orelse)
        return f"ternary({test}, {body}, {orelse})"

    def visit_expr_List(self, node: ast.List) -> str:
        elements = ", ".join(self.visit_expr(e) for e in node.elts)
        return f"[]interface{{}}{{{elements}}}"

    def visit_expr_Dict(self, node: ast.Dict) -> str:
        pairs = []
        for k, v in zip(node.keys, node.values, strict=True):
            pairs.append(f"{self.visit_expr(k)}: {self.visit_expr(v)}")
        return "map[string]interface{}{" + ", ".join(pairs) + "}"

    def visit_expr_Tuple(self, node: ast.Tuple) -> str:
        elements = ", ".join(self.visit_expr(e) for e in node.elts)
        return f"[]interface{{}}{{{elements}}}"

    def visit_expr_Set(self, node: ast.Set) -> str:
        elements = ", ".join(self.visit_expr(e) for e in node.elts)
        return f"toSet([]interface{{}}{{{elements}}})"

    def visit_expr_JoinedStr(self, node: ast.JoinedStr) -> str:
        """Handle f-strings."""
        parts = []
        format_args = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                # Escape % for fmt.Sprintf
                parts.append(value.value.replace("%", "%%"))
            elif isinstance(value, ast.FormattedValue):
                parts.append("%v")
                format_args.append(self.visit_expr(value.value))
        format_str = "".join(parts).replace('"', '\\"').replace("\n", "\\n")
        if format_args:
            args = ", ".join(format_args)
            return f'fmt.Sprintf("{format_str}", {args})'
        return f'"{format_str}"'


def main():
    if len(sys.argv) < 2:
        print("Usage: transpile-go.py <input.py>", file=sys.stderr)
        sys.exit(1)
    source = Path(sys.argv[1]).read_text()
    transpiler = GoTranspiler()
    print(transpiler.transpile(source))


if __name__ == "__main__":
    main()
