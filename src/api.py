from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from src.category import WorkerStatus, resolve_category
from src.models import RetailerListing
from src.runtime import load_runtime
from src.search import search


class MatchRequest(BaseModel):
    listing_id: str = Field(min_length=1)
    retailer: str = Field(min_length=1)
    raw_name: str = Field(min_length=1)
    brand_raw: str = ""
    size_raw: str = ""
    retailer_category: str = Field(min_length=1)
    price_cents: int = Field(ge=0)
    upstream_category: str | None = None
    upstream_status: WorkerStatus = "ok"


def create_app(fixtures_dir: Path = Path("fixtures")) -> FastAPI:
    runtime = load_runtime(fixtures_dir)
    app = FastAPI(title="Prox Product Identity Engine", version="0.1.0")

    @app.get("/health")
    def health():
        return {"status": "ok", "canonical_products": len(runtime.catalog), "retailer_listings": len(runtime.listings), "offline": True}

    @app.post("/match")
    def match_listing(request: MatchRequest):
        listing = RetailerListing(**request.model_dump(exclude={"upstream_category", "upstream_status"}))
        result = runtime.matcher.match(listing)
        payload = result.to_dict()
        category = resolve_category(result.assigned_category, request.upstream_category, request.upstream_status)
        payload["category_decision"] = asdict(category)
        payload["assigned_category"] = category.assigned_category if result.canonical_id else None
        return payload

    @app.get("/search")
    def search_listings(q: str = Query(min_length=1), retailer: str | None = None, limit: int = Query(10, ge=1, le=50)):
        results = runtime.search_index.search(q, retailer=retailer, limit=limit)
        return {"query": q, "count": len(results), "results": [item.to_dict() for item in results]}

    @app.get("/listings/{listing_id}/match")
    def match_seeded_listing(listing_id: str):
        listing = next((item for item in runtime.listings if item.listing_id == listing_id), None)
        if listing is None:
            raise HTTPException(status_code=404, detail="listing_not_found")
        return runtime.matcher.match(listing).to_dict()

    return app


app = create_app()
