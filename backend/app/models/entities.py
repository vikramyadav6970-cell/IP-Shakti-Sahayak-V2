"""
backend/app/models/entities.py

Authoritative SQLAlchemy 2.0 models for IP-SAKTI Sahayak.
Adheres to layered architecture and schema requirements from backend/coding_conventions.md.
"""

from datetime import datetime, timezone
import enum
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


# --- ENUMS ---

class RoleEnum(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    IP_FACILITATOR = "IP_FACILITATOR"
    CONTENT_MANAGER = "CONTENT_MANAGER"
    RESEARCHER = "RESEARCHER"


class DocumentTypeEnum(str, enum.Enum):
    STATUTE = "STATUTE"
    RULE = "RULE"
    TREATY = "TREATY"
    REGISTRY_RECORD = "REGISTRY_RECORD"
    CASE_LAW = "CASE_LAW"
    GUIDELINE = "GUIDELINE"


class DocumentVersionStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class DeclaredIntentEnum(str, enum.Enum):
    PATENT = "PATENT"
    RESEARCH = "RESEARCH"
    SELL_BUSINESS = "SELL_BUSINESS"
    AYUSH_APPLICATION = "AYUSH_APPLICATION"
    EXPORT = "EXPORT"
    OTHER = "OTHER"


class ExpertRequestStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"


# --- MODELS ---

class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User account model with role-based access control."""
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    organization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[RoleEnum] = mapped_column(
        SAEnum(RoleEnum, name="role_enum", native_enum=False),
        default=RoleEnum.USER,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    products: Mapped[List["Product"]] = relationship("Product", back_populates="user", cascade="all, delete-orphan")
    feedbacks: Mapped[List["Feedback"]] = relationship("Feedback", back_populates="user")
    expert_requests: Mapped[List["ExpertRequest"]] = relationship("ExpertRequest", foreign_keys="[ExpertRequest.user_id]", back_populates="user")


class Conversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Chat conversation session carrying active classification & intent context."""
    __tablename__ = "conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    active_classification_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("classifications.id", ondelete="SET NULL"), nullable=True)
    active_intent: Mapped[Optional[DeclaredIntentEnum]] = mapped_column(
        SAEnum(DeclaredIntentEnum, name="declared_intent_enum", native_enum=False),
        nullable=True,
    )
    product_context_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    classification_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="COLLECTING_PRODUCT_INFORMATION")

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    active_classification: Mapped[Optional["Classification"]] = relationship("Classification", foreign_keys=[active_classification_id])


class Message(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Turn in a consultation conversation."""
    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    jurisdiction: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence_label: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # "LOW" | "MEDIUM" | "HIGH"
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    classification: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    citations: Mapped[List["Citation"]] = relationship("Citation", back_populates="message", cascade="all, delete-orphan")
    feedbacks: Mapped[List["Feedback"]] = relationship("Feedback", back_populates="message")


class Citation(Base, UUIDPrimaryKeyMixin):
    """Statutory or prior-art evidence backing an assistant claim."""
    __tablename__ = "citations"

    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    document_title: Mapped[str] = mapped_column(String(500), nullable=False)
    section_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    document_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    chunk_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    message: Mapped["Message"] = relationship("Message", back_populates="citations")


class Document(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Primary authoritative source in the IP/regulatory corpus."""
    __tablename__ = "documents"

    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    jurisdiction: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    document_type: Mapped[DocumentTypeEnum] = mapped_column(
        SAEnum(DocumentTypeEnum, name="document_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    authority: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    versions: Mapped[List["DocumentVersion"]] = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Specific version / amendment of an authoritative document."""
    __tablename__ = "document_versions"

    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_label: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "2023 Amendment", "1970 Original"
    effective_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    object_storage_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[DocumentVersionStatus] = mapped_column(
        SAEnum(DocumentVersionStatus, name="document_version_status", native_enum=False),
        default=DocumentVersionStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="versions")


class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User product / formulation subject to IPR analysis."""
    __tablename__ = "products"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_ingredients: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="products")
    classifications: Mapped[List["Classification"]] = relationship("Classification", back_populates="product", cascade="all, delete-orphan")
    ip_assessments: Mapped[List["IPAssessment"]] = relationship("IPAssessment", back_populates="product", cascade="all, delete-orphan")
    abs_assessments: Mapped[List["ABSAssessment"]] = relationship("ABSAssessment", back_populates="product", cascade="all, delete-orphan")


class Classification(Base, UUIDPrimaryKeyMixin):
    """Deterministic product classification record with fired rules audit trail."""
    __tablename__ = "classifications"

    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    regulatory_pathway: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rules_fired: Mapped[List[str]] = mapped_column(JSON, nullable=False)  # Audit trail per context.md §2 rule 6
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="classifications")


class IPAssessment(Base, UUIDPrimaryKeyMixin):
    """Per-IP-type relevance assessment for a classified formulation."""
    __tablename__ = "ip_assessments"

    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True)
    ip_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # PATENT, TRADEMARK, GI, etc.
    relevance_label: Mapped[str] = mapped_column(String(50), nullable=False)  # HIGH, MEDIUM, LOW, NOT_APPLICABLE
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    legal_provisions: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="ip_assessments")


class ABSAssessment(Base, UUIDPrimaryKeyMixin):
    """Access & Benefit Sharing (NBA/Biological Diversity Act) compliance assessment."""
    __tablename__ = "abs_assessments"

    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True)
    biological_resources: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    origin: Mapped[str] = mapped_column(String(100), nullable=False)  # "INDIA" | "FOREIGN"
    purpose: Mapped[str] = mapped_column(String(50), nullable=False)   # "COMMERCIAL" | "RESEARCH"
    relevance_label: Mapped[str] = mapped_column(String(50), nullable=False)  # HIGH, MEDIUM, LOW, NOT_APPLICABLE
    next_steps: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="abs_assessments")


class AuditLog(Base, UUIDPrimaryKeyMixin):
    """Append-only audit trail aligned with DPDP compliance."""
    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)


class Feedback(Base, UUIDPrimaryKeyMixin):
    """User rating and feedback on generated responses."""
    __tablename__ = "feedbacks"

    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    message: Mapped["Message"] = relationship("Message", back_populates="feedbacks")
    user: Mapped["User"] = relationship("User", back_populates="feedbacks")


class ExpertRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Escalation of low-confidence consultation to a human IP facilitator."""
    __tablename__ = "expert_requests"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True)
    status: Mapped[ExpertRequestStatus] = mapped_column(
        SAEnum(ExpertRequestStatus, name="expert_request_status", native_enum=False),
        default=ExpertRequestStatus.OPEN,
        nullable=False,
        index=True,
    )
    context: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="expert_requests")
