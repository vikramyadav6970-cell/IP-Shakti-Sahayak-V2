"""
backend/app/services/document_service.py

Business logic for corpus documents, versions, and ingestion triggering.
"""

from typing import Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Document, DocumentTypeEnum, DocumentVersion, DocumentVersionStatus
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import (
    DocumentCreate,
    DocumentListResponse,
    DocumentRead,
    DocumentVersionCreate,
    DocumentVersionRead,
    IngestResponse,
)


class DocumentService:
    """Handles document management and indexing operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.doc_repo = DocumentRepository(session)

    async def get_document(self, doc_id: uuid.UUID) -> DocumentRead:
        doc = await self.doc_repo.get_by_id(doc_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
        return DocumentRead.model_validate(doc)

    async def create_document(self, data: DocumentCreate) -> DocumentRead:
        new_doc = Document(
            title=data.title.strip(),
            jurisdiction=data.jurisdiction.upper().strip(),
            document_type=data.document_type,
            authority=data.authority.strip(),
            language=data.language or "en",
            source_url=data.source_url.strip(),
            description=data.description,
        )
        doc = await self.doc_repo.create(new_doc)

        # Create initial version
        version = DocumentVersion(
            document_id=doc.id,
            version_label=data.initial_version_label or "Initial Version",
            is_current=True,
            status=DocumentVersionStatus.PENDING,
        )
        await self.doc_repo.create_version(version)

        await self.session.commit()
        # Reload with versions
        reloaded = await self.doc_repo.get_by_id(doc.id)
        return DocumentRead.model_validate(reloaded)

    async def create_version(self, doc_id: uuid.UUID, data: DocumentVersionCreate) -> DocumentVersionRead:
        doc = await self.doc_repo.get_by_id(doc_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        version = DocumentVersion(
            document_id=doc.id,
            version_label=data.version_label.strip(),
            effective_from=data.effective_from,
            object_storage_key=data.object_storage_key,
            is_current=data.is_current,
            status=DocumentVersionStatus.PENDING,
        )
        created_ver = await self.doc_repo.create_version(version)
        await self.session.commit()
        return DocumentVersionRead.model_validate(created_ver)

    async def list_documents(
        self,
        page: int = 1,
        page_size: int = 20,
        jurisdiction: Optional[str] = None,
        document_type: Optional[DocumentTypeEnum] = None,
        authority: Optional[str] = None,
    ) -> DocumentListResponse:
        docs, total = await self.doc_repo.list_documents(
            page=page,
            page_size=page_size,
            jurisdiction=jurisdiction,
            document_type=document_type,
            authority=authority,
        )
        return DocumentListResponse(
            items=[DocumentRead.model_validate(d) for d in docs],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def trigger_ingestion(self, doc_id: uuid.UUID) -> IngestResponse:
        doc = await self.doc_repo.get_by_id(doc_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        ver = await self.doc_repo.get_current_version(doc_id)
        if not ver:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active document version found to ingest.")

        ver.status = DocumentVersionStatus.PROCESSING
        await self.session.commit()

        # In production this dispatches to Celery / AI worker task.
        return IngestResponse(
            document_id=doc.id,
            version_id=ver.id,
            status=DocumentVersionStatus.PROCESSING,
            message=f"Ingestion triggered for document '{doc.title}'. Processing chunking & Qdrant indexing.",
        )
