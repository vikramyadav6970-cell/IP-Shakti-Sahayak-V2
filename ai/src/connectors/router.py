"""
ai/src/connectors/router.py

Lightweight live lookup classifier and multi-connector dispatcher.
Detects when a user consultation query specifically requests live data
(e.g., patent serial numbers, current filing status, global prior art lookups)
and dispatches to active external source connectors without blocking static RAG retrieval.
"""

import asyncio
from dataclasses import dataclass
import logging
import re
import time
from typing import Any, Dict, List, Optional, Union

from src.connectors.base import (
    ExternalHit,
    ExternalSourceConnector,
    ExternalStatus,
    connector_registry,
    usage_logger,
)

logger = logging.getLogger("ipsakti.connectors.router")

# Regex Patterns for Official Patent / Application / Trademark / Biomedical Serial Numbers
APPLICATION_NUMBER_PATTERNS = [
    # PCT: PCT/IN2023/050123, PCT/US2022/123456
    (r"\b(PCT\/[A-Z]{2}\d{4}\/\d{4,7})\b", "PCT_APPLICATION"),
    # WIPO WO Publication: WO/2024/123456, WO2024123456, WO 2023/012345
    (r"\b(WO\s*[\/\-]?\s*\d{4}\s*[\/\-]?\s*\d{5,7})\b", "WO_PUBLICATION"),
    # Indian Patent Application: IN202111012345, 202111012345, 202341012345
    (r"\b(IN\d{10,12})\b", "IPO_APPLICATION"),
    (r"\b(20[12]\d{9,10})\b", "IPO_APPLICATION_NUMERIC"),
    # US Patent / App: US11456789B2, US20230123456, US10123456A1
    (r"\b(US\s*\d{7,11}[A-Z\d]{0,4})\b", "US_PATENT"),
    # European Patent: EP1234567, EP 1234567 B1
    (r"\b(EP\s*\d{6,9}[A-Z\d]{0,4})\b", "EP_PATENT"),
    # NCBI PubMed PMID: PMID:35123456, PMID35123456, PMID 35123456
    (r"\b(PMID:?\s*\d{6,9})\b", "PUBMED_PMID"),
]

# Keywords & Phrases Indicating Live Status / Live Registry / Prior Art Search Intent
LIVE_STATUS_KEYWORDS = [
    # NCBI PubMed & Biomedical / Phytochemistry Prior Art triggers
    "ncbi pubmed",
    "search pubmed",
    "pubmed search",
    "pubmed",
    "ncbi",
    "clinical trials",
    "clinical trial",
    "clinical studies",
    "clinical study",
    "botanical research",
    "phytochemical research",
    "pharmacological study",
    "pharmacological trials",
    "pharmacological evidence",
    "biomedical prior art",
    "phytochemistry",
    # WIPO PATENTSCOPE triggers
    "wipo patentscope",
    "search wipo patentscope",
    "search patentscope",
    "patentscope search",
    "patentscope",
    "wipo search",
    "search wipo",
    "wipo status",
    "wipo register",
    "wipo database",
    "wipo portal",
    # WIPO Pearl & Multilingual Terminology triggers
    "wipo pearl",
    "pearl terminology",
    "patent terminology",
    "botanical synonym",
    "botanical name",
    "ipc classification",
    "ipc code",
    "multilingual patent",
    "translate term",
    # Global / Prior Art / Recent Filings triggers
    "recent patent filings",
    "recent patent filing",
    "recent patent",
    "recent patents",
    "patent filings",
    "patent filing",
    "global patent records",
    "global patent search",
    "global patent",
    "global patents",
    "international patent filings",
    "international patent records",
    "international patents",
    "international patent",
    "live prior art",
    "prior art search",
    "prior art",
    "patent search",
    "search patent",
    "search patents",
    "check global register",
    "global register",
    # Live Status & Registration check triggers
    "current status",
    "filing status",
    "legal status",
    "latest status",
    "live status",
    "application status",
    "status of application",
    "check application",
    "is this already registered",
    "is this registered",
    "is this filed",
    "is it filed",
    "check if registered",
    "check if filed",
    "as of today",
]

# Ensure longer compound phrases match before shorter single-word subsets
LIVE_STATUS_KEYWORDS_SORTED = sorted(LIVE_STATUS_KEYWORDS, key=len, reverse=True)


def _clean_search_subject(query: str, matched_kw: str) -> str:
    """
    Extracts core subject terms by removing trigger phrases and query boilerplate.
    E.g.: 'Search WIPO PATENTSCOPE for recent patent filings on standardized Ashwagandha withanolide extraction.'
          -> 'standardized Ashwagandha withanolide extraction'
    """
    clean = query.strip()
    # Remove matched keyword
    clean = re.sub(re.escape(matched_kw), " ", clean, flags=re.IGNORECASE)
    
    # Strip any occurrences of registry/database names
    clean = re.sub(r"\b(wipo pearl|patentscope|wipo|ncbi pubmed|pubmed|ncbi)\b", " ", clean, flags=re.IGNORECASE)
    
    # Strip common query boilerplate phrases iteratively
    for _ in range(3):
        clean = re.sub(r"^(search|check|find|lookup|look up|query|what (are|is)( the)?|tell me about|show me|live)\s+(for|on|about|in|of)?\s*", " ", clean, flags=re.IGNORECASE)
        clean = re.sub(r"^(recent|global|international|live)?\s*(patent filings|patents|patent records|prior art search|prior art|clinical trials|clinical study|clinical studies|studies|trials|research)\s*(on|for|about|in|of)?\s*", " ", clean, flags=re.IGNORECASE)
        clean = re.sub(r"^(multilingual patent terms and ipc classification for|ipc classification for|botanical name for|terms and ipc classification for|terms for)\s*", " ", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\s+(in|from|using|on|via)\s+(wipo pearl|patentscope|wipo|pearl|ncbi pubmed|pubmed|ncbi)\b.*$", " ", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\s*\?+$", " ", clean).strip()
        clean = re.sub(r"^(for|on|about|in|of|with|and|recent)\s+", " ", clean, flags=re.IGNORECASE).strip()
        clean = re.sub(r"\s+(in|on|for|at)$", " ", clean, flags=re.IGNORECASE).strip()
    
    clean = re.sub(r"\s+", " ", clean).strip()
    clean = re.sub(r"^[^\w\d]+|[^\w\d]+$", "", clean).strip()
    return clean or query


@dataclass
class LiveLookupSignal:
    """Classification signal representing whether a query warrants external live lookup."""
    has_live_signal: bool
    reference_number: Optional[str] = None
    search_terms: Optional[str] = None
    signal_type: str = "NONE"  # "APPLICATION_NUMBER" | "STATUS_KEYWORD" | "PRIOR_ART_SEARCH" | "NONE"
    confidence: float = 0.0
    detected_pattern: Optional[str] = None


def detect_live_lookup_intent(query: str) -> LiveLookupSignal:
    """
    Lightweight classification signal detecting live lookup intent.
    Zero latency overhead (<1ms regex and keyword scan).
    """
    if not query or not query.strip():
        return LiveLookupSignal(has_live_signal=False)

    clean_q = query.strip()

    # 1. Check for explicit application/patent/registration numbers
    for pattern, pat_name in APPLICATION_NUMBER_PATTERNS:
        match = re.search(pattern, clean_q, re.IGNORECASE)
        if match:
            ref_raw = match.group(1).replace(" ", "").upper()
            return LiveLookupSignal(
                has_live_signal=True,
                reference_number=ref_raw,
                search_terms=ref_raw,
                signal_type="APPLICATION_NUMBER",
                confidence=0.98,
                detected_pattern=pat_name,
            )

    # 2. Check for explicit live status / search keywords (ordered by descending length)
    lower_q = clean_q.lower()
    for kw in LIVE_STATUS_KEYWORDS_SORTED:
        if kw in lower_q:
            search_subject = _clean_search_subject(clean_q, kw)
            return LiveLookupSignal(
                has_live_signal=True,
                reference_number=None,
                search_terms=search_subject or clean_q,
                signal_type="STATUS_KEYWORD",
                confidence=0.90,
                detected_pattern=f"KEYWORD:{kw}",
            )

    # No live signal detected
    return LiveLookupSignal(
        has_live_signal=False,
        reference_number=None,
        search_terms=None,
        signal_type="NONE",
        confidence=0.0,
    )


async def dispatch_live_lookup(
    query: str,
    signal: Optional[LiveLookupSignal] = None,
    timeout: float = 8.0,
    user_id: Optional[Any] = None,
    db: Optional[Any] = None,
) -> List[ExternalHit]:
    """
    Dispatches live search / status queries across all available external connectors.
    Enforces per-user credential resolution (BYOK) with fallback to platform .env defaults,
    runs concurrently, and enforces strict overall timeout.
    """
    from src.connectors.credential_resolver import resolve_credentials

    active_signal = signal or detect_live_lookup_intent(query)
    if not active_signal.has_live_signal:
        return []

    available_connectors = await connector_registry.get_available_connectors()
    if not available_connectors:
        logger.info("Live lookup signal detected, but no external connectors are currently available/enabled.")
        return []

    t_start = time.perf_counter()
    tasks = []

    for connector in available_connectors:
        async def _run_connector(c: ExternalSourceConnector, sig: LiveLookupSignal) -> List[ExternalHit]:
            conn_timeout = min(getattr(c, "timeout_seconds", timeout), timeout)
            try:
                # Resolve user-specific credentials if available
                user_creds = None
                if user_id and db:
                    try:
                        from src.connectors.credential_resolver import get_user_connector_status
                        u_stat = await get_user_connector_status(user_id, c.name, db)
                        if u_stat == "disconnected":
                            logger.info(f"Connector '{c.name}' is disconnected by user. Skipping.")
                            return []
                        user_creds = await resolve_credentials(user_id, c.name, db)
                    except Exception as exc:
                        logger.warning(f"Error resolving user credentials for {c.name}: {exc}")

                async def _exec():
                    if sig.reference_number:
                        status_obj: Optional[ExternalStatus] = await c.get_status(
                            sig.reference_number,
                            credentials_override=user_creds,
                        )
                        if status_obj:
                            return [
                                ExternalHit(
                                    source_name=c.display_name,
                                    title=f"{status_obj.title or sig.reference_number} — Status: {status_obj.status}",
                                    reference_number=status_obj.reference_number,
                                    url=status_obj.url,
                                    snippet=(
                                        f"Live Filing Status: {status_obj.status}. "
                                        f"Applicant: {status_obj.applicant or 'Recorded on file'}. "
                                        f"Publication Date: {status_obj.publication_date or 'Recorded'}."
                                    ),
                                    retrieved_at=status_obj.retrieved_at,
                                    is_paid_source=status_obj.is_paid_source,
                                    metadata={"status": status_obj.status, "raw": status_obj.raw_details},
                                )
                            ]
                        return []
                    else:
                        search_query = sig.search_terms or query
                        return await c.search(
                            search_query,
                            credentials_override=user_creds,
                        )

                return await asyncio.wait_for(_exec(), timeout=conn_timeout)
            except (asyncio.TimeoutError, TimeoutError):
                logger.warning(f"Connector {c.name} timed out after {conn_timeout}s.")
                return []
            except Exception as exc:
                logger.warning(f"Connector {c.name} lookup failed: {exc}")
                return []

        tasks.append(_run_connector(connector, active_signal))

    try:
        # Run all connector tasks concurrently with overall safety timeout
        results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=timeout)
        all_hits: List[ExternalHit] = []
        for res in results:
            if isinstance(res, list):
                all_hits.extend(res)
            elif isinstance(res, Exception):
                logger.warning(f"Live connector task exception: {res}")

        latency_ms = (time.perf_counter() - t_start) * 1000.0
        logger.info(f"Dispatched live lookup for '{query}' -> Retrieved {len(all_hits)} hits in {latency_ms:.1f}ms")
        return all_hits

    except (asyncio.TimeoutError, TimeoutError):
        logger.warning(f"Live lookup overall dispatch timed out after {timeout}s.")
        return []
    except Exception as exc:
        logger.warning(f"Error during live lookup dispatch: {exc}")
        return []
