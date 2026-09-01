"""
backend/app/api/v1/documents.py

Document metadata management, versioning, and ingestion trigger endpoints.
"""

from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.entities import DocumentTypeEnum, RoleEnum, User
from app.schemas.document import (
    DocumentCreate,
    DocumentListResponse,
    DocumentRead,
    DocumentVersionCreate,
    DocumentVersionRead,
    IngestResponse,
)
from app.security.dependencies import require_roles
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get(
    "",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List corpus documents (public/authenticated)",
)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    jurisdiction: Optional[str] = None,
    document_type: Optional[DocumentTypeEnum] = None,
    authority: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Returns paginated list of authoritative corpus documents."""
    service = DocumentService(db)
    return await service.list_documents(
        page=page,
        page_size=page_size,
        jurisdiction=jurisdiction,
        document_type=document_type,
        authority=authority,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentRead,
    status_code=status.HTTP_200_OK,
    summary="Get document details and versions by ID",
)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Returns a specific document with its version history."""
    service = DocumentService(db)
    return await service.get_document(document_id)


@router.post(
    "",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create new document metadata (Admin / Content Manager only)",
)
async def create_document(
    req: DocumentCreate,
    _user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.CONTENT_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    """Registers a new document in the authoritative corpus."""
    service = DocumentService(db)
    return await service.create_document(req)


@router.post(
    "/{document_id}/versions",
    response_model=DocumentVersionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new version to an existing document",
)
async def create_document_version(
    document_id: uuid.UUID,
    req: DocumentVersionCreate,
    _user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.CONTENT_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    """Registers a new version/amendment for a document."""
    service = DocumentService(db)
    return await service.create_version(document_id, req)


@router.post(
    "/{document_id}/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger document parsing, chunking, and vector indexing",
)
async def trigger_document_ingestion(
    document_id: uuid.UUID,
    _user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.CONTENT_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    """Initiates async chunking & vector indexing pipeline for a document."""
    service = DocumentService(db)
    return await service.trigger_ingestion(document_id)
