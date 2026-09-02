"""
ai/src/embeddings/embedding_provider.py

Embedding Provider Abstraction for Dense (1024-dim) and Sparse embeddings.
Default model: BAAI/bge-m3 (multilingual, supporting English & Hindi).
"""

from abc import ABC, abstractmethod
import math
import os
from typing import Any, Dict, List, Optional, Union


class EmbeddingProvider(ABC):
    """Abstract base class for text embedding providers."""

    def __init__(self, model_name: str, dimension: int = 1024):
        self.model_name = model_name
        self.dimension = dimension

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate normalized dense vector embeddings for a list of texts."""
        pass

    def embed(self, input_text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Convenience method accepting either a single string or a list of strings."""
        if isinstance(input_text, str):
            res = self.embed_texts([input_text])
            return res[0] if res else [0.0] * self.dimension
        return self.embed_texts(input_text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embedding alias."""
        return self.embed_texts(texts)

    def embed_sparse(self, texts: List[str]) -> List[Dict[int, float]]:
        """Generate sparse/lexical token weights for hybrid search (if supported)."""
        return [{} for _ in texts]


_GLOBAL_MODEL = None
_GLOBAL_PROVIDER = None


class BGEM3EmbeddingProvider(EmbeddingProvider):
    """
    BAAI/bge-m3 embedding provider via sentence-transformers.
    Produces 1024-dimensional dense vectors with cosine similarity normalization.
    """

    def __init__(self, model_name: str = "BAAI/bge-m3", device: Optional[str] = None):
        super().__init__(model_name=model_name, dimension=1024)
        if device is None:
            try:
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:
                self.device = "cpu"
        else:
            self.device = device

    def _get_model(self):
        global _GLOBAL_MODEL
        if _GLOBAL_MODEL is None:
            from sentence_transformers import SentenceTransformer
            hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
            _GLOBAL_MODEL = SentenceTransformer(self.model_name, device=self.device, token=hf_token)
        return _GLOBAL_MODEL

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        model = self._get_model()
        try:
            import torch
            with torch.inference_mode():
                embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        except Exception:
            embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return [vec.tolist() for vec in embeddings]


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic mock embedding provider for fast unit tests without downloading weights.
    Produces valid unit-normalized vectors of length 1024.
    """

    def __init__(self, dimension: int = 1024):
        super().__init__(model_name="mock-bge-m3", dimension=dimension)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        results = []
        for text in texts:
            # Deterministic hash-based non-zero vector
            vector = []
            seed = sum(ord(c) for c in text) if text else 1
            for i in range(self.dimension):
                val = math.sin(seed + i * 0.1)
                vector.append(val)
            # Normalize to unit length
            norm = math.sqrt(sum(x * x for x in vector)) or 1.0
            results.append([x / norm for x in vector])
        return results


def get_embedding_provider(provider_type: Optional[str] = None) -> EmbeddingProvider:
    """
    Factory to obtain embedding provider with global singleton caching.
    Automatically uses BAAI/bge-m3 on GPU/CPU for live AI intelligence.
    Set EMBEDDING_PROVIDER=mock only for isolated unit tests.
    """
    global _GLOBAL_PROVIDER
    selected = (provider_type or os.environ.get("EMBEDDING_PROVIDER") or "").lower()
    if selected in ["mock", "test"]:
        return MockEmbeddingProvider()
    if _GLOBAL_PROVIDER is None:
        try:
            _GLOBAL_PROVIDER = BGEM3EmbeddingProvider()
        except Exception:
            _GLOBAL_PROVIDER = MockEmbeddingProvider()
    return _GLOBAL_PROVIDER
