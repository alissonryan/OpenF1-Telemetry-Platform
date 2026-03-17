"""
Build live prediction context from OpenF1 session data.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Sequence

from app.core.logging import logger
from app.services.openf1_client import openf1_client

DEFAULT_TOTAL_LAPS = {
    "Practice": 20,
    "Qualifying": 18,
    "Sprint": 24,
    "Race": 57,
}

RACE_TOTAL_LAPS_BY_CIRCUIT = {
    "Sakhir": 57,
    "Jeddah": 50,
    "Melbourne": 58,
    "Suzuka": 53,
    "Shanghai": 56,
    "Miami": 57,
    "Imola": 63,
    "Monaco": 78,
    "Montreal": 70,
    "Barcelona": 66,
    "Spielberg": 71,
    "Silverstone": 52,
    "Budapest": 70,
    "Spa": 44,
    "Zandvoort": 72,
    "Monza": 53,
    "Baku": 51,
    "Singapore": 62,
    "Austin": 56,
    "Mexico City": 71,
    "Sao Paulo": 71,
    "Las Vegas": 50,
    "Lusail": 57,
    "Yas Marina Circuit": 58,
    "Yas Marina": 58,
}


class PredictionContextService:
    """Assemble a session snapshot shared by prediction endpoints."""

    def __init__(self, ttl_seconds: int = 5):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[int, tuple[float, Dict[str, Any]]] = {}
        self._inflight: Dict[tuple[int, int], asyncio.Task[Dict[str, Any]]] = {}

    async def get_context(
        self,
        session_key: int,
        driver_numbers: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Return cached live context for a session."""
        cached = self._cache.get(session_key)
        now = time.monotonic()

        if cached and now - cached[0] < self.ttl_seconds:
            context = cached[1]
        else:
            loop_key = (session_key, id(asyncio.get_running_loop()))
            task = self._inflight.get(loop_key)

            if task is None:
                task = asyncio.create_task(self._build_context(session_key))
                self._inflight[loop_key] = task

            try:
                context = await task
            finally:
                if self._inflight.get(loop_key) is task and task.done():
                    self._inflight.pop(loop_key, None)

            self._cache[session_key] = (time.monotonic(), context)

        if not driver_numbers:
            return self._clone_context(context)

        requested = {int(driver_number) for driver_number in driver_numbers}
        filtered = self._clone_context(context)
        filtered["drivers"] = [
            driver for driver in filtered["drivers"]
            if driver["driver_number"] in requested
        ]
        return filtered

    async def _build_context(self, session_key: int) -> Dict[str, Any]:
        logger.info("Building live prediction context for session %s", session_key)

        session_list, drivers, laps, positions, stints, pit_stops, weather = await asyncio.gather(
            openf1_client.get_sessions(session_key=session_key),
            openf1_client.get_drivers(session_key=session_key),
            openf1_client.get_laps(session_key=session_key),
            openf1_client.get_positions(session_key=session_key),
            openf1_client.get_stints(session_key=session_key),
            openf1_client.get_pit(session_key=session_key),
            openf1_client.get_weather(session_key=session_key),
        )

        if not session_list:
            raise ValueError(f"Session {session_key} was not found")

        session = session_list[0]
        laps_by_driver = self._group_by_driver(laps, "lap_number", "date_start")
        positions_by_driver = self._group_by_driver(positions, "date")
        stints_by_driver = self._group_by_driver(stints, "stint_number", "lap_end", "lap_start")
        pit_by_driver = self._group_by_driver(pit_stops, "lap_number", "date")

        current_lap = max(
            (
                self._driver_current_lap(
                    driver_number=int(driver["driver_number"]),
                    driver_laps=laps_by_driver.get(int(driver["driver_number"]), []),
                    driver_stints=stints_by_driver.get(int(driver["driver_number"]), []),
                )
                for driver in drivers
                if driver.get("driver_number") is not None
            ),
            default=0,
        )
        total_laps = self._estimate_total_laps(session=session, current_lap=current_lap)
        latest_weather = weather[-1] if weather else {}

        driver_summaries = []
        for driver in drivers:
            driver_number = driver.get("driver_number")
            if driver_number is None:
                continue

            driver_number = int(driver_number)
            driver_summary = self._build_driver_summary(
                driver=driver,
                current_lap=current_lap,
                total_laps=total_laps,
                driver_laps=laps_by_driver.get(driver_number, []),
                driver_positions=positions_by_driver.get(driver_number, []),
                driver_stints=stints_by_driver.get(driver_number, []),
                driver_pits=pit_by_driver.get(driver_number, []),
            )
            driver_summaries.append(driver_summary)

        self._enrich_driver_summaries(driver_summaries)

        return {
            "session": session,
            "current_lap": current_lap,
            "total_laps": total_laps,
            "weather": {
                "track_temp": float(latest_weather.get("track_temperature") or 30.0),
                "air_temp": float(latest_weather.get("air_temperature") or 25.0),
                "rainfall": float(latest_weather.get("rainfall") or 0.0),
                "condition": "wet" if float(latest_weather.get("rainfall") or 0.0) > 0 else "dry",
            },
            "drivers": sorted(
                driver_summaries,
                key=lambda driver: (
                    driver.get("position", 999),
                    driver.get("driver_number", 999),
                ),
            ),
        }

    def _build_driver_summary(
        self,
        *,
        driver: Dict[str, Any],
        current_lap: int,
        total_laps: int,
        driver_laps: List[Dict[str, Any]],
        driver_positions: List[Dict[str, Any]],
        driver_stints: List[Dict[str, Any]],
        driver_pits: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        latest_lap = driver_laps[-1] if driver_laps else {}
        latest_position = driver_positions[-1] if driver_positions else {}
        latest_stint = driver_stints[-1] if driver_stints else {}

        completed_laps = [lap for lap in driver_laps if lap.get("lap_duration") is not None]
        recent_laps = completed_laps[-3:]
        previous_laps = completed_laps[-6:-3]

        avg_lap_time = self._rounded_mean(
            [float(lap["lap_duration"]) for lap in recent_laps if lap.get("lap_duration") is not None]
        )
        sector_1_avg = self._rounded_mean(
            [float(lap["duration_sector_1"]) for lap in recent_laps if lap.get("duration_sector_1") is not None]
        )
        sector_2_avg = self._rounded_mean(
            [float(lap["duration_sector_2"]) for lap in recent_laps if lap.get("duration_sector_2") is not None]
        )
        sector_3_avg = self._rounded_mean(
            [float(lap["duration_sector_3"]) for lap in recent_laps if lap.get("duration_sector_3") is not None]
        )
        previous_avg = self._rounded_mean(
            [float(lap["lap_duration"]) for lap in previous_laps if lap.get("lap_duration") is not None]
        )
        lap_time_trend = round(avg_lap_time - previous_avg, 3) if previous_avg else 0.0

        if len(recent_laps) >= 2:
            degradation_rate = round(
                (
                    float(recent_laps[-1]["lap_duration"])
                    - float(recent_laps[0]["lap_duration"])
                ) / max(len(recent_laps) - 1, 1),
                3,
            )
        else:
            degradation_rate = 0.0

        driver_current_lap = self._driver_current_lap(
            driver_number=int(driver["driver_number"]),
            driver_laps=driver_laps,
            driver_stints=driver_stints,
        )
        compound = latest_stint.get("compound") or "MEDIUM"
        tyre_age_at_start = int(latest_stint.get("tyre_age_at_start") or 0)
        lap_start = int(latest_stint.get("lap_start") or driver_current_lap or 0)
        tyre_age = max(0, driver_current_lap - lap_start + tyre_age_at_start)

        position_history = [
            int(position["position"])
            for position in driver_positions[-5:]
            if position.get("position") is not None
        ]
        position_change_rate = 0.0
        if len(position_history) >= 2:
            position_change_rate = round(
                (position_history[0] - position_history[-1]) / max(len(position_history) - 1, 1),
                3,
            )

        return {
            "driver_number": int(driver["driver_number"]),
            "name_acronym": driver.get("name_acronym", ""),
            "team_name": driver.get("team_name", ""),
            "position": latest_position.get("position"),
            "current_lap": driver_current_lap,
            "remaining_laps": max(total_laps - driver_current_lap, 0),
            "compound": compound,
            "current_compound": compound,
            "tyre_age": tyre_age,
            "avg_lap_time": avg_lap_time,
            "sector_1_avg": sector_1_avg,
            "sector_2_avg": sector_2_avg,
            "sector_3_avg": sector_3_avg,
            "lap_time_trend": lap_time_trend,
            "degradation_rate": degradation_rate,
            "pit_stop_count": len(driver_pits),
            "position_change_rate": position_change_rate,
        }

    def _enrich_driver_summaries(self, driver_summaries: List[Dict[str, Any]]) -> None:
        if not driver_summaries:
            return

        ranked = sorted(
            driver_summaries,
            key=lambda driver: (
                driver["position"] if driver["position"] is not None else 999,
                driver["avg_lap_time"] if driver["avg_lap_time"] > 0 else 999.0,
                driver["driver_number"],
            ),
        )

        fallback_rank = sorted(
            driver_summaries,
            key=lambda driver: (
                driver["avg_lap_time"] if driver["avg_lap_time"] > 0 else 999.0,
                driver["driver_number"],
            ),
        )
        fallback_positions = {
            driver["driver_number"]: index + 1 for index, driver in enumerate(fallback_rank)
        }

        for driver in ranked:
            if driver["position"] is None:
                driver["position"] = fallback_positions[driver["driver_number"]]

        ranked = sorted(ranked, key=lambda driver: (driver["position"], driver["driver_number"]))
        field_average = self._rounded_mean(
            [driver["avg_lap_time"] for driver in ranked if driver["avg_lap_time"] > 0]
        )
        leader_average = next(
            (driver["avg_lap_time"] for driver in ranked if driver["avg_lap_time"] > 0),
            0.0,
        )

        for index, driver in enumerate(ranked):
            ahead = ranked[index - 1] if index > 0 else None
            behind = ranked[index + 1] if index + 1 < len(ranked) else None

            if driver["avg_lap_time"] > 0 and field_average > 0:
                driver["pace_delta"] = round(driver["avg_lap_time"] - field_average, 3)
            else:
                driver["pace_delta"] = 0.0

            driver["gap_ahead"] = self._estimate_gap(ahead, driver)
            driver["gap_behind"] = self._estimate_gap(driver, behind)
            if driver["position"] == 1 or leader_average == 0 or driver["avg_lap_time"] == 0:
                driver["gap_to_leader"] = 0.0
            else:
                driver["gap_to_leader"] = round(
                    max(0.0, driver["avg_lap_time"] - leader_average) * max(min(driver["current_lap"], 5), 1),
                    3,
                )
            driver["drs_available"] = driver["position"] > 1 and 0 < driver["gap_ahead"] <= 1.0

    def _estimate_total_laps(self, session: Dict[str, Any], current_lap: int) -> int:
        session_name = session.get("session_name", "")
        session_type = session.get("session_type", "")
        circuit_name = session.get("circuit_short_name") or session.get("location", "")

        if session_name == "Race":
            baseline = RACE_TOTAL_LAPS_BY_CIRCUIT.get(
                circuit_name,
                DEFAULT_TOTAL_LAPS.get(session_type, 57),
            )
        elif session_name == "Sprint":
            race_total = RACE_TOTAL_LAPS_BY_CIRCUIT.get(circuit_name, 0)
            baseline = max(
                DEFAULT_TOTAL_LAPS.get(session_name, 24),
                round(race_total / 3) if race_total else 0,
            )
        else:
            baseline = DEFAULT_TOTAL_LAPS.get(session_type, 20)

        return max(baseline, current_lap)

    def _driver_current_lap(
        self,
        *,
        driver_number: int,
        driver_laps: List[Dict[str, Any]],
        driver_stints: List[Dict[str, Any]],
    ) -> int:
        latest_lap_number = int(driver_laps[-1].get("lap_number") or 0) if driver_laps else 0
        latest_stint_lap = int(driver_stints[-1].get("lap_end") or 0) if driver_stints else 0
        return max(latest_lap_number, latest_stint_lap)

    def _estimate_gap(
        self,
        front_driver: Optional[Dict[str, Any]],
        back_driver: Optional[Dict[str, Any]],
    ) -> float:
        if not front_driver or not back_driver:
            return 0.0

        front_average = front_driver.get("avg_lap_time") or 0.0
        back_average = back_driver.get("avg_lap_time") or 0.0
        if front_average <= 0 or back_average <= 0:
            return 1.5

        return round(max(0.0, back_average - front_average) * 3, 3)

    def _group_by_driver(
        self,
        records: Iterable[Dict[str, Any]],
        *sort_fields: str,
    ) -> Dict[int, List[Dict[str, Any]]]:
        grouped: Dict[int, List[Dict[str, Any]]] = defaultdict(list)

        for record in records:
            driver_number = record.get("driver_number")
            if driver_number is None:
                continue
            grouped[int(driver_number)].append(record)

        for items in grouped.values():
            items.sort(
                key=lambda item: tuple(
                    item.get(field) if item.get(field) is not None else 0
                    for field in sort_fields
                )
            )

        return grouped

    def _clone_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "session": dict(context["session"]),
            "current_lap": context["current_lap"],
            "total_laps": context["total_laps"],
            "weather": dict(context["weather"]),
            "drivers": [dict(driver) for driver in context["drivers"]],
        }

    def _rounded_mean(self, values: Sequence[float]) -> float:
        if not values:
            return 0.0
        return round(float(mean(values)), 3)


prediction_context_service = PredictionContextService()
