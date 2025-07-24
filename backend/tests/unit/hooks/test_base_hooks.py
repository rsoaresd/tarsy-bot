"""
Unit tests for Base Hooks infrastructure.

Tests the foundational hook infrastructure including utility functions,
context management, hook execution, and registration management.
"""

import asyncio
import pytest
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch

from tarsy.hooks.base_hooks import (
    generate_step_description,
    generate_microsecond_timestamp,
    HookContext,
    BaseEventHook,
    HookManager,
    get_hook_manager,
    create_sync_hook_wrapper,
    hook_decorator
)


class TestGenerateStepDescription:
    """Test the generate_step_description utility function."""

    @pytest.mark.unit
    def test_llm_interaction_description(self):
        """Test step description generation for LLM interactions."""
        context = {
            "model": "gpt-4",
            "purpose": "analysis",
            "has_tools": True
        }
        
        description = generate_step_description("llm_interaction", context)
        assert description == "LLM analysis using gpt-4"

    @pytest.mark.unit
    def test_llm_interaction_default_purpose(self):
        """Test LLM interaction with default purpose."""
        context = {
            "model": "claude-3",
            # No purpose specified
        }
        
        description = generate_step_description("llm_interaction", context)
        assert description == "LLM analysis using claude-3"

    @pytest.mark.unit
    def test_llm_interaction_unknown_model(self):
        """Test LLM interaction with unknown model."""
        context = {
            "purpose": "resolution"
            # No model specified
        }
        
        description = generate_step_description("llm_interaction", context)
        assert description == "LLM resolution using unknown"

    @pytest.mark.unit
    def test_mcp_tool_call_description(self):
        """Test step description generation for MCP tool calls."""
        context = {
            "tool_name": "kubectl-get-pods",
            "server": "kubernetes"
        }
        
        description = generate_step_description("mcp_tool_call", context)
        assert description == "Execute kubectl-get-pods via kubernetes"

    @pytest.mark.unit
    def test_mcp_tool_call_default_values(self):
        """Test MCP tool call with default values."""
        context = {}  # Empty context
        
        description = generate_step_description("mcp_tool_call", context)
        assert description == "Execute unknown via unknown"

    @pytest.mark.unit
    def test_mcp_tool_discovery_description(self):
        """Test step description generation for MCP tool discovery."""
        context = {
            "server": "filesystem"
        }
        
        description = generate_step_description("mcp_tool_discovery", context)
        assert description == "Discover available tools from filesystem"

    @pytest.mark.unit
    def test_mcp_tool_discovery_default_server(self):
        """Test MCP tool discovery with default server."""
        context = {}  # Empty context
        
        description = generate_step_description("mcp_tool_discovery", context)
        assert description == "Discover available tools from unknown"

    @pytest.mark.unit
    def test_unknown_operation_fallback(self):
        """Test fallback for unknown operations."""
        context = {"some": "data"}
        
        description = generate_step_description("custom_operation", context)
        assert description == "Execute custom_operation"

    @pytest.mark.unit
    def test_empty_operation_fallback(self):
        """Test fallback for empty operation."""
        context = {"some": "data"}
        
        description = generate_step_description("", context)
        assert description == "Execute "


class TestGenerateMicrosecondTimestamp:
    """Test the generate_microsecond_timestamp utility function."""

    @pytest.mark.unit
    def test_returns_datetime_with_timezone(self):
        """Test that function returns datetime with UTC timezone."""
        timestamp = generate_microsecond_timestamp()
        
        assert isinstance(timestamp, datetime)
        assert timestamp.tzinfo == timezone.utc

    @pytest.mark.unit
    def test_microsecond_precision(self):
        """Test that timestamp has microsecond precision."""
        timestamp = generate_microsecond_timestamp()
        
        # Should have microsecond component (non-zero most of the time)
        assert hasattr(timestamp, 'microsecond')
        assert 0 <= timestamp.microsecond <= 999999

    @pytest.mark.unit
    def test_consecutive_timestamps_different(self):
        """Test that consecutive calls return different timestamps."""
        timestamp1 = generate_microsecond_timestamp()
        timestamp2 = generate_microsecond_timestamp()
        
        # They should be different (at least by microseconds)
        assert timestamp1 != timestamp2
        assert timestamp2 > timestamp1

    @pytest.mark.unit
    def test_timestamp_recent(self):
        """Test that timestamp is recent (within last second)."""
        before = datetime.now(timezone.utc)
        timestamp = generate_microsecond_timestamp()
        after = datetime.now(timezone.utc)
        
        assert before <= timestamp <= after
        assert (timestamp - before).total_seconds() < 1


class TestHookContext:
    """Test the HookContext class for lifecycle and timing management."""

    @pytest.mark.unit
    def test_initialization(self):
        """Test HookContext initialization."""
        context = HookContext(
            service_type="test_service",
            method_name="test_method",
            session_id="test_session_123",
            param1="value1",
            param2="value2"
        )
        
        assert context.service_type == "test_service"
        assert context.method_name == "test_method"
        assert context.session_id == "test_session_123"
        assert context.method_args == {"param1": "value1", "param2": "value2"}
        assert context.start_time is None
        assert context.end_time is None
        assert len(context.request_id) == 8  # UUID truncated to 8 chars
        assert context.hook_context == {}
        assert context.hook_manager is None

    @pytest.mark.unit
    def test_initialization_without_session_id(self):
        """Test HookContext initialization without session ID."""
        context = HookContext(
            service_type="llm",
            method_name="generate",
            prompt="test prompt"
        )
        
        assert context.session_id is None
        assert context.method_args == {"prompt": "test prompt"}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_context_manager_success_flow(self):
        """Test HookContext as async context manager with success flow."""
        mock_hook_manager = Mock()
        mock_hook_manager.trigger_hooks = AsyncMock()
        
        with patch('tarsy.hooks.base_hooks.get_hook_manager', return_value=mock_hook_manager):
            context = HookContext("test", "method", session_id="session123", param="value")
            
            async with context as ctx:
                assert ctx is context
                assert context.start_time is not None
                assert context.hook_manager == mock_hook_manager
                assert "session_id" in context.hook_context
                assert "start_time" in context.hook_context
                assert context.hook_context["session_id"] == "session123"
                
                # Verify pre-hooks were triggered (check immediately after context entry)
                assert mock_hook_manager.trigger_hooks.call_count == 1
                pre_call = mock_hook_manager.trigger_hooks.call_args_list[0]
                assert pre_call[0][0] == "test.pre"
                pre_context = pre_call[1]
                assert pre_context["session_id"] == "session123"
                assert "start_time" in pre_context
                
                # Simulate some work
                result_data = {"status": "success", "data": "processed"}
                await context.complete_success(result_data)
            
            # Verify post-hooks were triggered
            assert mock_hook_manager.trigger_hooks.call_count == 2
            post_call = mock_hook_manager.trigger_hooks.call_args_list[1]
            assert post_call[0][0] == "test.post"
            post_context = post_call[1]
            assert post_context["result"] == result_data
            assert post_context["success"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_context_manager_error_flow(self):
        """Test HookContext with exception handling."""
        mock_hook_manager = Mock()
        mock_hook_manager.trigger_hooks = AsyncMock()
        
        with patch('tarsy.hooks.base_hooks.get_hook_manager', return_value=mock_hook_manager):
            context = HookContext("test", "method", session_id="session456")
            
            with pytest.raises(ValueError, match="Test error"):
                async with context:
                    raise ValueError("Test error")
            
            # Verify error hooks were triggered
            assert mock_hook_manager.trigger_hooks.call_count == 2
            error_call = mock_hook_manager.trigger_hooks.call_args_list[1]
            assert error_call[0][0] == "test.error"
            error_context = error_call[1]
            assert error_context["error"] == "Test error"
            assert error_context["success"] is False

    @pytest.mark.unit
    def test_get_request_id(self):
        """Test getting the request ID."""
        context = HookContext("test", "method")
        request_id = context.get_request_id()
        
        assert isinstance(request_id, str)
        assert len(request_id) == 8
        assert request_id == context.request_id

    @pytest.mark.unit
    def test_get_duration_ms_without_times(self):
        """Test duration calculation without start/end times."""
        context = HookContext("test", "method")
        duration = context.get_duration_ms()
        
        assert duration == 0

    @pytest.mark.unit
    def test_get_duration_ms_with_times(self):
        """Test duration calculation with start/end times."""
        context = HookContext("test", "method")
        context.start_time = datetime.now(timezone.utc)
        context.end_time = context.start_time + timedelta(milliseconds=1500)
        
        duration = context.get_duration_ms()
        assert duration == 1500

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_complete_success_sets_end_time(self):
        """Test that complete_success sets end time if not already set."""
        mock_hook_manager = Mock()
        mock_hook_manager.trigger_hooks = AsyncMock()
        
        context = HookContext("test", "method")
        context.hook_manager = mock_hook_manager
        context.hook_context = {"session_id": "test"}
        
        result_data = {"result": "success"}
        await context.complete_success(result_data)
        
        assert context.end_time is not None
        assert context.hook_context["result"] == result_data
        assert context.hook_context["success"] is True
        mock_hook_manager.trigger_hooks.assert_called_once_with("test.post", **context.hook_context)


class TestConcreteHook(BaseEventHook):
    """Concrete implementation of BaseEventHook for testing."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.execution_log = []
    
    async def execute(self, event_type: str, **kwargs) -> None:
        """Log execution for testing."""
        self.execution_log.append({
            "event_type": event_type,
            "kwargs": kwargs
        })


class TestFailingHook(BaseEventHook):
    """Hook that always fails for testing error handling."""
    
    def __init__(self, name: str, error_message: str = "Test error"):
        super().__init__(name)
        self.error_message = error_message
    
    async def execute(self, event_type: str, **kwargs) -> None:
        """Always raise an exception."""
        raise Exception(self.error_message)


class TestBaseEventHook:
    """Test the BaseEventHook abstract base class."""

    @pytest.mark.unit
    def test_initialization(self):
        """Test BaseEventHook initialization."""
        hook = TestConcreteHook("test_hook")
        
        assert hook.name == "test_hook"
        assert hook.is_enabled is True
        assert hook.error_count == 0
        assert hook.max_errors == 5

    @pytest.mark.unit
    def test_enable_disable(self):
        """Test hook enable/disable functionality."""
        hook = TestConcreteHook("test_hook")
        
        # Test disable
        hook.disable()
        assert hook.is_enabled is False
        
        # Test enable
        hook.enable()
        assert hook.is_enabled is True
        assert hook.error_count == 0  # Reset on enable

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_safe_execute_success(self):
        """Test successful hook execution."""
        hook = TestConcreteHook("test_hook")
        
        result = await hook.safe_execute("test.event", param1="value1", param2="value2")
        
        assert result is True
        assert len(hook.execution_log) == 1
        assert hook.execution_log[0]["event_type"] == "test.event"
        assert hook.execution_log[0]["kwargs"] == {"param1": "value1", "param2": "value2"}
        assert hook.error_count == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_safe_execute_when_disabled(self):
        """Test that disabled hooks don't execute."""
        hook = TestConcreteHook("test_hook")
        hook.disable()
        
        result = await hook.safe_execute("test.event", param="value")
        
        assert result is False
        assert len(hook.execution_log) == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_safe_execute_error_handling(self):
        """Test error handling in safe_execute."""
        hook = TestFailingHook("failing_hook", "Test failure")
        
        result = await hook.safe_execute("test.event")
        
        assert result is False
        assert hook.error_count == 1
        assert hook.is_enabled is True  # Still enabled after first error

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_safe_execute_auto_disable_after_max_errors(self):
        """Test automatic disable after max errors reached."""
        hook = TestFailingHook("failing_hook", "Persistent failure")
        
        # Execute multiple times to reach max_errors
        for i in range(6):  # max_errors is 5
            result = await hook.safe_execute("test.event")
            assert result is False
            
            if i < 4:  # 0-4 (5 errors)
                assert hook.is_enabled is True
                assert hook.error_count == i + 1
            else:  # 5th error and beyond
                assert hook.is_enabled is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_safe_execute_error_count_reset_on_success(self):
        """Test that error count resets on successful execution."""
        # Create a hook that fails then succeeds
        hook = TestConcreteHook("test_hook")
        
        # Manually set error count
        hook.error_count = 3
        
        result = await hook.safe_execute("test.event")
        
        assert result is True
        assert hook.error_count == 0  # Reset on success


class TestHookManager:
    """Test the HookManager class for hook registration and execution."""

    @pytest.fixture
    def hook_manager(self):
        """Create a fresh HookManager instance."""
        return HookManager()

    @pytest.fixture
    def test_hooks(self):
        """Create test hooks for registration."""
        return [
            TestConcreteHook("hook1"),
            TestConcreteHook("hook2"),
            TestConcreteHook("hook3")
        ]

    @pytest.mark.unit
    def test_initialization(self, hook_manager):
        """Test HookManager initialization."""
        assert hook_manager.hooks == {}
        assert hook_manager.execution_stats == {}

    @pytest.mark.unit
    def test_register_hook(self, hook_manager, test_hooks):
        """Test hook registration."""
        hook = test_hooks[0]
        
        hook_manager.register_hook("test.event", hook)
        
        assert "test.event" in hook_manager.hooks
        assert len(hook_manager.hooks["test.event"]) == 1
        assert hook_manager.hooks["test.event"][0] == hook

    @pytest.mark.unit
    def test_register_multiple_hooks_same_event(self, hook_manager, test_hooks):
        """Test registering multiple hooks for the same event."""
        for hook in test_hooks:
            hook_manager.register_hook("test.event", hook)
        
        assert len(hook_manager.hooks["test.event"]) == 3
        assert all(hook in hook_manager.hooks["test.event"] for hook in test_hooks)

    @pytest.mark.unit
    def test_unregister_hook_success(self, hook_manager, test_hooks):
        """Test successful hook unregistration."""
        hook = test_hooks[0]
        hook_manager.register_hook("test.event", hook)
        
        result = hook_manager.unregister_hook("test.event", "hook1")
        
        assert result is True
        assert len(hook_manager.hooks["test.event"]) == 0

    @pytest.mark.unit
    def test_unregister_hook_not_found(self, hook_manager):
        """Test unregistering non-existent hook."""
        result = hook_manager.unregister_hook("test.event", "nonexistent")
        assert result is False

    @pytest.mark.unit
    def test_unregister_hook_event_not_found(self, hook_manager):
        """Test unregistering hook from non-existent event."""
        result = hook_manager.unregister_hook("nonexistent.event", "hook1")
        assert result is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_trigger_hooks_success(self, hook_manager, test_hooks):
        """Test successful hook triggering."""
        for hook in test_hooks:
            hook_manager.register_hook("test.event", hook)
        
        results = await hook_manager.trigger_hooks("test.event", param1="value1", param2="value2")
        
        assert len(results) == 3
        assert all(result is True for result in results.values())
        assert set(results.keys()) == {"hook1", "hook2", "hook3"}
        
        # Verify all hooks were executed
        for hook in test_hooks:
            assert len(hook.execution_log) == 1
            assert hook.execution_log[0]["kwargs"]["param1"] == "value1"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_trigger_hooks_no_hooks_registered(self, hook_manager):
        """Test triggering hooks when none are registered."""
        results = await hook_manager.trigger_hooks("nonexistent.event", param="value")
        
        assert results == {}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_trigger_hooks_with_disabled_hook(self, hook_manager, test_hooks):
        """Test that disabled hooks are not triggered."""
        hook1, hook2 = test_hooks[0], test_hooks[1]
        hook_manager.register_hook("test.event", hook1)
        hook_manager.register_hook("test.event", hook2)
        
        hook2.disable()
        
        results = await hook_manager.trigger_hooks("test.event", param="value")
        
        assert len(results) == 1
        assert "hook1" in results
        assert results["hook1"] is True
        assert len(hook1.execution_log) == 1
        assert len(hook2.execution_log) == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_trigger_hooks_with_failing_hook(self, hook_manager):
        """Test hook triggering with one failing hook."""
        good_hook = TestConcreteHook("good_hook")
        bad_hook = TestFailingHook("bad_hook", "Test failure")
        
        hook_manager.register_hook("test.event", good_hook)
        hook_manager.register_hook("test.event", bad_hook)
        
        results = await hook_manager.trigger_hooks("test.event", param="value")
        
        assert len(results) == 2
        assert results["good_hook"] is True
        assert results["bad_hook"] is False
        assert len(good_hook.execution_log) == 1
        assert bad_hook.error_count == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_trigger_hooks_execution_stats(self, hook_manager, test_hooks):
        """Test that execution statistics are tracked."""
        for hook in test_hooks:
            hook_manager.register_hook("test.event", hook)
        
        await hook_manager.trigger_hooks("test.event", param="value")
        
        assert "test.event" in hook_manager.execution_stats
        stats = hook_manager.execution_stats["test.event"]
        assert stats["total"] == 3
        assert stats["success"] == 3
        assert stats["failed"] == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_trigger_hooks_mixed_success_failure_stats(self, hook_manager):
        """Test execution statistics with mixed success/failure."""
        good_hook = TestConcreteHook("good_hook")
        bad_hook = TestFailingHook("bad_hook")
        
        hook_manager.register_hook("test.event", good_hook)
        hook_manager.register_hook("test.event", bad_hook)
        
        await hook_manager.trigger_hooks("test.event", param="value")
        
        stats = hook_manager.execution_stats["test.event"]
        assert stats["total"] == 2
        assert stats["success"] == 1
        assert stats["failed"] == 1

    @pytest.mark.unit
    def test_get_hook_stats(self, hook_manager, test_hooks):
        """Test getting hook statistics."""
        for i, hook in enumerate(test_hooks):
            hook_manager.register_hook(f"event{i}", hook)
        
        # Disable one hook
        test_hooks[1].disable()
        
        stats = hook_manager.get_hook_stats()
        
        assert stats["event_types"] == 3
        assert stats["total_hooks"] == 3
        assert stats["enabled_hooks"] == 2
        assert "hook_status" in stats
        
        # Check hook status details
        hook_status = stats["hook_status"]
        assert len(hook_status) == 3
        for event, hooks in hook_status.items():
            assert len(hooks) == 1
            hook_info = hooks[0]
            assert "name" in hook_info
            assert "enabled" in hook_info
            assert "error_count" in hook_info


class TestUtilityFunctions:
    """Test utility functions for hook infrastructure."""

    @pytest.mark.unit
    def test_create_sync_hook_wrapper_basic(self):
        """Test creating a sync hook wrapper."""
        def sync_function(x, y):
            return x + y
        
        async_wrapper = create_sync_hook_wrapper(sync_function)
        
        # Should be an async function
        assert asyncio.iscoroutinefunction(async_wrapper)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_sync_hook_wrapper_execution(self):
        """Test execution of wrapped sync function."""
        def multiply(x, y):
            return x * y
        
        async_wrapper = create_sync_hook_wrapper(multiply)
        result = await async_wrapper(3, 4)
        
        assert result == 12

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_sync_hook_wrapper_with_exception(self):
        """Test wrapped sync function that raises exception."""
        def failing_function():
            raise ValueError("Test error")
        
        async_wrapper = create_sync_hook_wrapper(failing_function)
        
        with pytest.raises(ValueError, match="Test error"):
            await async_wrapper()


class TestGlobalHookManager:
    """Test global hook manager functionality."""

    @pytest.mark.unit
    def test_get_hook_manager_singleton(self):
        """Test that get_hook_manager returns the same instance."""
        manager1 = get_hook_manager()
        manager2 = get_hook_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, HookManager)

    @pytest.mark.unit
    def test_get_hook_manager_is_hook_manager_instance(self):
        """Test that get_hook_manager returns a HookManager instance."""
        manager = get_hook_manager()
        
        assert isinstance(manager, HookManager)
        assert hasattr(manager, 'register_hook')
        assert hasattr(manager, 'trigger_hooks')
        assert hasattr(manager, 'get_hook_stats')


class TestHookDecorator:
    """Test the hook_decorator functionality."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_hook_decorator_async_function(self):
        """Test hook decorator with async function."""
        mock_hook_manager = Mock()
        mock_hook_manager.trigger_hooks = AsyncMock()
        
        @hook_decorator(mock_hook_manager, "test_service")
        async def async_test_method(self, param1, param2="default"):
            return f"result_{param1}_{param2}"
        
        # Create a mock self object
        mock_self = Mock()
        
        result = await async_test_method(mock_self, "value1", param2="value2")
        
        assert result == "result_value1_value2"
        assert mock_hook_manager.trigger_hooks.call_count == 2
        
        # Check pre-hook call
        pre_call = mock_hook_manager.trigger_hooks.call_args_list[0]
        assert pre_call[0][0] == "test_service.pre"
        
        # Check post-hook call
        post_call = mock_hook_manager.trigger_hooks.call_args_list[1]
        assert post_call[0][0] == "test_service.post"
        post_context = post_call[1]
        assert post_context["result"] == "result_value1_value2"
        assert post_context["success"] is True

    @pytest.mark.unit
    def test_hook_decorator_sync_function(self):
        """Test hook decorator with sync function."""
        mock_hook_manager = Mock()
        mock_hook_manager.trigger_hooks = AsyncMock()
        
        @hook_decorator(mock_hook_manager, "test_service")
        def sync_test_method(self, param):
            return f"sync_result_{param}"
        
        # Note: The decorator converts sync functions to run in async context
        # In a real scenario, this would be called in an async context
        mock_self = Mock()
        
        # The sync wrapper uses asyncio.run, so we need to test differently
        assert callable(sync_test_method)


if __name__ == "__main__":
    pytest.main([__file__]) 