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
    PositionForecastRequest,
    PositionForecastResponse,
    DriverPositionForecast,
    StrategyRequest,
    StrategyAnalysisResponse,
    AllPredictionsResponse,
    ModelStatusResponse,
    FeatureImportanceResponse,
    HistoricalAccuracyResponse,
)
from app.ml.pit_predictor import PitStopPredictor
from app.ml.position_forecast import PositionForecaster
from app.ml.strategy_recommender import StrategyRecommender

router = APIRouter()

# Initialize models (lazy loading)
_pit_predictor: Optional[PitStopPredictor] = None
_position_forecaster: Optional[PositionForecaster] = None
_strategy_recommender: Optional[StrategyRecommender] = None


def get_pit_predictor() -> PitStopPredictor:
    """Get or initialize pit predictor."""
    global _pit_predictor
    if _pit_predictor is None:
        _pit_predictor = PitStopPredictor()
        try:
            _pit_predictor.load()
        except Exception as e:
            logger.warning(f"Could not load pit predictor model: {e}")
    return _pit_predictor


def get_position_forecaster() -> PositionForecaster:
    """Get or initialize position forecaster."""
    global _position_forecaster
    if _position_forecaster is None:
        _position_forecaster = PositionForecaster()
        try:
            _position_forecaster.load()
        except Exception as e:
            logger.warning(f"Could not load position forecaster model: {e}")
    return _position_forecaster


def get_strategy_recommender() -> StrategyRecommender:
    """Get or initialize strategy recommender."""
    global _strategy_recommender
    if _strategy_recommender is None:
        _strategy_recommender = StrategyRecommender()
        try:
            _strategy_recommender.load()
        except Exception as e:
            logger.warning(f"Could not load strategy recommender: {e}")
    return _strategy_recommender


@router.post("/pit-stop", response_model=PitPredictionResponse)
async def predict_pit_stop(request: PitPredictionRequest) -> PitPredictionResponse:
    """
    Predict the likelihood and timing of a pit stop.

    Uses ML model trained on historical telemetry and strategy data.
    Returns probability, predicted lap, and recommended compound.
    """
    try:
        predictor = get_pit_predictor()
        
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
        # This would normally fetch live data from telemetry service
        # For now, return mock predictions
        drivers = [1, 11, 16, 44, 55, 63, 14, 31, 10, 22, 4, 27, 20, 21, 18, 77, 24, 81, 3, 23]
        
        if driver_numbers:
            drivers = [int(d.strip()) for d in driver_numbers.split(",")]
        
        predictor = get_pit_predictor()
        predictions = []
        
        for idx, driver_num in enumerate(drivers):
            current_state = {
                "driver_number": driver_num,
                "lap_number": 25,
                "tyre_age": 15 + (idx % 20),
                "position": idx + 1,
                "compound_type": ["SOFT", "MEDIUM", "HARD"][idx % 3],
                "fuel_load": 70,
                "degradation_rate": 0.1 + (idx * 0.01),
            }
            
            pred = predictor.predict(current_state)
            
            predictions.append(PitPredictionResponse(
                driver_number=driver_num,
                probability=pred["probability"],
                predicted_lap=pred["predicted_lap"],
                recommended_compound=pred.get("recommended_compound"),
                confidence=pred["confidence"],
                reasons=pred["reasons"],
            ))
        
        return predictions
        
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
        forecaster = get_position_forecaster()
        
        # Build mock session data (would normally fetch from telemetry)
        drivers = [1, 11, 16, 44, 55, 63, 14, 31, 10, 22, 4, 27, 20, 21, 18, 77, 24, 81, 3, 23]
        
        if driver_number:
            drivers = [driver_number]
        
        driver_data = []
        for idx, d in enumerate(drivers):
            driver_data.append({
                "driver_number": d,
                "name_acronym": f"D{d}",
                "team_name": f"Team {d}",
                "position": idx + 1,
                "tyre_age": 10 + (idx * 2),
                "compound": ["SOFT", "MEDIUM", "HARD"][idx % 3],
                "pace_delta": -0.3 + (idx * 0.05),
                "gap_ahead": 1.0 + idx,
                "gap_behind": 0.5 + idx,
                "avg_lap_time": 90.0 + idx * 0.2,
                "sector_1_avg": 30.0,
                "sector_2_avg": 30.0,
                "sector_3_avg": 30.0,
                "drs_available": idx % 2 == 0,
                "position_change_rate": idx * 0.01,
            })
        
        session_data = {
            "current_lap": 25,
            "total_laps": 50,
            "drivers": driver_data,
        }
        
        predictions = forecaster.predict_final_positions(session_data, laps_ahead)
        
        forecast_predictions = [
            DriverPositionForecast(**pred) for pred in predictions
        ]
        
        return PositionForecastResponse(
            session_key=session_key,
            current_lap=25,
            total_laps=50,
            predictions=forecast_predictions,
            generated_at=datetime.now().isoformat(),
        )
        
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
        recommender = get_strategy_recommender()
        
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
    current_lap: int = Query(25, description="Current lap"),
    total_laps: int = Query(50, description="Total laps in race"),
) -> List[StrategyAnalysisResponse]:
    """
    Get strategy recommendations for all drivers.
    """
    try:
        recommender = get_strategy_recommender()
        strategies = []
        
        # Mock driver data
        drivers = [
            {"number": 1, "compound": "MEDIUM", "tyre_age": 15, "position": 1},
            {"number": 11, "compound": "MEDIUM", "tyre_age": 16, "position": 2},
            {"number": 16, "compound": "HARD", "tyre_age": 25, "position": 3},
            {"number": 44, "compound": "MEDIUM", "tyre_age": 14, "position": 4},
            {"number": 55, "compound": "SOFT", "tyre_age": 12, "position": 5},
        ]
        
        for driver in drivers:
            session_data = {
                "driver_number": driver["number"],
                "current_lap": current_lap,
                "total_laps": total_laps,
                "current_compound": driver["compound"],
                "tyre_age": driver["tyre_age"],
                "position": driver["position"],
                "track_temp": 32.0,
                "weather": "dry",
            }
            
            rec = recommender.recommend_strategy(session_data)
            
            strategies.append(StrategyAnalysisResponse(
                driver_number=driver["number"],
                current_compound=driver["compound"],
                tyre_age=driver["tyre_age"],
                recommended_stops=rec["recommended_stops"],
                optimal_laps=rec["optimal_laps"],
                compounds=rec["compounds"],
                risk_level=rec["risk_level"],
                expected_positions_gained=rec.get("expected_positions_gained", 0.0),
                confidence=rec.get("confidence", 0.5),
                alternative_strategies=rec.get("alternative_strategies", []),
                factors=rec.get("factors", []),
            ))
        
        return strategies
        
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
        # Get all predictions
        pit_predictions = await predict_pit_stops_batch(session_key)
        position_forecast = await get_position_forecast(session_key, laps_ahead=10)
        
        return AllPredictionsResponse(
            session_key=session_key,
            pit_predictions=pit_predictions[:5],  # Top 5
            position_forecast=position_forecast,
            generated_at=datetime.now().isoformat(),
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
        pit_predictor = get_pit_predictor()
        position_forecaster = get_position_forecaster()
        strategy_recommender = get_strategy_recommender()
        
        return ModelStatusResponse(
            pit_predictor={
                "loaded": pit_predictor.is_trained,
                "features": len(pit_predictor.feature_names),
            },
            position_forecaster={
                "loaded": position_forecaster.is_trained,
                "features": len(position_forecaster.feature_names),
            },
            strategy_recommender={
                "loaded": strategy_recommender.is_trained,
                "type": "rule_based",
            },
            models_loaded=pit_predictor.is_trained or position_forecaster.is_trained,
        )
        
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
        pit_predictor = get_pit_predictor()
        position_forecaster = get_position_forecaster()
        
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
