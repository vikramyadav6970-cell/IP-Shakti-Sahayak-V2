"""
backend/app/repositories/chat_repository.py

Database queries for Conversation, Message, Citation, Feedback, and AuditLog entities.
"""

from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import AuditLog, Citation, Conversation, Feedback, Message


class ChatRepository:
    """Encapsulates DB persistence for consultation sessions and message history."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_conversation(self, conv_id: uuid.UUID) -> Optional[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.id == conv_id)
            .options(
                selectinload(Conversation.messages).selectinload(Message.citations),
                selectinload(Conversation.active_classification),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_conversations(self, user_id: uuid.UUID) -> List[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .options(selectinload(Conversation.messages))
            .order_by(Conversation.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_conversation(self, conv_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        stmt = select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == user_id)
        result = await self.session.execute(stmt)
        conv = result.scalar_one_or_none()
        if not conv:
            return False
        await self.session.delete(conv)
        await self.session.flush()
        return True

    async def create_conversation(self, conv: Conversation) -> Conversation:
        self.session.add(conv)
        await self.session.flush()
        return conv

    async def add_message(self, message: Message) -> Message:
        self.session.add(message)
        await self.session.flush()
        return message

    async def add_citation(self, citation: Citation) -> Citation:
        self.session.add(citation)
        await self.session.flush()
        return citation

    async def add_feedback(self, feedback: Feedback) -> Feedback:
        self.session.add(feedback)
        await self.session.flush()
        return feedback

    async def add_audit_log(self, log: AuditLog) -> AuditLog:
        self.session.add(log)
        await self.session.flush()
        return log
