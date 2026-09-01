"""
ai/tests/confidence/test_confidence_scorer.py

Unit tests for composite confidence score computation.
"""

from src.citations.citation_validator import ValidatedCitation
from src.confidence.confidence_scorer import ConfidenceScorer
from src.retrieval.retriever import RetrievedEvidence


def test_confidence_scoring_high():
    evidence = [
        RetrievedEvidence(
            chunk_id="c1",
            content="Section 3(p) traditional knowledge exclusions",
            doc_title="The Patents Act, 1970",
            section_ref="Section 3(p)",
            source_url="https://wipolex.wipo.int/en/legislation/details/2143",
            jurisdiction="INDIA",
            document_type="STATUTE",
            target_collection="legal_statutory",
            verification_status="VERIFIED_OFFICIAL_GAZETTE",
            score=0.95,
            metadata={},
        )
    ]
    citations = [
        ValidatedCitation(
            document_title="The Patents Act, 1970",
            section_ref="Section 3(p)",
            source_url="https://wipolex.wipo.int/en/legislation/details/2143",
            jurisdiction="INDIA",
            document_type="STATUTE",
            verification_status="VERIFIED_OFFICIAL_GAZETTE",
            is_grounded=True,
            relevance_score=0.95,
        )
    ]

    response_text = "Under Section 3(p) of the Patents Act 1970, traditional knowledge is strictly excluded."
    assessment = ConfidenceScorer.calculate_confidence(response_text, evidence, citations, 1.0)

    assert assessment.composite_score >= 0.85
    assert assessment.confidence_label == "HIGH"
    assert assessment.requires_human_review is False
