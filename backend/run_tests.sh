#!/bin/bash
# Novamind Digital Twin Test Runner
# A clean, pure implementation for executing tests with mathematical precision

set -e

echo "Running Novamind Digital Twin tests with quantum-level precision..."
echo "========================================================================"

# Execute the neural architecture test system
cd "$(dirname "$0")"
./scripts/deploy/deploy_and_test.sh

echo "========================================================================"
echo "Tests completed with neural pathway validation"
