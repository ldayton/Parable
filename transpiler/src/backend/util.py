"""Shared utilities for backend code emitters."""

from __future__ import annotations

import re


def to_snake(name: str) -> str:
    """Convert camelCase/PascalCase to snake_case."""
    if name.startswith("_"):
        name = name[1:]
    if "_" in name or name.islower():
        return name.lower()
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    if name.startswith("_"):
        name = name[1:]
    if "_" not in name:
        return name[0].lower() + name[1:] if name else name
    parts = name.split("_")
    return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])


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
