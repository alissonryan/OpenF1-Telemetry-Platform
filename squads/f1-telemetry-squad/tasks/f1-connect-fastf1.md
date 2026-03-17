# Task: Connect Fast-F1

## Metadata
- **Agent**: @f1-data-engineer
- **Sprint**: 2
- **Priority**: HIGH
- **Estimate**: 6h

## Objective
Integrar a biblioteca Fast-F1 para dados históricos de F1, configurar cache e criar endpoints para análise de dados.

## Prerequisites
- [ ] Backend FastAPI scaffolded
- [ ] Python 3.11+ environment

## Inputs
- Fast-F1 library documentation
- Cache directory path: ./data/cache/fastf1

## Outputs
- [ ] FastF1Service implementada
- [ ] Cache configurado e funcionando
- [ ] Endpoints para dados históricos
- [ ] ETL básico para transformação de dados
- [ ] Integração com database

## Installation
```bash
pip install fastf1 pandas numpy
```

## Implementation

### Fast-F1 Service
```python
# app/services/fastf1_service.py
import fastf1
import pandas as pd
from typing import Optional, Dict, List, Any
from pathlib import Path

class FastF1Service:
    def __init__(self, cache_dir: str = "./data/cache/fastf1"):
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        fastf1.Cache.enable_cache(cache_dir)
    
    def get_session(
        self, 
        year: int, 
        round_number: int, 
        session_type: str = 'R'
    ) -> fastf1.core.Session:
        """
        Load a session with caching.
        
        Args:
            year: Season year
            round_number: Round number (1-24 typically)
            session_type: FP1, FP2, FP3, Q, S, SS, R
            
        Returns:
            Loaded Session object
        """
        session = fastf1.get_session(year, round_number, session_type)
        session.load()
        return session
    
    def get_session_info(self, year: int, round_number: int) -> Dict:
        """Get basic session information"""
        session = self.get_session(year, round_number, 'R')
        return {
            "year": year,
            "round": round_number,
            "event_name": session.event['EventName'],
            "circuit_name": session.event['Location'],
            "date": str(session.date),
            "total_laps": session.total_laps,
        }
    
    def get_lap_data(
        self, 
        year: int, 
        round_number: int,
        driver: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get lap data for a session.
        
        Args:
            year: Season year
            round_number: Round number
            driver: Driver code (e.g., 'VER', 'HAM'). None for all drivers.
            
        Returns:
            DataFrame with lap data
        """
        session = self.get_session(year, round_number, 'R')
        laps = session.laps
        
        if driver:
            laps = laps.pick_driver(driver)
        
        return laps[['Driver', 'LapNumber', 'LapTime', 'Sector1Time', 
                     'Sector2Time', 'Sector3Time', 'Compound', 'TyreLife',
                     'PitOutTime', 'PitInTime', 'IsPersonalBest']]
    
    def get_telemetry(
        self,
        year: int,
        round_number: int,
        driver: str,
        lap_number: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get car telemetry data.
        
        Args:
            year: Season year
            round_number: Round number
            driver: Driver code
            lap_number: Specific lap. None for fastest lap.
            
        Returns:
            DataFrame with telemetry (Speed, Throttle, Brake, Gear, RPM, DRS)
        """
        session = self.get_session(year, round_number, 'R')
        
        if lap_number:
            lap = session.laps.pick_driver(driver).pick_lap(lap_number)
        else:
            lap = session.laps.pick_driver(driver).pick_fastest()
        
        car_data = lap.get_car_data()
        car_data = car_data.add_distance()  # Add distance column
        
        return car_data[['Time', 'Distance', 'Speed', 'Throttle', 
                        'Brake', 'nGear', 'RPM', 'DRS']]
    
    def get_position_data(
        self,
        year: int,
        round_number: int,
        driver: str
    ) -> pd.DataFrame:
        """
        Get position data (x, y, z coordinates on track).
        
        Args:
            year: Season year
            round_number: Round number
            driver: Driver code
            
        Returns:
            DataFrame with position coordinates
        """
        session = self.get_session(year, round_number, 'R')
        lap = session.laps.pick_driver(driver).pick_fastest()
        
        pos_data = lap.get_pos_data()
        return pos_data[['Time', 'X', 'Y', 'Z', 'Status']]
    
    def get_weather_data(
        self,
        year: int,
        round_number: int
    ) -> pd.DataFrame:
        """
        Get weather data for a session.
        
        Args:
            year: Season year
            round_number: Round number
            
        Returns:
            DataFrame with weather data
        """
        session = self.get_session(year, round_number, 'R')
        return session.weather_data
    
    def get_all_drivers(
        self,
        year: int,
        round_number: int
    ) -> List[Dict]:
        """Get list of all drivers in a session"""
        session = self.get_session(year, round_number, 'R')
        results = session.results
        
        drivers = []
        for _, row in results.iterrows():
            drivers.append({
                "position": row['Position'],
                "driver_number": row['Abbreviation'],
                "driver_name": row['BroadcastName'],
                "team": row['TeamName'],
                "color": row['TeamColor'],
            })
        return drivers
    
    def export_to_dict(self, df: pd.DataFrame) -> List[Dict]:
        """Convert DataFrame to list of dicts for JSON response"""
        df = df.copy()
        # Convert timedelta to seconds
        for col in df.columns:
            if pd.api.types.is_timedelta64_dtype(df[col]):
                df[col] = df[col].dt.total_seconds()
        return df.to_dict('records')
```

### API Router
```python
# app/routers/historical.py
from fastapi import APIRouter, HTTPException, Query
from app.services.fastf1_service import FastF1Service

router = APIRouter(prefix="/api/v1/historical", tags=["historical"])
service = FastF1Service()

@router.get("/sessions/{year}/{round}")
async def get_session_info(year: int, round: int):
    """Get session information"""
    try:
        return service.get_session_info(year, round)
    except Exception as e:
        raise HTTPException(500, f"Failed to load session: {str(e)}")

@router.get("/sessions/{year}/{round}/drivers")
async def get_drivers(year: int, round: int):
    """Get all drivers from a session"""
    try:
        return service.get_all_drivers(year, round)
    except Exception as e:
        raise HTTPException(500, f"Failed to get drivers: {str(e)}")

@router.get("/sessions/{year}/{round}/laps")
async def get_laps(
    year: int, 
    round: int, 
    driver: Optional[str] = Query(None, min_length=3, max_length=3)
):
    """Get lap data for a session"""
    try:
        df = service.get_lap_data(year, round, driver)
        return service.export_to_dict(df)
    except Exception as e:
        raise HTTPException(500, f"Failed to get lap data: {str(e)}")

@router.get("/sessions/{year}/{round}/telemetry/{driver}")
async def get_telemetry(
    year: int,
    round: int,
    driver: str,
    lap: Optional[int] = Query(None, ge=1)
):
    """Get telemetry data for a driver"""
    try:
        df = service.get_telemetry(year, round, driver.upper(), lap)
        return service.export_to_dict(df)
    except Exception as e:
        raise HTTPException(500, f"Failed to get telemetry: {str(e)}")

@router.get("/sessions/{year}/{round}/weather")
async def get_weather(year: int, round: int):
    """Get weather data for a session"""
    try:
        df = service.get_weather_data(year, round)
        return service.export_to_dict(df)
    except Exception as e:
        raise HTTPException(500, f"Failed to get weather: {str(e)}")
```

### Data Transformation Utilities
```python
# app/utils/telemetry_transform.py
import pandas as pd
from typing import Dict, List

def normalize_telemetry(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize telemetry values to 0-1 range"""
    df = df.copy()
    df['Speed_norm'] = df['Speed'] / df['Speed'].max()
    df['Throttle_norm'] = df['Throttle'] / 100
    df['Brake_norm'] = df['Brake'] / 100
    df['RPM_norm'] = df['RPM'] / df['RPM'].max()
    return df

def resample_telemetry(df: pd.DataFrame, freq_hz: int = 10) -> pd.DataFrame:
    """Resample telemetry to specific frequency"""
    df = df.copy()
    df = df.set_index('Time')
    return df.resample(f'{1000//freq_hz}ms').mean().interpolate()

def calculate_telemetry_stats(df: pd.DataFrame) -> Dict:
    """Calculate statistics from telemetry"""
    return {
        "avg_speed": df['Speed'].mean(),
        "max_speed": df['Speed'].max(),
        "avg_throttle": df['Throttle'].mean(),
        "brake_percentage": (df['Brake'] > 0).mean() * 100,
        "gear_changes": (df['nGear'].diff() != 0).sum(),
        "drs_activations": (df['DRS'] > 0).sum(),
    }
```

## Acceptance Criteria
- [ ] Cache funcionando (dados persistem entre requisições)
- [ ] Todos os endpoints retornando dados válidos
- [ ] Tratamento de erros para sessões inexistentes
- [ ] Performance aceitável (< 5s para carregar sessão)
- [ ] Logs de carregamento de sessão

## Testing
```python
import pytest
from app.services.fastf1_service import FastF1Service

def test_get_session():
    service = FastF1Service()
    session = service.get_session(2024, 1, 'R')
    assert session is not None
    assert len(session.laps) > 0

def test_get_lap_data():
    service = FastF1Service()
    df = service.get_lap_data(2024, 1, 'VER')
    assert len(df) > 0
    assert 'LapTime' in df.columns

def test_cache():
    service = FastF1Service()
    # First call - should cache
    service.get_session(2024, 1, 'R')
    # Second call - should use cache
    service.get_session(2024, 1, 'R')
```

## Dependencies
- f1-setup-project

## Risks
- Cache pode ficar muito grande
- Algumas sessões antigas podem ter dados incompletos
