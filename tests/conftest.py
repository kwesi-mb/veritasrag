import os

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings
from app.db.base import Base


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    test_settings = Settings(
        database_url= os.getenv(
            "TEST_DATABASE_URL",
        )
    )

    # Safety quard: never run destructive setup against
    # the development or production database.
    if not test_settings.database_url.endswith("/veritasrag_test"):
        raise RuntimeError("Unsafe integration test database")

    engine = create_async_engine(
        test_settings.database_url,
        pool_pre_ping=True,
    )

    async with engine.begin() as connection:
        await connection.execute(
            text("CREATE EXTENSION IF NOT EXISTS vector")
        )
        await connection.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(test_engine):
    async with test_engine.connect() as connection:
        transaction = await connection.begin()

        session_factory = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False, 
            join_transaction_mode="create_savepoint",
        )

        async with session_factory() as session:
            yield session

        await transaction.rollback()