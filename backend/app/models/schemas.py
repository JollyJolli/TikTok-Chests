from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class ChestStatus(StrEnum):
    UPCOMING = "upcoming"
    OPEN = "open"
    EXPIRED = "expired"


class ConnectionStatus(StrEnum):
    QUEUED = "queued"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    OFFLINE = "offline"
    ERROR = "error"
    STOPPED = "stopped"


class Chest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(min_length=1, max_length=200)
    streamer_username: str = Field(min_length=1, max_length=50)
    streamer_display_name: str | None = Field(None, max_length=100)
    avatar_url: str | None = None
    room_id: str | None = Field(None, max_length=100)
    live_url: str
    coins: int | None = Field(None, ge=0)
    winners: int | None = Field(None, ge=0)
    reward_type: str | None = Field(None, max_length=50)
    opens_at: datetime | None = None
    expires_at: datetime | None = None
    chest_type: str | None = Field(None, max_length=50)
    region: str | None = Field(None, max_length=10)
    participants: int | None = Field(None, ge=0)
    viewer_count: int | None = Field(None, ge=0)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: ChestStatus = ChestStatus.UPCOMING
    source: Literal["live", "demo"] = "live"

    @field_validator("opens_at", "expires_at", "detected_at", "updated_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    @computed_field
    @property
    def coins_per_winner(self) -> float | None:
        return round(self.coins / self.winners, 2) if self.coins is not None and self.winners else None

    @computed_field
    @property
    def opportunity_score(self) -> float | None:
        from app.services.ranking import opportunity_score

        return opportunity_score(self)


class StreamState(BaseModel):
    username: str
    display_name: str | None = None
    avatar_url: str | None = None
    room_id: str | None = None
    viewer_count: int | None = None
    status: ConnectionStatus = ConnectionStatus.QUEUED
    source: Literal["manual", "configured", "discovery", "demo"] = "manual"
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    connected_at: datetime | None = None
    last_event_at: datetime | None = None
    last_error: str | None = None
    reconnect_attempts: int = 0


class ScannerStats(BaseModel):
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    monitored_streams: int = 0
    connected_streams: int = 0
    queued_streams: int = 0
    active_chests: int = 0
    expired_chests: int = 0
    detected_total: int = 0
    events_received: int = 0
    connection_errors: int = 0
    websocket_clients: int = 0
    last_update_at: datetime | None = None
    last_discovery_at: datetime | None = None
    discovery_mode: Literal["manual", "automatic", "demo"] = "manual"
    discovery_available: bool = False
    discovery_message: str = (
        "No stable credential-free server discovery feed is enabled; "
        "add public LIVE usernames manually."
    )
    demo_mode: bool = False


class MonitorRequest(BaseModel):
    value: str = Field(min_length=2, max_length=200)


class MonitorResponse(BaseModel):
    accepted: bool
    username: str
    status: ConnectionStatus
    message: str


class WSMessage(BaseModel):
    type: Literal[
        "snapshot", "chest.created", "chest.updated", "chest.expired", "stream.updated", "stats.updated", "error"
    ]
    data: Any
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sequence: int = 0
