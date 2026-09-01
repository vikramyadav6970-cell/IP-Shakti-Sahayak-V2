"""
backend/tests/test_chat_and_classification.py

Integration tests for Chat consultation, context threading, feedback, and product classification.
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
async def test_classification_and_chat_flow(test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register & Login
        await client.post(
            "/api/v1/auth/register",
            json={"name": "Vaidya Ananya", "email": "ananya@ayush.in", "password": "Password123!"},
        )
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "ananya@ayush.in", "password": "Password123!"},
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Product Classification
        class_payload = {
            "name": "Classical Haridra Khanda",
            "description": "Granular Ayurvedic preparation prepared per Bhaishajya Ratnavali for skin allergies.",
            "ingredients": ["Curcuma longa rhizome powder", "Cow ghee", "Milk", "Sugar"],
            "has_classical_text_reference": True,
            "classical_text_name": "Bhaishajya Ratnavali",
            "is_strict_classical_recipe": True,
            "has_novel_excipients_or_delivery": False,
        }
        res_class = await client.post("/api/v1/classification", headers=headers, json=class_payload)
        assert res_class.status_code == 200
        c_data = res_class.json()
        assert c_data["category"] == "CLASSICAL_MEDICINE"
        assert c_data["ip_protection_map"]["patent"]["eligibility"] == "EXCLUDED"
        class_id = c_data["id"]

        # 3. Chat with active classification context
        chat_payload = {
            "question": "Can I patent this Haridra Khanda formulation in India?",
            "jurisdiction": "INDIA",
            "active_classification_id": class_id,
            "active_intent": "PATENT",
        }
        res_chat = await client.post("/api/v1/chat", headers=headers, json=chat_payload)
        assert res_chat.status_code == 200
        chat_data = res_chat.json()
        assert "conversation_id" in chat_data
        assert "message_id" in chat_data
        assert "content" in chat_data
        conv_id = chat_data["conversation_id"]
        msg_id = chat_data["message_id"]

        # 4. Out of scope jurisdiction detection
        out_payload = {
            "question": "How do I file a 510(k) premarket notification with the US FDA?",
            "jurisdiction": "INDIA",
            "conversation_id": conv_id,
        }
        res_out = await client.post("/api/v1/chat", headers=headers, json=out_payload)
        assert res_out.status_code == 200
        out_data = res_out.json()
        assert out_data["out_of_scope_detected"] is True
        assert out_data["detected_jurisdiction"] == "INTERNATIONAL"

        # 5. Submit feedback
        res_fb = await client.post(
            f"/api/v1/chat/{msg_id}/feedback",
            headers=headers,
            json={"rating": 5, "comment": "Clear explanation of Section 3(p)!"},
        )
        assert res_fb.status_code == 201
        assert res_fb.json()["rating"] == 5

        # 6. Retrieve conversation history
        res_conv = await client.get(f"/api/v1/chat/conversations/{conv_id}", headers=headers)
        assert res_conv.status_code == 200
        conv_data = res_conv.json()
        assert len(conv_data["messages"]) >= 2
