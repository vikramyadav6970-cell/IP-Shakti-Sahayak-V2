"""
backend/tests/test_expert_my_requests.py

Tests for the User's Human IP Facilitator Desk Dashboard endpoints.
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
async def test_user_expert_my_requests_lifecycle(test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register and Login a regular User
        user_reg = {
            "name": "Ayurvedic Innovator",
            "email": "innovator@ayush-startups.in",
            "password": "Password123!",
            "organization": "Kerala Herbals Pvt Ltd",
        }
        await client.post("/api/v1/auth/register", json=user_reg)
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "innovator@ayush-startups.in", "password": "Password123!"},
        )
        user_token = login_res.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # 2. Initially my-requests should be empty
        init_res = await client.get("/api/v1/expert/my-requests", headers=user_headers)
        assert init_res.status_code == 200
        assert init_res.json() == []

        # 3. User submits an inquiry to the Human IP Facilitator
        inquiry_payload = {
            "issue_description": "[Category: Patentability §3(p) Clarification]\nNeed expert review on synergistic bioavailability enhancement claims for standardized Maricha piperine with sesame lipid matrix.",
            "urgency_level": "HIGH",
        }
        escalate_res = await client.post("/api/v1/expert/escalate", headers=user_headers, json=inquiry_payload)
        assert escalate_res.status_code == 201
        ticket = escalate_res.json()
        assert ticket["status"] == "OPEN"
        ticket_id = ticket["id"]

        # 4. User queries their my-requests dashboard endpoint
        my_reqs_res = await client.get("/api/v1/expert/my-requests", headers=user_headers)
        assert my_reqs_res.status_code == 200
        reqs = my_reqs_res.json()
        assert len(reqs) == 1
        assert reqs[0]["id"] == ticket_id
        assert reqs[0]["status"] == "OPEN"
        assert "Patentability §3(p)" in reqs[0]["context"]

        # 5. Register and login an IP Facilitator to review and answer the request
        facilitator_reg = {
            "name": "Dr. Rajesh Sharma, IP Facilitator",
            "email": "rajesh.facilitator@aiia.gov.in",
            "password": "Password123!",
            "role": "IP_FACILITATOR",
        }
        await client.post("/api/v1/auth/register", json=facilitator_reg)
        fac_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "rajesh.facilitator@aiia.gov.in", "password": "Password123!"},
        )
        fac_token = fac_login.json()["access_token"]
        fac_headers = {"Authorization": f"Bearer {fac_token}"}

        # Facilitator answers the ticket with advisory notes
        resolve_payload = {
            "status": "RESOLVED",
            "resolution_notes": "### Official Facilitator Advisory\n\n1. **Section 3(p) Traditional Knowledge:** *Maricha* as a *Yogavahi* (bioenhancer) is documented in classical texts.\n2. **Patentability Threshold:** Your lipid self-emulsifying delivery system is patentable if experimental comparative pharmacokinetic data (AUC enhancement > 3.5x over Sneha Kalpana) is included in the provisional specification.\n3. **Recommended Next Steps:** File Form 1 & Form 2 provisional specification with complete comparative bioavailability data.",
        }
        res_patch = await client.patch(f"/api/v1/expert/{ticket_id}", headers=fac_headers, json=resolve_payload)
        assert res_patch.status_code == 200
        resolved_ticket = res_patch.json()
        assert resolved_ticket["status"] == "RESOLVED"
        assert "Official Facilitator Advisory" in resolved_ticket["response"]

        # 6. User refreshes their dashboard and sees the Facilitator's Resolution Notes
        final_my_reqs = await client.get("/api/v1/expert/my-requests", headers=user_headers)
        assert final_my_reqs.status_code == 200
        final_reqs = final_my_reqs.json()
        assert len(final_reqs) == 1
        assert final_reqs[0]["status"] == "RESOLVED"
        assert final_reqs[0]["response"] is not None
        assert "Section 3(p) Traditional Knowledge" in final_reqs[0]["response"]

        # 7. Check individual request detail endpoint
        detail_res = await client.get(f"/api/v1/expert/my-requests/{ticket_id}", headers=user_headers)
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["id"] == ticket_id
        assert detail["status"] == "RESOLVED"
