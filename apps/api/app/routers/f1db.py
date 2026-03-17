"""
F1DB router for historical F1 data endpoints.

Provides endpoints for:
- Drivers and driver statistics
- Constructors and constructor statistics
- Circuits
- Races and race results
- Championship standings
- Global search
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Path, Query

from app.models.f1db import (
    CircuitListResponse,
    CircuitResponse,
    ConstructorListResponse,
    ConstructorResponse,
    ConstructorStatisticsResponse,
    ConstructorStandingListResponse,
    ConstructorStandingResponse,
    ConstructorWithStatsResponse,
    DriverListResponse,
    DriverResponse,
    DriverStatisticsResponse,
    DriverStandingListResponse,
    DriverStandingResponse,
    DriverWithStatsResponse,
    RaceListResponse,
    RaceResponse,
    RaceResultListResponse,
    RaceResultResponse,
    SearchResponse,
    SearchResultItem,
    SeasonListResponse,
)
from app.services.f1db_service import (
    F1DBError,
    F1DBNotFoundError,
    get_f1db_service,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== Drivers ====================


@router.get(
    "/drivers",
    response_model=DriverListResponse,
    summary="Get F1 Drivers",
    description="Retrieve all F1 drivers from 1950 to present with optional filtering by season.",
)
async def get_drivers(
    season: Optional[int] = Query(
        None,
        ge=1950,
        le=2100,
        description="Filter by season year (drivers who participated)",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
) -> DriverListResponse:
    """
    Get F1 drivers from the complete F1DB database (1950-present).

    **Examples:**
    - `/f1db/drivers` - All drivers
    - `/f1db/drivers?season=2024` - Drivers who raced in 2024
    - `/f1db/drivers?page=2&page_size=20` - Paginated results
    """
    try:
        service = get_f1db_service()
        drivers, total = service.get_drivers(season=season, page=page, page_size=page_size)

        return DriverListResponse(
            data=drivers,
            total=total,
            page=page,
            page_size=page_size,
        )

    except F1DBError as e:
        logger.error(f"Failed to fetch drivers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch drivers: {str(e)}",
        )


@router.get(
    "/drivers/{driver_id}",
    response_model=DriverResponse,
    summary="Get F1 Driver",
    description="Retrieve a specific F1 driver by ID.",
)
async def get_driver(
    driver_id: str = Path(..., description="Driver ID (e.g., 'max-verstappen')"),
) -> DriverResponse:
    """
    Get a specific F1 driver.

    **Driver ID format:** lowercase-firstname-lastname (e.g., 'max-verstappen', 'lewis-hamilton')
    """
    try:
        service = get_f1db_service()
        driver = service.get_driver(driver_id)

        if not driver:
            raise HTTPException(
                status_code=404,
                detail=f"Driver '{driver_id}' not found",
            )

        return driver

    except HTTPException:
        raise
    except F1DBError as e:
        logger.error(f"Failed to fetch driver: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch driver: {str(e)}",
        )


@router.get(
    "/drivers/{driver_id}/statistics",
    response_model=DriverStatisticsResponse,
    summary="Get Driver Statistics",
    description="Retrieve career statistics for a specific driver.",
)
async def get_driver_statistics(
    driver_id: str = Path(..., description="Driver ID"),
) -> DriverStatisticsResponse:
    """
    Get comprehensive career statistics for a driver.

    Includes: wins, poles, podiums, points, fastest laps, championships, etc.
    """
    try:
        service = get_f1db_service()
        stats = service.get_driver_statistics(driver_id)

        if not stats:
            raise HTTPException(
                status_code=404,
                detail=f"Driver '{driver_id}' not found",
            )

        return stats

    except HTTPException:
        raise
    except F1DBError as e:
        logger.error(f"Failed to fetch driver statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch driver statistics: {str(e)}",
        )


@router.get(
    "/drivers/{driver_id}/full",
    response_model=DriverWithStatsResponse,
    summary="Get Driver with Statistics",
    description="Retrieve driver information with career statistics included.",
)
async def get_driver_with_stats(
    driver_id: str = Path(..., description="Driver ID"),
) -> DriverWithStatsResponse:
    """
    Get driver information with statistics in a single request.
    """
    try:
        service = get_f1db_service()
        driver = service.get_driver(driver_id)
        stats = service.get_driver_statistics(driver_id)

        if not driver or not stats:
            raise HTTPException(
                status_code=404,
                detail=f"Driver '{driver_id}' not found",
            )

        return DriverWithStatsResponse(
            **driver.model_dump(),
            statistics=stats,
        )

    except HTTPException:
        raise
    except F1DBError as e:
        logger.error(f"Failed to fetch driver with stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch driver: {str(e)}",
        )


# ==================== Constructors ====================


@router.get(
    "/constructors",
    response_model=ConstructorListResponse,
    summary="Get F1 Constructors",
    description="Retrieve all F1 constructors/teams from 1950 to present.",
)
async def get_constructors(
    season: Optional[int] = Query(
        None,
        ge=1950,
        le=2100,
        description="Filter by season year",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
) -> ConstructorListResponse:
    """
    Get F1 constructors/teams from the complete F1DB database.

    **Examples:**
    - `/f1db/constructors` - All constructors
    - `/f1db/constructors?season=2024` - Constructors in 2024
    """
    try:
        service = get_f1db_service()
        constructors, total = service.get_constructors(season=season, page=page, page_size=page_size)

        return ConstructorListResponse(
            data=constructors,
            total=total,
            page=page,
            page_size=page_size,
        )

    except F1DBError as e:
        logger.error(f"Failed to fetch constructors: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch constructors: {str(e)}",
        )


@router.get(
    "/constructors/{constructor_id}",
    response_model=ConstructorResponse,
    summary="Get F1 Constructor",
    description="Retrieve a specific F1 constructor/team by ID.",
)
async def get_constructor(
    constructor_id: str = Path(..., description="Constructor ID (e.g., 'red-bull')"),
) -> ConstructorResponse:
    """
    Get a specific F1 constructor/team.

    **Constructor ID format:** lowercase-name (e.g., 'red-bull', 'ferrari', 'mercedes')
    """
    try:
        service = get_f1db_service()
        constructor = service.get_constructor(constructor_id)

        if not constructor:
            raise HTTPException(
                status_code=404,
                detail=f"Constructor '{constructor_id}' not found",
            )

        return constructor

    except HTTPException:
        raise
    except F1DBError as e:
        logger.error(f"Failed to fetch constructor: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch constructor: {str(e)}",
        )


@router.get(
    "/constructors/{constructor_id}/statistics",
    response_model=ConstructorStatisticsResponse,
    summary="Get Constructor Statistics",
    description="Retrieve career statistics for a specific constructor.",
)
async def get_constructor_statistics(
    constructor_id: str = Path(..., description="Constructor ID"),
) -> ConstructorStatisticsResponse:
    """
    Get comprehensive career statistics for a constructor.

    Includes: wins, poles, podiums, points, championships, 1-2 finishes, etc.
    """
    try:
        service = get_f1db_service()
        stats = service.get_constructor_statistics(constructor_id)

        if not stats:
            raise HTTPException(
                status_code=404,
                detail=f"Constructor '{constructor_id}' not found",
            )

        return stats

    except HTTPException:
        raise
    except F1DBError as e:
        logger.error(f"Failed to fetch constructor statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch constructor statistics: {str(e)}",
        )


@router.get(
    "/constructors/{constructor_id}/full",
    response_model=ConstructorWithStatsResponse,
    summary="Get Constructor with Statistics",
    description="Retrieve constructor information with career statistics included.",
)
async def get_constructor_with_stats(
    constructor_id: str = Path(..., description="Constructor ID"),
) -> ConstructorWithStatsResponse:
    """
    Get constructor information with statistics in a single request.
    """
    try:
        service = get_f1db_service()
        constructor = service.get_constructor(constructor_id)
        stats = service.get_constructor_statistics(constructor_id)

        if not constructor or not stats:
            raise HTTPException(
                status_code=404,
                detail=f"Constructor '{constructor_id}' not found",
            )

        return ConstructorWithStatsResponse(
            **constructor.model_dump(),
            statistics=stats,
        )

    except HTTPException:
        raise
    except F1DBError as e:
        logger.error(f"Failed to fetch constructor with stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch constructor: {str(e)}",
        )


# ==================== Circuits ====================


@router.get(
    "/circuits",
    response_model=CircuitListResponse,
    summary="Get F1 Circuits",
    description="Retrieve all F1 circuits from 1950 to present.",
)
async def get_circuits(
    country_id: Optional[str] = Query(
        None,
        description="Filter by country ID",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
) -> CircuitListResponse:
    """
    Get F1 circuits from the complete F1DB database.

    **Examples:**
    - `/f1db/circuits` - All circuits
    - `/f1db/circuits?country_id=italy` - Circuits in Italy
    """
    try:
        service = get_f1db_service()
        circuits, total = service.get_circuits(country_id=country_id, page=page, page_size=page_size)

        return CircuitListResponse(
            data=circuits,
            total=total,
            page=page,
            page_size=page_size,
        )

    except F1DBError as e:
        logger.error(f"Failed to fetch circuits: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch circuits: {str(e)}",
        )


@router.get(
    "/circuits/{circuit_id}",
    response_model=CircuitResponse,
    summary="Get F1 Circuit",
    description="Retrieve a specific F1 circuit by ID.",
)
async def get_circuit(
    circuit_id: str = Path(..., description="Circuit ID (e.g., 'monaco')"),
) -> CircuitResponse:
    """
    Get a specific F1 circuit.

    **Circuit ID format:** lowercase-name (e.g., 'monaco', 'silverstone', 'monza')
    """
    try:
        service = get_f1db_service()
        circuit = service.get_circuit(circuit_id)

        if not circuit:
            raise HTTPException(
                status_code=404,
                detail=f"Circuit '{circuit_id}' not found",
            )

        return circuit

    except HTTPException:
        raise
    except F1DBError as e:
        logger.error(f"Failed to fetch circuit: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch circuit: {str(e)}",
        )


# ==================== Seasons ====================


@router.get(
    "/seasons",
    response_model=SeasonListResponse,
    summary="Get F1 Seasons",
    description="Retrieve all F1 seasons from 1950 to present.",
)
async def get_seasons() -> SeasonListResponse:
    """
    Get all F1 seasons (years).

    Returns a list of years from 1950 to current season.
    """
    try:
        service = get_f1db_service()
        seasons = service.get_seasons()

        return SeasonListResponse(
            data=seasons,
            total=len(seasons),
        )

    except F1DBError as e:
        logger.error(f"Failed to fetch seasons: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch seasons: {str(e)}",
        )


# ==================== Races ====================


@router.get(
    "/races",
    response_model=RaceListResponse,
    summary="Get F1 Races",
    description="Retrieve F1 races with optional filtering.",
)
async def get_races(
    season: Optional[int] = Query(
        None,
        ge=1950,
        le=2100,
        description="Filter by season year",
    ),
    circuit_id: Optional[str] = Query(
        None,
        description="Filter by circuit ID",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
) -> RaceListResponse:
    """
    Get F1 races from the complete F1DB database.

    **Examples:**
    - `/f1db/races` - All races
    - `/f1db/races?season=2024` - All races in 2024 season
    - `/f1db/races?circuit_id=monaco` - All races at Monaco
    """
    try:
        service = get_f1db_service()
        races, total = service.get_races(season=season, circuit_id=circuit_id, page=page, page_size=page_size)

        return RaceListResponse(
            data=races,
            total=total,
            page=page,
            page_size=page_size,
        )

    except F1DBError as e:
        logger.error(f"Failed to fetch races: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch races: {str(e)}",
        )


@router.get(
    "/races/{race_id}",
    response_model=RaceResponse,
    summary="Get F1 Race",
    description="Retrieve a specific F1 race by ID.",
)
async def get_race(
    race_id: int = Path(..., ge=1, description="Race ID"),
) -> RaceResponse:
    """
    Get a specific F1 race by its ID.
    """
    try:
        service = get_f1db_service()
        race = service.get_race(race_id)

        if not race:
            raise HTTPException(
                status_code=404,
                detail=f"Race '{race_id}' not found",
            )

        return race

    except HTTPException:
        raise
    except F1DBError as e:
        logger.error(f"Failed to fetch race: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch race: {str(e)}",
        )


@router.get(
    "/races/{race_id}/results",
    response_model=RaceResultListResponse,
    summary="Get Race Results",
    description="Retrieve results for a specific race.",
)
async def get_race_results(
    race_id: int = Path(..., ge=1, description="Race ID"),
) -> RaceResultListResponse:
    """
    Get results for a specific race.

    Includes finishing positions, times, gaps, points, etc.
    """
    try:
        service = get_f1db_service()
        results = service.get_race_results(race_id)

        return RaceResultListResponse(
            data=results,
            total=len(results),
            race_id=race_id,
        )

    except F1DBError as e:
        logger.error(f"Failed to fetch race results: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch race results: {str(e)}",
        )


# ==================== Season Endpoints ====================


@router.get(
    "/seasons/{year}/races",
    response_model=RaceListResponse,
    summary="Get Season Races",
    description="Retrieve all races for a specific season.",
)
async def get_season_races(
    year: int = Path(..., ge=1950, le=2100, description="Season year"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
) -> RaceListResponse:
    """
    Get all races for a specific F1 season.

    **Example:** `/f1db/seasons/2024/races`
    """
    try:
        service = get_f1db_service()
        races, total = service.get_races(season=year, page=page, page_size=page_size)

        return RaceListResponse(
            data=races,
            total=total,
            page=page,
            page_size=page_size,
        )

    except F1DBError as e:
        logger.error(f"Failed to fetch season races: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch season races: {str(e)}",
        )


@router.get(
    "/seasons/{year}/standings/drivers",
    response_model=DriverStandingListResponse,
    summary="Get Driver Standings",
    description="Retrieve driver championship standings for a specific season.",
)
async def get_season_driver_standings(
    year: int = Path(..., ge=1950, le=2100, description="Season year"),
) -> DriverStandingListResponse:
    """
    Get final driver championship standings for a season.

    **Example:** `/f1db/seasons/2024/standings/drivers`
    """
    try:
        service = get_f1db_service()
        standings = service.get_driver_standings(year)

        if not standings:
            raise HTTPException(
                status_code=404,
                detail=f"No driver standings found for season {year}",
            )

        return DriverStandingListResponse(
            data=standings,
            total=len(standings),
            year=year,
        )

    except HTTPException:
        raise
    except F1DBError as e:
        logger.error(f"Failed to fetch driver standings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch driver standings: {str(e)}",
        )


@router.get(
    "/seasons/{year}/standings/constructors",
    response_model=ConstructorStandingListResponse,
    summary="Get Constructor Standings",
    description="Retrieve constructor championship standings for a specific season.",
)
async def get_season_constructor_standings(
    year: int = Path(..., ge=1950, le=2100, description="Season year"),
) -> ConstructorStandingListResponse:
    """
    Get final constructor championship standings for a season.

    **Example:** `/f1db/seasons/2024/standings/constructors`
    """
    try:
        service = get_f1db_service()
        standings = service.get_constructor_standings(year)

        if not standings:
            raise HTTPException(
                status_code=404,
                detail=f"No constructor standings found for season {year}",
            )

        return ConstructorStandingListResponse(
            data=standings,
            total=len(standings),
            year=year,
        )

    except HTTPException:
        raise
    except F1DBError as e:
        logger.error(f"Failed to fetch constructor standings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch constructor standings: {str(e)}",
        )


@router.get(
    "/seasons/{year}/round/{round}/results",
    response_model=RaceResultListResponse,
    summary="Get Race Results by Season and Round",
    description="Retrieve results for a specific race by season year and round number.",
)
async def get_race_results_by_round(
    year: int = Path(..., ge=1950, le=2100, description="Season year"),
    round: int = Path(..., ge=1, description="Round number"),
) -> RaceResultListResponse:
    """
    Get results for a race by season and round number.

    **Example:** `/f1db/seasons/2024/round/1/results` (Bahrain 2024)
    """
    try:
        service = get_f1db_service()
        results = service.get_race_results_by_season_round(year, round)

        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"No results found for season {year}, round {round}",
            )

        return RaceResultListResponse(
            data=results,
            total=len(results),
            race_id=0,  # Not available directly
        )

    except HTTPException:
        raise
    except F1DBError as e:
        logger.error(f"Failed to fetch race results: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch race results: {str(e)}",
        )


# ==================== Search ====================


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Search F1DB",
    description="Full-text search across drivers, constructors, and circuits.",
)
async def search_f1db(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results per category"),
) -> SearchResponse:
    """
    Search across all F1DB data.

    Searches drivers, constructors, and circuits simultaneously.

    **Example:** `/f1db/search?q=verstappen`
    """
    try:
        service = get_f1db_service()
        results = service.search(q, limit=limit)

        total = (
            len(results["drivers"])
            + len(results["constructors"])
            + len(results["circuits"])
        )

        return SearchResponse(
            query=q,
            drivers=results["drivers"],
            constructors=results["constructors"],
            circuits=results["circuits"],
            total_results=total,
        )

    except F1DBError as e:
        logger.error(f"Failed to search: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search: {str(e)}",
        )
