#!/usr/bin/env python3
"""Benchmark run_oracle performance: -e flag vs temp file approaches.

Run after bash-oracle -e bug is fixed to verify speed improvements.

Usage:
    # On main (temp file baseline):
    git checkout main
    uv run --directory tools/fuzzer python tools/fuzzer/tests/benchmark_oracle.py

    # On branch (with -e optimization):
    git checkout perf/oracle-inline-arg
    uv run --directory tools/fuzzer python tools/fuzzer/tests/benchmark_oracle.py

Expected result: -e approach should be ~10-20% faster due to eliminated
filesystem I/O (no temp file create/write/unlink per call).
"""

import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from fuzzer.common import ORACLE_PATH, REPO_ROOT, find_test_files, parse_test_file


def load_test_inputs(limit=500):
    """Load a sample of test inputs."""
    test_files = find_test_files(REPO_ROOT / "tests")
    inputs = []
    for f in test_files:
        inputs.extend(parse_test_file(f))
        if len(inputs) >= limit:
            break
    return inputs[:limit]


def benchmark_e_flag(inputs, iterations=3):
    """Benchmark -e flag approach."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        for inp in inputs:
            try:
                subprocess.run(
                    [str(ORACLE_PATH), "-e", inp],
                    capture_output=True,
                    timeout=0.5,
                )
            except (subprocess.TimeoutExpired, ValueError):
                pass
        times.append(time.perf_counter() - start)
    return times


def benchmark_temp_file(inputs, iterations=3):
    """Benchmark temp file approach."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        for inp in inputs:
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".sh", delete=False
                ) as f:
                    f.write(inp)
                    tmp = Path(f.name)
                subprocess.run(
                    [str(ORACLE_PATH), str(tmp)],
                    capture_output=True,
                    timeout=0.5,
                )
                tmp.unlink()
            except subprocess.TimeoutExpired:
                tmp.unlink(missing_ok=True)
        times.append(time.perf_counter() - start)
    return times


def main():
    print("Loading test inputs...")
    inputs = load_test_inputs(500)
    print(f"Loaded {len(inputs)} inputs\n")

    print("Benchmarking -e flag approach (3 iterations)...")
    e_times = benchmark_e_flag(inputs)
    
    print("Benchmarking temp file approach (3 iterations)...")
    file_times = benchmark_temp_file(inputs)

    print("\n" + "=" * 50)
    print("Results:")
    print(f"  -e flag:    {statistics.mean(e_times):.3f}s "
          f"(±{statistics.stdev(e_times):.3f}s) "
          f"= {len(inputs)/statistics.mean(e_times):.1f} calls/s")
    print(f"  temp file:  {statistics.mean(file_times):.3f}s "
          f"(±{statistics.stdev(file_times):.3f}s) "
          f"= {len(inputs)/statistics.mean(file_times):.1f} calls/s")
    
    speedup = statistics.mean(file_times) / statistics.mean(e_times)
    print(f"\nSpeedup: {speedup:.2f}x ({(speedup - 1) * 100:+.1f}%)")
    
    if speedup > 1.05:
        print("✓ -e flag is faster (as expected)")
    elif speedup < 0.95:
        print("✗ -e flag is slower (unexpected - check for issues)")
    else:
        print("≈ No significant difference")


if __name__ == "__main__":
    main()
