#!/usr/bin/env python3
"""Convert Oils corpus to .tests format using bash-oracle."""

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


def parse_oils_file(content: str) -> list[dict]:
    """Parse an Oils corpus file into test entries."""
    tests = []
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        # Look for separator line
        if lines[i].startswith("=" * 20):
            i += 1
            if i >= len(lines):
                break
            # Next line is "filename: test name"
            header = lines[i]
            if ":" in header:
                name = header.split(":", 1)[1].strip()
            else:
                name = header.strip()
            i += 1
            # Skip second separator
            if i < len(lines) and lines[i].startswith("=" * 20):
                i += 1
            # Skip blank lines
            while i < len(lines) and not lines[i].strip():
                i += 1
            # Collect code until dashed separator
            code_lines = []
            while i < len(lines) and not lines[i].startswith("-" * 20):
                code_lines.append(lines[i])
                i += 1
            # Remove trailing blank lines from code
            while code_lines and not code_lines[-1].strip():
                code_lines.pop()
            code = "\n".join(code_lines)
            if code.strip():
                tests.append({"name": name, "code": code})
            # Skip dashed separator and everything until next test
            while i < len(lines) and not lines[i].startswith("=" * 20):
                i += 1
        else:
            i += 1
    return tests


def convert_file(corpus_path: Path, output_dir: Path, oracle_path: Path) -> tuple[int, int]:
    """Convert a single corpus file to .tests format."""
    content = corpus_path.read_text()
    tests = parse_oils_file(content)
    output_lines = [f"# Converted from Oils corpus: {corpus_path.name}"]
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
    oracle_path = Path.home() / "source" / "bash-oracle" / "bash-oracle"
    corpus_dir = script_dir.parent.parent / "tests" / "corpus" / "oils"
    output_dir = corpus_dir
    if not oracle_path.exists():
        print(f"Error: bash-oracle not found at {oracle_path}", file=sys.stderr)
        sys.exit(1)
    corpus_files = sorted(corpus_dir.glob("*.txt"))
    if not corpus_files:
        print(f"No .txt files found in {corpus_dir}", file=sys.stderr)
        sys.exit(1)
    total_success = total_failed = 0
    for corpus_path in corpus_files:
        if corpus_path.name == "ORIGIN.md":
            continue
        success, failed = convert_file(corpus_path, output_dir, oracle_path)
        total_success += success
        total_failed += failed
        print(
            f"{corpus_path.name}: {success} ok, {failed} failed → {corpus_path.name.replace('.txt', '.tests')}"
        )
    print(f"\nTotal: {total_success} converted, {total_failed} failed")


if __name__ == "__main__":
    main()
