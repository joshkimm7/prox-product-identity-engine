from __future__ import annotations

from difflib import SequenceMatcher

from src.models import CandidateScore, CanonicalProduct, MatchResult, RetailerListing
from src.normalization import normalize_product


INCOMPATIBLE_FORMS = {
    frozenset({"canned", "fresh"}),
    frozenset({"broth", "fresh"}),
    frozenset({"dry pet food", "fresh"}),
    frozenset({"dry pet food", "canned"}),
}


class ProductMatcher:
    def __init__(self, catalog: list[CanonicalProduct], threshold: float = 0.72, ambiguity_margin: float = 0.04):
        self.catalog = catalog
        self.threshold = threshold
        self.ambiguity_margin = ambiguity_margin

    def match(self, listing: RetailerListing) -> MatchResult:
        normalized = normalize_product(listing.raw_name, listing.brand_raw, listing.size_raw)
        candidates = [self._score(listing, product) for product in self.catalog]
        candidates.sort(key=lambda item: (-item.score, item.canonical_id))
        top = candidates[:3]
        best = top[0]
        margin = best.score - top[1].score if len(top) > 1 else best.score

        if normalized.size.reason in {"NON_POSITIVE_SIZE", "INVALID_SIZE"}:
            return self._abstain(listing, normalized.size, top, "INVALID_SIZE")
        if best.score < self.threshold:
            return self._abstain(listing, normalized.size, top, "LOW_CONFIDENCE")
        if margin < self.ambiguity_margin:
            return self._abstain(listing, normalized.size, top, "AMBIGUOUS_TOP_CANDIDATES")
        if "HARD_CONFLICT" in best.reason_codes:
            return self._abstain(listing, normalized.size, top, "INCOMPATIBLE_PRODUCT")

        product = next(item for item in self.catalog if item.canonical_id == best.canonical_id)
        exact = all(
            best.components[key] == 1.0
            for key in ("name", "brand", "size", "category")
        )
        return MatchResult(
            listing_id=listing.listing_id,
            canonical_id=product.canonical_id,
            canonical_name=product.name,
            assigned_category=product.category,
            normalized_size=normalized.size,
            match_stage="exact" if exact else "similarity",
            confidence=round(best.score, 4),
            reason_codes=best.reason_codes,
            reviewer_flag=False,
            top_candidates=top,
        )

    def _score(self, listing: RetailerListing, product: CanonicalProduct) -> CandidateScore:
        source = normalize_product(listing.raw_name, listing.brand_raw, listing.size_raw)
        # Include structured form in the comparison because canonical display names
        # do not consistently contain words such as "canned" or "fresh".
        target = normalize_product(
            f"{product.name} {product.form}",
            product.brand,
            f"{product.size_value} {product.size_unit}",
        )
        source_tokens = set(source.tokens)
        target_tokens = set(target.tokens)
        token_union = source_tokens | target_tokens
        token_score = len(source_tokens & target_tokens) / len(token_union) if token_union else 0.0
        sequence_score = SequenceMatcher(None, " ".join(source.tokens), " ".join(target.tokens)).ratio()
        name_score = max(token_score, sequence_score)
        brand_score = float(source.brand == target.brand and bool(source.brand))
        category_score = float(listing.retailer_category.upper() == product.category.upper())
        size_score = self._size_score(source.size, target.size)

        reasons: list[str] = []
        if brand_score:
            reasons.append("BRAND_MATCH")
        if size_score == 1.0:
            reasons.append("SIZE_MATCH")
        elif size_score == 0.0:
            reasons.append("SIZE_MISMATCH_OR_UNKNOWN")
        if category_score:
            reasons.append("CATEGORY_MATCH")

        listing_words = set(source.tokens)
        if product.form == "fresh" and ({"broth", "canned", "tinned"} & listing_words):
            reasons.append("HARD_CONFLICT")
        if product.category != "PET" and ({"dog", "cat", "pet"} & listing_words):
            reasons.append("HARD_CONFLICT")

        score = 0.4 * name_score + 0.25 * brand_score + 0.2 * size_score + 0.15 * category_score
        if "HARD_CONFLICT" in reasons:
            score *= 0.25
        return CandidateScore(
            canonical_id=product.canonical_id,
            canonical_name=product.name,
            score=round(score, 4),
            components={
                "name": round(name_score, 4),
                "brand": brand_score,
                "size": size_score,
                "category": category_score,
            },
            reason_codes=reasons,
        )

    @staticmethod
    def _size_score(source, target) -> float:
        if not source.valid or not target.valid:
            return 0.0
        if source.dimension != target.dimension:
            return 0.0
        difference = abs(source.value - target.value) / target.value
        if difference <= 0.01:
            return 1.0
        if difference <= 0.1:
            return 0.5
        return 0.0

    @staticmethod
    def _abstain(listing, normalized_size, top, reason) -> MatchResult:
        return MatchResult(
            listing_id=listing.listing_id,
            canonical_id=None,
            canonical_name=None,
            assigned_category=None,
            normalized_size=normalized_size,
            match_stage="abstain",
            confidence=round(top[0].score, 4),
            reason_codes=[reason],
            reviewer_flag=True,
            top_candidates=top,
        )

