"""
backend/tests/test_conversation_session_persistence.py

Tests for conversation history, persistence, product context restoration, and session lifecycle.
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
async def test_conversation_history_and_persistence_lifecycle(test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register and Login a User
        user_reg = {
            "name": "Dr. Ayush Researcher",
            "email": "researcher@ayurveda-labs.in",
            "password": "Password123!",
        }
        await client.post("/api/v1/auth/register", json=user_reg)
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "researcher@ayurveda-labs.in", "password": "Password123!"},
        )
        user_token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {user_token}"}

        # 2. Initially conversation history should be empty
        init_res = await client.get("/api/v1/chat/conversations", headers=headers)
        assert init_res.status_code == 200
        assert init_res.json() == []

        # 3. Start first conversation: Classical formulation
        chat_turn_1 = {
            "question": "Classical Triphala Churna prepared per Ayurvedic Formulary of India (AFI).",
            "jurisdiction": "INDIA",
        }
        turn_1_res = await client.post("/api/v1/chat", headers=headers, json=chat_turn_1)
        assert turn_1_res.status_code == 200
        turn_1_data = turn_1_res.json()
        conv_1_id = turn_1_data["conversation_id"]

        # Follow-up in same conversation: Ask about patentability
        chat_turn_2 = {
            "question": "Is this classical formulation patentable under Indian Patent Law §3(p)?",
            "jurisdiction": "INDIA",
            "conversation_id": conv_1_id,
        }
        turn_2_res = await client.post("/api/v1/chat", headers=headers, json=chat_turn_2)
        assert turn_2_res.status_code == 200

        # 4. Start second conversation: Novel formulation
        chat_turn_3 = {
            "question": "Standardized nano-liposomal curcumin extract with piperine for targeted bioavailability.",
            "jurisdiction": "INDIA",
        }
        turn_3_res = await client.post("/api/v1/chat", headers=headers, json=chat_turn_3)
        assert turn_3_res.status_code == 200
        conv_2_id = turn_3_res.json()["conversation_id"]
        assert conv_2_id != conv_1_id

        # 5. List conversations: Should return 2 sessions with summary metadata
        list_res = await client.get("/api/v1/chat/conversations", headers=headers)
        assert list_res.status_code == 200
        sessions = list_res.json()
        assert len(sessions) == 2

        # Verify session ids
        session_ids = [s["id"] for s in sessions]
        assert conv_1_id in session_ids
        assert conv_2_id in session_ids

        # 6. Retrieve detailed conversation 1: Verify all messages and product context restored
        detail_res_1 = await client.get(f"/api/v1/chat/conversations/{conv_1_id}", headers=headers)
        assert detail_res_1.status_code == 200
        detail_1 = detail_res_1.json()
        assert detail_1["id"] == conv_1_id
        assert len(detail_1["messages"]) >= 4  # 2 user turns + 2 assistant turns
        assert detail_1["classification_state"] is not None

        # 7. Delete conversation 2
        del_res = await client.delete(f"/api/v1/chat/conversations/{conv_2_id}", headers=headers)
        assert del_res.status_code == 200

        # Verify only conversation 1 remains
        post_del_list = await client.get("/api/v1/chat/conversations", headers=headers)
        assert post_del_list.status_code == 200
        remaining = post_del_list.json()
        assert len(remaining) == 1
        assert remaining[0]["id"] == conv_1_id
