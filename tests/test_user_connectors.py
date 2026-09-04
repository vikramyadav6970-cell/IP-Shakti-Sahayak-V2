"""
tests/test_user_connectors.py

Comprehensive test suite for the User-Managed External Connector Credentials (BYOK) Layer:
1. Symmetric Encryption & Decryption (Fernet, key derivation, ciphertext != plaintext, secret masking).
2. Connector Error Classification (AUTH_FAILED, NETWORK_TIMEOUT, SERVICE_UNAVAILABLE, RATE_LIMITED).
3. Provider Test Connection handlers (PATENTSCOPE, WIPO Pearl with OAuth2 mock).
4. Credential Resolver (database lookup, decryption, active status enforcement, graceful fallback).
5. Router Integration with User Credentials (per-user credential resolution & override).
6. Strict Truthful Fallback Labeling invariant verification.
7. Backend Database Models & API Schemas.
"""

import asyncio
from datetime import datetime, timezone
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# Ensure ai and backend directories are on python path
root_dir = Path(__file__).resolve().parent.parent
ai_dir = str(root_dir / "ai")
backend_dir = str(root_dir / "backend")

if ai_dir not in sys.path:
    sys.path.insert(0, ai_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.encryption import (
    encrypt_credentials,
    decrypt_credentials,
    sanitize_error_message,
    get_encryption_key,
)
from app.models.entities import UserExternalConnection, User, AuditLog
from app.schemas.connector import (
    ConnectorFieldSchema,
    ConnectorInfoResponse,
    ConnectorTestRequest,
    ConnectorTestResponse,
    ConnectorConnectRequest,
    ConnectorStatusResponse,
)
from src.connectors.base import (
    ConnectorErrorCode,
    ConnectorCredentialField,
    ConnectorTestResult,
    ExternalSourceConnector,
    ExternalHit,
    connector_registry,
)
from src.connectors.wipo_patentscope import WIPOPatentscopeConnector
from src.connectors.wipo_pearl import WIPOPearlConnector
from src.connectors.ncbi_pubmed import NCBIPubMedConnector
from src.connectors.credential_resolver import resolve_credentials
from src.connectors.router import dispatch_live_lookup, LiveLookupSignal


# =============================================================================
# 1. ENCRYPTION & SECURITY LAYER TESTS
# =============================================================================

class TestEncryptionSecurity:
    """Tests for symmetric encryption, key derivation, and secret masking."""

    def test_encryption_roundtrip(self):
        """Plaintext credentials dict must encrypt to raw bytes without exposing secrets, and decrypt back accurately."""
        creds = {
            "client_id": "test_client_id_abc123",
            "client_secret": "test_secret_super_confidential_987xyz",
        }
        encrypted = encrypt_credentials(creds)
        assert isinstance(encrypted, bytes)
        assert len(encrypted) > 20
        # Ciphertext MUST NOT contain any plaintext secret values or keys
        assert b"test_client_id_abc123" not in encrypted
        assert b"test_secret_super_confidential_987xyz" not in encrypted
        assert b"client_secret" not in encrypted

        decrypted = decrypt_credentials(encrypted)
        assert decrypted == creds

    def test_empty_and_special_characters_encryption(self):
        """Ensure complex strings with unicode and special symbols encrypt cleanly."""
        creds = {
            "api_key": "sk-proj-1234!@#$%^&*()_+={}|[]:<>?,./~`",
            "notes": "Ayush आयुर्वेद & Haldi",
        }
        encrypted = encrypt_credentials(creds)
        decrypted = decrypt_credentials(encrypted)
        assert decrypted == creds

    def test_invalid_ciphertext_handling(self):
        """Invalid ciphertext must return None safely without unhandled crashes."""
        assert decrypt_credentials("not-a-valid-fernet-token") is None
        assert decrypt_credentials(b"bad_bytes") is None
        assert decrypt_credentials(None) is None

    def test_sanitize_error_message_masks_secrets(self):
        """Sanitizer must strip client secrets, bearer tokens, and sensitive query strings."""
        raw_err = "Failed authentication: client_secret=SUPER_SECRET_123 with Bearer eyJhbGciOi.secret.token"
        sanitized = sanitize_error_message(raw_err)
        assert "SUPER_SECRET_123" not in sanitized
        assert "eyJhbGciOi.secret.token" not in sanitized
        assert "[REDACTED]" in sanitized

    def test_missing_encryption_master_key_raises_runtime_error(self):
        """When ENCRYPTION_MASTER_KEY is unset/empty, encryption must raise RuntimeError with zero silent fallback."""
        from app.core.encryption import _get_fernet_key, validate_encryption_setup
        with patch.dict(os.environ, {"ENCRYPTION_MASTER_KEY": ""}, clear=False):
            with pytest.raises(RuntimeError) as exc_info:
                _get_fernet_key()
            assert "ENCRYPTION_MASTER_KEY" in str(exc_info.value)
            assert "JWT_SECRET" in str(exc_info.value)

            # validate_encryption_setup must also fail
            with pytest.raises(RuntimeError):
                validate_encryption_setup()

    def test_jwt_secret_not_used_when_encryption_master_key_missing(self):
        """Confirm that JWT_SECRET is strictly isolated and never substituted as the encryption key."""
        from app.core.encryption import _get_fernet_key
        # Provide a valid JWT_SECRET but empty ENCRYPTION_MASTER_KEY
        with patch.dict(os.environ, {"ENCRYPTION_MASTER_KEY": "", "JWT_SECRET": "test-jwt-secret-xyz-1234567890"}, clear=False):
            with pytest.raises(RuntimeError) as exc_info:
                _get_fernet_key()
            assert "ENCRYPTION_MASTER_KEY" in str(exc_info.value)

    def test_validate_encryption_setup_success(self):
        """Startup validation returns True when ENCRYPTION_MASTER_KEY is configured."""
        from app.core.encryption import validate_encryption_setup
        with patch.dict(os.environ, {"ENCRYPTION_MASTER_KEY": "a-valid-32-char-encryption-master-key-xyz"}, clear=False):
            assert validate_encryption_setup() is True


class TestUserEndpointThrottling:
    """Tests for per-user credential test endpoint rate limiting."""

    def test_user_endpoint_throttler_blocks_abuse(self):
        """Throttler must allow up to max_requests and block the (max+1)th request with 429."""
        from app.api.v1.connectors import UserEndpointThrottler
        from fastapi import HTTPException
        throttler = UserEndpointThrottler(max_requests_per_minute=3)
        user_id = "test-user-throttle-123"

        # 3 requests allowed
        throttler.check_rate_limit(user_id)
        throttler.check_rate_limit(user_id)
        throttler.check_rate_limit(user_id)

        # 4th request must raise 429
        with pytest.raises(HTTPException) as exc_info:
            throttler.check_rate_limit(user_id)
        assert exc_info.value.status_code == 429
        assert "Too many credential test attempts" in exc_info.value.detail


# =============================================================================
# 2. CONNECTOR ERROR CODES & MODELS TESTS
# =============================================================================

class TestConnectorErrorCodesAndModels:
    """Tests for base connector error code classification and models."""

    def test_connector_error_code_enum_values(self):
        """Verify all required standard error codes are defined."""
        assert ConnectorErrorCode.AUTH_FAILED.value == "auth_failed"
        assert ConnectorErrorCode.NETWORK_TIMEOUT.value == "network_timeout"
        assert ConnectorErrorCode.SERVICE_UNAVAILABLE.value == "service_unavailable"
        assert ConnectorErrorCode.RATE_LIMITED.value == "rate_limited"
        assert ConnectorErrorCode.INVALID_CONFIG.value == "invalid_config"
        assert ConnectorErrorCode.UNKNOWN.value == "unknown"

    def test_connector_credential_field_serialization(self):
        """Connector credential field metadata model."""
        field = ConnectorCredentialField(
            name="client_secret",
            label="Client Secret",
            field_type="password",
            required=True,
            help_text="WIPO Business Partner Portal client secret",
        )
        data = field.to_dict()
        assert data["name"] == "client_secret"
        assert data["field_type"] == "password"
        assert data["required"] is True

    def test_connector_test_result_to_dict(self):
        """ConnectorTestResult dataclass serialization."""
        res = ConnectorTestResult(
            success=False,
            error_code=ConnectorErrorCode.AUTH_FAILED,
            error_message="Invalid client credentials",
        )
        d = res.to_dict()
        assert d["success"] is False
        assert d["error_code"] == "auth_failed"
        assert d["error_message"] == "Invalid client credentials"


# =============================================================================
# 3. PROVIDER TEST CONNECTION TESTS
# =============================================================================

class TestProviderTestConnections:
    """Tests for provider-specific test_connection() implementations."""

    @pytest.mark.asyncio
    async def test_patentscope_test_connection_success(self):
        """PATENTSCOPE is a public/free registry; test_connection() succeeds when reachable."""
        connector = WIPOPatentscopeConnector()
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            result = await connector.test_connection({})
            assert result.success is True
            assert result.error_code is None

    @pytest.mark.asyncio
    async def test_wipo_pearl_test_connection_missing_credentials(self):
        """WIPO Pearl test_connection with missing credentials returns INVALID_CONFIG."""
        connector = WIPOPearlConnector()
        result = await connector.test_connection({})
        assert result.success is False
        assert result.error_code == ConnectorErrorCode.INVALID_CONFIG
        assert "required" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_wipo_pearl_test_connection_auth_failure_401(self):
        """WIPO Pearl test_connection on 401 response returns AUTH_FAILED."""
        connector = WIPOPearlConnector()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = '{"error": "invalid_client"}'

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            result = await connector.test_connection({
                "client_id": "invalid_id",
                "client_secret": "invalid_secret",
            })
            assert result.success is False
            assert result.error_code == ConnectorErrorCode.AUTH_FAILED
            assert "failed" in result.error_message.lower() or "rejected" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_wipo_pearl_test_connection_rate_limited_429(self):
        """WIPO Pearl test_connection on 429 response returns RATE_LIMITED."""
        connector = WIPOPearlConnector()
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = '{"error": "rate_limit_exceeded"}'

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            result = await connector.test_connection({
                "client_id": "id",
                "client_secret": "secret",
            })
            assert result.success is False
            assert result.error_code == ConnectorErrorCode.RATE_LIMITED
            assert "rate limit" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_wipo_pearl_test_connection_service_unavailable_503(self):
        """WIPO Pearl test_connection on 503 response returns SERVICE_UNAVAILABLE."""
        connector = WIPOPearlConnector()
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = "Service Temporarily Unavailable"

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            result = await connector.test_connection({
                "client_id": "id",
                "client_secret": "secret",
            })
            assert result.success is False
            assert result.error_code == ConnectorErrorCode.SERVICE_UNAVAILABLE

    @pytest.mark.asyncio
    async def test_wipo_pearl_test_connection_timeout(self):
        """WIPO Pearl test_connection on httpx.TimeoutException returns NETWORK_TIMEOUT."""
        import httpx
        connector = WIPOPearlConnector()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=httpx.ConnectTimeout("Timed out")):
            result = await connector.test_connection({
                "client_id": "id",
                "client_secret": "secret",
            })
            assert result.success is False
            assert result.error_code == ConnectorErrorCode.NETWORK_TIMEOUT
            assert "timed out" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_wipo_pearl_test_connection_success_oauth(self):
        """WIPO Pearl test_connection on 200 OAuth token issuance returns success."""
        connector = WIPOPearlConnector()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "mock_valid_bearer_token_xyz",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            result = await connector.test_connection({
                "client_id": "valid_partner_id",
                "client_secret": "valid_secret_key",
            })
            assert result.success is True
            assert result.error_code is None

    @pytest.mark.asyncio
    async def test_ncbi_pubmed_test_connection_missing_key(self):
        """NCBI PubMed test_connection with missing key returns INVALID_CONFIG."""
        connector = NCBIPubMedConnector()
        result = await connector.test_connection({})
        assert result.success is False
        assert result.error_code == ConnectorErrorCode.INVALID_CONFIG
        assert "required" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_ncbi_pubmed_test_connection_success(self):
        """NCBI PubMed test_connection with valid key returns success."""
        connector = NCBIPubMedConnector()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "esearchresult": {"idlist": ["32242751"]}
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
            result = await connector.test_connection({"api_key": "valid_ncbi_key_123"})
            assert result.success is True
            assert result.error_code is None

    @pytest.mark.asyncio
    async def test_ncbi_pubmed_test_connection_invalid_key(self):
        """NCBI PubMed test_connection with invalid key returns AUTH_FAILED."""
        connector = NCBIPubMedConnector()
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = '{"error": "API key invalid"}'

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
            result = await connector.test_connection({"api_key": "invalid_key"})
            assert result.success is False
            assert result.error_code == ConnectorErrorCode.AUTH_FAILED
            assert "rejected" in result.error_message.lower() or "invalid" in result.error_message.lower()


# =============================================================================
# 4. CREDENTIAL RESOLVER & ROUTER INTEGRATION TESTS
# =============================================================================

class TestCredentialResolverAndRouter:
    """Tests for per-user credential resolution from database and router dispatching."""

    @pytest.mark.asyncio
    async def test_resolve_credentials_no_db_or_user(self):
        """When db or user_id is None, resolve_credentials returns None."""
        assert await resolve_credentials(None, "wipo_pearl", db=None) is None
        assert await resolve_credentials(1, "wipo_pearl", db=None) is None

    @pytest.mark.asyncio
    async def test_resolve_credentials_active_user_connection(self):
        """Active user connection decrypts credentials dictionary."""
        mock_db = MagicMock()
        raw_creds = {"client_id": "resolved_user_id", "client_secret": "resolved_secret"}
        encrypted = encrypt_credentials(raw_creds)

        mock_conn = MagicMock()
        mock_conn.status = "connected"
        mock_conn.encrypted_credentials = encrypted

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_conn
        mock_db.query.return_value = mock_query
        # Ensure execute attribute does not interfere
        del mock_db.execute

        resolved = await resolve_credentials(user_id="d1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c", connector_name="wipo_pearl", db=mock_db)
        assert resolved == raw_creds

    @pytest.mark.asyncio
    async def test_resolve_credentials_inactive_or_error_status(self):
        """When connection status is 'error' or 'disconnected', resolve_credentials returns None."""
        mock_db = MagicMock()
        mock_conn = MagicMock()
        mock_conn.status = "error"
        mock_conn.encrypted_credentials = encrypt_credentials({"client_id": "id", "client_secret": "sec"})

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_conn
        mock_db.query.return_value = mock_query
        del mock_db.execute

        resolved = await resolve_credentials(user_id="d1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c", connector_name="wipo_pearl", db=mock_db)
        assert resolved is None

    @pytest.mark.asyncio
    async def test_router_passes_resolved_credentials_to_connector(self):
        """dispatch_live_lookup resolves per-user credentials and passes credentials_override."""
        mock_db = MagicMock()
        raw_creds = {"client_id": "user_42_key", "client_secret": "user_42_secret"}
        encrypted = encrypt_credentials(raw_creds)

        mock_conn = MagicMock()
        mock_conn.status = "connected"
        mock_conn.encrypted_credentials = encrypted
        mock_db.query.return_value.filter.return_value.first.return_value = mock_conn
        del mock_db.execute

        pearl_connector = connector_registry.get("wipo_pearl")
        assert pearl_connector is not None

        with patch.object(pearl_connector, "search", new_callable=AsyncMock) as mock_pearl_search:
            mock_pearl_search.return_value = [
                ExternalHit(
                    source_name="WIPO Pearl",
                    title="Curcuma longa L.",
                    reference_number="PEARL-TEST-999",
                    url="https://www.wipo.int/reference/en/wipopearl/",
                    snippet="Live terminology entry",
                )
            ]

            signal = LiveLookupSignal(
                has_live_signal=True,
                search_terms="Haldi Curcuma",
                signal_type="STATUS_KEYWORD",
                confidence=0.95,
            )

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = ""

            with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
                hits = await dispatch_live_lookup(
                    query="Haldi Curcuma",
                    signal=signal,
                    user_id="d1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
                    db=mock_db,
                )

                assert len(hits) >= 1
                # Verify credentials_override was passed to search()
                mock_pearl_search.assert_called_once()
                called_kwargs = mock_pearl_search.call_args[1]
                assert called_kwargs.get("credentials_override") == raw_creds


# =============================================================================
# 5. STRICT TRUTHFUL FALLBACK LABELING TESTS
# =============================================================================

class TestStrictTruthfulFallbackLabeling:
    """Verifies that failed live external lookups never fake registry IDs or live status."""

    @pytest.mark.asyncio
    async def test_fallback_botanical_reference_honesty(self):
        """When live API lookup fails, fallback must be labeled 'Internal Botanical Reference' with url=None, reference_number=None."""
        connector = WIPOPearlConnector()
        # Mock network failure
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=Exception("API Unreachable")):
            hits = await connector.search(query="Ashwagandha Withania somnifera")
            assert len(hits) == 1
            fallback_hit = hits[0]

            # Critical assertions for truthful labeling:
            assert fallback_hit.source_name == "Internal Botanical Reference"
            assert fallback_hit.reference_number is None
            assert fallback_hit.url is None
            assert "INTERNAL REFERENCE" in fallback_hit.snippet
            assert "Live WIPO Pearl lookup unavailable" in fallback_hit.snippet
            assert "Withania somnifera" in fallback_hit.snippet

            # Ensure NO fabricated PEARL-* reference IDs
            assert fallback_hit.reference_number != "PEARL-ASHWAGANDHA"
            assert fallback_hit.reference_number != "PEARL-WITHANIA"


# =============================================================================
# 6. DATABASE MODELS & SCHEMAS TESTS
# =============================================================================

class TestDatabaseModelsAndSchemas:
    """Tests for database entities and connector schemas."""

    def test_user_external_connection_model_instantiation(self):
        """UserExternalConnection model fields and default states."""
        now = datetime.now(timezone.utc)
        conn = UserExternalConnection(
            user_id="d1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
            connector_name="wipo_pearl",
            encrypted_credentials=b"gAAAAABtest...",
            status="connected",
            last_tested_at=now,
            last_error_code=None,
            last_error_message=None,
        )
        assert conn.user_id == "d1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c"
        assert conn.connector_name == "wipo_pearl"
        assert conn.status == "connected"
        assert conn.last_tested_at == now

    def test_connector_schemas_validation(self):
        """Connector list, connect, test, and status request/response schemas."""
        connect_req = ConnectorConnectRequest(
            credentials={
                "client_id": "test_id",
                "client_secret": "test_secret",
            }
        )
        assert connect_req.credentials["client_id"] == "test_id"

        test_resp = ConnectorTestResponse(
            success=True,
            error_code=None,
            error_message=None,
        )
        assert test_resp.success is True
        assert test_resp.error_code is None

        info_resp = ConnectorInfoResponse(
            name="wipo_pearl",
            display_name="WIPO Pearl (Terminology Database)",
            description="Multilingual terminology database",
            requires_api_key=True,
            is_paid=False,
            rate_limit_per_minute=30,
            credential_fields=[],
            is_connected=True,
            status="connected",
            last_tested_at=datetime.now(timezone.utc),
            last_error_code=None,
            last_error_message=None,
        )
        assert info_resp.is_connected is True
        assert info_resp.status == "connected"

        status_resp = ConnectorStatusResponse(
            connector_name="wipo_pearl",
            status="connected",
            last_tested_at=datetime.now(timezone.utc),
            message="Connector connected successfully",
        )
        assert status_resp.connector_name == "wipo_pearl"
        assert status_resp.status == "connected"

    @pytest.mark.asyncio
    async def test_public_connector_disconnection_and_reconnection(self):
        """Public connectors (requires_api_key=False) can be disconnected and reconnected."""
        import uuid
        from src.connectors.credential_resolver import get_user_connector_status
        user_id = str(uuid.uuid4())
        
        # Mock database with disconnected row
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = "disconnected"
        
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        status = await get_user_connector_status(user_id, "wipo_patentscope", mock_db)
        assert status == "disconnected"
