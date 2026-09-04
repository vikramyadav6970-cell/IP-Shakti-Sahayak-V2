"""
ai/src/connectors/wipo_pearl.py

WIPO Pearl Multilingual Terminology Connector implementation.
Provides programmatic access to WIPO's official multilingual terminology database (10 languages),
resolving scientific, botanical, and patent classification terms (IPC A61K 36/00) with OAuth2
Client Credentials authentication and resilient token caching.
"""

import base64
from datetime import datetime, timezone
import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional
import urllib.parse

import httpx

from src.connectors.base import (
    ConnectorCredentialField,
    ConnectorErrorCode,
    ConnectorTestResult,
    ExternalHit,
    ExternalSourceConnector,
    ExternalStatus,
    connector_registry,
    usage_logger,
)

logger = logging.getLogger("ipsakti.connectors.wipo_pearl")

# Common Ayurvedic & Botanical Term Mappings for IPC / Scientific Keyword Enrichment
BOTANICAL_IPC_MAP = {
    "ashwagandha": {"botanical": "Withania somnifera", "ipc": "A61K 36/81", "field": "PHARMACEUTICALS / BOTANY"},
    "withania somnifera": {"botanical": "Withania somnifera", "ipc": "A61K 36/81", "field": "PHARMACEUTICALS / BOTANY"},
    "turmeric": {"botanical": "Curcuma longa", "ipc": "A61K 36/9066", "field": "PHARMACEUTICALS / BIOCHEMISTRY"},
    "curcuma": {"botanical": "Curcuma longa", "ipc": "A61K 36/9066", "field": "PHARMACEUTICALS / BIOCHEMISTRY"},
    "curcumin": {"botanical": "Curcuma longa", "ipc": "A61K 36/9066", "field": "PHARMACEUTICALS / BIOCHEMISTRY"},
    "haldi": {"botanical": "Curcuma longa", "ipc": "A61K 36/9066", "field": "PHARMACEUTICALS / BIOCHEMISTRY"},
    "tulsi": {"botanical": "Ocimum sanctum / Ocimum tenuiflorum", "ipc": "A61K 36/53", "field": "PHARMACEUTICALS / BOTANY"},
    "ocimum": {"botanical": "Ocimum sanctum", "ipc": "A61K 36/53", "field": "PHARMACEUTICALS / BOTANY"},
    "neem": {"botanical": "Azadirachta indica", "ipc": "A61K 36/58", "field": "PHARMACEUTICALS / BIOPESTICIDES"},
    "azadirachta": {"botanical": "Azadirachta indica", "ipc": "A61K 36/58", "field": "PHARMACEUTICALS / BIOPESTICIDES"},
    "brahmi": {"botanical": "Bacopa monnieri", "ipc": "A61K 36/68", "field": "PHARMACEUTICALS / NEUROLOGY"},
    "guggulu": {"botanical": "Commiphora mukul", "ipc": "A61K 36/328", "field": "PHARMACEUTICALS / LIPID METABOLISM"},
    "amla": {"botanical": "Phyllanthus emblica", "ipc": "A61K 36/47", "field": "PHARMACEUTICALS / ANTIOXIDANTS"},
    "triphala": {"botanical": "Polyherbal (Emblica + Terminalia)", "ipc": "A61K 36/185", "field": "PHARMACEUTICALS / AYUSH"},
    "chyawanprash": {"botanical": "Polyherbal formulation", "ipc": "A61K 36/00", "field": "PHARMACEUTICALS / TRADITIONAL MEDICINE"},
}


class WIPOPearlConnector(ExternalSourceConnector):
    """
    Live connector for WIPO Pearl Multilingual Terminology Database.
    Authenticates via OAuth2 Client Credentials grant (Client ID & Client Secret)
    or direct JWT Bearer token (JWT-PLAN).
    Supports user-managed custom credentials with write-only encryption at rest.
    """

    name: str = "wipo_pearl"
    display_name: str = "WIPO Pearl (Multilingual Patent Terminology)"
    description: str = (
        "WIPO's official multilingual terminology database across 10 languages (PCT documentation). "
        "Provides validated botanical names, definitions, language equivalents, and IPC codes (A61K 36/00)."
    )
    requires_api_key: bool = True
    is_paid: bool = False
    rate_limit_per_minute: int = 30
    timeout_seconds: float = 4.0

    credential_fields: List[ConnectorCredentialField] = [
        ConnectorCredentialField(
            name="client_id",
            label="Client ID",
            field_type="text",
            placeholder="e.g. 20OpHs4WRFnKw2PyZjgcOKHHZc3q...",
            required=True,
            help_text="Your OAuth2 Client ID from WIPO Business Partner Portal / Developer Portal",
        ),
        ConnectorCredentialField(
            name="client_secret",
            label="Client Secret",
            field_type="password",
            placeholder="Enter your client secret / JWT token",
            required=True,
            help_text="Your OAuth2 Client Secret or JWT token (encrypted with master key at rest)",
        ),
    ]

    BASE_WEB_URL: str = "https://wipopearl.wipo.int/en/linguistic"
    DEFAULT_API_URL: str = "https://api.wipo.int/wipopearl"
    DEFAULT_TOKEN_URL: str = "https://api.wipo.int/oauth2/token"
    USER_AGENT: str = (
        "IP-SAKTI-Sahayak/2.0 (Ayush-IPR-Assistant; Government-of-India; compliance@ayush.gov.in)"
    )

    def __init__(self):
        super().__init__()
        self._enabled_override: Optional[bool] = None
        self._cached_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    @property
    def client_id(self) -> str:
        return os.environ.get("WIPO_PEARL_CLIENT_ID", "").strip()

    @property
    def client_secret(self) -> str:
        return os.environ.get("WIPO_PEARL_CLIENT_SECRET", "").strip()

    @property
    def base_api_url(self) -> str:
        return os.environ.get("WIPO_PEARL_BASE_URL", self.DEFAULT_API_URL).rstrip("/")

    @property
    def token_url(self) -> str:
        return os.environ.get("WIPO_PEARL_TOKEN_URL", self.DEFAULT_TOKEN_URL)

    async def is_available(self) -> bool:
        """Check if WIPO Pearl connector is enabled."""
        try:
            if self._enabled_override is not None:
                return self._enabled_override
            env_val = os.environ.get("WIPO_PEARL_ENABLED", "true").strip().lower()
            return env_val in ["true", "1", "yes", "on"]
        except Exception as e:
            logger.warning(f"Error checking WIPO Pearl availability: {e}")
            return False

    def set_enabled(self, enabled: bool) -> None:
        """Override availability for test fixtures."""
        self._enabled_override = enabled

    async def test_connection(self, credentials: Optional[Dict[str, Any]] = None) -> ConnectorTestResult:
        """
        Tests candidate or saved credentials against WIPO Pearl API gateway.
        """
        creds = credentials or {}
        cid = creds.get("client_id", self.client_id).strip()
        csecret = creds.get("client_secret", self.client_secret).strip()

        if not cid and not csecret:
            return ConnectorTestResult(
                success=False,
                error_code=ConnectorErrorCode.INVALID_CONFIG,
                error_message="Both Client ID and Client Secret are required to connect WIPO Pearl.",
            )

        # 1. Attempt OAuth2 token exchange if Client ID and Secret are provided and token URL is configured
        if cid and csecret and self.token_url:
            auth_str = f"{cid}:{csecret}"
            encoded_creds = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
            post_headers = {
                "Authorization": f"Basic {encoded_creds}",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": self.USER_AGENT,
            }
            post_data = {"grant_type": "client_credentials"}

            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.post(self.token_url, headers=post_headers, data=post_data)
                    if resp.status_code == 200:
                        payload = resp.json()
                        if payload.get("access_token"):
                            return ConnectorTestResult(success=True)
                    elif resp.status_code in [401, 403]:
                        return ConnectorTestResult(
                            success=False,
                            error_code=ConnectorErrorCode.AUTH_FAILED,
                            error_message="Authentication failed: The Client ID or Secret was rejected by WIPO.",
                        )
                    elif resp.status_code == 429:
                        return ConnectorTestResult(
                            success=False,
                            error_code=ConnectorErrorCode.RATE_LIMITED,
                            error_message="WIPO rate limit reached. Please try again in a few minutes.",
                        )
                    elif resp.status_code >= 500:
                        return ConnectorTestResult(
                            success=False,
                            error_code=ConnectorErrorCode.SERVICE_UNAVAILABLE,
                            error_message="WIPO service is currently unavailable (HTTP 5xx). Please try again later.",
                        )
            except (httpx.TimeoutException, TimeoutError):
                return ConnectorTestResult(
                    success=False,
                    error_code=ConnectorErrorCode.NETWORK_TIMEOUT,
                    error_message="Connection timed out while reaching WIPO token endpoint.",
                )
            except Exception as exc:
                logger.debug(f"OAuth token probe notice: {exc}")

        # 2. Test live WIPO Pearl concepts endpoint with Bearer authentication
        bearer_token = csecret or cid
        get_headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Accept": "application/json",
            "User-Agent": self.USER_AGENT,
        }
        test_url = f"{self.base_api_url}/concepts/search"
        params = {"term": "curcuma", "sourceLang": "en", "limit": 1}

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(test_url, headers=get_headers, params=params)

                if resp.status_code == 200:
                    return ConnectorTestResult(success=True)

                if resp.status_code in [401, 403]:
                    return ConnectorTestResult(
                        success=False,
                        error_code=ConnectorErrorCode.AUTH_FAILED,
                        error_message="Authentication failed: The Client ID or Secret was rejected by WIPO.",
                    )

                if resp.status_code == 429:
                    return ConnectorTestResult(
                        success=False,
                        error_code=ConnectorErrorCode.RATE_LIMITED,
                        error_message="WIPO rate limit reached. Please try again in a few minutes.",
                    )

                if resp.status_code >= 500:
                    return ConnectorTestResult(
                        success=False,
                        error_code=ConnectorErrorCode.SERVICE_UNAVAILABLE,
                        error_message="WIPO service is currently unavailable (HTTP 5xx). Please try again later.",
                    )

                return ConnectorTestResult(
                    success=False,
                    error_code=ConnectorErrorCode.AUTH_FAILED,
                    error_message=f"WIPO API endpoint returned HTTP {resp.status_code}. Verify your application subscription in the WIPO Business Partner Portal.",
                )

        except (httpx.TimeoutException, TimeoutError):
            return ConnectorTestResult(
                success=False,
                error_code=ConnectorErrorCode.NETWORK_TIMEOUT,
                error_message="Connection timed out while reaching WIPO API gateway.",
            )
        except Exception as exc:
            return ConnectorTestResult(
                success=False,
                error_code=ConnectorErrorCode.UNKNOWN,
                error_message=f"Connection test failed: {str(exc)}",
            )

    async def get_access_token(self, credentials_override: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Retrieves or refreshes OAuth2 Bearer token using Client Credentials grant
        ONLY if an explicit OAuth token endpoint is configured in environment.
        """
        if not self.token_url:
            return None

        now = time.time()
        client_id = (credentials_override.get("client_id") if credentials_override else None) or self.client_id
        client_secret = (credentials_override.get("client_secret") if credentials_override else None) or self.client_secret

        if not credentials_override and self._cached_token and now < (self._token_expires_at - 60):
            return self._cached_token

        if not client_id or not client_secret:
            return None

        # Don't hammer token URL if it recently failed
        if not credentials_override and hasattr(self, "_token_failed_until") and now < self._token_failed_until:
            return None

        # Build basic auth header
        creds = f"{client_id}:{client_secret}"
        encoded_creds = base64.b64encode(creds.encode("utf-8")).decode("utf-8")

        headers = {
            "Authorization": f"Basic {encoded_creds}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": self.USER_AGENT,
        }
        data = {
            "grant_type": "client_credentials",
        }

        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                resp = await client.post(self.token_url, headers=headers, data=data)
                if resp.status_code == 200:
                    payload = resp.json()
                    access_token = payload.get("access_token")
                    expires_in = payload.get("expires_in", 3600)
                    if access_token:
                        if not credentials_override:
                            self._cached_token = access_token
                            self._token_expires_at = now + float(expires_in)
                        logger.info("Successfully obtained WIPO Pearl OAuth2 access token")
                        return access_token
                else:
                    if not credentials_override:
                        self._token_failed_until = now + 120.0  # 2 minute cooldown
        except Exception as e:
            if not credentials_override:
                self._token_failed_until = now + 120.0  # 2 minute cooldown
            logger.debug(f"Exception during WIPO Pearl OAuth2 token exchange: {e}")

        return None

    async def search(
        self,
        query: str,
        max_results: int = 5,
        language: str = "en",
        filters: Optional[Dict[str, Any]] = None,
        credentials_override: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[ExternalHit]:
        """
        Search WIPO Pearl for multilingual patent terminology, scientific definitions,
        and IPC classifications for a given query term.
        """
        start_time = time.time()
        endpoint = f"{self.base_api_url}/concepts/search"
        clean_query = query.strip()

        if not clean_query:
            return []

        # Check rate limit
        if not self.rate_limiter.allow_request():
            logger.warning(
                "WIPO Pearl rate limit reached (30 requests/min). Returning structured fallback reference."
            )
            return self._build_botanical_reference(clean_query, note="(Rate limited - local fallback)")

        token = await self.get_access_token(credentials_override=credentials_override)
        hits: List[ExternalHit] = []

        cid = (credentials_override.get("client_id") if credentials_override else None) or self.client_id
        csecret = (credentials_override.get("client_secret") if credentials_override else None) or self.client_secret
        bearer_token = token or csecret or cid

        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "application/json",
        }
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"

        params = {
            "term": clean_query,
            "sourceLang": language,
            "limit": max_results,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.get(endpoint, headers=headers, params=params)
                latency_ms = (time.time() - start_time) * 1000

                if resp.status_code == 200:
                    data = resp.json()
                    hits = self._parse_pearl_response(data, clean_query)
                    usage_logger.log_call(
                        connector_name=self.name,
                        operation="search",
                        query_or_ref=clean_query,
                        is_paid=self.is_paid,
                        success=True,
                        latency_ms=latency_ms,
                        hit_count=len(hits),
                    )
                else:
                    logger.info(
                        f"WIPO Pearl API returned HTTP {resp.status_code} for query '{clean_query}'. Using structured fallback."
                    )
                    hits = self._build_botanical_reference(clean_query)
                    usage_logger.log_call(
                        connector_name=self.name,
                        operation="search",
                        query_or_ref=clean_query,
                        is_paid=self.is_paid,
                        success=False,
                        latency_ms=latency_ms,
                        hit_count=len(hits),
                        error_msg=f"HTTP {resp.status_code}",
                    )

        except httpx.TimeoutException:
            latency_ms = (time.time() - start_time) * 1000
            logger.warning(f"WIPO Pearl API timed out after {self.timeout_seconds}s for query '{clean_query}'")
            hits = self._build_botanical_reference(clean_query, note="(API timed out - terminology referenced)")
            usage_logger.log_call(
                connector_name=self.name,
                operation="search",
                query_or_ref=clean_query,
                is_paid=self.is_paid,
                success=False,
                latency_ms=latency_ms,
                hit_count=len(hits),
                error_msg="Request timeout (8s limit reached)",
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Error executing WIPO Pearl search for '{clean_query}': {e}")
            hits = self._build_botanical_reference(clean_query)
            usage_logger.log_call(
                connector_name=self.name,
                operation="search",
                query_or_ref=clean_query,
                is_paid=self.is_paid,
                success=False,
                latency_ms=latency_ms,
                hit_count=len(hits),
                error_msg=str(e),
            )

        return hits[:max_results]

    def _parse_pearl_response(self, data: Any, query: str) -> List[ExternalHit]:
        """
        Parses JSON response from WIPO Pearl API into ExternalHit models.
        """
        hits: List[ExternalHit] = []
        retrieved_at = datetime.now(timezone.utc).isoformat()

        # Handle different potential response shapes from OAS 3.0 WIPO Pearl schema
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("concepts") or data.get("results") or data.get("terms") or [data]

        for item in items:
            if not isinstance(item, dict):
                continue

            concept_id = item.get("conceptId") or item.get("id") or "WIPO-PEARL"
            term_val = item.get("term") or item.get("label") or query
            definition = item.get("definition") or item.get("context") or ""
            subject_field = item.get("subjectField") or item.get("domain") or "PHARMACEUTICALS / TRADITIONAL KNOWLEDGE"
            ipc_classes = item.get("ipcCodes") or item.get("ipc") or ["A61K 36/00"]
            ipc_str = ", ".join(ipc_classes) if isinstance(ipc_classes, list) else str(ipc_classes)

            # Language equivalents
            translations = item.get("translations") or item.get("equivalents") or {}
            trans_snippets = []
            if isinstance(translations, dict):
                for lang, t_val in translations.items():
                    trans_snippets.append(f"{lang.upper()}: {t_val}")
            elif isinstance(translations, list):
                for t in translations:
                    if isinstance(t, dict):
                        trans_snippets.append(f"{t.get('lang', 'EN').upper()}: {t.get('term', '')}")

            trans_str = f" | Equivalents: {', '.join(trans_snippets)}" if trans_snippets else ""
            portal_url = f"{self.BASE_WEB_URL}?searchQuery={urllib.parse.quote(query)}"

            snippet = (
                f"WIPO Pearl Concept #{concept_id}: {term_val} "
                f"[Field: {subject_field} | IPC: {ipc_str}]. {definition}{trans_str}"
            )

            hits.append(
                ExternalHit(
                    source_name=self.display_name,
                    title=f"WIPO Pearl Terminology: {term_val} ({subject_field})",
                    reference_number=f"PEARL-{concept_id}",
                    url=portal_url,
                    snippet=snippet.strip(),
                    is_paid_source=self.is_paid,
                    metadata={"subject_field": subject_field, "ipc": ipc_classes, "definition": definition},
                )
            )

        if not hits:
            return self._build_botanical_reference(query)

        return hits

    def _build_botanical_reference(self, query: str, note: str = "") -> List[ExternalHit]:
        """
        Constructs an internal botanical / traditional knowledge reference record
        when live external lookup is unavailable.
        TRUTHFUL LABELING: Clearly marked as internal fallback, with NO synthetic
        reference IDs or simulated live external URLs.
        """
        query_lower = query.lower()

        # Check botanical map for known Ayurvedic herbs
        matched_info = None
        for key, val in BOTANICAL_IPC_MAP.items():
            if key in query_lower:
                matched_info = val
                break

        if matched_info:
            botanical = matched_info["botanical"]
            ipc = matched_info["ipc"]
            field = matched_info["field"]
            abstract = (
                f"Internal botanical synonym: '{botanical}'. "
                f"Primary International Patent Classification (IPC): {ipc} ({field})."
            )
            snippet = (
                f"[INTERNAL REFERENCE — Live WIPO Pearl lookup unavailable] "
                f"Term: '{query}' -> Scientific Botanical Name: '{botanical}' | "
                f"IPC Classification: {ipc} | Subject Field: {field}. {note}"
            )
            metadata = {
                "is_fallback": True,
                "source": "internal_botanical_taxonomy",
                "botanical": botanical,
                "ipc": ipc,
                "field": field,
            }
        else:
            abstract = f"Internal terminology reference for '{query}'."
            snippet = (
                f"[INTERNAL REFERENCE — Live WIPO Pearl lookup unavailable] "
                f"Term: '{query}'. {note}"
            )
            metadata = {
                "is_fallback": True,
                "source": "internal_botanical_taxonomy",
                "botanical": None,
                "ipc": None,
            }

        return [
            ExternalHit(
                source_name="Internal Botanical Reference",
                title=f"Internal Reference: {query.title()}",
                reference_number=None,
                url=None,
                snippet=snippet.strip(),
                is_paid_source=False,
                metadata=metadata,
            )
        ]

    async def get_status(
        self,
        reference_number: str,
        credentials_override: Optional[Dict[str, Any]] = None,
    ) -> Optional[ExternalStatus]:
        """
        WIPO Pearl is primarily a terminology / classification database.
        Status lookups are deferred to WIPOPatentscopeConnector.
        """
        return None


# Global singleton instance & auto-registration
wipo_pearl_connector = WIPOPearlConnector()
connector_registry.register(wipo_pearl_connector)
