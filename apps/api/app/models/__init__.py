"""
Models module initialization.

Exports all Pydantic models for F1 telemetry data.
"""

from app.models.predictions import (
    PitPredictionRequest,
    PitPredictionResponse,
    PositionForecastResponse,
    StrategyAnalysisResponse,
)
from app.models.session import (
    FastF1ComparisonRequest,
    FastF1ComparisonResponse,
    FastF1LapData,
    FastF1LapsResponse,
    FastF1SessionInfo,
    FastF1SessionRequest,
    FastF1TelemetryPoint,
    FastF1TelemetryRequest,
    FastF1TelemetryResponse,
    FastF1TyreAnalysis,
    FastF1WeatherData,
    FastF1WeatherResponse,
    MeetingListResponse,
    MeetingResponse,
    SessionListResponse,
    SessionResponse,
    SessionType,
)
from app.models.telemetry import (
    CarDataBase,
    DriverListResponse,
    DriverResponse,
    DRSStratus,
    IntervalResponse,
    LapListResponse,
    LapResponse,
    PitResponse,
    PositionListResponse,
    PositionResponse,
    RaceControlResponse,
    SectorTimes,
    SpeedTrap,
    StintResponse,
    TeamRadioResponse,
    TelemetryListResponse,
    TelemetryResponse,
    TyreCompound,
    WeatherResponse,
)

__all__ = [
    # Telemetry
    "CarDataBase",
    "TelemetryResponse",
    "TelemetryListResponse",
    "PositionResponse",
    "PositionListResponse",
    "LapResponse",
    "LapListResponse",
    "DriverResponse",
    "DriverListResponse",
    "SectorTimes",
    "SpeedTrap",
    "PitResponse",
    "StintResponse",
    "WeatherResponse",
    "IntervalResponse",
    "RaceControlResponse",
    "TeamRadioResponse",
    "DRSStratus",
    "TyreCompound",
    # Session
    "MeetingResponse",
    "MeetingListResponse",
    "SessionResponse",
    "SessionListResponse",
    "SessionType",
    # Fast-F1
    "FastF1SessionRequest",
    "FastF1SessionInfo",
    "FastF1TelemetryRequest",
    "FastF1TelemetryPoint",
    "FastF1TelemetryResponse",
    "FastF1LapData",
    "FastF1LapsResponse",
    "FastF1WeatherData",
    "FastF1WeatherResponse",
    "FastF1TyreAnalysis",
    "FastF1ComparisonRequest",
    "FastF1ComparisonResponse",
    # Predictions
    "PitPredictionRequest",
    "PitPredictionResponse",
    "PositionForecastResponse",
    "StrategyAnalysisResponse",
]
