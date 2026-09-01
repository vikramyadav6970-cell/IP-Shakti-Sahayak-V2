"""
ai/tests/classification/test_jurisdiction_classifier.py

Unit tests for jurisdiction detection and out-of-scope guardrail triggers.
"""

from src.classification.jurisdiction_classifier import JurisdictionClassifier


def test_jurisdiction_detection():
    # India query in India session
    detected, out_scope, _ = JurisdictionClassifier.classify(
        "Is my formulation patentable under Section 3(p) and Section 3(d)?",
        current_active="INDIA",
    )
    assert detected == "INDIA"
    assert out_scope is False

    # International query while in India session -> triggers out of scope
    detected_intl, out_scope_intl, expl = JurisdictionClassifier.classify(
        "Can I file a US patent application with USPTO and comply with TRIPS Article 27?",
        current_active="INDIA",
    )
    assert detected_intl == "INTERNATIONAL"
    assert out_scope_intl is True
    assert "international legal markers" in expl.lower()

    # India query while in International session -> triggers out of scope
    detected_in, out_scope_in, expl2 = JurisdictionClassifier.classify(
        "Do I need NBA Form I and SBB intimation under Biological Diversity Act?",
        current_active="INTERNATIONAL",
    )
    assert detected_in == "INDIA"
    assert out_scope_in is True
    assert "indian statutory markers" in expl2.lower()
