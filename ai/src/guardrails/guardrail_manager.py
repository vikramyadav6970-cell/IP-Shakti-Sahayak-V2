"""
ai/src/guardrails/guardrail_manager.py

Domain-specific safety guardrails and disclaimer injection for IP-SAKTI Sahayak.
"""

from dataclasses import dataclass
import re
from typing import Optional, Tuple


@dataclass
class GuardrailResult:
    """Outcome of guardrail analysis."""
    triggered: bool
    guardrail_type: Optional[str]  # "MEDICAL_ADVICE" | "PATENT_DRAFTING" | "JURISDICTION_MISMATCH" | None
    advisory_message: Optional[str]


class GuardrailManager:
    """Enforces boundaries between legal/regulatory decision support and regulated professions."""

    MEDICAL_DIAGNOSIS_PATTERNS = [
        r"\bhow\s+do\s+i\s+cure\s+my\b",
        r"\btreat\s+my\s+(?:cancer|diabetes|arthritis|infection|disease)\b",
        r"\bwhat\s+dose\s+should\s+i\s+take\b",
        r"\bprescribe\s+medicine\s+for\b",
        r"\bi\s+have\s+(?:fever|pain|covid|hypertension)\b",
    ]

    PATENT_DRAFTING_PATTERNS = [
        r"\bdraft\s+a\s+complete\s+patent\s+application\b",
        r"\bwrite\s+independent\s+claims\s+for\s+filing\b",
        r"\brepresent\s+me\s+in\s+court\b",
    ]

    @classmethod
    def check_input(cls, query: str) -> GuardrailResult:
        q = query.lower()

        # 1. Medical Diagnosis Check
        for pattern in cls.MEDICAL_DIAGNOSIS_PATTERNS:
            if re.search(pattern, q):
                return GuardrailResult(
                    triggered=True,
                    guardrail_type="MEDICAL_ADVICE",
                    advisory_message=(
                        "IP-SAKTI Sahayak is an Intellectual Property and Regulatory Information System, "
                        "not a medical diagnostic tool. For medical advice, diagnosis, or personalized prescriptions, "
                        "please consult a qualified Registered Ayurvedic Medical Practitioner (BAMS/MD)."
                    ),
                )

        # 2. Complete Claim Drafting Check
        for pattern in cls.PATENT_DRAFTING_PATTERNS:
            if re.search(pattern, q):
                return GuardrailResult(
                    triggered=True,
                    guardrail_type="PATENT_DRAFTING",
                    advisory_message=(
                        "IP-SAKTI Sahayak provides statutory patentability assessment and prior-art guidance. "
                        "Formal patent drafting, claim drafting for IPO submission, and patent prosecution require "
                        "a Registered Patent Agent or IP Attorney."
                    ),
                )

        return GuardrailResult(triggered=False, guardrail_type=None, advisory_message=None)
