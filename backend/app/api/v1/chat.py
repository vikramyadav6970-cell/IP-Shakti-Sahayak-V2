"""
backend/app/api/v1/chat.py

Endpoints for chat consultation, conversation history, and feedback.
"""

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.entities import User
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    DeclaredIntentEnum,
    ConversationRead,
    ConversationSummaryRead,
    FeedbackCreate,
    FeedbackRead,
    VoiceChatResponse,
)
from app.security.dependencies import get_current_user, get_optional_current_user
from app.services.chat_service import ChatService
from app.services.voice_service import voice_service

router = APIRouter(prefix="/chat", tags=["Chat & Consultation"])


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute evidence-grounded AI consultation query",
)
async def chat(
    req: ChatRequest,
    current_user: User = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    RAG-grounded consultation endpoint.
    Performs jurisdiction guardrail check, hybrid evidence retrieval, and answer synthesis.
    """
    service = ChatService(db)
    return await service.execute_chat(current_user, req)


@router.post(
    "/voice",
    response_model=VoiceChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Full hands-free voice consultation: STT -> Multi-Agent RAG -> TTS Audio",
)
async def voice_chat(
    file: UploadFile = File(..., description="Recorded speech audio file (WAV/WebM/MP3)"),
    conversation_id: Optional[uuid.UUID] = Form(None),
    jurisdiction: str = Form("INDIA"),
    language: Optional[str] = Form("auto"),
    active_intent: Optional[DeclaredIntentEnum] = Form(None),
    active_classification_id: Optional[uuid.UUID] = Form(None),
    active_product_context: Optional[str] = Form(None),
    speaker: Optional[str] = Form(None),
    pace: float = Form(1.0),
    current_user: User = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Hands-free voice consultation turn.
    1. Transcribes incoming audio via Sarvam STT (saaras:v3).
    2. Runs standard RAG deliberation & multi-agent orchestration.
    3. Synthesizes spoken advisory via Sarvam TTS (bulbul:v3).
    """
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty audio recording submitted.",
        )

    # 1. Speech-to-Text
    try:
        transcript, detected_lang = await voice_service.transcribe_audio(
            audio_bytes=audio_bytes,
            filename=file.filename or "recording.wav",
            mime_type=file.content_type or "audio/wav",
            language_code=language,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Audio transcription failed: {str(exc)}",
        )

    if not transcript or not transcript.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No speech could be recognized in the provided audio.",
        )

    # 2. Execute RAG Chat pipeline with transcribed query
    chat_req = ChatRequest(
        question=transcript,
        query=transcript,
        jurisdiction=jurisdiction,
        language=language or detected_lang or "auto",
        conversation_id=conversation_id,
        active_intent=active_intent,
        active_classification_id=active_classification_id,
        active_product_context=active_product_context,
    )

    service = ChatService(db)
    chat_resp = await service.execute_chat(current_user, chat_req)

    # 3. Text-to-Speech synthesis on final answer text (in target language)
    target_lang = chat_resp.detected_language or detected_lang or "en-IN"
    audio_b64 = await voice_service.synthesize_speech(
        text=chat_resp.content,
        target_language_code=target_lang,
        speaker=speaker,
        pace=pace,
    )

    return VoiceChatResponse(
        conversation_id=chat_resp.conversation_id,
        message_id=chat_resp.message_id,
        content=chat_resp.content,
        jurisdiction=chat_resp.jurisdiction,
        confidence_score=chat_resp.confidence_score,
        confidence_label=chat_resp.confidence_label,
        requires_human_review=chat_resp.requires_human_review,
        citations=chat_resp.citations,
        out_of_scope_detected=chat_resp.out_of_scope_detected,
        detected_jurisdiction=chat_resp.detected_jurisdiction,
        detected_language=chat_resp.detected_language,
        original_language=chat_resp.original_language,
        is_translated=chat_resp.is_translated,
        product_classification=chat_resp.product_classification,
        product_context=chat_resp.product_context,
        domain_confidence=chat_resp.domain_confidence,
        transcribed_text=transcript,
        audio_base64=audio_b64,
        audio_format="audio/wav",
    )


@router.get(
    "/conversations",
    response_model=List[ConversationSummaryRead],
    status_code=status.HTTP_200_OK,
    summary="List past consultation sessions for current user",
)
async def list_conversations(
    current_user: User = Depends(get_optional_current_user),
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
    current_user: User = Depends(get_optional_current_user),
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
    current_user: User = Depends(get_optional_current_user),
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
    current_user: User = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Saves user rating and comments on AI responses for continuous improvement."""
    service = ChatService(db)
    return await service.record_feedback(current_user, message_id, req)
