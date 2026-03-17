"""
F1DB Service - SQLite database access for comprehensive F1 historical data.

F1DB contains all-time Formula 1 racing data and statistics from 1950 to present.
https://github.com/f1db/f1db

This service provides:
- Driver information and statistics
- Constructor/Team information and statistics
- Circuit information
- Race results and schedules
- Championship standings
- Full-text search capabilities
"""

import logging
import sqlite3
from contextlib import contextmanager
from datetime import date as date_type
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.models.f1db import (
    CircuitDirection,
    CircuitResponse,
    CircuitType,
    ConstructorResponse,
    ConstructorStatisticsResponse,
    ConstructorStandingResponse,
    DriverResponse,
    DriverStatisticsResponse,
    DriverStandingResponse,
    GrandPrixResponse,
    PaginationParams,
    QualifyingFormat,
    RaceResponse,
    RaceResultResponse,
    SearchResultItem,
)

logger = logging.getLogger(__name__)


class F1DBError(Exception):
    """Base exception for F1DB errors."""

    pass


class F1DBConnectionError(F1DBError):
    """Exception raised when database connection fails."""

    pass


class F1DBNotFoundError(F1DBError):
    """Exception raised when resource is not found."""

    pass


class F1DBService:
    """Service for accessing F1DB SQLite database."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize F1DB service.

        Args:
            db_path: Path to F1DB SQLite database. Defaults to data/f1db/f1db.db
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            # Default path relative to project root
            self.db_path = Path(settings.fastf1_cache_dir).parent.parent / "f1db" / "f1db.db"

        if not self.db_path.exists():
            raise F1DBConnectionError(f"F1DB database not found at {self.db_path}")

        logger.info(f"F1DB initialized with database: {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert sqlite3.Row to dictionary."""
        return dict(row)

    # ==================== Drivers ====================

    def get_driver(self, driver_id: str) -> Optional[DriverResponse]:
        """
        Get a single driver by ID.

        Args:
            driver_id: Driver ID (e.g., 'max-verstappen')

        Returns:
            DriverResponse or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT d.*, c.name as nationality_name
                FROM driver d
                LEFT JOIN country c ON d.nationality_country_id = c.id
                WHERE d.id = ?
                """,
                (driver_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self._parse_driver(row)

    def get_drivers(
        self,
        season: Optional[int] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[DriverResponse], int]:
        """
        Get list of drivers with optional filtering.

        Args:
            season: Filter by season year (drivers who participated)
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (list of drivers, total count)
        """
        with self._get_connection() as conn:
            if season:
                # Get drivers who participated in a specific season
                query = """
                    SELECT DISTINCT d.*
                    FROM driver d
                    INNER JOIN season_driver sd ON d.id = sd.driver_id
                    WHERE sd.year = ?
                    ORDER BY d.last_name, d.first_name
                """
                count_query = """
                    SELECT COUNT(DISTINCT d.id)
                    FROM driver d
                    INNER JOIN season_driver sd ON d.id = sd.driver_id
                    WHERE sd.year = ?
                """
                params = (season,)
            else:
                query = """
                    SELECT * FROM driver
                    ORDER BY last_name, first_name
                """
                count_query = "SELECT COUNT(*) FROM driver"
                params = ()

            # Get total count
            total = conn.execute(count_query, params).fetchone()[0]

            # Get paginated results
            offset = (page - 1) * page_size
            query += f" LIMIT {page_size} OFFSET {offset}"

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            drivers = [self._parse_driver(row) for row in rows]
            return drivers, total

    def get_driver_statistics(self, driver_id: str) -> Optional[DriverStatisticsResponse]:
        """
        Get career statistics for a driver.

        Args:
            driver_id: Driver ID

        Returns:
            DriverStatisticsResponse or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM driver WHERE id = ?
                """,
                (driver_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return DriverStatisticsResponse(
                driver_id=driver_id,
                best_championship_position=row["best_championship_position"],
                best_starting_grid_position=row["best_starting_grid_position"],
                best_race_result=row["best_race_result"],
                best_sprint_race_result=row["best_sprint_race_result"],
                total_championship_wins=row["total_championship_wins"] or 0,
                total_race_entries=row["total_race_entries"] or 0,
                total_race_starts=row["total_race_starts"] or 0,
                total_race_wins=row["total_race_wins"] or 0,
                total_race_laps=row["total_race_laps"] or 0,
                total_podiums=row["total_podiums"] or 0,
                total_points=float(row["total_points"] or 0),
                total_championship_points=float(row["total_championship_points"] or 0),
                total_pole_positions=row["total_pole_positions"] or 0,
                total_fastest_laps=row["total_fastest_laps"] or 0,
                total_sprint_race_starts=row["total_sprint_race_starts"] or 0,
                total_sprint_race_wins=row["total_sprint_race_wins"] or 0,
                total_driver_of_the_day=row["total_driver_of_the_day"] or 0,
                total_grand_slams=row["total_grand_slams"] or 0,
            )

    def _parse_driver(self, row: Dict[str, Any]) -> DriverResponse:
        """Parse database row into DriverResponse."""
        dob = row["date_of_birth"]
        if isinstance(dob, str):
            dob = date_type.fromisoformat(dob)

        dod = row.get("date_of_death")
        if dod and isinstance(dod, str):
            dod = date_type.fromisoformat(dod)

        return DriverResponse(
            id=row["id"],
            name=row["name"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            full_name=row["full_name"],
            abbreviation=row["abbreviation"],
            permanent_number=row.get("permanent_number"),
            gender=row.get("gender", "MALE"),
            date_of_birth=dob,
            date_of_death=dod,
            place_of_birth=row["place_of_birth"],
            country_of_birth_id=row["country_of_birth_country_id"],
            nationality_country_id=row["nationality_country_id"],
        )

    # ==================== Constructors ====================

    def get_constructor(self, constructor_id: str) -> Optional[ConstructorResponse]:
        """
        Get a single constructor by ID.

        Args:
            constructor_id: Constructor ID (e.g., 'red-bull')

        Returns:
            ConstructorResponse or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM constructor WHERE id = ?",
                (constructor_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self._parse_constructor(row)

    def get_constructors(
        self,
        season: Optional[int] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[ConstructorResponse], int]:
        """
        Get list of constructors with optional filtering.

        Args:
            season: Filter by season year
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (list of constructors, total count)
        """
        with self._get_connection() as conn:
            if season:
                query = """
                    SELECT DISTINCT c.*
                    FROM constructor c
                    INNER JOIN season_constructor sc ON c.id = sc.constructor_id
                    WHERE sc.year = ?
                    ORDER BY c.name
                """
                count_query = """
                    SELECT COUNT(DISTINCT c.id)
                    FROM constructor c
                    INNER JOIN season_constructor sc ON c.id = sc.constructor_id
                    WHERE sc.year = ?
                """
                params = (season,)
            else:
                query = "SELECT * FROM constructor ORDER BY name"
                count_query = "SELECT COUNT(*) FROM constructor"
                params = ()

            total = conn.execute(count_query, params).fetchone()[0]

            offset = (page - 1) * page_size
            query += f" LIMIT {page_size} OFFSET {offset}"

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            constructors = [self._parse_constructor(row) for row in rows]
            return constructors, total

    def get_constructor_statistics(self, constructor_id: str) -> Optional[ConstructorStatisticsResponse]:
        """
        Get career statistics for a constructor.

        Args:
            constructor_id: Constructor ID

        Returns:
            ConstructorStatisticsResponse or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM constructor WHERE id = ?",
                (constructor_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return ConstructorStatisticsResponse(
                constructor_id=constructor_id,
                best_championship_position=row["best_championship_position"],
                best_starting_grid_position=row["best_starting_grid_position"],
                best_race_result=row["best_race_result"],
                best_sprint_race_result=row["best_sprint_race_result"],
                total_championship_wins=row["total_championship_wins"] or 0,
                total_race_entries=row["total_race_entries"] or 0,
                total_race_starts=row["total_race_starts"] or 0,
                total_race_wins=row["total_race_wins"] or 0,
                total_1_and_2_finishes=row["total_1_and_2_finishes"] or 0,
                total_race_laps=row["total_race_laps"] or 0,
                total_podiums=row["total_podiums"] or 0,
                total_podium_races=row["total_podium_races"] or 0,
                total_points=float(row["total_points"] or 0),
                total_championship_points=float(row["total_championship_points"] or 0),
                total_pole_positions=row["total_pole_positions"] or 0,
                total_fastest_laps=row["total_fastest_laps"] or 0,
                total_sprint_race_starts=row["total_sprint_race_starts"] or 0,
                total_sprint_race_wins=row["total_sprint_race_wins"] or 0,
            )

    def _parse_constructor(self, row: Dict[str, Any]) -> ConstructorResponse:
        """Parse database row into ConstructorResponse."""
        return ConstructorResponse(
            id=row["id"],
            name=row["name"],
            full_name=row["full_name"],
            country_id=row["country_id"],
        )

    # ==================== Circuits ====================

    def get_circuit(self, circuit_id: str) -> Optional[CircuitResponse]:
        """
        Get a single circuit by ID.

        Args:
            circuit_id: Circuit ID (e.g., 'monaco')

        Returns:
            CircuitResponse or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM circuit WHERE id = ?",
                (circuit_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self._parse_circuit(row)

    def get_circuits(
        self,
        country_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[CircuitResponse], int]:
        """
        Get list of circuits with optional filtering.

        Args:
            country_id: Filter by country
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (list of circuits, total count)
        """
        with self._get_connection() as conn:
            if country_id:
                query = "SELECT * FROM circuit WHERE country_id = ? ORDER BY name"
                count_query = "SELECT COUNT(*) FROM circuit WHERE country_id = ?"
                params = (country_id,)
            else:
                query = "SELECT * FROM circuit ORDER BY name"
                count_query = "SELECT COUNT(*) FROM circuit"
                params = ()

            total = conn.execute(count_query, params).fetchone()[0]

            offset = (page - 1) * page_size
            query += f" LIMIT {page_size} OFFSET {offset}"

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            circuits = [self._parse_circuit(row) for row in rows]
            return circuits, total

    def _parse_circuit(self, row: Dict[str, Any]) -> CircuitResponse:
        """Parse database row into CircuitResponse."""
        return CircuitResponse(
            id=row["id"],
            name=row["name"],
            full_name=row["full_name"],
            previous_names=row.get("previous_names"),
            type=CircuitType(row["type"]),
            direction=CircuitDirection(row["direction"]),
            place_name=row["place_name"],
            country_id=row["country_id"],
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            length=float(row["length"]),
            turns=row["turns"],
            total_races_held=row["total_races_held"],
        )

    # ==================== Seasons ====================

    def get_seasons(self) -> List[int]:
        """
        Get list of all F1 seasons.

        Returns:
            List of season years
        """
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT year FROM season ORDER BY year DESC")
            return [row["year"] for row in cursor.fetchall()]

    # ==================== Races ====================

    def get_races(
        self,
        season: Optional[int] = None,
        circuit_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[RaceResponse], int]:
        """
        Get list of races with optional filtering.

        Args:
            season: Filter by season year
            circuit_id: Filter by circuit
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (list of races, total count)
        """
        with self._get_connection() as conn:
            conditions = []
            params = []

            if season:
                conditions.append("year = ?")
                params.append(season)

            if circuit_id:
                conditions.append("circuit_id = ?")
                params.append(circuit_id)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            query = f"SELECT * FROM race {where_clause} ORDER BY year DESC, round ASC"
            count_query = f"SELECT COUNT(*) FROM race {where_clause}"

            total = conn.execute(count_query, params).fetchone()[0]

            offset = (page - 1) * page_size
            query += f" LIMIT {page_size} OFFSET {offset}"

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            races = [self._parse_race(row) for row in rows]
            return races, total

    def get_race(self, race_id: int) -> Optional[RaceResponse]:
        """
        Get a single race by ID.

        Args:
            race_id: Race ID

        Returns:
            RaceResponse or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM race WHERE id = ?",
                (race_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self._parse_race(row)

    def get_race_by_season_round(self, year: int, round: int) -> Optional[RaceResponse]:
        """
        Get a race by season and round.

        Args:
            year: Season year
            round: Round number

        Returns:
            RaceResponse or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM race WHERE year = ? AND round = ?",
                (year, round),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self._parse_race(row)

    def _parse_race(self, row: Dict[str, Any]) -> RaceResponse:
        """Parse database row into RaceResponse."""
        race_date = row["date"]
        if isinstance(race_date, str):
            race_date = date_type.fromisoformat(race_date)

        return RaceResponse(
            id=row["id"],
            year=row["year"],
            round=row["round"],
            date=race_date,
            time=row.get("time"),
            grand_prix_id=row["grand_prix_id"],
            official_name=row["official_name"],
            qualifying_format=QualifyingFormat(row["qualifying_format"]),
            circuit_id=row["circuit_id"],
            circuit_type=CircuitType(row["circuit_type"]),
            direction=CircuitDirection(row["direction"]),
            course_length=float(row["course_length"]),
            turns=row["turns"],
            laps=row["laps"],
            distance=float(row["distance"]),
            drivers_championship_decider=bool(row.get("drivers_championship_decider", 0)),
            constructors_championship_decider=bool(row.get("constructors_championship_decider", 0)),
        )

    # ==================== Race Results ====================

    def get_race_results(self, race_id: int) -> List[RaceResultResponse]:
        """
        Get results for a specific race.

        Args:
            race_id: Race ID

        Returns:
            List of RaceResultResponse
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM race_result
                WHERE race_id = ?
                ORDER BY position_display_order
                """,
                (race_id,),
            )
            rows = cursor.fetchall()

            return [self._parse_race_result(row) for row in rows]

    def get_race_results_by_season_round(self, year: int, round: int) -> List[RaceResultResponse]:
        """
        Get results for a race by season and round.

        Args:
            year: Season year
            round: Round number

        Returns:
            List of RaceResultResponse
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT rr.*
                FROM race_result rr
                INNER JOIN race r ON rr.race_id = r.id
                WHERE r.year = ? AND r.round = ?
                ORDER BY rr.position_display_order
                """,
                (year, round),
            )
            rows = cursor.fetchall()

            return [self._parse_race_result(row) for row in rows]

    def _parse_race_result(self, row: Dict[str, Any]) -> RaceResultResponse:
        """Parse database row into RaceResultResponse."""
        return RaceResultResponse(
            race_id=row["race_id"],
            position_display_order=row["position_display_order"],
            position_number=row.get("position_number"),
            position_text=row["position_text"],
            driver_number=row.get("driver_number"),
            driver_id=row["driver_id"],
            constructor_id=row["constructor_id"],
            engine_manufacturer_id=row.get("engine_manufacturer_id"),
            tyre_manufacturer_id=row.get("tyre_manufacturer_id"),
            shared_car=row.get("shared_car"),
            laps=row.get("laps"),
            time=row.get("time"),
            time_millis=row.get("time_millis"),
            time_penalty=row.get("time_penalty"),
            time_penalty_millis=row.get("time_penalty_millis"),
            gap=row.get("gap"),
            gap_millis=row.get("gap_millis"),
            gap_laps=row.get("gap_laps"),
            interval=row.get("interval"),
            interval_millis=row.get("interval_millis"),
            reason_retired=row.get("reason_retired"),
            points=float(row["points"]) if row.get("points") else None,
            pole_position=row.get("pole_position"),
            qualification_position_number=row.get("qualification_position_number"),
            grid_position_number=row.get("grid_position_number"),
            positions_gained=row.get("positions_gained"),
            pit_stops=row.get("pit_stops"),
            fastest_lap=row.get("fastest_lap"),
            driver_of_the_day=row.get("driver_of_the_day"),
            grand_slam=row.get("grand_slam"),
        )

    # ==================== Standings ====================

    def get_driver_standings(self, year: int) -> List[DriverStandingResponse]:
        """
        Get driver championship standings for a season.

        Args:
            year: Season year

        Returns:
            List of DriverStandingResponse
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM season_driver_standing
                WHERE year = ?
                ORDER BY position_display_order
                """,
                (year,),
            )
            rows = cursor.fetchall()

            return [
                DriverStandingResponse(
                    year=row["year"],
                    position_display_order=row["position_display_order"],
                    position_number=row.get("position_number"),
                    position_text=row["position_text"],
                    driver_id=row["driver_id"],
                    points=float(row["points"]),
                    championship_won=bool(row["championship_won"]),
                )
                for row in rows
            ]

    def get_constructor_standings(self, year: int) -> List[ConstructorStandingResponse]:
        """
        Get constructor championship standings for a season.

        Args:
            year: Season year

        Returns:
            List of ConstructorStandingResponse
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM season_constructor_standing
                WHERE year = ?
                ORDER BY position_display_order
                """,
                (year,),
            )
            rows = cursor.fetchall()

            return [
                ConstructorStandingResponse(
                    year=row["year"],
                    position_display_order=row["position_display_order"],
                    position_number=row.get("position_number"),
                    position_text=row["position_text"],
                    constructor_id=row["constructor_id"],
                    points=float(row["points"]),
                    championship_won=bool(row["championship_won"]),
                )
                for row in rows
            ]

    # ==================== Search ====================

    def search(self, query: str, limit: int = 20) -> Dict[str, List[SearchResultItem]]:
        """
        Full-text search across drivers, constructors, and circuits.

        Args:
            query: Search query
            limit: Maximum results per category

        Returns:
            Dictionary with search results by category
        """
        search_term = f"%{query.lower()}%"
        results = {
            "drivers": [],
            "constructors": [],
            "circuits": [],
        }

        with self._get_connection() as conn:
            # Search drivers
            cursor = conn.execute(
                """
                SELECT id, full_name, name, abbreviation
                FROM driver
                WHERE LOWER(full_name) LIKE ? OR LOWER(name) LIKE ? OR abbreviation LIKE ?
                ORDER BY total_race_wins DESC, last_name
                LIMIT ?
                """,
                (search_term, search_term, search_term.upper(), limit),
            )
            for row in cursor.fetchall():
                results["drivers"].append(
                    SearchResultItem(
                        type="driver",
                        id=row["id"],
                        name=row["full_name"],
                        highlight=row["name"],
                    )
                )

            # Search constructors
            cursor = conn.execute(
                """
                SELECT id, full_name, name
                FROM constructor
                WHERE LOWER(full_name) LIKE ? OR LOWER(name) LIKE ?
                ORDER BY total_race_wins DESC, name
                LIMIT ?
                """,
                (search_term, search_term, limit),
            )
            for row in cursor.fetchall():
                results["constructors"].append(
                    SearchResultItem(
                        type="constructor",
                        id=row["id"],
                        name=row["full_name"],
                        highlight=row["name"],
                    )
                )

            # Search circuits
            cursor = conn.execute(
                """
                SELECT id, full_name, name
                FROM circuit
                WHERE LOWER(full_name) LIKE ? OR LOWER(name) LIKE ?
                ORDER BY total_races_held DESC, name
                LIMIT ?
                """,
                (search_term, search_term, limit),
            )
            for row in cursor.fetchall():
                results["circuits"].append(
                    SearchResultItem(
                        type="circuit",
                        id=row["id"],
                        name=row["full_name"],
                        highlight=row["name"],
                    )
                )

        return results

    # ==================== Grand Prix ====================

    def get_grand_prix(self, grand_prix_id: str) -> Optional[GrandPrixResponse]:
        """
        Get Grand Prix information.

        Args:
            grand_prix_id: Grand Prix ID

        Returns:
            GrandPrixResponse or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM grand_prix WHERE id = ?",
                (grand_prix_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return GrandPrixResponse(
                id=row["id"],
                name=row["name"],
                full_name=row["full_name"],
                short_name=row["short_name"],
                abbreviation=row["abbreviation"],
                country_id=row.get("country_id"),
                total_races_held=row["total_races_held"],
            )


# Singleton instance
_f1db_service: Optional[F1DBService] = None


def get_f1db_service() -> F1DBService:
    """Get or create F1DB service singleton."""
    global _f1db_service
    if _f1db_service is None:
        _f1db_service = F1DBService()
    return _f1db_service
