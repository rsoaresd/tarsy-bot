"""
Base event hook infrastructure for transparent service integration.

Provides the foundation for event hooks that capture data from existing services
without modifying their core logic, with comprehensive error handling to prevent
hooks from breaking parent operations.
"""

import asyncio
import functools
import inspect
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class HookContext:
    """
    Context manager for handling hook lifecycle with automatic timing and error handling.
    
    Eliminates code duplication in service integrations by providing a standardized
    way to handle pre/post/error hooks with timing and context management.
    """
    
    def __init__(self, service_type: str, method_name: str, session_id: Optional[str] = None, **method_args):
        """
        Initialize hook context.
        
        Args:
            service_type: Type of service (e.g., 'llm', 'mcp')
            method_name: Name of the method being hooked
            session_id: Session ID for history tracking
            **method_args: Method arguments to include in context
        """
        self.service_type = service_type
        self.method_name = method_name
        self.session_id = session_id
        self.method_args = method_args
        
        # Generate unique request ID and timing
        self.request_id = str(uuid.uuid4())[:8]
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # Hook context and manager
        self.hook_context: Dict[str, Any] = {}
        self.hook_manager: Optional[HookManager] = None
        
    async def __aenter__(self) -> 'HookContext':
        """Enter the hook context and trigger pre-execution hooks."""
        self.start_time = datetime.now(timezone.utc)
        self.hook_manager = get_hook_manager()
        
        # Prepare hook context for pre-execution
        self.hook_context = {
            'session_id': self.session_id,
            'method': self.method_name,
            'args': {
                'request_id': self.request_id,
                **self.method_args
            },
            'start_time': self.start_time,
            'timestamp': self.start_time
        }
        
        # Trigger pre-execution hooks
        await self.hook_manager.trigger_hooks(f"{self.service_type}.pre", **self.hook_context)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the hook context and trigger post/error hooks based on outcome."""
        self.end_time = datetime.now(timezone.utc)
        
        if exc_type is None:
            # Success case - will be updated with result via complete_success()
            pass
        else:
            # Error case - trigger error hooks
            self.hook_context.update({
                'error': str(exc_val) if exc_val else 'Unknown error',
                'end_time': self.end_time,
                'success': False
            })
            
            if self.hook_manager:
                await self.hook_manager.trigger_hooks(f"{self.service_type}.error", **self.hook_context)
        
        # Don't suppress exceptions
        return False
    
    async def complete_success(self, result: Any) -> None:
        """
        Mark the operation as successful and trigger post-execution hooks.
        
        Args:
            result: The result of the operation
        """
        if not self.end_time:
            self.end_time = datetime.now(timezone.utc)
            
        self.hook_context.update({
            'result': result,
            'end_time': self.end_time,
            'success': True
        })
        
        if self.hook_manager:
            await self.hook_manager.trigger_hooks(f"{self.service_type}.post", **self.hook_context)
    
    def get_request_id(self) -> str:
        """Get the generated request ID for logging purposes."""
        return self.request_id
    
    def get_duration_ms(self) -> int:
        """Get the operation duration in milliseconds."""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return 0


class BaseEventHook(ABC):
    """
    Abstract base class for event hooks.
    
    Provides the foundation for all event hooks with error handling,
    async support, and registration management.
    """
    
    def __init__(self, name: str):
        """
        Initialize base event hook.
        
        Args:
            name: Unique name for this hook
        """
        self.name = name
        self.is_enabled = True
        self.error_count = 0
        self.max_errors = 5  # Disable hook after 5 consecutive errors
    
    @abstractmethod
    async def execute(self, event_type: str, **kwargs) -> None:
        """
        Execute the hook logic.
        
        Args:
            event_type: Type of event being hooked
            **kwargs: Event-specific data
        """
        pass
    
    def enable(self) -> None:
        """Enable this hook."""
        self.is_enabled = True
        self.error_count = 0
        logger.info(f"Hook '{self.name}' enabled")
    
    def disable(self) -> None:
        """Disable this hook."""
        self.is_enabled = False
        logger.info(f"Hook '{self.name}' disabled")
    
    async def safe_execute(self, event_type: str, **kwargs) -> bool:
        """
        Safely execute the hook with error handling.
        
        Args:
            event_type: Type of event being hooked
            **kwargs: Event-specific data
            
        Returns:
            True if executed successfully, False otherwise
        """
        if not self.is_enabled:
            return False
        
        try:
            await self.execute(event_type, **kwargs)
            self.error_count = 0  # Reset error count on success
            return True
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Hook '{self.name}' error ({self.error_count}/{self.max_errors}): {e}")
            
            # Disable hook if too many errors
            if self.error_count >= self.max_errors:
                self.disable()
                logger.warning(f"Hook '{self.name}' disabled due to excessive errors")
            
            return False


class HookManager:
    """
    Manages registration and execution of event hooks.
    
    Provides centralized hook management with async execution,
    error isolation, and performance monitoring.
    """
    
    def __init__(self):
        """Initialize hook manager."""
        self.hooks: Dict[str, List[BaseEventHook]] = {}
        self.execution_stats: Dict[str, Dict[str, int]] = {}
    
    def register_hook(self, event_type: str, hook: BaseEventHook) -> None:
        """
        Register a hook for a specific event type.
        
        Args:
            event_type: The event type to hook
            hook: The hook instance to register
        """
        if event_type not in self.hooks:
            self.hooks[event_type] = []
        
        self.hooks[event_type].append(hook)
        logger.info(f"Registered hook '{hook.name}' for event type '{event_type}'")
    
    def unregister_hook(self, event_type: str, hook_name: str) -> bool:
        """
        Unregister a hook by name.
        
        Args:
            event_type: The event type
            hook_name: Name of the hook to remove
            
        Returns:
            True if hook was found and removed, False otherwise
        """
        if event_type not in self.hooks:
            return False
        
        for i, hook in enumerate(self.hooks[event_type]):
            if hook.name == hook_name:
                del self.hooks[event_type][i]
                logger.info(f"Unregistered hook '{hook_name}' from event type '{event_type}'")
                return True
        
        return False
    
    async def trigger_hooks(self, event_type: str, **kwargs) -> Dict[str, bool]:
        """
        Trigger all hooks for a specific event type.
        
        Args:
            event_type: The event type to trigger
            **kwargs: Event data to pass to hooks
            
        Returns:
            Dictionary mapping hook names to execution success status
        """
        if event_type not in self.hooks:
            return {}
        
        # Initialize stats if needed
        if event_type not in self.execution_stats:
            self.execution_stats[event_type] = {"total": 0, "success": 0, "failed": 0}
        
        results = {}
        start_time = datetime.now(timezone.utc)
        
        # Execute all hooks concurrently for better performance
        tasks = []
        hook_names = []
        
        for hook in self.hooks[event_type]:
            if hook.is_enabled:
                tasks.append(hook.safe_execute(event_type, **kwargs))
                hook_names.append(hook.name)
        
        if tasks:
            # Execute hooks concurrently but don't let them block each other
            try:
                # Use asyncio.gather with return_exceptions=True to prevent one hook failure from affecting others
                hook_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for hook_name, result in zip(hook_names, hook_results, strict=False):
                    if isinstance(result, Exception):
                        logger.error(f"Hook '{hook_name}' raised exception: {result}")
                        results[hook_name] = False
                        self.execution_stats[event_type]["failed"] += 1
                    else:
                        results[hook_name] = result
                        if result:
                            self.execution_stats[event_type]["success"] += 1
                        else:
                            self.execution_stats[event_type]["failed"] += 1
                
                self.execution_stats[event_type]["total"] += len(hook_results)
                
            except Exception as e:
                logger.error(f"Unexpected error executing hooks for '{event_type}': {e}")
                for hook_name in hook_names:
                    results[hook_name] = False
        
        duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        logger.debug(f"Triggered {len(results)} hooks for '{event_type}' in {duration:.1f}ms")
        
        return results
    
    def get_hook_stats(self) -> Dict[str, Any]:
        """
        Get hook execution statistics.
        
        Returns:
            Dictionary containing execution statistics
        """
        stats = {
            "event_types": len(self.hooks),
            "total_hooks": sum(len(hooks) for hooks in self.hooks.values()),
            "enabled_hooks": sum(len([h for h in hooks if h.is_enabled]) for hooks in self.hooks.values()),
            "execution_stats": self.execution_stats.copy()
        }
        
        # Add per-hook status
        hook_status = {}
        for event_type, hooks in self.hooks.items():
            hook_status[event_type] = [
                {"name": hook.name, "enabled": hook.is_enabled, "error_count": hook.error_count}
                for hook in hooks
            ]
        stats["hook_status"] = hook_status
        
        return stats


def create_sync_hook_wrapper(func: Callable) -> Callable:
    """
    Create a wrapper that converts sync functions to async hooks.
    
    Args:
        func: Synchronous function to wrap
        
    Returns:
        Async wrapper function
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Run sync function in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))
    
    return async_wrapper


def hook_decorator(hook_manager: HookManager, event_type: str):
    """
    Decorator to automatically trigger hooks before/after method execution.
    
    Args:
        hook_manager: The hook manager instance
        event_type: Event type to trigger
        
    Returns:
        Method decorator
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # Extract method arguments for hook context
            sig = inspect.signature(func)
            bound_args = sig.bind(self, *args, **kwargs)
            bound_args.apply_defaults()
            
            # Trigger pre-hooks
            hook_context = {
                "method": func.__name__,
                "args": bound_args.arguments,
                "timestamp": datetime.now(timezone.utc),
                "phase": "pre"
            }
            
            await hook_manager.trigger_hooks(f"{event_type}.pre", **hook_context)
            
            try:
                # Execute original method
                if asyncio.iscoroutinefunction(func):
                    result = await func(self, *args, **kwargs)
                else:
                    result = func(self, *args, **kwargs)
                
                # Trigger post-hooks with result
                hook_context.update({
                    "phase": "post",
                    "result": result,
                    "success": True
                })
                
                await hook_manager.trigger_hooks(f"{event_type}.post", **hook_context)
                return result
                
            except Exception as e:
                # Trigger error hooks
                hook_context.update({
                    "phase": "error",
                    "error": str(e),
                    "success": False
                })
                
                await hook_manager.trigger_hooks(f"{event_type}.error", **hook_context)
                raise
        
        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            # For sync methods, create async wrapper and run it
            return asyncio.run(async_wrapper(self, *args, **kwargs))
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global hook manager instance
_global_hook_manager: Optional[HookManager] = None


def get_hook_manager() -> HookManager:
    """
    Get the global hook manager instance.
    
    Returns:
        Global HookManager instance
    """
    global _global_hook_manager
    if _global_hook_manager is None:
        _global_hook_manager = HookManager()
    return _global_hook_manager


def generate_step_description(operation: str, context: Dict[str, Any]) -> str:
    """
    Generate human-readable step descriptions for timeline visualization.
    
    Args:
        operation: The operation being performed
        context: Context data for the operation
        
    Returns:
        Human-readable step description
    """
    if operation == "llm_interaction":
        model = context.get("model", "unknown")
        purpose = context.get("purpose", "analysis")
        return f"LLM {purpose} using {model}"
    
    elif operation == "mcp_tool_call":
        tool_name = context.get("tool_name", "unknown")
        server = context.get("server", "unknown")
        return f"Execute {tool_name} via {server}"
    
    elif operation == "mcp_tool_discovery":
        server = context.get("server", "unknown")
        return f"Discover available tools from {server}"
    
    else:
        return f"Execute {operation}"


def generate_microsecond_timestamp() -> datetime:
    """
    Generate microsecond-precision timestamp for chronological ordering.
    
    Returns:
        Current timestamp with microsecond precision
    """
    return datetime.now(timezone.utc) 