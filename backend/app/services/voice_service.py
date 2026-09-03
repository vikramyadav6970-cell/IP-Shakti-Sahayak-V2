"""
backend/app/services/voice_service.py

Voice Speech-to-Text (STT) and Text-to-Speech (TTS) Service for IP-SAKTI Sahayak
utilizing Sarvam AI's Speech & Audio APIs (saaras:v3 & bulbul:v3).
"""

import asyncio
import base64
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def strip_markdown_for_speech(text: str) -> str:
    """
    Sanitizes assistant markdown responses into natural, clean spoken text for TTS.
    - Strips [[PRODUCT_CONTEXT: ...]] JSON blocks completely (never read out JSON braces/keys)
    - Strips headers (### Header -> Header)
    - Strips bold/italic markers (**bold** -> bold, *italic* -> italic)
    - Strips markdown links ([Title](URL) -> Title)
    - Strips inline code blocks (`code` -> code)
    - Strips horizontal rules (---)
    - Strips bullet points (- bullet -> bullet)
    - Normalizes numbered lists (1. Item -> 1. Item)
    - Normalizes multiple newlines and spaces into natural pauses
    """
    if not text:
        return ""

    # 1. Remove PRODUCT_CONTEXT JSON block entirely — never speak raw JSON
    text = re.sub(r"\[\[PRODUCT_CONTEXT:.*?\]\]", "", text, flags=re.DOTALL)

    # 2. Markdown links: [Link Text](http://...) -> Link Text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

    # 3. Inline code & code blocks: `code` -> code
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # 4. Headers: "### Foo" -> "Foo"
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

    # 5. Bold & Italic: **text** or *text* or __text__ or _text_ -> text
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"_(.*?)_", r"\1", text)

    # 6. Horizontal rules: --- or ___ or ***
    text = re.sub(r"^\s*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    # 7. Bullet markers: "- ", "* ", "+ " -> drop the symbol, keep the text
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)

    # 8. Numbered list markers: "1. Foo" -> "1. Foo"
    text = re.sub(r"^\s*(\d+)\.\s+", r"\1. ", text, flags=re.MULTILINE)

    # 9. Blockquotes: "> quote" -> quote
    text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)

    # 10. Collapse extra whitespace and newlines into natural speech flow
    text = re.sub(r"\n{2,}", ". ", text)
    text = re.sub(r"\n", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+\.", ".", text)
    text = re.sub(r"\.{2,}", ".", text)

    return text.strip()

# Default high-quality speakers for Sarvam bulbul:v3 model per language code
DEFAULT_TTS_SPEAKERS: Dict[str, str] = {
    "hi-IN": "priya",
    "en-IN": "aditya",
    "bn-IN": "tanya",
    "gu-IN": "shubh",
    "kn-IN": "kavitha",
    "ml-IN": "gokul",
    "mr-IN": "rupali",
    "or-IN": "priya",
    "pa-IN": "simran",
    "ta-IN": "mani",
    "te-IN": "vijay",
}


class VoiceServiceError(Exception):
    """Custom exception raised when Sarvam Speech API operations fail."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class VoiceService:
    """
    Async client for Sarvam AI Speech-to-Text and Text-to-Speech.
    Provides robust retry, timeouts, and graceful fallbacks.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        stt_timeout: float = 15.0,
        tts_timeout: float = 20.0,
        max_retries: int = 1,
    ):
        self.api_key = api_key or settings.SARVAM_API_KEY
        self.base_url = (base_url or settings.SARVAM_API_BASE_URL or "https://api.sarvam.ai").rstrip("/")
        self.stt_timeout = stt_timeout
        self.tts_timeout = tts_timeout
        self.max_retries = max_retries

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        filename: str = "recording.wav",
        mime_type: str = "audio/wav",
        language_code: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Transcribes incoming user speech into text via Sarvam STT (saaras:v3).
        Returns (transcript_text, detected_or_resolved_language_code).
        """
        if not self.api_key:
            raise VoiceServiceError("SARVAM_API_KEY is not configured in backend environment.")

        endpoint = f"{self.base_url}/speech-to-text"
        headers = {
            "api-subscription-key": self.api_key,
        }

        # Resolve language code parameter for Sarvam STT
        lang_param = language_code if language_code and language_code != "auto" else "unknown"

        # Allowed MIME types by Sarvam STT API:
        # ['audio/mpeg', 'audio/mp3', 'audio/mpeg3', 'audio/x-mpeg-3', 'audio/x-mp3', 'audio/wav', 'audio/x-wav', 'audio/wave', 'audio/pcm_s16le', 'audio/l16', 'audio/raw', 'application/octet-stream']
        allowed_mimes = {
            "audio/wav", "audio/x-wav", "audio/wave", "audio/mpeg", "audio/mp3",
            "audio/mpeg3", "audio/pcm_s16le", "audio/l16", "audio/raw", "application/octet-stream"
        }
        resolved_mime = mime_type if mime_type in allowed_mimes else "audio/wav"
        resolved_filename = filename if (filename and filename.endswith((".wav", ".mp3", ".mpeg"))) else "recording.wav"

        files = {
            "file": (resolved_filename, audio_bytes, resolved_mime),
        }
        data = {
            "model": "saaras:v3",
            "language_code": lang_param,
        }

        last_err: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            t0 = time.time()
            try:
                async with httpx.AsyncClient(timeout=self.stt_timeout) as client:
                    response = await client.post(endpoint, headers=headers, files=files, data=data)
                    elapsed_ms = int((time.time() - t0) * 1000)

                    logger.info(
                        f"[SarvamSTT] bytes={len(audio_bytes)} status={response.status_code} elapsed={elapsed_ms}ms"
                    )

                    if response.status_code == 200:
                        res_json = response.json()
                        transcript = res_json.get("transcript", "").strip()
                        detected_lang = res_json.get("language_code", language_code or "en-IN")
                        return transcript, detected_lang

                    error_detail = response.text[:250]
                    raise VoiceServiceError(f"Sarvam STT returned HTTP {response.status_code}: {error_detail}")

            except httpx.TimeoutException as exc:
                elapsed_ms = int((time.time() - t0) * 1000)
                logger.warning(f"[SarvamSTT] Timeout on attempt {attempt + 1}/{self.max_retries + 1} ({elapsed_ms}ms)")
                last_err = exc
            except Exception as exc:
                logger.warning(f"[SarvamSTT] Error on attempt {attempt + 1}/{self.max_retries + 1}: {exc}")
                last_err = exc

            if attempt < self.max_retries:
                await asyncio.sleep(0.5 * (attempt + 1))

        raise VoiceServiceError(
            f"Sarvam STT failed after {self.max_retries + 1} attempts.",
            original_error=last_err,
        )

    async def synthesize_speech(
        self,
        text: str,
        target_language_code: str = "en-IN",
        speaker: Optional[str] = None,
        pace: float = 1.0,
    ) -> Optional[str]:
        """
        Synthesizes text to spoken audio via Sarvam TTS (bulbul:v3).
        Returns base64-encoded WAV audio string, or None if synthesis fails (graceful degradation).
        """
        if not self.api_key:
            logger.warning("[SarvamTTS] SARVAM_API_KEY not configured; skipping audio synthesis.")
            return None

        # Sanitize markdown formatting and strip [[PRODUCT_CONTEXT: ...]] JSON blocks for spoken audio
        clean_text = strip_markdown_for_speech(text)
        if not clean_text:
            return None

        # Truncate for TTS input if text exceeds comfortable audio buffer (max ~500 chars for crisp voice response)
        # Note: Full advisory details and markdown formatting remain fully intact in the visual chat UI
        tts_input_text = clean_text
        if len(tts_input_text) > 500:
            tts_input_text = tts_input_text[:497] + "..."

        # Resolve speaker
        lang = target_language_code if target_language_code in DEFAULT_TTS_SPEAKERS else "en-IN"
        chosen_speaker = speaker or DEFAULT_TTS_SPEAKERS.get(lang, "priya")

        endpoint = f"{self.base_url}/text-to-speech"
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": [tts_input_text],
            "target_language_code": lang,
            "speaker": chosen_speaker,
            "model": "bulbul:v3",
            "pace": max(0.5, min(2.0, pace)),
        }

        t0 = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.tts_timeout) as client:
                response = await client.post(endpoint, headers=headers, json=payload)
                elapsed_ms = int((time.time() - t0) * 1000)

                logger.info(
                    f"[SarvamTTS] lang={lang} speaker={chosen_speaker} status={response.status_code} elapsed={elapsed_ms}ms"
                )

                if response.status_code == 200:
                    res_json = response.json()
                    audios = res_json.get("audios", [])
                    if audios and len(audios) > 0:
                        return audios[0]
                    logger.warning("[SarvamTTS] Empty 'audios' list returned from TTS API.")
                    return None

                logger.warning(
                    f"[SarvamTTS] API returned HTTP {response.status_code}: {response.text[:200]}; falling back to text-only."
                )
                return None

        except httpx.TimeoutException:
            elapsed_ms = int((time.time() - t0) * 1000)
            logger.warning(f"[SarvamTTS] Timeout ({elapsed_ms}ms); falling back to text-only.")
            return None
        except Exception as exc:
            logger.warning(f"[SarvamTTS] Synthesis exception: {exc}; falling back to text-only.")
            return None


# Global singleton instance
voice_service = VoiceService()
