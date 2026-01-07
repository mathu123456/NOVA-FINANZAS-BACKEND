from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Database - Supabase PostgreSQL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:1062809468Ma@db.uenzpicclhiesyrejkmt.supabase.co:5432/postgres"
    )
    
    # Security
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "nova-finanzas-2024-secure-jwt-secret-key-min-32-chars"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 días
    
    # Application
    APP_NAME: str = "Nova Finanzas"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]  # En producción usar dominios específicos
    
    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://remarkable-travesseiro-6c06c6.netlify.app/")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()