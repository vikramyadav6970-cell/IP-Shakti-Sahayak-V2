"""
backend/app/schemas/expert.py

Pydantic schemas for human expert escalation and resolution queue.
"""

from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict
from app.models.entities import ExpertRequestStatus


class ExpertEscalateRequest(BaseModel):
    message_id: Optional[uuid.UUID] = None
    issue_description: str
    urgency_level: Optional[str] = "NORMAL"


class ExpertResolveRequest(BaseModel):
    status: ExpertRequestStatus
    resolution_notes: str


class ExpertRequestRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    message_id: Optional[uuid.UUID] = None
    status: ExpertRequestStatus
    context: str
    response: Optional[str] = None
    resolved_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
