#!/bin/bash

# Script to set up and run the Novamind test environment

set -e

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print a header
echo -e "${GREEN}=====================================================================${NC}"
echo -e "${GREEN}               Novamind Test Environment Setup${NC}"
echo -e "${GREEN}=====================================================================${NC}"

# Function to check if Docker is running
check_docker() {
  echo -e "${YELLOW}Checking if Docker is running...${NC}"
  if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker is not running. Please start Docker and try again.${NC}"
    exit 1
  fi
  echo -e "${GREEN}Docker is running.${NC}"
}

# Function to start the test environment
start_test_environment() {
  echo -e "${YELLOW}Starting test environment...${NC}"
  cd "$(dirname "$0")/.." || exit
  
  # Check if containers are already running
  if docker ps --format '{{.Names}}' | grep -q "novamind-db-test"; then
    echo -e "${YELLOW}Test environment is already running. Stopping and removing containers...${NC}"
    docker-compose -f docker-compose.test.yml down
  fi
  
  # Start containers in detached mode
  docker-compose -f docker-compose.test.yml up -d
  
  # Wait for database to be ready
  echo -e "${YELLOW}Waiting for database to be ready...${NC}"
  for i in {1..30}; do
    if docker exec novamind-db-test pg_isready -U postgres > /dev/null 2>&1; then
      echo -e "${GREEN}Database is ready.${NC}"
      break
    fi
    echo -n "."
    sleep 1
    if [ $i -eq 30 ]; then
      echo -e "\n${RED}Database did not become ready in time. Please check the logs.${NC}"
      exit 1
    fi
  done
  
  echo -e "${GREEN}Test environment is up and running.${NC}"
  echo -e "${YELLOW}PostgreSQL is available at localhost:15432${NC}"
  echo -e "${YELLOW}PgAdmin is available at http://localhost:15050${NC}"
  echo -e "${YELLOW}Redis is available at localhost:16379${NC}"
}

# Function to run the tests
run_tests() {
  echo -e "${YELLOW}Setting up environment variables for tests...${NC}"
  export TEST_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:15432/novamind_test"
  export TEST_REDIS_URL="redis://localhost:16379/0"
  export ENVIRONMENT="test"
  
  # Ensure we're in the backend directory
  cd "$(dirname "$0")/.." || exit
  
  # Run the tests
  echo -e "${YELLOW}Running tests...${NC}"
  echo -e "${GREEN}=====================================================================${NC}"
  
  # You can modify the test command based on your needs
  python -m pytest "$@"
  
  EXIT_CODE=$?
  
  echo -e "${GREEN}=====================================================================${NC}"
  
  # Check the exit code
  if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
  else
    echo -e "${RED}Tests failed with exit code $EXIT_CODE${NC}"
  fi
  
  return $EXIT_CODE
}

# Function to clean up the test environment
cleanup() {
  echo -e "${YELLOW}Cleaning up test environment...${NC}"
  cd "$(dirname "$0")/.." || exit
  docker-compose -f docker-compose.test.yml down
  echo -e "${GREEN}Test environment has been stopped and removed.${NC}"
}

# Main execution
case "$1" in
  start)
    check_docker
    start_test_environment
    ;;
  run)
    shift
    run_tests "$@"
    ;;
  stop|clean)
    cleanup
    ;;
  *)
    # Default: start environment and run tests
    check_docker
    start_test_environment
    run_tests
    # Uncomment the following line to automatically clean up after tests
    # cleanup
    ;;
esac

exit 0