#!/usr/bin/env python3
"""Structural fuzzer for differential testing.

Applies semantic transformations to corpus inputs to create structural nesting
patterns that character-level mutation can't generate. Tests Parable against
bash-oracle to find discrepancies.
"""

import argparse
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .common import (
    ORACLE_PATH,
    REPO_ROOT,
    Discrepancy,
    find_test_files,
    normalize,
    parse_layer_spec,
    parse_test_file,
    post_process_discrepancies,
    run_oracle,
    run_parable,
)


@dataclass
class Transform:
    """A structural transformation."""

    name: str
    description: str
    apply: Callable[[str], str | None]


def transform_subshell(s: str) -> str | None:
    """Wrap input in subshell: cmd -> (cmd)"""
    s = s.strip()
    if not s:
        return None
    if s.startswith("(") and not s.startswith("(("):
        return None
    if "<<" in s:
        return None
    return f"({s})"


def transform_cmdsub(s: str) -> str | None:
    """Wrap input in command substitution: cmd -> echo $(cmd)"""
    s = s.strip()
    if not s:
        return None
    if "<<" in s:
        return None
    return f"echo $({s})"


def transform_procsub_in(s: str) -> str | None:
    """Wrap input in process substitution: cmd -> cat <(cmd)"""
    s = s.strip()
    if not s:
        return None
    if "<<" in s or "\n" in s:
        return None
    return f"cat <({s})"


def transform_procsub_out(s: str) -> str | None:
    """Wrap input in output process substitution: cmd -> cmd > >(cat)"""
    s = s.strip()
    if not s:
        return None
    if "<<" in s or "\n" in s:
        return None
    if ">" in s:
        return None
    return f"{s} > >(cat)"


def transform_brace(s: str) -> str | None:
    """Wrap input in brace group: cmd -> { cmd; }"""
    s = s.strip()
    if not s:
        return None
    if s.startswith("{") and s.endswith("}"):
        return None
    if not s.endswith(";") and not s.endswith("\n"):
        s = s + ";"
    return f"{{ {s} }}"


def transform_arith(s: str) -> str | None:
    """Wrap input in arithmetic: cmd -> echo $((cmd)) for simple expressions"""
    s = s.strip()
    if not s:
        return None
    if not s.replace(" ", "").replace("+", "").replace("-", "").replace("*", "").isdigit():
        if not all(c.isalnum() or c in " +-*/%()_" for c in s):
            return None
    if "<<" in s or "\n" in s:
        return None
    return f"echo $(({s}))"


def transform_backtick(s: str) -> str | None:
    """Wrap input in backtick substitution: cmd -> echo `cmd`"""
    s = s.strip()
    if not s:
        return None
    if "<<" in s or "`" in s:
        return None
    return f"echo `{s}`"


def transform_double_subshell(s: str) -> str | None:
    """Double wrap in subshell: cmd -> ( (cmd) )"""
    s = s.strip()
    if not s:
        return None
    if s.startswith("("):
        return None
    if "<<" in s:
        return None
    return f"( ({s}) )"


def transform_cmdsub_in_cmdsub(s: str) -> str | None:
    """Nested command substitution: cmd -> echo $(echo $(cmd))"""
    s = s.strip()
    if not s:
        return None
    if "<<" in s:
        return None
    return f"echo $(echo $({s}))"


def transform_pipeline_prefix(s: str) -> str | None:
    """Prepend to pipeline: cmd -> true | cmd"""
    s = s.strip()
    if not s:
        return None
    if "<<" in s or "\n" in s:
        return None
    return f"true | {s}"


def transform_pipeline_suffix(s: str) -> str | None:
    """Append to pipeline: cmd -> cmd | cat"""
    s = s.strip()
    if not s:
        return None
    if "<<" in s or "\n" in s:
        return None
    return f"{s} | cat"


def transform_and_list(s: str) -> str | None:
    """Wrap in and-list: cmd -> true && cmd"""
    s = s.strip()
    if not s:
        return None
    if "<<" in s or "\n" in s:
        return None
    return f"true && {s}"


def transform_or_list(s: str) -> str | None:
    """Wrap in or-list: cmd -> false || cmd"""
    s = s.strip()
    if not s:
        return None
    if "<<" in s or "\n" in s:
        return None
    return f"false || {s}"


TRANSFORMS = [
    Transform("subshell", "Wrap in subshell: (cmd)", transform_subshell),
    Transform("cmdsub", "Wrap in command substitution: echo $(cmd)", transform_cmdsub),
    Transform("procsub_in", "Wrap in input process substitution: cat <(cmd)", transform_procsub_in),
    Transform(
        "procsub_out", "Wrap in output process substitution: cmd > >(cat)", transform_procsub_out
    ),
    Transform("brace", "Wrap in brace group: { cmd; }", transform_brace),
    Transform("arith", "Wrap in arithmetic: echo $((expr))", transform_arith),
    Transform("backtick", "Wrap in backticks: echo `cmd`", transform_backtick),
    Transform("double_subshell", "Double subshell: ( (cmd) )", transform_double_subshell),
    Transform(
        "cmdsub_nested", "Nested command sub: echo $(echo $(cmd))", transform_cmdsub_in_cmdsub
    ),
    Transform("pipe_prefix", "Prepend to pipeline: true | cmd", transform_pipeline_prefix),
    Transform("pipe_suffix", "Append to pipeline: cmd | cat", transform_pipeline_suffix),
    Transform("and_list", "And-list: true && cmd", transform_and_list),
    Transform("or_list", "Or-list: false || cmd", transform_or_list),
]


def check_discrepancy(original: str, transformed: str, transform_name: str) -> Discrepancy | None:
    """Check if Parable and oracle disagree on transformed input."""
    parable = run_parable(transformed)
    oracle = run_oracle(transformed)
    if parable is None and oracle is None:
        return None
    if (parable is None) != (oracle is None):
        return Discrepancy(
            original=original,
            mutated=transformed,
            mutation_desc=transform_name,
            parable_result=parable if parable else "<error>",
            oracle_result=oracle if oracle else "<error>",
        )
    if normalize(parable) != normalize(oracle):
        return Discrepancy(
            original=original,
            mutated=transformed,
            mutation_desc=transform_name,
            parable_result=parable,
            oracle_result=oracle,
        )
    return None


def main():
    parser = argparse.ArgumentParser(description="Structural fuzzer for Parable")
    parser.add_argument("-o", "--output", type=Path, help="Output file for discrepancies")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--transforms",
        help="Comma-separated list of transforms to run (default: all)",
    )
    parser.add_argument(
        "--both-succeed",
        action="store_true",
        help="Only show cases where both parsers succeed but differ",
    )
    parser.add_argument(
        "--stop-after",
        type=int,
        help="Stop after finding N unique discrepancies",
    )
    parser.add_argument(
        "--list-transforms",
        action="store_true",
        help="List available transforms and exit",
    )
    parser.add_argument(
        "--minimize",
        action="store_true",
        help="Minimize discrepancies before output",
    )
    parser.add_argument(
        "--filter-layer",
        help="Only show discrepancies at or below this layer (implies --minimize)",
    )
    args = parser.parse_args()

    if args.list_transforms:
        print("Available transforms:")
        for t in TRANSFORMS:
            print(f"  {t.name:20} {t.description}")
        sys.exit(0)

    if not ORACLE_PATH.exists():
        print(f"Error: bash-oracle not found at {ORACLE_PATH}", file=sys.stderr)
        sys.exit(1)

    transforms = TRANSFORMS
    if args.transforms:
        names = set(args.transforms.split(","))
        transforms = [t for t in TRANSFORMS if t.name in names]
        if not transforms:
            print(f"Error: no valid transforms in {args.transforms}", file=sys.stderr)
            sys.exit(1)

    tests_dir = REPO_ROOT / "tests"
    test_files = find_test_files(tests_dir)
    inputs = []
    for tf in test_files:
        inputs.extend(parse_test_file(tf))
    print(f"Loaded {len(inputs)} inputs from {len(test_files)} test files")
    print(f"Running {len(transforms)} transforms")

    discrepancies: list[Discrepancy] = []
    seen_signatures: set[str] = set()
    total = len(inputs) * len(transforms)
    checked = 0

    for input_text in inputs:
        for transform in transforms:
            transformed = transform.apply(input_text)
            if transformed is None:
                continue
            checked += 1
            d = check_discrepancy(input_text, transformed, transform.name)
            if d:
                if args.both_succeed:
                    if d.parable_result == "<error>" or d.oracle_result == "<error>":
                        continue
                sig = d.signature()
                if sig in seen_signatures:
                    continue
                seen_signatures.add(sig)
                discrepancies.append(d)
                if args.verbose:
                    print(f"\n[{checked}] DISCREPANCY: {d.mutation_desc}")
                    print(f"  Original: {d.original!r}")
                    print(f"  Mutated:  {d.mutated!r}")
                    print(f"  Parable:  {d.parable_result}")
                    print(f"  Oracle:   {d.oracle_result}")
                if args.stop_after and len(discrepancies) >= args.stop_after:
                    print(f"\nStopped after finding {args.stop_after} discrepancies")
                    break
        if args.stop_after and len(discrepancies) >= args.stop_after:
            break
        if checked % 100 == 0:
            print(
                f"\r{checked}/{total} checked, {len(discrepancies)} unique discrepancies",
                end="",
                flush=True,
            )
    print()

    print(f"\nChecked {checked} transformations")
    print(f"Found {len(discrepancies)} unique discrepancies")

    filter_layer = parse_layer_spec(args.filter_layer) if args.filter_layer else None
    discrepancies = post_process_discrepancies(discrepancies, args.minimize, filter_layer)

    both_ok = [
        d for d in discrepancies if d.parable_result != "<error>" and d.oracle_result != "<error>"
    ]
    parable_err = [
        d for d in discrepancies if d.parable_result == "<error>" and d.oracle_result != "<error>"
    ]
    oracle_err = [
        d for d in discrepancies if d.parable_result != "<error>" and d.oracle_result == "<error>"
    ]
    print(f"  Both succeed, different AST: {len(both_ok)}")
    print(f"  Parable errors, oracle succeeds: {len(parable_err)}")
    print(f"  Parable succeeds, oracle errors: {len(oracle_err)}")

    if discrepancies and args.output:
        with open(args.output, "w") as f:
            for d in discrepancies:
                f.write("=" * 60 + "\n")
                f.write(f"Transform: {d.mutation_desc}\n")
                f.write(f"Original: {d.original!r}\n")
                f.write(f"Mutated:  {d.mutated!r}\n")
                f.write(f"Parable:  {d.parable_result}\n")
                f.write(f"Oracle:   {d.oracle_result}\n")
        print(f"Discrepancies written to {args.output}")

    if both_ok:
        print("\n=== BOTH SUCCEED BUT DIFFER (most interesting) ===")
        for d in both_ok[:5]:
            print()
            print("-" * 40)
            print(f"Transform: {d.mutation_desc}")
            print(f"Original: {d.original!r}")
            print(f"Mutated:  {d.mutated!r}")
            print(f"Parable:  {d.parable_result[:200]}...")
            print(f"Oracle:   {d.oracle_result[:200]}...")

    if parable_err and not args.both_succeed:
        print("\n=== PARABLE ERRORS, ORACLE SUCCEEDS ===")
        for d in parable_err[:3]:
            print()
            print("-" * 40)
            print(f"Transform: {d.mutation_desc}")
            print(f"Original: {d.original!r}")
            print(f"Mutated:  {d.mutated!r}")
            print(f"Oracle:   {d.oracle_result[:200]}...")

    if oracle_err and not args.both_succeed:
        print("\n=== PARABLE SUCCEEDS, ORACLE ERRORS ===")
        for d in oracle_err[:3]:
            print()
            print("-" * 40)
            print(f"Transform: {d.mutation_desc}")
            print(f"Original: {d.original!r}")
            print(f"Mutated:  {d.mutated!r}")
            print(f"Parable:  {d.parable_result[:200]}...")

    sys.exit(1 if discrepancies else 0)


if __name__ == "__main__":
    main()
