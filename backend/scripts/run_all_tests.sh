#!/bin/bash
#
# Script to run all test suites for Novamind Digital Twin
# This runs tests in order of isolation level, from most isolated to least isolated
# Can also run tests in Docker with --docker flag
#

set -e  # Exit immediately if a command exits with a non-zero status

# Parse command line arguments
RUN_IN_DOCKER=0
for arg in "$@"; do
    case $arg in
        --docker)
        RUN_IN_DOCKER=1
        shift
        ;;
    esac
done

# Set base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Base directory: $BASE_DIR"

# Create results directory if it doesn't exist
mkdir -p "$BASE_DIR/test-results"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test suite counters
PASSED_SUITES=0
FAILED_SUITES=0
TOTAL_SUITES=4  # standalone, venv_only, integration, security

echo -e "${BLUE}==============================================${NC}"
echo -e "${BLUE}   NOVAMIND DIGITAL TWIN - TEST EXECUTION    ${NC}"
echo -e "${BLUE}==============================================${NC}"

# Generate a timestamp for this test run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$BASE_DIR/test-results/test_report_$TIMESTAMP.txt"
echo "Generating test report at: $REPORT_FILE"
echo "Test run started at $(date)" > "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Function to run a test suite
run_test_suite() {
    local suite_name=$1
    local test_command=$2
    local suite_dir=$3
    
    echo -e "\n${BLUE}==============================================${NC}"
    echo -e "${BLUE}   RUNNING $suite_name TESTS${NC}"
    echo -e "${BLUE}==============================================${NC}"
    echo "Running $suite_name tests..."
    
    # Add to report
    echo "### $suite_name Tests ###" >> "$REPORT_FILE"
    echo "Started at $(date)" >> "$REPORT_FILE"
    
    # Check if test directory exists and has tests
    if [ ! -d "$suite_dir" ] || [ -z "$(ls -A "$suite_dir" 2>/dev/null)" ]; then
        echo -e "${YELLOW}⚠️  No $suite_name tests found in $suite_dir${NC}"
        echo "⚠️ No $suite_name tests found." >> "$REPORT_FILE"
        return 0
    fi
    
    # Run the test command
    if eval "$test_command"; then
        echo -e "\n${GREEN}✅ All $suite_name tests passed!${NC}"
        echo "✅ All $suite_name tests passed!" >> "$REPORT_FILE"
        PASSED_SUITES=$((PASSED_SUITES + 1))
        return 0
    else
        echo -e "\n${RED}❌ Some $suite_name tests failed!${NC}"
        echo "❌ Some $suite_name tests failed!" >> "$REPORT_FILE"
        FAILED_SUITES=$((FAILED_SUITES + 1))
        return 1
    fi
}

# Ensure we're using the correct Python environment
echo "Setting up environment..."
export PYTHONPATH="$BASE_DIR"
export TESTING=1

# If running in Docker, use docker-compose
if [ $RUN_IN_DOCKER -eq 1 ]; then
    echo -e "\n${BLUE}Running tests in Docker containers${NC}"
    
    # Make sure docker-compose.test.yml exists
    if [ ! -f "$BASE_DIR/../docker-compose.test.yml" ]; then
        echo -e "${RED}Error: docker-compose.test.yml not found${NC}"
        exit 1
    fi
    
    # Run the tests in Docker
    cd "$BASE_DIR/.."
    docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
    
    # Check the exit code
    DOCKER_RESULT=$?
    
    # Clean up
    docker-compose -f docker-compose.test.yml down
    
    if [ $DOCKER_RESULT -eq 0 ]; then
        echo -e "\n${GREEN}✅ All Docker tests passed!${NC}"
        exit 0
    else
        echo -e "\n${RED}❌ Some Docker tests failed!${NC}"
        exit 1
    fi
fi

# Run standalone tests (no external dependencies)
export TEST_TYPE=standalone
run_test_suite "STANDALONE" \
    "python -m pytest '$BASE_DIR/app/tests/standalone/' -v --strict-markers --cov='$BASE_DIR/app' --cov-report=term --cov-report=xml:'$BASE_DIR/test-results/standalone-coverage.xml' --junitxml='$BASE_DIR/test-results/standalone-results.xml'" \
    "$BASE_DIR/app/tests/standalone"
STANDALONE_RESULT=$?

# Run venv_only tests (Python packages but no external services)
export TEST_TYPE=venv_only
run_test_suite "VENV_ONLY" \
    "python -m pytest '$BASE_DIR/app/tests/venv_only/' -v --strict-markers --cov='$BASE_DIR/app' --cov-report=term --cov-report=xml:'$BASE_DIR/test-results/venv_only-coverage.xml' --junitxml='$BASE_DIR/test-results/venv_only-results.xml'" \
    "$BASE_DIR/app/tests/venv_only"
VENV_ONLY_RESULT=$?

# Run integration tests (external services)
export TEST_TYPE=integration
run_test_suite "INTEGRATION" \
    "python -m pytest '$BASE_DIR/app/tests/integration/' -v --strict-markers --cov='$BASE_DIR/app' --cov-report=term --cov-report=xml:'$BASE_DIR/test-results/integration-coverage.xml' --junitxml='$BASE_DIR/test-results/integration-results.xml'" \
    "$BASE_DIR/app/tests/integration"
INTEGRATION_RESULT=$?

# Run security tests (PHI and HIPAA compliance)
export TEST_TYPE=security
run_test_suite "SECURITY" \
    "python -m pytest '$BASE_DIR/app/tests/security/' -v --strict-markers --cov='$BASE_DIR/app' --cov-report=term --cov-report=xml:'$BASE_DIR/test-results/security-coverage.xml' --junitxml='$BASE_DIR/test-results/security-results.xml'" \
    "$BASE_DIR/app/tests/security"
SECURITY_RESULT=$?

# Generate combined coverage report
echo -e "\n${BLUE}==============================================${NC}"
echo -e "${BLUE}   GENERATING COMBINED COVERAGE REPORT   ${NC}"
echo -e "${BLUE}==============================================${NC}"
echo "Generating combined coverage report..."

# Check if coverage files exist
COVERAGE_FILES=()
for suite in standalone venv_only integration security; do
    COVERAGE_FILE="$BASE_DIR/test-results/$suite-coverage.xml"
    if [ -f "$COVERAGE_FILE" ]; then
        COVERAGE_FILES+=("$COVERAGE_FILE")
    fi
done

if [ ${#COVERAGE_FILES[@]} -gt 0 ]; then
    # Combine coverage reports if there are any
    python -m coverage combine "${COVERAGE_FILES[@]}" || true
    python -m coverage report --show-missing || true
    python -m coverage xml -o "$BASE_DIR/test-results/combined-coverage.xml" || true
    python -m coverage html -d "$BASE_DIR/test-results/coverage-html" || true
    
    echo "Combined coverage report generated in $BASE_DIR/test-results/coverage-html"
    echo "Combined coverage report saved to $BASE_DIR/test-results/combined-coverage.xml"
    echo "" >> "$REPORT_FILE"
    echo "Coverage report generated at $(date)" >> "$REPORT_FILE"
else
    echo -e "${YELLOW}⚠️  No coverage files found to combine${NC}"
    echo "⚠️ No coverage files found to combine." >> "$REPORT_FILE"
fi

# Test summary
echo -e "\n${BLUE}==============================================${NC}"
echo -e "${BLUE}              TEST SUMMARY                  ${NC}"
echo -e "${BLUE}==============================================${NC}"
echo "Test run completed at $(date)"
echo "" >> "$REPORT_FILE"
echo "### Test Summary ###" >> "$REPORT_FILE"
echo "Completed at $(date)" >> "$REPORT_FILE"

# Check results
if [ $STANDALONE_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Standalone tests: PASSED${NC}"
    echo "✅ Standalone tests: PASSED" >> "$REPORT_FILE"
else
    echo -e "${RED}❌ Standalone tests: FAILED${NC}"
    echo "❌ Standalone tests: FAILED" >> "$REPORT_FILE"
fi

if [ $VENV_ONLY_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Venv_only tests: PASSED${NC}"
    echo "✅ Venv_only tests: PASSED" >> "$REPORT_FILE"
else
    echo -e "${RED}❌ Venv_only tests: FAILED${NC}"
    echo "❌ Venv_only tests: FAILED" >> "$REPORT_FILE"
fi

if [ $INTEGRATION_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Integration tests: PASSED${NC}"
    echo "✅ Integration tests: PASSED" >> "$REPORT_FILE"
else
    echo -e "${RED}❌ Integration tests: FAILED${NC}"
    echo "❌ Integration tests: FAILED" >> "$REPORT_FILE"
fi

if [ $SECURITY_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Security tests: PASSED${NC}"
    echo "✅ Security tests: PASSED" >> "$REPORT_FILE"
else
    echo -e "${RED}❌ Security tests: FAILED${NC}"
    echo "❌ Security tests: FAILED" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"
echo "Test suites passed: $PASSED_SUITES/$TOTAL_SUITES" >> "$REPORT_FILE"

# Final summary
echo -e "\n${BLUE}Test suites passed: ${GREEN}$PASSED_SUITES${BLUE}/${YELLOW}$TOTAL_SUITES${NC}"

if [ $FAILED_SUITES -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All test suites passed!${NC}"
    echo "🎉 All test suites passed!" >> "$REPORT_FILE"
    exit 0
else
    echo -e "\n${RED}⚠️ $FAILED_SUITES test suite(s) failed!${NC}"
    echo "⚠️ $FAILED_SUITES test suite(s) failed!" >> "$REPORT_FILE"
    exit 1
fi