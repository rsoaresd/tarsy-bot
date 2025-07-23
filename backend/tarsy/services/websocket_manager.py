"""
WebSocket manager for real-time progress updates.
"""

import json
from datetime import datetime
from typing import Dict, List

from fastapi import WebSocket

from tarsy.models.alert import ProcessingStatus


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Dictionary to store active connections by alert_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    def _datetime_serializer(self, obj):
        """Custom JSON serializer for datetime objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    async def connect(self, websocket: WebSocket, alert_id: str):
        """Connect a WebSocket for a specific alert."""
        await websocket.accept()
        
        if alert_id not in self.active_connections:
            self.active_connections[alert_id] = []
        
        self.active_connections[alert_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, alert_id: str):
        """Disconnect a WebSocket."""
        if alert_id in self.active_connections:
            if websocket in self.active_connections[alert_id]:
                self.active_connections[alert_id].remove(websocket)
            
            # Clean up empty lists
            if not self.active_connections[alert_id]:
                del self.active_connections[alert_id]
    
    async def send_status_update(self, alert_id: str, status: ProcessingStatus):
        """Send status update to all connected clients for an alert."""
        if alert_id not in self.active_connections:
            return
        
        # Prepare message with datetime serialization
        message = {
            "type": "status_update",
            "data": status.model_dump()
        }
        message_json = json.dumps(message, default=self._datetime_serializer)
        
        # Send to all connected clients for this alert
        disconnected = []
        for websocket in self.active_connections[alert_id]:
            try:
                await websocket.send_text(message_json)
            except Exception:
                # Mark for removal if connection is broken
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket, alert_id)
    
    async def send_message(self, alert_id: str, message: dict):
        """Send a custom message to all connected clients for an alert."""
        if alert_id not in self.active_connections:
            return
        
        message_json = json.dumps(message, default=self._datetime_serializer)
        
        # Send to all connected clients for this alert
        disconnected = []
        for websocket in self.active_connections[alert_id]:
            try:
                await websocket.send_text(message_json)
            except Exception:
                # Mark for removal if connection is broken
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket, alert_id) 