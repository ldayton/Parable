#!/usr/bin/env python3
"""Corpus mutation fuzzer for differential testing.

Mutates inputs from the test corpus (tests/**/*.tests) and compares Parable's
parse results against bash-oracle to find discrepancies.

Architecture:
    - FuzzerConfig: Immutable configuration dataclass
    - FuzzerStats: Mutable statistics tracking
    - FuzzerCoordinator: Manages workers, deduplication, output, and stopping
    - Worker processes: Run fuzz iterations and send results via queue
"""

from __future__ import annotations

import argparse
import multiprocessing as mp
import random
import re
import sys
from dataclasses import dataclass, field
from multiprocessing import Queue
from pathlib import Path
from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from multiprocessing.synchronize import Event as EventType

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

    def status_line(self, config: FuzzerConfig) -> str:
        if config.max_iterations:
            s = f"{self.iterations}/{config.max_iterations} iterations"
        else:
            s = f"{self.iterations} iterations"
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


def fuzz_once(inputs: tuple[str, ...], num_mutations: int) -> Discrepancy | None:
    """Run one fuzzing iteration. Returns Discrepancy if found, else None."""
    original = random.choice(inputs)
    mutated, desc = mutate(original, num_mutations)
    parable = run_parable(mutated)
    oracle = run_oracle(mutated)
    if parable is None and oracle is None:
        return None
    if (parable is None) != (oracle is None):
        return Discrepancy(
            original=original,
            mutated=mutated,
            mutation_desc=desc,
            parable_result=parable if parable else "<error>",
            oracle_result=oracle if oracle else "<error>",
        )
    if normalize(parable) != normalize(oracle):
        return Discrepancy(
            original=original,
            mutated=mutated,
            mutation_desc=desc,
            parable_result=parable,
            oracle_result=oracle,
        )
    return None


# ------------------------------------------------------------------------------
# Worker process
# ------------------------------------------------------------------------------


@dataclass
class WorkerResult:
    """Result from a worker."""

    iterations: int  # Iterations performed since last message
    discrepancy: Discrepancy | None = None  # None if no discrepancy or failed minimize
    found_discrepancy: bool = False  # True if a discrepancy was found (even if it failed minimize)
    survived_minimize: bool = False
    passed_filter: bool = False


# Sentinel value to signal workers to stop
STOP_SENTINEL = None


def worker_process(
    config: FuzzerConfig,
    result_queue: Queue[WorkerResult | None],
    stop_event: EventType,
    worker_id: int,
) -> None:
    """Worker process: fuzz continuously until stop_event is set."""
    # Seed each worker uniquely
    if config.seed is not None:
        random.seed(config.seed + worker_id)
    else:
        random.seed()

    iterations = 0
    while not stop_event.is_set():
        iterations += 1
        d = fuzz_once(config.inputs, config.mutations_per_input)
        if d is None:
            # Send progress update every 100 iterations even without discrepancy
            if iterations >= 100:
                result_queue.put(WorkerResult(iterations=iterations))
                iterations = 0
            continue
        # Filter --both-succeed
        if config.both_succeed:
            if d.parable_result == "<error>" or d.oracle_result == "<error>":
                continue
        # Found a discrepancy - minimize if needed
        if config.should_minimize:
            minimized = minimize_input(d.mutated)
            if minimized is None:
                # Failed to minimize - report but don't include discrepancy
                result_queue.put(
                    WorkerResult(
                        iterations=iterations,
                        found_discrepancy=True,
                        survived_minimize=False,
                    )
                )
                iterations = 0
                continue
            d.mutated = minimized
        # Check layer filter
        passed = True
        if config.filter_layer is not None:
            detected = detect_layer(d.mutated)
            if detected > config.filter_layer:
                passed = False
        result_queue.put(
            WorkerResult(
                iterations=iterations,
                discrepancy=d,
                found_discrepancy=True,
                survived_minimize=True,
                passed_filter=passed,
            )
        )
        iterations = 0
    # Signal this worker is done
    result_queue.put(STOP_SENTINEL)


# ------------------------------------------------------------------------------
# Coordinator
# ------------------------------------------------------------------------------


@dataclass
class FuzzerCoordinator:
    """Coordinates fuzzing: manages workers, collects results, handles output."""

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

    def process_result(self, result: WorkerResult) -> None:
        """Process a single result from a worker."""
        self.stats.iterations += result.iterations
        if not result.found_discrepancy:
            return  # Just a progress update
        self.stats.raw_discrepancies += 1
        if not result.survived_minimize:
            return  # Failed to minimize
        self.stats.survived_minimize += 1
        # Dedupe by minimized input
        key = result.discrepancy.mutated
        if key in self.seen:
            self.stats.duplicates_skipped += 1
            return
        self.seen.add(key)
        if not result.passed_filter:
            return  # Didn't pass layer filter
        self.stats.passed_filter += 1
        self.discrepancies.append(result.discrepancy)
        self._write_discrepancy(result.discrepancy)
        if self.config.verbose:
            self._print_discrepancy(result.discrepancy)

    def _write_discrepancy(self, d: Discrepancy) -> None:
        if self._output_file:
            # Output in .tests format with context as comments
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
        """Run the fuzzer with worker processes."""
        num_workers = mp.cpu_count()
        result_queue: Queue[WorkerResult | None] = mp.Queue()
        stop_event: EventType = mp.Event()

        # Open output file
        if self.config.output_path:
            self._output_file = open(self.config.output_path, "w")

        # Start workers
        workers = []
        for i in range(num_workers):
            p = mp.Process(
                target=worker_process,
                args=(self.config, result_queue, stop_event, i),
            )
            p.start()
            workers.append(p)

        try:
            workers_alive = num_workers
            last_status_iterations = 0
            while workers_alive > 0:
                result = result_queue.get()
                if result is STOP_SENTINEL:
                    workers_alive -= 1
                    continue
                self.process_result(result)
                # Print status every 100 iterations
                if self.stats.iterations - last_status_iterations >= 100:
                    self.print_status()
                    last_status_iterations = self.stats.iterations
                # Check stop condition
                if self.should_stop():
                    stop_event.set()
                    print(f"\nStopped: {self.config.stop_after} discrepancies found")
                    break
        finally:
            stop_event.set()
            for p in workers:
                p.join(timeout=1)
                if p.is_alive():
                    p.terminate()
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
    )

    # Run
    coordinator = FuzzerCoordinator(config)
    coordinator.run()
    coordinator.report()

    sys.exit(1 if coordinator.discrepancies else 0)


if __name__ == "__main__":
    main()
