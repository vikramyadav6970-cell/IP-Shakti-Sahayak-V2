"""
ai/src/embeddings/sparse_provider.py

Sparse vector generation for exact term matching (Section numbers, Latin binomials, statutory references).
Implements a deterministic lexical sparse encoder compatible with Qdrant named sparse vectors.
"""

from collections import Counter
import hashlib
import re
from typing import Dict, List, Tuple


class SparseVector:
    """Represents a sparse vector with indices and weights."""
    def __init__(self, indices: List[int], values: List[float]):
        self.indices = indices
        self.values = values

    def to_dict(self) -> Dict[str, List]:
        return {"indices": self.indices, "values": self.values}


class BM25SparseProvider:
    """
    Computes deterministic sparse term hash vectors for exact lexical matching.
    Provides fast, reproducible sparse representations for hybrid search without heavy external runtime.
    """

    def __init__(self, vocab_size: int = 100000):
        self.vocab_size = vocab_size

    def _tokenize(self, text: str) -> List[str]:
        # Tokenize retaining alphanumeric, section indicators (§, 3(p), 3(d)), and latin binomials
        tokens = re.findall(r"\b[\w\(\)\-\.§]+\b", text.lower())
        return [t for t in tokens if len(t) > 1 or t == "§"]

    def _hash_token(self, token: str) -> int:
        h = hashlib.md5(token.encode("utf-8")).hexdigest()
        return int(h, 16) % self.vocab_size

    def embed_sparse(self, text: str) -> SparseVector:
        """Embed a single text string into a sparse vector."""
        tokens = self._tokenize(text)
        if not tokens:
            return SparseVector(indices=[0], values=[0.0])

        counts = Counter(tokens)
        total_tokens = len(tokens)

        # Compute term frequencies with logarithmic scaling
        sparse_map: Dict[int, float] = {}
        for token, count in counts.items():
            idx = self._hash_token(token)
            tf = 1.0 + (count / total_tokens)
            # Give statutory markers higher weight
            if re.search(r"^(?:section|article|form|§|\d+\([a-z]\))", token):
                tf *= 1.5
            sparse_map[idx] = max(sparse_map.get(idx, 0.0), round(tf, 4))

        sorted_indices = sorted(sparse_map.keys())
        values = [sparse_map[idx] for idx in sorted_indices]

        return SparseVector(indices=sorted_indices, values=values)

    def embed_sparse_batch(self, texts: List[str]) -> List[SparseVector]:
        """Embed multiple texts in batch."""
        return [self.embed_sparse(t) for t in texts]
