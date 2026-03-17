"""
WebSocket router for real-time data streaming.
"""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Connection might be closed
                pass


manager = ConnectionManager()


@router.websocket("/")
async def websocket_endpoint(
    websocket: WebSocket,
    session_key: Optional[int] = None,
):
    """
    WebSocket endpoint for real-time telemetry streaming.

    Streams car data, positions, and timing updates.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Wait for any incoming message (subscription commands, etc.)
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                command = message.get("command")

                if command == "subscribe":
                    # Handle subscription to specific data streams
                    channels = message.get("channels", [])
                    await websocket.send_json(
                        {"type": "subscribed", "channels": channels}
                    )

                elif command == "ping":
                    await websocket.send_json({"type": "pong"})

            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def broadcast_telemetry(data: dict):
    """Broadcast telemetry data to all connected clients."""
    await manager.broadcast({"type": "telemetry", "data": data})


async def broadcast_positions(data: dict):
    """Broadcast position data to all connected clients."""
    await manager.broadcast({"type": "positions", "data": data})
