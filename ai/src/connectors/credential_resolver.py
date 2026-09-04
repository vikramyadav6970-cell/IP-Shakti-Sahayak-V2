"""
ai/src/connectors/credential_resolver.py

Per-user external connector credential resolution.
Fetches and decrypts user-specific credentials at execution time, enabling
Bring-Your-Own-Keys (BYOK) for paid and external IP registries without leaking
plaintext secrets into logs or client responses.
"""

import logging
from typing import Any, Dict, Optional
import uuid

logger = logging.getLogger("ipsakti.connectors.resolver")


async def resolve_credentials(
    user_id: Optional[str | uuid.UUID],
    connector_name: str,
    db: Optional[Any] = None,
) -> Optional[Dict[str, Any]]:
    """
    Returns decrypted per-user credentials if the user has an active connection
    for the specified connector.
    Returns None if:
      - No user is authenticated (anonymous session)
      - User has not configured credentials for this connector
      - Connection is in 'error' or 'disconnected' state
      - Database is unavailable
    """
    if not user_id or not connector_name:
        return None

    # Lazy import of encryption to avoid circular dependencies
    try:
        from app.core.encryption import decrypt_credentials
        from app.models.entities import UserExternalConnection
        from sqlalchemy import select
    except ImportError:
        try:
            # Fallback for running within ai subsystem directly
            import sys
            from pathlib import Path
            backend_dir = str(Path(__file__).resolve().parent.parent.parent.parent / "backend")
            if backend_dir not in sys.path:
                sys.path.insert(0, backend_dir)
            from app.core.encryption import decrypt_credentials
            from app.models.entities import UserExternalConnection
            from sqlalchemy import select
        except Exception as exc:
            logger.warning(f"Could not import database models for credential resolution: {exc}")
            return None

    if db is None:
        return None

    try:
        # Convert string to UUID if valid UUID
        try:
            uid = uuid.UUID(str(user_id)) if isinstance(user_id, (str, uuid.UUID)) else user_id
        except Exception:
            uid = user_id

        conn_row = None
        # Check if db is async session
        if hasattr(db, "execute"):
            stmt = select(UserExternalConnection).where(
                UserExternalConnection.user_id == uid,
                UserExternalConnection.connector_name == connector_name,
            )
            import inspect
            exec_res = db.execute(stmt)
            if inspect.isawaitable(exec_res):
                exec_res = await exec_res
            conn_row = exec_res.scalar_one_or_none() if hasattr(exec_res, "scalar_one_or_none") else None
        elif hasattr(db, "query"):
            conn_row = db.query(UserExternalConnection).filter(
                UserExternalConnection.user_id == uid,
                UserExternalConnection.connector_name == connector_name,
            ).first()

        if not conn_row:
            return None

        if conn_row.status != "connected":
            logger.info(f"User {uid} has connection for {connector_name} but status is '{conn_row.status}'")
            return None

        decrypted = decrypt_credentials(conn_row.encrypted_credentials)
        if decrypted:
            logger.info(f"Successfully resolved per-user credentials for connector '{connector_name}' (User: {uid})")
            return decrypted

    except Exception as exc:
        logger.warning(f"Error resolving credentials for {connector_name}: {exc}")

    return None


async def get_user_connector_status(
    user_id: Optional[str | uuid.UUID],
    connector_name: str,
    db: Optional[Any] = None,
) -> Optional[str]:
    """
    Returns the user's connection status string ('connected', 'disconnected', 'error')
    or None if no specific configuration row exists.
    """
    if not user_id or not connector_name or db is None:
        return None

    try:
        from app.models.entities import UserExternalConnection
        from sqlalchemy import select
    except ImportError:
        try:
            import sys
            from pathlib import Path
            backend_dir = str(Path(__file__).resolve().parent.parent.parent.parent / "backend")
            if backend_dir not in sys.path:
                sys.path.insert(0, backend_dir)
            from app.models.entities import UserExternalConnection
            from sqlalchemy import select
        except Exception:
            return None

    try:
        uid = uuid.UUID(str(user_id)) if isinstance(user_id, (str, uuid.UUID)) else user_id
        if hasattr(db, "execute"):
            stmt = select(UserExternalConnection.status).where(
                UserExternalConnection.user_id == uid,
                UserExternalConnection.connector_name == connector_name,
            )
            import inspect
            exec_res = db.execute(stmt)
            if inspect.isawaitable(exec_res):
                exec_res = await exec_res
            return exec_res.scalar_one_or_none() if hasattr(exec_res, "scalar_one_or_none") else None
        elif hasattr(db, "query"):
            row = db.query(UserExternalConnection).filter(
                UserExternalConnection.user_id == uid,
                UserExternalConnection.connector_name == connector_name,
            ).first()
            return row.status if row else None
    except Exception as exc:
        logger.warning(f"Error checking user connection status for {connector_name}: {exc}")

    return None
