import json
from pathlib import Path

from src.matcher import ProductMatcher
from src.models import CanonicalProduct, RetailerListing
from src.search import SearchIndex


ROOT = Path(__file__).parent.parent


def load_records(name, record_type):
    return [record_type(**row) for row in json.loads((ROOT / "fixtures" / name).read_text())]


def runtime():
    catalog = load_records("catalog.json", CanonicalProduct)
    listings = load_records("listings.json", RetailerListing)
    return catalog, listings, ProductMatcher(catalog)


def listing(raw_name, brand, size, category="PANTRY", listing_id="ADV"):
    return RetailerListing(listing_id, "FreshTown", raw_name, brand, size, category, 499)


def test_canned_tuna_does_not_match_raw_tuna_steak():
    _, _, matcher = runtime()
    result = matcher.match(listing("Ocean Catch Canned Tuna", "Ocean Catch", "5 oz"))
    assert result.canonical_id == "C101"
    assert all(item.canonical_id != "C102" or item.score < result.confidence for item in result.top_candidates)


def test_tinned_salmon_does_not_match_fresh_fillet():
    _, _, matcher = runtime()
    result = matcher.match(listing("Harbor Table Tinned Pink Salmon", "Harbor Table", "14.75 oz"))
    assert result.canonical_id == "C106"


def test_chicken_broth_does_not_match_meat():
    _, _, matcher = runtime()
    result = matcher.match(listing("Heritage Chicken Broth", "Heritage", "32 fl oz"))
    assert result.canonical_id == "C104"
    assert result.canonical_id != "C103"


def test_chicken_dog_food_does_not_match_human_food():
    _, _, matcher = runtime()
    result = matcher.match(listing("Happy Hound Chicken Dry Dog Food", "Happy Hound", "12 lb", "PET"))
    assert result.canonical_id == "C111"


def test_multipack_equals_single_total_size():
    _, _, matcher = runtime()
    result = matcher.match(listing("Nut House Creamy Peanut Butter", "Nut House", "2 x 8 oz"))
    assert result.canonical_id == "C117"
    assert result.normalized_size.value == 16


def test_gallon_equals_128_fluid_ounces():
    _, _, matcher = runtime()
    result = matcher.match(listing("Meadow Vale Whole Milk", "Meadow Vale", "1 gal", "DAIRY"))
    assert result.canonical_id == "C107"
    assert result.normalized_size.value == 128
    assert result.normalized_size.unit == "fl oz"


def test_organic_and_nonorganic_spinach_remain_distinguishable():
    _, _, matcher = runtime()
    organic = matcher.match(listing("Green Field Organic Baby Spinach", "Green Field", "5 oz", "PRODUCE", "ORG"))
    regular = matcher.match(listing("Green Field Baby Spinach Regular", "Green Field", "5 oz", "PRODUCE", "REG"))
    assert organic.canonical_id == "C109"
    assert regular.canonical_id in {"C110", None}
    assert regular.canonical_id != "C109"


def test_oat_milk_does_not_match_dairy_milk():
    _, _, matcher = runtime()
    result = matcher.match(listing("Oat Valley Original Oat Milk", "Oat Valley", "64 fl oz", "DAIRY_ALT"))
    assert result.canonical_id == "C113"
    assert result.canonical_id not in {"C107", "C108", "C114"}


def test_false_brand_alias_does_not_force_a_match():
    _, _, matcher = runtime()
    result = matcher.match(listing("Whole Milk", "Ocean Catch", "128 fl oz", "DAIRY"))
    assert result.canonical_id is None


def test_identical_title_uses_brand_to_separate_products():
    _, _, matcher = runtime()
    meadow = matcher.match(listing("Whole Milk", "Meadow Vale", "128 fl oz", "DAIRY", "M1"))
    dairy = matcher.match(listing("Whole Milk", "Dairy Best", "128 fl oz", "DAIRY", "M2"))
    assert meadow.canonical_id == "C107"
    assert dairy.canonical_id == "C108"


def test_missing_size_and_ambiguous_form_abstains():
    _, _, matcher = runtime()
    result = matcher.match(listing("Salmon", "Harbor Table", "", "SEAFOOD"))
    assert result.canonical_id is None
    assert result.reviewer_flag


def test_tied_peanut_butter_variants_abstain():
    _, _, matcher = runtime()
    result = matcher.match(listing("Peanut Butter", "Nut House", "16 oz"))
    assert result.canonical_id is None
    assert result.reason_codes == ["AMBIGUOUS_TOP_CANDIDATES"]


def test_unrelated_token_overlap_is_filtered_from_search():
    _, listings, matcher = runtime()
    results = SearchIndex(listings, matcher).search("chicken breast")
    assert results
    assert all(item.assigned_category != "PET" for item in results)
    assert all("Broth" not in item.canonical_name for item in results)

