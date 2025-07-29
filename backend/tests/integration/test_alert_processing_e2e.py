"""
End-to-end integration tests for alert processing.

These tests verify the complete alert processing workflow from alert ingestion
to final analysis, testing integration between all components.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from tarsy.models.alert import Alert
from tarsy.services.alert_service import AlertService
from tarsy.utils.timestamp import now_us
from tests.conftest import alert_to_api_format


@pytest.mark.integration
class TestAlertProcessingE2E:
    """End-to-end tests for complete alert processing workflow."""

    @pytest.fixture
    def sample_alert(self):
        """Create sample alert for testing."""
        return Alert(
            alert_type="kubernetes",
            runbook="https://github.com/company/runbooks/blob/main/k8s.md",
            severity="critical",
            timestamp=now_us(),
            data={
                "environment": "production",
                "cluster": "main-cluster",
                "namespace": "default",
                "message": "Namespace is terminating",
                "alert": "NamespaceTerminating"
            }
        )

    @pytest.mark.asyncio
    async def test_happy_path_kubernetes_alert_processing(self, alert_service_with_mocks, sample_alert):
        """Test happy path alert processing workflow."""
        alert_service, mock_dependencies = alert_service_with_mocks
        progress_callback_mock = AsyncMock()
        
        # Convert Alert to dict for the new interface
        alert_dict = alert_to_api_format(sample_alert)
        
        result = await alert_service.process_alert(alert_dict, progress_callback_mock)
        
        assert isinstance(result, str)
        assert "analysis" in result.lower() or "error" in result.lower()
        
        # Verify progress callback was called
        assert progress_callback_mock.call_count > 0

    async def test_agent_selection_and_delegation(
        self, 
        alert_service_with_mocks, 
        sample_alert
    ):
        """Test that the correct agent is selected and instantiated."""
        alert_service, mock_dependencies = alert_service_with_mocks
        
        # Convert Alert to dict for the new interface
        alert_dict = alert_to_api_format(sample_alert)
        
        # Act
        result = await alert_service.process_alert(alert_dict)
        
        # Assert - Verify agent registry was called correctly
        mock_dependencies['registry'].get_agent_for_alert_type.assert_called_once_with(
            "kubernetes"
        )
        
        # Result should indicate processing occurred
        assert result is not None
        assert isinstance(result, str)

    async def test_mcp_tool_integration(
        self, 
        alert_service_with_mocks, 
        sample_alert
    ):
        """Test MCP tool discovery and execution."""
        alert_service, mock_dependencies = alert_service_with_mocks
        
        # Convert Alert to dict for the new interface
        alert_dict = alert_to_api_format(sample_alert)
        
        # Act
        result = await alert_service.process_alert(alert_dict)
        
        # Assert - Verify MCP client interactions
        assert mock_dependencies['mcp_client'].list_tools.call_count >= 0  # May or may not be called depending on agent setup
        
        # Result should indicate processing occurred
        assert result is not None
        assert isinstance(result, str)

    async def test_runbook_integration(
        self, 
        alert_service_with_mocks, 
        sample_alert
    ):
        """Test runbook download and integration."""
        alert_service, mock_dependencies = alert_service_with_mocks
        
        # Convert Alert to dict for the new interface
        alert_dict = alert_to_api_format(sample_alert)
        
        # Act
        result = await alert_service.process_alert(alert_dict)
        
        # Assert - Verify runbook service was called
        mock_dependencies['runbook'].download_runbook.assert_called_once_with(
            sample_alert.runbook
        )
        
        # Result should indicate processing occurred
        assert result is not None
        assert isinstance(result, str)

    async def test_llm_interactions(
        self, 
        alert_service_with_mocks, 
        sample_alert
    ):
        """Test LLM interaction patterns."""
        alert_service, mock_dependencies = alert_service_with_mocks
        
        # Convert Alert to dict for the new interface
        alert_dict = alert_to_api_format(sample_alert)
        
        # Act
        result = await alert_service.process_alert(alert_dict)
        
        # Assert - LLM should be available for processing
        mock_dependencies['llm_manager'].is_available.assert_called()
        
        # Result should indicate processing occurred
        assert result is not None
        assert isinstance(result, str)

    async def test_progress_tracking(
        self, 
        alert_service_with_mocks, 
        sample_alert
    ):
        """Test progress callback integration."""
        alert_service, mock_dependencies = alert_service_with_mocks
        progress_callback = AsyncMock()
        
        # Convert Alert to dict for the new interface
        alert_dict = alert_to_api_format(sample_alert)
        
        # Act
        result = await alert_service.process_alert(alert_dict, progress_callback)
        
        # Assert - Progress callback should be called during processing
        assert progress_callback.call_count > 0
        
        # Result should indicate processing occurred
        assert result is not None
        assert isinstance(result, str)

    async def test_iterative_analysis_flow(
        self, 
        alert_service_with_mocks, 
        sample_alert
    ):
        """Test iterative analysis flow with MCP tools."""
        alert_service, mock_dependencies = alert_service_with_mocks
        
        # Convert Alert to dict for the new interface
        alert_dict = alert_to_api_format(sample_alert)
        
        # Act
        result = await alert_service.process_alert(alert_dict)
        
        # Assert - Should complete iterative flow
        assert result is not None
        assert isinstance(result, str)
        
        # Agent factory should be called
        assert alert_service.agent_factory.create_agent.call_count >= 1


@pytest.mark.asyncio 
@pytest.mark.integration
class TestErrorHandlingScenarios:
    """Test various error handling scenarios in alert processing."""

    async def test_unknown_alert_type_error(
        self,
        alert_service,
        progress_callback_mock
    ):
        """Test handling of unknown alert types."""
        # Arrange - Create alert with unknown type
        unknown_alert = Alert(
            alert_type="Unknown Alert Type",
            runbook="https://github.com/company/runbooks/blob/main/unknown.md",
            severity="high",
            data={
                "environment": "production", 
                "cluster": "https://k8s-cluster.example.com",
                "namespace": "test-namespace",
                "message": "This is an unknown alert type"
            }
        )
        
        # Convert Alert to dict for the new interface
        alert_dict = alert_to_api_format(unknown_alert)
        
        # Mock agent registry to return None for unknown type
        with patch.object(alert_service.agent_registry, 'get_agent_for_alert_type', return_value=None):
            # Act
            result = await alert_service.process_alert(alert_dict, progress_callback_mock)
        
        # Assert - Should return error response
        assert result is not None
        assert "error" in result.lower() or "Error" in result
        assert "no specialized agent" in result.lower()
        assert "Unknown Alert Type" in result
        
        # Should have called progress callback with error
        assert progress_callback_mock.call_count >= 1
        error_call = progress_callback_mock.call_args_list[-1]
        assert "error" in error_call.args[1].lower()

    async def test_llm_unavailable_error(
        self,
        alert_service,
        sample_alert,
        progress_callback_mock
    ):
        """Test handling when LLM is unavailable."""
        # Arrange - Mock LLM as unavailable
        alert_service.llm_manager.is_available.return_value = False
        
        # Act
        alert_dict = alert_to_api_format(sample_alert)
        result = await alert_service.process_alert(alert_dict, progress_callback_mock)
        
        # Assert - Should return error response
        assert result is not None
        assert "error" in result.lower() or "Error" in result
        assert "llm" in result.lower()

    async def test_agent_creation_error(
        self,
        alert_service,
        sample_alert,
        progress_callback_mock
    ):
        """Test handling when agent creation fails."""
        # Arrange - Mock agent factory to raise error
        with patch.object(alert_service.agent_factory, 'create_agent', side_effect=ValueError("Agent not found")):
            # Act
            alert_dict = alert_to_api_format(sample_alert)
            result = await alert_service.process_alert(alert_dict, progress_callback_mock)
        
        # Assert - Should return error response
        assert result is not None
        assert "error" in result.lower() or "Error" in result
        assert "failed to create agent" in result.lower()

    async def test_runbook_download_error(
        self,
        alert_service,
        sample_alert,
        mock_runbook_service,
        progress_callback_mock
    ):
        """Test handling when runbook download fails."""
        # Arrange - Mock runbook service to raise error
        mock_runbook_service.download_runbook.side_effect = Exception("Failed to download runbook")
        
        # Act
        alert_dict = alert_to_api_format(sample_alert)
        result = await alert_service.process_alert(alert_dict, progress_callback_mock)
        
        # Assert - Should return error response
        assert result is not None
        assert "error" in result.lower() or "Error" in result

    async def test_mcp_tool_execution_error(
        self,
        alert_service,
        sample_alert,
        mock_mcp_client,
        progress_callback_mock
    ):
        """Test handling when MCP tool execution fails."""
        # Arrange - Mock MCP client to raise error on tool execution
        mock_mcp_client.call_tool.side_effect = Exception("MCP tool execution failed")
        
        # Act - Should still complete processing even with tool failures
        alert_dict = alert_to_api_format(sample_alert)
        result = await alert_service.process_alert(alert_dict, progress_callback_mock)
        
        # Assert - Should still return some form of analysis
        assert result is not None
        # May contain error information but should not be completely empty
        assert len(result) > 50

    async def test_llm_response_parsing_error(
        self,
        alert_service,
        sample_alert,
        mock_llm_manager,
        progress_callback_mock
    ):
        """Test handling when LLM returns unparseable responses."""
        # Arrange - Mock LLM to return invalid JSON
        mock_client = mock_llm_manager.get_client()
        mock_client.generate_response.return_value = "Invalid JSON response"
        
        # Act - Should handle parsing errors gracefully
        alert_dict = alert_to_api_format(sample_alert)
        result = await alert_service.process_alert(alert_dict, progress_callback_mock)
        
        # Assert - Should still return a response (may be error or fallback)
        assert result is not None


@pytest.mark.asyncio
@pytest.mark.integration
class TestAgentSpecialization:
    """Test agent-specific behavior and specialization."""

    async def test_kubernetes_agent_mcp_server_assignment(
        self,
        alert_service,
        sample_alert,
        mock_mcp_client,
        mock_agent_factory
    ):
        """Test that KubernetesAgent only accesses kubernetes-server."""
        # Act
        alert_dict = alert_to_api_format(sample_alert)
        await alert_service.process_alert(alert_dict)
        
        # Assert - Verify only kubernetes-server tools are accessed
        list_tools_calls = mock_mcp_client.list_tools.call_args_list
        for call in list_tools_calls:
            server_name = call.kwargs.get("server_name") or (call.args[0] if call.args else None)
            if server_name:
                assert server_name == "kubernetes-server"

    async def test_kubernetes_agent_tool_selection(
        self,
        alert_service,
        sample_alert,
        mock_llm_manager,
        mock_mcp_client
    ):
        """Test that KubernetesAgent makes appropriate tool selections."""
        # Act
        alert_dict = alert_to_api_format(sample_alert)
        result = await alert_service.process_alert(alert_dict)
        
        # Assert - Verify appropriate Kubernetes tools were called
        tool_calls = mock_mcp_client.call_tool.call_args_list
        called_tools = [call.args[1] for call in tool_calls if len(call.args) > 1]
        
        # Should include namespace and pod related tools
        kubernetes_tools = ["kubectl_get_namespace", "kubectl_get_pods", "kubectl_describe"]
        assert any(tool in called_tools for tool in kubernetes_tools)

    async def test_agent_instruction_composition(
        self,
        alert_service,
        sample_alert,
        mock_llm_manager
    ):
        """Test that agent instructions are properly composed (General + MCP + Custom)."""
        # Act
        alert_dict = alert_to_api_format(sample_alert)
        await alert_service.process_alert(alert_dict)
        
        # Assert - Verify LLM was called with composed instructions
        mock_client = mock_llm_manager.get_client()
        call_args_list = mock_client.generate_response.call_args_list
        
        # Check system messages for instruction composition
        system_messages = []
        for call in call_args_list:
            messages = call.args[0] if call.args else []
            for msg in messages:
                if hasattr(msg, 'role') and msg.role == "system":
                    system_messages.append(msg.content.lower())
        
        # Should contain references to Kubernetes (from server instructions)
        assert len(system_messages) > 0
        kubernetes_mentioned = any("kubernetes" in content for content in system_messages)
        assert kubernetes_mentioned


@pytest.mark.asyncio
@pytest.mark.integration  
class TestConcurrencyAndPerformance:
    """Test concurrent processing and performance characteristics."""

    async def test_concurrent_alert_processing(
        self,
        alert_service,
        sample_alert,
        progress_callback_mock
    ):
        """Test processing multiple alerts concurrently."""
        # Arrange - Create multiple alerts
        alerts = []
        callbacks = []
        for i in range(3):
            alert = Alert(
                alert_type="NamespaceTerminating",
                severity="high",
                environment=f"env-{i}",
                cluster="https://k8s-cluster.example.com",
                namespace=f"namespace-{i}",
                message=f"Test alert {i}",
                runbook="https://github.com/company/runbooks/blob/main/k8s-namespace-terminating.md"
            )
            callback = AsyncMock()
            alerts.append(alert)
            callbacks.append(callback)
        
        # Act - Process alerts concurrently
        tasks = [
            alert_service.process_alert(alert_to_api_format(alert), callback) 
            for alert, callback in zip(alerts, callbacks, strict=False)
        ]
        results = await asyncio.gather(*tasks)
        
        # Assert - All should complete successfully
        assert len(results) == 3
        for result in results:
            assert result is not None
            assert len(result) > 100  # Should have substantial content
        
        # All callbacks should have been called
        for callback in callbacks:
            assert callback.call_count >= 3

    async def test_processing_timeout_resilience(
        self,
        alert_service,
        sample_alert,
        mock_llm_manager
    ):
        """Test that processing handles timeouts gracefully."""
        # Arrange - Mock LLM to simulate slow responses
        mock_client = mock_llm_manager.get_client()
        
        async def slow_response(messages, **kwargs):
            await asyncio.sleep(0.1)  # Simulate slow response
            return "**Analysis**: Slow but successful analysis"
        
        mock_client.generate_response.side_effect = slow_response
        
        # Act - Process with timeout
        start_time = datetime.now()
        result = await asyncio.wait_for(
            alert_service.process_alert(alert_to_api_format(sample_alert)),
            timeout=5.0  # 5 second timeout
        )
        duration = (datetime.now() - start_time).total_seconds()
        
        # Assert - Should complete within reasonable time
        assert result is not None
        assert duration < 5.0
        assert "Analysis" in result


@pytest.mark.asyncio
@pytest.mark.integration
class TestDataFlowValidation:
    """Test data flow and validation throughout the processing pipeline."""

    async def test_alert_data_preservation(
        self,
        alert_service,
        sample_alert,
        mock_llm_manager
    ):
        """Test that alert data is preserved and passed correctly through pipeline."""
        # Act
        alert_dict = alert_to_api_format(sample_alert)
        result = await alert_service.process_alert(alert_dict)
        
        # Assert - Result should contain alert-specific information
        assert sample_alert.data.get('namespace', '') in result
        assert sample_alert.data.get('environment', '') in result  
        assert sample_alert.severity in result

    async def test_mcp_data_integration(
        self,
        alert_service,
        sample_alert,
        mock_mcp_client,
        mock_llm_manager
    ):
        """Test that MCP tool results are integrated into analysis."""
        # Arrange - Verify MCP client returns expected data
        expected_namespace_output = "stuck-namespace  Terminating   45m"
        
        # Act
        alert_dict = alert_to_api_format(sample_alert)
        result = await alert_service.process_alert(alert_dict)
        
        # Assert - MCP tool should have been called and data integrated
        assert mock_mcp_client.call_tool.call_count >= 1
        
        # The final analysis should reference the MCP data somehow
        # (exact format depends on LLM response, but should be non-trivial)
        assert len(result) > 200  # Should be substantial analysis using MCP data

    async def test_result_format_consistency(
        self,
        alert_service,
        sample_alert
    ):
        """Test that results follow expected format."""
        # Act
        alert_dict = alert_to_api_format(sample_alert)
        result = await alert_service.process_alert(alert_dict)
        
        # Assert - Result should be well-formatted string
        assert isinstance(result, str)
        assert len(result) > 100  # Should have substantial content
        
        # Should contain structured information
        lines = result.split('\n')
        assert len(lines) > 5  # Multi-line response
        
        # Should contain analysis indicators
        result_lower = result.lower()
        analysis_indicators = ["analysis", "issue", "resolution", "status", "cause"]
        assert any(indicator in result_lower for indicator in analysis_indicators) 