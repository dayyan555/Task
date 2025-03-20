from fastapi import WebSocket
from typing import Dict, List, Set
from datetime import datetime
import logging
import asyncio
import json

# Configure logging
logger = logging.getLogger("chat_app.websocket")

class ConnectionManager:
    def __init__(self):
        # active_connections[room_id] = list of websocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # user_connections[user_id] = list of websocket connections
        self.user_connections: Dict[int, List[WebSocket]] = {}
        # Set to track active users in each room
        self.active_users: Dict[int, Set[int]] = {}
        
    async def connect(self, websocket: WebSocket, room_id: int, user_id: int):
        await websocket.accept()
        
        # Initialize room connections if not exists
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
            self.active_users[room_id] = set()
            
        # Add connection to room
        self.active_connections[room_id].append(websocket)
        
        # Add to user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)
        
        # Add user to active users in this room
        self.active_users[room_id].add(user_id)
        
        logger.info(f"User {user_id} connected to room {room_id}")
        logger.debug(f"Room {room_id} has {len(self.active_connections[room_id])} connections")
        
        # Announce user joined room
        await self.broadcast_user_activity(room_id, user_id, action="joined")
        
    def disconnect(self, websocket: WebSocket, room_id: int, user_id: int):
        # Remove from room connections
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
                logger.info(f"User {user_id} disconnected from room {room_id}")
        
        # Remove from user connections
        if user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
                if len(self.user_connections[user_id]) == 0:
                    del self.user_connections[user_id]
                    
                    # Remove user from active users in this room
                    if room_id in self.active_users and user_id in self.active_users[room_id]:
                        self.active_users[room_id].remove(user_id)
                    
                    # Announce user left room
                    asyncio.create_task(self.broadcast_user_activity(room_id, user_id, action="left"))
    
    async def broadcast_message(self, message: dict, room_id: int):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting message: {str(e)}")
    
    async def broadcast_user_activity(self, room_id: int, user_id: int, action: str):
        """Broadcast user activity (joined/left) to all users in a room"""
        message = {
            "type": "user_activity",
            "user_id": user_id,
            "action": action,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_message(message, room_id)
    
    def get_active_users(self, room_id: int) -> List[int]:
        """Get list of active user IDs in a room"""
        if room_id in self.active_users:
            return list(self.active_users[room_id])
        return []

# Initialize connection manager (singleton instance)
manager = ConnectionManager()