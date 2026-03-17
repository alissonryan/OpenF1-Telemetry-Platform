"""
Fast-F1 integration service.
"""

import os
from typing import Any, Dict, List, Optional

import fastf1
import pandas as pd

from app.core.config import settings


class FastF1Service:
    """Service for Fast-F1 data extraction and analysis."""

    def __init__(self):
        # Configure Fast-F1 cache
        cache_dir = settings.fastf1_cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        fastf1.Cache.enable_cache(cache_dir)

    def get_session(
        self,
        year: int,
        grand_prix: str,
        session_type: str = "R",
    ) -> fastf1.core.Session:
        """
        Load a session from Fast-F1.

        Args:
            year: Championship year
            grand_prix: Grand Prix name (e.g., "Monaco", "British Grand Prix")
            session_type: Session identifier (FP1, FP2, FP3, Q, S, R)

        Returns:
            Session object with loaded data
        """
        session = fastf1.get_session(year, grand_prix, session_type)
        session.load()
        return session

    def get_telemetry(
        self,
        session: fastf1.core.Session,
        driver: str,
    ) -> pd.DataFrame:
        """
        Get telemetry data for a driver in a session.

        Args:
            session: Loaded Fast-F1 session
            driver: Driver identifier (e.g., "VER", "HAM")

        Returns:
            DataFrame with telemetry data
        """
        lap = session.laps.pick_driver(driver).pick_fastest()
        if lap is None:
            raise ValueError(f"No data found for driver {driver}")

        telemetry = lap.get_car_data().add_distance()
        return telemetry

    def get_lap_times(
        self,
        session: fastf1.core.Session,
        driver: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get lap times from a session.

        Args:
            session: Loaded Fast-F1 session
            driver: Optional driver filter

        Returns:
            DataFrame with lap times
        """
        laps = session.laps
        if driver:
            laps = laps.pick_driver(driver)
        return laps

    def get_weather_data(
        self,
        session: fastf1.core.Session,
    ) -> pd.DataFrame:
        """
        Get weather data from a session.

        Args:
            session: Loaded Fast-F1 session

        Returns:
            DataFrame with weather data
        """
        return session.weather_data

    def get_track_status(
        self,
        session: fastf1.core.Session,
    ) -> pd.DataFrame:
        """
        Get track status changes during a session.

        Args:
            session: Loaded Fast-F1 session

        Returns:
            DataFrame with track status data
        """
        return session.track_status

    def analyze_tyre_degradation(
        self,
        session: fastf1.core.Session,
        driver: str,
    ) -> Dict[str, Any]:
        """
        Analyze tyre degradation for a driver.

        Args:
            session: Loaded Fast-F1 session
            driver: Driver identifier

        Returns:
            Dictionary with degradation analysis
        """
        laps = session.laps.pick_driver(driver)

        # Group by tyre compound and stint
        analysis = {}
        for compound in laps["Compound"].unique():
            compound_laps = laps[laps["Compound"] == compound]
            analysis[compound] = {
                "total_laps": len(compound_laps),
                "avg_lap_time": compound_laps["LapTime"].mean().total_seconds()
                if not compound_laps["LapTime"].isna().all()
                else None,
                "lap_times": [
                    lt.total_seconds() if pd.notna(lt) else None
                    for lt in compound_laps["LapTime"]
                ],
            }

        return analysis


# Singleton instance
fastf1_service = FastF1Service()
