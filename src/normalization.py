from __future__ import annotations

import re
import unicodedata

from src.models import NormalizedProduct, NormalizedSize


BRAND_ALIASES = {
    "ocean catch co": "ocean catch",
    "ocean catch company": "ocean catch",
    "atl fresh": "atlantic fresh",
}

STOPWORDS = {"the", "a", "an", "brand", "package", "pkg"}
TOKEN_ALIASES = {"can": "canned", "tinned": "canned"}
SIZE_TOKENS = {
    "oz", "ounce", "ounces", "lb", "lbs", "pound", "pounds", "kg",
    "fl", "gal", "gallon", "gallons", "ct", "count",
}


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).lower()
    value = value.replace("×", "x")
    # Preserve decimal points in values such as 14.75, but remove punctuation
    # periods such as the one in "Co." so aliases remain stable.
    value = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", value)
    value = re.sub(r"[^a-z0-9.]+", " ", value)
    return " ".join(value.split())


def normalize_brand(value: str) -> str:
    normalized = normalize_text(value)
    return BRAND_ALIASES.get(normalized, normalized)


def tokenize(value: str) -> tuple[str, ...]:
    tokens = []
    for token in normalize_text(value).split():
        if token in STOPWORDS or token in SIZE_TOKENS or _is_number(token):
            continue
        tokens.append(TOKEN_ALIASES.get(token, token))
    return tuple(tokens)


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def normalize_size(value: str) -> NormalizedSize:
    text = normalize_text(value)
    if not text:
        return NormalizedSize(None, None, "unknown", False, "MISSING_SIZE")

    multipack = re.fullmatch(
        r"(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(fl oz|floz|oz|lb|kg|gal|ct|count)",
        text,
    )
    if multipack:
        quantity = float(multipack.group(1))
        item_value = float(multipack.group(2))
        return _convert(quantity * item_value, multipack.group(3))

    match = re.fullmatch(
        r"(\d+(?:\.\d+)?)\s*(fl oz|floz|fluid ounces?|ounces?|ounce|oz|pounds?|pound|lbs?|kilograms?|kg|gallons?|gallon|gal|count|ct)",
        text,
    )
    if not match:
        return NormalizedSize(None, None, "unknown", False, "INVALID_SIZE")
    return _convert(float(match.group(1)), match.group(2))


def _convert(value: float, unit: str) -> NormalizedSize:
    aliases = {
        "ounce": "oz",
        "ounces": "oz",
        "pound": "lb",
        "pounds": "lb",
        "lbs": "lb",
        "kilogram": "kg",
        "kilograms": "kg",
        "gallon": "gal",
        "gallons": "gal",
        "floz": "fl oz",
        "fluid ounce": "fl oz",
        "fluid ounces": "fl oz",
        "count": "ct",
    }
    unit = aliases.get(unit, unit)
    if value <= 0:
        return NormalizedSize(None, None, "unknown", False, "NON_POSITIVE_SIZE")
    if unit == "lb":
        return NormalizedSize(round(value * 16, 4), "oz", "weight", True)
    if unit == "kg":
        return NormalizedSize(round(value * 35.274, 4), "oz", "weight", True)
    if unit == "gal":
        return NormalizedSize(round(value * 128, 4), "fl oz", "volume", True)
    if unit == "oz":
        return NormalizedSize(value, "oz", "weight", True)
    if unit == "fl oz":
        return NormalizedSize(value, "fl oz", "volume", True)
    if unit == "ct":
        return NormalizedSize(value, "ct", "count", True)
    return NormalizedSize(None, None, "unknown", False, "UNSUPPORTED_UNIT")


def normalize_product(name: str, brand: str, size: str) -> NormalizedProduct:
    normalized_name = normalize_text(name)
    organic = True if "organic" in normalized_name.split() else None
    return NormalizedProduct(
        tokens=tokenize(name),
        brand=normalize_brand(brand),
        size=normalize_size(size),
        organic=organic,
    )

