"""
FastAPI dependencies for dependency injection.
"""

from typing import AsyncGenerator

from fastapi import Depends
from httpx import AsyncClient

from app.services.openf1_client import openf1_client


async def get_http_client() -> AsyncGenerator[AsyncClient, None]:
    """Get an HTTP client for making external API requests."""
    async with AsyncClient(timeout=30.0) as client:
        yield client


async def get_openf1_client():
    """Get the OpenF1 client instance."""
    return openf1_client


# Common dependency types
HTTPClient = Depends(get_http_client)
OpenF1Dependency = Depends(get_openf1_client)
