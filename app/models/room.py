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

    users = relationship("User", secondary=room_users, back_populates="rooms")
    messages = relationship("Message", back_populates="room")
    creator = relationship("User", foreign_keys=[creator_id])