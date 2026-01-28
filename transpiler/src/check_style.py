#!/usr/bin/env python3
"""Check for banned Python constructions in parable.py.

Goal: C-style code that translates easily to JS/TS.

Banned constructions:

    Construction          Example                   Use instead
    --------------------  ------------------------  --------------------------
    **kwargs              def f(**kwargs):          explicit parameters
    all                   all(x for x in lst)       explicit loop with early return
    any                   any(x for x in lst)       explicit loop with early return
    assert                assert x                  if not x: raise
    async def             async def f():            avoid async
    async for             async for x in y:         avoid async
    async with            async with x:             avoid async
    await                 await x                   avoid async
    chained comparison    a < b < c                 a < b and b < c
    decorator             @cache                    call wrapper manually
    del statement         del x                     reassign or let go out of scope
    generator expression  (x for x in ...)          explicit loop
    global                global x                  pass as parameter
    hasattr               hasattr(x, 'y')           explicit field check
    import                import x                  not allowed (self-contained)
    import from           from x import y           not allowed (except __future__, typing)
    loop else             for x: ... else:          use flag variable
    match/case            match x:                  if/elif chain
    nonlocal              nonlocal x                pass as parameter
    or-default            x or []                   if x is None: x = []
    try else              try: ... else:            move else code after try block
    with statement        with open(f) as x:        try/finally
    yield                 yield x                   return list or use callback
    yield from            yield from iter           explicit loop
    getattr               getattr(x, 'y', None)     direct attribute access
    tuple from variable   a, b = op (op is var)     unpack directly: a, b = func()
    lambda                lambda x: x+1             named function
    **exponentiation      x ** 2                    x * x or loop
    pow                   pow(x, 2)                 multiplication
    staticmethod          @staticmethod             module-level function
    classmethod           @classmethod              module-level function
    property              @property                 explicit getter method
    multiple inherit      class Foo(A, B):          single inheritance
    nested function       def f(): def g():         flatten or pass callback
    nested class          class A: class B:         module-level classes
    dunder methods        __str__, __eq__, etc      only __init__/__new__/__repr__ allowed
    bare except           except:                   except ExceptionType:
    type()                type(x)                   isinstance()
    __class__             x.__class__               isinstance()
    *args in call         f(*items)                 unpack explicitly
    **kwargs in call      f(**d)                    pass args explicitly
    is/is not (non-None)  x is y                    x == y (except None checks)
    mutable default       def f(x=[]):              x=None then if x is None

Required annotations (for Go/TS transpiler):

    Missing                Example                   Required
    --------------------   ------------------------  --------------------------
    return type            def f():                  def f() -> int:
    parameter type         def f(x):                 def f(x: int):
    bare list              x: list                   x: list[Node]
    bare dict              x: dict                   x: dict[str, int]
    bare set               x: set                    x: set[str]
    bare tuple             -> tuple:                 -> tuple[int, str]:
    unannotated field      self.x = CONST            self.x: int = CONST
"""

import ast
import os
import sys

BARE_COLLECTION_TYPES = {"list", "dict", "set", "tuple"}


def is_bare_collection(annotation):
    """Check if annotation is a bare collection type without parameters."""
    if isinstance(annotation, ast.Name):
        return annotation.id in BARE_COLLECTION_TYPES
    return False


def is_obvious_literal(node):
    """Check if node is a literal with obvious type (str, int, bool, float)."""
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (str, int, bool, float)) and node.value is not None
    # True/False are Names in older Python, Constants in newer
    if isinstance(node, ast.Name) and node.id in ("True", "False"):
        return True
    return False


def check_unannotated_field_assigns(tree):
    """Check for self.x = val assignments that should have type annotations.

    Skips assignments where type is obvious:
    - Value is an annotated parameter (type flows from param)
    - Value is a literal (str, int, bool, float)
    """
    errors = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        # Collect all annotated field names for this class
        annotated_fields = set()
        for item in ast.walk(node):
            if isinstance(item, ast.AnnAssign):
                # Class-level: x: int = 0
                if isinstance(item.target, ast.Name):
                    annotated_fields.add(item.target.id)
                # Method-level: self.x: int = 0
                if isinstance(item.target, ast.Attribute):
                    if isinstance(item.target.value, ast.Name):
                        if item.target.value.id == "self":
                            annotated_fields.add(item.target.attr)
        # Check each method for unannotated field assignments
        for item in node.body:
            if not isinstance(item, ast.FunctionDef):
                continue
            # Collect annotated parameter names
            annotated_params = set()
            for arg in item.args.args:
                if arg.annotation is not None:
                    annotated_params.add(arg.arg)
            # Walk method body for self.x = val assignments
            for stmt in ast.walk(item):
                if not isinstance(stmt, ast.Assign):
                    continue
                for target in stmt.targets:
                    if not isinstance(target, ast.Attribute):
                        continue
                    if not isinstance(target.value, ast.Name):
                        continue
                    if target.value.id != "self":
                        continue
                    field_name = target.attr
                    # Skip if already annotated somewhere
                    if field_name in annotated_fields:
                        continue
                    # Skip if value is just an annotated parameter
                    if isinstance(stmt.value, ast.Name):
                        if stmt.value.id in annotated_params:
                            annotated_fields.add(field_name)
                            continue
                    # Skip if value is an obvious literal
                    if is_obvious_literal(stmt.value):
                        annotated_fields.add(field_name)
                        continue
                    # Flag it
                    errors.append(
                        (
                            stmt.lineno,
                            "unannotated field: self." + field_name + " needs type annotation",
                        )
                    )
                    # Add to annotated_fields to avoid duplicate errors
                    annotated_fields.add(field_name)
    return errors


def check_nested_functions(tree):
    """Check for function definitions inside other functions."""
    errors = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        # Look for FunctionDef in body (direct children only to avoid class methods)
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef):
                errors.append(
                    (
                        stmt.lineno,
                        "nested function '"
                        + stmt.name
                        + "': define at module level or pass as callback",
                    )
                )
    return errors


def find_python_files(directory):
    """Find all .py files recursively."""
    result = []
    for root, _dirs, files in os.walk(directory):
        for f in files:
            if f.endswith(".py"):
                result.append(os.path.join(root, f))
    result.sort()
    return result


def check_file(filepath):
    f = open(filepath)
    try:
        source = f.read()
    finally:
        f.close()

    tree = ast.parse(source, filepath)
    errors = []

    # Check for unannotated field assignments
    errors.extend(check_unannotated_field_assigns(tree))

    # Check for nested functions
    errors.extend(check_nested_functions(tree))

    for node in ast.walk(tree):
        lineno = getattr(node, "lineno", 0)

        # generator expression
        if isinstance(node, ast.GeneratorExp):
            errors.append((lineno, "generator expression: use explicit for loop"))

        # decorator
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for dec in node.decorator_list:
                dec_name = None
                if isinstance(dec, ast.Name):
                    dec_name = dec.id
                elif isinstance(dec, ast.Attribute):
                    dec_name = dec.attr
                if dec_name == "staticmethod":
                    errors.append((lineno, "@staticmethod: use module-level function instead"))
                elif dec_name == "classmethod":
                    errors.append((lineno, "@classmethod: use module-level function instead"))
                elif dec_name == "property":
                    errors.append((lineno, "@property: use explicit getter method instead"))
                else:
                    errors.append((lineno, "decorator: call wrapper function manually"))

        # with statement
        if isinstance(node, ast.With):
            errors.append((lineno, "with statement: use try/finally instead"))

        # **kwargs (but *args is allowed - transpiles to rest params)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.args.kwarg:
                errors.append((lineno, "**kwargs: use explicit parameters"))

        # match/case (Python 3.10+)
        if isinstance(node, ast.Match):
            errors.append((lineno, "match/case: use if/elif chain instead"))

        # chained comparison: a < b < c
        if isinstance(node, ast.Compare):
            if len(node.ops) > 1:
                errors.append(
                    (lineno, "chained comparison: use 'and' explicitly, e.g. a < b and b < c")
                )

        # yield
        if isinstance(node, ast.Yield):
            errors.append((lineno, "yield: return a list or use a callback instead"))

        # yield from
        if isinstance(node, ast.YieldFrom):
            errors.append((lineno, "yield from: use explicit loop instead"))

        # global
        if isinstance(node, ast.Global):
            errors.append((lineno, "global: pass as parameter instead"))

        # nonlocal
        if isinstance(node, ast.Nonlocal):
            errors.append((lineno, "nonlocal: pass as parameter instead"))

        # async def
        if isinstance(node, ast.AsyncFunctionDef):
            errors.append((lineno, "async def: avoid async, use synchronous code"))

        # async for
        if isinstance(node, ast.AsyncFor):
            errors.append((lineno, "async for: avoid async, use synchronous code"))

        # async with
        if isinstance(node, ast.AsyncWith):
            errors.append((lineno, "async with: avoid async, use synchronous code"))

        # await
        if isinstance(node, ast.Await):
            errors.append((lineno, "await: avoid async, use synchronous code"))

        # assert
        if isinstance(node, ast.Assert):
            errors.append((lineno, "assert: use 'if not x: raise' instead"))

        # hasattr
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "hasattr":
                errors.append((lineno, "hasattr: use explicit field check instead"))

        # getattr
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "getattr":
                errors.append((lineno, "getattr: use direct attribute access instead"))

        # tuple unpack from variable (Go can't store multi-return in single var)
        # BAD:  op = func(); ...; a, b = op
        # GOOD: a, b = func()  or  a, b = x, y
        if isinstance(node, ast.Assign):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple):
                if isinstance(node.value, ast.Name):
                    errors.append(
                        (lineno, "tuple unpack from variable: unpack directly from call instead")
                    )

        # all()
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "all":
                errors.append((lineno, "all(): use explicit loop with early return"))

        # any()
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "any":
                errors.append((lineno, "any(): use explicit loop with early return"))

        # loop else (for...else, while...else) - Python-specific
        if isinstance(node, (ast.For, ast.While)):
            if node.orelse:
                errors.append((lineno, "loop else: use flag variable instead"))

        # or-default pattern: x or []
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            for val in node.values[1:]:  # check non-first values
                if isinstance(val, (ast.List, ast.Dict, ast.Set)):
                    errors.append((lineno, "or-default: use 'if x is None: x = ...' instead"))
                if isinstance(val, ast.Constant) and val.value in (0, "", None, False):
                    errors.append((lineno, "or-default: use 'if x is None: x = ...' instead"))

        # del statement
        if isinstance(node, ast.Delete):
            errors.append((lineno, "del: reassign or let variable go out of scope"))

        # try...else
        if isinstance(node, ast.Try) and node.orelse:
            errors.append((lineno, "try else: move else code after try block"))

        # import
        if isinstance(node, ast.Import):
            errors.append((lineno, "import: not allowed, code must be self-contained"))

        # from ... import (allow __future__, typing, collections.abc)
        if isinstance(node, ast.ImportFrom):
            if node.module not in ("__future__", "typing", "collections.abc"):
                errors.append((lineno, "from import: not allowed, code must be self-contained"))

        # missing return type annotation (skip __init__ and __new__)
        if isinstance(node, ast.FunctionDef):
            if node.returns is None and node.name not in ("__init__", "__new__"):
                errors.append((lineno, "missing return type: def " + node.name + "() -> ..."))

        # missing parameter type annotation (skip self/cls)
        if isinstance(node, ast.FunctionDef):
            for i, arg in enumerate(node.args.args):
                if arg.arg in ("self", "cls") and i == 0:
                    continue
                if arg.annotation is None:
                    errors.append(
                        (lineno, "missing param type: " + arg.arg + " in " + node.name + "()")
                    )

        # bare collection in parameter annotation
        if isinstance(node, ast.FunctionDef):
            for arg in node.args.args:
                if arg.annotation and is_bare_collection(arg.annotation):
                    errors.append(
                        (
                            lineno,
                            "bare "
                            + arg.annotation.id
                            + ": "
                            + arg.arg
                            + " in "
                            + node.name
                            + "() needs type parameter",
                        )
                    )

        # bare collection in return type annotation
        if isinstance(node, ast.FunctionDef):
            if node.returns and is_bare_collection(node.returns):
                errors.append(
                    (
                        lineno,
                        "bare "
                        + node.returns.id
                        + ": "
                        + node.name
                        + "() return needs type parameter",
                    )
                )

        # bare collection in variable annotation
        if isinstance(node, ast.AnnAssign):
            if is_bare_collection(node.annotation):
                target_name = node.target.id if isinstance(node.target, ast.Name) else "?"
                errors.append(
                    (
                        lineno,
                        "bare " + node.annotation.id + ": " + target_name + " needs type parameter",
                    )
                )

        # lambda
        if isinstance(node, ast.Lambda):
            errors.append((lineno, "lambda: use named function instead"))

        # ** exponentiation
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            errors.append((lineno, "**: use multiplication or helper function"))

        # pow()
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "pow":
                errors.append((lineno, "pow(): use multiplication instead"))

        # type()
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "type":
                errors.append((lineno, "type(): use isinstance() instead"))

        # multiple inheritance (exclude Exception from base count)
        if isinstance(node, ast.ClassDef):
            real_bases = []
            for b in node.bases:
                if isinstance(b, ast.Name) and b.id == "Exception":
                    continue
                real_bases.append(b)
            if len(real_bases) > 1:
                errors.append((lineno, "multiple inheritance: use single base class"))

        # nested class
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.ClassDef):
                    errors.append((child.lineno, "nested class: define at module level"))

        # bare except
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                errors.append((lineno, "bare except: specify exception type"))

        # dunder methods (except __init__, __new__, __repr__)
        if isinstance(node, ast.FunctionDef):
            if node.name.startswith("__") and node.name.endswith("__"):
                if node.name not in ("__init__", "__new__", "__repr__"):
                    errors.append(
                        (
                            lineno,
                            "dunder method "
                            + node.name
                            + ": only __init__/__new__/__repr__ allowed",
                        )
                    )

        # *args in call (starred argument)
        if isinstance(node, ast.Call):
            for arg in node.args:
                if isinstance(arg, ast.Starred):
                    errors.append((lineno, "*args in call: unpack arguments explicitly"))
                    break

        # **kwargs in call
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg is None:  # **kwargs
                    errors.append((lineno, "**kwargs in call: pass arguments explicitly"))
                    break

        # is/is not with non-None
        if isinstance(node, ast.Compare):
            left = node.left
            for i, op in enumerate(node.ops):
                comparator = node.comparators[i]
                if isinstance(op, (ast.Is, ast.IsNot)):
                    left_is_none = isinstance(left, ast.Constant) and left.value is None
                    right_is_none = (
                        isinstance(comparator, ast.Constant) and comparator.value is None
                    )
                    if not left_is_none and not right_is_none:
                        errors.append((lineno, "is/is not: only use with None, use == otherwise"))
                left = comparator

        # mutable default argument
        if isinstance(node, ast.FunctionDef):
            all_defaults = list(node.args.defaults)
            for d in node.args.kw_defaults:
                if d is not None:
                    all_defaults.append(d)
            for default in all_defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    errors.append(
                        (lineno, "mutable default argument: use None and initialize in body")
                    )
                    break

        # __class__ attribute access
        if isinstance(node, ast.Attribute):
            if node.attr == "__class__":
                errors.append((lineno, "__class__: use isinstance() instead"))

    return errors


def main():
    src_dir = "src"
    if len(sys.argv) > 1:
        src_dir = sys.argv[1]

    if not os.path.isdir(src_dir):
        print("Directory not found: " + src_dir)
        sys.exit(1)

    files = find_python_files(src_dir)
    if not files:
        print("No Python files found in: " + src_dir)
        sys.exit(1)

    all_errors = []
    for filepath in files:
        try:
            errors = check_file(filepath)
            for lineno, description in errors:
                all_errors.append((filepath, lineno, description))
        except SyntaxError as e:
            print("Syntax error in " + filepath + ": " + str(e))
            sys.exit(1)

    if not all_errors:
        sys.exit(0)

    print("Found " + str(len(all_errors)) + " banned construction(s):")
    for filepath, lineno, description in sorted(all_errors):
        print("  " + filepath + ":" + str(lineno) + ": " + description)
    sys.exit(1)


if __name__ == "__main__":
    main()
