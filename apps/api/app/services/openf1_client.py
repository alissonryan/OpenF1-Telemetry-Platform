"""
OpenF1 API client service.
"""

from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings


class OpenF1Client:
    """Client for interacting with the OpenF1 API."""

    def __init__(self):
        self.base_url = settings.openf1_base_url
        self.timeout = 30.0

    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """Make a GET request to the OpenF1 API."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()

    async def get_meetings(self, year: Optional[int] = None) -> List[Dict]:
        """Get all meetings for a given year."""
        params = {"year": year} if year else {}
        return await self._get("meetings", params)

    async def get_sessions(
        self,
        meeting_key: Optional[int] = None,
        session_type: Optional[str] = None,
    ) -> List[Dict]:
        """Get sessions, optionally filtered."""
        params = {}
        if meeting_key:
            params["meeting_key"] = meeting_key
        if session_type:
            params["session_type"] = session_type
        return await self._get("sessions", params)

    async def get_drivers(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
    ) -> List[Dict]:
        """Get driver information."""
        params = {}
        if session_key:
            params["session_key"] = session_key
        if driver_number:
            params["driver_number"] = driver_number
        return await self._get("drivers", params)

    async def get_car_data(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
        speed_gt: Optional[int] = None,
    ) -> List[Dict]:
        """Get car telemetry data."""
        params = {}
        if session_key:
            params["session_key"] = session_key
        if driver_number:
            params["driver_number"] = driver_number
        data = await self._get("car_data", params)
        if speed_gt is not None:
            data = [d for d in data if d.get("speed", 0) > speed_gt]
        return data

    async def get_positions(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
    ) -> List[Dict]:
        """Get position data."""
        params = {}
        if session_key:
            params["session_key"] = session_key
        if driver_number:
            params["driver_number"] = driver_number
        return await self._get("position", params)

    async def get_laps(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
        lap_number: Optional[int] = None,
    ) -> List[Dict]:
        """Get lap timing data."""
        params = {}
        if session_key:
            params["session_key"] = session_key
        if driver_number:
            params["driver_number"] = driver_number
        if lap_number:
            params["lap_number"] = lap_number
        return await self._get("laps", params)

    async def get_weather(self, session_key: Optional[int] = None) -> List[Dict]:
        """Get weather data."""
        params = {"session_key": session_key} if session_key else {}
        return await self._get("weather", params)


# Singleton instance
openf1_client = OpenF1Client()
