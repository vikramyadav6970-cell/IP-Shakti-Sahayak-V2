"""
backend/app/schemas/chat.py

Pydantic schemas for chat consultation, messages, citations, feedback,
and structured conversational product classification context.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, model_validator
from app.models.entities import DeclaredIntentEnum


class CitationRead(BaseModel):
    id: Optional[uuid.UUID] = None
    document_title: str
    section_ref: str
    source_url: str
    jurisdiction: str
    document_type: Optional[str] = None
    verification_status: Optional[str] = "VERIFIED_OFFICIAL_GAZETTE"

    model_config = ConfigDict(from_attributes=True)


class ProductClassificationMeta(BaseModel):
    category: str  # CLASSICAL_MEDICINE | PROPRIETARY_MEDICINE | NEW_DRUG | PHYTOPHARMACEUTICAL | AYURVEDA_AAHARA | COSMETIC
    category_name: str
    product_name: Optional[str] = None
    regulatory_pathway: str
    statutory_authority: str
    reasoning: str
    patent_eligibility: str  # EXCLUDED | CONDITIONAL | HIGH
    patent_reasoning: str
    abs_requirement: str
    confidence: float = 0.95


class ProductContextData(BaseModel):
    product_name: Optional[str] = None
    description: Optional[str] = None
    formulation: Optional[str] = None
    ingredients: Optional[List[str]] = None
    dosage_form: Optional[str] = None
    intended_use: Optional[str] = None
    therapeutic_claims: Optional[str] = None
    classical_source: Optional[str] = None
    other_relevant_info: Optional[str] = None
    state: str = "PENDING"  # PENDING | COLLECTING_PRODUCT_INFORMATION | READY_FOR_CLASSIFICATION | CLASSIFIED
    category: Optional[str] = None
    category_name: Optional[str] = None
    classification_reason: Optional[str] = None
    regulatory_pathway: Optional[str] = None
    statutory_authority: Optional[str] = None
    patent_eligibility: Optional[str] = None
    patent_reasoning: Optional[str] = None
    abs_requirement: Optional[str] = None


class MessageRead(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    jurisdiction: Optional[str] = None
    confidence_score: Optional[float] = None
    confidence_label: Optional[str] = None
    requires_human_review: bool = False
    classification: Optional[str] = None
    created_at: datetime
    citations: List[CitationRead] = []

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    question: Optional[str] = None
    query: Optional[str] = None
    jurisdiction: str = "INDIA"
    language: str = "auto"
    conversation_id: Optional[uuid.UUID] = None
    active_classification_id: Optional[uuid.UUID] = None
    active_intent: Optional[DeclaredIntentEnum] = None
    active_product_context: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def check_question_or_query(cls, data: Any) -> Any:
        if isinstance(data, dict):
            q_val = data.get("question") or data.get("query")
            if not q_val:
                raise ValueError("Either 'question' or 'query' field is required.")
            data["question"] = q_val
            data["query"] = q_val

            # Sanitize conversation_id if invalid/empty/mock
            conv_id = data.get("conversation_id")
            if conv_id is not None:
                try:
                    if isinstance(conv_id, str):
                        data["conversation_id"] = uuid.UUID(conv_id)
                except Exception:
                    data["conversation_id"] = None

            # Sanitize active_classification_id if invalid/empty/mock
            class_id = data.get("active_classification_id")
            if class_id is not None:
                try:
                    if isinstance(class_id, str):
                        data["active_classification_id"] = uuid.UUID(class_id)
                except Exception:
                    data["active_classification_id"] = None

            # Sanitize active_intent
            intent_val = data.get("active_intent")
            if intent_val:
                try:
                    data["active_intent"] = DeclaredIntentEnum(intent_val)
                except Exception:
                    data["active_intent"] = None
        return data


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    content: str
    jurisdiction: str
    confidence_score: Optional[float] = None
    confidence_label: Optional[str] = None
    requires_human_review: bool
    citations: List[CitationRead]
    out_of_scope_detected: bool = False
    detected_jurisdiction: Optional[str] = None
    detected_language: Optional[str] = None
    original_language: Optional[str] = None
    is_translated: bool = False
    product_classification: Optional[ProductClassificationMeta] = None
    product_context: Optional[ProductContextData] = None
    domain_confidence: Optional[Dict[str, Any]] = None


class VoiceChatResponse(ChatResponse):
    """Extends standard chat advisory with speech transcription and synthesized voice audio."""
    transcribed_text: str
    audio_base64: Optional[str] = None
    audio_format: Optional[str] = "audio/wav"


class ConversationRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: Optional[str] = None
    active_classification_id: Optional[uuid.UUID] = None
    active_intent: Optional[DeclaredIntentEnum] = None
    product_context: Optional[ProductContextData] = None
    product_classification: Optional[ProductClassificationMeta] = None
    classification_state: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[MessageRead] = []

    model_config = ConfigDict(from_attributes=True)


class ConversationSummaryRead(BaseModel):
    id: uuid.UUID
    title: Optional[str] = None
    active_classification_id: Optional[uuid.UUID] = None
    active_intent: Optional[DeclaredIntentEnum] = None
    product_name: Optional[str] = None
    category: Optional[str] = None
    category_name: Optional[str] = None
    dosage_form: Optional[str] = None
    ingredients: List[str] = []
    patent_eligibility: Optional[str] = None
    regulatory_pathway: Optional[str] = None
    classification_state: Optional[str] = None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeedbackCreate(BaseModel):
    rating: int  # 1 to 5
    comment: Optional[str] = None


class FeedbackRead(BaseModel):
    id: uuid.UUID
    message_id: uuid.UUID
    user_id: uuid.UUID
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
