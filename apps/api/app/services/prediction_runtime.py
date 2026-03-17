"""
Shared runtime helpers for live prediction endpoints and streaming.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.logging import logger
from app.ml.pit_predictor import PitStopPredictor
from app.ml.position_forecast import PositionForecaster
from app.ml.strategy_recommender import StrategyRecommender
from app.services.prediction_context import prediction_context_service


class PredictionRuntime:
    """Centralize predictor lifecycle and live session prediction assembly."""

    def __init__(self) -> None:
        self._pit_predictor: Optional[PitStopPredictor] = None
        self._position_forecaster: Optional[PositionForecaster] = None
        self._strategy_recommender: Optional[StrategyRecommender] = None

    def get_pit_predictor(self) -> PitStopPredictor:
        if self._pit_predictor is None:
            self._pit_predictor = PitStopPredictor()
            try:
                self._pit_predictor.load()
            except Exception as exc:
                logger.warning("Could not load pit predictor model: %s", exc)
        return self._pit_predictor

    def get_position_forecaster(self) -> PositionForecaster:
        if self._position_forecaster is None:
            self._position_forecaster = PositionForecaster()
            try:
                self._position_forecaster.load()
            except Exception as exc:
                logger.warning("Could not load position forecaster model: %s", exc)
        return self._position_forecaster

    def get_strategy_recommender(self) -> StrategyRecommender:
        if self._strategy_recommender is None:
            self._strategy_recommender = StrategyRecommender()
            try:
                self._strategy_recommender.load()
            except Exception as exc:
                logger.warning("Could not load strategy recommender: %s", exc)
        return self._strategy_recommender

    def get_model_status(self) -> Dict[str, Any]:
        pit_predictor = self.get_pit_predictor()
        position_forecaster = self.get_position_forecaster()
        strategy_recommender = self.get_strategy_recommender()

        pit_mode = "trained_model" if pit_predictor.is_trained else "heuristic_fallback"
        position_mode = (
            "trained_model"
            if position_forecaster.is_trained
            else "heuristic_fallback"
        )

        if pit_predictor.is_trained and position_forecaster.is_trained:
            overall_mode = "trained"
        elif pit_predictor.is_trained or position_forecaster.is_trained:
            overall_mode = "hybrid"
        else:
            overall_mode = "heuristic"

        return {
            "pit_predictor": {
                "loaded": pit_predictor.is_trained,
                "features": len(pit_predictor.feature_names),
                "mode": pit_mode,
            },
            "position_forecaster": {
                "loaded": position_forecaster.is_trained,
                "features": len(position_forecaster.feature_names),
                "mode": position_mode,
            },
            "strategy_recommender": {
                "loaded": strategy_recommender.is_trained,
                "type": "rule_based",
                "mode": "rule_based",
            },
            "models_loaded": pit_predictor.is_trained or position_forecaster.is_trained,
            "overall_mode": overall_mode,
        }

    async def get_live_predictions(
        self,
        session_key: int,
        driver_numbers: Optional[List[int]] = None,
        laps_ahead: int = 10,
        current_lap: Optional[int] = None,
        total_laps: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Assemble live pit, position and strategy predictions from session context."""
        context = await prediction_context_service.get_context(session_key, driver_numbers)

        effective_current_lap = (
            current_lap if current_lap is not None else context["current_lap"]
        )
        effective_total_laps = (
            total_laps if total_laps is not None else context["total_laps"]
        )
        effective_total_laps = max(effective_total_laps, effective_current_lap)

        pit_predictions = self._build_pit_predictions(context)
        position_forecast = self._build_position_forecast(
            session_key=session_key,
            context=context,
            laps_ahead=laps_ahead,
            current_lap=effective_current_lap,
            total_laps=effective_total_laps,
        )
        strategies = self._build_strategies(
            context=context,
            current_lap=effective_current_lap,
            total_laps=effective_total_laps,
        )

        generated_at = datetime.now().isoformat()
        return {
            "session_key": session_key,
            "generated_at": generated_at,
            "context": context,
            "pit_predictions": pit_predictions,
            "position_forecast": {
                "session_key": session_key,
                "current_lap": effective_current_lap,
                "total_laps": effective_total_laps,
                "predictions": position_forecast,
                "generated_at": generated_at,
            },
            "strategies": strategies,
            "model_status": self.get_model_status(),
        }

    def _build_pit_predictions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        predictor = self.get_pit_predictor()
        predictions: List[Dict[str, Any]] = []

        for driver in context["drivers"]:
            current_state = {
                "driver_number": driver["driver_number"],
                "lap_number": driver["current_lap"],
                "tyre_age": driver["tyre_age"],
                "position": driver["position"],
                "compound_type": driver["compound"],
                "fuel_load": max(
                    0.0,
                    round(
                        110
                        * (driver["remaining_laps"] / max(context["total_laps"], 1)),
                        1,
                    ),
                ),
                "degradation_rate": driver["degradation_rate"],
                "gap_to_leader": driver["gap_to_leader"],
                "gap_to_ahead": driver["gap_ahead"],
                "avg_lap_time": driver["avg_lap_time"],
                "lap_time_trend": driver["lap_time_trend"],
                "stint_length": driver["tyre_age"],
                "remaining_laps": driver["remaining_laps"],
            }

            pred = predictor.predict(current_state)
            predictions.append(
                {
                    "driver_number": driver["driver_number"],
                    "probability": pred["probability"],
                    "predicted_lap": pred["predicted_lap"],
                    "recommended_compound": pred.get("recommended_compound"),
                    "confidence": pred["confidence"],
                    "reasons": pred["reasons"],
                }
            )

        return sorted(
            predictions,
            key=lambda prediction: prediction["probability"],
            reverse=True,
        )

    def _build_position_forecast(
        self,
        *,
        session_key: int,
        context: Dict[str, Any],
        laps_ahead: int,
        current_lap: int,
        total_laps: int,
    ) -> List[Dict[str, Any]]:
        forecaster = self.get_position_forecaster()
        session_data = {
            "current_lap": current_lap,
            "total_laps": max(total_laps, current_lap + laps_ahead),
            "drivers": context["drivers"],
        }
        return forecaster.predict_final_positions(session_data, laps_ahead)

    def _build_strategies(
        self,
        *,
        context: Dict[str, Any],
        current_lap: int,
        total_laps: int,
    ) -> List[Dict[str, Any]]:
        recommender = self.get_strategy_recommender()
        strategies: List[Dict[str, Any]] = []

        for driver in context["drivers"]:
            session_data = {
                "driver_number": driver["driver_number"],
                "current_lap": current_lap,
                "total_laps": total_laps,
                "current_compound": driver["current_compound"],
                "tyre_age": driver["tyre_age"],
                "position": driver["position"],
                "track_temp": context["weather"]["track_temp"],
                "weather": context["weather"]["condition"],
            }

            strategy = recommender.recommend_strategy(session_data)
            strategies.append(
                {
                    "driver_number": driver["driver_number"],
                    "current_compound": driver["current_compound"],
                    "tyre_age": driver["tyre_age"],
                    "recommended_stops": strategy["recommended_stops"],
                    "optimal_laps": strategy["optimal_laps"],
                    "compounds": strategy["compounds"],
                    "risk_level": strategy["risk_level"],
                    "expected_positions_gained": strategy.get(
                        "expected_positions_gained",
                        0.0,
                    ),
                    "confidence": strategy.get("confidence", 0.5),
                    "alternative_strategies": strategy.get(
                        "alternative_strategies",
                        [],
                    ),
                    "factors": strategy.get("factors", []),
                }
            )

        return sorted(strategies, key=lambda item: item["driver_number"])


prediction_runtime = PredictionRuntime()
