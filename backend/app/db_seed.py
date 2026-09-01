"""
backend/app/db_seed.py

Seeds the database with essential administrative and facilitator accounts:
- admin@ayush.gov.in (Role: ADMIN)
- facilitator@ayush.gov.in (Role: IP_FACILITATOR)
"""

import asyncio
import uuid
from app.database import async_session_factory
from app.models.entities import User, RoleEnum
from app.repositories.user_repository import UserRepository
from app.security.auth import get_password_hash

SEED_ACCOUNTS = [
    {
        "name": "Ayush System Administrator",
        "email": "admin@ayush.gov.in",
        "password": "Admin@123",
        "role": RoleEnum.ADMIN,
        "organization": "Ministry of Ayush",
    },
    {
        "name": "Senior IP Facilitator",
        "email": "facilitator@ayush.gov.in",
        "password": "Facilitator@123",
        "role": RoleEnum.IP_FACILITATOR,
        "organization": "Ministry of Ayush",
    },
]


async def seed_users():
    """Ensure standard administrative & facilitator accounts exist in DB."""
    async with async_session_factory() as session:
        user_repo = UserRepository(session)
        created_count = 0
        updated_count = 0

        for item in SEED_ACCOUNTS:
            existing = await user_repo.get_by_email(item["email"])
            if not existing:
                new_user = User(
                    id=uuid.uuid4(),
                    name=item["name"],
                    email=item["email"],
                    hashed_password=get_password_hash(item["password"]),
                    role=item["role"],
                    organization=item["organization"],
                    is_active=True,
                )
                session.add(new_user)
                created_count += 1
                print(f"[Seed] Created {item['role'].value} account: {item['email']}")
            else:
                # Ensure correct role & active status
                existing.role = item["role"]
                existing.is_active = True
                # Reset password to seed standard
                existing.hashed_password = get_password_hash(item["password"])
                updated_count += 1
                print(f"[Seed] Verified/Updated {item['role'].value} account: {item['email']}")

        await session.commit()
        print(f"[Seed] Completed. Created: {created_count}, Updated: {updated_count}")


if __name__ == "__main__":
    asyncio.run(seed_users())
