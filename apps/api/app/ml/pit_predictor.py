"""
Pit stop prediction model with XGBoost classifier.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib

from app.core.config import settings
from app.core.logging import logger


class PitStopPredictor:
    """ML model for predicting pit stops with confidence scores."""

    def __init__(self, use_xgboost: bool = True):
        self.model = None
        self.scaler = StandardScaler()
        self.use_xgboost = use_xgboost
        self.is_trained = False
        
        # Feature names for pit stop prediction
        self.feature_names = [
            "tyre_age",
            "position",
            "lap_number",
            "gap_to_leader",
            "gap_to_ahead",
            "fuel_load",
            "compound_type",
            "degradation_rate",
            "avg_lap_time",
            "lap_time_trend",
            "stint_length",
            "remaining_laps",
        ]
        
        # Compound encoding
        self.compound_encoding = {
            "SOFT": 1,
            "MEDIUM": 2,
            "HARD": 3,
            "INTERMEDIATE": 4,
            "WET": 5,
        }
        
        # Compound recommendations based on current compound
        self.compound_recommendations = {
            "SOFT": ["MEDIUM", "HARD"],
            "MEDIUM": ["HARD", "MEDIUM"],
            "HARD": ["MEDIUM", "SOFT"],
            "INTERMEDIATE": ["WET", "INTERMEDIATE"],
            "WET": ["INTERMEDIATE", "WET"],
        }

    def _initialize_model(self):
        """Initialize the ML model."""
        if self.use_xgboost:
            try:
                import xgboost as xgb
                self.model = xgb.XGBClassifier(
                    n_estimators=150,
                    learning_rate=0.1,
                    max_depth=6,
                    min_child_weight=3,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    eval_metric='logloss',
                    use_label_encoder=False
                )
            except ImportError:
                logger.warning("XGBoost not available, falling back to GradientBoosting")
                self.model = GradientBoostingClassifier(
                    n_estimators=150,
                    learning_rate=0.1,
                    max_depth=6,
                    random_state=42,
                )
        else:
            self.model = GradientBoostingClassifier(
                n_estimators=150,
                learning_rate=0.1,
                max_depth=6,
                random_state=42,
            )

    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare and engineer features for training/prediction.
        
        Args:
            data: Raw data DataFrame
            
        Returns:
            DataFrame with prepared features
        """
        df = data.copy()
        
        # Encode compound type if string
        if 'compound_type' in df.columns and df['compound_type'].dtype == object:
            df['compound_type'] = df['compound_type'].map(self.compound_encoding).fillna(0)
        
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
        Train the pit stop prediction model.

        Args:
            data: DataFrame with training data including 'pitted_next_lap' target
            test_size: Fraction of data for testing
            random_state: Random seed for reproducibility

        Returns:
            Dictionary with training metrics
        """
        if self.model is None:
            self._initialize_model()
        
        # Prepare features
        X = self.prepare_features(data)
        y = data["pitted_next_lap"]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        metrics = {
            "train_accuracy": accuracy_score(y_train, self.model.predict(X_train_scaled)),
            "test_accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall": recall_score(y_test, y_pred, zero_division=0),
            "f1_score": f1_score(y_test, y_pred, zero_division=0),
        }

        logger.info(f"PitStopPredictor trained: {metrics}")
        return metrics

    def predict(self, current_state: Dict) -> Dict:
        """
        Predict probability of pit stop with detailed output.

        Args:
            current_state: Dictionary containing current driver state

        Returns:
            Dictionary with prediction details
        """
        if not self.is_trained or self.model is None:
            # Return heuristic-based prediction if model not trained
            return self._heuristic_prediction(current_state)
        
        # Prepare features
        features = {}
        for name in self.feature_names:
            if name == "compound_type" and isinstance(current_state.get(name), str):
                features[name] = self.compound_encoding.get(current_state.get(name), 0)
            else:
                features[name] = current_state.get(name, 0)
        
        X = np.array([[features.get(f, 0) for f in self.feature_names]])
        X_scaled = self.scaler.transform(X)
        
        # Get prediction probability
        probability = float(self.model.predict_proba(X_scaled)[0][1])
        
        # Predict lap (based on probability and current state)
        predicted_lap = current_state.get("lap_number", 0) + max(1, int(5 * (1 - probability)))
        
        # Get recommended compound
        current_compound = current_state.get("compound_type", "MEDIUM")
        if isinstance(current_compound, int):
            current_compound = {v: k for k, v in self.compound_encoding.items()}.get(current_compound, "MEDIUM")
        recommended_compound = self.compound_recommendations.get(current_compound, ["MEDIUM"])[0]
        
        # Calculate confidence based on feature values
        confidence = self._calculate_confidence(features, probability)
        
        # Get reasons for prediction
        reasons = self._get_prediction_reasons(features, probability)
        
        return {
            "probability": round(probability, 3),
            "predicted_lap": predicted_lap,
            "recommended_compound": recommended_compound,
            "confidence": round(confidence, 3),
            "reasons": reasons,
        }

    def _heuristic_prediction(self, state: Dict) -> Dict:
        """Generate heuristic-based prediction when model is not trained."""
        tyre_age = state.get("tyre_age", 0)
        compound = state.get("compound_type", "MEDIUM")
        if isinstance(compound, str):
            compound_encoded = self.compound_encoding.get(compound, 2)
        else:
            compound_encoded = compound
            compound = {v: k for k, v in self.compound_encoding.items()}.get(compound, "MEDIUM")
        
        # Heuristic: higher tyre age and softer compounds increase pit probability
        base_prob = 0.1
        
        # Tyre age factor
        if tyre_age > 30:
            base_prob += 0.5
        elif tyre_age > 20:
            base_prob += 0.3
        elif tyre_age > 15:
            base_prob += 0.15
        
        # Compound factor (softer = more likely to pit)
        if compound_encoded == 1:  # SOFT
            base_prob += 0.2
        elif compound_encoded == 2:  # MEDIUM
            base_prob += 0.1
        
        # Degradation factor
        degradation = state.get("degradation_rate", 0)
        if degradation > 0.5:
            base_prob += 0.2
        
        probability = min(0.95, max(0.05, base_prob))
        
        recommended_compound = self.compound_recommendations.get(compound, ["MEDIUM"])[0]
        
        reasons = []
        if tyre_age > 20:
            reasons.append(f"High tyre age ({tyre_age} laps)")
        if compound_encoded == 1 and tyre_age > 15:
            reasons.append("Soft compound degradation")
        if degradation > 0.3:
            reasons.append("Elevated degradation rate")
        if not reasons:
            reasons.append("Routine pit window approaching")
        
        return {
            "probability": round(probability, 3),
            "predicted_lap": state.get("lap_number", 0) + max(1, int(5 * (1 - probability))),
            "recommended_compound": recommended_compound,
            "confidence": 0.6,  # Lower confidence for heuristic
            "reasons": reasons,
        }

    def _calculate_confidence(self, features: Dict, probability: float) -> float:
        """Calculate prediction confidence based on feature values."""
        # Higher confidence when probability is extreme or tyre age is high
        confidence = 0.5
        
        # Probability extremity
        confidence += 0.2 * abs(probability - 0.5)
        
        # Tyre age confidence
        tyre_age = features.get("tyre_age", 0)
        if tyre_age > 20:
            confidence += 0.15
        elif tyre_age > 10:
            confidence += 0.1
        
        return min(0.95, max(0.3, confidence))

    def _get_prediction_reasons(self, features: Dict, probability: float) -> List[str]:
        """Generate human-readable reasons for the prediction."""
        reasons = []
        
        if features.get("tyre_age", 0) > 25:
            reasons.append(f"High tyre age ({int(features['tyre_age'])} laps)")
        elif features.get("tyre_age", 0) > 15:
            reasons.append(f"Moderate tyre age ({int(features['tyre_age'])} laps)")
        
        if features.get("degradation_rate", 0) > 0.3:
            reasons.append("Elevated degradation rate")
        
        compound = features.get("compound_type", 2)
        if compound == 1:  # SOFT
            reasons.append("Soft compound strategy")
        
        if features.get("remaining_laps", 20) < 15:
            reasons.append("Approaching end of race")
        
        if probability > 0.7:
            reasons.append("Multiple factors indicate pit window")
        
        if not reasons:
            reasons.append("Routine pit window analysis")
        
        return reasons[:4]  # Limit to 4 reasons

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model."""
        if not self.is_trained or self.model is None:
            return {}
        
        if hasattr(self.model, 'feature_importances_'):
            return dict(zip(self.feature_names, self.model.feature_importances_))
        return {}

    def save(self, path: Optional[Path] = None) -> None:
        """Save the trained model and scaler to disk."""
        if self.model is None:
            raise ValueError("No model to save")

        path = path or Path(settings.models_dir) / "pit_predictor"
        path.mkdir(parents=True, exist_ok=True)
        
        # Save model
        joblib.dump(self.model, path / "model.pkl")
        joblib.dump(self.scaler, path / "scaler.pkl")
        joblib.dump({
            "feature_names": self.feature_names,
            "is_trained": self.is_trained,
        }, path / "metadata.pkl")
        
        logger.info(f"Model saved to {path}")

    def load(self, path: Optional[Path] = None) -> None:
        """Load a trained model and scaler from disk."""
        path = path or Path(settings.models_dir) / "pit_predictor"
        
        try:
            self.model = joblib.load(path / "model.pkl")
            self.scaler = joblib.load(path / "scaler.pkl")
            metadata = joblib.load(path / "metadata.pkl")
            self.feature_names = metadata.get("feature_names", self.feature_names)
            self.is_trained = metadata.get("is_trained", False)
            logger.info(f"Model loaded from {path}")
        except FileNotFoundError:
            logger.warning(f"No saved model found at {path}, using heuristic predictions")
            self.is_trained = False
