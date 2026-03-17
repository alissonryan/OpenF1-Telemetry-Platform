"""
WebSocket Connection Manager for real-time data streaming.

Provides:
- Multi-client broadcast support
- Real-time telemetry streaming (~3.7Hz)
- Position updates (~4 seconds)
- Pit stop notifications
- Weather updates
- Heartbeat for connection health
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from fastapi import WebSocket

from app.services.openf1_client import openf1_client

logger = logging.getLogger(__name__)


@dataclass
class ClientSubscription:
    """Tracks what data a client is subscribed to."""
    session_key: Optional[int] = None
    driver_numbers: Set[int] = field(default_factory=set)
    channels: Set[str] = field(default_factory=lambda: {"telemetry", "positions", "pit_stop", "weather"})


class ConnectionManager:
    """
    Manages WebSocket connections and real-time data streaming.
    
    Features:
    - Broadcast to all or specific clients
    - Per-client subscriptions
    - Heartbeat for connection health
    - Background tasks for data streaming
    """
    
    def __init__(self):
        self.active_connections: Dict[WebSocket, ClientSubscription] = {}
        self._background_tasks: Set[asyncio.Task] = set()
        self._running = False
        self._heartbeat_interval = 30  # seconds
        self._telemetry_interval = 0.27  # ~3.7Hz
        self._position_interval = 4  # 4 seconds
        self._weather_interval = 60  # 1 minute
        self._telemetry_buffer: Dict[int, List[dict]] = {}  # Circular buffer per driver
        self._buffer_size = 100  # Keep last 100 data points
        
    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[websocket] = ClientSubscription()
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            del self.active_connections[websocket]
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
        
    async def send_personal(self, websocket: WebSocket, message: dict) -> bool:
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.warning(f"Failed to send message to client: {e}")
            return False
            
    async def broadcast(self, message: dict, channel: Optional[str] = None) -> None:
        """Broadcast a message to all subscribed clients."""
        disconnected = []
        
        for websocket, subscription in self.active_connections.items():
            # Check if client is subscribed to this channel
            if channel and channel not in subscription.channels:
                continue
                
            if not await self.send_personal(websocket, message):
                disconnected.append(websocket)
                
        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws)
            
    async def broadcast_to_session(self, session_key: int, message: dict, channel: Optional[str] = None) -> None:
        """Broadcast to clients subscribed to a specific session."""
        disconnected = []
        
        for websocket, subscription in self.active_connections.items():
            if subscription.session_key != session_key:
                continue
            if channel and channel not in subscription.channels:
                continue
                
            if not await self.send_personal(websocket, message):
                disconnected.append(websocket)
                
        for ws in disconnected:
            self.disconnect(ws)
            
    def update_subscription(self, websocket: WebSocket, **kwargs) -> None:
        """Update client subscription settings."""
        if websocket not in self.active_connections:
            return
            
        subscription = self.active_connections[websocket]
        
        if "session_key" in kwargs:
            subscription.session_key = kwargs["session_key"]
        if "driver_numbers" in kwargs:
            subscription.driver_numbers = set(kwargs["driver_numbers"])
        if "channels" in kwargs:
            subscription.channels = set(kwargs["channels"])
            
    def get_session_clients(self, session_key: int) -> List[WebSocket]:
        """Get all clients subscribed to a session."""
        return [
            ws for ws, sub in self.active_connections.items()
            if sub.session_key == session_key
        ]
        
    # ==================== Data Streaming Methods ====================
    
    async def send_heartbeat(self) -> None:
        """Send heartbeat to all connected clients."""
        message = {
            "type": "heartbeat",
            "timestamp": time.time(),
        }
        await self.broadcast(message, channel="heartbeat")
        
    async def send_telemetry(self, session_key: int, driver_numbers: Optional[List[int]] = None) -> None:
        """Fetch and broadcast telemetry data for a session."""
        try:
            # Fetch telemetry for each driver
            for driver_number in driver_numbers or []:
                data = await openf1_client.get_car_data(
                    session_key=session_key,
                    driver_number=driver_number,
                )
                
                if data:
                    # Update buffer
                    if driver_number not in self._telemetry_buffer:
                        self._telemetry_buffer[driver_number] = []
                    self._telemetry_buffer[driver_number].extend(data[-10:])  # Add last 10 points
                    # Keep buffer size limited
                    self._telemetry_buffer[driver_number] = self._telemetry_buffer[driver_number][-self._buffer_size:]
                    
                    message = {
                        "type": "telemetry",
                        "data": data[-10:],  # Send last 10 data points
                        "driver_number": driver_number,
                        "timestamp": time.time(),
                    }
                    await self.broadcast_to_session(session_key, message, channel="telemetry")
                    
        except Exception as e:
            logger.error(f"Error fetching telemetry: {e}")
            
    async def send_positions(self, session_key: int) -> None:
        """Fetch and broadcast position data for a session."""
        try:
            data = await openf1_client.get_positions(session_key=session_key)
            
            if data:
                # Get latest position for each driver
                latest_positions = {}
                for pos in reversed(data):
                    driver_num = pos.get("driver_number")
                    if driver_num and driver_num not in latest_positions:
                        latest_positions[driver_num] = pos
                        
                message = {
                    "type": "positions",
                    "data": list(latest_positions.values()),
                    "timestamp": time.time(),
                }
                await self.broadcast_to_session(session_key, message, channel="positions")
                
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            
    async def send_pit_stops(self, session_key: int) -> None:
        """Fetch and broadcast pit stop data for a session."""
        try:
            data = await openf1_client.get_pit(session_key=session_key)
            
            if data:
                # Get latest pit stop for each driver
                latest_pits = {}
                for pit in reversed(data):
                    driver_num = pit.get("driver_number")
                    if driver_num and driver_num not in latest_pits:
                        latest_pits[driver_num] = pit
                        
                message = {
                    "type": "pit_stop",
                    "data": latest_pits,
                    "timestamp": time.time(),
                }
                await self.broadcast_to_session(session_key, message, channel="pit_stop")
                
        except Exception as e:
            logger.error(f"Error fetching pit stops: {e}")
            
    async def send_weather(self, session_key: int) -> None:
        """Fetch and broadcast weather data for a session."""
        try:
            data = await openf1_client.get_weather(session_key=session_key)
            
            if data:
                # Get latest weather data
                latest_weather = data[-1] if data else {}
                
                message = {
                    "type": "weather",
                    "data": latest_weather,
                    "timestamp": time.time(),
                }
                await self.broadcast_to_session(session_key, message, channel="weather")
                
        except Exception as e:
            logger.error(f"Error fetching weather: {e}")
            
    # ==================== Background Streaming Tasks ====================
    
    async def start_streaming(self) -> None:
        """Start background streaming tasks."""
        if self._running:
            return
            
        self._running = True
        logger.info("Starting WebSocket data streaming...")
        
        # Create background tasks
        self._background_tasks.add(
            asyncio.create_task(self._heartbeat_loop())
        )
        self._background_tasks.add(
            asyncio.create_task(self._telemetry_loop())
        )
        self._background_tasks.add(
            asyncio.create_task(self._position_loop())
        )
        self._background_tasks.add(
            asyncio.create_task(self._weather_loop())
        )
        
    async def stop_streaming(self) -> None:
        """Stop all background streaming tasks."""
        self._running = False
        
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
                
        self._background_tasks.clear()
        logger.info("WebSocket data streaming stopped")
        
    async def _heartbeat_loop(self) -> None:
        """Send heartbeat periodically."""
        while self._running:
            try:
                await self.send_heartbeat()
                await asyncio.sleep(self._heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(5)
                
    async def _telemetry_loop(self) -> None:
        """Stream telemetry data for active sessions."""
        while self._running:
            try:
                # Get unique sessions with subscribed clients
                sessions: Dict[int, Set[int]] = {}
                for subscription in self.active_connections.values():
                    if subscription.session_key and "telemetry" in subscription.channels:
                        if subscription.session_key not in sessions:
                            sessions[subscription.session_key] = set()
                        sessions[subscription.session_key].update(subscription.driver_numbers)
                        
                # Stream telemetry for each session
                for session_key, driver_numbers in sessions.items():
                    if driver_numbers:
                        await self.send_telemetry(session_key, list(driver_numbers))
                        
                await asyncio.sleep(self._telemetry_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Telemetry streaming error: {e}")
                await asyncio.sleep(1)
                
    async def _position_loop(self) -> None:
        """Stream position data for active sessions."""
        while self._running:
            try:
                sessions = set()
                for subscription in self.active_connections.values():
                    if subscription.session_key and "positions" in subscription.channels:
                        sessions.add(subscription.session_key)
                        
                for session_key in sessions:
                    await self.send_positions(session_key)
                    
                await asyncio.sleep(self._position_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Position streaming error: {e}")
                await asyncio.sleep(1)
                
    async def _weather_loop(self) -> None:
        """Stream weather data for active sessions."""
        while self._running:
            try:
                sessions = set()
                for subscription in self.active_connections.values():
                    if subscription.session_key and "weather" in subscription.channels:
                        sessions.add(subscription.session_key)
                        
                for session_key in sessions:
                    await self.send_weather(session_key)
                    
                await asyncio.sleep(self._weather_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Weather streaming error: {e}")
                await asyncio.sleep(5)


# Global connection manager instance
connection_manager = ConnectionManager()
