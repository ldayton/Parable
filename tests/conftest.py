"""Pytest configuration for Parable tests."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from testformat import TestCase, parse_test_file


def pytest_collect_file(parent, file_path):
    """Collect all .tests files."""
    if file_path.suffix == ".tests":
        return TestsFile.from_parent(parent, path=file_path)
    return None


class TestsFile(pytest.File):
    """A .tests file containing test cases."""

    def collect(self):
        for tc in parse_test_file(self.path):
            yield TestItem.from_parent(self, name=tc.name, test_case=tc)


class TestItem(pytest.Item):
    """A single test case."""

    def __init__(self, name, parent, test_case):
        super().__init__(name, parent)
        self.test_case = test_case

    def runtest(self):
        from parable import parse
        from parable.core.errors import ParseError

        try:
            nodes = parse(self.test_case.input)
            actual = " ".join(n.to_sexp() for n in nodes)
        except ParseError as e:
            raise TestFailed(
                input=self.test_case.input,
                expected=self.test_case.expected,
                actual="<parse error>",
                error=str(e),
            ) from None

        expected_norm = " ".join(self.test_case.expected.split())
        actual_norm = " ".join(actual.split())
        if expected_norm != actual_norm:
            raise TestFailed(
                input=self.test_case.input,
                expected=self.test_case.expected,
                actual=actual,
            )

    def repr_failure(self, excinfo):
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
