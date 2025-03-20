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
