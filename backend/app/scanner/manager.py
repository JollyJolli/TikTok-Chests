import asyncio
import logging
import random
import re
from datetime import datetime, timezone
from typing import Any

from app.core.config import Settings
from app.models.schemas import ConnectionStatus, StreamState
from app.services.parser import NonActionableEnvelopeError, parse_envelope_event
from app.services.state import MemoryState

logger = logging.getLogger(__name__)
USERNAME_RE = re.compile(r"^[A-Za-z0-9._]{2,24}$")
LIVE_URL_RE = re.compile(r"^https://(?:www\.)?tiktok\.com/@([A-Za-z0-9._]{2,24})/live/?(?:\?.*)?$", re.I)


def normalize_username(value: str) -> str:
    value = value.strip()
    match = LIVE_URL_RE.fullmatch(value)
    if match:
        value = match.group(1)
    value = value.lstrip("@").lower()
    if not USERNAME_RE.fullmatch(value):
        raise ValueError("Use a TikTok username or a https://www.tiktok.com/@username/live URL")
    return value


class ScannerManager:
    def __init__(self, state: MemoryState, settings: Settings) -> None:
        self.state = state
        self.settings = settings
        self.queue: asyncio.Queue[str] = asyncio.Queue(maxsize=settings.max_queue_size)
        self.tasks: dict[str, asyncio.Task[None]] = {}
        self.worker_task: asyncio.Task[None] | None = None
        self.cleanup_task: asyncio.Task[None] | None = None
        self.demo_task: asyncio.Task[None] | None = None
        self._stopping = asyncio.Event()
        self._semaphore = asyncio.Semaphore(settings.max_connections)

    async def start(self) -> None:
        self.state.stats.demo_mode = self.settings.demo_mode
        self.state.stats.discovery_mode = "demo" if self.settings.demo_mode else "manual"
        self.worker_task = asyncio.create_task(self._queue_worker(), name="scanner-queue")
        self.cleanup_task = asyncio.create_task(self._cleanup_loop(), name="state-cleanup")
        if self.settings.demo_mode:
            self.demo_task = asyncio.create_task(self._demo_loop(), name="demo-provider")
        for username in self.settings.initial_usernames:
            await self.add_stream(username, source="configured")

    async def stop(self) -> None:
        self._stopping.set()
        all_tasks = [task for task in [self.worker_task, self.cleanup_task, self.demo_task] if task]
        all_tasks.extend(self.tasks.values())
        for task in all_tasks:
            task.cancel()
        await asyncio.gather(*all_tasks, return_exceptions=True)

    async def add_stream(self, value: str, source: str = "manual") -> StreamState:
        username = normalize_username(value)
        existing = self.state.streams.get(username)
        if existing and existing.status not in {
            ConnectionStatus.ERROR,
            ConnectionStatus.OFFLINE,
            ConnectionStatus.STOPPED,
        }:
            return existing
        if len(self.state.streams) >= self.settings.max_queue_size + self.settings.max_connections:
            raise OverflowError("Monitor capacity reached")
        stream = StreamState(username=username, source=source, status=ConnectionStatus.QUEUED)  # type: ignore[arg-type]
        await self.state.upsert_stream(stream)
        try:
            self.queue.put_nowait(username)
        except asyncio.QueueFull as exc:
            await self.state.remove_stream(username)
            raise OverflowError("Monitor queue is full") from exc
        return stream

    async def remove_stream(self, value: str) -> bool:
        username = normalize_username(value)
        task = self.tasks.pop(username, None)
        if task:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        return await self.state.remove_stream(username)

    async def _queue_worker(self) -> None:
        while not self._stopping.is_set():
            username = await self.queue.get()
            if username in self.tasks and not self.tasks[username].done():
                self.queue.task_done()
                continue
            task = asyncio.create_task(self._monitor(username), name=f"monitor:{username}")
            self.tasks[username] = task
            task.add_done_callback(lambda _task, name=username: self.tasks.pop(name, None))
            self.queue.task_done()

    async def _monitor(self, username: str) -> None:
        async with self._semaphore:
            stream = self.state.streams[username]
            for attempt in range(self.settings.reconnect_max_attempts + 1):
                if self._stopping.is_set():
                    return
                stream.status = ConnectionStatus.CONNECTING if attempt == 0 else ConnectionStatus.RECONNECTING
                stream.reconnect_attempts = attempt
                await self.state.upsert_stream(stream)
                try:
                    await self._connect_tiktok(stream)
                    stream.status = ConnectionStatus.OFFLINE
                    stream.last_error = "The LIVE ended or the connection closed."
                    await self.state.upsert_stream(stream)
                    return
                except asyncio.CancelledError:
                    stream.status = ConnectionStatus.STOPPED
                    await self.state.upsert_stream(stream)
                    raise
                except Exception as exc:
                    self.state.stats.connection_errors += 1
                    message = str(exc)[:240] or exc.__class__.__name__
                    stream.last_error = message
                    logger.warning(
                        "stream_connection_failed", extra={"username": username, "attempt": attempt, "error": message}
                    )
                    if any(token in exc.__class__.__name__.lower() for token in ("blocked", "restricted", "age")):
                        break
                    if attempt < self.settings.reconnect_max_attempts:
                        delay = min(self.settings.reconnect_base_seconds * (2**attempt), 60) + random.random()
                        await asyncio.sleep(delay)
            stream.status = ConnectionStatus.ERROR
            await self.state.upsert_stream(stream)

    async def _connect_tiktok(self, stream: StreamState) -> None:
        try:
            from TikTokLive import TikTokLiveClient
            from TikTokLive.events import ConnectEvent, EnvelopeEvent, RoomUserSeqEvent
        except ImportError as exc:
            raise RuntimeError("TikTokLive is not installed; install backend requirements") from exc

        client = TikTokLiveClient(unique_id=f"@{stream.username}")

        @client.on(ConnectEvent)
        async def on_connect(event: Any) -> None:
            stream.status = ConnectionStatus.CONNECTED
            stream.room_id = str(getattr(event, "room_id", "")) or None
            stream.connected_at = datetime.now(timezone.utc)
            stream.last_error = None
            await self.state.upsert_stream(stream)

        @client.on(RoomUserSeqEvent)
        async def on_viewers(event: Any) -> None:
            count = getattr(event, "total", None) or getattr(event, "viewer_count", None)
            if count is not None:
                stream.viewer_count = max(int(count), 0)
                stream.last_event_at = datetime.now(timezone.utc)
                self.state.stats.events_received += 1
                await self.state.upsert_stream(stream)

        @client.on(EnvelopeEvent)
        async def on_envelope(event: Any) -> None:
            self.state.stats.events_received += 1
            stream.last_event_at = datetime.now(timezone.utc)
            try:
                chest = parse_envelope_event(
                    event,
                    stream.username,
                    display_name=stream.display_name,
                    avatar_url=stream.avatar_url,
                    viewer_count=stream.viewer_count,
                )
                await self.state.upsert_chest(chest)
            except NonActionableEnvelopeError:
                logger.debug("ignored_non_actionable_envelope", extra={"username": stream.username})
            except Exception:
                logger.exception("invalid_envelope_event", extra={"username": stream.username})

        await client.connect(fetch_room_info=False, fetch_gift_info=False)

    async def _cleanup_loop(self) -> None:
        while not self._stopping.is_set():
            await asyncio.sleep(self.settings.cleanup_interval_seconds)
            await self.state.cleanup()

    async def _demo_loop(self) -> None:
        from app.providers.demo import demo_chest, demo_stream

        stream = demo_stream()
        await self.state.upsert_stream(stream)
        index = 0
        while not self._stopping.is_set():
            await self.state.upsert_chest(demo_chest(index))
            index += 1
            await asyncio.sleep(45)
