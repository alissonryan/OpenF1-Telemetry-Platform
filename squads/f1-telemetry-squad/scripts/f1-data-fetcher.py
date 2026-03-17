#!/usr/bin/env python3
"""
F1 Data Fetcher - Script para buscar dados da OpenF1 API

Usage:
    python f1-data-fetcher.py sessions --year 2024
    python f1-data-fetcher.py telemetry --session 1234 --driver 1
    python f1-data-fetcher.py positions --session 1234
"""

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path

import httpx


class F1DataFetcher:
    """Fetch data from OpenF1 API."""
    
    BASE_URL = "https://api.openf1.org/v1"
    
    def __init__(self, output_dir: str = "./data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.AsyncClient(base_url=self.BASE_URL, timeout=30.0)
    
    async def fetch_sessions(self, year: int = None) -> list:
        """Fetch available sessions."""
        params = {}
        if year:
            params["year"] = year
        
        response = await self.client.get("/sessions", params=params)
        response.raise_for_status()
        return response.json()
    
    async def fetch_drivers(self, session_key: int) -> list:
        """Fetch drivers for a session."""
        response = await self.client.get("/drivers", params={"session_key": session_key})
        response.raise_for_status()
        return response.json()
    
    async def fetch_car_data(self, session_key: int, driver_number: int = None) -> list:
        """Fetch car telemetry data."""
        params = {"session_key": session_key}
        if driver_number:
            params["driver_number"] = driver_number
        
        response = await self.client.get("/car_data", params=params)
        response.raise_for_status()
        return response.json()
    
    async def fetch_positions(self, session_key: int) -> list:
        """Fetch driver positions."""
        response = await self.client.get("/position", params={"session_key": session_key})
        response.raise_for_status()
        return response.json()
    
    async def fetch_laps(self, session_key: int, driver_number: int = None) -> list:
        """Fetch lap data."""
        params = {"session_key": session_key}
        if driver_number:
            params["driver_number"] = driver_number
        
        response = await self.client.get("/laps", params=params)
        response.raise_for_status()
        return response.json()
    
    async def fetch_pit_stops(self, session_key: int) -> list:
        """Fetch pit stop data."""
        response = await self.client.get("/pit", params={"session_key": session_key})
        response.raise_for_status()
        return response.json()
    
    async def fetch_weather(self, session_key: int) -> list:
        """Fetch weather data."""
        response = await self.client.get("/weather", params={"session_key": session_key})
        response.raise_for_status()
        return response.json()
    
    def save_data(self, data: list, filename: str):
        """Save data to JSON file."""
        output_path = self.output_dir / filename
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"Saved {len(data)} records to {output_path}")
    
    async def close(self):
        await self.client.aclose()


async def main():
    parser = argparse.ArgumentParser(description="F1 Data Fetcher")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Sessions command
    sessions_parser = subparsers.add_parser("sessions", help="Fetch sessions")
    sessions_parser.add_argument("--year", type=int, help="Filter by year")
    
    # Telemetry command
    telemetry_parser = subparsers.add_parser("telemetry", help="Fetch car telemetry")
    telemetry_parser.add_argument("--session", type=int, required=True, help="Session key")
    telemetry_parser.add_argument("--driver", type=int, help="Driver number")
    
    # Positions command
    positions_parser = subparsers.add_parser("positions", help="Fetch positions")
    positions_parser.add_argument("--session", type=int, required=True, help="Session key")
    
    # Laps command
    laps_parser = subparsers.add_parser("laps", help="Fetch laps")
    laps_parser.add_argument("--session", type=int, required=True, help="Session key")
    laps_parser.add_argument("--driver", type=int, help="Driver number")
    
    # Pit stops command
    pit_parser = subparsers.add_parser("pits", help="Fetch pit stops")
    pit_parser.add_argument("--session", type=int, required=True, help="Session key")
    
    # Weather command
    weather_parser = subparsers.add_parser("weather", help="Fetch weather")
    weather_parser.add_argument("--session", type=int, required=True, help="Session key")
    
    # All command
    all_parser = subparsers.add_parser("all", help="Fetch all data for a session")
    all_parser.add_argument("--session", type=int, required=True, help="Session key")
    
    args = parser.parse_args()
    
    fetcher = F1DataFetcher()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        if args.command == "sessions":
            data = await fetcher.fetch_sessions(year=args.year)
            fetcher.save_data(data, f"sessions_{args.year or 'all'}_{timestamp}.json")
        
        elif args.command == "telemetry":
            data = await fetcher.fetch_car_data(args.session, args.driver)
            driver_suffix = f"_driver{args.driver}" if args.driver else ""
            fetcher.save_data(data, f"telemetry_session{args.session}{driver_suffix}_{timestamp}.json")
        
        elif args.command == "positions":
            data = await fetcher.fetch_positions(args.session)
            fetcher.save_data(data, f"positions_session{args.session}_{timestamp}.json")
        
        elif args.command == "laps":
            data = await fetcher.fetch_laps(args.session, args.driver)
            driver_suffix = f"_driver{args.driver}" if args.driver else ""
            fetcher.save_data(data, f"laps_session{args.session}{driver_suffix}_{timestamp}.json")
        
        elif args.command == "pits":
            data = await fetcher.fetch_pit_stops(args.session)
            fetcher.save_data(data, f"pits_session{args.session}_{timestamp}.json")
        
        elif args.command == "weather":
            data = await fetcher.fetch_weather(args.session)
            fetcher.save_data(data, f"weather_session{args.session}_{timestamp}.json")
        
        elif args.command == "all":
            print(f"Fetching all data for session {args.session}...")
            
            # Fetch all data types
            tasks = [
                ("drivers", fetcher.fetch_drivers(args.session)),
                ("telemetry", fetcher.fetch_car_data(args.session)),
                ("positions", fetcher.fetch_positions(args.session)),
                ("laps", fetcher.fetch_laps(args.session)),
                ("pits", fetcher.fetch_pit_stops(args.session)),
                ("weather", fetcher.fetch_weather(args.session)),
            ]
            
            for name, task in tasks:
                try:
                    data = await task
                    fetcher.save_data(data, f"{name}_session{args.session}_{timestamp}.json")
                except Exception as e:
                    print(f"Error fetching {name}: {e}")
    
    finally:
        await fetcher.close()


if __name__ == "__main__":
    asyncio.run(main())
