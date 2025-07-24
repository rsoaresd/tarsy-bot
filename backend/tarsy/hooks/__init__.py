"""
Event hooks package for transparent integration with existing services.

Provides event hook infrastructure for capturing LLM interactions and MCP
communications without modifying core service logic, with both history logging
and dashboard broadcasting capabilities.
"""

from .base_hooks import BaseEventHook, HookContext, HookManager
from .history_hooks import LLMHooks, MCPHooks, register_history_hooks
from .dashboard_hooks import DashboardLLMHooks, DashboardMCPHooks, register_dashboard_hooks, register_integrated_hooks

__all__ = [
    "BaseEventHook", 
    "HookManager", 
    "HookContext", 
    "LLMHooks", 
    "MCPHooks",
    "DashboardLLMHooks",
    "DashboardMCPHooks", 
    "register_history_hooks",
    "register_dashboard_hooks",
    "register_integrated_hooks"
] 