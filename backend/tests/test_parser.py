from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from TikTokLiveProto.v3.webcast.model.data import EnvelopeBusinessType

from app.services.parser import NonActionableEnvelopeError, parse_envelope_event


def test_parses_supported_envelope_fields():
    event = SimpleNamespace(
        envelope_info=SimpleNamespace(
            envelope_id="abc",
            room_id=123,
            diamond_count=500,
            people_count=20,
            unpack_at=2_000_000_000,
            create_at=1_999_999_900,
            business_type=19,
            send_user_avatar=None,
        )
    )
    chest = parse_envelope_event(event, "creator", viewer_count=42)
    assert chest.id == "abc"
    assert chest.coins == 500 and chest.winners == 20
    assert chest.coins_per_winner == 25
    assert chest.chest_type == "super_fan"
    assert chest.live_url == "https://www.tiktok.com/@creator/live"
    assert chest.opens_at == datetime.fromtimestamp(2_000_000_000, tz=timezone.utc)


def test_missing_payload_is_rejected():
    with pytest.raises(ValueError, match="envelope_info"):
        parse_envelope_event({}, "creator")


def test_missing_optional_fields_stay_unavailable():
    chest = parse_envelope_event({"envelope_info": {"envelope_id": "x", "unpack_at": 2_000_000_000}}, "creator")
    assert chest.coins is None and chest.winners is None
    assert chest.reward_type is None


def test_zero_value_lifecycle_message_is_not_actionable():
    with pytest.raises(NonActionableEnvelopeError):
        parse_envelope_event(
            {"envelope_info": {"envelope_id": "x", "diamond_count": 0, "people_count": 0}}, "creator"
        )


def test_real_proto_business_enum_is_normalized():
    chest = parse_envelope_event(
        {
            "envelope_info": {
                "envelope_id": "x",
                "diamond_count": 20,
                "people_count": 16,
                "business_type": EnvelopeBusinessType.BUSINESS_TYPE_USER_DIAMOND,
            }
        },
        "creator",
    )
    assert chest.chest_type == "user_diamond"
