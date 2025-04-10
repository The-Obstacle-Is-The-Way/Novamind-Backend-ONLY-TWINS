#!/bin/bash
# Enhanced test runner for Novamind Digital Twin Backend
# This script runs various test suites with appropriate settings

set -e

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  Novamind Digital Twin Test Suite      ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Function for running tests
run_test() {
    local name=$1
    local command=$2
    
    echo -e "\n${YELLOW}Running $name tests...${NC}"
    if eval $command; then
        echo -e "${GREEN}✓ $name tests passed!${NC}"
        return 0
    else
        echo -e "${RED}✗ $name tests failed!${NC}"
        return 1
    fi
}

# Install test dependencies if needed
if [[ $1 == "--install" ]]; then
    echo -e "${YELLOW}Installing test dependencies...${NC}"
    pip install -e ".[test,dev]"
    shift
fi

# Set PYTHONPATH to include project root
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Default to running all tests if no arguments given
if [[ $# -eq 0 ]]; then
    set -- "all"
fi

# Process arguments
EXIT_CODE=0

for arg in "$@"; do
    case $arg in
        "core")
            run_test "Core" "python -m pytest app/tests/core -v" || EXIT_CODE=1
            ;;
        "domain")
            run_test "Domain" "python -m pytest app/tests/domain -v" || EXIT_CODE=1
            ;;
        "api")
            run_test "API" "python -m pytest app/tests/api -v" || EXIT_CODE=1
            ;;
        "security")
            run_test "Security" "python -m pytest app/tests/security -v" || EXIT_CODE=1
            ;;
        "fixtures")
            run_test "Fixtures" "python -m pytest app/tests/fixtures -v" || EXIT_CODE=1
            ;;
        "infrastructure")
            run_test "Infrastructure" "python -m pytest app/tests/infrastructure -v" || EXIT_CODE=1
            ;;
        "integration")
            run_test "Integration" "python -m pytest app/tests/integration -v" || EXIT_CODE=1
            ;;
        "coverage")
            echo -e "\n${YELLOW}Running full test suite with coverage...${NC}"
            python -m pytest --cov=app --cov-report=term --cov-report=html:coverage_html app/tests/ -v
            echo -e "${GREEN}Coverage report generated in ./coverage_html/${NC}"
            ;;
        "all")
            echo -e "\n${YELLOW}Running all tests...${NC}"
            python -m pytest app/tests/ -v || EXIT_CODE=1
            ;;
        *)
            echo -e "${RED}Unknown test suite: $arg${NC}"
            echo -e "Available options: core, domain, api, security, fixtures, infrastructure, integration, coverage, all"
            EXIT_CODE=1
            ;;
    esac
done

echo -e "\n${BLUE}=========================================${NC}"
if [[ $EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}All test suites completed successfully!${NC}"
else
    echo -e "${RED}Some tests failed. Please check the output above.${NC}"
fi
echo -e "${BLUE}=========================================${NC}"

exit $EXIT_CODE