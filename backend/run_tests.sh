#!/bin/bash
# Novamind Digital Twin Test Runner
# This script provides a simple command-line interface for running tests
# organized by dependency level.

set -e

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Determine the script directory and backend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}"

# Print header
echo -e "${BLUE}${BOLD}=====================================================================${NC}"
echo -e "${BLUE}${BOLD}                Novamind Digital Twin Test Runner                    ${NC}"
echo -e "${BLUE}${BOLD}=====================================================================${NC}"

# Function to display help
show_help() {
    echo -e "Usage: $0 [options]"
    echo -e ""
    echo -e "Options:"
    echo -e "  ${BOLD}Test Selection${NC}"
    echo -e "  --all              Run all tests (default)"
    echo -e "  --standalone       Run only standalone tests"
    echo -e "  --venv             Run only VENV-dependent tests"
    echo -e "  --db               Run only DB-dependent tests"
    echo -e ""
    echo -e "  ${BOLD}Test Environment${NC}"
    echo -e "  --setup-env        Set up test environment without running tests"
    echo -e "  --cleanup-env      Clean up test environment without running tests"
    echo -e "  --cleanup          Clean up test environment after running tests"
    echo -e ""
    echo -e "  ${BOLD}Output Options${NC}"
    echo -e "  -v, --verbose      Enable verbose output"
    echo -e "  --xml              Generate XML test reports"
    echo -e "  --html             Generate HTML coverage reports"
    echo -e "  --ci               Run in CI mode (fail fast)"
    echo -e ""
    echo -e "  ${BOLD}Utility Options${NC}"
    echo -e "  --classify         Classify tests by dependency level"
    echo -e "  --classify-update  Classify tests and update markers"
    echo -e "  --help             Display this help message"
    echo -e ""
    echo -e "  ${BOLD}Example Usage${NC}"
    echo -e "  $0 --standalone --verbose"
    echo -e "  $0 --classify-update"
    echo -e "  $0 --db --xml --html --cleanup"
}

# Check for no arguments
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}No arguments provided, running all tests with default options.${NC}"
    echo -e "${YELLOW}Use --help to see available options.${NC}"
    echo -e ""
fi

# Parse arguments
RUN_ALL=0
RUN_STANDALONE=0
RUN_VENV=0
RUN_DB=0
SETUP_ENV=0
CLEANUP_ENV=0
CLEANUP=0
VERBOSE=0
XML=0
HTML=0
CI=0
CLASSIFY=0
CLASSIFY_UPDATE=0

for arg in "$@"; do
    case $arg in
        --help)
            show_help
            exit 0
            ;;
        --all)
            RUN_ALL=1
            ;;
        --standalone)
            RUN_STANDALONE=1
            ;;
        --venv)
            RUN_VENV=1
            ;;
        --db)
            RUN_DB=1
            ;;
        --setup-env)
            SETUP_ENV=1
            ;;
        --cleanup-env)
            CLEANUP_ENV=1
            ;;
        --cleanup)
            CLEANUP=1
            ;;
        -v|--verbose)
            VERBOSE=1
            ;;
        --xml)
            XML=1
            ;;
        --html)
            HTML=1
            ;;
        --ci)
            CI=1
            ;;
        --classify)
            CLASSIFY=1
            ;;
        --classify-update)
            CLASSIFY_UPDATE=1
            ;;
        *)
            # Unknown option
            echo -e "${RED}Unknown option: $arg${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Set default to run all tests if no specific test type selected
if [ $RUN_STANDALONE -eq 0 ] && [ $RUN_VENV -eq 0 ] && [ $RUN_DB -eq 0 ] && [ $SETUP_ENV -eq 0 ] && [ $CLEANUP_ENV -eq 0 ] && [ $CLASSIFY -eq 0 ] && [ $CLASSIFY_UPDATE -eq 0 ]; then
    RUN_ALL=1
fi

# Ensure permissions
chmod +x "${BACKEND_DIR}/scripts/run_tests_by_dependency.py"
chmod +x "${BACKEND_DIR}/scripts/classify_tests.py"

# Handle special commands
if [ $SETUP_ENV -eq 1 ]; then
    echo -e "${BLUE}Setting up test environment...${NC}"
    "${BACKEND_DIR}/scripts/run_test_environment.sh" start
    exit $?
fi

if [ $CLEANUP_ENV -eq 1 ]; then
    echo -e "${BLUE}Cleaning up test environment...${NC}"
    "${BACKEND_DIR}/scripts/run_test_environment.sh" stop
    exit $?
fi

# Run test classification if requested
if [ $CLASSIFY -eq 1 ] || [ $CLASSIFY_UPDATE -eq 1 ]; then
    echo -e "${BLUE}Classifying tests by dependency level...${NC}"
    
    CLASSIFY_ARGS="--path ${BACKEND_DIR}/app/tests"
    
    if [ $CLASSIFY_UPDATE -eq 1 ]; then
        CLASSIFY_ARGS="${CLASSIFY_ARGS} --update"
    fi
    
    if [ $VERBOSE -eq 1 ]; then
        CLASSIFY_ARGS="${CLASSIFY_ARGS} --log-level DEBUG"
    fi
    
    python "${BACKEND_DIR}/scripts/classify_tests.py" ${CLASSIFY_ARGS}
    exit $?
fi

# Build args for test runner
RUNNER_ARGS=""

# Test selection
if [ $RUN_ALL -eq 1 ]; then
    RUNNER_ARGS="${RUNNER_ARGS} --all"
elif [ $RUN_STANDALONE -eq 1 ]; then
    RUNNER_ARGS="${RUNNER_ARGS} --standalone-only"
elif [ $RUN_VENV -eq 1 ]; then
    RUNNER_ARGS="${RUNNER_ARGS} --venv-only"
elif [ $RUN_DB -eq 1 ]; then
    RUNNER_ARGS="${RUNNER_ARGS} --db-only"
fi

# Output options
if [ $VERBOSE -eq 1 ]; then
    RUNNER_ARGS="${RUNNER_ARGS} --verbose"
fi

if [ $XML -eq 1 ]; then
    RUNNER_ARGS="${RUNNER_ARGS} --xml"
fi

if [ $HTML -eq 1 ]; then
    RUNNER_ARGS="${RUNNER_ARGS} --html"
fi

# Behavior options
if [ $CI -eq 1 ]; then
    RUNNER_ARGS="${RUNNER_ARGS} --ci"
fi

if [ $CLEANUP -eq 1 ]; then
    RUNNER_ARGS="${RUNNER_ARGS} --cleanup"
fi

# Run the tests
echo -e "${BLUE}Running tests with arguments: ${RUNNER_ARGS}${NC}"
echo -e ""
python "${BACKEND_DIR}/scripts/run_tests_by_dependency.py" ${RUNNER_ARGS}
EXIT_CODE=$?

# Show final message
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}${BOLD}All tests passed!${NC}"
else
    echo -e "${RED}${BOLD}Some tests failed with exit code ${EXIT_CODE}${NC}"
fi

exit $EXIT_CODE