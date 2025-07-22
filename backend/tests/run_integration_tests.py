#!/usr/bin/env python3
"""
Test runner for SRE AI Agent integration tests.

This script sets up the environment and runs comprehensive integration tests
with proper mocking of external services using uv for dependency management.
"""

import sys
import subprocess
from pathlib import Path
import importlib.util
import importlib.metadata
import shutil

def check_uv_available():
    """Check if uv is available in the system."""
    return shutil.which("uv") is not None

def check_dependencies():
    """Check if test dependencies are available."""
    # Check core packages that can be imported directly
    core_packages = ["pytest", "pytest_asyncio"]
    missing = []
    
    for package in core_packages:
        spec = importlib.util.find_spec(package.replace("-", "_"))
        if spec is None:
            missing.append(package)
    
    # Note: pytest-mock is a plugin that loads automatically if installed
    # We don't need to check for it explicitly - pytest will handle it
    
    if missing:
        print("❌ Missing test dependencies:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\n💡 Install test dependencies with:")
        if check_uv_available():
            print("   uv sync --extra test")
        else:
            print("   pip install -e '.[test]'")
            print("   # Consider installing uv for faster dependency management:")
            print("   # curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False
    
    return True

def main():
    """Run integration tests with appropriate configuration."""
    
    # Add project root to Python path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # Check if uv is available and provide helpful message
    uv_available = check_uv_available()
    if uv_available:
        print("✅ Using uv for fast dependency management")
    else:
        print("ℹ️  uv not found, using standard pip (consider installing uv for faster builds)")
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Define test command - now uses pyproject.toml configuration
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/integration/",
        "-m", "integration",  # Run only integration tests
        "--durations=10",  # Show 10 slowest tests
    ]
    
    print("🚀 Running SRE AI Agent Integration Tests")
    print("=" * 60)
    print(f"Command: {' '.join(cmd)}")
    print(f"Working Directory: {project_root}")
    print(f"Dependency Manager: {'uv' if uv_available else 'pip'}")
    print("=" * 60)
    
    # Run tests
    try:
        result = subprocess.run(cmd, cwd=project_root)
        if result.returncode == 0:
            print("\n✅ All integration tests passed!")
            return 0
        else:
            print("\n❌ Some integration tests failed!")
            return result.returncode
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 