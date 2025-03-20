# app/api/auth.py
from fastapi import APIRouter, HTTPException, status, Depends, Response
from sqlalchemy.orm import Session
from app.crud.user import create_user, delete_user
from app.db.session import get_db
from app.dependencies.auth import create_access_token, get_current_user, authenticate_user
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import LoginRequest, Token
from datetime import timedelta
import random
from app.utils.logger import logger
from app.config import settings

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Generate a random 4-digit ID for the user
    random_id = random.randint(1000, 9999)
    logger.info(f"Generated random 4-digit ID: {random_id} for user {user_data.username}")

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
    
    # Create new user with the random ID
    new_user = create_user(db, user_data, random_id)  # Pass the random ID to create_user
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

@router.delete("/delete", response_model=str)
async def delete_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Call the function to delete the user
    deleted_user = delete_user(db, current_user.id)
    
    if deleted_user:
        logger.info(f"User '{current_user.username}' has been deleted")
        return {"detail": f"User '{current_user.username}' deleted successfully"}
    else:
        logger.warning(f"Attempted to delete user '{current_user.username}', but user was not found.")
        raise HTTPException(status_code=404, detail="User not found")