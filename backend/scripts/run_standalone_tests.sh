#!/bin/bash
#
# Script to run standalone tests for Novamind Digital Twin
# These tests run without any external dependencies like databases or network services
#

set -e  # Exit immediately if a command exits with a non-zero status

# Set base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Base directory: $BASE_DIR"

# Ensure we're using the correct Python environment
echo "Setting up environment..."
export PYTHONPATH="$BASE_DIR"
export TESTING=1
export TEST_TYPE=standalone

# Run the standalone tests with proper markers
echo "Running standalone tests..."
python -m pytest "$BASE_DIR/app/tests/standalone/" \
  -v \
  --no-header \
  --strict-markers \
  --cov="$BASE_DIR/app" \
  --cov-report=term \
  --cov-report=xml:"$BASE_DIR/test-results/standalone-coverage.xml" \
  --junitxml="$BASE_DIR/test-results/standalone-results.xml" \
  "$@"  # Pass any additional arguments to pytest

# Check if the tests passed
if [ $? -eq 0 ]; then
  echo -e "\n✅ All standalone tests passed!"
  echo "Coverage report generated in $BASE_DIR/test-results/standalone-coverage.xml"
  echo "Test results saved to $BASE_DIR/test-results/standalone-results.xml"
else
  echo -e "\n❌ Some standalone tests failed! Check the output above for details."
  exit 1
fi