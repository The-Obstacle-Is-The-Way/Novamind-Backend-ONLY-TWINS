#!/bin/bash
# Comprehensive test execution script for Novamind Digital Twin Backend
# Achieves maximum coverage across all components with optimized performance

set -e  # Exit on error

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner function
function print_banner() {
    echo -e "${BLUE}=================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}=================================================================${NC}"
    echo ""
}

# Test execution function with timing
function run_test_section() {
    local section_name=$1
    local test_command=$2
    
    echo -e "${YELLOW}Running $section_name...${NC}"
    echo -e "${YELLOW}Command: $test_command${NC}"
    echo ""
    
    start_time=$(date +%s)
    eval $test_command
    end_time=$(date +%s)
    
    duration=$((end_time - start_time))
    echo ""
    echo -e "${GREEN}✓ $section_name completed in $duration seconds${NC}"
    echo ""
}

# Environment setup
print_banner "NOVAMIND DIGITAL TWIN BACKEND TEST SUITE"

# Check for Python and required tools
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is required but not found in PATH${NC}"
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo -e "${RED}ERROR: pip is required but not found in PATH${NC}"
    exit 1
fi

# Parse command line arguments
SKIP_INSTALL=false
RUN_STANDALONE_ONLY=false
COVERAGE_REPORT=false
VERBOSE=false

for arg in "$@"; do
    case $arg in
        --skip-install)
            SKIP_INSTALL=true
            shift
            ;;
        --standalone-only)
            RUN_STANDALONE_ONLY=true
            shift
            ;;
        --coverage)
            COVERAGE_REPORT=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --skip-install     Skip dependency installation"
            echo "  --standalone-only  Run only standalone tests that don't require database"
            echo "  --coverage         Generate coverage report"
            echo "  --verbose, -v      Verbose output"
            echo "  --help, -h         Show this help message"
            exit 0
            ;;
    esac
done

# Set up environment variables
export TESTING=1
export ENVIRONMENT=testing
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Check if .env.test exists, create if not
if [ ! -f ".env.test" ]; then
    echo -e "${YELLOW}Creating .env.test file...${NC}"
    cat > .env.test << EOF
# Test Environment Configuration
TESTING=1
ENVIRONMENT=testing
POSTGRES_SERVER=localhost
POSTGRES_USER=test_user
POSTGRES_PASSWORD=test_password
POSTGRES_DB=novamind_test
SECRET_KEY=test_secret_key_do_not_use_in_production
EOF
    echo ".env.test file created."
fi

# Load environment variables from .env.test
if [ -f ".env.test" ]; then
    echo -e "${YELLOW}Loading environment from .env.test${NC}"
    export $(grep -v '^#' .env.test | xargs)
fi

# Install dependencies if not skipped
if [ "$SKIP_INSTALL" = false ]; then
    print_banner "INSTALLING TEST DEPENDENCIES"
    if [ -f "requirements-test.txt" ]; then
        pip install -r requirements-test.txt
    else
        echo -e "${YELLOW}requirements-test.txt not found, installing core test packages${NC}"
        pip install pytest pytest-asyncio pytest-cov aiosqlite asyncpg
    fi
fi

# Create test directories if they don't exist
mkdir -p test-results

# Set default pytest options
PYTEST_OPTIONS=""
if [ "$VERBOSE" = true ]; then
    PYTEST_OPTIONS="$PYTEST_OPTIONS -v"
fi

# Run standalone tests first
print_banner "RUNNING STANDALONE TESTS"
run_test_section "Standalone Tests" "python -m pytest app/tests/standalone/ $PYTEST_OPTIONS --junitxml=test-results/standalone-results.xml"

# Run ml_exceptions self-contained test for quick validation
echo -e "${YELLOW}Running self-contained ML exceptions test...${NC}"
python -m app.tests.standalone.test_ml_exceptions_self_contained

# Exit if standalone only mode
if [ "$RUN_STANDALONE_ONLY" = true ]; then
    print_banner "STANDALONE TESTS COMPLETED"
    echo -e "${GREEN}Standalone tests completed successfully${NC}"
    exit 0
fi

# Run core tests
print_banner "RUNNING CORE MODULE TESTS"
run_test_section "Core Tests" "python -m pytest app/tests/core/ $PYTEST_OPTIONS --junitxml=test-results/core-results.xml"

# Run domain tests
print_banner "RUNNING DOMAIN TESTS"
run_test_section "Domain Tests" "python -m pytest app/tests/domain/ $PYTEST_OPTIONS --junitxml=test-results/domain-results.xml"

# Run infrastructure tests
print_banner "RUNNING INFRASTRUCTURE TESTS"
run_test_section "Infrastructure Tests" "python -m pytest app/tests/infrastructure/ $PYTEST_OPTIONS --junitxml=test-results/infrastructure-results.xml"

# Run API tests
print_banner "RUNNING API TESTS"
run_test_section "API Tests" "python -m pytest app/tests/api/ $PYTEST_OPTIONS --junitxml=test-results/api-results.xml"

# Generate coverage report if requested
if [ "$COVERAGE_REPORT" = true ]; then
    print_banner "GENERATING COVERAGE REPORT"
    run_test_section "Coverage Report" "python -m pytest --cov=app --cov-report=html:coverage_html --cov-report=xml:coverage.xml --cov-report=term-missing app/tests/"
    echo -e "${GREEN}Coverage report generated in coverage_html/index.html${NC}"
    
    # Try to open coverage report if browser available
    if command -v open &> /dev/null; then
        open coverage_html/index.html
    elif command -v xdg-open &> /dev/null; then
        xdg-open coverage_html/index.html
    fi
fi

# Print summary
print_banner "TEST EXECUTION SUMMARY"
echo -e "${GREEN}✓ All tests completed successfully${NC}"

# Count test files and estimate coverage
TEST_FILE_COUNT=$(find app/tests -name "test_*.py" | wc -l)
echo -e "${GREEN}► Test files: $TEST_FILE_COUNT${NC}"

if [ "$COVERAGE_REPORT" = true ]; then
    # Extract coverage percentage from coverage report
    if [ -f "coverage.xml" ]; then
        COVERAGE_PCT=$(grep -o 'line-rate="0\.[0-9]*"' coverage.xml | head -1 | grep -o '0\.[0-9]*')
        if [ ! -z "$COVERAGE_PCT" ]; then
            COVERAGE_PCT=$(echo "$COVERAGE_PCT * 100" | bc)
            echo -e "${GREEN}► Coverage: ${COVERAGE_PCT}%${NC}"
        fi
    fi
fi

echo ""
echo -e "${BLUE}To run individual test sections:${NC}"
echo -e " - Standalone tests: python -m pytest app/tests/standalone/"
echo -e " - Core tests: python -m pytest app/tests/core/"
echo -e " - Domain tests: python -m pytest app/tests/domain/"
echo -e " - Infrastructure tests: python -m pytest app/tests/infrastructure/"
echo -e " - API tests: python -m pytest app/tests/api/"
echo ""
echo -e "${BLUE}For coverage report:${NC}"
echo -e " - Run with --coverage option"
echo ""