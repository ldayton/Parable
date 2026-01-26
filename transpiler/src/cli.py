"""Command-line interface."""

from __future__ import annotations

import sys
from pathlib import Path

from .frontend import Frontend
from .backend.go import GoBackend


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m src.cli <input.py>", file=sys.stderr)
        sys.exit(1)
    source = Path(sys.argv[1]).read_text()
    fe = Frontend()
    module = fe.transpile(source)
    be = GoBackend()
    code = be.emit(module)
    print(code)


if __name__ == "__main__":
    main()
