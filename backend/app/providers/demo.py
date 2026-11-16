from datetime import datetime, timedelta, timezone

from app.models.schemas import Chest, ConnectionStatus, StreamState


def demo_stream() -> StreamState:
    return StreamState(
        username="demo_creator",
        display_name="Demo Creator",
        viewer_count=842,
        status=ConnectionStatus.CONNECTED,
        source="demo",
        connected_at=datetime.now(timezone.utc),
    )


def demo_chest(index: int = 0) -> Chest:
    now = datetime.now(timezone.utc)
    return Chest(
        id=f"demo-{index}",
        streamer_username="demo_creator",
        streamer_display_name="Demo Creator",
        room_id="demo-room",
        live_url="https://www.tiktok.com/",
        coins=500 + index * 100,
        winners=25,
        reward_type="coins",
        opens_at=now + timedelta(minutes=3),
        expires_at=now + timedelta(minutes=4),
        chest_type="demo",
        viewer_count=842,
        detected_at=now,
        updated_at=now,
        source="demo",
    )
