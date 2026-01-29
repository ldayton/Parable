"""Frontend package - converts Python AST to IR."""

from .frontend import Frontend
from .parse import ParseError, parse


def compile(source: str) -> "Module":
    """Frontend pipeline: source → IR Module. Orchestrates phases 2-9."""
    # Phase 2: Parse to dict-based AST
    _ast_dict = parse(source)  # validates syntax

    # Phases 3-9: Use existing Frontend (still uses ast.* internally)
    fe = Frontend()
    return fe.transpile(source)


__all__ = ["Frontend", "compile", "parse", "ParseError"]
