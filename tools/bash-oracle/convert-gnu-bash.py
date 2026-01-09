#!/usr/bin/env python3
"""Convert gnu-bash corpus to .tests format using bash-oracle."""

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
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout.decode("utf-8", errors="replace").strip()
        return None
    except (subprocess.TimeoutExpired, OSError):
        return None


def parse_gnubash_file(content: str) -> list[dict]:
    """Parse the gnu-bash corpus file into test entries."""
    tests = []
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        # Look for separator line
        if lines[i].startswith("=" * 20):
            i += 1
            if i >= len(lines):
                break
            # Next line is test name
            name = lines[i].strip()
            i += 1
            # Skip second separator
            if i < len(lines) and lines[i].startswith("=" * 20):
                i += 1
            # Skip blank lines
            while i < len(lines) and not lines[i].strip():
                i += 1
            # Collect code until (program) marker or next separator
            code_lines = []
            while i < len(lines) and not lines[i].startswith("=" * 20):
                if lines[i].strip() == "(program)":
                    i += 1
                    continue
                code_lines.append(lines[i])
                i += 1
            # Remove trailing blank lines from code
            while code_lines and not code_lines[-1].strip():
                code_lines.pop()
            code = "\n".join(code_lines)
            if code.strip():
                tests.append({"name": name, "code": code})
        else:
            i += 1
    return tests


def convert_file(corpus_path: Path, output_dir: Path, oracle_path: Path) -> tuple[int, int]:
    """Convert the corpus file to .tests format."""
    content = corpus_path.read_text()
    tests = parse_gnubash_file(content)
    output_lines = [f"# Converted from GNU Bash test suite"]
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
            print(f"  FAIL: {test['name']}", file=sys.stderr)
    # Write output
    output_path = output_dir / "tests.tests"
    output_path.write_text("\n".join(output_lines))
    return success, failed


def main():
    script_dir = Path(__file__).parent
    oracle_path = script_dir / "bash-oracle"
    corpus_dir = script_dir.parent.parent / "tests" / "corpus" / "gnu-bash"
    output_dir = corpus_dir
    if not oracle_path.exists():
        print(f"Error: bash-oracle not found at {oracle_path}", file=sys.stderr)
        sys.exit(1)
    corpus_path = corpus_dir / "tests.txt"
    if not corpus_path.exists():
        print(f"No tests.txt found in {corpus_dir}", file=sys.stderr)
        sys.exit(1)
    success, failed = convert_file(corpus_path, output_dir, oracle_path)
    print(f"tests.txt: {success} ok, {failed} failed → tests.tests")
    print(f"\nTotal: {success} converted, {failed} failed")


if __name__ == "__main__":
    main()
