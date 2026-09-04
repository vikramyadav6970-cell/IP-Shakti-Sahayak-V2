"""
ai/src/orchestration/decomposer.py

Multi-Agent Query Decomposer for IP-SAKTI Sahayak.
Decomposes compound user inquiries into domain-scoped AgentTasks for parallel retrieval and synthesis.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import re

from src.classification.intent_classifier import IntentClassifier


# Canonical mapping from statutory intent to multi-agent scope
INTENT_TO_AGENT_SCOPE: Dict[str, str] = {
    "PATENT": "patent_agent",
    "ABS": "biodiversity_agent",
    "FOOD_REGULATION": "food_regulation_agent",
    "TRADEMARK": "trademark_agent",
    "FORMULATION": "formulation_agent",
    "EXPORT": "international_agent",
    "CASE_LAW": "patent_agent",
    "RESEARCH": "patent_agent",
    "OUT_OF_SCOPE": "out_of_scope_agent",
}


@dataclass
class AgentTask:
    """Domain-specific sub-task dispatched to a specialized legal/regulatory retrieval agent."""
    agent_scope: str        # e.g. "patent_agent", "biodiversity_agent", "out_of_scope_agent"
    intent: str             # e.g. "PATENT", "ABS", "OUT_OF_SCOPE"
    sub_question: str       # Domain-specific slice or full inquiry
    jurisdiction: str       # "INDIA" | "INTERNATIONAL"
    confidence: float       # Intent match confidence (0.0 to 1.0)


class QueryDecomposer:
    """Decomposes compound user queries into structured domain-scoped AgentTasks."""

    @staticmethod
    def decompose(
        query: str,
        jurisdiction: str = "INDIA",
        explicit_intent: Optional[str] = None,
        confidence_threshold: float = 0.15,
        product_context: Optional[Dict] = None,
        has_prior_dialogue: bool = False,
    ) -> List[AgentTask]:
        """
        Decomposes query into one or more AgentTasks.
        For single-domain inquiries, returns a single-element list for zero-overhead fast-path retrieval.
        """
        # 1. Multi-intent classification check
        scored_intents: List[Tuple[str, float]] = IntentClassifier.classify_multi(query)
        qualifying = [(intent, score) for intent, score in scored_intents if score >= confidence_threshold and intent != "OUT_OF_SCOPE"]

        # If user explicitly pinned an intent AND query does not contain multiple qualifying intents, respect it
        if explicit_intent and explicit_intent != "OUT_OF_SCOPE" and len(qualifying) <= 1:
            scope = INTENT_TO_AGENT_SCOPE.get(explicit_intent, "patent_agent")
            return [
                AgentTask(
                    agent_scope=scope,
                    intent=explicit_intent,
                    sub_question=query,
                    jurisdiction=jurisdiction,
                    confidence=1.0,
                )
            ]

        # If no qualifying in-domain patterns matched
        if not qualifying:
            in_domain, conf, _ = IntentClassifier.is_in_domain(
                query,
                product_context=product_context,
                has_prior_dialogue=has_prior_dialogue,
            )
            if in_domain:
                primary_intent = explicit_intent or "FORMULATION"
                scope = INTENT_TO_AGENT_SCOPE.get(primary_intent, "formulation_agent")
                return [
                    AgentTask(
                        agent_scope=scope,
                        intent=primary_intent,
                        sub_question=query,
                        jurisdiction=jurisdiction,
                        confidence=conf or 0.5,
                    )
                ]

            return [
                AgentTask(
                    agent_scope="out_of_scope_agent",
                    intent="OUT_OF_SCOPE",
                    sub_question=query,
                    jurisdiction=jurisdiction,
                    confidence=0.0,
                )
            ]

        # 3. Single-domain query (Fast Path: no decomposition overhead)
        if len(qualifying) == 1:
            intent, score = qualifying[0]
            scope = INTENT_TO_AGENT_SCOPE.get(intent, "patent_agent")
            return [
                AgentTask(
                    agent_scope=scope,
                    intent=intent,
                    sub_question=query,
                    jurisdiction=jurisdiction,
                    confidence=score,
                )
            ]

        # 4. Multi-domain query: decompose into separate agent tasks
        # Check if query contains conjunctive split markers ('and', 'also', 'as well as', '?', ';', ',')
        sub_splits = re.split(r"(?:\band\b|\balso\b|\bas well as\b|\?|;)\s*", query, flags=re.IGNORECASE)
        tasks: List[AgentTask] = []
        used_scopes = set()

        for intent, score in qualifying:
            scope = INTENT_TO_AGENT_SCOPE.get(intent, "patent_agent")
            if scope in used_scopes:
                continue
            used_scopes.add(scope)

            # Determine best sub-question slice
            best_sub = query
            if len(sub_splits) > 1:
                for split in sub_splits:
                    split_clean = split.strip()
                    if split_clean and len(split_clean) > 8 and IntentClassifier.matches_intent(split_clean, intent):
                        best_sub = split_clean
                        break

            tasks.append(
                AgentTask(
                    agent_scope=scope,
                    intent=intent,
                    sub_question=best_sub,
                    jurisdiction=jurisdiction,
                    confidence=score,
                )
            )

        return tasks
