"""
ai/tests/classification/test_product_classifier.py

Unit tests for deterministic product classification and IP protection mapping.
"""

from src.classification.product_classifier import ProductClassifier, FormulationInput


def test_classical_medicine_classification():
    form = FormulationInput(
        name="Triphala Churna",
        description="Classical Ayurvedic formulation consisting of Haritaki, Bibhitaki, and Amalaki.",
        ingredients=["Terminalia chebula", "Terminalia bellirica", "Phyllanthus emblica"],
        has_classical_text_reference=True,
        classical_text_name="Ayurvedic Formulary of India",
        is_strict_classical_recipe=True,
        has_novel_excipients_or_delivery=False,
    )
    result = ProductClassifier.classify(form)
    assert result.category == "CLASSICAL_MEDICINE"
    assert "RULE_CLASSICAL_FIRST_SCHEDULE_TEXT" in result.rules_fired
    assert result.ip_protection_map["patent"]["eligibility"] == "EXCLUDED"
    assert "Section 3(p)" in result.ip_protection_map["patent"]["reason"]


def test_phytopharmaceutical_classification():
    form = FormulationInput(
        name="Standardized Curcuminoids 95%",
        description="Purified bioactive fraction of Curcuma longa with characterized biomarkers.",
        ingredients=["Curcuma longa rhizome purified fraction"],
        is_purified_standardized_fraction=True,
        is_food_or_dietary_supplement=False,
    )
    result = ProductClassifier.classify(form)
    assert result.category == "PHYTOPHARMACEUTICAL"
    assert "RULE_STANDARDIZED_FRACTION_PHYTOPHARMACEUTICAL" in result.rules_fired
    assert result.ip_protection_map["patent"]["eligibility"] == "HIGH"


def test_ayurveda_aahara_classification():
    form = FormulationInput(
        name="Herbal Golden Milk Premix",
        description="Ayurveda Aahara beverage mix containing turmeric, black pepper, cardamom, and almond flour.",
        ingredients=["Curcuma longa", "Piper nigrum", "Elettaria cardamomum", "Prunus dulcis"],
        is_food_or_dietary_supplement=True,
        has_synthetic_additives=False,
    )
    result = ProductClassifier.classify(form)
    assert result.category == "AYURVEDA_AAHARA"
    assert "RULE_FSSAI_AYURVEDA_AAHARA_2022" in result.rules_fired
    assert "FSSAI License" in result.regulatory_pathway


def test_reconciliation_override():
    form = FormulationInput(
        name="Novel Turmeric Complex",
        description="Modified formulation with piperine bio-enhancer.",
        ingredients=["Curcuma longa", "Piperine"],
        has_novel_excipients_or_delivery=True,
        user_selected_category="PHYTOPHARMACEUTICAL",
    )
    result = ProductClassifier.classify(form)
    assert result.is_reconciled is True
    assert result.category == "PHYTOPHARMACEUTICAL"
    assert any("USER_OVERRIDE" in r for r in result.rules_fired)
