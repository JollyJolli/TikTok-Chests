import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.scanner.manager import ScannerManager
from app.services.state import MemoryState

settings = get_settings()
logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    memory = MemoryState(settings.max_chests, settings.expired_retention_seconds)
    scanner = ScannerManager(memory, settings)
    app.state.settings = settings
    app.state.memory = memory
    app.state.scanner = scanner
    await scanner.start()
    try:
        yield
    finally:
        await scanner.stop()


app = FastAPI(
    title="TikTok-Chests API",
    version="1.0.0",
    lifespan=lifespan,
    description="In-memory radar backend for public TikTok LIVE envelope events.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)
app.include_router(router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    origin = websocket.headers.get("origin")
    if origin and origin not in settings.allowed_origins:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await websocket.accept()
    queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=100)

    async def deliver(message) -> None:
        item = message.model_dump(mode="json")
        if queue.full():
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
        queue.put_nowait(item)

    app.state.memory.subscribe(deliver)
    app.state.memory.stats.websocket_clients += 1
    try:
        snapshot = await app.state.memory.snapshot()
        await websocket.send_json({"type": "snapshot", "data": snapshot, "sequence": snapshot["sequence"]})
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=25)
                await websocket.send_json(item)
            except asyncio.TimeoutError:
                await websocket.send_json(
                    {"type": "stats.updated", "data": app.state.memory.stats.model_dump(mode="json")}
                )
    except WebSocketDisconnect:
        pass
    finally:
        app.state.memory.unsubscribe(deliver)
        app.state.memory.stats.websocket_clients = max(0, app.state.memory.stats.websocket_clients - 1)
