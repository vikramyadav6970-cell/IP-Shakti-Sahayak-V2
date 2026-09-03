"""
ai/src/confidence/confidence_scorer.py

Composite confidence scoring engine evaluating retrieval strength, citation grounding,
and response certainty (ai/coding_conventions.md).
"""

from dataclasses import dataclass
from typing import List, Tuple, Any, Dict, Optional
from src.citations.citation_validator import ValidatedCitation
from src.retrieval.retriever import RetrievedEvidence


@dataclass
class ConfidenceAssessment:
    """Detailed confidence breakdown."""
    composite_score: float
    confidence_label: str       # "HIGH" | "MEDIUM" | "LOW"
    requires_human_review: bool
    retrieval_similarity: float
    citation_grounding: float
    reason: str


@dataclass
class MultiDomainConfidenceAssessment:
    """Composite confidence breakdown across multiple specialized agents."""
    overall_composite_score: float
    overall_confidence_label: str       # "HIGH" | "MEDIUM" | "LOW"
    requires_human_review: bool
    domain_confidence: dict[str, dict[str, Any]]


class ConfidenceScorer:
    """Calculates multidimensional confidence score for consultation responses."""

    @staticmethod
    def calculate_confidence(
        response_text: str,
        evidence_hits: List[RetrievedEvidence],
        validated_citations: List[ValidatedCitation],
        citation_ratio: float,
    ) -> ConfidenceAssessment:
        """
        Computes composite confidence based on retrieval similarity, citation overlap,
        and linguistic uncertainty markers.
        """
        # 1. Retrieval strength component (scaled from dense cosine similarity range)
        if evidence_hits:
            top_score = max(h.score for h in evidence_hits)
            avg_score = sum(h.score for h in evidence_hits) / len(evidence_hits)
            # Map typical cosine similarity [0.45, 0.75] -> [0.60, 0.98]
            norm_top = 0.60 + ((min(0.75, max(0.45, top_score)) - 0.45) / 0.30) * 0.38
            norm_avg = 0.55 + ((min(0.70, max(0.40, avg_score)) - 0.40) / 0.30) * 0.35
            retrieval_similarity = 0.70 * norm_top + 0.30 * norm_avg
        else:
            retrieval_similarity = 0.45

        # 2. Citation grounding component (percentage of retrieved evidence cited/grounded)
        citation_grounding = min(1.0, max(0.40, citation_ratio))

        # 3. Uncertainty penalty check (detecting hedge phrases / legal ambiguity)
        uncertainty_phrases = [
            "unclear from statutory text",
            "not explicitly specified",
            "consult a lawyer immediately",
            "cannot be definitively determined",
            "conflicting court decisions",
            "statutory ambiguity",
            "unsettled legal principle",
        ]
        penalty = 0.0
        resp_lower = response_text.lower()
        for phrase in uncertainty_phrases:
            if phrase in resp_lower:
                penalty += 0.08

        # Weighted composite score: 55% retrieval strength + 45% citation grounding - penalty
        composite = (0.55 * retrieval_similarity) + (0.45 * citation_grounding) - penalty
        composite = round(min(0.98, max(0.35, composite)), 2)

        # Determine label and human review threshold
        if composite >= 0.82:
            label = "HIGH"
            requires_review = False
            reason = "High statutory evidence grounding with verified citations."
        elif composite >= 0.68:
            label = "MEDIUM"
            requires_review = False
            reason = "Moderate evidence grounding; statutory principles apply."
        else:
            label = "LOW"
            requires_review = True
            reason = "Low retrieval match or high legal ambiguity; expert review recommended."

        return ConfidenceAssessment(
            composite_score=composite,
            confidence_label=label,
            requires_human_review=requires_review,
            retrieval_similarity=round(retrieval_similarity, 2),
            citation_grounding=round(citation_grounding, 2),
            reason=reason,
        )

    @staticmethod
    def calculate_multi_domain_confidence(
        response_text: str,
        domain_evidence_map: dict[str, Any],
        validated_citations: List[ValidatedCitation],
    ) -> MultiDomainConfidenceAssessment:
        """
        Computes independent confidence assessments for each participating domain agent,
        and derives an overall confidence score driven by the weakest domain.
        """
        domain_results: dict[str, dict[str, Any]] = {}

        for domain_name, data in domain_evidence_map.items():
            hits_found = data.get("hits_found", False)
            ev_list = data.get("evidence", [])

            if not hits_found or not ev_list:
                domain_results[domain_name] = {
                    "score": 0.38,
                    "label": "LOW",
                    "requires_human_review": True,
                    "reason": f"No statutory chunks retrieved for domain '{domain_name}'; zero-hallucination policy applied.",
                }
                continue

            # Check citation grounding specifically for this domain's evidence
            domain_matched = 0
            for c in validated_citations:
                c_title = (getattr(c, "document_title", None) or (c.get("document_title") if isinstance(c, dict) else "")).lower()
                for e in ev_list:
                    e_title = (getattr(e, "doc_title", None) or (e.get("doc_title") if isinstance(e, dict) else "")).lower()
                    if c_title and e_title and (c_title in e_title or e_title in c_title):
                        domain_matched += 1
                        break
            ratio = domain_matched / max(1, len(ev_list))

            assessment = ConfidenceScorer.calculate_confidence(
                response_text=response_text,
                evidence_hits=ev_list,
                validated_citations=validated_citations,
                citation_ratio=ratio,
            )

            domain_results[domain_name] = {
                "score": assessment.composite_score,
                "label": assessment.confidence_label,
                "requires_human_review": assessment.requires_human_review,
                "reason": assessment.reason,
            }

        # Overall composite is determined by the weakest domain to prevent masking
        scores = [d["score"] for d in domain_results.values()] if domain_results else [0.50]
        min_score = min(scores)
        
        if min_score >= 0.82:
            overall_label = "HIGH"
            overall_review = False
        elif min_score >= 0.68:
            overall_label = "MEDIUM"
            overall_review = False
        else:
            overall_label = "LOW"
            overall_review = True

        return MultiDomainConfidenceAssessment(
            overall_composite_score=min_score,
            overall_confidence_label=overall_label,
            requires_human_review=overall_review,
            domain_confidence=domain_results,
        )
