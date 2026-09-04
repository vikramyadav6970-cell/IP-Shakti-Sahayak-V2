"""
backend/app/config.py

Pydantic-Settings configuration for IP-SAKTI Sahayak backend.
Reads configuration from environment variables and .env file.
"""

from typing import List, Optional, Union
import os
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Authoritative application settings."""

    # Application
    APP_NAME: str = "IP-SAKTI Sahayak API"
    ENVIRONMENT: str = Field(default="development", description="development | staging | production")
    DEBUG: bool = True
    PORT: int = 8000
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ]

    # Database (Supabase / Postgres)
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./test_local.db",
        description="Postgres async connection string: postgresql+asyncpg://...",
    )
    DATABASE_URL_SYNC: Optional[str] = Field(
        default=None,
        description="Postgres sync connection string for Alembic: postgresql://...",
    )

    # Redis (Upstash)
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis connection URL (rediss://...)",
    )

    # Storage (Supabase Storage / S3)
    S3_ENDPOINT: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET: str = "documents"
    S3_REGION: str = "ap-south-1"

    # Security & Auth
    JWT_SECRET: str = Field(
        default="development-secret-key-must-be-changed-in-production-min-32-chars",
        description="JWT secret key for HS256 signing",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Dedicated Master Key for User-Managed External Connector Symmetric Encryption
    ENCRYPTION_MASTER_KEY: Optional[str] = Field(
        default=None,
        description="Dedicated 32+ char key strictly required for encrypting external connector credentials at rest. Must NOT be shared with JWT_SECRET.",
    )

    # Qdrant Vector Store
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None

    # LLM Provider Configuration (dynamically loaded from .env)
    LLM_PROVIDER: str = Field(
        default="gemini",
        description="LLM provider: 'gemini' | 'openai' | 'anthropic' | 'mock'",
    )
    LLM_MODEL: str = Field(
        default="gemini-2.5-flash",
        description="LLM model name (e.g. gemini-2.5-flash, gemini-3.5-flash-lite, gpt-4o, claude-3-5-sonnet)",
    )
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # Translation Provider (Sarvam AI)
    SARVAM_API_KEY: Optional[str] = None
    SARVAM_API_BASE_URL: str = "https://api.sarvam.ai"

    # Hugging Face Hub (Model Weights & Downloads)
    HF_TOKEN: Optional[str] = None

    # Monitoring
    SENTRY_DSN: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=(
            str(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")),
            str(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ai", ".env")),
            str(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backend", ".env")),
            str(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")),
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            v_clean = v.strip()
            if v_clean.startswith("[") and v_clean.endswith("]"):
                import json
                try:
                    return json.loads(v_clean)
                except Exception:
                    pass
            return [i.strip() for i in v_clean.split(",") if i.strip()]
        return v


# Singleton instance
settings = Settings()
