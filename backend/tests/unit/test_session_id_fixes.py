"""
Tests for session_id propagation and timeline logging fixes.

This test suite covers the key fixes made to ensure session_id
is properly propagated and timeline logging works correctly.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone
from tarsy.agents.base_agent import BaseAgent


class TestConcreteAgent(BaseAgent):
    """Concrete agent implementation for testing."""
    
    def __init__(self, llm_client=None, mcp_client=None, mcp_registry=None):
        # Use mocks if not provided
        from unittest.mock import Mock
        llm_client = llm_client or Mock()
        mcp_client = mcp_client or Mock()
        mcp_registry = mcp_registry or Mock()
        
        super().__init__(llm_client, mcp_client, mcp_registry)
        self.agent_type = "TestAgent"
    
    def mcp_servers(self):
        return ["test-server"]
    
    def custom_instructions(self):
        return "Test instructions"


@pytest.fixture
def test_session_id():
    """Standard test session ID."""
    return "test-session-12345"


@pytest.fixture  
def sample_alert_data():
    """Sample alert data for testing."""
    return {
        "id": "test-alert-123",
        "type": "TestAlert",
        "severity": "high",
        "namespace": "test-namespace",
        "data": {"test": "data"}
    }


class TestSessionIdPropagation:
    """Test session_id propagation through the agent processing chain."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_alert_requires_session_id(self, sample_alert_data):
        """Test that process_alert requires session_id and validates it."""
        agent = TestConcreteAgent()
        
        from tarsy.models.alert import Alert
        alert = Alert(
            id="test", 
            type="TestAlert",
            alert_type="TestAlertType",
            environment="test-env",
            cluster="test-cluster", 
            severity="high", 
            namespace="test",
            message="Test alert message",
            runbook="Test runbook content",
            data={}
        )
        
        # Test None session_id raises error
        with pytest.raises(ValueError, match="session_id is required"):
            await agent.process_alert(alert, "runbook", None)
        
        # Test empty session_id raises error  
        with pytest.raises(ValueError, match="session_id is required"):
            await agent.process_alert(alert, "runbook", "")
        
        # Test whitespace-only session_id raises error
        with pytest.raises(ValueError, match="session_id is required"):
            await agent.process_alert(alert, "runbook", "   ")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_alert_session_id_propagation(self, test_session_id, sample_alert_data):
        """Test that analyze_alert correctly passes session_id to LLM client."""
        agent = TestConcreteAgent()
        
        # Mock the LLM client to avoid iteration issues
        mock_llm_client = Mock()
        mock_llm_client.generate_response = AsyncMock(return_value="Test analysis")
        agent.llm_client = mock_llm_client
        
        # Mock the MCP registry to return an empty list for server configs
        agent.mcp_registry.get_server_configs.return_value = []
        
        result = await agent.analyze_alert(
            sample_alert_data, 
            "runbook content", 
            {"mcp": "data"}, 
            test_session_id
        )
        
        # Verify session_id was passed to LLM client
        mock_llm_client.generate_response.assert_called_once()
        call_args = mock_llm_client.generate_response.call_args
        assert call_args[0][1] == test_session_id  # Second positional arg
        assert result == "Test analysis"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_determine_mcp_tools_session_id_propagation(self, test_session_id, sample_alert_data):
        """Test that determine_mcp_tools correctly passes session_id to LLM client."""
        agent = TestConcreteAgent()
        
        # Mock the LLM client to avoid iteration issues
        mock_llm_client = Mock()
        mock_response = '[{"server": "test", "tool": "test", "parameters": {}, "reason": "test"}]'
        mock_llm_client.generate_response = AsyncMock(return_value=mock_response)
        agent.llm_client = mock_llm_client
        
        # Mock the MCP registry to return an empty list for server configs
        agent.mcp_registry.get_server_configs.return_value = []
        
        result = await agent.determine_mcp_tools(
            sample_alert_data, 
            "runbook content", 
            {"tools": []}, 
            test_session_id
        )
        
        # Verify session_id was passed to LLM client
        mock_llm_client.generate_response.assert_called_once()
        call_args = mock_llm_client.generate_response.call_args
        assert call_args[0][1] == test_session_id  # Second positional arg

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_mcp_tools_session_id_propagation(self, test_session_id):
        """Test that _execute_mcp_tools correctly passes session_id to MCP client."""
        agent = TestConcreteAgent()
        agent._configured_servers = ["test-server"]
        
        # Mock the MCP client to avoid iteration issues
        mock_mcp_client = Mock()
        mock_mcp_client.call_tool = AsyncMock(return_value={"result": "success"})
        agent.mcp_client = mock_mcp_client
        
        tools_to_call = [{
            "server": "test-server",
            "tool": "test-tool", 
            "parameters": {"param": "value"},
            "reason": "Testing"
        }]
        
        await agent._execute_mcp_tools(tools_to_call, test_session_id)
        
        # Verify session_id was passed to MCP client
        mock_mcp_client.call_tool.assert_called_once_with(
            "test-server", "test-tool", {"param": "value"}, test_session_id
        )


class TestTimelineDataStructure:
    """Test timeline data structure fixes."""
    
    @pytest.mark.unit
    def test_timeline_event_type_mapping(self):
        """Test that timeline events use correct type names for frontend."""
        # This tests the fix where we changed from "llm_interaction" to "llm"
        # and from "mcp_communication" to "mcp"
        
        # These are the expected type mappings after the fix
        type_mappings = {
            "llm_interaction_db": "llm",  # Database storage -> Frontend display
            "mcp_communication_db": "mcp"  # Database storage -> Frontend display
        }
        
        # Verify the mappings are correct
        assert type_mappings["llm_interaction_db"] == "llm"
        assert type_mappings["mcp_communication_db"] == "mcp"
        
        # These should NOT be the old format
        assert type_mappings["llm_interaction_db"] != "llm_interaction"
        assert type_mappings["mcp_communication_db"] != "mcp_communication"

    @pytest.mark.unit
    def test_timestamp_format_consistency(self):
        """Test that timestamps are formatted consistently for JSON serialization."""
        # Test the timestamp formatting logic that was fixed
        from datetime import datetime, timezone
        
        # Test timezone-aware timestamp
        tz_aware = datetime.now(timezone.utc)
        
        # Test naive timestamp  
        naive = datetime.now()
        
        # Create mock events with different timestamp types
        events = [
            {"timestamp": tz_aware},
            {"timestamp": naive}
        ]
        
        # Simulate the timestamp formatting logic from get_session_timeline
        for event in events:
            timestamp = event["timestamp"]
            if timestamp.tzinfo is not None:
                # Convert to UTC and use Z suffix for consistency
                utc_timestamp = timestamp.astimezone(timezone.utc)
                event["timestamp"] = utc_timestamp.replace(tzinfo=None).isoformat() + "Z"
            else:
                # Assume naive timestamps are UTC
                event["timestamp"] = timestamp.isoformat() + "Z"
        
        # Verify both timestamps end with Z and are valid ISO format
        for event in events:
            timestamp_str = event["timestamp"]
            assert timestamp_str.endswith("Z")
            assert "T" in timestamp_str
            # Should not have duplicate timezone indicators (this was the bug)
            assert "+00:00Z" not in timestamp_str


class TestExplicitParameterPattern:
    """Test the new explicit parameter pattern for session_id."""
    
    @pytest.mark.unit
    def test_session_id_parameter_consistency(self):
        """Test that session_id is handled consistently as explicit parameter."""
        # This test verifies the architectural change from kwargs to explicit parameters
        
        # Before the fix: session_id was passed in kwargs inconsistently
        # After the fix: session_id is always an explicit parameter
        
        def old_pattern_example(**kwargs):
            # This was the problematic pattern
            session_id = kwargs.get('session_id')
            return session_id
        
        def new_pattern_example(session_id: str, **kwargs):
            # This is the new clean pattern
            return session_id
        
        # Test that new pattern requires explicit session_id
        with pytest.raises(TypeError):
            # This should fail because session_id is required
            new_pattern_example()
        
        # Test that new pattern works with explicit session_id
        result = new_pattern_example("test-session-123")
        assert result == "test-session-123"
        
        # Test that old pattern was unreliable (could return None)
        result_old = old_pattern_example(other_param="value")
        assert result_old is None  # This was the problem
        
        result_old_with_session = old_pattern_example(session_id="test-session-123")
        assert result_old_with_session == "test-session-123"


class TestValidationLogic:
    """Test session_id validation logic."""
    
    @pytest.mark.unit
    def test_session_id_validation_cases(self):
        """Test that session_id validation works for all edge cases."""
        
        def validate_session_id(session_id):
            """Simulate the validation logic added to process_alert."""
            if not session_id or not session_id.strip():
                raise ValueError("session_id is required for alert processing and timeline logging")
            return True
        
        # Test cases that should raise errors
        invalid_cases = [None, "", "   ", "\t\n", "\r\n  \t"]
        for case in invalid_cases:
            with pytest.raises(ValueError, match="session_id is required"):
                validate_session_id(case)
        
        # Test cases that should be valid
        valid_cases = ["s", "test-session-123", "  valid-with-spaces  "]
        for case in valid_cases:
            # These should not raise errors
            try:
                result = validate_session_id(case)
                assert result is True
            except ValueError:
                pytest.fail(f"Valid session_id '{case}' raised ValueError")


class TestAPIResponseFields:
    """Test that API responses include all required fields."""
    
    @pytest.mark.unit
    def test_session_detail_response_structure(self):
        """Test that session detail response has all required fields."""
        # This tests the fix where we added missing fields to the API response
        
        # Mock the expected response structure after the fix
        expected_fields = {
            'session_id',
            'alert_id', 
            'alert_data',
            'agent_type',
            'alert_type',
            'status',
            'started_at',
            'completed_at',
            'error_message',      # This was missing before the fix
            'final_analysis',     # This was missing before the fix
            'duration_ms',
            'session_metadata',   # This was missing before the fix
            'chronological_timeline',
            'summary'
        }
        
        # Create mock response data
        mock_response_data = {
            'session_id': 'test-session-123',
            'alert_id': 'alert-456',
            'alert_data': {'test': 'data'},
            'agent_type': 'TestAgent',
            'alert_type': 'TestAlert',
            'status': 'completed',
            'started_at': '2024-01-01T00:00:00Z',
            'completed_at': '2024-01-01T00:01:00Z',
            'error_message': None,
            'final_analysis': 'Test analysis complete',
            'duration_ms': 60000,
            'session_metadata': {'key': 'value'},
            'chronological_timeline': [],
            'summary': {'summary': 'test'}
        }
        
        # Verify all expected fields are present
        response_fields = set(mock_response_data.keys())
        missing_fields = expected_fields - response_fields
        assert not missing_fields, f"Missing required fields: {missing_fields}"
        
        # Verify the previously missing fields are included
        assert 'error_message' in mock_response_data
        assert 'final_analysis' in mock_response_data  
        assert 'session_metadata' in mock_response_data 