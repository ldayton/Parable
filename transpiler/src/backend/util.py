"""Shared utilities for backend code emitters."""

from __future__ import annotations

from re import sub as re_sub

# Go reserved words that need renaming
GO_RESERVED = frozenset(
    {
        "break",
        "case",
        "chan",
        "const",
        "continue",
        "default",
        "defer",
        "else",
        "fallthrough",
        "for",
        "func",
        "go",
        "goto",
        "if",
        "import",
        "interface",
        "map",
        "package",
        "range",
        "return",
        "select",
        "struct",
        "switch",
        "type",
        "var",
    }
)


def _upper_first(s: str) -> str:
    """Uppercase the first character of a string."""
    return (s[0].upper() + s[1:]) if s else ""


def go_to_pascal(name: str) -> str:
    """Convert snake_case to PascalCase for Go. Private methods (underscore prefix) become unexported."""
    is_private = name.startswith("_")
    if is_private:
        name = name[1:]
    parts = name.split("_")
    # Use upper on first char only (not capitalize which lowercases rest)
    result = "".join(_upper_first(p) for p in parts)
    # All-caps names (constants) stay all-caps even if originally private
    if name.isupper():
        return result
    if is_private:
        # Make first letter lowercase for unexported (private) names
        return result[0].lower() + result[1:] if result else result
    return result


def go_to_camel(name: str) -> str:
    """Convert snake_case to camelCase for Go."""
    if name == "self":
        return name
    if name.startswith("_"):
        name = name[1:]
    parts = name.split("_")
    if not parts:
        return name
    # All-caps names (constants) should use PascalCase in Go
    if name.isupper():
        return "".join(_upper_first(p) for p in parts)
    result = parts[0] + "".join(_upper_first(p) for p in parts[1:])
    # Handle Go reserved words
    if result in GO_RESERVED:
        return result + "_"
    return result


def to_snake(name: str) -> str:
    """Convert camelCase/PascalCase to snake_case."""
    if name.startswith("_"):
        name = name[1:]
    if "_" in name or name.islower():
        return name.lower()
    s1 = re_sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re_sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def to_camel(name: str) -> str:
    """Convert snake_case to camelCase, preserving leading underscores."""
    prefix = ""
    if name.startswith("_"):
        prefix = "_"
        name = name[1:]
    if "_" not in name:
        return prefix + (name[0].lower() + name[1:] if name else name)
    parts = name.split("_")
    return prefix + parts[0].lower() + "".join(p.capitalize() for p in parts[1:])


def to_pascal(name: str) -> str:
    """Convert snake_case to PascalCase."""
    if name.startswith("_"):
        name = name[1:]
    parts = name.split("_")
    return "".join(p.capitalize() for p in parts)


def to_screaming_snake(name: str) -> str:
    """Convert to SCREAMING_SNAKE_CASE."""
    return to_snake(name).upper()


def escape_string(value: str) -> str:
    """Escape a string for use in a string literal (without quotes)."""
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
        .replace("\r", "\\r")
        .replace("\x01", "\\u0001")
        .replace("\x7f", "\\u007f")
    )


class Emitter:
    """Base class for code emitters with indentation tracking."""

    def __init__(self, indent_str: str = "    ") -> None:
        self.indent = 0
        self.lines: list[str] = []
        self._indent_str = indent_str

    def line(self, text: str = "") -> None:
        """Emit a line with current indentation."""
        if text:
            self.lines.append(self._indent_str * self.indent + text)
        else:
            self.lines.append("")

    def output(self) -> str:
        """Return the accumulated output as a string."""
        return "\n".join(self.lines)
