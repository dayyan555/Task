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
