"""
backend/app/api/v1/connectors.py

REST API endpoints for User-Managed External Connector Credentials (BYOK).
Provides full lifecycle management: test, connect (encrypt at rest), retest,
and delete with structured error classification and zero secret leakage.
"""

from collections import defaultdict
from datetime import datetime, timezone
import logging
import time
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_credentials, encrypt_credentials, sanitize_error_message
from app.database import get_db
from app.models.entities import AuditLog, User, UserExternalConnection
from app.schemas.connector import (
    ConnectorConnectRequest,
    ConnectorFieldSchema,
    ConnectorInfoResponse,
    ConnectorStatusResponse,
    ConnectorTestRequest,
    ConnectorTestResponse,
)
from app.security.dependencies import get_current_user

# Import connector registry and all concrete connectors
from src.connectors import (
    ConnectorErrorCode,
    ConnectorTestResult,
    connector_registry,
    wipo_connector,
    wipo_pearl_connector,
    ncbi_pubmed_connector,
)

logger = logging.getLogger("ipsakti.api.connectors")

router = APIRouter(prefix="/connectors", tags=["External Connectors & BYOK"])


class UserEndpointThrottler:
    """
    Sliding window per-user throttler for sensitive test/connect endpoints.
    Protects against candidate credential brute-forcing, enumeration, and provider API abuse.
    """
    def __init__(self, max_requests_per_minute: int = 10):
        self.max_requests = max_requests_per_minute
        self._history = defaultdict(list)

    def check_rate_limit(self, user_id: str) -> None:
        now = time.time()
        window_start = now - 60.0
        # Filter timestamps within the last 60 seconds
        timestamps = [t for t in self._history[user_id] if t > window_start]
        self._history[user_id] = timestamps

        if len(timestamps) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many credential test attempts. Please wait a minute before trying again.",
                headers={"Retry-After": "60"},
            )
        self._history[user_id].append(now)


# Global throttler: max 10 candidate credential tests/connections per user per minute
connector_test_throttler = UserEndpointThrottler(max_requests_per_minute=10)


@router.get(
    "",
    response_model=List[ConnectorInfoResponse],
    summary="List all external connectors and current user connection status",
)
async def list_connectors(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all registered external source connectors, their required credential fields schema,
    and the authenticated user's current connection status.
    Write-only guarantee: Never returns decrypted credential values.
    """
    # Fetch all user connections for this user
    stmt = select(UserExternalConnection).where(UserExternalConnection.user_id == current_user.id)
    res = await db.execute(stmt)
    user_conns = {c.connector_name: c for c in res.scalars().all()}

    all_connectors = connector_registry.list_all()
    response_list: List[ConnectorInfoResponse] = []

    for conn in all_connectors:
        user_c = user_conns.get(conn.name)
        fields = [
            ConnectorFieldSchema(
                name=f.name,
                label=f.label,
                field_type=f.field_type,
                placeholder=f.placeholder,
                required=f.required,
                help_text=f.help_text,
            )
            for f in conn.credential_fields
        ]

        if conn.requires_api_key:
            is_conn = user_c is not None and user_c.status == "connected"
            conn_status = user_c.status if user_c else "disconnected"
        else:
            is_conn = user_c.status == "connected" if user_c else True
            conn_status = user_c.status if user_c else "connected"

        last_tested = user_c.last_tested_at if user_c else None
        last_err_code = user_c.last_error_code if user_c else None
        last_err_msg = user_c.last_error_message if user_c else None

        response_list.append(
            ConnectorInfoResponse(
                name=conn.name,
                display_name=conn.display_name,
                description=conn.description or f"{conn.display_name} external data integration.",
                requires_api_key=conn.requires_api_key,
                is_paid=conn.is_paid,
                rate_limit_per_minute=conn.rate_limit_per_minute or 30,
                credential_fields=fields,
                is_connected=is_conn,
                status=conn_status,
                last_tested_at=last_tested,
                last_error_code=last_err_code,
                last_error_message=last_err_msg,
            )
        )

    return response_list


@router.post(
    "/{connector_name}/test",
    response_model=ConnectorTestResponse,
    summary="Test candidate connector credentials without persisting",
)
async def test_connector_credentials(
    connector_name: str,
    req: ConnectorTestRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Executes a lightweight authentication test against the external provider.
    Returns structured error codes (AUTH_FAILED, NETWORK_TIMEOUT, etc.).
    Guarantees credentials are NOT saved on test failure.
    """
    connector = connector_registry.get(connector_name)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"External connector '{connector_name}' is not registered.",
        )

    # Enforce per-user throttle to prevent brute-force / high-frequency testing abuse
    connector_test_throttler.check_rate_limit(str(current_user.id))

    test_result: ConnectorTestResult = await connector.test_connection(req.credentials)
    safe_error_msg = sanitize_error_message(test_result.error_message or "", req.credentials)

    return ConnectorTestResponse(
        success=test_result.success,
        error_code=test_result.error_code.value if test_result.error_code else None,
        error_message=safe_error_msg if not test_result.success else None,
    )


@router.post(
    "/{connector_name}/connect",
    response_model=ConnectorStatusResponse,
    summary="Encrypt and persist verified connector credentials",
)
async def connect_connector(
    connector_name: str,
    req: ConnectorConnectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Validates, encrypts at rest, and saves credentials for the authenticated user.
    Records connection action in DPDP-compliant AuditLog.
    """
    connector = connector_registry.get(connector_name)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"External connector '{connector_name}' is not registered.",
        )

    # Enforce per-user throttle
    connector_test_throttler.check_rate_limit(str(current_user.id))

    # 1. Execute live credential test (pass empty dict for public connectors if credentials not supplied)
    creds = req.credentials or {}
    test_result: ConnectorTestResult = await connector.test_connection(creds)
    now = datetime.now(timezone.utc)

    if not test_result.success:
        safe_error_msg = sanitize_error_message(test_result.error_message or "", creds)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Connection test failed. Credentials were not saved.",
                "error_code": test_result.error_code.value if test_result.error_code else "UNKNOWN",
                "error_message": safe_error_msg,
            },
        )

    # 2. Encrypt credentials at rest using Fernet (empty bytes if public connector)
    encrypted_blob = encrypt_credentials(creds) if creds else b""

    # 3. Upsert user_external_connections row
    stmt = select(UserExternalConnection).where(
        UserExternalConnection.user_id == current_user.id,
        UserExternalConnection.connector_name == connector_name,
    )
    res = await db.execute(stmt)
    existing_conn = res.scalar_one_or_none()

    if existing_conn:
        existing_conn.encrypted_credentials = encrypted_blob
        existing_conn.status = "connected"
        existing_conn.last_tested_at = now
        existing_conn.last_error_code = None
        existing_conn.last_error_message = None
        existing_conn.updated_at = now
    else:
        new_conn = UserExternalConnection(
            user_id=current_user.id,
            connector_name=connector_name,
            encrypted_credentials=encrypted_blob,
            status="connected",
            last_tested_at=now,
            last_error_code=None,
            last_error_message=None,
        )
        db.add(new_conn)

    # 4. Append AuditLog event (NEVER include raw credential values)
    audit = AuditLog(
        user_id=current_user.id,
        action="CONNECTOR_CONNECTED",
        resource_type="EXTERNAL_CONNECTOR",
        resource_id=connector_name,
        metadata_json={
            "connector_name": connector_name,
            "display_name": connector.display_name,
            "connected_at": now.isoformat(),
        },
    )
    db.add(audit)
    await db.commit()

    logger.info(f"User {current_user.id} successfully connected {connector_name}")

    return ConnectorStatusResponse(
        connector_name=connector_name,
        status="connected",
        last_tested_at=now,
        message=f"Successfully connected to {connector.display_name}.",
    )


@router.delete(
    "/{connector_name}",
    response_model=ConnectorStatusResponse,
    summary="Disconnect and hard-delete stored connector credentials",
)
async def disconnect_connector(
    connector_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Hard-deletes the encrypted credentials row for BYOK connectors or sets status to disconnected.
    Records disconnection event in AuditLog.
    """
    connector = connector_registry.get(connector_name)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"External connector '{connector_name}' is not registered.",
        )

    stmt = select(UserExternalConnection).where(
        UserExternalConnection.user_id == current_user.id,
        UserExternalConnection.connector_name == connector_name,
    )
    res = await db.execute(stmt)
    existing_conn = res.scalar_one_or_none()

    if existing_conn:
        if connector.requires_api_key:
            await db.delete(existing_conn)
        else:
            existing_conn.status = "disconnected"
            existing_conn.updated_at = datetime.now(timezone.utc)
    else:
        if connector.requires_api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active connection found for '{connector_name}'.",
            )
        else:
            disconn_conn = UserExternalConnection(
                user_id=current_user.id,
                connector_name=connector_name,
                encrypted_credentials=b"",
                status="disconnected",
            )
            db.add(disconn_conn)

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="CONNECTOR_DISCONNECTED",
        resource_type="EXTERNAL_CONNECTOR",
        resource_id=connector_name,
        metadata_json={
            "connector_name": connector_name,
            "disconnected_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    db.add(audit)
    await db.commit()

    logger.info(f"User {current_user.id} disconnected connector {connector_name}")

    return ConnectorStatusResponse(
        connector_name=connector_name,
        status="disconnected",
        last_tested_at=None,
        message=f"Disconnected from {connector.display_name}.",
    )


@router.post(
    "/{connector_name}/retest",
    response_model=ConnectorTestResponse,
    summary="Retest connection using stored encrypted credentials",
)
async def retest_connector(
    connector_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves and decrypts stored credentials in memory, executes auth check,
    and updates the connection status (connected / error) accordingly.
    """
    connector = connector_registry.get(connector_name)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"External connector '{connector_name}' is not registered.",
        )

    # Enforce per-user throttle to protect against spamming /retest against live providers
    connector_test_throttler.check_rate_limit(str(current_user.id))

    if not connector.requires_api_key:
        test_result: ConnectorTestResult = await connector.test_connection({})
        now = datetime.now(timezone.utc)
        stmt = select(UserExternalConnection).where(
            UserExternalConnection.user_id == current_user.id,
            UserExternalConnection.connector_name == connector_name,
        )
        res = await db.execute(stmt)
        conn_row = res.scalar_one_or_none()
        if conn_row:
            conn_row.last_tested_at = now
            conn_row.status = "connected" if test_result.success else "error"
            await db.commit()
        return ConnectorTestResponse(
            success=test_result.success,
            error_code=test_result.error_code.value if test_result.error_code else None,
            error_message=test_result.error_message,
        )

    stmt = select(UserExternalConnection).where(
        UserExternalConnection.user_id == current_user.id,
        UserExternalConnection.connector_name == connector_name,
    )
    res = await db.execute(stmt)
    conn_row = res.scalar_one_or_none()

    if not conn_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No stored credentials found for '{connector_name}'. Please connect first.",
        )

    # Decrypt credentials in-memory for testing
    decrypted_creds = decrypt_credentials(conn_row.encrypted_credentials)
    if not decrypted_creds:
        conn_row.status = "error"
        conn_row.last_error_code = ConnectorErrorCode.AUTH_FAILED.value
        conn_row.last_error_message = "Decryption failed. Please re-enter your credentials."
        conn_row.last_tested_at = datetime.now(timezone.utc)
        await db.commit()
        return ConnectorTestResponse(
            success=False,
            error_code=ConnectorErrorCode.AUTH_FAILED.value,
            error_message="Stored credentials could not be decrypted. Please reconnect.",
        )

    test_result: ConnectorTestResult = await connector.test_connection(decrypted_creds)
    now = datetime.now(timezone.utc)
    safe_error_msg = sanitize_error_message(test_result.error_message or "", decrypted_creds)

    conn_row.last_tested_at = now
    if test_result.success:
        conn_row.status = "connected"
        conn_row.last_error_code = None
        conn_row.last_error_message = None
    else:
        conn_row.status = "error"
        conn_row.last_error_code = test_result.error_code.value if test_result.error_code else "UNKNOWN"
        conn_row.last_error_message = safe_error_msg

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="CONNECTOR_RETESTED",
        resource_type="EXTERNAL_CONNECTOR",
        resource_id=connector_name,
        metadata_json={
            "connector_name": connector_name,
            "success": test_result.success,
            "error_code": test_result.error_code.value if test_result.error_code else None,
            "retested_at": now.isoformat(),
        },
    )
    db.add(audit)
    await db.commit()

    return ConnectorTestResponse(
        success=test_result.success,
        error_code=test_result.error_code.value if test_result.error_code else None,
        error_message=safe_error_msg if not test_result.success else None,
    )
