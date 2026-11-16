import asyncio
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone

from app.models.schemas import Chest, ChestStatus, ConnectionStatus, ScannerStats, StreamState, WSMessage

Subscriber = Callable[[WSMessage], Awaitable[None]]


class MemoryState:
    def __init__(self, max_chests: int = 1000, retention_seconds: int = 300) -> None:
        self.chests: OrderedDict[str, Chest] = OrderedDict()
        self.streams: dict[str, StreamState] = {}
        self.stats = ScannerStats()
        self.max_chests = max_chests
        self.retention = timedelta(seconds=retention_seconds)
        self._lock = asyncio.Lock()
        self._subscribers: set[Subscriber] = set()
        self._sequence = 0

    def subscribe(self, callback: Subscriber) -> None:
        self._subscribers.add(callback)

    def unsubscribe(self, callback: Subscriber) -> None:
        self._subscribers.discard(callback)

    async def _publish(self, kind: str, data: object) -> None:
        self._sequence += 1
        message = WSMessage(type=kind, data=data, sequence=self._sequence)  # type: ignore[arg-type]
        await asyncio.gather(*(cb(message) for cb in tuple(self._subscribers)), return_exceptions=True)

    async def upsert_chest(self, chest: Chest) -> bool:
        async with self._lock:
            existed = chest.id in self.chests
            if existed:
                original = self.chests[chest.id]
                chest.detected_at = original.detected_at
            else:
                self.stats.detected_total += 1
            self.chests[chest.id] = chest
            self.chests.move_to_end(chest.id)
            while len(self.chests) > self.max_chests:
                self.chests.popitem(last=False)
            self.stats.last_update_at = datetime.now(timezone.utc)
            self._recount()
        await self._publish("chest.updated" if existed else "chest.created", chest.model_dump(mode="json"))
        return not existed

    async def upsert_stream(self, stream: StreamState) -> None:
        async with self._lock:
            self.streams[stream.username] = stream
            self.stats.last_update_at = datetime.now(timezone.utc)
            self._recount()
        await self._publish("stream.updated", stream.model_dump(mode="json"))

    async def remove_stream(self, username: str) -> bool:
        async with self._lock:
            removed = self.streams.pop(username, None) is not None
            self._recount()
        return removed

    async def cleanup(self, now: datetime | None = None) -> list[str]:
        now = now or datetime.now(timezone.utc)
        expired_ids: list[str] = []
        opened: list[Chest] = []
        async with self._lock:
            for chest in list(self.chests.values()):
                if chest.status == ChestStatus.UPCOMING and chest.opens_at and chest.opens_at <= now:
                    chest.status = ChestStatus.OPEN
                    chest.updated_at = now
                    opened.append(chest)
                should_expire = bool(chest.expires_at and chest.expires_at <= now)
                if chest.status == ChestStatus.OPEN and chest.expires_at is None and chest.opens_at:
                    should_expire = chest.opens_at + self.retention <= now
                if should_expire and chest.status != ChestStatus.EXPIRED:
                    chest.status = ChestStatus.EXPIRED
                    chest.updated_at = now
                    expired_ids.append(chest.id)
                if chest.status == ChestStatus.EXPIRED and chest.updated_at + self.retention <= now:
                    self.chests.pop(chest.id, None)
            self._recount()
        for chest in opened:
            await self._publish("chest.updated", chest.model_dump(mode="json"))
        for chest_id in expired_ids:
            await self._publish("chest.expired", {"id": chest_id})
        return expired_ids

    def _recount(self) -> None:
        self.stats.monitored_streams = len(self.streams)
        self.stats.connected_streams = sum(s.status == ConnectionStatus.CONNECTED for s in self.streams.values())
        self.stats.queued_streams = sum(s.status == ConnectionStatus.QUEUED for s in self.streams.values())
        self.stats.active_chests = sum(c.status != ChestStatus.EXPIRED for c in self.chests.values())
        self.stats.expired_chests = sum(c.status == ChestStatus.EXPIRED for c in self.chests.values())

    async def snapshot(self) -> dict[str, object]:
        async with self._lock:
            return {
                "chests": [c.model_dump(mode="json") for c in self.chests.values()],
                "streams": [s.model_dump(mode="json") for s in self.streams.values()],
                "stats": self.stats.model_dump(mode="json"),
                "sequence": self._sequence,
            }
