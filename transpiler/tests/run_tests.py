"""Subset-compliant test runner for transpiler tests.

Reads test stream from stdin, runs subset/names verification,
outputs results to stdout.
"""

from __future__ import annotations

import sys

from src.frontend.names import resolve_names
from src.frontend.parse import parse
from src.frontend.subset import verify as verify_subset


def parse_test_stream(content: str) -> list[tuple[str, list[tuple[str, str, str, int]]]]:
    """Parse stdin stream into list of (filepath, tests) tuples."""
    result: list[tuple[str, list[tuple[str, str, str, int]]]] = []
    lines = content.split("\n")
    current_file: str = ""
    current_lines: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("### FILE:"):
            if current_file != "" and len(current_lines) > 0:
                tests = parse_tests(current_lines)
                result.append((current_file, tests))
            current_file = line[9:].strip()
            current_lines = []
        else:
            current_lines.append(line)
        i += 1
    if current_file != "" and len(current_lines) > 0:
        tests = parse_tests(current_lines)
        result.append((current_file, tests))
    return result


def parse_tests(lines: list[str]) -> list[tuple[str, str, str, int]]:
    """Parse .tests content into (name, input, expected, line_num) tuples."""
    result: list[tuple[str, str, str, int]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("=== "):
            test_name = line[4:].strip()
            test_line = i + 1
            i += 1
            input_lines: list[str] = []
            while i < len(lines) and lines[i] != "---":
                input_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1  # skip ---
            expected_lines: list[str] = []
            while i < len(lines) and lines[i] != "---":
                expected_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1  # skip ---
            test_input = "\n".join(input_lines)
            expected = "\n".join(expected_lines)
            result.append((test_name, test_input, expected, test_line))
        else:
            i += 1
    return result


def run_test(filepath: str, code: str, expected: str) -> tuple[bool, str]:
    """Run a single test. Returns (passed, message)."""
    ast_dict = parse(code)
    if "subset" in filepath:
        result = verify_subset(ast_dict)
        errors = result.errors()
        warnings = result.warnings()
    else:
        result = resolve_names(ast_dict)
        errors = result.errors()
        warnings = result.warnings
    expected_stripped = expected.strip()
    if expected_stripped == "ok":
        if len(errors) == 0:
            return (True, "")
        return (False, "expected ok but got: " + errors[0].message)
    if expected_stripped.startswith("error:"):
        substring = expected_stripped[6:].strip()
        i = 0
        while i < len(errors):
            if substring in errors[i].message:
                return (True, "")
            i += 1
        if len(errors) == 0:
            return (False, "expected error containing '" + substring + "' but got no errors")
        return (False, "expected error containing '" + substring + "' but got: " + errors[0].message)
    if expected_stripped.startswith("warning:"):
        substring = expected_stripped[8:].strip()
        i = 0
        while i < len(warnings):
            if substring in warnings[i].message:
                return (True, "")
            i += 1
        if len(warnings) == 0:
            return (False, "expected warning containing '" + substring + "' but got no warnings")
        return (False, "expected warning containing '" + substring + "' but got: " + warnings[0].message)
    return (False, "unknown expected format: " + expected_stripped)


def main() -> int:
    """Main entry point."""
    content = sys.stdin.read()
    files = parse_test_stream(content)
    passed = 0
    failed = 0
    failures: list[tuple[str, str, str]] = []
    i = 0
    while i < len(files):
        filepath = files[i][0]
        tests = files[i][1]
        j = 0
        while j < len(tests):
            test_name = tests[j][0]
            test_input = tests[j][1]
            expected = tests[j][2]
            test_line = tests[j][3]
            ok = run_test(filepath, test_input, expected)
            if ok[0]:
                passed += 1
            else:
                failed += 1
                loc = filepath + ":" + str(test_line)
                failures.append((loc, test_name, ok[1]))
            j += 1
        i += 1
    if failed > 0:
        print("FAILURES:")
        k = 0
        while k < len(failures):
            print("  " + failures[k][0] + " " + failures[k][1])
            print("    " + failures[k][2])
            k += 1
        print("")
    print(str(passed) + " passed, " + str(failed) + " failed")
    if failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
