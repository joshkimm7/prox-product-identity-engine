from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal


Dimension = Literal["weight", "volume", "count", "unknown"]
MatchStage = Literal["exact", "similarity", "abstain"]


@dataclass(frozen=True)
class CanonicalProduct:
    canonical_id: str
    name: str
    brand: str
    category: str
    type: str
    form: str
    organic: bool
    size_value: float
    size_unit: str


@dataclass(frozen=True)
class RetailerListing:
    listing_id: str
    retailer: str
    raw_name: str
    brand_raw: str
    size_raw: str
    retailer_category: str
    price_cents: int


@dataclass(frozen=True)
class NormalizedSize:
    value: float | None
    unit: str | None
    dimension: Dimension
    valid: bool
    reason: str | None = None


@dataclass(frozen=True)
class NormalizedProduct:
    tokens: tuple[str, ...]
    brand: str
    size: NormalizedSize
    organic: bool | None


@dataclass
class CandidateScore:
    canonical_id: str
    canonical_name: str
    score: float
    components: dict[str, float]
    reason_codes: list[str]


@dataclass
class MatchResult:
    listing_id: str
    canonical_id: str | None
    canonical_name: str | None
    assigned_category: str | None
    normalized_size: NormalizedSize
    match_stage: MatchStage
    confidence: float
    reason_codes: list[str]
    reviewer_flag: bool
    top_candidates: list[CandidateScore] = field(default_factory=list)
    price_per_unit_cents: float | None = None
    price_unit: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

