"""
ai/src/retrieval/qdrant_manager.py

Qdrant collection lifecycle, payload index configuration, and hybrid search execution
across the 5 canonical collections defined in ARCHITECTURE.md §3.
"""

import os
from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest


CANONICAL_COLLECTIONS = [
    "legal_statutory",
    "standards_formulations",
    "case_law_prior_art",
    "procedural_forms_checklists",
    "international_export",
]

DENSE_VECTOR_DIM = 1024


class QdrantManager:
    """Manages Qdrant client connection, schema setup, point upserts, and vector searches."""

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        in_memory: bool = False,
    ):
        self.url = url or os.getenv("QDRANT_URL")
        self.api_key = api_key or os.getenv("QDRANT_API_KEY")

        if in_memory or (not self.url and not self.api_key):
            self.client = QdrantClient(":memory:")
            self.is_cloud = False
        else:
            self.client = QdrantClient(url=self.url, api_key=self.api_key)
            self.is_cloud = True

    def init_collections(self) -> None:
        """Create the 5 canonical collections if they don't already exist."""
        existing = {c.name for c in self.client.get_collections().collections}

        for col in CANONICAL_COLLECTIONS:
            if col not in existing:
                self.client.create_collection(
                    collection_name=col,
                    vectors_config={
                        "dense": rest.VectorParams(
                            size=DENSE_VECTOR_DIM,
                            distance=rest.Distance.COSINE,
                        )
                    },
                    sparse_vectors_config={
                        "sparse": rest.SparseVectorParams(
                            index=rest.SparseIndexParams(
                                on_disk=False,
                            )
                        )
                    },
                )
                # Create payload indexes for fast filtering
                self._create_payload_indexes(col)

    def _create_payload_indexes(self, collection_name: str) -> None:
        """Create indexes on frequently filtered fields."""
        fields_to_index = [
            ("jurisdiction", rest.PayloadSchemaType.KEYWORD),
            ("document_type", rest.PayloadSchemaType.KEYWORD),
            ("document_id", rest.PayloadSchemaType.KEYWORD),
            ("verification_status", rest.PayloadSchemaType.KEYWORD),
            ("section_ref", rest.PayloadSchemaType.KEYWORD),
        ]
        for field_name, field_type in fields_to_index:
            try:
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field_name,
                    field_schema=field_type,
                )
            except Exception:
                pass  # Ignore if index already exists

    def upsert_points(
        self,
        collection_name: str,
        points: List[rest.PointStruct],
    ) -> None:
        """Upsert batch of points into a collection."""
        if collection_name not in CANONICAL_COLLECTIONS:
            raise ValueError(f"Unknown collection: {collection_name}. Must be one of {CANONICAL_COLLECTIONS}")
        self.client.upsert(
            collection_name=collection_name,
            points=points,
            wait=True,
        )

    def search_dense(
        self,
        collection_name: str,
        vector: List[float],
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[rest.ScoredPoint]:
        """Execute dense vector similarity query."""
        q_filter = self._build_filter(filters)
        return self.client.query_points(
            collection_name=collection_name,
            query=vector,
            using="dense",
            limit=limit,
            query_filter=q_filter,
            with_payload=True,
        ).points

    def search_hybrid(
        self,
        collection_name: str,
        dense_vector: List[float],
        sparse_indices: List[int],
        sparse_values: List[float],
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[rest.ScoredPoint]:
        """
        Execute hybrid search using Reciprocal Rank Fusion (RRF).
        """
        q_filter = self._build_filter(filters)

        prefetch = [
            rest.Prefetch(
                query=rest.SparseVector(indices=sparse_indices, values=sparse_values),
                using="sparse",
                filter=q_filter,
                limit=limit * 2,
            ),
            rest.Prefetch(
                query=dense_vector,
                using="dense",
                filter=q_filter,
                limit=limit * 2,
            ),
        ]

        results = self.client.query_points(
            collection_name=collection_name,
            prefetch=prefetch,
            query=rest.FusionQuery(fusion=rest.Fusion.RRF),
            limit=limit,
            with_payload=True,
        )

        return results.points

    def _build_filter(self, filter_dict: Optional[Dict[str, Any]]) -> Optional[rest.Filter]:
        """Convert a simple dictionary filter to a Qdrant Filter object."""
        if not filter_dict:
            return None

        must_conditions = []
        for key, val in filter_dict.items():
            if val is not None:
                if isinstance(val, list):
                    must_conditions.append(
                        rest.FieldCondition(
                            key=key,
                            match=rest.MatchAny(any=val),
                        )
                    )
                else:
                    must_conditions.append(
                        rest.FieldCondition(
                            key=key,
                            match=rest.MatchValue(value=val),
                        )
                    )

        if not must_conditions:
            return None

        return rest.Filter(must=must_conditions)
