#!/bin/bash
# ===============================================================================
# Novamind Digital Twin - Deployment and Test Automation Script
# ===============================================================================
# This script orchestrates the deployment and testing of the Novamind Digital Twin
# platform following clean architecture principles with mathematical precision.
# It ensures a completely deterministic testing environment with neural pathways
# for error handling and feedback.
# ===============================================================================

set -e  # Exit immediately if a command exits with a non-zero status

# ANSI color codes for output beautification
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ===============================================================================
# Neural execution parameters
# ===============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}"
DOCKER_COMPOSE_FILE="${BACKEND_DIR}/docker-compose.test.yml"
TEST_RESULTS_DIR="${BACKEND_DIR}/test-results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${TEST_RESULTS_DIR}/test_run_${TIMESTAMP}.log"

# ===============================================================================
# Neural functions - maintaining clean separation of concerns
# ===============================================================================

function print_banner() {
    echo -e "\n${PURPLE}=================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${PURPLE}=================================================${NC}\n"
}

function print_step() {
    echo -e "\n${BLUE}>>> ${CYAN}$1${NC}"
}

function print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

function print_error() {
    echo -e "${RED}✗ $1${NC}"
}

function print_warning() {
    echo -e "${YELLOW}! $1${NC}"
}

function ensure_directories() {
    print_step "Ensuring necessary directories exist..."
    
    mkdir -p "${TEST_RESULTS_DIR}"
    
    print_success "Directories ready"
}

function check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose not found. Please install Docker Compose."
        exit 1
    fi
    
    print_success "All prerequisites satisfied"
}

function build_test_containers() {
    print_step "Building test containers with mathematical precision..."
    
    docker-compose -f "${DOCKER_COMPOSE_FILE}" build
    
    print_success "Test containers built successfully"
}

function start_test_environment() {
    print_step "Starting test environment with neural synchronization..."
    
    # Down first to ensure clean state
    docker-compose -f "${DOCKER_COMPOSE_FILE}" down -v
    
    # Up with detached mode
    docker-compose -f "${DOCKER_COMPOSE_FILE}" up -d novamind-db-test novamind-redis-test
    
    print_success "Test environment ready"
}

function run_tests() {
    print_step "Executing tests with quantum-level precision..."
    
    # Run the tests inside the test runner container
    docker-compose -f "${DOCKER_COMPOSE_FILE}" run --rm novamind-test-runner
    TEST_EXIT_CODE=$?
    
    print_step "Collecting test artifacts..."
    
    # Copy test results 
    mkdir -p "${TEST_RESULTS_DIR}/reports"
    docker cp novamind-test-runner:/app/test-results/. "${TEST_RESULTS_DIR}/reports/"
    
    if [ ${TEST_EXIT_CODE} -eq 0 ]; then
        print_success "All tests passed successfully"
    else
        print_error "Tests failed with exit code ${TEST_EXIT_CODE}"
    fi
    
    return ${TEST_EXIT_CODE}
}

function clean_test_environment() {
    print_step "Cleaning test environment..."
    
    docker-compose -f "${DOCKER_COMPOSE_FILE}" down -v
    
    print_success "Test environment cleaned"
}

# ===============================================================================
# Main Neural Execution Path
# ===============================================================================

print_banner "Novamind Digital Twin - Test Automation Pipeline"

# Prepare environment
ensure_directories
check_prerequisites

# Start test sequence
build_test_containers
start_test_environment

# Execute tests
TEST_SUCCESS=0
if run_tests; then
    TEST_SUCCESS=1
fi

# Clean up
clean_test_environment

# Final results
if [ ${TEST_SUCCESS} -eq 1 ]; then
    print_banner "Test Run Completed Successfully"
    exit 0
else
    print_banner "Test Run Failed"
    print_warning "See test results for details: ${TEST_RESULTS_DIR}/reports"
    exit 1
fi
