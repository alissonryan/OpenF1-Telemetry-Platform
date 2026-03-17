"""
Pit stop prediction model.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split

from app.core.config import settings
from app.core.logging import logger


class PitPredictor:
    """ML model for predicting pit stops."""

    def __init__(self):
        self.model: Optional[GradientBoostingClassifier] = None
        self.feature_names = [
            "tyre_age",
            "position",
            "lap_number",
            "gap_to_leader",
            "fuel_load",
            "compound_type",
        ]

    def train(
        self,
        data: pd.DataFrame,
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> Dict[str, float]:
        """
        Train the pit stop prediction model.

        Args:
            data: DataFrame with training data
            test_size: Fraction of data for testing
            random_state: Random seed for reproducibility

        Returns:
            Dictionary with training metrics
        """
        # Prepare features and target
        X = data[self.feature_names]
        y = data["pitted_next_lap"]

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        # Train model
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=random_state,
        )
        self.model.fit(X_train, y_train)

        # Evaluate
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)

        metrics = {
            "train_accuracy": train_score,
            "test_accuracy": test_score,
        }

        logger.info(f"PitPredictor trained: {metrics}")
        return metrics

    def predict(self, features: Dict[str, float]) -> float:
        """
        Predict probability of pit stop.

        Args:
            features: Dictionary of feature values

        Returns:
            Probability of pit stop in next lap
        """
        if self.model is None:
            raise ValueError("Model not trained")

        X = np.array([[features.get(f, 0) for f in self.feature_names]])
        return float(self.model.predict_proba(X)[0][1])

    def save(self, path: Optional[Path] = None) -> None:
        """Save the trained model to disk."""
        import joblib

        if self.model is None:
            raise ValueError("No model to save")

        path = path or Path(settings.models_dir) / "pit_predictor.pkl"
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)
        logger.info(f"Model saved to {path}")

    def load(self, path: Optional[Path] = None) -> None:
        """Load a trained model from disk."""
        import joblib

        path = path or Path(settings.models_dir) / "pit_predictor.pkl"
        self.model = joblib.load(path)
        logger.info(f"Model loaded from {path}")
