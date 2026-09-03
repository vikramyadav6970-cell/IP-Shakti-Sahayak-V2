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


class RemoteEmbeddingProvider(EmbeddingProvider):
    """
    Remote HTTP embedding provider for delegating BAAI/bge-m3 dense vector generation
    to a dedicated external endpoint (e.g. Hugging Face Space, Modal, Cloud Run) with 0 local RAM.
    """

    def __init__(self, endpoint_url: Optional[str] = None, api_key: Optional[str] = None, dimension: int = 1024):
        super().__init__(model_name="remote-bge-m3", dimension=dimension)
        self.endpoint_url = endpoint_url or os.environ.get("EMBEDDING_API_URL") or "https://router.huggingface.co/hf-inference/models/BAAI/bge-m3"
        self.api_key = api_key or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        import httpx
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {"inputs": texts} if "huggingface" in self.endpoint_url else {"texts": texts}
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(self.endpoint_url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    # Handle both HF feature extraction format and custom API format
                    if isinstance(data, dict) and "embeddings" in data:
                        return data["embeddings"]
                    if isinstance(data, list):
                        # If list of vectors
                        if len(data) > 0 and isinstance(data[0], list):
                            # If 3D token-level [batch, seq, dim], mean pool to 2D
                            if len(data[0]) > 0 and isinstance(data[0][0], list):
                                pooled = []
                                for token_seq in data:
                                    dim = len(token_seq[0])
                                    mean_vec = [sum(token[i] for token in token_seq) / len(token_seq) for i in range(dim)]
                                    # Normalize
                                    norm = math.sqrt(sum(x * x for x in mean_vec)) or 1.0
                                    pooled.append([x / norm for x in mean_vec])
                                return pooled
                            return data
        except Exception as e:
            print(f"[Remote Embedding Notice]: {e}")
        return [[0.0] * self.dimension for _ in texts]


def get_embedding_provider(provider_type: Optional[str] = None) -> EmbeddingProvider:
    """
    Factory to obtain embedding provider with global singleton caching.
    Supports:
    - 'bge-m3' (default): In-memory PyTorch BGEM3EmbeddingProvider
    - 'remote' / 'hf': Remote HTTP BGEM3 vector endpoint (0 RAM usage, for 512MB hosting)
    - 'mock' / 'test': Fast unit test mock provider
    """
    global _GLOBAL_PROVIDER
    selected = (provider_type or os.environ.get("EMBEDDING_PROVIDER") or "").lower()
    if selected in ["mock", "test"]:
        return MockEmbeddingProvider()
    if selected in ["remote", "hf", "huggingface"]:
        if _GLOBAL_PROVIDER is None or not isinstance(_GLOBAL_PROVIDER, RemoteEmbeddingProvider):
            _GLOBAL_PROVIDER = RemoteEmbeddingProvider()
        return _GLOBAL_PROVIDER

    if _GLOBAL_PROVIDER is None:
        try:
            _GLOBAL_PROVIDER = BGEM3EmbeddingProvider()
        except Exception:
            _GLOBAL_PROVIDER = MockEmbeddingProvider()
    return _GLOBAL_PROVIDER

