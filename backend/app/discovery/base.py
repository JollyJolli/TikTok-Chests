from abc import ABC, abstractmethod
from datetime import datetime

from pydantic import BaseModel


class DiscoveredStream(BaseModel):
    username: str
    display_name: str | None = None
    room_id: str | None = None
    viewer_count: int | None = None
    discovered_at: datetime


class DiscoveryResult(BaseModel):
    streams: list[DiscoveredStream] = []
    available: bool = False
    message: str


class DiscoveryProvider(ABC):
    name: str

    @abstractmethod
    async def discover(self) -> DiscoveryResult: ...
