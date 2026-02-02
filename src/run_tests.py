"""Test runner for the Python parser."""

import os
import signal
import sys
import time


class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("Test timed out")


def find_test_files(directory):
    """Find all .tests files recursively."""
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
        if line.startswith("#") or line.strip() == "":
            i = i + 1
            continue
        if line.startswith("=== "):
            name = line[4:].strip()
            start_line = i + 1
            i = i + 1
            input_lines = []
            while i < n and lines[i] != "---":
                input_lines.append(lines[i])
                i = i + 1
            if i < n and lines[i] == "---":
                i = i + 1
            expected_lines = []
            while i < n and lines[i] != "---" and not lines[i].startswith("=== "):
                expected_lines.append(lines[i])
                i = i + 1
            if i < n and lines[i] == "---":
                i = i + 1
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

    extglob = False
    if test_input.startswith("# @extglob\n"):
        extglob = True
        test_input = test_input[len("# @extglob\n") :]

    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(10)
    try:
        nodes = parse(test_input, extglob=extglob)
        actual = " ".join(node.to_sexp() for node in nodes)
    except TimeoutError:
        return (False, "<timeout>", "Test timed out after 10 seconds")
    except ParseError as e:
        if normalize(test_expected) == "<error>":
            return (True, "<error>", None)
        return (False, "<parse error>", str(e))
    except Exception as e:
        return (False, "<exception>", str(e))
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

    if normalize(test_expected) == "<error>":
        return (False, actual, "Expected parse error but got successful parse")

    expected_norm = normalize(test_expected)
    actual_norm = normalize(actual)
    if expected_norm == actual_norm:
        return (True, actual, None)
    else:
        return (False, actual, None)


def print_usage():
    print("Usage: parable-test [options] <test_dir>")
    print("Options:")
    print("  -v, --verbose       Show PASS/FAIL for each test")
    print("  -f, --filter PAT    Only run tests matching PAT")
    print("  --max-failures N    Show at most N failures (0=unlimited, default=20)")
    print("  -h, --help          Show this help message")


def main():
    verbose = False
    filter_pattern = None
    max_failures = 20
    test_dir = None

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "-h" or arg == "--help":
            print_usage()
            sys.exit(0)
        elif arg == "-v" or arg == "--verbose":
            verbose = True
        elif arg == "-f" or arg == "--filter":
            i = i + 1
            if i < len(sys.argv):
                filter_pattern = sys.argv[i]
        elif arg == "--max-failures":
            i = i + 1
            if i < len(sys.argv):
                max_failures = int(sys.argv[i])
        elif not arg.startswith("-"):
            test_dir = arg
        i = i + 1

    if test_dir is None:
        print("Error: test_dir is required", file=sys.stderr)
        print_usage()
        sys.exit(1)

    if not os.path.exists(test_dir):
        print(f"Error: {test_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    start_time = time.time()
    total_passed = 0
    total_failed = 0
    failed_tests = []

    base_dir = os.path.dirname(os.path.abspath(test_dir))

    if os.path.isfile(test_dir):
        test_files = [test_dir]
    else:
        test_files = find_test_files(test_dir)

    for filepath in test_files:
        tests = parse_test_file(filepath)
        rel_path = os.path.relpath(filepath, base_dir)

        for name, test_input, test_expected, line_num in tests:
            if filter_pattern is not None:
                if filter_pattern not in name and filter_pattern not in rel_path:
                    continue

            effective_expected = test_expected
            if normalize(test_expected) == "<infinite>":
                effective_expected = "<error>"

            passed, actual, error_msg = run_test(test_input, effective_expected)

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

    if total_failed > 0:
        print("=" * 60)
        print("FAILURES")
        print("=" * 60)
        show_count = (
            len(failed_tests) if max_failures == 0 else min(len(failed_tests), max_failures)
        )
        for rel_path, line_num, name, inp, expected, actual, error_msg in failed_tests[:show_count]:
            print(f"\n{rel_path}:{line_num} {name}")
            print(f"  Input:    {inp!r}")
            print(f"  Expected: {expected}")
            print(f"  Actual:   {actual}")
            if error_msg is not None:
                print(f"  Error:    {error_msg}")
        if max_failures > 0 and total_failed > max_failures:
            print(f"\n... and {total_failed - max_failures} more failures")

    print(f"{total_passed} passed, {total_failed} failed in {elapsed:.2f}s")

    if total_failed > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
