"""
WebSocket router for real-time data streaming.

Provides real-time F1 telemetry data via WebSocket:
- Car telemetry (~3.7Hz): speed, throttle, brake, gear, RPM, DRS
- Positions (~4s intervals): driver positions on track
- Pit stops: real-time pit stop notifications
- Weather: track conditions updates
- Predictions (~12s intervals): pit, position and strategy bundle
- Heartbeat: connection health monitoring

Usage:
    ws://localhost:8000/ws?session_key=9471
    
Commands (send JSON):
    {"command": "subscribe", "session_key": 9471, "driver_numbers": [1, 11], "channels": ["telemetry", "positions", "predictions"]}
    {"command": "ping"}
"""

import asyncio
import json
import logging
import time
from typing import List, Optional, Set

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.services.openf1_client import openf1_client
from app.services.websocket_manager import connection_manager

router = APIRouter()
logger = logging.getLogger(__name__)


async def _resolve_driver_numbers(session_key: int) -> List[int]:
    """Resolve all driver numbers for a session when the client omits them."""
    try:
        drivers = await openf1_client.get_drivers(session_key=session_key)
    except Exception as exc:
        logger.warning("Could not resolve drivers for session %s: %s", session_key, exc)
        return []

    return [
        int(driver["driver_number"])
        for driver in drivers
        if driver.get("driver_number") is not None
    ]


@router.websocket("")
@router.websocket("/")
async def websocket_endpoint(
    websocket: WebSocket,
    session_key: Optional[int] = Query(None, description="Session key to subscribe"),
):
    """
    WebSocket endpoint for real-time telemetry streaming.
    
    Query Parameters:
        session_key: Optional session key to auto-subscribe on connect
    
    Client Commands:
        subscribe: Subscribe to data channels
            {"command": "subscribe", "session_key": 9471, "driver_numbers": [1, 11], "channels": ["telemetry"]}
        ping: Connection health check
            {"command": "ping"}
    
    Server Messages:
        telemetry: Real-time car data (~3.7Hz)
            {"type": "telemetry", "data": [...], "driver_number": 1, "timestamp": ...}
        positions: Driver positions (~4s)
            {"type": "positions", "data": [...], "timestamp": ...}
        pit_stop: Pit stop updates
            {"type": "pit_stop", "data": {...}, "timestamp": ...}
        weather: Track conditions (~60s)
            {"type": "weather", "data": {...}, "timestamp": ...}
        predictions: Live prediction bundle (~12s)
            {"type": "predictions", "data": {...}, "timestamp": ...}
        heartbeat: Connection health (~30s)
            {"type": "heartbeat", "timestamp": ...}
        pong: Response to ping
            {"type": "pong", "timestamp": ...}
        error: Error message
            {"type": "error", "message": "..."}
    """
    await connection_manager.connect(websocket)
    
    # Auto-subscribe if session_key provided
    if session_key:
        driver_numbers = await _resolve_driver_numbers(session_key)
        connection_manager.update_subscription(
            websocket,
            session_key=session_key,
            driver_numbers=driver_numbers,
        )
        await websocket.send_json({
            "type": "subscribed",
            "session_key": session_key,
            "driver_numbers": driver_numbers,
            "channels": list(connection_manager.active_connections[websocket].channels),
        })
    
    try:
        while True:
            # Wait for incoming messages with timeout for heartbeat
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60)
            except asyncio.TimeoutError:
                # Send heartbeat if no message received
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": time.time(),
                })
                continue
            
            try:
                message = json.loads(data)
                command = message.get("command")
                
                if command == "subscribe":
                    # Handle subscription
                    new_session_key = message.get("session_key")
                    driver_numbers = message.get("driver_numbers", [])
                    channels = message.get("channels", ["telemetry", "positions", "pit_stop", "weather"])
                    current_subscription = connection_manager.active_connections.get(websocket)
                    effective_session_key = (
                        new_session_key
                        or (current_subscription.session_key if current_subscription else None)
                    )
                    if effective_session_key and not driver_numbers:
                        driver_numbers = await _resolve_driver_numbers(effective_session_key)
                    
                    connection_manager.update_subscription(
                        websocket,
                        session_key=new_session_key,
                        driver_numbers=driver_numbers,
                        channels=channels,
                    )
                    
                    await websocket.send_json({
                        "type": "subscribed",
                        "session_key": new_session_key,
                        "driver_numbers": driver_numbers,
                        "channels": list(channels),
                        "timestamp": time.time(),
                    })
                    logger.info(f"Client subscribed to session {new_session_key}, drivers: {driver_numbers}")
                    
                elif command == "unsubscribe":
                    # Handle unsubscription
                    channels = message.get("channels", [])
                    if channels:
                        current_sub = connection_manager.active_connections.get(websocket)
                        if current_sub:
                            current_sub.channels -= set(channels)
                            
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "channels": channels,
                        "timestamp": time.time(),
                    })
                    
                elif command == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time(),
                    })
                    
                elif command == "get_buffer":
                    # Get buffered telemetry data
                    driver_number = message.get("driver_number")
                    if driver_number:
                        buffer = connection_manager._telemetry_buffer.get(driver_number, [])
                        await websocket.send_json({
                            "type": "buffer",
                            "driver_number": driver_number,
                            "data": buffer[-50:],  # Last 50 points
                            "timestamp": time.time(),
                        })
                        
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown command: {command}",
                    })
                    
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format",
                })
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info("Client disconnected normally")
        
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)


# ==================== Lifecycle Events ====================

async def start_websocket_streaming():
    """Start background streaming tasks. Called on app startup."""
    await connection_manager.start_streaming()
    logger.info("WebSocket streaming started")


async def stop_websocket_streaming():
    """Stop background streaming tasks. Called on app shutdown."""
    await connection_manager.stop_streaming()
    logger.info("WebSocket streaming stopped")


# ==================== Utility Functions ====================

async def broadcast_telemetry(session_key: int, data: dict, driver_number: Optional[int] = None):
    """Broadcast telemetry data to session subscribers."""
    message = {
        "type": "telemetry",
        "data": data,
        "driver_number": driver_number,
        "timestamp": time.time(),
    }
    await connection_manager.broadcast_to_session(session_key, message, channel="telemetry")


async def broadcast_positions(session_key: int, data: dict):
    """Broadcast position data to session subscribers."""
    message = {
        "type": "positions",
        "data": data,
        "timestamp": time.time(),
    }
    await connection_manager.broadcast_to_session(session_key, message, channel="positions")


async def broadcast_pit_stop(session_key: int, data: dict):
    """Broadcast pit stop data to session subscribers."""
    message = {
        "type": "pit_stop",
        "data": data,
        "timestamp": time.time(),
    }
    await connection_manager.broadcast_to_session(session_key, message, channel="pit_stop")


async def broadcast_weather(session_key: int, data: dict):
    """Broadcast weather data to session subscribers."""
    message = {
        "type": "weather",
        "data": data,
        "timestamp": time.time(),
    }
    await connection_manager.broadcast_to_session(session_key, message, channel="weather")


def get_connection_count() -> int:
    """Get number of active WebSocket connections."""
    return len(connection_manager.active_connections)


def get_session_subscribers(session_key: int) -> int:
    """Get number of clients subscribed to a session."""
    return len(connection_manager.get_session_clients(session_key))
