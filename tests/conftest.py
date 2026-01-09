"""Pytest configuration and fixtures for Parable tests."""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest


# === Oils corpus filtering ===
# All 213 oils test failures are tracked in docs/ROADMAP.md
# No tests are skipped - failures show as actual test failures

OILS_BANNED_FILES: set[str] = set()
OILS_SKIP_TESTS: set[str] = set()


def oils_skip_reason(filepath: Path, name: str) -> str | None:
    """Return skip reason if this oils test should be skipped, else None."""
    if filepath.name in OILS_BANNED_FILES:
        return f"banned: {filepath.name}"

    key = f"{filepath.name}::{name}"
    if key in OILS_SKIP_TESTS:
        return f"covered: {key}"

    return None


# Find bash 4.0+ for validation
def _find_bash() -> str | None:
    for path in ["/opt/homebrew/bin/bash", "/usr/local/bin/bash", "/bin/bash"]:
        if Path(path).exists():
            result = subprocess.run([path, "--version"], capture_output=True, text=True)
            match = re.search(r"version (\d+)", result.stdout)
            if match and int(match.group(1)) >= 4:
                return path
    return None


BASH_PATH = _find_bash()


@dataclass
class TestCase:
    """A single test case from a .tests file."""

    name: str
    input: str
    expected: str
    file: str
    line: int

    def __str__(self):
        return self.name


def parse_test_file(filepath: Path) -> list[TestCase]:
    """Parse a .tests file and return list of TestCases.

    Format:
        === test name
        input line(s)
        ---
        (expected s-expression)

    The --- separator is optional for backwards compatibility when input
    doesn't start with '('.
    """
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

        # Skip comments and empty lines outside of test cases
        if current_name is None:
            if line.startswith("#") or not line.strip():
                i += 1
                continue

        # New test case
        if line.startswith("=== "):
            # Save previous test if exists
            if current_name is not None and current_expected is not None:
                tests.append(
                    TestCase(
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

        # Inside a test case
        if current_name is not None:
            # Check for separator
            if line.strip() == "---":
                seen_separator = True
                i += 1
                continue

            # After separator, collect expected output
            if seen_separator and current_expected is None:
                # Collect multi-line expected output
                expected_lines = [line]
                # Count parens to handle multi-line s-expressions
                paren_count = line.count("(") - line.count(")")
                while paren_count > 0 and i + 1 < len(lines):
                    i += 1
                    next_line = lines[i]
                    expected_lines.append(next_line)
                    paren_count += next_line.count("(") - next_line.count(")")
                current_expected = "\n".join(expected_lines)
            elif not seen_separator:
                # Before separator, collect input
                current_input_lines.append(line)

        i += 1

    # Don't forget the last test
    if current_name is not None and current_expected is not None:
        tests.append(
            TestCase(
                name=current_name,
                input="\n".join(current_input_lines),
                expected=current_expected,
                file=str(filepath),
                line=start_line,
            )
        )

    return tests


def pytest_collect_file(parent, file_path):
    """Collect .tests files and tree-sitter corpus files as test modules."""
    if file_path.suffix == ".tests":
        return TestsFile.from_parent(parent, path=file_path)
    # Corpus files in corpus*/ subdirectories (tree-sitter, oils, etc.)
    if file_path.suffix == ".txt" and any(p.startswith("corpus") for p in file_path.parts):
        return TreeSitterCorpusFile.from_parent(parent, path=file_path)
    return None


class TestsFile(pytest.File):
    """A .tests file containing test cases."""

    def collect(self):
        """Yield test items from the .tests file."""
        for test_case in parse_test_file(self.path):
            yield TestItem.from_parent(self, name=test_case.name, test_case=test_case)


class TestItem(pytest.Item):
    """A single test case from a .tests file."""

    def __init__(self, name, parent, test_case):
        super().__init__(name, parent)
        self.test_case = test_case

    def runtest(self):
        """Run the test."""
        from parable import parse
        from parable.core.errors import ParseError

        try:
            nodes = parse(self.test_case.input)
            if len(nodes) == 1:
                actual = nodes[0].to_sexp()
            else:
                actual = " ".join(n.to_sexp() for n in nodes)
        except ParseError as e:
            raise TestFailed(
                input=self.test_case.input,
                expected=self.test_case.expected,
                actual="<parse error>",
                error=str(e),
            ) from None

        # Normalize whitespace for comparison
        expected_norm = " ".join(self.test_case.expected.split())
        actual_norm = " ".join(actual.split())

        if expected_norm != actual_norm:
            raise TestFailed(
                input=self.test_case.input,
                expected=self.test_case.expected,
                actual=actual,
            )

    def repr_failure(self, excinfo):
        """Format test failure output."""
        if isinstance(excinfo.value, TestFailed):
            tf = excinfo.value
            lines = [
                f"Input:    {tf.input!r}",
                f"Expected: {tf.expected}",
                f"Actual:   {tf.actual}",
            ]
            if tf.error:
                lines.append(f"Error:    {tf.error}")
            return "\n".join(lines)
        return super().repr_failure(excinfo)

    def reportinfo(self):
        return self.path, self.test_case.line, f"{self.path.name}::{self.name}"


class TestFailed(Exception):
    """Raised when a test fails."""

    def __init__(self, input: str, expected: str, actual: str, error: str = None):
        self.input = input
        self.expected = expected
        self.actual = actual
        self.error = error
        super().__init__(f"Expected {expected!r}, got {actual!r}")


# === Tree-sitter corpus support ===


@dataclass
class TreeSitterTestCase:
    """A test case from a tree-sitter corpus file."""

    name: str
    input: str
    file: str
    line: int


def parse_tree_sitter_corpus(filepath: Path) -> list[TreeSitterTestCase]:
    """Parse a tree-sitter corpus .txt file.

    Format:
        ================================================================================
        Test Name
        ================================================================================

        input code here
        (can be multiple lines)

        --------------------------------------------------------------------------------

        (expected parse tree - ignored, different AST format)
    """
    tests = []
    content = filepath.read_text()
    lines = content.splitlines()

    # Split by separator (line of = signs)
    i = 0
    while i < len(lines):
        line = lines[i]

        # Look for test header (line of = signs, at least 20)
        if len(line) >= 20 and all(c == "=" for c in line):
            start_line = i
            i += 1
            if i >= len(lines):
                break

            # Next line is test name
            name = lines[i].strip()
            i += 1
            if i >= len(lines):
                break

            # Skip second row of = signs
            if len(lines[i]) >= 20 and all(c == "=" for c in lines[i]):
                i += 1

            # Collect input until we hit dashes
            input_lines = []
            while i < len(lines):
                if lines[i].startswith("-" * 3) and all(c == "-" for c in lines[i]):
                    break
                input_lines.append(lines[i])
                i += 1

            # Skip past the expected output section
            while i < len(lines) and not (len(lines[i]) >= 20 and all(c == "=" for c in lines[i])):
                i += 1

            input_code = "\n".join(input_lines).strip()
            if input_code:
                tests.append(
                    TreeSitterTestCase(
                        name=name,
                        input=input_code,
                        file=str(filepath),
                        line=start_line + 1,
                    )
                )
        else:
            i += 1

    return tests


class TreeSitterCorpusFile(pytest.File):
    """A tree-sitter corpus .txt file."""

    def collect(self):
        """Yield test items from the corpus file."""
        for test_case in parse_tree_sitter_corpus(self.path):
            yield TreeSitterTestItem.from_parent(self, name=test_case.name, test_case=test_case)


class TreeSitterTestItem(pytest.Item):
    """A single test from a tree-sitter corpus file."""

    def __init__(self, name, parent, test_case):
        super().__init__(name, parent)
        self.test_case = test_case
        self._is_oils = "corpus/oils" in test_case.file

    def runtest(self):
        """Validate the input parses correctly."""
        from parable import parse
        from parable.core.errors import ParseError

        # For oils corpus, check if we should skip
        if self._is_oils:
            skip_reason = oils_skip_reason(Path(self.test_case.file), self.test_case.name)
            if skip_reason:
                pytest.skip(skip_reason)

        # First check bash accepts it (with extglob for extended patterns)
        if BASH_PATH:
            result = subprocess.run(
                [BASH_PATH, "-O", "extglob", "-n"],
                input=self.test_case.input,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise TreeSitterTestFailed(
                    input=self.test_case.input,
                    error=f"bash -n failed: {result.stderr.strip()}",
                )

        # Then check our parser accepts it
        try:
            parse(self.test_case.input)
        except ParseError as e:
            raise TreeSitterTestFailed(
                input=self.test_case.input,
                error=f"parse error: {e}",
            ) from None

    def repr_failure(self, excinfo):
        """Format test failure output."""
        if isinstance(excinfo.value, TreeSitterTestFailed):
            tf = excinfo.value
            return f"Input: {tf.input!r}\nError: {tf.error}"
        return super().repr_failure(excinfo)

    def reportinfo(self):
        return self.path, self.test_case.line, f"{self.path.name}::{self.name}"


class TreeSitterTestFailed(Exception):
    """Raised when a tree-sitter test fails."""

    def __init__(self, input: str, error: str):
        self.input = input
        self.error = error
        super().__init__(error)
