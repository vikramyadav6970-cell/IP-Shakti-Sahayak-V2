"""
backend/app/api/v1/router.py

Aggregates and mounts all API v1 domain sub-routers.
"""

from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.documents import router as documents_router
from app.api.v1.chat import router as chat_router
from app.api.v1.classification import router as classification_router
from app.api.v1.abs import router as abs_router
from app.api.v1.ip import router as ip_router
from app.api.v1.sources import router as sources_router
from app.api.v1.expert import router as expert_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(classification_router)
api_v1_router.include_router(abs_router)
api_v1_router.include_router(ip_router)
api_v1_router.include_router(sources_router)
api_v1_router.include_router(expert_router)


@api_v1_router.get("/ping", tags=["Health"])
async def ping():
    return {"status": "pong", "version": "v1"}
