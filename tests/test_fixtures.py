from scripts.generate_fixtures import ABSTAINS, CATALOG, TRICKY, build_fixtures


def test_fixture_generator_meets_required_counts():
    catalog, listings, truth = build_fixtures()
    assert len(catalog) >= 40
    assert len(listings) >= 80
    assert len(truth) == len(listings)
    assert len(TRICKY) >= 25
    assert len(ABSTAINS) >= 5


def test_fixture_generator_has_three_retailers_and_unique_ids():
    catalog, listings, truth = build_fixtures()
    assert len({item["retailer"] for item in listings}) >= 3
    assert len({item["canonical_id"] for item in catalog}) == len(catalog)
    assert len({item["listing_id"] for item in listings}) == len(listings)
    assert len({item["listing_id"] for item in truth}) == len(truth)


def test_required_starter_catalog_ids_are_present():
    ids = {row[0] for row in CATALOG}
    assert {f"C{number}" for number in range(101, 113)} <= ids

