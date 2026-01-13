#!/usr/bin/env python3
"""Run Parable against the bigtable-bash corpus and report failures."""

import os
import sys

# Add src to path for parable import
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARABLE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
sys.path.insert(0, os.path.join(PARABLE_ROOT, "src"))

from parable import ParseError, parse  # noqa: E402

CORPUS_DIR = os.path.expanduser("~/source/bigtable-bash/tests")
FAILURES_FILE = os.path.join(SCRIPT_DIR, "failures.txt")
HEREDOC_DASHES_FILE = os.path.join(SCRIPT_DIR, "heredoc-dashes.txt")
MAX_FAILURES = 100

# Test files to skip (known issues to investigate later)
SKIP_FILES = {
    "001629__Patlol__Handy-Install-Web-Server-ruTorrent-__util_listeusers.tests",
    "012091__johnchronis__exareme__exareme-admin.tests",  # very long expected output
    "012559__bbgw__kubernetes__test-cmd.tests",  # very long expected output
    "012773__Devindik__origin__git-sh-setup.tests",  # very long expected output
    "014119__kyma-project__test-infra__integration-tests.tests",  # heredoc contains ---
    "014246__istio__istio.io__snips.tests",  # heredoc contains ---
    "014289__chaolou__kubernetes__test-cmd.tests",  # corpus expects $(! but oracle now outputs $(\!
    "051344__nemesiscodex__jukyOS-osbuilder__preimage.90.core.tests",  # heredoc contains ===
}

# Files where heredoc contains --- which breaks the corpus test parser
# (loaded from heredoc-dashes.txt)
HEREDOC_DASHES_FILES: set[str] = set()
if os.path.exists(HEREDOC_DASHES_FILE):
    with open(HEREDOC_DASHES_FILE) as f:
        HEREDOC_DASHES_FILES = {line.strip() for line in f if line.strip()}


def parse_test_file(filepath):
    """Parse a .tests file. Returns list of (name, input, expected) tuples."""
    tests = []
    with open(filepath) as f:
        lines = f.read().split("\n")
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.startswith("=== "):
            name = line[4:].strip()
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
            tests.append((name, "\n".join(input_lines), "\n".join(expected_lines)))
        else:
            i += 1
    return tests


def normalize(s):
    """Normalize whitespace for comparison."""
    return " ".join(s.split())


def run_test(test_input, test_expected):
    """Run a single test. Returns (passed, actual)."""
    if test_expected == "<error>":
        try:
            nodes = parse(test_input)
            actual = " ".join(node.to_sexp() for node in nodes)
            return (False, actual)  # Expected error but got parse
        except ParseError:
            return (True, "<error>")
        except Exception:
            return (True, "<error>")

    try:
        nodes = parse(test_input)
        actual = " ".join(node.to_sexp() for node in nodes)
    except ParseError as e:
        return (False, f"<error>: {e}")
    except Exception as e:
        return (False, f"!exception: {e}")

    if normalize(actual) == normalize(test_expected):
        return (True, actual)
    return (False, actual)


def main():
    if not os.path.isdir(CORPUS_DIR):
        print(f"Error: corpus not found at {CORPUS_DIR}", file=sys.stderr)
        sys.exit(1)

    test_files = sorted(
        os.path.join(CORPUS_DIR, f) for f in os.listdir(CORPUS_DIR) if f.endswith(".tests")
    )
    total_files = len(test_files)
    passed = 0
    failed = 0

    skipped = 0
    all_skip_files = SKIP_FILES | HEREDOC_DASHES_FILES
    with open(FAILURES_FILE, "w") as failures_f:
        for i, test_file in enumerate(test_files):
            if os.path.basename(test_file) in all_skip_files:
                skipped += 1
                continue
            tests = parse_test_file(test_file)
            for _name, test_input, test_expected in tests:
                ok, actual = run_test(test_input, test_expected)
                if ok:
                    passed += 1
                else:
                    failed += 1
                    failures_f.write(test_file + "\n")
                    failures_f.flush()
                    if failed >= MAX_FAILURES:
                        break
            print(f"\r{i + 1}/{total_files} files ({failed} failures)", end="", flush=True)
            if failed >= MAX_FAILURES:
                break

    print()
    if failed:
        print(f"Failures written to {FAILURES_FILE}")
    print(f"Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
