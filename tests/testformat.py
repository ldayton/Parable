"""Shared test file format parser."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestCase:
    """A single test case from a .tests file."""
    name: str
    input: str
    expected: str
    file: Path
    line: int


def parse_test_file(filepath: Path) -> list[TestCase]:
    """Parse a .tests file into TestCases.

    Format:
        === test name
        input line(s)
        ---
        expected s-expression(s)
    """
    tests = []
    lines = filepath.read_text().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        # Skip comments and blank lines outside tests
        if line.startswith("#") or not line.strip():
            i += 1
            continue
        # Test header
        if line.startswith("=== "):
            name = line[4:].strip()
            start_line = i + 1
            i += 1
            # Collect input until ---
            input_lines = []
            while i < len(lines) and lines[i] != "---":
                input_lines.append(lines[i])
                i += 1
            # Skip ---
            if i < len(lines) and lines[i] == "---":
                i += 1
            # Collect expected until ---, next test header, or EOF
            expected_lines = []
            while i < len(lines) and lines[i] != "---" and not lines[i].startswith("=== "):
                expected_lines.append(lines[i])
                i += 1
            # Skip --- end marker if present
            if i < len(lines) and lines[i] == "---":
                i += 1
            # Strip trailing blank lines
            while expected_lines and not expected_lines[-1].strip():
                expected_lines.pop()
            tests.append(TestCase(
                name=name,
                input="\n".join(input_lines),
                expected="\n".join(expected_lines),
                file=filepath,
                line=start_line,
            ))
        else:
            i += 1
    return tests
