#!/usr/bin/env python3
"""
Simple script to run all tests (unit + integration).
"""

import sys
from pathlib import Path

# Add the parent directory to import run_tests
sys.path.insert(0, str(Path(__file__).parent))

try:
    from run_dashboard_tests import run_tests
except ImportError:
    print("❌ Error: Could not import test runner")
    print("Make sure run_dashboard_tests.py exists in the tests directory")
    sys.exit(1)

if __name__ == "__main__":
    # Run all tests with verbose output
    success = run_tests("all", verbose=True)
    sys.exit(0 if success else 1) 