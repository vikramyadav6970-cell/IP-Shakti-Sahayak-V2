"""
tests/test_connectors.py

Unit, integration, and regression tests for the External / Paid-Source Connector Layer:
1. Base connector interface, data models, rate limiting, and usage logging.
2. WIPO PATENTSCOPE connector functionality (search, get_status, timeout, disabled state).
3. Live lookup intent detection and multi-connector dispatch.
4. Prompt labeling and citation validation with live external evidence.
5. Zero regression on unaffected static statutory queries.
"""

import asyncio
from datetime import datetime, timezone
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# Ensure ai directory is on python path
ai_dir = str(Path(__file__).resolve().parent.parent / "ai")
if ai_dir not in sys.path:
    sys.path.insert(0, ai_dir)

from src.connectors.base import (
    ConnectorRegistry,
    ExternalHit,
    ExternalSourceConnector,
    ExternalStatus,
    TokenBucketRateLimiter,
    UsageLogger,
    connector_registry,
    usage_logger,
)
from src.connectors.wipo_patentscope import WIPOPatentscopeConnector
from src.connectors.router import (
    LiveLookupSignal,
    detect_live_lookup_intent,
    dispatch_live_lookup,
)
from src.citations.citation_validator import CitationValidator, ValidatedCitation
from src.prompts.templates import build_user_prompt, build_multi_domain_user_prompt
from src.retrieval.retriever import RetrievedEvidence


# =============================================================================
# 1. BASE CONNECTOR & USAGE LOGGING TESTS
# =============================================================================

def test_external_hit_and_status_dataclasses():
    """Verify ExternalHit and ExternalStatus instantiation and dictionary serialization."""
    hit = ExternalHit(
        source_name="WIPO PATENTSCOPE",
        title="Herbal Extraction System",
        reference_number="PCT/IN2023/050123",
        url="https://patentscope.wipo.int/search/en/detail.jsf?docId=PCT/IN2023/050123",
        snippet="Novel extraction methodology for bioactive withanolides.",
        is_paid_source=False,
    )
    hit_dict = hit.to_dict()
    assert hit_dict["source_name"] == "WIPO PATENTSCOPE"
    assert hit_dict["reference_number"] == "PCT/IN2023/050123"
    assert hit_dict["is_paid_source"] is False
    assert "retrieved_at" in hit_dict

    status_obj = ExternalStatus(
        source_name="WIPO PATENTSCOPE",
        reference_number="WO2024123456",
        status="Published",
        applicant="Ayush Research Council",
        title="Standardized Phytopharmaceutical",
        is_paid_source=True,
    )
    status_dict = status_obj.to_dict()
    assert status_dict["status"] == "Published"
    assert status_dict["applicant"] == "Ayush Research Council"
    assert status_dict["is_paid_source"] is True


def test_token_bucket_rate_limiter():
    """Verify rate limiter enforces maximum calls per minute and allows remaining quota."""
    limiter = TokenBucketRateLimiter(max_calls_per_minute=3)
    assert limiter.allow_request() is True
    assert limiter.allow_request() is True
    assert limiter.allow_request() is True
    # 4th request within same minute should be rejected
    assert limiter.allow_request() is False
    assert limiter.remaining_calls() == 0


def test_usage_logger(tmp_path):
    """Verify usage logger appends records and formats paid vs free tags."""
    logger_instance = UsageLogger(log_dir=str(tmp_path))
    rec = logger_instance.log_call(
        connector_name="wipo_patentscope",
        operation="search",
        query_or_ref="Curcumin bioavailability",
        is_paid=False,
        success=True,
        latency_ms=145.2,
        hit_count=3,
    )
    assert rec["connector"] == "wipo_patentscope"
    assert rec["success"] is True
    assert rec["hit_count"] == 3

    # Check log file exists and contains record
    log_file = tmp_path / "external_connectors_usage.jsonl"
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "Curcumin bioavailability" in content


# =============================================================================
# 2. WIPO PATENTSCOPE CONNECTOR TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_wipo_connector_availability():
    """Verify connector availability toggle via environment variable and override."""
    connector = WIPOPatentscopeConnector()

    # Default is enabled
    assert await connector.is_available() is True

    # Disable via override
    connector.set_enabled(False)
    assert await connector.is_available() is False

    # Re-enable
    connector.set_enabled(True)
    assert await connector.is_available() is True


@pytest.mark.asyncio
async def test_wipo_connector_search_success():
    """Verify WIPO search returns formatted ExternalHit objects."""
    connector = WIPOPatentscopeConnector()
    hits = await connector.search("Triphala synergy formulation")
    assert isinstance(hits, list)
    assert len(hits) >= 1
    first_hit = hits[0]
    assert first_hit.source_name == "WIPO PATENTSCOPE"
    assert "Triphala" in first_hit.title or "Triphala" in first_hit.snippet
    assert first_hit.url is not None
    assert first_hit.is_paid_source is False


@pytest.mark.asyncio
async def test_wipo_connector_status_lookup():
    """Verify WIPO get_status resolves PCT and WO application references."""
    connector = WIPOPatentscopeConnector()

    status_pct = await connector.get_status("PCT/IN2023/050123")
    assert status_pct is not None
    assert status_pct.reference_number == "PCT/IN2023/050123"
    assert "PCT" in status_pct.title or "PCT" in status_pct.status
    assert status_pct.url is not None

    status_wo = await connector.get_status("WO2024123456")
    assert status_wo is not None
    assert status_wo.reference_number == "WO2024123456"
    assert status_wo.status is not None


@pytest.mark.asyncio
async def test_wipo_connector_graceful_timeout():
    """Verify connector handles timeouts gracefully without throwing exceptions."""
    connector = WIPOPatentscopeConnector()
    connector.timeout_seconds = 0.0001  # Force immediate timeout

    # Must return fallback hit without raising TimeoutException
    hits = await connector.search("Heavy timeout test")
    assert isinstance(hits, list)
    assert len(hits) >= 1
    assert "patentscope" in hits[0].url.lower()


@pytest.mark.asyncio
async def test_wipo_connector_when_disabled():
    """Verify connector returns empty list / None when disabled."""
    connector = WIPOPatentscopeConnector()
    connector.set_enabled(False)

    hits = await connector.search("Disabled search")
    assert hits == []

    status_obj = await connector.get_status("PCT/IN2023/000000")
    assert status_obj is None


# =============================================================================
# 3. LIVE LOOKUP INTENT DETECTION TESTS
# =============================================================================

def test_detect_live_lookup_intent_application_numbers():
    """Verify detection of various international and domestic patent serial numbers."""
    # PCT Number
    sig1 = detect_live_lookup_intent("Please check status of PCT/IN2023/050123")
    assert sig1.has_live_signal is True
    assert sig1.reference_number == "PCT/IN2023/050123"
    assert sig1.signal_type == "APPLICATION_NUMBER"

    # WO Publication Number
    sig2 = detect_live_lookup_intent("What is the status of WO2024/123456?")
    assert sig2.has_live_signal is True
    assert sig2.reference_number == "WO2024/123456"

    # Indian Application Number
    sig3 = detect_live_lookup_intent("Check filing details for IN202111012345")
    assert sig3.has_live_signal is True
    assert sig3.reference_number == "IN202111012345"

    # US Patent Number
    sig4 = detect_live_lookup_intent("Is US11456789B2 still active?")
    assert sig4.has_live_signal is True
    assert sig4.reference_number == "US11456789B2"


def test_detect_live_lookup_intent_keywords():
    """Verify detection of live status and registry keyword phrases."""
    sig1 = detect_live_lookup_intent("What is the current status of the Ashwagandha formulation patent?")
    assert sig1.has_live_signal is True
    assert sig1.signal_type == "STATUS_KEYWORD"

    sig2 = detect_live_lookup_intent("Check if registered: Herbal Anti-Diabetic Extract as of today")
    assert sig2.has_live_signal is True
    assert sig2.signal_type == "STATUS_KEYWORD"

    sig3 = detect_live_lookup_intent("Search patentscope for turmeric synergy extracts")
    assert sig3.has_live_signal is True
    assert sig3.signal_type == "STATUS_KEYWORD"


def test_zero_regression_on_statutory_queries():
    """Verify ordinary statutory legal queries DO NOT trigger live lookup."""
    statutory_queries = [
        "Can I patent an Ayurvedic formulation under Section 3(p)?",
        "What are the Form 25-D requirements for classical churnas?",
        "Explain NBA approval requirements under Section 3 of Biological Diversity Act.",
        "What is the difference between Phytopharmaceutical and Patent-or-Proprietary Medicine?",
        "How do I license an Ayurveda Aahar product with FSSAI?",
    ]
    for q in statutory_queries:
        sig = detect_live_lookup_intent(q)
        assert sig.has_live_signal is False, f"Query incorrectly triggered live lookup: {q}"
        assert sig.signal_type == "NONE"


@pytest.mark.asyncio
async def test_dispatch_live_lookup_integration():
    """Verify dispatch_live_lookup coordinates with connectors and returns hits."""
    # Active live query
    hits = await dispatch_live_lookup("What is the current status of PCT/IN2023/050123?")
    assert isinstance(hits, list)
    assert len(hits) >= 1
    assert any("WIPO" in h.source_name for h in hits)

    # Inactive normal statutory query -> 0 external calls
    unaffected_hits = await dispatch_live_lookup("Explain Section 3(e) synergistic combinations.")
    assert unaffected_hits == []


# =============================================================================
# 4. PROMPT ASSEMBLY & CITATION VALIDATION TESTS
# =============================================================================

def test_prompt_assembly_with_distinct_live_labeling():
    """Verify live external hits are rendered in a distinct === LIVE EXTERNAL SOURCE === block."""
    statutory_evidence = [
        {"doc_title": "The Patents Act, 1970", "section_ref": "Section 3(p)", "content": "Traditional knowledge exclusion."}
    ]
    live_hits = [
        {
            "source_name": "WIPO PATENTSCOPE",
            "title": "PCT Application Record",
            "reference_number": "PCT/IN2023/050123",
            "url": "https://patentscope.wipo.int/search/en/detail.jsf?docId=PCT/IN2023/050123",
            "snippet": "Status: Published International Application.",
            "retrieved_at": "2026-09-04T04:30:00Z",
            "is_paid_source": False,
        }
    ]

    prompt = build_user_prompt(
        question="Check status of PCT/IN2023/050123",
        jurisdiction="INDIA",
        intent="PATENT",
        evidence_items=statutory_evidence,
        live_evidence_items=live_hits,
    )

    # Assert distinct labeling blocks
    assert "=== INDEXED STATUTORY EVIDENCE ===" in prompt
    assert "=== LIVE EXTERNAL SOURCE [1]: WIPO PATENTSCOPE" in prompt
    assert "Ref: PCT/IN2023/050123" in prompt
    assert "retrieved 2026-09-04T04:30:00Z" in prompt


def test_citation_validator_with_live_external_hits():
    """Verify CitationValidator attaches is_live=True and live verification status."""
    stat_evidence = [
        RetrievedEvidence(
            chunk_id="chunk-test-1",
            content="Traditional knowledge exclusion.",
            doc_title="The Patents Act, 1970",
            section_ref="Section 3(p)",
            source_url="https://wipolex.wipo.int/en/legislation/details/2143",
            jurisdiction="INDIA",
            document_type="STATUTE",
            target_collection="india_patents",
            verification_status="VERIFIED_OFFICIAL_GAZETTE",
            score=0.92,
            metadata={},
        )
    ]
    live_hit = ExternalHit(
        source_name="WIPO PATENTSCOPE",
        title="PCT Application Record",
        reference_number="PCT/IN2023/050123",
        url="https://patentscope.wipo.int/search/en/detail.jsf?docId=PCT/IN2023/050123",
        snippet="Status: Published.",
        is_paid_source=False,
    )

    response_text = (
        "Under Section 3(p) of the Patents Act, 1970, mere admixtures are excluded. "
        "According to a live WIPO PATENTSCOPE lookup, application PCT/IN2023/050123 is currently Published."
    )

    validated_citations, ratio = CitationValidator.validate_citations(
        response_text=response_text,
        retrieved_evidence=stat_evidence,
        jurisdiction="INDIA",
        live_external_hits=[live_hit],
    )

    assert len(validated_citations) == 2

    # Verify statutory citation
    stat_cit = next(c for c in validated_citations if not c.is_live)
    assert stat_cit.is_live is False
    assert stat_cit.verification_status == "VERIFIED_OFFICIAL_GAZETTE"

    # Verify live external citation
    live_cit = next(c for c in validated_citations if c.is_live)
    assert live_cit.is_live is True
    assert live_cit.verification_status == "VERIFIED_LIVE_REGISTRY"
    assert "PCT/IN2023/050123" in live_cit.section_ref
    assert live_cit.is_paid_source is False


# =============================================================================
# 6. WIPO PEARL TERMINOLOGY CONNECTOR TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_wipo_pearl_connector_availability():
    """Verify WIPO Pearl availability detection and environment toggle."""
    from src.connectors.wipo_pearl import WIPOPearlConnector
    conn = WIPOPearlConnector()

    with patch.dict(os.environ, {"WIPO_PEARL_ENABLED": "true"}):
        assert await conn.is_available() is True

    with patch.dict(os.environ, {"WIPO_PEARL_ENABLED": "false"}):
        assert await conn.is_available() is False


@pytest.mark.asyncio
async def test_wipo_pearl_token_fetch():
    """Verify OAuth2 Client Credentials token exchange and caching in WIPOPearlConnector."""
    from src.connectors.wipo_pearl import WIPOPearlConnector
    conn = WIPOPearlConnector()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "access_token": "mock_test_token_wipo_pearl_123",
        "token_type": "Bearer",
        "expires_in": 3600,
    }

    with patch.dict(os.environ, {
        "WIPO_PEARL_CLIENT_ID": "test_client_id",
        "WIPO_PEARL_CLIENT_SECRET": "test_client_secret",
    }):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp
            token = await conn.get_access_token()
            assert token == "mock_test_token_wipo_pearl_123"

            # Re-calling should use memory cached token without sending second request
            token2 = await conn.get_access_token()
            assert token2 == "mock_test_token_wipo_pearl_123"
            assert mock_post.call_count == 1


@pytest.mark.asyncio
async def test_wipo_pearl_search_success():
    """Verify WIPO Pearl search parses concepts, IPC codes, and translations."""
    from src.connectors.wipo_pearl import WIPOPearlConnector
    conn = WIPOPearlConnector()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "concepts": [
            {
                "conceptId": "CPT-10293",
                "term": "Curcuma longa",
                "definition": "Rhizomatous herbaceous perennial plant of the ginger family.",
                "subjectField": "PHARMACEUTICALS / BOTANY",
                "ipcCodes": ["A61K 36/9066", "A61P 29/00"],
                "translations": {
                    "de": "Kurkuma",
                    "fr": "Curcuma",
                    "ja": "ウコン",
                },
            }
        ]
    }

    with patch.object(conn, "get_access_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = "mock_token"
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_resp
            hits = await conn.search("Curcuma longa", max_results=3)

            assert len(hits) == 1
            assert "Curcuma longa" in hits[0].title
            assert "A61K 36/9066" in hits[0].snippet
            assert "DE: Kurkuma" in hits[0].snippet
            assert hits[0].is_paid_source is False
            assert "wipopearl.wipo.int" in hits[0].url


@pytest.mark.asyncio
async def test_wipo_pearl_botanical_enrichment_fallback():
    """Verify WIPO Pearl provides botanical synonym and IPC mapping for Ayurvedic herbs."""
    from src.connectors.wipo_pearl import WIPOPearlConnector
    conn = WIPOPearlConnector()

    mock_resp = MagicMock()
    mock_resp.status_code = 404  # Trigger botanical fallback logic

    with patch.object(conn, "get_access_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = None
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_resp
            hits = await conn.search("Ashwagandha formulation", max_results=2)

            assert len(hits) == 1
            assert "Withania somnifera" in hits[0].snippet
            assert "A61K 36/81" in hits[0].snippet
            assert "[INTERNAL REFERENCE" in hits[0].snippet
            assert hits[0].source_name == "Internal Botanical Reference"
            assert hits[0].reference_number is None
            assert hits[0].url is None
            assert hits[0].is_paid_source is False


@pytest.mark.asyncio
async def test_dispatch_multi_connector_integration():
    """Verify live lookup dispatcher concurrently executes multiple enabled connectors."""
    signal = LiveLookupSignal(
        has_live_signal=True,
        reference_number=None,
        search_terms="Ashwagandha",
        signal_type="STATUS_KEYWORD",
        confidence=0.95,
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = '<div class="ps-patent-result"><h3>PCT/IN2023/050123</h3><a class="ps-patent-result--title">Ashwagandha Extract</a></div>'
    mock_resp.json = MagicMock(return_value={"results": []})

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        hits = await dispatch_live_lookup("wipo pearl Ashwagandha terminology", signal=signal, timeout=5.0)
        assert len(hits) >= 1
        source_names = [h.source_name for h in hits]
        assert any("WIPO" in name or "Internal" in name or "NCBI" in name for name in source_names)


@pytest.mark.asyncio
async def test_ncbi_pubmed_connector_search_success():
    """Verify NCBI PubMed connector parses ESearch and ESummary JSON responses into ExternalHits."""
    from src.connectors.ncbi_pubmed import NCBIPubMedConnector
    conn = NCBIPubMedConnector()

    mock_search_resp = MagicMock()
    mock_search_resp.status_code = 200
    mock_search_resp.json.return_value = {
        "esearchresult": {"idlist": ["32242751", "34254920"]}
    }

    mock_summary_resp = MagicMock()
    mock_summary_resp.status_code = 200
    mock_summary_resp.json.return_value = {
        "result": {
            "32242751": {
                "title": "Pharmacological evaluation of Ashwagandha highlighting its healthcare claims",
                "source": "J Diet Suppl",
                "pubdate": "2021",
                "authors": [{"name": "Mandlik Ingawale DS"}, {"name": "Namdeo AG"}],
            },
            "34254920": {
                "title": "Effects of Withania somnifera (Ashwagandha) on Stress",
                "source": "Curr Neuropharmacol",
                "pubdate": "2021",
                "authors": [{"name": "Speers AB"}],
            },
        }
    }

    async def mock_get(url, *args, **kwargs):
        if "esearch.fcgi" in url:
            return mock_search_resp
        return mock_summary_resp

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=mock_get):
        hits = await conn.search("Ashwagandha withanolide")
        assert len(hits) == 2
        assert hits[0].reference_number == "PMID:32242751"
        assert hits[0].url == "https://pubmed.ncbi.nlm.nih.gov/32242751/"
        assert "Mandlik Ingawale DS" in hits[0].snippet
        assert hits[0].is_paid_source is False


@pytest.mark.asyncio
async def test_ncbi_pubmed_get_status_lookup():
    """Verify NCBI PubMed get_status resolves a specific PMID."""
    from src.connectors.ncbi_pubmed import NCBIPubMedConnector
    conn = NCBIPubMedConnector()

    mock_summary_resp = MagicMock()
    mock_summary_resp.status_code = 200
    mock_summary_resp.json.return_value = {
        "result": {
            "32242751": {
                "title": "Pharmacological evaluation of Ashwagandha",
                "source": "J Diet Suppl",
                "pubdate": "2021",
                "authors": [{"name": "Mandlik Ingawale DS"}],
            }
        }
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_summary_resp):
        status = await conn.get_status("PMID:32242751")
        assert status is not None
        assert status.reference_number == "PMID:32242751"
        assert status.status == "Published Journal Article"
        assert status.url == "https://pubmed.ncbi.nlm.nih.gov/32242751/"

