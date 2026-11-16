from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.routes import _rate_limit, _requests, chests, health
from app.core.config import get_settings
from app.services.state import MemoryState


@pytest.mark.asyncio
async def test_health_and_empty_state():
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(settings=get_settings(), memory=MemoryState())))
    response = await health(request)
    assert response["status"] == "ok" and response["database"] is False
    assert await chests(request) == []


def test_monitor_rate_limit():
    _requests.clear()
    request = SimpleNamespace(
        client=SimpleNamespace(host="127.0.0.1"),
        app=SimpleNamespace(state=SimpleNamespace(settings=SimpleNamespace(monitor_requests_per_minute=1))),
    )
    _rate_limit(request)
    with pytest.raises(HTTPException) as error:
        _rate_limit(request)
    assert error.value.status_code == 429
