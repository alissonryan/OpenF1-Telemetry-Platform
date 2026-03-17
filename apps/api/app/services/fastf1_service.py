"""
Fast-F1 integration service for historical F1 data analysis.

Fast-F1 Documentation: https://docs.fastf1.dev/
Provides access to detailed telemetry, lap times, and weather data for historical sessions.
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from fastf1 import Cache
from fastf1.core import Session, Laps, Telemetry
from fastf1.ergast import Ergast
from fastf1 import get_session as fastf1_get_session
from fastf1 import get_event as fastf1_get_event
from fastf1 import get_events_remaining as fastf1_get_events_remaining

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class SessionType(str, Enum):
    """Fast-F1 session type identifiers."""

    FP1 = "FP1"
    FP2 = "FP2"
    FP3 = "FP3"
    QUALIFYING = "Q"
    SPRINT = "S"
    SPRINT_QUALIFYING = "SS"
    RACE = "R"


class TyreCompound(str, Enum):
    """F1 tyre compound types."""

    SOFT = "SOFT"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    INTERMEDIATE = "INTERMEDIATE"
    WET = "WET"
    UNKNOWN = "UNKNOWN"


@dataclass
class SessionInfo:
    """Information about a loaded session."""

    year: int
    grand_prix: str
    session_type: str
    session_name: str
    date: Optional[datetime]
    total_laps: int
    drivers: List[str]


class FastF1Service:
    """
    Service for Fast-F1 data extraction and analysis.

    Provides methods to:
    - Load historical sessions
    - Extract detailed telemetry data
    - Analyze lap times and sectors
    - Get weather and track status data
    - Perform tyre degradation analysis
    """

    def __init__(self):
        """Initialize Fast-F1 service with cache configuration."""
        self._cache_enabled = False
        self._session_cache: Dict[Tuple[int, str, str], Session] = {}
        self._setup_cache()

    def _setup_cache(self) -> None:
        """Configure Fast-F1 cache directory."""
        cache_dir = Path(settings.fastf1_cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)

        try:
            Cache.enable_cache(str(cache_dir))
            self._cache_enabled = True
            logger.info(f"Fast-F1 cache enabled at: {cache_dir}")
        except Exception as e:
            logger.warning(f"Failed to enable Fast-F1 cache: {e}")
            self._cache_enabled = False

    # ==================== Session Loading ====================

    def get_session(
        self,
        year: int,
        grand_prix: Union[str, int],
        session_type: Union[str, SessionType] = SessionType.RACE,
    ) -> Session:
        """
        Load a session from Fast-F1.

        Args:
            year: Championship year (e.g., 2024)
            grand_prix: Grand Prix name (e.g., "Monaco", "British Grand Prix")
                       or round number (e.g., 1, 2, 3)
            session_type: Session identifier (FP1, FP2, FP3, Q, S, SS, R)

        Returns:
            Loaded Session object with all data

        Raises:
            ValueError: If session not found or invalid parameters
        """
        if isinstance(session_type, SessionType):
            session_type = session_type.value

        cache_key = (year, str(grand_prix), session_type)
        cached_session = self._session_cache.get(cache_key)
        if cached_session is not None:
            logger.info(f"Using cached FastF1 session: {year} {grand_prix} {session_type}")
            return cached_session

        logger.info(f"Loading session: {year} {grand_prix} {session_type}")

        try:
            session = fastf1_get_session(year, grand_prix, session_type)
            session.load()
            self._session_cache[cache_key] = session
            logger.info(
                f"Session loaded successfully: {session.event['EventName']} - "
                f"{len(session.laps)} laps recorded"
            )
            return session
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            raise ValueError(f"Failed to load session {year} {grand_prix} {session_type}: {e}")

    def get_event(
        self,
        year: int,
        grand_prix: Union[str, int],
    ) -> Dict[str, Any]:
        """
        Get event information without loading full session data.

        Args:
            year: Championship year
            grand_prix: Grand Prix name or round number

        Returns:
            Dictionary with event information
        """
        try:
            event = fastf1_get_event(year, grand_prix)
            return event.to_dict()
        except Exception as e:
            logger.error(f"Failed to get event: {e}")
            raise ValueError(f"Failed to get event {year} {grand_prix}: {e}")

    def get_events_remaining(
        self,
        year: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get remaining events in the current season.

        Args:
            year: Championship year (defaults to current year)

        Returns:
            List of remaining event dictionaries
        """
        try:
            events = fastf1_get_events_remaining(year)
            return [e.to_dict() for e in events]
        except Exception as e:
            logger.error(f"Failed to get remaining events: {e}")
            return []

    # ==================== Telemetry Extraction ====================

    def get_telemetry(
        self,
        session: Session,
        driver: str,
        lap_number: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Get telemetry data for a driver in a session.

        Args:
            session: Loaded Fast-F1 session
            driver: Driver identifier (e.g., "VER", "HAM")
            lap_number: Optional specific lap number (defaults to fastest lap)

        Returns:
            DataFrame with telemetry columns:
            - Speed, Throttle, Brake, nGear, RPM, DRS
            - Distance, Time, SessionTime
        """
        logger.info(f"Getting telemetry for {driver}, lap {lap_number or 'fastest'}")

        try:
            if lap_number is not None:
                lap = session.laps.pick_driver(driver).pick_lap(lap_number)
            else:
                lap = session.laps.pick_driver(driver).pick_fastest()

            if lap is None or lap.empty:
                raise ValueError(f"No lap data found for driver {driver}")

            # Get car telemetry with distance data
            telemetry = lap.get_car_data().add_distance()

            # Add driver and lap info
            telemetry = telemetry.copy()
            telemetry["Driver"] = driver
            telemetry["LapNumber"] = lap["LapNumber"]

            logger.info(f"Retrieved {len(telemetry)} telemetry samples")
            return telemetry

        except Exception as e:
            logger.error(f"Failed to get telemetry: {e}")
            raise

    def get_full_session_telemetry(
        self,
        session: Session,
        driver: str,
    ) -> pd.DataFrame:
        """
        Get telemetry data for all laps of a driver in a session.

        Args:
            session: Loaded Fast-F1 session
            driver: Driver identifier

        Returns:
            DataFrame with telemetry for all laps
        """
        logger.info(f"Getting full session telemetry for {driver}")

        try:
            driver_laps = session.laps.pick_driver(driver)
            all_telemetry = []

            for _, lap in driver_laps.iterrows():
                try:
                    tel = lap.get_car_data().add_distance()
                    tel["Driver"] = driver
                    tel["LapNumber"] = lap["LapNumber"]
                    all_telemetry.append(tel)
                except Exception as e:
                    logger.warning(f"Failed to get telemetry for lap {lap['LapNumber']}: {e}")
                    continue

            if not all_telemetry:
                raise ValueError(f"No telemetry data found for driver {driver}")

            result = pd.concat(all_telemetry, ignore_index=True)
            logger.info(f"Retrieved {len(result)} total telemetry samples")
            return result

        except Exception as e:
            logger.error(f"Failed to get full session telemetry: {e}")
            raise

    def get_position_data(
        self,
        session: Session,
        driver: str,
        lap_number: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Get position data (x, y coordinates) for a driver.

        Args:
            session: Loaded Fast-F1 session
            driver: Driver identifier
            lap_number: Optional specific lap (defaults to fastest)

        Returns:
            DataFrame with X, Y, Z coordinates
        """
        logger.info(f"Getting position data for {driver}")

        try:
            if lap_number is not None:
                lap = session.laps.pick_driver(driver).pick_lap(lap_number)
            else:
                lap = session.laps.pick_driver(driver).pick_fastest()

            if lap is None or lap.empty:
                raise ValueError(f"No lap data found for driver {driver}")

            pos_data = lap.get_pos_data()
            logger.info(f"Retrieved {len(pos_data)} position samples")
            return pos_data

        except Exception as e:
            logger.error(f"Failed to get position data: {e}")
            raise

    # ==================== Lap Data ====================

    def get_lap_times(
        self,
        session: Session,
        driver: Optional[str] = None,
        include_deleted: bool = False,
    ) -> pd.DataFrame:
        """
        Get lap times from a session.

        Args:
            session: Loaded Fast-F1 session
            driver: Optional driver filter
            include_deleted: Include deleted lap times

        Returns:
            DataFrame with lap data including:
            - LapTime, LapNumber, Sector times, Tyre info
        """
        logger.info(f"Getting lap times, driver={driver}")

        try:
            laps = session.laps

            if driver:
                laps = laps.pick_driver(driver)

            if not include_deleted:
                # Filter out deleted laps if column exists
                if "Deleted" in laps.columns:
                    laps = laps[~laps["Deleted"].fillna(False)]

            logger.info(f"Retrieved {len(laps)} laps")
            return laps

        except Exception as e:
            logger.error(f"Failed to get lap times: {e}")
            raise

    def get_fastest_lap(
        self,
        session: Session,
        driver: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get the fastest lap information.

        Args:
            session: Loaded Fast-F1 session
            driver: Optional driver filter

        Returns:
            Dictionary with fastest lap details
        """
        logger.info(f"Getting fastest lap, driver={driver}")

        try:
            if driver:
                fastest = session.laps.pick_driver(driver).pick_fastest()
            else:
                fastest = session.laps.pick_fastest()

            if fastest is None or fastest.empty:
                return {}

            result = {
                "driver": fastest["Driver"],
                "lap_number": int(fastest["LapNumber"]),
                "lap_time": str(fastest["LapTime"]),
                "lap_time_seconds": fastest["LapTime"].total_seconds()
                if pd.notna(fastest["LapTime"])
                else None,
                "sector_1": str(fastest["Sector1Time"])
                if pd.notna(fastest.get("Sector1Time"))
                else None,
                "sector_2": str(fastest["Sector2Time"])
                if pd.notna(fastest.get("Sector2Time"))
                else None,
                "sector_3": str(fastest["Sector3Time"])
                if pd.notna(fastest.get("Sector3Time"))
                else None,
                "tyre_compound": fastest.get("Compound"),
                "tyre_life": int(fastest["TyreLife"]) if pd.notna(fastest.get("TyreLife")) else None,
                "is_personal_best": fastest.get("IsPersonalBest", False),
            }

            logger.info(f"Fastest lap: {result['driver']} - {result['lap_time']}")
            return result

        except Exception as e:
            logger.error(f"Failed to get fastest lap: {e}")
            return {}

    def get_sector_analysis(
        self,
        session: Session,
        driver: str,
    ) -> Dict[str, Any]:
        """
        Get sector time analysis for a driver.

        Args:
            session: Loaded Fast-F1 session
            driver: Driver identifier

        Returns:
            Dictionary with sector analysis
        """
        logger.info(f"Getting sector analysis for {driver}")

        try:
            laps = session.laps.pick_driver(driver)

            analysis = {
                "driver": driver,
                "sectors": {
                    "sector_1": {
                        "best": None,
                        "average": None,
                        "worst": None,
                    },
                    "sector_2": {
                        "best": None,
                        "average": None,
                        "worst": None,
                    },
                    "sector_3": {
                        "best": None,
                        "average": None,
                        "worst": None,
                    },
                },
            }

            for sector in ["Sector1Time", "Sector2Time", "Sector3Time"]:
                if sector in laps.columns:
                    times = laps[sector].dropna()
                    if len(times) > 0:
                        sector_key = sector.lower().replace("time", "")
                        analysis["sectors"][sector_key]["best"] = times.min().total_seconds()
                        analysis["sectors"][sector_key]["average"] = times.mean().total_seconds()
                        analysis["sectors"][sector_key]["worst"] = times.max().total_seconds()

            return analysis

        except Exception as e:
            logger.error(f"Failed to get sector analysis: {e}")
            return {"driver": driver, "sectors": {}}

    # ==================== Weather & Track Status ====================

    def get_weather_data(
        self,
        session: Session,
    ) -> pd.DataFrame:
        """
        Get weather data from a session.

        Args:
            session: Loaded Fast-F1 session

        Returns:
            DataFrame with weather data:
            - AirTemp, Humidity, Pressure, Rainfall, TrackTemp, WindDirection, WindSpeed
        """
        logger.info("Getting weather data")

        try:
            weather = session.weather_data
            logger.info(f"Retrieved {len(weather)} weather samples")
            return weather
        except Exception as e:
            logger.error(f"Failed to get weather data: {e}")
            raise

    def get_weather_summary(
        self,
        session: Session,
    ) -> Dict[str, Any]:
        """
        Get a summary of weather conditions during the session.

        Args:
            session: Loaded Fast-F1 session

        Returns:
            Dictionary with weather summary statistics
        """
        logger.info("Getting weather summary")

        try:
            weather = session.weather_data

            if weather is None or weather.empty:
                return {}

            summary = {
                "air_temp": {
                    "min": float(weather["AirTemp"].min()),
                    "max": float(weather["AirTemp"].max()),
                    "avg": float(weather["AirTemp"].mean()),
                },
                "track_temp": {
                    "min": float(weather["TrackTemp"].min()),
                    "max": float(weather["TrackTemp"].max()),
                    "avg": float(weather["TrackTemp"].mean()),
                },
                "humidity": {
                    "min": float(weather["Humidity"].min()),
                    "max": float(weather["Humidity"].max()),
                    "avg": float(weather["Humidity"].mean()),
                },
                "rainfall": bool(weather["Rainfall"].any()),
                "wind_speed": {
                    "min": float(weather["WindSpeed"].min()),
                    "max": float(weather["WindSpeed"].max()),
                    "avg": float(weather["WindSpeed"].mean()),
                },
            }

            return summary

        except Exception as e:
            logger.error(f"Failed to get weather summary: {e}")
            return {}

    def get_track_status(
        self,
        session: Session,
    ) -> pd.DataFrame:
        """
        Get track status changes during a session.

        Args:
            session: Loaded Fast-F1 session

        Returns:
            DataFrame with track status data
        """
        logger.info("Getting track status")

        try:
            status = session.track_status
            logger.info(f"Retrieved {len(status)} track status entries")
            return status
        except Exception as e:
            logger.error(f"Failed to get track status: {e}")
            raise

    # ==================== Tyre Analysis ====================

    def analyze_tyre_degradation(
        self,
        session: Session,
        driver: str,
    ) -> Dict[str, Any]:
        """
        Analyze tyre degradation for a driver.

        Args:
            session: Loaded Fast-F1 session
            driver: Driver identifier

        Returns:
            Dictionary with degradation analysis per compound
        """
        logger.info(f"Analyzing tyre degradation for {driver}")

        try:
            laps = session.laps.pick_driver(driver)
            analysis = {"driver": driver, "compounds": {}}

            for compound in laps["Compound"].unique():
                if pd.isna(compound):
                    continue

                compound_laps = laps[laps["Compound"] == compound]
                lap_times = compound_laps["LapTime"].dropna()

                if len(lap_times) == 0:
                    continue

                # Calculate degradation (lap time increase per lap)
                tyre_life = compound_laps["TyreLife"].values
                times_seconds = [t.total_seconds() for t in lap_times]

                if len(tyre_life) > 1 and len(times_seconds) > 1:
                    # Linear regression for degradation rate
                    coeffs = np.polyfit(tyre_life[: len(times_seconds)], times_seconds, 1)
                    degradation_rate = coeffs[0]  # seconds per lap
                else:
                    degradation_rate = 0

                analysis["compounds"][compound] = {
                    "total_laps": int(len(compound_laps)),
                    "stints": int(compound_laps["Stint"].nunique()),
                    "avg_lap_time": float(np.mean(times_seconds)),
                    "best_lap_time": float(np.min(times_seconds)),
                    "degradation_rate": float(degradation_rate),  # seconds per lap
                    "lap_times": times_seconds,
                }

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze tyre degradation: {e}")
            return {"driver": driver, "compounds": {}, "error": str(e)}

    def get_tyre_strategy(
        self,
        session: Session,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get tyre strategy for all drivers in the session.

        Args:
            session: Loaded Fast-F1 session

        Returns:
            Dictionary mapping driver to their tyre strategy
        """
        logger.info("Getting tyre strategy for all drivers")

        try:
            strategy = {}

            for driver in session.laps["Driver"].unique():
                driver_laps = session.laps.pick_driver(driver)

                stints = []
                for stint_num in sorted(driver_laps["Stint"].unique()):
                    stint_laps = driver_laps[driver_laps["Stint"] == stint_num]

                    stints.append({
                        "stint_number": int(stint_num),
                        "compound": stint_laps["Compound"].iloc[0],
                        "lap_start": int(stint_laps["LapNumber"].min()),
                        "lap_end": int(stint_laps["LapNumber"].max()),
                        "total_laps": int(len(stint_laps)),
                    })

                strategy[driver] = stints

            return strategy

        except Exception as e:
            logger.error(f"Failed to get tyre strategy: {e}")
            return {}

    # ==================== Comparison & Analysis ====================

    def compare_drivers(
        self,
        session: Session,
        drivers: List[str],
    ) -> Dict[str, Any]:
        """
        Compare telemetry data between drivers.

        Args:
            session: Loaded Fast-F1 session
            drivers: List of driver identifiers to compare

        Returns:
            Dictionary with comparison data
        """
        logger.info(f"Comparing drivers: {drivers}")

        comparison = {
            "drivers": drivers,
            "fastest_laps": {},
            "telemetry_delta": {},
        }

        try:
            # Get fastest lap for each driver
            for driver in drivers:
                fastest = self.get_fastest_lap(session, driver)
                comparison["fastest_laps"][driver] = fastest

            # Calculate delta between drivers
            if len(drivers) >= 2:
                base_driver = drivers[0]
                base_time = comparison["fastest_laps"][base_driver].get("lap_time_seconds", 0)

                for driver in drivers[1:]:
                    driver_time = comparison["fastest_laps"][driver].get("lap_time_seconds", 0)
                    if base_time and driver_time:
                        comparison["telemetry_delta"][f"{base_driver}_vs_{driver}"] = {
                            "delta": driver_time - base_time,
                            "faster": base_driver if base_time < driver_time else driver,
                        }

            return comparison

        except Exception as e:
            logger.error(f"Failed to compare drivers: {e}")
            return comparison

    # ==================== Data Export ====================

    def telemetry_to_dict(
        self,
        telemetry: pd.DataFrame,
    ) -> List[Dict[str, Any]]:
        """
        Convert telemetry DataFrame to list of dictionaries.

        Args:
            telemetry: Telemetry DataFrame

        Returns:
            List of dictionaries with telemetry data
        """
        try:
            # Handle datetime/timedelta columns
            df = telemetry.copy()

            for col in df.columns:
                if pd.api.types.is_timedelta64_dtype(df[col]):
                    df[col] = df[col].dt.total_seconds()
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].astype(str)

            return df.to_dict(orient="records")

        except Exception as e:
            logger.error(f"Failed to convert telemetry to dict: {e}")
            return []

    def session_info(self, session: Session) -> SessionInfo:
        """
        Get session information.

        Args:
            session: Loaded Fast-F1 session

        Returns:
            SessionInfo dataclass with session details
        """
        session_meta = getattr(session, "session_info", {}) or {}
        session_type = session_meta.get("Type") or getattr(session, "name", None) or "Unknown"
        session_name = session_meta.get("Name") or getattr(session, "name", None) or session_type

        return SessionInfo(
            year=int(session.event["EventDate"].year),
            grand_prix=session.event["EventName"],
            session_type=session_type,
            session_name=session_name,
            date=session.date,
            total_laps=len(session.laps),
            drivers=list(session.laps["Driver"].unique()),
        )


# Singleton instance
fastf1_service = FastF1Service()
