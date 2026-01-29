"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .frontend import Frontend
from .middleend import analyze
from .backend.go import GoBackend
from .backend.java import JavaBackend
from .backend.python import PythonBackend
from .backend.typescript import TsBackend


BACKENDS = {
    "go": GoBackend,
    "java": JavaBackend,
    "python": PythonBackend,
    "ts": TsBackend,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Transpile Python to other languages")
    parser.add_argument("input", nargs="?", help="Input Python file")
    parser.add_argument(
        "-b", "--backend", choices=BACKENDS.keys(), default="go", help="Target backend"
    )
    parser.add_argument(
        "--check-style", metavar="DIR", help="Check style constraints on Python files in DIR"
    )
    args = parser.parse_args()

    if args.check_style:
        from .check_style import find_python_files, check_file

        src_dir = args.check_style
        if not Path(src_dir).is_dir():
            print("Directory not found: " + src_dir)
            sys.exit(1)
        files = find_python_files(src_dir)
        if not files:
            print("No Python files found in: " + src_dir)
            sys.exit(1)
        all_errors = []
        for filepath in files:
            try:
                errors = check_file(filepath)
                for lineno, description in errors:
                    all_errors.append((filepath, lineno, description))
            except SyntaxError as e:
                print("Syntax error in " + filepath + ": " + str(e))
                sys.exit(1)
        if not all_errors:
            sys.exit(0)
        print("Found " + str(len(all_errors)) + " banned construction(s):")
        for filepath, lineno, description in sorted(all_errors):
            print("  " + filepath + ":" + str(lineno) + ": " + description)
        sys.exit(1)

    if not args.input:
        parser.error("input is required for transpilation")

    source = Path(args.input).read_text()
    fe = Frontend()
    module = fe.transpile(source)
    analyze(module)
    be = BACKENDS[args.backend]()
    code = be.emit(module)
    print(code)


if __name__ == "__main__":
    main()
