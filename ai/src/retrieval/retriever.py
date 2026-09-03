"""
ai/src/retrieval/retriever.py

Hybrid retriever orchestrating collection routing, multi-collection query execution,
jurisdiction filtering, and evidence payload ranking.
"""

import re
import concurrent.futures
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


@dataclass
class DomainEvidenceSet:
    """Domain-specific evidence package returned by scoped agent retrieval."""
    agent_scope: str
    intent: str
    sub_question: str
    evidence: List[RetrievedEvidence]
    hits_found: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_scope": self.agent_scope,
            "intent": self.intent,
            "sub_question": self.sub_question,
            "evidence": [e.to_dict() for e in self.evidence],
            "hits_found": self.hits_found,
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
    "PATENT": ["patents", "traditional_knowledge", "drugs_cosmetics", "herbal_standards", "general_ip", "international_treaties"],
    "ABS": ["biological_diversity", "traditional_knowledge", "international_treaties", "general_ip"],
    "TRADEMARK": ["trademarks", "general_ip", "international_treaties"],
    "FOOD_REGULATION": ["food_safety", "food_regulation", "traditional_knowledge", "drugs_cosmetics", "herbal_standards"],
    "FORMULATION": ["herbal_standards", "traditional_knowledge", "drugs_cosmetics", "patents"],
    "EXPORT": ["export_control", "international_treaties", "traditional_knowledge", "patents", "trademarks", "general_ip", "copyright", "geographical_indications", "industrial_designs"],
    "CASE_LAW": ["patents", "trademarks", "copyright", "industrial_designs", "geographical_indications", "traditional_knowledge", "general_ip", "drugs_cosmetics"],
}


def get_adaptive_query_anchor(query: str, intent: Optional[str] = None) -> str:
    """Derives dynamic statutory semantic anchors tailored to the query's specific domain context."""
    q_lower = query.lower()
    anchors = []

    # 1. Extraction / Process / Isolation
    if any(w in q_lower for w in ["extract", "process", "method", "isolate", "fraction", "purif", "solvent", "yield", "synthesis"]):
        anchors.append("process patent Section 2(1)(ja) inventive step Section 3(d) technical advance")

    # 2. Formulation / Synergistic combination / Traditional Ayush
    if any(w in q_lower for w in ["formulat", "combin", "mixtur", "synerg", "ayurved", "herbal", "tradition", "oil", "powder", "churna", "ghrita", "bhasma", "vati", "kwath"]):
        anchors.append("Section 3(p) traditional knowledge exclusion Section 3(e) synergistic admixture")

    # 3. Polymorph / Crystalline / New form / Bioavailability
    if any(w in q_lower for w in ["polymorph", "crystallin", "bioavailab", "efficacy", "salt", "derivative"]):
        anchors.append("Section 3(d) new form of known substance enhancement of efficacy")

    # 4. Biological material / Sourcing / Foreign filing / NBA ABS
    if any(w in q_lower for w in ["herb", "plant", "collect", "wild", "himalayan", "foreign", "export", "nba", "biodiversity", "source", "origin", "abs", "benefit sharing"]):
        anchors.append("Section 10(4)(d)(ii) biological material origin disclosure Biological Diversity Act Section 3 NBA approval")

    # 5. Trademark / Brand Name / Prohibited names
    if any(w in q_lower for w in ["brand", "trademark", "name", "logo", "mark", "generic"]):
        anchors.append("Trade Marks Act Section 9 absolute grounds Section 11 relative grounds")

    # 6. Food / Nutraceutical / Aahara
    if any(w in q_lower for w in ["food", "supplement", "nutraceutical", "aahar", "dietary", "fssai"]):
        anchors.append("FSSAI Ayurveda Aahara Regulations 2022 schedule food safety standards")

    return " ".join(anchors)


MIN_RELEVANCE_SCORE = 0.45


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
        Executes hybrid retrieval across routed collections with strict jurisdiction and domain filtering.
        """
        # 1. Determine collections to query
        avail = self.qdrant.get_available_collections()
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

        # Filter strictly to collections currently present in active Qdrant cluster
        effective_collections = [c for c in collections if c in avail]
        if not effective_collections and "legal_statutory" in avail:
            effective_collections = ["legal_statutory"]
        elif not effective_collections:
            effective_collections = list(avail)
        collections = effective_collections

        # 2. Derive dynamic semantic anchor and vectorize query
        anchor = get_adaptive_query_anchor(query, intent=intent)
        search_query = f"{query} {anchor}".strip() if anchor else query

        dense_vec = self.dense_provider.embed(search_query)
        sparse_vec = self.sparse_provider.embed_sparse(search_query)

        # 3. Build strict jurisdiction metadata filters (never cross-contaminate India vs International)
        filters: Dict[str, Any] = {}
        if jurisdiction:
            jur_lower = jurisdiction.lower()
            if jur_lower in ["india", "in"]:
                filters["jurisdiction"] = ["India", "india", "INDIA", "IN", "in"]
            else:
                # For any international or foreign jurisdiction query, strictly search international corpus
                filters["jurisdiction"] = ["International", "international", "WIPO", "wipo"]

        if intent and intent in INTENT_IP_DOMAINS:
            filters["ip_domain"] = INTENT_IP_DOMAINS[intent]

        # 4. Search across target collections in parallel
        all_hits: List[RetrievedEvidence] = []
        limit_per_col = max(3, top_k // max(1, len(collections)) + 2)

        def _fetch_collection(col_name: str) -> List[RetrievedEvidence]:
            hits = []
            try:
                scored_points = self.qdrant.search_hybrid(
                    collection_name=col_name,
                    dense_vector=dense_vec,
                    sparse_indices=sparse_vec.indices,
                    sparse_values=sparse_vec.values,
                    limit=limit_per_col,
                    filters=filters if col_name == "legal_statutory" else None,
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
                        target_collection=col_name,
                        verification_status=payload.get("verification_status", "VERIFIED_OFFICIAL_GAZETTE"),
                        score=float(pt.score or 0.0),
                        metadata=payload,
                    )
                    hits.append(evidence)
            except Exception:
                pass
            return hits

        if len(collections) > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(collections))) as executor:
                results = executor.map(_fetch_collection, collections)
                for res in results:
                    all_hits.extend(res)
        else:
            for col in collections:
                all_hits.extend(_fetch_collection(col))

        # 5. Fallback: if domain filters yielded 0 hits, retry with only jurisdiction filter
        if not all_hits:
            try:
                jur_only_filter = {"jurisdiction": filters["jurisdiction"]} if "jurisdiction" in filters else None
                scored_points = self.qdrant.search_dense(
                    collection_name="legal_statutory",
                    vector=dense_vec,
                    limit=top_k,
                    filters=jur_only_filter,
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

        # 6. Apply Minimum Relevance Score Gate (Discard weak/irrelevant noise)
        qualified_hits = [h for h in all_hits if h.score >= MIN_RELEVANCE_SCORE]
        qualified_hits.sort(key=lambda x: x.score, reverse=True)

        # 7. Deduplicate near-identical statutory content to prevent duplicate crowding
        deduped_hits: List[RetrievedEvidence] = []
        seen_section_keys = set()
        seen_content_prefixes = set()

        for hit in qualified_hits:
            # Create a normalized content fingerprint (first 120 non-whitespace chars)
            norm_prefix = re.sub(r"\s+", "", hit.content[:120].lower())
            
            # Scope section uniqueness to document identity + doc category + section ref + jurisdiction
            # This ensures cross-Act provisions (e.g. Patents vs TM) and complementary Case Law + Statute pairs coexist freely
            doc_id = hit.metadata.get("document_id") or hit.doc_title
            doc_type = hit.document_type
            sec_name = hit.section_ref.strip().lower() if hit.section_ref else None
            sec_key = (doc_id, doc_type, sec_name, hit.jurisdiction) if sec_name else None

            # Skip if identical verbatim content already present
            if norm_prefix and norm_prefix in seen_content_prefixes:
                continue
            # Skip if same specific section within the same document already present
            if sec_key and sec_key in seen_section_keys:
                continue

            deduped_hits.append(hit)
            if norm_prefix:
                seen_content_prefixes.add(norm_prefix)
            if sec_key:
                seen_section_keys.add(sec_key)

            if len(deduped_hits) >= top_k:
                break

        return deduped_hits

    def retrieve_for_task(self, task: Any, top_k: int = 3) -> DomainEvidenceSet:
        """
        Executes domain-scoped retrieval for an individual AgentTask in multi-agent orchestration.
        Maintains independent gating, filtering, adaptive query anchoring, and deduplication.
        """
        hits = self.retrieve(
            query=task.sub_question,
            jurisdiction=task.jurisdiction,
            intent=task.intent,
            top_k=top_k,
        )
        return DomainEvidenceSet(
            agent_scope=task.agent_scope,
            intent=task.intent,
            sub_question=task.sub_question,
            evidence=hits,
            hits_found=len(hits) > 0,
        )
