"""Fetch model pricing from AWS, Azure, and GCP APIs.

Claude models use hardcoded values because AWS Pricing API is incomplete
(missing output token prices and newer models).

Sources:
- AWS Pricing API: Nova, Llama, DeepSeek models
- AWS Bedrock pricing page: Claude models (manually verified)
- Azure Retail Prices API: Azure OpenAI models
- GCP Cloud Billing API: Vertex AI Gemini models
"""

import json
import sys
from collections import defaultdict

import boto3
import requests
from tabulate import tabulate

REGION = "US East (Ohio)"

# Claude pricing hardcoded - AWS Pricing API is incomplete (missing output prices)
# Source: https://aws.amazon.com/bedrock/pricing/
# Bug: https://github.com/aws/aws-cli/issues/9567
CLAUDE_PRICING: dict[str, tuple[float, float]] = {
    "haiku-3": (0.25, 1.25),
    "haiku-3.5": (0.80, 4.00),
    "haiku-4.5": (1.00, 5.00),
    "sonnet-3": (3.00, 15.00),
    "sonnet-3.5": (3.00, 15.00),
    "sonnet-4": (3.00, 15.00),
    "sonnet-4.5": (3.00, 15.00),
    "opus-4": (15.00, 75.00),
    "opus-4.5": (5.00, 25.00),
}

# Non-Claude Bedrock pricing (fetched 2026-01-16, can be refreshed with --prices)
OTHER_PRICING: dict[str, tuple[float, float]] = {
    "deepseek-r1": (1.35, 5.40),
    "llama-3.1-70b": (0.72, 0.72),
    "llama-3.2-90b": (0.72, 0.72),
    "llama-3.3-70b": (0.72, 0.72),
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
    "gpt-5": (1.25, 10.00),
    "gpt-5.1": (1.25, 10.00),
    "gpt-5.2": (1.75, 14.00),
}

# GCP Vertex AI fallback pricing (used if API fetch fails)
# Source: https://cloud.google.com/vertex-ai/generative-ai/pricing
GCP_PRICING: dict[str, tuple[float, float]] = {
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-2.5-flash": (0.15, 0.60),
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-3-flash": (0.50, 3.00),
    "gemini-3-pro": (2.00, 12.00),
}

# Azure OpenAI models to fetch (skuName pattern -> our name)
AZURE_MODELS = {
    "gpt 4.5 0227": "gpt-4.5",
    "gpt 4.1 nano": "gpt-4.1-nano",
    "gpt 4.1 mini": "gpt-4.1-mini",
    "gpt 4.1": "gpt-4.1",
    "gpt-4o-mini-0718": "gpt-4o-mini",
    "gpt-4o-0806": "gpt-4o",
    "gpt 5.2": "gpt-5.2",
    "gpt 5.1": "gpt-5.1",
    "gpt 5": "gpt-5",
}

# Models to fetch from AWS Pricing API (API name -> our name)
API_MODELS = {
    "DeepSeek V3.1": "deepseek-v3.1",
    "Nova Micro": "nova-micro",
    "Nova Lite": "nova-lite",
    "Nova Pro": "nova-pro",
    "Llama 3.3 70B": "llama-3.3-70b",
    "Llama 3.2 90B": "llama-3.2-90b",
    "Llama 3.1 70B": "llama-3.1-70b",
}

# GCP Vertex AI models to fetch (SKU description pattern -> our name)
GCP_MODELS = {
    "Gemini 2.0 Flash": "gemini-2.0-flash",
    "Gemini 2.5 Flash": "gemini-2.5-flash",
    "Gemini 2.5 Pro": "gemini-2.5-pro",
    "Gemini 3 Flash": "gemini-3-flash",
    "Gemini 3 Pro": "gemini-3-pro",
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
            if any(
                x in meter.lower()
                for x in ["batch", "ft", "cach", "rt-", "aud", "train", "host", "transcr", "tts"]
            ):
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


def fetch_gcp_pricing() -> dict[str, tuple[float, float]]:
    """Fetch GCP Vertex AI pricing from Cloud Billing API. Returns {model: (input, output)} per 1M tokens."""
    from google.cloud import billing_v1

    client = billing_v1.CloudCatalogClient()
    # Find Vertex AI service
    vertex_service = None
    for service in client.list_services():
        if "Vertex AI" in service.display_name:
            vertex_service = service.name
            break
    if not vertex_service:
        return {}
    # Fetch SKUs for Vertex AI
    prices: dict[str, dict[str, float]] = defaultdict(dict)
    for sku in client.list_skus(parent=vertex_service):
        desc = sku.description
        # Match Gemini models
        model_name = None
        for pattern, our_name in GCP_MODELS.items():
            if pattern in desc:
                model_name = our_name
                break
        if not model_name:
            continue
        # Get pricing (first tier, USD)
        for tier in sku.pricing_info:
            for rate in tier.pricing_expression.tiered_rates:
                price_per_unit = rate.unit_price.units + rate.unit_price.nanos / 1e9
                # Pricing is per 1K characters, convert to per 1M tokens (approx 4 chars/token)
                # Actually GCP uses per 1K tokens for Gemini
                price_per_1m = price_per_unit * 1000
                if "Input" in desc or "input" in desc:
                    prices[model_name]["input"] = price_per_1m
                elif "Output" in desc or "output" in desc:
                    prices[model_name]["output"] = price_per_1m
                break
    # Convert to our format
    result: dict[str, tuple[float, float]] = {}
    for model, p in prices.items():
        if "input" in p and "output" in p:
            result[model] = (p["input"], p["output"])
    return result


def get_all_pricing() -> dict[str, tuple[float, float]]:
    """Get pricing for all models, combining API and hardcoded values."""
    import concurrent.futures

    prices = {**CLAUDE_PRICING, **OTHER_PRICING, **AZURE_PRICING, **GCP_PRICING}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        aws_future = executor.submit(fetch_bedrock_pricing)
        azure_future = executor.submit(fetch_azure_pricing)
        gcp_future = executor.submit(fetch_gcp_pricing)
        try:
            prices.update(aws_future.result(timeout=30))
        except Exception as e:
            print(f"Warning: Could not fetch AWS pricing: {e}", file=sys.stderr)
        try:
            prices.update(azure_future.result(timeout=30))
        except Exception as e:
            print(f"Warning: Could not fetch Azure pricing: {e}", file=sys.stderr)
        try:
            prices.update(gcp_future.result(timeout=30))
        except Exception as e:
            print(f"Warning: Could not fetch GCP pricing: {e}", file=sys.stderr)
    return prices


def _get_provider(model: str) -> str:
    """Get provider name for a model."""
    if model.startswith(("haiku", "sonnet", "opus")):
        return "Anthropic"
    if model.startswith("deepseek"):
        return "DeepSeek"
    if model.startswith("llama"):
        return "Meta"
    if model.startswith("nova"):
        return "Amazon"
    if model.startswith("gpt"):
        return "OpenAI"
    if model.startswith("gemini"):
        return "Google"
    return "Unknown"


def _get_host(model: str) -> str:
    """Get cloud host for a model."""
    if model in AZURE_PRICING:
        return "Azure"
    if model in GCP_PRICING:
        return "GCP"
    return "AWS"


def main() -> None:
    """Fetch and print pricing for all models."""
    print("Fetching pricing from AWS, Azure, and GCP...", file=sys.stderr)
    prices = get_all_pricing()
    live_models = set(API_MODELS.values()) | set(AZURE_MODELS.values()) | set(GCP_MODELS.values())
    all_models = sorted(
        set(CLAUDE_PRICING.keys())
        | set(OTHER_PRICING.keys())
        | set(API_MODELS.values())
        | set(AZURE_PRICING.keys())
        | set(GCP_PRICING.keys()),
        key=lambda m: (_get_provider(m), m),
    )
    rows = []
    for model in all_models:
        if model in prices:
            input_price, output_price = prices[model]
            live = "✓" if model in live_models else ""
            rows.append(
                [
                    _get_provider(model),
                    _get_host(model),
                    model,
                    f"${input_price:.2f}",
                    f"${output_price:.2f}",
                    live,
                ]
            )
        else:
            rows.append(
                [_get_provider(model), _get_host(model), model, "(not found)", "(not found)", ""]
            )
    print()
    print(
        tabulate(
            rows,
            headers=["Provider", "Host", "Model", "Input/1M", "Output/1M", "Live"],
            tablefmt="fancy_grid",
        )
    )


if __name__ == "__main__":
    main()
