#!/bin/bash
# Novamind Digital Twin Deployment and Test Orchestration
# This script follows clean architecture principles with a focus on 
# domain-driven deployment and testing.

set -e  # Exit immediately if a command exits with a non-zero status

# Color constants for output formatting
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Banner with neural inspiration
echo -e "${BLUE}"
echo "======================================================================"
echo "  NOVAMIND DIGITAL TWIN - NEURAL DEPLOYMENT AND TEST ORCHESTRATION"
echo "  Pure Clean Architecture with Quantum-Level Testing"
echo "======================================================================"
echo -e "${NC}"

# Environment detection for adaptive behavior
ENVIRONMENT=${ENVIRONMENT:-development}
echo -e "${GREEN}Detected environment: ${ENVIRONMENT}${NC}"

# Neuromorphic deployment phases
function check_prerequisites() {
    echo -e "${BLUE}[1/7] Validating prerequisites...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker not found. Please install Docker to continue.${NC}"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Docker Compose not found. Please install Docker Compose to continue.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All prerequisites satisfied${NC}"
}

function prepare_environment() {
    echo -e "${BLUE}[2/7] Preparing environment...${NC}"
    
    # Create necessary directories
    mkdir -p test-results
    mkdir -p logs
    
    # Set environment variables
    export PYTHONPATH=$(pwd)
    export TESTING=1
    export TEST_MODE=1
    
    echo -e "${GREEN}✓ Environment prepared${NC}"
}

function build_containers() {
    echo -e "${BLUE}[3/7] Building containers...${NC}"
    
    # Build with proper caching and minimal layers
    docker-compose -f docker-compose.test.yml build --no-cache
    
    echo -e "${GREEN}✓ Containers built successfully${NC}"
}

function start_dependencies() {
    echo -e "${BLUE}[4/7] Starting dependencies...${NC}"
    
    # Start database and Redis with health checks
    docker-compose -f docker-compose.test.yml up -d novamind-db-test novamind-redis-test
    
    # Wait for services to be healthy
    echo -e "${YELLOW}Waiting for database to be ready...${NC}"
    until docker-compose -f docker-compose.test.yml exec -T novamind-db-test pg_isready -U postgres; do
        echo -n "."
        sleep 1
    done
    
    echo -e "${GREEN}✓ Dependencies started and healthy${NC}"
}

function run_standalone_tests() {
    echo -e "${BLUE}[5/7] Running standalone tests...${NC}"
    
    # Run tests that don't need external dependencies
    docker-compose -f docker-compose.test.yml run --rm novamind-test-runner python -m scripts.run_tests_by_level standalone --docker --xml
    
    echo -e "${GREEN}✓ Standalone tests completed${NC}"
}

function run_integration_tests() {
    echo -e "${BLUE}[6/7] Running integration tests...${NC}"
    
    # Run tests that require database and other external services
    docker-compose -f docker-compose.test.yml run --rm novamind-test-runner python -m scripts.run_tests_by_level db_required --docker --xml
    
    echo -e "${GREEN}✓ Integration tests completed${NC}"
}

function generate_reports() {
    echo -e "${BLUE}[7/7] Generating reports...${NC}"
    
    # Copy reports from container
    if [ -d "test-results" ]; then
        cp -r test-results/* reports/
    fi
    
    echo -e "${GREEN}✓ Reports generated${NC}"
}

function cleanup() {
    echo -e "${YELLOW}Cleaning up...${NC}"
    
    # Stop all containers
    docker-compose -f docker-compose.test.yml down
    
    echo -e "${GREEN}✓ Cleanup completed${NC}"
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Main orchestration flow - mathematical execution order
check_prerequisites
prepare_environment
build_containers
start_dependencies
run_standalone_tests
run_integration_tests
generate_reports

echo -e "${BLUE}======================================================================"
echo "  DEPLOYMENT AND TESTING COMPLETE"
echo -e "======================================================================${NC}"
