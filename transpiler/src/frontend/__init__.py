"""Frontend package - converts Python AST to IR."""

from .frontend import Frontend
from .parse import ParseError, parse
from .subset import VerifyResult, Violation, verify


def compile(source: str) -> "Module":
    """Frontend pipeline: source → IR Module. Orchestrates phases 2-9."""
    # Phase 2: Parse to dict-based AST
    ast_dict = parse(source)  # validates syntax

    # Phase 3: Verify subset compliance
    result = verify(ast_dict)
    if not result.ok():
        errors = result.errors()
        if len(errors) > 0:
            first = errors[0]
            raise ParseError(first.message, first.lineno, first.col)

    # Phases 4-9: Use existing Frontend (still uses ast.* internally)
    fe = Frontend()
    return fe.transpile(source)


__all__ = ["Frontend", "compile", "parse", "ParseError", "verify", "VerifyResult", "Violation"]
