"""
Pydantic models for F1 session and meeting data.

These models define the structure and validation for:
- Meetings (race weekends)
- Sessions (practice, qualifying, sprint, race)
- Session status and timing information
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class SessionType(str, Enum):
    """F1 session type enumeration."""

    PRACTICE_1 = "Practice 1"
    PRACTICE_2 = "Practice 2"
    PRACTICE_3 = "Practice 3"
    QUALIFYING = "Qualifying"
    SPRINT_QUALIFYING = "Sprint Qualifying"
    SPRINT = "Sprint"
    RACE = "Race"


class MeetingResponse(BaseModel):
    """Meeting (race weekend) response model."""

    meeting_key: int = Field(..., description="Unique meeting identifier")
    meeting_name: str = Field(..., description="Name of the race weekend")
    location: str = Field(..., description="Location/city name")
    official_name: str = Field(..., description="Official event name")
    country_key: int = Field(..., description="Country identifier")
    country_name: str = Field(..., description="Country name")
    country_code: str = Field(..., description="ISO country code")
    circuit_key: int = Field(..., description="Circuit identifier")
    circuit_short_name: str = Field(..., description="Short circuit name")
    date_start: str = Field(..., description="Event start date (ISO format)")
    date_end: Optional[str] = Field(None, description="Event end date (ISO format)")
    year: int = Field(..., ge=1950, le=2100, description="Championship year")
    gmt_offset: Optional[str] = Field(None, description="GMT timezone offset")
    meeting_code: Optional[str] = Field(None, description="Short meeting code")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "meeting_key": 1229,
                    "meeting_name": "Bahrain Grand Prix",
                    "location": "Sakhir",
                    "official_name": "Formula 1 Gulf Air Bahrain Grand Prix 2024",
                    "country_key": 12,
                    "country_name": "Bahrain",
                    "country_code": "BHR",
                    "circuit_key": 3,
                    "circuit_short_name": "Bahrain",
                    "date_start": "2024-03-02",
                    "date_end": "2024-03-03",
                    "year": 2024,
                    "gmt_offset": "+03:00",
                    "meeting_code": "BAH",
                }
            ]
        }
    }


class MeetingListResponse(BaseModel):
    """Response model for meeting list."""

    data: List[MeetingResponse]
    total: int
    year: Optional[int] = None


class SessionResponse(BaseModel):
    """Session response model."""

    session_key: int = Field(..., description="Unique session identifier")
    meeting_key: int = Field(..., description="Parent meeting identifier")
    location: str = Field(..., description="Session location")
    session_type: str = Field(
        ...,
        description="Session type (Practice, Qualifying, Sprint, Race)",
    )
    session_name: str = Field(..., description="Full session name")
    date_start: str = Field(..., description="Session start date/time (ISO format)")
    date_end: Optional[str] = Field(None, description="Session end date/time (ISO format)")
    country_name: str = Field(..., description="Country name")
    country_code: Optional[str] = Field(None, description="ISO country code")
    circuit_short_name: str = Field(..., description="Short circuit name")
    year: int = Field(..., ge=1950, le=2100, description="Championship year")
    gmt_offset: Optional[str] = Field(None, description="GMT timezone offset")
    circuit_key: Optional[int] = Field(None, description="Circuit identifier")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_key": 9471,
                    "meeting_key": 1229,
                    "location": "Sakhir",
                    "session_type": "Race",
                    "session_name": "Race",
                    "date_start": "2024-03-02T15:00:00",
                    "date_end": "2024-03-02T17:00:00",
                    "country_name": "Bahrain",
                    "country_code": "BHR",
                    "circuit_short_name": "Bahrain",
                    "year": 2024,
                    "gmt_offset": "+03:00",
                    "circuit_key": 3,
                }
            ]
        }
    }

    @field_validator("session_type")
    @classmethod
    def validate_session_type(cls, v: str) -> str:
        """Validate session type."""
        valid_types = [
            "Practice",
            "Practice 1",
            "Practice 2",
            "Practice 3",
            "Qualifying",
            "Sprint Qualifying",
            "Sprint",
            "Race",
        ]
        if v not in valid_types:
            raise ValueError(f"Invalid session type: {v}")
        return v


class SessionListResponse(BaseModel):
    """Response model for session list."""

    data: List[SessionResponse]
    total: int
    meeting_key: Optional[int] = None
    year: Optional[int] = None


# ==================== Fast-F1 Specific Models ====================


class FastF1SessionRequest(BaseModel):
    """Request model for loading a Fast-F1 session."""

    year: int = Field(..., ge=2018, le=2100, description="Championship year")
    grand_prix: str = Field(
        ...,
        min_length=1,
        description="Grand Prix name (e.g., 'Monaco', 'British Grand Prix') or round number",
    )
    session_type: str = Field(
        default="R",
        description="Session type: FP1, FP2, FP3, Q, S, SS, R",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "year": 2024,
                    "grand_prix": "Monaco",
                    "session_type": "R",
                }
            ]
        }
    }

    @field_validator("session_type")
    @classmethod
    def validate_session_type(cls, v: str) -> str:
        """Validate Fast-F1 session type."""
        valid_types = ["FP1", "FP2", "FP3", "Q", "S", "SS", "R"]
        v_upper = v.upper()
        if v_upper not in valid_types:
            raise ValueError(f"Invalid session type: {v}. Must be one of {valid_types}")
        return v_upper


class FastF1SessionInfo(BaseModel):
    """Fast-F1 session information response."""

    year: int
    grand_prix: str
    session_type: str
    session_name: str
    date: Optional[str] = None
    total_laps: int
    drivers: List[str]
    circuit_name: Optional[str] = None
    country: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "year": 2024,
                    "grand_prix": "Monaco Grand Prix",
                    "session_type": "R",
                    "session_name": "Race",
                    "date": "2024-05-26T13:00:00",
                    "total_laps": 78,
                    "drivers": ["VER", "LEC", "NOR", "PIA", "SAI"],
                    "circuit_name": "Circuit de Monaco",
                    "country": "Monaco",
                }
            ]
        }
    }


class FastF1TelemetryRequest(BaseModel):
    """Request model for Fast-F1 telemetry extraction."""

    year: int = Field(..., ge=2018, le=2100)
    grand_prix: str = Field(..., min_length=1)
    session_type: str = Field(default="R")
    driver: str = Field(..., min_length=3, max_length=3, description="3-letter driver code")
    lap_number: Optional[int] = Field(None, ge=1, description="Specific lap (default: fastest)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "year": 2024,
                    "grand_prix": "Monaco",
                    "session_type": "R",
                    "driver": "VER",
                    "lap_number": 45,
                }
            ]
        }
    }


class FastF1TelemetryPoint(BaseModel):
    """Single telemetry data point from Fast-F1."""

    time: float = Field(..., description="Session time in seconds")
    speed: int = Field(..., ge=0, le=400, description="Speed in km/h")
    throttle: float = Field(..., ge=0, le=100, description="Throttle percentage")
    brake: bool = Field(..., description="Brake status")
    n_gear: int = Field(..., ge=0, le=8, description="Gear number")
    rpm: int = Field(..., ge=0, le=15000, description="Engine RPM")
    drs: Optional[int] = Field(None, description="DRS status")
    distance: Optional[float] = Field(None, description="Distance around track in meters")
    driver: str = Field(..., description="Driver code")
    lap_number: int = Field(..., description="Lap number")


class FastF1TelemetryResponse(BaseModel):
    """Response model for Fast-F1 telemetry data."""

    session_info: FastF1SessionInfo
    driver: str
    lap_number: int
    data: List[FastF1TelemetryPoint]
    total_samples: int


class FastF1LapData(BaseModel):
    """Fast-F1 lap data model."""

    driver: str
    lap_number: int
    lap_time: Optional[float] = Field(None, description="Lap time in seconds")
    sector_1: Optional[float] = Field(None, description="Sector 1 time in seconds")
    sector_2: Optional[float] = Field(None, description="Sector 2 time in seconds")
    sector_3: Optional[float] = Field(None, description="Sector 3 time in seconds")
    tyre_compound: Optional[str] = Field(None, description="Tyre compound")
    tyre_life: Optional[int] = Field(None, description="Tyre age in laps")
    is_personal_best: Optional[bool] = Field(None, description="Is this a personal best")
    is_fresh_tyre: Optional[bool] = Field(None, description="Fresh tyre compound")


class FastF1LapsResponse(BaseModel):
    """Response model for Fast-F1 laps data."""

    session_info: FastF1SessionInfo
    laps: List[FastF1LapData]
    total_laps: int


class FastF1WeatherData(BaseModel):
    """Fast-F1 weather data model."""

    time: Optional[float] = Field(None, description="Session time in seconds")
    air_temp: Optional[float] = Field(None, description="Air temperature in Celsius")
    track_temp: Optional[float] = Field(None, description="Track temperature in Celsius")
    humidity: Optional[float] = Field(None, description="Relative humidity %")
    pressure: Optional[float] = Field(None, description="Atmospheric pressure")
    rainfall: Optional[int] = Field(None, description="Rainfall indicator (0/1)")
    wind_direction: Optional[int] = Field(None, description="Wind direction in degrees")
    wind_speed: Optional[float] = Field(None, description="Wind speed in m/s")


class FastF1WeatherResponse(BaseModel):
    """Response model for Fast-F1 weather data."""

    session_info: FastF1SessionInfo
    data: List[FastF1WeatherData]
    summary: Optional[Dict[str, Any]] = Field(None, description="Weather summary statistics")


class FastF1TyreAnalysis(BaseModel):
    """Fast-F1 tyre analysis model."""

    driver: str
    compounds: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Analysis per tyre compound",
    )


class FastF1ComparisonRequest(BaseModel):
    """Request model for driver comparison."""

    year: int = Field(..., ge=2018, le=2100)
    grand_prix: str = Field(..., min_length=1)
    session_type: str = Field(default="R")
    drivers: List[str] = Field(
        ...,
        min_length=2,
        max_length=4,
        description="List of driver codes to compare (2-4 drivers)",
    )


class FastF1ComparisonResponse(BaseModel):
    """Response model for driver comparison."""

    session_info: FastF1SessionInfo
    drivers: List[str]
    fastest_laps: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Fastest lap data per driver",
    )
    telemetry_delta: Optional[Dict[str, Any]] = Field(
        None,
        description="Time delta between drivers",
    )
