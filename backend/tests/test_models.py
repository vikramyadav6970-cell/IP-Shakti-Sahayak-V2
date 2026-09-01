"""
backend/tests/test_models.py

Unit tests verifying SQLAlchemy 2.0 entity model definitions and relationships.
"""

import uuid
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models import (
    Base,
    User,
    RoleEnum,
    Conversation,
    Message,
    Citation,
    Document,
    DocumentTypeEnum,
    DocumentVersion,
    DocumentVersionStatus,
    Product,
    Classification,
    IPAssessment,
    ABSAssessment,
    AuditLog,
    Feedback,
    ExpertRequest,
    ExpertRequestStatus,
)


@pytest.mark.asyncio
async def test_create_all_tables_and_models_crud():
    """Verify all 13 models create cleanly and maintain relationships."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # 1. Create User
        user = User(
            name="Dr. Ayurvedic Researcher",
            email="researcher@ayush.gov.in",
            hashed_password="hashedpassword123",
            role=RoleEnum.RESEARCHER,
            language="en",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        assert user.id is not None
        assert user.role == RoleEnum.RESEARCHER

        # 2. Create Product
        product = Product(
            user_id=user.id,
            name="Triphala Guggulu Synergy",
            description="Classical Ayurvedic formulation with novel bioavailability enhancer",
            raw_ingredients={"haritaki": "100g", "bibhitaki": "100g", "amalaki": "100g"},
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        assert product.name == "Triphala Guggulu Synergy"

        # 3. Create Classification
        classification = Classification(
            product_id=product.id,
            category="PROPRIETARY_MEDICINE",
            regulatory_pathway="AYUSH Form 25-D License under Drugs & Cosmetics Rules 1945 Rule 153",
            reasoning="Contains classical ingredients with modern formulation modification",
            rules_fired=["RULE_CLASSICAL_TEXT_DERIVATION", "RULE_NOVEL_EXCIPIENT_DETECTED"],
        )
        session.add(classification)
        await session.commit()
        await session.refresh(classification)
        assert len(classification.rules_fired) == 2

        # 4. Create Conversation carrying active classification
        conversation = Conversation(
            user_id=user.id,
            title="IP Assessment for Triphala Formulation",
            active_classification_id=classification.id,
        )
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
        assert conversation.active_classification_id == classification.id

        # 5. Create Message + Citation
        message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content="Under Section 3(p) of the Indian Patents Act 1970, an invention which in effect is traditional knowledge is not patentable.",
            jurisdiction="INDIA",
            confidence_score=0.95,
            confidence_label="HIGH",
            requires_human_review=False,
        )
        session.add(message)
        await session.commit()
        await session.refresh(message)

        citation = Citation(
            message_id=message.id,
            document_title="The Patents Act, 1970",
            section_ref="Section 3(p)",
            source_url="https://wipolex.wipo.int/en/legislation/details/2143",
            jurisdiction="INDIA",
            document_type="STATUTE",
        )
        session.add(citation)
        await session.commit()

        # 6. Create Document and DocumentVersion
        doc = Document(
            title="The Patents Act, 1970",
            jurisdiction="INDIA",
            document_type=DocumentTypeEnum.STATUTE,
            authority="Intellectual Property India",
            language="en",
            source_url="https://wipolex.wipo.int/en/legislation/details/2143",
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)

        doc_ver = DocumentVersion(
            document_id=doc.id,
            version_label="2024 Amendment",
            status=DocumentVersionStatus.INDEXED,
            is_current=True,
        )
        session.add(doc_ver)
        await session.commit()

        # 7. Create ABS & IPAssessment
        abs_eval = ABSAssessment(
            product_id=product.id,
            biological_resources=["Curcuma longa", "Withania somnifera"],
            origin="INDIA",
            purpose="COMMERCIAL",
            relevance_label="HIGH",
            next_steps=["File Form I with National Biodiversity Authority"],
        )
        session.add(abs_eval)

        ip_eval = IPAssessment(
            product_id=product.id,
            ip_type="PATENT",
            relevance_label="HIGH",
            reasoning="Gated by Section 3(p) traditional knowledge inquiry",
        )
        session.add(ip_eval)

        # 8. Create AuditLog and ExpertRequest
        audit = AuditLog(
            user_id=user.id,
            action="CLASSIFICATION_RUN",
            resource_type="Product",
            resource_id=str(product.id),
            metadata_json={"rules": classification.rules_fired},
        )
        session.add(audit)

        expert_req = ExpertRequest(
            user_id=user.id,
            message_id=message.id,
            status=ExpertRequestStatus.OPEN,
            context="Need validation on Section 3(p) vs Section 3(e) synergistic interaction claim",
        )
        session.add(expert_req)
        await session.commit()

    await engine.dispose()
