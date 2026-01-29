"""Subset-compliant entry point - reads from stdin, writes to stdout."""

from __future__ import annotations

import sys

from .frontend import Frontend
from .frontend.parse import parse
from .frontend.subset import verify as verify_subset
from .frontend.names import resolve_names
from .middleend import analyze
from .backend.go import GoBackend
from .backend.java import JavaBackend
from .backend.python import PythonBackend
from .backend.typescript import TsBackend

BACKENDS: dict[str, type[GoBackend] | type[JavaBackend] | type[PythonBackend] | type[TsBackend]] = {
    "go": GoBackend,
    "java": JavaBackend,
    "py": PythonBackend,
    "ts": TsBackend,
}

USAGE: str = """\
tongues [OPTIONS] < input.py > output.go

Options:
  --target TARGET   Output language: go, java, py, ts (default: go)
  --verify [PATH]   Check subset compliance only, no codegen
                    PATH can be a file or directory (reads stdin if omitted)
  --help            Show this help message
"""


def run_verify_stdin() -> int:
    """Verify source from stdin. Returns exit code."""
    source = sys.stdin.read()
    ast_dict = parse(source)
    result = verify_subset(ast_dict)
    errors = result.errors()
    if len(errors) > 0:
        i = 0
        while i < len(errors):
            e = errors[i]
            print(str(e), file=sys.stderr)
            i += 1
        return 1
    name_result = resolve_names(ast_dict)
    errors = name_result.errors()
    if len(errors) > 0:
        i = 0
        while i < len(errors):
            e = errors[i]
            print(str(e), file=sys.stderr)
            i += 1
        return 1
    return 0


def run_transpile(target: str) -> int:
    """Transpile source from stdin to target language. Returns exit code."""
    source = sys.stdin.read()
    fe = Frontend()
    module = fe.transpile(source)
    analyze(module)
    backend_cls = BACKENDS.get(target)
    if backend_cls is None:
        print("error: unknown target: " + target, file=sys.stderr)
        return 1
    be = backend_cls()
    code = be.emit(module)
    print(code)
    return 0


def parse_args() -> tuple[str, bool, str | None]:
    """Parse command-line arguments.

    Returns:
        (target, verify_mode, verify_path) where verify_path is None for stdin mode
    """
    args = sys.argv[1:]
    target = "go"
    verify = False
    verify_path: str | None = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--help" or arg == "-h":
            print(USAGE, end="")
            sys.exit(0)
        elif arg == "--target":
            if i + 1 >= len(args):
                print("error: --target requires an argument", file=sys.stderr)
                sys.exit(1)
            target = args[i + 1]
            i += 2
        elif arg == "--verify":
            verify = True
            i += 1
            if i < len(args) and not args[i].startswith("-"):
                verify_path = args[i]
                i += 1
        else:
            print("error: unknown option: " + arg, file=sys.stderr)
            sys.exit(1)
    if target == "python":
        target = "py"
    if target == "typescript":
        target = "ts"
    if target in ("rust", "c"):
        print("error: backend '" + target + "' is not yet implemented", file=sys.stderr)
        sys.exit(1)
    if target not in BACKENDS:
        print("error: unknown target: " + target, file=sys.stderr)
        sys.exit(1)
    return (target, verify, verify_path)


def main() -> int:
    """Main entry point for stdin-only mode."""
    target, verify, verify_path = parse_args()
    if verify:
        if verify_path is not None:
            print("error: --verify PATH requires cli.py (file I/O not in subset)", file=sys.stderr)
            return 1
        return run_verify_stdin()
    return run_transpile(target)


if __name__ == "__main__":
    sys.exit(main())
