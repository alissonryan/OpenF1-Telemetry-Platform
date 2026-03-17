"""Pydantic models for session data."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MeetingResponse(BaseModel):
    """Meeting (race weekend) response model."""

    meeting_key: int
    meeting_name: str
    location: str
    official_name: str
    country_key: int
    country_name: str
    circuit_key: int
    circuit_short_name: str
    date_start: str
    date_end: str
    year: int
    gmt_offset: Optional[str] = None


class SessionResponse(BaseModel):
    """Session response model."""

    session_key: int
    meeting_key: int
    location: str
    session_type: str = Field(..., description="practice, qualifying, sprint, or race")
    session_name: str
    date_start: str
    date_end: str
    country_name: str
    circuit_short_name: str
    year: int
    gmt_offset: Optional[str] = None
