#!/usr/bin/env python3
"""Benchmark Parable parser against GNU Bash test corpus."""

import os

import pyperf

from parable import parse

CORPUS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "tests", "corpus", "gnu-bash", "tests.tests"
)


def load_corpus():
    """Extract bash source from corpus file. Returns list of source strings."""
    with open(CORPUS_PATH) as f:
        lines = f.read().split("\n")
    sources = []
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
            # Skip expected output
            while i < n and lines[i] != "---" and not lines[i].startswith("=== "):
                i += 1
            if i < n and lines[i] == "---":
                i += 1
            sources.append("\n".join(input_lines))
        else:
            i += 1
    return sources


def parse_all(sources):
    """Parse all sources."""
    for src in sources:
        parse(src)


def main():
    sources = load_corpus()
    runner = pyperf.Runner()
    runner.metadata["corpus_scripts"] = len(sources)
    runner.metadata["corpus_lines"] = sum(src.count("\n") + 1 for src in sources)
    runner.metadata["corpus_bytes"] = sum(len(src) for src in sources)
    runner.bench_func("gnu_bash_corpus", parse_all, sources)


if __name__ == "__main__":
    main()
