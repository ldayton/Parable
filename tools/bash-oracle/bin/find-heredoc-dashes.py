#!/usr/bin/env python3
"""Find corpus test files where heredocs contain --- which breaks the test parser."""

import os
import re

CORPUS_DIR = os.path.expanduser("~/source/bigtable-bash/tests")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "heredoc-dashes.txt")


def has_heredoc_with_dashes(filepath):
    """Check if file has a heredoc containing ---."""
    with open(filepath) as f:
        content = f.read()

    # Find the input section (between first === and first ---)
    lines = content.split("\n")
    in_input = False
    input_lines = []

    for line in lines:
        if line.startswith("==="):
            in_input = True
            continue
        if in_input and line == "---":
            break
        if in_input:
            input_lines.append(line)

    input_text = "\n".join(input_lines)

    # Look for heredoc patterns: <<EOF or <<'EOF' or <<"EOF" or <<-EOF etc
    # followed by content that includes ---
    heredoc_pattern = r'<<-?\s*[\'"]?(\w+)[\'"]?'

    for match in re.finditer(heredoc_pattern, input_text):
        delimiter = match.group(1)
        start_pos = match.end()

        # Find the closing delimiter
        remaining = input_text[start_pos:]
        delimiter_pattern = r"^\s*" + re.escape(delimiter) + r"\s*$"

        for i, line in enumerate(remaining.split("\n")):
            if re.match(delimiter_pattern, line):
                # Found end of heredoc, check if content between has ---
                heredoc_content = "\n".join(remaining.split("\n")[:i])
                if "---" in heredoc_content:
                    return True
                break

    return False


def main():
    test_files = sorted(f for f in os.listdir(CORPUS_DIR) if f.endswith(".tests"))

    found = []
    for i, filename in enumerate(test_files):
        if (i + 1) % 1000 == 0:
            print(f"\r{i + 1}/{len(test_files)}", end="", flush=True)

        filepath = os.path.join(CORPUS_DIR, filename)
        try:
            if has_heredoc_with_dashes(filepath):
                found.append(filename)
        except Exception:
            pass  # Skip files that can't be parsed

    print(f"\n\nFound {len(found)} files with heredocs containing ---")

    with open(OUTPUT_FILE, "w") as f:
        for filename in found:
            f.write(filename + "\n")

    print(f"Written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
