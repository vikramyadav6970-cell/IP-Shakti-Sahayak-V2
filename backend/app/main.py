"""
backend/app/main.py

FastAPI application entrypoint for IP-SAKTI Sahayak (v2.1 Speech Sanitized).
"""

import os
from contextlib import asynccontextmanager
from typing import Any, Dict
from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middleware.rate_limit import RateLimitMiddleware

# HF Hub Token configuration for models & embeddings
if settings.HF_TOKEN:
    os.environ["HF_TOKEN"] = settings.HF_TOKEN
    os.environ["HUGGINGFACE_HUB_TOKEN"] = settings.HF_TOKEN

# Sentry Monitoring Initialization
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            environment=settings.ENVIRONMENT,
        )
    except Exception as e:
        print(f"Sentry init notice: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    try:
        from app.database import engine
        from app.models.base import Base

        async with engine.connect() as conn:
            try:
                await conn.run_sync(Base.metadata.create_all)
                await conn.commit()
            except Exception as dbe:
                await conn.rollback()
                print(f"[Lifespan Schema Init Notice]: {dbe}")

            # Safe column additions for PostgreSQL / SQLite with independent transactions
            for stmt in [
                "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS product_context_json JSONB;",
                "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS classification_state VARCHAR(50) DEFAULT 'COLLECTING_PRODUCT_INFORMATION';",
            ]:
                try:
                    await conn.execute(text(stmt))
                    await conn.commit()
                except Exception:
                    await conn.rollback()
        # Check Embedding Provider Configuration
        embedding_prov = (os.environ.get("EMBEDDING_PROVIDER") or "bge-m3").lower()
        if embedding_prov in ["mock", "test"] and settings.ENVIRONMENT != "test":
            print("\n" + "!" * 80)
            print(" ⚠️  CRITICAL CONFIGURATION WARNING: RUNNING WITH MOCK EMBEDDINGS!")
            print(" Vector searches against Qdrant will use synthetic hash vectors and produce 0 hits.")
            print(" To enable real AI vector retrieval, set EMBEDDING_PROVIDER=bge-m3 in your .env file.")
            print("!" * 80 + "\n")
        else:
            print("\n" + "=" * 80)
            print(" [AI RUNTIME READY] Dense Embeddings: BAAI/bge-m3 (1024-dim) | Qdrant: Connected")
            print("=" * 80 + "\n")
            # Pre-warm embedding model and Qdrant client in memory
            try:
                from app.services.chat_service import get_shared_retriever
                _retriever = get_shared_retriever()
                _ = _retriever.dense_provider.embed("Warmup query embedding for pre-loading weights")
                print(" [AI RUNTIME READY] Embedding model & vector retriever pre-warmed successfully in memory.")
            except Exception as e_warm:
                print(f"[AI Pre-warm Notice]: {e_warm}")
    except Exception as e:
        print(f"[Lifespan Startup Notice]: {e}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for IP-SAKTI Sahayak (SIH 2026 Problem Statement 26045)",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Mount Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware, max_requests_per_minute=120)

# Configure CORS (Support all Vercel domains, Render domains, local ports, and configured origins)
cors_origins_list = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list,
    allow_origin_regex=r"https://.*\.vercel\.app|https://.*\.onrender\.com|http://localhost:\d+|http://127\.0\.0\.1:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", status_code=status.HTTP_200_OK, tags=["System"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint returning system status and service connectivity info.
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "database": "configured" if settings.DATABASE_URL else "unconfigured",
        "redis": "configured" if settings.REDIS_URL else "unconfigured",
        "storage": "configured" if settings.S3_ENDPOINT else "local_or_unconfigured",
        "llm_provider": settings.LLM_PROVIDER,
        "qdrant": "configured" if settings.QDRANT_URL else "unconfigured",
    }


@app.get("/health/ready", status_code=status.HTTP_200_OK, tags=["System"])
async def readiness_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Readiness probe verifying live database connection.
    """
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ready" if db_status == "connected" else "degraded",
        "database": db_status,
        "environment": settings.ENVIRONMENT,
    }


# Import and mount /api/v1 router
from app.api.v1.router import api_v1_router
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/", tags=["System"])
async def root() -> Dict[str, str]:
    return {
        "message": "IP-SAKTI Sahayak API is operational",
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else "disabled",
    }
