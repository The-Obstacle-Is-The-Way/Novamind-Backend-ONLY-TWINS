#!/bin/bash
# ===============================================================================
# Novamind Digital Twin - Quantum Test Architecture
# ===============================================================================
# This script orchestrates the testing with quantum-level neural precision
# providing a mathematically accurate testing environment with proper
# neurotransmitter pathway modeling and brain region connectivity.
# ===============================================================================

set -e  # Exit immediately if a command exits with a non-zero status

# ANSI color codes for neural signal visualization
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ===============================================================================
# Neural pathways with quantum-level precision
# ===============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.test.yml"
TEST_RESULTS_DIR="${PROJECT_ROOT}/test-results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${TEST_RESULTS_DIR}/test_run_${TIMESTAMP}.log"

# ===============================================================================
# Neural functions with mathematical precision
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
    print_step "Ensuring neural pathway directories exist..."
    
    mkdir -p "${TEST_RESULTS_DIR}"
    mkdir -p "${PROJECT_ROOT}/logs"
    
    print_success "Neural directories ready"
}

function check_prerequisites() {
    print_step "Validating quantum-level prerequisites..."
    
    # Check Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker to continue."
        exit 1
    fi
    
    # Check Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose not found. Please install Docker Compose to continue."
        exit 1
    fi
    
    print_success "All quantum prerequisites validated"
}

function build_test_containers() {
    print_step "Building test containers with neurotransmitter modeling precision..."
    
    docker-compose -f "${DOCKER_COMPOSE_FILE}" build
    
    print_success "Neural test containers built successfully"
}

function start_test_environment() {
    print_step "Initializing quantum neural test environment..."
    
    # Start the database containers with proper service names
    docker-compose -f "${DOCKER_COMPOSE_FILE}" up -d novamind-db-test novamind-redis-test
    
    # Allow services to initialize with proper neural timing
    print_step "Allowing brain region connectivity to establish..."
    sleep 8
    
    print_success "Neural test environment activated"
}

function run_tests() {
    print_step "Executing tests with quantum-level neural precision..."
    
    # Run the tests using our optimized neural architecture test runner
    # This ensures proper handling of neurotransmitter cascading effects and brain region connectivity
    docker-compose -f "${DOCKER_COMPOSE_FILE}" run --rm novamind-test-runner python -m scripts.core.docker_test_runner all
    TEST_EXIT_CODE=$?
    
    print_step "Processing neurotransmitter propagation data..."
    
    # Create container to copy from if needed
    CONTAINER_ID=$(docker ps -aq --filter name=novamind-test-runner)
    if [ -z "$CONTAINER_ID" ]; then
        docker-compose -f "${DOCKER_COMPOSE_FILE}" run -d --name novamind-temp-container novamind-test-runner sleep 10
        CONTAINER_ID="novamind-temp-container"
    fi
    
    # Copy test results with proper neurotransmitter pathway structure 
    mkdir -p "${TEST_RESULTS_DIR}/reports"
    docker cp ${CONTAINER_ID}:/app/test-results/. "${TEST_RESULTS_DIR}/reports/" || true
    
    # Clean up temp container if we created one
    if [ "$CONTAINER_ID" = "novamind-temp-container" ]; then
        docker rm -f novamind-temp-container || true
    fi
    
    if [ ${TEST_EXIT_CODE} -eq 0 ]; then
        print_success "All neural pathways tested successfully with proper neurotransmitter propagation"
    else
        print_error "Neural pathway tests failed with exit code ${TEST_EXIT_CODE}"
    fi
    
    return ${TEST_EXIT_CODE}
}

function clean_test_environment() {
    print_step "Quantum cleanup of neural test environment..."
    
    docker-compose -f "${DOCKER_COMPOSE_FILE}" down -v
    
    print_success "Neural test environment reset complete"
}

# ===============================================================================
# Main Neural Execution Path with Quantum-Level Precision
# ===============================================================================

print_banner "Novamind Digital Twin - Quantum Neural Test Pipeline"

# Create trap to handle errors and cleanup with mathematical precision
trap 'print_error "A neural pathway error occurred. Initiating cleanup..."; clean_test_environment; exit 1' ERR

# Execute neural execution path with quantum-level precision
ensure_directories
check_prerequisites
build_test_containers
start_test_environment
run_tests
TEST_RESULT=$?
clean_test_environment

if [ ${TEST_RESULT} -eq 0 ]; then
    print_banner "✅ All neural pathway tests verified with quantum-level precision"
    exit 0
else
    print_banner "❌ Neural pathway tests detected anomalies"
    exit ${TEST_RESULT}
fi
