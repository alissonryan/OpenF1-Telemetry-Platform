"""
Telemetry router for real-time F1 data endpoints.

Provides endpoints for:
- Car telemetry data (speed, throttle, brake, RPM, etc.)
- Driver position data (x, y, z coordinates)
- Lap timing data
- Driver information
- Interval data between drivers
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.models.telemetry import (
    DriverListResponse,
    DriverResponse,
    IntervalResponse,
    LapListResponse,
    LapResponse,
    PositionListResponse,
    PositionResponse,
    TelemetryListResponse,
    TelemetryResponse,
)
from app.services.openf1_client import (
    OpenF1APIError,
    OpenF1RateLimitError,
    openf1_client,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _raise_openf1_http_error(detail: str, exc: OpenF1APIError) -> None:
    """Map upstream OpenF1 failures to the correct HTTP response."""
    status_code = 429 if isinstance(exc, OpenF1RateLimitError) else 503
    raise HTTPException(status_code=status_code, detail=f"{detail}: {str(exc)}")


@router.get(
    "/car-data",
    response_model=TelemetryListResponse,
    summary="Get Car Telemetry Data",
    description="Retrieve real-time car telemetry data at ~3.7 Hz frequency.",
)
async def get_car_data(
    session_key: Optional[int] = Query(
        None,
        ge=1,
        description="Filter by session key",
    ),
    driver_number: Optional[int] = Query(
        None,
        ge=1,
        le=99,
        description="Filter by driver number",
    ),
    speed_gt: Optional[int] = Query(
        None,
        ge=0,
        le=400,
        description="Filter: speed greater than (km/h)",
    ),
    speed_lt: Optional[int] = Query(
        None,
        ge=0,
        le=400,
        description="Filter: speed less than (km/h)",
    ),
    throttle_gt: Optional[int] = Query(
        None,
        ge=0,
        le=100,
        description="Filter: throttle greater than (%)",
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Maximum number of records to return",
    ),
) -> TelemetryListResponse:
    """
    Get real-time car telemetry data.

    Returns speed, throttle, brake, DRS, gear, and RPM data at 3.7Hz.

    **Examples:**
    - `/telemetry/car-data?session_key=9471` - All telemetry for session
    - `/telemetry/car-data?session_key=9471&driver_number=1` - Telemetry for driver #1
    - `/telemetry/car-data?session_key=9471&speed_gt=300` - Only high-speed data
    """
    try:
        data = await openf1_client.get_car_data(
            session_key=session_key,
            driver_number=driver_number,
            speed_gt=speed_gt,
            speed_lt=speed_lt,
            throttle_gt=throttle_gt,
        )

        # Convert to response models
        telemetry = [TelemetryResponse(**t) for t in data[:limit]]

        return TelemetryListResponse(
            data=telemetry,
            total=len(telemetry),
            session_key=session_key or 0,
            driver_number=driver_number,
        )

    except OpenF1APIError as e:
        logger.error(f"Failed to fetch car data: {e}")
        _raise_openf1_http_error("Failed to fetch telemetry from OpenF1 API", e)


@router.get(
    "/position",
    response_model=PositionListResponse,
    summary="Get Driver Position Data",
    description="Retrieve driver position data (x, y, z coordinates) on track at ~4 second intervals.",
)
async def get_position(
    session_key: Optional[int] = Query(
        None,
        ge=1,
        description="Filter by session key",
    ),
    driver_number: Optional[int] = Query(
        None,
        ge=1,
        le=99,
        description="Filter by driver number",
    ),
    position: Optional[int] = Query(
        None,
        ge=1,
        le=20,
        description="Filter by race position",
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Maximum number of records to return",
    ),
) -> PositionListResponse:
    """
    Get driver position data on track.

    Returns x, y, z coordinates and race position at ~4 second intervals.

    **Examples:**
    - `/telemetry/position?session_key=9471` - All position data for session
    - `/telemetry/position?session_key=9471&driver_number=1` - Position for driver #1
    """
    try:
        data = await openf1_client.get_positions(
            session_key=session_key,
            driver_number=driver_number,
            position=position,
        )

        positions = [PositionResponse(**p) for p in data[:limit]]

        return PositionListResponse(
            data=positions,
            total=len(positions),
            session_key=session_key or 0,
        )

    except OpenF1APIError as e:
        logger.error(f"Failed to fetch position data: {e}")
        _raise_openf1_http_error("Failed to fetch position data from OpenF1 API", e)


@router.get(
    "/laps",
    response_model=LapListResponse,
    summary="Get Lap Timing Data",
    description="Retrieve lap timing data including sector times and speed traps.",
)
async def get_laps(
    session_key: Optional[int] = Query(
        None,
        ge=1,
        description="Filter by session key",
    ),
    driver_number: Optional[int] = Query(
        None,
        ge=1,
        le=99,
        description="Filter by driver number",
    ),
    lap_number: Optional[int] = Query(
        None,
        ge=1,
        description="Filter by specific lap number",
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Maximum number of records to return",
    ),
) -> LapListResponse:
    """
    Get lap timing data.

    Returns sector times, lap duration, and speed trap data.

    **Examples:**
    - `/telemetry/laps?session_key=9471` - All laps for session
    - `/telemetry/laps?session_key=9471&driver_number=1` - Laps for driver #1
    - `/telemetry/laps?session_key=9471&driver_number=1&lap_number=15` - Specific lap
    """
    try:
        data = await openf1_client.get_laps(
            session_key=session_key,
            driver_number=driver_number,
            lap_number=lap_number,
        )

        # Transform data to match LapResponse model
        laps = []
        for lap in data[:limit]:
            lap_data = {
                "session_key": lap.get("session_key", 0),
                "meeting_key": lap.get("meeting_key", 0),
                "driver_number": lap.get("driver_number", 0),
                "lap_number": lap.get("lap_number", 0),
                "date_start": lap.get("date_start", ""),
                "lap_duration": lap.get("lap_duration"),
                "is_pit_out_lap": lap.get("is_pit_out_lap"),
                "sectors": {
                    "sector_1": lap.get("duration_sector_1"),
                    "sector_2": lap.get("duration_sector_2"),
                    "sector_3": lap.get("duration_sector_3"),
                },
                "speed_traps": {
                    "i1_speed": lap.get("i1_speed"),
                    "i2_speed": lap.get("i2_speed"),
                    "st_speed": lap.get("st_speed"),
                },
            }
            laps.append(LapResponse(**lap_data))

        return LapListResponse(
            data=laps,
            total=len(laps),
            session_key=session_key or 0,
            driver_number=driver_number,
        )

    except OpenF1APIError as e:
        logger.error(f"Failed to fetch lap data: {e}")
        _raise_openf1_http_error("Failed to fetch lap data from OpenF1 API", e)


@router.get(
    "/drivers",
    response_model=DriverListResponse,
    summary="Get Driver Information",
    description="Retrieve driver information including names, teams, and colors.",
)
async def get_drivers(
    session_key: Optional[int] = Query(
        None,
        ge=1,
        description="Filter by session key",
    ),
    driver_number: Optional[int] = Query(
        None,
        ge=1,
        le=99,
        description="Get specific driver by number",
    ),
    team_name: Optional[str] = Query(
        None,
        description="Filter by team name",
    ),
) -> DriverListResponse:
    """
    Get driver information.

    Returns driver names, team names, colors, and headshots.

    **Examples:**
    - `/telemetry/drivers?session_key=9471` - All drivers in session
    - `/telemetry/drivers?session_key=9471&driver_number=1` - Specific driver
    - `/telemetry/drivers?team_name=Red Bull Racing` - Drivers by team
    """
    try:
        data = await openf1_client.get_drivers(
            session_key=session_key,
            driver_number=driver_number,
            team_name=team_name,
        )

        drivers = [DriverResponse(**d) for d in data]

        return DriverListResponse(
            data=drivers,
            total=len(drivers),
            session_key=session_key,
        )

    except OpenF1APIError as e:
        logger.error(f"Failed to fetch driver data: {e}")
        _raise_openf1_http_error("Failed to fetch driver data from OpenF1 API", e)


@router.get(
    "/intervals",
    response_model=List[IntervalResponse],
    summary="Get Timing Intervals",
    description="Retrieve timing interval data between drivers during a session.",
)
async def get_intervals(
    session_key: int = Query(
        ...,
        ge=1,
        description="Session key (required)",
    ),
    driver_number: Optional[int] = Query(
        None,
        ge=1,
        le=99,
        description="Filter by driver number",
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Maximum number of records to return",
    ),
) -> List[IntervalResponse]:
    """
    Get timing interval data between drivers.

    Returns gap to leader and interval to car ahead.

    **Examples:**
    - `/telemetry/intervals?session_key=9471` - All intervals for session
    - `/telemetry/intervals?session_key=9471&driver_number=1` - Intervals for driver #1
    """
    try:
        data = await openf1_client.get_intervals(
            session_key=session_key,
            driver_number=driver_number,
        )

        intervals = [IntervalResponse(**i) for i in data[:limit]]

        return intervals

    except OpenF1APIError as e:
        logger.error(f"Failed to fetch interval data: {e}")
        _raise_openf1_http_error("Failed to fetch interval data from OpenF1 API", e)


@router.get(
    "/fastest-lap",
    summary="Get Fastest Lap",
    description="Get the fastest lap information for a session or driver.",
)
async def get_fastest_lap(
    session_key: int = Query(
        ...,
        ge=1,
        description="Session key (required)",
    ),
    driver_number: Optional[int] = Query(
        None,
        ge=1,
        le=99,
        description="Get fastest lap for specific driver",
    ),
) -> dict:
    """
    Get fastest lap information.

    Returns lap time, sectors, and speed trap data for the fastest lap.

    **Examples:**
    - `/telemetry/fastest-lap?session_key=9471` - Fastest lap of the session
    - `/telemetry/fastest-lap?session_key=9471&driver_number=1` - Driver #1's fastest lap
    """
    try:
        # Get all laps
        data = await openf1_client.get_laps(
            session_key=session_key,
            driver_number=driver_number,
        )

        if not data:
            raise HTTPException(
                status_code=404,
                detail="No lap data found for the specified session/driver",
            )

        # Find fastest lap
        valid_laps = [l for l in data if l.get("lap_duration") is not None]
        if not valid_laps:
            raise HTTPException(
                status_code=404,
                detail="No valid lap times found",
            )

        fastest = min(valid_laps, key=lambda x: x.get("lap_duration", float("inf")))

        return {
            "driver_number": fastest.get("driver_number"),
            "lap_number": fastest.get("lap_number"),
            "lap_duration": fastest.get("lap_duration"),
            "sector_1": fastest.get("duration_sector_1"),
            "sector_2": fastest.get("duration_sector_2"),
            "sector_3": fastest.get("duration_sector_3"),
            "i1_speed": fastest.get("i1_speed"),
            "i2_speed": fastest.get("i2_speed"),
            "st_speed": fastest.get("st_speed"),
        }

    except OpenF1APIError as e:
        logger.error(f"Failed to fetch fastest lap: {e}")
        _raise_openf1_http_error("Failed to fetch lap data from OpenF1 API", e)
