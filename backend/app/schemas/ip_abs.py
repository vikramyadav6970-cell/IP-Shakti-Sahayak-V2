"""
backend/app/schemas/ip_abs.py

Pydantic schemas for ABS and IP Assessments.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict


class ABSAssessmentRequest(BaseModel):
    product_id: Optional[uuid.UUID] = None
    entity_nationality: str         # "INDIAN" | "FOREIGN" | "INDIAN_WITH_FOREIGN_EQUITY"
    biological_resources: List[str]
    resource_origin: str            # "INDIA" | "FOREIGN" | "BOTH"
    activity_type: str              # "COMMERCIAL_UTILIZATION" | "RESEARCH" | "IPR_APPLICATION" | "TRANSFER_OF_RESULTS"
    is_ayush_practitioner: bool = False
    is_codified_traditional_knowledge: bool = False
    is_normally_traded_commodity: bool = False


class ABSAssessmentResponse(BaseModel):
    id: Optional[uuid.UUID] = None
    approval_required: bool
    approving_authority: str
    form_type: Optional[str] = None
    benefit_sharing_levy: str
    relevance_label: str
    statutory_provisions: List[str]
    next_steps: List[str]
    audit_notes: List[str]

    model_config = ConfigDict(from_attributes=True)


class IPAssessmentRequest(BaseModel):
    product_id: Optional[uuid.UUID] = None
    product_name: str
    category: str
    ingredients: List[str]
    has_novel_tech: bool = False
    intent: str = "PATENT"


class IPAssessmentResponse(BaseModel):
    id: Optional[uuid.UUID] = None
    product_id: Optional[uuid.UUID] = None
    product_name: str
    category: str
    patent_eligibility: str
    patent_reasoning: str
    trademark_recommendation: str
    abs_requirement: str
    gi_relevance: str
    actionable_roadmap: List[str]
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
