"""Fetch model pricing from AWS and Azure APIs.

Claude models use hardcoded values because AWS Pricing API is incomplete
(missing output token prices and newer models).

Sources:
- AWS Pricing API: Nova, Llama models
- AWS Bedrock pricing page: Claude models (manually verified)
- Azure Retail Prices API: Azure OpenAI models
"""

import json
import sys
from collections import defaultdict

import boto3
import requests

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

# Azure OpenAI fallback pricing (used if API fetch fails)
AZURE_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4.5": (75.00, 150.00),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1-nano": (0.10, 0.40),
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
}

# Azure OpenAI models to fetch (skuName pattern -> our name)
AZURE_MODELS = {
    "gpt 4.5 0227": "gpt-4.5",
    "gpt 4.1 nano": "gpt-4.1-nano",
    "gpt 4.1 mini": "gpt-4.1-mini",
    "gpt 4.1": "gpt-4.1",
    "gpt-4o-mini-0718": "gpt-4o-mini",
    "gpt-4o-0806": "gpt-4o",
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


def fetch_azure_pricing() -> dict[str, tuple[float, float]]:
    """Fetch Azure OpenAI pricing from Retail Prices API. Returns {model: (input, output)} per 1M tokens."""
    api_url = "https://prices.azure.com/api/retail/prices"
    params = {"api-version": "2023-01-01-preview", "$filter": "productName eq 'Azure OpenAI'"}
    prices: dict[str, dict[str, float]] = defaultdict(dict)
    while True:
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        for item in data.get("Items", []):
            sku = item.get("skuName", "")
            meter = item.get("meterName", "")
            price = item.get("retailPrice", 0)
            # Skip batch, fine-tuning, cached, realtime, audio, training, hosting
            if any(x in meter.lower() for x in ["batch", "ft", "cach", "rt-", "aud", "train", "host", "transcr", "tts"]):
                continue
            # Only global pricing (most common)
            if "glbl" not in meter:
                continue
            # Find matching model (check longest patterns first to avoid partial matches)
            our_name = None
            for azure_sku, name in sorted(AZURE_MODELS.items(), key=lambda x: -len(x[0])):
                if sku.startswith(azure_sku):
                    our_name = name
                    break
            if not our_name:
                continue
            # Determine input/output
            if "Inp" in meter:
                prices[our_name]["input"] = price * 1000  # Convert per 1K to per 1M
            elif "Outp" in meter or "Out" in meter:
                prices[our_name]["output"] = price * 1000
        # Handle pagination
        next_link = data.get("NextPageLink")
        if not next_link:
            break
        api_url = next_link
        params = {}
    # Convert to our format
    result: dict[str, tuple[float, float]] = {}
    for model, p in prices.items():
        if "input" in p and "output" in p:
            result[model] = (p["input"], p["output"])
    return result


def get_all_pricing() -> dict[str, tuple[float, float]]:
    """Get pricing for all models, combining API and hardcoded values."""
    import concurrent.futures
    prices = {**CLAUDE_PRICING, **AZURE_PRICING}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        aws_future = executor.submit(fetch_bedrock_pricing)
        azure_future = executor.submit(fetch_azure_pricing)
        try:
            prices.update(aws_future.result(timeout=30))
        except Exception as e:
            print(f"Warning: Could not fetch AWS pricing: {e}", file=sys.stderr)
        try:
            prices.update(azure_future.result(timeout=30))
        except Exception as e:
            print(f"Warning: Could not fetch Azure pricing: {e}", file=sys.stderr)
    return prices


def _get_provider(model: str) -> str:
    """Get provider name for a model."""
    if model.startswith(("haiku", "sonnet", "opus")):
        return "Anthropic"
    if model.startswith("llama"):
        return "Meta"
    if model.startswith("nova"):
        return "Amazon"
    if model.startswith("gpt"):
        return "OpenAI"
    return "Unknown"


def main() -> None:
    """Fetch and print pricing for all models."""
    print("Fetching pricing from AWS and Azure...", file=sys.stderr)
    prices = get_all_pricing()
    live_models = set(API_MODELS.values()) | set(AZURE_MODELS.values())
    print(f"\n{'Provider':<10} {'Model':<15} {'Input/1M':<10} {'Output/1M':<10} {'Live':<4}")
    print("-" * 54)
    all_models = sorted(
        set(CLAUDE_PRICING.keys()) | set(API_MODELS.values()) | set(AZURE_PRICING.keys()),
        key=lambda m: (_get_provider(m), m),
    )
    for model in all_models:
        if model in prices:
            input_price, output_price = prices[model]
            live = "✓" if model in live_models else ""
            print(f"{_get_provider(model):<10} {model:<15} ${input_price:<9.2f} ${output_price:<9.2f} {live}")
        else:
            print(f"{_get_provider(model):<10} {model:<15} {'(not found)':<10} {'(not found)':<10}")


if __name__ == "__main__":
    main()
