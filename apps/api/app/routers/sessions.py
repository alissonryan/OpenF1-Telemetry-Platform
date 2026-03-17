"""
Sessions router for F1 session and meeting endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from httpx import AsyncClient

from app.core.config import settings
from app.core.dependencies import HTTPClient
from app.models.session import MeetingResponse, SessionResponse

router = APIRouter()


@router.get("/meetings", response_model=List[MeetingResponse])
async def get_meetings(
    client: AsyncClient = HTTPClient,
    year: Optional[int] = Query(None, description="Year filter"),
    meeting_key: Optional[int] = Query(None, description="Specific meeting key"),
) -> List[dict]:
    """
    Get F1 meetings (race weekends).

    Returns meeting information including circuit, country, and dates.
    """
    params: dict = {}
    if year:
        params["year"] = year
    if meeting_key:
        params["meeting_key"] = meeting_key

    response = await client.get(f"{settings.openf1_base_url}/meetings", params=params)
    response.raise_for_status()

    return response.json()


@router.get("/", response_model=List[SessionResponse])
async def get_sessions(
    client: AsyncClient = HTTPClient,
    meeting_key: Optional[int] = Query(None, description="Meeting key filter"),
    session_type: Optional[str] = Query(None, description="Session type filter"),
    year: Optional[int] = Query(None, description="Year filter"),
) -> List[dict]:
    """
    Get F1 sessions.

    Returns session information including type (practice, qualifying, race),
    dates, and circuit details.
    """
    params: dict = {}
    if meeting_key:
        params["meeting_key"] = meeting_key
    if session_type:
        params["session_type"] = session_type
    if year:
        params["year"] = year

    response = await client.get(f"{settings.openf1_base_url}/sessions", params=params)
    response.raise_for_status()

    return response.json()


@router.get("/weather")
async def get_weather(
    client: AsyncClient = HTTPClient,
    session_key: Optional[int] = Query(None, description="Session key filter"),
    limit: int = Query(100, ge=1, le=1000),
) -> List[dict]:
    """
    Get weather data for a session.

    Returns temperature, humidity, pressure, rainfall, wind data.
    """
    params: dict = {}
    if session_key:
        params["session_key"] = session_key

    response = await client.get(f"{settings.openf1_base_url}/weather", params=params)
    response.raise_for_status()
    data = response.json()

    return data[:limit]
