"""Fetch model pricing from AWS Price List API."""

import json
import sys
import urllib.request
from typing import Any

OFFERS_URL = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrockFoundationModels/current/index.json"

# Map our model names to AWS service names
MODEL_SERVICE_NAMES = {
    "haiku-3": "Claude 3 Haiku",
    "haiku-35": "Claude 3.5 Haiku",
    "haiku-45": "Claude Haiku 4.5",
    "sonnet-35": "Claude 3.5 Sonnet",
    "sonnet-37": "Claude 3.7 Sonnet",
    "sonnet-4": "Claude Sonnet 4",
    "sonnet-45": "Claude Sonnet 4.5",
    "opus-4": "Claude Opus 4",
    "opus-41": "Claude Opus 4.1",
    "opus-45": "Claude Opus 4.5",
    "llama-33-70b": "Llama 3.3 70B Instruct",
    "llama-32-90b": "Llama 3.2 90B Instruct",
    "llama-31-70b": "Llama 3.1 70B Instruct",
    "nova-pro": "Amazon Nova Pro",
    "nova-premier": "Amazon Nova Premier",
}

REGION = "us-east-2"


def fetch_pricing() -> dict[str, Any]:
    """Fetch pricing data from AWS."""
    with urllib.request.urlopen(OFFERS_URL) as response:
        return json.loads(response.read().decode())


def extract_prices(data: dict[str, Any]) -> dict[str, tuple[float, float]]:
    """Extract input/output prices per 1M tokens for each model in us-east-2."""
    products = data.get("products", {})
    terms = data.get("terms", {}).get("OnDemand", {})
    # Build SKU to product info map
    sku_info: dict[str, dict] = {}
    for sku, product in products.items():
        attrs = product.get("attributes", {})
        if attrs.get("regionCode") == REGION:
            sku_info[sku] = attrs
    # Extract prices by SKU
    sku_prices: dict[str, dict[str, float]] = {}
    for sku, term_data in terms.items():
        if sku not in sku_info:
            continue
        for term_key, term in term_data.items():
            for dim_key, dim in term.get("priceDimensions", {}).items():
                desc = dim.get("description", "").lower()
                price = float(dim.get("pricePerUnit", {}).get("USD", "0"))
                if sku not in sku_prices:
                    sku_prices[sku] = {}
                if "input" in desc and "million" in desc:
                    sku_prices[sku]["input"] = price
                elif "output" in desc and "million" in desc:
                    sku_prices[sku]["output"] = price
    # Map model names to prices
    result: dict[str, tuple[float, float]] = {}
    for model_name, service_pattern in MODEL_SERVICE_NAMES.items():
        pattern_lower = service_pattern.lower()
        for sku, attrs in sku_info.items():
            service_name = attrs.get("servicename", "")
            usage_type = attrs.get("usagetype", "")
            # Match service name and basic input/output token types
            if pattern_lower in service_name.lower():
                if "InputTokenCount-Units" in usage_type and "_" not in usage_type.split(":")[-1].replace("InputTokenCount-Units", ""):
                    if sku in sku_prices and "input" in sku_prices[sku]:
                        if model_name not in result:
                            result[model_name] = (0.0, 0.0)
                        result[model_name] = (sku_prices[sku]["input"], result[model_name][1])
                elif "OutputTokenCount-Units" in usage_type and "_" not in usage_type.split(":")[-1].replace("OutputTokenCount-Units", ""):
                    if sku in sku_prices and "output" in sku_prices[sku]:
                        if model_name not in result:
                            result[model_name] = (0.0, 0.0)
                        result[model_name] = (result[model_name][0], sku_prices[sku]["output"])
    # Fill in missing models with 0
    for model_name in MODEL_SERVICE_NAMES:
        if model_name not in result:
            result[model_name] = (0.0, 0.0)
    return result


def main() -> None:
    """Fetch and print pricing for all models."""
    print("Fetching pricing from AWS...", file=sys.stderr)
    data = fetch_pricing()
    prices = extract_prices(data)
    print(f"\n{'Model':<15} {'Input/1M':<12} {'Output/1M':<12}")
    print("-" * 40)
    for model_name in MODEL_SERVICE_NAMES:
        input_price, output_price = prices.get(model_name, (0.0, 0.0))
        if input_price == 0 and output_price == 0:
            print(f"{model_name:<15} {'(not found)':<12} {'(not found)':<12}")
        else:
            print(f"{model_name:<15} ${input_price:<11.2f} ${output_price:<11.2f}")
    # Output as Python dict for easy copy
    print("\n# Python dict format:")
    print("MODEL_PRICING = {")
    for model_name in MODEL_SERVICE_NAMES:
        input_price, output_price = prices.get(model_name, (0.0, 0.0))
        print(f'    "{model_name}": ({input_price:.2f}, {output_price:.2f}),')
    print("}")


if __name__ == "__main__":
    main()
