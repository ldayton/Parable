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
README = PROJECT_ROOT / "README.md"


def get_banner():
    """Extract banner from README.md between <pre> tags."""
    import re

    text = README.read_text()
    match = re.search(r"<pre>\n(.*?)</pre>", text, re.DOTALL)
    if match:
        banner = match.group(1)
        banner = re.sub(r"<[^>]+>", "", banner)  # strip HTML tags
        return banner
    return ""


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


def get_commit_message(ref):
    """Get first line of commit message for a ref."""
    return run(["git", "-C", str(PROJECT_ROOT), "log", "-1", "--format=%s", ref]).strip()


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
    subprocess.run(cmd, env=env, check=True, stdout=subprocess.DEVNULL)


def compare_benchmarks(baseline, current, name1, name2, msg1="", msg2=""):
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

    label1 = f"{name1} {msg1}" if msg1 else name1
    label2 = f"{name2} {msg2}" if msg2 else name2
    time1 = f"{avg1 * 1000:.1f} ms"
    time2 = f"{avg2 * 1000:.1f} ms"
    check1 = " ✓" if avg1 < avg2 else ""
    check2 = " ✓" if avg2 < avg1 else ""
    label_width = max(len(label1), len(label2))
    print(f"\n{label1:<{label_width}}  {time1:>10}{check1}")
    print(f"{label2:<{label_width}}  {time2:>10}{check2}")
    if avg1 < avg2:
        winner, loser, pct = label1, label2, (avg2 - avg1) / avg2 * 100
    else:
        winner, loser, pct = label2, label1, (avg1 - avg2) / avg1 * 100
    print(f"\nWINNER: {winner}")
    print(f"{pct:.1f}% faster than {loser}")


def main():
    import argparse
    import tempfile

    print(get_banner())
    print("Benchmarking parable.py\n")
    parser = argparse.ArgumentParser(description="Compare benchmarks between git refs")
    parser.add_argument("ref1", help="First git ref (SHA, branch, tag)")
    parser.add_argument("ref2", nargs="?", help="Second git ref (default: current working tree)")
    parser.add_argument("--fast", action="store_true", help="Quick run with fewer iterations")
    args = parser.parse_args()

    sha1 = get_short_sha(args.ref1)
    raw_msg1 = get_commit_message(args.ref1)
    msg1 = f'"{raw_msg1[:40]}{"..." if len(raw_msg1) > 40 else ""}"'
    use_current = args.ref2 is None
    sha2 = "current" if use_current else get_short_sha(args.ref2)
    if use_current:
        msg2 = ""
    else:
        raw_msg2 = get_commit_message(args.ref2)
        msg2 = f'"{raw_msg2[:40]}{"..." if len(raw_msg2) > 40 else ""}"'
    sha_width = max(len(sha1), len(sha2))
    print(f"Comparing {sha1:<{sha_width}} {msg1}")
    print(f"       vs {sha2:<{sha_width}} {msg2 if msg2 else '(working tree)'}")

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

        print(f"\n=== Benchmarking {sha1} {msg1} ===")
        run_benchmark(src1, json1, args.fast)

        print(f"\n=== Benchmarking {sha2} {msg2} ===")
        run_benchmark(src2, json2, args.fast)

        compare_benchmarks(json1, json2, sha1, sha2, msg1, msg2)
        print(f"\nResults saved to {results_dir}")


if __name__ == "__main__":
    main()
