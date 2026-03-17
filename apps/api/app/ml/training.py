"""
Training script for ML models using Fast-F1 historical data.
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import numpy as np
import pandas as pd

from app.core.config import settings
from app.core.logging import logger
from app.ml.pit_predictor import PitStopPredictor
from app.ml.position_forecast import PositionForecaster
from app.ml.strategy_recommender import StrategyRecommender
from app.ml.feature_engineer import FeatureEngineer


class ModelTrainingPipeline:
    """Pipeline for training all ML models with Fast-F1 data."""

    def __init__(self):
        self.models_dir = Path(settings.models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_dir = Path(settings.fastf1_cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.feature_engineer = FeatureEngineer()
        self.pit_predictor = PitStopPredictor()
        self.position_forecaster = PositionForecaster()
        self.strategy_recommender = StrategyRecommender()

    def load_historical_data(
        self,
        years: List[int] = None,
        sessions: List[str] = None,
        max_races: int = 10,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load historical race data from Fast-F1.
        
        Args:
            years: Years to load (default: [2023, 2024])
            sessions: Session types to load (default: ['R'] for race)
            max_races: Maximum number of races to load per year
            
        Returns:
            Tuple of (pit_data, position_data) DataFrames
        """
        try:
            import fastf1
            fastf1.Cache.enable_cache(str(self.cache_dir))
        except ImportError:
            logger.error("Fast-F1 not installed. Install with: pip install fastf1")
            return pd.DataFrame(), pd.DataFrame()
        
        years = years or [2023, 2024]
        sessions = sessions or ['R']  # Race sessions only
        
        pit_data_list = []
        position_data_list = []
        
        for year in years:
            # Get schedule for the year
            try:
                schedule = fastf1.get_event_schedule(year)
                race_events = schedule[schedule['Session5'] == 'Race'].head(max_races)
                
                for _, event in race_events.iterrows():
                    try:
                        logger.info(f"Loading {year} {event['EventName']}")
                        
                        session = fastf1.get_session(year, event['EventName'], 'R')
                        session.load()
                        
                        # Extract pit stop training data
                        pit_df = self._extract_pit_training_data(session, year, event['EventName'])
                        if not pit_df.empty:
                            pit_data_list.append(pit_df)
                        
                        # Extract position training data
                        pos_df = self._extract_position_training_data(session, year, event['EventName'])
                        if not pos_df.empty:
                            position_data_list.append(pos_df)
                            
                    except Exception as e:
                        logger.warning(f"Failed to load {year} {event['EventName']}: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Failed to get schedule for {year}: {e}")
                continue
        
        pit_data = pd.concat(pit_data_list, ignore_index=True) if pit_data_list else pd.DataFrame()
        position_data = pd.concat(position_data_list, ignore_index=True) if position_data_list else pd.DataFrame()
        
        logger.info(f"Loaded {len(pit_data)} pit samples, {len(position_data)} position samples")
        return pit_data, position_data

    def _extract_pit_training_data(
        self,
        session,
        year: int,
        event_name: str,
    ) -> pd.DataFrame:
        """Extract training data for pit stop prediction."""
        data = []
        
        try:
            laps = session.laps
            drivers = laps['Driver'].unique()
            
            for driver in drivers:
                driver_laps = laps.pick_driver(driver)
                
                if driver_laps.empty:
                    continue
                
                # Get pit stops for this driver
                pit_laps = set()
                if hasattr(session, 'pitstops') and session.pitstops is not None:
                    driver_pits = session.pitstops[session.pitstops['Driver'] == driver]
                    pit_laps = set(driver_pits['LapNumber'].tolist())
                
                # Also detect from lap data (compound changes)
                compounds = driver_laps['Compound'].tolist()
                for i in range(1, len(compounds)):
                    if compounds[i] != compounds[i-1]:
                        pit_laps.add(driver_laps.iloc[i]['LapNumber'])
                
                # Create samples for each lap
                for idx, lap in driver_laps.iterrows():
                    lap_number = lap['LapNumber']
                    
                    # Check if driver pits in next lap
                    pitted_next_lap = (lap_number + 1) in pit_laps
                    
                    # Calculate features
                    tyre_age = self._calculate_tyre_age(driver_laps, lap_number)
                    
                    sample = {
                        'year': year,
                        'event': event_name,
                        'driver': driver,
                        'lap_number': lap_number,
                        'position': lap.get('Position', 0),
                        'tyre_age': tyre_age,
                        'compound_type': lap.get('Compound', 'UNKNOWN'),
                        'pitted_next_lap': int(pitted_next_lap),
                        'gap_to_leader': 0,  # Would need to calculate
                        'fuel_load': max(0, 110 - (lap_number * 1.5)),  # Approximate
                        'degradation_rate': self._calculate_degradation(driver_laps, lap_number),
                        'avg_lap_time': self._get_avg_lap_time(driver_laps, lap_number),
                        'stint_length': tyre_age,
                        'remaining_laps': len(driver_laps) - lap_number,
                    }
                    
                    data.append(sample)
                    
        except Exception as e:
            logger.warning(f"Error extracting pit data: {e}")
        
        return pd.DataFrame(data)

    def _extract_position_training_data(
        self,
        session,
        year: int,
        event_name: str,
    ) -> pd.DataFrame:
        """Extract training data for position forecasting."""
        data = []
        
        try:
            laps = session.laps
            drivers = laps['Driver'].unique()
            
            # Get final positions
            final_positions = {}
            for driver in drivers:
                driver_laps = laps.pick_driver(driver)
                if not driver_laps.empty:
                    last_lap = driver_laps.iloc[-1]
                    final_positions[driver] = last_lap.get('Position', 0)
            
            # Create samples at different race points
            for driver in drivers:
                driver_laps = laps.pick_driver(driver)
                
                if driver_laps.empty:
                    continue
                
                total_laps = len(driver_laps)
                
                # Sample at 25%, 50%, 75% of race
                sample_points = [0.25, 0.5, 0.75]
                
                for point in sample_points:
                    sample_lap = int(total_laps * point)
                    if sample_lap < 1:
                        continue
                    
                    lap = driver_laps[driver_laps['LapNumber'] == sample_lap]
                    if lap.empty:
                        continue
                    
                    lap = lap.iloc[0]
                    
                    sample = {
                        'year': year,
                        'event': event_name,
                        'driver': driver,
                        'lap_number': sample_lap,
                        'current_position': lap.get('Position', 0),
                        'final_position': final_positions.get(driver, 0),
                        'tyre_age': self._calculate_tyre_age(driver_laps, sample_lap),
                        'compound_type': lap.get('Compound', 'UNKNOWN'),
                        'pace_delta': 0,  # Would calculate vs average
                        'gap_ahead': 0,
                        'gap_behind': 0,
                        'remaining_laps': total_laps - sample_lap,
                        'avg_lap_time': self._get_avg_lap_time(driver_laps, sample_lap),
                    }
                    
                    data.append(sample)
                    
        except Exception as e:
            logger.warning(f"Error extracting position data: {e}")
        
        return pd.DataFrame(data)

    def _calculate_tyre_age(self, laps: pd.DataFrame, current_lap: int) -> int:
        """Calculate tyre age at a specific lap."""
        relevant_laps = laps[laps['LapNumber'] <= current_lap]
        
        if relevant_laps.empty:
            return 0
        
        # Find stint start
        compounds = relevant_laps['Compound'].tolist()
        tyre_age = 1
        
        for i in range(len(compounds) - 2, -1, -1):
            if i < len(compounds) and compounds[i] == compounds[-1]:
                tyre_age += 1
            else:
                break
        
        return tyre_age

    def _calculate_degradation(self, laps: pd.DataFrame, current_lap: int) -> float:
        """Calculate tyre degradation rate."""
        relevant_laps = laps[laps['LapNumber'] <= current_lap]
        relevant_laps = relevant_laps[relevant_laps['LapTime'].notna()]
        
        if len(relevant_laps) < 5:
            return 0.0
        
        lap_numbers = relevant_laps['LapNumber'].values[-10:]
        lap_times = relevant_laps['LapTime'].dt.total_seconds().values[-10:]
        
        if len(lap_numbers) < 5:
            return 0.0
        
        # Linear regression for degradation rate
        try:
            slope, _ = np.polyfit(lap_numbers, lap_times, 1)
            return slope
        except:
            return 0.0

    def _get_avg_lap_time(self, laps: pd.DataFrame, current_lap: int) -> float:
        """Get average lap time up to current lap."""
        relevant_laps = laps[laps['LapNumber'] <= current_lap]
        relevant_laps = relevant_laps[relevant_laps['LapTime'].notna()]
        
        if relevant_laps.empty:
            return 90.0
        
        return relevant_laps['LapTime'].dt.total_seconds().mean()

    def generate_synthetic_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate synthetic training data for testing.
        
        Returns:
            Tuple of (pit_data, position_data) DataFrames
        """
        np.random.seed(42)
        
        # Generate pit stop data
        pit_samples = 5000
        
        pit_data = pd.DataFrame({
            'tyre_age': np.random.randint(1, 40, pit_samples),
            'position': np.random.randint(1, 21, pit_samples),
            'lap_number': np.random.randint(1, 60, pit_samples),
            'gap_to_leader': np.random.uniform(0, 30, pit_samples),
            'gap_to_ahead': np.random.uniform(0.5, 5, pit_samples),
            'fuel_load': np.random.uniform(30, 110, pit_samples),
            'compound_type': np.random.choice([1, 2, 3], pit_samples),
            'degradation_rate': np.random.uniform(-0.1, 0.5, pit_samples),
            'avg_lap_time': np.random.uniform(85, 95, pit_samples),
            'lap_time_trend': np.random.uniform(-0.1, 0.3, pit_samples),
            'stint_length': np.random.randint(1, 35, pit_samples),
            'remaining_laps': np.random.randint(1, 50, pit_samples),
        })
        
        # Generate target: probability increases with tyre age and degradation
        pit_probability = (
            (pit_data['tyre_age'] / 40) * 0.4 +
            (pit_data['degradation_rate'] / 0.5) * 0.3 +
            (pit_data['stint_length'] / 35) * 0.2 +
            np.random.uniform(0, 0.1, pit_samples)
        )
        pit_data['pitted_next_lap'] = (pit_probability > np.random.uniform(0, 1, pit_samples)).astype(int)
        
        # Generate position data
        pos_samples = 3000
        
        position_data = pd.DataFrame({
            'current_position': np.random.randint(1, 21, pos_samples),
            'lap_number': np.random.randint(5, 55, pos_samples),
            'tyre_age': np.random.randint(1, 35, pos_samples),
            'pace_delta': np.random.uniform(-1, 1, pos_samples),
            'gap_ahead': np.random.uniform(0.5, 10, pos_samples),
            'gap_behind': np.random.uniform(0.5, 10, pos_samples),
            'remaining_laps': np.random.randint(5, 45, pos_samples),
            'compound_type': np.random.choice([1, 2, 3], pos_samples),
            'avg_lap_time': np.random.uniform(85, 95, pos_samples),
            'sector_1_avg': np.random.uniform(28, 32, pos_samples),
            'sector_2_avg': np.random.uniform(28, 32, pos_samples),
            'sector_3_avg': np.random.uniform(28, 32, pos_samples),
            'drs_available': np.random.choice([0, 1], pos_samples),
            'position_change_rate': np.random.uniform(-0.1, 0.1, pos_samples),
        })
        
        # Generate final position (slightly correlated with current position)
        position_data['final_position'] = np.clip(
            position_data['current_position'] + 
            np.random.randint(-3, 4, pos_samples) +
            (position_data['pace_delta'] * -2).astype(int),
            1, 20
        )
        
        logger.info(f"Generated synthetic data: {len(pit_data)} pit, {len(position_data)} position samples")
        return pit_data, position_data

    def train_all_models(
        self,
        use_historical: bool = True,
        years: List[int] = None,
        max_races: int = 5,
    ) -> Dict:
        """
        Train all ML models.
        
        Args:
            use_historical: Whether to use historical data (vs synthetic)
            years: Years to load for historical data
            max_races: Maximum races to load per year
            
        Returns:
            Dictionary with training results
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'models': {}
        }
        
        # Load or generate data
        if use_historical:
            pit_data, position_data = self.load_historical_data(
                years=years,
                max_races=max_races
            )
            
            # Fall back to synthetic if not enough data
            if len(pit_data) < 1000 or len(position_data) < 500:
                logger.warning("Insufficient historical data, using synthetic data")
                syn_pit, syn_pos = self.generate_synthetic_data()
                
                if len(pit_data) < 1000:
                    pit_data = syn_pit
                if len(position_data) < 500:
                    position_data = syn_pos
        else:
            pit_data, position_data = self.generate_synthetic_data()
        
        # Train pit predictor
        try:
            logger.info("Training PitStopPredictor...")
            pit_metrics = self.pit_predictor.train(pit_data)
            self.pit_predictor.save()
            results['models']['pit_predictor'] = {
                'status': 'success',
                'metrics': pit_metrics
            }
        except Exception as e:
            logger.error(f"Failed to train pit predictor: {e}")
            results['models']['pit_predictor'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Train position forecaster
        try:
            logger.info("Training PositionForecaster...")
            pos_metrics = self.position_forecaster.train(position_data)
            self.position_forecaster.save()
            results['models']['position_forecaster'] = {
                'status': 'success',
                'metrics': pos_metrics
            }
        except Exception as e:
            logger.error(f"Failed to train position forecaster: {e}")
            results['models']['position_forecaster'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Initialize strategy recommender (rule-based)
        try:
            logger.info("Initializing StrategyRecommender...")
            self.strategy_recommender.train(pd.DataFrame())
            self.strategy_recommender.save()
            results['models']['strategy_recommender'] = {
                'status': 'success',
                'metrics': {'method': 'rule_based'}
            }
        except Exception as e:
            logger.error(f"Failed to initialize strategy recommender: {e}")
            results['models']['strategy_recommender'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Save training summary
        summary_path = self.models_dir / "training_summary.json"
        import json
        with open(summary_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Training complete. Summary saved to {summary_path}")
        return results


def train_models_cli():
    """CLI entry point for training models."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train F1 ML models')
    parser.add_argument('--synthetic', action='store_true', 
                       help='Use synthetic data instead of historical')
    parser.add_argument('--years', nargs='+', type=int, default=[2023, 2024],
                       help='Years to load historical data from')
    parser.add_argument('--max-races', type=int, default=5,
                       help='Maximum races to load per year')
    
    args = parser.parse_args()
    
    pipeline = ModelTrainingPipeline()
    results = pipeline.train_all_models(
        use_historical=not args.synthetic,
        years=args.years,
        max_races=args.max_races
    )
    
    print("\n=== Training Results ===")
    for model, result in results['models'].items():
        status = result['status']
        if status == 'success':
            print(f"✅ {model}: {result.get('metrics', {})}")
        else:
            print(f"❌ {model}: {result.get('error', 'Unknown error')}")


if __name__ == '__main__':
    train_models_cli()
