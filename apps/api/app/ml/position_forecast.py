"""
Position forecasting model for predicting final race positions.
"""

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

from app.core.config import settings
from app.core.logging import logger


class PositionForecaster:
    """ML model for forecasting driver positions."""

    def __init__(self, use_xgboost: bool = True):
        self.model = None
        self.scaler = StandardScaler()
        self.use_xgboost = use_xgboost
        self.is_trained = False
        
        # Feature names for position forecasting
        self.feature_names = [
            "current_position",
            "lap_number",
            "tyre_age",
            "pace_delta",
            "gap_ahead",
            "gap_behind",
            "remaining_laps",
            "compound_type",
            "avg_lap_time",
            "sector_1_avg",
            "sector_2_avg",
            "sector_3_avg",
            "drs_available",
            "position_change_rate",
        ]

    def _initialize_model(self):
        """Initialize the ML model."""
        if self.use_xgboost:
            try:
                import xgboost as xgb
                self.model = xgb.XGBRegressor(
                    n_estimators=150,
                    learning_rate=0.1,
                    max_depth=6,
                    min_child_weight=3,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                )
            except ImportError:
                logger.warning("XGBoost not available, falling back to GradientBoosting")
                self.model = GradientBoostingRegressor(
                    n_estimators=150,
                    learning_rate=0.1,
                    max_depth=6,
                    random_state=42,
                )
        else:
            self.model = GradientBoostingRegressor(
                n_estimators=150,
                learning_rate=0.1,
                max_depth=6,
                random_state=42,
            )

    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for training/prediction.
        
        Args:
            data: Raw data DataFrame
            
        Returns:
            DataFrame with prepared features
        """
        df = data.copy()
        
        # Compound encoding
        compound_encoding = {
            "SOFT": 1,
            "MEDIUM": 2,
            "HARD": 3,
            "INTERMEDIATE": 4,
            "WET": 5,
        }
        
        if 'compound_type' in df.columns and df['compound_type'].dtype == object:
            df['compound_type'] = df['compound_type'].map(compound_encoding).fillna(0)
        
        # Fill missing values
        for col in self.feature_names:
            if col in df.columns:
                df[col] = df[col].fillna(0)
        
        return df[self.feature_names]

    def train(
        self,
        data: pd.DataFrame,
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> Dict[str, float]:
        """
        Train the position forecasting model.

        Args:
            data: DataFrame with training data including 'final_position' target
            test_size: Fraction of data for testing
            random_state: Random seed

        Returns:
            Dictionary with training metrics
        """
        if self.model is None:
            self._initialize_model()
        
        X = self.prepare_features(data)
        y = data["final_position"]
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        
        metrics = {
            "train_r2": self.model.score(X_train_scaled, y_train),
            "test_r2": r2_score(y_test, y_pred),
            "mae": mean_absolute_error(y_test, y_pred),
        }

        logger.info(f"PositionForecaster trained: {metrics}")
        return metrics

    def predict_final_positions(
        self,
        session_data: Dict,
        laps_ahead: int = 10
    ) -> List[Dict]:
        """
        Predict final positions for all drivers.

        Args:
            session_data: Dictionary containing session state for all drivers
            laps_ahead: Number of laps to forecast ahead

        Returns:
            List of dictionaries with predictions per driver
        """
        if not self.is_trained or self.model is None:
            return self._heuristic_prediction(session_data, laps_ahead)
        
        predictions = []
        drivers = session_data.get("drivers", [])
        
        for driver in drivers:
            features = self._extract_features(driver, session_data)
            X = np.array([[features.get(f, 0) for f in self.feature_names]])
            X_scaled = self.scaler.transform(X)
            
            predicted_position = float(self.model.predict(X_scaled)[0])
            current_position = driver.get("position", 0)
            
            # Calculate confidence based on prediction variance
            confidence = self._calculate_confidence(features, current_position, predicted_position)
            
            predictions.append({
                "driver_number": driver.get("driver_number"),
                "driver_name": driver.get("name_acronym", ""),
                "team_name": driver.get("team_name", ""),
                "current_position": int(current_position),
                "predicted_position": max(1, min(20, round(predicted_position))),
                "position_change": int(current_position - round(predicted_position)),
                "confidence": round(confidence, 3),
                "factors": self._get_prediction_factors(features, current_position, predicted_position),
            })
        
        # Sort by predicted position
        predictions.sort(key=lambda x: x["predicted_position"])
        
        return predictions

    def _extract_features(self, driver: Dict, session_data: Dict) -> Dict:
        """Extract features for a single driver."""
        return {
            "current_position": driver.get("position", 0),
            "lap_number": session_data.get("current_lap", 0),
            "tyre_age": driver.get("tyre_age", 0),
            "pace_delta": driver.get("pace_delta", 0),
            "gap_ahead": driver.get("gap_ahead", 0),
            "gap_behind": driver.get("gap_behind", 0),
            "remaining_laps": session_data.get("total_laps", 50) - session_data.get("current_lap", 0),
            "compound_type": self._encode_compound(driver.get("compound", "MEDIUM")),
            "avg_lap_time": driver.get("avg_lap_time", 90),
            "sector_1_avg": driver.get("sector_1_avg", 30),
            "sector_2_avg": driver.get("sector_2_avg", 30),
            "sector_3_avg": driver.get("sector_3_avg", 30),
            "drs_available": 1 if driver.get("drs_available", False) else 0,
            "position_change_rate": driver.get("position_change_rate", 0),
        }

    def _encode_compound(self, compound: str) -> int:
        """Encode tyre compound as integer."""
        encoding = {
            "SOFT": 1,
            "MEDIUM": 2,
            "HARD": 3,
            "INTERMEDIATE": 4,
            "WET": 5,
        }
        return encoding.get(compound, 0)

    def _heuristic_prediction(self, session_data: Dict, laps_ahead: int) -> List[Dict]:
        """Generate heuristic-based predictions when model is not trained."""
        predictions = []
        drivers = session_data.get("drivers", [])
        
        for driver in drivers:
            current_position = driver.get("position", 0)
            pace_delta = driver.get("pace_delta", 0)
            tyre_age = driver.get("tyre_age", 0)
            
            # Heuristic: pace advantage + fresh tyres = position gain
            position_change = 0
            
            # Pace advantage (positive = faster)
            position_change += pace_delta * -0.1 * laps_ahead
            
            # Tyre age factor (fresh tyres advantage)
            if tyre_age < 10:
                position_change += 1
            elif tyre_age > 25:
                position_change -= 1
            
            predicted_position = max(1, min(20, current_position - round(position_change)))
            
            # Calculate confidence
            confidence = 0.5 + min(0.3, abs(pace_delta) * 0.05)
            
            predictions.append({
                "driver_number": driver.get("driver_number"),
                "driver_name": driver.get("name_acronym", ""),
                "team_name": driver.get("team_name", ""),
                "current_position": int(current_position),
                "predicted_position": predicted_position,
                "position_change": int(current_position - predicted_position),
                "confidence": round(confidence, 3),
                "factors": self._get_heuristic_factors(driver),
            })
        
        predictions.sort(key=lambda x: x["predicted_position"])
        return predictions

    def _calculate_confidence(
        self,
        features: Dict,
        current_position: float,
        predicted_position: float
    ) -> float:
        """Calculate prediction confidence."""
        confidence = 0.5
        
        # Higher confidence for positions near front (less variance typically)
        if current_position <= 5:
            confidence += 0.15
        elif current_position <= 10:
            confidence += 0.1
        
        # Higher confidence when prediction is close to current
        position_diff = abs(current_position - predicted_position)
        confidence += max(0, 0.2 - position_diff * 0.03)
        
        # Remaining laps factor
        remaining = features.get("remaining_laps", 20)
        if remaining < 10:
            confidence += 0.15  # More certain near end
        elif remaining < 20:
            confidence += 0.1
        
        return min(0.95, max(0.3, confidence))

    def _get_prediction_factors(
        self,
        features: Dict,
        current_position: float,
        predicted_position: float
    ) -> List[str]:
        """Get human-readable factors affecting prediction."""
        factors = []
        
        if predicted_position < current_position:
            factors.append("Pace advantage over rivals")
        elif predicted_position > current_position:
            factors.append("Under pressure from behind")
        
        if features.get("tyre_age", 0) > 20:
            factors.append("High tyre degradation")
        elif features.get("tyre_age", 0) < 10:
            factors.append("Fresh tyre advantage")
        
        pace_delta = features.get("pace_delta", 0)
        if pace_delta < -0.5:
            factors.append("Strong recent pace")
        elif pace_delta > 0.5:
            factors.append("Losing pace relative to rivals")
        
        if features.get("drs_available", 0):
            factors.append("DRS advantage available")
        
        return factors[:3]

    def _get_heuristic_factors(self, driver: Dict) -> List[str]:
        """Get factors for heuristic prediction."""
        factors = []
        
        pace_delta = driver.get("pace_delta", 0)
        if pace_delta < -0.3:
            factors.append("Strong race pace")
        elif pace_delta > 0.3:
            factors.append("Slower race pace")
        
        tyre_age = driver.get("tyre_age", 0)
        if tyre_age > 20:
            factors.append("Tyre degradation concern")
        elif tyre_age < 10:
            factors.append("Fresh tyre advantage")
        
        return factors[:2]

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model."""
        if not self.is_trained or self.model is None:
            return {}
        
        if hasattr(self.model, 'feature_importances_'):
            return dict(zip(self.feature_names, self.model.feature_importances_))
        return {}

    def save(self, path: Optional[Path] = None) -> None:
        """Save the trained model and scaler."""
        if self.model is None:
            raise ValueError("No model to save")

        path = path or Path(settings.models_dir) / "position_forecaster"
        path.mkdir(parents=True, exist_ok=True)
        
        joblib.dump(self.model, path / "model.pkl")
        joblib.dump(self.scaler, path / "scaler.pkl")
        joblib.dump({
            "feature_names": self.feature_names,
            "is_trained": self.is_trained,
        }, path / "metadata.pkl")
        
        logger.info(f"PositionForecaster saved to {path}")

    def load(self, path: Optional[Path] = None) -> None:
        """Load a trained model and scaler."""
        path = path or Path(settings.models_dir) / "position_forecaster"
        
        try:
            self.model = joblib.load(path / "model.pkl")
            self.scaler = joblib.load(path / "scaler.pkl")
            metadata = joblib.load(path / "metadata.pkl")
            self.feature_names = metadata.get("feature_names", self.feature_names)
            self.is_trained = metadata.get("is_trained", False)
            logger.info(f"PositionForecaster loaded from {path}")
        except FileNotFoundError:
            logger.warning(f"No saved model found at {path}, using heuristic predictions")
            self.is_trained = False
