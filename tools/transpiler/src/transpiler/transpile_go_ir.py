#!/usr/bin/env python3
"""Transpile parable.py to Go using the new IR-based pipeline.

Architecture:
    parable.py -> [Python AST] -> Frontend -> [IR] -> GoBackend -> Go code
"""

import ast
import shutil
import subprocess
import sys
from pathlib import Path

from .backend_go import GoBackend
from .frontend import Frontend


def transpile_go_ir(source: str) -> str:
    """Transpile Python source to Go using the IR pipeline."""
    fe = Frontend()
    module = fe.transpile(source)
    # Now rebuild with full bodies
    tree = ast.parse(source)
    _rebuild_with_bodies(fe, module, tree)
    be = GoBackend()
    return be.emit(module)


def _rebuild_with_bodies(fe: Frontend, module, tree: ast.Module) -> None:
    """Rebuild module with fully lowered function bodies."""
    # Rebuild functions with bodies
    new_functions = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            func = fe._build_function_shell(node, with_body=True)
            new_functions.append(func)
    module.functions = new_functions
    # Rebuild struct methods with bodies
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for struct in module.structs:
                if struct.name == node.name:
                    new_methods = []
                    for stmt in node.body:
                        if isinstance(stmt, ast.FunctionDef) and stmt.name != "__init__":
                            method = fe._build_method_shell(stmt, node.name, with_body=True)
                            new_methods.append(method)
                    struct.methods = new_methods
                    break


def main():
    if len(sys.argv) < 2:
        print("Usage: transpiler --transpile-go-ir <input.py>", file=sys.stderr)
        sys.exit(1)
    source = Path(sys.argv[1]).read_text()
    code = transpile_go_ir(source)
    if shutil.which("goimports"):
        result = subprocess.run(["goimports"], input=code, capture_output=True, text=True)
        if result.returncode == 0:
            code = result.stdout
        else:
            print(f"goimports failed: {result.stderr}", file=sys.stderr)
    print(code)


if __name__ == "__main__":
    main()
