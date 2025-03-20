# app/crud/room.py
from sqlalchemy.orm import Session
from app.models.room import ChatRoom
from app.schemas.room import ChatRoomCreate, ChatRoomResponse
from app.utils.logger import logger
from app.models.user import User

# Create a new chat room
def create_chat_room(db: Session, room_data: ChatRoomCreate, creator_id: int):
    new_room = ChatRoom(name=room_data.name, creator_id=creator_id, is_private=room_data.is_private)
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    
    # Add creator to the room
    creator = db.query(User).filter(User.id == creator_id).first()
    new_room.users.append(creator)
    db.commit()
    
    logger.info(f"Chat room created: {new_room.name} (ID: {new_room.id})")
    return new_room

# Get chat room by ID
def get_chat_room(db: Session, room_id: int):
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if room:
        logger.info(f"Fetched chat room: {room.name} (ID: {room.id})")  # Log room fetch
    else:
        logger.warning(f"Chat room with ID {room_id} not found")  # Log warning if room not found
    return room

# Get all chat rooms
def get_chat_rooms(db: Session):
    rooms = db.query(ChatRoom).all()
    logger.info(f"Fetched {len(rooms)} chat rooms")  # Log the number of rooms fetched
    return rooms

# Delete a chat room by ID
def delete_chat_room(db: Session, room_id: int):
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if room:
        db.delete(room)
        db.commit()
        logger.info(f"Deleted chat room: {room.name} (ID: {room.id})")  # Log room deletion
        return room
    logger.warning(f"Chat room with ID {room_id} not found for deletion")  # Log warning if room not found
    return None


def add_user_to_room(db: Session, user_id: int, room_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    
    if not user or not room:
        logger.warning(f"Failed to add user to room: User ID {user_id} or Room ID {room_id} not found")
        return False
    
    if user not in room.users:
        room.users.append(user)
        db.commit()
        logger.info(f"Added user {user.username} to room {room.name}")
    else:
        logger.debug(f"User {user.username} already in room {room.name}")
    
    return True

def remove_user_from_room(db: Session, user_id: int, room_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    
    if not user or not room:
        logger.warning(f"Failed to remove user from room: User ID {user_id} or Room ID {room_id} not found")
        return False
    
    if user in room.users:
        room.users.remove(user)
        db.commit()
        logger.info(f"Removed user {user.username} from room {room.name}")
        return True
    
    logger.debug(f"User {user.username} not in room {room.name}")
    return False
