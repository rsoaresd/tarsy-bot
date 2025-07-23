"""
Event hooks package for transparent integration with existing services.

Provides event hook infrastructure for capturing LLM interactions and MCP
communications without modifying core service logic.
"""

from .base_hooks import BaseEventHook, HookManager, HookContext
from .history_hooks import LLMHooks, MCPHooks

__all__ = ["BaseEventHook", "HookManager", "HookContext", "LLMHooks", "MCPHooks"] 