"""
backend/app/services/chat_summary_service.py

Service for generating structured LLM executive summaries and publication-ready
PDF consultation dossiers for any chat session.
"""

from datetime import datetime, timezone
import json
import logging
import re
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.entities import Citation, Conversation, Message, RoleEnum, User
from app.services.report_generator import consultation_pdf_generator
from src.reasoning.llm_provider import GeminiProvider, get_llm_provider

logger = logging.getLogger("ipsakti.services.chat_summary")

SUMMARY_SYSTEM_PROMPT = """You are an expert legal and regulatory analyst for the Ministry of Ayush and IP-SAKTI Sahayak.
Your task is to analyze the provided multi-turn consultation between an Ayurvedic innovator and the AI assistant, and synthesize an authoritative, publication-ready executive summary.

You MUST return a VALID JSON object with this EXACT structure (do not include markdown code block quotes, only raw valid JSON):
{
  "executive_summary": "High-level 2-3 sentence overview of the consultation, product nature, and primary legal takeaways.",
  "product_classification": {
    "category": "Classical / Generic Medicine | Patent-or-Proprietary Medicine | New or Non-Classical Drug | Phytopharmaceutical | Ayurveda-Aahar / Nutraceutical | Cosmetic",
    "classification_reason": "Specific statutory reasoning under Section 3(h), Rule 158B, or First Schedule authoritative texts.",
    "dosage_form": "e.g. Syrup, Tablet, Oil, Extract",
    "ingredients": ["Ingredient 1", "Ingredient 2"],
    "therapeutic_claims": "e.g. Stress relief, enhanced bioavailability, cognitive support"
  },
  "patentability_assessment": {
    "section_3p_status": "Evaluation under Section 3(p) (Traditional Knowledge exclusion / AFI status).",
    "section_3e_status": "Evaluation under Section 3(e) (Synergy / enhancement of therapeutic efficacy / Novartis standard).",
    "overall_eligibility": "EXCLUDED | CONDITIONAL | HIGH"
  },
  "abs_compliance": {
    "summary": "Biological Diversity Act compliance summary regarding bio-resource utilization in India.",
    "sbb_nba_requirements": "State Biodiversity Board prior intimation (Form I) or NBA Section 3/6 approvals required."
  },
  "regulatory_pathway": {
    "licensing_authority": "State Licensing Authority (AYUSH) / CDSCO / FSSAI",
    "license_form": "Form 25-D under Drugs and Cosmetics Rules, 1945 (or applicable framework)",
    "compliance_steps": "Key compliance and standardization requirements."
  },
  "citations": [
    {
      "source": "Document or Registry Name (e.g. Drugs and Cosmetics Act, 1940 / WIPO PATENTSCOPE / NCBI PubMed)",
      "section": "Section or Article Reference (e.g. Section 3(h) / PMID:34090907)",
      "title": "Brief description of the cited provision or research publication"
    }
  ],
  "actionable_next_steps": [
    "Step 1 for the innovator",
    "Step 2 for the innovator",
    "Step 3 for the innovator"
  ]
}

Ground all analysis strictly in the facts and dialogue provided. If any field was not discussed, provide a legally accurate inferred baseline under Indian/International Ayush regulations.
"""


class ChatSummaryService:
    """Orchestrates LLM conversation summarization and PDF compilation."""

    def __init__(self, db: AsyncSession):
        self.db = db
        active_provider = settings.LLM_PROVIDER or os.environ.get("LLM_PROVIDER", "gemini")
        active_model = settings.LLM_MODEL or os.environ.get("LLM_MODEL")
        if active_provider == "openai":
            active_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
        elif active_provider in ["anthropic", "claude"]:
            active_key = settings.ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY")
        else:
            active_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")

        self.llm = get_llm_provider(
            provider_name=active_provider,
            model_name=active_model,
            api_key=active_key,
        )

    async def _get_conversation_with_messages(
        self, conversation_id: uuid.UUID, current_user: Optional[User] = None
    ) -> Optional[Conversation]:
        """Fetch conversation, messages, and citations."""
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(
                selectinload(Conversation.messages).selectinload(Message.citations)
            )
        )
        if current_user and getattr(current_user, "role", None) != RoleEnum.ADMIN:
            stmt = stmt.where(Conversation.user_id == current_user.id)

        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    def _build_dialogue_transcript(self, conversation: Conversation) -> str:
        """Formats the conversation turns and citations into a text transcript for the LLM."""
        lines = [
            f"=== CONSULTATION SESSION: {conversation.title or 'Ayurvedic Innovation Consultation'} ===",
            f"Active Intent: {conversation.active_intent.value if conversation.active_intent else 'FORMULATION'}",
            f"Classification State: {conversation.classification_state or 'CLASSIFIED'}",
        ]
        if conversation.product_context_json:
            lines.append(f"Recorded Product Context: {json.dumps(conversation.product_context_json)}")

        lines.append("\n=== DIALOGUE TRANSCRIPT ===")
        for msg in conversation.messages:
            role_label = "INNOVATOR (User)" if msg.role == "user" else "AI SAHAYAK (Assistant)"
            lines.append(f"\n[{role_label} - Jurisdiction: {msg.jurisdiction or 'INDIA'}]:\n{msg.content}")

            if msg.citations:
                lines.append("Cited Authorities / Evidence:")
                for c in msg.citations:
                    lines.append(f"  - {c.document_title} | {c.section_ref} ({c.source_url})")

        return "\n".join(lines)

    def _clean_json_response(self, raw_text: str) -> Dict[str, Any]:
        """Strips markdown code blocks and parses raw JSON."""
        clean = raw_text.strip()
        # Remove ```json ... ``` wrappers if present
        if clean.startswith("```"):
            clean = re.sub(r"^```(?:json)?\s*", "", clean, flags=re.IGNORECASE)
            clean = re.sub(r"\s*```$", "", clean)

        # Remove any leading/trailing non-json characters
        match = re.search(r"\{[\s\S]*\}", clean)
        if match:
            clean = match.group(0)

        return json.loads(clean)

    def _build_fallback_summary(self, conversation: Conversation) -> Dict[str, Any]:
        """Constructs a structured fallback summary if LLM response cannot be parsed."""
        p_ctx = conversation.product_context_json or {}
        cat_name = p_ctx.get("category") or "Patent-or-Proprietary Medicine"
        cat_reason = p_ctx.get("classification_reason") or "Ayurvedic product evaluated under ASU statutory rules."
        ingredients = p_ctx.get("ingredients") or ["Ayurvedic Botanical Ingredients"]
        dosage = p_ctx.get("dosage_form") or "Formulation"

        # Collect existing citations from conversation messages
        extracted_citations = []
        for m in conversation.messages:
            for c in m.citations:
                extracted_citations.append({
                    "source": c.document_title,
                    "section": c.section_ref,
                    "title": f"Statutory evidence indexed for {c.jurisdiction}",
                })

        return {
            "executive_summary": (
                f"Consultation session on {conversation.title or 'Ayurvedic innovation'}. "
                f"The product was evaluated and categorized under {cat_name} with statutory compliance pathways."
            ),
            "product_classification": {
                "category": cat_name,
                "classification_reason": cat_reason,
                "dosage_form": dosage,
                "ingredients": ingredients,
                "therapeutic_claims": p_ctx.get("therapeutic_claims") or "Therapeutic wellness and health enhancement",
            },
            "patentability_assessment": {
                "section_3p_status": "Subject to Section 3(p) Traditional Knowledge exclusion unless novelty/synergy established.",
                "section_3e_status": "Requires comparative synergism data under Section 3(e) for proprietary combinations.",
                "overall_eligibility": p_ctx.get("patent_eligibility") or "CONDITIONAL",
            },
            "abs_compliance": {
                "summary": "Commercial utilization of biological resources sourced from India requires compliance with Biological Diversity Act.",
                "sbb_nba_requirements": "Prior intimation to State Biodiversity Board (Form I) required before commercial exploitation.",
            },
            "regulatory_pathway": {
                "licensing_authority": "State Licensing Authority (AYUSH)",
                "license_form": "Form 25-D under Drugs and Cosmetics Rules, 1945",
                "compliance_steps": "Standardization, safety proof, and manufacturing compliance under Schedule T (GMP).",
            },
            "citations": extracted_citations or [
                {"source": "Drugs and Cosmetics Act, 1940", "section": "Section 3(h)", "title": "Patent or Proprietary Medicine definition"},
                {"source": "Patents Act, 1970", "section": "Section 3(p) & 3(e)", "title": "Traditional Knowledge & Synergistic combination exclusions"},
            ],
            "actionable_next_steps": [
                "Document technical formulation ratios and establish synergistic efficacy data under Section 3(e).",
                "Submit prior intimation to State Biodiversity Board (Form I) prior to commercial manufacture.",
                "Apply for Form 25-D manufacturing license through the State Licensing Authority (AYUSH).",
            ],
        }

    async def generate_summary(
        self, conversation_id: uuid.UUID, current_user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Executes LLM summarization over the conversation transcript and returns structured JSON summary.
        """
        conversation = await self._get_conversation_with_messages(conversation_id, current_user)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found or access denied.")

        if not conversation.messages:
            return self._build_fallback_summary(conversation)

        transcript = self._build_dialogue_transcript(conversation)
        user_prompt = f"Analyze the following conversation and generate the comprehensive JSON consultation summary:\n\n{transcript}"

        try:
            raw_response = await self.llm.generate_async(
                system_prompt=SUMMARY_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.1,
                max_tokens=2500,
            )
            summary_dict = self._clean_json_response(raw_response)

            # Ensure all required top-level keys exist
            for required_key in [
                "executive_summary",
                "product_classification",
                "patentability_assessment",
                "abs_compliance",
                "regulatory_pathway",
                "citations",
                "actionable_next_steps",
            ]:
                if required_key not in summary_dict:
                    logger.warning(f"Key '{required_key}' missing from LLM summary. Merging fallback.")
                    fallback = self._build_fallback_summary(conversation)
                    summary_dict[required_key] = fallback[required_key]

            # Merge any citations present in the DB that may have been missed
            db_cites = []
            for m in conversation.messages:
                for c in m.citations:
                    db_cites.append({
                        "source": c.document_title,
                        "section": c.section_ref,
                        "title": c.source_url or "Statutory reference",
                    })
            if db_cites and not summary_dict.get("citations"):
                summary_dict["citations"] = db_cites

            return summary_dict

        except Exception as exc:
            logger.warning(f"LLM summarization failed for {conversation_id}: {exc}. Using fallback.")
            return self._build_fallback_summary(conversation)

    async def generate_pdf_report(
        self, conversation_id: uuid.UUID, current_user: Optional[User] = None
    ) -> bytes:
        """
        Generates and returns PDF report binary bytes for the specified conversation.
        """
        conversation = await self._get_conversation_with_messages(conversation_id, current_user)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found or access denied.")

        summary_data = await self.generate_summary(conversation_id, current_user)
        conv_title = conversation.title or "Ayurvedic Innovation Consultation"
        
        # Determine jurisdiction from messages
        jurisdiction = "INDIA"
        for m in reversed(conversation.messages):
            if m.jurisdiction:
                jurisdiction = m.jurisdiction
                break

        pdf_bytes = consultation_pdf_generator.generate_report(
            summary_data=summary_data,
            conversation_title=conv_title,
            jurisdiction=jurisdiction,
            conversation_id=str(conversation_id),
        )
        return pdf_bytes
