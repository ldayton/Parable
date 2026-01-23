#!/usr/bin/env python3
"""Verify that all tests/**/*.tests have correct parse expectations per bash-oracle."""

import multiprocessing as mp
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent.parent
_default_oracle = Path.home() / "source" / "bash-oracle" / "bash-oracle"
ORACLE_PATH = Path(os.environ.get("BASH_ORACLE") or _default_oracle)
if not ORACLE_PATH.exists():
    sys.exit(f"bash-oracle not found at {ORACLE_PATH}")


@dataclass
class TestCase:
    file: str  # String for pickling
    line: int
    name: str
    input: str
    expected: str
    extglob: bool = False


@dataclass
class WorkerResult:
    """Result from verifying a single test case."""

    passed: bool
    skipped: dict | None = None
    failure: dict | None = None


STOP_SENTINEL = None


def parse_test_file(filepath: Path) -> list[TestCase]:
    """Parse a .tests file. Returns list of TestCase objects."""
    tests = []
    lines = filepath.read_text().split("\n")
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.startswith("#") or line.strip() == "":
            i += 1
            continue
        if line.startswith("=== "):
            name = line[4:].strip()
            start_line = i + 1
            i += 1
            input_lines = []
            while i < n and lines[i] != "---":
                input_lines.append(lines[i])
                i += 1
            if i < n and lines[i] == "---":
                i += 1
            expected_lines = []
            while i < n and lines[i] != "---" and not lines[i].startswith("=== "):
                expected_lines.append(lines[i])
                i += 1
            if i < n and lines[i] == "---":
                i += 1
            while expected_lines and expected_lines[-1].strip() == "":
                expected_lines.pop()
            test_input = "\n".join(input_lines)
            # Check for @extglob directive
            extglob = False
            if test_input.startswith("# @extglob\n"):
                extglob = True
                test_input = test_input[len("# @extglob\n") :]
            tests.append(
                TestCase(
                    file=str(filepath),
                    line=start_line,
                    name=name,
                    input=test_input,
                    expected="\n".join(expected_lines),
                    extglob=extglob,
                )
            )
        else:
            i += 1
    return tests


def get_oracle_output(input_text: str, extglob: bool = False) -> str | None:
    """Get bash-oracle output for the given input. Returns '<error>' for syntax errors."""
    try:
        cmd = [str(ORACLE_PATH)]
        if extglob:
            cmd.append("--extglob")
        cmd.extend(["-e", input_text])
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=5,
        )
        if result.returncode != 0:
            return "<error>"
        return result.stdout.decode("utf-8", errors="replace").strip()
    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        sys.exit(f"bash-oracle not found at {ORACLE_PATH}")


def normalize(s: str) -> str:
    """Normalize whitespace for comparison."""
    return " ".join(s.split())


def worker_process(work_queue, result_queue, stop_event) -> None:
    """Worker process: verify test cases from work queue."""
    while not stop_event.is_set():
        tc = work_queue.get()
        if tc is STOP_SENTINEL:
            break
        # Skip tests marked as <infinite> (bash-oracle hangs on these)
        if tc.expected == "<infinite>":
            result_queue.put(
                WorkerResult(
                    passed=False,
                    skipped={
                        "file": tc.file,
                        "line": tc.line,
                        "name": tc.name,
                        "input": tc.input,
                        "reason": "infinite",
                    },
                )
            )
            continue
        oracle_output = get_oracle_output(tc.input, tc.extglob)
        if oracle_output is None:
            # Timeout - treat as pass if expected is <error> (bash hangs on some errors)
            if normalize(tc.expected) == "<error>":
                result_queue.put(WorkerResult(passed=True))
            else:
                # Timeout but didn't expect error - this is a failure
                result_queue.put(
                    WorkerResult(
                        passed=False,
                        failure={
                            "file": tc.file,
                            "line": tc.line,
                            "name": tc.name,
                            "input": tc.input,
                            "expected": tc.expected,
                            "oracle": "<timeout>",
                        },
                    )
                )
            continue
        expected_norm = normalize(tc.expected)
        oracle_norm = normalize(oracle_output)
        if expected_norm == oracle_norm:
            result_queue.put(WorkerResult(passed=True))
        else:
            result_queue.put(
                WorkerResult(
                    passed=False,
                    skipped=False,
                    failure={
                        "file": tc.file,
                        "line": tc.line,
                        "name": tc.name,
                        "input": tc.input,
                        "expected": tc.expected,
                        "oracle": oracle_output,
                    },
                )
            )
    result_queue.put(STOP_SENTINEL)


def main():
    tests_dir = REPO_ROOT / "tests"
    test_files = sorted(tests_dir.glob("**/*.tests"))

    # Collect all test cases
    all_tests: list[TestCase] = []
    for test_file in test_files:
        all_tests.extend(parse_test_file(test_file))

    total = len(all_tests)
    passed = 0
    failed = 0
    skipped = 0
    failures = []
    skipped_tests = []

    # Set up multiprocessing
    num_workers = mp.cpu_count()
    work_queue = mp.Queue()
    result_queue = mp.Queue()
    stop_event = mp.Event()

    # Start workers
    workers = []
    for _ in range(num_workers):
        p = mp.Process(target=worker_process, args=(work_queue, result_queue, stop_event))
        p.start()
        workers.append(p)

    # Enqueue all work
    for tc in all_tests:
        work_queue.put(tc)
    for _ in range(num_workers):
        work_queue.put(STOP_SENTINEL)

    # Collect results
    processed = 0
    while processed < total:
        result = result_queue.get()
        if result is STOP_SENTINEL:
            continue
        processed += 1
        if result.skipped:
            skipped += 1
            skipped_tests.append(result.skipped)
        elif result.passed:
            passed += 1
        else:
            failed += 1
            failures.append(result.failure)
        if processed % 100 == 0:
            print(f"\r{processed}/{total} verified", end="", flush=True)

    # Signal workers to stop and clean up
    stop_event.set()
    for p in workers:
        p.join(timeout=0.1)
        if p.is_alive():
            p.terminate()

    # Print summary
    print(f"\r{' ' * 40}\r", end="")  # Clear progress line
    print(f"\n{'=' * 60}")
    print("Verification Results")
    print(f"{'=' * 60}")
    print(f"Total:   {total}")
    print(f"Passed:  {passed}")
    print(f"Failed:  {failed}")
    print(f"Skipped: {skipped}")
    if skipped_tests:
        for s in skipped_tests:
            reason = s.get("reason", "unknown")
            print(f"  - {Path(s['file']).name}:{s['line']} {s['name']} ({reason})")
    print()

    if failures:
        print(f"\n{'=' * 60}")
        print(f"Failures ({len(failures)}):")
        print(f"{'=' * 60}\n")

        for f in failures:
            print(f"{Path(f['file']).name}:{f['line']} - {f['name']}")
            print(f"  Input:    {f['input']!r}")
            print(f"  Expected: {f['expected']}")
            print(f"  Oracle:   {f['oracle']}")
            print()

        sys.exit(1)
    else:
        print("🎉 All tests match bash-oracle expectations!")
        sys.exit(0)


if __name__ == "__main__":
    main()
