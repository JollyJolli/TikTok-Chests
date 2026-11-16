import hashlib
from datetime import datetime, timezone
from typing import Any

from app.models.schemas import Chest, ChestStatus


class NonActionableEnvelopeError(ValueError):
    """Envelope lifecycle/update message without usable box data."""


def _attr(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _timestamp(value: Any) -> datetime | None:
    if value in (None, 0, ""):
        return None
    try:
        number = float(value)
        if number > 10_000_000_000:
            number /= 1000
        return datetime.fromtimestamp(number, tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return None


def _image_url(image: Any) -> str | None:
    if image is None:
        return None
    values = _attr(image, "url_list") or _attr(image, "urls") or []
    return str(values[0]) if values else None


def _positive_int(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _business_type(value: Any) -> tuple[int | None, str | None]:
    numeric = getattr(value, "value", value)
    try:
        numeric = int(numeric)
    except (TypeError, ValueError):
        numeric = None
    name = getattr(value, "name", None)
    if numeric == 19:
        return numeric, "super_fan"
    if name and name != "BUSINESS_TYPE_UNKNOWN":
        return numeric, name.removeprefix("BUSINESS_TYPE_").lower()
    return numeric, f"business_{numeric}" if numeric not in (None, 0) else None


def parse_envelope_event(
    event: Any,
    username: str,
    *,
    display_name: str | None = None,
    avatar_url: str | None = None,
    viewer_count: int | None = None,
    source: str = "live",
) -> Chest:
    info = _attr(event, "envelope_info")
    if info is None:
        raise ValueError("Envelope event has no envelope_info payload")
    raw_id = _attr(info, "envelope_id")
    room_id = str(_attr(info, "room_id") or "") or None
    opens_at = _timestamp(_attr(info, "unpack_at"))
    created_at = _timestamp(_attr(info, "create_at")) or datetime.now(timezone.utc)
    _, chest_type = _business_type(_attr(info, "business_type"))
    coins = _positive_int(_attr(info, "diamond_count"))
    winners = _positive_int(_attr(info, "people_count"))
    if coins is None and winners is None and opens_at is None:
        raise NonActionableEnvelopeError("Envelope contains no positive reward, winner count, or opening time")
    if not raw_id:
        identity = ":".join(
            str(value)
            for value in (
                username,
                room_id,
                created_at.isoformat(),
                _attr(info, "diamond_count"),
                _attr(info, "people_count"),
            )
        )
        raw_id = hashlib.sha256(identity.encode()).hexdigest()[:24]
    now = datetime.now(timezone.utc)
    status = ChestStatus.OPEN if opens_at and opens_at <= now else ChestStatus.UPCOMING
    return Chest(
        id=str(raw_id),
        streamer_username=username,
        streamer_display_name=display_name,
        avatar_url=avatar_url or _image_url(_attr(info, "send_user_avatar")),
        room_id=room_id,
        live_url=f"https://www.tiktok.com/@{username}/live",
        coins=coins,
        winners=winners,
        reward_type="coins" if coins is not None else None,
        opens_at=opens_at,
        chest_type=chest_type,
        participants=None,
        viewer_count=viewer_count,
        detected_at=created_at,
        updated_at=now,
        status=status,
        source=source,
    )
