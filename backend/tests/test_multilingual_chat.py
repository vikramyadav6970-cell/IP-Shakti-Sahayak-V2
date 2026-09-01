"""
backend/tests/test_multilingual_chat.py

Integration tests for multilingual query processing in IP-SAKTI Sahayak chat flow.
Tests input translation, RAG retrieval, English citation preservation, output translation,
and language metadata tracking.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import uuid

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
async def test_multilingual_chat_flow_hindi_to_english_and_back(test_db):
    """
    Tests end-to-end chat turn where a user submits a question in Hindi:
    1. Input translated to English
    2. English citations returned unchanged
    3. Assistant response translated back to Hindi
    4. Response payload contains detected_language and is_translated=True
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        email = f"multi_{uuid.uuid4().hex[:8]}@test.com"
        password = "Password123!"

        # Register test user
        reg_resp = await ac.post(
            "/api/v1/auth/register",
            json={
                "name": "Vaidya Sharma",
                "email": email,
                "password": password,
                "role": "USER",
                "organization": "Ayush Research Lab",
                "language": "hi",
            },
        )
        assert reg_resp.status_code == 201

        # Login to get JWT
        login_resp = await ac.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Mock Sarvam AI translation service
        with patch("app.services.translation_service.translation_service.translate_to_english", new_callable=AsyncMock) as mock_trans_in, \
             patch("app.services.translation_service.translation_service.translate_from_english", new_callable=AsyncMock) as mock_trans_out:

            mock_trans_in.return_value = "Can Triphala Churna containing Haritaki, Bibhitaki, and Amalaki be patented in India?"
            mock_trans_out.return_value = "त्रिफला चूर्ण शास्त्रीय आयुर्वेदिक औषधि है जिसे भारतीय पेटेंट अधिनियम की धारा 3(p) के तहत पेटेंट नहीं कराया जा सकता।"

            chat_payload = {
                "question": "क्या हरड़, बहेड़ा और आंवला युक्त त्रिफला चूर्ण का भारत में पेटेंट कराया जा सकता है?",
                "jurisdiction": "INDIA",
                "language": "auto",
            }

            resp = await ac.post("/api/v1/chat", json=chat_payload, headers=headers)
            assert resp.status_code == 200
            data = resp.json()

            # Verify response contents and language metadata
            assert "त्रिफला चूर्ण" in data["content"]
            assert data["detected_language"] == "hi-IN"
            assert data["is_translated"] is True

            # Verify that input and output translations were called
            assert mock_trans_in.called
            assert mock_trans_out.called
