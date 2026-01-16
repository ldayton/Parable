"""CLI entry point for the fuzzer agent."""

import argparse
import sys

from .agent import MODELS, FuzzerFixer


def main():
    parser = argparse.ArgumentParser(description="Autonomous fuzzer bug fixing agent")
    parser.add_argument("--model", default="sonnet-45", choices=MODELS.keys(), help="Model to use")
    args = parser.parse_args()
    sys.exit(FuzzerFixer(model=args.model).run())


if __name__ == "__main__":
    main()
