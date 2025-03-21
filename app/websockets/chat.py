from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import json
import jwt
from app.db.session import SessionLocal
from app.models.user import User
from app.models.room import ChatRoom
from app.models.message import Message
from app.config import settings
from app.websockets.connection import manager
from app.utils.logger import logger

async def chat_websocket(websocket: WebSocket, room_id: int, token: str = None):
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return
    
    # Authenticate user from token
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=1008, reason="Invalid authentication token")
            return
        
        # Get user and room from database
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == int(user_id)).first()
            room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
            
            if not user or not room:
                await websocket.close(code=1008, reason="User or room not found")
                return
            
            # Check if user is in the room
            if user not in room.users:
                await websocket.close(code=1008, reason="Access denied: You are not a member of this room")
                return
            
            # Accept the connection and add to connection manager
            await manager.connect(websocket, room_id, user.id)
            
            try:
                while True:
                    # Receive and process messages
                    data = await websocket.receive_text()
                    message_data = json.loads(data)

                    message_text = message_data.get("text")
                    
                    # Process message based on type
                    if not message_text:
                        continue
                    # Create and save message to database
                    new_message = Message(
                        text=message_data.get("text"),
                        sender_id=user.id,
                        room_id=room_id,
                        created_at=datetime.utcnow()
                    )
                    db.add(new_message)
                    db.commit()
                    db.refresh(new_message)
                    
                    # Broadcast message to all users in the room
                    await manager.broadcast_message({
                        "type": "new_message",
                        "id": new_message.id,
                        "text": new_message.text,
                        "sender_id": new_message.sender_id,
                        "sender_username": user.username,
                        "room_id": new_message.room_id,
                        "created_at": new_message.created_at.isoformat()
                    }, room_id)
                    
                    
                
            except WebSocketDisconnect:
                # Handle disconnection
                manager.disconnect(websocket, room_id, user.id)
                logger.info(f"User {user.username} disconnected from room {room.name}")
            
        finally:
            db.close()
    
    except jwt.PyJWTError:
        await websocket.close(code=1008, reason="Invalid authentication token")
        logger.warning("WebSocket connection rejected: Invalid token")
        return