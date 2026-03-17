# Task: Connect OpenF1 API

## Metadata
- **Agent**: @f1-backend-dev (ou @f1-data-engineer)
- **Sprint**: 2
- **Priority**: HIGH
- **Estimate**: 6h

## Objective
Implementar cliente para OpenF1 API com suporte a dados em tempo real via WebSocket e REST endpoints.

## Prerequisites
- [ ] Backend FastAPI scaffolded
- [ ] OpenF1 API documentation reviewed

## Inputs
- OpenF1 API base URL: https://api.openf1.org/v1
- Rate limit: 30 requests/minute

## Outputs
- [ ] OpenF1Client class implementada
- [ ] REST endpoints para dados históricos
- [ ] WebSocket connection para real-time
- [ ] Rate limiting handler
- [ ] Error handling robusto
- [ ] Cache layer

## Endpoints to Implement

### REST Endpoints
| Endpoint | Description | Cache TTL |
|----------|-------------|-----------|
| `/sessions` | Lista sessões disponíveis | 5 min |
| `/drivers` | Lista drivers de uma sessão | 5 min |
| `/car_data` | Dados do carro (speed, throttle, etc) | 1 min |
| `/position` | Posições dos drivers | 10s |
| `/laps` | Dados de voltas | 1 min |
| `/pit` | Pit stops | 1 min |
| `/stints` | Stints de pneus | 5 min |
| `/weather` | Dados meteorológicos | 30s |
| `/team_radio` | Rádio da equipe | 5 min |
| `/race_control` | Mensagens de controle | 10s |

## Implementation

### OpenF1 Client Class
```python
# app/services/openf1_client.py
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio

class OpenF1Client:
    BASE_URL = "https://api.openf1.org/v1"
    RATE_LIMIT = 30  # requests per minute
    
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=self.BASE_URL, timeout=10.0)
        self._request_times: List[datetime] = []
    
    async def _check_rate_limit(self):
        """Ensure we don't exceed rate limit"""
        now = datetime.now()
        self._request_times = [t for t in self._request_times 
                               if (now - t).seconds < 60]
        
        if len(self._request_times) >= self.RATE_LIMIT:
            wait_time = 60 - (now - self._request_times[0]).seconds
            await asyncio.sleep(wait_time)
        
        self._request_times.append(now)
    
    async def get_sessions(self, year: Optional[int] = None) -> List[Dict]:
        """Get available sessions"""
        await self._check_rate_limit()
        params = {"year": year} if year else {}
        response = await self.client.get("/sessions", params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_car_data(
        self, 
        session_key: int, 
        driver_number: Optional[int] = None,
        speed_gte: Optional[float] = None
    ) -> List[Dict]:
        """Get car telemetry data"""
        await self._check_rate_limit()
        params = {"session_key": session_key}
        if driver_number:
            params["driver_number"] = driver_number
        if speed_gte:
            params["speed>="] = speed_gte
            
        response = await self.client.get("/car_data", params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_positions(
        self, 
        session_key: int,
        driver_number: Optional[int] = None
    ) -> List[Dict]:
        """Get driver positions"""
        await self._check_rate_limit()
        params = {"session_key": session_key}
        if driver_number:
            params["driver_number"] = driver_number
            
        response = await self.client.get("/position", params=params)
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        await self.client.aclose()
```

### WebSocket Handler
```python
# app/routers/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from app.services.openf1_client import OpenF1Client
import asyncio
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/telemetry/{session_key}")
async def telemetry_websocket(websocket: WebSocket, session_key: int):
    await manager.connect(websocket)
    client = OpenF1Client()
    
    try:
        while True:
            # Poll for position updates (every 4 seconds)
            positions = await client.get_positions(session_key)
            await websocket.send_json({
                "type": "positions",
                "data": positions
            })
            await asyncio.sleep(4)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    finally:
        await client.close()
```

### API Router
```python
# app/routers/telemetry.py
from fastapi import APIRouter, HTTPException
from app.services.openf1_client import OpenF1Client

router = APIRouter(prefix="/api/v1", tags=["telemetry"])

@router.get("/sessions")
async def list_sessions(year: Optional[int] = None):
    """List available F1 sessions"""
    async with OpenF1Client() as client:
        return await client.get_sessions(year)

@router.get("/sessions/{session_key}/car-data")
async def get_car_data(
    session_key: int, 
    driver_number: Optional[int] = None
):
    """Get car telemetry data for a session"""
    async with OpenF1Client() as client:
        return await client.get_car_data(session_key, driver_number)

@router.get("/sessions/{session_key}/positions")
async def get_positions(session_key: int):
    """Get current driver positions"""
    async with OpenF1Client() as client:
        return await client.get_positions(session_key)
```

## Acceptance Criteria
- [ ] Todos os endpoints REST funcionando
- [ ] WebSocket enviando dados a cada 4 segundos
- [ ] Rate limiting respeitado
- [ ] Erros tratados com HTTP status codes apropriados
- [ ] Cache implementado com TTL correto
- [ ] Logs de requisições funcionando

## Testing
```python
import pytest
from app.services.openf1_client import OpenF1Client

@pytest.mark.asyncio
async def test_get_sessions():
    async with OpenF1Client() as client:
        sessions = await client.get_sessions(year=2024)
        assert len(sessions) > 0
        assert "session_key" in sessions[0]

@pytest.mark.asyncio
async def test_rate_limiting():
    client = OpenF1Client()
    # Make 31 requests quickly
    for _ in range(31):
        await client.get_sessions()
    # Should not raise, should wait
```

## Dependencies
- f1-setup-project

## Risks
- Rate limiting pode causar delays
- API pode ter downtime durante corridas
