from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.db.models import Base

async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_tables_on_startup():
    async with async_engine.begin() as conn:

        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector;'))

        await conn.run_sync(Base.metadata.create_all)

    print(
        'Database tables created and '
        'pgvector extension enabled successfully.',
    )


async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
