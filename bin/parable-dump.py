#!/usr/bin/env python3
"""CLI tool to parse bash and dump the AST."""

import sys

from parable import parse
from parable.core.errors import ParseError


def main():
    if len(sys.argv) < 2:
        print("Usage: parable-dump.py 'bash command'", file=sys.stderr)
        print("       parable-dump.py -f <file>", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "-f":
        if len(sys.argv) < 3:
            print("Error: -f requires a filename", file=sys.stderr)
            sys.exit(1)
        with open(sys.argv[2]) as f:
            source = f.read()
    else:
        source = sys.argv[1]

    try:
        nodes = parse(source)
        for node in nodes:
            print(node.to_sexp())
    except ParseError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
