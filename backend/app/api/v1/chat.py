"""
backend/app/api/v1/chat.py

Endpoints for chat consultation, conversation history, and feedback.
"""

from typing import List
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.entities import User
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationRead,
    ConversationSummaryRead,
    FeedbackCreate,
    FeedbackRead,
)
from app.security.dependencies import get_current_user
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat & Consultation"])


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute evidence-grounded AI consultation query",
)
async def chat(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    RAG-grounded consultation endpoint.
    Performs jurisdiction guardrail check, hybrid evidence retrieval, and answer synthesis.
    """
    service = ChatService(db)
    return await service.execute_chat(current_user, req)


@router.get(
    "/conversations",
    response_model=List[ConversationSummaryRead],
    status_code=status.HTTP_200_OK,
    summary="List past consultation sessions for current user",
)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns past chat sessions."""
    service = ChatService(db)
    return await service.list_user_conversations(current_user)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationRead,
    status_code=status.HTTP_200_OK,
    summary="Get full conversation history and citations",
)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns conversation transcript and citations."""
    service = ChatService(db)
    return await service.get_conversation_details(current_user, conversation_id)


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a consultation session",
)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(db)
    await service.delete_user_conversation(current_user, conversation_id)
    return {"message": "Conversation deleted successfully", "id": str(conversation_id)}


@router.post(
    "/{message_id}/feedback",
    response_model=FeedbackRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit user feedback on assistant response",
)
async def submit_feedback(
    message_id: uuid.UUID,
    req: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Saves rating (1-5) and user comments on assistant answer."""
    service = ChatService(db)
    return await service.add_message_feedback(current_user, message_id, req)
