#!/bin/bash
# Main test runner script for the Novamind Digital Twin Backend
# This script provides a simple interface to the test infrastructure

# Set strict error handling
set -e

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Determine the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values
RUN_STANDALONE=false
RUN_VENV=false
RUN_DB=false
RUN_ALL=false
XML_OUTPUT=false
HTML_OUTPUT=false
VERBOSE=false
CI_MODE=false
CLEANUP=false
SETUP_ENV=false
CLEANUP_ENV=false
CLASSIFY=false
CLASSIFY_UPDATE=false

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --standalone)
      RUN_STANDALONE=true
      shift
      ;;
    --venv)
      RUN_VENV=true
      shift
      ;;
    --db)
      RUN_DB=true
      shift
      ;;
    --all)
      RUN_ALL=true
      shift
      ;;
    --xml)
      XML_OUTPUT=true
      shift
      ;;
    --html)
      HTML_OUTPUT=true
      shift
      ;;
    --verbose|-v)
      VERBOSE=true
      shift
      ;;
    --ci)
      CI_MODE=true
      shift
      ;;
    --cleanup)
      CLEANUP=true
      shift
      ;;
    --setup-env)
      SETUP_ENV=true
      shift
      ;;
    --cleanup-env)
      CLEANUP_ENV=true
      shift
      ;;
    --classify)
      CLASSIFY=true
      shift
      ;;
    --classify-update)
      CLASSIFY=true
      CLASSIFY_UPDATE=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo "Test runner for Novamind Digital Twin Backend"
      echo ""
      echo "Options:"
      echo "  --standalone          Run standalone tests only"
      echo "  --venv                Run venv-dependent tests only"
      echo "  --db                  Run database-dependent tests only"
      echo "  --all                 Run all tests (default if no test type specified)"
      echo "  --xml                 Generate XML test report"
      echo "  --html                Generate HTML coverage report"
      echo "  --verbose, -v         Verbose output"
      echo "  --ci                  Run in CI mode (changes output paths)"
      echo "  --cleanup             Clean up test environment after tests"
      echo "  --setup-env           Set up test environment without running tests"
      echo "  --cleanup-env         Clean up test environment without running tests"
      echo "  --classify            Analyze and classify test files by dependency"
      echo "  --classify-update     Analyze test files and update with appropriate markers"
      echo "  --help, -h            Show this help message"
      echo ""
      echo "Examples:"
      echo "  $0 --standalone       # Run standalone tests only"
      echo "  $0 --all --xml        # Run all tests with XML report"
      echo "  $0 --classify-update  # Update test files with dependency markers"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Print Novamind banner
echo -e "${BLUE}${BOLD}=====================================================================${NC}"
echo -e "${BLUE}${BOLD}                Novamind Digital Twin Test Runner                    ${NC}"
echo -e "${BLUE}${BOLD}=====================================================================${NC}"

# If no test type specified, run all
if [[ "$RUN_STANDALONE" == "false" && "$RUN_VENV" == "false" && "$RUN_DB" == "false" && "$RUN_ALL" == "false" && "$CLASSIFY" == "false" && "$SETUP_ENV" == "false" && "$CLEANUP_ENV" == "false" ]]; then
  RUN_ALL=true
fi

# Handle test classification
if [[ "$CLASSIFY" == "true" ]]; then
  echo -e "${YELLOW}Analyzing test files to determine dependency levels...${NC}"
  
  CLASSIFY_ARGS=""
  if [[ "$CLASSIFY_UPDATE" == "true" ]]; then
    CLASSIFY_ARGS="--update"
    echo -e "${YELLOW}Will update test files with appropriate markers${NC}"
  fi
  
  if [[ "$VERBOSE" == "true" ]]; then
    CLASSIFY_ARGS="$CLASSIFY_ARGS --verbose"
  fi
  
  python "${SCRIPT_DIR}/scripts/classify_tests.py" $CLASSIFY_ARGS
  
  echo -e "${GREEN}Test classification complete${NC}"
  
  # Exit if we were only classifying
  if [[ "$RUN_ALL" == "false" && "$RUN_STANDALONE" == "false" && "$RUN_VENV" == "false" && "$RUN_DB" == "false" ]]; then
    exit 0
  fi
fi

# Handle environment setup/cleanup only
if [[ "$SETUP_ENV" == "true" ]]; then
  echo -e "${YELLOW}Setting up test environment...${NC}"
  python "${SCRIPT_DIR}/scripts/run_tests_by_dependency.py" --setup-env
  echo -e "${GREEN}Test environment setup complete${NC}"
  exit 0
fi

if [[ "$CLEANUP_ENV" == "true" ]]; then
  echo -e "${YELLOW}Cleaning up test environment...${NC}"
  python "${SCRIPT_DIR}/scripts/run_tests_by_dependency.py" --cleanup-env
  echo -e "${GREEN}Test environment cleanup complete${NC}"
  exit 0
fi

# Build arguments for the test runner
RUNNER_ARGS=""

if [[ "$RUN_ALL" == "true" ]]; then
  RUNNER_ARGS="$RUNNER_ARGS --all"
elif [[ "$RUN_STANDALONE" == "true" ]]; then
  RUNNER_ARGS="$RUNNER_ARGS --standalone"
elif [[ "$RUN_VENV" == "true" ]]; then
  RUNNER_ARGS="$RUNNER_ARGS --venv"
elif [[ "$RUN_DB" == "true" ]]; then
  RUNNER_ARGS="$RUNNER_ARGS --db"
fi

if [[ "$XML_OUTPUT" == "true" ]]; then
  RUNNER_ARGS="$RUNNER_ARGS --xml"
fi

if [[ "$HTML_OUTPUT" == "true" ]]; then
  RUNNER_ARGS="$RUNNER_ARGS --html"
fi

if [[ "$VERBOSE" == "true" ]]; then
  RUNNER_ARGS="$RUNNER_ARGS --verbose"
fi

if [[ "$CI_MODE" == "true" ]]; then
  RUNNER_ARGS="$RUNNER_ARGS --ci"
fi

if [[ "$CLEANUP" == "true" ]]; then
  RUNNER_ARGS="$RUNNER_ARGS --cleanup"
fi

echo -e "${YELLOW}Starting test run with args: $RUNNER_ARGS${NC}"
python "${SCRIPT_DIR}/scripts/run_tests_by_dependency.py" $RUNNER_ARGS

echo -e "${GREEN}Test run complete${NC}"
exit 0