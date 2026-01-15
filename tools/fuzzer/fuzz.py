#!/usr/bin/env python3
"""Phase 1 fuzzer: corpus mutation for differential testing.

Mutates inputs from the test corpus (tests/**/*.tests) and compares Parable's
parse results against bash-oracle to find discrepancies.

Limitations:
    Single-character mutations struggle to create structural combinations that
    don't already exist in the corpus. Real-world corpora (like bigtable) find
    bugs this fuzzer misses because they naturally contain diverse nesting.

Potential improvements:

    | Improvement             | Impact | Difficulty | Notes                          |
    |-------------------------|--------|------------|--------------------------------|
    | Cross-pollination       | High   | Medium     | Graft subtrees between inputs  |
    | Structural mutations    | High   | Medium     | Wrap exprs in $(), <(), etc.   |
    | Grammar-aware generation| High   | High       | Different tool entirely        |

    The corpus (tests/**/*.tests) is fed from tree-sitter, oils, gnu bash,
    hand-written tests, bigtable discoveries, and fuzzer discoveries (fuzz-*.tests).
"""

import argparse
import random
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from parable import ParseError, parse  # noqa: E402

ORACLE_PATH = Path.home() / "source" / "bash-oracle" / "bash-oracle"
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
    """Pick a mutation char. Digits are weighted as a group, not individually."""
    group = random.choice(MUTATION_GROUPS)
    return random.choice(group) if len(group) > 1 else group


def pick_insertion() -> str:
    """Pick something to insert: single char or multi-char pattern."""
    if random.random() < 0.2:
        return random.choice(INSERTION_PATTERNS)
    return pick_mutation_char()


@dataclass
class Discrepancy:
    original: str
    mutated: str
    mutation_desc: str
    parable_result: str
    oracle_result: str

    def signature(self) -> str:
        """Return a signature for deduplication."""
        # Dedupe by (parable_error, oracle_error, first 50 chars of input)
        p = "err" if self.parable_result == "<error>" else "ok"
        o = "err" if self.oracle_result == "<error>" else "ok"
        return f"{p}:{o}:{self.mutated[:50]}"


def find_test_files(directory: Path) -> list[Path]:
    """Find all .tests files recursively."""
    return sorted(directory.rglob("*.tests"))


def parse_test_file(filepath: Path) -> list[str]:
    """Extract just the inputs from a .tests file."""
    inputs = []
    lines = filepath.read_text().split("\n")
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.startswith("=== "):
            i += 1
            input_lines = []
            while i < n and lines[i] != "---":
                input_lines.append(lines[i])
                i += 1
            if i < n and lines[i] == "---":
                i += 1
            # Skip expected section
            while i < n and lines[i] != "---" and not lines[i].startswith("=== "):
                i += 1
            if i < n and lines[i] == "---":
                i += 1
            inputs.append("\n".join(input_lines))
        else:
            i += 1
    return inputs


def mutate(s: str, num_mutations: int = 1) -> tuple[str, str]:
    """Apply random mutations. Returns (mutated_string, description)."""
    import re

    if not s:
        return s, "empty"
    # Protect $'...' and $"..." sequences from mutation
    protected = []

    def save(m):
        protected.append(m.group())
        return chr(len(protected))  # \x01, \x02, ...

    s = re.sub(r"\$'[^']*'", save, s)
    s = re.sub(r'\$"(?:[^"\\]|\\.)*"', save, s)
    # Mutate
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
            # Try to delete a multi-char pattern
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
    # Restore protected sequences
    for i, p in enumerate(protected):
        result_str = result_str.replace(chr(i + 1), p)
    return result_str, "; ".join(ops) if ops else "no-op"


def run_oracle(input_text: str) -> str | None:
    """Run bash-oracle on input. Returns s-expr or None on error/timeout."""
    import tempfile

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(input_text)
            tmp_path = Path(f.name)
        result = subprocess.run(
            [str(ORACLE_PATH), str(tmp_path)],
            capture_output=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None
        return result.stdout.decode("utf-8", errors="replace").strip()
    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        return None
    finally:
        if tmp_path:
            tmp_path.unlink(missing_ok=True)


def run_parable(input_text: str) -> str | None:
    """Run Parable on input. Returns s-expr, None on parse error, or <crash:...>."""
    try:
        nodes = parse(input_text)
        return " ".join(node.to_sexp() for node in nodes)
    except ParseError:
        return None
    except Exception as e:
        return f"<crash: {type(e).__name__}: {e}>"


def normalize(s: str) -> str:
    """Normalize for comparison, ignoring cosmetic differences."""
    import re

    # Collapse whitespace
    s = " ".join(s.split())
    # Normalize fd 1 redirects: 1> -> >, 1>& -> >&
    s = re.sub(r"\b1>", ">", s)
    s = re.sub(r"\b1>&", ">&", s)
    # Normalize indentation inside quoted strings (\\n followed by spaces)
    s = re.sub(r"\\n\s+", r"\\n", s)
    return s


def fuzz_once(inputs: list[str], num_mutations: int) -> Discrepancy | None:
    """Run one fuzzing iteration. Returns Discrepancy if found, else None."""
    original = random.choice(inputs)
    mutated, desc = mutate(original, num_mutations)
    parable = run_parable(mutated)
    oracle = run_oracle(mutated)
    # Both error → no discrepancy
    if parable is None and oracle is None:
        return None
    # One errors, other succeeds → discrepancy
    if (parable is None) != (oracle is None):
        return Discrepancy(
            original=original,
            mutated=mutated,
            mutation_desc=desc,
            parable_result=parable if parable else "<error>",
            oracle_result=oracle if oracle else "<error>",
        )
    # Both succeed but differ → discrepancy
    if normalize(parable) != normalize(oracle):
        return Discrepancy(
            original=original,
            mutated=mutated,
            mutation_desc=desc,
            parable_result=parable,
            oracle_result=oracle,
        )
    return None


def main():
    parser = argparse.ArgumentParser(description="Phase 1 corpus mutation fuzzer")
    parser.add_argument("-n", "--iterations", type=int, default=1000, help="Number of iterations")
    parser.add_argument("-m", "--mutations", type=int, default=2, help="Mutations per input")
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
        help="Stop after finding N unique discrepancies",
    )
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    if not ORACLE_PATH.exists():
        print(f"Error: bash-oracle not found at {ORACLE_PATH}", file=sys.stderr)
        sys.exit(1)

    # Collect inputs from test corpus
    tests_dir = REPO_ROOT / "tests"
    test_files = find_test_files(tests_dir)
    inputs = []
    for tf in test_files:
        inputs.extend(parse_test_file(tf))
    print(f"Loaded {len(inputs)} inputs from {len(test_files)} test files")

    # Fuzz
    discrepancies: list[Discrepancy] = []
    seen_signatures: set[str] = set()
    for i in range(args.iterations):
        d = fuzz_once(inputs, args.mutations)
        if d:
            # Filter if --both-succeed
            if args.both_succeed:
                if d.parable_result == "<error>" or d.oracle_result == "<error>":
                    continue
            # Deduplicate
            sig = d.signature()
            if sig in seen_signatures:
                continue
            seen_signatures.add(sig)
            discrepancies.append(d)
            if args.verbose:
                print(f"\n[{i + 1}] DISCREPANCY: {d.mutation_desc}")
                print(f"  Mutated:  {d.mutated!r}")
                print(f"  Parable:  {d.parable_result}")
                print(f"  Oracle:   {d.oracle_result}")
            if args.stop_after and len(discrepancies) >= args.stop_after:
                print(f"\nStopped after finding {args.stop_after} discrepancies")
                break
        if (i + 1) % 100 == 0:
            print(
                f"\r{i + 1}/{args.iterations} iterations, {len(discrepancies)} unique discrepancies",
                end="",
                flush=True,
            )
    print()

    # Report
    print(f"\nFound {len(discrepancies)} unique discrepancies in {args.iterations} iterations")

    # Categorize
    both_ok = [
        d for d in discrepancies if d.parable_result != "<error>" and d.oracle_result != "<error>"
    ]
    parable_err = [
        d for d in discrepancies if d.parable_result == "<error>" and d.oracle_result != "<error>"
    ]
    oracle_err = [
        d for d in discrepancies if d.parable_result != "<error>" and d.oracle_result == "<error>"
    ]
    print(f"  Both succeed, different AST: {len(both_ok)}")
    print(f"  Parable errors, oracle succeeds: {len(parable_err)}")
    print(f"  Parable succeeds, oracle errors: {len(oracle_err)}")

    if discrepancies and args.output:
        with open(args.output, "w") as f:
            for d in discrepancies:
                f.write("=" * 60 + "\n")
                f.write(f"Mutation: {d.mutation_desc}\n")
                f.write(f"Original: {d.original!r}\n")
                f.write(f"Mutated:  {d.mutated!r}\n")
                f.write(f"Parable:  {d.parable_result}\n")
                f.write(f"Oracle:   {d.oracle_result}\n")
        print(f"Discrepancies written to {args.output}")

    # Print interesting discrepancies (both succeed but differ)
    if both_ok:
        print("\n=== BOTH SUCCEED BUT DIFFER (most interesting) ===")
        for d in both_ok[:5]:
            print()
            print("-" * 40)
            print(f"Input:    {d.mutated!r}")
            print(f"Parable:  {d.parable_result[:200]}...")
            print(f"Oracle:   {d.oracle_result[:200]}...")

    # Print a few error discrepancies
    if oracle_err and not args.both_succeed:
        print("\n=== PARABLE SUCCEEDS, ORACLE ERRORS ===")
        for d in oracle_err[:3]:
            print()
            print("-" * 40)
            print(f"Input:    {d.mutated!r}")
            print(f"Parable:  {d.parable_result[:200]}...")

    sys.exit(1 if discrepancies else 0)


if __name__ == "__main__":
    main()
