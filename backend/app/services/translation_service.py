"""
backend/app/services/translation_service.py

Multilingual Translation Service for IP-SAKTI Sahayak using Sarvam AI Translation API.
Supports Indic languages: Hindi, Bengali, Gujarati, Kannada, Malayalam, Marathi, Odia, Punjabi, Tamil, Telugu, and English.
"""

import asyncio
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Standard BCP 47 language codes supported by Sarvam AI
SUPPORTED_INDIC_LANGUAGES = {
    "hi-IN": "Hindi",
    "bn-IN": "Bengali",
    "gu-IN": "Gujarati",
    "kn-IN": "Kannada",
    "ml-IN": "Malayalam",
    "mr-IN": "Marathi",
    "or-IN": "Odia",
    "od-IN": "Odia",
    "pa-IN": "Punjabi",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
    "en-IN": "English",
}

# Unicode block ranges for deterministic script detection
UNICODE_SCRIPT_PATTERNS = [
    (re.compile(r"[\u0900-\u097F]"), "hi-IN"),   # Devanagari (Hindi, Marathi, Sanskrit)
    (re.compile(r"[\u0980-\u09FF]"), "bn-IN"),   # Bengali
    (re.compile(r"[\u0A80-\u0AFF]"), "gu-IN"),   # Gujarati
    (re.compile(r"[\u0C80-\u0CFF]"), "kn-IN"),   # Kannada
    (re.compile(r"[\u0D00-\u0D7F]"), "ml-IN"),   # Malayalam
    (re.compile(r"[\u0B00-\u0B7F]"), "or-IN"),   # Odia
    (re.compile(r"[\u0A00-\u0A7F]"), "pa-IN"),   # Gurmukhi (Punjabi)
    (re.compile(r"[\u0B80-\u0BFF]"), "ta-IN"),   # Tamil
    (re.compile(r"[\u0C00-\u0C7F]"), "te-IN"),   # Telugu
]


class TranslationServiceError(Exception):
    """Custom exception raised when translation via Sarvam AI fails."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class TranslationService:
    """
    Async client for Sarvam AI Translation and Language Detection.
    Handles timeout, exponential backoff retries, and graceful fallbacks.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: float = 10.0,
        max_retries: int = 1,
    ):
        self.api_key = api_key or settings.SARVAM_API_KEY
        self.base_url = (base_url or settings.SARVAM_API_BASE_URL or "https://api.sarvam.ai").rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def detect_language(self, text: str) -> str:
        """
        Detects language of input text using deterministic Unicode script analysis.
        Returns BCP-47 language tag (e.g. 'hi-IN', 'ta-IN', 'en-IN').
        """
        if not text or not text.strip():
            return "en-IN"

        # Count character frequencies across Indic script ranges
        script_counts: Dict[str, int] = {}
        for pattern, lang_code in UNICODE_SCRIPT_PATTERNS:
            matches = len(pattern.findall(text))
            if matches > 0:
                script_counts[lang_code] = matches

        if script_counts:
            # Pick language with the highest script character count
            detected_lang = max(script_counts.items(), key=lambda x: x[1])[0]
            logger.debug(f"[LanguageDetector] Detected Indic language: {detected_lang} (chars: {script_counts[detected_lang]})")
            return detected_lang

        return "en-IN"

    def normalize_language_code(self, lang_code: Optional[str]) -> str:
        """Normalizes input language codes (e.g. 'hi', 'hindi', 'hi-IN') to standard format."""
        if not lang_code or lang_code.lower() in ["auto", "default"]:
            return "auto"

        clean = lang_code.strip().lower()
        if clean in ["en", "en-in", "english"]:
            return "en-IN"
        if clean in ["hi", "hi-in", "hindi"]:
            return "hi-IN"
        if clean in ["bn", "bn-in", "bengali", "bangla"]:
            return "bn-IN"
        if clean in ["gu", "gu-in", "gujarati"]:
            return "gu-IN"
        if clean in ["kn", "kn-in", "kannada"]:
            return "kn-IN"
        if clean in ["ml", "ml-in", "malayalam"]:
            return "ml-IN"
        if clean in ["mr", "mr-in", "marathi"]:
            return "mr-IN"
        if clean in ["or", "or-in", "od", "od-in", "odia", "oriya"]:
            return "or-IN"
        if clean in ["pa", "pa-in", "punjabi"]:
            return "pa-IN"
        if clean in ["ta", "ta-in", "tamil"]:
            return "ta-IN"
        if clean in ["te", "te-in", "telugu"]:
            return "te-IN"

        return lang_code if lang_code in SUPPORTED_INDIC_LANGUAGES else "en-IN"

    async def _call_sarvam_translate_api(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """
        Executes HTTP POST call to Sarvam AI Translation endpoint with retry logic.
        """
        if not self.api_key:
            raise TranslationServiceError("SARVAM_API_KEY is not configured in backend environment.")

        endpoint = f"{self.base_url}/translate"
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "input": text,
            "source_language_code": source_lang,
            "target_language_code": target_lang,
            "speaker_gender": "Male",
            "mode": "formal",
            "model": "mayura:v1",
            "enable_preprocessing": True,
        }

        last_err: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            start_time = time.time()
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(endpoint, json=payload, headers=headers)
                    elapsed_ms = int((time.time() - start_time) * 1000)

                    logger.info(
                        f"[SarvamTranslation] {source_lang}->{target_lang} "
                        f"len={len(text)} status={response.status_code} elapsed={elapsed_ms}ms"
                    )

                    if response.status_code == 200:
                        data = response.json()
                        translated_text = data.get("translated_text")
                        if translated_text:
                            return translated_text.strip()
                        raise TranslationServiceError("Invalid response structure from Sarvam AI: missing 'translated_text'")

                    error_detail = response.text[:200]
                    raise TranslationServiceError(
                        f"Sarvam AI Translation API returned HTTP {response.status_code}: {error_detail}"
                    )

            except httpx.TimeoutException as exc:
                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.warning(
                    f"[SarvamTranslation] Timeout on attempt {attempt + 1}/{self.max_retries + 1} ({elapsed_ms}ms)"
                )
                last_err = exc
            except Exception as exc:
                logger.warning(
                    f"[SarvamTranslation] Error on attempt {attempt + 1}/{self.max_retries + 1}: {exc}"
                )
                last_err = exc

            if attempt < self.max_retries:
                await asyncio.sleep(0.5 * (attempt + 1))

        raise TranslationServiceError(
            f"Sarvam AI translation failed after {self.max_retries + 1} attempts.",
            original_error=last_err,
        )

    def _split_text_into_chunks(self, text: str, max_chars: int = 1400) -> List[str]:
        """
        Splits text into chunks <= max_chars respecting markdown paragraph,
        newline, sentence, and word boundaries.
        """
        if not text or len(text) <= max_chars:
            return [text] if text else []

        chunks: List[str] = []
        paragraphs = text.split("\n\n")
        current_chunk = ""

        for para in paragraphs:
            if not para:
                continue

            if len(para) > max_chars:
                lines = para.split("\n")
                for line in lines:
                    if len(line) > max_chars:
                        sentences = re.split(r"(?<=[.?!])\s+", line)
                        for sentence in sentences:
                            if len(current_chunk) + len(sentence) + 1 <= max_chars:
                                current_chunk = f"{current_chunk} {sentence}".strip()
                            else:
                                if current_chunk:
                                    chunks.append(current_chunk)
                                current_chunk = sentence
                    else:
                        if len(current_chunk) + len(line) + 1 <= max_chars:
                            current_chunk = f"{current_chunk}\n{line}".strip()
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = line
            else:
                if len(current_chunk) + len(para) + 2 <= max_chars:
                    current_chunk = f"{current_chunk}\n\n{para}".strip()
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    async def translate_to_english(self, text: str, source_lang: str) -> str:
        """
        Translates user query from source_lang to English (en-IN).
        If source_lang is already English, returns text as-is without API call.
        """
        norm_source = self.normalize_language_code(source_lang)
        if norm_source in ["en-IN", "en", "auto"]:
            detected = self.detect_language(text)
            if detected in ["en-IN", "en"]:
                return text
            norm_source = detected

        if len(text) <= 1400:
            return await self._call_sarvam_translate_api(
                text=text,
                source_lang=norm_source,
                target_lang="en-IN",
            )

        chunks = self._split_text_into_chunks(text, max_chars=1400)
        tasks = [
            self._call_sarvam_translate_api(
                text=chunk,
                source_lang=norm_source,
                target_lang="en-IN",
            )
            for chunk in chunks
        ]
        translated_chunks = await asyncio.gather(*tasks)
        return "\n\n".join(translated_chunks)

    async def translate_from_english(self, text: str, target_lang: str) -> str:
        """
        Translates generated English answer back into target_lang.
        If target_lang is English, returns text as-is without API call.
        Handles text chunking if text exceeds Sarvam AI's 2000 character limit.
        """
        norm_target = self.normalize_language_code(target_lang)
        if norm_target in ["en-IN", "en", "auto"]:
            return text

        if len(text) <= 1400:
            return await self._call_sarvam_translate_api(
                text=text,
                source_lang="en-IN",
                target_lang=norm_target,
            )

        chunks = self._split_text_into_chunks(text, max_chars=1400)
        logger.info(
            f"[SarvamTranslation] Chunking text ({len(text)} chars -> {len(chunks)} chunks) for {norm_target}"
        )
        tasks = [
            self._call_sarvam_translate_api(
                text=chunk,
                source_lang="en-IN",
                target_lang=norm_target,
            )
            for chunk in chunks
        ]
        translated_chunks = await asyncio.gather(*tasks)
        return "\n\n".join(translated_chunks)

    async def safe_translate_to_english(
        self, text: str, source_lang: str
    ) -> Tuple[str, bool, Optional[str]]:
        """
        Safe wrapper for input translation.
        Returns: (translated_or_original_text, is_success, error_message)
        """
        norm_source = self.normalize_language_code(source_lang)
        if norm_source == "auto":
            norm_source = self.detect_language(text)

        if norm_source in ["en-IN", "en"]:
            return text, True, None

        try:
            translated = await self.translate_to_english(text, source_lang=norm_source)
            return translated, True, None
        except Exception as err:
            logger.error(f"[TranslationService] Input translation error: {err}")
            return text, False, str(err)

    async def safe_translate_from_english(
        self, text: str, target_lang: str
    ) -> Tuple[str, bool, Optional[str]]:
        """
        Safe wrapper for output translation.
        Returns: (translated_or_original_text, is_success, error_message)
        """
        norm_target = self.normalize_language_code(target_lang)
        if norm_target in ["en-IN", "en", "auto"]:
            return text, True, None

        try:
            translated = await self.translate_from_english(text, target_lang=norm_target)
            return translated, True, None
        except Exception as err:
            logger.error(f"[TranslationService] Output translation error: {err}")
            return text, False, str(err)


# Singleton service instance
translation_service = TranslationService()
