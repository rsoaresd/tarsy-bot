#!/usr/bin/env python3
"""
Simple script to run unit tests only.
"""

import sys
from pathlib import Path

# Add the parent directory to import run_tests
sys.path.insert(0, str(Path(__file__).parent))

from run_tests import run_tests

if __name__ == "__main__":
    sys.exit(run_tests("unit", verbose=True)) 