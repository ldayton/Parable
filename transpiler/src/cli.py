"""Command-line interface."""

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

BACKENDS = {
    "go": GoBackend,
    "java": JavaBackend,
    "py": PythonBackend,
    "ts": TsBackend,
}

USAGE = """\
tongues [OPTIONS] < input.py > output.go

Options:
  --target TARGET   Output language: go, java, py, ts (default: go)
  --verify          Check subset compliance only, no codegen
  --help            Show this help message
"""


def main() -> int:
    args = sys.argv[1:]
    target = "go"
    verify = False
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--help" or arg == "-h":
            print(USAGE, end="")
            return 0
        elif arg == "--target":
            if i + 1 >= len(args):
                print("error: --target requires an argument", file=sys.stderr)
                return 1
            target = args[i + 1]
            i += 2
        elif arg == "--verify":
            verify = True
            i += 1
        else:
            print("error: unknown option: " + arg, file=sys.stderr)
            return 1
    # Normalize aliases
    if target == "python":
        target = "py"
    if target == "typescript":
        target = "ts"
    # Validate target
    if target in ("rust", "c"):
        print("error: backend '" + target + "' is not yet implemented", file=sys.stderr)
        return 1
    if target not in BACKENDS:
        print("error: unknown target: " + target, file=sys.stderr)
        return 1
    source = sys.stdin.read()
    if verify:
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
    fe = Frontend()
    module = fe.transpile(source)
    analyze(module)
    be = BACKENDS[target]()
    code = be.emit(module)
    print(code)
    return 0


if __name__ == "__main__":
    sys.exit(main())
