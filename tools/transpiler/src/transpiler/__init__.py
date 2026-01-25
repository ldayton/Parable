"""Python to JavaScript/Go transpiler for Parable."""

import sys


def main():
    """Route to transpiler subcommands."""
    args = sys.argv[1:]
    if "--transpile-go" in args:
        args.remove("--transpile-go")
        sys.argv = [sys.argv[0]] + args
        from .transpile_go import main as transpile_go_main

        transpile_go_main()
    elif "--transpile-js" in args:
        args.remove("--transpile-js")
        sys.argv = [sys.argv[0]] + args
        from .transpile_js import main as transpile_js_main

        transpile_js_main()
    elif "--transpile-dts" in args:
        args.remove("--transpile-dts")
        sys.argv = [sys.argv[0]] + args
        from .transpile_dts import main as transpile_dts_main

        transpile_dts_main()
    elif "--check-style" in args:
        args.remove("--check-style")
        sys.argv = [sys.argv[0]] + args
        from .check_style import main as check_main

        check_main()
    else:
        print("Usage: transpiler --transpile-js <input.py>")
        print("       transpiler --transpile-go <input.py>")
        print("       transpiler --transpile-dts <parable.js>")
        print("       transpiler --check-style")
        print()
        print("  --transpile-js   Transpile parable.py to JavaScript")
        print("  --transpile-go   Transpile parable.py to Go")
        print("  --transpile-dts  Generate TypeScript definitions from parable.js")
        print("  --check-style    Check parable.py style constraints")
        sys.exit(1)
