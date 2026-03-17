"""
Weather API endpoints using Open-Meteo.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel

from app.services.weather_service import get_weather_service


router = APIRouter(tags=["weather"])


class WeatherResponse(BaseModel):
    """Weather response model."""
    circuit: str
    coordinates: dict
    current: dict
    forecast: dict


class CurrentWeatherResponse(BaseModel):
    """Current weather response model."""
    latitude: float
    longitude: float
    current: dict


@router.get("/current", response_model=CurrentWeatherResponse)
async def get_current_weather(
    latitude: float = Query(..., description="Latitude of the location"),
    longitude: float = Query(..., description="Longitude of the location"),
):
    """
    Get current weather for a location.

    Free API, no authentication required.
    """
    service = get_weather_service()
    try:
        data = await service.get_current_weather(latitude, longitude)
        return {
            "latitude": latitude,
            "longitude": longitude,
            "current": data.get("current", {}),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast")
async def get_forecast(
    latitude: float = Query(..., description="Latitude of the location"),
    longitude: float = Query(..., description="Longitude of the location"),
    days: int = Query(7, ge=1, le=16, description="Number of forecast days"),
):
    """
    Get weather forecast for a location.

    Returns hourly and daily forecasts for up to 16 days.
    """
    service = get_weather_service()
    try:
        data = await service.get_forecast(latitude, longitude, days=days)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/circuit/{circuit_name}", response_model=WeatherResponse)
async def get_circuit_weather(
    circuit_name: str,
    latitude: Optional[float] = Query(None, description="Optional latitude override"),
    longitude: Optional[float] = Query(None, description="Optional longitude override"),
):
    """
    Get weather for a specific circuit.

    Supported circuits: Sakhir, Jeddah, Melbourne, Imola, Miami, Barcelona,
    Monaco, Baku, Silverstone, Spielberg, Le Castellet, Budapest, Spa,
    Zandvoort, Monza, Singapore, Suzuka, Austin, Mexico City, Sao Paulo,
    Las Vegas, Abu Dhabi, Lusail
    """
    service = get_weather_service()
    try:
        data = await service.get_circuit_weather(
            circuit_name,
            latitude=latitude,
            longitude=longitude,
        )
        return data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/historical")
async def get_historical_weather(
    latitude: float = Query(..., description="Latitude of the location"),
    longitude: float = Query(..., description="Longitude of the location"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
):
    """
    Get historical weather data.

    Available for past 80 years.
    """
    service = get_weather_service()
    try:
        data = await service.get_historical_weather(
            latitude,
            longitude,
            start_date,
            end_date,
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parse-code/{code}")
async def parse_weather_code(code: int):
    """
    Parse WMO weather code to human-readable description.

    Weather codes range from 0 to 99.
    """
    service = get_weather_service()
    return service.parse_weather_code(code)
