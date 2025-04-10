#!/usr/bin/env python
"""
Setup script for venv_only tests in Novamind Digital Twin.

This script creates the necessary directory structure and configuration files for 
running tests that require only a Python virtual environment but no external services.

These tests are the next tier after standalone tests, allowing for:
- Tests that use third-party packages (like pandas, numpy, etc.)
- Tests with more complex dependencies that can still run in isolation
- Tests that access the filesystem but don't need a database or network
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime


def create_directory(path):
    """Create a directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"✅ Created directory: {path}")
    else:
        print(f"ℹ️ Directory already exists: {path}")


def write_file(path, content):
    """Write content to a file."""
    with open(path, 'w') as f:
        f.write(content)
    print(f"✅ Created file: {path}")


def main():
    # Get the base directory (backend/)
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(script_dir)

    # Define paths
    venv_tests_dir = os.path.join(base_dir, "app", "tests", "venv_only")
    
    # Create directory structure
    create_directory(venv_tests_dir)
    
    # Create conftest.py for venv_only tests
    conftest_content = '''"""
Configuration for venv_only tests.

These tests require Python packages but no external services like databases or APIs.
They sit between standalone tests (no dependencies) and integration tests (external services).
"""

import os
import sys
import pytest
from unittest.mock import MagicMock

def pytest_configure(config):
    """Configure pytest environment for venv_only tests."""
    # Ensure we're running in test mode
    os.environ["TESTING"] = "1"
    os.environ["TEST_TYPE"] = "venv_only"
    
    # Add backend to path if not already there
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

@pytest.fixture
def mock_db_session():
    """Mock database session that prevents actual database operations."""
    session = MagicMock()
    session.query.return_value = session
    session.filter.return_value = session
    session.filter_by.return_value = session
    session.all.return_value = []
    session.first.return_value = None
    session.add.return_value = None
    session.commit.return_value = None
    session.close.return_value = None
    return session

@pytest.fixture(autouse=True)
def no_database_access():
    """Prevent actual database connections."""
    import sqlalchemy
    original_create_engine = sqlalchemy.create_engine
    
    def mock_create_engine(*args, **kwargs):
        raise RuntimeError("Database connections are not allowed in venv_only tests")
    
    sqlalchemy.create_engine = mock_create_engine
    yield
    sqlalchemy.create_engine = original_create_engine

@pytest.fixture(autouse=True)
def no_network_access():
    """Prevent actual network requests."""
    import socket
    original_socket = socket.socket
    
    def mock_socket(*args, **kwargs):
        mock = MagicMock()
        mock.connect = lambda *_, **__: exec('raise RuntimeError("Network connections are not allowed in venv_only tests")')
        return mock
    
    socket.socket = mock_socket
    yield
    socket.socket = original_socket
'''
    
    write_file(os.path.join(venv_tests_dir, "__init__.py"), '''"""
venv_only Tests Package for Novamind Digital Twin Platform.

This package contains tests that require Python packages but no external services:
- Can use third-party packages (pandas, numpy, etc.)
- Cannot connect to databases
- Cannot make network requests
- Can access the filesystem

These tests are run after standalone tests but before integration tests.
"""''')
    
    write_file(os.path.join(venv_tests_dir, "conftest.py"), conftest_content)
    
    # Create a sample test file
    sample_test = '''"""
Sample venv_only test that demonstrates using third-party packages without external services.

This test uses pandas for data processing but doesn't connect to any external services.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

@pytest.mark.venv_only
def test_pandas_processing():
    """Test that pandas can be used for data processing in venv_only tests."""
    # Create a sample DataFrame
    dates = pd.date_range(datetime.now() - timedelta(days=10), periods=10, freq='D')
    df = pd.DataFrame({
        'date': dates,
        'value': np.random.randn(10)
    })
    
    # Perform some operations
    df['rolling_mean'] = df['value'].rolling(window=3).mean()
    df['cumulative_sum'] = df['value'].cumsum()
    
    # Verify results
    assert len(df) == 10
    assert 'rolling_mean' in df.columns
    assert 'cumulative_sum' in df.columns
    assert pd.isna(df['rolling_mean'].iloc[0])
    assert pd.isna(df['rolling_mean'].iloc[1])
    assert not pd.isna(df['rolling_mean'].iloc[2])
'''
    
    write_file(os.path.join(venv_tests_dir, "test_sample_venv.py"), sample_test)
    
    # Create a script to run the venv_only tests
    run_script = '''#!/bin/bash
#
# Script to run venv_only tests for Novamind Digital Twin
# These tests require Python packages but no external services
#

set -e  # Exit immediately if a command exits with a non-zero status

# Set base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Base directory: $BASE_DIR"

# Ensure we're using the correct Python environment
echo "Setting up environment..."
export PYTHONPATH="$BASE_DIR"
export TESTING=1
export TEST_TYPE=venv_only

# Run the venv_only tests with proper markers
echo "Running venv_only tests..."
python -m pytest "$BASE_DIR/app/tests/venv_only/" \
  -v \
  --strict-markers \
  --cov="$BASE_DIR/app" \
  --cov-report=term \
  --cov-report=xml:"$BASE_DIR/test-results/venv_only-coverage.xml" \
  --junitxml="$BASE_DIR/test-results/venv_only-results.xml" \
  "$@"  # Pass any additional arguments to pytest

# Check if the tests passed
if [ $? -eq 0 ]; then
  echo -e "\\n✅ All venv_only tests passed!"
  echo "Coverage report generated in $BASE_DIR/test-results/venv_only-coverage.xml"
  echo "Test results saved to $BASE_DIR/test-results/venv_only-results.xml"
else
  echo -e "\\n❌ Some venv_only tests failed! Check the output above for details."
  exit 1
fi
'''
    
    run_script_path = os.path.join(base_dir, "scripts", "run_venv_tests.sh")
    write_file(run_script_path, run_script)
    os.chmod(run_script_path, 0o755)  # Make executable
    
    print("\n✅ Successfully set up venv_only test infrastructure!")
    print(f"  - Created directory: {venv_tests_dir}")
    print(f"  - Created conftest.py with test isolation")
    print(f"  - Added sample test: test_sample_venv.py")
    print(f"  - Created run script: scripts/run_venv_tests.sh")
    print("\nNext steps:")
    print("1. Add more venv_only tests that use third-party packages")
    print("2. Run the tests with: ./scripts/run_venv_tests.sh")


if __name__ == "__main__":
    main()