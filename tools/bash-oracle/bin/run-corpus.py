#!/usr/bin/env python3
"""Run Parable against the bigtable-bash corpus and report failures."""

import os
import sys

# Add src to path for parable import
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARABLE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
sys.path.insert(0, os.path.join(PARABLE_ROOT, "src"))

from parable import ParseError, parse

CORPUS_DIR = os.path.expanduser("~/source/bigtable-bash/tests")
MAX_FAILURES = 100


def parse_test_file(filepath):
    """Parse a .tests file. Returns list of (name, input, expected) tuples."""
    tests = []
    with open(filepath) as f:
        lines = f.read().split("\n")
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.startswith("=== "):
            name = line[4:].strip()
            i += 1
            input_lines = []
            while i < n and lines[i] != "---":
                input_lines.append(lines[i])
                i += 1
            if i < n and lines[i] == "---":
                i += 1
            expected_lines = []
            while i < n and lines[i] != "---" and not lines[i].startswith("=== "):
                expected_lines.append(lines[i])
                i += 1
            if i < n and lines[i] == "---":
                i += 1
            while expected_lines and expected_lines[-1].strip() == "":
                expected_lines.pop()
            tests.append((name, "\n".join(input_lines), "\n".join(expected_lines)))
        else:
            i += 1
    return tests


def normalize(s):
    """Normalize whitespace for comparison."""
    return " ".join(s.split())


def run_test(test_input, test_expected):
    """Run a single test. Returns (passed, actual)."""
    if test_expected == "!error":
        try:
            nodes = parse(test_input)
            actual = " ".join(node.to_sexp() for node in nodes)
            return (False, actual)  # Expected error but got parse
        except ParseError:
            return (True, "!error")
        except Exception:
            return (True, "!error")

    try:
        nodes = parse(test_input)
        actual = " ".join(node.to_sexp() for node in nodes)
    except ParseError as e:
        return (False, f"!error: {e}")
    except Exception as e:
        return (False, f"!exception: {e}")

    if normalize(actual) == normalize(test_expected):
        return (True, actual)
    return (False, actual)


def main():
    if not os.path.isdir(CORPUS_DIR):
        print(f"Error: corpus not found at {CORPUS_DIR}", file=sys.stderr)
        sys.exit(1)

    test_files = sorted(
        os.path.join(CORPUS_DIR, f)
        for f in os.listdir(CORPUS_DIR)
        if f.endswith(".tests")
    )

    total = 0
    passed = 0
    failed = 0
    failures = []

    for test_file in test_files:
        tests = parse_test_file(test_file)
        for name, test_input, test_expected in tests:
            total += 1
            ok, actual = run_test(test_input, test_expected)
            if ok:
                passed += 1
            else:
                failed += 1
                failures.append({
                    "file": os.path.basename(test_file),
                    "name": name,
                    "input": test_input,
                    "expected": test_expected,
                    "actual": actual,
                })
                if len(failures) >= MAX_FAILURES:
                    break
        if len(failures) >= MAX_FAILURES:
            break

    # Print failures
    for i, f in enumerate(failures, 1):
        print(f"{'=' * 60}")
        print(f"FAIL {i}: {f['file']} - {f['name']}")
        print(f"{'=' * 60}")
        print(f"Input:\n{f['input']}")
        print(f"\nExpected:\n{f['expected']}")
        print(f"\nActual:\n{f['actual']}")
        print()

    # Summary
    print(f"{'=' * 60}")
    print(f"Tested: {total} | Passed: {passed} | Failed: {failed}")
    if len(failures) >= MAX_FAILURES:
        print(f"(stopped after {MAX_FAILURES} failures)")
    print(f"{'=' * 60}")

    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
