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