#!/usr/bin/env python3
"""Convert tree-sitter-bash corpus to .tests format using bash-oracle."""

import os
import subprocess
import sys
from pathlib import Path


def get_oracle_output(bash_program: str, oracle_path: Path) -> str | None:
    """Run bash program through oracle and return s-expression output."""
    try:
        result = subprocess.run(
            [str(oracle_path), "--dump-ast"],
            input=bash_program.encode("utf-8", errors="replace"),
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.decode("utf-8", errors="replace").strip()
        return None
    except (subprocess.TimeoutExpired, OSError):
        return None


def parse_treesitter_file(content: str) -> list[dict]:
    """Parse a tree-sitter-bash corpus file into test entries."""
    tests = []
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        # Look for separator line (all = signs)
        if lines[i].startswith("==="):
            i += 1
            if i >= len(lines):
                break
            # Next line is test name
            name = lines[i].strip()
            i += 1
            # Skip second separator
            if i < len(lines) and lines[i].startswith("==="):
                i += 1
            # Skip blank lines
            while i < len(lines) and not lines[i].strip():
                i += 1
            # Collect code until dashed separator
            code_lines = []
            while i < len(lines) and not lines[i].startswith("---"):
                code_lines.append(lines[i])
                i += 1
            # Remove trailing blank lines from code
            while code_lines and not code_lines[-1].strip():
                code_lines.pop()
            code = "\n".join(code_lines)
            if code.strip():
                tests.append({"name": name, "code": code})
            # Skip until next separator
            while i < len(lines) and not lines[i].startswith("==="):
                i += 1
        else:
            i += 1
    return tests


def convert_file(corpus_path: Path, output_dir: Path, oracle_path: Path) -> tuple[int, int]:
    """Convert a single corpus file to .tests format."""
    content = corpus_path.read_text()
    tests = parse_treesitter_file(content)
    output_lines = [f"# Converted from tree-sitter-bash corpus: {corpus_path.name}"]
    output_lines.append("")
    success = 0
    failed = 0
    for test in tests:
        ast = get_oracle_output(test["code"], oracle_path)
        if ast:
            output_lines.append(f"=== {test['name']}")
            output_lines.append(test["code"])
            output_lines.append("---")
            output_lines.append(ast)
            output_lines.append("---")
            output_lines.append("")
            success += 1
        else:
            failed += 1
    # Write output
    output_path = output_dir / corpus_path.name.replace(".txt", ".tests")
    output_path.write_text("\n".join(output_lines))
    return success, failed


def main():
    script_dir = Path(__file__).parent
    _default = Path.home() / "source" / "bash-oracle" / "bash-oracle"
    oracle_path = Path(os.environ.get("BASH_ORACLE") or _default)
    if not oracle_path.exists():
        sys.exit(f"bash-oracle not found at {oracle_path}")
    corpus_dir = script_dir.parent.parent / "tests" / "corpus" / "tree-sitter-bash"
    output_dir = corpus_dir
    corpus_files = sorted(corpus_dir.glob("*.txt"))
    if not corpus_files:
        print(f"No .txt files found in {corpus_dir}", file=sys.stderr)
        sys.exit(1)
    total_success = total_failed = 0
    for corpus_path in corpus_files:
        success, failed = convert_file(corpus_path, output_dir, oracle_path)
        total_success += success
        total_failed += failed
        print(
            f"{corpus_path.name}: {success} ok, {failed} failed → {corpus_path.name.replace('.txt', '.tests')}"
        )
    print(f"\nTotal: {total_success} converted, {total_failed} failed")


if __name__ == "__main__":
    main()
