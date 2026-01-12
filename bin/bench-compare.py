#!/usr/bin/env python3
"""Compare parser benchmarks between current code and a git ref."""

import subprocess
import sys
import tempfile
from pathlib import Path

BENCH_SCRIPT = Path(__file__).parent.parent / "bench" / "bench_parse.py"
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"


def run(cmd, **kwargs):
    """Run a command and return output."""
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        print(f"Error running {cmd}:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout


def get_short_sha(ref):
    """Get short SHA for a ref."""
    return run(["git", "-C", str(PROJECT_ROOT), "rev-parse", "--short", ref]).strip()


def get_file_at_ref(ref, path):
    """Get file contents at a git ref."""
    return run(["git", "-C", str(PROJECT_ROOT), "show", f"{ref}:{path}"])


def run_benchmark(src_dir, output_file, fast=False):
    """Run benchmark with given src directory."""
    cmd = [
        sys.executable,
        str(BENCH_SCRIPT),
        "--output",
        str(output_file),
    ]
    if fast:
        cmd.append("--fast")
    env = dict(subprocess.os.environ)
    env["PYTHONPATH"] = str(src_dir)
    subprocess.run(cmd, env=env, check=True)


def compare_benchmarks(baseline, current):
    """Compare two benchmark files using pyperf."""
    subprocess.run(
        [sys.executable, "-m", "pyperf", "compare_to", str(baseline), str(current), "--table"],
        check=True,
    )


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Compare benchmarks against a git ref")
    parser.add_argument("ref", help="Git ref to compare against (SHA, branch, tag)")
    parser.add_argument("--fast", action="store_true", help="Quick run with fewer iterations")
    args = parser.parse_args()

    ref = args.ref
    short_sha = get_short_sha(ref)
    print(f"Comparing current code against {ref} ({short_sha})")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Get old parable.py
        old_src = tmpdir / "old"
        old_src.mkdir(parents=True)
        old_content = get_file_at_ref(ref, "src/parable.py")
        (old_src / "parable.py").write_text(old_content)

        baseline_json = tmpdir / "baseline.json"
        current_json = tmpdir / "current.json"

        # Benchmark old version
        print(f"\n=== Benchmarking {short_sha} ===")
        run_benchmark(old_src, baseline_json, args.fast)

        # Benchmark current version
        print("\n=== Benchmarking current ===")
        run_benchmark(SRC_DIR, current_json, args.fast)

        # Compare
        print(f"\n=== Comparison ({short_sha} vs current) ===")
        compare_benchmarks(baseline_json, current_json)


if __name__ == "__main__":
    main()
