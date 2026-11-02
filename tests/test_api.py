from fastapi.testclient import TestClient

from src.api import app

client = TestClient(app)


def test_health_reports_offline_fixture_counts():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["canonical_products"] == 40
    assert response.json()["retailer_listings"] == 90


def test_search_endpoint_excludes_broth_for_chicken_breast():
    payload = client.get("/search", params={"q": "chicken breast"}).json()
    assert payload["results"][0]["canonical_id"] == "C103"
    assert all(item["canonical_id"] != "C104" for item in payload["results"])


def test_match_endpoint_preserves_category_on_worker_timeout():
    response = client.post("/match", json={"listing_id": "API1", "retailer": "FreshTown", "raw_name": "Atlantic Fresh Tuna Steak", "brand_raw": "Atlantic Fresh", "size_raw": "1 lb", "retailer_category": "SEAFOOD", "price_cents": 1299, "upstream_status": "timeout"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["canonical_id"] == "C102"
    assert payload["assigned_category"] == "SEAFOOD"
    assert "UPSTREAM_TIMEOUT" in payload["category_decision"]["reason_codes"]


def test_unknown_seeded_listing_returns_404():
    response = client.get("/listings/DOES_NOT_EXIST/match")
    assert response.status_code == 404
