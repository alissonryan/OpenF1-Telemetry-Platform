"""
Weather service using Open-Meteo API.
Free weather API with no API key required.
"""
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio


class WeatherService:
    """Service for fetching weather data from Open-Meteo API."""

    BASE_URL = "https://api.open-meteo.com/v1"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> Dict[str, Any]:
        """
        Get current weather for a location.

        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location

        Returns:
            Dictionary with current weather data
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "dew_point_2m",
                "apparent_temperature",
                "precipitation",
                "rain",
                "showers",
                "snowfall",
                "weather_code",
                "cloud_cover",
                "pressure_msl",
                "surface_pressure",
                "wind_speed_10m",
                "wind_direction_10m",
                "wind_gusts_10m",
            ],
            "timezone": "auto",
        }

        response = await self.client.get(
            f"{self.BASE_URL}/forecast",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get weather forecast for a location.

        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            days: Number of days to forecast (1-16)

        Returns:
            Dictionary with forecast data
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "apparent_temperature_max",
                "apparent_temperature_min",
                "sunrise",
                "sunset",
                "uv_index_max",
                "precipitation_sum",
                "rain_sum",
                "showers_sum",
                "snowfall_sum",
                "precipitation_hours",
                "precipitation_probability_max",
                "wind_speed_10m_max",
                "wind_gusts_10m_max",
                "wind_direction_10m_dominant",
            ],
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "dew_point_2m",
                "apparent_temperature",
                "precipitation_probability",
                "precipitation",
                "rain",
                "showers",
                "snowfall",
                "snow_depth",
                "weather_code",
                "pressure_msl",
                "surface_pressure",
                "cloud_cover",
                "cloud_cover_low",
                "cloud_cover_mid",
                "cloud_cover_high",
                "visibility",
                "wind_speed_10m",
                "wind_direction_10m",
                "wind_gusts_10m",
            ],
            "timezone": "auto",
            "forecast_days": days,
        }

        response = await self.client.get(
            f"{self.BASE_URL}/forecast",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def get_historical_weather(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """
        Get historical weather data for a location.

        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Dictionary with historical weather data
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "dew_point_2m",
                "apparent_temperature",
                "precipitation",
                "rain",
                "snowfall",
                "weather_code",
                "pressure_msl",
                "cloud_cover",
                "wind_speed_10m",
                "wind_direction_10m",
                "wind_gusts_10m",
            ],
            "timezone": "auto",
        }

        response = await self.client.get(
            f"{self.BASE_URL}/forecast",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def parse_weather_code(self, code: int) -> Dict[str, str]:
        """
        Parse WMO weather code to human-readable description.

        Args:
            code: WMO weather code

        Returns:
            Dictionary with description and icon
        """
        weather_codes = {
            0: {"description": "Clear sky", "icon": "☀️"},
            1: {"description": "Mainly clear", "icon": "🌤️"},
            2: {"description": "Partly cloudy", "icon": "⛅"},
            3: {"description": "Overcast", "icon": "☁️"},
            45: {"description": "Foggy", "icon": "🌫️"},
            48: {"description": "Depositing rime fog", "icon": "🌫️"},
            51: {"description": "Light drizzle", "icon": "🌧️"},
            53: {"description": "Moderate drizzle", "icon": "🌧️"},
            55: {"description": "Dense drizzle", "icon": "🌧️"},
            56: {"description": "Light freezing drizzle", "icon": "🌨️"},
            57: {"description": "Moderate freezing drizzle", "icon": "🌨️"},
            58: {"description": "Dense freezing drizzle", "icon": "🌨️"},
            61: {"description": "Slight rain", "icon": "🌧️"},
            63: {"description": "Moderate rain", "icon": "🌧️"},
            65: {"description": "Heavy rain", "icon": "🌧️"},
            66: {"description": "Light freezing rain", "icon": "🌨️"},
            67: {"description": "Moderate freezing rain", "icon": "🌨️"},
            68: {"description": "Heavy freezing rain", "icon": "🌨️"},
            71: {"description": "Slight snow fall", "icon": "🌨️"},
            73: {"description": "Moderate snow fall", "icon": "🌨️"},
            75: {"description": "Heavy snow fall", "icon": "🌨️"},
            77: {"description": "Snow grains", "icon": "🌨️"},
            80: {"description": "Slight rain showers", "icon": "🌦️"},
            81: {"description": "Moderate rain showers", "icon": "🌦️"},
            82: {"description": "Violent rain showers", "icon": "⛈️"},
            85: {"description": "Slight snow showers", "icon": "🌨️"},
            86: {"description": "Moderate snow showers", "icon": "🌨️"},
            95: {"description": "Thunderstorm", "icon": "⛈️"},
            96: {"description": "Thunderstorm with slight hail", "icon": "⛈️"},
            99: {"description": "Thunderstorm with heavy hail", "icon": "⛈️"},
        }
        return weather_codes.get(code, {"description": "Unknown", "icon": "❓"})

    async def get_circuit_weather(
        self,
        circuit_name: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Get weather for a specific circuit.

        Args:
            circuit_name: Name of the circuit
            latitude: Optional latitude (will use circuit database if not provided)
            longitude: Optional longitude (will use circuit database if not provided)

        Returns:
            Dictionary with circuit weather data
        """
        # Circuit coordinates database
        circuits = {
            "Sakhir": {"lat": 26.032, "lon": 50.511},
            "Jeddah": {"lat": 21.632, "lon": 39.104},
            "Melbourne": {"lat": -37.849, "lon": 144.968},
            "Imola": {"lat": 44.341, "lon": 11.713},
            "Miami": {"lat": 25.957, "lon": -80.239},
            "Barcelona": {"lat": 41.569, "lon": 2.259},
            "Monaco": {"lat": 43.734, "lon": 7.421},
            "Baku": {"lat": 40.369, "lon": 49.842},
            "Silverstone": {"lat": 52.073, "lon": -1.017},
            "Spielberg": {"lat": 47.222, "lon": 14.765},
            "Le Castellet": {"lat": 43.456, "lon": 5.789},
            "Budapest": {"lat": 47.583, "lon": 19.250},
            "Spa": {"lat": 50.437, "lon": 5.971},
            "Zandvoort": {"lat": 52.389, "lon": 4.545},
            "Monza": {"lat": 45.621, "lon": 9.290},
            "Singapore": {"lat": 1.291, "lon": 103.864},
            "Suzuka": {"lat": 34.843, "lon": 136.539},
            "Austin": {"lat": 30.135, "lon": -97.633},
            "Mexico City": {"lat": 19.404, "lon": -99.091},
            "Sao Paulo": {"lat": -23.702, "lon": -46.698},
            "Las Vegas": {"lat": 36.115, "lon": -115.173},
            "Abu Dhabi": {"lat": 24.467, "lon": 54.603},
            "Lusail": {"lat": 25.493, "lon": 51.454},
        }

        # Get coordinates
        if latitude is None or longitude is None:
            coords = circuits.get(circuit_name)
            if coords:
                latitude = coords["lat"]
                longitude = coords["lon"]
            else:
                raise ValueError(f"Circuit '{circuit_name}' not found in database")

        # Get current weather
        current = await self.get_current_weather(latitude, longitude)

        # Get forecast
        forecast = await self.get_forecast(latitude, longitude, days=7)

        return {
            "circuit": circuit_name,
            "coordinates": {"latitude": latitude, "longitude": longitude},
            "current": current.get("current", {}),
            "forecast": forecast,
        }


# Singleton instance
_weather_service: Optional[WeatherService] = None


def get_weather_service() -> WeatherService:
    """Get or create the weather service singleton."""
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService()
    return _weather_service
