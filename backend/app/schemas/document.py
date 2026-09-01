"""
backend/app/schemas/document.py

Pydantic schemas for Document and DocumentVersion entities.
"""

from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict
from app.models.entities import DocumentTypeEnum, DocumentVersionStatus


class DocumentVersionRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    version_label: str
    effective_from: Optional[datetime] = None
    object_storage_key: Optional[str] = None
    is_current: bool
    status: DocumentVersionStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentVersionCreate(BaseModel):
    version_label: str
    effective_from: Optional[datetime] = None
    object_storage_key: Optional[str] = None
    is_current: bool = True


class DocumentCreate(BaseModel):
    title: str
    jurisdiction: str
    document_type: DocumentTypeEnum
    authority: str
    language: str = "en"
    source_url: str
    description: Optional[str] = None
    initial_version_label: Optional[str] = "Initial Version"


class DocumentRead(BaseModel):
    id: uuid.UUID
    title: str
    jurisdiction: str
    document_type: DocumentTypeEnum
    authority: str
    language: str
    source_url: str
    description: Optional[str] = None
    created_at: datetime
    versions: List[DocumentVersionRead] = []

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    items: List[DocumentRead]
    total: int
    page: int
    page_size: int


class IngestResponse(BaseModel):
    document_id: uuid.UUID
    version_id: uuid.UUID
    status: DocumentVersionStatus
    message: str
