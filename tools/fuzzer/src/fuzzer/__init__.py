"""Parable fuzzers for differential testing against bash-oracle."""

import argparse
import sys
from pathlib import Path

MAIN_DESC = """\
Differential fuzzers for testing Parable against bash-oracle.

Parable is a bash parser; bash-oracle is a patched GNU Bash that outputs its
internal AST. These fuzzers find inputs where the two disagree, revealing
parsing bugs. Three fuzzing strategies are available, plus a minimizer for
reducing failing inputs to their minimal reproducing example.
"""

CHAR_DESC = """\
Mutate inputs from the test corpus with random character changes.

Loads all .tests files from tests/, applies random insertions, deletions, and
substitutions of shell-significant characters ($, {, (, |, etc.), then checks
if Parable and bash-oracle produce different ASTs. Good for finding edge cases
around existing test coverage, but limited in creating novel structural nesting.
"""

STRUCT_DESC = """\
Apply structural transformations to corpus inputs.

Wraps each input in constructs like $(), <(), { }, (( )), etc. to create
nesting patterns that character mutation can't generate. Deterministic: runs
each transform on every corpus input exactly once. Effective at finding bugs
in nested construct handling.
"""

GEN_DESC = """\
Generate bash scripts from scratch using grammar rules.

Builds random scripts by following bash grammar productions with configurable
probability weights (Csmith-style). Supports layered complexity: start with
simple words and expansions, then incrementally enable commands, pipelines,
control flow, and functions. Useful for exploring grammar corners that don't
appear in the test corpus.
"""

MIN_DESC = """\
Reduce a failing input to its minimal reproducing example.

Uses delta debugging to iteratively remove characters while preserving the
discrepancy between Parable and bash-oracle. The result is typically much
smaller and easier to debug than the original failing input.
"""


def main():
    """Unified entry point for all fuzzer modes."""
    parser = argparse.ArgumentParser(
        description=MAIN_DESC,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="mode", required=True, metavar="MODE")

    # Common arguments for fuzzing modes
    def add_common_args(p, has_iterations=True):
        if has_iterations:
            p.add_argument(
                "-n",
                "--iterations",
                type=int,
                default=1000,
                help="number of iterations (default: 1000)",
            )
        p.add_argument(
            "-o", "--output", type=Path, metavar="FILE", help="output file for discrepancies"
        )
        p.add_argument("-v", "--verbose", action="store_true", help="verbose output")
        p.add_argument(
            "--both-succeed",
            action="store_true",
            help="only show cases where both parsers succeed but differ",
        )
        p.add_argument(
            "--stop-after", type=int, metavar="N", help="stop after finding N unique discrepancies"
        )
        p.add_argument(
            "--minimize", action="store_true", help="minimize discrepancies before output"
        )
        p.add_argument(
            "--filter-layer",
            metavar="SPEC",
            help="only show discrepancies at or below this layer (implies --minimize)",
        )

    # Character mode
    char_parser = subparsers.add_parser(
        "character",
        aliases=["char"],
        help="character mutation fuzzer",
        description=CHAR_DESC,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_common_args(char_parser)
    char_parser.add_argument(
        "-m", "--mutations", type=int, default=2, help="mutations per input (default: 2)"
    )
    char_parser.add_argument("-s", "--seed", type=int, help="random seed")

    # Structural mode
    struct_parser = subparsers.add_parser(
        "structural",
        aliases=["struct"],
        help="structural transformation fuzzer",
        description=STRUCT_DESC,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_common_args(struct_parser, has_iterations=False)
    struct_parser.add_argument(
        "--transforms", metavar="LIST", help="comma-separated transforms (default: all)"
    )
    struct_parser.add_argument(
        "--list-transforms", action="store_true", help="list available transforms and exit"
    )

    # Generator mode
    gen_parser = subparsers.add_parser(
        "generator",
        aliases=["gen"],
        help="grammar-based generator fuzzer",
        description=GEN_DESC,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_common_args(gen_parser)
    gen_parser.add_argument("-s", "--seed", type=int, help="random seed")
    gen_parser.add_argument(
        "--layer",
        default="full",
        metavar="SPEC",
        help="layer spec: 0-12, range (0-5), or preset (words, commands, full)",
    )
    gen_parser.add_argument(
        "--max-depth", type=int, default=5, help="max recursion depth (default: 5)"
    )
    gen_parser.add_argument(
        "--list-layers", action="store_true", help="list available layers and exit"
    )
    gen_parser.add_argument(
        "--dry-run", type=int, metavar="N", help="generate N samples without testing"
    )

    # Minimize mode
    min_parser = subparsers.add_parser(
        "minimize",
        aliases=["min"],
        help="minimize a discrepancy to its MRE",
        description=MIN_DESC,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    min_parser.add_argument("input", nargs="?", help="bash code, @file, or - for stdin")
    min_parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    min_parser.add_argument(
        "-t", "--timeout", type=int, default=10, help="timeout in seconds (default: 10)"
    )

    args = parser.parse_args()

    # Route to appropriate module
    if args.mode in ("character", "char"):
        _run_character(args)
    elif args.mode in ("structural", "struct"):
        _run_structural(args)
    elif args.mode in ("generator", "gen"):
        _run_generator(args)
    elif args.mode in ("minimize", "min"):
        _run_minimize(args)


def _run_character(args):
    from .character import main as char_main

    # Rebuild sys.argv for the submodule
    argv = ["fuzzer"]
    if args.iterations != 1000:
        argv += ["-n", str(args.iterations)]
    if args.mutations != 2:
        argv += ["-m", str(args.mutations)]
    if args.output:
        argv += ["-o", str(args.output)]
    if args.seed is not None:
        argv += ["-s", str(args.seed)]
    if args.verbose:
        argv += ["-v"]
    if args.both_succeed:
        argv += ["--both-succeed"]
    if args.stop_after:
        argv += ["--stop-after", str(args.stop_after)]
    if args.minimize:
        argv += ["--minimize"]
    if args.filter_layer:
        argv += ["--filter-layer", args.filter_layer]
    sys.argv = argv
    char_main()


def _run_structural(args):
    from .structural import main as struct_main

    argv = ["fuzzer"]
    if args.output:
        argv += ["-o", str(args.output)]
    if args.verbose:
        argv += ["-v"]
    if args.transforms:
        argv += ["--transforms", args.transforms]
    if args.both_succeed:
        argv += ["--both-succeed"]
    if args.stop_after:
        argv += ["--stop-after", str(args.stop_after)]
    if args.list_transforms:
        argv += ["--list-transforms"]
    if args.minimize:
        argv += ["--minimize"]
    if args.filter_layer:
        argv += ["--filter-layer", args.filter_layer]
    sys.argv = argv
    struct_main()


def _run_generator(args):
    from .generator import main as gen_main

    argv = ["fuzzer"]
    if args.iterations != 1000:
        argv += ["-n", str(args.iterations)]
    if args.output:
        argv += ["-o", str(args.output)]
    if args.seed is not None:
        argv += ["-s", str(args.seed)]
    if args.verbose:
        argv += ["-v"]
    if args.both_succeed:
        argv += ["--both-succeed"]
    if args.stop_after:
        argv += ["--stop-after", str(args.stop_after)]
    if args.layer != "full":
        argv += ["--layer", args.layer]
    if args.max_depth != 5:
        argv += ["--max-depth", str(args.max_depth)]
    if args.list_layers:
        argv += ["--list-layers"]
    if args.dry_run:
        argv += ["--dry-run", str(args.dry_run)]
    if args.minimize:
        argv += ["--minimize"]
    if args.filter_layer:
        argv += ["--filter-layer", args.filter_layer]
    sys.argv = argv
    gen_main()


def _run_minimize(args):
    from .minimize import main as min_main

    argv = ["minimizer"]
    if args.verbose:
        argv += ["-v"]
    if args.timeout != 10:
        argv += ["-t", str(args.timeout)]
    if args.input:
        argv += [args.input]
    sys.argv = argv
    min_main()
