#!/bin/bash
# Run Standalone Tests
# This script runs all standalone tests (tests that don't require external dependencies)
# and generates coverage reports.

# Ensure we're in the backend directory
cd "$(dirname "$0")"

# Set environment variables
export TESTING=1
export TEST_TYPE=unit

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found at $(pwd)/venv"
    echo "Please create a virtual environment first using: python -m venv venv"
    exit 1
fi

# Parse arguments
VERBOSE=""
XML=""
HTML=""
CI=""

while [[ $# -gt 0 ]]; do
  case $1 in
    -v|--verbose)
      VERBOSE="--verbose"
      shift
      ;;
    --xml)
      XML="--xml"
      shift
      ;;
    --html)
      HTML="--html"
      shift
      ;;
    --ci)
      CI="--ci"
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: ./run-standalone-tests.sh [--verbose|-v] [--xml] [--html] [--ci]"
      exit 1
      ;;
  esac
done

# Ensure the test results directory exists
mkdir -p test-results

# Make the Python script executable if it isn't already
chmod +x scripts/run_standalone_tests.py

# Use the Python from the virtual environment
VENV_PYTHON="$(pwd)/venv/bin/python"

# Run the Python script with the given arguments
$VENV_PYTHON scripts/run_standalone_tests.py $VERBOSE $XML $HTML $CI

# Store the exit code
EXIT_CODE=$?

# Output a summary message
if [ $EXIT_CODE -eq 0 ]; then
  echo -e "\n\033[32m✅ All standalone tests passed!\033[0m"
  echo "Coverage reports are available in the coverage_html directory (if --html was specified)"
else
  echo -e "\n\033[31m❌ Some standalone tests failed!\033[0m"
  echo "See the output above for details"
fi

exit $EXIT_CODE