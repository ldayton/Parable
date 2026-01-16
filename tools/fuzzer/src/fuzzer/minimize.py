"""Delta debugging minimizer for Parable discrepancies."""

import argparse
import sys

from .common import normalize, run_oracle, run_parable

_verbose = False


def ddmin(chars: list[str], test_fn) -> list[str]:
    """Delta debugging algorithm - find 1-minimal failing input."""
    n = 2
    tests = 0
    while len(chars) >= 2:
        chunk_size = max(len(chars) // n, 1)
        reduced = False
        for i in range(n):
            start = i * chunk_size
            end = min(start + chunk_size, len(chars))
            candidate = chars[:start] + chars[end:]
            if not candidate:
                continue
            tests += 1
            if _verbose:
                print(f"  [{tests}] {len(chars)} -> {len(candidate)} chars", file=sys.stderr)
            if test_fn(candidate):
                chars = candidate
                n = max(n - 1, 2)
                reduced = True
                break
        if not reduced:
            if n >= len(chars):
                break
            n = min(n * 2, len(chars))
    if _verbose:
        print(f"  Done after {tests} tests", file=sys.stderr)
    return chars


def is_interesting(input_text: str) -> bool:
    """Check if input shows a discrepancy between Parable and oracle."""
    parable = run_parable(input_text)
    oracle = run_oracle(input_text)
    # Both must succeed and produce different results
    if parable is None or oracle is None:
        return False
    return normalize(parable) != normalize(oracle)


def minimize(input_text: str) -> str | None:
    """Minimize input to smallest string that still shows discrepancy."""
    if not is_interesting(input_text):
        return None
    chars = ddmin(list(input_text), lambda c: is_interesting("".join(c)))
    return "".join(chars)


def main():
    global _verbose
    parser = argparse.ArgumentParser(description="Minimize a failing input to its MRE")
    parser.add_argument("input", help="The bash code that triggers a discrepancy")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show progress")
    args = parser.parse_args()
    _verbose = args.verbose

    if _verbose:
        print(f"Input ({len(args.input)} chars): {args.input!r}", file=sys.stderr)

    result = minimize(args.input)
    if result is None:
        print("Error: input does not reproduce a discrepancy", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"MRE ({len(result)} chars): {result!r}", file=sys.stderr)

    print(result)
