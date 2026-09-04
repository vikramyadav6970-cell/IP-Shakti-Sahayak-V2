"""
backend/tests/test_chat_summary.py

Unit and integration tests for LLM Chat Summary Generation and Vector PDF Report compilation.
"""

import json
import uuid
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.database import get_db
from app.main import app
from app.models.base import Base
from app.models import Conversation, Message, Citation, User
from app.services.chat_summary_service import ChatSummaryService
from app.services.report_generator import ConsultationPDFGenerator


@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    yield async_session

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_pdf_generator_raw_compilation():
    """Verify that ConsultationPDFGenerator outputs valid PDF magic bytes without errors."""
    mock_summary_data = {
        "executive_summary": "Comprehensive regulatory and IPR evaluation for an Ayurvedic wellness formulation.",
        "product_classification": {
            "category": "Patent-or-Proprietary Medicine",
            "classification_reason": "Proprietary ratio with novel bioavailability enhancer.",
            "dosage_form": "Syrup",
            "ingredients": ["Withania somnifera", "Piperine"],
            "therapeutic_claims": "Bioavailability enhancement and stress relief",
        },
        "patentability_assessment": {
            "section_3p_status": "Known single herb use in TKDL; combination requires proof of synergy under Section 3(e).",
            "section_3e_status": "Synergistic bioavailability enhancement demonstrated with Piperine.",
            "overall_eligibility": "CONDITIONAL",
        },
        "abs_compliance": {
            "summary": "Commercial utilization of biological resources sourced from India requires compliance with Biological Diversity Act.",
            "sbb_nba_requirements": "Prior intimation to State Biodiversity Board (Form I) required before commercial exploitation.",
        },
        "regulatory_pathway": {
            "licensing_authority": "State Licensing Authority (AYUSH)",
            "license_form": "Form 25-D under Drugs and Cosmetics Rules, 1945",
            "compliance_steps": "Standardization, safety proof, and manufacturing compliance under Schedule T (GMP).",
        },
        "citations": [
            {
                "source": "Indian Patents Act, 1970",
                "section": "Section 3(p)",
                "title": "Bars patenting of traditional knowledge without synergistic efficacy.",
            },
            {
                "source": "Biological Diversity Act, 2002",
                "section": "Section 6",
                "title": "Mandatory prior approval before applying for IPR on Indian biological resources.",
            },
            {
                "source": "NCBI PubMed Research",
                "section": "PMID: 32847521",
                "title": "Bioavailability enhancement of withanolides via piperine administration.",
            },
        ],
        "actionable_next_steps": [
            "File NBA Form 1 before patent application grant",
            "Conduct Rule 158B safety trials",
            "Apply for Form 25-D State Licensing",
        ],
    }

    generator = ConsultationPDFGenerator()
    pdf_bytes = generator.generate_report(
        summary_data=mock_summary_data,
        conversation_title="Ayurvedic Ashwagandha & Piperine Synergy Consultation",
        jurisdiction="INDIA",
        conversation_id="conv-12345678-abcd",
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # Standard PDF header magic bytes
    assert pdf_bytes.startswith(b"%PDF-1.4") or pdf_bytes.startswith(b"%PDF-")


@pytest.mark.asyncio
async def test_chat_summary_fallback_builder():
    """Verify fallback summary generation if LLM is unavailable or yields non-JSON."""
    conv_id = uuid.uuid4()
    conv = Conversation(
        id=conv_id,
        user_id=uuid.uuid4(),
        title="Ashwagandha Syrup Session",
        product_context_json={
            "category": "PATENT_PROPRIETARY",
            "ingredients": ["Withania somnifera", "Piperine"],
            "state": "CLASSIFIED",
        },
    )
    msg1 = Message(id=uuid.uuid4(), conversation_id=conv_id, role="user", content="Can I patent Ashwagandha syrup?")
    msg2 = Message(
        id=uuid.uuid4(),
        conversation_id=conv_id,
        role="assistant",
        content="Under Section 3(p) of the Patents Act, 1970, known uses are excluded unless synergistic efficacy is proven under Section 3(e).",
    )
    cite1 = Citation(
        id=uuid.uuid4(),
        message_id=msg2.id,
        document_title="Indian Patents Act 1970",
        section_ref="Section 3(p)",
        jurisdiction="INDIA",
        source_url="https://ipindia.gov.in/patents-act",
    )
    msg2.citations = [cite1]
    msg1.citations = []
    conv.messages = [msg1, msg2]

    service = ChatSummaryService(db=None)  # type: ignore
    fallback = service._build_fallback_summary(conv)

    assert "executive_summary" in fallback
    assert "patentability_assessment" in fallback
    assert "regulatory_pathway" in fallback
    assert len(fallback["citations"]) >= 1
    assert "Section 3(p)" in fallback["citations"][0]["section"]
    assert fallback["product_classification"]["category"] == "PATENT_PROPRIETARY"


@pytest.mark.asyncio
async def test_chat_summary_and_pdf_endpoints(test_db):
    """Test full integration from conversation creation to JSON summary and PDF download."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register & Login
        await client.post(
            "/api/v1/auth/register",
            json={"name": "Dr. Rajesh Sharma", "email": "rajesh@ayush-lab.in", "password": "Password123!"},
        )
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "rajesh@ayush-lab.in", "password": "Password123!"},
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Mock LLM Response for chat and summary
        mock_summary = {
            "executive_summary": "Consultation evaluating novel extraction of Withania somnifera and Piperine synergy.",
            "product_classification": {
                "category": "Phytopharmaceutical",
                "classification_reason": "Purified fraction of medicinal plant with enhanced bioavailability.",
                "dosage_form": "Standardized Extract",
                "ingredients": ["Withania somnifera", "Piperine"],
                "therapeutic_claims": "Bioavailability enhancement and stress mitigation",
            },
            "patentability_assessment": {
                "section_3p_status": "Overcomes Section 3(p) via novel extraction and synergistic ratio under 3(e).",
                "section_3e_status": "Synergy data demonstrates enhanced withanolide absorption.",
                "overall_eligibility": "HIGH",
            },
            "abs_compliance": {
                "summary": "Mandatory NBA Form 1 approval required under Section 6 of Biological Diversity Act 2002.",
                "sbb_nba_requirements": "File Form 1 before grant of patent.",
            },
            "regulatory_pathway": {
                "licensing_authority": "CDSCO / State Licensing Authority",
                "license_form": "Form CT-20 / Form 25-D",
                "compliance_steps": "Standardization, Phase I safety, Schedule T GMP.",
            },
            "citations": [
                {
                    "source": "Drugs and Cosmetics Rules 1945",
                    "section": "Rule 158B",
                    "title": "Regulatory requirements for Ayurvedic ASU medicines",
                }
            ],
            "actionable_next_steps": [
                "File NBA Form 1",
                "Submit provisional patent application with synergistic data",
            ],
        }

        # Seed conversation and messages directly in test_db
        async with test_db() as session:
            from sqlalchemy import select
            user_res = await session.execute(select(User).where(User.email == "rajesh@ayush-lab.in"))
            user = user_res.scalar_one()

            conv = Conversation(
                user_id=user.id,
                title="Ashwagandha & Piperine Formulation Session",
                product_context_json={
                    "category": "Phytopharmaceutical",
                    "ingredients": ["Withania somnifera", "Piperine"],
                    "state": "CLASSIFIED",
                },
                classification_state="CLASSIFIED",
            )
            session.add(conv)
            await session.flush()

            msg1 = Message(
                conversation_id=conv.id,
                role="user",
                content="What are the IPR and Form 25-D requirements for this formulation?",
                jurisdiction="INDIA",
            )
            msg2 = Message(
                conversation_id=conv.id,
                role="assistant",
                content="Under Section 3(p) and 3(e), you must demonstrate synergistic bio-enhancement.",
                jurisdiction="INDIA",
            )
            session.add_all([msg1, msg2])
            await session.flush()

            cite = Citation(
                message_id=msg2.id,
                document_title="Indian Patents Act 1970",
                section_ref="Section 3(e)",
                jurisdiction="INDIA",
                source_url="https://ipindia.gov.in/patents-act",
            )
            session.add(cite)
            await session.commit()
            conv_id = str(conv.id)

        # Patch LLM in ChatSummaryService
        with patch("app.services.chat_summary_service.GeminiProvider.generate_async", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = json.dumps(mock_summary)

            # 3. Request Summary JSON
            res_summary = await client.get(f"/api/v1/chat/conversations/{conv_id}/summary", headers=headers)
            assert res_summary.status_code == 200
            summary_data = res_summary.json()
            assert "executive_summary" in summary_data
            assert "patentability_assessment" in summary_data
            assert "regulatory_pathway" in summary_data
            assert "citations" in summary_data
            assert summary_data["product_classification"]["category"] == "Phytopharmaceutical"

            # 4. Request Summary PDF
            res_pdf = await client.get(f"/api/v1/chat/conversations/{conv_id}/summary/pdf", headers=headers)
            assert res_pdf.status_code == 200
            assert res_pdf.headers["content-type"] == "application/pdf"
            assert "Content-Disposition" in res_pdf.headers
            assert "attachment; filename=" in res_pdf.headers["Content-Disposition"]
            assert len(res_pdf.content) > 1000
            assert res_pdf.content.startswith(b"%PDF-")
