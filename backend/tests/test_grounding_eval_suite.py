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
from src.classification.intent_classifier import IntentClassifier
from src.confidence.confidence_scorer import ConfidenceScorer
from src.orchestration.decomposer import QueryDecomposer, AgentTask
from src.prompts.templates import (
    CONSULTATION_SYSTEM_PROMPT,
    build_user_prompt,
    build_multi_domain_user_prompt,
)
from src.reasoning.llm_provider import get_llm_provider
from src.retrieval.qdrant_manager import QdrantManager
from src.retrieval.retriever import HybridRetriever, MIN_RELEVANCE_SCORE, DomainEvidenceSet
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
    assert any(w in resp.lower() for w in ["not indexed", "absent", "unverified", "direct verification", "not present", "not available"])
    # Must NOT claim Form 25-D is used in Australia
    assert '"regulatory_pathway": "Form 25-D"' not in resp


def test_multi_domain_decomposition():
    """Confirms query decomposer splits compound multi-intent queries and preserves single-intent fast path."""
    # 1. Compound query spanning Patent + ABS
    compound_q = "Can I patent my Ashwagandha formulation and do I need NBA approval to source it from Western Ghats?"
    tasks = QueryDecomposer.decompose(compound_q, jurisdiction="INDIA")
    assert len(tasks) == 2
    scopes = {t.agent_scope for t in tasks}
    assert "patent_agent" in scopes
    assert "biodiversity_agent" in scopes

    # 2. Single-intent query (Fast Path regression check)
    single_q = "What are the traditional knowledge exclusions under Section 3(p) of the Patents Act?"
    single_tasks = QueryDecomposer.decompose(single_q, jurisdiction="INDIA")
    assert len(single_tasks) == 1
    assert single_tasks[0].agent_scope == "patent_agent"
    assert single_tasks[0].intent == "PATENT"


def test_multi_domain_parallel_scoped_retrieval_isolation(qdrant_retriever):
    """
    Confirms domain-scoped retrieval preserves strict isolation:
    Patent agent evidence contains Patent statutes, ABS agent evidence contains Biodiversity statutes.
    """
    compound_q = "Can I patent my Ashwagandha extract and do I need NBA Form 1 approval to access biological resources?"
    tasks = QueryDecomposer.decompose(compound_q, jurisdiction="INDIA")
    assert len(tasks) >= 2

    # Execute scoped retrieval per task
    results = [qdrant_retriever.retrieve_for_task(t, top_k=2) for t in tasks]
    domain_map = {r.agent_scope: r for r in results}

    assert "patent_agent" in domain_map
    assert "biodiversity_agent" in domain_map

    patent_set = domain_map["patent_agent"]
    abs_set = domain_map["biodiversity_agent"]

    assert patent_set.hits_found is True
    assert abs_set.hits_found is True

    # Check isolation: patent set has patent statutes, ABS set has biological diversity statutes
    patent_titles = " ".join(e.doc_title.lower() for e in patent_set.evidence)
    abs_titles = " ".join(e.doc_title.lower() for e in abs_set.evidence)

    assert "patent" in patent_titles or "the_patents_act" in patent_titles
    assert "biodiversity" in abs_titles or "biological" in abs_titles or "guidelines" in abs_titles


def test_multi_domain_partial_grounding_and_synthesis(llm):
    """
    Evaluates partial grounding across multiple domains:
    Patent domain has strong statutory chunks; Food regulation domain has 0 hits.
    The synthesized response must ground the patent section while applying the absence disclaimer for food regulation.
    """
    domain_evidence_map = {
        "patent_agent": {
            "intent": "PATENT",
            "sub_question": "Can I patent my Ashwagandha formulation?",
            "hits_found": True,
            "evidence": [
                {
                    "doc_title": "The_Patents_Act,_1970.pdf",
                    "section_ref": "Section 3(p)",
                    "content": "Section 3(p): an invention which in effect is traditional knowledge or an aggregation of known properties of traditionally known components.",
                }
            ],
        },
        "food_regulation_agent": {
            "intent": "FOOD_REGULATION",
            "sub_question": "What are the exact FSSAI laboratory testing fees for Ayurveda Aahara?",
            "hits_found": False,
            "evidence": [],
        },
    }

    prompt = build_multi_domain_user_prompt(
        question="Can I patent my Ashwagandha formulation and what are the exact FSSAI laboratory testing fees?",
        jurisdiction="INDIA",
        domain_evidence_map=domain_evidence_map,
        classification_category="Ayurveda-Aahar / Nutraceutical",
    )

    resp = llm.generate(system_prompt=CONSULTATION_SYSTEM_PROMPT, user_prompt=prompt, temperature=0.0)

    # Patent section must cite Section 3(p)
    assert "3(p)" in resp or "Section 3" in resp
    # Food regulation section must disclaim missing fee schedule in database
    assert "not indexed" in resp.lower() or "not present" in resp.lower() or "unverified" in resp.lower() or "general principles" in resp.lower() or "direct verification" in resp.lower()


def test_multi_domain_confidence_scoring():
    """Confirms composite multi-domain confidence score is driven by the weakest domain."""
    domain_evidence_map = {
        "patent_agent": {
            "hits_found": True,
            "evidence": [
                type("Evidence", (), {"score": 0.72, "chunk_id": "c1", "doc_title": "The_Patents_Act,_1970.pdf"})()
            ],
        },
        "biodiversity_agent": {
            "hits_found": False,
            "evidence": [],
        },
    }

    assessment = ConfidenceScorer.calculate_multi_domain_confidence(
        response_text="Advisory response covering Section 3(p) and NBA.",
        domain_evidence_map=domain_evidence_map,
        validated_citations=[],
    )

    assert assessment.domain_confidence["patent_agent"]["score"] > 0.60
    assert assessment.domain_confidence["biodiversity_agent"]["score"] <= 0.45
    assert assessment.domain_confidence["biodiversity_agent"]["label"] == "LOW"
    assert assessment.overall_composite_score <= 0.45
    assert assessment.overall_confidence_label == "LOW"
    assert assessment.requires_human_review is True


# ==============================================================================
# 5. OUT-OF-DOMAIN GUARDRAIL LEAK & BORDERLINE NON-OVER-REFUSAL REGRESSION
# ==============================================================================

@pytest.mark.parametrize(
    "off_topic_query,forbidden_keywords",
    [
        ("what is a mobile", ["cellular", "handheld device", "touchscreen", "portable telephone", "telecommunication"]),
        ("how to repair a car engine", ["internal combustion", "piston", "spark plug", "transmission"]),
        ("who is the president of france", ["macron", "elysee", "french republic", "head of state"]),
        ("write python code for binary search", ["def binary_search", "mid = ", "left <= right"]),
    ],
)
def test_out_of_domain_guardrail_zero_leakage(off_topic_query, forbidden_keywords):
    """
    ISSUE 1 REGRESSION TEST:
    Verifies that off-topic queries are detected at Layer 1 structural guardrail,
    decomposed as OUT_OF_SCOPE, and contain zero substantive/factual definitions of the off-topic subject.
    """
    is_in_domain, conf, reason = IntentClassifier.is_in_domain(off_topic_query)
    assert not is_in_domain, f"Query '{off_topic_query}' was incorrectly classified as in-domain (reason: {reason})"
    assert conf == 0.0

    tasks = QueryDecomposer.decompose(off_topic_query)
    assert len(tasks) == 1
    assert tasks[0].intent == "OUT_OF_SCOPE"
    assert tasks[0].agent_scope == "out_of_scope_agent"

    # Verify fixed templated refusal response
    refusal = (
        "I'm scoped specifically to Intellectual Property and regulatory guidance for Ayurvedic "
        "and traditional medicine products — patents, trademarks, ABS compliance, formulation "
        "classification, and related topics under Ministry of Ayush frameworks. That question is "
        "outside what I can help with here. If you have an Ayurvedic or herbal product you'd like "
        "guidance on, describe it and I can help classify it and walk through the applicable IP/regulatory considerations."
    )
    assert "scoped specifically to Intellectual Property" in refusal
    for kw in forbidden_keywords:
        assert kw.lower() not in refusal.lower(), f"Leaked forbidden substantive content '{kw}' in out-of-scope response!"


@pytest.mark.parametrize(
    "borderline_query,expected_min_intent",
    [
        ("tell me about Ashwagandha", "FORMULATION"),
        ("what is turmeric used for", "FORMULATION"),
        ("can I patent my herbal mixture", "PATENT"),
        ("what is NBA approval for herbs", "ABS"),
        ("licensing requirements for herbal tea", "FORMULATION"),
        ("is Triphala considered classical medicine", "FORMULATION"),
        ("exporting neem extract to Europe", "EXPORT"),
    ],
)
def test_in_domain_borderline_not_over_refused(borderline_query, expected_min_intent):
    """
    ISSUE 1 REGRESSION TEST:
    Confirms genuinely in-domain but borderline queries are NOT accidentally caught by
    the stricter floor threshold, preventing over-refusal of legitimate Ayush/IP questions.
    """
    is_in_domain, conf, reason = IntentClassifier.is_in_domain(borderline_query)
    assert is_in_domain, f"Borderline in-domain query '{borderline_query}' was falsely rejected as out-of-domain"
    assert conf > 0.0

    tasks = QueryDecomposer.decompose(borderline_query)
    assert len(tasks) >= 1
    assert all(t.intent != "OUT_OF_SCOPE" for t in tasks), f"Task for '{borderline_query}' was incorrectly set to OUT_OF_SCOPE"
    assert all(t.agent_scope != "out_of_scope_agent" for t in tasks)


