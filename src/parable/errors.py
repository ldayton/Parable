"""Error types for Parable."""


class ParseError(Exception):
    """Raised when parsing fails."""

    def __init__(self, message: str, pos: int = None, line: int = None):
        self.message = message
        self.pos = pos
        self.line = line
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        if self.line is not None and self.pos is not None:
            return f"Parse error at line {self.line}, position {self.pos}: {self.message}"
        elif self.pos is not None:
            return f"Parse error at position {self.pos}: {self.message}"
        return f"Parse error: {self.message}"
