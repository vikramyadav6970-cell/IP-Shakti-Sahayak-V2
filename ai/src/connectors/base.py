"""
ai/src/connectors/base.py

Core abstract interfaces, data contracts, rate limiting, and usage logging
for external live and paid source connectors in IP-SAKTI Sahayak.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ipsakti.connectors")


@dataclass
class ExternalHit:
    """Individual search result / evidence hit returned by an external connector."""
    source_name: str
    title: str
    reference_number: Optional[str]
    url: Optional[str]
    snippet: str
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_paid_source: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name,
            "title": self.title,
            "reference_number": self.reference_number,
            "url": self.url,
            "snippet": self.snippet,
            "retrieved_at": self.retrieved_at.isoformat(),
            "is_paid_source": self.is_paid_source,
            "metadata": self.metadata,
        }


@dataclass
class ExternalStatus:
    """Detailed live filing/legal status for a specific application/patent number."""
    source_name: str
    reference_number: str
    status: str
    filing_date: Optional[str] = None
    publication_date: Optional[str] = None
    applicant: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_paid_source: bool = False
    raw_details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name,
            "reference_number": self.reference_number,
            "status": self.status,
            "filing_date": self.filing_date,
            "publication_date": self.publication_date,
            "applicant": self.applicant,
            "title": self.title,
            "url": self.url,
            "retrieved_at": self.retrieved_at.isoformat(),
            "is_paid_source": self.is_paid_source,
            "raw_details": self.raw_details or {},
        }


class TokenBucketRateLimiter:
    """In-memory sliding window rate limiter for external connector calls."""

    def __init__(self, max_calls_per_minute: Optional[int] = 60):
        self.max_calls = max_calls_per_minute
        self.timestamps: List[float] = []

    def allow_request(self) -> bool:
        if not self.max_calls or self.max_calls <= 0:
            return True

        now = time.time()
        # Filter timestamps within the last 60 seconds
        self.timestamps = [t for t in self.timestamps if now - t < 60.0]

        if len(self.timestamps) < self.max_calls:
            self.timestamps.append(now)
            return True
        return False

    def remaining_calls(self) -> int:
        if not self.max_calls:
            return 999999
        now = time.time()
        self.timestamps = [t for t in self.timestamps if now - t < 60.0]
        return max(0, self.max_calls - len(self.timestamps))


class UsageLogger:
    """
    Append-only usage logger for tracking external connector calls,
    especially paid / commercial APIs where cost control is paramount.
    """

    def __init__(self, log_dir: Optional[str] = None):
        if log_dir is None:
            # Default to backend logs or workspace logs
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.log_dir = base_dir / "logs"
        else:
            self.log_dir = Path(log_dir)

        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        self.log_file = self.log_dir / "external_connectors_usage.jsonl"
        self._in_memory_records: List[Dict[str, Any]] = []

    def log_call(
        self,
        connector_name: str,
        operation: str,
        query_or_ref: str,
        is_paid: bool,
        success: bool,
        latency_ms: float,
        hit_count: int,
        error_msg: Optional[str] = None,
    ) -> Dict[str, Any]:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "connector": connector_name,
            "operation": operation,
            "query_or_ref": query_or_ref,
            "is_paid": is_paid,
            "success": success,
            "latency_ms": round(latency_ms, 2),
            "hit_count": hit_count,
            "error": error_msg,
        }

        self._in_memory_records.append(record)

        # Append to JSONL log file
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as exc:
            logger.warning(f"Failed to append to usage log file {self.log_file}: {exc}")

        # Console logging for paid/external calls
        cost_tag = "[PAID SOURCE]" if is_paid else "[FREE SOURCE]"
        status_tag = "SUCCESS" if success else f"FAILED ({error_msg or 'Unknown'})"
        logger.info(
            f"{cost_tag} [{connector_name}] {operation}('{query_or_ref}') -> {status_tag} | "
            f"Hits: {hit_count} | Latency: {latency_ms:.1f}ms"
        )
        return record

    def get_recent_records(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._in_memory_records[-limit:]


# Global singleton usage logger
usage_logger = UsageLogger()


import enum


class ConnectorErrorCode(str, enum.Enum):
    """Structured error codes for external connector test and authentication failures."""
    AUTH_FAILED = "auth_failed"                # Invalid/rejected API key, client secret, or expired token
    NETWORK_TIMEOUT = "network_timeout"         # Provider unreachable or exceeded timeout (8s)
    SERVICE_UNAVAILABLE = "service_unavailable" # Provider returned 5xx server error
    RATE_LIMITED = "rate_limited"               # Provider returned 429 too many requests
    INVALID_CONFIG = "invalid_config"           # Missing required credential fields or malformed parameters
    UNKNOWN = "unknown"                         # Unclassified failure (safe generic message returned)


@dataclass
class ConnectorCredentialField:
    """Specification of an individual credential input field required by a connector."""
    name: str
    label: str
    field_type: str = "text"  # "text" | "password"
    placeholder: str = ""
    required: bool = True
    help_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "field_type": self.field_type,
            "placeholder": self.placeholder,
            "required": self.required,
            "help_text": self.help_text,
        }


@dataclass
class ConnectorTestResult:
    """Result of testing candidate or stored credentials against an external provider."""
    success: bool
    error_code: Optional[ConnectorErrorCode] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "error_code": self.error_code.value if self.error_code else None,
            "error_message": self.error_message,
        }


class ExternalSourceConnector(ABC):
    """
    Abstract Base Class for all external source connectors.
    Architected so third-party databases (WIPO, Manupatra, PatSnap, CDSCO)
    can be plugged in without changing downstream RAG or orchestration logic.
    """

    name: str = "base_connector"
    display_name: str = "Base External Connector"
    description: str = ""
    requires_api_key: bool = False
    is_paid: bool = False
    rate_limit_per_minute: Optional[int] = 60
    timeout_seconds: float = 8.0
    credential_fields: List[ConnectorCredentialField] = []

    def __init__(self):
        self.rate_limiter = TokenBucketRateLimiter(self.rate_limit_per_minute)

    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if API key is present and service is configured / reachable.
        MUST NEVER raise an exception — returns False on any failure
        so callers degrade gracefully.
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        credentials_override: Optional[Dict[str, Any]] = None,
    ) -> List[ExternalHit]:
        """
        Execute a live keyword / faceted search against external database.
        Enforces its own timeout (<= 8.0s) and returns empty list on failure.
        MUST NEVER raise an unhandled exception.
        """
        pass

    @abstractmethod
    async def get_status(
        self,
        reference_number: str,
        credentials_override: Optional[Dict[str, Any]] = None,
    ) -> Optional[ExternalStatus]:
        """
        Look up a specific patent/application/trademark serial number.
        Returns None if unsupported or not found — NEVER fabricates status.
        MUST NEVER raise an unhandled exception.
        """
        pass

    async def test_connection(self, credentials: Optional[Dict[str, Any]] = None) -> ConnectorTestResult:
        """
        Lightweight connection and credential validity test.
        Distinguishes AUTH_FAILED, NETWORK_TIMEOUT, SERVICE_UNAVAILABLE, and RATE_LIMITED.
        """
        try:
            available = await self.is_available()
            if available:
                return ConnectorTestResult(success=True)
            return ConnectorTestResult(
                success=False,
                error_code=ConnectorErrorCode.INVALID_CONFIG,
                error_message="Connector is currently disabled or unconfigured in the platform environment.",
            )
        except Exception as exc:
            return ConnectorTestResult(
                success=False,
                error_code=ConnectorErrorCode.UNKNOWN,
                error_message="Connection test failed.",
            )


class ConnectorRegistry:
    """Registry managing available external source connectors."""

    def __init__(self):
        self._connectors: Dict[str, ExternalSourceConnector] = {}

    def register(self, connector: ExternalSourceConnector) -> None:
        self._connectors[connector.name] = connector
        logger.info(f"Registered external connector: {connector.name} ({connector.display_name})")

    def get(self, name: str) -> Optional[ExternalSourceConnector]:
        return self._connectors.get(name)

    def list_all(self) -> List[ExternalSourceConnector]:
        return list(self._connectors.values())

    async def get_available_connectors(self) -> List[ExternalSourceConnector]:
        available = []
        for c in self._connectors.values():
            try:
                if await c.is_available():
                    available.append(c)
            except Exception as exc:
                logger.warning(f"Connector {c.name} is_available() check failed: {exc}")
        return available


# Global singleton connector registry
connector_registry = ConnectorRegistry()
