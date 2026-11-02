import json
from pathlib import Path

from src.matcher import ProductMatcher
from src.models import CanonicalProduct, RetailerListing
from src.search import search


ROOT = Path(__file__).parent.parent


def load_records(path, record_type):
    return [record_type(**row) for row in json.loads(path.read_text())]


def setup_data():
    catalog = load_records(ROOT / "fixtures/catalog.json", CanonicalProduct)
    listings = load_records(ROOT / "fixtures/listings.json", RetailerListing)
    return listings, ProductMatcher(catalog)


def test_chicken_breast_search_excludes_broth():
    listings, matcher = setup_data()
    results = search("chicken breast", listings, matcher)
    assert results
    assert results[0].canonical_id == "C103"
    assert all(result.canonical_id != "C104" for result in results)
    assert "query_token_overlap" in results[0].components


def test_search_filters_by_retailer_case_insensitively():
    listings, matcher = setup_data()
    results = search("salmon", listings, matcher, retailer="marketsquare")
    assert results
    assert all(result.retailer == "MarketSquare" for result in results)


def test_empty_query_returns_no_results():
    listings, matcher = setup_data()
    assert search("   ", listings, matcher) == []


def test_search_does_not_include_abstained_listings():
    listings, matcher = setup_data()
    results = search("tuna", listings, matcher)
    assert all(result.listing_id != "L007" for result in results)

