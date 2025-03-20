# app/crud/user.py
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.utils.logger import logger
from app.dependencies.auth import get_password_hash

def create_user(db: Session, user_data: UserCreate, random_id: int):
    # Hash the password
    hashed_password = get_password_hash(user_data.password)
    
    # Create the new user with the random ID
    db_user = User(
        id=random_id,  # Use the generated random ID here
        username=user_data.username,
        email=user_data.email,
        password=hashed_password
    )
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


