"""CLI wrapper with file I/O - not in subset, delegates to cli.py."""
# tongues: skip

from __future__ import annotations

import os
import sys

from .tongues import parse_args, run_verify_stdin, run_transpile
from .frontend.parse import parse
from .frontend.subset import (
    verify as verify_subset,
    extract_imports,
    ImportInfo,
    ProjectVerifyResult,
    VerifyResult,
)


def should_skip_file(source: str) -> bool:
    """Check if file has a tongues: skip directive in first 5 lines."""
    lines = source.split("\n", 5)
    for line in lines[:5]:
        if "tongues: skip" in line:
            return True
    return False


def resolve_import(
    importing_file: str, module: str, level: int, project_root: str
) -> str | None:
    """Resolve an import to a file path."""
    if level > 0:
        dir_path = os.path.dirname(importing_file)
        up = level - 1
        while up > 0:
            dir_path = os.path.dirname(dir_path)
            up -= 1
        if module:
            parts = module.split(".")
            rel_path = os.path.join(dir_path, *parts)
        else:
            rel_path = dir_path
    else:
        parts = module.split(".")
        rel_path = os.path.join(project_root, *parts)
    init_path = os.path.join(rel_path, "__init__.py")
    if os.path.isfile(init_path):
        return init_path
    module_path = rel_path + ".py"
    if os.path.isfile(module_path):
        return module_path
    return None


def verify_project(path: str) -> ProjectVerifyResult:
    """Verify a project directory or single file."""
    result = ProjectVerifyResult()

    if os.path.isfile(path):
        with open(path, "r") as f:
            source = f.read()
        if should_skip_file(source):
            return result
        ast_dict = parse(source)
        result.file_results[path] = verify_subset(ast_dict)
        return result

    project_root = path
    pending: list[str] = []
    visited: set[str] = set()

    entries = os.listdir(project_root)
    for entry in entries:
        if entry.endswith(".py"):
            full_path = os.path.join(project_root, entry)
            if os.path.isfile(full_path):
                pending.append(full_path)

    while len(pending) > 0:
        file_path = pending.pop()
        if file_path in visited:
            continue
        visited.add(file_path)

        with open(file_path, "r") as f:
            source = f.read()
        if should_skip_file(source):
            continue
        ast_dict = parse(source)
        result.file_results[file_path] = verify_subset(ast_dict)

        imports = extract_imports(ast_dict)
        for imp in imports:
            if imp.level == 0:
                continue
            resolved = resolve_import(file_path, imp.module, imp.level, project_root)
            if resolved is not None and resolved not in visited:
                pending.append(resolved)

    return result


def main() -> int:
    """Main entry point with file I/O support."""
    target, verify, verify_path = parse_args()

    if verify:
        if verify_path is not None:
            result = verify_project(verify_path)
            errors = result.errors()
            if len(errors) > 0:
                for e in errors:
                    print(e, file=sys.stderr)
                return 1
            return 0
        return run_verify_stdin()

    return run_transpile(target)


if __name__ == "__main__":
    sys.exit(main())
