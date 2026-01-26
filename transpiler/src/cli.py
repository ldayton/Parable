"""Command-line interface."""

from __future__ import annotations

import argparse
from pathlib import Path

from .frontend import Frontend
from .middleend import analyze
from .backend.c import CBackend
from .backend.csharp import CSharpBackend
from .backend.go import GoBackend
from .backend.java import JavaBackend
from .backend.python import PythonBackend
from .backend.ruby import RubyBackend
from .backend.rust import RustBackend
from .backend.swift import SwiftBackend
from .backend.typescript import TsBackend
from .backend.zig import ZigBackend


BACKENDS = {
    "c": CBackend,
    "csharp": CSharpBackend,
    "go": GoBackend,
    "java": JavaBackend,
    "python": PythonBackend,
    "ruby": RubyBackend,
    "rust": RustBackend,
    "swift": SwiftBackend,
    "ts": TsBackend,
    "zig": ZigBackend,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Transpile Python to other languages")
    parser.add_argument("input", help="Input Python file")
    parser.add_argument(
        "-b", "--backend", choices=BACKENDS.keys(), default="go", help="Target backend"
    )
    args = parser.parse_args()

    source = Path(args.input).read_text()
    fe = Frontend()
    module = fe.transpile(source)
    analyze(module)
    be = BACKENDS[args.backend]()
    code = be.emit(module)
    print(code)


if __name__ == "__main__":
    main()
