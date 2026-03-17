"""
F1 Telemetry API - Main Application Entry Point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import predictions, sessions, telemetry, websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events handler."""
    # Startup
    print(f"🚀 Starting F1 Telemetry API v{settings.app_version}")
    yield
    # Shutdown
    print("🛑 Shutting down F1 Telemetry API")


app = FastAPI(
    title="F1 Telemetry API",
    description="Real-time F1 telemetry and ML-powered predictions",
    version="0.1.0",
    lifespan=lifespan,
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
app.include_router(telemetry.router, prefix="/api/telemetry", tags=["telemetry"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "F1 Telemetry API",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
