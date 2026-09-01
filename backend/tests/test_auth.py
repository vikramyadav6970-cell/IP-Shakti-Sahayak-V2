"""
backend/tests/test_auth.py

Integration tests for JWT auth flow, password hashing, and role checks.
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
async def test_auth_register_and_login_flow(test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register a new user
        reg_payload = {
            "name": "Vaidya Rajesh Sharma",
            "email": "rajesh.sharma@ayurveda.org",
            "password": "SecurePassword123!",
            "role": "USER",
            "organization": "All India Institute of Ayurveda",
            "language": "en",
        }
        res_reg = await client.post("/api/v1/auth/register", json=reg_payload)
        assert res_reg.status_code == 201
        data_reg = res_reg.json()
        assert data_reg["email"] == "rajesh.sharma@ayurveda.org"
        assert data_reg["name"] == "Vaidya Rajesh Sharma"
        assert data_reg["role"] == "USER"

        # 2. Duplicate registration rejected
        res_dup = await client.post("/api/v1/auth/register", json=reg_payload)
        assert res_dup.status_code == 409

        # 3. Login with wrong password rejected
        res_wrong_pw = await client.post(
            "/api/v1/auth/login",
            json={"email": "rajesh.sharma@ayurveda.org", "password": "WrongPassword!"},
        )
        assert res_wrong_pw.status_code == 401

        # 4. Successful Login
        res_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "rajesh.sharma@ayurveda.org", "password": "SecurePassword123!"},
        )
        assert res_login.status_code == 200
        token_data = res_login.json()
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert token_data["token_type"] == "bearer"

        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]

        # 5. Access /users/me with token
        headers = {"Authorization": f"Bearer {access_token}"}
        res_me = await client.get("/api/v1/users/me", headers=headers)
        assert res_me.status_code == 200
        assert res_me.json()["email"] == "rajesh.sharma@ayurveda.org"

        # 6. Refresh token flow
        res_refresh = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert res_refresh.status_code == 200
        new_token_data = res_refresh.json()
        assert "access_token" in new_token_data
