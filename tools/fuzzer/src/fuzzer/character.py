#!/usr/bin/env python3
"""Corpus mutation fuzzer for differential testing.

Mutates inputs from the test corpus (tests/**/*.tests) and compares Parable's
parse results against bash-oracle to find discrepancies.

Uses loky for robust, deadlock-free multiprocessing with bounded parallelism.
"""

from __future__ import annotations

import argparse
import os
import random
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from loky import get_reusable_executor

from .common import (
    ORACLE_PATH,
    REPO_ROOT,
    Discrepancy,
    find_test_files,
    normalize,
    parse_layer_spec,
    parse_test_file,
    run_oracle,
    run_parable,
)
from .generator import detect_layer
from .minimize import minimize as minimize_input

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------


@dataclass(frozen=True)
class FuzzerConfig:
    """Immutable fuzzer configuration."""

    inputs: tuple[str, ...]
    mutations_per_input: int = 2
    seed: int | None = None
    minimize: bool = False
    filter_layer: int | None = None
    both_succeed: bool = False
    stop_after: int | None = None
    max_iterations: int | None = None
    batch_size: int = 100
    verbose: bool = False
    output_path: Path | None = None
    max_workers: int = 4  # Limit concurrent processes to prevent contention

    @property
    def should_minimize(self) -> bool:
        return self.minimize or self.filter_layer is not None


# ------------------------------------------------------------------------------
# Statistics
# ------------------------------------------------------------------------------


@dataclass
class FuzzerStats:
    """Mutable fuzzer statistics."""

    iterations: int = 0
    raw_discrepancies: int = 0
    survived_minimize: int = 0
    passed_filter: int = 0
    duplicates_skipped: int = 0
    start_time: float = field(default_factory=lambda: __import__("time").time())

    def status_line(self, config: FuzzerConfig) -> str:
        import time

        elapsed = time.time() - self.start_time
        rate = self.iterations / elapsed if elapsed > 0 else 0
        if config.max_iterations:
            s = f"{self.iterations}/{config.max_iterations} iterations"
        else:
            s = f"{self.iterations} iterations"
        s += f" ({rate:.1f}/s)"
        if config.should_minimize:
            s += f", {self.raw_discrepancies} found"
            s += f", {self.survived_minimize} minimized"
            s += f", {self.passed_filter} pass filter"
        else:
            s += f", {self.passed_filter} unique"
        return s


# ------------------------------------------------------------------------------
# Mutation logic
# ------------------------------------------------------------------------------

MUTATION_GROUPS = list("${}()|&<>;\"'\\` \t\n@#![]:=*?~/+-,%^") + ["0123456789"]
INSERTION_PATTERNS = [
    "$(",
    "${",
    "<(",
    ">(",
    "((",
    "<<",  # openers
    "))",
    "}}",  # closers
    ">&",
    "2>",
    "|&",  # redirects
    "||",
    "&&",  # logical
    "$((",
    "<<<",  # arithmetic, herestring
]
DELETION_PATTERNS = ["$(", "${", "<(", ">(", "((", "<<", "))", "}}", "||", "&&"]


def pick_mutation_char() -> str:
    group = random.choice(MUTATION_GROUPS)
    return random.choice(group) if len(group) > 1 else group


def pick_insertion() -> str:
    if random.random() < 0.2:
        return random.choice(INSERTION_PATTERNS)
    return pick_mutation_char()


def mutate(s: str, num_mutations: int = 1) -> tuple[str, str]:
    """Apply random mutations. Returns (mutated_string, description)."""
    if not s:
        return s, "empty"
    # Protect $'...' and $"..." sequences from mutation
    protected: list[str] = []

    def save(m: re.Match[str]) -> str:
        protected.append(m.group())
        return chr(len(protected))

    s = re.sub(r"\$'[^']*'", save, s)
    s = re.sub(r'\$"(?:[^"\\]|\\.)*"', save, s)
    result = list(s)
    ops = []
    for _ in range(num_mutations):
        op = random.choice(["insert", "delete", "swap", "replace"])
        if op == "insert" and len(result) > 0:
            pos = random.randint(0, len(result))
            insertion = pick_insertion()
            for i, c in enumerate(insertion):
                result.insert(pos + i, c)
            ops.append(f"insert {insertion!r} at {pos}")
        elif op == "delete" and len(result) > 1:
            result_str_tmp = "".join(result)
            pattern = random.choice(DELETION_PATTERNS)
            if pattern in result_str_tmp and random.random() < 0.3:
                idx = result_str_tmp.index(pattern)
                for _ in range(len(pattern)):
                    result.pop(idx)
                ops.append(f"delete {pattern!r} at {idx}")
            else:
                pos = random.randint(0, len(result) - 1)
                deleted = result.pop(pos)
                ops.append(f"delete {deleted!r} at {pos}")
        elif op == "swap" and len(result) > 1:
            pos = random.randint(0, len(result) - 2)
            result[pos], result[pos + 1] = result[pos + 1], result[pos]
            ops.append(f"swap at {pos}")
        elif op == "replace" and len(result) > 0:
            pos = random.randint(0, len(result) - 1)
            old = result[pos]
            result[pos] = pick_mutation_char()
            ops.append(f"replace {old!r} with {result[pos]!r} at {pos}")
    result_str = "".join(result)
    for i, p in enumerate(protected):
        result_str = result_str.replace(chr(i + 1), p)
    return result_str, "; ".join(ops) if ops else "no-op"


# ------------------------------------------------------------------------------
# Worker state (initialized once per worker, avoids pickle overhead)
# ------------------------------------------------------------------------------

_worker_inputs: tuple[str, ...] = ()


def _init_worker(inputs: tuple[str, ...]) -> None:
    """Initialize worker with inputs. Called once per worker process."""
    global _worker_inputs
    _worker_inputs = inputs


# ------------------------------------------------------------------------------
# Task function (runs in worker process)
# ------------------------------------------------------------------------------


@dataclass
class TaskResult:
    """Result from a single fuzz task."""

    discrepancy: Discrepancy | None = None
    found_discrepancy: bool = False
    survived_minimize: bool = False
    passed_filter: bool = False


def fuzz_task(
    num_mutations: int,
    should_minimize: bool,
    filter_layer: int | None,
    both_succeed: bool,
    seed: int | None,
) -> TaskResult:
    """Single fuzz iteration as an independent task. Runs in worker process."""
    if seed is not None:
        random.seed(seed)
    else:
        random.seed()

    original = random.choice(_worker_inputs)
    mutated, desc = mutate(original, num_mutations)
    parable = run_parable(mutated)
    oracle = run_oracle(mutated)

    # Check for discrepancy
    if parable is None and oracle is None:
        return TaskResult()
    if (parable is None) == (oracle is None) and normalize(parable) == normalize(oracle):
        return TaskResult()

    # Found a discrepancy
    d = Discrepancy(
        original=original,
        mutated=mutated,
        mutation_desc=desc,
        parable_result=parable if parable else "<error>",
        oracle_result=oracle if oracle else "<error>",
    )

    # Filter --both-succeed
    if both_succeed:
        if d.parable_result == "<error>" or d.oracle_result == "<error>":
            return TaskResult()

    # Minimize if needed
    if should_minimize:
        minimized = minimize_input(d.mutated)
        if minimized is None:
            return TaskResult(found_discrepancy=True, survived_minimize=False)
        d.mutated = minimized

    # Check layer filter
    passed = True
    if filter_layer is not None:
        detected = detect_layer(d.mutated)
        if detected > filter_layer:
            passed = False

    return TaskResult(
        discrepancy=d,
        found_discrepancy=True,
        survived_minimize=True,
        passed_filter=passed,
    )


# ------------------------------------------------------------------------------
# Coordinator
# ------------------------------------------------------------------------------


@dataclass
class FuzzerCoordinator:
    """Coordinates fuzzing using loky executor."""

    config: FuzzerConfig
    stats: FuzzerStats = field(default_factory=FuzzerStats)
    discrepancies: list[Discrepancy] = field(default_factory=list)
    seen: set[str] = field(default_factory=set)
    _output_file: object = field(default=None, repr=False)

    def should_stop(self) -> bool:
        if self.config.stop_after and len(self.discrepancies) >= self.config.stop_after:
            return True
        if self.config.max_iterations and self.stats.iterations >= self.config.max_iterations:
            return True
        return False

    def process_result(self, result: TaskResult) -> None:
        """Process a single result from a task."""
        self.stats.iterations += 1
        if not result.found_discrepancy:
            return
        self.stats.raw_discrepancies += 1
        if not result.survived_minimize:
            return
        self.stats.survived_minimize += 1
        # Dedupe by minimized input
        key = result.discrepancy.mutated
        if key in self.seen:
            self.stats.duplicates_skipped += 1
            return
        self.seen.add(key)
        if not result.passed_filter:
            return
        self.stats.passed_filter += 1
        self.discrepancies.append(result.discrepancy)
        self._write_discrepancy(result.discrepancy)
        if self.config.verbose:
            self._print_discrepancy(result.discrepancy)

    def _write_discrepancy(self, d: Discrepancy) -> None:
        if self._output_file:
            self._output_file.write(f"# Original: {d.original!r}\n")
            self._output_file.write(f"# Parable:  {d.parable_result}\n")
            self._output_file.write(f"=== {d.mutation_desc}\n")
            self._output_file.write(f"{d.mutated}\n")
            self._output_file.write("---\n")
            self._output_file.write(f"{d.oracle_result}\n")
            self._output_file.write("---\n\n")
            self._output_file.flush()

    def _print_discrepancy(self, d: Discrepancy) -> None:
        print(f"\n[{len(self.discrepancies)}] DISCREPANCY: {d.mutation_desc}")
        print(f"  Mutated:  {d.mutated!r}")
        print(f"  Parable:  {d.parable_result}")
        print(f"  Oracle:   {d.oracle_result}")

    def print_status(self) -> None:
        print(f"\r{self.stats.status_line(self.config)}", end="", flush=True)

    def run(self) -> None:
        """Run the fuzzer using loky executor."""
        # Open output file
        if self.config.output_path:
            self._output_file = open(self.config.output_path, "w")

        # Use loky's reusable executor - robust and deadlock-free
        # max_workers limits concurrent processes
        # initializer loads inputs once per worker to avoid pickle overhead
        executor = get_reusable_executor(
            max_workers=self.config.max_workers,
            timeout=60,  # Workers idle timeout
            initializer=_init_worker,
            initargs=(self.config.inputs,),
        )

        try:
            last_status_iterations = 0
            pending_futures = set()

            while not self.should_stop():
                # Submit batch of tasks up to batch_size pending
                while len(pending_futures) < self.config.batch_size and not self.should_stop():
                    # Generate unique seed for each task
                    task_seed = None
                    if self.config.seed is not None:
                        task_seed = self.config.seed + self.stats.iterations + len(pending_futures)

                    future = executor.submit(
                        fuzz_task,
                        self.config.mutations_per_input,
                        self.config.should_minimize,
                        self.config.filter_layer,
                        self.config.both_succeed,
                        task_seed,
                    )
                    pending_futures.add(future)

                # Wait for at least one to complete
                if pending_futures:
                    done = set()
                    for future in list(pending_futures):
                        if future.done():
                            done.add(future)
                    if not done:
                        import concurrent.futures

                        done_iter, _ = concurrent.futures.wait(
                            pending_futures,
                            return_when=concurrent.futures.FIRST_COMPLETED,
                            timeout=10,
                        )
                        done = done_iter
                        if not done:
                            continue

                    for future in done:
                        pending_futures.discard(future)
                        try:
                            result = future.result()
                            self.process_result(result)
                        except Exception as e:
                            self.stats.iterations += 1
                            if self.config.verbose:
                                print(f"\nWorker error: {e}")

                # Print status periodically
                if self.stats.iterations - last_status_iterations >= 100:
                    self.print_status()
                    last_status_iterations = self.stats.iterations

            # Drain remaining futures
            for future in pending_futures:
                try:
                    result = future.result(timeout=10)
                    self.process_result(result)
                except Exception:
                    pass

            if self.config.stop_after:
                print(f"\nStopped: {self.config.stop_after} discrepancies found")
        finally:
            if self._output_file:
                self._output_file.close()
        print()

    def report(self) -> None:
        """Print final report."""
        print(
            f"\nFound {len(self.discrepancies)} discrepancies in {self.stats.iterations} iterations"
        )
        if self.config.should_minimize:
            print(f"  {self.stats.raw_discrepancies} raw")
            print(f"  {self.stats.survived_minimize} survived minimize")
            print(f"  {self.stats.passed_filter} passed layer filter")
            print(f"  {self.stats.duplicates_skipped} duplicates skipped")

        both_ok = [
            d
            for d in self.discrepancies
            if d.parable_result != "<error>" and d.oracle_result != "<error>"
        ]
        parable_err = [
            d
            for d in self.discrepancies
            if d.parable_result == "<error>" and d.oracle_result != "<error>"
        ]
        oracle_err = [
            d
            for d in self.discrepancies
            if d.parable_result != "<error>" and d.oracle_result == "<error>"
        ]
        print(f"  Both succeed, different AST: {len(both_ok)}")
        print(f"  Parable errors, oracle succeeds: {len(parable_err)}")
        print(f"  Parable succeeds, oracle errors: {len(oracle_err)}")

        if self.discrepancies and self.config.output_path:
            print(f"Discrepancies written to {self.config.output_path}")

        if both_ok:
            print("\n=== BOTH SUCCEED BUT DIFFER (most interesting) ===")
            for d in both_ok[:5]:
                print()
                print("-" * 40)
                print(f"Input:    {d.mutated!r}")
                print(f"Parable:  {d.parable_result[:200]}...")
                print(f"Oracle:   {d.oracle_result[:200]}...")

        if parable_err and not self.config.both_succeed:
            print("\n=== PARABLE ERRORS, ORACLE SUCCEEDS ===")
            for d in parable_err[:3]:
                print()
                print("-" * 40)
                print(f"Input:    {d.mutated!r}")
                print(f"Oracle:   {d.oracle_result[:200]}...")

        if oracle_err and not self.config.both_succeed:
            print("\n=== PARABLE SUCCEEDS, ORACLE ERRORS ===")
            for d in oracle_err[:3]:
                print()
                print("-" * 40)
                print(f"Input:    {d.mutated!r}")
                print(f"Parable:  {d.parable_result[:200]}...")


# ------------------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Character mutation fuzzer")
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=1000,
        help="Max iterations (ignored if --stop-after is set)",
    )
    parser.add_argument(
        "-m", "--mutations", type=int, default=2, help="Mutations per input (default: 2)"
    )
    parser.add_argument("-o", "--output", type=Path, help="Output file for discrepancies")
    parser.add_argument("-s", "--seed", type=int, help="Random seed")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--both-succeed",
        action="store_true",
        help="Only show cases where both parsers succeed but differ",
    )
    parser.add_argument(
        "--stop-after",
        type=int,
        help="Stop after finding N unique discrepancies (runs indefinitely)",
    )
    parser.add_argument(
        "--minimize", action="store_true", help="Minimize discrepancies before output"
    )
    parser.add_argument(
        "--filter-layer", help="Only show discrepancies at or below this layer (implies --minimize)"
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=None,
        help="Max parallel workers (default: number of CPU cores)",
    )
    args = parser.parse_args()

    if not ORACLE_PATH.exists():
        print(f"Error: bash-oracle not found at {ORACLE_PATH}", file=sys.stderr)
        sys.exit(1)

    # Load corpus
    tests_dir = REPO_ROOT / "tests"
    test_files = find_test_files(tests_dir)
    inputs: list[str] = []
    for tf in test_files:
        inputs.extend(parse_test_file(tf))
    print(f"Loaded {len(inputs)} inputs from {len(test_files)} test files")

    # Build config
    filter_layer = parse_layer_spec(args.filter_layer) if args.filter_layer else None
    config = FuzzerConfig(
        inputs=tuple(inputs),
        mutations_per_input=args.mutations,
        seed=args.seed,
        minimize=args.minimize,
        filter_layer=filter_layer,
        both_succeed=args.both_succeed,
        stop_after=args.stop_after,
        max_iterations=None if args.stop_after else args.iterations,
        verbose=args.verbose,
        output_path=args.output,
        max_workers=args.jobs or os.cpu_count() or 4,
    )

    # Run
    coordinator = FuzzerCoordinator(config)
    coordinator.run()
    coordinator.report()

    sys.exit(1 if coordinator.discrepancies else 0)


if __name__ == "__main__":
    main()
