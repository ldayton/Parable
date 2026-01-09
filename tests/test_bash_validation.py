"""Validate that all test inputs are valid bash syntax using real bash."""

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest


# Find bash 4.0+ (required for features like |&, ;&, {fd}>)
def _find_bash() -> str:
    for path in ["/opt/homebrew/bin/bash", "/usr/local/bin/bash", "/bin/bash"]:
        if Path(path).exists():
            result = subprocess.run([path, "--version"], capture_output=True, text=True)
            # Extract major version number
            import re

            match = re.search(r"version (\d+)", result.stdout)
            if match and int(match.group(1)) >= 4:
                return path
    # No suitable bash found
    default = shutil.which("bash") or "/bin/bash"
    result = subprocess.run([default, "--version"], capture_output=True, text=True)
    raise RuntimeError(
        f"Bash 4.0+ required for validation tests. Found: {result.stdout.split(chr(10))[0]}\n"
        f"Install with: brew install bash"
    )


BASH_PATH = _find_bash()


@dataclass
class BashTestCase:
    """A single test case from a .tests file."""

    name: str
    input: str
    expected: str
    file: str
    line: int


def parse_test_file(filepath: Path) -> list[BashTestCase]:
    """Parse a .tests file and return list of BashTestCases."""
    tests = []
    current_name = None
    current_input_lines = []
    current_expected = None
    start_line = 0
    seen_separator = False

    lines = filepath.read_text().splitlines()

    i = 0
    while i < len(lines):
        line = lines[i]

        if current_name is None:
            if line.startswith("#") or not line.strip():
                i += 1
                continue

        if line.startswith("=== "):
            if current_name is not None and current_expected is not None:
                tests.append(
                    BashTestCase(
                        name=current_name,
                        input="\n".join(current_input_lines),
                        expected=current_expected,
                        file=str(filepath),
                        line=start_line,
                    )
                )

            current_name = line[4:].strip()
            current_input_lines = []
            current_expected = None
            start_line = i + 1
            seen_separator = False
            i += 1
            continue

        if current_name is not None:
            if line.strip() == "---":
                seen_separator = True
                i += 1
                continue

            if seen_separator and current_expected is None:
                expected_lines = [line]
                paren_count = line.count("(") - line.count(")")
                while paren_count > 0 and i + 1 < len(lines):
                    i += 1
                    next_line = lines[i]
                    expected_lines.append(next_line)
                    paren_count += next_line.count("(") - next_line.count(")")
                current_expected = "\n".join(expected_lines)
            elif not seen_separator:
                current_input_lines.append(line)

        i += 1

    if current_name is not None and current_expected is not None:
        tests.append(
            BashTestCase(
                name=current_name,
                input="\n".join(current_input_lines),
                expected=current_expected,
                file=str(filepath),
                line=start_line,
            )
        )

    return tests


def get_all_test_cases():
    """Collect all test cases from all .tests files."""
    tests_dir = Path(__file__).parent
    test_cases = []
    for test_file in sorted(tests_dir.glob("*.tests")):
        for tc in parse_test_file(test_file):
            test_cases.append(pytest.param(tc, id=f"{test_file.name}::{tc.name}"))
    return test_cases


@pytest.mark.parametrize("test_case", get_all_test_cases())
def test_valid_bash_syntax(test_case):
    """Verify that the test input is valid bash syntax."""
    # Build bash command - enable extglob for extglob tests
    cmd = [BASH_PATH]
    if "extglob" in test_case.file:
        cmd.extend(["-O", "extglob"])
    cmd.append("-n")

    # Run bash -n to check syntax without executing
    result = subprocess.run(
        cmd,
        input=test_case.input,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        pytest.fail(
            f"Invalid bash syntax:\n  Input: {test_case.input!r}\n  Error: {result.stderr.strip()}"
        )
