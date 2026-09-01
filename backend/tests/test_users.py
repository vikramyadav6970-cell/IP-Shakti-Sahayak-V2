"""
backend/tests/test_users.py

Tests for user management endpoints and RBAC authorization.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.database import get_db
from app.main import app
from app.models.base import Base


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
async def test_rbac_user_vs_admin_access(test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register normal user
        await client.post(
            "/api/v1/auth/register",
            json={
                "name": "Standard Entrepreneur",
                "email": "user@ayurveda.in",
                "password": "Password123!",
                "role": "USER",
            },
        )
        login_user = await client.post(
            "/api/v1/auth/login",
            json={"email": "user@ayurveda.in", "password": "Password123!"},
        )
        user_token = login_user.json()["access_token"]

        # Register admin user
        await client.post(
            "/api/v1/auth/register",
            json={
                "name": "Admin Officer",
                "email": "admin@ayush.gov.in",
                "password": "AdminPassword123!",
                "role": "ADMIN",
            },
        )
        login_admin = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@ayush.gov.in", "password": "AdminPassword123!"},
        )
        admin_token = login_admin.json()["access_token"]

        # 1. Normal user tries to list all users -> 403 Forbidden
        user_headers = {"Authorization": f"Bearer {user_token}"}
        res_forbidden = await client.get("/api/v1/users", headers=user_headers)
        assert res_forbidden.status_code == 403

        # 2. Admin lists all users -> 200 OK
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        res_admin = await client.get("/api/v1/users", headers=admin_headers)
        assert res_admin.status_code == 200
        data = res_admin.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

        # 3. User updates their own profile
        res_update = await client.patch(
            "/api/v1/users/me",
            headers=user_headers,
            json={"organization": "Himalaya Herbal Labs"},
        )
        assert res_update.status_code == 200
        assert res_update.json()["organization"] == "Himalaya Herbal Labs"
