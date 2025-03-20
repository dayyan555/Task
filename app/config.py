
#app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database Configuration
    DB_URL: str

    # Security Settings
    SECRET_KEY: str

    # CORS Configuration
    ALLOWED_ORIGINS: str = "*"

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # FastAPI Application Settings
    APP_NAME: str = "Chat Application"
    APP_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"

# Initialize settings
settings = Settings()

print(f"DB_URL: {settings.DB_URL}")
print(f"SECRET_KEY: {settings.SECRET_KEY}")
print(f"ALLOWED_ORIGINS: {settings.ALLOWED_ORIGINS}")
print(f"APP_NAME: {settings.APP_NAME}")
print(f"APP_VERSION: {settings.APP_VERSION}")
