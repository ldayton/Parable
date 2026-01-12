#!/usr/bin/env python3
"""Simple test runner. No dependencies beyond parable itself."""

import os
import sys
import time


def find_test_files(directory):
    """Find all .tests files recursively. Returns list of paths."""
    result = []
    for root, _dirs, files in os.walk(directory):
        for f in files:
            if f.endswith(".tests"):
                result.append(os.path.join(root, f))
    result.sort()
    return result


def parse_test_file(filepath):
    """Parse a .tests file. Returns list of (name, input, expected, line_num) tuples."""
    tests = []
    with open(filepath) as f:
        lines = f.read().split("\n")
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        # Skip comments and blank lines
        if line.startswith("#") or line.strip() == "":
            i = i + 1
            continue
        # Test header
        if line.startswith("=== "):
            name = line[4:].strip()
            start_line = i + 1
            i = i + 1
            # Collect input until ---
            input_lines = []
            while i < n and lines[i] != "---":
                input_lines.append(lines[i])
                i = i + 1
            # Skip ---
            if i < n and lines[i] == "---":
                i = i + 1
            # Collect expected until ---, next test, or EOF
            expected_lines = []
            while i < n and lines[i] != "---" and not lines[i].startswith("=== "):
                expected_lines.append(lines[i])
                i = i + 1
            # Skip --- end marker
            if i < n and lines[i] == "---":
                i = i + 1
            # Strip trailing blank lines from expected
            while len(expected_lines) > 0 and expected_lines[-1].strip() == "":
                expected_lines.pop()
            test_input = "\n".join(input_lines)
            test_expected = "\n".join(expected_lines)
            tests.append((name, test_input, test_expected, start_line))
        else:
            i = i + 1
    return tests


def normalize(s):
    """Normalize whitespace for comparison."""
    return " ".join(s.split())


def run_test(test_input, test_expected):
    """Run a single test. Returns (passed, actual, error_msg)."""
    from parable import ParseError, parse

    try:
        nodes = parse(test_input)
        actual = " ".join(node.to_sexp() for node in nodes)
    except ParseError as e:
        return (False, "<parse error>", str(e))
    except Exception as e:
        return (False, "<exception>", str(e))

    expected_norm = normalize(test_expected)
    actual_norm = normalize(actual)
    if expected_norm == actual_norm:
        return (True, actual, None)
    else:
        return (False, actual, None)


def main():
    # Find test directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    test_dir = os.path.dirname(script_dir)  # tests/
    repo_root = os.path.dirname(test_dir)

    # Parse arguments
    verbose = False
    filter_pattern = None
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "-v" or arg == "--verbose":
            verbose = True
        elif arg == "-f" or arg == "--filter":
            i = i + 1
            if i < len(sys.argv):
                filter_pattern = sys.argv[i]
        else:
            # Assume it's a test directory or file
            if os.path.exists(arg):
                test_dir = arg
        i = i + 1

    # Find and run tests
    start_time = time.time()
    total_passed = 0
    total_failed = 0
    failed_tests = []

    if os.path.isfile(test_dir):
        test_files = [test_dir]
    else:
        test_files = find_test_files(test_dir)

    for filepath in test_files:
        tests = parse_test_file(filepath)
        rel_path = os.path.relpath(filepath, repo_root)

        for name, test_input, test_expected, line_num in tests:
            # Apply filter
            if filter_pattern is not None:
                if filter_pattern not in name and filter_pattern not in rel_path:
                    continue

            passed, actual, error_msg = run_test(test_input, test_expected)

            if passed:
                total_passed = total_passed + 1
                if verbose:
                    print(f"PASS {rel_path}:{line_num} {name}")
            else:
                total_failed = total_failed + 1
                failed_tests.append(
                    (rel_path, line_num, name, test_input, test_expected, actual, error_msg)
                )
                if verbose:
                    print(f"FAIL {rel_path}:{line_num} {name}")

    elapsed = time.time() - start_time

    # Print summary
    print("")
    if total_failed > 0:
        print("=" * 60)
        print("FAILURES")
        print("=" * 60)
        for rel_path, line_num, name, inp, expected, actual, error_msg in failed_tests:
            print(f"\n{rel_path}:{line_num} {name}")
            print(f"  Input:    {inp!r}")
            print(f"  Expected: {expected}")
            print(f"  Actual:   {actual}")
            if error_msg is not None:
                print(f"  Error:    {error_msg}")
        print("")

    print(f"{total_passed} passed, {total_failed} failed in {elapsed:.2f}s")

    if total_failed > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
