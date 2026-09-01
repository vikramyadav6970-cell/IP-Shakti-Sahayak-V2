"""
backend/tests/test_translation_service.py

Unit tests for TranslationService (Sarvam AI Translation API client,
Unicode script detection, retry mechanism, and safe fallback handling).
"""

import pytest
from unittest.mock import AsyncMock, patch
import httpx

from app.services.translation_service import (
    TranslationService,
    TranslationServiceError,
    translation_service,
)


def test_language_detection_indic_scripts():
    """Verifies deterministic Unicode detection for major Indian scripts and English."""
    ts = TranslationService()

    assert ts.detect_language("त्रिफला चूर्ण की पेटेंटेबिलिटी क्या है?") == "hi-IN"
    assert ts.detect_language("ত্রিফলা চূর্ণের পেটেন্ট সংক্রান্ত তথ্য") == "bn-IN"
    assert ts.detect_language("திரிபலா சூரணம் காப்புரிமை விவரங்கள்") == "ta-IN"
    assert ts.detect_language("త్రిఫల చూర్ణం పేటెంట్ సమాచారం") == "te-IN"
    assert ts.detect_language("ત્રિફળા ચૂર્ણ પેટન્ટ માહિતી") == "gu-IN"
    assert ts.detect_language("ತ್ರಿಫಲ ಚೂರ್ಣ ಪೇಟೆಂಟ್ ವಿವರ") == "kn-IN"
    assert ts.detect_language("ത്രിഫല ചൂർണ്ണം പേറ്റന്റ് വിവരങ്ങൾ") == "ml-IN"
    assert ts.detect_language("ਤ੍ਰਿਫਲਾ ਚੂਰਨ ਪੇਟੈਂਟ ਜਾਣਕਾਰੀ") == "pa-IN"
    assert ts.detect_language("ତ୍ରିଫଳା ଚୂର୍ଣ୍ଣ ପେଟେଣ୍ଟ ବିବରଣୀ") == "or-IN"
    assert ts.detect_language("What is the Section 3(p) patent eligibility of Triphala?") == "en-IN"
    assert ts.detect_language("") == "en-IN"


def test_normalize_language_code():
    """Verifies normalization of user-entered language aliases."""
    ts = TranslationService()

    assert ts.normalize_language_code("hi") == "hi-IN"
    assert ts.normalize_language_code("HINDI") == "hi-IN"
    assert ts.normalize_language_code("hi-IN") == "hi-IN"
    assert ts.normalize_language_code("bn") == "bn-IN"
    assert ts.normalize_language_code("ta") == "ta-IN"
    assert ts.normalize_language_code("te") == "te-IN"
    assert ts.normalize_language_code("en") == "en-IN"
    assert ts.normalize_language_code("english") == "en-IN"
    assert ts.normalize_language_code("auto") == "auto"


@pytest.mark.asyncio
async def test_english_skips_translation_api():
    """English text must never trigger external API calls."""
    ts = TranslationService(api_key="mock_key")

    with patch("httpx.AsyncClient.post") as mock_post:
        res_in = await ts.translate_to_english("Is Triphala patentable?", source_lang="en-IN")
        assert res_in == "Is Triphala patentable?"
        mock_post.assert_not_called()

        res_out = await ts.translate_from_english("Form 25-D is required.", target_lang="en-IN")
        assert res_out == "Form 25-D is required."
        mock_post.assert_not_called()


@pytest.mark.asyncio
async def test_successful_sarvam_translation():
    """Verifies successful payload formation and response parsing from Sarvam AI."""
    ts = TranslationService(api_key="valid_key", base_url="https://api.sarvam.ai")

    mock_resp = httpx.Response(
        status_code=200,
        json={"translated_text": "What is the patent status of Triphala Churna?"},
        request=httpx.Request("POST", "https://api.sarvam.ai/translate"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        result = await ts.translate_to_english("त्रिफला चूर्ण का पेटेंट क्या है?", source_lang="hi-IN")
        assert result == "What is the patent status of Triphala Churna?"
        assert mock_post.call_count == 1

        # Check call arguments
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["source_language_code"] == "hi-IN"
        assert call_kwargs["json"]["target_language_code"] == "en-IN"
        assert call_kwargs["headers"]["api-subscription-key"] == "valid_key"


@pytest.mark.asyncio
async def test_retry_and_safe_fallback_on_failure():
    """Verifies retry mechanism and safe fallback when API fails or times out."""
    ts = TranslationService(api_key="mock_key", max_retries=1, timeout_seconds=1.0)

    # Simulate HTTP 500 error
    error_resp = httpx.Response(
        status_code=500,
        text="Internal Server Error",
        request=httpx.Request("POST", "https://api.sarvam.ai/translate"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = error_resp

        # Direct call raises TranslationServiceError after retries
        with pytest.raises(TranslationServiceError):
            await ts.translate_to_english("नमस्ते", source_lang="hi-IN")

        assert mock_post.call_count == 2  # 1 initial + 1 retry

    # Safe wrapper returns fallback without crashing
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = error_resp

        text, ok, err = await ts.safe_translate_to_english("नमस्ते", source_lang="hi-IN")
        assert text == "नमस्ते"
        assert ok is False
        assert err is not None

        out_text, out_ok, out_err = await ts.safe_translate_from_english("Hello", target_lang="hi-IN")
        assert out_text == "Hello"
        assert out_ok is False


def test_split_text_into_chunks():
    """Verifies that long text is cleanly chunked without breaking sentences or exceeding character limits."""
    ts = TranslationService()

    short_text = "This is a short text."
    assert ts._split_text_into_chunks(short_text, max_chars=1400) == [short_text]

    # Create long text of 3500 chars across paragraphs
    para1 = "Paragraph 1: " + "This is a detailed legal analysis under Section 3(p). " * 20
    para2 = "Paragraph 2: " + "Here are the manufacturing license requirements under Rule 153. " * 20
    long_text = f"{para1}\n\n{para2}"

    chunks = ts._split_text_into_chunks(long_text, max_chars=1400)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= 1400


@pytest.mark.asyncio
async def test_translate_from_english_long_text_chunks_concurrently():
    """Verifies that long answers exceeding Sarvam character limits are chunked and translated concurrently."""
    ts = TranslationService(api_key="valid_key")

    para1 = "Paragraph 1: " + "This is a detailed legal analysis under Section 3(p). " * 20
    para2 = "Paragraph 2: " + "Here are the manufacturing license requirements under Rule 153. " * 20
    long_text = f"{para1}\n\n{para2}"

    mock_resp = httpx.Response(
        status_code=200,
        json={"translated_text": "अनुवादित कानूनी विश्लेषण"},
        request=httpx.Request("POST", "https://api.sarvam.ai/translate"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        result = await ts.translate_from_english(long_text, target_lang="hi-IN")
        assert "अनुवादित कानूनी विश्लेषण" in result
        assert mock_post.call_count >= 2  # Proves text was chunked and multiple calls were made
