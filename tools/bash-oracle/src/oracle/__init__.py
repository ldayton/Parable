"""Bash oracle utilities for Parable."""

import sys


def main():
    """Route to oracle subcommands."""
    args = sys.argv[1:]
    if "--verify-tests" in args:
        args.remove("--verify-tests")
        sys.argv = [sys.argv[0]] + args
        from .verify_tests import main as verify_main

        verify_main()
    elif "--run-corpus" in args:
        args.remove("--run-corpus")
        sys.argv = [sys.argv[0]] + args
        from .run_corpus import main as corpus_main

        corpus_main()
    elif "--convert-gnu-bash" in args:
        args.remove("--convert-gnu-bash")
        sys.argv = [sys.argv[0]] + args
        from .convert_gnu_bash import main as gnu_main

        gnu_main()
    elif "--convert-oils" in args:
        args.remove("--convert-oils")
        sys.argv = [sys.argv[0]] + args
        from .convert_oils import main as oils_main

        oils_main()
    elif "--convert-tree-sitter" in args:
        args.remove("--convert-tree-sitter")
        sys.argv = [sys.argv[0]] + args
        from .convert_tree_sitter import main as ts_main

        ts_main()
    else:
        print("Usage: oracle --verify-tests [options]")
        print("       oracle --run-corpus [options]")
        print("       oracle --convert-gnu-bash [options]")
        print("       oracle --convert-oils [options]")
        print("       oracle --convert-tree-sitter [options]")
        print()
        print("  --verify-tests       Verify test expectations against bash-oracle")
        print("  --run-corpus         Run Parable against bigtable-bash corpus")
        print("  --convert-gnu-bash   Convert GNU Bash test corpus")
        print("  --convert-oils       Convert Oils test corpus")
        print("  --convert-tree-sitter Convert tree-sitter-bash corpus")
        print()
        print("Run with -h after subcommand for options.")
        sys.exit(1)
