#!/usr/bin/env python3
"""Compare parser benchmarks between current code and a git ref."""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

BENCH_SCRIPT = Path(__file__).parent.parent / "bench" / "bench_parse.py"
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
PYPERF_DIR = PROJECT_ROOT / ".pyperf"


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
        "--quiet",
    ]
    if fast:
        cmd.append("--fast")
    env = dict(subprocess.os.environ)
    env["PYTHONPATH"] = str(src_dir)
    subprocess.run(cmd, env=env, check=True)


def compare_benchmarks(baseline, current, name1, name2):
    """Compare two benchmark files and print summary."""
    import json

    with open(baseline) as f:
        data1 = json.load(f)
    with open(current) as f:
        data2 = json.load(f)

    # Extract all values from all runs (skip calibration runs without values)
    values1 = []
    for run in data1["benchmarks"][0]["runs"]:
        if "values" in run:
            values1.extend(run["values"])
    values2 = []
    for run in data2["benchmarks"][0]["runs"]:
        if "values" in run:
            values2.extend(run["values"])

    avg1 = sum(values1) / len(values1)
    avg2 = sum(values2) / len(values2)

    ratio = avg2 / avg1
    if ratio < 1:
        pct = (1 - ratio) * 100
        direction = "faster"
    else:
        pct = (ratio - 1) * 100
        direction = "slower"

    print(f"\n{name1}: {avg1 * 1000:.1f} ms")
    print(f"{name2}: {avg2 * 1000:.1f} ms")
    print(f"Result: {name2} is {ratio:.2f}x ({pct:.1f}% {direction})")


def main():
    import argparse
    import tempfile

    parser = argparse.ArgumentParser(description="Compare benchmarks between git refs")
    parser.add_argument("ref1", help="First git ref (SHA, branch, tag)")
    parser.add_argument("ref2", nargs="?", help="Second git ref (default: current working tree)")
    parser.add_argument("--fast", action="store_true", help="Quick run with fewer iterations")
    args = parser.parse_args()

    sha1 = get_short_sha(args.ref1)
    use_current = args.ref2 is None
    sha2 = "current" if use_current else get_short_sha(args.ref2)
    print(f"Comparing {args.ref1} ({sha1}) vs {args.ref2 or 'current'} ({sha2})")

    # Create results directory (use short SHAs for filenames)
    date_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    label1 = sha1
    label2 = sha2
    results_dir = PYPERF_DIR / f"{date_str}_{label1}_vs_{label2}"
    results_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Get first version
        src1 = tmpdir / "src1"
        src1.mkdir(parents=True)
        (src1 / "parable.py").write_text(get_file_at_ref(args.ref1, "src/parable.py"))

        # Get second version
        if use_current:
            src2 = SRC_DIR
        else:
            src2 = tmpdir / "src2"
            src2.mkdir(parents=True)
            (src2 / "parable.py").write_text(get_file_at_ref(args.ref2, "src/parable.py"))

        json1 = results_dir / f"1_{label1}.json"
        json2 = results_dir / f"2_{label2}.json"

        print(f"\n=== Benchmarking {sha1} ===")
        run_benchmark(src1, json1, args.fast)

        print(f"\n=== Benchmarking {sha2} ===")
        run_benchmark(src2, json2, args.fast)

        compare_benchmarks(json1, json2, sha1, sha2)
        print(f"\nResults saved to {results_dir}")


if __name__ == "__main__":
    main()
