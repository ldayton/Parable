"""Test runner wrapper with file I/O - not in subset."""
# tongues: skip

import os
import subprocess
import sys
from pathlib import Path


def find_test_files(directory: str) -> list[str]:
    """Find all .tests files recursively."""
    result: list[str] = []
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith(".tests"):
                result.append(os.path.join(root, f))
    result.sort()
    return result


def build_stream(test_files: list[str], base_dir: str) -> str:
    """Build stdin stream with ### FILE: markers."""
    parts: list[str] = []
    for filepath in test_files:
        relpath = os.path.relpath(filepath, base_dir)
        content = Path(filepath).read_text()
        parts.append(f"### FILE: {relpath}")
        parts.append(content)
    return "\n".join(parts)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: run-testsw.py <tests_directory>", file=sys.stderr)
        return 1

    tests_dir = sys.argv[1]
    if not os.path.isdir(tests_dir):
        print(f"Error: {tests_dir} is not a directory", file=sys.stderr)
        return 1

    script_dir = os.path.dirname(os.path.abspath(__file__))
    runner = os.path.join(script_dir, "run_tests.py")
    repo_root = os.path.dirname(script_dir)

    test_files = find_test_files(tests_dir)
    if len(test_files) == 0:
        print(f"No .tests files found in {tests_dir}", file=sys.stderr)
        return 1

    stream = build_stream(test_files, tests_dir)

    env = os.environ.copy()
    env["PYTHONPATH"] = repo_root
    result = subprocess.run(
        ["python3", runner],
        input=stream,
        text=True,
        cwd=repo_root,
        env=env,
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
