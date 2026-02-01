"""End-to-end codegen test runner for transpiler backends.

Reads test stream from stdin, runs transpilation for each backend,
compares output against expected, outputs results to stdout.
"""

from __future__ import annotations

import sys

from src.frontend import Frontend
from src.frontend.parse import parse
from src.frontend.subset import verify as verify_subset
from src.frontend.names import resolve_names
from src.middleend import analyze
from src.backend.go import GoBackend
from src.backend.java import JavaBackend
from src.backend.javascript import JsBackend
from src.backend.lua import LuaBackend
from src.backend.perl import PerlBackend
from src.backend.python import PythonBackend
from src.backend.ruby import RubyBackend
from src.backend.typescript import TsBackend
from src.backend.csharp import CSharpBackend
from src.backend.php import PhpBackend

BACKENDS: dict[str, type[GoBackend] | type[JavaBackend] | type[JsBackend] | type[LuaBackend] | type[PerlBackend] | type[PythonBackend] | type[RubyBackend] | type[TsBackend] | type[CSharpBackend] | type[PhpBackend]] = {
    "csharp": CSharpBackend,
    "go": GoBackend,
    "java": JavaBackend,
    "javascript": JsBackend,
    "lua": LuaBackend,
    "perl": PerlBackend,
    "php": PhpBackend,
    "python": PythonBackend,
    "ruby": RubyBackend,
    "typescript": TsBackend,
}


def parse_test_stream(content: str) -> list[tuple[str, list[tuple[str, str, dict[str, str], int]]]]:
    """Parse stdin stream into list of (filepath, tests) tuples.

    Each test is (name, input, {lang: expected}, line_num).
    """
    result: list[tuple[str, list[tuple[str, str, dict[str, str], int]]]] = []
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


def parse_tests(lines: list[str]) -> list[tuple[str, str, dict[str, str], int]]:
    """Parse .tests content into (name, input, {lang: expected}, line_num) tuples."""
    result: list[tuple[str, str, dict[str, str], int]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("=== "):
            test_name = line[4:].strip()
            test_line = i + 1
            i += 1
            input_lines: list[str] = []
            while i < len(lines) and not lines[i].startswith("---"):
                input_lines.append(lines[i])
                i += 1
            expected_by_lang: dict[str, str] = {}
            while i < len(lines) and lines[i].startswith("--- "):
                lang = lines[i][4:].strip()
                i += 1
                expected_lines: list[str] = []
                while i < len(lines) and not lines[i].startswith("---"):
                    expected_lines.append(lines[i])
                    i += 1
                expected_by_lang[lang] = "\n".join(expected_lines)
            if i < len(lines) and lines[i] == "---":
                i += 1
            test_input = "\n".join(input_lines)
            result.append((test_name, test_input, expected_by_lang, test_line))
        else:
            i += 1
    return result


def transpile(source: str, target: str) -> tuple[str | None, str | None]:
    """Transpile source to target language. Returns (output, error)."""
    ast_dict = parse(source)
    result = verify_subset(ast_dict)
    errors = result.errors()
    if len(errors) > 0:
        return (None, errors[0].message)
    name_result = resolve_names(ast_dict)
    errors = name_result.errors()
    if len(errors) > 0:
        return (None, errors[0].message)
    fe = Frontend()
    module = fe.transpile(source, ast_dict, name_result=name_result)
    analyze(module)
    backend_cls = BACKENDS.get(target)
    if backend_cls is None:
        return (None, "unknown target: " + target)
    be = backend_cls()
    code = be.emit(module)
    return (code, None)


def normalize(s: str) -> str:
    """Normalize whitespace for comparison."""
    return s.strip()


def contains_normalized(haystack: str, needle: str) -> bool:
    """Check if needle appears in haystack, normalizing line-by-line whitespace."""
    needle_lines = [line.strip() for line in needle.strip().split("\n") if line.strip() != ""]
    haystack_lines = [line.strip() for line in haystack.split("\n") if line.strip() != ""]
    if len(needle_lines) == 0:
        return True
    i = 0
    while i < len(haystack_lines):
        if haystack_lines[i] == needle_lines[0]:
            match = True
            j = 1
            while j < len(needle_lines):
                if i + j >= len(haystack_lines) or haystack_lines[i + j] != needle_lines[j]:
                    match = False
                    break
                j += 1
            if match:
                return True
        i += 1
    return False


def run_test(code: str, lang: str, expected: str) -> tuple[bool, str]:
    """Run a single test. Returns (passed, message)."""
    output, err = transpile(code, lang)
    if err is not None:
        return (False, "transpile error: " + err)
    if output is None:
        return (False, "no output")
    if not contains_normalized(output, expected):
        return (False, "expected not found in output:\n--- expected ---\n" + expected + "\n--- got ---\n" + output)
    return (True, "")


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
            expected_by_lang = tests[j][2]
            test_line = tests[j][3]
            langs_to_test = list(expected_by_lang.keys())
            if "python" not in langs_to_test:
                langs_to_test.append("python")
            for lang in langs_to_test:
                if lang in expected_by_lang:
                    expected = expected_by_lang[lang]
                else:
                    expected = test_input
                ok = run_test(test_input, lang, expected)
                if ok[0]:
                    passed += 1
                else:
                    failed += 1
                    loc = filepath + ":" + str(test_line)
                    failures.append((loc, test_name + " [" + lang + "]", ok[1]))
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
