"""
ai/src/ingestion/indexer.py

Indexes canonical chunks into Qdrant collections with dense and sparse vectors.
"""

from typing import Any, Dict, List
import uuid
from qdrant_client.http import models as rest

from src.embeddings.embedding_provider import EmbeddingProvider
from src.embeddings.sparse_provider import BM25SparseProvider
from src.ingestion.chunker import CanonicalChunk
from src.retrieval.qdrant_manager import QdrantManager


class DocumentIndexer:
    """Orchestrates embedding computation and batch ingestion into Qdrant."""

    def __init__(
        self,
        qdrant_manager: QdrantManager,
        dense_provider: EmbeddingProvider,
        sparse_provider: BM25SparseProvider,
    ):
        self.qdrant = qdrant_manager
        self.dense_provider = dense_provider
        self.sparse_provider = sparse_provider

    def index_chunks(self, chunks: List[CanonicalChunk]) -> Dict[str, int]:
        """
        Indexes a list of CanonicalChunks into their respective target Qdrant collections.
        Returns a dictionary mapping collection_name to the number of points inserted.
        """
        if not chunks:
            return {}

        self.qdrant.init_collections()

        # Group chunks by target collection
        grouped: Dict[str, List[CanonicalChunk]] = {}
        for c in chunks:
            col = c.target_collection
            grouped.setdefault(col, []).append(c)

        counts: Dict[str, int] = {}

        for col, col_chunks in grouped.items():
            texts = [c.content for c in col_chunks]

            # Compute dense embeddings
            dense_vectors = self.dense_provider.embed_batch(texts)
            # Compute sparse embeddings
            sparse_vectors = self.sparse_provider.embed_sparse_batch(texts)

            points: List[rest.PointStruct] = []
            for i, chunk in enumerate(col_chunks):
                # Generate a deterministic or random UUID for point id
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.id))

                points.append(
                    rest.PointStruct(
                        id=point_id,
                        vector={
                            "dense": dense_vectors[i],
                            "sparse": rest.SparseVector(
                                indices=sparse_vectors[i].indices,
                                values=sparse_vectors[i].values,
                            ),
                        },
                        payload=chunk.payload,
                    )
                )

            self.qdrant.upsert_points(col, points)
            counts[col] = len(points)

        return counts
