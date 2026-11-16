import time
from collections import defaultdict, deque

from fastapi import APIRouter, HTTPException, Request, status

from app.models.schemas import MonitorRequest, MonitorResponse
from app.scanner.manager import normalize_username

router = APIRouter(prefix="/api")
_requests: dict[str, deque[float]] = defaultdict(deque)


def _rate_limit(request: Request) -> None:
    key = request.client.host if request.client else "unknown"
    now = time.monotonic()
    bucket = _requests[key]
    while bucket and bucket[0] < now - 60:
        bucket.popleft()
    limit = request.app.state.settings.monitor_requests_per_minute
    if len(bucket) >= limit:
        raise HTTPException(status_code=429, detail="Too many monitoring requests; try again later.")
    bucket.append(now)


@router.get("/health")
async def health(request: Request) -> dict[str, object]:
    return {"status": "ok", "demo_mode": request.app.state.settings.demo_mode, "database": False}


@router.get("/stats")
async def stats(request: Request):
    request.app.state.memory._recount()
    return request.app.state.memory.stats


@router.get("/chests")
async def chests(request: Request, include_expired: bool = False):
    values = list(request.app.state.memory.chests.values())
    return values if include_expired else [value for value in values if value.status != "expired"]


@router.get("/streams")
async def streams(request: Request):
    return list(request.app.state.memory.streams.values())


@router.post("/streams", response_model=MonitorResponse, status_code=status.HTTP_202_ACCEPTED)
async def add_stream(payload: MonitorRequest, request: Request) -> MonitorResponse:
    _rate_limit(request)
    try:
        stream = await request.app.state.scanner.add_stream(payload.value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except OverflowError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return MonitorResponse(
        accepted=True,
        username=stream.username,
        status=stream.status,
        message="Stream accepted for public LIVE monitoring.",
    )


@router.delete("/streams/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_stream(username: str, request: Request) -> None:
    _rate_limit(request)
    try:
        removed = await request.app.state.scanner.remove_stream(normalize_username(username))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not removed:
        raise HTTPException(status_code=404, detail="Stream is not monitored")
