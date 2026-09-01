"""
ai/src/classification/product_classifier.py

Deterministic and LLM-assisted Product Classification Engine for Ayurvedic, Herbal, and Traditional Innovations.
Categorizes products under the 6 canonical statutory categories:
1. Classical / Generic Medicine (First-Schedule authoritative text)
2. Patent-or-Proprietary Medicine (Section 3(h))
3. New or Non-Classical Drug (Rule 158B)
4. Phytopharmaceutical (CDSCO Form CT-20 / New Drugs Rules 2019)
5. Ayurveda-Aahar / Nutraceutical (FSSAI Regulations 2022)
6. Cosmetic (Topical beautification / cleansing without therapeutic claims)
"""

from dataclasses import dataclass
import re
from typing import Any, Dict, List, Optional


CATEGORIES_REGISTRY = {
    "CLASSICAL_MEDICINE": {
        "id": "CLASSICAL_MEDICINE",
        "name": "Classical / Generic Medicine",
        "short_desc": "Formulation and method drawn verbatim from a First-Schedule authoritative text (e.g. AFI, API, Charaka, Sushruta).",
        "statutory_authority": "Drugs & Cosmetics Act 1940 & Rules 1945 Rule 153 (Form 25-D)",
        "regulatory_pathway": "Form 25-D AYUSH Manufacturing License without requiring clinical efficacy proof.",
        "patent_eligibility": "EXCLUDED",
        "patent_reasoning": "Barred under Patents Act 1970 Section 3(p) (Traditional Knowledge) and Section 3(e) (admixture).",
        "abs_requirement": "SBB Prior Intimation for Indian entities; NBA Form I approval for foreign entities.",
    },
    "PROPRIETARY_MEDICINE": {
        "id": "PROPRIETARY_MEDICINE",
        "name": "Patent-or-Proprietary Medicine",
        "short_desc": "Formulation containing First Schedule ingredients in proprietary ratios, modified delivery, or with non-classical excipients (Section 3(h)).",
        "statutory_authority": "Drugs & Cosmetics Act 1940 Section 3(h) & Rule 158B (Form 25-D)",
        "regulatory_pathway": "Form 25-D AYUSH License with published textual or safety proof under Rule 158B.",
        "patent_eligibility": "CONDITIONAL",
        "patent_reasoning": "May be patentable if novel synergistic bio-enhancement or distinct extraction process is proven with comparative data.",
        "abs_requirement": "SBB Prior Intimation for commercial utilization in India; NBA approval for foreign access.",
    },
    "NEW_DRUG": {
        "id": "NEW_DRUG",
        "name": "New or Non-Classical Drug",
        "short_desc": "Novel botanical entity, new therapeutic indication, or new route of administration requiring proof of safety and clinical efficacy.",
        "statutory_authority": "Drugs and Cosmetics Rules 1945 Rule 158B(IV) & AYUSH Guidelines",
        "regulatory_pathway": "Phase I-III clinical trial evaluation and AYUSH State Licensing Authority special approval.",
        "patent_eligibility": "HIGH",
        "patent_reasoning": "High patentability for novel therapeutic composition, provided unexpected synergy over §3(p)/§3(e) is proven.",
        "abs_requirement": "Mandatory NBA Form I / Form III clearance prior to patent grant.",
    },
    "PHYTOPHARMACEUTICAL": {
        "id": "PHYTOPHARMACEUTICAL",
        "name": "Phytopharmaceutical",
        "short_desc": "Purified and standardized fraction of medicinal plant (min 4 bioactive markers) with scientific clinical evaluation.",
        "statutory_authority": "CDSCO / New Drugs and Clinical Trials Rules 2019 (Form CT-20)",
        "regulatory_pathway": "Form CT-20 Central Licensing from CDSCO (DCGI) with full IND dossier.",
        "patent_eligibility": "HIGH",
        "patent_reasoning": "Purified fraction, distinctive extraction method, and characterized bioactive markers are eligible for composition and process patents.",
        "abs_requirement": "Mandatory NBA Form I approval for access and Form III before patent grant.",
    },
    "AYURVEDA_AAHARA": {
        "id": "AYURVEDA_AAHARA",
        "name": "Ayurveda-Aahar / Nutraceutical",
        "short_desc": "Food or dietary supplement prepared per classical recipes for wellness and physiological balance (no synthetic vitamins/isolates).",
        "statutory_authority": "Food Safety and Standards (Ayurveda Aahara) Regulations 2022 (FSSAI)",
        "regulatory_pathway": "FSSAI License under Ayurveda-Aahara with mandatory dedicated logo on primary packaging.",
        "patent_eligibility": "EXCLUDED",
        "patent_reasoning": "Excluded under Section 3(p) and 3(e) as traditional food. Trade secret and trademark are primary IP tools.",
        "abs_requirement": "SBB/NBA compliance applies for commercial biological resource procurement.",
    },
    "COSMETIC": {
        "id": "COSMETIC",
        "name": "Cosmetic",
        "short_desc": "Topical formulation intended for cleansing, beautifying, or altering external appearance without disease treatment claims.",
        "statutory_authority": "Drugs & Cosmetics Rules 1945 Part XV (Cosmetics Licensing - Form 32)",
        "regulatory_pathway": "Form 32 Cosmetic Manufacturing License from State Drug Controller / FDA.",
        "patent_eligibility": "CONDITIONAL",
        "patent_reasoning": "Novel topical delivery base or unexpected synergistic dermatological action may be patentable.",
        "abs_requirement": "Biological resource procurement subject to State Biodiversity Board rules.",
    },
}

# Lookup map supporting normalized names and ids
CANONICAL_NAME_MAP = {
    "classical / generic medicine": "CLASSICAL_MEDICINE",
    "classical medicine": "CLASSICAL_MEDICINE",
    "classical_medicine": "CLASSICAL_MEDICINE",
    "patent-or-proprietary medicine": "PROPRIETARY_MEDICINE",
    "patent or proprietary medicine": "PROPRIETARY_MEDICINE",
    "proprietary medicine": "PROPRIETARY_MEDICINE",
    "proprietary_medicine": "PROPRIETARY_MEDICINE",
    "new or non-classical drug": "NEW_DRUG",
    "new drug": "NEW_DRUG",
    "new_drug": "NEW_DRUG",
    "phytopharmaceutical": "PHYTOPHARMACEUTICAL",
    "phytopharmaceutical drug": "PHYTOPHARMACEUTICAL",
    "ayurveda-aahar / nutraceutical": "AYURVEDA_AAHARA",
    "ayurveda-aahar": "AYURVEDA_AAHARA",
    "ayurveda aahara": "AYURVEDA_AAHARA",
    "ayurveda_aahara": "AYURVEDA_AAHARA",
    "nutraceutical": "AYURVEDA_AAHARA",
    "cosmetic": "COSMETIC",
    "ayurvedic cosmetic": "COSMETIC",
}


def normalize_category_key(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    cleaned = raw.strip().lower()
    return CANONICAL_NAME_MAP.get(cleaned, raw.upper() if raw.upper() in CATEGORIES_REGISTRY else None)


@dataclass
class FormulationInput:
    """Input payload describing a user's product or formulation."""
    name: str
    description: str
    ingredients: List[str]
    has_classical_text_reference: bool = False
    classical_text_name: Optional[str] = None
    is_strict_classical_recipe: bool = False
    has_novel_excipients_or_delivery: bool = False
    is_purified_standardized_fraction: bool = False
    is_food_or_dietary_supplement: bool = False
    is_cosmetic_or_topical_care: bool = False
    is_new_botanical_or_indication: bool = False
    has_synthetic_additives: bool = False
    target_market: str = "DOMESTIC"
    user_selected_category: Optional[str] = None


@dataclass
class ProductClassificationResult:
    """Classification output with complete regulatory pathway and IP mapping."""
    category: str
    category_name: str
    regulatory_pathway: str
    statutory_authority: str
    reasoning: str
    rules_fired: List[str]
    is_reconciled: bool
    user_selected_category: Optional[str]
    patent_eligibility: str
    patent_reasoning: str
    abs_requirement: str
    ip_protection_map: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "category_name": self.category_name,
            "regulatory_pathway": self.regulatory_pathway,
            "statutory_authority": self.statutory_authority,
            "reasoning": self.reasoning,
            "rules_fired": self.rules_fired,
            "is_reconciled": self.is_reconciled,
            "user_selected_category": self.user_selected_category,
            "patent_eligibility": self.patent_eligibility,
            "patent_reasoning": self.patent_reasoning,
            "abs_requirement": self.abs_requirement,
            "ip_protection_map": self.ip_protection_map,
        }


class ProductClassifier:
    """Deterministic rules engine and classification reference for 6 statutory categories."""

    @classmethod
    def classify(cls, form: FormulationInput) -> ProductClassificationResult:
        rules_fired: List[str] = []
        desc = (form.description + " " + " ".join(form.ingredients)).lower()

        is_fraction = form.is_purified_standardized_fraction or bool(
            re.search(r"\b(?:purified\s+fraction|isolated\s+marker|phytopharmaceutical|bioactive\s+fraction)\b", desc)
        )
        is_food = form.is_food_or_dietary_supplement or bool(
            re.search(r"\b(?:food|dietary|aahara|nutraceutical|supplement|beverage|tea|candy)\b", desc)
        )
        is_cosmetic = form.is_cosmetic_or_topical_care or bool(
            re.search(r"\b(?:cosmetic|cream|lotion|shampoo|soap|face\s+wash|beautifying|hair\s+oil|sunscreen)\b", desc)
        )
        is_new_entity = form.is_new_botanical_or_indication or bool(
            re.search(r"\b(?:new\s+drug|novel\s+indication|untested\s+species|non-classical\s+botanical)\b", desc)
        )
        has_synthetic = form.has_synthetic_additives or bool(
            re.search(r"\b(?:synthetic|vitamin\s+[a-d]|mineral\s+premix|isolated\s+chemical)\b", desc)
        )
        is_classical_recipe = form.is_strict_classical_recipe and form.has_classical_text_reference
        has_novel_tech = form.has_novel_excipients_or_delivery or bool(
            re.search(r"\b(?:nanoparticle|liposomal|bioavailability\s+enhancer|sustained\s+release|novel\s+excipient)\b", desc)
        )

        # 1. Phytopharmaceutical Drug check
        if is_fraction and not is_food and not is_cosmetic:
            category_key = "PHYTOPHARMACEUTICAL"
            reasoning = "Formulation contains purified/standardized fractions of medicinal plants evaluated under New Drugs Rules 2019."
            rules_fired.append("RULE_STANDARDIZED_FRACTION_PHYTOPHARMACEUTICAL")

        # 2. Ayurvedic Cosmetic check
        elif is_cosmetic and not is_food:
            category_key = "COSMETIC"
            reasoning = "Topical preparation intended for external beautification, cleansing, or skin care without claiming therapeutic cure for disease."
            rules_fired.append("RULE_COSMETIC_TOPICAL_BEAUTIFICATION")

        # 3. Ayurveda-Aahara / Nutraceutical check
        elif is_food and not has_synthetic:
            category_key = "AYURVEDA_AAHARA"
            reasoning = "Food or dietary preparation made per classical recipes without synthetic vitamins, minerals, or chemical isolates."
            rules_fired.append("RULE_FSSAI_AYURVEDA_AAHARA_2022")

        # 4. New or Non-Classical Drug check
        elif is_new_entity and not is_classical_recipe:
            category_key = "NEW_DRUG"
            reasoning = "Formulation utilizes non-classical botanicals or novel indications requiring clinical proof of safety and efficacy under Rule 158B."
            rules_fired.append("RULE_NEW_DRUG_RULE_158B")

        # 5. Classical ASU Medicine check
        elif is_classical_recipe and not has_novel_tech:
            category_key = "CLASSICAL_MEDICINE"
            reasoning = "Ingredients and manufacturing process strictly adhere to authoritative texts in the First Schedule."
            rules_fired.append("RULE_CLASSICAL_FIRST_SCHEDULE_TEXT")

        # 6. Proprietary ASU Medicine check (Default)
        else:
            category_key = "PROPRIETARY_MEDICINE"
            reasoning = "Formulation uses Ayurvedic ingredients in proprietary proportions, novel delivery mechanisms, or modified classical combinations."
            rules_fired.append("RULE_PROPRIETARY_MODIFIED_FORMULATION")

        final_category = category_key
        is_reconciled = False
        if form.user_selected_category:
            normalized_selected = normalize_category_key(form.user_selected_category)
            if normalized_selected and normalized_selected in CATEGORIES_REGISTRY:
                if normalized_selected != category_key:
                    is_reconciled = True
                    final_category = normalized_selected
                    rules_fired.append(f"USER_OVERRIDE_RECONCILIATION: User selected {final_category}")

        meta = CATEGORIES_REGISTRY[final_category]

        ip_map = {
            "patent": {"eligibility": meta["patent_eligibility"], "reason": meta["patent_reasoning"]},
            "trademark": {"eligibility": "HIGH", "nice_class": "Class 5 (Medicine) / Class 3 (Cosmetic) / Class 30 (Food)"},
            "abs": {"eligibility": "MANDATORY", "action": meta["abs_requirement"]},
        }

        return ProductClassificationResult(
            category=final_category,
            category_name=meta["name"],
            regulatory_pathway=meta["regulatory_pathway"],
            statutory_authority=meta["statutory_authority"],
            reasoning=reasoning,
            rules_fired=rules_fired,
            is_reconciled=is_reconciled,
            user_selected_category=form.user_selected_category,
            patent_eligibility=meta["patent_eligibility"],
            patent_reasoning=meta["patent_reasoning"],
            abs_requirement=meta["abs_requirement"],
            ip_protection_map=ip_map,
        )
