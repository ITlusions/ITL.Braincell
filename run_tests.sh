#!/bin/bash
# Test execution script for get_relevant_context tests
# Usage: ./run_tests.sh [test_type]

set -e

TEST_DIR="tests"
TEST_FILE="test_get_relevant_context.py"
VENV_PATH=".venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if Python virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    print_warning "Virtual environment not found. Creating..."
    python -m venv $VENV_PATH
    source $VENV_PATH/bin/activate
    pip install -q -r requirements.txt
    print_success "Virtual environment created and requirements installed"
else
    source $VENV_PATH/bin/activate
fi

# Check if test file exists
if [ ! -f "$TEST_DIR/$TEST_FILE" ]; then
    print_error "Test file not found: $TEST_DIR/$TEST_FILE"
    exit 1
fi

# Parse command line arguments
TEST_TYPE="${1:-all}"

case $TEST_TYPE in
    functional)
        print_header "Running Functional Tests"
        pytest -m functional "$TEST_DIR/$TEST_FILE" -v --tb=short
        ;;
    
    edge)
        print_header "Running Edge Case Tests"
        pytest -m edge "$TEST_DIR/$TEST_FILE" -v --tb=short
        ;;
    
    state)
        print_header "Running Memory State Tests"
        pytest -m state "$TEST_DIR/$TEST_FILE" -v --tb=short
        ;;
    
    performance)
        print_header "Running Performance Tests"
        pytest -m performance "$TEST_DIR/$TEST_FILE" -v --tb=short --timeout=60
        ;;
    
    integration)
        print_header "Running Integration Tests"
        pytest -m integration "$TEST_DIR/$TEST_FILE" -v --tb=short
        ;;
    
    critical)
        print_header "Running Critical Path Tests"
        pytest -m critical "$TEST_DIR/$TEST_FILE" -v --tb=short
        ;;
    
    all)
        print_header "Running ALL Tests"
        pytest "$TEST_DIR/$TEST_FILE" -v --tb=short --html=report.html --self-contained-html
        ;;
    
    coverage)
        print_header "Running Tests with Coverage Report"
        pytest "$TEST_DIR/$TEST_FILE" --cov=src --cov-report=html --cov-report=term-missing
        ;;
    
    clean)
        print_header "Cleaning up test artifacts"
        find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
        find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
        find . -name ".coverage" -delete 2>/dev/null || true
        rm -rf htmlcov/ report.html 2>/dev/null || true
        print_success "Cleanup completed"
        ;;
    
    *)
        echo "Usage: $0 [test_type]"
        echo ""
        echo "Available test types:"
        echo "  functional    - Run functional tests only"
        echo "  edge          - Run edge case tests only"
        echo "  state         - Run memory state tests only"
        echo "  performance   - Run performance tests only"
        echo "  integration   - Run integration tests only"
        echo "  critical      - Run critical path tests only"
        echo "  all           - Run all tests (default)"
        echo "  coverage      - Run with coverage report"
        echo "  clean         - Clean up test artifacts"
        exit 1
        ;;
esac

RESULT=$?

if [ $RESULT -eq 0 ]; then
    print_success "Tests completed successfully!"
else
    print_error "Some tests failed! (Exit code: $RESULT)"
fi

exit $RESULT
