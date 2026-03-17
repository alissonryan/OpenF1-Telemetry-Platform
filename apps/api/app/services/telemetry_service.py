"""
Telemetry processing service.
"""

from typing import Dict, List, Optional

from app.services.openf1_client import openf1_client


class TelemetryService:
    """Service for processing and aggregating telemetry data."""

    async def get_latest_telemetry(
        self,
        session_key: int,
        driver_number: Optional[int] = None,
    ) -> List[Dict]:
        """Get the latest telemetry data for a session."""
        data = await openf1_client.get_car_data(
            session_key=session_key,
            driver_number=driver_number,
        )
        return data

    async def get_telemetry_summary(
        self,
        session_key: int,
        driver_number: int,
    ) -> Dict:
        """Get a summary of telemetry data for a driver."""
        data = await openf1_client.get_car_data(
            session_key=session_key,
            driver_number=driver_number,
        )

        if not data:
            return {}

        # Calculate summary statistics
        speeds = [d["speed"] for d in data if d.get("speed")]
        throttles = [d["throttle"] for d in data if d.get("throttle") is not None]
        brakes = [d["brake"] for d in data if d.get("brake") is not None]

        return {
            "driver_number": driver_number,
            "session_key": session_key,
            "samples": len(data),
            "max_speed": max(speeds) if speeds else 0,
            "avg_speed": sum(speeds) / len(speeds) if speeds else 0,
            "avg_throttle": sum(throttles) / len(throttles) if throttles else 0,
            "brake_percentage": sum(brakes) / len(brakes) * 100 if brakes else 0,
        }


# Singleton instance
telemetry_service = TelemetryService()
