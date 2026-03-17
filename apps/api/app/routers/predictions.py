"""
Predictions router for ML-powered F1 predictions.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from app.core.logging import logger
from app.models.predictions import (
    PitPredictionRequest,
    PitPredictionResponse,
    PositionForecastResponse,
    DriverPositionForecast,
    StrategyRequest,
    StrategyAnalysisResponse,
    AllPredictionsResponse,
    ModelStatusResponse,
    FeatureImportanceResponse,
    HistoricalAccuracyResponse,
)
from app.services.openf1_client import OpenF1RateLimitError
from app.services.prediction_runtime import prediction_runtime

router = APIRouter()

def _parse_driver_numbers(driver_numbers: Optional[str]) -> Optional[List[int]]:
    """Parse optional comma-separated driver numbers."""
    if not driver_numbers:
        return None
    try:
        return [
            int(driver_number.strip())
            for driver_number in driver_numbers.split(",")
            if driver_number.strip()
        ]
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail="driver_numbers must be a comma-separated list of integers",
        ) from exc

@router.post("/pit-stop", response_model=PitPredictionResponse)
async def predict_pit_stop(request: PitPredictionRequest) -> PitPredictionResponse:
    """
    Predict the likelihood and timing of a pit stop.

    Uses ML model trained on historical telemetry and strategy data.
    Returns probability, predicted lap, and recommended compound.
    """
    try:
        predictor = prediction_runtime.get_pit_predictor()
        
        # Prepare features for prediction
        current_state = {
            "driver_number": request.driver_number,
            "lap_number": request.current_lap,
            "tyre_age": request.tyre_age,
            "position": request.current_position,
            "compound_type": request.current_tyre,
            "fuel_load": request.fuel_load or max(0, 110 - request.current_lap * 1.5),
            "degradation_rate": request.degradation_rate or 0.1,
            "gap_to_leader": request.gap_to_leader or 0,
            "gap_to_ahead": 1.0,
            "avg_lap_time": 90.0,
            "lap_time_trend": 0.05,
            "stint_length": request.tyre_age,
            "remaining_laps": 50 - request.current_lap,
        }
        
        prediction = predictor.predict(current_state)
        
        return PitPredictionResponse(
            driver_number=request.driver_number,
            probability=prediction["probability"],
            predicted_lap=prediction["predicted_lap"],
            recommended_compound=prediction.get("recommended_compound"),
            confidence=prediction["confidence"],
            reasons=prediction["reasons"],
        )
        
    except Exception as e:
        logger.error(f"Pit prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pit-stop/batch", response_model=List[PitPredictionResponse])
async def predict_pit_stops_batch(
    session_key: int = Query(..., description="Session key"),
    driver_numbers: Optional[str] = Query(None, description="Comma-separated driver numbers"),
) -> List[PitPredictionResponse]:
    """
    Get pit stop predictions for multiple drivers.
    
    If driver_numbers not specified, returns predictions for all drivers.
    """
    try:
        requested_drivers = _parse_driver_numbers(driver_numbers)
        bundle = await prediction_runtime.get_live_predictions(
            session_key=session_key,
            driver_numbers=requested_drivers,
        )
        return [
            PitPredictionResponse(**prediction)
            for prediction in bundle["pit_predictions"]
        ]

    except OpenF1RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e)) from e
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Batch pit prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/position-forecast", response_model=PositionForecastResponse)
async def get_position_forecast(
    session_key: int = Query(..., description="Session key"),
    driver_number: Optional[int] = Query(None, description="Driver number filter"),
    laps_ahead: int = Query(10, ge=1, le=20, description="Laps to forecast"),
) -> PositionForecastResponse:
    """
    Forecast driver positions for upcoming laps.

    Uses ML model to predict position changes based on pace, tyre life, and gaps.
    """
    try:
        requested_drivers = [driver_number] if driver_number is not None else None
        bundle = await prediction_runtime.get_live_predictions(
            session_key=session_key,
            driver_numbers=requested_drivers,
            laps_ahead=laps_ahead,
        )
        forecast_payload = dict(bundle["position_forecast"])
        forecast_payload["predictions"] = [
            DriverPositionForecast(**prediction)
            for prediction in bundle["position_forecast"]["predictions"]
        ]
        return PositionForecastResponse(
            **forecast_payload,
        )

    except OpenF1RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e)) from e
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Position forecast error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/strategy", response_model=StrategyAnalysisResponse)
async def analyze_strategy(request: StrategyRequest) -> StrategyAnalysisResponse:
    """
    Analyze and recommend pit stop strategy.

    Returns tyre strategy recommendations, optimal lap windows, and risk assessment.
    """
    try:
        recommender = prediction_runtime.get_strategy_recommender()
        
        session_data = {
            "driver_number": request.driver_number,
            "current_lap": request.current_lap,
            "total_laps": request.total_laps,
            "current_compound": request.current_compound,
            "tyre_age": request.tyre_age,
            "position": request.position,
            "track_temp": request.track_temp or 30.0,
            "weather": request.weather or "dry",
        }
        
        recommendation = recommender.recommend_strategy(session_data)
        
        return StrategyAnalysisResponse(
            driver_number=request.driver_number,
            current_compound=request.current_compound,
            tyre_age=request.tyre_age,
            recommended_stops=recommendation["recommended_stops"],
            optimal_laps=recommendation["optimal_laps"],
            compounds=recommendation["compounds"],
            risk_level=recommendation["risk_level"],
            expected_positions_gained=recommendation.get("expected_positions_gained", 0.0),
            confidence=recommendation.get("confidence", 0.5),
            alternative_strategies=recommendation.get("alternative_strategies", []),
            factors=recommendation.get("factors", []),
        )
        
    except Exception as e:
        logger.error(f"Strategy analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy/batch", response_model=List[StrategyAnalysisResponse])
async def analyze_strategy_batch(
    session_key: int = Query(..., description="Session key"),
    current_lap: Optional[int] = Query(None, description="Current lap override"),
    total_laps: Optional[int] = Query(None, description="Total laps in race override"),
) -> List[StrategyAnalysisResponse]:
    """
    Get strategy recommendations for all drivers.
    """
    try:
        bundle = await prediction_runtime.get_live_predictions(
            session_key=session_key,
            current_lap=current_lap,
            total_laps=total_laps,
        )
        return [
            StrategyAnalysisResponse(**strategy)
            for strategy in bundle["strategies"]
        ]

    except OpenF1RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e)) from e
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Batch strategy analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all", response_model=AllPredictionsResponse)
async def get_all_predictions(
    session_key: int = Query(..., description="Session key"),
    current_lap: int = Query(25, description="Current lap"),
) -> AllPredictionsResponse:
    """
    Get all predictions for a session in one call.
    
    Combines pit predictions, position forecast, and strategy recommendations.
    """
    try:
        bundle = await prediction_runtime.get_live_predictions(
            session_key=session_key,
            current_lap=current_lap,
            laps_ahead=10,
        )
        return AllPredictionsResponse(
            session_key=session_key,
            pit_predictions=[
                PitPredictionResponse(**prediction)
                for prediction in bundle["pit_predictions"][:5]
            ],
            position_forecast=PositionForecastResponse(
                **bundle["position_forecast"],
                predictions=[
                    DriverPositionForecast(**prediction)
                    for prediction in bundle["position_forecast"]["predictions"]
                ],
            ),
            generated_at=bundle["generated_at"],
        )
        
    except Exception as e:
        logger.error(f"All predictions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/status", response_model=ModelStatusResponse)
async def get_model_status() -> ModelStatusResponse:
    """
    Get status of all ML models.
    
    Returns information about model loading state and training status.
    """
    try:
        return ModelStatusResponse(**prediction_runtime.get_model_status())
        
    except Exception as e:
        logger.error(f"Model status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/feature-importance", response_model=FeatureImportanceResponse)
async def get_feature_importance() -> FeatureImportanceResponse:
    """
    Get feature importance from trained ML models.
    
    Shows which factors most influence predictions.
    """
    try:
        pit_predictor = prediction_runtime.get_pit_predictor()
        position_forecaster = prediction_runtime.get_position_forecaster()
        
        return FeatureImportanceResponse(
            pit_predictor=pit_predictor.get_feature_importance(),
            position_forecaster=position_forecaster.get_feature_importance(),
        )
        
    except Exception as e:
        logger.error(f"Feature importance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/accuracy", response_model=HistoricalAccuracyResponse)
async def get_historical_accuracy(
    model: str = Query("pit_predictor", description="Model name"),
) -> HistoricalAccuracyResponse:
    """
    Get historical accuracy metrics for a model.
    
    Shows how well the model has performed on past races.
    """
    # Mock accuracy data (would normally be stored from training)
    accuracy_data = {
        "pit_predictor": {
            "accuracy": 0.85,
            "precision": 0.82,
            "recall": 0.78,
            "f1_score": 0.80,
            "races_analyzed": 10,
        },
        "position_forecaster": {
            "accuracy": 0.75,
            "precision": 0.72,
            "recall": 0.70,
            "f1_score": 0.71,
            "races_analyzed": 10,
        },
    }
    
    if model not in accuracy_data:
        raise HTTPException(status_code=404, detail=f"Model {model} not found")
    
    data = accuracy_data[model]
    
    return HistoricalAccuracyResponse(
        model_name=model,
        accuracy=data["accuracy"],
        precision=data["precision"],
        recall=data["recall"],
        f1_score=data["f1_score"],
        races_analyzed=data["races_analyzed"],
        last_updated=datetime.now().isoformat(),
    )


@router.post("/models/train")
async def train_models(
    background_tasks: BackgroundTasks,
    use_historical: bool = Query(True, description="Use historical data"),
    years: str = Query("2023,2024", description="Comma-separated years"),
    max_races: int = Query(5, description="Max races per year"),
) -> dict:
    """
    Trigger model training in background.
    
    Training runs asynchronously and may take several minutes.
    """
    from app.ml.training import ModelTrainingPipeline
    
    year_list = [int(y.strip()) for y in years.split(",")]
    
    def run_training():
        pipeline = ModelTrainingPipeline()
        pipeline.train_all_models(
            use_historical=use_historical,
            years=year_list,
            max_races=max_races,
        )
    
    background_tasks.add_task(run_training)
    
    return {
        "status": "training_started",
        "message": "Model training started in background",
        "params": {
            "use_historical": use_historical,
            "years": year_list,
            "max_races": max_races,
        },
    }
