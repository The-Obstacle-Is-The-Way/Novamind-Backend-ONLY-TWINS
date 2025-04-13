"""
Tests for the database utilities.

This module tests the database connection utilities for SQLAlchemy.
"""
import pytest
import os
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import engine, init_db, get_session, Base


@pytest.mark.asyncio()
@pytest.mark.db_required()
async def test_engine_creation():
             """Test that the database engine is created with correct settings."""
    # Verify the engine is correctly configured for testing
    assert engine is not None
    assert engine.dialect.name in ["sqlite", "postgresql"]

    # Check test mode settings
    assert os.environ.get("TESTING") == "1"

    # Ensure URL has async driver
    if engine.dialect.name == "sqlite":
        assert "sqlite+aiosqlite" in str(engine.url)
        elif engine.dialect.name == "postgresql":
            assert "postgresql+asyncpg" in str(engine.url)

            @pytest.mark.asyncio()
            @pytest.mark.db_required()
            async def test_init_db():
                """Test database initialization."""
                # Clear any existing tables
                async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

                # Run initialization
                await init_db()

                # Verify tables were created (check that metadata is bound)
                assert Base.metadata.is_bound()

                # Count tables (should be > 0 if initialization worked,
                table_count= len(Base.metadata.tables)
                assert table_count > 0

                @pytest.mark.asyncio()
                @pytest.mark.db_required()
                async def test_get_session():
             """Test that get_session returns valid sessions."""
            # Test that the session dependency yields an async session
            session_generator = get_session(,
            session= await anext(session_generator)

            try:
                # Verify session properties
                assert isinstance(session, AsyncSession)
                assert not session.expired_transaction

                # Simple query to check session works
                # Just ping the database with a simple SQL expression
                result = await session.execute("SELECT 1",
                row= result.scalar()
                assert row == 1
                finally:
            # Clean up
            try:
                await session.close()
                except Exception:
                pass

                # Exhaust the generator
                try:
                    await anext(session_generator, None)
                    except StopAsyncIteration:
                    passclass TestDatabaseBase:
                    """Test base class for database-related tests."""

                    @pytest.mark.asyncio()
                    @pytest.mark.db_required()
                    async def test_base_class_table_creation(self):
                    """Test that Base can create tables."""
                    # Model definition moved outside the test method
                    # Create just this table
                    async with engine.begin() as conn:
            await conn.run_sync(lambda schema: TestModel.__table__.create(schema, checkfirst=True))

            # Verify the table exists by querying it
            async with AsyncSession(engine) as session:
                result = await session.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_models_temp'",
                table_exists= result.scalar() is not None
                assert table_exists

                # Clean up - drop the table
                async with engine.begin() as conn:
                await conn.run_sync(lambda schema: TestModel.__table__.drop(schema, checkfirst=True))

                # Define TestModel at module level
                from sqlalchemy import Column, String, Integer  # Move import here too
                class TestModel(Base):
            __tablename__ = "test_models_temp"
            id = Column(Integer, primary_key=True,
            name= Column(String, nullable=False)
