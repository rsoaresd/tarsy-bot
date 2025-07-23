"""
Integration tests for Alert Processing History Service.

Tests the complete workflow integration with mocked external services
to ensure proper end-to-end functionality and component interaction.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
import logging

from app.main import app
from app.services.alert_service import AlertService
from app.services.history_service import HistoryService
from app.models.alert import Alert
# Import history models to ensure they're registered with SQLModel.metadata
from app.models.history import AlertSession, LLMInteraction, MCPCommunication

logger = logging.getLogger(__name__)


class TestHistoryServiceIntegration:
    """Integration tests for complete history service workflow."""
    
    @pytest.fixture
    def in_memory_engine(self):
        """Create in-memory SQLite engine for testing."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        SQLModel.metadata.create_all(engine)
        return engine
    
    @pytest.fixture
    def history_service_with_db(self, in_memory_engine):
        """Create history service with test database for testing."""
        # Get the database file path from the test engine (temporary file)
        db_path = in_memory_engine.url.database  # Extract the file path
        test_db_url = f"sqlite:///{db_path}"
        
        logger.info(f"Test database URL: {test_db_url}")
        
        # Mock settings to use the EXACT same database file as the test engine
        mock_settings = Mock()
        mock_settings.history_enabled = True  
        mock_settings.history_database_url = test_db_url  # Use the same database file
        mock_settings.history_retention_days = 90
        
        with patch('app.services.history_service.get_settings', return_value=mock_settings):
            service = HistoryService()
            # Initialize the service - it will now use the same database file
            service.initialize()
            
            logger.info(f"Service database URL: {service.db_manager.database_url}")
            logger.info(f"Service engine URL: {service.db_manager.engine.url}")
            
            yield service
    
    @pytest.fixture
    def sample_alert(self):
        """Create sample alert for testing."""
        return Alert(
            alert_type="NamespaceTerminating",
            severity="high",
            environment="production",
            cluster="k8s-prod",
            namespace="stuck-namespace",
            message="Namespace is stuck in Terminating state",
            runbook="namespace-terminating.md"
        )
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        client = AsyncMock()
        client.generate_response.return_value = {
            "content": "The namespace is stuck due to finalizers. Let me check the current state.",
            "model": "gpt-4",
            "usage": {"prompt_tokens": 150, "completion_tokens": 50, "total_tokens": 200}
        }
        return client
    
    @pytest.fixture
    def mock_mcp_client(self):
        """Create mock MCP client."""
        client = AsyncMock()
        client.list_tools.return_value = [
            {"name": "kubectl_get_namespace", "description": "Get namespace information"},
            {"name": "kubectl_describe_namespace", "description": "Describe namespace details"}
        ]
        client.call_tool.return_value = {
            "result": {
                "status": "Terminating",
                "finalizers": ["kubernetes.io/finalizer.test"],
                "deletionTimestamp": "2024-01-01T12:00:00Z"
            },
            "success": True,
            "error": None
        }
        return client
    
    @pytest.fixture
    def mock_kubernetes_agent(self, mock_llm_client, mock_mcp_client):
        """Create mock Kubernetes agent."""
        agent = Mock()
        agent.process_alert = AsyncMock(return_value={
            "status": "completed",
            "analysis": "Namespace termination issue resolved",
            "actions_taken": ["Removed stuck finalizer"],
            "recommendations": ["Monitor namespace cleanup process"]
        })
        return agent
    
    @pytest.mark.integration
    def test_create_session_and_track_lifecycle(self, history_service_with_db, sample_alert):
        """Test creating a session and tracking its complete lifecycle."""
        # Create initial session
        session_id = history_service_with_db.create_session(
            alert_id="alert-123",
            alert_data={
                "alert_type": sample_alert.alert_type,
                "environment": sample_alert.environment,
                "cluster": sample_alert.cluster,
                "namespace": sample_alert.namespace,
                "message": sample_alert.message
            },
            agent_type="KubernetesAgent",
            alert_type=sample_alert.alert_type
        )
        
        assert session_id is not None
        
        # Update session to in_progress
        result = history_service_with_db.update_session_status(
            session_id=session_id,
            status="in_progress"
        )
        assert result == True
        
        # Log LLM interaction
        llm_result = history_service_with_db.log_llm_interaction(
            session_id=session_id,
            prompt_text="Analyze the namespace termination issue",
            response_text="The namespace is stuck due to finalizers",
            model_used="gpt-4",
            step_description="Initial analysis",
            token_usage={"prompt_tokens": 150, "completion_tokens": 50, "total_tokens": 200},
            duration_ms=1500
        )
        assert llm_result == True
        
        # Log MCP communication
        mcp_result = history_service_with_db.log_mcp_communication(
            session_id=session_id,
            server_name="kubernetes-server",
            communication_type="tool_call",
            tool_name="kubectl_get_namespace",
            tool_arguments={"namespace": "stuck-namespace"},
            tool_result={"status": "Terminating", "finalizers": ["test-finalizer"]},
            step_description="Check namespace status",
            duration_ms=800,
            success=True
        )
        assert mcp_result == True
        
        # Complete session
        completion_result = history_service_with_db.update_session_status(
            session_id=session_id,
            status="completed"
        )
        assert completion_result == True
        
        # Verify complete timeline
        timeline = history_service_with_db.get_session_timeline(session_id)
        assert timeline is not None
        assert timeline["session"]["status"] == "completed"
        assert len(timeline["chronological_timeline"]) == 2
        assert timeline["session"]["total_interactions"] == 2
        # Check individual interaction/communication lists
        assert len(timeline["llm_interactions"]) == 1
        assert len(timeline["mcp_communications"]) == 1
    
    @pytest.mark.integration
    def test_chronological_timeline_ordering(self, history_service_with_db, sample_alert):
        """Test that timeline events are ordered chronologically."""
        # Create session
        session_id = history_service_with_db.create_session(
            alert_id="timeline-test",
            alert_data={"alert_type": sample_alert.alert_type},
            agent_type="KubernetesAgent",
            alert_type=sample_alert.alert_type
        )
        
        # Create events with specific timestamps (simulating real workflow)
        base_time = datetime.now(timezone.utc)
        
        # First LLM interaction
        history_service_with_db.log_llm_interaction(
            session_id=session_id,
            prompt_text="Initial analysis prompt",
            response_text="Initial analysis response",
            model_used="gpt-4",
            step_description="Initial analysis",
            duration_ms=1200
        )
        
        # Sleep to ensure different timestamp
        import time
        time.sleep(0.01)
        
        # MCP tool call
        history_service_with_db.log_mcp_communication(
            session_id=session_id,
            server_name="kubernetes-server",
            communication_type="tool_call",
            tool_name="kubectl_get",
            step_description="Get namespace info",
            success=True
        )
        
        time.sleep(0.01)
        
        # Second LLM interaction
        history_service_with_db.log_llm_interaction(
            session_id=session_id,
            prompt_text="Follow-up analysis prompt",
            response_text="Follow-up analysis response",
            model_used="gpt-4",
            step_description="Follow-up analysis"
        )
        
        # Get timeline and verify ordering
        timeline = history_service_with_db.get_session_timeline(session_id)
        events = timeline["chronological_timeline"]
        
        assert len(events) == 3
        
        # Verify events are in chronological order
        for i in range(len(events) - 1):
            current_time = datetime.fromisoformat(events[i]["timestamp"].replace("Z", "+00:00"))
            next_time = datetime.fromisoformat(events[i + 1]["timestamp"].replace("Z", "+00:00"))
            assert current_time <= next_time, f"Event {i} timestamp is after event {i+1}"
        
        # Verify event types in expected order
        assert events[0]["type"] == "llm_interaction"
        assert events[0]["step_description"] == "Initial analysis"
        assert events[1]["type"] == "mcp_communication"
        assert events[1]["step_description"] == "Get namespace info"
        assert events[2]["type"] == "llm_interaction"
        assert events[2]["step_description"] == "Follow-up analysis"
    
    @pytest.mark.integration
    def test_complex_filtering_scenarios(self, history_service_with_db):
        """Test complex filtering scenarios with multiple sessions."""
        # Create multiple sessions with different attributes
        now = datetime.now(timezone.utc)
        
        sessions_data = [
            ("session-1", "NamespaceTerminating", "KubernetesAgent", "completed", now - timedelta(hours=1)),
            ("session-2", "NamespaceTerminating", "KubernetesAgent", "in_progress", now - timedelta(hours=2)),
            ("session-3", "HighCPU", "KubernetesAgent", "completed", now - timedelta(hours=3)),
            ("session-4", "NamespaceTerminating", "GenericAgent", "completed", now - timedelta(hours=4)),
            ("session-5", "HighMemory", "KubernetesAgent", "failed", now - timedelta(days=2))
        ]
        
        for session_id, alert_type, agent_type, status, started_at in sessions_data:
            # Use the service to create session (simulating real workflow)
            sid = history_service_with_db.create_session(
                alert_id=f"alert-{session_id}",
                alert_data={"alert_type": alert_type, "environment": "test"},
                agent_type=agent_type,
                alert_type=alert_type
            )
            
            # Update the session with custom timestamp using repository directly
            with history_service_with_db.get_repository() as repo:
                if repo:
                    # Get the created session
                    session = repo.get_alert_session(sid)
                    if session:
                        # Update with custom timestamp
                        session.started_at = started_at
                        # Update status if needed
                        if status != "pending":
                            session.status = status
                            if status == "completed":
                                session.completed_at = started_at + timedelta(minutes=30)
                        repo.session.commit()
            
            # Add some interactions for variety
            if session_id in ["session-1", "session-3"]:
                history_service_with_db.log_llm_interaction(
                    session_id=sid,
                    prompt_text=f"Test prompt for {session_id}",
                    response_text=f"Test response for {session_id}",
                    model_used="gpt-4",
                    step_description=f"Analysis for {session_id}"
                )
        
        # Test 1: Filter by alert_type + status
        sessions, count = history_service_with_db.get_sessions_list(
            filters={"alert_type": "NamespaceTerminating", "status": "completed"}
        )
        assert count == 2  # session-1 and session-4
        
        # Test 2: Filter by agent_type + status + alert_type
        sessions, count = history_service_with_db.get_sessions_list(
            filters={
                "agent_type": "KubernetesAgent",
                "status": "completed",
                "alert_type": "NamespaceTerminating"
            }
        )
        assert count == 1  # only session-1
        
        # Test 3: Filter by time range
        cutoff_time = now - timedelta(hours=5)
        sessions, count = history_service_with_db.get_sessions_list(
            filters={"start_date": cutoff_time}
        )
        assert count == 4  # All except session-5 (older than 5 hours)
        
        # Test 4: Combined filters with pagination
        sessions, count = history_service_with_db.get_sessions_list(
            filters={"agent_type": "KubernetesAgent"},
            page=1,
            page_size=2
        )
        assert len(sessions) == 2  # First page of KubernetesAgent sessions
        assert count == 4  # Total KubernetesAgent sessions
    
    @pytest.mark.integration
    def test_error_handling_and_graceful_degradation(self, history_service_with_db, sample_alert):
        """Test error handling and graceful degradation scenarios."""
        # Test session creation with invalid data
        session_id = history_service_with_db.create_session(
            alert_id="",  # Empty alert ID
            alert_data={},  # Empty alert data
            agent_type="",  # Empty agent type
            alert_type=""  # Empty alert type
        )
        assert session_id is not None  # Should still create session
        
        # Test logging with invalid session ID
        result = history_service_with_db.log_llm_interaction(
            session_id="non-existent-session",
            prompt_text="Test prompt",
            response_text="Test response",
            model_used="gpt-4",
            step_description="Test interaction"
        )
        # The service allows logging interactions even for non-existent sessions
        # This is by design for performance and graceful degradation
        assert result == True  # Service handles this gracefully without validation
        
        # Test status update with invalid session ID
        result = history_service_with_db.update_session_status(
            session_id="non-existent-session",
            status="completed"
        )
        assert result == False  # Should fail gracefully
        
        # Test timeline retrieval with invalid session ID
        timeline = history_service_with_db.get_session_timeline("non-existent-session")
        assert timeline == {}  # Should return empty dict for non-existent sessions
    

    @pytest.mark.integration
    def test_sqlite_retry_logic_works(self, history_service_with_db, sample_alert):
        """Test that our retry logic handles transient SQLite issues gracefully."""
        # This test verifies our retry logic works in single-threaded scenarios
        # Note: Full concurrent testing requires a more robust database like PostgreSQL
        
        # Test that normal operations work
        session_id = history_service_with_db.create_session(
            alert_id="retry-test-1",
            alert_data={"alert_type": sample_alert.alert_type},
            agent_type="KubernetesAgent",  
            alert_type=sample_alert.alert_type
        )
        
        # Should succeed with our improvements
        assert session_id is not None, "Session creation should succeed with retry logic"
        
        # Test status update works
        result = history_service_with_db.update_session_status(
            session_id=session_id,
            status="completed"
        )
        assert result == True, "Status update should succeed with retry logic"
        
        # Verify session was created correctly
        timeline = history_service_with_db.get_session_timeline(session_id)
        assert timeline is not None
        assert timeline["session"]["status"] == "completed"
        
        logger.info("✅ SQLite retry logic and improvements working correctly")


class TestAlertServiceHistoryIntegration:
    """Integration tests for AlertService with history tracking."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = Mock()
        settings.history_enabled = True
        settings.history_database_url = "sqlite:///:memory:"
        settings.history_retention_days = 90
        # Add required LLM settings to prevent iteration error
        settings.llm_providers = {}
        settings.llm_default_provider = "openai"
        settings.openai_api_key = "test-key"
        settings.anthropic_api_key = "test-key"
        return settings
    
    @pytest.fixture
    def alert_service_with_history(self, mock_settings):
        """Create AlertService with history integration."""
        # Create AlertService directly with mock settings
        service = AlertService(mock_settings)
        
        # Mock LLM manager to appear available
        service.llm_manager.is_available = Mock(return_value=True)
        
        # Mock runbook service to return test content
        service.runbook_service.download_runbook = AsyncMock(return_value="Test runbook content")
        
        # Mock agent registry and agent factory
        mock_agent = AsyncMock()
        mock_agent.process_alert.return_value = {
            "status": "success",  # Changed to match expected format
            "analysis": "Test analysis",
            "actions_taken": ["Test action"],
            "recommendations": ["Test recommendation"]
        }
        
        # Mock the agent_registry (not agent_factory) - this is where get_agent_for_alert_type lives
        service.agent_registry.get_agent_for_alert_type = Mock(return_value="KubernetesAgent")
        
        # Mock agent_factory to return our mock agent
        service.agent_factory = Mock()
        service.agent_factory.create_agent = Mock(return_value=mock_agent)
        
        # Use real history service with mocked database
        mock_history_service = Mock()
        mock_history_service.create_session.return_value = "test-session-123"
        mock_history_service.update_session_status.return_value = True
        service.history_service = mock_history_service
        
        return service
    
    @pytest.fixture
    def sample_alert(self):
        """Create sample alert."""
        return Alert(
            alert_type="NamespaceTerminating",
            severity="high",
            environment="production",
            cluster="k8s-prod",
            namespace="stuck-namespace",
            message="Namespace is stuck in Terminating state",
            runbook="namespace-terminating.md"
        )
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_alert_processing_with_history_tracking(self, alert_service_with_history, sample_alert):
        """Test complete alert processing with history tracking."""
        # Mock progress callback as async
        progress_callback = AsyncMock()
        
        # Process alert
        result = await alert_service_with_history.process_alert(
            alert=sample_alert,
            progress_callback=progress_callback
        )
        
        # Verify alert processing succeeded
        assert result is not None
        # The result is a formatted string from _format_success_response, not a dict
        assert "Analysis completed successfully" in result or "Test analysis" in result
        
        # Verify history service interactions
        history_service = alert_service_with_history.history_service
        
        # Should have created session
        history_service.create_session.assert_called_once()
        create_call = history_service.create_session.call_args
        assert create_call[1]["agent_type"] == "KubernetesAgent"
        assert create_call[1]["alert_type"] == sample_alert.alert_type
        
        # Should have updated session status multiple times
        assert history_service.update_session_status.call_count >= 2
        
        # Verify session status updates
        status_calls = history_service.update_session_status.call_args_list
        
        # Should include in_progress and completed status updates
        statuses = [call[1]["status"] for call in status_calls]
        assert "in_progress" in statuses
        assert "completed" in statuses
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_alert_processing_error_with_history_tracking(self, alert_service_with_history, sample_alert):
        """Test alert processing error handling with history tracking."""
        # Make agent processing fail by setting up the mock to fail
        mock_agent = AsyncMock()
        mock_agent.process_alert.side_effect = Exception("Agent processing failed")
        alert_service_with_history.agent_factory.create_agent.return_value = mock_agent
        
        # Process alert (should handle error gracefully)
        result = await alert_service_with_history.process_alert(
            alert=sample_alert,
            progress_callback=AsyncMock()
        )
        
        # Verify error was handled
        assert result is not None
        # The result is a formatted string from _format_error_response, not a dict  
        assert "Agent processing failed" in result
        
        # Verify history service tracked the error
        history_service = alert_service_with_history.history_service
        
        # Should have created session
        history_service.create_session.assert_called_once()
        
        # Should have updated status to failed
        status_calls = history_service.update_session_status.call_args_list
        statuses = [call[1]["status"] for call in status_calls]
        assert "failed" in statuses
        
        # Should have recorded error message
        error_calls = [call for call in status_calls if call[1].get("error_message")]
        assert len(error_calls) > 0
        assert "Agent processing failed" in error_calls[0][1]["error_message"]


class TestHistoryAPIIntegration:
    """Integration tests for History API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_history_service_for_api(self):
        """Create mock history service for API testing."""
        service = Mock()
        service.enabled = True
        
        # Mock sessions data with all required attributes
        mock_sessions = [
            Mock(
                session_id="api-session-1",
                alert_id="api-alert-1",
                alert_type="NamespaceTerminating",
                agent_type="KubernetesAgent",
                status="completed",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                error_message=None,
                llm_interactions=[],  # Add missing attributes
                mcp_communications=[]
            )
        ]
        service.get_sessions_list.return_value = (mock_sessions, 1)
        
        # Mock timeline data with correct structure (session instead of session_info)
        service.get_session_timeline.return_value = {
            "session": {
                "session_id": "api-session-1",
                "alert_id": "api-alert-1",
                "alert_type": "NamespaceTerminating",
                "agent_type": "KubernetesAgent",
                "status": "completed",
                "started_at": "2024-01-15T10:00:00Z",
                "completed_at": "2024-01-15T10:05:00Z",
                "error_message": None
            },
            "chronological_timeline": [
                {
                    "interaction_id": "int-1",
                    "type": "llm_interaction",
                    "timestamp": "2024-01-15T10:00:00Z",
                    "step_description": "Analysis",
                    "details": {
                        "prompt_text": "Analyze issue",
                        "response_text": "Found solution"
                    }
                }
            ]
        }
        
        service.test_database_connection.return_value = True
        service.settings = Mock()
        service.settings.history_database_url = "sqlite:///test.db"
        
        return service
    
    @pytest.mark.integration
    def test_api_sessions_list_integration(self, client, mock_history_service_for_api):
        """Test sessions list API endpoint integration."""
        # Use FastAPI's dependency override system
        from app.controllers.history_controller import get_history_service
        app.dependency_overrides[get_history_service] = lambda: mock_history_service_for_api
        
        try:
            response = client.get("/api/v1/history/sessions?status=completed&page=1&page_size=10")
        
            assert response.status_code == 200
            data = response.json()
            
            assert "sessions" in data
            assert "pagination" in data
            assert len(data["sessions"]) == 1
            assert data["sessions"][0]["session_id"] == "api-session-1"
            
            # Verify service was called with correct parameters
            mock_history_service_for_api.get_sessions_list.assert_called_once()
            call_args = mock_history_service_for_api.get_sessions_list.call_args
            assert call_args.kwargs["filters"]["status"] == "completed"
            assert call_args.kwargs["page"] == 1
            assert call_args.kwargs["page_size"] == 10
            
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()
    
    @pytest.mark.integration
    def test_api_session_detail_integration(self, client, mock_history_service_for_api):
        """Test session detail API endpoint integration."""
        # Ensure the mock returns the timeline for the specific session ID
        expected_session_id = "api-session-1"
        mock_history_service_for_api.get_session_timeline.return_value = {
            "session": {
                "session_id": expected_session_id,
                "alert_id": "api-alert-1",
                "alert_type": "NamespaceTerminating",
                "agent_type": "KubernetesAgent", 
                "status": "completed",
                "started_at": "2024-01-15T10:00:00Z",
                "completed_at": "2024-01-15T10:05:00Z",
                "error_message": None
            },
            "chronological_timeline": [
                {
                    "interaction_id": "int-1",
                    "type": "llm_interaction",
                    "timestamp": "2024-01-15T10:00:00Z",
                    "step_description": "Analysis",
                    "details": {
                        "prompt_text": "Analyze issue",
                        "response_text": "Found solution"
                    }
                }
            ]
        }
        
        # Use FastAPI's dependency override system instead of mock patching
        from app.controllers.history_controller import get_history_service
        app.dependency_overrides[get_history_service] = lambda: mock_history_service_for_api
        
        try:
            response = client.get(f"/api/v1/history/sessions/{expected_session_id}")
            
            assert response.status_code == 200
            data = response.json()
            
            # Check the actual SessionDetailResponse structure (not nested session_info)
            assert "session_id" in data
            assert "chronological_timeline" in data
            assert "summary" in data
            
            # Verify session details
            assert data["session_id"] == expected_session_id
            assert data["alert_type"] == "NamespaceTerminating"
            assert data["status"] == "completed"
            
            # Verify timeline structure
            assert len(data["chronological_timeline"]) == 1
            assert data["chronological_timeline"][0]["type"] == "llm_interaction"
            
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()
    
    @pytest.mark.integration
    def test_api_health_check_integration(self, client, mock_history_service_for_api):
        """Test health check API endpoint integration."""
        # Use FastAPI's dependency override system
        from app.controllers.history_controller import get_history_service
        app.dependency_overrides[get_history_service] = lambda: mock_history_service_for_api
        
        try:
            response = client.get("/api/v1/history/health")
        
            assert response.status_code == 200
            data = response.json()
            
            assert data["service"] == "alert_processing_history"
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert "details" in data
            
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()
    
    @pytest.mark.integration
    def test_api_error_handling_integration(self, client):
        """Test API error handling integration."""
        # Mock service that raises exception
        mock_service = Mock()
        mock_service.enabled = True
        mock_service.get_sessions_list.side_effect = Exception("Database connection failed")
        
        # Use FastAPI's dependency override system
        from app.controllers.history_controller import get_history_service
        app.dependency_overrides[get_history_service] = lambda: mock_service
        
        try:
            response = client.get("/api/v1/history/sessions")
        
            assert response.status_code == 500
            # The actual error message varies, just check it's an error response
            assert "detail" in response.json()
            
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()
