"""Opt-in live feasibility probe. No credentials, cookies, claiming, or discovery.

Usage: python scripts/feasibility_probe.py <public-live-username> [seconds]
"""

import asyncio
import json
import sys
from typing import Any

from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, EnvelopeEvent, RoomUserSeqEvent


async def probe(username: str, seconds: int = 90) -> None:
    client = TikTokLiveClient(unique_id=f"@{username.lstrip('@')}")
    received: set[str] = set()

    @client.on(ConnectEvent)
    async def connected(event: Any) -> None:
        received.add("ConnectEvent")
        print(json.dumps({"event": "connected", "room_id": str(event.room_id)}), flush=True)

    @client.on(RoomUserSeqEvent)
    async def viewers(event: Any) -> None:
        received.add("RoomUserSeqEvent")
        print(json.dumps({"event": "viewers", "total": getattr(event, "total", None)}), flush=True)

    @client.on(EnvelopeEvent)
    async def envelope(event: Any) -> None:
        received.add("EnvelopeEvent")
        info = event.envelope_info
        safe = (
            {
                key: getattr(info, key, None)
                for key in (
                    "envelope_id",
                    "business_type",
                    "diamond_count",
                    "people_count",
                    "unpack_at",
                    "create_at",
                    "room_id",
                    "super_fan_count",
                )
            }
            if info
            else None
        )
        print(json.dumps({"event": "envelope", "fields": safe}, default=str), flush=True)

    task = await client.start(fetch_room_info=False, fetch_gift_info=False)
    try:
        await asyncio.wait_for(asyncio.shield(task), timeout=seconds)
    except asyncio.TimeoutError:
        await client.disconnect(close_client=True)
    print(json.dumps({"observed_event_types": sorted(received), "seconds": seconds}), flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Provide the username of a public account that is currently LIVE.")
    asyncio.run(probe(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 90))
