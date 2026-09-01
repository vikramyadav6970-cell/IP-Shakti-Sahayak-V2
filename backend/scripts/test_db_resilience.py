import asyncio
import os
import sys
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Ensure backend root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings

async def test_db():
    db_url = settings.DATABASE_URL
    if ":5432" in db_url:
        db_url = db_url.replace(":5432", ":6543")
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print(f"Testing connection to: {db_url.split('@')[1] if '@' in db_url else db_url}")
    
    engine = create_async_engine(
        db_url,
        echo=False,
        pool_size=5,
        max_overflow=5,
        pool_recycle=300,
        pool_timeout=30,
        pool_pre_ping=False,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "timeout": 30,
            "command_timeout": 30,
        },
    )

    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1;"))
            print("Query SELECT 1 result:", result.scalar())
            
            # Test multiple concurrent queries on users, conversations, expert_requests
            async def run_query(table):
                async with engine.connect() as c:
                    r = await c.execute(text(f"SELECT count(*) FROM {table};"))
                    return r.scalar()
            
            tables = ["users", "conversations", "expert_requests", "audit_logs", "classifications"] * 10
            results = await asyncio.gather(*[run_query(t) for t in tables])
            print("50 concurrent table count queries executed successfully:", len(results))
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_db())
