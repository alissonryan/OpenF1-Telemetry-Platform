"""
FastAPI dependencies for dependency injection.
"""

from typing import AsyncGenerator

from fastapi import Depends
from httpx import AsyncClient


async def get_http_client() -> AsyncGenerator[AsyncClient, None]:
    """Get an HTTP client for making external API requests."""
    async with AsyncClient(timeout=30.0) as client:
        yield client


# Common dependency types
HTTPClient = Depends(get_http_client)
