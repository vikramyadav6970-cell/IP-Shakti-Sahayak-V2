"""
ai/tests/reasoning/test_query_pipeline.py

Integration tests for the complete QueryPipeline.
"""

from src.reasoning.query_pipeline import QueryPipeline


def test_query_pipeline_statutory_run():
    pipeline = QueryPipeline(llm_provider_type="mock", embedding_provider_type="mock")
    result = pipeline.run(
        question="Is classical Triphala patentable under Section 3(p)?",
        jurisdiction="INDIA",
        intent="PATENT",
    )
    assert result.jurisdiction == "INDIA"
    assert result.confidence.composite_score >= 0.60
    assert len(result.citations) >= 1
    assert result.is_out_of_scope is False
    assert result.guardrail_triggered is False


def test_query_pipeline_medical_guardrail():
    pipeline = QueryPipeline(llm_provider_type="mock", embedding_provider_type="mock")
    result = pipeline.run(
        question="How do I cure my diabetes with herbal powder?",
        jurisdiction="INDIA",
    )
    assert result.guardrail_triggered is True
    assert result.guardrail_type == "MEDICAL_ADVICE"
    assert "medical diagnostic tool" in result.content


def test_query_pipeline_jurisdiction_mismatch():
    pipeline = QueryPipeline(llm_provider_type="mock", embedding_provider_type="mock")
    result = pipeline.run(
        question="Can I file this with USPTO and comply with TRIPS Article 27?",
        jurisdiction="INDIA",
    )
    assert result.is_out_of_scope is True
    assert result.detected_jurisdiction == "INTERNATIONAL"
