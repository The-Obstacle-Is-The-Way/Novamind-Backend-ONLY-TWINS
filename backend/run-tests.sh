#!/bin/bash
# Novamind Digital Twin Platform Test Runner
# This script provides an easy way to run different test suites

set -e  # Exit on error

# Terminal colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Show usage information
function show_usage {
    echo -e "${BLUE}Novamind Digital Twin Platform Test Runner${NC}"
    echo ""
    echo "Usage: ./run-tests.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --all             Run all tests"
    echo "  --unit            Run only unit tests"
    echo "  --integration     Run only integration tests"
    echo "  --ml-mock         Run only ML mock tests"
    echo "  --security        Run only security tests"
    echo "  --quick           Run a subset of tests for quick feedback"
    echo "  --coverage        Include coverage reporting"
    echo "  --verbose, -v     Display verbose output"
    echo "  --help, -h        Display this help message"
    echo ""
    echo "Examples:"
    echo "  ./run-tests.sh --unit               # Run unit tests only"
    echo "  ./run-tests.sh --all --coverage     # Run all tests with coverage reporting"
    echo "  ./run-tests.sh --ml-mock --verbose  # Run ML mock tests with verbose output"
    echo ""
}

# Check if venv exists, if not create it
function ensure_venv {
    echo -e "${BLUE}Checking virtual environment...${NC}"
    if [ ! -d "./venv" ]; then
        echo -e "${YELLOW}Virtual environment not found, creating one...${NC}"
        python -m venv venv
        source ./venv/bin/activate
        pip install -U pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
        echo -e "${GREEN}Virtual environment created and dependencies installed.${NC}"
    else
        echo -e "${GREEN}Using existing virtual environment.${NC}"
        source ./venv/bin/activate
    fi
}

# Parse arguments
ALL=false
UNIT=false
INTEGRATION=false
ML_MOCK=false
SECURITY=false
QUICK=false
COVERAGE=false
VERBOSE=false

# If no arguments provided, show usage
if [ $# -eq 0 ]; then
    show_usage
    exit 0
fi

# Parse command line arguments
while [ $# -gt 0 ]; do
    case "$1" in
        --all)
            ALL=true
            ;;
        --unit)
            UNIT=true
            ;;
        --integration)
            INTEGRATION=true
            ;;
        --ml-mock)
            ML_MOCK=true
            ;;
        --security)
            SECURITY=true
            ;;
        --quick)
            QUICK=true
            ;;
        --coverage)
            COVERAGE=true
            ;;
        --verbose|-v)
            VERBOSE=true
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            show_usage
            exit 1
            ;;
    esac
    shift
done

# Ensure virtual environment is set up
ensure_venv

# Build the command
CMD="./scripts/run_tests.py"

if [ "$ALL" == "true" ]; then
    echo -e "${BLUE}Running all tests...${NC}"
elif [ "$UNIT" == "true" ]; then
    CMD="$CMD --unit"
    echo -e "${BLUE}Running unit tests...${NC}"
elif [ "$INTEGRATION" == "true" ]; then
    CMD="$CMD --integration"
    echo -e "${BLUE}Running integration tests...${NC}"
elif [ "$ML_MOCK" == "true" ]; then
    CMD="$CMD --ml-mock"
    echo -e "${BLUE}Running ML mock tests...${NC}"
elif [ "$SECURITY" == "true" ]; then
    CMD="$CMD --security"
    echo -e "${BLUE}Running security tests...${NC}"
elif [ "$QUICK" == "true" ]; then
    CMD="$CMD --quick"
    echo -e "${BLUE}Running quick tests...${NC}"
fi

if [ "$COVERAGE" == "true" ]; then
    CMD="$CMD --coverage"
    echo -e "${BLUE}Including coverage reporting...${NC}"
fi

if [ "$VERBOSE" == "true" ]; then
    CMD="$CMD --verbose"
    echo -e "${BLUE}Using verbose output...${NC}"
fi

# Run the tests
echo -e "${BLUE}Executing: $CMD${NC}"
$CMD

# Handle exit code
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Tests completed successfully!${NC}"
    exit 0
else
    echo -e "${RED}Tests failed!${NC}"
    exit 1
fi