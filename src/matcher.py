from __future__ import annotations

from difflib import SequenceMatcher

from src.models import CandidateScore, CanonicalProduct, MatchResult, RetailerListing
from src.normalization import normalize_product, tokenize
from collections import defaultdict


# Explicit modifiers are identity evidence, not optional lexical overlap.
MODIFIER_GROUPS = (
    {"fresh", "canned", "frozen", "broth"},
    {"strawberry", "blueberry", "vanilla", "chocolate", "plain"},
    {"creamy", "crunchy"}, {"block", "shredded"},
)


def conflicts(source, product):
    words = set(source.tokens)
    target = set(tokenize(f"{product.name} {product.form}"))
    reasons = []
    if not source.size.valid:
        reasons.append("UNTRUSTED_SIZE")
    if source.organic is not None and source.organic != product.organic:
        reasons.append("ORGANIC_CONFLICT")
    if bool(words & {"dog", "cat", "pet"}) != (product.category == "PET"):
        reasons.append("PET_HUMAN_CONFLICT")
    for group in MODIFIER_GROUPS:
        left, right = words & group, target & group
        if left and right and left != right:
            reasons.append("MODIFIER_CONFLICT")
    if "milk" in words and "milk" in target and (("oat" in words) != ("oat" in target)):
        reasons.append("TYPE_CONFLICT")
    return reasons


class ProductMatcher:
    def __init__(self, catalog: list[CanonicalProduct], threshold: float = 0.72, ambiguity_margin: float = 0.04):
        self.catalog = catalog
        self.threshold = threshold
        self.ambiguity_margin = ambiguity_margin
        self.signatures = defaultdict(list)
        self.token_index = defaultdict(set)
        self.by_id = {p.canonical_id: p for p in catalog}
        for product in catalog:
            for name in (product.name, f"{product.name} {product.form}"):
                normalized = normalize_product(name, product.brand, f"{product.size_value} {product.size_unit}")
                key = self._signature(normalized)
                if product.canonical_id not in self.signatures[key]:
                    self.signatures[key].append(product.canonical_id)
            for token in tokenize(f"{product.name} {product.form}"):
                self.token_index[token].add(product.canonical_id)

    @staticmethod
    def _signature(product):
        return (tuple(sorted(set(product.tokens))), product.brand,
                product.size.dimension, product.size.value)


    def match(self, listing: RetailerListing) -> MatchResult:
        normalized = normalize_product(listing.raw_name, listing.brand_raw, listing.size_raw)
        exact_ids = self.signatures.get(self._signature(normalized), [])
        # A signature lookup precedes lexical retrieval. Duplicate signatures
        # remain ambiguous rather than silently selecting the first ID.
        exact_ids = [cid for cid in exact_ids if not conflicts(normalized, self.by_id[cid])]
        if len(exact_ids) == 1:
            product = self.by_id[exact_ids[0]]
            candidate = self._score(listing, product)
            return MatchResult(listing.listing_id, product.canonical_id, product.name,
                               product.category, normalized.size, "exact", 1.0,
                               ["EXACT_SIGNATURE"], False, [candidate],
                               round(listing.price_cents / normalized.size.value, 4), normalized.size.unit)
        retrieved = set()
        for token in normalized.tokens:
            retrieved.update(self.token_index.get(token, set()))
        # Unknown titles still receive three diagnostic alternatives.
        pool = [self.by_id[cid] for cid in sorted(retrieved)] if retrieved else self.catalog
        if len(pool) < 3:
            pool += [product for product in self.catalog if product.canonical_id not in retrieved][:3 - len(pool)]
        candidates = [self._score(listing, product) for product in pool]
        candidates.sort(key=lambda item: (-item.score, item.canonical_id))
        top = candidates[:3]
        if not top:
            return MatchResult(listing.listing_id, None, None, None, normalized.size,
                               "abstain", 0.0, ["EMPTY_CATALOG"], True, [])
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
        return MatchResult(
            listing_id=listing.listing_id,
            canonical_id=product.canonical_id,
            canonical_name=product.name,
            assigned_category=product.category,
            normalized_size=normalized.size,
            match_stage="similarity",
            confidence=round(best.score, 4),
            reason_codes=best.reason_codes,
            reviewer_flag=False,
            top_candidates=top,
            price_per_unit_cents=round(listing.price_cents / normalized.size.value, 4),
            price_unit=normalized.size.unit,
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

        reasons = conflicts(source, product)
        if source.size.valid and target.size.valid and (
            source.size.dimension != target.size.dimension or size_score != 1.0
        ):
            reasons.append("SIZE_CONFLICT")
        if reasons:
            reasons.append("HARD_CONFLICT")
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

