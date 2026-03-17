"""
Feature engineering for ML models.
"""

from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from fastf1.core import Session


class FeatureEngineer:
    """Feature engineering for F1 ML models."""

    def extract_race_features(
        self,
        session: Session,
        driver: str,
        lap_number: int,
    ) -> Dict[str, float]:
        """
        Extract features for a specific driver at a specific lap.

        Args:
            session: Fast-F1 session object
            driver: Driver identifier
            lap_number: Target lap number

        Returns:
            Dictionary of extracted features
        """
        driver_laps = session.laps.pick_driver(driver)
        current_lap = driver_laps[driver_laps["LapNumber"] == lap_number]

        if current_lap.empty:
            raise ValueError(f"No data for {driver} at lap {lap_number}")

        current_lap = current_lap.iloc[0]

        features = {
            # Basic info
            "lap_number": lap_number,
            "position": current_lap.get("Position", 0),
            # Tyre info
            "tyre_age": self._get_tyre_age(driver_laps, lap_number),
            "compound_type": self._encode_compound(current_lap.get("Compound", "UNKNOWN")),
            # Pace features
            "lap_time": current_lap["LapTime"].total_seconds()
            if pd.notna(current_lap["LapTime"])
            else 0,
            "sector_1": current_lap["Sector1Time"].total_seconds()
            if pd.notna(current_lap["Sector1Time"])
            else 0,
            "sector_2": current_lap["Sector2Time"].total_seconds()
            if pd.notna(current_lap["Sector2Time"])
            else 0,
            "sector_3": current_lap["Sector3Time"].total_seconds()
            if pd.notna(current_lap["Sector3Time"])
            else 0,
        }

        return features

    def _get_tyre_age(self, laps: pd.DataFrame, current_lap: int) -> int:
        """Calculate tyre age at current lap."""
        relevant_laps = laps[laps["LapNumber"] <= current_lap]

        # Find stint start
        compounds = relevant_laps["Compound"].tolist()
        tyre_age = 1

        for i in range(len(compounds) - 2, -1, -1):
            if compounds[i] == compounds[-1]:
                tyre_age += 1
            else:
                break

        return tyre_age

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

    def calculate_pace_delta(
        self,
        laps: pd.DataFrame,
        reference_lap_time: float,
    ) -> float:
        """Calculate pace delta from reference."""
        avg_lap_time = laps["LapTime"].mean().total_seconds()
        return avg_lap_time - reference_lap_time

    def calculate_degradation_rate(
        self,
        laps: pd.DataFrame,
        min_samples: int = 5,
    ) -> float:
        """Calculate tyre degradation rate."""
        valid_laps = laps[laps["LapTime"].notna()]

        if len(valid_laps) < min_samples:
            return 0.0

        lap_numbers = valid_laps["LapNumber"].values
        lap_times = valid_laps["LapTime"].dt.total_seconds().values

        # Linear regression
        slope, _ = np.polyfit(lap_numbers, lap_times, 1)
        return slope
