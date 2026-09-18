import os
from typing import List
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Institute Student Development Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    # Security
    SECRET_KEY: str = "isdp-super-secret-key-for-jwt-signing-minimum-32-chars-imrd"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day for development ease
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./isdp_campus.db")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "tauri://localhost"
    ]
    
    # AI Engine
    AI_PROVIDER: str = "local_deterministic"  # local_deterministic, gemini, openai
    AI_MODEL: str = "arohan-bkt-v1"
    AI_API_KEY: str = os.getenv("AI_API_KEY", "mock-key")
    
    # Institutional Default
    INSTITUTION_NAME: str = "Institute of Management Research and Development, Shirpur"
    INSTITUTION_CODE: str = "IMRD"

    model_config = ConfigDict(case_sensitive=True)

settings = Settings()
