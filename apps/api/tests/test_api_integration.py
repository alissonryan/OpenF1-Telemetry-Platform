#!/usr/bin/env python3
"""
Integration tests for the OpenF1 and Fast-F1 services.
"""

import logging
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.services.openf1_client import OpenF1APIError, openf1_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

STABLE_SESSION_KEY = 9472


def _skip_if_rate_limited(exc: OpenF1APIError) -> None:
    """Skip tests when the free OpenF1 tier rate limits the suite."""
    if "429" in str(exc) or "Rate limit exceeded" in str(exc):
        pytest.skip(f"OpenF1 rate limited this integration test: {exc}")


def _skip_if_rate_limited_response(response) -> None:
    """Skip HTTP-level integration tests when the upstream free tier throttles them."""
    if response.status_code in {429, 503} and "Rate limit" in response.text:
        pytest.skip(f"OpenF1 rate limited this integration test: {response.text}")


@pytest.fixture
def session_key() -> int:
    """Use a known 2024 race session instead of relying on API ordering."""
    return STABLE_SESSION_KEY


@pytest.fixture
async def api_client() -> AsyncClient:
    """Return an async test client bound to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


async def test_openf1_meetings() -> None:
    """Meetings endpoint should return 2024 race weekends."""
    try:
        meetings = await openf1_client.get_meetings(year=2024)
    except OpenF1APIError as exc:
        _skip_if_rate_limited(exc)
        raise

    assert isinstance(meetings, list)
    assert meetings, "Expected at least one meeting for 2024"
    assert meetings[0].get("meeting_name")


async def test_openf1_sessions(session_key: int) -> None:
    """Sessions endpoint should return a usable session key."""
    try:
        sessions = await openf1_client.get_sessions(year=2024)
    except OpenF1APIError as exc:
        _skip_if_rate_limited(exc)
        raise

    assert isinstance(sessions, list)
    assert sessions, "Expected at least one session for 2024"
    assert any(session.get("session_key") == session_key for session in sessions)


async def test_openf1_drivers(session_key: int) -> None:
    """Drivers endpoint should return at least one driver for the session."""
    try:
        drivers = await openf1_client.get_drivers(session_key=session_key)
    except OpenF1APIError as exc:
        _skip_if_rate_limited(exc)
        raise

    assert isinstance(drivers, list)
    assert drivers, f"Expected drivers for session {session_key}"
    assert drivers[0].get("driver_number") is not None


async def test_openf1_car_data(session_key: int) -> None:
    """Car data endpoint should return telemetry or a documented API limit."""
    try:
        data = await openf1_client.get_car_data(
            session_key=session_key,
            driver_number=1,
            date="2024-02-21T12:00:00+00:00",
        )
    except OpenF1APIError as exc:
        message = str(exc)
        if "422" in message or "429" in message or "Rate limit exceeded" in message:
            pytest.skip(f"OpenF1 limited this telemetry query: {message}")
        raise

    assert isinstance(data, list)


async def test_openf1_laps(session_key: int) -> None:
    """Laps endpoint should return lap timing data for the session."""
    try:
        laps = await openf1_client.get_laps(session_key=session_key)
    except OpenF1APIError as exc:
        _skip_if_rate_limited(exc)
        raise

    assert isinstance(laps, list)
    assert laps, f"Expected lap data for session {session_key}"
    assert laps[0].get("lap_number") is not None


async def test_openf1_weather(session_key: int) -> None:
    """Weather endpoint should return at least one weather sample."""
    try:
        weather = await openf1_client.get_weather(session_key=session_key)
    except OpenF1APIError as exc:
        _skip_if_rate_limited(exc)
        raise

    assert isinstance(weather, list)
    assert weather, f"Expected weather data for session {session_key}"


async def test_openf1_positions(session_key: int) -> None:
    """Positions endpoint should return position data for a driver."""
    try:
        positions = await openf1_client.get_positions(
            session_key=session_key,
            driver_number=1,
        )
    except OpenF1APIError as exc:
        _skip_if_rate_limited(exc)
        raise

    assert isinstance(positions, list)
    assert positions, f"Expected position data for session {session_key}"
    assert positions[0].get("position") is not None


async def test_openf1_stints(session_key: int) -> None:
    """Stints endpoint should return tyre stint data."""
    try:
        stints = await openf1_client.get_stints(session_key=session_key)
    except OpenF1APIError as exc:
        _skip_if_rate_limited(exc)
        raise

    assert isinstance(stints, list)
    assert stints, f"Expected stint data for session {session_key}"


async def test_openf1_pit(session_key: int) -> None:
    """Pit endpoint should return pit stop data when available."""
    try:
        pits = await openf1_client.get_pit(session_key=session_key)
    except OpenF1APIError as exc:
        _skip_if_rate_limited(exc)
        raise

    assert isinstance(pits, list)


async def test_prediction_pit_batch_uses_live_session_data(
    api_client: AsyncClient,
    session_key: int,
) -> None:
    """Pit-stop predictions should be generated from a live session snapshot."""
    response = await api_client.get(
        "/api/predictions/pit-stop/batch",
        params={"session_key": session_key},
    )

    if response.status_code == 429:
        pytest.skip(f"OpenF1 rate limited this integration test: {response.text}")

    assert response.status_code == 200
    data = response.json()
    assert data, f"Expected pit predictions for session {session_key}"
    assert len({prediction["driver_number"] for prediction in data}) == len(data)
    assert all("probability" in prediction for prediction in data)
    assert all(isinstance(prediction["reasons"], list) for prediction in data)


async def test_prediction_position_forecast_includes_driver_metadata(
    api_client: AsyncClient,
    session_key: int,
) -> None:
    """Position forecast should expose live driver/team metadata."""
    response = await api_client.get(
        "/api/predictions/position-forecast",
        params={"session_key": session_key, "laps_ahead": 5},
    )

    if response.status_code == 429:
        pytest.skip(f"OpenF1 rate limited this integration test: {response.text}")

    assert response.status_code == 200
    data = response.json()
    assert data["session_key"] == session_key
    assert data["predictions"], f"Expected forecast predictions for session {session_key}"
    first_prediction = data["predictions"][0]
    assert first_prediction["driver_name"]
    assert first_prediction["team_name"]


async def test_prediction_strategy_batch_uses_live_compounds(
    api_client: AsyncClient,
    session_key: int,
) -> None:
    """Strategy recommendations should reflect compounds observed in session data."""
    response = await api_client.get(
        "/api/predictions/strategy/batch",
        params={"session_key": session_key},
    )

    if response.status_code == 429:
        pytest.skip(f"OpenF1 rate limited this integration test: {response.text}")

    assert response.status_code == 200
    data = response.json()
    assert data, f"Expected strategy recommendations for session {session_key}"
    assert all(strategy["current_compound"] for strategy in data)
    assert all(strategy["risk_level"] in {"low", "medium", "high"} for strategy in data)


async def test_prediction_pit_batch_rejects_invalid_driver_numbers(
    api_client: AsyncClient,
    session_key: int,
) -> None:
    """Batch pit endpoint should surface invalid driver filters as client errors."""
    response = await api_client.get(
        "/api/predictions/pit-stop/batch",
        params={"session_key": session_key, "driver_numbers": "abc"},
    )

    assert response.status_code == 422


async def test_sessions_meetings_endpoint_maps_official_name(
    api_client: AsyncClient,
) -> None:
    """Meetings route should backfill official_name from OpenF1 payloads."""
    response = await api_client.get("/api/sessions/meetings", params={"year": 2024})

    _skip_if_rate_limited_response(response)

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]
    assert payload["data"][0]["official_name"]


async def test_sessions_endpoint_accepts_openf1_practice_type(
    api_client: AsyncClient,
) -> None:
    """Sessions route should accept OpenF1's generic Practice session_type."""
    response = await api_client.get("/api/sessions/", params={"meeting_key": 1229})

    _skip_if_rate_limited_response(response)

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]
    assert any(session["session_type"] == "Practice" for session in payload["data"])


async def test_f1db_drivers_endpoint_returns_paginated_drivers(
    api_client: AsyncClient,
) -> None:
    """F1DB drivers endpoint should return a stable paginated payload."""
    response = await api_client.get(
        "/api/f1db/drivers",
        params={"season": 2024, "page_size": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= len(payload["data"])
    assert payload["page"] == 1
    assert payload["page_size"] == 5
    assert payload["data"]
    assert payload["data"][0]["id"]
    assert payload["data"][0]["full_name"]


async def test_f1db_driver_standings_endpoint_returns_records(
    api_client: AsyncClient,
) -> None:
    """F1DB driver standings endpoint should expose season standings."""
    response = await api_client.get("/api/f1db/seasons/2024/standings/drivers")

    assert response.status_code == 200
    payload = response.json()
    assert payload["year"] == 2024
    assert payload["total"] == len(payload["data"])
    assert payload["data"]
    assert payload["data"][0]["driver_id"]


async def test_f1db_races_endpoint_accepts_circuit_filter(
    api_client: AsyncClient,
) -> None:
    """F1DB races endpoint should return circuit-filtered results without enum errors."""
    response = await api_client.get(
        "/api/f1db/races",
        params={"circuit_id": "avus", "page_size": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= len(payload["data"])
    assert payload["data"]
    assert all(race["circuit_id"] == "avus" for race in payload["data"])


async def test_fastf1_session_endpoint_returns_session_metadata(
    api_client: AsyncClient,
) -> None:
    """FastF1 session endpoint should derive session metadata from loaded session info."""
    response = await api_client.get(
        "/api/fastf1/session",
        params={"year": 2026, "grand_prix": 1, "session_type": "R"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["grand_prix"]
    assert payload["session_type"] == "Race"
    assert payload["session_name"] == "Race"
    assert payload["drivers"]


async def test_fastf1_laps_endpoint_returns_lap_payload(
    api_client: AsyncClient,
) -> None:
    """FastF1 laps endpoint should return lap rows once session metadata resolves."""
    response = await api_client.get(
        "/api/fastf1/laps",
        params={"year": 2026, "grand_prix": 1, "session_type": "R"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_info"]["session_type"] == "Race"
    assert payload["total_laps"] == len(payload["laps"])


async def test_fastf1_weather_endpoint_returns_summary(
    api_client: AsyncClient,
) -> None:
    """FastF1 weather endpoint should return a weather summary for the session."""
    response = await api_client.get(
        "/api/fastf1/weather",
        params={"year": 2026, "grand_prix": 1, "session_type": "R"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_info"]["session_type"] == "Race"
    assert "air_temp" in payload["summary"]
    assert "avg" in payload["summary"]["air_temp"]


def test_fastf1_service() -> None:
    """Fast-F1 service should initialize without raising exceptions."""
    from app.services.fastf1_service import fastf1_service

    assert fastf1_service is not None
    assert isinstance(fastf1_service._cache_enabled, bool)


def test_websocket_endpoint_accepts_path_without_trailing_slash() -> None:
    """WebSocket endpoint should accept the `/ws` path used by the frontend."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({"command": "ping"})
            message = websocket.receive_json()

    assert message["type"] == "pong"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
