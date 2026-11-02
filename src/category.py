from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

WorkerStatus = Literal["ok", "uncertain", "timeout"]


@dataclass(frozen=True)
class CategoryDecision:
    assigned_category: str
    source: str
    reviewer_flag: bool
    reason_codes: list[str]


def resolve_category(canonical_category: str | None, upstream_category: str | None, worker_status: WorkerStatus) -> CategoryDecision:
    """Never let an unreliable upstream worker erase canonical truth."""
    if canonical_category:
        if worker_status == "timeout":
            return CategoryDecision(canonical_category, "canonical_catalog", False, ["UPSTREAM_TIMEOUT", "CANONICAL_CATEGORY_PRESERVED"])
        if worker_status == "uncertain" or upstream_category == "CATEGORY_UNCERTAIN":
            return CategoryDecision(canonical_category, "canonical_catalog", False, ["UPSTREAM_UNCERTAIN", "CANONICAL_CATEGORY_PRESERVED"])
        if upstream_category and upstream_category != canonical_category:
            return CategoryDecision(canonical_category, "canonical_catalog", True, ["CATEGORY_CONFLICT", "CANONICAL_CATEGORY_PRESERVED"])
        return CategoryDecision(canonical_category, "canonical_catalog", False, ["CANONICAL_CATEGORY_USED"])
    if worker_status == "ok" and upstream_category and upstream_category != "CATEGORY_UNCERTAIN":
        return CategoryDecision(upstream_category, "upstream_worker", True, ["NO_CANONICAL_CATEGORY", "UPSTREAM_CATEGORY_REQUIRES_REVIEW"])
    return CategoryDecision("UNRESOLVED", "none", True, ["CATEGORY_UNRESOLVED"])
