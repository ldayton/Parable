"""Frontend package - converts Python AST to IR."""

from .frontend import Frontend
from .names import NameInfo, NameResult, NameTable, resolve_names
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

    # Phase 4: Resolve names
    name_result = resolve_names(ast_dict)
    if not name_result.ok():
        errors = name_result.errors()
        if len(errors) > 0:
            first = errors[0]
            raise ParseError(first.message, first.lineno, first.col)

    # Phases 5-9: Use existing Frontend with dict AST
    fe = Frontend()
    return fe.transpile(source, ast_dict, name_result=name_result)


__all__ = [
    "Frontend",
    "NameInfo",
    "NameResult",
    "NameTable",
    "ParseError",
    "VerifyResult",
    "Violation",
    "compile",
    "parse",
    "resolve_names",
    "verify",
]
