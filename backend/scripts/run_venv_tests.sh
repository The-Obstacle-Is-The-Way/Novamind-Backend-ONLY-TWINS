#!/bin/bash
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
python -m pytest "$BASE_DIR/app/tests/venv_only/"   -v   --strict-markers   --cov="$BASE_DIR/app"   --cov-report=term   --cov-report=xml:"$BASE_DIR/test-results/venv_only-coverage.xml"   --junitxml="$BASE_DIR/test-results/venv_only-results.xml"   "$@"  # Pass any additional arguments to pytest

# Check if the tests passed
if [ $? -eq 0 ]; then
  echo -e "\n✅ All venv_only tests passed!"
  echo "Coverage report generated in $BASE_DIR/test-results/venv_only-coverage.xml"
  echo "Test results saved to $BASE_DIR/test-results/venv_only-results.xml"
else
  echo -e "\n❌ Some venv_only tests failed! Check the output above for details."
  exit 1
fi
