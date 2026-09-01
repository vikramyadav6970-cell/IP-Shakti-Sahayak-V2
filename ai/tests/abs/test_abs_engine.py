"""
ai/tests/abs/test_abs_engine.py

Unit tests for Access and Benefit Sharing (ABS) assessment rules.
"""

from src.abs.abs_engine import ABSEngine, ABSInput


def test_foreign_entity_commercial_access():
    data = ABSInput(
        entity_nationality="FOREIGN",
        biological_resources=["Withania somnifera", "Bacopa monnieri"],
        resource_origin="INDIA",
        activity_type="COMMERCIAL_UTILIZATION",
    )
    result = ABSEngine.evaluate(data)
    assert result.approval_required is True
    assert "National Biodiversity Authority" in result.approving_authority
    assert result.form_type == "Form I"
    assert result.relevance_label == "HIGH"


def test_patent_filing_on_indian_resource():
    data = ABSInput(
        entity_nationality="INDIAN",
        biological_resources=["Curcuma longa"],
        resource_origin="INDIA",
        activity_type="IPR_APPLICATION",
    )
    result = ABSEngine.evaluate(data)
    assert result.approval_required is True
    assert "Form III" in result.form_type
    assert any("Section 6" in p for p in result.statutory_provisions)


def test_ayush_practitioner_exemption():
    data = ABSInput(
        entity_nationality="INDIAN",
        biological_resources=["Terminalia chebula"],
        resource_origin="INDIA",
        activity_type="COMMERCIAL_UTILIZATION",
        is_ayush_practitioner=True,
        is_codified_traditional_knowledge=True,
    )
    result = ABSEngine.evaluate(data)
    assert result.approval_required is False
    assert result.relevance_label == "LOW"
    assert "2023" in result.benefit_sharing_levy
