"""
Pydantic models for F1 telemetry data.

These models define the structure and validation for:
- Car telemetry (speed, throttle, brake, RPM, etc.)
- Position data (x, y, z coordinates)
- Lap timing data
- Driver information
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class DRSStratus(int, Enum):
    """DRS status codes as per OpenF1 API."""

    OFF = 0
    POSSIBLE = 1
    ACTIVE = 2
    UNKNOWN = 8


class TyreCompound(str, Enum):
    """F1 tyre compound types."""

    SOFT = "SOFT"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    INTERMEDIATE = "INTERMEDIATE"
    WET = "WET"
    UNKNOWN = "UNKNOWN"


# ==================== Car Telemetry Models ====================


class CarDataBase(BaseModel):
    """Base model for car telemetry data."""

    date: str = Field(..., description="ISO timestamp of the measurement")
    session_key: int = Field(..., description="Unique session identifier")
    meeting_key: int = Field(..., description="Unique meeting identifier")
    driver_number: int = Field(..., ge=1, le=99, description="Driver's car number")


class TelemetryResponse(CarDataBase):
    """Car telemetry data response model."""

    speed: int = Field(..., ge=0, le=400, description="Speed in km/h")
    throttle: int = Field(..., ge=0, le=100, description="Throttle percentage")
    brake: bool = Field(..., description="Brake status (True = braking)")
    drs: int = Field(
        ...,
        ge=0,
        le=14,
        description="DRS status code (0=off, 1=possible, 2=active)",
    )
    n_gear: int = Field(..., ge=0, le=8, description="Gear number (0=neutral)")
    rpm: int = Field(..., ge=0, le=15000, description="Engine RPM")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "date": "2024-03-02T14:30:00.000",
                    "session_key": 9471,
                    "meeting_key": 1229,
                    "driver_number": 1,
                    "speed": 312,
                    "throttle": 100,
                    "brake": False,
                    "drs": 2,
                    "n_gear": 8,
                    "rpm": 11800,
                }
            ]
        }
    }


class TelemetryListResponse(BaseModel):
    """Response model for a list of telemetry data points."""

    data: List[TelemetryResponse]
    total: int = Field(..., description="Total number of records")
    session_key: int
    driver_number: Optional[int] = None


# ==================== Position Models ====================


class PositionResponse(CarDataBase):
    """Driver position data response model (track coordinates)."""

    position: Optional[int] = Field(None, ge=1, le=25, description="Race position")
    x: float = Field(..., description="X coordinate on track")
    y: float = Field(..., description="Y coordinate on track")
    z: float = Field(..., description="Z coordinate (elevation)")
    date: str = Field(..., description="ISO timestamp")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "date": "2024-03-02T14:30:00.000",
                    "session_key": 9471,
                    "meeting_key": 1229,
                    "driver_number": 1,
                    "position": 1,
                    "x": 1540.5,
                    "y": -320.2,
                    "z": 12.8,
                }
            ]
        }
    }


class PositionListResponse(BaseModel):
    """Response model for position data list."""

    data: List[PositionResponse]
    total: int
    session_key: int


# ==================== Lap Models ====================


class SectorTimes(BaseModel):
    """Sector time breakdown for a lap."""

    sector_1: Optional[float] = Field(None, description="Sector 1 time in seconds")
    sector_2: Optional[float] = Field(None, description="Sector 2 time in seconds")
    sector_3: Optional[float] = Field(None, description="Sector 3 time in seconds")


class SpeedTrap(BaseModel):
    """Speed trap data for a lap."""

    i1_speed: Optional[int] = Field(None, description="Intermediary 1 speed (km/h)")
    i2_speed: Optional[int] = Field(None, description="Intermediary 2 speed (km/h)")
    st_speed: Optional[int] = Field(None, description="Speed trap speed (km/h)")


class LapResponse(BaseModel):
    """Lap timing data response model."""

    session_key: int
    meeting_key: int
    driver_number: int = Field(..., ge=1, le=99)
    lap_number: int = Field(..., ge=1)
    date_start: str = Field(..., description="ISO timestamp of lap start")
    lap_duration: Optional[float] = Field(None, description="Lap time in seconds")
    is_pit_out_lap: Optional[bool] = Field(None, description="Whether this was a pit out lap")
    sectors: Optional[SectorTimes] = Field(None, description="Sector times")
    speed_traps: Optional[SpeedTrap] = Field(None, description="Speed trap data")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_key": 9471,
                    "meeting_key": 1229,
                    "driver_number": 1,
                    "lap_number": 15,
                    "date_start": "2024-03-02T14:30:00.000",
                    "lap_duration": 92.418,
                    "is_pit_out_lap": False,
                    "sectors": {
                        "sector_1": 30.123,
                        "sector_2": 32.456,
                        "sector_3": 29.839,
                    },
                    "speed_traps": {
                        "i1_speed": 285,
                        "i2_speed": 310,
                        "st_speed": 325,
                    },
                }
            ]
        }
    }


class LapListResponse(BaseModel):
    """Response model for lap data list."""

    data: List[LapResponse]
    total: int
    session_key: int
    driver_number: Optional[int] = None


# ==================== Driver Models ====================


class DriverResponse(BaseModel):
    """Driver information response model."""

    driver_number: int = Field(..., ge=1, le=99)
    broadcast_name: Optional[str] = Field(None, description="Name used in broadcasts")
    full_name: Optional[str] = Field(None, description="Driver's full name")
    first_name: Optional[str] = Field(None, description="Driver's first name")
    last_name: Optional[str] = Field(None, description="Driver's last name")
    name_acronym: Optional[str] = Field(
        None,
        min_length=3,
        max_length=3,
        description="3-letter driver code",
    )
    team_name: Optional[str] = Field(None, description="Team/constructor name")
    team_colour: Optional[str] = Field(
        None,
        description="Team's hex color code (e.g., '00A19C')",
    )
    country_code: Optional[str] = Field(
        None,
        min_length=3,
        max_length=3,
        description="ISO country code",
    )
    headshot_url: Optional[str] = Field(None, description="URL to driver headshot image")
    session_key: Optional[int] = Field(None, description="Session key if session-specific")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "driver_number": 1,
                    "broadcast_name": "M VERSTAPPEN",
                    "full_name": "Max Verstappen",
                    "first_name": "Max",
                    "last_name": "Verstappen",
                    "name_acronym": "VER",
                    "team_name": "Red Bull Racing",
                    "team_colour": "3671C6",
                    "country_code": "NED",
                    "headshot_url": "https://...",
                }
            ]
        }
    }

    @field_validator("team_colour")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        """Validate hex color format."""
        if not all(c in "0123456789ABCDEFabcdef" for c in v):
            raise ValueError("Invalid hex color format")
        return v.upper()


class DriverListResponse(BaseModel):
    """Response model for driver list."""

    data: List[DriverResponse]
    total: int
    session_key: Optional[int] = None


# ==================== Pit Stop Models ====================


class PitResponse(BaseModel):
    """Pit stop data response model."""

    session_key: int
    meeting_key: int
    driver_number: int
    date: str = Field(..., description="ISO timestamp of pit entry")
    lap_number: int = Field(..., ge=1)
    pit_duration: Optional[float] = Field(None, description="Pit stop duration in seconds")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_key": 9471,
                    "meeting_key": 1229,
                    "driver_number": 1,
                    "date": "2024-03-02T14:45:00.000",
                    "lap_number": 18,
                    "pit_duration": 2.45,
                }
            ]
        }
    }


# ==================== Stint Models ====================


class StintResponse(BaseModel):
    """Stint data response model (tyre usage period)."""

    session_key: int
    meeting_key: int
    driver_number: int
    stint_number: int = Field(..., ge=1)
    lap_start: int = Field(..., ge=1, description="First lap of stint")
    lap_end: int = Field(..., ge=1, description="Last lap of stint")
    compound: TyreCompound = Field(..., description="Tyre compound used")
    tyre_life_at_start: Optional[int] = Field(
        None,
        ge=0,
        description="Tyre age at stint start (laps already used)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_key": 9471,
                    "meeting_key": 1229,
                    "driver_number": 1,
                    "stint_number": 1,
                    "lap_start": 1,
                    "lap_end": 17,
                    "compound": "MEDIUM",
                    "tyre_life_at_start": 0,
                }
            ]
        }
    }


# ==================== Weather Models ====================


class WeatherResponse(BaseModel):
    """Weather data response model."""

    session_key: int
    meeting_key: int
    date: str = Field(..., description="ISO timestamp")
    air_temperature: Optional[float] = Field(None, description="Air temperature in Celsius")
    track_temperature: Optional[float] = Field(None, description="Track temperature in Celsius")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Relative humidity %")
    pressure: Optional[float] = Field(None, description="Atmospheric pressure in hPa")
    rainfall: Optional[int] = Field(None, ge=0, le=1, description="Rainfall indicator (0/1)")
    wind_direction: Optional[int] = Field(None, ge=0, le=360, description="Wind direction in degrees")
    wind_speed: Optional[float] = Field(None, ge=0, description="Wind speed in m/s")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_key": 9471,
                    "meeting_key": 1229,
                    "date": "2024-03-02T14:30:00.000",
                    "air_temperature": 28.5,
                    "track_temperature": 42.3,
                    "humidity": 45.0,
                    "pressure": 1013.2,
                    "rainfall": 0,
                    "wind_direction": 180,
                    "wind_speed": 3.5,
                }
            ]
        }
    }


# ==================== Interval Models ====================


class IntervalResponse(BaseModel):
    """Timing interval data between drivers."""

    session_key: int
    meeting_key: int
    date: str
    driver_number: int
    gap_to_leader: Optional[float] = Field(None, description="Gap to leader in seconds")
    interval: Optional[float] = Field(None, description="Gap to car ahead in seconds")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_key": 9471,
                    "meeting_key": 1229,
                    "date": "2024-03-02T14:30:00.000",
                    "driver_number": 11,
                    "gap_to_leader": 5.432,
                    "interval": 1.234,
                }
            ]
        }
    }


# ==================== Race Control Models ====================


class RaceControlResponse(BaseModel):
    """Race control message response model."""

    session_key: int
    meeting_key: int
    date: str
    category: Optional[str] = Field(None, description="Message category")
    message: Optional[str] = Field(None, description="Control message text")
    flag: Optional[str] = Field(None, description="Flag type if applicable")
    scope: Optional[str] = Field(None, description="Scope of the message")
    sector: Optional[int] = Field(None, description="Affected sector")
    driver_number: Optional[int] = Field(None, description="Affected driver if applicable")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_key": 9471,
                    "meeting_key": 1229,
                    "date": "2024-03-02T14:30:00.000",
                    "category": "Flag",
                    "message": "YELLOW FLAG",
                    "flag": "YELLOW",
                    "scope": "Track",
                    "sector": 2,
                }
            ]
        }
    }


# ==================== Team Radio Models ====================


class TeamRadioResponse(BaseModel):
    """Team radio transcript response model."""

    session_key: int
    meeting_key: int
    date: str
    driver_number: int
    recording_url: Optional[str] = Field(None, description="URL to audio recording")
    transcript: Optional[str] = Field(None, description="Text transcript of the radio")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_key": 9471,
                    "meeting_key": 1229,
                    "date": "2024-03-02T14:30:00.000",
                    "driver_number": 1,
                    "recording_url": "https://...",
                    "transcript": "Box this lap for mediums",
                }
            ]
        }
    }
