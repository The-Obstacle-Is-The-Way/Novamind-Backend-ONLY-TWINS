#!/bin/bash
# Novamind Digital Twin Backend Test Runner
# 
# This script runs tests in the optimal order based on their dependency level:
# 1. Standalone tests (no dependencies)
# 2. VENV-only tests (require packages but no external services)
# 3. DB-required tests (require database connections)
#
# Usage:
#   ./run_tests.sh standalone    # Run only standalone tests
#   ./run_tests.sh venv          # Run only venv-dependent tests
#   ./run_tests.sh db            # Run only database-dependent tests
#   ./run_tests.sh all           # Run all tests in optimal order
#   ./run_tests.sh report        # Generate a test dependency report
#   ./run_tests.sh candidates    # Identify standalone test candidates
#   ./run_tests.sh help          # Show this help message

set -e  # Exit on any error

# Colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Make sure we're in the backend directory
cd "$(dirname "$0")/.."
BACKEND_DIR=$(pwd)
PYTHON_CMD="python"

# Function to display help
display_help() {
    echo -e "${BLUE}Novamind Digital Twin Backend Test Runner${NC}"
    echo
    echo -e "This script runs tests in dependency order (standalone → venv → db)"
    echo
    echo -e "${CYAN}Usage:${NC}"
    echo -e "  $0 ${GREEN}standalone${NC} [args]   # Run only standalone tests"
    echo -e "  $0 ${GREEN}venv${NC} [args]         # Run only venv-dependent tests"
    echo -e "  $0 ${GREEN}db${NC} [args]           # Run only database-dependent tests"
    echo -e "  $0 ${GREEN}all${NC} [args]          # Run all tests in optimal order"
    echo -e "  $0 ${GREEN}report${NC}              # Generate a test dependency report"
    echo -e "  $0 ${GREEN}candidates${NC}          # Identify standalone test candidates"
    echo -e "  $0 ${GREEN}help${NC}                # Show this help message"
    echo
    echo -e "${CYAN}Examples:${NC}"
    echo -e "  $0 standalone -v                  # Run standalone tests with verbose output"
    echo -e "  $0 venv -k test_utils             # Run only venv tests matching 'test_utils'"
    echo -e "  $0 candidates --output report.txt # Generate standalone candidate report to file"
    echo -e "  $0 all --cov=app                  # Run all tests with coverage reporting"
    echo
    echo -e "${CYAN}More info:${NC}"
    echo -e "  - Stand-alone tests: No dependencies beyond Python itself"
    echo -e "  - VENV-only tests: Require Python packages but no external services"
    echo -e "  - DB-required tests: Require database connections"
    echo
}

# Function to run a specific test level
run_test_level() {
    local level=$1
    shift  # Remove the first argument, leaving the rest for pytest

    echo -e "${BLUE}Running ${YELLOW}$level${BLUE} tests ${NC}"
    echo -e "${CYAN}======================${NC}"

    # Run using the dependency test runner script
    $PYTHON_CMD "$BACKEND_DIR/scripts/run_dependency_tests.py" --level "$level" "$@"
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✓ $level tests passed${NC}"
    else
        echo -e "${RED}✗ $level tests failed with exit code $exit_code${NC}"
        if [ "$level" != "standalone" ]; then
            echo -e "${RED}Stopping test run due to failures${NC}"
            exit $exit_code
        fi
    fi
    
    echo
    return $exit_code
}

# Function to run all tests in order
run_all_tests() {
    echo -e "${BLUE}Running all tests in dependency order${NC}"
    echo -e "${CYAN}=====================================${NC}"
    
    # Run standalone tests first
    run_test_level "standalone" "$@"
    standalone_exit=$?
    
    # Run venv-only tests next
    run_test_level "venv" "$@"
    venv_exit=$?
    
    # Run db-required tests last
    run_test_level "db" "$@"
    db_exit=$?
    
    # Return overall status
    if [ $standalone_exit -eq 0 ] && [ $venv_exit -eq 0 ] && [ $db_exit -eq 0 ]; then
        echo -e "${GREEN}All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}Some test runs failed:${NC}"
        [ $standalone_exit -ne 0 ] && echo -e "${RED}  - Standalone tests: Exit code $standalone_exit${NC}"
        [ $venv_exit -ne 0 ] && echo -e "${RED}  - VENV tests: Exit code $venv_exit${NC}"
        [ $db_exit -ne 0 ] && echo -e "${RED}  - DB tests: Exit code $db_exit${NC}"
        return 1
    fi
}

# Function to generate a test dependency report
generate_report() {
    echo -e "${BLUE}Generating test dependency report${NC}"
    echo -e "${CYAN}================================${NC}"
    
    $PYTHON_CMD "$BACKEND_DIR/scripts/run_dependency_tests.py" --report "$@"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Report generated successfully${NC}"
    else
        echo -e "${RED}Failed to generate report${NC}"
        return 1
    fi
}

# Function to identify standalone test candidates
find_candidates() {
    echo -e "${BLUE}Identifying standalone test candidates${NC}"
    echo -e "${CYAN}====================================${NC}"
    
    $PYTHON_CMD "$BACKEND_DIR/scripts/identify_standalone_candidates.py" "$@"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Candidate analysis completed successfully${NC}"
    else
        echo -e "${RED}Failed to identify candidates${NC}"
        return 1
    fi
}

# Check if a command was provided
if [ $# -eq 0 ]; then
    display_help
    exit 1
fi

# Get the command (first argument)
COMMAND=$1
shift

# Process the command
case "$COMMAND" in
    standalone)
        run_test_level "standalone" "$@"
        ;;
    venv)
        run_test_level "venv" "$@"
        ;;
    db)
        run_test_level "db" "$@"
        ;;
    all)
        run_all_tests "$@"
        ;;
    report)
        generate_report "$@"
        ;;
    candidates)
        find_candidates "$@"
        ;;
    help|--help|-h)
        display_help
        ;;
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        display_help
        exit 1
        ;;
esac

exit $?