"""
OpenF1 API client service with robust error handling and retry logic.

OpenF1 API Documentation: https://api.openf1.org/v1
Rate Limit: 3 requests/second (free tier)
"""

import asyncio
import copy
import json
import logging
import time
from typing import Any, Dict, List, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class OpenF1APIError(Exception):
    """Base exception for OpenF1 API errors."""

    pass


class OpenF1RateLimitError(OpenF1APIError):
    """Exception raised when rate limit is exceeded."""

    pass


class OpenF1NotFoundError(OpenF1APIError):
    """Exception raised when resource is not found."""

    pass


class OpenF1ConnectionError(OpenF1APIError):
    """Exception raised when connection fails."""

    pass


class RateLimiter:
    """
    Rate limiter to ensure we stay within API limits.
    OpenF1 allows 3 requests/second, we use 2.5 to be safe.
    """

    def __init__(self, calls_per_second: float = 2.5):
        self.min_interval = 1.0 / calls_per_second
        self._last_called: Dict[int, float] = {}
        self._locks: Dict[int, asyncio.Lock] = {}

    async def acquire(self):
        """Wait until we can make the next request."""
        loop = asyncio.get_running_loop()
        loop_id = id(loop)
        lock = self._locks.get(loop_id)

        if lock is None:
            lock = asyncio.Lock()
            self._locks[loop_id] = lock

        async with lock:
            now = loop.time()
            elapsed = now - self._last_called.get(loop_id, 0.0)
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
            self._last_called[loop_id] = loop.time()


# Global rate limiter instance
_rate_limiter = RateLimiter(calls_per_second=2.5)


class OpenF1Client:
    """Client for interacting with the OpenF1 API with retry and rate limiting."""

    def __init__(self):
        self.base_url = settings.openf1_base_url
        self.timeout = 30.0
        self._client: Optional[httpx.AsyncClient] = None
        self._client_loop_id: Optional[int] = None
        self._response_cache: Dict[str, tuple[float, List[Dict[str, Any]]]] = {}
        self._inflight_requests: Dict[tuple[int, str], asyncio.Task[List[Dict[str, Any]]]] = {}

    def _cache_policy_for(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> tuple[int, int]:
        """Return fresh/stale TTLs for a given OpenF1 endpoint."""
        policies: Dict[str, tuple[int, int]] = {
            "meetings": (1800, 86400),
            "sessions": (900, 3600),
            "drivers": (300, 1800),
            "weather": (30, 300),
            "car_data": (2, 10),
            "position": (3, 15),
            "pit": (10, 120),
            "stints": (15, 180),
            "laps": (5, 60),
            "intervals": (4, 30),
            "race_control": (10, 120),
            "team_radio": (10, 120),
        }
        return policies.get(endpoint, (0, 0))

    def _cache_key(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build a stable cache key from endpoint and params."""
        normalized_params = {
            key: value
            for key, value in sorted((params or {}).items())
            if value is not None
        }
        return f"{endpoint}:{json.dumps(normalized_params, sort_keys=True, default=str, separators=(',', ':'))}"

    def _clone_payload(self, payload: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prevent callers from mutating cached payloads in place."""
        return copy.deepcopy(payload)

    def _read_cache(
        self,
        cache_key: str,
        *,
        max_age_seconds: int,
    ) -> Optional[List[Dict[str, Any]]]:
        """Read a cached payload if it is still within the allowed age."""
        if max_age_seconds <= 0:
            return None

        cached = self._response_cache.get(cache_key)
        if not cached:
            return None

        cached_at, payload = cached
        if time.monotonic() - cached_at > max_age_seconds:
            return None

        return self._clone_payload(payload)

    async def __aenter__(self) -> "OpenF1Client":
        """Async context manager entry."""
        await self._get_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create an HTTP client bound to the current event loop."""
        current_loop_id = id(asyncio.get_running_loop())

        if self._client is not None and self._client_loop_id != current_loop_id:
            await self.close()

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
            self._client_loop_id = current_loop_id
        return self._client

    @retry(
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Make an HTTP request to the OpenF1 API with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters

        Returns:
            List of dictionaries with response data

        Raises:
            OpenF1NotFoundError: When resource is not found (404)
            OpenF1RateLimitError: When rate limit is exceeded (429)
            OpenF1ConnectionError: When connection fails
            OpenF1APIError: For other API errors
        """
        # Apply rate limiting
        await _rate_limiter.acquire()

        url = f"{self.base_url}/{endpoint}"
        client = await self._get_client()

        logger.debug(f"Making {method} request to {endpoint} with params: {params}")

        try:
            response = await client.request(method, url, params=params)

            # Handle specific status codes
            if response.status_code == 404:
                logger.warning(f"Resource not found: {endpoint}")
                return []
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                raise OpenF1RateLimitError(
                    f"Rate limit exceeded. Retry after {retry_after}s"
                )

            response.raise_for_status()
            data = response.json()

            logger.debug(f"Received {len(data) if isinstance(data, list) else 1} records from {endpoint}")
            return data if isinstance(data, list) else [data]

        except httpx.ConnectError as e:
            logger.error(f"Connection error to OpenF1 API: {e}")
            raise OpenF1ConnectionError(f"Failed to connect to OpenF1 API: {e}")
        except httpx.ReadTimeout as e:
            logger.error(f"Timeout waiting for OpenF1 API response: {e}")
            raise OpenF1ConnectionError(f"Request timed out: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from OpenF1 API: {e}")
            raise OpenF1APIError(f"API error: {e.response.status_code} - {e.response.text}")
        except OpenF1APIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling OpenF1 API: {e}")
            raise OpenF1APIError(f"Unexpected error: {e}")

    async def _get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Make a GET request to the OpenF1 API."""
        cache_key = self._cache_key(endpoint, params)
        fresh_ttl, stale_ttl = self._cache_policy_for(endpoint, params)

        fresh_payload = self._read_cache(cache_key, max_age_seconds=fresh_ttl)
        if fresh_payload is not None:
            logger.debug("Serving cached OpenF1 response for %s", cache_key)
            return fresh_payload

        loop_key = (id(asyncio.get_running_loop()), cache_key)
        request_task = self._inflight_requests.get(loop_key)

        if request_task is None:
            request_task = asyncio.create_task(self._request("GET", endpoint, params))
            self._inflight_requests[loop_key] = request_task

        try:
            payload = await request_task
            if fresh_ttl > 0:
                self._response_cache[cache_key] = (
                    time.monotonic(),
                    self._clone_payload(payload),
                )
            return self._clone_payload(payload)
        except (OpenF1RateLimitError, OpenF1ConnectionError) as exc:
            stale_payload = self._read_cache(cache_key, max_age_seconds=stale_ttl)
            if stale_payload is not None:
                logger.warning(
                    "Serving stale OpenF1 cache for %s after upstream error: %s",
                    cache_key,
                    exc,
                )
                return stale_payload
            raise
        finally:
            if self._inflight_requests.get(loop_key) is request_task and request_task.done():
                self._inflight_requests.pop(loop_key, None)

    # ==================== Meetings ====================

    async def get_meetings(
        self,
        year: Optional[int] = None,
        meeting_key: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all meetings (race weekends).

        Args:
            year: Championship year (e.g., 2024)
            meeting_key: Specific meeting key

        Returns:
            List of meeting data
        """
        params: Dict[str, Any] = {}
        if year is not None:
            params["year"] = year
        if meeting_key is not None:
            params["meeting_key"] = meeting_key

        logger.info(f"Fetching meetings for year={year}, meeting_key={meeting_key}")
        return await self._get("meetings", params)

    # ==================== Sessions ====================

    async def get_sessions(
        self,
        meeting_key: Optional[int] = None,
        session_type: Optional[str] = None,
        session_key: Optional[int] = None,
        year: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get session information.

        Args:
            meeting_key: Filter by meeting
            session_type: Filter by type (Practice, Qualifying, Sprint, Race)
            session_key: Specific session key
            year: Championship year

        Returns:
            List of session data
        """
        params: Dict[str, Any] = {}
        if meeting_key is not None:
            params["meeting_key"] = meeting_key
        if session_type is not None:
            params["session_type"] = session_type
        if session_key is not None:
            params["session_key"] = session_key
        if year is not None:
            params["year"] = year

        logger.info(f"Fetching sessions with params: {params}")
        return await self._get("sessions", params)

    # ==================== Drivers ====================

    async def get_drivers(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
        team_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get driver information.

        Args:
            session_key: Filter by session
            driver_number: Specific driver number
            team_name: Filter by team name

        Returns:
            List of driver data
        """
        params: Dict[str, Any] = {}
        if session_key is not None:
            params["session_key"] = session_key
        if driver_number is not None:
            params["driver_number"] = driver_number
        if team_name is not None:
            params["team_name"] = team_name

        logger.info(f"Fetching drivers with params: {params}")
        return await self._get("drivers", params)

    # ==================== Car Data (Telemetry) ====================

    async def get_car_data(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
        meeting_key: Optional[int] = None,
        speed_gt: Optional[int] = None,
        speed_lt: Optional[int] = None,
        throttle_gt: Optional[int] = None,
        brake: Optional[bool] = None,
        date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get car telemetry data (speed, throttle, brake, DRS, gear, RPM).
        Data is available at ~3.7 Hz frequency.

        Args:
            session_key: Filter by session
            driver_number: Filter by driver
            meeting_key: Filter by meeting
            speed_gt: Minimum speed filter (km/h)
            speed_lt: Maximum speed filter (km/h)
            throttle_gt: Minimum throttle percentage
            brake: Brake status filter
            date: Date/time filter (ISO format)

        Returns:
            List of car telemetry data
        """
        params: Dict[str, Any] = {}
        if session_key is not None:
            params["session_key"] = session_key
        if driver_number is not None:
            params["driver_number"] = driver_number
        if meeting_key is not None:
            params["meeting_key"] = meeting_key
        if date is not None:
            params["date"] = date

        logger.info(f"Fetching car_data with params: {params}")
        data = await self._get("car_data", params)

        # Apply client-side filters
        if speed_gt is not None:
            data = [d for d in data if d.get("speed", 0) > speed_gt]
        if speed_lt is not None:
            data = [d for d in data if d.get("speed", 0) < speed_lt]
        if throttle_gt is not None:
            data = [d for d in data if d.get("throttle", 0) > throttle_gt]
        if brake is not None:
            data = [d for d in data if d.get("brake") == brake]

        return data

    # ==================== Laps ====================

    async def get_laps(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
        lap_number: Optional[int] = None,
        meeting_key: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get lap timing data including sector times and speed traps.

        Args:
            session_key: Filter by session
            driver_number: Filter by driver
            lap_number: Specific lap number
            meeting_key: Filter by meeting

        Returns:
            List of lap data
        """
        params: Dict[str, Any] = {}
        if session_key is not None:
            params["session_key"] = session_key
        if driver_number is not None:
            params["driver_number"] = driver_number
        if lap_number is not None:
            params["lap_number"] = lap_number
        if meeting_key is not None:
            params["meeting_key"] = meeting_key

        logger.info(f"Fetching laps with params: {params}")
        return await self._get("laps", params)

    # ==================== Position ====================

    async def get_positions(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
        meeting_key: Optional[int] = None,
        position: Optional[int] = None,
        date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get driver position data (x, y, z coordinates on track).
        Data is available at ~4 second intervals.

        Args:
            session_key: Filter by session
            driver_number: Filter by driver
            meeting_key: Filter by meeting
            position: Filter by race position
            date: Date/time filter (ISO format)

        Returns:
            List of position data
        """
        params: Dict[str, Any] = {}
        if session_key is not None:
            params["session_key"] = session_key
        if driver_number is not None:
            params["driver_number"] = driver_number
        if meeting_key is not None:
            params["meeting_key"] = meeting_key
        if date is not None:
            params["date"] = date

        logger.info(f"Fetching positions with params: {params}")
        data = await self._get("position", params)

        # Apply client-side filter
        if position is not None:
            data = [d for d in data if d.get("position") == position]

        return data

    # ==================== Pit Stops ====================

    async def get_pit(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
        meeting_key: Optional[int] = None,
        lap_number: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get pit stop information.

        Args:
            session_key: Filter by session
            driver_number: Filter by driver
            meeting_key: Filter by meeting
            lap_number: Filter by lap number

        Returns:
            List of pit stop data
        """
        params: Dict[str, Any] = {}
        if session_key is not None:
            params["session_key"] = session_key
        if driver_number is not None:
            params["driver_number"] = driver_number
        if meeting_key is not None:
            params["meeting_key"] = meeting_key
        if lap_number is not None:
            params["lap_number"] = lap_number

        logger.info(f"Fetching pit data with params: {params}")
        return await self._get("pit", params)

    # ==================== Stints ====================

    async def get_stints(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
        meeting_key: Optional[int] = None,
        tyre_compound: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get stint information including tyre compound and lap ranges.

        Args:
            session_key: Filter by session
            driver_number: Filter by driver
            meeting_key: Filter by meeting
            tyre_compound: Filter by compound (SOFT, MEDIUM, HARD, INTERMEDIATE, WET)

        Returns:
            List of stint data
        """
        params: Dict[str, Any] = {}
        if session_key is not None:
            params["session_key"] = session_key
        if driver_number is not None:
            params["driver_number"] = driver_number
        if meeting_key is not None:
            params["meeting_key"] = meeting_key

        logger.info(f"Fetching stints with params: {params}")
        data = await self._get("stints", params)

        # Apply client-side filter
        if tyre_compound is not None:
            data = [d for d in data if d.get("compound") == tyre_compound]

        return data

    # ==================== Weather ====================

    async def get_weather(
        self,
        session_key: Optional[int] = None,
        meeting_key: Optional[int] = None,
        date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get weather data (temperature, humidity, pressure, rainfall, wind).

        Args:
            session_key: Filter by session
            meeting_key: Filter by meeting
            date: Date/time filter (ISO format)

        Returns:
            List of weather data
        """
        params: Dict[str, Any] = {}
        if session_key is not None:
            params["session_key"] = session_key
        if meeting_key is not None:
            params["meeting_key"] = meeting_key
        if date is not None:
            params["date"] = date

        logger.info(f"Fetching weather with params: {params}")
        return await self._get("weather", params)

    # ==================== Team Radio ====================

    async def get_team_radio(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
        meeting_key: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get team radio transcripts.

        Args:
            session_key: Filter by session
            driver_number: Filter by driver
            meeting_key: Filter by meeting

        Returns:
            List of team radio data
        """
        params: Dict[str, Any] = {}
        if session_key is not None:
            params["session_key"] = session_key
        if driver_number is not None:
            params["driver_number"] = driver_number
        if meeting_key is not None:
            params["meeting_key"] = meeting_key

        logger.info(f"Fetching team_radio with params: {params}")
        return await self._get("team_radio", params)

    # ==================== Control Messages (Race Control) ====================

    async def get_race_control(
        self,
        session_key: Optional[int] = None,
        meeting_key: Optional[int] = None,
        category: Optional[str] = None,
        flag: Optional[str] = None,
        scope: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get race control messages (flags, safety car, penalties, etc.).

        Args:
            session_key: Filter by session
            meeting_key: Filter by meeting
            category: Filter by category
            flag: Filter by flag type
            scope: Filter by scope

        Returns:
            List of race control messages
        """
        params: Dict[str, Any] = {}
        if session_key is not None:
            params["session_key"] = session_key
        if meeting_key is not None:
            params["meeting_key"] = meeting_key
        if category is not None:
            params["category"] = category
        if flag is not None:
            params["flag"] = flag
        if scope is not None:
            params["scope"] = scope

        logger.info(f"Fetching race_control with params: {params}")
        return await self._get("race_control", params)

    # ==================== Intervals ====================

    async def get_intervals(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
        meeting_key: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get timing interval data between drivers.

        Args:
            session_key: Filter by session
            driver_number: Filter by driver
            meeting_key: Filter by meeting

        Returns:
            List of interval data
        """
        params: Dict[str, Any] = {}
        if session_key is not None:
            params["session_key"] = session_key
        if driver_number is not None:
            params["driver_number"] = driver_number
        if meeting_key is not None:
            params["meeting_key"] = meeting_key

        logger.info(f"Fetching intervals with params: {params}")
        return await self._get("intervals", params)

    # ==================== Utility Methods ====================

    async def close(self) -> None:
        """Close the HTTP client connection."""
        if self._client:
            try:
                await self._client.aclose()
            except RuntimeError as exc:
                if "Event loop is closed" not in str(exc):
                    raise
                logger.warning("OpenF1 client closed after event loop shutdown")
            finally:
                self._client = None
                self._client_loop_id = None
            logger.info("OpenF1 client connection closed")


# Singleton instance
openf1_client = OpenF1Client()
