"""
ai/src/reasoning/llm_provider.py

Provider abstraction for Google Gemini LLM (gemini-3.6-flash).
Adheres to ai/coding_conventions.md:
- Never call provider SDKs directly in pipeline code; call through LLMProvider.
- Model name and API keys are driven by environment variables.
"""

from abc import ABC, abstractmethod
import json
import os
from pathlib import Path
from typing import Any, Optional
import urllib.request
import urllib.error

try:
    from dotenv import load_dotenv
    # Load environment variables from all workspace .env files
    _root = Path(__file__).resolve().parent.parent.parent.parent
    for _env_path in [
        _root / ".env",
        _root / "backend" / ".env",
        _root / "ai" / ".env",
    ]:
        if _env_path.exists():
            load_dotenv(_env_path, override=True)
except Exception:
    pass


class LLMProvider(ABC):
    """Abstract interface for LLM text generation."""

    def __init__(self, model_name: str, api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> str:
        """
        Generate text synchronously from the LLM given a system and user prompt.
        """
        pass

    async def generate_async(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> str:
        """Asynchronous generation fallback (default delegates to sync generate)."""
        return self.generate(system_prompt, user_prompt, **kwargs)


_GENAI_CLIENT = None
_GEMINI_HTTP_CLIENT = None


def _get_genai_client(api_key: str):
    global _GENAI_CLIENT
    if _GENAI_CLIENT is None:
        try:
            from google import genai
            _GENAI_CLIENT = genai.Client(api_key=api_key)
        except Exception:
            _GENAI_CLIENT = None
    return _GENAI_CLIENT


def _get_gemini_client():
    global _GEMINI_HTTP_CLIENT
    if _GEMINI_HTTP_CLIENT is None:
        try:
            import httpx
            _GEMINI_HTTP_CLIENT = httpx.Client(timeout=30.0)
        except Exception:
            _GEMINI_HTTP_CLIENT = None
    return _GEMINI_HTTP_CLIENT


class GeminiProvider(LLMProvider):
    """Google Gemini provider implementation (dynamically driven by LLM_MODEL in .env)."""

    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        model = model_name or os.environ.get("LLM_MODEL") or "gemini-2.5-flash"
        # Strip any accidental prefixes like 'models/'
        if model.startswith("models/"):
            model = model.replace("models/", "")
        super().__init__(model_name=model, api_key=key)

    def generate(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is missing.")

        # Primary: Official google-genai SDK (persistent client)
        try:
            from google.genai import types

            client = _get_genai_client(self.api_key)
            if client is None:
                from google import genai
                client = genai.Client(api_key=self.api_key)

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                temperature=kwargs.get("temperature", 0.1),
                max_output_tokens=kwargs.get("max_tokens", 2048),
            )
            response = client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=config,
            )
            output_text = response.text or ""
            print("\n===== LLM RESPONSE =====")
            print(output_text[:300] + ("..." if len(output_text) > 300 else ""))
            print("========================\n")
            return output_text
        except Exception as e_sdk:
            print(f"[Gemini SDK Primary Notice]: {e_sdk}, trying REST fallback...")
            # Fallback: Direct REST API
            return self._generate_rest(system_prompt, user_prompt, **kwargs)

    def _generate_rest(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> str:
        """Call Google Gemini REST API directly with connection pooling."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        
        payload: dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": user_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.1),
                "maxOutputTokens": kwargs.get("max_tokens", 2048),
            }
        }
        if system_prompt:
            payload["system_instruction"] = {
                "parts": [{"text": system_prompt}]
            }

        client = _get_gemini_client()
        if client:
            try:
                resp = client.post(url, json=payload, timeout=20.0)
                if resp.status_code == 200:
                    resp_data = resp.json()
                    candidates = resp_data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        text_parts = [p.get("text", "") for p in parts if "text" in p]
                        output_text = "".join(text_parts)
                        return output_text
            except Exception:
                pass

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=20) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            candidates = resp_data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                text_parts = [p.get("text", "") for p in parts if "text" in p]
                output_text = "".join(text_parts)
                return output_text
            raise ValueError(f"No candidates returned from Gemini REST API: {resp_data}")


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation (driven by LLM_MODEL in .env)."""

    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        key = api_key or os.environ.get("OPENAI_API_KEY")
        model = model_name or os.environ.get("LLM_MODEL") or "gpt-4o"
        super().__init__(model_name=model, api_key=key)

    def generate(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is missing.")
        import httpx
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 2048),
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            raise ValueError(f"OpenAI API returned HTTP {resp.status_code}: {resp.text}")


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider implementation (driven by LLM_MODEL in .env)."""

    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        model = model_name or os.environ.get("LLM_MODEL") or "claude-3-5-sonnet-20241022"
        super().__init__(model_name=model, api_key=key)

    def generate(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> str:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is missing.")
        import httpx
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": user_prompt}],
            "max_tokens": kwargs.get("max_tokens", 2048),
            "temperature": kwargs.get("temperature", 0.1),
        }
        if system_prompt:
            payload["system"] = system_prompt
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["content"][0]["text"]
            raise ValueError(f"Anthropic API returned HTTP {resp.status_code}: {resp.text}")


class MockLLMProvider(LLMProvider):
    """Deterministic Mock LLM provider for unit tests and offline testing."""

    def __init__(self, model_name: str = "mock-model", mock_response: str = "Mock generated response"):
        super().__init__(model_name=model_name, api_key="mock-key")
        self.mock_response = mock_response

    def generate(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> str:
        print("\n===== LLM RESPONSE =====")
        print(self.mock_response)
        print("========================\n")
        return self.mock_response


def get_llm_provider(
    provider_name: Optional[str] = None,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
) -> LLMProvider:
    """
    Factory to return the configured LLMProvider instance.
    Dynamically resolved from .env configuration (LLM_PROVIDER and LLM_MODEL).
    """
    selected_provider = (
        provider_name or os.environ.get("LLM_PROVIDER") or "gemini"
    ).lower().strip()

    selected_model = model_name or os.environ.get("LLM_MODEL")

    if selected_provider == "mock":
        return MockLLMProvider(model_name=selected_model or "mock-model")

    if selected_provider == "openai":
        return OpenAIProvider(model_name=selected_model, api_key=api_key)

    if selected_provider in ["anthropic", "claude"]:
        return AnthropicProvider(model_name=selected_model, api_key=api_key)

    return GeminiProvider(model_name=selected_model, api_key=api_key)
