#!/usr/bin/env python3
"""Verify bash-oracle -e flag produces identical results to file mode.

Run after bash-oracle -e bug is fixed to confirm behavioral equivalence.

Usage:
    uv run --directory tools/fuzzer python tools/fuzzer/tests/verify_oracle_e_flag.py

Expected: 0 mismatches (excluding timeouts which indicate the bug isn't fixed).
"""

import subprocess
import sys
import tempfile
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from fuzzer.common import ORACLE_PATH, REPO_ROOT, find_test_files, parse_test_file

MUTATION_CHARS = list("${}()|&<>;\"'\\` \t\n@#![]:=*?~/+-,%^0123456789")


def run_e(text):
    try:
        r = subprocess.run(
            [str(ORACLE_PATH), "-e", text],
            capture_output=True,
            timeout=0.5,
        )
        return ("ok", r.stdout) if r.returncode == 0 else ("error", r.returncode)
    except subprocess.TimeoutExpired:
        return ("timeout", None)
    except ValueError:
        return ("valueerror", None)


def run_file(text):
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(text)
            tmp = Path(f.name)
        r = subprocess.run(
            [str(ORACLE_PATH), str(tmp)],
            capture_output=True,
            timeout=0.5,
        )
        tmp.unlink()
        return ("ok", r.stdout) if r.returncode == 0 else ("error", r.returncode)
    except subprocess.TimeoutExpired:
        tmp.unlink(missing_ok=True)
        return ("timeout", None)


def mutate(text, rng):
    chars = list(text)
    for _ in range(2):
        if not chars:
            break
        op = rng.choice(["insert", "delete", "replace"])
        pos = rng.randint(0, len(chars))
        if op == "insert":
            chars.insert(pos, rng.choice(MUTATION_CHARS))
        elif op == "delete" and chars:
            del chars[min(pos, len(chars) - 1)]
        elif op == "replace" and chars:
            chars[min(pos, len(chars) - 1)] = rng.choice(MUTATION_CHARS)
    return "".join(chars)


def main():
    print("Loading test inputs...")
    test_files = find_test_files(REPO_ROOT / "tests")
    inputs = []
    for f in test_files:
        inputs.extend(parse_test_file(f))
    print(f"Loaded {len(inputs)} base inputs\n")

    # Test 1: Unmutated corpus
    print("Test 1: Verifying unmutated corpus...")
    mismatches = 0
    timeouts = 0
    for i, inp in enumerate(inputs):
        if i % 500 == 0:
            print(f"  {i}/{len(inputs)}...", flush=True)
        e_result = run_e(inp)
        f_result = run_file(inp)
        if e_result[0] == "timeout":
            timeouts += 1
        elif e_result != f_result:
            mismatches += 1
            if mismatches <= 3:
                print(f"  MISMATCH: {inp!r}")
                print(f"    -e:   {e_result}")
                print(f"    file: {f_result}")
    print(f"  Unmutated: {mismatches} mismatches, {timeouts} timeouts\n")

    # Test 2: Mutated inputs
    print("Test 2: Verifying 10000 mutated inputs...")
    rng = random.Random(42)
    mismatches = 0
    timeouts = 0
    for i in range(10000):
        if i % 2000 == 0:
            print(f"  {i}/10000...", flush=True)
        mutated = mutate(rng.choice(inputs), rng)
        e_result = run_e(mutated)
        f_result = run_file(mutated)
        if e_result[0] == "timeout":
            timeouts += 1
        elif e_result != f_result:
            mismatches += 1
            if mismatches <= 3:
                print(f"  MISMATCH: {mutated!r}")
                print(f"    -e:   {e_result}")
                print(f"    file: {f_result}")
    print(f"  Mutated: {mismatches} mismatches, {timeouts} timeouts\n")

    # Summary
    print("=" * 50)
    if timeouts > 0:
        print(f"⚠ {timeouts} timeouts detected - bash-oracle -e bug may not be fixed")
    if mismatches > 0:
        print(f"✗ {mismatches} mismatches - -e flag not equivalent to file mode")
    else:
        print("✓ All tests passed - -e flag is equivalent to file mode")


if __name__ == "__main__":
    main()
