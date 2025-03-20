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
