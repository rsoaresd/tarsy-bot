"""
Unit tests for BaseAgent.

Tests the base agent functionality with mocked dependencies to ensure
proper interface implementation and parameter handling.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from tarsy.agents.base_agent import BaseAgent
from tarsy.integrations.llm.client import LLMClient
from tarsy.integrations.mcp.client import MCPClient
from tarsy.models.alert import Alert
from tarsy.services.mcp_server_registry import MCPServerRegistry


class TestConcreteAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""
    
    def mcp_servers(self):
        return ["test-server"]
    
    def custom_instructions(self):
        return "Test instructions"


@pytest.mark.unit
class TestBaseAgent:
    """Test suite for BaseAgent class."""
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        client = Mock(spec=LLMClient)
        client.generate_response = AsyncMock(return_value="Test analysis result")
        return client
    
    @pytest.fixture
    def mock_mcp_client(self):
        """Create mock MCP client."""
        client = Mock(spec=MCPClient)
        client.list_tools = AsyncMock(return_value={"test-server": []})
        client.call_tool = AsyncMock(return_value={"result": "test"})
        return client
    
    @pytest.fixture
    def mock_mcp_registry(self):
        """Create mock MCP server registry."""
        registry = Mock(spec=MCPServerRegistry)
        mock_config = Mock()
        mock_config.server_id = "test-server"
        mock_config.server_type = "test"
        mock_config.instructions = "Test server instructions"
        registry.get_server_configs.return_value = [mock_config]
        return registry
    
    @pytest.fixture
    def sample_alert(self):
        """Create a sample alert for testing."""
        return Alert(
            alert_type="TestAlert",
            severity="high",
            environment="test",
            cluster="test-cluster",
            namespace="test-namespace",
            message="Test alert message",
            runbook="test-runbook.md"
        )
    
    @pytest.fixture
    def base_agent(self, mock_llm_client, mock_mcp_client, mock_mcp_registry):
        """Create a concrete BaseAgent instance for testing."""
        return TestConcreteAgent(
            llm_client=mock_llm_client,
            mcp_client=mock_mcp_client,
            mcp_registry=mock_mcp_registry
        )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_process_alert_with_session_id_parameter(
        self, 
        base_agent, 
        sample_alert,
        mock_mcp_client
    ):
        """Test that process_alert accepts session_id parameter without error."""
        # Arrange
        runbook_content = "Test runbook content"
        session_id = "test-session-123"
        progress_callback = Mock()
        
        # Mock the tools listing to avoid MCP calls
        mock_mcp_client.list_tools.return_value = {"test-server": []}
        
        # Act - This should not raise a TypeError about unexpected keyword argument
        result = await base_agent.process_alert(
            alert=sample_alert,
            runbook_content=runbook_content,
            callback=progress_callback,
            session_id=session_id
        )
        
        # Assert
        assert result is not None
        assert isinstance(result, dict)
        assert result["status"] in ["success", "error"]
        assert result["agent"] == "TestConcreteAgent"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_process_alert_without_session_id_parameter(
        self, 
        base_agent, 
        sample_alert,
        mock_mcp_client
    ):
        """Test that process_alert works without session_id parameter."""
        # Arrange
        runbook_content = "Test runbook content"
        progress_callback = Mock()
        
        # Mock the tools listing to avoid MCP calls
        mock_mcp_client.list_tools.return_value = {"test-server": []}
        
        # Act - Should work without session_id parameter
        result = await base_agent.process_alert(
            alert=sample_alert,
            runbook_content=runbook_content,
            callback=progress_callback
        )
        
        # Assert
        assert result is not None
        assert isinstance(result, dict)
        assert result["status"] in ["success", "error"]
        assert result["agent"] == "TestConcreteAgent"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_process_alert_with_none_session_id(
        self, 
        base_agent, 
        sample_alert,
        mock_mcp_client
    ):
        """Test that process_alert works with None session_id."""
        # Arrange
        runbook_content = "Test runbook content"
        progress_callback = Mock()
        
        # Mock the tools listing to avoid MCP calls
        mock_mcp_client.list_tools.return_value = {"test-server": []}
        
        # Act - Should work with explicit None session_id
        result = await base_agent.process_alert(
            alert=sample_alert,
            runbook_content=runbook_content,
            callback=progress_callback,
            session_id=None
        )
        
        # Assert
        assert result is not None
        assert isinstance(result, dict)
        assert result["status"] in ["success", "error"]
        assert result["agent"] == "TestConcreteAgent"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_process_alert_parameter_order_flexibility(
        self, 
        base_agent, 
        sample_alert,
        mock_mcp_client
    ):
        """Test that process_alert accepts parameters in different orders."""
        # Arrange
        runbook_content = "Test runbook content"
        session_id = "test-session-456"
        progress_callback = Mock()
        
        # Mock the tools listing to avoid MCP calls
        mock_mcp_client.list_tools.return_value = {"test-server": []}
        
        # Act - Pass parameters in different order using keywords
        result = await base_agent.process_alert(
            session_id=session_id,
            callback=progress_callback,
            alert=sample_alert,
            runbook_content=runbook_content
        )
        
        # Assert
        assert result is not None
        assert isinstance(result, dict)
        assert result["status"] in ["success", "error"]
        assert result["agent"] == "TestConcreteAgent"
    
    @pytest.mark.unit
    def test_concrete_agent_abstract_methods(self, base_agent):
        """Test that concrete agent properly implements abstract methods."""
        # Act & Assert
        assert base_agent.mcp_servers() == ["test-server"]
        assert base_agent.custom_instructions() == "Test instructions"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_process_alert_error_handling_preserves_session_id_interface(
        self, 
        base_agent, 
        sample_alert,
        mock_mcp_client
    ):
        """Test error handling preserves session_id interface."""
        # Arrange
        runbook_content = "Test runbook content"
        session_id = "test-session-error"
        
        # Mock MCP client to raise an error
        mock_mcp_client.list_tools.side_effect = Exception("MCP connection failed")
        
        # Act - Should handle error gracefully while preserving interface
        result = await base_agent.process_alert(
            alert=sample_alert,
            runbook_content=runbook_content,
            session_id=session_id
        )
        
        # Assert - Agent handles MCP errors gracefully and continues with analysis
        assert result is not None
        assert isinstance(result, dict)
        assert result["status"] in ["success", "error"]  # Either is acceptable
        assert result["agent"] == "TestConcreteAgent" 