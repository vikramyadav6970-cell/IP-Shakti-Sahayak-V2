"""
ai/tests/reasoning/test_llm_provider.py

Unit and smoke tests for LLM provider abstraction.
"""

import os
import pytest
from src.reasoning.llm_provider import (
    LLMProvider,
    MockLLMProvider,
    GeminiProvider,
    OpenAIProvider,
    AnthropicProvider,
    get_llm_provider,
)


def test_mock_llm_provider():
    """Verify MockLLMProvider works deterministically without external keys."""
    provider = MockLLMProvider(mock_response="Test output")
    assert isinstance(provider, LLMProvider)
    result = provider.generate("You are a legal assistant.", "What is Section 3(p)?")
    assert result == "Test output"


def test_provider_factory_routing(monkeypatch):
    """Test get_llm_provider returns the right provider based on LLM_PROVIDER env var."""
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    provider = get_llm_provider()
    assert isinstance(provider, MockLLMProvider)

    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    provider = get_llm_provider()
    assert isinstance(provider, GeminiProvider)

    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")
    provider = get_llm_provider()
    assert isinstance(provider, OpenAIProvider)

    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    provider = get_llm_provider()
    assert isinstance(provider, AnthropicProvider)


@pytest.mark.live_llm
def test_live_llm_smoke():
    """Live smoke test that executes against a real API when key is provided."""
    has_key = bool(
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
    )
    if not has_key:
        pytest.skip("No real LLM API key configured in environment. Skipping live smoke test.")
    
    try:
        provider = get_llm_provider()
        response = provider.generate(
            system_prompt="You are a test assistant. Reply with one word.",
            user_prompt="Say 'PASSED'.",
            temperature=0.0,
        )
        assert len(response.strip()) > 0
    except ImportError as e:
        pytest.skip(f"Provider package not installed: {e}")
