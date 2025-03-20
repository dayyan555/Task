import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app import crud, schemas
from app.db.session import SessionLocal
from app.config import settings
from app.models.user import User
from passlib.context import CryptContext
from app.utils.logger import logger
from app.db.session import get_db

# Initialize JWT and password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2PasswordBearer is used to get the token from the request's Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# JWT token expiration time
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Token will expire in 30 minutes

# Secret key for JWT encoding and decoding
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


# Function to verify the password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Function to hash the password
def get_password_hash(password):
    return pwd_context.hash(password)


# Function to create a JWT token
def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=settings.ALGORITHM)
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
