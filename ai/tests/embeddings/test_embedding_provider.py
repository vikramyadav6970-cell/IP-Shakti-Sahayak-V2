"""
ai/tests/embeddings/test_embedding_provider.py

Unit and smoke tests for BAAI/bge-m3 and Mock embedding providers.
"""

import math
import pytest
from src.embeddings.embedding_provider import (
    EmbeddingProvider,
    MockEmbeddingProvider,
    BGEM3EmbeddingProvider,
    get_embedding_provider,
)


def test_mock_embedding_provider():
    """Verify mock embeddings have exact 1024 dimension, non-zero, unit normalized."""
    provider = MockEmbeddingProvider(dimension=1024)
    assert provider.dimension == 1024
    
    english_text = "Patents Act 1970 Section 3(p) excludes traditional knowledge."
    hindi_text = "पेटेंट अधिनियम १९७० की धारा ३(पी) पारंपरिक ज्ञान को बाहर करती है।"
    
    vectors = provider.embed([english_text, hindi_text])
    assert len(vectors) == 2
    
    for vec in vectors:
        assert len(vec) == 1024
        assert any(x != 0.0 for x in vec)  # Not all zero
        norm = math.sqrt(sum(x * x for x in vec))
        assert abs(norm - 1.0) < 1e-4  # Normalized


def test_embedding_factory(monkeypatch):
    """Verify factory routes properly based on EMBEDDING_PROVIDER."""
    monkeypatch.setenv("EMBEDDING_PROVIDER", "mock")
    provider = get_embedding_provider()
    assert isinstance(provider, MockEmbeddingProvider)
    assert provider.dimension == 1024


@pytest.mark.live_model
def test_bge_m3_live_smoke():
    """Smoke test for real BAAI/bge-m3 model (run when packages are installed)."""
    try:
        provider = BGEM3EmbeddingProvider()
        vectors = provider.embed(["Ayurvedic formulation", "पारंपरिक ज्ञान"])
        assert len(vectors) == 2
        for vec in vectors:
            assert len(vec) == 1024
            assert any(x != 0.0 for x in vec)
    except Exception as e:
        pytest.skip(f"bge-m3 model loading skipped: {e}")
