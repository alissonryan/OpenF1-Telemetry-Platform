"""
Telemetry router for real-time F1 data endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from httpx import AsyncClient

from app.core.config import settings
from app.core.dependencies import HTTPClient
from app.models.telemetry import (
    DriverResponse,
    LapResponse,
    PositionResponse,
    TelemetryResponse,
)

router = APIRouter()


@router.get("/car-data", response_model=List[TelemetryResponse])
async def get_car_data(
    client: AsyncClient = HTTPClient,
    session_key: Optional[int] = Query(None, description="Session key filter"),
    driver_number: Optional[int] = Query(None, description="Driver number filter"),
    speed_gt: Optional[int] = Query(None, description="Minimum speed filter"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results"),
) -> List[dict]:
    """
    Get real-time car telemetry data.

    Returns speed, throttle, brake, DRS, gear, and RPM data at 3.7Hz.
    """
    params: dict = {}
    if session_key:
        params["session_key"] = session_key
    if driver_number:
        params["driver_number"] = driver_number

    response = await client.get(f"{settings.openf1_base_url}/car_data", params=params)
    response.raise_for_status()
    data = response.json()

    # Apply additional filters
    if speed_gt is not None:
        data = [d for d in data if d.get("speed", 0) > speed_gt]

    return data[:limit]


@router.get("/position", response_model=List[PositionResponse])
async def get_position(
    client: AsyncClient = HTTPClient,
    session_key: Optional[int] = Query(None, description="Session key filter"),
    driver_number: Optional[int] = Query(None, description="Driver number filter"),
    limit: int = Query(100, ge=1, le=1000),
) -> List[dict]:
    """
    Get driver position data on track.

    Returns x, y, z coordinates and position at ~4 second intervals.
    """
    params: dict = {}
    if session_key:
        params["session_key"] = session_key
    if driver_number:
        params["driver_number"] = driver_number

    response = await client.get(f"{settings.openf1_base_url}/position", params=params)
    response.raise_for_status()
    data = response.json()

    return data[:limit]


@router.get("/laps", response_model=List[LapResponse])
async def get_laps(
    client: AsyncClient = HTTPClient,
    session_key: Optional[int] = Query(None, description="Session key filter"),
    driver_number: Optional[int] = Query(None, description="Driver number filter"),
    lap_number: Optional[int] = Query(None, description="Specific lap number"),
    limit: int = Query(100, ge=1, le=1000),
) -> List[dict]:
    """
    Get lap timing data.

    Returns sector times, lap duration, and speed trap data.
    """
    params: dict = {}
    if session_key:
        params["session_key"] = session_key
    if driver_number:
        params["driver_number"] = driver_number
    if lap_number:
        params["lap_number"] = lap_number

    response = await client.get(f"{settings.openf1_base_url}/laps", params=params)
    response.raise_for_status()
    data = response.json()

    return data[:limit]


@router.get("/drivers", response_model=List[DriverResponse])
async def get_drivers(
    client: AsyncClient = HTTPClient,
    session_key: Optional[int] = Query(None, description="Session key filter"),
    driver_number: Optional[int] = Query(None, description="Driver number filter"),
) -> List[dict]:
    """
    Get driver information.

    Returns driver names, team names, colors, and headshots.
    """
    params: dict = {}
    if session_key:
        params["session_key"] = session_key
    if driver_number:
        params["driver_number"] = driver_number

    response = await client.get(f"{settings.openf1_base_url}/drivers", params=params)
    response.raise_for_status()

    return response.json()
