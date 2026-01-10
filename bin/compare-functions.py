#!/usr/bin/env python3
# /// script
# dependencies = ["esprima"]
# ///
"""Compare function definitions between Python and JavaScript parsers."""

import ast
import sys
from pathlib import Path

import esprima


def snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    parts = name.split('_')
    if not parts:
        return name
    leading = ''
    while parts and parts[0] == '':
        leading += '_'
        parts = parts[1:]
    if not parts:
        return leading
    result = parts[0]
    for part in parts[1:]:
        if part:
            result += part[0].upper() + part[1:]
    return leading + result


def extract_python_functions(path: Path) -> dict[str, tuple[int, int]]:
    """Extract function/method names, line numbers, and lengths from Python file."""
    content = path.read_text()
    tree = ast.parse(content)
    functions = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            start = node.lineno
            end = node.end_lineno
            length = end - start + 1
            functions[node.name] = (start, length)
    return functions


def extract_js_functions(path: Path) -> dict[str, tuple[int, int]]:
    """Extract function/method names, line numbers, and lengths from JavaScript file."""
    content = path.read_text()
    tree = esprima.parseScript(content, loc=True)
    functions = {}

    def visit(node):
        if node is None:
            return
        if isinstance(node, list):
            for item in node:
                visit(item)
            return
        if not hasattr(node, 'type'):
            return
        # Function declaration: function foo() {}
        if node.type == 'FunctionDeclaration' and node.id:
            name = node.id.name
            start = node.loc.start.line
            end = node.loc.end.line
            functions[name] = (start, end - start + 1)
        # Method definition: foo() {} inside a class
        elif node.type == 'MethodDefinition' and node.key:
            name = node.key.name if hasattr(node.key, 'name') else str(node.key.value)
            start = node.loc.start.line
            end = node.loc.end.line
            functions[name] = (start, end - start + 1)
        # Recurse into child nodes
        for key in dir(node):
            if key.startswith('_'):
                continue
            val = getattr(node, key)
            if isinstance(val, list):
                for item in val:
                    visit(item)
            elif hasattr(val, 'type'):
                visit(val)

    visit(tree)
    return functions


def main():
    sort_by_delta = '--delta' in sys.argv

    root = Path(__file__).parent.parent
    py_path = root / 'src' / 'parable.py'
    js_path = root / 'src' / 'parable.js'

    py_funcs = extract_python_functions(py_path)
    js_funcs = extract_js_functions(js_path)

    # Build mapping
    rows = []
    for py_name, (py_line, py_len) in py_funcs.items():
        js_name = snake_to_camel(py_name)
        if js_name in js_funcs:
            js_line, js_len = js_funcs[js_name]
            delta = js_len - py_len
            rows.append((py_name, py_line, py_len, js_line, js_len, delta))
        else:
            rows.append((py_name, py_line, py_len, '-', '-', None))

    if sort_by_delta:
        rows.sort(key=lambda x: (x[5] is None, -abs(x[5]) if x[5] is not None else 0))
    else:
        rows.sort(key=lambda x: x[1])

    # Find JS functions not in Python
    py_names_as_camel = {snake_to_camel(n) for n in py_funcs}
    js_only = [(n, l, ln) for n, (l, ln) in js_funcs.items() if n not in py_names_as_camel]

    # Print table
    print(f"{'Python Function':<45} {'Py Line':>8} {'JS Line':>8} {'Py Len':>7} {'JS Len':>7} {'Delta':>7}")
    print('-' * 85)
    for py_name, py_line, py_len, js_line, js_len, delta in rows:
        delta_str = '-' if delta is None else delta
        print(f"{py_name:<45} {py_line:>8} {js_line:>8} {py_len:>7} {js_len:>7} {delta_str:>7}")

    if js_only:
        print()
        print("JS-only functions:")
        print('-' * 50)
        for name, line, length in sorted(js_only, key=lambda x: x[1]):
            print(f"  {name:<35} {line:>8} {length:>7}")


if __name__ == '__main__':
    main()
