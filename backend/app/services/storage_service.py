"""
backend/app/services/storage_service.py

Object storage integration wrapping Supabase Storage (S3-compatible API).
Supports local temporary fallback when S3 credentials are not configured.
"""

from io import BytesIO
import os
from typing import Optional
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import settings


class StorageService:
    """Provides file upload, retrieval, and URL generation for corpus documents."""

    def __init__(self):
        self.endpoint = settings.S3_ENDPOINT
        self.access_key = settings.S3_ACCESS_KEY
        self.secret_key = settings.S3_SECRET_KEY
        self.bucket_name = settings.S3_BUCKET
        self.region = settings.S3_REGION

        self.is_configured = bool(
            self.access_key
            and self.secret_key
            and not self.access_key.startswith("[YOUR-")
            and not self.secret_key.startswith("[YOUR-")
        )

        if self.is_configured:
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                config=Config(signature_version="s3v4"),
            )
        else:
            self.s3_client = None

    def upload_file(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/pdf",
    ) -> str:
        """Uploads file bytes and returns storage key."""
        if not self.is_configured or not self.s3_client:
            # Dev mock fallback
            return f"mock_storage://{self.bucket_name}/{key}"

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            return key
        except ClientError as e:
            raise RuntimeError(f"Storage upload failed: {str(e)}") from e

    def download_file(self, key: str) -> bytes:
        """Downloads file bytes given a storage key."""
        if not self.is_configured or not self.s3_client:
            return b"mock file content for development"

        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read()
        except ClientError as e:
            raise RuntimeError(f"Storage download failed: {str(e)}") from e

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Generates a secure presigned download URL."""
        if not self.is_configured or not self.s3_client:
            return f"https://mock-storage.supabase.co/documents/{key}"

        try:
            return self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )
        except ClientError as e:
            raise RuntimeError(f"Presigned URL generation failed: {str(e)}") from e
