#!/usr/bin/env python3
"""Grammar-based generator fuzzer for differential testing.

Generates bash scripts from scratch using grammar rules, then compares
Parable vs bash-oracle to find discrepancies.
"""

import argparse
import random
import sys
from pathlib import Path

from .common import (
    ORACLE_PATH,
    Discrepancy,
    normalize,
    run_oracle,
    run_parable,
)


def generate() -> str:
    """Generate a random bash script. Trivial implementation for now."""
    templates = [
        "echo hello",
        "echo $var",
        "echo ${var}",
        "echo $(pwd)",
        "cat file",
        "true && false",
        "true || false",
        "cmd1 | cmd2",
        "{ echo x; }",
        "(echo y)",
    ]
    return random.choice(templates)


def check_discrepancy(generated: str) -> Discrepancy | None:
    """Check if Parable and oracle disagree on generated input."""
    parable = run_parable(generated)
    oracle = run_oracle(generated)
    if parable is None and oracle is None:
        return None
    if (parable is None) != (oracle is None):
        return Discrepancy(
            original="<generated>",
            mutated=generated,
            mutation_desc="generator",
            parable_result=parable if parable else "<error>",
            oracle_result=oracle if oracle else "<error>",
        )
    if normalize(parable) != normalize(oracle):
        return Discrepancy(
            original="<generated>",
            mutated=generated,
            mutation_desc="generator",
            parable_result=parable,
            oracle_result=oracle,
        )
    return None


def main():
    parser = argparse.ArgumentParser(description="Grammar-based generator fuzzer")
    parser.add_argument("-n", "--iterations", type=int, default=1000)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("-s", "--seed", type=int)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--both-succeed", action="store_true")
    parser.add_argument("--stop-after", type=int)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    if not ORACLE_PATH.exists():
        print(f"Error: bash-oracle not found at {ORACLE_PATH}", file=sys.stderr)
        sys.exit(1)

    discrepancies: list[Discrepancy] = []
    seen_signatures: set[str] = set()

    for i in range(args.iterations):
        generated = generate()
        d = check_discrepancy(generated)
        if d:
            if args.both_succeed and (
                d.parable_result == "<error>" or d.oracle_result == "<error>"
            ):
                continue
            sig = d.signature()
            if sig in seen_signatures:
                continue
            seen_signatures.add(sig)
            discrepancies.append(d)
            if args.verbose:
                print(f"\n[{i + 1}] DISCREPANCY")
                print(f"  Generated: {d.mutated!r}")
                print(f"  Parable:   {d.parable_result}")
                print(f"  Oracle:    {d.oracle_result}")
            if args.stop_after and len(discrepancies) >= args.stop_after:
                break
        if (i + 1) % 100 == 0:
            print(
                f"\r{i + 1}/{args.iterations}, {len(discrepancies)} discrepancies",
                end="",
                flush=True,
            )

    print()
    print(f"Found {len(discrepancies)} unique discrepancies in {args.iterations} iterations")
    sys.exit(1 if discrepancies else 0)


if __name__ == "__main__":
    main()
