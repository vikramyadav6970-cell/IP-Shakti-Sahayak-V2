"""
ai/src/connectors/__init__.py

External and Paid Source Connector Layer for IP-SAKTI Sahayak.
Provides pluggable live data access (WIPO PATENTSCOPE, IPO, Commercial IP APIs)
with strict rate limiting, 8-second timeouts, and distinct live evidence labeling.
"""

from src.connectors.base import (
    ConnectorCredentialField,
    ConnectorErrorCode,
    ConnectorRegistry,
    ConnectorTestResult,
    ExternalHit,
    ExternalSourceConnector,
    ExternalStatus,
    TokenBucketRateLimiter,
    UsageLogger,
    connector_registry,
    usage_logger,
)
from src.connectors.router import (
    LiveLookupSignal,
    detect_live_lookup_intent,
    dispatch_live_lookup,
)
from src.connectors.wipo_patentscope import WIPOPatentscopeConnector, wipo_connector
from src.connectors.wipo_pearl import WIPOPearlConnector, wipo_pearl_connector
from src.connectors.ncbi_pubmed import NCBIPubMedConnector, ncbi_pubmed_connector
from src.connectors.credential_resolver import resolve_credentials

__all__ = [
    "ConnectorCredentialField",
    "ConnectorErrorCode",
    "ConnectorTestResult",
    "ExternalHit",
    "ExternalStatus",
    "ExternalSourceConnector",
    "TokenBucketRateLimiter",
    "UsageLogger",
    "usage_logger",
    "ConnectorRegistry",
    "connector_registry",
    "WIPOPatentscopeConnector",
    "wipo_connector",
    "WIPOPearlConnector",
    "wipo_pearl_connector",
    "NCBIPubMedConnector",
    "ncbi_pubmed_connector",
    "LiveLookupSignal",
    "detect_live_lookup_intent",
    "dispatch_live_lookup",
    "resolve_credentials",
]
