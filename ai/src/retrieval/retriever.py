"""
ai/src/retrieval/retriever.py

Hybrid retriever orchestrating collection routing, multi-collection query execution,
jurisdiction filtering, and evidence payload ranking.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.embeddings.embedding_provider import EmbeddingProvider
from src.embeddings.sparse_provider import BM25SparseProvider
from src.retrieval.qdrant_manager import QdrantManager, CANONICAL_COLLECTIONS


@dataclass
class RetrievedEvidence:
    """Standardized evidence payload returned by the retriever."""
    chunk_id: str
    content: str
    doc_title: str
    section_ref: Optional[str]
    source_url: str
    jurisdiction: str
    document_type: str
    target_collection: str
    verification_status: str
    score: float
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "doc_title": self.doc_title,
            "section_ref": self.section_ref,
            "source_url": self.source_url,
            "jurisdiction": self.jurisdiction,
            "document_type": self.document_type,
            "target_collection": self.target_collection,
            "verification_status": self.verification_status,
            "score": self.score,
            "metadata": self.metadata,
        }


# Intent to collection mapping
INTENT_COLLECTION_ROUTING: Dict[str, List[str]] = {
    "PATENT": ["legal_statutory", "case_law_prior_art", "procedural_forms_checklists"],
    "ABS": ["legal_statutory", "procedural_forms_checklists"],
    "TRADEMARK": ["legal_statutory"],
    "FOOD_REGULATION": ["legal_statutory", "standards_formulations"],
    "FORMULATION": ["standards_formulations", "legal_statutory"],
    "EXPORT": ["international_export", "legal_statutory", "procedural_forms_checklists"],
    "CASE_LAW": ["case_law_prior_art"],
    "ALL": CANONICAL_COLLECTIONS,
}

# Intent to canonical IP domain metadata tag mapping
INTENT_IP_DOMAINS: Dict[str, List[str]] = {
    "PATENT": ["patents", "traditional_knowledge", "drugs_cosmetics", "herbal_standards"],
    "ABS": ["biological_diversity", "traditional_knowledge"],
    "TRADEMARK": ["trademarks", "general_ip"],
    "FOOD_REGULATION": ["food_safety", "traditional_knowledge", "drugs_cosmetics"],
    "FORMULATION": ["herbal_standards", "traditional_knowledge", "drugs_cosmetics"],
    "EXPORT": ["export_control", "international_treaties", "traditional_knowledge", "patents", "trademarks"],
}


class HybridRetriever:
    """Executes multi-collection hybrid retrieval with metadata filtering."""

    def __init__(
        self,
        qdrant_manager: QdrantManager,
        dense_provider: EmbeddingProvider,
        sparse_provider: BM25SparseProvider,
    ):
        self.qdrant = qdrant_manager
        self.dense_provider = dense_provider
        self.sparse_provider = sparse_provider

    def retrieve(
        self,
        query: str,
        jurisdiction: str = "INDIA",
        intent: Optional[str] = None,
        top_k: int = 5,
        target_collections: Optional[List[str]] = None,
    ) -> List[RetrievedEvidence]:
        """
        Executes hybrid retrieval across routed collections with jurisdiction and domain filtering.
        """
        # 1. Determine collections to query
        if target_collections:
            collections = [c for c in target_collections if c in CANONICAL_COLLECTIONS]
        elif intent and intent in INTENT_COLLECTION_ROUTING:
            collections = INTENT_COLLECTION_ROUTING[intent]
        else:
            # Default collections based on jurisdiction
            if jurisdiction.upper() == "INTERNATIONAL":
                collections = ["international_export", "case_law_prior_art", "legal_statutory"]
            else:
                collections = ["legal_statutory", "standards_formulations", "case_law_prior_art", "procedural_forms_checklists"]

        # 2. Vectorize query
        dense_vec = self.dense_provider.embed(query)
        sparse_vec = self.sparse_provider.embed_sparse(query)

        # 3. Build robust metadata filters
        filters: Dict[str, Any] = {}
        if jurisdiction:
            jur_lower = jurisdiction.lower()
            if jur_lower in ["india", "in"]:
                filters["jurisdiction"] = ["India", "india", "INDIA", "IN", "in", "International", "None"]
            elif jur_lower in ["international", "usa", "eu", "wipo"]:
                filters["jurisdiction"] = ["International", "international", "WIPO", "wipo", "India", "india"]

        if intent and intent in INTENT_IP_DOMAINS:
            filters["ip_domain"] = INTENT_IP_DOMAINS[intent]

        # 4. Search across target collections
        all_hits: List[RetrievedEvidence] = []
        limit_per_col = max(3, top_k // max(1, len(collections)) + 2)

        for col in collections:
            try:
                scored_points = self.qdrant.search_hybrid(
                    collection_name=col,
                    dense_vector=dense_vec,
                    sparse_indices=sparse_vec.indices,
                    sparse_values=sparse_vec.values,
                    limit=limit_per_col,
                    filters=filters if col == "legal_statutory" else None,
                )

                for pt in scored_points:
                    payload = pt.payload or {}
                    content_str = payload.get("chunk_text") or payload.get("content", "")
                    title_str = payload.get("source_filename") or payload.get("doc_title", "")
                    sec_str = payload.get("section_number") or payload.get("section_ref") or payload.get("article_ref")
                    evidence = RetrievedEvidence(
                        chunk_id=str(pt.id),
                        content=content_str,
                        doc_title=title_str,
                        section_ref=sec_str,
                        source_url=payload.get("source_url", ""),
                        jurisdiction=str(payload.get("jurisdiction", jurisdiction)).upper(),
                        document_type=payload.get("doc_category") or payload.get("document_type", "STATUTE"),
                        target_collection=col,
                        verification_status=payload.get("verification_status", "VERIFIED_OFFICIAL_GAZETTE"),
                        score=float(pt.score or 0.0),
                        metadata=payload,
                    )
                    all_hits.append(evidence)
            except Exception:
                # If collection empty or error, continue to next
                continue

        # 5. Fallback: if collection routing or filters yielded 0 hits, query legal_statutory directly
        if not all_hits:
            try:
                scored_points = self.qdrant.search_dense(
                    collection_name="legal_statutory",
                    vector=dense_vec,
                    limit=top_k,
                )
                for pt in scored_points:
                    payload = pt.payload or {}
                    content_str = payload.get("chunk_text") or payload.get("content", "")
                    title_str = payload.get("source_filename") or payload.get("doc_title", "")
                    sec_str = payload.get("section_number") or payload.get("section_ref") or payload.get("article_ref")
                    evidence = RetrievedEvidence(
                        chunk_id=str(pt.id),
                        content=content_str,
                        doc_title=title_str,
                        section_ref=sec_str,
                        source_url=payload.get("source_url", ""),
                        jurisdiction=str(payload.get("jurisdiction", jurisdiction)).upper(),
                        document_type=payload.get("doc_category") or payload.get("document_type", "STATUTE"),
                        target_collection="legal_statutory",
                        verification_status=payload.get("verification_status", "VERIFIED_OFFICIAL_GAZETTE"),
                        score=float(pt.score or 0.0),
                        metadata=payload,
                    )
                    all_hits.append(evidence)
            except Exception:
                pass

        # 6. Sort by relevance score descending and take top_k
        all_hits.sort(key=lambda x: x.score, reverse=True)
        return all_hits[:top_k]
