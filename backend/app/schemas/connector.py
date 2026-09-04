"""
backend/app/schemas/connector.py

Pydantic schemas for User-Managed External Connector Credentials (BYOK).
Ensures clear request/response models and guarantees write-only security for secrets.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConnectorFieldSchema(BaseModel):
    """Specification of an input credential field required by a connector."""
    name: str
    label: str
    field_type: str = "text"
    placeholder: str = ""
    required: bool = True
    help_text: str = ""


class ConnectorInfoResponse(BaseModel):
    """Metadata and user connection state for an external connector."""
    name: str
    display_name: str
    description: str
    requires_api_key: bool
    is_paid: bool
    rate_limit_per_minute: int = 30
    credential_fields: List[ConnectorFieldSchema] = []
    is_connected: bool = False
    status: str = "disconnected"  # "connected" | "error" | "disconnected"
    last_tested_at: Optional[datetime] = None
    last_error_code: Optional[str] = None
    last_error_message: Optional[str] = None


class ConnectorTestRequest(BaseModel):
    """Request payload to test candidate connector credentials without saving."""
    credentials: Dict[str, str] = Field(default_factory=dict)


class ConnectorTestResponse(BaseModel):
    """Structured response from testing connector credentials."""
    success: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class ConnectorConnectRequest(BaseModel):
    """Request payload to encrypt and save verified connector credentials."""
    credentials: Dict[str, str] = Field(..., description="Validated key-value credential map")


class ConnectorStatusResponse(BaseModel):
    """Response returned upon saving, disconnecting, or retesting a connector."""
    connector_name: str
    status: str
    last_tested_at: Optional[datetime] = None
    message: str
