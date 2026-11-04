from __future__ import annotations

from dataclasses import asdict, dataclass

from src.matcher import ProductMatcher
from src.models import RetailerListing
from src.normalization import tokenize


@dataclass(frozen=True)
class SearchResult:
    listing_id: str
    retailer: str
    raw_name: str
    canonical_id: str
    canonical_name: str
    assigned_category: str
    score: float
    components: dict[str, float]

    def to_dict(self) -> dict:
        return asdict(self)


INCOMPATIBLE_QUERY_TERMS = {
    "breast": {"broth", "pet", "dog", "cat"},
    "fresh": {"canned", "broth"},
}


class SearchIndex:
    """Precompute approved identity matches once, then serve cheap searches."""

    def __init__(self, listings: list[RetailerListing], matcher: ProductMatcher):
        self.records = []
        for listing in listings:
            match = matcher.match(listing)
            if match.canonical_id and match.canonical_name and match.assigned_category:
                self.records.append((listing, match))

    def search(self, query: str, *, retailer: str | None = None, limit: int = 10) -> list[SearchResult]:
        return _search_records(query, self.records, retailer=retailer, limit=limit)


def search(
    query: str,
    listings: list[RetailerListing],
    matcher: ProductMatcher,
    *,
    retailer: str | None = None,
    limit: int = 10,
) -> list[SearchResult]:
    return SearchIndex(listings, matcher).search(query, retailer=retailer, limit=limit)


def _search_records(
    query: str,
    records,
    *,
    retailer: str | None = None,
    limit: int = 10,
) -> list[SearchResult]:
    query_tokens = set(tokenize(query))
    if not query_tokens:
        return []

    results: list[SearchResult] = []
    seen: set[tuple[str, str]] = set()
    for listing, match in records:
        if retailer and listing.retailer.casefold() != retailer.casefold():
            continue
        candidate_tokens = set(tokenize(match.canonical_name)) | set(tokenize(listing.raw_name))
        if _is_incompatible(query_tokens, candidate_tokens):
            continue
        overlap = len(query_tokens & candidate_tokens) / len(query_tokens)
        coverage = len(query_tokens & candidate_tokens) / len(candidate_tokens)
        phrase_bonus = float(
            " ".join(tokenize(query)) in " ".join(tokenize(match.canonical_name))
        )
        score = 0.65 * overlap + 0.2 * coverage + 0.15 * phrase_bonus
        if overlap == 0:
            continue
        dedupe_key = (listing.retailer.casefold(), match.canonical_id)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        results.append(
            SearchResult(
                listing_id=listing.listing_id,
                retailer=listing.retailer,
                raw_name=listing.raw_name,
                canonical_id=match.canonical_id,
                canonical_name=match.canonical_name,
                assigned_category=match.assigned_category,
                score=round(score, 4),
                components={
                    "query_token_overlap": round(overlap, 4),
                    "candidate_token_coverage": round(coverage, 4),
                    "exact_phrase_bonus": phrase_bonus,
                    "identity_confidence": match.confidence,
                },
            )
        )
    return sorted(results, key=lambda item: (-item.score, item.listing_id))[:limit]


def _is_incompatible(query_tokens: set[str], candidate_tokens: set[str]) -> bool:
    if "milk" in query_tokens and "milk" not in candidate_tokens:
        return True
    if "breast" in query_tokens and "breast" not in candidate_tokens:
        return True
    if "milk" in query_tokens and "milk" in candidate_tokens:
        if ("oat" in query_tokens) != ("oat" in candidate_tokens):
            return True
    if "organic" in query_tokens and "organic" not in candidate_tokens:
        return True
    # Attribute overlap alone is not a useful product fallback.
    meaningful = query_tokens - {"organic", "fresh", "regular"}
    if meaningful and not meaningful & candidate_tokens:
        return True
    for query_term, blocked_terms in INCOMPATIBLE_QUERY_TERMS.items():
        if query_term in query_tokens and candidate_tokens & blocked_terms:
            return True
    return False

