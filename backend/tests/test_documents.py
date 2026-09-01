"""
backend/tests/test_documents.py

Integration tests for Document metadata CRUD, versions, and ingestion triggering.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.database import get_db
from app.main import app
from app.models.base import Base
from app.services.storage_service import StorageService


@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    yield async_session

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_documents_crud_and_ingestion_flow(test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register Admin & Normal User
        await client.post(
            "/api/v1/auth/register",
            json={"name": "Admin", "email": "admin@ayush.in", "password": "AdminPassword123!", "role": "ADMIN"},
        )
        login_admin = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@ayush.in", "password": "AdminPassword123!"},
        )
        admin_token = login_admin.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        await client.post(
            "/api/v1/auth/register",
            json={"name": "User", "email": "user@ayurveda.in", "password": "UserPassword123!", "role": "USER"},
        )
        login_user = await client.post(
            "/api/v1/auth/login",
            json={"email": "user@ayurveda.in", "password": "UserPassword123!"},
        )
        user_token = login_user.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # 1. Normal user blocked from creating document -> 403 Forbidden
        doc_payload = {
            "title": "The Patents Act, 1970",
            "jurisdiction": "INDIA",
            "document_type": "STATUTE",
            "authority": "IP India",
            "language": "en",
            "source_url": "https://wipolex.wipo.int/en/legislation/details/2143",
            "description": "Statutory basis for Section 3(p) TK exclusions",
        }
        res_block = await client.post("/api/v1/documents", headers=user_headers, json=doc_payload)
        assert res_block.status_code == 403

        # 2. Admin creates document -> 201 Created
        res_create = await client.post("/api/v1/documents", headers=admin_headers, json=doc_payload)
        assert res_create.status_code == 201
        doc_data = res_create.json()
        doc_id = doc_data["id"]
        assert doc_data["title"] == "The Patents Act, 1970"
        assert len(doc_data["versions"]) == 1

        # 3. List documents -> 200 OK
        res_list = await client.get("/api/v1/documents")
        assert res_list.status_code == 200
        assert res_list.json()["total"] == 1

        # 4. Add new version to document -> 201 Created
        ver_payload = {
            "version_label": "2024 Amendment",
            "object_storage_key": "patents_act_1970_2024.pdf",
            "is_current": True,
        }
        res_ver = await client.post(f"/api/v1/documents/{doc_id}/versions", headers=admin_headers, json=ver_payload)
        assert res_ver.status_code == 201
        assert res_ver.json()["version_label"] == "2024 Amendment"

        # 5. Trigger ingestion -> 202 Accepted
        res_ingest = await client.post(f"/api/v1/documents/{doc_id}/ingest", headers=admin_headers)
        assert res_ingest.status_code == 202
        ingest_data = res_ingest.json()
        assert ingest_data["status"] == "PROCESSING"
        assert "Ingestion triggered" in ingest_data["message"]


def test_storage_service_mock_fallback():
    storage = StorageService()
    key = storage.upload_file("test.pdf", b"test data")
    assert "test.pdf" in key
    url = storage.get_presigned_url("test.pdf")
    assert "test.pdf" in url
    content = storage.download_file("test.pdf")
    assert len(content) > 0
