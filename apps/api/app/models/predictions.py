"""Pydantic models for ML predictions."""

from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field


# ============== Request Models ==============

class PitPredictionRequest(BaseModel):
    """Request model for pit stop prediction."""

    session_key: int
    driver_number: int
    current_lap: int
    current_tyre: str
    tyre_age: int
    current_position: int
    fuel_load: Optional[float] = None
    degradation_rate: Optional[float] = None
    gap_to_leader: Optional[float] = None


class PositionForecastRequest(BaseModel):
    """Request model for position forecast."""

    session_key: int
    laps_ahead: int = Field(default=10, ge=1, le=20)
    driver_numbers: Optional[List[int]] = None


class StrategyRequest(BaseModel):
    """Request model for strategy analysis."""

    session_key: int
    driver_number: int
    current_lap: int
    total_laps: int = Field(default=50)
    current_compound: str
    tyre_age: int
    position: int
    track_temp: Optional[float] = 30.0
    weather: Optional[str] = "dry"


# ============== Response Models ==============

class PitPredictionResponse(BaseModel):
    """Pit stop prediction response model."""

    driver_number: int
    probability: float = Field(..., ge=0, le=1, description="Probability of pit stop")
    predicted_lap: int = Field(..., description="Predicted lap for pit stop")
    recommended_compound: Optional[str] = Field(None, description="Recommended tyre compound")
    confidence: float = Field(..., ge=0, le=1, description="Model confidence")
    reasons: List[str] = Field(default_factory=list, description="Factors influencing prediction")


class DriverPositionForecast(BaseModel):
    """Single driver position forecast."""

    driver_number: int
    driver_name: Optional[str] = None
    team_name: Optional[str] = None
    current_position: int = Field(..., ge=1, le=25)
    predicted_position: int = Field(..., ge=1, le=25)
    position_change: int = Field(..., description="Positive = gained positions, negative = lost")
    confidence: float = Field(..., ge=0, le=1)
    factors: List[str] = Field(default_factory=list)


class PositionForecastResponse(BaseModel):
    """Position forecast response model."""

    session_key: int
    current_lap: Optional[int] = None
    total_laps: Optional[int] = None
    predictions: List[DriverPositionForecast]
    generated_at: Optional[str] = None


class StrategyAlternative(BaseModel):
    """Alternative strategy option."""

    strategy: str
    risk: str
    expected_gain: Optional[float] = None
    condition: Optional[str] = None


class StrategyAnalysisResponse(BaseModel):
    """Strategy analysis response model."""

    driver_number: int
    current_compound: str = Field(..., description="Current tyre compound")
    tyre_age: int = Field(..., ge=0, description="Laps on current tyres")
    recommended_stops: int = Field(..., ge=0, description="Recommended remaining stops")
    optimal_laps: List[int] = Field(default_factory=list, description="Optimal laps for pit stops")
    compounds: List[str] = Field(default_factory=list, description="Recommended compounds")
    risk_level: Literal["low", "medium", "high"]
    expected_positions_gained: float = Field(default=0.0)
    confidence: float = Field(default=0.5)
    alternative_strategies: List[StrategyAlternative] = Field(default_factory=list)
    factors: List[str] = Field(default_factory=list)


# ============== Aggregated Models ==============

class AllPredictionsResponse(BaseModel):
    """All predictions for a session."""

    session_key: int
    pit_predictions: List[PitPredictionResponse]
    position_forecast: PositionForecastResponse
    generated_at: str


class ModelStatusResponse(BaseModel):
    """Status of ML models."""

    pit_predictor: Dict[str, Any]
    position_forecaster: Dict[str, Any]
    strategy_recommender: Dict[str, Any]
    models_loaded: bool
    overall_mode: Optional[str] = None


class FeatureImportanceResponse(BaseModel):
    """Feature importance from ML models."""

    pit_predictor: Optional[Dict[str, float]] = None
    position_forecaster: Optional[Dict[str, float]] = None


class HistoricalAccuracyResponse(BaseModel):
    """Historical accuracy metrics."""

    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    races_analyzed: int
    last_updated: str
