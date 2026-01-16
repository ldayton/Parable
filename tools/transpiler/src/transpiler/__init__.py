"""Python to JavaScript transpiler for Parable."""

import sys


def main():
    """Route to transpiler subcommands."""
    args = sys.argv[1:]
    if "--transpile" in args:
        args.remove("--transpile")
        sys.argv = [sys.argv[0]] + args
        from .transpile import main as transpile_main

        transpile_main()
    elif "--check-style" in args:
        args.remove("--check-style")
        sys.argv = [sys.argv[0]] + args
        from .check_style import main as check_main

        check_main()
    else:
        print("Usage: transpiler --transpile <input.py>")
        print("       transpiler --check-style")
        print()
        print("  --transpile    Transpile parable.py to JavaScript")
        print("  --check-style  Check parable.py style constraints")
        sys.exit(1)
