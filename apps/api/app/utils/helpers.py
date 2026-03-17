"""
Helper utilities.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


def format_lap_time(seconds: float) -> str:
    """Format lap time from seconds to F1 format (M:SS.mmm)."""
    if seconds <= 0:
        return "--:--.---"

    minutes = int(seconds // 60)
    secs = seconds % 60

    return f"{minutes}:{secs:06.3f}"


def format_gap(seconds: Optional[float]) -> str:
    """Format gap time."""
    if seconds is None:
        return "---"
    if seconds < 0:
        return f"{seconds:.3f}"
    return f"+{seconds:.3f}"


def get_team_color(team_name: str) -> str:
    """Get hex color for a team."""
    team_colors = {
        "Red Bull Racing": "#0600EF",
        "Ferrari": "#DC0000",
        "Mercedes": "#00D2BE",
        "McLaren": "#FF8700",
        "Aston Martin": "#006F62",
        "Alpine": "#0090FF",
        "Williams": "#005AFF",
        "AlphaTauri": "#2B4562",
        "Alfa Romeo": "#900000",
        "Haas F1 Team": "#FFFFFF",
        "RB": "#6692FF",
        "Kick Sauber": "#52E252",
    }
    return team_colors.get(team_name, "#38383F")


def parse_iso_datetime(iso_string: str) -> datetime:
    """Parse ISO datetime string."""
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


def calculate_pace_difference(
    lap_time: float,
    reference_time: float,
) -> float:
    """Calculate pace difference as percentage."""
    if reference_time == 0:
        return 0.0
    return ((lap_time - reference_time) / reference_time) * 100
