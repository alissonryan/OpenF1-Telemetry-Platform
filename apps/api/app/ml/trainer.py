"""
Model training pipeline.
"""

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from app.core.config import settings
from app.core.logging import logger
from app.ml.feature_engineer import FeatureEngineer
from app.ml.pit_predictor import PitPredictor
from app.ml.position_forecast import PositionForecaster


class ModelTrainer:
    """Pipeline for training ML models."""

    def __init__(self):
        self.models_dir = Path(settings.models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.feature_engineer = FeatureEngineer()
        self.pit_predictor = PitPredictor()
        self.position_forecaster = PositionForecaster()

    def prepare_training_data(
        self,
        years: List[int],
        sessions: List[str],
    ) -> pd.DataFrame:
        """
        Prepare training data from historical sessions.

        Args:
            years: List of years to include
            sessions: List of session identifiers

        Returns:
            DataFrame with training features
        """
        # TODO: Implement data preparation from Fast-F1
        # This would load historical sessions and extract features
        logger.info(f"Preparing training data for {years}")
        return pd.DataFrame()

    def train_pit_predictor(
        self,
        data: Optional[pd.DataFrame] = None,
    ) -> Dict[str, float]:
        """
        Train the pit stop prediction model.

        Args:
            data: Optional pre-prepared training data

        Returns:
            Training metrics
        """
        if data is None:
            data = self.prepare_training_data(
                years=[2022, 2023],
                sessions=["R"],
            )

        metrics = self.pit_predictor.train(data)
        self.pit_predictor.save()
        return metrics

    def train_position_forecaster(
        self,
        data: Optional[pd.DataFrame] = None,
    ) -> Dict[str, float]:
        """
        Train the position forecasting model.

        Args:
            data: Optional pre-prepared training data

        Returns:
            Training metrics
        """
        if data is None:
            data = self.prepare_training_data(
                years=[2022, 2023],
                sessions=["R"],
            )

        metrics = self.position_forecaster.train(data)
        self.position_forecaster.save()
        return metrics

    def train_all(self) -> Dict[str, Dict[str, float]]:
        """
        Train all models.

        Returns:
            Dictionary of training metrics for each model
        """
        results = {}

        try:
            results["pit_predictor"] = self.train_pit_predictor()
        except Exception as e:
            logger.error(f"Failed to train pit predictor: {e}")
            results["pit_predictor"] = {"error": str(e)}

        try:
            results["position_forecaster"] = self.train_position_forecaster()
        except Exception as e:
            logger.error(f"Failed to train position forecaster: {e}")
            results["position_forecaster"] = {"error": str(e)}

        return results
