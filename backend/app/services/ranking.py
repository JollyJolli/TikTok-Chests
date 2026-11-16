from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.schemas import Chest


def opportunity_score(chest: "Chest", now: datetime | None = None) -> float | None:
    """Transparent 0-100 heuristic; never a probability or guaranteed outcome."""
    now = now or datetime.now(timezone.utc)
    parts: list[tuple[float, float]] = []
    if chest.coins is not None:
        parts.append((min(chest.coins / 1000, 1) * 25, 25))
    if chest.coins is not None and chest.winners:
        parts.append((min((chest.coins / chest.winners) / 50, 1) * 30, 30))
    if chest.winners is not None:
        parts.append((min(chest.winners / 100, 1) * 15, 15))
    if chest.participants is not None and chest.winners:
        parts.append((min(chest.winners / max(chest.participants, 1), 1) * 20, 20))
    elif chest.viewer_count is not None:
        parts.append(((1 - min(chest.viewer_count / 10000, 1)) * 10, 10))
    if chest.opens_at is not None:
        seconds = max((chest.opens_at - now).total_seconds(), 0)
        parts.append(((1 - min(seconds / 600, 1)) * 10, 10))
    if not parts:
        return None
    earned = sum(value for value, _ in parts)
    available = sum(weight for _, weight in parts)
    return round(earned / available * 100, 1)
