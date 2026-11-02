import pytest

from src.normalization import normalize_brand, normalize_size, normalize_text


def test_unicode_and_punctuation_normalization():
    assert normalize_text("  Tuna—Steak (Fresh)! ") == "tuna steak fresh"


def test_brand_alias():
    assert normalize_brand("Ocean Catch Co.") == "ocean catch"


@pytest.mark.parametrize(
    ("raw", "value", "unit", "dimension"),
    [
        ("1 lb", 16, "oz", "weight"),
        ("1 gal", 128, "fl oz", "volume"),
        ("1 kg", 35.274, "oz", "weight"),
        ("2 x 8 oz", 16, "oz", "weight"),
        ("12 count", 12, "ct", "count"),
    ],
)
def test_size_conversion(raw, value, unit, dimension):
    result = normalize_size(raw)
    assert result.valid
    assert result.value == pytest.approx(value)
    assert result.unit == unit
    assert result.dimension == dimension


def test_missing_size_is_explicitly_invalid():
    result = normalize_size("")
    assert not result.valid
    assert result.reason == "MISSING_SIZE"


def test_weight_and_volume_remain_distinct():
    assert normalize_size("16 oz").dimension != normalize_size("16 fl oz").dimension

