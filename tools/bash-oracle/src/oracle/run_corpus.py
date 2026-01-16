#!/usr/bin/env python3
"""Run Parable against the bigtable-bash corpus and report failures."""

import argparse
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

# Add src to path for parable import
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARABLE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR))))
sys.path.insert(0, os.path.join(PARABLE_ROOT, "src"))

from parable import ParseError, parse  # noqa: E402

CORPUS_DIR = os.path.expanduser("~/source/bigtable-bash/tests")
TOOL_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # tools/bash-oracle
FAILURES_FILE = os.path.join(TOOL_DIR, "failures.txt")


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
            while i < n and lines[i] != "c209da5127ac3b3fe0ac82c29cbe77df":
                input_lines.append(lines[i])
                i += 1
            if i < n and lines[i] == "c209da5127ac3b3fe0ac82c29cbe77df":
                i += 1
            expected_lines = []
            while (
                i < n
                and lines[i] != "c209da5127ac3b3fe0ac82c29cbe77df"
                and not lines[i].startswith("=== ")
            ):
                expected_lines.append(lines[i])
                i += 1
            if i < n and lines[i] == "c209da5127ac3b3fe0ac82c29cbe77df":
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
    if test_expected == "<error>":
        try:
            nodes = parse(test_input)
            actual = " ".join(node.to_sexp() for node in nodes)
            return (False, actual)  # Expected error but got parse
        except ParseError:
            return (True, "<error>")
        except Exception:
            return (True, "<error>")

    try:
        nodes = parse(test_input)
        actual = " ".join(node.to_sexp() for node in nodes)
    except ParseError as e:
        return (False, f"<error>: {e}")
    except Exception as e:
        return (False, f"!exception: {e}")

    if normalize(actual) == normalize(test_expected):
        return (True, actual)
    return (False, actual)


def process_file(test_file):
    """Process a single test file. Returns dict with counts and failures."""
    tests = parse_test_file(test_file)
    passed = failed = total = 0
    failures = []
    for _name, test_input, test_expected in tests:
        total += 1
        ok, _actual = run_test(test_input, test_expected)
        if ok:
            passed += 1
        else:
            failed += 1
            failures.append(test_file)
    return {"passed": passed, "failed": failed, "total": total, "failures": failures}


def main():
    parser = argparse.ArgumentParser(description="Run Parable against bigtable-bash corpus")
    parser.add_argument(
        "--max-failures",
        type=int,
        help="Stop after N failures (default: run to completion)",
    )
    args = parser.parse_args()
    max_failures = args.max_failures if args.max_failures is not None else sys.maxsize

    if not os.path.isdir(CORPUS_DIR):
        print(f"Error: corpus not found at {CORPUS_DIR}", file=sys.stderr)
        sys.exit(1)
    test_files = sorted(
        os.path.join(CORPUS_DIR, f) for f in os.listdir(CORPUS_DIR) if f.endswith(".tests")
    )
    total_files = len(test_files)
    passed = failed = total = 0
    all_failures = []
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = {executor.submit(process_file, f): f for f in test_files}
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            passed += result["passed"]
            failed += result["failed"]
            total += result["total"]
            all_failures.extend(result["failures"])
            print(f"\r{i + 1}/{total_files} files ({failed} failures)", end="", flush=True)
            if failed >= max_failures:
                executor.shutdown(cancel_futures=True)
                break
    print()
    with open(FAILURES_FILE, "w") as f:
        for failure in all_failures[:max_failures]:
            f.write(failure + "\n")
    if failed:
        print(f"Failures written to {FAILURES_FILE}")
    print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
