import asyncio
import time

import pytest

from app.services.openf1_client import OpenF1Client, OpenF1RateLimitError


async def test_openf1_client_reuses_fresh_cached_response(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OpenF1Client()
    calls = 0

    async def fake_request(method: str, endpoint: str, params=None):
        nonlocal calls
        calls += 1
        return [{"meeting_key": 1229, "meeting_name": "Bahrain Grand Prix"}]

    monkeypatch.setattr(client, "_request", fake_request)
    monkeypatch.setattr(client, "_cache_policy_for", lambda endpoint, params=None: (60, 300))

    first = await client._get("meetings", {"year": 2024})
    second = await client._get("meetings", {"year": 2024})

    assert calls == 1
    assert first == second
    assert first is not second


async def test_openf1_client_deduplicates_concurrent_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OpenF1Client()
    calls = 0

    async def fake_request(method: str, endpoint: str, params=None):
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.01)
        return [{"session_key": 9472, "session_name": "Race"}]

    monkeypatch.setattr(client, "_request", fake_request)
    monkeypatch.setattr(client, "_cache_policy_for", lambda endpoint, params=None: (0, 0))

    first, second = await asyncio.gather(
        client._get("sessions", {"session_key": 9472}),
        client._get("sessions", {"session_key": 9472}),
    )

    assert calls == 1
    assert first == second


async def test_openf1_client_serves_stale_cache_after_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OpenF1Client()
    params = {"year": 2024}
    cache_key = client._cache_key("meetings", params)
    cached_payload = [{"meeting_key": 1229, "meeting_name": "Bahrain Grand Prix"}]

    client._response_cache[cache_key] = (
        time.monotonic() - 5,
        client._clone_payload(cached_payload),
    )

    async def fake_request(method: str, endpoint: str, params=None):
        raise OpenF1RateLimitError("Rate limit exceeded. Retry after 60s")

    monkeypatch.setattr(client, "_request", fake_request)
    monkeypatch.setattr(client, "_cache_policy_for", lambda endpoint, params=None: (1, 60))

    payload = await client._get("meetings", params)

    assert payload == cached_payload
    assert payload is not cached_payload
