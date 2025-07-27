"""
Unit tests for DashboardUpdateService.
"""

from collections import deque
from dataclasses import asdict
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from tarsy.services.dashboard_update_service import (
    DashboardMetrics,
    DashboardUpdateService,
    SessionSummary,
)


class TestSessionSummary:
    """Test SessionSummary dataclass functionality."""
    
    @pytest.mark.unit
    def test_session_summary_creation(self):
        """Test SessionSummary creation with defaults."""
        summary = SessionSummary(session_id="session_123", status="active")
        
        assert summary.session_id == "session_123"
        assert summary.status == "active"
        assert summary.start_time is None  # Default is None
        assert summary.llm_interactions == 0
        assert summary.mcp_communications == 0
        assert summary.current_step is None  # Default is None
        assert summary.agent_type is None
        assert summary.last_activity is None  # Default is None
        assert summary.errors_count == 0
    
    @pytest.mark.unit
    def test_session_summary_with_custom_values(self):
        """Test SessionSummary creation with custom values."""
        start_time = datetime.now()
        summary = SessionSummary(
            session_id="session_456",
            status="processing",
            start_time=start_time,
            llm_interactions=5,
            mcp_communications=3,
            current_step="Analyzing logs",
            agent_type="kubernetes_agent",
            errors_count=1
        )
        
        assert summary.session_id == "session_456"
        assert summary.status == "processing"
        assert summary.start_time == start_time
        assert summary.llm_interactions == 5
        assert summary.mcp_communications == 3
        assert summary.current_step == "Analyzing logs"
        assert summary.agent_type == "kubernetes_agent"
        assert summary.errors_count == 1
    
    @pytest.mark.unit
    def test_session_summary_to_dict_conversion(self):
        """Test converting SessionSummary to dictionary."""
        summary = SessionSummary(
            session_id="session_789",
            status="completed",
            llm_interactions=10,
            mcp_communications=7
        )
        
        summary_dict = asdict(summary)
        
        assert summary_dict["session_id"] == "session_789"
        assert summary_dict["status"] == "completed"
        assert summary_dict["llm_interactions"] == 10
        assert summary_dict["mcp_communications"] == 7
        assert "start_time" in summary_dict
        assert "last_activity" in summary_dict


class TestDashboardMetrics:
    """Test DashboardMetrics dataclass functionality."""
    
    @pytest.mark.unit
    def test_dashboard_metrics_creation(self):
        """Test DashboardMetrics creation with defaults."""
        metrics = DashboardMetrics()
        
        assert metrics.active_sessions == 0
        assert metrics.completed_sessions == 0
        assert metrics.failed_sessions == 0
        assert metrics.total_interactions == 0
        assert metrics.avg_session_duration == 0.0
        assert metrics.error_rate == 0.0
        assert metrics.last_updated is None
    
    @pytest.mark.unit
    def test_dashboard_metrics_with_custom_values(self):
        """Test DashboardMetrics creation with custom values."""
        last_updated = datetime.now()
        metrics = DashboardMetrics(
            active_sessions=5,
            completed_sessions=80,
            failed_sessions=20,
            total_interactions=500,
            avg_session_duration=45.5,
            error_rate=15.2,
            last_updated=last_updated
        )
        
        assert metrics.active_sessions == 5
        assert metrics.completed_sessions == 80
        assert metrics.failed_sessions == 20
        assert metrics.total_interactions == 500
        assert metrics.avg_session_duration == 45.5
        assert metrics.error_rate == 15.2
        assert metrics.last_updated == last_updated
    
    @pytest.mark.unit
    def test_dashboard_metrics_to_dict_conversion(self):
        """Test converting DashboardMetrics to dictionary."""
        metrics = DashboardMetrics(
            active_sessions=3,
            completed_sessions=40,
            failed_sessions=10
        )
        
        metrics_dict = asdict(metrics)
        
        assert metrics_dict["active_sessions"] == 3
        assert metrics_dict["completed_sessions"] == 40
        assert metrics_dict["failed_sessions"] == 10
        assert "last_updated" in metrics_dict


class TestDashboardUpdateService:
    """Test DashboardUpdateService main functionality."""
    
    @pytest.fixture
    def mock_broadcaster(self):
        """Mock dashboard broadcaster."""
        broadcaster = AsyncMock()
        broadcaster.broadcast_dashboard_update = AsyncMock(return_value=3)
        broadcaster.broadcast_session_update = AsyncMock(return_value=2)
        broadcaster.broadcast_system_health = AsyncMock(return_value=1)
        return broadcaster
    
    @pytest.fixture
    def update_service(self, mock_broadcaster):
        """Create DashboardUpdateService instance."""
        return DashboardUpdateService(mock_broadcaster)
    
    @pytest.mark.unit
    def test_initialization(self, update_service, mock_broadcaster):
        """Test DashboardUpdateService initialization."""
        assert update_service.broadcaster == mock_broadcaster
        assert isinstance(update_service.active_sessions, dict)
        assert isinstance(update_service.session_history, deque)
        assert isinstance(update_service.pending_session_updates, dict)
        assert update_service.running is False
        assert update_service.batch_timeout == 2.0
        assert update_service.max_updates_per_session == 10
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_start_stop_service(self, update_service):
        """Test starting and stopping the service."""
        assert update_service.running is False
        
        # Start service
        await update_service.start()
        assert update_service.running is True
        assert update_service.batch_processor_task is not None
        
        # Stop service
        await update_service.stop()
        assert update_service.running is False
    
    @pytest.mark.unit
    def test_get_session_summary(self, update_service):
        """Test getting session summary."""
        session_id = "session_summary_test"
        
        # Create a session
        summary = SessionSummary(
            session_id=session_id,
            status="processing",
            llm_interactions=5,
            mcp_communications=3
        )
        update_service.active_sessions[session_id] = summary
        
        # Get summary
        retrieved_summary = update_service.get_session_summary(session_id)
        
        assert retrieved_summary is not None
        assert retrieved_summary.session_id == session_id
        assert retrieved_summary.status == "processing"
        assert retrieved_summary.llm_interactions == 5
        assert retrieved_summary.mcp_communications == 3
    
    @pytest.mark.unit
    def test_get_session_summary_nonexistent(self, update_service):
        """Test getting summary for nonexistent session."""
        summary = update_service.get_session_summary("nonexistent_session")
        assert summary is None
    
    @pytest.mark.unit
    def test_get_all_active_sessions(self, update_service):
        """Test getting all active sessions."""
        # Create multiple sessions
        session_ids = ["session_1", "session_2", "session_3"]
        for session_id in session_ids:
            summary = SessionSummary(session_id=session_id, status="active")
            update_service.active_sessions[session_id] = summary
        
        active_sessions = update_service.get_all_active_sessions()
        
        assert len(active_sessions) == 3
        assert all(session.status == "active" for session in active_sessions)
        assert set(session.session_id for session in active_sessions) == set(session_ids)
    
    @pytest.mark.unit
    def test_get_dashboard_metrics(self, update_service):
        """Test getting current dashboard metrics."""
        # Set up test metrics
        test_metrics = DashboardMetrics(
            active_sessions=5,
            completed_sessions=100,
            failed_sessions=10,
            total_interactions=500
        )
        update_service.metrics = test_metrics
        
        metrics = update_service.get_dashboard_metrics()
        
        assert metrics.active_sessions == 5
        assert metrics.completed_sessions == 100
        assert metrics.failed_sessions == 10
        assert metrics.total_interactions == 500


class TestLLMInteractionProcessing:
    """Test LLM interaction processing with correct data formats."""
    
    @pytest.fixture
    def mock_broadcaster(self):
        """Mock broadcaster."""
        broadcaster = AsyncMock()
        broadcaster.broadcast_dashboard_update = AsyncMock(return_value=3)
        broadcaster.broadcast_session_update = AsyncMock(return_value=2)
        return broadcaster
    
    @pytest.fixture
    def update_service(self, mock_broadcaster):
        """Create service instance."""
        return DashboardUpdateService(mock_broadcaster)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_process_llm_interaction_success(self, update_service, mock_broadcaster):
        """Test processing successful LLM interaction with production data format."""
        session_id = "llm_session_123"
        interaction_data = {
            'interaction_type': 'llm',
            'session_id': session_id,
            'step_description': 'LLM analysis using gpt-4',
            'model_used': 'gpt-4',
            'success': True,
            'duration_ms': 1500,
            'timestamp': datetime.now().isoformat(),
            'tool_calls_present': True,
            'error_message': None
        }
        
        # Test batched processing (default)
        sent_count = await update_service.process_llm_interaction(session_id, interaction_data)
        assert sent_count == 0  # Batched, not sent immediately
        
        # Verify session was created/updated
        assert session_id in update_service.active_sessions
        session = update_service.active_sessions[session_id]
        assert session.llm_interactions == 1
        assert session.interactions_count == 1
        assert session.errors_count == 0
        assert session.current_step == 'LLM analysis using gpt-4'
        assert session.status == "active"
        
        # Verify update was added to batch
        assert session_id in update_service.pending_session_updates
        assert len(update_service.pending_session_updates[session_id]) == 1
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_process_llm_interaction_error(self, update_service, mock_broadcaster):
        """Test processing LLM interaction error."""
        session_id = "llm_error_session"
        interaction_data = {
            'interaction_type': 'llm',
            'session_id': session_id,
            'step_description': 'LLM analysis failed',
            'model_used': 'gpt-4',
            'success': False,
            'duration_ms': 500,
            'timestamp': datetime.now().isoformat(),
            'tool_calls_present': False,
            'error_message': 'Connection timeout to LLM service'
        }
        
        sent_count = await update_service.process_llm_interaction(session_id, interaction_data)
        
        # Verify session error tracking
        session = update_service.active_sessions[session_id]
        assert session.errors_count == 1
        assert session.current_step == "LLM analysis failed"  # Uses step_description from data
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_process_llm_interaction_broadcast_immediately(self, update_service, mock_broadcaster):
        """Test immediate broadcasting of LLM interaction."""
        session_id = "llm_immediate_session"
        interaction_data = {
            'interaction_type': 'llm',
            'session_id': session_id,
            'step_description': 'Critical LLM analysis',
            'model_used': 'gpt-4',
            'success': True,
            'duration_ms': 1200,
            'timestamp': datetime.now().isoformat(),
            'tool_calls_present': False,
            'error_message': None
        }
        
        # Test immediate broadcasting
        sent_count = await update_service.process_llm_interaction(
            session_id, interaction_data, broadcast_immediately=True
        )
        
        assert sent_count == 2  # Broadcaster returned 2 from session-specific broadcast
        mock_broadcaster.broadcast_session_update.assert_called_once()
        mock_broadcaster.broadcast_dashboard_update.assert_not_called()
        
        # Verify update was NOT added to batch
        assert session_id not in update_service.pending_session_updates


class TestMCPCommunicationProcessing:
    """Test MCP communication processing with correct data formats."""
    
    @pytest.fixture
    def mock_broadcaster(self):
        """Mock broadcaster."""
        broadcaster = AsyncMock()
        broadcaster.broadcast_dashboard_update = AsyncMock(return_value=2)
        return broadcaster
    
    @pytest.fixture
    def update_service(self, mock_broadcaster):
        """Create service instance."""
        return DashboardUpdateService(mock_broadcaster)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_process_mcp_communication_success(self, update_service, mock_broadcaster):
        """Test processing successful MCP communication with production data format."""
        session_id = "mcp_session_456"
        communication_data = {
            'interaction_type': 'mcp',
            'session_id': session_id,
            'step_description': 'Execute kubectl via kubernetes server',
            'server_name': 'kubernetes',
            'tool_name': 'kubectl',
            'success': True,
            'duration_ms': 800,
            'timestamp': datetime.now().isoformat(),
            'error_message': None
        }
        
        # Test batched processing (default)
        sent_count = await update_service.process_mcp_communication(session_id, communication_data)
        assert sent_count == 0  # Batched, not sent immediately
        
        # Verify session was created/updated
        session = update_service.active_sessions[session_id]
        assert session.mcp_communications == 1
        assert session.interactions_count == 1
        assert session.errors_count == 0
        assert session.current_step == "Execute kubectl via kubernetes server"  # Uses step_description from data
        assert session.status == "active"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_process_mcp_communication_error(self, update_service, mock_broadcaster):
        """Test processing MCP communication error."""
        session_id = "mcp_error_session"
        communication_data = {
            'interaction_type': 'mcp',
            'session_id': session_id,
            'step_description': 'kubectl execution failed',
            'server_name': 'kubernetes',
            'tool_name': 'kubectl',
            'success': False,
            'duration_ms': 200,
            'timestamp': datetime.now().isoformat(),
            'error_message': 'Tool execution failed: kubectl not found'
        }
        
        sent_count = await update_service.process_mcp_communication(session_id, communication_data)
        
        # Verify session error tracking
        session = update_service.active_sessions[session_id]
        assert session.errors_count == 1
        assert session.current_step == "kubectl execution failed"  # Uses step_description from data
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_process_mcp_communication_with_step_description(self, update_service, mock_broadcaster):
        """Test MCP communication with explicit step description."""
        session_id = "mcp_step_session"
        communication_data = {
            'interaction_type': 'mcp',
            'session_id': session_id,
            'step_description': 'Custom step description from hook',
            'server_name': 'file_operations',
            'tool_name': 'read_file',
            'success': True,
            'duration_ms': 150,
            'timestamp': datetime.now().isoformat(),
            'error_message': None
        }
        
        await update_service.process_mcp_communication(session_id, communication_data)
        
        # Verify custom step description is used
        session = update_service.active_sessions[session_id]
        assert session.current_step == "Custom step description from hook"


class TestSessionStatusManagement:
    """Test session status change processing."""
    
    @pytest.fixture
    def mock_broadcaster(self):
        """Mock broadcaster."""
        broadcaster = AsyncMock()
        broadcaster.broadcast_dashboard_update = AsyncMock(return_value=3)
        broadcaster.broadcast_session_update = AsyncMock(return_value=2)
        return broadcaster
    
    @pytest.fixture
    def update_service(self, mock_broadcaster):
        """Create service instance."""
        return DashboardUpdateService(mock_broadcaster)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_process_session_status_change_new_session(self, update_service, mock_broadcaster):
        """Test creating new session with status change."""
        session_id = "new_status_session"
        status = "processing"
        details = {
            "agent_type": "kubernetes_agent",
            "current_step": "Analyzing error logs",
            "progress_percentage": 25
        }
        
        sent_count = await update_service.process_session_status_change(session_id, status, details)
        
        assert sent_count == 5  # Broadcaster returned 3 + 2 = 5 (dual-channel broadcasting)
        mock_broadcaster.broadcast_dashboard_update.assert_called_once()
        mock_broadcaster.broadcast_session_update.assert_called_once()
        
        # Verify session was created
        assert session_id in update_service.active_sessions
        session = update_service.active_sessions[session_id]
        assert session.status == status
        assert session.agent_type == "kubernetes_agent"
        assert session.current_step == "Analyzing error logs"
        assert session.progress_percentage == 25
        assert session.start_time is not None
        assert session.last_activity is not None
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_process_session_status_change_existing_session(self, update_service, mock_broadcaster):
        """Test updating existing session status."""
        session_id = "existing_session"
        
        # Create existing session
        original_session = SessionSummary(
            session_id=session_id,
            status="active",
            agent_type="log_analyzer",
            start_time=datetime.now() - timedelta(minutes=5)
        )
        update_service.active_sessions[session_id] = original_session
        
        # Update status
        new_status = "completed"
        details = {"current_step": "Analysis complete", "progress_percentage": 100}
        
        sent_count = await update_service.process_session_status_change(session_id, new_status, details)
        
        # Verify session was updated but start_time preserved
        session = update_service.active_sessions.get(session_id)  # May be None if archived
        if session:  # Session not yet archived (test timing)
            assert session.status == new_status
            assert session.agent_type == "log_analyzer"  # Preserved
            assert session.current_step == "Analysis complete"
            assert session.progress_percentage == 100
            assert session.start_time == original_session.start_time  # Preserved
        
        # Verify session was archived (moved to history)
        if new_status in ["completed", "error", "timeout"]:
            # Session should be moved to history
            assert len(update_service.session_history) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_session_archiving_on_completion(self, update_service, mock_broadcaster):
        """Test session archiving when status indicates completion."""
        session_id = "archiving_session"
        
        # Create active session
        update_service.active_sessions[session_id] = SessionSummary(
            session_id=session_id,
            status="processing",
            llm_interactions=5,
            mcp_communications=3
        )
        
        # Complete the session
        await update_service.process_session_status_change(session_id, "completed")
        
        # Verify session was archived
        assert session_id not in update_service.active_sessions
        assert len(update_service.session_history) == 1
        archived_session = update_service.session_history[0]
        assert archived_session.session_id == session_id
        assert archived_session.status == "completed"
        assert archived_session.llm_interactions == 5
        assert archived_session.mcp_communications == 3


class TestSystemMetricsBroadcasting:
    """Test system metrics broadcasting functionality."""
    
    @pytest.fixture
    def mock_broadcaster(self):
        """Mock broadcaster."""
        broadcaster = AsyncMock()
        broadcaster.broadcast_dashboard_update = AsyncMock(return_value=7)
        return broadcaster
    
    @pytest.fixture
    def update_service(self, mock_broadcaster):
        """Create service instance with test data."""
        service = DashboardUpdateService(mock_broadcaster)
        
        # Set up test sessions
        service.active_sessions = {
            "session_1": SessionSummary(
                session_id="session_1",
                status="active",
                agent_type="kubernetes_agent",
                current_step="Analyzing pods",
                progress_percentage=60,
                interactions_count=10,
                errors_count=1
            ),
            "session_2": SessionSummary(
                session_id="session_2", 
                status="processing",
                agent_type="log_analyzer",
                current_step="Processing logs",
                progress_percentage=30,
                interactions_count=5,
                errors_count=0
            )
        }
        
        # Set up test metrics
        service.metrics = DashboardMetrics(
            active_sessions=2,
            completed_sessions=50,
            failed_sessions=5,
            total_interactions=1000,
            avg_session_duration=45.5,
            error_rate=8.5,
            last_updated=datetime.now()
        )
        
        return service
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_broadcast_system_metrics(self, update_service, mock_broadcaster):
        """Test broadcasting system metrics."""
        sent_count = await update_service.broadcast_system_metrics()
        
        assert sent_count == 7  # Mock broadcaster return value
        mock_broadcaster.broadcast_dashboard_update.assert_called_once()
        
        # Verify the broadcast call arguments
        call_args = mock_broadcaster.broadcast_dashboard_update.call_args[0][0]
        
        assert call_args["type"] == "system_metrics"
        assert "metrics" in call_args
        assert "active_sessions_list" in call_args
        assert "timestamp" in call_args
        
        # Verify metrics data
        metrics = call_args["metrics"]
        assert metrics["active_sessions"] == 2
        assert metrics["completed_sessions"] == 50
        assert metrics["failed_sessions"] == 5
        
        # Verify active sessions list
        sessions_list = call_args["active_sessions_list"]
        assert len(sessions_list) == 2
        
        session_1 = next(s for s in sessions_list if s["session_id"] == "session_1")
        assert session_1["status"] == "active"
        assert session_1["agent_type"] == "kubernetes_agent"
        assert session_1["current_step"] == "Analyzing pods"
        assert session_1["progress"] == 60
        assert session_1["interactions"] == 10
        assert session_1["errors"] == 1


class TestMultipleSessionInteractions:
    """Test multiple interactions on the same session."""
    
    @pytest.fixture
    def mock_broadcaster(self):
        """Mock broadcaster."""
        broadcaster = AsyncMock()
        broadcaster.broadcast_dashboard_update = AsyncMock(return_value=2)
        return broadcaster
    
    @pytest.fixture
    def update_service(self, mock_broadcaster):
        """Create service instance."""
        return DashboardUpdateService(mock_broadcaster)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_multiple_llm_interactions_same_session(self, update_service):
        """Test multiple LLM interactions on the same session."""
        session_id = "multi_llm_session"
        
        # First LLM interaction
        interaction_1 = {
            'interaction_type': 'llm',
            'session_id': session_id,
            'step_description': 'First analysis',
            'model_used': 'gpt-4',
            'success': True,
            'duration_ms': 1000,
            'timestamp': datetime.now().isoformat()
        }
        
        await update_service.process_llm_interaction(session_id, interaction_1)
        
        # Second LLM interaction
        interaction_2 = {
            'interaction_type': 'llm',
            'session_id': session_id,
            'step_description': 'Second analysis',
            'model_used': 'gpt-4',
            'success': False,
            'duration_ms': 500,
            'timestamp': datetime.now().isoformat(),
            'error_message': 'Analysis failed'
        }
        
        await update_service.process_llm_interaction(session_id, interaction_2)
        
        # Verify cumulative session tracking
        session = update_service.active_sessions[session_id]
        assert session.llm_interactions == 2
        assert session.interactions_count == 2
        assert session.errors_count == 1  # One failed interaction
        assert session.current_step == "Second analysis"  # Uses step_description from last interaction
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_mixed_llm_mcp_interactions_same_session(self, update_service):
        """Test mixed LLM and MCP interactions on the same session."""
        session_id = "mixed_session"
        
        # LLM interaction
        llm_data = {
            'interaction_type': 'llm',
            'session_id': session_id,
            'step_description': 'LLM analysis',
            'model_used': 'gpt-4',
            'success': True,
            'duration_ms': 1200,
            'timestamp': datetime.now().isoformat()
        }
        
        await update_service.process_llm_interaction(session_id, llm_data)
        
        # MCP interaction
        mcp_data = {
            'interaction_type': 'mcp',
            'session_id': session_id,
            'step_description': 'Execute kubectl command',
            'server_name': 'kubernetes',
            'tool_name': 'kubectl',
            'success': True,
            'duration_ms': 800,
            'timestamp': datetime.now().isoformat()
        }
        
        await update_service.process_mcp_communication(session_id, mcp_data)
        
        # Verify mixed interaction tracking
        session = update_service.active_sessions[session_id]
        assert session.llm_interactions == 1
        assert session.mcp_communications == 1
        assert session.interactions_count == 2
        assert session.errors_count == 0
        assert session.current_step == "Execute kubectl command"  # Uses step_description from last interaction


class TestErrorHandling:
    """Test error handling in dashboard update service."""
    
    @pytest.fixture
    def mock_broadcaster(self):
        """Mock dashboard broadcaster that sometimes fails."""
        broadcaster = AsyncMock()
        return broadcaster
    
    @pytest.fixture
    def update_service(self, mock_broadcaster):
        """Create DashboardUpdateService instance."""
        return DashboardUpdateService(mock_broadcaster)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_broadcaster_failure_handling(self, update_service, mock_broadcaster):
        """Test handling broadcaster failures gracefully."""
        # Configure broadcaster to fail
        mock_broadcaster.broadcast_session_update.side_effect = Exception("Broadcast failed")
        
        session_id = "broadcast_fail_session"
        interaction_data = {
            'interaction_type': 'llm',
            'session_id': session_id,
            'step_description': 'Test interaction',
            'model_used': 'gpt-4',
            'success': True,
            'duration_ms': 1000,
            'timestamp': datetime.now().isoformat()
        }
        
        # Should not raise exception, should return 0
        sent_count = await update_service.process_llm_interaction(
            session_id, interaction_data, broadcast_immediately=True
        )
        
        assert sent_count == 0  # Failed broadcast returns 0
        
        # Session should still be updated despite broadcast failure
        assert session_id in update_service.active_sessions
        session = update_service.active_sessions[session_id]
        assert session.llm_interactions == 1
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalid_session_data_handling(self, update_service):
        """Test handling invalid session data gracefully."""
        # Missing required fields - should not crash
        invalid_data = {"invalid": "data"}
        
        # Should not raise exception
        sent_count = await update_service.process_llm_interaction("invalid_session", invalid_data)
        assert sent_count == 0
        
        sent_count = await update_service.process_mcp_communication("invalid_session", invalid_data)
        assert sent_count == 0


class TestDualChannelBroadcasting:
    """Test dual-channel broadcasting for session-specific updates."""
    
    @pytest.fixture
    def mock_broadcaster(self):
        """Mock broadcaster configured for dual-channel testing."""
        broadcaster = AsyncMock()
        broadcaster.broadcast_dashboard_update = AsyncMock(return_value=3)
        broadcaster.broadcast_session_update = AsyncMock(return_value=2)
        return broadcaster
    
    @pytest.fixture  
    def update_service(self, mock_broadcaster):
        """Create service instance."""
        return DashboardUpdateService(mock_broadcaster)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_session_status_change_dual_channel_broadcast(self, update_service, mock_broadcaster):
        """Test that session status changes are broadcast to both channels."""
        session_id = "dual_broadcast_session"
        status = "completed"
        details = {"final_analysis": "Test analysis completed"}
        
        sent_count = await update_service.process_session_status_change(session_id, status, details)
        
        # Should return sum of both broadcasts (3 + 2 = 5)
        assert sent_count == 5
        
        # Both broadcast methods should be called
        mock_broadcaster.broadcast_session_update.assert_called_once()
        mock_broadcaster.broadcast_dashboard_update.assert_called_once()
        
        # Verify the update data structure for session-specific broadcast
        session_call_args = mock_broadcaster.broadcast_session_update.call_args
        assert session_call_args[0][0] == session_id  # First arg is session_id
        session_update_data = session_call_args[0][1]  # Second arg is update data
        assert session_update_data['type'] == 'session_status_change'
        assert session_update_data['session_id'] == session_id
        assert session_update_data['status'] == status
        
        # Verify the update data structure for dashboard broadcast  
        dashboard_call_args = mock_broadcaster.broadcast_dashboard_update.call_args
        dashboard_update_data = dashboard_call_args[0][0]  # First arg is update data
        assert dashboard_update_data['type'] == 'session_status_change'
        assert dashboard_update_data['session_id'] == session_id
        assert dashboard_update_data['status'] == status
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_broadcast_update_method_dual_channel_logic(self, update_service, mock_broadcaster):
        """Test that the _broadcast_update method correctly routes session status changes to both channels."""
        session_id = "broadcast_method_test_session"
        
        # Create a session status change update (should go to both channels)
        status_update = {
            "type": "session_status_change",
            "session_id": session_id,
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
        
        sent_count = await update_service._broadcast_update(status_update)
        
        # Should return sum of both broadcasts (3 + 2 = 5)
        assert sent_count == 5
        
        # Both broadcast methods should be called
        mock_broadcaster.broadcast_session_update.assert_called_once()
        mock_broadcaster.broadcast_dashboard_update.assert_called_once()
        
        # Create a batched session updates (should also go to both channels)
        mock_broadcaster.reset_mock()
        batched_update = {
            "type": "batched_session_updates",
            "session_id": session_id,
            "updates": [{"type": "llm_interaction", "session_id": session_id}],
            "timestamp": datetime.now().isoformat()
        }
        
        sent_count = await update_service._broadcast_update(batched_update)
        
        # Should return sum of both broadcasts (3 + 2 = 5)
        assert sent_count == 5
        
        # Both broadcast methods should be called for batched updates too
        mock_broadcaster.broadcast_session_update.assert_called_once()
        mock_broadcaster.broadcast_dashboard_update.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.unit 
    async def test_llm_interaction_single_channel_broadcast(self, update_service, mock_broadcaster):
        """Test that LLM interactions only go to session-specific channel (not dual-channel)."""
        session_id = "single_channel_session"
        llm_data = {
            'interaction_type': 'llm',
            'session_id': session_id,
            'step_description': 'Test LLM interaction',
            'model_used': 'gpt-4',
            'success': True,
            'duration_ms': 1000,
            'timestamp': datetime.now().isoformat()
        }
        
        sent_count = await update_service.process_llm_interaction(
            session_id, llm_data, broadcast_immediately=True
        )
        
        # Should only return session broadcast count (2)
        assert sent_count == 2
        
        # Only session-specific broadcast should be called
        mock_broadcaster.broadcast_session_update.assert_called_once()
        mock_broadcaster.broadcast_dashboard_update.assert_not_called()
        
        # Verify the update data structure  
        call_args = mock_broadcaster.broadcast_session_update.call_args
        assert call_args[0][0] == session_id  # First arg is session_id
        update_data = call_args[0][1]  # Second arg is update data
        assert update_data['type'] == 'llm_interaction'
        assert update_data['session_id'] == session_id


if __name__ == "__main__":
    pytest.main([__file__]) 