"""Corpus extraction utilities for tests and benchmarks."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestCase:
    """A test case with input code."""

    name: str
    input: str
    file: str
    line: int


def parse_tree_sitter_corpus(filepath: Path) -> list[TestCase]:
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
    lines = filepath.read_text().splitlines()

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
                    TestCase(
                        name=name,
                        input=input_code,
                        file=str(filepath),
                        line=start_line + 1,
                    )
                )
        else:
            i += 1

    return tests


def load_corpus(corpus_path: Path) -> list[TestCase]:
    """Load all test cases from corpus directory."""
    tests = []
    for txt in corpus_path.rglob("*.txt"):
        tests.extend(parse_tree_sitter_corpus(txt))
    return tests
