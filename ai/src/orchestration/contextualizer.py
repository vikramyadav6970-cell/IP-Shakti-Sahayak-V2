"""
ai/src/orchestration/contextualizer.py

Conversational Query Contextualizer for IP-SAKTI Sahayak.
Resolves conversational follow-ups, affirmations ("yes", "proceed", "sure"),
anaphoric references ("can I patent it?"), and diagnostic clarification answers
into self-contained, domain-rich search and synthesis queries.
"""

from dataclasses import dataclass
import re
from typing import Any, Dict, List, Optional, Tuple


AFFIRMATIVE_PATTERNS = [
    r"^(?:yes|yep|yeah|sure|ok|okay|proceed|go\s*ahead|continue|please\s*do|yes\s*please|sure\s*thing|tell\s*me\s*more|elaborate|explain(?:\s*further|\s*more)?|let['’]?s\s*do\s*that|do\s*that|why(?:\s*not)?|how(?:\s*so)?)\.?$",
    r"^(?:yes|yeah|sure),\s*(?:please|go\s*ahead|proceed|tell\s*me|continue|elaborate).*",
    r"^tell\s*me\s*(?:about\s*)?(?:both|all|more|this|that|the\s*requirements?|the\s*details?)\.?$",
    r"^(?:both|all\s*of\s*them|all|option\s*[1-2]|the\s*first\s*one|the\s*second\s*one|first\s*one|second\s*one)\.?$",
]

ANAPHORIC_PRONOUNS = [
    r"\b(?:it|this|this\s*product|this\s*formulation|my\s*formulation|the\s*product|the\s*formulation|the\s*cream|the\s*syrup|the\s*oil|the\s*medicine)\b"
]


@dataclass
class ContextualizedQuery:
    """Result of conversational query contextualization."""
    raw_query: str
    resolved_query: str
    is_followup: bool
    is_diagnostic_intake: bool
    inferred_intent: Optional[str]
    context_source: Optional[str]  # e.g., "ASSISTANT_PROMPT_QUESTION", "PRODUCT_CONTEXT", "STANDALONE"


class QueryContextualizer:
    """Contextualizes user queries against dialogue history and active product context."""

    @staticmethod
    def is_affirmative_followup(query: str) -> bool:
        """Determines if the query is an affirmative continuation or instruction."""
        q = query.lower().strip()
        if not q:
            return False
        return any(re.search(pattern, q, re.IGNORECASE) for pattern in AFFIRMATIVE_PATTERNS)

    @staticmethod
    def extract_assistant_offer(last_assistant_content: str) -> Optional[str]:
        """
        Extracts offered follow-up topic(s) or questions from the previous assistant response.
        Example: "Would you like to explore the requirements for documenting 'non-obviousness' or the implications of using biological resources in your formulation?"
        """
        if not last_assistant_content:
            return None

        # Clean off any [[PRODUCT_CONTEXT:...]] tags first
        clean_text = re.sub(r"\[\[PRODUCT_CONTEXT:\s*(?:```json)?\s*\{[\s\S]*?\}\s*(?:```)?\s*\]\]", "", last_assistant_content).strip()

        # 1. Look for explicit invitation sentences at the end of the text
        invitation_patterns = [
            r"(?:would\s+you\s+like\s+to\s+(?:explore|discuss|examine|understand|learn\s+about)|feel\s+free\s+to\s+ask\s+about|shall\s+we\s+explore|we\s+can\s+also\s+examine)\s+([^?\n]+(?:\?|\n|$))",
            r"(?:what\s+would\s+you\s+like\s+to\s+explore\s+next\??\s*)(?:feel\s+free\s+to\s+ask\s+about:?\s*)?([\s\S]+?)(?:\Z|\n\n)",
            r"(?:explore\s+the\s+requirements\s+for\s+)([^?\n]+(?:\?|\n|$))",
            r"(?:next\s+steps?:\s*)([^?\n]+(?:\?|\n|$))",
        ]

        for pattern in invitation_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                # Clean punctuation and bullet characters without stripping internal hyphens
                extracted = re.sub(r"[\?\*\•\_\#]", "", extracted).strip()
                extracted = re.sub(r"^[\-\s\•]+", "", extracted).strip()
                if len(extracted) > 8:
                    return extracted

        # 2. Extract last question in the response
        sentences = [s.strip() for s in re.split(r"(?<=[.?!])\s+", clean_text) if s.strip()]
        for s in reversed(sentences):
            if s.endswith("?") and len(s) > 15:
                # Clean question
                clean_q = re.sub(r"[\*\_\#]", "", s).strip()
                # Strip leading conversational starter
                clean_q = re.sub(r"^(?:would\s+you\s+like\s+to\s+|shall\s+we\s+|can\s+we\s+|do\s+you\s+want\s+to\s+)", "", clean_q, flags=re.IGNORECASE)
                clean_q = clean_q.rstrip("?").strip()
                return clean_q

        return None

    @classmethod
    def contextualize(
        cls,
        query: str,
        history_messages: Optional[List[Dict[str, str]]] = None,
        product_context: Optional[Dict[str, Any]] = None,
        jurisdiction: str = "INDIA",
        classification_state: Optional[str] = None,
    ) -> ContextualizedQuery:
        """
        Contextualizes a user query given recent dialogue history and product context.
        """
        raw_clean = query.strip()
        q_lower = raw_clean.lower()
        p_ctx = product_context or {}

        prod_name = p_ctx.get("product_name") or p_ctx.get("category_name") or "product formulation"
        ingredients = p_ctx.get("ingredients")
        if isinstance(ingredients, list):
            ing_str = ", ".join(str(i) for i in ingredients[:4])
        elif ingredients:
            ing_str = str(ingredients)
        else:
            ing_str = ""

        prod_desc = f"{prod_name}" + (f" ({ing_str})" if ing_str else "")
        current_state = classification_state or p_ctx.get("state") or "CLASSIFIED"

        # Check for previous assistant message
        last_assistant_msg = None
        last_user_msg = None
        if history_messages:
            for msg in reversed(history_messages):
                role = msg.get("role")
                content = msg.get("content", "")
                if role == "assistant" and not last_assistant_msg and content:
                    last_assistant_msg = content
                elif role == "user" and not last_user_msg and content:
                    last_user_msg = content

        # CASE 1: Affirmative Follow-up (e.g., "yes", "proceed", "sure", "tell me more")
        if cls.is_affirmative_followup(raw_clean):
            if last_assistant_msg:
                offer = cls.extract_assistant_offer(last_assistant_msg)
                if offer:
                    resolved = f"{offer} for {prod_desc} in {jurisdiction}"
                    return ContextualizedQuery(
                        raw_query=raw_clean,
                        resolved_query=resolved,
                        is_followup=True,
                        is_diagnostic_intake=False,
                        inferred_intent=None,
                        context_source="ASSISTANT_PROMPT_QUESTION",
                    )

            # Fallback for affirmative without explicit extracted question: explore active product IP & regulatory path
            resolved = f"Statutory patentability assessment, ABS compliance, and regulatory pathway for {prod_desc} under {jurisdiction} law"
            return ContextualizedQuery(
                raw_query=raw_clean,
                resolved_query=resolved,
                is_followup=True,
                is_diagnostic_intake=False,
                inferred_intent=None,
                context_source="PRODUCT_CONTEXT",
            )

        # CASE 2: Short Selection / Topic Refinement (e.g., "non-obviousness", "biological resources", "the first one", "Section 3(p)")
        is_short_phrase = len(raw_clean.split()) <= 4
        if is_short_phrase and last_assistant_msg:
            # If user mentioned a specific legal keyword or option
            if any(k in q_lower for k in ["non-obvious", "obvious", "patent", "abs", "nba", "trademark", "license", "form 25", "first", "second", "both"]):
                resolved = f"{raw_clean} requirements and legal analysis for {prod_desc} in {jurisdiction}"
                return ContextualizedQuery(
                    raw_query=raw_clean,
                    resolved_query=resolved,
                    is_followup=True,
                    is_diagnostic_intake=False,
                    inferred_intent=None,
                    context_source="ASSISTANT_PROMPT_QUESTION",
                )

        # CASE 3: Pure Diagnostic Intake Response
        # If in intake phase and user is providing product attributes (e.g., "topical cream", "intended for eczema", "twice daily")
        is_answering_intake = (
            current_state == "COLLECTING_PRODUCT_INFORMATION"
            and not any(k in q_lower for k in ["patent", "section 3", "abs", "nba", "trademark", "sbb", "wipo", "infringement"])
            and len(raw_clean.split()) <= 20
        )
        if is_answering_intake:
            return ContextualizedQuery(
                raw_query=raw_clean,
                resolved_query=f"Product classification intake response: {raw_clean}",
                is_followup=True,
                is_diagnostic_intake=True,
                inferred_intent="FORMULATION",
                context_source="DIAGNOSTIC_INTAKE",
            )

        # CASE 4: Anaphoric Pronoun Replacement (e.g., "Can I patent it?", "What license is needed for this?")
        has_anaphora = any(re.search(p, q_lower) for p in ANAPHORIC_PRONOUNS)
        if has_anaphora and prod_desc:
            resolved = raw_clean
            for p in ANAPHORIC_PRONOUNS:
                resolved = re.sub(p, f"the {prod_desc}", resolved, flags=re.IGNORECASE)
            return ContextualizedQuery(
                raw_query=raw_clean,
                resolved_query=resolved,
                is_followup=True,
                is_diagnostic_intake=False,
                inferred_intent=None,
                context_source="PRODUCT_CONTEXT",
            )

        # CASE 5: Standalone Query
        return ContextualizedQuery(
            raw_query=raw_clean,
            resolved_query=raw_clean,
            is_followup=False,
            is_diagnostic_intake=False,
            inferred_intent=None,
            context_source="STANDALONE",
        )
