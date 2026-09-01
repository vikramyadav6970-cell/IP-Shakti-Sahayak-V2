"""
backend/app/api/v1/abs.py

ABS compliance assessment endpoints.
"""

import sys
from pathlib import Path
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure AI path is accessible
ai_path = str(Path(__file__).resolve().parent.parent.parent.parent / "ai")
if ai_path not in sys.path:
    sys.path.insert(0, ai_path)

from src.abs.abs_engine import ABSEngine, ABSInput
from app.database import get_db
from app.models.entities import ABSAssessment, User
from app.schemas.ip_abs import ABSAssessmentRequest, ABSAssessmentResponse
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/abs", tags=["Access and Benefit Sharing"])


@router.post(
    "",
    response_model=ABSAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate ABS compliance under Biological Diversity Act",
)
async def evaluate_abs(
    req: ABSAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluates entity nationality and activity type to determine Form I / Form II / Form III
    or SBB prior intimation requirements under the Biological Diversity Act 2002 & 2023.
    """
    ai_input = ABSInput(
        entity_nationality=req.entity_nationality,
        biological_resources=req.biological_resources,
        resource_origin=req.resource_origin,
        activity_type=req.activity_type,
        is_ayush_practitioner=req.is_ayush_practitioner,
        is_codified_traditional_knowledge=req.is_codified_traditional_knowledge,
        is_normally_traded_commodity=req.is_normally_traded_commodity,
    )

    result = ABSEngine.evaluate(ai_input)

    # Persist assessment record
    record = ABSAssessment(
        product_id=req.product_id,
        biological_resources=req.biological_resources,
        origin=req.resource_origin,
        purpose=req.activity_type,
        relevance_label=result.relevance_label,
        next_steps=result.next_steps,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return ABSAssessmentResponse(
        id=record.id,
        approval_required=result.approval_required,
        approving_authority=result.approving_authority,
        form_type=result.form_type,
        benefit_sharing_levy=result.benefit_sharing_levy,
        relevance_label=result.relevance_label,
        statutory_provisions=result.statutory_provisions,
        next_steps=result.next_steps,
        audit_notes=result.audit_notes,
    )
