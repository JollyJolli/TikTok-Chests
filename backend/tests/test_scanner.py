import pytest

from app.scanner.manager import normalize_username


@pytest.mark.parametrize(
    ("value", "expected"), [("@Creator.Name", "creator.name"), ("https://www.tiktok.com/@Creator_1/live", "creator_1")]
)
def test_normalize_username(value, expected):
    assert normalize_username(value) == expected


@pytest.mark.parametrize("value", ["https://evil.test/@name/live", "https://www.tiktok.com/other", "a", "name/../../"])
def test_rejects_arbitrary_urls_and_invalid_names(value):
    with pytest.raises(ValueError):
        normalize_username(value)
