"""
backend/app/api/v1/expert.py

Human Expert Escalation API endpoints for complex inquiries or low-confidence assessments.
"""

from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.entities import AuditLog, ExpertRequest, ExpertRequestStatus, RoleEnum, User
from app.schemas.expert import ExpertEscalateRequest, ExpertRequestRead, ExpertResolveRequest
from app.security.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/expert", tags=["Human Expert Escalation"])


@router.post(
    "/escalate",
    response_model=ExpertRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Escalate consultation query to AIIA / Human IP Facilitator Desk",
)
async def escalate_query(
    req: ExpertEscalateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates an ExpertRequest in the human review queue.
    """
    record = ExpertRequest(
        user_id=current_user.id,
        message_id=req.message_id,
        status=ExpertRequestStatus.OPEN,
        context=req.issue_description,
    )
    db.add(record)
    await db.flush()

    audit = AuditLog(
        user_id=current_user.id,
        action="EXPERT_ESCALATION",
        resource_type="ExpertRequest",
        resource_id=str(record.id),
        metadata_json={"urgency": req.urgency_level},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(record)

    return ExpertRequestRead.model_validate(record)


@router.get(
    "/my-requests",
    response_model=List[ExpertRequestRead],
    status_code=status.HTTP_200_OK,
    summary="List all queries and updates submitted by the current user to Human IP Facilitators",
)
async def list_my_expert_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all escalation requests and status updates for the authenticated user.
    """
    stmt = (
        select(ExpertRequest)
        .where(ExpertRequest.user_id == current_user.id)
        .order_by(ExpertRequest.created_at.desc())
    )
    result = await db.execute(stmt)
    records = list(result.scalars().all())
    return [ExpertRequestRead.model_validate(r) for r in records]


@router.get(
    "/my-requests/{expert_request_id}",
    response_model=ExpertRequestRead,
    status_code=status.HTTP_200_OK,
    summary="Get single expert request detail for current user",
)
async def get_my_expert_request_detail(
    expert_request_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ExpertRequest).where(
        ExpertRequest.id == expert_request_id,
        ExpertRequest.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expert request not found.")
    return ExpertRequestRead.model_validate(record)


@router.get(
    "/queue",
    response_model=List[ExpertRequestRead],
    status_code=status.HTTP_200_OK,
    summary="List pending escalation requests (Facilitator/Admin only)",
)
async def list_escalation_queue(
    current_user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.IP_FACILITATOR)),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ExpertRequest).order_by(ExpertRequest.created_at.desc())
    result = await db.execute(stmt)
    records = list(result.scalars().all())
    return [ExpertRequestRead.model_validate(r) for r in records]


@router.patch(
    "/{expert_request_id}",
    response_model=ExpertRequestRead,
    status_code=status.HTTP_200_OK,
    summary="Update resolution status for escalation request",
)
async def resolve_escalation(
    expert_request_id: uuid.UUID,
    req: ExpertResolveRequest,
    current_user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.IP_FACILITATOR)),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ExpertRequest).where(ExpertRequest.id == expert_request_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expert request not found.")

    record.status = req.status
    record.response = req.resolution_notes
    record.resolved_by = current_user.id

    audit = AuditLog(
        user_id=current_user.id,
        action="EXPERT_RESOLVE",
        resource_type="ExpertRequest",
        resource_id=str(record.id),
        metadata_json={"new_status": req.status.value},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(record)

    return ExpertRequestRead.model_validate(record)
