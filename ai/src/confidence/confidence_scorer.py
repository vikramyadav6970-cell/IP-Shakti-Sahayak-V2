"""
ai/src/confidence/confidence_scorer.py

Composite confidence scoring engine evaluating retrieval strength, citation grounding,
and response certainty (ai/coding_conventions.md).
"""

from dataclasses import dataclass
from typing import List, Tuple
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
        # 1. Retrieval strength component
        if evidence_hits:
            top_score = max(h.score for h in evidence_hits)
            retrieval_similarity = min(1.0, max(0.4, top_score if top_score <= 1.0 else 0.88))
        else:
            retrieval_similarity = 0.50

        # 2. Citation grounding component
        citation_grounding = min(1.0, max(0.3, citation_ratio))

        # 3. Uncertainty penalty check
        uncertainty_phrases = [
            "unclear from statutory text",
            "not explicitly specified",
            "consult a lawyer immediately",
            "cannot be definitively determined",
            "conflicting court decisions",
        ]
        penalty = 0.0
        resp_lower = response_text.lower()
        for phrase in uncertainty_phrases:
            if phrase in resp_lower:
                penalty += 0.08

        # Weighted composite score: 50% retrieval + 50% citation grounding - penalty
        composite = (0.50 * retrieval_similarity) + (0.50 * citation_grounding) - penalty
        composite = round(min(0.98, max(0.30, composite)), 2)

        # Determine label and human review threshold
        if composite >= 0.85:
            label = "HIGH"
            requires_review = False
            reason = "High statutory evidence grounding with verified citations."
        elif composite >= 0.70:
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
