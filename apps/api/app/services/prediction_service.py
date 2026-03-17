"""
ML Prediction service.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np

from app.core.config import settings
from app.core.logging import logger


class PredictionService:
    """Service for ML-powered predictions."""

    def __init__(self):
        self.models_dir = Path(settings.models_dir)
        self.models: Dict[str, Any] = {}

    def load_model(self, model_name: str) -> Any:
        """Load a trained model from disk."""
        if model_name in self.models:
            return self.models[model_name]

        model_path = self.models_dir / f"{model_name}.pkl"
        if not model_path.exists():
            logger.warning(f"Model not found: {model_path}")
            return None

        model = joblib.load(model_path)
        self.models[model_name] = model
        logger.info(f"Loaded model: {model_name}")
        return model

    def predict_pit_stop(
        self,
        driver_number: int,
        current_lap: int,
        tyre_age: int,
        position: int,
        features: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Predict pit stop probability.

        Args:
            driver_number: Driver's racing number
            current_lap: Current lap number
            tyre_age: Laps on current tyres
            position: Current race position
            features: Additional features for prediction

        Returns:
            Dictionary with prediction results
        """
        model = self.load_model("pit_predictor")

        if model is None:
            # Return heuristic-based prediction if model not available
            return self._heuristic_pit_prediction(
                driver_number, current_lap, tyre_age, position
            )

        # Prepare features
        X = np.array([[tyre_age, position, current_lap]])

        # Get prediction
        probability = model.predict_proba(X)[0][1]
        predicted_lap = current_lap + int(max(1, 10 * (1 - probability)))

        return {
            "driver_number": driver_number,
            "probability": float(probability),
            "predicted_lap": predicted_lap,
            "confidence": 0.75,  # Placeholder
            "reasons": self._get_pit_reasons(probability, tyre_age, position),
        }

    def _heuristic_pit_prediction(
        self,
        driver_number: int,
        current_lap: int,
        tyre_age: int,
        position: int,
    ) -> Dict[str, Any]:
        """Heuristic-based pit prediction when model is unavailable."""
        # Simple heuristics
        probability = 0.0
        reasons = []

        if tyre_age > 25:
            probability = 0.9
            reasons.append("Tyre age critical (>25 laps)")
        elif tyre_age > 18:
            probability = 0.6
            reasons.append("Tyre degradation significant")
        elif tyre_age > 12:
            probability = 0.3
            reasons.append("Approaching optimal pit window")

        if position > 10 and tyre_age > 10:
            probability = min(probability + 0.2, 1.0)
            reasons.append("Strategic opportunity in midfield")

        predicted_lap = current_lap + max(1, int(15 * (1 - probability)))

        return {
            "driver_number": driver_number,
            "probability": probability,
            "predicted_lap": predicted_lap,
            "confidence": 0.5,
            "reasons": reasons or ["No immediate pit window"],
        }

    def _get_pit_reasons(
        self, probability: float, tyre_age: int, position: int
    ) -> List[str]:
        """Generate reasons for pit prediction."""
        reasons = []
        if tyre_age > 20:
            reasons.append("High tyre degradation")
        if probability > 0.7:
            reasons.append("Model confidence high")
        if position < 5:
            reasons.append("Front-running strategy")
        elif position > 10:
            reasons.append("Midfield strategy")
        return reasons or ["Standard strategy window"]


# Singleton instance
prediction_service = PredictionService()
