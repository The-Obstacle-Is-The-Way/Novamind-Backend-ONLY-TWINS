#!/bin/bash
# Test runner script for Novamind Digital Twin Backend
# This script sets up the environment and runs the tests

set -e

# Display a header
echo "==============================================="
echo "  Novamind Digital Twin Backend Test Runner   "
echo "==============================================="

# Set environment variables for testing if .env.test doesn't exist
if [ ! -f ".env.test" ]; then
    echo "Creating default .env.test file..."
    cat > .env.test << EOF
# Environment configuration for testing
ENVIRONMENT=test
TESTING=true
LOG_LEVEL=DEBUG

# Database configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:15432/novamind_test
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:15432/novamind_test
SQLALCHEMY_DATABASE_URI=postgresql+asyncpg://postgres:postgres@localhost:15432/novamind_test

# Security settings
SECRET_KEY=test-key-long-enough-for-testing-purposes-only
ENCRYPTION_KEY=test-encryption-key-32-bytes-long!!
JWT_SECRET_KEY=test-jwt-secret-key-for-testing-only

# Audit logging
AUDIT_LOG_LEVEL=20
AUDIT_LOG_TO_FILE=False
EXTERNAL_AUDIT_ENABLED=False

# Authentication
AUTH_DISABLED=false
TEST_USER_ID=test-user-123
TEST_USER_ROLES=clinician,researcher

# PHI Settings
PHI_DETECTION_ENABLED=true
PHI_REDACTION_ENABLED=true
PHI_AUDIT_ENABLED=true

# Performance
ASYNC_TASKS_ENABLED=false
EOF
fi

# Check if Docker is running
echo "Checking Docker status..."
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running or not accessible."
    echo "Please start Docker and try again."
    exit 1
fi

# Check if the test database container is running, if not start it
echo "Checking test database..."
if ! docker-compose -f docker-compose.test.yml ps | grep -q "postgres"; then
    echo "Starting test database..."
    docker-compose -f docker-compose.test.yml up -d postgres
    
    # Wait for the database to be ready
    echo "Waiting for database to be ready..."
    for i in {1..30}; do
        if docker-compose -f docker-compose.test.yml exec postgres pg_isready -U postgres > /dev/null 2>&1; then
            echo "Database is ready!"
            break
        fi
        echo -n "."
        sleep 1
    done
    echo ""
else
    echo "Test database is already running."
fi

# Install test dependencies if needed
if [ "$1" == "--install" ] || [ "$1" == "-i" ]; then
    echo "Installing test dependencies..."
    pip install -r requirements-dev.txt
    shift  # Remove the first argument
fi

# Prepare coverage paths
COVERAGE_DIR="coverage_html"
mkdir -p "$COVERAGE_DIR"

# Run the tests
echo "Running tests..."
if [ $# -eq 0 ]; then
    # No arguments, run all tests with coverage
    python -m pytest app/tests/ -v --cov=app --cov-report=term --cov-report=html:$COVERAGE_DIR
else
    # Run with provided arguments
    python -m pytest "$@"
fi

TEST_EXIT_CODE=$?

# Generate coverage report
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "Tests passed successfully!"
    echo "Generating coverage report..."
    coverage report -m
    coverage xml -o coverage.xml
    coverage json -o coverage.json
    
    echo "Coverage report generated at:"
    echo "  HTML: $COVERAGE_DIR/index.html"
    echo "  XML: coverage.xml"
    echo "  JSON: coverage.json"
else
    echo "Tests failed with exit code $TEST_EXIT_CODE"
fi

# Ask if user wants to shut down the test database
if [ "$TEST_EXIT_CODE" -eq 0 ]; then
    read -p "Do you want to shut down the test database container? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Shutting down test database..."
        docker-compose -f docker-compose.test.yml down
    fi
fi

exit $TEST_EXIT_CODE