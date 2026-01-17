"""Delta debugging minimizer for Parable discrepancies."""

import argparse
import sys

from .common import normalize, run_oracle, run_parable

_verbose = False
_deadline = None


class TimeoutError(Exception):
    pass


def _check_timeout():
    """Raise TimeoutError if deadline exceeded."""
    import time

    if _deadline and time.time() > _deadline:
        raise TimeoutError("timeout")


def ddmin(chars: list[str], test_fn) -> list[str]:
    """Delta debugging algorithm - find 1-minimal failing input."""
    n = 2
    tests = 0
    while len(chars) >= 2:
        _check_timeout()
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
    import time

    global _verbose, _deadline
    parser = argparse.ArgumentParser(description="Minimize a failing input to its MRE")
    parser.add_argument(
        "input", nargs="?", help="The bash code (or - for stdin, or @file to read from file)"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Show progress")
    parser.add_argument(
        "-t", "--timeout", type=int, default=10, help="Timeout in seconds (default: 10)"
    )
    args = parser.parse_args()
    _verbose = args.verbose
    _deadline = time.time() + args.timeout

    # Get input from argument, file, or stdin
    if args.input is None or args.input == "-":
        input_text = sys.stdin.read()
    elif args.input.startswith("@"):
        with open(args.input[1:]) as f:
            input_text = f.read()
    else:
        input_text = args.input

    if _verbose:
        print(f"Input ({len(input_text)} chars): {input_text!r}", file=sys.stderr)

    try:
        result = minimize(input_text)
    except TimeoutError:
        print(f"Error: timeout after {args.timeout}s", file=sys.stderr)
        sys.exit(2)

    if result is None:
        print("Error: input does not reproduce a discrepancy", file=sys.stderr)
        sys.exit(1)

    if _verbose:
        print(f"MRE ({len(result)} chars): {result!r}", file=sys.stderr)

    print(result)


if __name__ == "__main__":
    main()
