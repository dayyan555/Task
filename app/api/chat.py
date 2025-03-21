#app/api/chat.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import random
import asyncio
from app.schemas.room import ChatRoomCreate, ChatRoomResponse
from app.schemas.message import MessageCreate, MessageResponse
from app.schemas.user import UserResponse
from app.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.room import ChatRoom
from app.crud.room import create_chat_room, get_chat_room, get_chat_rooms, add_user_to_room, remove_user_from_room
from app.crud.message import create_message, get_messages
from app.websockets.connection import manager
from app.utils.logger import logger
from app.utils.utils import create_json_response
import json

router = APIRouter()

@router.get("/rooms", response_model=List[ChatRoomResponse])
async def get_all_chat_rooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rooms = get_chat_rooms(db)
    if not rooms:
        raise HTTPException(status_code=404, detail="No chat rooms found.")
    
    return rooms
    

@router.post("/rooms", response_model=ChatRoomResponse)
async def create_room(
    room_data: ChatRoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    random_id = random.randint(1000, 9999)
    logger.info(f"Generated random 4-digit ID: {random_id} for room.")
    new_room = create_chat_room(db, room_data, current_user.id, random_id)
    print("new room", new_room.name)
    return new_room


@router.get("/rooms/{room_id}", response_model=ChatRoomResponse)
async def get_room_details(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    room = get_chat_room(db, room_id)
    if not room:
        return create_json_response(False, "Chat room not found", status_code=404)
    
    # Check if user has access to the room
    if current_user not in room.users:
        logger.warning(f"Access denied: User {current_user.username} attempted to access room {room.name} they are not a member of.")
        return create_json_response(False, "Access denied: You are not a member of this room", status_code=403)
    
    return room

@router.post("/rooms/{room_id}/join")
async def join_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    room = get_chat_room(db, room_id)
    if not room:
        raise create_json_response(False, "Room not found", status_code=404)
    
    # Check if room is private and user is not already a member
    if current_user in room.users:
        return create_json_response(False, "You are already a member of this room", status_code=400)

    
    success = add_user_to_room(db, current_user.id, room_id)
    if success:
        return create_json_response(True, f"Successfully joined room: {room.name}", data={"room_id": room.id, "room_name": room.name})
    
    return create_json_response(False, "Failed to join room", status_code=400)


@router.post("/rooms/{room_id}/leave")
async def leave_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    room = get_chat_room(db, room_id)
    if not room:
         return create_json_response(False, "Room not found", status_code=404)
    
    # Check if user is in the room
    if current_user not in room.users:
        return create_json_response(False, "You are not a member of this room", status_code=400)
    
    # Don't allow the creator to leave their own room
    if room.creator_id == current_user.id:
        return create_json_response(False, "Room creator cannot leave. Delete the room instead.", status_code=400)
    
    success = remove_user_from_room(db, current_user.id, room_id)
    if success:
        return create_json_response(True, f"Successfully left room: {room.name}", data={"room_id": room.id, "room_name": room.name})
    
    return create_json_response(False, "Failed to leave room", status_code=400)


@router.get("/rooms/{room_id}/users")
async def get_room_users(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    room = get_chat_room(db, room_id)
    if not room:
        return create_json_response(False, "Room not found", status_code=404)
    
    if current_user not in room.users:
        logger.warning(f"Access denied: User {current_user.username} attempted to access room {room.name} they are not a member of.")
        return create_json_response(False, "Access denied: You are not a member of this room", status_code=403)
    
    # Get active users in the room
    active_users = manager.get_active_users(room_id)
    
    # Prepare response with all room users and their online status
    users_data = [
        {"id": user.id, "username": user.username, "is_online": user.id in active_users} for user in room.users
    ]
    
    return create_json_response(True, "Room users successfully retrieved.", data={"users": users_data})


@router.get("/rooms/{room_id}/messages", response_model=List[MessageResponse])
async def get_room_messages(
    room_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if room exists
    room = get_chat_room(db, room_id)
    if not room:
        return create_json_response(False, "Room not found", status_code=404)
    

    if current_user not in room.users:
        logger.warning(f"Access denied: User {current_user.username} attempted to access room {room.name} they are not a member of.")
        return create_json_response(False, "Access denied: You are not a member of this room", status_code=403)
    
    
    messages = get_messages(db, room_id, limit)
    return messages

# @app.post("/api/chat/rooms/{room_id}/messages", response_model=MessageResponse)
# async def send_message(
#     room_id: int,
#     message_data: MessageCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     # Check if room exists
#     room = get_chat_room(db, room_id)
#     if not room:
#         raise HTTPException(status_code=404, detail="Chat room not found")
    
#     # Check if user is in room
#     if current_user not in room.users:
#         logger.warning(f"Access denied: User {current_user.username} attempted to send message to room {room.name}")
#         raise HTTPException(status_code=403, detail="You must join the room to send messages")
    
#     # Create the message
#     new_message = create_message(db, message_data, room_id, current_user.id)
    
#     # Broadcast to WebSocket clients if any
#     message_dict = {
#         "type": "new_message",
#         "id": new_message.id,
#         "text": new_message.text,
#         "sender_id": new_message.sender_id,
#         "sender_username": current_user.username,
#         "room_id": new_message.room_id,
#         "created_at": new_message.created_at.isoformat()
#     }
    
#     # Using asyncio.create_task to avoid waiting for the broadcast to complete
#     import asyncio
#     asyncio.create_task(manager.broadcast_message(message_dict, room_id))
    
#     return new_message



# @app.post("/api/chat/rooms/{room_id}/join")
# async def join_room(
#     room_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     # Check if room exists
#     room = get_chat_room(db, room_id)
#     if not room:
#         raise HTTPException(status_code=404, detail="Chat room not found")
    
#     # Add user to room
#     success = add_user_to_room(db, current_user.id, room_id)
#     if success:
#         return {"detail": f"Successfully joined room: {room.name}"}
#     return {"detail": "Already in this room"}

# @app.post("/api/chat/rooms/{room_id}/leave")
# async def leave_room(
#     room_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     # Check if room exists
#     room = get_chat_room(db, room_id)
#     if not room:
#         raise HTTPException(status_code=404, detail="Chat room not found")
    
#     # Remove user from room
#     success = remove_user_from_room(db, current_user.id, room_id)
#     if success:
#         return {"detail": f"Successfully left room: {room.name}"}
#     return {"detail": "Not in this room"}

# @app.websocket("/ws/chat/{room_id}")
# async def websocket_endpoint(websocket: WebSocket, room_id: int, token: str = None):
#     if not token:
#         await websocket.close(code=1008, reason="Missing authentication token")
#         return
    
#     # Authenticate user from token
#     try:
#         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
#         user_id = payload.get("sub")
#         if not user_id:
#             await websocket.close(code=1008, reason="Invalid authentication token")
#             return
        
#         # Get user and room from database
#         db = SessionLocal()
#         try:
#             user = db.query(User).filter(User.id == int(user_id)).first()
#             room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
            
#             if not user or not room:
#                 await websocket.close(code=1008, reason="User or room not found")
#                 return
            
#             # Check if user is in the room
#             if room.is_private and user not in room.users:
#                 await websocket.close(code=1008, reason="Not authorized to join this room")
#                 return
            
#             # Accept the connection and add to connection manager
#             await manager.connect(websocket, room_id, user.id)
            
#             try:
#                 while True:
#                     # Receive and process messages
#                     data = await websocket.receive_text()
#                     message_data = json.loads(data)
                    
#                     # Process message based on type
#                     if message_data.get("type") == "chat_message":
#                         # Create and save message to database
#                         new_message = Message(
#                             text=message_data.get("text"),
#                             sender_id=user.id,
#                             room_id=room_id,
#                             created_at=datetime.utcnow()
#                         )
#                         db.add(new_message)
#                         db.commit()
#                         db.refresh(new_message)
                        
#                         # Broadcast message to all users in the room
#                         await manager.broadcast_message({
#                             "type": "new_message",
#                             "id": new_message.id,
#                             "text": new_message.text,
#                             "sender_id": new_message.sender_id,
#                             "sender_username": user.username,
#                             "room_id": new_message.room_id,
#                             "created_at": new_message.created_at.isoformat()
#                         }, room_id)
                    
#                     elif message_data.get("type") == "typing":
#                         # Broadcast typing indicator
#                         await manager.broadcast_message({
#                             "type": "typing",
#                             "user_id": user.id,
#                             "username": user.username,
#                             "room_id": room_id,
#                             "is_typing": message_data.get("is_typing", False)
#                         }, room_id)
                
#             except WebSocketDisconnect:
#                 # Handle disconnection
#                 manager.disconnect(websocket, room_id, user.id)
#                 logger.info(f"User {user.username} disconnected from room {room.name}")
            
#         finally:
#             db.close()
    
#     except jwt.PyJWTError:
#         await websocket.close(code=1008, reason="Invalid authentication token")
#         logger.warning("WebSocket connection rejected: Invalid token")
#         return