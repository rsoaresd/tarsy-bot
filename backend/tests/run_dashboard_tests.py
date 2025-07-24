#!/usr/bin/env python3
"""
Test runner for Tarsy backend tests.

This script runs unit and integration tests with optional coverage reporting.
It can run all tests or filter by test type (unit/integration).
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_tests(test_type="all", verbose=False, quick=False, coverage=False):
    """
    Run tests with specified options.
    
    Args:
        test_type: Type of tests to run ("unit", "integration", "all")
        verbose: Enable verbose output
        quick: Run quick tests only (skip slow ones)
        coverage: Generate coverage report
    """
    # Get the backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Test selection based on type
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
        print("🧪 Running unit tests only...")
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
        print("🔗 Running integration tests only...")
    else:
        print("🚀 Running all tests (unit + integration)...")
    
    # Add verbose output if requested
    if verbose:
        cmd.append("-v")
    
    # Add quick test filtering
    if quick:
        cmd.extend(["-m", "not slow"])
        print("⚡ Quick mode: Skipping slow tests...")
    
    # Coverage configuration
    if coverage:
        cmd.extend([
            "--cov=tarsy",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=xml:coverage.xml"
        ])
        print("📊 Coverage reporting enabled...")
    
    # Test discovery paths based on test type
    if test_type == "unit":
        test_paths = ["tests/unit"]
    elif test_type == "integration":
        test_paths = ["tests/integration"]
    else:
        test_paths = ["tests/unit", "tests/integration"]
    
    # Add test paths to command
    cmd.extend(test_paths)
    
    # Additional pytest options for better output
    cmd.extend([
        "--tb=short",  # Shorter traceback format
        "--strict-markers",  # Strict marker checking
        "--strict-config",  # Strict config checking
    ])
    
    print(f"Executing: {' '.join(cmd)}")
    print("-" * 80)
    
    try:
        # Run the tests
        result = subprocess.run(cmd, check=False)
        
        if result.returncode == 0:
            print("\n" + "=" * 80)
            print("✅ All tests passed!")
            
            if coverage:
                print("\n📊 Coverage report generated:")
                print("  - HTML: htmlcov/index.html")
                print("  - XML: coverage.xml")
                print("  - Terminal output above")
        else:
            print("\n" + "=" * 80)
            print("❌ Some tests failed!")
            return False
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Error running tests: {e}")
        return False
    
    return True


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="Run Tarsy backend tests with various options",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                     # Run all tests
  %(prog)s --type unit         # Run unit tests only
  %(prog)s --type integration  # Run integration tests only
  %(prog)s --coverage          # Run all tests with coverage
  %(prog)s --quick --verbose   # Quick run with verbose output
  %(prog)s --type unit --coverage --verbose  # Unit tests with coverage and verbose output
        """
    )
    
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "all"],
        default="all",
        help="Type of tests to run (default: all)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose test output"
    )
    
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Skip slow tests for quick feedback"
    )
    
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Generate coverage report"
    )
    
    args = parser.parse_args()
    
    print("🔬 Tarsy Backend Test Runner")
    print(f"📁 Backend directory: {Path(__file__).parent.parent.absolute()}")
    print("-" * 80)
    
    # Run the tests
    success = run_tests(
        test_type=args.type,
        verbose=args.verbose,
        quick=args.quick,
        coverage=args.coverage
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 