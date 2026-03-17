"""
Sessions router for F1 session and meeting endpoints.

Provides endpoints for:
- Listing F1 meetings (race weekends)
- Listing sessions within meetings
- Getting weather data for sessions
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.core.dependencies import get_http_client
from app.models.session import (
    MeetingListResponse,
    MeetingResponse,
    SessionListResponse,
    SessionResponse,
)
from app.models.telemetry import WeatherResponse
from app.services.openf1_client import (
    OpenF1APIError,
    OpenF1Client,
    openf1_client,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/meetings",
    response_model=MeetingListResponse,
    summary="Get F1 Meetings",
    description="Retrieve all meetings (race weekends) for a given year or specific meeting details.",
)
async def get_meetings(
    year: Optional[int] = Query(
        None,
        ge=1950,
        le=2100,
        description="Filter by championship year (e.g., 2024)",
    ),
    meeting_key: Optional[int] = Query(
        None,
        ge=1,
        description="Get a specific meeting by its key",
    ),
) -> MeetingListResponse:
    """
    Get F1 meetings (race weekends).

    Returns meeting information including circuit, country, and dates.

    **Examples:**
    - `/meetings` - All meetings
    - `/meetings?year=2024` - All meetings in 2024
    - `/meetings?meeting_key=1229` - Specific meeting
    """
    try:
        data = await openf1_client.get_meetings(year=year, meeting_key=meeting_key)

        meetings = [MeetingResponse(**m) for m in data]

        return MeetingListResponse(
            data=meetings,
            total=len(meetings),
            year=year,
        )

    except OpenF1APIError as e:
        logger.error(f"Failed to fetch meetings: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch meetings from OpenF1 API: {str(e)}",
        )


@router.get(
    "/",
    response_model=SessionListResponse,
    summary="Get F1 Sessions",
    description="Retrieve session information for F1 meetings.",
)
async def get_sessions(
    meeting_key: Optional[int] = Query(
        None,
        ge=1,
        description="Filter by meeting key",
    ),
    session_type: Optional[str] = Query(
        None,
        description="Filter by session type (Practice, Qualifying, Sprint, Race)",
    ),
    session_key: Optional[int] = Query(
        None,
        ge=1,
        description="Get a specific session by its key",
    ),
    year: Optional[int] = Query(
        None,
        ge=1950,
        le=2100,
        description="Filter by championship year",
    ),
) -> SessionListResponse:
    """
    Get F1 sessions.

    Returns session information including type (practice, qualifying, race),
    dates, and circuit details.

    **Examples:**
    - `/sessions` - All sessions
    - `/sessions?meeting_key=1229` - Sessions for a specific meeting
    - `/sessions?year=2024&session_type=Race` - All races in 2024
    """
    try:
        data = await openf1_client.get_sessions(
            meeting_key=meeting_key,
            session_type=session_type,
            session_key=session_key,
            year=year,
        )

        sessions = [SessionResponse(**s) for s in data]

        return SessionListResponse(
            data=sessions,
            total=len(sessions),
            meeting_key=meeting_key,
            year=year,
        )

    except OpenF1APIError as e:
        logger.error(f"Failed to fetch sessions: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch sessions from OpenF1 API: {str(e)}",
        )


@router.get(
    "/{session_key}/weather",
    response_model=List[WeatherResponse],
    summary="Get Session Weather Data",
    description="Retrieve weather data for a specific session.",
)
async def get_session_weather(
    session_key: int = Path(
        ...,
        ge=1,
        description="Session key to get weather for",
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Maximum number of records to return",
    ),
) -> List[WeatherResponse]:
    """
    Get weather data for a session.

    Returns temperature, humidity, pressure, rainfall, and wind data.

    **Example:**
    - `/sessions/9471/weather` - Weather data for session 9471
    """
    try:
        data = await openf1_client.get_weather(session_key=session_key)

        weather = [WeatherResponse(**w) for w in data[:limit]]

        return weather

    except OpenF1APIError as e:
        logger.error(f"Failed to fetch weather: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch weather data from OpenF1 API: {str(e)}",
        )


@router.get(
    "/{session_key}/stints",
    summary="Get Session Stint Data",
    description="Retrieve stint information (tyre usage periods) for a session.",
)
async def get_session_stints(
    session_key: int = Path(
        ...,
        ge=1,
        description="Session key to get stints for",
    ),
    driver_number: Optional[int] = Query(
        None,
        ge=1,
        le=99,
        description="Filter by driver number",
    ),
) -> List[dict]:
    """
    Get stint information for a session.

    Returns tyre compound and lap ranges for each driver's stints.

    **Example:**
    - `/sessions/9471/stints` - All stints for session 9471
    - `/sessions/9471/stints?driver_number=1` - Stints for driver #1
    """
    try:
        data = await openf1_client.get_stints(
            session_key=session_key,
            driver_number=driver_number,
        )
        return data

    except OpenF1APIError as e:
        logger.error(f"Failed to fetch stints: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch stint data from OpenF1 API: {str(e)}",
        )


@router.get(
    "/{session_key}/pit",
    summary="Get Session Pit Stop Data",
    description="Retrieve pit stop information for a session.",
)
async def get_session_pit_stops(
    session_key: int = Path(
        ...,
        ge=1,
        description="Session key to get pit stops for",
    ),
    driver_number: Optional[int] = Query(
        None,
        ge=1,
        le=99,
        description="Filter by driver number",
    ),
) -> List[dict]:
    """
    Get pit stop information for a session.

    Returns pit stop times and lap numbers.

    **Example:**
    - `/sessions/9471/pit` - All pit stops for session 9471
    """
    try:
        data = await openf1_client.get_pit(
            session_key=session_key,
            driver_number=driver_number,
        )
        return data

    except OpenF1APIError as e:
        logger.error(f"Failed to fetch pit stops: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch pit stop data from OpenF1 API: {str(e)}",
        )


@router.get(
    "/{session_key}/race-control",
    summary="Get Race Control Messages",
    description="Retrieve race control messages (flags, safety car, penalties).",
)
async def get_race_control(
    session_key: int = Path(
        ...,
        ge=1,
        description="Session key",
    ),
    category: Optional[str] = Query(
        None,
        description="Filter by category",
    ),
    flag: Optional[str] = Query(
        None,
        description="Filter by flag type",
    ),
) -> List[dict]:
    """
    Get race control messages for a session.

    Returns flags, safety car deployments, penalties, and other race control events.

    **Example:**
    - `/sessions/9471/race-control` - All race control messages
    - `/sessions/9471/race-control?flag=YELLOW` - Yellow flag incidents only
    """
    try:
        data = await openf1_client.get_race_control(
            session_key=session_key,
            category=category,
            flag=flag,
        )
        return data

    except OpenF1APIError as e:
        logger.error(f"Failed to fetch race control messages: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch race control data from OpenF1 API: {str(e)}",
        )


@router.get(
    "/{session_key}/team-radio",
    summary="Get Team Radio Transcripts",
    description="Retrieve team radio communications for a session.",
)
async def get_team_radio(
    session_key: int = Path(
        ...,
        ge=1,
        description="Session key",
    ),
    driver_number: Optional[int] = Query(
        None,
        ge=1,
        le=99,
        description="Filter by driver number",
    ),
) -> List[dict]:
    """
    Get team radio communications for a session.

    Returns transcripts and audio URLs for team radio messages.

    **Example:**
    - `/sessions/9471/team-radio` - All team radio for session 9471
    - `/sessions/9471/team-radio?driver_number=1` - Team radio for driver #1
    """
    try:
        data = await openf1_client.get_team_radio(
            session_key=session_key,
            driver_number=driver_number,
        )
        return data

    except OpenF1APIError as e:
        logger.error(f"Failed to fetch team radio: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch team radio data from OpenF1 API: {str(e)}",
        )
