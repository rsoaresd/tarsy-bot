#!/usr/bin/env python3
"""
Comprehensive test runner for SRE AI Agent.

This script provides simple commands to run different categories of tests:
- Integration tests only
- Unit tests only  
- All tests
"""

import argparse
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path


def check_uv_available():
    """Check if uv is available in the system."""
    return shutil.which("uv") is not None

def check_dependencies():
    """Check if test dependencies are available."""
    core_packages = ["pytest", "pytest_asyncio"]
    missing = []
    
    for package in core_packages:
        spec = importlib.util.find_spec(package.replace("-", "_"))
        if spec is None:
            missing.append(package)
    
    if missing:
        print("❌ Missing test dependencies:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\n💡 Install test dependencies with:")
        if check_uv_available():
            print("   uv sync --extra test")
        else:
            print("   pip install -e '.[test]'")
        return False
    
    return True

def run_tests(test_type, verbose=False):
    """Run tests based on the specified type."""
    
    # Add project root to Python path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # Check if uv is available
    uv_available = check_uv_available()
    if uv_available:
        print("✅ Using uv for fast dependency management")
    else:
        print("ℹ️  uv not found, using standard pip")
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Build base command
    if uv_available:
        base_cmd = ["uv", "run", "python", "-m", "pytest"]
    else:
        base_cmd = [sys.executable, "-m", "pytest"]
    
    # Configure command based on test type
    if test_type == "integration":
        cmd = base_cmd + [
            "tests/integration/",
            "-m", "integration",
            "--durations=10",
        ]
        test_description = "Integration Tests"
    elif test_type == "unit":
        cmd = base_cmd + [
            "tests/unit/",
            "--durations=10",
        ]  
        test_description = "Unit Tests"
    elif test_type == "all":
        cmd = base_cmd + [
            "tests/",
            "--durations=10",
        ]
        test_description = "All Tests"
    else:
        print(f"❌ Unknown test type: {test_type}")
        return 1
    
    # Add verbose flag if requested
    if verbose:
        cmd.append("-v")
    
    print(f"🚀 Running SRE AI Agent {test_description}")
    print("=" * 60)
    print(f"Command: {' '.join(cmd)}")
    print(f"Working Directory: {project_root}")
    print(f"Test Type: {test_type}")
    print("=" * 60)
    
    # Run tests
    try:
        result = subprocess.run(cmd, cwd=project_root)
        if result.returncode == 0:
            print(f"\n✅ All {test_description.lower()} passed!")
            return 0
        else:
            print(f"\n❌ Some {test_description.lower()} failed!")
            return result.returncode
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Error running tests: {e}")
        return 1

def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Run SRE AI Agent tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py integration  # Run integration tests only
  python run_tests.py unit         # Run unit tests only  
  python run_tests.py all          # Run all tests
  python run_tests.py all -v       # Run all tests with verbose output
        """
    )
    
    parser.add_argument(
        "test_type",
        choices=["integration", "unit", "all"],
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    return run_tests(args.test_type, args.verbose)

if __name__ == "__main__":
    sys.exit(main()) 