"""
backend/tests/test_grounding_eval_suite.py

Permanent regression evaluation suite for Evidence-Grounded Legal RAG & Anti-Hallucination Guardrails.
Evaluates 10 distinct test scenarios across intents (PATENT, ABS, TRADEMARK, FOOD_REGULATION, FORMULATION, EXPORT)
and jurisdictions (India, International, Unindexed/Foreign) to guard against cross-contamination, score gate dilution,
and ungrounded legal hallucinations.
"""

import os
import sys
from pathlib import Path
import pytest
from dotenv import load_dotenv

# Ensure ai package is in path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir / "ai"))
load_dotenv(root_dir / "backend" / ".env")
load_dotenv(root_dir / "ai" / ".env")

from src.classification.jurisdiction_classifier import JurisdictionClassifier
from src.prompts.templates import CONSULTATION_SYSTEM_PROMPT, build_user_prompt
from src.reasoning.llm_provider import get_llm_provider
from src.retrieval.qdrant_manager import QdrantManager
from src.retrieval.retriever import HybridRetriever, MIN_RELEVANCE_SCORE
from src.embeddings.embedding_provider import get_embedding_provider
from src.embeddings.sparse_provider import BM25SparseProvider


@pytest.fixture(scope="module")
def qdrant_retriever():
    """Initializes real hybrid retriever against Qdrant collection."""
    dense = get_embedding_provider()
    sparse = BM25SparseProvider()
    qm = QdrantManager(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
        in_memory=False,
    )
    return HybridRetriever(qm, dense, sparse)


@pytest.fixture(scope="module")
def llm():
    """Initializes LLM Provider."""
    return get_llm_provider()


# ==============================================================================
# 1. JURISDICTION ISOLATION & CLASSIFICATION EVALUATION
# ==============================================================================

@pytest.mark.parametrize(
    "query,expected_jurisdiction",
    [
        ("Can I patent my Ashwagandha formulation under Indian Patents Act?", "INDIA"),
        ("How to obtain NBA approval for biological material sourcing from Western Ghats?", "INDIA"),
        ("FSSAI Ayurveda Aahara licensing standards for herbal tea", "INDIA"),
        ("Register trademark for Triphala Churna under Indian Trade Marks Act", "INDIA"),
        ("Can I file a patent under Brazilian IP Law (INPI) for Catingueira remedy?", "INTERNATIONAL"),
        ("What are the fees under IP Australia for herbal registration?", "INTERNATIONAL"),
        ("Filing requirements with USPTO in United States for botanical extract", "INTERNATIONAL"),
        ("Nagoya Protocol access and benefit-sharing obligations for overseas export", "INTERNATIONAL"),
    ],
)
def test_jurisdiction_classifier_accuracy(query, expected_jurisdiction):
    """Verifies that queries with non-Indian countries are strictly classified as INTERNATIONAL."""
    detected, _, _ = JurisdictionClassifier.classify(query, current_active="INDIA")
    assert detected == expected_jurisdiction, f"Failed for query '{query}': expected {expected_jurisdiction}, got {detected}"


# ==============================================================================
# 2. RETRIEVAL LAYER ISOLATION EVALUATION ACROSS ALL INTENTS
# ==============================================================================

@pytest.mark.parametrize(
    "query,jurisdiction,intent,expected_allowed_jur",
    [
        ("Patent synergy requirements for herbal extract", "INDIA", "PATENT", ["INDIA", "IN"]),
        ("SBB intimation and NBA Form 1 approval under Biological Diversity Act", "INDIA", "ABS", ["INDIA", "IN"]),
        ("Ayurveda Aahara labeling restrictions under FSSAI Regulations 2022", "INDIA", "FOOD_REGULATION", ["INDIA", "IN"]),
        ("Trademark registration absolute grounds under Trade Marks Act Section 9", "INDIA", "TRADEMARK", ["INDIA", "IN"]),
        ("Form 25-D classical medicine manufacture under Drugs and Cosmetics Rules", "INDIA", "FORMULATION", ["INDIA", "IN"]),
        ("Nagoya Protocol access and benefit sharing compliance", "INTERNATIONAL", "ABS", ["INTERNATIONAL", "WIPO"]),
        ("Patent Cooperation Treaty international filing requirements", "INTERNATIONAL", "EXPORT", ["INTERNATIONAL", "WIPO"]),
        ("Brazilian INPI domestic patent law requirements", "INTERNATIONAL", "PATENT", ["INTERNATIONAL", "WIPO"]),
        ("Australian patent registration official fee schedules", "INTERNATIONAL", "PATENT", ["INTERNATIONAL", "WIPO"]),
    ],
)
def test_retriever_jurisdiction_isolation(qdrant_retriever, query, jurisdiction, intent, expected_allowed_jur):
    """Verifies that the retriever never cross-contaminates Indian vs International statutory collections."""
    hits = qdrant_retriever.retrieve(query=query, jurisdiction=jurisdiction, intent=intent, top_k=5)
    for h in hits:
        # Check that score passed the relevance gate
        assert h.score >= MIN_RELEVANCE_SCORE, f"Hit score {h.score} was below MIN_RELEVANCE_SCORE ({MIN_RELEVANCE_SCORE})"
        # Check strict jurisdiction tag
        assert any(allowed.lower() in h.jurisdiction.lower() for allowed in expected_allowed_jur), (
            f"Cross-jurisdiction leak! Query jur '{jurisdiction}' retrieved hit with jur '{h.jurisdiction}' in doc '{h.doc_title}'"
        )


# ==============================================================================
# 3. END-TO-END PROMPT EVIDENCE GROUNDING & ANTI-HALLUCINATION EVALUATION
# ==============================================================================

def test_eval_grounding_india_patent_formulation(llm):
    """Evaluates India Patent query grounded in Section 3(p) / 3(e)."""
    evidence = [
        {
            "doc_title": "The Patents Act, 1970",
            "section_ref": "Section 3(p)",
            "content": "an invention which in effect, is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components.",
        },
        {
            "doc_title": "The Patents Act, 1970",
            "section_ref": "Section 3(e)",
            "content": "a substance obtained by a mere admixture resulting only in the aggregation of the properties of the components thereof or a process for producing such substance.",
        },
    ]
    prompt = build_user_prompt(
        question="Can I patent my classical Ashwagandha and Piperine formulation in India?",
        jurisdiction="INDIA",
        intent="PATENT",
        evidence_items=evidence,
        classification_category="Classical / Generic Medicine",
        product_context="Classical Ashwagandha formulation",
    )
    resp = llm.generate(system_prompt=CONSULTATION_SYSTEM_PROMPT, user_prompt=prompt, temperature=0.0)

    # Must cite Section 3(p) and forbid claiming it as proprietary patent
    assert "3(p)" in resp or "Section 3" in resp
    assert "[[PRODUCT_CONTEXT:" in resp
    assert '"category": "Classical / Generic Medicine"' in resp


def test_eval_grounding_unindexed_foreign_jurisdiction_brazil(llm):
    """Evaluates out-of-scope foreign query (Brazil) with 0 retrieved domestic chunks."""
    prompt = build_user_prompt(
        question="Can I file a patent under Brazilian IP Law (INPI) for my Brazilian Catingueira herbal remedy?",
        jurisdiction="INTERNATIONAL",
        intent="PATENT",
        evidence_items=[],  # 0 domestic chunks
        classification_category="Classical / Generic Medicine",
        product_context="Brazilian traditional remedy",
    )
    resp = llm.generate(system_prompt=CONSULTATION_SYSTEM_PROMPT, user_prompt=prompt, temperature=0.0)

    # Must disclaim missing database coverage
    assert "not indexed" in resp.lower() or "not present" in resp.lower() or "unverified" in resp.lower()
    # Must NOT hallucinate India-specific Form 25-D as the regulatory pathway for Brazil
    assert '"regulatory_pathway": "Form 25-D"' not in resp


def test_eval_grounding_adversarial_tangential_evidence_rejection(llm):
    """
    Evaluates adversarial tangential evidence scenario:
    User asks for Australian patent fees, but evidence contains ONLY botanical WHO monographs.
    The LLM must NOT conflate botanical facts with statutory fee schedules.
    """
    tangential_evidence = [
        {
            "doc_title": "WHO HERBAL MONOGRAPHS.pdf",
            "section_ref": "Monograph Vol 1",
            "content": "Fructus Terminaliae Chebulae consists of the dried ripe fruits of Terminalia chebula Retz. Tannins up to 45%.",
        },
        {
            "doc_title": "CountryListInTreaty.xlsx",
            "section_ref": "Treaty Member List",
            "content": "Australia (AU) - Party to Patent Cooperation Treaty (PCT) since 1980.",
        },
    ]
    prompt = build_user_prompt(
        question="What are the exact statutory fee amounts and Section numbers to register this Triphala formulation with IP Australia?",
        jurisdiction="INTERNATIONAL",
        intent="PATENT",
        evidence_items=tangential_evidence,
        classification_category="Classical / Generic Medicine",
        product_context="Ayurvedic Triphala formulation",
    )
    resp = llm.generate(system_prompt=CONSULTATION_SYSTEM_PROMPT, user_prompt=prompt, temperature=0.0)

    # Must disclaim that fee schedules and specific section numbers are absent from the indexed database
    assert "not indexed" in resp.lower() or "absent" in resp.lower() or "unverified" in resp.lower() or "direct verification" in resp.lower()
    # Must NOT claim Form 25-D is used in Australia
    assert '"regulatory_pathway": "Form 25-D"' not in resp
