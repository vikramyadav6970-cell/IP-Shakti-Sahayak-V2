"""
backend/scripts/migrate_live_db.py

Applies schema updates (adding missing columns to existing tables in Supabase Postgres).
"""

import asyncio
import os
import sys
from pathlib import Path
from sqlalchemy import text

# Ensure backend root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import engine


async def run_migration():
    print("Starting database schema migration...")
    async with engine.begin() as conn:
        print("Checking and adding columns to 'conversations' table...")
        # 1. Add product_context_json to conversations
        await conn.execute(
            text("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS product_context_json JSONB;")
        )
        # 2. Add classification_state to conversations
        await conn.execute(
            text(
                "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS classification_state VARCHAR(50) DEFAULT 'COLLECTING_PRODUCT_INFORMATION';"
            )
        )
        print("Columns successfully added / verified on 'conversations'!")
    print("Migration completed successfully!")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_migration())
