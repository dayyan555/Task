# app/models/room_users.py
from sqlalchemy import Table, Column, Integer, ForeignKey
from app.db.session import Base

room_users = Table(
    "room_users",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("room_id", Integer, ForeignKey("chat_rooms.id", ondelete="CASCADE"), primary_key=True),
)
