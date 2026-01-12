#!/usr/bin/env python3
"""Check for banned Python constructions in parable.py.

Goal: C-style code that translates easily to Go/Rust/JS.

Banned constructions:

    Construction          Example                   Use instead
    --------------------  ------------------------  --------------------------
    ** exponentiation     2 ** 3                    pow() or multiplication
    // floor division     a // b                    int(a / b)
    *args / **kwargs      def f(*args):             explicit parameters
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
    dict comprehension    {k: v for k, v in ...}    explicit loop
    enumerate             for i, x in enumerate()   manual index counter
    generator expression  (x for x in ...)          explicit loop
    global                global x                  pass as parameter
    hasattr               hasattr(x, 'y')           explicit field check
    loop else             for x: ... else:          use flag variable
    list comprehension    [x*2 for x in items]      explicit loop
    match/case            match x:                  if/elif chain
    negative index        lst[-1]                   lst[len(lst)-1]
    nonlocal              nonlocal x                pass as parameter
    or-default            x or []                   if x is None: x = []
    reversed              reversed(lst)             reverse index loop
    set comprehension     {x for x in items}        explicit loop
    step slicing          a[::2], a[1:10:2]         explicit index math
    string multiply       "x" * 3                   loop or helper function
    star unpacking        a, *rest = lst            manual indexing
    try else              try: ... else:            move else code after try block
    tuple unpacking       a, b = b, a               use temp variable
    walrus operator       if (x := foo()):          assign, then test
    with statement        with open(f) as x:        try/finally
    yield                 yield x                   return list or use callback
    yield from            yield from iter           explicit loop
    zip                   for a, b in zip(x, y)     indexed loop
"""

import ast
import os
import sys


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

    for node in ast.walk(tree):
        lineno = getattr(node, "lineno", 0)

        # list/dict/set comprehensions
        if isinstance(node, ast.ListComp):
            errors.append((lineno, "list comprehension: use explicit for loop with append"))
        if isinstance(node, ast.DictComp):
            errors.append((lineno, "dict comprehension: use explicit for loop with assignment"))
        if isinstance(node, ast.SetComp):
            errors.append((lineno, "set comprehension: use explicit for loop with add"))

        # generator expression
        if isinstance(node, ast.GeneratorExp):
            errors.append((lineno, "generator expression: use explicit for loop"))

        # decorator
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.decorator_list:
                errors.append((lineno, "decorator: call wrapper function manually"))

        # walrus operator
        if isinstance(node, ast.NamedExpr):
            errors.append((lineno, "walrus operator :=: assign to variable first, then test"))

        # with statement
        if isinstance(node, ast.With):
            errors.append((lineno, "with statement: use try/finally instead"))

        # *args / **kwargs
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.args.vararg or node.args.kwarg:
                errors.append((lineno, "*args or **kwargs: use explicit parameters"))

        # match/case (Python 3.10+)
        if isinstance(node, ast.Match):
            errors.append((lineno, "match/case: use if/elif chain instead"))

        # tuple unpacking in assignment
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Tuple):
                    errors.append(
                        (lineno, "tuple unpacking: use temp variable and separate assignments")
                    )

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

        # star unpacking in assignment: a, *rest = lst
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Tuple):
                    for elt in target.elts:
                        if isinstance(elt, ast.Starred):
                            errors.append((lineno, "star unpacking: use manual indexing instead"))

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

        # step slicing (basic slicing a[x:y] is allowed, step slicing a[::n] is not)
        if isinstance(node, ast.Subscript):
            if isinstance(node.slice, ast.Slice):
                if node.slice.step is not None:
                    errors.append((lineno, "step slicing: use explicit index math instead"))

        # negative indexing
        if isinstance(node, ast.Subscript):
            if isinstance(node.slice, ast.Constant):
                if isinstance(node.slice.value, int) and node.slice.value < 0:
                    errors.append((lineno, "negative index: use len(x)-n instead"))
            # Also check UnaryOp with USub (e.g., -1 as expression)
            if isinstance(node.slice, ast.UnaryOp):
                if isinstance(node.slice.op, ast.USub):
                    errors.append((lineno, "negative index: use len(x)-n instead"))

        # all()
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "all":
                errors.append((lineno, "all(): use explicit loop with early return"))

        # any()
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "any":
                errors.append((lineno, "any(): use explicit loop with early return"))

        # enumerate()
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "enumerate":
                errors.append((lineno, "enumerate(): use manual index counter"))

        # reversed()
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "reversed":
                errors.append((lineno, "reversed(): use reverse index loop"))

        # zip()
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "zip":
                errors.append((lineno, "zip(): use indexed loop"))

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

        # ** exponentiation
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            errors.append((lineno, "**: use pow() or explicit multiplication"))

        # // floor division
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.FloorDiv):
            errors.append((lineno, "//: use int(a / b) instead"))

        # del statement
        if isinstance(node, ast.Delete):
            errors.append((lineno, "del: reassign or let variable go out of scope"))

        # try...else
        if isinstance(node, ast.Try) and node.orelse:
            errors.append((lineno, "try else: move else code after try block"))

        # string multiplication "x" * n
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
            left_is_str = isinstance(node.left, ast.Constant) and isinstance(node.left.value, str)
            right_is_str = isinstance(node.right, ast.Constant) and isinstance(
                node.right.value, str
            )
            if left_is_str or right_is_str:
                errors.append((lineno, "string * n: use loop or helper function"))

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
