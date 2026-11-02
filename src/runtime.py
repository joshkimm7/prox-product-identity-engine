from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.matcher import ProductMatcher
from src.models import CanonicalProduct, RetailerListing
from src.search import SearchIndex


@dataclass(frozen=True)
class RuntimeData:
    catalog: list[CanonicalProduct]
    listings: list[RetailerListing]
    matcher: ProductMatcher
    search_index: SearchIndex


def load_runtime(fixtures_dir: Path = Path("fixtures")) -> RuntimeData:
    catalog = [CanonicalProduct(**row) for row in json.loads((fixtures_dir / "catalog.json").read_text(encoding="utf-8"))]
    listings = [RetailerListing(**row) for row in json.loads((fixtures_dir / "listings.json").read_text(encoding="utf-8"))]
    matcher = ProductMatcher(catalog)
    return RuntimeData(catalog, listings, matcher, SearchIndex(listings, matcher))
