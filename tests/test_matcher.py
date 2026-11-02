import json
from pathlib import Path

from src.matcher import ProductMatcher
from src.models import CanonicalProduct, RetailerListing


ROOT = Path(__file__).parent.parent


def load_records(path, record_type):
    return [record_type(**row) for row in json.loads(path.read_text())]


def test_core_listings_match_expected_products():
    catalog = load_records(ROOT / "fixtures/catalog.json", CanonicalProduct)
    listings = load_records(ROOT / "fixtures/listings.json", RetailerListing)
    matcher = ProductMatcher(catalog)
    expected = {
        "L001": "C101",
        "L002": "C102",
        "L003": "C103",
        "L004": "C104",
        "L005": "C105",
        "L006": "C106",
    }
    for listing in listings[:6]:
        result = matcher.match(listing)
        assert result.canonical_id == expected[listing.listing_id], result.to_dict()
        assert result.assigned_category is not None
        assert result.top_candidates


def test_ambiguous_tuna_abstains():
    catalog = load_records(ROOT / "fixtures/catalog.json", CanonicalProduct)
    listings = load_records(ROOT / "fixtures/listings.json", RetailerListing)
    listing = next(item for item in listings if item.raw_name == "Tuna")
    result = ProductMatcher(catalog).match(listing)
    assert result.canonical_id is None
    assert result.match_stage == "abstain"
    assert result.reviewer_flag


def test_explicit_zero_size_forces_review():
    catalog = load_records(ROOT / "fixtures/catalog.json", CanonicalProduct)
    listings = load_records(ROOT / "fixtures/listings.json", RetailerListing)
    listing = next(item for item in listings if item.size_raw == "0 oz")
    result = ProductMatcher(catalog).match(listing)
    assert result.canonical_id is None
    assert result.reason_codes == ["INVALID_SIZE"]


def test_broth_does_not_match_fresh_chicken():
    catalog = load_records(ROOT / "fixtures/catalog.json", CanonicalProduct)
    listing = RetailerListing(
        listing_id="ADV001",
        retailer="FreshTown",
        raw_name="Farmhouse Chicken Broth",
        brand_raw="Farmhouse",
        size_raw="16 fl oz",
        retailer_category="PANTRY",
        price_cents=399,
    )
    result = ProductMatcher(catalog).match(listing)
    assert result.canonical_id != "C103"

