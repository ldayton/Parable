"""Tests for check_style.py banned construct detection."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tempfile

from src.check_style import check_file


def check_code(code: str) -> list[tuple[int, str]]:
    """Parse code string and return list of (lineno, message) errors."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    try:
        f.write(code)
        f.close()
        return check_file(f.name)
    finally:
        os.unlink(f.name)


def has_error(errors: list[tuple[int, str]], substring: str) -> bool:
    """Check if any error message contains substring."""
    for _, msg in errors:
        if substring in msg:
            return True
    return False


# --- Tests for new checks ---


def test_lambda() -> None:
    errors = check_code("f = lambda x: x + 1")
    assert has_error(errors, "lambda")


def test_pow_operator() -> None:
    errors = check_code("def f() -> int:\n    return 2 ** 3")
    assert has_error(errors, "**:")


def test_pow_function() -> None:
    errors = check_code("def f() -> int:\n    return pow(2, 3)")
    assert has_error(errors, "pow()")


def test_type_function() -> None:
    errors = check_code("def f(x: object) -> bool:\n    return type(x) == int")
    assert has_error(errors, "type()")


def test_multiple_inheritance() -> None:
    code = """
class A:
    pass
class B:
    pass
class C(A, B):
    pass
"""
    errors = check_code(code)
    assert has_error(errors, "multiple inheritance")


def test_single_inheritance_allowed() -> None:
    code = """
class A:
    pass
class B(A):
    pass
"""
    errors = check_code(code)
    assert not has_error(errors, "multiple inheritance")


def test_exception_inheritance_allowed() -> None:
    code = """
class A:
    pass
class MyError(A, Exception):
    pass
"""
    errors = check_code(code)
    assert not has_error(errors, "multiple inheritance")


def test_nested_class() -> None:
    code = """
class Outer:
    class Inner:
        pass
"""
    errors = check_code(code)
    assert has_error(errors, "nested class")


def test_bare_except() -> None:
    code = """
def f() -> None:
    try:
        pass
    except:
        pass
"""
    errors = check_code(code)
    assert has_error(errors, "bare except")


def test_typed_except_allowed() -> None:
    code = """
def f() -> None:
    try:
        pass
    except ValueError:
        pass
"""
    errors = check_code(code)
    assert not has_error(errors, "bare except")


def test_dunder_method_banned() -> None:
    code = """
class Foo:
    def __str__(self) -> str:
        return "foo"
"""
    errors = check_code(code)
    assert has_error(errors, "dunder method __str__")


def test_dunder_eq_banned() -> None:
    code = """
class Foo:
    def __eq__(self, other: object) -> bool:
        return True
"""
    errors = check_code(code)
    assert has_error(errors, "dunder method __eq__")


def test_dunder_init_allowed() -> None:
    code = """
class Foo:
    def __init__(self) -> None:
        pass
"""
    errors = check_code(code)
    assert not has_error(errors, "dunder method __init__")


def test_dunder_new_allowed() -> None:
    code = """
class Foo:
    def __new__(cls) -> "Foo":
        return object.__new__(cls)
"""
    errors = check_code(code)
    assert not has_error(errors, "dunder method __new__")


def test_dunder_repr_allowed() -> None:
    code = """
class Foo:
    def __repr__(self) -> str:
        return "Foo()"
"""
    errors = check_code(code)
    assert not has_error(errors, "dunder method __repr__")


def test_starred_args_in_call() -> None:
    code = """
def f(a: int, b: int) -> int:
    return a + b
def g() -> int:
    items: list[int] = [1, 2]
    return f(*items)
"""
    errors = check_code(code)
    assert has_error(errors, "*args in call")


def test_kwargs_in_call() -> None:
    code = """
def f(a: int, b: int) -> int:
    return a + b
def g() -> int:
    d: dict[str, int] = {"a": 1, "b": 2}
    return f(**d)
"""
    errors = check_code(code)
    assert has_error(errors, "**kwargs in call")


def test_is_with_non_none() -> None:
    code = """
def f(a: int, b: int) -> bool:
    return a is b
"""
    errors = check_code(code)
    assert has_error(errors, "is/is not")


def test_is_not_with_non_none() -> None:
    code = """
def f(a: int, b: int) -> bool:
    return a is not b
"""
    errors = check_code(code)
    assert has_error(errors, "is/is not")


def test_is_none_allowed() -> None:
    code = """
def f(a: int | None) -> bool:
    return a is None
"""
    errors = check_code(code)
    assert not has_error(errors, "is/is not")


def test_is_not_none_allowed() -> None:
    code = """
def f(a: int | None) -> bool:
    return a is not None
"""
    errors = check_code(code)
    assert not has_error(errors, "is/is not")


def test_none_is_x_allowed() -> None:
    code = """
def f(a: int | None) -> bool:
    return None is a
"""
    errors = check_code(code)
    assert not has_error(errors, "is/is not")


def test_mutable_default_list() -> None:
    code = """
def f(x: list[int] = []) -> list[int]:
    return x
"""
    errors = check_code(code)
    assert has_error(errors, "mutable default")


def test_mutable_default_dict() -> None:
    code = """
def f(x: dict[str, int] = {}) -> dict[str, int]:
    return x
"""
    errors = check_code(code)
    assert has_error(errors, "mutable default")


def test_none_default_allowed() -> None:
    code = """
def f(x: list[int] | None = None) -> list[int]:
    if x is None:
        x = []
    return x
"""
    errors = check_code(code)
    assert not has_error(errors, "mutable default")


def test_dunder_class_attribute() -> None:
    code = """
def f(x: object) -> type:
    return x.__class__
"""
    errors = check_code(code)
    assert has_error(errors, "__class__")


def test_nested_function() -> None:
    code = """
def outer() -> int:
    def inner() -> int:
        return 1
    return inner()
"""
    errors = check_code(code)
    assert has_error(errors, "nested function 'inner'")


def test_staticmethod_decorator() -> None:
    code = """
class Foo:
    @staticmethod
    def bar() -> int:
        return 1
"""
    errors = check_code(code)
    assert has_error(errors, "@staticmethod")


def test_classmethod_decorator() -> None:
    code = """
class Foo:
    @classmethod
    def bar(cls) -> int:
        return 1
"""
    errors = check_code(code)
    assert has_error(errors, "@classmethod")


def test_property_decorator() -> None:
    code = """
class Foo:
    @property
    def bar(self) -> int:
        return 1
"""
    errors = check_code(code)
    assert has_error(errors, "@property")


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
