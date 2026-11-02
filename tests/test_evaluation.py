import json
from pathlib import Path

import pytest

from src.evaluation import GroundTruth, evaluate
from src.matcher import ProductMatcher
from src.models import CanonicalProduct, RetailerListing


ROOT = Path(__file__).parent.parent


def load_records(path, record_type):
    return [record_type(**row) for row in json.loads(path.read_text())]


def test_sample_evaluation_is_computed_from_independent_truth():
    catalog = load_records(ROOT / "fixtures/catalog.json", CanonicalProduct)
    listings = load_records(ROOT / "fixtures/listings.json", RetailerListing)
    truth = load_records(ROOT / "fixtures/ground_truth.json", GroundTruth)
    report = evaluate(ProductMatcher(catalog), listings, truth)

    assert report.total >= 80
    assert report.correct >= 80
    assert report.precision >= 0.98
    assert report.recall >= 0.85
    assert report.exact_id_accuracy >= 0.88
    assert report.abstention_rate > 0
    assert report.high_confidence_false_positive_rate == 0
    assert report.category_error_rate == 0


def test_evaluation_rejects_truth_for_missing_listing():
    matcher = ProductMatcher(
        [
            CanonicalProduct(
                "C1", "Milk", "Example", "DAIRY", "milk", "liquid", False, 1, "gal"
            )
        ]
    )
    with pytest.raises(ValueError, match="missing listings"):
        evaluate(
            matcher,
            [],
            [GroundTruth("DOES_NOT_EXIST", "C1", "Invalid truth fixture")],
        )


def test_evaluation_rejects_duplicate_truth_ids():
    matcher = ProductMatcher([])
    listing = RetailerListing("L1", "R", "Milk", "B", "1 gal", "DAIRY", 1)
    truth = [GroundTruth("L1", "ABSTAIN", "one"), GroundTruth("L1", "ABSTAIN", "two")]
    with pytest.raises(ValueError, match="duplicate"):
        evaluate(matcher, [listing], truth)

