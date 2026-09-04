"""
backend/app/core/encryption.py

Symmetric encryption utilities for sensitive credentials at rest using Fernet.
Ensures user-managed external connector API keys and client secrets are NEVER
stored in plaintext.
"""

import base64
import hashlib
import json
import logging
import os
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger("ipsakti.encryption")


def _get_fernet_key() -> bytes:
    """
    Derives a 32-byte URL-safe base64-encoded Fernet key strictly from ENCRYPTION_MASTER_KEY.
    Fails loud with a descriptive RuntimeError if ENCRYPTION_MASTER_KEY is missing or empty.
    Strictly isolated from JWT_SECRET to allow independent secret rotation.
    """
    raw_key = os.environ.get("ENCRYPTION_MASTER_KEY")
    if raw_key is None:
        try:
            from app.config import settings
            raw_key = getattr(settings, "ENCRYPTION_MASTER_KEY", None)
        except Exception:
            raw_key = None

    if not raw_key or not raw_key.strip():
        raise RuntimeError(
            "CRITICAL CONFIGURATION ERROR: ENCRYPTION_MASTER_KEY environment variable is missing or empty. "
            "A dedicated master key (32+ characters) is strictly required to encrypt and decrypt "
            "user-managed external connector credentials. It must NOT be shared with JWT_SECRET. "
            "Please set ENCRYPTION_MASTER_KEY in your .env file."
        )

    # Hash to standard 32 bytes and base64-encode for Fernet compatibility
    hashed = hashlib.sha256(raw_key.strip().encode("utf-8")).digest()
    return base64.urlsafe_b64encode(hashed)


def get_encryption_key() -> bytes:
    """
    Public accessor to derive the 32-byte URL-safe base64 Fernet key.
    """
    return _get_fernet_key()


def validate_encryption_setup() -> bool:
    """
    Startup validation hook to verify that ENCRYPTION_MASTER_KEY is set and functional.
    Raises RuntimeError on failure so the application fails fast at startup.
    """
    try:
        key = _get_fernet_key()
        f = Fernet(key)
        sample = {"ping": "encryption_master_key_health_check"}
        token = f.encrypt(json.dumps(sample).encode("utf-8"))
        decrypted = json.loads(f.decrypt(token).decode("utf-8"))
        return decrypted == sample
    except Exception as exc:
        raise RuntimeError(
            f"ENCRYPTION_MASTER_KEY validation failed: {exc}. "
            "Ensure ENCRYPTION_MASTER_KEY is set to a valid secret string in .env."
        ) from exc


def encrypt_credentials(payload: Dict[str, Any]) -> bytes:
    """
    Serializes a dictionary of credentials to JSON and encrypts it using Fernet.
    Returns raw encrypted bytes suitable for storing in a PostgreSQL bytea / LargeBinary column.
    """
    if not payload:
        raise ValueError("Cannot encrypt empty credentials payload")

    key = _get_fernet_key()
    f = Fernet(key)
    serialized = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return f.encrypt(serialized)


def decrypt_credentials(encrypted_blob: Any) -> Optional[Dict[str, Any]]:
    """
    Decrypts encrypted bytea blob or base64 token string and deserializes it back to a credential dictionary.
    Returns None if decryption fails or token is invalid.
    """
    if not encrypted_blob:
        return None

    if isinstance(encrypted_blob, str):
        encrypted_blob = encrypted_blob.encode("utf-8")

    key = _get_fernet_key()
    f = Fernet(key)

    try:
        decrypted_bytes = f.decrypt(encrypted_blob)
        return json.loads(decrypted_bytes.decode("utf-8"))
    except InvalidToken:
        logger.error("Failed to decrypt credentials: InvalidToken / incorrect master key")
        return None
    except Exception as exc:
        logger.error(f"Failed to decrypt credentials: {exc}")
        return None


def sanitize_error_message(error_msg: Optional[str], candidate_credentials: Optional[Dict[str, Any]] = None) -> str:
    """
    Sanitizes error messages before persisting to database or returning to UI.
    Guarantees that no raw credential values leak into last_error_message.
    """
    if not error_msg:
        return "Unknown connection error"

    sanitized = error_msg
    if candidate_credentials:
        for key, val in candidate_credentials.items():
            if val and isinstance(val, str) and len(val.strip()) > 3:
                sanitized = sanitized.replace(val.strip(), f"<{key.upper()}_REDACTED>")

    # Redact any obvious Bearer tokens or secret assignments
    import re
    sanitized = re.sub(r"Bearer\s+[A-Za-z0-9\-_.]+", "Bearer [REDACTED]", sanitized)
    sanitized = re.sub(r"(client_secret|api_key|password|secret)=([^\s&,]+)", r"\1=[REDACTED]", sanitized, flags=re.IGNORECASE)

    return sanitized
