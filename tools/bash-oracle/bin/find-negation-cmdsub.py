#!/usr/bin/env python3
"""Find corpus test files with negation patterns affected by oracle escaping."""

import os

CORPUS_DIR = os.path.expanduser("~/source/bigtable-bash/tests")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "negation-cmdsub.txt")


def has_negation_pattern(filepath):
    """Check if file has negation patterns that oracle escapes incorrectly."""
    with open(filepath) as f:
        content = f.read()

    lines = content.split("\n")
    in_input = False

    for line in lines:
        if line.startswith("==="):
            in_input = True
            continue
        if in_input and line == "c209da5127ac3b3fe0ac82c29cbe77df":
            break
        if in_input:
            # $(! ...) - negation in command substitution
            if "$(!" in line:
                return True
            # [[ ! - negation in conditional expression
            if "[[ !" in line:
                return True

    return False


def main():
    test_files = sorted(f for f in os.listdir(CORPUS_DIR) if f.endswith(".tests"))

    found = []
    for i, filename in enumerate(test_files):
        if (i + 1) % 1000 == 0:
            print(f"\r{i + 1}/{len(test_files)}", end="", flush=True)

        filepath = os.path.join(CORPUS_DIR, filename)
        try:
            if has_negation_pattern(filepath):
                found.append(filename)
        except Exception:
            pass

    print(f"\n\nFound {len(found)} files with negation patterns")

    with open(OUTPUT_FILE, "w") as f:
        for filename in found:
            f.write(filename + "\n")

    print(f"Written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
