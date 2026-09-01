"""
ai/src/abs/abs_engine.py

Access and Benefit Sharing (ABS) Compliance Engine under the Biological Diversity Act, 2002
and Biological Diversity (Amendment) Act, 2023 (context.md §3).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ABSInput:
    """Input parameters for ABS regulatory assessment."""
    entity_nationality: str         # "INDIAN" | "FOREIGN" | "INDIAN_WITH_FOREIGN_EQUITY"
    biological_resources: List[str] # List of botanical/biological resources (e.g. ["Curcuma longa", "Withania somnifera"])
    resource_origin: str            # "INDIA" | "FOREIGN" | "BOTH"
    activity_type: str              # "COMMERCIAL_UTILIZATION" | "RESEARCH" | "IPR_APPLICATION" | "TRANSFER_OF_RESULTS"
    is_ayush_practitioner: bool = False
    is_codified_traditional_knowledge: bool = False
    is_normally_traded_commodity: bool = False


@dataclass
class ABSAssessmentResponse:
    """Structured compliance assessment with actionable next steps and statutory references."""
    approval_required: bool
    approving_authority: str       # "National Biodiversity Authority (NBA)" | "State Biodiversity Board (SBB)" | "Exempt"
    form_type: Optional[str]       # "Form I" | "Form II" | "Form III" | "Form IV" | "SBB Intimation"
    benefit_sharing_levy: str
    relevance_label: str           # "HIGH" | "MEDIUM" | "LOW" | "NOT_APPLICABLE"
    statutory_provisions: List[str]
    next_steps: List[str]
    audit_notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approval_required": self.approval_required,
            "approving_authority": self.approving_authority,
            "form_type": self.form_type,
            "benefit_sharing_levy": self.benefit_sharing_levy,
            "relevance_label": self.relevance_label,
            "statutory_provisions": self.statutory_provisions,
            "next_steps": self.next_steps,
            "audit_notes": self.audit_notes,
        }


class ABSEngine:
    """Evaluates biological diversity access compliance and benefit sharing obligations."""

    @classmethod
    def evaluate(cls, data: ABSInput) -> ABSAssessmentResponse:
        next_steps: List[str] = []
        statutory_provisions: List[str] = []
        audit_notes: List[str] = []

        is_foreign = data.entity_nationality in ["FOREIGN", "INDIAN_WITH_FOREIGN_EQUITY"]
        is_india_resource = data.resource_origin in ["INDIA", "BOTH"]

        # Case 0: Non-Indian biological resources only
        if not is_india_resource:
            return ABSAssessmentResponse(
                approval_required=False,
                approving_authority="Exempt",
                form_type=None,
                benefit_sharing_levy="Not applicable for non-Indian biological resources.",
                relevance_label="NOT_APPLICABLE",
                statutory_provisions=["Biological Diversity Act Section 1 (Territorial Scope)"],
                next_steps=["Maintain documentation of foreign origin (import certificate, customs bill of entry)."],
                audit_notes=["Biological resources sourced entirely outside India."],
            )

        # Case 1: Foreign entity accessing Indian biological resource (Section 3)
        if is_foreign:
            statutory_provisions.append("Section 3, Biological Diversity Act 2002 & 2023 (Foreign Entity Access)")
            if data.activity_type in ["COMMERCIAL_UTILIZATION", "RESEARCH"]:
                return ABSAssessmentResponse(
                    approval_required=True,
                    approving_authority="National Biodiversity Authority (NBA)",
                    form_type="Form I",
                    benefit_sharing_levy="0.1% to 0.5% of annual gross ex-factory sales or mutually agreed terms.",
                    relevance_label="HIGH",
                    statutory_provisions=statutory_provisions,
                    next_steps=[
                        "File NBA Form I application on the NBA Access and Benefit Sharing portal.",
                        "Execute Benefit Sharing Agreement with NBA prior to commercial shipment or extraction.",
                        "Obtain Prior Informed Consent (PIC) where local community knowledge is accessed.",
                    ],
                    audit_notes=["Foreign entity / entity with foreign equity accessing Indian biological resources."],
                )

        # Case 2: IPR / Patent Application on Indian Biological Resource (Section 6)
        if data.activity_type == "IPR_APPLICATION":
            statutory_provisions.append("Section 6, Biological Diversity Act 2002 & 2023 (IPR Application Approval)")
            return ABSAssessmentResponse(
                approval_required=True,
                approving_authority="National Biodiversity Authority (NBA)",
                form_type="Form III",
                benefit_sharing_levy="Benefit sharing terms determined upon patent grant or commercial exploitation.",
                relevance_label="HIGH",
                statutory_provisions=statutory_provisions,
                next_steps=[
                    "Submit Form III application to NBA before the grant of the patent in India or abroad.",
                    "Disclose source and geographical origin of biological resource in Patent Specification (Section 10(4)(d)(ii) Patents Act).",
                ],
                audit_notes=["Patent filing based on research on biological resource originating in India."],
            )

        # Case 3: Transfer of Research Results to Non-Indian (Section 4)
        if data.activity_type == "TRANSFER_OF_RESULTS":
            statutory_provisions.append("Section 4, Biological Diversity Act (Transfer of Research Results)")
            return ABSAssessmentResponse(
                approval_required=True,
                approving_authority="National Biodiversity Authority (NBA)",
                form_type="Form II",
                benefit_sharing_levy="Assessed per collaborative agreement.",
                relevance_label="HIGH",
                statutory_provisions=statutory_provisions,
                next_steps=[
                    "File Form II with NBA prior to transferring research results or biological samples to foreign collaborators.",
                ],
                audit_notes=["Transfer of research results derived from Indian biological resources."],
            )

        # Case 4: Indian entity / Manufacturer accessing for Commercial Utilization (Section 7)
        if data.is_ayush_practitioner or (data.is_codified_traditional_knowledge and not is_foreign):
            statutory_provisions.append("Section 7 proviso, Biological Diversity (Amendment) Act 2023")
            return ABSAssessmentResponse(
                approval_required=False,
                approving_authority="State Biodiversity Board (SBB)",
                form_type="SBB Intimation / Exemption Notice",
                benefit_sharing_levy="Exempt from ABS fee under 2023 Amendment for registered AYUSH practitioners.",
                relevance_label="LOW",
                statutory_provisions=statutory_provisions,
                next_steps=[
                    "Submit formal intimation to the concerned State Biodiversity Board.",
                    "Retain practitioner registration certificate for verification.",
                ],
                audit_notes=["Registered AYUSH practitioner accessing codified traditional knowledge."],
            )

        # Standard Indian commercial manufacturer
        statutory_provisions.append("Section 7, Biological Diversity Act 2002 & 2023 (SBB Prior Intimation)")
        return ABSAssessmentResponse(
            approval_required=True,
            approving_authority="State Biodiversity Board (SBB)",
            form_type="SBB Prior Intimation Form",
            benefit_sharing_levy="0.1% to 0.5% ex-factory sales as prescribed under State ABS guidelines.",
            relevance_label="MEDIUM",
            statutory_provisions=statutory_provisions,
            next_steps=[
                "Submit prior intimation to the State Biodiversity Board of the state where raw material is procured.",
                "Maintain traceability register of raw herbal material procurement.",
            ],
            audit_notes=["Indian commercial enterprise accessing biological resources within India."],
        )
