#!/usr/bin/env python3
"""
F1 ML Trainer - Script para treinar modelos de ML

Usage:
    python f1-ml-trainer.py train-pit --seasons 2022 2023 2024
    python f1-ml-trainer.py train-position --seasons 2022 2023 2024
    python f1-ml-trainer.py evaluate --model pit_predictor_v1.pkl
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import classification_report, mean_absolute_error, r2_score
import xgboost as xgb
import joblib

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "apps" / "api"))

try:
    from app.ml.feature_engineer import F1FeatureEngineer
    from app.ml.pit_predictor import PitStopPredictor
    from app.ml.position_forecaster import PositionForecaster
except ImportError:
    print("Warning: Could not import ML modules. Using standalone mode.")
    F1FeatureEngineer = None
    PitStopPredictor = None
    PositionForecaster = None


class F1MLTrainer:
    """Train and evaluate F1 prediction models."""
    
    def __init__(self, data_dir: str = "./data/processed", model_dir: str = "./models"):
        self.data_dir = Path(data_dir)
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        if F1FeatureEngineer:
            self.feature_engineer = F1FeatureEngineer()
        else:
            self.feature_engineer = None
    
    def load_training_data(self, seasons: List[int]) -> pd.DataFrame:
        """Load and combine training data from multiple seasons."""
        all_data = []
        
        for season in seasons:
            season_file = self.data_dir / f"season_{season}_features.csv"
            if season_file.exists():
                df = pd.read_csv(season_file)
                all_data.append(df)
                print(f"Loaded {len(df)} records from {season}")
            else:
                print(f"Warning: No data file for season {season}")
        
        if not all_data:
            raise FileNotFoundError("No training data found")
        
        combined = pd.concat(all_data, ignore_index=True)
        print(f"Total training records: {len(combined)}")
        
        return combined
    
    def train_pit_predictor(
        self, 
        seasons: List[int],
        output_name: str = None
    ) -> dict:
        """Train pit stop prediction model."""
        
        print("\n" + "="*50)
        print("Training Pit Stop Predictor")
        print("="*50)
        
        # Load data
        df = self.load_training_data(seasons)
        
        # Prepare features and target
        feature_cols = [
            'tire_age', 'current_position', 'gap_to_leader', 'gap_to_ahead',
            'lap_number', 'avg_lap_time', 'tire_degradation_rate',
            'stops_completed', 'fuel_factor'
        ]
        
        X = df[feature_cols].fillna(0)
        y = df['will_pit_next_5_laps']
        
        print(f"\nFeatures: {len(feature_cols)}")
        print(f"Samples: {len(X)}")
        print(f"Positive class: {y.sum()} ({y.mean()*100:.1f}%)")
        
        # Time-series cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        
        # Train model
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss'
        )
        
        # Cross-validation scores
        cv_scores = cross_val_score(model, X, y, cv=tscv, scoring='f1')
        print(f"\nCross-validation F1 scores: {cv_scores}")
        print(f"Mean F1: {cv_scores.mean():.3f} (+/- {cv_scores.std()*2:.3f})")
        
        # Train on full data
        model.fit(X, y)
        
        # Feature importance
        importance = dict(zip(feature_cols, model.feature_importances_))
        print("\nFeature Importance:")
        for feat, imp in sorted(importance.items(), key=lambda x: -x[1]):
            print(f"  {feat}: {imp:.4f}")
        
        # Save model
        output_name = output_name or f"pit_predictor_{datetime.now().strftime('%Y%m%d')}.pkl"
        model_path = self.model_dir / output_name
        joblib.dump(model, model_path)
        print(f"\nModel saved to: {model_path}")
        
        return {
            "model_path": str(model_path),
            "cv_f1_mean": cv_scores.mean(),
            "cv_f1_std": cv_scores.std(),
            "feature_importance": importance
        }
    
    def train_position_forecaster(
        self,
        seasons: List[int],
        output_name: str = None
    ) -> dict:
        """Train position forecasting model."""
        
        print("\n" + "="*50)
        print("Training Position Forecaster")
        print("="*50)
        
        # Load data
        df = self.load_training_data(seasons)
        
        # Prepare features and target
        feature_cols = [
            'current_position', 'current_lap', 'tire_age',
            'avg_lap_time', 'lap_time_std', 'best_lap_time',
            'sector_1_avg', 'sector_2_avg', 'sector_3_avg',
            'pace_vs_leader', 'stops_completed'
        ]
        
        X = df[feature_cols].fillna(0)
        y = df['final_position']
        
        print(f"\nFeatures: {len(feature_cols)}")
        print(f"Samples: {len(X)}")
        
        # Time-series cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        
        # Train model
        model = xgb.XGBRegressor(
            n_estimators=150,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )
        
        # Cross-validation scores
        cv_mae = -cross_val_score(model, X, y, cv=tscv, scoring='neg_mean_absolute_error')
        cv_r2 = cross_val_score(model, X, y, cv=tscv, scoring='r2')
        
        print(f"\nCross-validation MAE: {cv_mae}")
        print(f"Mean MAE: {cv_mae.mean():.3f} (+/- {cv_mae.std()*2:.3f})")
        print(f"\nCross-validation R²: {cv_r2}")
        print(f"Mean R²: {cv_r2.mean():.3f} (+/- {cv_r2.std()*2:.3f})")
        
        # Train on full data
        model.fit(X, y)
        
        # Feature importance
        importance = dict(zip(feature_cols, model.feature_importances_))
        print("\nFeature Importance:")
        for feat, imp in sorted(importance.items(), key=lambda x: -x[1]):
            print(f"  {feat}: {imp:.4f}")
        
        # Save model
        output_name = output_name or f"position_forecaster_{datetime.now().strftime('%Y%m%d')}.pkl"
        model_path = self.model_dir / output_name
        joblib.dump(model, model_path)
        print(f"\nModel saved to: {model_path}")
        
        return {
            "model_path": str(model_path),
            "cv_mae_mean": cv_mae.mean(),
            "cv_r2_mean": cv_r2.mean(),
            "feature_importance": importance
        }
    
    def evaluate_model(self, model_path: str, test_data_path: str = None) -> dict:
        """Evaluate a trained model."""
        
        print("\n" + "="*50)
        print(f"Evaluating Model: {model_path}")
        print("="*50)
        
        model = joblib.load(model_path)
        
        # Determine model type
        is_classifier = hasattr(model, 'predict_proba')
        
        if test_data_path:
            df = pd.read_csv(test_data_path)
            # Add evaluation logic here
        else:
            print("No test data provided. Model loaded successfully.")
            print(f"Model type: {'Classifier' if is_classifier else 'Regressor'}")
        
        return {"model_path": model_path, "type": "classifier" if is_classifier else "regressor"}


def main():
    parser = argparse.ArgumentParser(description="F1 ML Trainer")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Train pit predictor
    pit_parser = subparsers.add_parser("train-pit", help="Train pit stop predictor")
    pit_parser.add_argument("--seasons", type=int, nargs="+", required=True, help="Seasons to train on")
    pit_parser.add_argument("--output", type=str, help="Output model name")
    
    # Train position forecaster
    pos_parser = subparsers.add_parser("train-position", help="Train position forecaster")
    pos_parser.add_argument("--seasons", type=int, nargs="+", required=True, help="Seasons to train on")
    pos_parser.add_argument("--output", type=str, help="Output model name")
    
    # Evaluate model
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate a model")
    eval_parser.add_argument("--model", type=str, required=True, help="Path to model file")
    eval_parser.add_argument("--test-data", type=str, help="Path to test data")
    
    args = parser.parse_args()
    
    trainer = F1MLTrainer()
    
    if args.command == "train-pit":
        results = trainer.train_pit_predictor(args.seasons, args.output)
    
    elif args.command == "train-position":
        results = trainer.train_position_forecaster(args.seasons, args.output)
    
    elif args.command == "evaluate":
        results = trainer.evaluate_model(args.model, args.test_data)
    
    print("\n" + "="*50)
    print("Results:")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
