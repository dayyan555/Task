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