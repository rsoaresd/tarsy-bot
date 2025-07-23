"""
Repository package for database abstraction layer.

Provides database access patterns and CRUD operations for the tarsy system.
"""

from .base_repository import BaseRepository
from .history_repository import HistoryRepository

__all__ = ["BaseRepository", "HistoryRepository"] 