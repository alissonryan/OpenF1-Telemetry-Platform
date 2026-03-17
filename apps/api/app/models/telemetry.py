"""Pydantic models for telemetry data."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TelemetryResponse(BaseModel):
    """Car telemetry data response model."""

    date: str
    session_key: int
    meeting_key: int
    driver_number: int
    speed: int = Field(..., ge=0, le=400, description="Speed in km/h")
    throttle: int = Field(..., ge=0, le=100, description="Throttle percentage")
    brake: bool = Field(..., description="Brake status")
    drs: int = Field(..., ge=0, le=14, description="DRS status code")
    n_gear: int = Field(..., ge=0, le=8, description="Gear number")
    rpm: int = Field(..., ge=0, le=15000, description="Engine RPM")


class PositionResponse(BaseModel):
    """Driver position data response model."""

    date: str
    session_key: int
    meeting_key: int
    driver_number: int
    position: int = Field(..., ge=1, le=20)
    x: float = Field(..., description="X coordinate on track")
    y: float = Field(..., description="Y coordinate on track")
    z: float = Field(..., description="Z coordinate on track")


class LapResponse(BaseModel):
    """Lap timing data response model."""

    session_key: int
    meeting_key: int
    driver_number: int
    lap_number: int
    date_start: str
    lap_duration: Optional[float] = Field(None, description="Lap time in seconds")
    i1_speed: Optional[int] = Field(None, description="Intermediary 1 speed")
    i2_speed: Optional[int] = Field(None, description="Intermediary 2 speed")
    st_speed: Optional[int] = Field(None, description="Speed trap speed")
    is_pit_out_lap: Optional[bool] = None


class DriverResponse(BaseModel):
    """Driver information response model."""

    driver_number: int
    broadcast_name: str
    full_name: str
    name_acronym: str = Field(..., min_length=3, max_length=3)
    team_name: str
    team_colour: str = Field(..., description="Hex color code")
    country_code: str = Field(..., min_length=3, max_length=3)
    headshot_url: Optional[str] = None
