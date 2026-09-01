"""
backend/app/repositories/document_repository.py

Database queries for Document and DocumentVersion entities.
"""

from typing import List, Optional, Tuple
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import Document, DocumentTypeEnum, DocumentVersion, DocumentVersionStatus


class DocumentRepository:
    """Encapsulates DB persistence for authoritative documents and versions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, doc_id: uuid.UUID) -> Optional[Document]:
        stmt = (
            select(Document)
            .where(Document.id == doc_id)
            .options(selectinload(Document.versions))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, doc: Document) -> Document:
        self.session.add(doc)
        await self.session.flush()
        await self.session.refresh(doc)
        return doc

    async def create_version(self, version: DocumentVersion) -> DocumentVersion:
        if version.is_current:
            # Set older versions for this document to is_current=False
            stmt = select(DocumentVersion).where(
                DocumentVersion.document_id == version.document_id,
                DocumentVersion.is_current.is_(True),
            )
            res = await self.session.execute(stmt)
            for old_ver in res.scalars().all():
                old_ver.is_current = False

        self.session.add(version)
        await self.session.flush()
        await self.session.refresh(version)
        return version

    async def get_current_version(self, doc_id: uuid.UUID) -> Optional[DocumentVersion]:
        stmt = (
            select(DocumentVersion)
            .where(DocumentVersion.document_id == doc_id, DocumentVersion.is_current.is_(True))
            .order_by(DocumentVersion.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_documents(
        self,
        page: int = 1,
        page_size: int = 20,
        jurisdiction: Optional[str] = None,
        document_type: Optional[DocumentTypeEnum] = None,
        authority: Optional[str] = None,
    ) -> Tuple[List[Document], int]:
        query = select(Document).options(selectinload(Document.versions))
        count_query = select(func.count(Document.id))

        if jurisdiction:
            query = query.where(func.lower(Document.jurisdiction) == jurisdiction.lower())
            count_query = count_query.where(func.lower(Document.jurisdiction) == jurisdiction.lower())

        if document_type:
            query = query.where(Document.document_type == document_type)
            count_query = count_query.where(Document.document_type == document_type)

        if authority:
            query = query.where(func.lower(Document.authority).contains(authority.lower()))
            count_query = count_query.where(func.lower(Document.authority).contains(authority.lower()))

        total_res = await self.session.execute(count_query)
        total = total_res.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(Document.created_at.desc()).offset(offset).limit(page_size)

        result = await self.session.execute(query)
        docs = list(result.scalars().all())

        return docs, total
