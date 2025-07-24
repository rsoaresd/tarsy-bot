"""
Unit tests for Dashboard Hooks.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from tarsy.hooks.dashboard_hooks import DashboardLLMHooks, DashboardMCPHooks
from tarsy.models.websocket_models import ChannelType


class TestDashboardLLMHooks:
    """Test DashboardLLMHooks functionality."""
    
    @pytest.fixture
    def mock_update_service(self):
        """Mock dashboard update service."""
        service = AsyncMock()
        service.process_llm_interaction = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_websocket_manager(self):
        """Mock WebSocket manager as fallback."""
        manager = AsyncMock()
        manager.broadcast_dashboard_update = AsyncMock()
        # Mock dashboard_manager with update_service
        dashboard_manager = Mock()
        dashboard_manager.update_service = None  # Will be set in tests
        manager.dashboard_manager = dashboard_manager
        manager.broadcast_session_update_advanced = AsyncMock(return_value=2)
        manager.broadcast_dashboard_update_advanced = AsyncMock(return_value=3)
        return manager
    
    @pytest.fixture
    def dashboard_hooks(self, mock_websocket_manager, mock_update_service):
        """Create DashboardLLMHooks instance for testing."""
        return DashboardLLMHooks(
            websocket_manager=mock_websocket_manager,
            update_service=mock_update_service
        )
    
    @pytest.mark.unit
    def test_initialization(self, dashboard_hooks, mock_update_service, mock_websocket_manager):
        """Test DashboardLLMHooks initialization."""
        assert dashboard_hooks.update_service == mock_update_service
        assert dashboard_hooks.websocket_manager == mock_websocket_manager
        
        # Test with only websocket manager
        hooks = DashboardLLMHooks(websocket_manager=mock_websocket_manager)
        assert hooks.update_service is None
        assert hooks.websocket_manager == mock_websocket_manager


class TestDashboardLLMHooksUtilityMethods:
    """Test LLM hooks utility methods for data extraction and processing."""
    
    @pytest.fixture
    def llm_hooks(self):
        """Create LLM hooks instance for utility method testing."""
        return DashboardLLMHooks(websocket_manager=None)

    @pytest.mark.unit
    def test_extract_response_text_string_result(self, llm_hooks):
        """Test response text extraction from string result."""
        result = "This is a simple string response"
        extracted = llm_hooks._extract_response_text(result)
        assert extracted == "This is a simple string response"

    @pytest.mark.unit
    def test_extract_response_text_dict_with_content(self, llm_hooks):
        """Test response text extraction from dict with content field."""
        result = {"content": "Response content", "metadata": {"tokens": 150}}
        extracted = llm_hooks._extract_response_text(result)
        assert extracted == "Response content"

    @pytest.mark.unit
    def test_extract_response_text_dict_with_text(self, llm_hooks):
        """Test response text extraction from dict with text field."""
        result = {"text": "Text response", "status": "success"}
        extracted = llm_hooks._extract_response_text(result)
        assert extracted == "Text response"

    @pytest.mark.unit
    def test_extract_response_text_dict_with_message(self, llm_hooks):
        """Test response text extraction from dict with message field."""
        result = {"message": "Message response", "id": "msg_123"}
        extracted = llm_hooks._extract_response_text(result)
        assert extracted == "Message response"

    @pytest.mark.unit
    def test_extract_response_text_object_with_content_attr(self, llm_hooks):
        """Test response text extraction from object with content attribute."""
        class MockResponse:
            def __init__(self):
                self.content = "Object content response"
                self.status = "completed"
        
        result = MockResponse()
        extracted = llm_hooks._extract_response_text(result)
        assert extracted == "Object content response"

    @pytest.mark.unit
    def test_extract_response_text_object_with_text_attr(self, llm_hooks):
        """Test response text extraction from object with text attribute."""
        class MockResponse:
            def __init__(self):
                self.text = "Object text response"
        
        result = MockResponse()
        extracted = llm_hooks._extract_response_text(result)
        assert extracted == "Object text response"

    @pytest.mark.unit
    def test_extract_response_text_fallback_str_conversion(self, llm_hooks):
        """Test response text extraction fallback to string conversion."""
        result = {"unknown_field": "value", "data": [1, 2, 3]}
        extracted = llm_hooks._extract_response_text(result)
        assert "unknown_field" in extracted
        assert "value" in extracted

    @pytest.mark.unit
    def test_extract_tool_calls_from_result_tool_calls(self, llm_hooks):
        """Test tool calls extraction from result with tool_calls field."""
        args = {"prompt": "Test prompt"}
        result = {
            "content": "Response",
            "tool_calls": [
                {"name": "kubectl", "arguments": {"namespace": "default"}},
                {"name": "grep", "arguments": {"pattern": "error"}}
            ]
        }
        
        tool_calls = llm_hooks._extract_tool_calls(args, result)
        assert tool_calls == result["tool_calls"]
        assert len(tool_calls) == 2
        assert tool_calls[0]["name"] == "kubectl"

    @pytest.mark.unit
    def test_extract_tool_calls_from_result_function_calls(self, llm_hooks):
        """Test tool calls extraction from result with function_calls field."""
        args = {"prompt": "Test prompt"}
        result = {
            "content": "Response",
            "function_calls": [{"function": "analyze", "args": {"data": "logs"}}]
        }
        
        tool_calls = llm_hooks._extract_tool_calls(args, result)
        assert tool_calls == result["function_calls"]

    @pytest.mark.unit
    def test_extract_tool_calls_from_args_tools(self, llm_hooks):
        """Test tool calls extraction from args with available tools."""
        args = {
            "prompt": "Test prompt",
            "tools": [
                {"name": "kubectl", "description": "Kubernetes tool"},
                {"name": "grep", "description": "Search tool"}
            ]
        }
        result = {"content": "Response"}
        
        tool_calls = llm_hooks._extract_tool_calls(args, result)
        assert tool_calls == {"available_tools": args["tools"]}

    @pytest.mark.unit
    def test_extract_tool_calls_none_when_missing(self, llm_hooks):
        """Test tool calls extraction returns None when no tools present."""
        args = {"prompt": "Test prompt"}
        result = {"content": "Response"}
        
        tool_calls = llm_hooks._extract_tool_calls(args, result)
        assert tool_calls is None

    @pytest.mark.unit
    def test_calculate_duration_with_valid_times(self, llm_hooks):
        """Test duration calculation with valid start and end times."""
        start_time = datetime.now()
        end_time = start_time + timedelta(milliseconds=1500)
        
        duration = llm_hooks._calculate_duration(start_time, end_time)
        assert duration == 1500

    @pytest.mark.unit
    def test_calculate_duration_with_missing_times(self, llm_hooks):
        """Test duration calculation with missing times returns 0."""
        assert llm_hooks._calculate_duration(None, None) == 0
        assert llm_hooks._calculate_duration(datetime.now(), None) == 0
        assert llm_hooks._calculate_duration(None, datetime.now()) == 0

    @pytest.mark.unit
    def test_infer_purpose_analysis_keywords(self, llm_hooks):
        """Test purpose inference for analysis-related prompts."""
        prompts = [
            "Analyze the error logs from the application",
            "Please analysis this data for insights",
            "I need to investigate the root cause"
        ]
        
        for prompt in prompts:
            purpose = llm_hooks._infer_purpose(prompt)
            assert purpose == "analysis"

    @pytest.mark.unit
    def test_infer_purpose_resolution_keywords(self, llm_hooks):
        """Test purpose inference for resolution-related prompts."""
        prompts = [
            "Fix the deployment issue in production",
            "How can I resolve this error?",
            "Please solve this problem for me",
            "Repair the broken configuration"
        ]
        
        for prompt in prompts:
            purpose = llm_hooks._infer_purpose(prompt)
            assert purpose == "resolution"

    @pytest.mark.unit
    def test_infer_purpose_inspection_keywords(self, llm_hooks):
        """Test purpose inference for inspection-related prompts."""
        prompts = [
            "Check the status of all pods",
            "Inspect the system health metrics",
            "What is the current status?"
        ]
        
        for prompt in prompts:
            purpose = llm_hooks._infer_purpose(prompt)
            assert purpose == "inspection"

    @pytest.mark.unit
    def test_infer_purpose_planning_keywords(self, llm_hooks):
        """Test purpose inference for planning-related prompts."""
        prompts = [
            "Create a plan for the migration",
            "What strategy should I use?",
            "Help me approach this problem"
        ]
        
        for prompt in prompts:
            purpose = llm_hooks._infer_purpose(prompt)
            assert purpose == "planning"

    @pytest.mark.unit
    def test_infer_purpose_default_processing(self, llm_hooks):
        """Test purpose inference defaults to processing for unclear prompts."""
        prompts = [
            "Hello there, how are you?",
            "Generate a random number",
            "Convert this data format"
        ]
        
        for prompt in prompts:
            purpose = llm_hooks._infer_purpose(prompt)
            assert purpose == "processing"

    @pytest.mark.unit
    def test_infer_purpose_case_insensitive(self, llm_hooks):
        """Test purpose inference is case insensitive."""
        prompts = [
            "ANALYZE THIS ERROR LOG",
            "Fix This Issue",
            "check the STATUS",
            "PLAN the approach"
        ]
        
        expected_purposes = ["analysis", "resolution", "inspection", "planning"]
        
        for prompt, expected in zip(prompts, expected_purposes):
            purpose = llm_hooks._infer_purpose(prompt)
            assert purpose == expected


class TestDashboardMCPHooksUtilityMethods:
    """Test MCP hooks utility methods for data extraction and processing."""
    
    @pytest.fixture
    def mcp_hooks(self):
        """Create MCP hooks instance for utility method testing."""
        return DashboardMCPHooks(websocket_manager=None)

    @pytest.mark.unit
    def test_infer_communication_type_tool_list(self, mcp_hooks):
        """Test communication type inference for tool listing operations."""
        test_cases = [
            ("list_tools", {}),
            ("discover_tools", {}),
            ("get_available_tools", {}),
            ("LIST_AVAILABLE_TOOLS", {})
        ]
        
        for method_name, args in test_cases:
            comm_type = mcp_hooks._infer_communication_type(method_name, args)
            assert comm_type == "tool_list"

    @pytest.mark.unit
    def test_infer_communication_type_tool_call_by_method(self, mcp_hooks):
        """Test communication type inference for tool calls by method name."""
        test_cases = [
            ("call_tool", {}),
            ("execute_tool", {}),
            ("invoke_tool", {})
        ]
        
        for method_name, args in test_cases:
            comm_type = mcp_hooks._infer_communication_type(method_name, args)
            assert comm_type == "tool_call"

    @pytest.mark.unit
    def test_infer_communication_type_tool_call_by_args(self, mcp_hooks):
        """Test communication type inference for tool calls by arguments."""
        args = {"tool_name": "kubectl-get-pods"}
        comm_type = mcp_hooks._infer_communication_type("unknown_method", args)
        assert comm_type == "tool_call"

    @pytest.mark.unit
    def test_infer_communication_type_result(self, mcp_hooks):
        """Test communication type inference for result operations."""
        test_cases = [
            ("get_result", {}),
            ("fetch_response", {}),
            ("tool_result", {})
        ]
        
        for method_name, args in test_cases:
            comm_type = mcp_hooks._infer_communication_type(method_name, args)
            assert comm_type == "result"

    @pytest.mark.unit
    def test_infer_communication_type_default(self, mcp_hooks):
        """Test communication type inference defaults to tool_call."""
        comm_type = mcp_hooks._infer_communication_type("unknown_method", {})
        assert comm_type == "tool_call"

    @pytest.mark.unit
    def test_extract_tool_result_none_input(self, mcp_hooks):
        """Test tool result extraction with None input."""
        result = mcp_hooks._extract_tool_result(None)
        assert result is None

    @pytest.mark.unit
    def test_extract_tool_result_dict_input(self, mcp_hooks):
        """Test tool result extraction with dict input."""
        input_result = {"output": "pod1 Running\npod2 Pending", "status": "success"}
        result = mcp_hooks._extract_tool_result(input_result)
        assert result == input_result

    @pytest.mark.unit
    def test_extract_tool_result_primitive_types(self, mcp_hooks):
        """Test tool result extraction with primitive types."""
        test_cases = [
            ("Simple string output", {"result": "Simple string output"}),
            (42, {"result": 42}),
            (3.14, {"result": 3.14}),
            (True, {"result": True}),
            (False, {"result": False})
        ]
        
        for input_val, expected in test_cases:
            result = mcp_hooks._extract_tool_result(input_val)
            assert result == expected

    @pytest.mark.unit
    def test_extract_tool_result_complex_object(self, mcp_hooks):
        """Test tool result extraction with complex object."""
        class MockResult:
            def __init__(self):
                self.data = "complex data"
            
            def __str__(self):
                return "MockResult with complex data"
        
        input_result = MockResult()
        result = mcp_hooks._extract_tool_result(input_result)
        assert result == {"result": "MockResult with complex data"}

    @pytest.mark.unit
    def test_calculate_duration_with_valid_times(self, mcp_hooks):
        """Test duration calculation with valid start and end times."""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=2, milliseconds=500)
        
        duration = mcp_hooks._calculate_duration(start_time, end_time)
        assert duration == 2500

    @pytest.mark.unit
    def test_calculate_duration_with_missing_times(self, mcp_hooks):
        """Test duration calculation with missing times returns 0."""
        assert mcp_hooks._calculate_duration(None, None) == 0
        assert mcp_hooks._calculate_duration(datetime.now(), None) == 0
        assert mcp_hooks._calculate_duration(None, datetime.now()) == 0

    @pytest.mark.unit
    def test_generate_step_description_tool_list(self, mcp_hooks):
        """Test step description generation for tool list operations."""
        description = mcp_hooks._generate_step_description(
            "tool_list", "kubernetes", None, {}
        )
        assert description == "Discover available tools from kubernetes"

    @pytest.mark.unit
    def test_generate_step_description_kubectl_with_namespace(self, mcp_hooks):
        """Test step description generation for kubectl with namespace."""
        args = {"tool_arguments": {"namespace": "production"}}
        description = mcp_hooks._generate_step_description(
            "tool_call", "kubernetes", "kubectl-get-pods", args
        )
        assert description == "Execute kubectl-get-pods in production namespace"

    @pytest.mark.unit
    def test_generate_step_description_kubectl_without_namespace(self, mcp_hooks):
        """Test step description generation for kubectl without namespace."""
        args = {"tool_arguments": {"resource": "pods"}}
        description = mcp_hooks._generate_step_description(
            "tool_call", "kubernetes", "kubectl-describe", args
        )
        assert description == "Execute Kubernetes command kubectl-describe"

    @pytest.mark.unit
    def test_generate_step_description_file_operation_with_path(self, mcp_hooks):
        """Test step description generation for file operations with path."""
        args = {"tool_arguments": {"path": "/var/log/app.log"}}
        description = mcp_hooks._generate_step_description(
            "tool_call", "filesystem", "read_file", args
        )
        assert description == "File operation read_file on /var/log/app.log"

    @pytest.mark.unit
    def test_generate_step_description_file_operation_without_path(self, mcp_hooks):
        """Test step description generation for file operations without path."""
        args = {"tool_arguments": {"content": "data"}}
        description = mcp_hooks._generate_step_description(
            "tool_call", "filesystem", "write_file", args
        )
        assert description == "Execute file operation write_file"

    @pytest.mark.unit
    def test_generate_step_description_generic_tool(self, mcp_hooks):
        """Test step description generation for generic tools."""
        args = {"tool_arguments": {"query": "search term"}}
        description = mcp_hooks._generate_step_description(
            "tool_call", "search", "elasticsearch_query", args
        )
        assert description == "Execute elasticsearch_query via search"

    @pytest.mark.unit
    def test_generate_step_description_fallback(self, mcp_hooks):
        """Test step description generation fallback for unknown types."""
        description = mcp_hooks._generate_step_description(
            "unknown_type", "server", "tool", {}
        )
        assert description == "Communicate with server"


class TestDashboardHooksContentTruncation:
    """Test content truncation logic for large responses."""
    
    @pytest.fixture
    def llm_hooks(self):
        """Create LLM hooks instance."""
        return DashboardLLMHooks(websocket_manager=None)

    @pytest.fixture
    def mcp_hooks(self):
        """Create MCP hooks instance."""
        return DashboardMCPHooks(websocket_manager=None)

    @pytest.mark.unit
    def test_prompt_preview_truncation_over_200_chars(self, llm_hooks):
        """Test prompt preview truncation for content over 200 characters."""
        long_prompt = "a" * 250  # 250 characters
        
        # Simulate the truncation logic from execute method
        prompt_preview = str(long_prompt)[:200] + "..." if len(str(long_prompt)) > 200 else str(long_prompt)
        
        assert len(prompt_preview) == 203  # 200 + "..."
        assert prompt_preview.endswith("...")
        assert prompt_preview.startswith("a" * 200)

    @pytest.mark.unit
    def test_prompt_preview_no_truncation_under_200_chars(self, llm_hooks):
        """Test prompt preview no truncation for content under 200 characters."""
        short_prompt = "a" * 150  # 150 characters
        
        # Simulate the truncation logic from execute method
        prompt_preview = str(short_prompt)[:200] + "..." if len(str(short_prompt)) > 200 else str(short_prompt)
        
        assert len(prompt_preview) == 150
        assert not prompt_preview.endswith("...")
        assert prompt_preview == short_prompt

    @pytest.mark.unit
    def test_response_preview_truncation_over_200_chars(self, llm_hooks):
        """Test response preview truncation for content over 200 characters."""
        long_response = "b" * 300  # 300 characters
        
        # Simulate the truncation logic from execute method
        response_preview = str(long_response)[:200] + "..." if len(str(long_response)) > 200 else str(long_response)
        
        assert len(response_preview) == 203  # 200 + "..."
        assert response_preview.endswith("...")
        assert response_preview.startswith("b" * 200)

    @pytest.mark.unit
    def test_tool_result_preview_truncation_over_300_chars(self, mcp_hooks):
        """Test tool result preview truncation for content over 300 characters."""
        large_result = {"output": "c" * 400}  # Large result
        
        # Simulate the truncation logic from execute method
        result_str = str(large_result)
        tool_result_preview = result_str[:300] + "..." if len(result_str) > 300 else result_str
        
        assert len(tool_result_preview) == 303  # 300 + "..."
        assert tool_result_preview.endswith("...")

    @pytest.mark.unit
    def test_tool_result_preview_no_truncation_under_300_chars(self, mcp_hooks):
        """Test tool result preview no truncation for content under 300 characters."""
        small_result = {"output": "small data", "status": "success"}
        
        # Simulate the truncation logic from execute method
        result_str = str(small_result)
        tool_result_preview = result_str[:300] + "..." if len(result_str) > 300 else result_str
        
        assert len(tool_result_preview) < 300
        assert not tool_result_preview.endswith("...")
        assert tool_result_preview == str(small_result)


class TestDashboardLLMHooksExecution:
    """Test core LLM hook execution logic."""
    
    @pytest.fixture
    def mock_update_service(self):
        """Mock dashboard update service."""
        service = AsyncMock()
        service.process_llm_interaction = AsyncMock(return_value=3)
        return service
    
    @pytest.fixture
    def mock_websocket_manager(self):
        """Mock WebSocket manager."""
        manager = AsyncMock()
        dashboard_manager = Mock()
        manager.dashboard_manager = dashboard_manager
        manager.broadcast_session_update_advanced = AsyncMock(return_value=2)
        manager.broadcast_dashboard_update_advanced = AsyncMock(return_value=3)
        return manager
    
    @pytest.fixture
    def llm_hooks_with_service(self, mock_websocket_manager, mock_update_service):
        """Create LLM hooks with update service."""
        mock_websocket_manager.dashboard_manager.update_service = mock_update_service
        return DashboardLLMHooks(
            websocket_manager=mock_websocket_manager,
            update_service=mock_update_service
        )
    
    @pytest.fixture
    def llm_hooks_without_service(self, mock_websocket_manager):
        """Create LLM hooks without update service (fallback mode)."""
        mock_websocket_manager.dashboard_manager.update_service = None
        return DashboardLLMHooks(websocket_manager=mock_websocket_manager)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_llm_success_with_update_service(self, llm_hooks_with_service, mock_update_service):
        """Test successful LLM interaction with update service."""
        event_data = {
            'session_id': 'test_session_123',
            'args': {
                'prompt': 'Test prompt for analysis',
                'model': 'gpt-4'
            },
            'result': {
                'content': 'Test response from LLM',
                'tool_calls': [{'name': 'kubectl', 'args': {}}]
            },
            'start_time': datetime.now(),
            'end_time': datetime.now(),
            'error': None
        }
        
        await llm_hooks_with_service.execute('llm.post', **event_data)
        
        # Verify update service was called
        mock_update_service.process_llm_interaction.assert_called_once()
        call_args = mock_update_service.process_llm_interaction.call_args
        
        # Extract positional and keyword arguments
        args, kwargs = call_args
        session_id, update_data = args
        broadcast_immediately = kwargs.get('broadcast_immediately', False)
        
        assert session_id == 'test_session_123'
        assert update_data['interaction_type'] == 'llm'
        assert update_data['model_used'] == 'gpt-4'
        assert update_data['success'] is True
        assert 'step_description' in update_data
        assert broadcast_immediately is False  # Success should not broadcast immediately (not success = False)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_llm_error_with_update_service(self, llm_hooks_with_service, mock_update_service):
        """Test LLM error with update service."""
        error_msg = "Connection timeout to LLM service"
        event_data = {
            'session_id': 'test_session_456',
            'args': {'prompt': 'Test prompt', 'model': 'gpt-4'},
            'result': {},
            'error': Exception(error_msg),
            'start_time': datetime.now(),
            'end_time': datetime.now()
        }
        
        await llm_hooks_with_service.execute('llm.error', **event_data)
        
        # Verify update service was called
        mock_update_service.process_llm_interaction.assert_called_once()
        call_args = mock_update_service.process_llm_interaction.call_args
        
        # Extract positional and keyword arguments
        args, kwargs = call_args
        session_id, update_data = args
        broadcast_immediately = kwargs.get('broadcast_immediately', False)
        
        assert session_id == 'test_session_456'
        assert update_data['success'] is False
        assert update_data['error_message'] == error_msg
        assert broadcast_immediately is True  # Errors should broadcast immediately (not success = True)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_llm_fallback_to_websocket(self, llm_hooks_without_service, mock_websocket_manager):
        """Test fallback when update_service is None."""
        event_data = {
            'session_id': 'test_session_789',
            'args': {'prompt': 'Test prompt', 'model': 'claude-3'},
            'result': {'content': 'Test response'},
            'start_time': datetime.now(),
            'end_time': datetime.now()
        }
        
        await llm_hooks_without_service.execute('llm.post', **event_data)
        
        # Verify fallback to direct WebSocket broadcasting
        mock_websocket_manager.broadcast_session_update_advanced.assert_called_once()
        mock_websocket_manager.broadcast_dashboard_update_advanced.assert_called_once()
        
        # Check session update call
        session_call_args = mock_websocket_manager.broadcast_session_update_advanced.call_args
        session_id, session_data = session_call_args[0]
        assert session_id == 'test_session_789'
        assert session_data['interaction_type'] == 'llm'
        assert session_data['model_used'] == 'claude-3'
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_ignores_non_post_error_events(self, llm_hooks_with_service, mock_update_service):
        """Test that pre-events and other events are ignored."""
        event_data = {'session_id': 'test_session', 'args': {}}
        
        # Test pre-event (should be ignored)
        await llm_hooks_with_service.execute('llm.pre', **event_data)
        mock_update_service.process_llm_interaction.assert_not_called()
        
        # Test random event (should be ignored)
        await llm_hooks_with_service.execute('llm.something', **event_data)
        mock_update_service.process_llm_interaction.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_ignores_missing_session_id(self, llm_hooks_with_service, mock_update_service):
        """Test that events without session_id are ignored."""
        event_data = {
            'args': {'prompt': 'Test prompt'},
            'result': {'content': 'Response'}
        }
        
        await llm_hooks_with_service.execute('llm.post', **event_data)
        
        # Should not call update service without session_id
        mock_update_service.process_llm_interaction.assert_not_called()


class TestDashboardMCPHooks:
    """Test DashboardMCPHooks functionality."""
    
    @pytest.fixture
    def mock_update_service(self):
        """Mock dashboard update service."""
        service = AsyncMock()
        service.process_mcp_interaction = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_websocket_manager(self):
        """Mock WebSocket manager as fallback."""
        manager = AsyncMock()
        manager.broadcast_dashboard_update = AsyncMock()
        # Mock dashboard_manager with update_service
        dashboard_manager = Mock()
        dashboard_manager.update_service = None  # Will be set in tests
        manager.dashboard_manager = dashboard_manager
        manager.broadcast_session_update_advanced = AsyncMock(return_value=2)
        manager.broadcast_dashboard_update_advanced = AsyncMock(return_value=3)
        return manager
    
    @pytest.fixture
    def dashboard_hooks(self, mock_websocket_manager, mock_update_service):
        """Create DashboardMCPHooks instance for testing."""  
        return DashboardMCPHooks(
            websocket_manager=mock_websocket_manager,
            update_service=mock_update_service
        )
    
    @pytest.mark.unit
    def test_initialization(self, dashboard_hooks, mock_update_service, mock_websocket_manager):
        """Test DashboardMCPHooks initialization."""
        assert dashboard_hooks.update_service == mock_update_service
        assert dashboard_hooks.websocket_manager == mock_websocket_manager


class TestDashboardMCPHooksExecution:
    """Test core MCP hook execution logic."""
    
    @pytest.fixture
    def mock_update_service(self):
        """Mock dashboard update service."""
        service = AsyncMock()
        service.process_mcp_communication = AsyncMock(return_value=2)
        return service
    
    @pytest.fixture
    def mock_websocket_manager(self):
        """Mock WebSocket manager."""
        manager = AsyncMock()
        dashboard_manager = Mock()
        manager.dashboard_manager = dashboard_manager
        manager.broadcast_session_update_advanced = AsyncMock(return_value=2)
        manager.broadcast_dashboard_update_advanced = AsyncMock(return_value=3)
        return manager
    
    @pytest.fixture
    def mcp_hooks_with_service(self, mock_websocket_manager, mock_update_service):
        """Create MCP hooks with update service."""
        mock_websocket_manager.dashboard_manager.update_service = mock_update_service
        return DashboardMCPHooks(
            websocket_manager=mock_websocket_manager,
            update_service=mock_update_service
        )
    
    @pytest.fixture
    def mcp_hooks_without_service(self, mock_websocket_manager):
        """Create MCP hooks without update service (fallback mode)."""
        mock_websocket_manager.dashboard_manager.update_service = None
        return DashboardMCPHooks(websocket_manager=mock_websocket_manager)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_mcp_success_with_update_service(self, mcp_hooks_with_service, mock_update_service):
        """Test successful MCP communication with update service."""
        event_data = {
            'session_id': 'mcp_session_123',
            'method': 'call_tool',
            'args': {
                'server_name': 'kubernetes',
                'tool_name': 'kubectl',
                'tool_arguments': {'namespace': 'default', 'command': 'get pods'}
            },
            'result': {'output': 'pod1 Running\npod2 Pending'},
            'start_time': datetime.now(),
            'end_time': datetime.now(),
            'error': None
        }
        
        await mcp_hooks_with_service.execute('mcp.post', **event_data)
        
        # Verify update service was called
        mock_update_service.process_mcp_communication.assert_called_once()
        call_args = mock_update_service.process_mcp_communication.call_args
        
        # Extract positional and keyword arguments
        args, kwargs = call_args
        session_id, update_data = args
        broadcast_immediately = kwargs.get('broadcast_immediately', False)
        
        assert session_id == 'mcp_session_123'
        assert update_data['interaction_type'] == 'mcp'
        assert update_data['server_name'] == 'kubernetes'
        assert update_data['tool_name'] == 'kubectl'
        assert update_data['success'] is True
        assert 'step_description' in update_data
        assert broadcast_immediately is False  # Success should not broadcast immediately (not success = False)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_mcp_error_with_update_service(self, mcp_hooks_with_service, mock_update_service):
        """Test MCP error with update service."""
        error_msg = "Tool execution failed: kubectl not found"
        event_data = {
            'session_id': 'mcp_session_456',
            'method': 'call_tool',
            'args': {'server_name': 'kubernetes', 'tool_name': 'kubectl'},
            'result': None,
            'error': Exception(error_msg),
            'start_time': datetime.now(),
            'end_time': datetime.now()
        }
        
        await mcp_hooks_with_service.execute('mcp.error', **event_data)
        
        # Verify update service was called
        mock_update_service.process_mcp_communication.assert_called_once()
        call_args = mock_update_service.process_mcp_communication.call_args
        
        # Extract positional and keyword arguments
        args, kwargs = call_args
        session_id, update_data = args
        broadcast_immediately = kwargs.get('broadcast_immediately', False)
        
        assert session_id == 'mcp_session_456'
        assert update_data['success'] is False
        assert update_data['error_message'] == error_msg
        assert broadcast_immediately is True  # Errors should broadcast immediately (not success = True)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_mcp_fallback_to_websocket(self, mcp_hooks_without_service, mock_websocket_manager):
        """Test fallback when update_service is None."""
        event_data = {
            'session_id': 'mcp_session_789',
            'method': 'list_tools',
            'args': {'server_name': 'file_operations'},
            'result': {'tools': ['read_file', 'write_file']},
            'start_time': datetime.now(),
            'end_time': datetime.now()
        }
        
        await mcp_hooks_without_service.execute('mcp.post', **event_data)
        
        # Verify fallback to direct WebSocket broadcasting
        mock_websocket_manager.broadcast_session_update_advanced.assert_called_once()
        mock_websocket_manager.broadcast_dashboard_update_advanced.assert_called_once()
        
        # Check session update call
        session_call_args = mock_websocket_manager.broadcast_session_update_advanced.call_args
        session_id, session_data = session_call_args[0]
        assert session_id == 'mcp_session_789'
        assert session_data['interaction_type'] == 'mcp'
        assert session_data['server_name'] == 'file_operations'
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_ignores_non_post_error_events(self, mcp_hooks_with_service, mock_update_service):
        """Test that pre-events and other events are ignored."""
        event_data = {'session_id': 'test_session', 'args': {}}
        
        # Test pre-event (should be ignored)
        await mcp_hooks_with_service.execute('mcp.pre', **event_data)
        mock_update_service.process_mcp_communication.assert_not_called()
        
        # Test random event (should be ignored)
        await mcp_hooks_with_service.execute('mcp.something', **event_data)
        mock_update_service.process_mcp_communication.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_ignores_missing_session_id(self, mcp_hooks_with_service, mock_update_service):
        """Test that events without session_id are ignored."""
        event_data = {
            'method': 'call_tool',
            'args': {'server_name': 'test', 'tool_name': 'test_tool'},
            'result': {'success': True}
        }
        
        await mcp_hooks_with_service.execute('mcp.post', **event_data)
        
        # Should not call update service without session_id
        mock_update_service.process_mcp_communication.assert_not_called()


class TestHookRegistration:
    """Test hook registration functions."""
    
    @pytest.mark.unit
    def test_register_dashboard_hooks_with_services(self):
        """Test registering dashboard hooks with both services."""
        mock_hook_manager = Mock()
        mock_update_service = AsyncMock()
        mock_websocket_manager = AsyncMock()
        
        with patch('tarsy.hooks.dashboard_hooks.DashboardLLMHooks') as mock_llm_hooks_class:
            with patch('tarsy.hooks.dashboard_hooks.DashboardMCPHooks') as mock_mcp_hooks_class:
                with patch('tarsy.hooks.base_hooks.get_hook_manager', return_value=mock_hook_manager):
                    # Import and test the registration function
                    from tarsy.hooks.dashboard_hooks import register_dashboard_hooks
                    
                    mock_llm_hooks = Mock()
                    mock_mcp_hooks = Mock()
                    mock_llm_hooks_class.return_value = mock_llm_hooks
                    mock_mcp_hooks_class.return_value = mock_mcp_hooks
                    
                    register_dashboard_hooks(
                        websocket_manager=mock_websocket_manager
                    )
                    
                    # Verify hooks were created with correct parameters
                    mock_llm_hooks_class.assert_called_once_with(
                        websocket_manager=mock_websocket_manager
                    )
                    mock_mcp_hooks_class.assert_called_once_with(
                        websocket_manager=mock_websocket_manager
                    )
                    
                    # Verify hooks were registered
                    assert mock_hook_manager.register_hook.call_count == 4  # 2 LLM hooks + 2 MCP hooks
    
    @pytest.mark.unit
    def test_register_dashboard_hooks_websocket_only(self):
        """Test registering dashboard hooks with only WebSocket manager."""
        mock_hook_manager = Mock()
        mock_websocket_manager = AsyncMock()
        
        with patch('tarsy.hooks.dashboard_hooks.DashboardLLMHooks') as mock_llm_hooks_class:
            with patch('tarsy.hooks.dashboard_hooks.DashboardMCPHooks') as mock_mcp_hooks_class:
                from tarsy.hooks.dashboard_hooks import register_dashboard_hooks
                
                register_dashboard_hooks(
                    websocket_manager=mock_websocket_manager
                )
                
                # Verify hooks were created with only WebSocket manager
                mock_llm_hooks_class.assert_called_once_with(
                    websocket_manager=mock_websocket_manager
                )
                mock_mcp_hooks_class.assert_called_once_with(
                    websocket_manager=mock_websocket_manager
                )
    
    @pytest.mark.unit
    def test_register_integrated_hooks(self):
        """Test registering integrated hooks with history system."""
        mock_hook_manager = Mock()
        mock_update_service = AsyncMock()
        mock_websocket_manager = AsyncMock()
        
        # Mock the history hooks registration function
        with patch('tarsy.hooks.dashboard_hooks.register_history_hooks') as mock_register_history:
            with patch('tarsy.hooks.dashboard_hooks.register_dashboard_hooks') as mock_register_dashboard:
                from tarsy.hooks.dashboard_hooks import register_integrated_hooks
                
                register_integrated_hooks(
                    websocket_manager=mock_websocket_manager
                )
                
                # Verify both registration functions were called
                mock_register_history.assert_called_once()
                mock_register_dashboard.assert_called_once_with(mock_websocket_manager)


class TestHookErrorHandling:
    """Test error handling in dashboard hooks."""
    
    @pytest.fixture
    def mock_update_service(self):
        """Mock dashboard update service."""
        service = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_websocket_manager(self):
        """Mock WebSocket manager."""
        manager = AsyncMock()
        return manager
    
    @pytest.mark.unit
    def test_hooks_with_none_services(self):
        """Test hooks initialization with None services."""
        # Should not raise exception
        llm_hooks = DashboardLLMHooks(websocket_manager=None)
        mcp_hooks = DashboardMCPHooks(websocket_manager=None)
        
        assert llm_hooks.websocket_manager is None
        assert mcp_hooks.websocket_manager is None

if __name__ == "__main__":
    pytest.main([__file__]) 