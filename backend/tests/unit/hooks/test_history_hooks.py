"""
Unit tests for History Hooks.

Tests the history hook functionality with mocked dependencies to ensure
proper data extraction, logging, and integration with history service.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from tarsy.hooks.history_hooks import LLMHooks, MCPHooks, register_history_hooks


class TestLLMHooks:
    """Test LLMHooks functionality."""
    
    @pytest.fixture
    def mock_history_service(self):
        """Mock history service."""
        service = Mock()
        service.log_llm_interaction = Mock(return_value=True)
        return service
    
    @pytest.fixture
    def llm_hooks(self, mock_history_service):
        """Create LLMHooks instance for testing."""
        with patch('tarsy.hooks.history_hooks.get_history_service', return_value=mock_history_service):
            return LLMHooks()
    
    @pytest.mark.unit
    def test_initialization(self, llm_hooks, mock_history_service):
        """Test LLMHooks initialization."""
        assert llm_hooks.name == "llm_history_hook"
        assert llm_hooks.history_service == mock_history_service
        assert llm_hooks.is_enabled is True


class TestLLMHooksUtilityMethods:
    """Test LLM hooks utility methods for data extraction and processing."""
    
    @pytest.fixture
    def llm_hooks(self):
        """Create LLM hooks instance for utility method testing."""
        with patch('tarsy.hooks.history_hooks.get_history_service'):
            return LLMHooks()

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
    def test_extract_response_text_dict_with_response(self, llm_hooks):
        """Test response text extraction from dict with response field."""
        result = {"response": "Response field content", "other": "data"}
        extracted = llm_hooks._extract_response_text(result)
        assert extracted == "Response field content"

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
    def test_extract_tool_results_tool_results_field(self, llm_hooks):
        """Test tool results extraction from tool_results field."""
        result = {
            "content": "Response",
            "tool_results": [
                {"tool": "kubectl", "result": "pod1 Running"},
                {"tool": "grep", "result": "Found 3 matches"}
            ]
        }
        
        tool_results = llm_hooks._extract_tool_results(result)
        assert tool_results == result["tool_results"]

    @pytest.mark.unit
    def test_extract_tool_results_function_results_field(self, llm_hooks):
        """Test tool results extraction from function_results field."""
        result = {
            "content": "Response",
            "function_results": [{"function": "analyze", "output": "analysis complete"}]
        }
        
        tool_results = llm_hooks._extract_tool_results(result)
        assert tool_results == result["function_results"]

    @pytest.mark.unit
    def test_extract_tool_results_tool_outputs_field(self, llm_hooks):
        """Test tool results extraction from tool_outputs field."""
        result = {
            "content": "Response",
            "tool_outputs": {"kubectl": "pods listed", "grep": "patterns found"}
        }
        
        tool_results = llm_hooks._extract_tool_results(result)
        assert tool_results == result["tool_outputs"]

    @pytest.mark.unit
    def test_extract_tool_results_none_when_missing(self, llm_hooks):
        """Test tool results extraction returns None when no results present."""
        result = {"content": "Response", "metadata": {"tokens": 100}}
        
        tool_results = llm_hooks._extract_tool_results(result)
        assert tool_results is None

    @pytest.mark.unit
    def test_extract_token_usage_usage_field(self, llm_hooks):
        """Test token usage extraction from usage field."""
        result = {
            "content": "Response",
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 100,
                "total_tokens": 150
            }
        }
        
        token_usage = llm_hooks._extract_token_usage(result)
        assert token_usage == result["usage"]

    @pytest.mark.unit
    def test_extract_token_usage_token_usage_field(self, llm_hooks):
        """Test token usage extraction from token_usage field."""
        result = {
            "content": "Response",
            "token_usage": {
                "input": 30,
                "output": 70,
                "total": 100
            }
        }
        
        token_usage = llm_hooks._extract_token_usage(result)
        assert token_usage == result["token_usage"]

    @pytest.mark.unit
    def test_extract_token_usage_object_with_usage_attr(self, llm_hooks):
        """Test token usage extraction from object with usage attribute."""
        class MockUsage:
            def __init__(self):
                self.prompt_tokens = 25
                self.completion_tokens = 50
            
            def dict(self):
                return {"prompt_tokens": 25, "completion_tokens": 50}
        
        class MockResult:
            def __init__(self):
                self.content = "Response"
                self.usage = MockUsage()
        
        result = MockResult()
        token_usage = llm_hooks._extract_token_usage(result)
        assert token_usage == {"prompt_tokens": 25, "completion_tokens": 50}

    @pytest.mark.unit
    def test_extract_token_usage_object_without_dict_method(self, llm_hooks):
        """Test token usage extraction from object without dict method."""
        class MockUsage:
            def __init__(self):
                self.prompt_tokens = 25
            
            def __str__(self):
                return "Usage: 25 tokens"
        
        class MockResult:
            def __init__(self):
                self.content = "Response"
                self.usage = MockUsage()
        
        result = MockResult()
        token_usage = llm_hooks._extract_token_usage(result)
        assert token_usage == "Usage: 25 tokens"

    @pytest.mark.unit
    def test_extract_token_usage_none_when_missing(self, llm_hooks):
        """Test token usage extraction returns None when not present."""
        result = {"content": "Response", "metadata": {"model": "gpt-4"}}
        
        token_usage = llm_hooks._extract_token_usage(result)
        assert token_usage is None

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


class TestLLMHooksExecution:
    """Test LLM hook execution logic and history service integration."""
    
    @pytest.fixture
    def mock_history_service(self):
        """Mock history service."""
        service = Mock()
        service.log_llm_interaction = Mock(return_value=True)
        return service
    
    @pytest.fixture
    def llm_hooks(self, mock_history_service):
        """Create LLM hooks with mocked history service."""
        with patch('tarsy.hooks.history_hooks.get_history_service', return_value=mock_history_service):
            return LLMHooks()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_successful_interaction(self, llm_hooks, mock_history_service):
        """Test successful LLM interaction execution and logging."""
        event_data = {
            'session_id': 'test_session_123',
            'args': {
                'prompt': 'Test prompt for analysis',
                'model': 'gpt-4'
            },
            'result': {
                'content': 'Test response from LLM',
                'usage': {'prompt_tokens': 10, 'completion_tokens': 20}
            },
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(milliseconds=1500)
        }
        
        with patch('tarsy.hooks.history_hooks.generate_step_description', return_value="LLM analysis using gpt-4"):
            await llm_hooks.execute('llm.post', **event_data)
        
        # Verify history service was called
        mock_history_service.log_llm_interaction.assert_called_once()
        call_args = mock_history_service.log_llm_interaction.call_args
        
        # Verify call arguments
        kwargs = call_args[1]
        assert kwargs['session_id'] == 'test_session_123'
        assert kwargs['model_used'] == 'gpt-4'
        assert kwargs['step_description'] == "LLM analysis using gpt-4"
        assert kwargs['prompt_text'] == 'Test prompt for analysis'
        assert kwargs['response_text'] == 'Test response from LLM'
        assert kwargs['token_usage'] == {'prompt_tokens': 10, 'completion_tokens': 20}
        assert kwargs['duration_ms'] == 1500

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_ignores_pre_events(self, llm_hooks, mock_history_service):
        """Test that pre-events are ignored."""
        event_data = {'session_id': 'test_session', 'args': {}}
        
        await llm_hooks.execute('llm.pre', **event_data)
        
        mock_history_service.log_llm_interaction.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_ignores_missing_session_id(self, llm_hooks, mock_history_service):
        """Test that events without session_id are ignored."""
        event_data = {
            'args': {'prompt': 'Test prompt'},
            'result': {'content': 'Response'}
        }
        
        await llm_hooks.execute('llm.post', **event_data)
        
        mock_history_service.log_llm_interaction.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_with_large_content_truncation(self, llm_hooks, mock_history_service):
        """Test that large content is truncated to 10000 characters."""
        large_prompt = "a" * 15000  # 15k characters
        large_response = "b" * 12000  # 12k characters
        
        event_data = {
            'session_id': 'test_session_456',
            'args': {'prompt': large_prompt, 'model': 'gpt-3.5'},
            'result': {'content': large_response},
            'start_time': datetime.now(),
            'end_time': datetime.now()
        }
        
        with patch('tarsy.hooks.history_hooks.generate_step_description', return_value="LLM processing using gpt-3.5"):
            await llm_hooks.execute('llm.post', **event_data)
        
        call_args = mock_history_service.log_llm_interaction.call_args[1]
        
        # Verify truncation to 10000 characters
        assert len(call_args['prompt_text']) == 10000
        assert len(call_args['response_text']) == 10000
        assert call_args['prompt_text'] == large_prompt[:10000]
        assert call_args['response_text'] == large_response[:10000]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_history_service_failure(self, llm_hooks, mock_history_service):
        """Test handling of history service failure."""
        mock_history_service.log_llm_interaction.return_value = False
        
        event_data = {
            'session_id': 'test_session_fail',
            'args': {'prompt': 'Test prompt', 'model': 'gpt-4'},
            'result': {'content': 'Response'},
            'start_time': datetime.now(),
            'end_time': datetime.now()
        }
        
        with patch('tarsy.hooks.history_hooks.generate_step_description', return_value="LLM processing using gpt-4"):
            # Should not raise exception despite service failure
            await llm_hooks.execute('llm.post', **event_data)
        
        mock_history_service.log_llm_interaction.assert_called_once()


class TestMCPHooks:
    """Test MCPHooks functionality."""
    
    @pytest.fixture
    def mock_history_service(self):
        """Mock history service."""
        service = Mock()
        service.log_mcp_communication = Mock(return_value=True)
        return service
    
    @pytest.fixture
    def mcp_hooks(self, mock_history_service):
        """Create MCPHooks instance for testing."""
        with patch('tarsy.hooks.history_hooks.get_history_service', return_value=mock_history_service):
            return MCPHooks()
    
    @pytest.mark.unit
    def test_initialization(self, mcp_hooks, mock_history_service):
        """Test MCPHooks initialization."""
        assert mcp_hooks.name == "mcp_history_hook"
        assert mcp_hooks.history_service == mock_history_service
        assert mcp_hooks.is_enabled is True


class TestMCPHooksUtilityMethods:
    """Test MCP hooks utility methods for data extraction and processing."""
    
    @pytest.fixture
    def mcp_hooks(self):
        """Create MCP hooks instance for utility method testing."""
        with patch('tarsy.hooks.history_hooks.get_history_service'):
            return MCPHooks()

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
    def test_extract_available_tools_dict_with_tools(self, mcp_hooks):
        """Test available tools extraction from dict with tools field."""
        result = {
            "tools": [
                {"name": "kubectl", "description": "Kubernetes CLI"},
                {"name": "grep", "description": "Search tool"}
            ]
        }
        
        available_tools = mcp_hooks._extract_available_tools(result)
        assert available_tools == result

    @pytest.mark.unit
    def test_extract_available_tools_dict_as_list(self, mcp_hooks):
        """Test available tools extraction from dict containing list."""
        result = [
            {"name": "kubectl", "description": "Kubernetes CLI"},
            {"name": "grep", "description": "Search tool"}
        ]
        
        # When result is a dict that contains a list
        dict_result = {"other_field": "data", "some_list": result}
        available_tools = mcp_hooks._extract_available_tools(dict_result)
        assert available_tools is None  # No 'tools' field

    @pytest.mark.unit
    def test_extract_available_tools_direct_list(self, mcp_hooks):
        """Test available tools extraction from direct list."""
        result = [
            {"name": "kubectl", "description": "Kubernetes CLI"},
            {"name": "grep", "description": "Search tool"}
        ]
        
        available_tools = mcp_hooks._extract_available_tools(result)
        assert available_tools == {"tools": result}

    @pytest.mark.unit
    def test_extract_available_tools_none_when_missing(self, mcp_hooks):
        """Test available tools extraction returns None when not present."""
        result = {"status": "success", "message": "Command completed"}
        
        available_tools = mcp_hooks._extract_available_tools(result)
        assert available_tools is None

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


class TestMCPHooksExecution:
    """Test MCP hook execution logic and history service integration."""
    
    @pytest.fixture
    def mock_history_service(self):
        """Mock history service."""
        service = Mock()
        service.log_mcp_communication = Mock(return_value=True)
        return service
    
    @pytest.fixture
    def mcp_hooks(self, mock_history_service):
        """Create MCP hooks with mocked history service."""
        with patch('tarsy.hooks.history_hooks.get_history_service', return_value=mock_history_service):
            return MCPHooks()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_successful_tool_call(self, mcp_hooks, mock_history_service):
        """Test successful MCP tool call execution and logging."""
        event_data = {
            'session_id': 'mcp_session_123',
            'method': 'call_tool',
            'args': {
                'server_name': 'kubernetes',
                'tool_name': 'kubectl-get-pods',
                'tool_arguments': {'namespace': 'default'}
            },
            'result': {'output': 'pod1 Running\npod2 Pending'},
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(milliseconds=2500)
        }
        
        await mcp_hooks.execute('mcp.post', **event_data)
        
        # Verify history service was called
        mock_history_service.log_mcp_communication.assert_called_once()
        call_args = mock_history_service.log_mcp_communication.call_args[1]
        
        assert call_args['session_id'] == 'mcp_session_123'
        assert call_args['server_name'] == 'kubernetes'
        assert call_args['communication_type'] == 'tool_call'
        assert call_args['tool_name'] == 'kubectl-get-pods'
        assert call_args['tool_arguments'] == {'namespace': 'default'}
        assert call_args['tool_result'] == {'output': 'pod1 Running\npod2 Pending'}
        assert call_args['success'] is True
        assert call_args['duration_ms'] == 2500
        assert call_args['error_message'] is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_error_scenario(self, mcp_hooks, mock_history_service):
        """Test MCP error scenario execution and logging."""
        error_msg = "Tool execution failed: kubectl not found"
        event_data = {
            'session_id': 'mcp_session_error',
            'method': 'call_tool',
            'args': {'server_name': 'kubernetes', 'tool_name': 'kubectl'},
            'result': None,
            'error': Exception(error_msg),
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(milliseconds=500)
        }
        
        await mcp_hooks.execute('mcp.error', **event_data)
        
        call_args = mock_history_service.log_mcp_communication.call_args[1]
        
        assert call_args['success'] is False
        assert call_args['error_message'] == error_msg
        assert call_args['tool_result'] is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_tool_list_operation(self, mcp_hooks, mock_history_service):
        """Test tool list operation execution."""
        event_data = {
            'session_id': 'mcp_session_list',
            'method': 'list_tools',
            'args': {'server_name': 'filesystem'},
            'result': {
                'tools': [
                    {'name': 'read_file', 'description': 'Read file contents'},
                    {'name': 'write_file', 'description': 'Write file contents'}
                ]
            },
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(milliseconds=300)
        }
        
        await mcp_hooks.execute('mcp.post', **event_data)
        
        call_args = mock_history_service.log_mcp_communication.call_args[1]
        
        assert call_args['communication_type'] == 'tool_list'
        assert call_args['available_tools'] == event_data['result']
        assert call_args['tool_name'] is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_ignores_pre_events(self, mcp_hooks, mock_history_service):
        """Test that pre-events are ignored."""
        event_data = {'session_id': 'test_session', 'args': {}}
        
        await mcp_hooks.execute('mcp.pre', **event_data)
        
        mock_history_service.log_mcp_communication.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_ignores_missing_session_id(self, mcp_hooks, mock_history_service):
        """Test that events without session_id are ignored."""
        event_data = {
            'method': 'call_tool',
            'args': {'server_name': 'test', 'tool_name': 'test_tool'},
            'result': {'success': True}
        }
        
        await mcp_hooks.execute('mcp.post', **event_data)
        
        mock_history_service.log_mcp_communication.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_history_service_failure(self, mcp_hooks, mock_history_service):
        """Test handling of history service failure."""
        mock_history_service.log_mcp_communication.return_value = False
        
        event_data = {
            'session_id': 'mcp_session_fail',
            'method': 'call_tool',
            'args': {'server_name': 'test', 'tool_name': 'test_tool'},
            'result': {'status': 'success'},
            'start_time': datetime.now(),
            'end_time': datetime.now()
        }
        
        # Should not raise exception despite service failure
        await mcp_hooks.execute('mcp.post', **event_data)
        
        mock_history_service.log_mcp_communication.assert_called_once()


class TestHistoryHookRegistration:
    """Test history hook registration functions."""
    
    @pytest.mark.unit
    def test_register_history_hooks(self):
        """Test registering history hooks with hook manager."""
        mock_hook_manager = Mock()
        
        with patch('tarsy.hooks.history_hooks.LLMHooks') as mock_llm_hooks_class:
            with patch('tarsy.hooks.history_hooks.MCPHooks') as mock_mcp_hooks_class:
                with patch('tarsy.hooks.base_hooks.get_hook_manager', return_value=mock_hook_manager):
                    mock_llm_hooks = Mock()
                    mock_mcp_hooks = Mock()
                    mock_llm_hooks_class.return_value = mock_llm_hooks
                    mock_mcp_hooks_class.return_value = mock_mcp_hooks
                    
                    result = register_history_hooks()
                    
                    # Verify hooks were created
                    mock_llm_hooks_class.assert_called_once()
                    mock_mcp_hooks_class.assert_called_once()
                    
                    # Verify hooks were registered
                    assert mock_hook_manager.register_hook.call_count == 4  # 2 LLM hooks + 2 MCP hooks
                    
                    # Verify return value
                    assert result == mock_hook_manager


if __name__ == "__main__":
    pytest.main([__file__]) 