"""
backend/app/api/v1/classification.py

Product classification wizard API endpoint.
"""

from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.entities import User
from app.schemas.classification import ClassificationResponse, FormulationCreate
from app.security.dependencies import get_current_user
from app.services.classification_service import ClassificationService

router = APIRouter(prefix="/classification", tags=["Product Classification"])


@router.post(
    "",
    response_model=ClassificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Classify Ayurvedic formulation and generate IP protection map",
)
async def classify_product(
    req: FormulationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Applies deterministic rules tree across ASU drugs, Ayurveda-Aahara, and phytopharmaceuticals.
    Returns regulatory pathway, fired rules audit trail, and IP recommendations.
    """
    service = ClassificationService(db)
    return await service.classify_product(req, current_user=current_user)
