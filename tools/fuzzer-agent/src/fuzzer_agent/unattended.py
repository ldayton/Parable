"""Unattended loop runner for fuzzer-agent."""

import argparse
import os
import select
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
MIN_RUN_SECONDS = 120
MAX_RUN_SECONDS = 1800
INITIAL_BACKOFF = 30
MAX_BACKOFF = 600


def _print_banner(text: str) -> None:
    """Print a very prominent banner."""
    width = max(len(text) + 4, 60)
    border = "█" * width
    padding = "█" + " " * (width - 2) + "█"
    centered = "█ " + text.center(width - 4) + " █"
    print(f"\n{border}\n{padding}\n{centered}\n{padding}\n{border}\n", flush=True)


def _format_duration(seconds: float) -> str:
    """Format duration as human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    if minutes < 60:
        return f"{minutes}m {secs:.0f}s"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"


def run(max_iterations: int | None = None) -> int:
    """Run fuzzer-agent in unattended loop mode."""
    iteration = 0
    successes = 0
    failures = 0
    backoff = INITIAL_BACKOFF
    total_start = time.time()
    while max_iterations is None or iteration < max_iterations:
        iteration += 1
        iter_str = f"{iteration}" if max_iterations is None else f"{iteration}/{max_iterations}"
        _print_banner(f"ITERATION {iter_str}  |  OK: {successes}  FAIL: {failures}")
        print(f"Total runtime: {_format_duration(time.time() - total_start)}", flush=True)
        print(f"Current backoff: {backoff}s\n", flush=True)
        # Create workdir and clone
        workdir = tempfile.mkdtemp(prefix="fuzzer-agent-")
        clone_target = Path(workdir) / "Parable"
        print(f"Cloning into {clone_target}...", flush=True)
        clone_result = subprocess.run(
            ["git", "clone", "--depth=1", str(REPO_ROOT), str(clone_target)],
            capture_output=True,
            text=True,
        )
        if clone_result.returncode != 0:
            print(f"Clone failed: {clone_result.stderr}", flush=True)
            failures += 1
            time.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF)
            continue
        # Create TMPDIR for the subprocess
        agent_tmpdir = tempfile.mkdtemp(prefix="fuzzer-tmp-")
        agent_dir = clone_target / "tools" / "fuzzer-agent"
        env = os.environ.copy()
        env["TMPDIR"] = agent_tmpdir
        env["PYTHONUNBUFFERED"] = "1"
        print(f"TMPDIR={agent_tmpdir}", flush=True)
        print(f"Running fuzzer-agent --claude (timeout: {MAX_RUN_SECONDS}s)...\n", flush=True)
        run_start = time.time()
        proc = subprocess.Popen(
            ["uv", "run", "fuzzer-agent", "--claude"],
            cwd=str(agent_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        timed_out = False
        while True:
            remaining = MAX_RUN_SECONDS - (time.time() - run_start)
            if remaining <= 0:
                print("\n*** TIMEOUT ***", flush=True)
                proc.kill()
                proc.wait()
                timed_out = True
                break
            # Wait for output with timeout
            ready, _, _ = select.select([proc.stdout], [], [], min(remaining, 1.0))
            if ready:
                line = proc.stdout.readline()
                if not line and proc.poll() is not None:
                    break
                if line:
                    print(line, end="", flush=True)
            elif proc.poll() is not None:
                break
        exit_code = 2 if timed_out else proc.returncode
        run_duration = time.time() - run_start
        # Determine success/failure
        too_fast = run_duration < MIN_RUN_SECONDS
        failed = exit_code == 2 or too_fast
        status = "FAILURE" if failed else ("NO BUGS" if exit_code == 1 else "SUCCESS")
        if too_fast:
            status += f" (too fast: {run_duration:.1f}s < {MIN_RUN_SECONDS}s)"
        _print_banner(f"RESULT: {status}")
        print(f"Exit code: {exit_code}", flush=True)
        print(f"Duration: {_format_duration(run_duration)}", flush=True)
        if failed:
            failures += 1
            print(f"Backing off for {backoff}s...", flush=True)
            time.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF)
        else:
            successes += 1
            backoff = INITIAL_BACKOFF
        print(f"\nStats: {successes} successes, {failures} failures", flush=True)
    # Finished all iterations
    _print_banner("COMPLETE")
    print(f"Total iterations: {iteration}", flush=True)
    print(f"Successes: {successes}", flush=True)
    print(f"Failures: {failures}", flush=True)
    print(f"Total runtime: {_format_duration(time.time() - total_start)}", flush=True)
    return 0 if failures == 0 else 2


def main():
    parser = argparse.ArgumentParser(description="Run fuzzer-agent in unattended loop mode")
    parser.add_argument(
        "--max-iterations",
        type=int,
        metavar="N",
        help="Maximum iterations (default: unlimited)",
    )
    args = parser.parse_args()
    sys.exit(run(max_iterations=args.max_iterations))


if __name__ == "__main__":
    main()
