# Task: Build Prediction Engine

## Metadata
- **Agent**: @f1-ml-engineer
- **Sprint**: 6-7
- **Priority**: HIGH
- **Estimate**: 16h

## Objective
Implementar o engine de predições ML para pit stops e posições finais.

## Prerequisites
- [ ] Database com dados históricos
- [ ] Fast-F1 integration funcionando
- [ ] Feature engineering pipeline

## Inputs
- Dados históricos de corridas (2018-2024)
- Features definidas

## Outputs
- [ ] Pit Stop Predictor model
- [ ] Position Forecaster model
- [ ] API endpoints de predição
- [ ] Feature engineering pipeline

## Implementation

### Feature Engineering
```python
# app/ml/feature_engineer.py
import pandas as pd
import numpy as np
from typing import Dict, List

class F1FeatureEngineer:
    """Extract and transform features for ML models."""
    
    def __init__(self):
        self.feature_columns = [
            'tire_age', 'current_position', 'gap_to_leader', 'gap_to_ahead',
            'lap_number', 'avg_lap_time', 'tire_degradation_rate',
            'stops_completed', 'fuel_factor', 'sector_1_ratio', 
            'sector_2_ratio', 'sector_3_ratio'
        ]
    
    def extract_pit_features(
        self, 
        session_data: pd.DataFrame,
        driver_number: int,
        current_lap: int
    ) -> Dict:
        """Extract features for pit stop prediction."""
        
        driver_laps = session_data[
            session_data['driver_number'] == driver_number
        ]
        
        current_lap_data = driver_laps[
            driver_laps['lap_number'] == current_lap
        ].iloc[0]
        
        # Tire state
        tire_age = current_lap_data.get('tire_age', 0)
        tire_compound = current_lap_data.get('tire_compound', 'UNKNOWN')
        
        # Position
        current_position = current_lap_data.get('position', 20)
        gap_to_leader = current_lap_data.get('gap_to_leader', 0)
        
        # Calculate gap to car ahead
        positions = session_data[session_data['lap_number'] == current_lap]
        positions = positions.sort_values('position')
        current_idx = positions[positions['driver_number'] == driver_number].index[0]
        
        if current_idx > 0:
            ahead_gap = positions.iloc[current_idx - 1]['gap_to_leader']
            gap_to_ahead = gap_to_leader - ahead_gap
        else:
            gap_to_ahead = 0
        
        # Performance metrics
        recent_laps = driver_laps[
            (driver_laps['lap_number'] >= current_lap - 5) &
            (driver_laps['lap_number'] <= current_lap)
        ]
        
        avg_lap_time = recent_laps['lap_time'].mean()
        
        # Tire degradation (simplified)
        if len(recent_laps) >= 3:
            lap_times = recent_laps['lap_time'].values
            tire_degradation_rate = (lap_times[-1] - lap_times[0]) / len(lap_times)
        else:
            tire_degradation_rate = 0
        
        # Stops
        stops_completed = len(driver_laps[driver_laps['is_pit_in'] == True])
        
        # Fuel factor (simplified - decreases throughout race)
        total_laps = session_data['lap_number'].max()
        fuel_factor = 1 - (current_lap / total_laps)
        
        # Sector ratios
        sector_1_ratio = current_lap_data.get('sector_1', 0) / current_lap_data.get('lap_time', 1)
        sector_2_ratio = current_lap_data.get('sector_2', 0) / current_lap_data.get('lap_time', 1)
        sector_3_ratio = current_lap_data.get('sector_3', 0) / current_lap_data.get('lap_time', 1)
        
        return {
            'tire_age': tire_age,
            'current_position': current_position,
            'gap_to_leader': gap_to_leader,
            'gap_to_ahead': gap_to_ahead,
            'lap_number': current_lap,
            'avg_lap_time': avg_lap_time,
            'tire_degradation_rate': tire_degradation_rate,
            'stops_completed': stops_completed,
            'fuel_factor': fuel_factor,
            'sector_1_ratio': sector_1_ratio,
            'sector_2_ratio': sector_2_ratio,
            'sector_3_ratio': sector_3_ratio,
            'tire_compound_soft': 1 if tire_compound == 'SOFT' else 0,
            'tire_compound_medium': 1 if tire_compound == 'MEDIUM' else 0,
            'tire_compound_hard': 1 if tire_compound == 'HARD' else 0,
        }
    
    def extract_position_features(
        self,
        session_data: pd.DataFrame,
        driver_number: int,
        current_lap: int
    ) -> Dict:
        """Extract features for position forecasting."""
        
        driver_laps = session_data[
            session_data['driver_number'] == driver_number
        ]
        
        current_data = driver_laps[
            driver_laps['lap_number'] == current_lap
        ].iloc[0]
        
        # Current state
        features = {
            'current_position': current_data.get('position', 20),
            'current_lap': current_lap,
            'tire_age': current_data.get('tire_age', 0),
        }
        
        # Performance metrics
        recent = driver_laps[
            driver_laps['lap_number'] >= current_lap - 10
        ]
        
        features['avg_lap_time'] = recent['lap_time'].mean()
        features['lap_time_std'] = recent['lap_time'].std()
        features['best_lap_time'] = recent['lap_time'].min()
        
        # Sector analysis
        features['sector_1_avg'] = recent['sector_1'].mean()
        features['sector_2_avg'] = recent['sector_2'].mean()
        features['sector_3_avg'] = recent['sector_3'].mean()
        
        # Relative performance
        all_drivers = session_data['driver_number'].unique()
        leader_laps = session_data[session_data['position'] == 1]
        leader_avg = leader_laps['lap_time'].mean()
        
        features['pace_vs_leader'] = features['avg_lap_time'] - leader_avg
        
        # Strategy
        features['stops_completed'] = len(driver_laps[driver_laps['is_pit_in'] == True])
        
        return features
    
    def prepare_training_data(
        self, 
        sessions: List[pd.DataFrame],
        target: str = 'pit_stop'
    ) -> tuple[pd.DataFrame, pd.Series]:
        """Prepare training data from multiple sessions."""
        
        all_features = []
        all_targets = []
        
        for session in sessions:
            drivers = session['driver_number'].unique()
            
            for driver in drivers:
                driver_laps = session[session['driver_number'] == driver]
                pit_laps = driver_laps[driver_laps['is_pit_in'] == True]['lap_number'].values
                
                for lap_num in driver_laps['lap_number'].values:
                    features = self.extract_pit_features(session, driver, lap_num)
                    
                    # Target: will pit in next 5 laps?
                    if target == 'pit_stop':
                        will_pit = any(
                            pit_lap - lap_num <= 5 and pit_lap > lap_num 
                            for pit_lap in pit_laps
                        )
                        all_targets.append(1 if will_pit else 0)
                    
                    all_features.append(features)
        
        X = pd.DataFrame(all_features)
        y = pd.Series(all_targets)
        
        return X, y
```

### Pit Stop Predictor
```python
# app/ml/pit_predictor.py
import xgboost as xgb
import joblib
from pathlib import Path
from typing import Dict, Optional
import numpy as np

class PitStopPredictor:
    """Predict probability of pit stop in next 5 laps."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.feature_engineer = F1FeatureEngineer()
        
        if model_path:
            self.load(model_path)
    
    def train(self, X, y):
        """Train the pit stop prediction model."""
        
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss'
        )
        
        self.model.fit(X, y)
        
        # Log feature importance
        importance = dict(zip(
            self.feature_engineer.feature_columns,
            self.model.feature_importances_
        ))
        print("Feature Importance:", sorted(importance.items(), key=lambda x: -x[1]))
    
    def predict(self, features: Dict) -> float:
        """Predict pit stop probability."""
        
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        X = self._preprocess(features)
        proba = self.model.predict_proba(X)[0]
        
        return float(proba[1])  # Probability of pit stop
    
    def predict_batch(self, features_list: List[Dict]) -> List[float]:
        """Predict for multiple drivers."""
        
        X = np.array([self._preprocess(f)[0] for f in features_list])
        probas = self.model.predict_proba(X)
        
        return [float(p[1]) for p in probas]
    
    def _preprocess(self, features: Dict) -> np.ndarray:
        """Convert features dict to array."""
        
        # Ensure all expected features exist
        processed = []
        for col in self.feature_engineer.feature_columns:
            processed.append(features.get(col, 0))
        
        # Add compound one-hot encoding
        compound = features.get('tire_compound', 'UNKNOWN')
        processed.extend([
            1 if compound == 'SOFT' else 0,
            1 if compound == 'MEDIUM' else 0,
            1 if compound == 'HARD' else 0,
        ])
        
        return np.array([processed])
    
    def save(self, path: str):
        """Save model to disk."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)
    
    def load(self, path: str):
        """Load model from disk."""
        self.model = joblib.load(path)
```

### Position Forecaster
```python
# app/ml/position_forecaster.py
import xgboost as xgb
import joblib
from typing import Dict, List, Optional
import numpy as np

class PositionForecaster:
    """Predict final race position."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.feature_engineer = F1FeatureEngineer()
        
        if model_path:
            self.load(model_path)
    
    def train(self, X, y):
        """Train the position forecasting model."""
        
        self.model = xgb.XGBRegressor(
            n_estimators=150,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )
        
        self.model.fit(X, y)
    
    def predict(self, features: Dict) -> int:
        """Predict final position."""
        
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        X = self._preprocess(features)
        prediction = self.model.predict(X)[0]
        
        # Clamp to valid range
        return max(1, min(20, int(round(prediction))))
    
    def predict_batch(self, features_list: List[Dict]) -> List[int]:
        """Predict positions for all drivers."""
        
        X = np.array([self._preprocess(f)[0] for f in features_list])
        predictions = self.model.predict(X)
        
        # Normalize to ensure unique positions 1-20
        # (simplified - real implementation would use ranking)
        return [max(1, min(20, int(round(p)))) for p in predictions]
    
    def _preprocess(self, features: Dict) -> np.ndarray:
        """Convert features dict to array."""
        processed = []
        for col in self.feature_engineer.feature_columns:
            processed.append(features.get(col, 0))
        return np.array([processed])
    
    def save(self, path: str):
        joblib.dump(self.model, path)
    
    def load(self, path: str):
        self.model = joblib.load(path)
```

### Prediction API
```python
# app/routers/predictions.py
from fastapi import APIRouter, HTTPException
from app.ml.pit_predictor import PitStopPredictor
from app.ml.position_forecaster import PositionForecaster
from app.services.fastf1_service import FastF1Service

router = APIRouter(prefix="/api/v1/predictions", tags=["predictions"])

pit_predictor = PitStopPredictor(model_path="./models/pit_predictor_v1.pkl")
position_forecaster = PositionForecaster(model_path="./models/position_forecast_v1.pkl")

@router.get("/pit-probability/{session_key}/{driver_number}")
async def get_pit_probability(session_key: int, driver_number: int):
    """Get pit stop probability for a driver."""
    try:
        # Get current session data
        session_data = await get_session_data(session_key)
        current_lap = get_current_lap(session_data)
        
        # Extract features
        features = feature_engineer.extract_pit_features(
            session_data, driver_number, current_lap
        )
        
        # Predict
        probability = pit_predictor.predict(features)
        
        return {
            "driver_number": driver_number,
            "current_lap": current_lap,
            "pit_probability": probability,
            "confidence": "high" if probability > 0.7 or probability < 0.3 else "medium"
        }
    except Exception as e:
        raise HTTPException(500, f"Prediction failed: {str(e)}")

@router.get("/position-forecast/{session_key}")
async def get_position_forecast(session_key: int):
    """Get final position forecast for all drivers."""
    try:
        session_data = await get_session_data(session_key)
        current_lap = get_current_lap(session_data)
        
        drivers = session_data['driver_number'].unique()
        predictions = []
        
        for driver in drivers:
            features = feature_engineer.extract_position_features(
                session_data, driver, current_lap
            )
            position = position_forecaster.predict(features)
            
            predictions.append({
                "driver_number": driver,
                "current_position": features['current_position'],
                "predicted_final_position": position,
                "position_change": position - features['current_position']
            })
        
        # Sort by predicted position
        predictions.sort(key=lambda x: x['predicted_final_position'])
        
        return {
            "current_lap": current_lap,
            "predictions": predictions
        }
    except Exception as e:
        raise HTTPException(500, f"Forecast failed: {str(e)}")
```

## Acceptance Criteria
- [ ] Pit stop predictor com F1 > 0.75
- [ ] Position forecaster com MAE < 2.0
- [ ] API endpoints funcionando
- [ ] Models serializados e carregando
- [ ] Feature extraction otimizada

## Dependencies
- f1-connect-fastf1
- f1-design-database

## Risks
- Qualidade dos dados históricos
- Overfitting em condições específicas
