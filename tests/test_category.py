from src.category import resolve_category


def test_uncertain_worker_never_overwrites_canonical_category():
    result = resolve_category("SEAFOOD", "CATEGORY_UNCERTAIN", "uncertain")
    assert result.assigned_category == "SEAFOOD"
    assert result.source == "canonical_catalog"


def test_timeout_never_erases_canonical_category():
    result = resolve_category("PANTRY", None, "timeout")
    assert result.assigned_category == "PANTRY"
    assert "CANONICAL_CATEGORY_PRESERVED" in result.reason_codes


def test_conflicting_worker_category_is_flagged_for_review():
    result = resolve_category("MEAT", "PET", "ok")
    assert result.assigned_category == "MEAT"
    assert result.reviewer_flag
    assert "CATEGORY_CONFLICT" in result.reason_codes
