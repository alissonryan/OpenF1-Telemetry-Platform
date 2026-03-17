"""
Position forecasting model.
"""

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split

from app.core.config import settings
from app.core.logging import logger


class PositionForecaster:
    """ML model for forecasting driver positions."""

    def __init__(self):
        self.model: Optional[GradientBoostingRegressor] = None
        self.feature_names = [
            "current_position",
            "lap_number",
            "tyre_age",
            "pace_delta",
            "gap_ahead",
            "gap_behind",
            "remaining_laps",
        ]

    def train(
        self,
        data: pd.DataFrame,
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> Dict[str, float]:
        """
        Train the position forecasting model.

        Args:
            data: DataFrame with training data
            test_size: Fraction of data for testing
            random_state: Random seed

        Returns:
            Dictionary with training metrics
        """
        X = data[self.feature_names]
        y = data["final_position"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        self.model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=random_state,
        )
        self.model.fit(X_train, y_train)

        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)

        metrics = {
            "train_r2": train_score,
            "test_r2": test_score,
        }

        logger.info(f"PositionForecaster trained: {metrics}")
        return metrics

    def predict(self, features: Dict[str, float]) -> float:
        """Predict final position."""
        if self.model is None:
            raise ValueError("Model not trained")

        X = np.array([[features.get(f, 0) for f in self.feature_names]])
        return float(self.model.predict(X)[0])

    def save(self, path: Optional[Path] = None) -> None:
        """Save the trained model."""
        import joblib

        if self.model is None:
            raise ValueError("No model to save")

        path = path or Path(settings.models_dir) / "position_forecast.pkl"
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)

    def load(self, path: Optional[Path] = None) -> None:
        """Load a trained model."""
        import joblib

        path = path or Path(settings.models_dir) / "position_forecast.pkl"
        self.model = joblib.load(path)
