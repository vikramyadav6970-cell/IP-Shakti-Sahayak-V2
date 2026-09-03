"""
backend/tests/test_voice_chat.py

Comprehensive test suite for Full Hands-Free Voice Conversation Mode:
- Audio upload & transcription (STT)
- Multi-Agent RAG execution & translation
- Spoken audio synthesis (TTS) & fallback resilience
- Regression safety for text chat endpoints
"""

import io
import os
import sys
import wave
import struct
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

# Path setup
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir.parent / "ai"))

from app.database import get_db
from app.main import app
from app.models.base import Base
from app.services.voice_service import voice_service


def create_dummy_wav_bytes(duration_sec: float = 1.0) -> bytes:
    """Generates synthetic 16kHz mono PCM WAV bytes for test uploads."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        n_frames = int(16000 * duration_sec)
        for _ in range(n_frames):
            wf.writeframes(struct.pack("<h", 0))
    buf.seek(0)
    return buf.read()


@pytest_asyncio.fixture
async def test_db():
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
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


async def get_test_auth_headers(client: AsyncClient) -> dict:
    """Helper to register and authenticate a test innovator user."""
    import uuid
    email = f"voice_{uuid.uuid4().hex[:8]}@ipsakti.gov.in"
    password = "VoicePassword123!"
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Voice Innovator",
            "email": email,
            "password": password,
            "role": "USER",
        },
    )
    assert reg_resp.status_code == 201, reg_resp.text

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_voice_chat_english_flow(test_db):
    """Tests complete English voice consultation with STT, RAG, and TTS audio synthesis."""
    wav_bytes = create_dummy_wav_bytes(1.0)

    # Mock voice service STT & TTS methods
    mock_stt = AsyncMock(return_value=("Can I patent my Ashwagandha formulation under Section 3(p)?", "en-IN"))
    mock_tts = AsyncMock(return_value="UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=")

    with patch.object(voice_service, "transcribe_audio", mock_stt), \
         patch.object(voice_service, "synthesize_speech", mock_tts):

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            headers = await get_test_auth_headers(client)
            files = {
                "file": ("recording.wav", wav_bytes, "audio/wav"),
            }
            data = {
                "jurisdiction": "INDIA",
                "language": "en-IN",
            }

            resp = await client.post("/api/v1/chat/voice", files=files, data=data, headers=headers)
            assert resp.status_code == 200, resp.text
            res_json = resp.json()

            # Verify response schema fields
            assert res_json["transcribed_text"] == "Can I patent my Ashwagandha formulation under Section 3(p)?"
            assert res_json["content"] is not None
            assert len(res_json["content"]) > 10
            assert res_json["audio_base64"] == "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA="
            assert res_json["audio_format"] == "audio/wav"
            assert "conversation_id" in res_json
            assert "message_id" in res_json


@pytest.mark.asyncio
async def test_voice_chat_indic_hindi_flow(test_db):
    """Tests multilingual Indic voice consultation with Hindi STT and Hindi TTS audio synthesis."""
    wav_bytes = create_dummy_wav_bytes(1.0)

    hindi_query = "क्या मैं अपनी अश्वगंधा दवा का पेटेंट करा सकता हूँ?"
    mock_stt = AsyncMock(return_value=(hindi_query, "hi-IN"))
    mock_tts = AsyncMock(return_value="UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=")

    with patch.object(voice_service, "transcribe_audio", mock_stt), \
         patch.object(voice_service, "synthesize_speech", mock_tts):

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            headers = await get_test_auth_headers(client)
            files = {
                "file": ("recording.wav", wav_bytes, "audio/wav"),
            }
            data = {
                "jurisdiction": "INDIA",
                "language": "hi-IN",
            }

            resp = await client.post("/api/v1/chat/voice", files=files, data=data, headers=headers)
            assert resp.status_code == 200, resp.text
            res_json = resp.json()

            assert res_json["transcribed_text"] == hindi_query
            assert res_json["detected_language"] in ["hi-IN", "hi"] or res_json["is_translated"] is True
            assert res_json["audio_base64"] is not None


@pytest.mark.asyncio
async def test_voice_chat_tts_failure_fallback(test_db):
    """
    Tests graceful degradation: when Sarvam TTS fails or times out,
    the endpoint still returns 200 OK with full text advisory and audio_base64=None.
    """
    wav_bytes = create_dummy_wav_bytes(1.0)

    mock_stt = AsyncMock(return_value=("What is Section 3(p) of the Indian Patents Act?", "en-IN"))
    mock_tts = AsyncMock(return_value=None)  # Simulate TTS API failure

    with patch.object(voice_service, "transcribe_audio", mock_stt), \
         patch.object(voice_service, "synthesize_speech", mock_tts):

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            headers = await get_test_auth_headers(client)
            files = {
                "file": ("recording.wav", wav_bytes, "audio/wav"),
            }
            data = {
                "jurisdiction": "INDIA",
            }

            resp = await client.post("/api/v1/chat/voice", files=files, data=data, headers=headers)
            assert resp.status_code == 200, resp.text
            res_json = resp.json()

            # Must succeed with text answer even without audio
            assert res_json["content"] is not None
            assert res_json["audio_base64"] is None


@pytest.mark.asyncio
async def test_voice_chat_empty_audio_rejection(test_db):
    """Confirms empty audio payload returns 400 Bad Request."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await get_test_auth_headers(client)
        files = {
            "file": ("empty.wav", b"", "audio/wav"),
        }
        resp = await client.post("/api/v1/chat/voice", files=files, data={}, headers=headers)
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_text_chat_endpoint_regression(test_db):
    """Confirms existing text chat endpoint POST /api/v1/chat is completely unaffected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await get_test_auth_headers(client)
        payload = {
            "question": "Can I patent traditional Ayurvedic formulation in India?",
            "query": "Can I patent traditional Ayurvedic formulation in India?",
            "jurisdiction": "INDIA",
        }
        resp = await client.post("/api/v1/chat", json=payload, headers=headers)
        assert resp.status_code == 200
        res_json = resp.json()
        assert "content" in res_json
        assert "conversation_id" in res_json


def test_strip_markdown_for_speech():
    """Confirms markdown and PRODUCT_CONTEXT JSON are stripped for natural TTS speech."""
    from app.services.voice_service import strip_markdown_for_speech

    raw_markdown = """### **Patentability Assessment (Section 3(p))**

Based on the [Indian Patents Act, 1970](https://ipindia.gov.in), your formulation has the following:

---

1. **Section 3(p) Traditional Knowledge:**
   - Classical formulations found in *Ayurvedic texts* cannot be patented.
   - Synergy must be proven under `Section 3(e)`.

2. **ABS Approval:**
   - Prior approval from the **National Biodiversity Authority (NBA)** via **Form 1**.

---
[[PRODUCT_CONTEXT:{"state": "CLASSIFIED", "product_name": "Ashwagandha Extract", "category": "Classical Medicine"}]]
"""
    spoken = strip_markdown_for_speech(raw_markdown)
    assert "###" not in spoken
    assert "**" not in spoken
    assert "---" not in spoken
    assert "PRODUCT_CONTEXT" not in spoken
    assert "{" not in spoken and "}" not in spoken
    assert "https://" not in spoken
    assert "`" not in spoken
    assert "Patentability Assessment (Section 3(p))" in spoken
    assert "Classical formulations found in Ayurvedic texts cannot be patented" in spoken
