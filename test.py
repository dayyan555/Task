# Project Structure
# chat_app/
# ├── app/
# │   ├── api/
# │   │   ├── __init__.py
# │   │   ├── auth.py
# │   │   └── chat.py
# │   ├── crud/
# │   │   ├── __init__.py
# │   │   ├── message.py
# │   │   ├── room.py
# │   │   └── user.py
# │   ├── db/
# │   │   ├── __init__.py
# │   │   └── session.py
# │   ├── dependencies/
# │   │   ├── __init__.py
# │   │   └── auth.py
# │   ├── models/
# │   │   ├── __init__.py
# │   │   ├── message.py
# │   │   ├── room.py
# │   │   ├── room_users.py
# │   │   └── user.py
# │   ├── schemas/
# │   │   ├── __init__.py
# │   │   ├── auth.py
# │   │   ├── message.py
# │   │   ├── room.py
# │   │   ├── user.py
# │   │   └── websocket.py
# │   ├── utils/
# │   │   ├── __init__.py
# │   │   └── logger.py
# │   ├── websockets/
# │   │   ├── __init__.py
# │   │   ├── chat.py
# │   │   └── connection.py
# │   ├── __init__.py
# │   └── config.py
# ├── .env
# └── main.py

# app/config.py
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    APP_NAME: str = "Chat Application"
    APP_VERSION: str = "1.0.0"
    DB_URL: str = "mysql://root:chatdb@localhost:3306/chatdb"
    SECRET_KEY: str = "chat_app"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALLOWED_ORIGINS: str = "*"

    class Config:
        env_file = ".env"

settings = Settings()

# app/utils/logger.py
import logging

def setup_logger():
    logger = logging.getLogger("chat-app")
    logger.setLevel(logging.DEBUG)
    
    # Create console handler for logging to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    # Create formatter to format the log messages
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Add the handler to the logger
    logger.addHandler(console_handler)
    
    return logger

# Initialize logger
logger = setup_logger()

# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Database URL to connect to MySQL running in Docker container
DATABASE_URL = settings.DB_URL

# Create engine and session
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# app/models/room_users.py
from sqlalchemy import Table, Column, Integer, ForeignKey
from app.db.session import Base

room_users = Table(
    "room_users",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("room_id", Integer, ForeignKey("chat_rooms.id", ondelete="CASCADE"), primary_key=True),
)

# app/models/user.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.room_users import room_users

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    password = Column(String(255))

    messages = relationship("Message", back_populates="sender")
    rooms = relationship("ChatRoom", secondary=room_users, back_populates="users")

# app/models/room.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.room_users import room_users

class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    creator_id = Column(Integer, ForeignKey("users.id"))
    is_private = Column(Boolean, default=False)

    users = relationship("User", secondary=room_users, back_populates="rooms")
    messages = relationship("Message", back_populates="room")
    creator = relationship("User", foreign_keys=[creator_id])

# app/models/message.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String(1000))
    sender_id = Column(Integer, ForeignKey("users.id"))
    room_id = Column(Integer, ForeignKey("chat_rooms.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", back_populates="messages")
    room = relationship("ChatRoom", back_populates="messages")

# app/schemas/user.py
from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True  # Tells Pydantic to treat SQLAlchemy models as dicts

# app/schemas/auth.py
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

    class Config:
        orm_mode = True

# app/schemas/room.py
from pydantic import BaseModel
from typing import List, Optional
from app.schemas.user import UserResponse

class ChatRoomCreate(BaseModel):
    name: str
    is_private: Optional[bool] = False  # Default to False (public room)

class ChatRoomResponse(BaseModel):
    id: int
    name: str
    creator_id: int
    is_private: bool
    users: List[UserResponse]  # List of usernames in the room

    class Config:
        orm_mode = True  # Tells Pydantic to treat SQLAlchemy models as dicts

# app/schemas/message.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MessageCreate(BaseModel):
    text: str

class MessageResponse(BaseModel):
    id: int
    text: str
    sender_id: int
    room_id: int
    created_at: datetime

    class Config:
        orm_mode = True  # Tells Pydantic to treat SQLAlchemy models as dicts

# app/schemas/websocket.py
from pydantic import BaseModel
from typing import Optional

class WSMessage(BaseModel):
    type: str
    text: Optional[str] = None
    is_typing: Optional[bool] = None

# app/dependencies/auth.py
import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from passlib.context import CryptContext
from app.utils.logger import logger
from app.config import settings

# Initialize JWT and password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2PasswordBearer is used to get the token from the request's Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# Function to verify the password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Function to hash the password
def get_password_hash(password):
    return pwd_context.hash(password)

# Function to create a JWT token
def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# Function to authenticate the user (login)
def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        logger.warning(f"Authentication failed: User '{username}' not found")
        return None
    if not verify_password(password, user.password):
        logger.warning(f"Authentication failed: Invalid password for user '{username}'")
        return None
    logger.info(f"User authenticated successfully: {username}")
    return user

# Dependency: Get the current user from the JWT token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            logger.warning("Token validation failed: Missing user ID")
            raise credentials_exception
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            logger.warning(f"Token validation failed: User ID {user_id} not found")
            raise credentials_exception
        logger.debug(f"User authenticated via token: {user.username}")
        return user
    except jwt.PyJWTError:
        logger.warning("Token validation failed: JWT error")
        raise credentials_exception

# app/websockets/connection.py
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

# app/websockets/chat.py
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
            if room.is_private and user not in room.users:
                await websocket.close(code=1008, reason="Not authorized to join this room")
                return
            
            # Accept the connection and add to connection manager
            await manager.connect(websocket, room_id, user.id)
            
            try:
                while True:
                    # Receive and process messages
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    # Process message based on type
                    if message_data.get("type") == "chat_message":
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
                    
                    elif message_data.get("type") == "typing":
                        # Broadcast typing indicator
                        await manager.broadcast_message({
                            "type": "typing",
                            "user_id": user.id,
                            "username": user.username,
                            "room_id": room_id,
                            "is_typing": message_data.get("is_typing", False)
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

# app/crud/user.py
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.utils.logger import logger
from app.dependencies.auth import get_password_hash

def create_user(db: Session, user_data: UserCreate):
    hashed_password = get_password_hash(user_data.password)  # Hash the password
    db_user = User(username=user_data.username, email=user_data.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"User created: {db_user.username} (ID: {db_user.id})")  # Log user creation
    return db_user

# Get user by ID
def get_user(db: Session, user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        logger.info(f"Fetched user: {db_user.username} (ID: {db_user.id})")  # Log user fetch
    else:
        logger.warning(f"User with ID {user_id} not found")  # Log warning if user not found
    return db_user

# Get all users
def get_all_users(db: Session):
    db_users = db.query(User).all()
    logger.info(f"Fetched {len(db_users)} users")  # Log the number of users fetched
    return db_users

# Delete user by ID
def delete_user(db: Session, user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        logger.info(f"Deleted user: {db_user.username} (ID: {db_user.id})")  # Log user deletion
        return db_user
    logger.warning(f"User with ID {user_id} not found for deletion")  # Log warning if user not found
    return None

# app/crud/room.py
from sqlalchemy.orm import Session
from app.models.room import ChatRoom
from app.models.user import User
from app.schemas.room import ChatRoomCreate, ChatRoomResponse
from app.utils.logger import logger

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

# app/crud/message.py
from sqlalchemy.orm import Session
from app.models.message import Message
from app.schemas.message import MessageCreate, MessageResponse
from app.utils.logger import logger

# Create a new message in a chat room
def create_message(db: Session, message_data: MessageCreate, room_id: int, sender_id: int):
    new_message = Message(text=message_data.text, room_id=room_id, sender_id=sender_id)
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    logger.info(f"Message created in room ID {room_id} by user ID {sender_id}")
    logger.debug(f"Message content: {new_message.text[:50]}...")
    return new_message

# Get all messages in a chat room
def get_messages(db: Session, room_id: int, limit: int = 100):
    messages = db.query(Message).filter(Message.room_id == room_id).order_by(Message.created_at.desc()).limit(limit).all()
    messages.reverse()  # Return in chronological order
    logger.debug(f"Fetched {len(messages)} messages from room ID {room_id}")
    return messages

# Delete a message by ID
def delete_message(db: Session, message_id: int):
    message = db.query(Message).filter(Message.id == message_id).first()
    if message:
        db.delete(message)
        db.commit()
        logger.info(f"Deleted message ID {message.id} from room ID {message.room_id}")
        return message
    logger.warning(f"Message with ID {message_id} not found for deletion")
    return None

# app/api/auth.py
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import LoginRequest, Token
from app.db.session import get_db
from app.dependencies.auth import create_access_token, get_current_user, authenticate_user
from app.models.user import User
from app.crud.user import create_user
from app.utils.logger import logger
from app.config import settings
from datetime import timedelta

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        logger.warning(f"Registration failed: Username '{user_data.username}' already exists")
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        logger.warning(f"Registration failed: Email '{user_data.email}' already exists")
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create new user
    new_user = create_user(db, user_data)
    return new_user

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: LoginRequest, db: Session = Depends(get_db)):
    # Authenticate user
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Login failed: Invalid credentials for username '{form_data.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate the access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    logger.info(f"User '{user.username}' logged in successfully")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # This is a stateless JWT-based auth, so actual logout is handled client-side
    # by removing the token. Server-side we just log the event.
    logger.info(f"User '{current_user.username}' logged out")
    return {"detail": "Successfully logged out"}

# app/api/chat.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import asyncio
from app.schemas.room import ChatRoomCreate, ChatRoomResponse
from app.schemas.message import MessageCreate, MessageResponse
from app.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.room import ChatRoom
from app.crud.room import create_chat_room, get_chat_room, get_chat_rooms, add_user_to_room, remove_user_from_room
from app.crud.message import create_message, get_messages
from app.websockets.connection import manager
from app.utils.logger import logger

router = APIRouter()

@router.get("/rooms", response_model=List[ChatRoomResponse])
async def get_all_chat_rooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rooms = get_chat_rooms(db)
    return rooms

@router.post("/rooms", response_model=ChatRoomResponse)
async def create_room(
    room_data: ChatRoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_room = create_chat_room(db, room_data, current_user.id)
    return new_room

@router.get("/rooms/{room_id}", response_model=ChatRoomResponse)
async def get_room_details(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    room = get_chat_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Check if user has access to private room
    if room.is_private and current_user not in room.users:
        raise HTTPException(status_code=403, detail="Not authorized to access this room")
    
    return room

@router.post("/rooms/{room_id}/join")
async def join_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    room = get_chat_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Check if room is private and user is not already a member
    if room.is_private and current_user not in room.users:
        raise HTTPException(status_code=403, detail="Not authorized to join this private room")
    
    success = add_user_to_room(db, current_user.id, room_id)
    if success:
        return {"detail": f"Joined room: {room.name}"}
    
    raise HTTPException(status_code=400, detail="Failed to join room")

@router.post("/rooms/{room_id}/leave")
async def leave_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    room = get_chat_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Check if user is in the room
    if current_user not in room.users:
        raise HTTPException(status_code=400, detail="You are not a member of this room")
    
    # Don't allow the creator to leave their own room
    if room.creator_id == current_user.id:
        raise HTTPException(status_code=400, detail="Room creator cannot leave. Delete the room instead.")
    
    success = remove_user_from_room(db, current_user.id, room_id)
    if success:
        return {"detail": f"Left room: {room.name}"}
    
    raise HTTPException(status_code=400, detail="Failed to leave room")

@router.get("/rooms/{room_id}/messages", response_model=List[MessageResponse])
async def get_room_messages(
    room_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    room = get_chat_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Check if user has access to this room
    if room.is_private and current_user not in room.users:
        raise HTTPException(status_code=403, detail="Not authorized to access messages in this room")
    
    messages = get_messages(db, room_id, limit)
    return messages

@router.get("/rooms/{room_id}/users")
async def get_room_users(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    room = get_chat_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Check if user has access to this room
    if room.is_private and current_user not in room.users:
        raise HTTPException(status_code=403, detail="Not authorized to access this room")
    
    # Get active users in the room
    active_users = manager.get_active_users(room_id)
    
    # Prepare response with all room users and their online status
    users_data = []
    for user in room.users:
        users_data.append({
            "id": user.id,
            "username": user.username,
            "is_online": user.id in active_users
        })
    
    return {"users": users_data}

# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, chat
from app.websockets.chat import chat_websocket
from app.db.session import Base, engine
from app.config import settings
from app.utils.logger import logger

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])

# WebSocket endpoint for chat
@app.websocket("/ws/chat/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    room_id: int, 
    token: str = Query(None)
):
    await chat_websocket(websocket, room_id, token)

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.APP_NAME}")