#!/bin/bash
#
# Script to run tests in Docker containers
# This ensures consistent test environments across different systems
#

set -e  # Exit immediately if a command exits with a non-zero status

# Set base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Base directory: $BASE_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==============================================${NC}"
echo -e "${BLUE}   NOVAMIND DIGITAL TWIN - DOCKER TESTS      ${NC}"
echo -e "${BLUE}==============================================${NC}"

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose could not be found${NC}"
    echo "Please install docker-compose and try again"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker is not running${NC}"
    echo "Please start Docker and try again"
    exit 1
fi

# Function to handle cleanup
cleanup() {
    echo -e "\n${BLUE}Cleaning up containers...${NC}"
    cd "$BASE_DIR"
    docker-compose -f docker-compose.test.yml down
    echo "Clean up complete"
}

# Set up trap to ensure cleanup on exit
trap cleanup EXIT

# Build and run the tests
echo -e "\n${BLUE}Building and running test containers...${NC}"
cd "$BASE_DIR"
docker-compose -f docker-compose.test.yml build --no-cache
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Check the exit code
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ All tests in Docker passed!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some tests in Docker failed!${NC}"
    exit 1
fi