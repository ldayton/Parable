#!/usr/bin/env python3
"""Verify that all tests/**/*.tests have correct parse expectations per bash-oracle."""

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent.parent
ORACLE_PATH = Path.home() / "source" / "bash-oracle" / "bash-oracle"


@dataclass
class TestCase:
    file: Path
    line: int
    name: str
    input: str
    expected: str


def parse_test_file(filepath: Path) -> list[TestCase]:
    """Parse a .tests file. Returns list of TestCase objects."""
    tests = []
    lines = filepath.read_text().split("\n")
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.startswith("#") or line.strip() == "":
            i += 1
            continue
        if line.startswith("=== "):
            name = line[4:].strip()
            start_line = i + 1
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
            tests.append(
                TestCase(
                    file=filepath,
                    line=start_line,
                    name=name,
                    input="\n".join(input_lines),
                    expected="\n".join(expected_lines),
                )
            )
        else:
            i += 1
    return tests


def get_oracle_output(input_text: str) -> str | None:
    """Get bash-oracle output for the given input. Returns '<error>' for syntax errors."""
    try:
        result = subprocess.run(
            [str(ORACLE_PATH), "-e", input_text],
            capture_output=True,
            timeout=5,
        )
        if result.returncode != 0:
            return "<error>"
        return result.stdout.decode("utf-8", errors="replace").strip()
    except subprocess.TimeoutExpired:
        return None


def normalize(s: str) -> str:
    """Normalize whitespace for comparison."""
    return " ".join(s.split())


def main():
    if not ORACLE_PATH.exists():
        print(f"Error: bash-oracle not found at {ORACLE_PATH}", file=sys.stderr)
        print("Build it with: cd tools/bash-oracle && just build", file=sys.stderr)
        sys.exit(1)

    tests_dir = REPO_ROOT / "tests"

    # Collect all test files recursively
    test_files = sorted(tests_dir.glob("**/*.tests"))

    total = 0
    passed = 0
    failed = 0
    skipped = 0

    failures = []

    for test_file in test_files:
        test_cases = parse_test_file(test_file)

        for tc in test_cases:
            total += 1

            oracle_output = get_oracle_output(tc.input)

            if oracle_output is None:
                skipped += 1
                continue

            expected_norm = normalize(tc.expected)
            oracle_norm = normalize(oracle_output)

            if expected_norm == oracle_norm:
                passed += 1
            else:
                failed += 1
                failures.append(
                    {
                        "file": tc.file,
                        "line": tc.line,
                        "name": tc.name,
                        "input": tc.input,
                        "expected": tc.expected,
                        "oracle": oracle_output,
                    }
                )

    # Print summary
    print(f"\n{'=' * 60}")
    print("Verification Results")
    print(f"{'=' * 60}")
    print(f"Total:   {total}")
    print(f"Passed:  {passed}")
    print(f"Failed:  {failed}")
    print(f"Skipped: {skipped} (invalid bash or timeout)")
    print()

    if failures:
        print(f"\n{'=' * 60}")
        print(f"Failures ({len(failures)}):")
        print(f"{'=' * 60}\n")

        for f in failures:
            print(f"{f['file'].name}:{f['line']} - {f['name']}")
            print(f"  Input:    {f['input']!r}")
            print(f"  Expected: {f['expected']}")
            print(f"  Oracle:   {f['oracle']}")
            print()

        sys.exit(1)
    else:
        print("All tests match bash-oracle expectations!")
        sys.exit(0)


if __name__ == "__main__":
    main()
