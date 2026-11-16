from datetime import datetime, timedelta, timezone

from app.models.schemas import Chest
from app.services.ranking import opportunity_score


def test_score_is_bounded_and_missing_is_none():
    empty = Chest(id="x", streamer_username="u", live_url="https://www.tiktok.com/@u/live")
    assert opportunity_score(empty) is None
    rich = Chest(
        id="y",
        streamer_username="u",
        live_url="https://www.tiktok.com/@u/live",
        coins=10000,
        winners=1000,
        participants=1000,
        opens_at=datetime.now(timezone.utc) + timedelta(seconds=1),
    )
    score = opportunity_score(rich)
    assert score is not None and 0 <= score <= 100
