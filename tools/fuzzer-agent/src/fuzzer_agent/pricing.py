"""Fetch model pricing from AWS Pricing API.

Claude models use hardcoded values because AWS Pricing API is incomplete
(missing output token prices and newer models).

Sources:
- AWS Pricing API: Nova, Llama models
- AWS Bedrock pricing page: Claude models (manually verified)
"""

import json
import sys
from collections import defaultdict

import boto3

REGION = "US East (Ohio)"

# Claude pricing hardcoded - AWS Pricing API is incomplete (missing output prices)
# Source: https://aws.amazon.com/bedrock/pricing/
# Bug: https://github.com/aws/aws-cli/issues/9567
CLAUDE_PRICING: dict[str, tuple[float, float]] = {
    "haiku-3": (0.25, 1.25),
    "haiku-35": (0.80, 4.00),
    "haiku-45": (1.00, 5.00),
    "sonnet-3": (3.00, 15.00),
    "sonnet-35": (3.00, 15.00),
    "sonnet-4": (3.00, 15.00),
    "sonnet-45": (3.00, 15.00),
    "opus-4": (15.00, 75.00),
    "opus-45": (5.00, 25.00),
}

# Non-Claude pricing (fetched 2026-01-16, can be refreshed with --prices)
OTHER_PRICING: dict[str, tuple[float, float]] = {
    "llama-31-70b": (0.72, 0.72),
    "llama-32-90b": (0.72, 0.72),
    "llama-33-70b": (0.72, 0.72),
    "nova-lite": (0.06, 0.24),
    "nova-micro": (0.03, 0.14),
    "nova-pro": (0.80, 3.20),
}

# Models to fetch from AWS Pricing API (API name -> our name)
API_MODELS = {
    "Nova Micro": "nova-micro",
    "Nova Lite": "nova-lite",
    "Nova Pro": "nova-pro",
    "Llama 3.3 70B": "llama-33-70b",
    "Llama 3.2 90B": "llama-32-90b",
    "Llama 3.1 70B": "llama-31-70b",
}


def fetch_bedrock_pricing() -> dict[str, tuple[float, float]]:
    """Fetch pricing from AWS Pricing API. Returns {model: (input, output)} per 1M tokens."""
    client = boto3.client("pricing", region_name="us-east-1")
    prices: dict[str, dict[str, float]] = defaultdict(dict)
    next_token = None
    while True:
        kwargs: dict = {
            "ServiceCode": "AmazonBedrock",
            "Filters": [{"Type": "TERM_MATCH", "Field": "location", "Value": REGION}],
            "MaxResults": 100,
        }
        if next_token:
            kwargs["NextToken"] = next_token
        response = client.get_products(**kwargs)
        for price_item in response["PriceList"]:
            item = json.loads(price_item)
            attrs = item.get("product", {}).get("attributes", {})
            model = attrs.get("model")
            inference_type = attrs.get("inferenceType")
            feature = attrs.get("feature")
            if not model or model not in API_MODELS:
                continue
            if feature != "On-demand Inference":
                continue
            if inference_type not in ("Input tokens", "Output tokens"):
                continue
            terms = item.get("terms", {}).get("OnDemand", {})
            for term in terms.values():
                for dim in term.get("priceDimensions", {}).values():
                    price_per_1k = float(dim["pricePerUnit"]["USD"])
                    price_per_1m = price_per_1k * 1000
                    key = "input" if inference_type == "Input tokens" else "output"
                    prices[model][key] = price_per_1m
        next_token = response.get("NextToken")
        if not next_token:
            break
    # Convert to our format
    result: dict[str, tuple[float, float]] = {}
    for api_name, our_name in API_MODELS.items():
        if api_name in prices:
            p = prices[api_name]
            if "input" in p and "output" in p:
                result[our_name] = (p["input"], p["output"])
    return result


def get_all_pricing() -> dict[str, tuple[float, float]]:
    """Get pricing for all models, combining API and hardcoded values."""
    prices = dict(CLAUDE_PRICING)
    try:
        api_prices = fetch_bedrock_pricing()
        prices.update(api_prices)
    except Exception as e:
        print(f"Warning: Could not fetch API pricing: {e}", file=sys.stderr)
    return prices


def main() -> None:
    """Fetch and print pricing for all models."""
    print("Fetching pricing from AWS...", file=sys.stderr)
    prices = get_all_pricing()
    print(f"\n{'Model':<15} {'Input/1M':<12} {'Output/1M':<12}")
    print("-" * 40)
    all_models = sorted(set(CLAUDE_PRICING.keys()) | set(API_MODELS.values()))
    for model in all_models:
        if model in prices:
            input_price, output_price = prices[model]
            print(f"{model:<15} ${input_price:<11.2f} ${output_price:<11.2f}")
        else:
            print(f"{model:<15} {'(not found)':<12} {'(not found)':<12}")
    # Output as Python dict for easy copy
    print("\n# Python dict format:")
    print("MODEL_PRICING = {")
    for model in all_models:
        if model in prices:
            input_price, output_price = prices[model]
            print(f'    "{model}": ({input_price:.2f}, {output_price:.2f}),')
    print("}")


if __name__ == "__main__":
    main()
