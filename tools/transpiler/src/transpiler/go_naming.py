"""Name conversion utilities for Go transpiler."""

# Go reserved words mapping
GO_RESERVED_WORDS: dict[str, str] = {
    "type": "typ",
    "func": "fn",
    "var": "variable",
    "range": "rng",
    "map": "m",
    "interface": "iface",
    "chan": "ch",
    "select": "sel",
    "case": "caseVal",
    "default": "defaultVal",
    "package": "pkg",
    "import": "imp",
    "go": "goVal",
    "defer": "deferVal",
    "return": "ret",
    "break": "brk",
    "continue": "cont",
    "fallthrough": "fallthru",
    "if": "ifVal",
    "else": "elseVal",
    "for": "forVal",
    "switch": "switchVal",
    "const": "constVal",
    "struct": "structVal",
}


class NamingMixin:
    """Mixin providing name conversion methods for Go transpiler."""

    def _safe_go_name(self, name: str) -> str:
        """Make sure name is not a Go reserved word."""
        return GO_RESERVED_WORDS.get(name, name)

    def _snake_to_pascal(self, name: str) -> str:
        """Convert snake_case to PascalCase."""
        return "".join(word.capitalize() for word in name.split("_"))

    def _snake_to_camel(self, name: str) -> str:
        """Convert snake_case to camelCase."""
        if name == "_":
            return "_"
        parts = name.split("_")
        # Filter out empty parts from leading underscores
        parts = [p for p in parts if p]
        if not parts:
            return name
        return parts[0] + "".join(word.capitalize() for word in parts[1:])

    def _to_go_var(self, name: str) -> str:
        """Convert a Python variable name to a Go variable name."""
        return self._safe_go_name(self._snake_to_camel(name))

    def _to_go_func_name(self, name: str) -> str:
        """Convert Python function name to Go function name."""
        if name.startswith("_"):
            # Keep leading underscore for private functions
            return name[0] + self._snake_to_pascal(name[1:])
        return self._snake_to_pascal(name)

    def _capitalize_first(self, name: str) -> str:
        """Capitalize first letter of name."""
        if not name:
            return name
        return name[0].upper() + name[1:]

    def _to_go_field_name(self, name: str) -> str:
        """Convert Python field name to Go exported field name."""
        if name.startswith("_"):
            # Private fields stay private but capitalize rest
            return name[0] + self._capitalize_first(name[1:])
        return self._capitalize_first(name)
