#!/bin/bash

# Run tests for the Zyte API integration

echo "===== Zyte API Integration Tests ====="
echo ""

# Get the project root directory
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.."; pwd)"

# Check if .env file exists in the project root
if [ ! -f "$ROOT_DIR/.env" ]; then
    echo "Error: .env file not found"
    echo "Please create a .env file in the project root with your Zyte API key:"
    echo "ZYTE_API_KEY=your_api_key_here"
    exit 1
fi

# Change to the project root directory to ensure imports work correctly
cd "$ROOT_DIR"

# Test with a simple example URL
echo "Testing with example.com (browser rendering enabled, 15s timeout)"
python3 tests/integration/test_zyte_api.py https://airlogix.io/en --timeout 15
test_result=$?

# Try with a simple website without browser rendering if the first test fails
if [ $test_result -ne 0 ]; then
    echo ""
    echo "First test failed, trying again with browser rendering disabled..."
    python3 tests/integration/test_zyte_api.py https://airlogix.io/en --no-browser --timeout 15
    test_result=$?
fi

# Additional test with a more complex site (if previous tests passed)
if [ $test_result -eq 0 ]; then
    echo ""
    echo "Testing with a more complex site (MDN Web Docs)"
    python3 tests/integration/test_zyte_api.py https://developer.mozilla.org/en-US/docs/Web/HTML --timeout 20
fi

# Show instructions if any tests failed
if [ $test_result -ne 0 ]; then
    echo ""
    echo "=== TROUBLESHOOTING ==="
    echo "1. Check that your Zyte API key is correct in the .env file"
    echo "2. Ensure you have a valid subscription to Zyte API"
    echo "3. Check your internet connection"
    echo "4. Try with --no-browser flag which may be more reliable"
    echo "5. Increase timeout with --timeout parameter (e.g., --timeout 30)"
fi

echo ""
echo "Tests completed."
