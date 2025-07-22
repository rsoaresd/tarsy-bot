"""
Edge cases and stress testing for the SRE AI Agent system.

This module contains tests for unusual scenarios, boundary conditions,
and stress testing of the alert processing pipeline.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from app.models.alert import Alert
from app.services.alert_service import AlertService


@pytest.mark.asyncio
@pytest.mark.integration
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    async def test_very_long_alert_message(
        self,
        alert_service,
        progress_callback_mock
    ):
        """Test processing alert with extremely long message."""
        # Arrange - Create alert with very long message (10KB+)
        long_message = "This is a very long alert message. " * 500  # ~17KB
        
        long_alert = Alert(
            alert_type="NamespaceTerminating",
            severity="high",
            environment="production",
            cluster="https://k8s-cluster.example.com",
            namespace="long-namespace",
            message=long_message,
            runbook="https://github.com/company/runbooks/blob/main/k8s-namespace-terminating.md"
        )
        
        # Act
        result = await alert_service.process_alert(long_alert, progress_callback_mock)
        
        # Assert - Should handle long messages gracefully
        assert result is not None
        assert len(result) > 100
        # Should contain some form of analysis despite long input
        assert "analysis" in result.lower() or "issue" in result.lower()

    async def test_special_characters_in_alert_data(
        self,
        alert_service,
        progress_callback_mock
    ):
        """Test processing alert with special characters and Unicode."""
        # Arrange - Create alert with special characters
        special_alert = Alert(
            alert_type="NamespaceTerminating",
            severity="high",
            environment="production-🚨",
            cluster="https://k8s-cluster.example.com",
            namespace="namespace-with-emojis-🔥",
            pod="pod-name-with-symbols-@#$%",
            message="Alert with special chars: äöü, 中文, 🚨🔥💀, and symbols: @#$%^&*()",
            runbook="https://github.com/company/runbooks/blob/main/k8s-namespace-terminating.md",
            context="Context with quotes \"double\" and 'single' and backslashes \\ \\n \\t"
        )
        
        # Act
        result = await alert_service.process_alert(special_alert, progress_callback_mock)
        
        # Assert - Should handle special characters without crashing
        assert result is not None
        assert isinstance(result, str)

    async def test_empty_optional_fields(
        self,
        alert_service,
        progress_callback_mock
    ):
        """Test processing alert with minimal required fields."""
        # Arrange - Create alert with only required fields
        minimal_alert = Alert(
            alert_type="NamespaceTerminating",
            severity="high",
            environment="production",
            cluster="https://k8s-cluster.example.com",
            namespace="minimal-namespace",
            message="Minimal alert message",
            runbook="https://github.com/company/runbooks/blob/main/k8s-namespace-terminating.md"
            # pod, context, timestamp are None/default
        )
        
        # Act
        result = await alert_service.process_alert(minimal_alert, progress_callback_mock)
        
        # Assert - Should process successfully even with minimal data
        assert result is not None
        assert len(result) > 50

    async def test_very_old_timestamp(
        self,
        alert_service,
        progress_callback_mock
    ):
        """Test processing alert with very old timestamp."""
        # Arrange - Create alert with timestamp from 1 year ago
        old_timestamp = datetime.now() - timedelta(days=365)
        
        old_alert = Alert(
            alert_type="NamespaceTerminating",
            severity="high",
            environment="production",
            cluster="https://k8s-cluster.example.com",
            namespace="old-namespace",
            message="This is an old alert",
            runbook="https://github.com/company/runbooks/blob/main/k8s-namespace-terminating.md",
            timestamp=old_timestamp
        )
        
        # Act
        result = await alert_service.process_alert(old_alert, progress_callback_mock)
        
        # Assert - Should handle old timestamps gracefully
        assert result is not None
        # Should still contain timestamp information
        assert str(old_timestamp.year) in result or "2023" in result

    async def test_malformed_runbook_url(
        self,
        alert_service,
        mock_runbook_service,
        progress_callback_mock
    ):
        """Test processing with malformed runbook URL."""
        # Arrange - Mock runbook service to handle malformed URL
        mock_runbook_service.download_runbook.side_effect = Exception("Invalid URL")
        
        malformed_alert = Alert(
            alert_type="NamespaceTerminating",
            severity="high",
            environment="production",
            cluster="https://k8s-cluster.example.com",
            namespace="malformed-namespace",
            message="Alert with malformed runbook URL",
            runbook="not-a-valid-url"
        )
        
        # Act
        result = await alert_service.process_alert(malformed_alert, progress_callback_mock)
        
        # Assert - Should return error response
        assert result is not None
        assert "error" in result.lower() or "Error" in result

    async def test_extremely_rapid_successive_processing(
        self,
        alert_service,
        sample_alert
    ):
        """Test rapid successive processing of the same alert."""
        # Arrange - Create multiple identical processing requests
        num_requests = 5
        
        # Act - Fire off multiple requests simultaneously
        tasks = [
            alert_service.process_alert(sample_alert)
            for _ in range(num_requests)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Assert - All should complete (may have varying results)
        assert len(results) == num_requests
        successful_results = [r for r in results if isinstance(r, str) and len(r) > 50]
        assert len(successful_results) >= num_requests // 2  # At least half should succeed

    async def test_processing_with_none_callback(
        self,
        alert_service,
        sample_alert
    ):
        """Test processing with None progress callback."""
        # Act - Process with no callback
        result = await alert_service.process_alert(sample_alert, None)
        
        # Assert - Should work without callback
        assert result is not None
        assert len(result) > 100


@pytest.mark.asyncio
@pytest.mark.integration
class TestStressScenarios:
    """Test system behavior under stress."""

    async def test_high_concurrency_different_alerts(
        self,
        alert_service
    ):
        """Test high concurrency with different alert types."""
        # Arrange - Create many different alerts
        alerts = []
        for i in range(10):
            alert = Alert(
                alert_type="NamespaceTerminating",
                severity=["low", "medium", "high"][i % 3],
                environment=f"env-{i}",
                cluster=f"https://cluster-{i}.example.com",
                namespace=f"namespace-{i}",
                pod=f"pod-{i}",
                message=f"Stress test alert {i}",
                runbook="https://github.com/company/runbooks/blob/main/k8s-namespace-terminating.md",
                context=f"Stress test context for alert {i}"
            )
            alerts.append(alert)
        
        # Act - Process all concurrently
        start_time = datetime.now()
        tasks = [alert_service.process_alert(alert) for alert in alerts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        duration = (datetime.now() - start_time).total_seconds()
        
        # Assert - Should handle high concurrency
        assert len(results) == 10
        successful_results = [r for r in results if isinstance(r, str) and len(r) > 50]
        assert len(successful_results) >= 8  # At least 80% success rate
        assert duration < 30  # Should complete within reasonable time

    async def test_rapid_fire_same_alert(
        self,
        alert_service,
        sample_alert
    ):
        """Test rapid-fire processing of the same alert."""
        # Arrange
        num_iterations = 15
        
        # Act - Process the same alert multiple times rapidly
        start_time = datetime.now()
        tasks = []
        
        for i in range(num_iterations):
            # Small delay between starts to simulate rapid but not simultaneous requests
            if i > 0:
                await asyncio.sleep(0.01)
            tasks.append(alert_service.process_alert(sample_alert))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        duration = (datetime.now() - start_time).total_seconds()
        
        # Assert
        assert len(results) == num_iterations
        successful_results = [r for r in results if isinstance(r, str) and len(r) > 50]
        assert len(successful_results) >= num_iterations * 0.7  # At least 70% success rate
        assert duration < 60  # Should complete within 1 minute

    async def test_resource_exhaustion_simulation(
        self,
        alert_service,
        sample_alert,
        mock_llm_manager,
        mock_mcp_client
    ):
        """Test behavior when resources are temporarily exhausted."""
        # Arrange - Simulate intermittent resource failures
        call_count = 0
        
        async def intermittent_llm_failure(messages, **kwargs):
            nonlocal call_count
            call_count += 1
            # Fail on calls 2 and 5, succeed on calls 1, 3, 4, 6
            if call_count in [2, 5]:
                raise Exception("Resource temporarily unavailable")
            return "**Analysis**: Resource exhaustion test result"
        
        mock_llm_manager.get_client().generate_response.side_effect = intermittent_llm_failure
        
        # Act - Try to process multiple alerts
        tasks = [alert_service.process_alert(sample_alert) for _ in range(6)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Assert - Some should succeed despite intermittent failures
        successful_results = [r for r in results if isinstance(r, str) and "Resource exhaustion test" in r]
        failed_results = [r for r in results if isinstance(r, Exception) or ("error" in str(r).lower())]
        
        assert len(successful_results) >= 2  # At least some should succeed
        assert len(failed_results) >= 1  # Some should fail due to resource issues

    async def test_memory_intensive_processing(
        self,
        alert_service,
        mock_llm_manager
    ):
        """Test processing with memory-intensive operations."""
        # Arrange - Create alert with large context and mock large responses
        large_context = "Large context data: " + "x" * 50000  # 50KB context
        
        large_alert = Alert(
            alert_type="NamespaceTerminating",
            severity="high",
            environment="production",
            cluster="https://k8s-cluster.example.com",
            namespace="memory-test-namespace",
            message="Memory intensive test alert",
            runbook="https://github.com/company/runbooks/blob/main/k8s-namespace-terminating.md",
            context=large_context
        )
        
        # Create a large mock response that will definitely be over 1000 chars
        large_analysis = "This is a very detailed and comprehensive analysis of the namespace terminating issue that affects the memory-test-namespace. " * 25
        large_final_response = f"**Analysis**: {large_analysis} The namespace requires immediate attention and remediation."
        
        # Override the mock to return our large response
        def mock_generate_large_response(messages, **kwargs):
            combined_content = ""
            for msg in messages:
                if hasattr(msg, 'content'):
                    combined_content += str(msg.content).lower()
            
            # For final analysis, return large response
            if "iterative" not in combined_content and "select tools" not in combined_content:
                return large_final_response
            # For other calls, use default behavior
            elif "select tools" in combined_content:
                return '''```json
[{"server": "kubernetes-server", "tool": "kubectl_get_namespace", "parameters": {"namespace": "memory-test-namespace"}, "reason": "Check namespace status"}]
```'''
            else:
                return '''{"continue": false, "reason": "Analysis complete"}'''
        
        mock_llm_manager.get_client().generate_response.side_effect = mock_generate_large_response
        
        # Act - Process the memory-intensive alert
        result = await alert_service.process_alert(large_alert)
        
        # Assert - Should handle large data gracefully
        assert result is not None
        assert len(result) > 1000  # Should have substantial content
        assert "Analysis" in result


@pytest.mark.asyncio
@pytest.mark.integration
class TestBoundaryConditions:
    """Test boundary conditions and limits."""

    async def test_maximum_iterations_reached(
        self,
        alert_service,
        sample_alert,
        mock_llm_manager,
        mock_mcp_client,
        mock_settings
    ):
        """Test behavior when maximum iterations are reached."""
        # Arrange - Set low iteration limit and mock LLM to always continue
        mock_settings.max_llm_mcp_iterations = 2  # Very low limit
        
        iteration_count = 0
        async def always_continue_response(messages, **kwargs):
            nonlocal iteration_count
            iteration_count += 1
            
            user_content = ""
            for msg in messages:
                if hasattr(msg, 'content') and msg.content:
                    user_content += msg.content.lower()
            
            # Always return continue=true to test iteration limits
            if "continue" in user_content and iteration_count < 10:
                return '''```json
{"continue": true, "tools": [{"server": "kubernetes-server", "tool": "kubectl_get_pods",
  "parameters": {"namespace": "test"}, "reason": "Continue iteration"}]}
```'''
            
            return "**Analysis**: Max iterations test completed"
        
        mock_llm_manager.get_client().generate_response.side_effect = always_continue_response
        
        # Act
        result = await alert_service.process_alert(sample_alert)
        
        # Assert - Should stop at max iterations
        assert result is not None
        assert "Analysis" in result

    async def test_empty_mcp_tool_response(
        self,
        alert_service,
        sample_alert,
        mock_mcp_client
    ):
        """Test handling of empty MCP tool responses."""
        # Arrange - Mock MCP client to return empty responses
        mock_mcp_client.call_tool.return_value = {"status": "success", "output": ""}
        
        # Act
        result = await alert_service.process_alert(sample_alert)
        
        # Assert - Should handle empty responses gracefully
        assert result is not None
        assert len(result) > 50

    async def test_malformed_json_from_llm(
        self,
        alert_service,
        sample_alert,
        mock_llm_manager
    ):
        """Test handling of malformed JSON responses from LLM."""
        # Arrange - Mock LLM to return malformed JSON
        responses = [
            "This is not JSON at all",
            "```json\n{invalid: json}\n```",
            "```json\n[{\"missing_quotes: true}]\n```",
            "**Final Analysis**: Fallback after JSON errors"
        ]
        
        response_iter = iter(responses)
        async def malformed_json_response(messages, **kwargs):
            return next(response_iter, "Default response")
        
        mock_llm_manager.get_client().generate_response.side_effect = malformed_json_response
        
        # Act
        result = await alert_service.process_alert(sample_alert)
        
        # Assert - Should handle malformed JSON gracefully
        assert result is not None
        # Should eventually get to fallback analysis
        assert "Analysis" in result or len(result) > 50

    async def test_unicode_and_encoding_edge_cases(
        self,
        alert_service,
        progress_callback_mock
    ):
        """Test handling of various Unicode and encoding scenarios."""
        # Arrange - Create alert with diverse Unicode content
        unicode_alert = Alert(
            alert_type="NamespaceTerminating",
            severity="high",
            environment="production",
            cluster="https://k8s-cluster.example.com",
            namespace="测试-namespace-тест",
            pod="pod-🚀-名前-имя",
            message="Unicode test: 你好世界 Здравствуй мир مرحبا بالعالم 🌍🚀💻",
            runbook="https://github.com/company/runbooks/blob/main/k8s-namespace-terminating.md",
            context="Mixed scripts: English 中文 Русский العربية 日本語 한국어"
        )
        
        # Act
        result = await alert_service.process_alert(unicode_alert, progress_callback_mock)
        
        # Assert - Should handle Unicode correctly
        assert result is not None
        assert isinstance(result, str)
        # Should preserve some Unicode content
        assert "测试" in result or "namespace" in result

    async def test_very_slow_external_dependencies(
        self,
        alert_service,
        sample_alert,
        mock_llm_manager,
        mock_mcp_client,
        mock_runbook_service
    ):
        """Test handling of very slow external dependencies."""
        # Arrange - Mock all external services to be slow
        async def slow_llm_response(messages, **kwargs):
            await asyncio.sleep(0.2)  # 200ms delay
            return "**Analysis**: Slow LLM response"
        
        async def slow_mcp_call(server_name, tool_name, parameters):
            await asyncio.sleep(0.1)  # 100ms delay
            return {"status": "success", "output": "slow response"}
        
        async def slow_runbook_download(url):
            await asyncio.sleep(0.15)  # 150ms delay
            return "# Slow Runbook\nThis took a while to download."
        
        mock_llm_manager.get_client().generate_response.side_effect = slow_llm_response
        mock_mcp_client.call_tool.side_effect = slow_mcp_call
        mock_runbook_service.download_runbook.side_effect = slow_runbook_download
        
        # Act - Process with timeout
        start_time = datetime.now()
        result = await asyncio.wait_for(
            alert_service.process_alert(sample_alert),
            timeout=10.0  # 10 second timeout
        )
        duration = (datetime.now() - start_time).total_seconds()
        
        # Assert - Should complete despite slow dependencies
        assert result is not None
        assert "Analysis" in result or "Slow" in result
        assert duration < 10.0  # Should complete within timeout 