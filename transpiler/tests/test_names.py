"""Tests for names.py name resolution (Phase 4)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.frontend.names import resolve_names
from src.frontend.parse import parse


def check_names(code: str) -> list[tuple[int, str]]:
    """Parse code string and return list of (lineno, message) errors."""
    ast_dict = parse(code)
    result = resolve_names(ast_dict)
    return [(v.lineno, v.message) for v in result.violations]


def check_warnings(code: str) -> list[tuple[int, str]]:
    """Parse code string and return list of (lineno, message) warnings."""
    ast_dict = parse(code)
    result = resolve_names(ast_dict)
    return [(w.lineno, w.message) for w in result.warnings]


def has_error(errors: list[tuple[int, str]], substring: str) -> bool:
    """Check if any error message contains substring."""
    for _, msg in errors:
        if substring in msg:
            return True
    return False


# --- Tests for undefined names ---


def test_undefined_name() -> None:
    errors = check_names("def f() -> int:\n    return x")
    assert has_error(errors, "not defined")


def test_undefined_name_in_expression() -> None:
    errors = check_names("def f() -> int:\n    y: int = 1\n    return x + y")
    assert has_error(errors, "'x' is not defined")


# --- Tests for parameters ---


def test_parameter_in_scope() -> None:
    errors = check_names("def f(x: int) -> int:\n    return x")
    assert not has_error(errors, "undefined")


def test_multiple_parameters() -> None:
    errors = check_names("def f(x: int, y: int) -> int:\n    return x + y")
    assert not has_error(errors, "undefined")


# --- Tests for local variables ---


def test_local_variable() -> None:
    errors = check_names("def f() -> int:\n    x: int = 1\n    return x")
    assert not has_error(errors, "undefined")


def test_local_assign_without_annotation() -> None:
    errors = check_names("def f() -> int:\n    x = 1\n    return x")
    assert not has_error(errors, "undefined")


def test_for_loop_variable() -> None:
    code = """
def f() -> int:
    total: int = 0
    i = 0
    while i < 10:
        total = total + i
        i = i + 1
    return total
"""
    errors = check_names(code)
    assert not has_error(errors, "undefined")


def test_for_loop_target_in_scope() -> None:
    code = """
def f(items: list[int]) -> int:
    total: int = 0
    for x in items:
        total = total + x
    return total
"""
    errors = check_names(code)
    assert not has_error(errors, "undefined")


# --- Tests for class methods ---


def test_class_method_self_field() -> None:
    code = """
class Foo:
    def __init__(self) -> None:
        self.x: int = 1
    def get(self) -> int:
        return self.x
"""
    errors = check_names(code)
    assert not has_error(errors, "undefined")


def test_class_method_self_parameter() -> None:
    code = """
class Foo:
    def set(self, value: int) -> None:
        self.x = value
"""
    errors = check_names(code)
    assert not has_error(errors, "undefined")


def test_method_parameter_in_scope() -> None:
    code = """
class Foo:
    def add(self, x: int, y: int) -> int:
        return x + y
"""
    errors = check_names(code)
    assert not has_error(errors, "undefined")


# --- Tests for builtins ---


def test_builtin_allowed() -> None:
    errors = check_names("def f(items: list[int]) -> int:\n    return len(items)")
    assert not has_error(errors, "undefined")


def test_builtin_range() -> None:
    code = """
def f() -> int:
    total: int = 0
    for i in range(10):
        total = total + i
    return total
"""
    errors = check_names(code)
    assert not has_error(errors, "undefined")


def test_builtin_print() -> None:
    code = """
def f() -> None:
    print("hello")
"""
    errors = check_names(code)
    assert not has_error(errors, "undefined")


def test_builtin_isinstance() -> None:
    code = """
def f(x: object) -> bool:
    return isinstance(x, int)
"""
    errors = check_names(code)
    assert not has_error(errors, "undefined")


# --- Tests for module-level names ---


def test_function_calls_function() -> None:
    code = """
def helper() -> int:
    return 1
def main() -> int:
    return helper()
"""
    errors = check_names(code)
    assert not has_error(errors, "undefined")


def test_function_instantiates_class() -> None:
    code = """
class Foo:
    def __init__(self) -> None:
        pass
def make() -> Foo:
    return Foo()
"""
    errors = check_names(code)
    assert not has_error(errors, "undefined")


def test_constant_in_function() -> None:
    code = """
MAX_SIZE: int = 100
def f() -> int:
    return MAX_SIZE
"""
    errors = check_names(code)
    assert not has_error(errors, "undefined")


# --- Tests for redefinition ---


def test_redefinition_function() -> None:
    code = """
def f() -> int:
    return 1
def f() -> int:
    return 2
"""
    errors = check_names(code)
    assert has_error(errors, "already defined")


def test_redefinition_class() -> None:
    code = """
class Foo:
    pass
class Foo:
    pass
"""
    errors = check_names(code)
    assert has_error(errors, "already defined")


def test_redefinition_function_and_class() -> None:
    code = """
def Foo() -> int:
    return 1
class Foo:
    pass
"""
    errors = check_names(code)
    assert has_error(errors, "already defined")


# --- Tests for tuple unpacking ---


def test_tuple_unpack_in_for() -> None:
    code = """
def f(items: list[tuple[int, int]]) -> int:
    total: int = 0
    for x, y in items:
        total = total + x + y
    return total
"""
    errors = check_names(code)
    assert not has_error(errors, "undefined")


def test_tuple_unpack_in_assign() -> None:
    code = """
def f() -> int:
    x, y = 1, 2
    return x + y
"""
    errors = check_names(code)
    assert not has_error(errors, "undefined")


# --- Edge cases ---


def test_empty_function() -> None:
    code = """
def f() -> None:
    pass
"""
    errors = check_names(code)
    assert len(errors) == 0


def test_class_with_no_methods() -> None:
    code = """
class Empty:
    pass
"""
    errors = check_names(code)
    assert len(errors) == 0


def test_class_field_annotation() -> None:
    code = """
class Foo:
    x: int
    def get(self) -> int:
        return self.x
"""
    errors = check_names(code)
    assert not has_error(errors, "undefined")


# --- Tests for shadowing warnings ---


def test_parameter_shadows_builtin() -> None:
    code = """
def f(len: int) -> int:
    return len
"""
    warnings = check_warnings(code)
    assert has_error(warnings, "shadows builtin")


def test_parameter_no_shadow() -> None:
    code = """
def f(x: int) -> int:
    return x
"""
    warnings = check_warnings(code)
    assert not has_error(warnings, "shadows")


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
