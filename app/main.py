# app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, chat
from app.websockets.chat import chat_websocket
from app.db.session import Base, engine
from app.config import settings
from app.utils.logger import logger

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app instance
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)

# CORS configuration
origins = [
    settings.ALLOWED_ORIGINS,  # You can specify a list of allowed origins
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Allow all headers
)

# Include API routers
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])

# WebSocket endpoint
@app.websocket("/ws/chat/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int, token: str = None):
    await chat_websocket(websocket, room_id, token=token)

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the Chat Application API", "version": settings.APP_VERSION}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Run the application
if __name__ == "__main__":
    import uvicorn
    import asyncio
    
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)