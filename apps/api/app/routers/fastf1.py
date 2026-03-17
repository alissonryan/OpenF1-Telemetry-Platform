"""
Fast-F1 router for historical F1 data analysis.

Provides endpoints for:
- Loading historical sessions
- Extracting detailed telemetry data
- Lap time analysis
- Weather data
- Tyre degradation analysis
- Driver comparisons
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.models.session import (
    FastF1ComparisonRequest,
    FastF1ComparisonResponse,
    FastF1LapsResponse,
    FastF1SessionInfo,
    FastF1TelemetryRequest,
    FastF1TelemetryResponse,
    FastF1WeatherResponse,
)
from app.services.fastf1_service import FastF1Service, fastf1_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/session",
    response_model=FastF1SessionInfo,
    summary="Load Fast-F1 Session",
    description="Load a historical F1 session and get session information.",
)
async def load_session(
    year: int = Query(
        ...,
        ge=2018,
        le=2100,
        description="Championship year (e.g., 2024)",
    ),
    grand_prix: str = Query(
        ...,
        min_length=1,
        description="Grand Prix name (e.g., 'Monaco', 'British Grand Prix') or round number",
    ),
    session_type: str = Query(
        "R",
        description="Session type: FP1, FP2, FP3, Q, S, SS, R",
    ),
) -> FastF1SessionInfo:
    """
    Load a historical F1 session.

    Returns session information including drivers and total laps.

    **Note:** First load may take longer due to data download and caching.

    **Examples:**
    - `/fastf1/session?year=2024&grand_prix=Monaco&session_type=R`
    - `/fastf1/session?year=2023&grand_prix=British Grand Prix&session_type=Q`
    """
    try:
        session = fastf1_service.get_session(year, grand_prix, session_type.upper())
        info = fastf1_service.session_info(session)

        return FastF1SessionInfo(
            year=info.year,
            grand_prix=info.grand_prix,
            session_type=info.session_type,
            session_name=info.session_name,
            date=str(info.date) if info.date else None,
            total_laps=info.total_laps,
            drivers=info.drivers,
        )

    except ValueError as e:
        logger.error(f"Invalid session parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to load session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load session: {str(e)}",
        )


@router.get(
    "/telemetry",
    response_model=FastF1TelemetryResponse,
    summary="Get Fast-F1 Telemetry",
    description="Extract detailed telemetry data for a driver in a historical session.",
)
async def get_telemetry(
    year: int = Query(..., ge=2018, le=2100),
    grand_prix: str = Query(..., min_length=1),
    session_type: str = Query("R"),
    driver: str = Query(..., min_length=3, max_length=3, description="3-letter driver code"),
    lap_number: Optional[int] = Query(None, ge=1, description="Specific lap (default: fastest)"),
) -> FastF1TelemetryResponse:
    """
    Get detailed telemetry data for a driver.

    Returns speed, throttle, brake, gear, RPM, and distance data.

    **Examples:**
    - `/fastf1/telemetry?year=2024&grand_prix=Monaco&driver=VER`
    - `/fastf1/telemetry?year=2024&grand_prix=Monaco&driver=VER&lap_number=45`
    """
    try:
        # Load session
        session = fastf1_service.get_session(year, grand_prix, session_type.upper())
        session_info = fastf1_service.session_info(session)

        # Get telemetry
        telemetry_df = fastf1_service.get_telemetry(session, driver, lap_number)

        # Convert to response format
        data = []
        for _, row in telemetry_df.iterrows():
            data.append({
                "time": row.get("Time", 0).total_seconds() if hasattr(row.get("Time"), "total_seconds") else 0,
                "speed": int(row.get("Speed", 0)),
                "throttle": float(row.get("Throttle", 0)),
                "brake": bool(row.get("Brake", False)),
                "n_gear": int(row.get("nGear", 0)),
                "rpm": int(row.get("RPM", 0)),
                "drs": row.get("DRS"),
                "distance": row.get("Distance"),
                "driver": driver,
                "lap_number": lap_number or int(row.get("LapNumber", 0)),
            })

        return FastF1TelemetryResponse(
            session_info=FastF1SessionInfo(
                year=session_info.year,
                grand_prix=session_info.grand_prix,
                session_type=session_info.session_type,
                session_name=session_info.session_name,
                date=str(session_info.date) if session_info.date else None,
                total_laps=session_info.total_laps,
                drivers=session_info.drivers,
            ),
            driver=driver,
            lap_number=lap_number or 0,
            data=data,
            total_samples=len(data),
        )

    except ValueError as e:
        logger.error(f"Invalid telemetry parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get telemetry: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get telemetry: {str(e)}",
        )


@router.get(
    "/laps",
    response_model=FastF1LapsResponse,
    summary="Get Fast-F1 Lap Data",
    description="Get lap timing data for a session or specific driver.",
)
async def get_laps(
    year: int = Query(..., ge=2018, le=2100),
    grand_prix: str = Query(..., min_length=1),
    session_type: str = Query("R"),
    driver: Optional[str] = Query(None, min_length=3, max_length=3),
) -> FastF1LapsResponse:
    """
    Get lap timing data for a session.

    Returns lap times, sector times, and tyre information.

    **Examples:**
    - `/fastf1/laps?year=2024&grand_prix=Monaco`
    - `/fastf1/laps?year=2024&grand_prix=Monaco&driver=VER`
    """
    try:
        # Load session
        session = fastf1_service.get_session(year, grand_prix, session_type.upper())
        session_info = fastf1_service.session_info(session)

        # Get lap times
        laps_df = fastf1_service.get_lap_times(session, driver)

        # Convert to response format
        laps = []
        for _, lap in laps_df.iterrows():
            lap_data = {
                "driver": lap.get("Driver", ""),
                "lap_number": int(lap.get("LapNumber", 0)),
                "lap_time": lap.get("LapTime").total_seconds() if hasattr(lap.get("LapTime"), "total_seconds") else None,
                "sector_1": lap.get("Sector1Time").total_seconds() if hasattr(lap.get("Sector1Time"), "total_seconds") else None,
                "sector_2": lap.get("Sector2Time").total_seconds() if hasattr(lap.get("Sector2Time"), "total_seconds") else None,
                "sector_3": lap.get("Sector3Time").total_seconds() if hasattr(lap.get("Sector3Time"), "total_seconds") else None,
                "tyre_compound": lap.get("Compound"),
                "tyre_life": int(lap.get("TyreLife", 0)) if lap.get("TyreLife") is not None else None,
                "is_personal_best": lap.get("IsPersonalBest", False),
                "is_fresh_tyre": lap.get("FreshTyre", False),
            }
            laps.append(lap_data)

        return FastF1LapsResponse(
            session_info=FastF1SessionInfo(
                year=session_info.year,
                grand_prix=session_info.grand_prix,
                session_type=session_info.session_type,
                session_name=session_info.session_name,
                date=str(session_info.date) if session_info.date else None,
                total_laps=session_info.total_laps,
                drivers=session_info.drivers,
            ),
            laps=laps,
            total_laps=len(laps),
        )

    except ValueError as e:
        logger.error(f"Invalid lap parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get laps: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get lap data: {str(e)}",
        )


@router.get(
    "/weather",
    response_model=FastF1WeatherResponse,
    summary="Get Fast-F1 Weather Data",
    description="Get weather data for a historical session.",
)
async def get_weather(
    year: int = Query(..., ge=2018, le=2100),
    grand_prix: str = Query(..., min_length=1),
    session_type: str = Query("R"),
) -> FastF1WeatherResponse:
    """
    Get weather data for a session.

    Returns temperature, humidity, pressure, rainfall, and wind data.

    **Example:**
    - `/fastf1/weather?year=2024&grand_prix=Monaco&session_type=R`
    """
    try:
        # Load session
        session = fastf1_service.get_session(year, grand_prix, session_type.upper())
        session_info = fastf1_service.session_info(session)

        # Get weather data
        weather_df = fastf1_service.get_weather_data(session)
        weather_summary = fastf1_service.get_weather_summary(session)

        # Convert to response format
        data = []
        for _, row in weather_df.iterrows():
            data.append({
                "time": row.get("Time").total_seconds() if hasattr(row.get("Time"), "total_seconds") else None,
                "air_temp": row.get("AirTemp"),
                "track_temp": row.get("TrackTemp"),
                "humidity": row.get("Humidity"),
                "pressure": row.get("Pressure"),
                "rainfall": row.get("Rainfall"),
                "wind_direction": row.get("WindDirection"),
                "wind_speed": row.get("WindSpeed"),
            })

        return FastF1WeatherResponse(
            session_info=FastF1SessionInfo(
                year=session_info.year,
                grand_prix=session_info.grand_prix,
                session_type=session_info.session_type,
                session_name=session_info.session_name,
                date=str(session_info.date) if session_info.date else None,
                total_laps=session_info.total_laps,
                drivers=session_info.drivers,
            ),
            data=data,
            summary=weather_summary,
        )

    except ValueError as e:
        logger.error(f"Invalid weather parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get weather: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get weather data: {str(e)}",
        )


@router.get(
    "/tyre-analysis",
    summary="Get Tyre Degradation Analysis",
    description="Analyze tyre degradation for a driver in a session.",
)
async def get_tyre_analysis(
    year: int = Query(..., ge=2018, le=2100),
    grand_prix: str = Query(..., min_length=1),
    session_type: str = Query("R"),
    driver: str = Query(..., min_length=3, max_length=3),
) -> dict:
    """
    Analyze tyre degradation for a driver.

    Returns degradation rate and lap time trends per compound.

    **Example:**
    - `/fastf1/tyre-analysis?year=2024&grand_prix=Monaco&driver=VER`
    """
    try:
        # Load session
        session = fastf1_service.get_session(year, grand_prix, session_type.upper())

        # Get tyre analysis
        analysis = fastf1_service.analyze_tyre_degradation(session, driver)

        return analysis

    except ValueError as e:
        logger.error(f"Invalid tyre analysis parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get tyre analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tyre analysis: {str(e)}",
        )


@router.get(
    "/tyre-strategy",
    summary="Get Tyre Strategy",
    description="Get tyre strategy for all drivers in a session.",
)
async def get_tyre_strategy(
    year: int = Query(..., ge=2018, le=2100),
    grand_prix: str = Query(..., min_length=1),
    session_type: str = Query("R"),
) -> dict:
    """
    Get tyre strategy for all drivers.

    Returns stint information including compound and lap ranges.

    **Example:**
    - `/fastf1/tyre-strategy?year=2024&grand_prix=Monaco&session_type=R`
    """
    try:
        # Load session
        session = fastf1_service.get_session(year, grand_prix, session_type.upper())

        # Get tyre strategy
        strategy = fastf1_service.get_tyre_strategy(session)

        return {
            "year": year,
            "grand_prix": grand_prix,
            "session_type": session_type,
            "strategy": strategy,
        }

    except ValueError as e:
        logger.error(f"Invalid tyre strategy parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get tyre strategy: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tyre strategy: {str(e)}",
        )


@router.get(
    "/compare",
    summary="Compare Drivers",
    description="Compare telemetry data between drivers in a session.",
)
async def compare_drivers(
    year: int = Query(..., ge=2018, le=2100),
    grand_prix: str = Query(..., min_length=1),
    session_type: str = Query("R"),
    drivers: str = Query(
        ...,
        description="Comma-separated driver codes (e.g., 'VER,LEC,NOR')",
    ),
) -> dict:
    """
    Compare telemetry data between drivers.

    Returns fastest laps and time deltas.

    **Example:**
    - `/fastf1/compare?year=2024&grand_prix=Monaco&drivers=VER,LEC,NOR`
    """
    try:
        # Parse driver list
        driver_list = [d.strip().upper() for d in drivers.split(",")]

        if len(driver_list) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 drivers required for comparison",
            )
        if len(driver_list) > 4:
            raise HTTPException(
                status_code=400,
                detail="Maximum 4 drivers can be compared at once",
            )

        # Load session
        session = fastf1_service.get_session(year, grand_prix, session_type.upper())

        # Compare drivers
        comparison = fastf1_service.compare_drivers(session, driver_list)

        return comparison

    except ValueError as e:
        logger.error(f"Invalid comparison parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to compare drivers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare drivers: {str(e)}",
        )


@router.get(
    "/fastest-lap",
    summary="Get Fastest Lap Details",
    description="Get detailed fastest lap information for a session or driver.",
)
async def get_fastest_lap(
    year: int = Query(..., ge=2018, le=2100),
    grand_prix: str = Query(..., min_length=1),
    session_type: str = Query("R"),
    driver: Optional[str] = Query(None, min_length=3, max_length=3),
) -> dict:
    """
    Get fastest lap information.

    Returns lap time, sector times, and tyre data.

    **Examples:**
    - `/fastf1/fastest-lap?year=2024&grand_prix=Monaco` - Session fastest lap
    - `/fastf1/fastest-lap?year=2024&grand_prix=Monaco&driver=VER` - Driver's fastest lap
    """
    try:
        # Load session
        session = fastf1_service.get_session(year, grand_prix, session_type.upper())

        # Get fastest lap
        fastest = fastf1_service.get_fastest_lap(session, driver)

        return fastest

    except ValueError as e:
        logger.error(f"Invalid fastest lap parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get fastest lap: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get fastest lap: {str(e)}",
        )
