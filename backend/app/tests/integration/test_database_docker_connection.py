"""
Test that validates database connectivity in the Docker environment.
This ensures our Docker container tests can properly connect to the database.
"""

import os
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

@pytest.mark.asyncio
async def test_docker_database_connection():
    """Test that the Docker database connection works properly."""
    # Get database URL from environment
    db_url = os.environ.get("TEST_DATABASE_URL")
    
    # If not running in Docker, skip test
    if not db_url:
        pytest.skip("Not running in Docker environment (TEST_DATABASE_URL not set)")
    
    # Create engine with the database URL
    engine = create_async_engine(db_url)
    
    # Try to connect to the database
    try:
        async with engine.connect() as connection:
            # Execute a simple SQL query
            result = await connection.execute(text("SELECT 1"))
            value = result.scalar()
            
            # Check the result
            assert value == 1, f"Expected 1, got {value}"
            print(f"✅ Successfully connected to database at {db_url}")
    except Exception as e:
        pytest.fail(f"Failed to connect to database: {e}")
    finally:
        # Clean up
        await engine.dispose()
