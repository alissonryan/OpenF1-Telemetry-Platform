"""
Pydantic models for F1DB data.

F1DB is a comprehensive F1 database with data from 1950 to present.
https://github.com/f1db/f1db

Models represent:
- Drivers, Constructors, Circuits
- Races, Results, Qualifying
- Standings, Statistics
"""

from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CircuitType(str, Enum):
    """Circuit type classification."""

    RACE = "RACE"
    STREET = "STREET"
    ROAD = "ROAD"


class CircuitDirection(str, Enum):
    """Circuit direction."""

    CLOCKWISE = "CLOCKWISE"
    ANTI_CLOCKWISE = "ANTI_CLOCKWISE"


class QualifyingFormat(str, Enum):
    """Qualifying format types."""

    ONE_SESSION = "ONE_SESSION"
    TWO_SESSIONS = "TWO_SESSIONS"
    THREE_SESSIONS = "THREE_SESSIONS"
    SPRINT_QUALIFYING = "SPRINT_QUALIFYING"


# ==================== Country ====================


class CountryResponse(BaseModel):
    """Country information."""

    id: str = Field(..., description="Country ID (e.g., 'united-kingdom')")
    alpha2_code: str = Field(..., description="ISO 3166-1 alpha-2 code")
    alpha3_code: str = Field(..., description="ISO 3166-1 alpha-3 code")
    name: str = Field(..., description="Country name")
    demonym: Optional[str] = Field(None, description="Demonym (e.g., 'British')")
    ioc_code: Optional[str] = Field(None, description="IOC country code")


# ==================== Circuit ====================


class CircuitResponse(BaseModel):
    """Circuit information response model."""

    id: str = Field(..., description="Circuit ID (e.g., 'monaco')")
    name: str = Field(..., description="Circuit short name")
    full_name: str = Field(..., description="Full circuit name")
    previous_names: Optional[str] = Field(None, description="Previous names if any")
    type: CircuitType = Field(..., description="Circuit type (RACE, STREET, ROAD)")
    direction: CircuitDirection = Field(..., description="Track direction")
    place_name: str = Field(..., description="Location name")
    country_id: str = Field(..., description="Country ID")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    length: float = Field(..., description="Circuit length in km")
    turns: int = Field(..., description="Number of turns")
    total_races_held: int = Field(..., description="Total races held at this circuit")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "monaco",
                    "name": "Monaco",
                    "full_name": "Circuit de Monaco",
                    "type": "STREET",
                    "direction": "CLOCKWISE",
                    "place_name": "Monte Carlo",
                    "country_id": "monaco",
                    "latitude": 43.734722,
                    "longitude": 7.420556,
                    "length": 3.337,
                    "turns": 19,
                    "total_races_held": 70,
                }
            ]
        }
    }


class CircuitListResponse(BaseModel):
    """Response model for circuit list."""

    data: List[CircuitResponse]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)


# ==================== Driver ====================


class DriverResponse(BaseModel):
    """Driver information response model."""

    id: str = Field(..., description="Driver ID (e.g., 'max-verstappen')")
    name: str = Field(..., description="Short name")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    full_name: str = Field(..., description="Full name")
    abbreviation: str = Field(..., min_length=3, max_length=3, description="3-letter code")
    permanent_number: Optional[str] = Field(None, description="Permanent car number")
    gender: str = Field(default="MALE", description="Gender")
    date_of_birth: date = Field(..., description="Date of birth")
    date_of_death: Optional[date] = Field(None, description="Date of death if deceased")
    place_of_birth: str = Field(..., description="Place of birth")
    country_of_birth_id: str = Field(..., description="Country of birth ID")
    nationality_country_id: str = Field(..., description="Nationality country ID")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "max-verstappen",
                    "name": "Max Verstappen",
                    "first_name": "Max",
                    "last_name": "Verstappen",
                    "full_name": "Max Verstappen",
                    "abbreviation": "VER",
                    "permanent_number": "1",
                    "gender": "MALE",
                    "date_of_birth": "1997-09-30",
                    "place_of_birth": "Hasselt",
                    "country_of_birth_id": "belgium",
                    "nationality_country_id": "netherlands",
                }
            ]
        }
    }


class DriverStatisticsResponse(BaseModel):
    """Driver career statistics."""

    driver_id: str
    best_championship_position: Optional[int] = Field(None, description="Best championship position")
    best_starting_grid_position: Optional[int] = Field(None, description="Best grid position")
    best_race_result: Optional[int] = Field(None, description="Best race finish position")
    best_sprint_race_result: Optional[int] = Field(None, description="Best sprint race finish")
    total_championship_wins: int = Field(default=0, description="Total championships won")
    total_race_entries: int = Field(default=0, description="Total races entered")
    total_race_starts: int = Field(default=0, description="Total races started")
    total_race_wins: int = Field(default=0, description="Total races won")
    total_race_laps: int = Field(default=0, description="Total laps completed")
    total_podiums: int = Field(default=0, description="Total podium finishes")
    total_points: float = Field(default=0.0, description="Total career points")
    total_championship_points: float = Field(default=0.0, description="Total championship points")
    total_pole_positions: int = Field(default=0, description="Total pole positions")
    total_fastest_laps: int = Field(default=0, description="Total fastest laps")
    total_sprint_race_starts: int = Field(default=0, description="Total sprint races started")
    total_sprint_race_wins: int = Field(default=0, description="Total sprint races won")
    total_driver_of_the_day: int = Field(default=0, description="Total Driver of the Day awards")
    total_grand_slams: int = Field(default=0, description="Total Grand Slams (pole, win, fastest lap, led every lap)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "driver_id": "max-verstappen",
                    "best_championship_position": 1,
                    "total_championship_wins": 4,
                    "total_race_wins": 60,
                    "total_pole_positions": 40,
                    "total_points": 2500.5,
                }
            ]
        }
    }


class DriverWithStatsResponse(DriverResponse):
    """Driver with statistics included."""

    statistics: DriverStatisticsResponse


class DriverListResponse(BaseModel):
    """Response model for driver list."""

    data: List[DriverResponse]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)


# ==================== Constructor ====================


class ConstructorResponse(BaseModel):
    """Constructor/Team information response model."""

    id: str = Field(..., description="Constructor ID (e.g., 'red-bull')")
    name: str = Field(..., description="Short name")
    full_name: str = Field(..., description="Full team name")
    country_id: str = Field(..., description="Country ID")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "red-bull",
                    "name": "Red Bull",
                    "full_name": "Red Bull Racing",
                    "country_id": "austria",
                }
            ]
        }
    }


class ConstructorStatisticsResponse(BaseModel):
    """Constructor career statistics."""

    constructor_id: str
    best_championship_position: Optional[int] = Field(None, description="Best championship position")
    best_starting_grid_position: Optional[int] = Field(None, description="Best grid position")
    best_race_result: Optional[int] = Field(None, description="Best race finish position")
    best_sprint_race_result: Optional[int] = Field(None, description="Best sprint race finish")
    total_championship_wins: int = Field(default=0, description="Total championships won")
    total_race_entries: int = Field(default=0, description="Total races entered")
    total_race_starts: int = Field(default=0, description="Total races started")
    total_race_wins: int = Field(default=0, description="Total races won")
    total_1_and_2_finishes: int = Field(default=0, description="Total 1-2 finishes")
    total_race_laps: int = Field(default=0, description="Total laps completed")
    total_podiums: int = Field(default=0, description="Total podium finishes")
    total_podium_races: int = Field(default=0, description="Total races with podium finish")
    total_points: float = Field(default=0.0, description="Total career points")
    total_championship_points: float = Field(default=0.0, description="Total championship points")
    total_pole_positions: int = Field(default=0, description="Total pole positions")
    total_fastest_laps: int = Field(default=0, description="Total fastest laps")
    total_sprint_race_starts: int = Field(default=0, description="Total sprint races started")
    total_sprint_race_wins: int = Field(default=0, description="Total sprint races won")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "constructor_id": "red-bull",
                    "best_championship_position": 1,
                    "total_championship_wins": 6,
                    "total_race_wins": 100,
                    "total_points": 5000.0,
                }
            ]
        }
    }


class ConstructorWithStatsResponse(ConstructorResponse):
    """Constructor with statistics included."""

    statistics: ConstructorStatisticsResponse


class ConstructorListResponse(BaseModel):
    """Response model for constructor list."""

    data: List[ConstructorResponse]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)


# ==================== Grand Prix ====================


class GrandPrixResponse(BaseModel):
    """Grand Prix information."""

    id: str = Field(..., description="Grand Prix ID")
    name: str = Field(..., description="Short name")
    full_name: str = Field(..., description="Full name")
    short_name: str = Field(..., description="Short display name")
    abbreviation: str = Field(..., min_length=3, max_length=3, description="3-letter code")
    country_id: Optional[str] = Field(None, description="Country ID")
    total_races_held: int = Field(default=0, description="Total races held")


# ==================== Race ====================


class RaceResponse(BaseModel):
    """Race information response model."""

    id: int = Field(..., description="Race ID")
    year: int = Field(..., description="Season year")
    round: int = Field(..., description="Round number in season")
    date: date = Field(..., description="Race date")
    time: Optional[str] = Field(None, description="Race start time")
    grand_prix_id: str = Field(..., description="Grand Prix ID")
    official_name: str = Field(..., description="Official race name")
    qualifying_format: QualifyingFormat = Field(..., description="Qualifying format")
    circuit_id: str = Field(..., description="Circuit ID")
    circuit_type: CircuitType = Field(..., description="Circuit type")
    direction: CircuitDirection = Field(..., description="Track direction")
    course_length: float = Field(..., description="Course length in km")
    turns: int = Field(..., description="Number of turns")
    laps: int = Field(..., description="Number of laps")
    distance: float = Field(..., description="Total race distance in km")
    drivers_championship_decider: bool = Field(default=False, description="Drivers championship decided")
    constructors_championship_decider: bool = Field(default=False, description="Constructors championship decided")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1120,
                    "year": 2024,
                    "round": 1,
                    "date": "2024-03-02",
                    "time": "15:00",
                    "grand_prix_id": "bahrain",
                    "official_name": "Formula 1 Gulf Air Bahrain Grand Prix 2024",
                    "qualifying_format": "THREE_SESSIONS",
                    "circuit_id": "bahrain",
                    "circuit_type": "RACE",
                    "direction": "CLOCKWISE",
                    "course_length": 5.412,
                    "turns": 15,
                    "laps": 57,
                    "distance": 308.238,
                }
            ]
        }
    }


class RaceListResponse(BaseModel):
    """Response model for race list."""

    data: List[RaceResponse]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)


# ==================== Race Result ====================


class RaceResultResponse(BaseModel):
    """Race result for a single driver."""

    race_id: int = Field(..., description="Race ID")
    position_display_order: int = Field(..., description="Position order (for display)")
    position_number: Optional[int] = Field(None, description="Finishing position number")
    position_text: str = Field(..., description="Position text (e.g., '1', 'DNF', 'DSQ')")
    driver_number: Optional[int] = Field(None, description="Car number")
    driver_id: str = Field(..., description="Driver ID")
    constructor_id: str = Field(..., description="Constructor ID")
    engine_manufacturer_id: Optional[str] = Field(None, description="Engine manufacturer ID")
    tyre_manufacturer_id: Optional[str] = Field(None, description="Tyre manufacturer ID")
    shared_car: Optional[bool] = Field(None, description="Shared car (historical)")
    laps: Optional[int] = Field(None, description="Laps completed")
    time: Optional[str] = Field(None, description="Finish time")
    time_millis: Optional[int] = Field(None, description="Finish time in milliseconds")
    time_penalty: Optional[str] = Field(None, description="Time penalty")
    time_penalty_millis: Optional[int] = Field(None, description="Time penalty in milliseconds")
    gap: Optional[str] = Field(None, description="Gap to winner")
    gap_millis: Optional[int] = Field(None, description="Gap to winner in milliseconds")
    gap_laps: Optional[int] = Field(None, description="Laps behind")
    interval: Optional[str] = Field(None, description="Interval to car ahead")
    interval_millis: Optional[int] = Field(None, description="Interval in milliseconds")
    reason_retired: Optional[str] = Field(None, description="Reason for retirement")
    points: Optional[float] = Field(None, description="Points scored")
    pole_position: Optional[bool] = Field(None, description="Started from pole")
    qualification_position_number: Optional[int] = Field(None, description="Qualifying position")
    grid_position_number: Optional[int] = Field(None, description="Grid position")
    positions_gained: Optional[int] = Field(None, description="Positions gained/lost")
    pit_stops: Optional[int] = Field(None, description="Number of pit stops")
    fastest_lap: Optional[bool] = Field(None, description="Set fastest lap")
    driver_of_the_day: Optional[bool] = Field(None, description="Driver of the Day")
    grand_slam: Optional[bool] = Field(None, description="Achieved Grand Slam")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "race_id": 1120,
                    "position_display_order": 1,
                    "position_number": 1,
                    "position_text": "1",
                    "driver_number": 1,
                    "driver_id": "max-verstappen",
                    "constructor_id": "red-bull",
                    "laps": 57,
                    "time": "1:31:44.742",
                    "points": 25.0,
                    "pole_position": True,
                    "fastest_lap": True,
                }
            ]
        }
    }


class RaceResultListResponse(BaseModel):
    """Response model for race results."""

    data: List[RaceResultResponse]
    total: int
    race_id: int


# ==================== Standings ====================


class DriverStandingResponse(BaseModel):
    """Driver championship standing."""

    year: int = Field(..., description="Season year")
    position_display_order: int = Field(..., description="Position order")
    position_number: Optional[int] = Field(None, description="Position number")
    position_text: str = Field(..., description="Position text")
    driver_id: str = Field(..., description="Driver ID")
    points: float = Field(..., description="Championship points")
    championship_won: bool = Field(..., description="Championship won")


class DriverStandingListResponse(BaseModel):
    """Response model for driver standings."""

    data: List[DriverStandingResponse]
    total: int
    year: int


class ConstructorStandingResponse(BaseModel):
    """Constructor championship standing."""

    year: int = Field(..., description="Season year")
    position_display_order: int = Field(..., description="Position order")
    position_number: Optional[int] = Field(None, description="Position number")
    position_text: str = Field(..., description="Position text")
    constructor_id: str = Field(..., description="Constructor ID")
    points: float = Field(..., description="Championship points")
    championship_won: bool = Field(..., description="Championship won")


class ConstructorStandingListResponse(BaseModel):
    """Response model for constructor standings."""

    data: List[ConstructorStandingResponse]
    total: int
    year: int


# ==================== Season ====================


class SeasonResponse(BaseModel):
    """Season information."""

    year: int = Field(..., description="Season year")


class SeasonListResponse(BaseModel):
    """Response model for season list."""

    data: List[int]
    total: int


# ==================== Search ====================


class SearchResultItem(BaseModel):
    """Single search result item."""

    type: str = Field(..., description="Result type (driver, constructor, circuit)")
    id: str = Field(..., description="Entity ID")
    name: str = Field(..., description="Display name")
    highlight: Optional[str] = Field(None, description="Highlighted match")


class SearchResponse(BaseModel):
    """Response model for search."""

    query: str
    drivers: List[SearchResultItem] = Field(default_factory=list)
    constructors: List[SearchResultItem] = Field(default_factory=list)
    circuits: List[SearchResultItem] = Field(default_factory=list)
    total_results: int = Field(default=0, description="Total number of results")


# ==================== Pagination ====================


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=50, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate SQL offset."""
        return (self.page - 1) * self.page_size
