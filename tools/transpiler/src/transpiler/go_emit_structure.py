"""Module and struct emission for Go transpiler."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .go_types import ClassInfo


class EmitStructureMixin:
    """Mixin for module-level and struct code emission."""

    # Functions that are replaced by hardcoded Go implementations (skip transpilation)
    SKIP_FUNCTIONS = {
        "_substring",  # Replaced by rune-based _Substring in _emit_helpers()
    }

    # Functions that require duck typing (Part 6d) or have complex patterns - skip body for now
    SKIP_BODY_FUNCTIONS = {
        # Duck typing (Part 6d) - isinstance-based dispatch
        "_format_cond_value",
        "_collect_cmdsubs",
        "_collect_assignments",
        # Complex lexer methods with walrus operators
        "_parse_matched_pair",
        "_read_bracket_regex",
    }

    # Methods that truly need manual implementation (tuple stacks, complex patterns)
    # KEEP THIS MINIMAL - fix transpiler issues rather than skipping methods
    SKIP_METHODS = {
        # Higher-order function patterns and arithmetic parsing
        # Higher-order function - not called, kept as stub
        "_arith_parse_left_assoc",
    }

    def visit_Module(self, node: ast.Module):
        """Emit package declaration and all definitions."""
        # Package comment with usage example
        self.emit("// Package parable is a recursive descent parser for bash.")
        self.emit("//")
        self.emit("// MIT License - https://github.com/ldayton/Parable")
        self.emit("//")
        self.emit('//   import "parable"')
        self.emit('//   ast, err := parable.Parse("ps aux | grep python")')
        self.emit("package parable")
        self.emit("")
        # Emit imports
        self._emit_imports()
        # Emit error types first
        self._emit_error_types()
        # Emit Node interface
        self._emit_node_interface()
        # Emit module-level constants
        self._emit_module_constants(node)
        # Emit helper types
        self._emit_helper_types()
        # Emit all structs
        self._emit_all_structs()
        # Emit helper functions
        self._emit_helper_functions(node)
        # Emit methods for all classes
        self._emit_all_methods(node)

    def _emit_module_constants(self, tree: ast.Module):
        """Emit module-level constants."""
        # Skip these as they're manually emitted or handled specially
        skip_constants = {"ANSI_C_ESCAPES"}
        constants = []
        sets = []  # For set literals like RESERVED_WORDS
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        if name in skip_constants:
                            continue
                        # Check if it's a constant (uppercase or _UPPERCASE)
                        if name.isupper() or (name.startswith("_") and name[1:].isupper()):
                            if isinstance(node.value, ast.Constant):
                                constants.append((name, node.value.value))
                            elif isinstance(node.value, ast.Set):
                                # Handle set literals as map[string]bool for O(1) lookup
                                elts = []
                                for elt in node.value.elts:
                                    if isinstance(elt, ast.Constant):
                                        elts.append(elt.value)
                                if elts:
                                    sets.append((name, elts))
        if constants:
            self.emit("// Module-level constants")
            self.emit("const (")
            self.indent += 1
            for name, value in constants:
                # Convert Python name to Go name (remove leading underscore, use CamelCase)
                go_name = name.lstrip("_")
                # Convert SCREAMING_CASE to CamelCase
                parts = go_name.split("_")
                go_name = "".join(p.capitalize() for p in parts)
                if isinstance(value, int):
                    self.emit(f"{go_name} = {value}")
                elif isinstance(value, str):
                    self.emit(f'{go_name} = "{value}"')
                else:
                    self.emit(f"{go_name} = {value}")
            self.indent -= 1
            self.emit(")")
            self.emit("")
        # Emit sets as map[string]bool for O(1) lookup (Go doesn't have set type)
        for name, values in sets:
            go_name = name.lstrip("_")
            parts = go_name.split("_")
            go_name = "".join(p.capitalize() for p in parts)
            self.emit(f"var {go_name} = map[string]bool{{")
            self.indent += 1
            for val in sorted(values):
                self.emit(f'"{val}": true,')
            self.indent -= 1
            self.emit("}")
            self.emit("")

    def _emit_imports(self):
        """Emit Go import statements."""
        self.emit("import (")
        self.indent += 1
        self.emit('"fmt"')
        self.emit('"reflect"')
        self.emit('"strconv"')
        self.emit('"strings"')
        self.emit('"unicode"')
        self.emit('"unicode/utf8"')
        self.indent -= 1
        self.emit(")")
        self.emit("")
        # Suppress unused import warnings until we implement bodies
        self.emit("var (")
        self.indent += 1
        self.emit("_ = fmt.Sprintf")
        self.emit("_ = strings.Contains")
        self.emit("_ = strconv.Atoi")
        self.emit("_ = unicode.IsLetter")
        self.emit("_ = utf8.RuneCountInString")
        self.indent -= 1
        self.emit(")")
        self.emit("")

    def _emit_error_types(self):
        """Emit ParseError and MatchedPairError structs."""
        # ParseError
        self.emit("// ParseError is raised when parsing fails.")
        self.emit("type ParseError struct {")
        self.indent += 1
        self.emit("Message string")
        self.emit("Pos     int")
        self.emit("Line    int")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("func (e *ParseError) Error() string {")
        self.indent += 1
        self.emit("if e.Line != 0 && e.Pos != 0 {")
        self.indent += 1
        self.emit(
            'return fmt.Sprintf("Parse error at line %d, position %d: %s", e.Line, e.Pos, e.Message)'
        )
        self.indent -= 1
        self.emit("}")
        self.emit("if e.Pos != 0 {")
        self.indent += 1
        self.emit('return fmt.Sprintf("Parse error at position %d: %s", e.Pos, e.Message)')
        self.indent -= 1
        self.emit("}")
        self.emit('return fmt.Sprintf("Parse error: %s", e.Message)')
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # ParseError constructor
        self.emit("func NewParseError(message string, pos int, line int) *ParseError {")
        self.indent += 1
        self.emit("return &ParseError{Message: message, Pos: pos, Line: line}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # MatchedPairError
        self.emit("// MatchedPairError is raised when a matched pair is unclosed at EOF.")
        self.emit("type MatchedPairError struct {")
        self.indent += 1
        self.emit("ParseError")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # MatchedPairError constructor
        self.emit("func NewMatchedPairError(message string, pos int, line int) *MatchedPairError {")
        self.indent += 1
        self.emit("return &MatchedPairError{ParseError{Message: message, Pos: pos, Line: line}}")
        self.indent -= 1
        self.emit("}")
        self.emit("")

    def _emit_node_interface(self):
        """Emit the Node interface."""
        self.emit("// Node is the base interface for all AST nodes.")
        self.emit("type Node interface {")
        self.indent += 1
        self.emit("Kind() string")
        self.emit("ToSexp() string")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Emit helper functions and constants
        self._emit_helpers()

    def _emit_helpers(self):
        """Emit helper functions needed by transpiled code."""
        # ANSI-C escapes map
        self.emit("// ANSICEscapes maps ANSI-C escape characters to byte values")
        self.emit("var ANSICEscapes = map[rune]int{")
        self.indent += 1
        self.emit("'a': 0x07, 'b': 0x08, 'e': 0x1B, 'E': 0x1B,")
        self.emit("'f': 0x0C, 'n': 0x0A, 'r': 0x0D, 't': 0x09,")
        self.emit("'v': 0x0B, '\\\\': 0x5C, '\"': 0x22, '?': 0x3F,")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Helper functions
        self.emit("func _mapGet[K comparable, V any](m map[K]V, key K, def V) V {")
        self.indent += 1
        self.emit("if v, ok := m[key]; ok {")
        self.indent += 1
        self.emit("return v")
        self.indent -= 1
        self.emit("}")
        self.emit("return def")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("func _ternary[T any](cond bool, a, b T) T {")
        self.indent += 1
        self.emit("if cond {")
        self.indent += 1
        self.emit("return a")
        self.indent -= 1
        self.emit("}")
        self.emit("return b")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Helper to detect typed nil (e.g., (*Command)(nil) assigned to Node interface)
        self.emit("func _isNilNode(n Node) bool {")
        self.indent += 1
        self.emit("if n == nil {")
        self.indent += 1
        self.emit("return true")
        self.indent -= 1
        self.emit("}")
        self.emit("v := reflect.ValueOf(n)")
        self.emit("return v.Kind() == reflect.Ptr && v.IsNil()")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Character helper - get character (rune) from string at character index
        self.emit("func _runeAt(s string, i int) string {")
        self.indent += 1
        self.emit("runes := []rune(s)")
        self.emit("if i < 0 || i >= len(runes) {")
        self.indent += 1
        self.emit('return ""')
        self.indent -= 1
        self.emit("}")
        self.emit("return string(runes[i])")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Rune length helper - get character count (not byte count)
        self.emit("func _runeLen(s string) int {")
        self.indent += 1
        self.emit("return utf8.RuneCountInString(s)")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # String to rune (first char) - uses for range to get first rune
        self.emit("func _strToRune(s string) rune {")
        self.indent += 1
        self.emit("for _, r := range s {")
        self.indent += 1
        self.emit("return r")
        self.indent -= 1
        self.emit("}")
        self.emit("return 0")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Convert any char type (string, byte, rune) to rune
        self.emit("func _runeFromChar(c interface{}) rune {")
        self.indent += 1
        self.emit("switch v := c.(type) {")
        self.emit("case rune:")
        self.indent += 1
        self.emit("return v")
        self.indent -= 1
        self.emit("case byte:")
        self.indent += 1
        self.emit("return rune(v)")
        self.indent -= 1
        self.emit("case string:")
        self.indent += 1
        self.emit("for _, r := range v {")
        self.indent += 1
        self.emit("return r")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("return 0")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Contains helper for `in` operator
        self.emit("func _contains[T comparable](slice []T, val T) bool {")
        self.indent += 1
        self.emit("for _, v := range slice {")
        self.indent += 1
        self.emit("if v == val {")
        self.indent += 1
        self.emit("return true")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("return false")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # Contains helper for interface{} slices
        self.emit("func _containsAny(slice []interface{}, val interface{}) bool {")
        self.indent += 1
        self.emit("for _, v := range slice {")
        self.indent += 1
        self.emit("if v == val {")
        self.indent += 1
        self.emit("return true")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("return false")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # parseInt helper - int(str, base) equivalent
        self.emit("func _parseInt(s string, base int) int {")
        self.indent += 1
        self.emit("v, err := strconv.ParseInt(s, base, 64)")
        self.emit("if err != nil {")
        self.indent += 1
        self.emit("return 0")
        self.indent -= 1
        self.emit("}")
        self.emit("return int(v)")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # max/min helpers for int
        self.emit("func _max(a, b int) int {")
        self.indent += 1
        self.emit("if a > b {")
        self.indent += 1
        self.emit("return a")
        self.indent -= 1
        self.emit("}")
        self.emit("return b")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        self.emit("func _min(a, b int) int {")
        self.indent += 1
        self.emit("if a < b {")
        self.indent += 1
        self.emit("return a")
        self.indent -= 1
        self.emit("}")
        self.emit("return b")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # mustAtoi helper - int(str) equivalent
        self.emit("func _mustAtoi(s string) int {")
        self.indent += 1
        self.emit("v, err := strconv.Atoi(s)")
        self.emit("if err != nil {")
        self.indent += 1
        self.emit("return 0")
        self.indent -= 1
        self.emit("}")
        self.emit("return v")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # _strIsDigits helper - str.isdigit() equivalent (true if non-empty and all digits)
        self.emit("func _strIsDigits(s string) bool {")
        self.indent += 1
        self.emit("if len(s) == 0 {")
        self.indent += 1
        self.emit("return false")
        self.indent -= 1
        self.emit("}")
        self.emit("for _, r := range s {")
        self.indent += 1
        self.emit("if !unicode.IsDigit(r) {")
        self.indent += 1
        self.emit("return false")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("return true")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # _getattr helper - getattr(obj, attr, default) equivalent using reflection
        self.emit("func _getattr(obj interface{}, attr string, def interface{}) interface{} {")
        self.indent += 1
        self.emit("if obj == nil {")
        self.indent += 1
        self.emit("return def")
        self.indent -= 1
        self.emit("}")
        self.emit("v := reflect.ValueOf(obj)")
        self.emit("if v.Kind() == reflect.Ptr {")
        self.indent += 1
        self.emit("v = v.Elem()")
        self.indent -= 1
        self.emit("}")
        self.emit("if v.Kind() != reflect.Struct {")
        self.indent += 1
        self.emit("return def")
        self.indent -= 1
        self.emit("}")
        self.emit("// Convert snake_case to PascalCase")
        self.emit("fieldName := _snakeToPascal(attr)")
        self.emit("f := v.FieldByName(fieldName)")
        self.emit("if !f.IsValid() {")
        self.indent += 1
        self.emit("// Try lowercase 'kind' field")
        self.emit('if attr == "kind" {')
        self.indent += 1
        self.emit('f = v.FieldByName("kind")')
        self.emit("if f.IsValid() {")
        self.indent += 1
        self.emit("return f.Interface()")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit("return def")
        self.indent -= 1
        self.emit("}")
        self.emit("return f.Interface()")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # _FormatArithVal helper - formats arithmetic values for to_sexp
        self.emit("func _FormatArithVal(s string) string {")
        self.indent += 1
        self.emit("w := NewWord(s, []Node{})")
        self.emit("val := w._ExpandAllAnsiCQuotes(s)")
        self.emit("val = w._StripLocaleStringDollars(val)")
        self.emit("val = w._FormatCommandSubstitutions(val, false)")
        self.emit(
            'val = strings.ReplaceAll(strings.ReplaceAll(val, "\\\\", "\\\\\\\\"), "\\"", "\\\\\\"")'
        )
        self.emit(
            'val = strings.ReplaceAll(strings.ReplaceAll(val, "\\n", "\\\\n"), "\\t", "\\\\t")'
        )
        self.emit("return val")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # _snakeToPascal helper
        self.emit("func _snakeToPascal(s string) string {")
        self.indent += 1
        self.emit('parts := strings.Split(s, "_")')
        self.emit("for i, p := range parts {")
        self.indent += 1
        self.emit("if len(p) > 0 {")
        self.indent += 1
        self.emit("parts[i] = strings.ToUpper(p[:1]) + p[1:]")
        self.indent -= 1
        self.emit("}")
        self.indent -= 1
        self.emit("}")
        self.emit('return strings.Join(parts, "")')
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # _Substring helper - rune-based substring extraction
        self.emit("func _Substring(s string, start int, end int) string {")
        self.indent += 1
        self.emit("runes := []rune(s)")
        self.emit("if start < 0 {")
        self.indent += 1
        self.emit("start = 0")
        self.indent -= 1
        self.emit("}")
        self.emit("if end > len(runes) {")
        self.indent += 1
        self.emit("end = len(runes)")
        self.indent -= 1
        self.emit("}")
        self.emit("if start >= end {")
        self.indent += 1
        self.emit('return ""')
        self.indent -= 1
        self.emit("}")
        self.emit("return string(runes[start:end])")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # _pop helper - pop from slice (generic)
        self.emit("func _pop[T any](s *[]T) T {")
        self.indent += 1
        self.emit("last := (*s)[len(*s)-1]")
        self.emit("*s = (*s)[:len(*s)-1]")
        self.emit("return last")
        self.indent -= 1
        self.emit("}")
        self.emit("")

    def _emit_helper_types(self):
        """Emit helper types used by transpiled code."""
        # quoteStackEntry is used by QuoteState._Stack to hold (single, double) tuples
        self.emit("// quoteStackEntry holds pushed quote state (single, double)")
        self.emit("type quoteStackEntry struct {")
        self.indent += 1
        self.emit("single bool")
        self.emit("double bool")
        self.indent -= 1
        self.emit("}")
        self.emit("")

    def _emit_all_structs(self):
        """Emit all struct definitions."""
        # Skip error types (already emitted) and Node (interface)
        skip = {"ParseError", "MatchedPairError", "Node"}
        for name, info in self.symbols.classes.items():
            if name in skip:
                continue
            self._emit_struct(name, info)

    def _emit_struct(self, name: str, info: ClassInfo):
        """Emit a single struct definition."""
        from .go_overrides import FIELD_TYPE_OVERRIDES

        is_node = "Node" in info.bases
        # Emit class constants first
        if info.constants:
            self.emit(f"// {name} constants")
            self.emit("const (")
            self.indent += 1
            for const_name, const_value in info.constants.items():
                go_const_name = f"{name}_{const_name}"
                if isinstance(const_value, int):
                    # Format hex values
                    if const_value > 9 and const_value not in (10, 100, 1000):
                        self.emit(f"{go_const_name} = 0x{const_value:02X}")
                    else:
                        self.emit(f"{go_const_name} = {const_value}")
                else:
                    self.emit(f'{go_const_name} = "{const_value}"')
            self.indent -= 1
            self.emit(")")
            self.emit("")
        # Skip struct emission for enum-only classes (no fields, no __init__)
        if (
            info.constants
            and not info.fields
            and not any(m for m in info.methods if m != "__init__" or info.methods[m].params)
        ):
            return
        self.emit(f"type {name} struct {{")
        self.indent += 1
        # Embed base classes (except Node which is an interface)
        for base in info.bases:
            if base != "Node" and base != "Exception":
                self.emit(base)
        # Emit fields
        for field_name, field_info in info.fields.items():
            go_type = field_info.go_type or "interface{}"
            # Check for field type overrides
            override_key = (name, field_name)
            if override_key in FIELD_TYPE_OVERRIDES:
                go_type = FIELD_TYPE_OVERRIDES[override_key]
            # For Node structs, make 'kind' lowercase to avoid conflict with Kind() method
            if is_node and field_name == "kind":
                self.emit(f"kind {go_type}")
            else:
                go_name = self._to_go_field_name(field_name)
                self.emit(f"{go_name} {go_type}")
        # Emit additional fields from FIELD_TYPE_OVERRIDES that don't exist in the class
        for (class_name, field_name), go_type in FIELD_TYPE_OVERRIDES.items():
            if class_name == name and field_name not in info.fields:
                go_name = self._to_go_field_name(field_name)
                self.emit(f"{go_name} {go_type}")
        self.indent -= 1
        self.emit("}")
        self.emit("")
        # For Node structs, emit Kind() and ToSexp() methods to implement Node interface
        if is_node:
            receiver = name[0].lower()
            self.emit(f"func ({receiver} *{name}) Kind() string {{")
            self.indent += 1
            self.emit(f"return {receiver}.kind")
            self.indent -= 1
            self.emit("}")
            self.emit("")
            # ToSexp() will be implemented by the actual method, emit stub if not defined
            if "to_sexp" not in info.methods:
                self.emit(f"func ({receiver} *{name}) ToSexp() string {{")
                self.indent += 1
                self.emit('panic("TODO: ToSexp not implemented")')
                self.indent -= 1
                self.emit("}")
                self.emit("")

    def _emit_helper_functions(self, tree: ast.Module):
        """Emit module-level helper functions."""
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                if node.name in self.SKIP_FUNCTIONS:
                    continue
                self._emit_function(node)
