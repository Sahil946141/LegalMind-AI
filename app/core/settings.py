import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import Optional

# Explicitly load .env from the project root
load_dotenv()

class Settings(BaseSettings):
    # Database settings with defaults for development
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "legal_analyzer")
    ENV: str = os.getenv("ENV", "dev")

    # JWT settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Warn if using default JWT secret in production
        if self.JWT_SECRET_KEY == "dev-secret-key-change-in-production" and self.ENV == "prod":
            print("WARNING: Using default JWT secret key in production! Please set JWT_SECRET_KEY in .env")

settings = Settings()