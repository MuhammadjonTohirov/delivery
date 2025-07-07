#!/bin/bash

# Run the test suite for the Delivery Platform API

# Display banner
echo "====================================================="
echo "        Delivery Platform API Test Suite"
echo "====================================================="

# Set environment variables for testing
export DJANGO_SETTINGS_MODULE=delivery.settings
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Create tests directory if it doesn't exist
mkdir -p tests

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "Pytest not found. Installing..."
    pip install pytest pytest-django pytest-cov
fi

# Function to run tests with different options
run_tests() {
    local test_type=$1
    local description=$2
    local args=${@:3}
    
    echo ""
    echo "-----------------------------------------------------"
    echo "Running $description"
    echo "-----------------------------------------------------"
    
    pytest $args $test_type -v
    
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "❌ $description failed with exit code $exit_code"
    else
        echo "✅ $description passed"
    fi
    
    return $exit_code
}

# First run only the user tests
run_tests tests/test_users.py "User Authentication Tests"

# Run integration tests
run_tests tests/test_integration.py "Integration Tests"

# Run edge case tests
run_tests tests/test_edge_cases.py "Edge Case Tests"

# Run all tests with coverage
echo ""
echo "-----------------------------------------------------"
echo "Running Complete Test Suite with Coverage Report"
echo "-----------------------------------------------------"
pytest --cov=users --cov=restaurants --cov=orders --cov=drivers --cov-report=term

# Display completion message
echo ""
echo "====================================================="
echo "              Test Suite Completed"
echo "====================================================="
