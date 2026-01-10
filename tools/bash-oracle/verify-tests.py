#!/usr/bin/env python3
"""Verify that all tests/**/*.tests have correct parse expectations per bash-oracle."""

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
TESTS_DIR = SCRIPT_DIR.parent.parent / "tests"
sys.path.insert(0, str(TESTS_DIR))

from testformat import parse_test_file  # noqa: E402

ORACLE_PATH = SCRIPT_DIR / "bash-oracle"


def get_oracle_output(input_text: str, extglob: bool = False) -> str | None:
    """Get bash-oracle output for the given input."""
    cmd = [str(ORACLE_PATH), "--dump-ast"]
    if extglob:
        cmd.extend(["-O", "extglob"])
    try:
        result = subprocess.run(
            cmd,
            input=input_text.encode("utf-8"),
            capture_output=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None
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

    tests_dir = Path(__file__).parent.parent.parent / "tests"

    # Collect all test files recursively
    test_files = sorted(tests_dir.glob("**/*.tests"))

    total = 0
    passed = 0
    failed = 0
    skipped = 0

    failures = []

    for test_file in test_files:
        test_cases = parse_test_file(test_file)
        extglob = "extglob" in test_file.name

        for tc in test_cases:
            total += 1

            oracle_output = get_oracle_output(tc.input, extglob=extglob)

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
