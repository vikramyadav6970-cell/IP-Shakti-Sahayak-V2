"""
backend/tests/test_phase4_endpoints.py

Integration tests for ABS compliance, IP assessment, Source Explorer, and Expert Escalation endpoints.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.database import get_db
from app.main import app
from app.models.base import Base


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
async def test_abs_and_ip_endpoints(test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register user
        await client.post(
            "/api/v1/auth/register",
            json={"name": "Dr. Sharma", "email": "sharma@ayush.org", "password": "Password123!"},
        )
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "sharma@ayush.org", "password": "Password123!"},
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Test ABS Assessment endpoint
        abs_payload = {
            "entity_nationality": "FOREIGN",
            "biological_resources": ["Withania somnifera"],
            "resource_origin": "INDIA",
            "activity_type": "COMMERCIAL_UTILIZATION",
        }
        res_abs = await client.post("/api/v1/abs", headers=headers, json=abs_payload)
        assert res_abs.status_code == 200
        abs_data = res_abs.json()
        assert abs_data["approval_required"] is True
        assert abs_data["form_type"] == "Form I"
        assert "National Biodiversity Authority" in abs_data["approving_authority"]

        # 2. Test IP Assessment endpoint
        ip_payload = {
            "product_name": "Triphala Churna",
            "category": "CLASSICAL_MEDICINE",
            "ingredients": ["Terminalia chebula", "Terminalia bellirica", "Phyllanthus emblica"],
            "has_novel_tech": False,
        }
        res_ip = await client.post("/api/v1/ip", headers=headers, json=ip_payload)
        assert res_ip.status_code == 200
        ip_data = res_ip.json()
        assert ip_data["patent_eligibility"] == "EXCLUDED"
        assert "Section 3(p)" in ip_data["patent_reasoning"]
        assert len(ip_data["actionable_roadmap"]) >= 2

        # 3. Test Source Explorer endpoints
        res_sources_overview = await client.get("/api/v1/sources/overview", headers=headers)
        assert res_sources_overview.status_code == 200
        overview = res_sources_overview.json()
        assert len(overview["collections"]) == 5

        res_sources_docs = await client.get("/api/v1/sources/documents", headers=headers)
        assert res_sources_docs.status_code == 200
        docs = res_sources_docs.json()
        assert len(docs) >= 5

        # 4. Create chat conversation and test expert escalation
        chat_res = await client.post(
            "/api/v1/chat",
            headers=headers,
            json={"question": "Need clarification on TKDL reference for patent", "jurisdiction": "INDIA"},
        )
        msg_id = chat_res.json()["message_id"]

        esc_payload = {
            "message_id": msg_id,
            "issue_description": "Complex dispute over TKDL citation interpretation",
            "urgency_level": "HIGH",
        }
        res_esc = await client.post("/api/v1/expert/escalate", headers=headers, json=esc_payload)
        assert res_esc.status_code == 201
        esc_data = res_esc.json()
        assert esc_data["status"] == "OPEN"
        assert esc_data["context"] == "Complex dispute over TKDL citation interpretation"
