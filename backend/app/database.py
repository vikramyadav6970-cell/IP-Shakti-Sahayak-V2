"""
backend/app/database.py

Async SQLAlchemy database session management.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Format connection URL for asyncpg if postgresql://
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

connect_args = {}
engine_kwargs = {
    "echo": False,
    "future": True,
}

if db_url.startswith("postgresql"):
    connect_args = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "timeout": 30,
        "command_timeout": 30,
        "server_settings": {
            "tcp_keepalives_idle": "60",
            "tcp_keepalives_interval": "10",
            "tcp_keepalives_count": "5",
        },
    }
    engine_kwargs.update({
        "pool_size": 5,
        "max_overflow": 10,
        "pool_recycle": 60,
        "pool_timeout": 30,
        "pool_pre_ping": True,
        "connect_args": connect_args,
    })

engine = create_async_engine(db_url, **engine_kwargs)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for yielding transactional async DB sessions."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
