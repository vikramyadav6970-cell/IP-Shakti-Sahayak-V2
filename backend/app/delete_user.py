"""
backend/app/delete_user.py

CLI utility to delete an account from the Supabase PostgreSQL database by email.
Usage:
    python -m app.delete_user user@example.com
"""

import sys
import asyncio
from sqlalchemy import select, delete
from app.database import async_session_factory
from app.models.entities import User


async def delete_user_by_email(email: str):
    if not email:
        print("Please provide an email address: python -m app.delete_user <email>")
        return

    email_clean = email.strip().lower()
    async with async_session_factory() as session:
        stmt = select(User).where(User.email == email_clean)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            print(f"[Supabase] User not found with email: {email_clean}")
            return

        user_id = user.id
        user_name = user.name
        user_role = user.role.value if hasattr(user.role, "value") else str(user.role)

        # Delete user (cascades to related conversations and records)
        await session.delete(user)
        await session.commit()
        print(f"[Supabase] Successfully deleted user '{user_name}' ({email_clean}) [Role: {user_role}, ID: {user_id}]")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.delete_user <email>")
    else:
        asyncio.run(delete_user_by_email(sys.argv[1]))
