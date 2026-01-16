"""CLI entry point for the fuzzer agent."""

import argparse
import sys

from .agent import MODELS, FuzzerFixer
from .pricing import AZURE_PRICING, CLAUDE_PRICING, GCP_PRICING, OTHER_PRICING

MODEL_PRICES = {**CLAUDE_PRICING, **OTHER_PRICING, **AZURE_PRICING, **GCP_PRICING}


def _build_model_table() -> str:
    lines = [
        "models (per 1M tokens):",
        "  model          input    output",
        "  -------------- -------- --------",
    ]
    for model in MODELS:
        inp, out = MODEL_PRICES.get(model, (0.0, 0.0))
        lines.append(f"  {model:<14} ${inp:<7.2f} ${out:<7.2f}")
    lines.append("")
    lines.append("prices may be outdated. use --prices to fetch latest from AWS.")
    lines.append("claude prices require manual update: aws.amazon.com/bedrock/pricing")
    lines.append("")
    lines.append("exit codes: 0 (fixed + PR), 1 (no bugs), 2 (failed)")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous fuzzer bug fixing agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_build_model_table(),
    )
    parser.add_argument(
        "--model",
        default="sonnet-4.5",
        metavar="MODEL",
        choices=MODELS.keys(),
        help="Model to use (default: sonnet-4.5)",
    )
    parser.add_argument(
        "--prices", action="store_true", help="Fetch live pricing from AWS and exit"
    )
    parser.add_argument(
        "--claude", action="store_true", help="Use Claude Agent SDK instead of Strands"
    )
    args = parser.parse_args()
    if args.prices:
        from .pricing import main as pricing_main

        pricing_main()
        sys.exit(0)
    if args.claude:
        from .claude_agent import ClaudeFuzzerFixer

        sys.exit(ClaudeFuzzerFixer().run())
    sys.exit(FuzzerFixer(model=args.model).run())


if __name__ == "__main__":
    main()
