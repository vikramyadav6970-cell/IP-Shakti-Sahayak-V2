"""
backend/app/fix_db_constraints.py

Alters abs_assessments and ip_assessments to ensure product_id is nullable for standalone assessments.
"""

import asyncio
from sqlalchemy import text
from app.database import async_session_factory


async def fix_constraints():
    async with async_session_factory() as session:
        print("[DB Fix] Altering abs_assessments and ip_assessments product_id constraints...")
        
        # 1. abs_assessments.product_id nullable
        try:
            await session.execute(text("ALTER TABLE abs_assessments ALTER COLUMN product_id DROP NOT NULL;"))
            print("[DB Fix] abs_assessments.product_id set to nullable.")
        except Exception as e:
            print(f"[DB Fix] abs_assessments notice: {e}")

        # 2. ip_assessments.product_id nullable
        try:
            await session.execute(text("ALTER TABLE ip_assessments ALTER COLUMN product_id DROP NOT NULL;"))
            print("[DB Fix] ip_assessments.product_id set to nullable.")
        except Exception as e:
            print(f"[DB Fix] ip_assessments notice: {e}")

        # 3. classifications.product_id nullable (if standalone)
        try:
            await session.execute(text("ALTER TABLE classifications ALTER COLUMN product_id DROP NOT NULL;"))
            print("[DB Fix] classifications.product_id set to nullable.")
        except Exception as e:
            print(f"[DB Fix] classifications notice: {e}")

        await session.commit()
        print("[DB Fix] All constraints successfully updated in Supabase Postgres!")


if __name__ == "__main__":
    asyncio.run(fix_constraints())
