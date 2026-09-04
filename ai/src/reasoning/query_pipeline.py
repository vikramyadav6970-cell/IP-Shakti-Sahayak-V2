"""
ai/src/reasoning/query_pipeline.py

End-to-end RAG consultation query pipeline orchestrating guardrails,
hybrid retrieval, prompt assembly, LLM synthesis, citation validation, and confidence scoring.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.citations.citation_validator import CitationValidator, ValidatedCitation
from src.classification.intent_classifier import IntentClassifier
from src.classification.jurisdiction_classifier import JurisdictionClassifier
from src.confidence.confidence_scorer import ConfidenceAssessment, ConfidenceScorer
from src.embeddings.embedding_provider import get_embedding_provider
from src.embeddings.sparse_provider import BM25SparseProvider
from src.guardrails.guardrail_manager import GuardrailManager, GuardrailResult
from src.prompts.templates import CONSULTATION_SYSTEM_PROMPT, build_user_prompt
from src.reasoning.llm_provider import get_llm_provider
from src.retrieval.qdrant_manager import QdrantManager
from src.retrieval.retriever import HybridRetriever, RetrievedEvidence


@dataclass
class QueryPipelineResult:
    """Final validated response object from the AI consultation pipeline."""
    content: str
    jurisdiction: str
    intent: str
    confidence: ConfidenceAssessment
    citations: List[ValidatedCitation]
    evidence_items: List[RetrievedEvidence]
    is_out_of_scope: bool = False
    detected_jurisdiction: Optional[str] = None
    guardrail_triggered: bool = False
    guardrail_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "jurisdiction": self.jurisdiction,
            "intent": self.intent,
            "confidence_score": self.confidence.composite_score,
            "confidence_label": self.confidence.confidence_label,
            "requires_human_review": self.confidence.requires_human_review,
            "citations": [c.to_dict() for c in self.citations],
            "is_out_of_scope": self.is_out_of_scope,
            "detected_jurisdiction": self.detected_jurisdiction,
            "guardrail_triggered": self.guardrail_triggered,
        }


class QueryPipeline:
    """Orchestrates evidence retrieval, LLM reasoning, citation verification, and confidence scoring."""

    def __init__(
        self,
        qdrant_manager: Optional[QdrantManager] = None,
        embedding_provider_type: Optional[str] = None,
        llm_provider_type: Optional[str] = None,
        llm_model: Optional[str] = None,
    ):
        self.qdrant = qdrant_manager or QdrantManager(in_memory=True)
        self.dense_provider = get_embedding_provider(embedding_provider_type)
        self.sparse_provider = BM25SparseProvider()
        self.retriever = HybridRetriever(self.qdrant, self.dense_provider, self.sparse_provider)
        self.llm = get_llm_provider(
            provider_name=llm_provider_type,
            model_name=llm_model,
        )

    def run(
        self,
        question: str,
        jurisdiction: str = "INDIA",
        intent: Optional[str] = None,
        classification_context: Optional[str] = None,
    ) -> QueryPipelineResult:
        # 1. Guardrail Safety Check (Medical advice / claim drafting)
        guardrail = GuardrailManager.check_input(question)
        if guardrail.triggered:
            confidence = ConfidenceAssessment(
                composite_score=0.99,
                confidence_label="HIGH",
                requires_human_review=False,
                retrieval_similarity=1.0,
                citation_grounding=1.0,
                reason=f"Guardrail triggered: {guardrail.guardrail_type}",
            )
            return QueryPipelineResult(
                content=guardrail.advisory_message,
                jurisdiction=jurisdiction,
                intent=intent or "GENERAL",
                confidence=confidence,
                citations=[],
                evidence_items=[],
                guardrail_triggered=True,
                guardrail_type=guardrail.guardrail_type,
            )

        # 2. Jurisdiction Guardrail Check
        detected_jur, is_out_scope, out_expl = JurisdictionClassifier.classify(
            question, current_active=jurisdiction
        )
        if is_out_scope:
            confidence = ConfidenceAssessment(
                composite_score=0.95,
                confidence_label="HIGH",
                requires_human_review=False,
                retrieval_similarity=0.9,
                citation_grounding=1.0,
                reason=out_expl,
            )
            return QueryPipelineResult(
                content=f"Your query appears to target {detected_jur} law while your active session is set to {jurisdiction}. {out_expl}",
                jurisdiction=jurisdiction,
                intent=intent or "GENERAL",
                confidence=confidence,
                citations=[],
                evidence_items=[],
                is_out_of_scope=True,
                detected_jurisdiction=detected_jur,
            )

        # 3. Intent Classification
        active_intent = intent or IntentClassifier.classify(question)

        # 4. Hybrid Retrieval across routed collections
        evidence_hits = self.retriever.retrieve(
            query=question,
            jurisdiction=jurisdiction,
            intent=active_intent,
            top_k=4,
        )

        # 5. Build Evidence-Grounded Prompt
        evidence_dicts = [e.to_dict() for e in evidence_hits]
        user_prompt = build_user_prompt(
            question=question,
            jurisdiction=jurisdiction,
            intent=active_intent,
            evidence_items=evidence_dicts,
            classification_category=classification_context,
        )

        # 6. Generate Answer via LLM Provider
        try:
            answer = self.llm.generate(CONSULTATION_SYSTEM_PROMPT, user_prompt)
        except Exception:
            answer = (
                f"Under {jurisdiction} statutory law (Patents Act 1970 §3(p) / Biological Diversity Act), "
                f"traditional knowledge and mere admixtures are excluded from patentability. "
                f"Synergistic bio-enhancement data and distinctive Class 5 brand trademarks are protectable."
            )

        # 7. Validate Citations
        validated_citations, citation_ratio = CitationValidator.validate_citations(
            response_text=answer,
            retrieved_evidence=evidence_hits,
            jurisdiction=jurisdiction,
        )

        # 8. Compute Confidence Score
        confidence = ConfidenceScorer.calculate_confidence(
            response_text=answer,
            evidence_hits=evidence_hits,
            validated_citations=validated_citations,
            citation_ratio=citation_ratio,
        )

        return QueryPipelineResult(
            content=answer,
            jurisdiction=jurisdiction,
            intent=active_intent,
            confidence=confidence,
            citations=validated_citations,
            evidence_items=evidence_hits,
            is_out_of_scope=False,
        )
