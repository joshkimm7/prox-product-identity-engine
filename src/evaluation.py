from __future__ import annotations

from dataclasses import asdict, dataclass

from src.matcher import ProductMatcher
from src.models import RetailerListing


ABSTAIN = "ABSTAIN"


@dataclass(frozen=True)
class GroundTruth:
    listing_id: str
    expected: str
    note: str


@dataclass(frozen=True)
class EvaluationCase:
    listing_id: str
    expected: str
    predicted: str
    confidence: float
    correct: bool
    high_confidence_false_positive: bool
    category_error: bool
    reason_codes: list[str]


@dataclass(frozen=True)
class EvaluationReport:
    total: int
    correct: int
    attempted_matches: int
    expected_matches: int
    correct_matches: int
    abstentions: int
    false_positives: int
    high_confidence_false_positives: int
    category_errors: int
    precision: float
    recall: float
    exact_id_accuracy: float
    abstention_rate: float
    high_confidence_false_positive_rate: float
    category_error_rate: float
    cases: list[EvaluationCase]

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate(
    matcher: ProductMatcher,
    listings: list[RetailerListing],
    truth: list[GroundTruth],
    *,
    high_confidence_threshold: float = 0.85,
) -> EvaluationReport:
    listings_by_id = {listing.listing_id: listing for listing in listings}
    truth_ids = {item.listing_id for item in truth}
    missing = truth_ids - listings_by_id.keys()
    if missing:
        raise ValueError(f"Ground truth references missing listings: {sorted(missing)}")
    if len(truth_ids) != len(truth):
        raise ValueError("Ground truth contains duplicate listing IDs")

    catalog_categories = {
        product.canonical_id: product.category for product in matcher.catalog
    }
    cases: list[EvaluationCase] = []
    for expected in truth:
        listing = listings_by_id[expected.listing_id]
        result = matcher.match(listing)
        predicted = result.canonical_id or ABSTAIN
        correct = predicted == expected.expected
        false_positive = predicted != ABSTAIN and predicted != expected.expected
        high_confidence_false_positive = (
            false_positive and result.confidence >= high_confidence_threshold
        )
        category_error = bool(
            result.canonical_id
            and result.assigned_category
            != catalog_categories.get(result.canonical_id)
        )
        cases.append(
            EvaluationCase(
                listing_id=listing.listing_id,
                expected=expected.expected,
                predicted=predicted,
                confidence=result.confidence,
                correct=correct,
                high_confidence_false_positive=high_confidence_false_positive,
                category_error=category_error,
                reason_codes=result.reason_codes,
            )
        )

    total = len(cases)
    attempted = sum(case.predicted != ABSTAIN for case in cases)
    expected_matches = sum(case.expected != ABSTAIN for case in cases)
    correct_matches = sum(
        case.correct and case.expected != ABSTAIN for case in cases
    )
    false_positives = sum(
        case.predicted != ABSTAIN and case.predicted != case.expected for case in cases
    )
    high_confidence_false_positives = sum(
        case.high_confidence_false_positive for case in cases
    )
    category_errors = sum(case.category_error for case in cases)
    abstentions = sum(case.predicted == ABSTAIN for case in cases)

    return EvaluationReport(
        total=total,
        correct=sum(case.correct for case in cases),
        attempted_matches=attempted,
        expected_matches=expected_matches,
        correct_matches=correct_matches,
        abstentions=abstentions,
        false_positives=false_positives,
        high_confidence_false_positives=high_confidence_false_positives,
        category_errors=category_errors,
        precision=_safe_divide(correct_matches, attempted),
        recall=_safe_divide(correct_matches, expected_matches),
        exact_id_accuracy=_safe_divide(sum(case.correct for case in cases), total),
        abstention_rate=_safe_divide(abstentions, total),
        high_confidence_false_positive_rate=_safe_divide(
            high_confidence_false_positives, attempted
        ),
        category_error_rate=_safe_divide(category_errors, attempted),
        cases=cases,
    )


def _safe_divide(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0

