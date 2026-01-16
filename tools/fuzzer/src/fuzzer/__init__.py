"""Parable fuzzers for differential testing against bash-oracle."""

import sys


def main():
    """Route to structural or character fuzzer based on flags."""
    args = sys.argv[1:]
    if "--structural" in args:
        args.remove("--structural")
        sys.argv = [sys.argv[0]] + args
        from .structural import main as structural_main

        structural_main()
    elif "--character" in args:
        args.remove("--character")
        sys.argv = [sys.argv[0]] + args
        from .character import main as character_main

        character_main()
    elif "--generator" in args:
        args.remove("--generator")
        sys.argv = [sys.argv[0]] + args
        from .generator import main as generator_main

        generator_main()
    else:
        print("Usage: fuzzer --structural [options]")
        print("       fuzzer --character [options]")
        print("       fuzzer --generator [options]")
        print()
        print("  --structural  Structural fuzzer: wraps inputs in $(), <(), etc.")
        print("  --character   Character mutation fuzzer: random char mutations")
        print("  --generator   Generator fuzzer: generates scripts from scratch")
        print()
        print("Run with -h after mode flag for mode-specific options.")
        sys.exit(1)
