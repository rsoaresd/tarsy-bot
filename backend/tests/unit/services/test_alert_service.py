"""
Unit tests for AlertService - Main alert processing orchestrator.

Tests the complete alert processing workflow including agent selection,
delegation, error handling, progress tracking, and history management.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest

from tarsy.config.settings import Settings
from tarsy.models.alert import Alert
from tarsy.services.alert_service import AlertService


@pytest.mark.unit
class TestAlertServiceInitialization:
    """Test AlertService initialization and setup."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = Mock(spec=Settings)
        settings.github_token = "test_token"
        settings.history_enabled = True
        return settings
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all AlertService dependencies."""
        with patch('tarsy.services.alert_service.RunbookService') as mock_runbook, \
             patch('tarsy.services.alert_service.get_history_service') as mock_history, \
             patch('tarsy.services.alert_service.AgentRegistry') as mock_registry, \
             patch('tarsy.services.alert_service.MCPServerRegistry') as mock_mcp_registry, \
             patch('tarsy.services.alert_service.MCPClient') as mock_mcp_client, \
             patch('tarsy.services.alert_service.LLMManager') as mock_llm_manager:
            
            yield {
                'runbook': mock_runbook.return_value,
                'history': mock_history.return_value,
                'registry': mock_registry.return_value,
                'mcp_registry': mock_mcp_registry.return_value,
                'mcp_client': mock_mcp_client.return_value,
                'llm_manager': mock_llm_manager.return_value
            }
    
    def test_initialization_success(self, mock_settings, mock_dependencies):
        """Test successful AlertService initialization."""
        service = AlertService(mock_settings)
        
        assert service.settings == mock_settings
        assert service.runbook_service == mock_dependencies['runbook']
        assert service.history_service == mock_dependencies['history']
        assert service.agent_registry == mock_dependencies['registry']
        assert service.mcp_server_registry == mock_dependencies['mcp_registry']
        assert service.mcp_client == mock_dependencies['mcp_client']
        assert service.llm_manager == mock_dependencies['llm_manager']
        assert service.agent_factory is None  # Not initialized yet
    
    def test_initialization_with_dependencies(self, mock_settings):
        """Test that dependencies are created with correct parameters."""
        with patch('tarsy.services.alert_service.RunbookService') as mock_runbook, \
             patch('tarsy.services.alert_service.get_history_service') as mock_history, \
             patch('tarsy.services.alert_service.AgentRegistry') as mock_registry, \
             patch('tarsy.services.alert_service.MCPServerRegistry') as mock_mcp_registry, \
             patch('tarsy.services.alert_service.MCPClient') as mock_mcp_client, \
             patch('tarsy.services.alert_service.LLMManager') as mock_llm_manager:
            
            service = AlertService(mock_settings)
            
            # Verify RunbookService created with settings
            mock_runbook.assert_called_once_with(mock_settings)
            
            # Verify MCP client created with settings and registry
            mock_mcp_client.assert_called_once_with(
                mock_settings, mock_mcp_registry.return_value
            )
            
            # Verify LLM manager created with settings
            mock_llm_manager.assert_called_once_with(mock_settings)


@pytest.mark.unit
class TestAlertServiceAsyncInitialization:
    """Test AlertService async initialization methods."""
    
    @pytest.fixture
    async def alert_service(self):
        """Create AlertService with mocked dependencies."""
        mock_settings = Mock(spec=Settings)
        
        with patch('tarsy.services.alert_service.RunbookService'), \
             patch('tarsy.services.alert_service.get_history_service'), \
             patch('tarsy.services.alert_service.AgentRegistry'), \
             patch('tarsy.services.alert_service.MCPServerRegistry'), \
             patch('tarsy.services.alert_service.MCPClient') as mock_mcp_client, \
             patch('tarsy.services.alert_service.LLMManager') as mock_llm_manager, \
             patch('tarsy.services.alert_service.AgentFactory') as mock_agent_factory:
            
            service = AlertService(mock_settings)
            
            # Setup mocks for initialize()
            service.mcp_client = AsyncMock()
            service.llm_manager = Mock()
            service.llm_manager.is_available.return_value = True
            service.agent_factory = mock_agent_factory.return_value
            
            yield service
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, alert_service):
        """Test successful async initialization."""
        with patch('tarsy.services.alert_service.AgentFactory') as mock_factory:
            await alert_service.initialize()
            
            # Verify MCP client initialization
            alert_service.mcp_client.initialize.assert_called_once()
            
            # Verify LLM availability check
            alert_service.llm_manager.is_available.assert_called_once()
            
            # Verify agent factory creation
            mock_factory.assert_called_once_with(
                llm_client=alert_service.llm_manager,
                mcp_client=alert_service.mcp_client,
                progress_callback=None,
                mcp_registry=alert_service.mcp_server_registry
            )
    
    @pytest.mark.asyncio
    async def test_initialize_llm_unavailable(self, alert_service):
        """Test initialization failure when LLM is unavailable."""
        alert_service.llm_manager.is_available.return_value = False
        alert_service.llm_manager.list_available_providers.return_value = ["provider1"]
        alert_service.llm_manager.get_availability_status.return_value = {"status": "error"}
        
        with pytest.raises(Exception, match="No LLM providers are available"):
            await alert_service.initialize()
    
    @pytest.mark.asyncio
    async def test_initialize_mcp_client_failure(self, alert_service):
        """Test initialization failure when MCP client initialization fails."""
        alert_service.mcp_client.initialize.side_effect = Exception("MCP init failed")
        
        with pytest.raises(Exception, match="MCP init failed"):
            await alert_service.initialize()


@pytest.mark.unit
class TestAlertProcessing:
    """Test the main alert processing workflow."""
    
    @pytest.fixture
    def sample_alert(self):
        """Create a sample alert for testing."""
        return Alert(
            alert_type="NamespaceTerminating",
            environment="production",
            cluster="main-cluster",
            namespace="test-namespace",
            runbook="https://github.com/company/runbooks/blob/main/k8s.md",
            message="Namespace is terminating",
            severity="critical"
        )
    
    @pytest.fixture
    async def initialized_service(self, sample_alert):
        """Create fully initialized AlertService."""
        mock_settings = Mock(spec=Settings)
        
        with patch('tarsy.services.alert_service.RunbookService') as mock_runbook, \
             patch('tarsy.services.alert_service.get_history_service') as mock_history, \
             patch('tarsy.services.alert_service.AgentRegistry') as mock_registry, \
             patch('tarsy.services.alert_service.MCPServerRegistry'), \
             patch('tarsy.services.alert_service.MCPClient'), \
             patch('tarsy.services.alert_service.LLMManager') as mock_llm_manager, \
             patch('tarsy.services.alert_service.AgentFactory') as mock_agent_factory:
            
            service = AlertService(mock_settings)
            
            # Setup successful dependencies
            service.mcp_client = AsyncMock()
            service.llm_manager = Mock()
            service.llm_manager.is_available.return_value = True
            
            # Setup agent registry
            service.agent_registry.get_agent_for_alert_type.return_value = "KubernetesAgent"
            service.agent_registry.get_supported_alert_types.return_value = ["NamespaceTerminating"]
            
            # Setup runbook service
            service.runbook_service = AsyncMock()
            service.runbook_service.download_runbook.return_value = "# Runbook content"
            
            # Setup agent factory and agent
            mock_agent = AsyncMock()
            mock_agent.process_alert.return_value = {
                'status': 'success',
                'analysis': 'Test analysis result',
                'iterations': 3,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            service.agent_factory = Mock()
            service.agent_factory.create_agent.return_value = mock_agent
            
            # Setup history service
            service.history_service = Mock()
            service.history_service.enabled = True
            service.history_service.create_session.return_value = "session_123"
            
            yield service, mock_agent
    
    @pytest.mark.asyncio
    async def test_process_alert_success(self, initialized_service, sample_alert):
        """Test successful alert processing workflow."""
        service, mock_agent = initialized_service
        progress_callback = AsyncMock()
        
        result = await service.process_alert(sample_alert, progress_callback)
        
        # Verify workflow steps
        service.agent_registry.get_agent_for_alert_type.assert_called_once_with("NamespaceTerminating")
        service.runbook_service.download_runbook.assert_called_once_with(sample_alert.runbook)
        service.agent_factory.create_agent.assert_called_once_with("KubernetesAgent")
        
        # Verify agent processing
        mock_agent.process_alert.assert_called_once()
        call_args = mock_agent.process_alert.call_args
        assert call_args[1]['alert'] == sample_alert
        assert call_args[1]['runbook_content'] == "# Runbook content"
        assert call_args[1]['session_id'] == "session_123"
        
        # Verify progress callbacks
        assert progress_callback.call_count >= 5
        progress_callback.assert_any_call(5, "Selecting specialized agent")
        progress_callback.assert_any_call(100, "Analysis completed successfully")
        
        # Verify result format
        assert "# Alert Analysis Report" in result
        assert "**Alert Type:** NamespaceTerminating" in result
        assert "**Processing Agent:** KubernetesAgent" in result
        assert "Test analysis result" in result
    
    @pytest.mark.asyncio
    async def test_process_alert_unsupported_type(self, initialized_service):
        """Test processing with unsupported alert type."""
        service, _ = initialized_service
        service.agent_registry.get_agent_for_alert_type.return_value = None
        
        unsupported_alert = Alert(
            alert_type="UnsupportedType",
            environment="test",
            cluster="test",
            namespace="test",
            runbook="http://example.com",
            message="Test",
            severity="low"
        )
        
        result = await service.process_alert(unsupported_alert)
        
        assert "# Alert Processing Error" in result
        assert "No specialized agent available for alert type: 'UnsupportedType'" in result
        assert "Supported alert types:" in result
    
    @pytest.mark.asyncio
    async def test_process_alert_agent_creation_failure(self, initialized_service, sample_alert):
        """Test agent creation failure handling."""
        service, _ = initialized_service
        service.agent_factory.create_agent.side_effect = ValueError("Agent creation failed")
        
        result = await service.process_alert(sample_alert)
        
        assert "# Alert Processing Error" in result
        assert "Failed to create agent: Agent creation failed" in result
    
    @pytest.mark.asyncio
    async def test_process_alert_agent_processing_failure(self, initialized_service, sample_alert):
        """Test agent processing failure handling."""
        service, mock_agent = initialized_service
        mock_agent.process_alert.return_value = {
            'status': 'error',
            'error': 'Agent processing failed'
        }
        
        result = await service.process_alert(sample_alert)
        
        assert "# Alert Processing Error" in result
        assert "Agent processing failed" in result
        assert "**Failed Agent:** KubernetesAgent" in result
    
    @pytest.mark.asyncio
    async def test_process_alert_llm_unavailable(self, initialized_service, sample_alert):
        """Test processing when LLM becomes unavailable."""
        service, _ = initialized_service
        service.llm_manager.is_available.return_value = False
        
        result = await service.process_alert(sample_alert)
        
        assert "# Alert Processing Error" in result
        assert "Cannot process alert: No LLM providers are available" in result
    
    @pytest.mark.asyncio
    async def test_process_alert_agent_factory_not_initialized(self, initialized_service, sample_alert):
        """Test processing when agent factory is not initialized."""
        service, _ = initialized_service
        service.agent_factory = None
        
        result = await service.process_alert(sample_alert)
        
        assert "# Alert Processing Error" in result
        assert "Agent factory not initialized - call initialize() first" in result
    
    @pytest.mark.asyncio
    async def test_process_alert_runbook_download_failure(self, initialized_service, sample_alert):
        """Test runbook download failure handling."""
        service, _ = initialized_service
        service.runbook_service.download_runbook.side_effect = Exception("Download failed")
        
        result = await service.process_alert(sample_alert)
        
        assert "# Alert Processing Error" in result
        assert "Alert processing failed: Download failed" in result


@pytest.mark.unit
class TestHistorySessionManagement:
    """Test history session management methods."""
    
    @pytest.fixture
    def alert_service_with_history(self):
        """Create AlertService with mocked history service."""
        mock_settings = Mock(spec=Settings)
        
        with patch('tarsy.services.alert_service.RunbookService'), \
             patch('tarsy.services.alert_service.get_history_service') as mock_history, \
             patch('tarsy.services.alert_service.AgentRegistry'), \
             patch('tarsy.services.alert_service.MCPServerRegistry'), \
             patch('tarsy.services.alert_service.MCPClient'), \
             patch('tarsy.services.alert_service.LLMManager'):
            
            service = AlertService(mock_settings)
            service.history_service = Mock()
            service.history_service.enabled = True
            service.agent_registry = Mock()
            
            yield service
    
    @pytest.fixture
    def sample_alert(self):
        """Create sample alert for history testing."""
        return Alert(
            alert_type="NamespaceTerminating",
            environment="production",
            cluster="main-cluster",
            namespace="test-namespace",
            runbook="https://github.com/company/runbooks/blob/main/k8s.md",
            message="Namespace is terminating",
            severity="critical"
        )
    
    def test_create_history_session_success(self, alert_service_with_history, sample_alert):
        """Test successful history session creation."""
        service = alert_service_with_history
        service.agent_registry.get_agent_for_alert_type.return_value = "KubernetesAgent"
        service.history_service.create_session.return_value = "session_123"
        
        session_id = service._create_history_session(sample_alert, "KubernetesAgent")
        
        assert session_id == "session_123"
        service.history_service.create_session.assert_called_once()
        
        # Verify call arguments
        call_args = service.history_service.create_session.call_args
        assert call_args[1]['agent_type'] == "KubernetesAgent"
        assert call_args[1]['alert_type'] == "NamespaceTerminating"
        assert 'alert_data' in call_args[1]
        
        alert_data = call_args[1]['alert_data']
        assert alert_data['alert_type'] == "NamespaceTerminating"
        assert alert_data['environment'] == "production"
        assert alert_data['cluster'] == "main-cluster"
        assert alert_data['namespace'] == "test-namespace"
    
    def test_create_history_session_disabled(self, alert_service_with_history, sample_alert):
        """Test history session creation when service is disabled."""
        service = alert_service_with_history
        service.history_service.enabled = False
        
        session_id = service._create_history_session(sample_alert)
        
        assert session_id is None
        service.history_service.create_session.assert_not_called()
    
    def test_create_history_session_no_service(self, alert_service_with_history, sample_alert):
        """Test history session creation when service is None."""
        service = alert_service_with_history
        service.history_service = None
        
        session_id = service._create_history_session(sample_alert)
        
        assert session_id is None
    
    def test_create_history_session_with_exception(self, alert_service_with_history, sample_alert):
        """Test history session creation with exception handling."""
        service = alert_service_with_history
        service.history_service.create_session.side_effect = Exception("Database error")
        
        # Should not raise exception, but return None
        session_id = service._create_history_session(sample_alert)
        
        assert session_id is None
    
    def test_update_session_status_success(self, alert_service_with_history):
        """Test successful session status update."""
        service = alert_service_with_history
        
        service._update_session_status("session_123", "in_progress", "Processing alert")
        
        service.history_service.update_session_status.assert_called_once_with(
            session_id="session_123",
            status="in_progress"
        )
    
    def test_update_session_status_disabled(self, alert_service_with_history):
        """Test session status update when service is disabled."""
        service = alert_service_with_history
        service.history_service.enabled = False
        
        service._update_session_status("session_123", "in_progress")
        
        service.history_service.update_session_status.assert_not_called()
    
    def test_update_session_completed_success(self, alert_service_with_history):
        """Test marking session as completed."""
        service = alert_service_with_history
        
        service._update_session_completed("session_123", "completed")
        
        service.history_service.update_session_status.assert_called_once_with(
            session_id="session_123",
            status="completed",
            final_analysis=None
        )
    
    def test_update_session_completed_with_final_analysis(self, alert_service_with_history):
        """Test marking session as completed with final analysis."""
        service = alert_service_with_history
        analysis = "# Alert Analysis\n\nSuccessfully resolved the issue."
        
        service._update_session_completed("session_123", "completed", analysis)
        
        service.history_service.update_session_status.assert_called_once_with(
            session_id="session_123",
            status="completed",
            final_analysis=analysis
        )
    
    def test_update_session_error_success(self, alert_service_with_history):
        """Test marking session as failed with error."""
        service = alert_service_with_history
        
        service._update_session_error("session_123", "Processing failed")
        
        service.history_service.update_session_status.assert_called_once_with(
            session_id="session_123",
            status="failed",
            error_message="Processing failed"
        )


@pytest.mark.unit
class TestResponseFormatting:
    """Test response formatting methods."""
    
    @pytest.fixture
    def alert_service(self):
        """Create basic AlertService for formatting tests."""
        mock_settings = Mock(spec=Settings)
        
        with patch('tarsy.services.alert_service.RunbookService'), \
             patch('tarsy.services.alert_service.get_history_service'), \
             patch('tarsy.services.alert_service.AgentRegistry'), \
             patch('tarsy.services.alert_service.MCPServerRegistry'), \
             patch('tarsy.services.alert_service.MCPClient'), \
             patch('tarsy.services.alert_service.LLMManager'):
            
            return AlertService(mock_settings)
    
    @pytest.fixture
    def sample_alert(self):
        """Create sample alert for formatting tests."""
        return Alert(
            alert_type="NamespaceTerminating",
            environment="production",
            cluster="main-cluster",
            namespace="test-namespace",
            runbook="https://github.com/company/runbooks/blob/main/k8s.md",
            message="Namespace is terminating",
            severity="critical"
        )
    
    def test_format_success_response(self, alert_service, sample_alert):
        """Test formatting successful response."""
        result = alert_service._format_success_response(
            alert=sample_alert,
            agent_name="KubernetesAgent",
            analysis="Detailed analysis result",
            iterations=3,
            timestamp="2024-01-01T12:00:00Z"
        )
        
        assert "# Alert Analysis Report" in result
        assert "**Alert Type:** NamespaceTerminating" in result
        assert "**Processing Agent:** KubernetesAgent" in result
        assert "**Environment:** production" in result
        assert "**Severity:** critical" in result
        assert "**Timestamp:** 2024-01-01T12:00:00Z" in result
        assert "## Analysis" in result
        assert "Detailed analysis result" in result
        assert "*Processed by KubernetesAgent in 3 iterations*" in result
    
    def test_format_success_response_without_timestamp(self, alert_service, sample_alert):
        """Test formatting successful response without timestamp."""
        result = alert_service._format_success_response(
            alert=sample_alert,
            agent_name="KubernetesAgent",
            analysis="Test analysis",
            iterations=1
        )
        
        # Should include current timestamp
        assert "**Timestamp:**" in result
        assert "# Alert Analysis Report" in result
    
    def test_format_error_response_basic(self, alert_service, sample_alert):
        """Test formatting basic error response."""
        result = alert_service._format_error_response(
            alert=sample_alert,
            error="Processing failed"
        )
        
        assert "# Alert Processing Error" in result
        assert "**Alert Type:** NamespaceTerminating" in result
        assert "**Environment:** production" in result
        assert "**Error:** Processing failed" in result
        assert "## Troubleshooting" in result
        assert "Check that the alert type is supported" in result
    
    def test_format_error_response_with_agent(self, alert_service, sample_alert):
        """Test formatting error response with agent information."""
        result = alert_service._format_error_response(
            alert=sample_alert,
            error="Agent initialization failed",
            agent_name="KubernetesAgent"
        )
        
        assert "# Alert Processing Error" in result
        assert "**Failed Agent:** KubernetesAgent" in result
        assert "**Error:** Agent initialization failed" in result


@pytest.mark.unit
class TestCleanup:
    """Test cleanup and resource management."""
    
    @pytest.fixture
    async def alert_service_with_resources(self):
        """Create AlertService with resource mocks."""
        mock_settings = Mock(spec=Settings)
        
        with patch('tarsy.services.alert_service.RunbookService') as mock_runbook, \
             patch('tarsy.services.alert_service.get_history_service'), \
             patch('tarsy.services.alert_service.AgentRegistry'), \
             patch('tarsy.services.alert_service.MCPServerRegistry'), \
             patch('tarsy.services.alert_service.MCPClient') as mock_mcp_client, \
             patch('tarsy.services.alert_service.LLMManager'):
            
            service = AlertService(mock_settings)
            service.runbook_service = AsyncMock()
            service.mcp_client = AsyncMock()
            
            yield service
    
    @pytest.mark.asyncio
    async def test_close_success(self, alert_service_with_resources):
        """Test successful resource cleanup."""
        service = alert_service_with_resources
        
        await service.close()
        
        service.runbook_service.close.assert_called_once()
        service.mcp_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_with_exception(self, alert_service_with_resources):
        """Test cleanup with exception handling."""
        service = alert_service_with_resources
        service.runbook_service.close.side_effect = Exception("Cleanup failed")
        
        # Should not raise exception
        await service.close()
        
        # Only the first cleanup method should be attempted due to exception handling
        service.runbook_service.close.assert_called_once()
        service.mcp_client.close.assert_not_called() 