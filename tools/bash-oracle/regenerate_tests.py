#!/usr/bin/env python3
"""Regenerate .tests files using bash-oracle as the source of truth."""

import subprocess
import sys
from pathlib import Path


def get_oracle_output(bash_program: str, oracle_path: Path) -> str | None:
    """Run bash program through oracle and return s-expression output."""
    try:
        result = subprocess.run(
            [str(oracle_path), "--dump-ast"],
            input=bash_program,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, OSError):
        return None


def parse_tests_file(content: str) -> list[dict]:
    """Parse a .tests file into a list of test entries."""
    tests = []
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        # Skip blank lines and comments at top level
        if not line or line.startswith("#"):
            tests.append({"type": "comment", "text": line})
            i += 1
            continue
        # Test header
        if line.startswith("==="):
            name = line
            i += 1
            # Collect bash program until ---
            program_lines = []
            while i < len(lines) and lines[i] != "---":
                program_lines.append(lines[i])
                i += 1
            program = "\n".join(program_lines)
            # Skip ---
            if i < len(lines) and lines[i] == "---":
                i += 1
            # Collect expected output until blank line or next test or comment
            expected_lines = []
            while i < len(lines) and lines[i] and not lines[i].startswith("===") and not lines[i].startswith("#"):
                expected_lines.append(lines[i])
                i += 1
            expected = "\n".join(expected_lines)
            tests.append({
                "type": "test",
                "name": name,
                "program": program,
                "expected": expected,
            })
        else:
            # Unexpected line, preserve it
            tests.append({"type": "comment", "text": line})
            i += 1
    return tests


def regenerate_file(tests_path: Path, oracle_path: Path) -> tuple[int, int, int]:
    """Regenerate a .tests file, return (total, success, failed) counts."""
    content = tests_path.read_text()
    tests = parse_tests_file(content)
    output_lines = []
    total = success = failed = 0
    for entry in tests:
        if entry["type"] == "comment":
            output_lines.append(entry["text"])
        else:
            total += 1
            program = entry["program"]
            oracle_output = get_oracle_output(program, oracle_path)
            if oracle_output is None:
                # Oracle failed, keep original
                print(f"  FAIL: {entry['name'][4:].strip()}", file=sys.stderr)
                failed += 1
                output_lines.append(entry["name"])
                output_lines.append(program)
                output_lines.append("---")
                output_lines.append(entry["expected"])
            else:
                success += 1
                output_lines.append(entry["name"])
                output_lines.append(program)
                output_lines.append("---")
                output_lines.append(oracle_output)
            output_lines.append("")  # blank line between tests
    # Write output
    output_path = tests_path.with_suffix(".tests.ok")
    # Remove trailing blank lines but ensure file ends with newline
    while output_lines and output_lines[-1] == "":
        output_lines.pop()
    output_path.write_text("\n".join(output_lines) + "\n")
    return total, success, failed


def main():
    script_dir = Path(__file__).parent
    oracle_path = script_dir / "bash-oracle"
    tests_dir = script_dir.parent.parent / "tests"
    if not oracle_path.exists():
        print(f"Error: bash-oracle not found at {oracle_path}", file=sys.stderr)
        print("Run 'just build' first", file=sys.stderr)
        sys.exit(1)
    tests_files = sorted(tests_dir.glob("*.tests"))
    if not tests_files:
        print(f"No .tests files found in {tests_dir}", file=sys.stderr)
        sys.exit(1)
    grand_total = grand_success = grand_failed = 0
    for tests_path in tests_files:
        print(f"{tests_path.name}:")
        total, success, failed = regenerate_file(tests_path, oracle_path)
        grand_total += total
        grand_success += success
        grand_failed += failed
        output_path = tests_path.with_suffix(".tests.ok")
        print(f"  {success}/{total} tests → {output_path.name}")
    print()
    print(f"Total: {grand_success}/{grand_total} tests regenerated, {grand_failed} failed")


if __name__ == "__main__":
    main()
