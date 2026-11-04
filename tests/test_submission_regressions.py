from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from src.api import app
from src.evaluation import GroundTruth, evaluate
from src.matcher import ProductMatcher
from src.models import RetailerListing
from src.normalization import normalize_size
from src.runtime import load_runtime


@pytest.fixture(scope="module")
def runtime():
    return load_runtime()


def listing(name="Ocean Catch Solid White Tuna canned", size="5 oz", brand="Ocean Catch", category="PANTRY"):
    return RetailerListing("PROBE", "FreshTown", name, brand, size, category, 500)


@pytest.mark.parametrize("size", ["5 fl oz", "50 oz", "-5 oz", "−5 oz", "0 oz", ""])
def test_untrusted_or_incompatible_size_abstains(runtime, size):
    result = runtime.matcher.match(listing(size=size))
    assert result.canonical_id is None
    assert result.reviewer_flag
    assert len(result.top_candidates) == 3


@pytest.mark.parametrize("name,brand,size,category", [
    ("Organic Farmhouse Chicken Breast", "Farmhouse", "16 oz", "MEAT"),
    ("Cultured Farms Blueberry Yogurt", "Cultured Farms", "6 oz", "DAIRY"),
    ("Ocean Catch Solid White Tuna fresh", "Ocean Catch", "5 oz", "PANTRY"),
])
def test_explicit_identity_conflicts_abstain(runtime, name, brand, size, category):
    assert runtime.matcher.match(listing(name, size, brand, category)).canonical_id is None


def test_negative_size_is_not_normalized_to_positive():
    assert not normalize_size("-5 oz").valid
    assert not normalize_size("2 x -8 oz").valid


def test_oat_milk_search_returns_oat_milk(runtime):
    results = runtime.search_index.search("oat milk")
    assert results
    assert all(result.canonical_id == "C113" for result in results)


def test_organic_chicken_does_not_return_regular_chicken_or_spinach(runtime):
    assert runtime.search_index.search("organic chicken breast") == []


def test_exact_signature_and_price_per_unit(runtime):
    result = runtime.matcher.match(listing())
    assert result.match_stage == "exact"
    assert result.price_per_unit_cents == 100
    assert result.price_unit == "oz"


def test_duplicate_signatures_abstain(runtime):
    product = runtime.catalog[0]
    matcher = ProductMatcher([product, replace(product, canonical_id="DUPLICATE")])
    assert matcher.match(listing()).canonical_id is None


def test_empty_catalog_abstains():
    assert ProductMatcher([]).match(listing()).canonical_id is None


def test_category_conflict_propagates_review_flag():
    payload = vars(listing()) | {"upstream_category": "SEAFOOD"}
    result = TestClient(app).post("/match", json=payload).json()
    assert result["assigned_category"] == "PANTRY"
    assert result["reviewer_flag"] is True


def test_evaluation_uses_expected_category_and_high_confidence_denominator(runtime):
    products = runtime.catalog
    first = runtime.matcher.match(listing())
    wrong = replace(first, canonical_id="C102", assigned_category="SEAFOOD", confidence=0.95)
    correct = replace(first, confidence=0.75)
    class Stub:
        catalog = products
        def match(self, item):
            return wrong if item.listing_id == "WRONG" else correct
    rows = [replace(listing(), listing_id="WRONG"), listing()]
    truth = [GroundTruth(item.listing_id, "C101", "authored") for item in rows]
    report = evaluate(Stub(), rows, truth)
    assert report.category_error_rate == 0.5
    assert report.high_confidence_false_positive_rate == 1.0
