"""
F1 Telemetry API - Main Application Entry Point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import fastf1, f1db, predictions, sessions, telemetry, websocket, weather


from app.routers.websocket import start_websocket_streaming, stop_websocket_streaming


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events handler."""
    # Startup
    print(f"🚀 Starting F1 Telemetry API v{settings.app_version}")
    print(f"📍 OpenF1 API: {settings.openf1_base_url}")
    print(f"💾 Fast-F1 Cache: {settings.fastf1_cache_dir}")
    
    # Start WebSocket streaming
    await start_websocket_streaming()
    print("📡 WebSocket streaming started")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down F1 Telemetry API")
    await stop_websocket_streaming()
    print("📡 WebSocket streaming stopped")


app = FastAPI(
    title="F1 Telemetry API",
    description="""
## Real-time F1 Telemetry and ML-Powered Predictions

This API provides access to:
- **OpenF1 API**: Real-time telemetry data during live sessions
- **Fast-F1**: Historical session data and detailed analysis
- **F1DB**: Complete F1 database from 1950 to present (drivers, teams, circuits, races, standings)
- **ML Predictions**: Pit stop timing, position forecasts, and strategy analysis

### Data Sources
- [OpenF1 API](https://openf1.org/) - Real-time F1 data
- [Fast-F1](https://docs.fastf1.dev/) - Historical F1 data analysis
- [F1DB](https://github.com/f1db/f1db) - Comprehensive F1 database (1950-present)

### Rate Limits
- OpenF1: 3 requests/second (free tier)
- Fast-F1: Data is cached locally after first request
- F1DB: Local SQLite database, no rate limits
""",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    telemetry.router,
    prefix="/api/telemetry",
    tags=["Telemetry (OpenF1)"],
)
app.include_router(
    sessions.router,
    prefix="/api/sessions",
    tags=["Sessions (OpenF1)"],
)
app.include_router(
    fastf1.router,
    prefix="/api/fastf1",
    tags=["Historical Data (Fast-F1)"],
)
app.include_router(
    predictions.router,
    prefix="/api/predictions",
    tags=["ML Predictions"],
)
app.include_router(
    websocket.router,
    prefix="/ws",
    tags=["WebSocket"],
)
app.include_router(
    weather.router,
    prefix="/api/weather",
    tags=["Weather (Open-Meteo)"],
)
app.include_router(
    f1db.router,
    prefix="/api/f1db",
    tags=["F1DB Historical Data"],
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "F1 Telemetry API",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "running",
        "endpoints": {
            "telemetry": "/api/telemetry",
            "sessions": "/api/sessions",
            "fastf1": "/api/fastf1",
            "f1db": "/api/f1db",
            "predictions": "/api/predictions",
            "websocket": "/ws",
            "weather": "/api/weather",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
    }
