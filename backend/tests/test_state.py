from datetime import datetime, timedelta, timezone

import pytest

from app.models.schemas import Chest, ChestStatus
from app.services.state import MemoryState


def chest(identifier: str, opens_delta: int = 60) -> Chest:
    now = datetime.now(timezone.utc)
    return Chest(
        id=identifier,
        streamer_username="creator",
        live_url="https://www.tiktok.com/@creator/live",
        coins=100,
        winners=10,
        opens_at=now + timedelta(seconds=opens_delta),
        detected_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_duplicate_updates_do_not_increment_total():
    state = MemoryState()
    assert await state.upsert_chest(chest("same")) is True
    assert await state.upsert_chest(chest("same")) is False
    assert state.stats.detected_total == 1 and len(state.chests) == 1


@pytest.mark.asyncio
async def test_expiration_and_retention_cleanup():
    state = MemoryState(retention_seconds=10)
    item = chest("old", -1)
    await state.upsert_chest(item)
    now = datetime.now(timezone.utc)
    assert await state.cleanup(now) == []
    assert state.chests["old"].status == ChestStatus.OPEN
    assert await state.cleanup(now + timedelta(seconds=11)) == ["old"]
    assert state.chests["old"].status == ChestStatus.EXPIRED
    await state.cleanup(now + timedelta(seconds=22))
    assert "old" not in state.chests


@pytest.mark.asyncio
async def test_size_limit_evicts_oldest():
    state = MemoryState(max_chests=2)
    for name in ("a", "b", "c"):
        await state.upsert_chest(chest(name))
    assert list(state.chests) == ["b", "c"]
