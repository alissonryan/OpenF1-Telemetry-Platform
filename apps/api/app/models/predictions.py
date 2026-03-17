"""Pydantic models for ML predictions."""

from typing import List, Literal, Optional, Tuple

from pydantic import BaseModel, Field


class PitPredictionRequest(BaseModel):
    """Request model for pit stop prediction."""

    session_key: int
    driver_number: int
    current_lap: int
    current_tyre: str
    tyre_age: int
    current_position: int
    fuel_load: Optional[float] = None


class PitPredictionResponse(BaseModel):
    """Pit stop prediction response model."""

    driver_number: int
    probability: float = Field(..., ge=0, le=1, description="Probability of pit stop")
    predicted_lap: int = Field(..., description="Predicted lap for pit stop")
    confidence: float = Field(..., ge=0, le=1, description="Model confidence")
    reasons: List[str] = Field(default_factory=list, description="Factors influencing prediction")


class PositionForecastResponse(BaseModel):
    """Position forecast response model."""

    driver_number: int
    current_position: int = Field(..., ge=1, le=20)
    predicted_position: int = Field(..., ge=1, le=20)
    position_change: int = Field(..., description="Positive = gained positions, negative = lost")
    confidence: float = Field(..., ge=0, le=1)


class StrategyAnalysisResponse(BaseModel):
    """Strategy analysis response model."""

    driver_number: int
    current_tyre: str = Field(..., description="Current tyre compound")
    tyre_age: int = Field(..., ge=0, description="Laps on current tyres")
    recommended_stops: int = Field(..., ge=0, description="Recommended remaining stops")
    optimal_lap_window: Tuple[int, int] = Field(..., description="Optimal lap range for next stop")
    risk_level: Literal["low", "medium", "high"]
