"""
ai/tests/citations/test_citation_validator.py

Unit tests for citation validation against retrieved evidence.
"""

from src.citations.citation_validator import CitationValidator
from src.retrieval.retriever import RetrievedEvidence


def test_citation_validation():
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
            score=0.92,
            metadata={},
        )
    ]

    response_text = "Under Section 3(p) of the Patents Act, traditional knowledge is not patentable."
    validated, ratio = CitationValidator.validate_citations(response_text, evidence, "INDIA")

    assert len(validated) == 1
    assert validated[0].is_grounded is True
    assert ratio >= 0.9
