"""
Timestamp utilities for tarsy.

Provides common timestamp functions used across the application.
"""

from datetime import datetime, timezone


def now_us() -> int:
    """Get current timestamp as microseconds since epoch (UTC)."""
    return int(datetime.now(timezone.utc).timestamp() * 1000000)