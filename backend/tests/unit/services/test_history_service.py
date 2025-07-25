"""
Unit tests for HistoryService.

Tests the history service functionality with mocked dependencies to ensure
proper business logic implementation without external dependencies.
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from tarsy.config.settings import Settings
from tarsy.models.history import AlertSession
from tarsy.services.history_service import HistoryService, get_history_service


class TestHistoryService:
    """Test suite for HistoryService class."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing."""
        settings = Mock(spec=Settings)
        settings.history_enabled = True
        settings.history_database_url = "sqlite:///test_history.db"
        settings.history_retention_days = 90
        return settings
    
    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager."""
        db_manager = Mock()
        db_manager.create_tables.return_value = True
        db_manager.get_session.return_value.__enter__ = Mock()
        db_manager.get_session.return_value.__exit__ = Mock()
        return db_manager
    
    @pytest.fixture
    def mock_repository(self):
        """Create mock history repository."""
        repo = Mock()
        # Create a mock session object with session_id attribute
        mock_session = Mock()
        mock_session.session_id = "test-session-id"
        repo.create_alert_session.return_value = mock_session
        repo.get_alert_session.return_value = Mock(spec=AlertSession)
        repo.update_alert_session.return_value = True
        repo.get_alert_sessions.return_value = {
            "sessions": [],
            "pagination": {"page": 1, "page_size": 20, "total_pages": 0, "total_items": 0}
        }
        return repo
    
    @pytest.fixture
    def history_service(self, mock_settings):
        """Create HistoryService instance with mocked dependencies."""
        with patch('tarsy.services.history_service.get_settings', return_value=mock_settings):
            service = HistoryService()
            service._initialization_attempted = True
            service._is_healthy = True
            return service
    
    @pytest.mark.unit
    def test_initialization_enabled(self, history_service, mock_settings):
        """Test service initialization when history is enabled."""
        assert history_service.is_enabled == True
        assert history_service.settings.history_enabled == True
        assert history_service.settings.history_database_url == "sqlite:///test_history.db"
    
    @pytest.mark.unit
    def test_initialization_disabled(self):
        """Test service initialization when history is disabled."""
        mock_settings = Mock(spec=Settings)
        mock_settings.history_enabled = False
        
        with patch('tarsy.services.history_service.get_settings', return_value=mock_settings):
            service = HistoryService()
            assert service.is_enabled == False
    
    @pytest.mark.unit
    def test_enabled_property(self, history_service):
        """Test the enabled property."""
        assert history_service.enabled == True
        
        history_service.is_enabled = False
        assert history_service.enabled == False
    
    @pytest.mark.unit
    @patch('tarsy.services.history_service.DatabaseManager')
    def test_initialize_success(self, mock_db_manager_class, mock_settings):
        """Test successful service initialization."""
        mock_db_instance = Mock()
        mock_db_manager_class.return_value = mock_db_instance
        
        with patch('tarsy.services.history_service.get_settings', return_value=mock_settings):
            service = HistoryService()
            result = service.initialize()
            
            assert result == True
            assert service._initialization_attempted == True
            assert service._is_healthy == True
            mock_db_instance.initialize.assert_called_once()
            mock_db_instance.create_tables.assert_called_once()
    
    @pytest.mark.unit
    @patch('tarsy.services.history_service.DatabaseManager')
    def test_initialize_database_failure(self, mock_db_manager_class, mock_settings):
        """Test initialization with database connection failure."""
        mock_db_manager_class.side_effect = Exception("Database connection failed")
        
        with patch('tarsy.services.history_service.get_settings', return_value=mock_settings):
            service = HistoryService()
            result = service.initialize()
            
            assert result == False
            assert service._initialization_attempted == True
            assert service._is_healthy == False
    
    @pytest.mark.unit
    @patch('tarsy.services.history_service.DatabaseManager')
    def test_initialize_schema_creation_failure(self, mock_db_manager_class, mock_settings):
        """Test initialization with schema creation failure."""
        mock_db_instance = Mock()
        mock_db_instance.initialize.return_value = None
        mock_db_instance.create_tables.side_effect = Exception("Schema creation failed")
        mock_db_manager_class.return_value = mock_db_instance
        
        with patch('tarsy.services.history_service.get_settings', return_value=mock_settings):
            service = HistoryService()
            result = service.initialize()
            
            assert result == False
            assert service._initialization_attempted == True
            assert service._is_healthy == False
    
    @pytest.mark.unit
    def test_initialize_disabled_service(self):
        """Test initialization when history service is disabled."""
        mock_settings = Mock(spec=Settings)
        mock_settings.history_enabled = False
        
        with patch('tarsy.services.history_service.get_settings', return_value=mock_settings):
            service = HistoryService()
            result = service.initialize()
            
            assert result == False
            assert service._initialization_attempted == False  # Should not attempt when disabled
            assert service._is_healthy == False
    
    @pytest.mark.unit
    @patch('tarsy.services.history_service.HistoryRepository')
    def test_get_repository_context_manager(self, mock_repo_class, history_service, mock_db_manager):
        """Test the repository context manager."""
        history_service.db_manager = mock_db_manager
        mock_repo_instance = Mock()
        mock_repo_class.return_value = mock_repo_instance
        
        # Test successful context manager usage
        with history_service.get_repository() as repo:
            assert repo == mock_repo_instance
    
    @pytest.mark.unit
    @patch('tarsy.services.history_service.HistoryRepository')
    def test_get_repository_disabled_service(self, mock_repo_class, history_service):
        """Test repository access when service is disabled."""
        history_service.is_enabled = False
        
        with history_service.get_repository() as repo:
            assert repo is None
    
    @pytest.mark.unit
    def test_create_session_success(self, history_service, mock_repository):
        """Test successful session creation."""
        with patch.object(history_service, 'get_repository') as mock_get_repo:
            mock_get_repo.return_value.__enter__.return_value = mock_repository
            mock_get_repo.return_value.__exit__.return_value = None
            
            session_id = history_service.create_session(
                alert_id="test-alert-123",
                alert_data={"alert_type": "test", "environment": "test"},
                agent_type="TestAgent",
                alert_type="test_alert"
            )
            
            assert session_id == "test-session-id"
            mock_repository.create_alert_session.assert_called_once()
    
    @pytest.mark.unit
    def test_create_session_disabled_service(self, history_service):
        """Test session creation when service is disabled."""
        history_service.is_enabled = False
        
        session_id = history_service.create_session(
            alert_id="test-alert-123",
            alert_data={},
            agent_type="TestAgent",
            alert_type="test_alert"
        )
        
        assert session_id is None
    
    @pytest.mark.unit
    def test_create_session_exception_handling(self, history_service):
        """Test session creation with exception handling."""
        with patch.object(history_service, 'get_repository') as mock_get_repo:
            mock_get_repo.side_effect = Exception("Database error")
            
            session_id = history_service.create_session(
                alert_id="test-alert-123",
                alert_data={},
                agent_type="TestAgent",
                alert_type="test_alert"
            )
            
            assert session_id is None
    
    @pytest.mark.unit
    def test_update_session_status_success(self, history_service, mock_repository):
        """Test successful session status update."""
        mock_session = Mock(spec=AlertSession)
        mock_repository.get_alert_session.return_value = mock_session
        
        with patch.object(history_service, 'get_repository') as mock_get_repo:
            mock_get_repo.return_value.__enter__.return_value = mock_repository
            mock_get_repo.return_value.__exit__.return_value = None
            
            result = history_service.update_session_status(
                session_id="test-session-id",
                status="completed",
                error_message=None
            )
            
            assert result == True
            assert mock_session.status == "completed"
            mock_repository.update_alert_session.assert_called_once_with(mock_session)
    
    @pytest.mark.unit
    def test_update_session_status_with_completion(self, history_service, mock_repository):
        """Test session status update with completion timestamp."""
        mock_session = Mock(spec=AlertSession)
        mock_repository.get_alert_session.return_value = mock_session
        
        with patch.object(history_service, 'get_repository') as mock_get_repo:
            mock_get_repo.return_value.__enter__.return_value = mock_repository
            mock_get_repo.return_value.__exit__.return_value = None
            
            result = history_service.update_session_status(
                session_id="test-session-id",
                status="completed"
            )
            
            assert result == True
            assert mock_session.status == "completed"
            assert mock_session.completed_at is not None
    
    @pytest.mark.unit
    def test_update_session_status_disabled_service(self, history_service):
        """Test session status update when service is disabled."""
        history_service.is_enabled = False
        
        result = history_service.update_session_status(
            session_id="test-session-id",
            status="completed"
        )
        
        assert result == False
    
    @pytest.mark.unit
    def test_log_llm_interaction_success(self, history_service, mock_repository):
        """Test successful LLM interaction logging."""
        with patch.object(history_service, 'get_repository') as mock_get_repo:
            mock_get_repo.return_value.__enter__.return_value = mock_repository
            mock_get_repo.return_value.__exit__.return_value = None
            
            result = history_service.log_llm_interaction(
                session_id="test-session-id",
                prompt_text="Test prompt",
                response_text="Test response",
                model_used="gpt-4",
                step_description="Test LLM call"
            )
            
            assert result == True
            mock_repository.create_llm_interaction.assert_called_once()
    
    @pytest.mark.unit
    def test_log_mcp_communication_success(self, history_service, mock_repository):
        """Test successful MCP communication logging."""
        with patch.object(history_service, 'get_repository') as mock_get_repo:
            mock_get_repo.return_value.__enter__.return_value = mock_repository
            mock_get_repo.return_value.__exit__.return_value = None
            
            result = history_service.log_mcp_communication(
                session_id="test-session-id",
                server_name="test-server",
                communication_type="tool_call",
                tool_name="test_tool",
                step_description="Test MCP call",
                success=True
            )
            
            assert result == True
            mock_repository.create_mcp_communication.assert_called_once()
    
    @pytest.mark.unit
    def test_get_sessions_list_success(self, history_service, mock_repository):
        """Test successful sessions list retrieval."""
        mock_sessions = [Mock(spec=AlertSession) for _ in range(3)]
        mock_repository.get_alert_sessions.return_value = {
            "sessions": mock_sessions,
            "pagination": {"page": 1, "page_size": 20, "total_pages": 1, "total_items": 3}
        }
        
        with patch.object(history_service, 'get_repository') as mock_get_repo:
            mock_get_repo.return_value.__enter__.return_value = mock_repository
            mock_get_repo.return_value.__exit__.return_value = None
            
            sessions, total_count = history_service.get_sessions_list(
                filters={"status": "completed"},
                page=1,
                page_size=20
            )
            
            assert len(sessions) == 3
            assert total_count == 3
            mock_repository.get_alert_sessions.assert_called_once()
    
    @pytest.mark.unit
    def test_get_sessions_list_disabled_service(self, history_service):
        """Test sessions list retrieval when service is disabled."""
        history_service.is_enabled = False
        
        sessions, total_count = history_service.get_sessions_list()
        
        assert sessions == []
        assert total_count == 0
    
    @pytest.mark.unit
    def test_get_session_timeline_success(self, history_service, mock_repository):
        """Test successful session timeline retrieval."""
        mock_timeline_data = {
            "session_info": {"session_id": "test-session-id", "status": "completed"},
            "chronological_timeline": [
                {"type": "llm_interaction", "timestamp": datetime.now(timezone.utc)},
                {"type": "mcp_communication", "timestamp": datetime.now(timezone.utc)}
            ],
            "summary": {"total_interactions": 2}
        }
        mock_repository.get_session_timeline.return_value = mock_timeline_data
        
        with patch.object(history_service, 'get_repository') as mock_get_repo:
            mock_get_repo.return_value.__enter__.return_value = mock_repository
            mock_get_repo.return_value.__exit__.return_value = None
            
            timeline = history_service.get_session_timeline("test-session-id")
            
            assert timeline == mock_timeline_data
            assert timeline["session_info"]["session_id"] == "test-session-id"
            assert len(timeline["chronological_timeline"]) == 2
    
    @pytest.mark.unit
    def test_test_database_connection_success(self, history_service, mock_repository):
        """Test successful database connection test."""
        with patch.object(history_service, 'get_repository') as mock_get_repo:
            mock_get_repo.return_value.__enter__.return_value = mock_repository
            mock_get_repo.return_value.__exit__.return_value = None
            
            result = history_service.test_database_connection()
            
            assert result == True
            mock_repository.get_alert_sessions.assert_called_once_with(page=1, page_size=1)
    
    @pytest.mark.unit
    def test_test_database_connection_failure(self, history_service):
        """Test database connection test failure."""
        with patch.object(history_service, 'get_repository') as mock_get_repo:
            mock_get_repo.side_effect = Exception("Connection failed")
            
            result = history_service.test_database_connection()
            
            assert result == False
    
    @pytest.mark.unit
    def test_health_check(self, history_service):
        """Test health check functionality."""
        health = history_service.health_check()
        
        assert health["enabled"] == True
        assert health["healthy"] == True
        assert "database_url" in health
        assert "retention_days" in health
    
    @pytest.mark.unit
    def test_get_active_sessions(self, history_service, mock_repository):
        """Test active sessions retrieval."""
        mock_active_sessions = [Mock(spec=AlertSession) for _ in range(2)]
        mock_repository.get_active_sessions.return_value = mock_active_sessions
        
        with patch.object(history_service, 'get_repository') as mock_get_repo:
            mock_get_repo.return_value.__enter__.return_value = mock_repository
            mock_get_repo.return_value.__exit__.return_value = None
            
            active_sessions = history_service.get_active_sessions()
            
            assert len(active_sessions) == 2
            mock_repository.get_active_sessions.assert_called_once()
    
    @pytest.mark.unit
    def test_cleanup_old_sessions(self, history_service, mock_repository):
        """Test cleanup of old sessions."""
        mock_repository.cleanup_old_sessions.return_value = 5
        
        with patch.object(history_service, 'get_repository') as mock_get_repo:
            mock_get_repo.return_value.__enter__.return_value = mock_repository
            mock_get_repo.return_value.__exit__.return_value = None
            
            cleaned_count = history_service.cleanup_old_sessions()
            
            assert cleaned_count == 5
            mock_repository.cleanup_old_sessions.assert_called_once()
    
    @pytest.mark.unit
    @patch('time.sleep')
    def test_retry_database_operation_success_after_retry(self, mock_sleep, history_service):
        """Test operation succeeds after transient failure."""
        call_count = 0
        
        def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("database is locked")
            return "success"
        
        result = history_service._retry_database_operation("test_operation", mock_operation)
        
        assert result == "success"
        assert call_count == 2
        mock_sleep.assert_called_once()  # Should have slept once for retry
    
    @pytest.mark.unit
    @patch('time.sleep')
    def test_retry_database_operation_exhausts_retries(self, mock_sleep, history_service):
        """Test operation fails after max retries."""
        def mock_operation():
            raise Exception("database is locked")
        
        result = history_service._retry_database_operation("test_operation", mock_operation)
        
        assert result is None
        assert mock_sleep.call_count == history_service.max_retries  # Should retry max_retries times
    
    @pytest.mark.unit
    @patch('time.sleep')
    def test_retry_database_operation_non_retryable_error(self, mock_sleep, history_service):
        """Test operation fails immediately on non-retryable error."""
        def mock_operation():
            raise Exception("syntax error")  # Non-retryable error
        
        result = history_service._retry_database_operation("test_operation", mock_operation)
        
        assert result is None
        mock_sleep.assert_not_called()  # Should not retry for non-retryable errors
    
    @pytest.mark.unit
    def test_get_sessions_dict_format(self, history_service, mock_repository):
        """Test get_sessions method returns dict format (different from get_sessions_list)."""
        mock_sessions = [Mock(spec=AlertSession) for _ in range(2)]
        expected_result = {
            "sessions": mock_sessions,
            "pagination": {"page": 1, "page_size": 20, "total_pages": 1, "total_items": 2}
        }
        mock_repository.get_alert_sessions.return_value = expected_result
        
        with patch.object(history_service, 'get_repository') as mock_get_repo:
            mock_get_repo.return_value.__enter__.return_value = mock_repository
            mock_get_repo.return_value.__exit__.return_value = None
            
            result = history_service.get_sessions(status="completed", page=1, page_size=20)
            
            assert result == expected_result
            assert isinstance(result, dict)  # Different from get_sessions_list which returns tuple
            mock_repository.get_alert_sessions.assert_called_once_with(
                status="completed",
                agent_type=None,
                alert_type=None,
                start_date=None,
                end_date=None,
                page=1,
                page_size=20
            )
    
    @pytest.mark.unit
    @patch('tarsy.services.history_service.DatabaseManager')
    def test_shutdown_cleanup(self, mock_db_manager_class, mock_settings):
        """Test graceful service shutdown."""
        mock_db_instance = Mock()
        mock_db_manager_class.return_value = mock_db_instance
        
        with patch('tarsy.services.history_service.get_settings', return_value=mock_settings):
            service = HistoryService()
            service.db_manager = mock_db_instance
            
            service.shutdown()
            
            mock_db_instance.close.assert_called_once()
    
    @pytest.mark.unit
    def test_shutdown_with_exception_handling(self, history_service):
        """Test shutdown handles exceptions gracefully."""
        mock_db_manager = Mock()
        mock_db_manager.close.side_effect = Exception("Close failed")
        history_service.db_manager = mock_db_manager
        
        # Should not raise exception
        history_service.shutdown()
        
        mock_db_manager.close.assert_called_once()


class TestHistoryServiceGlobalInstance:
    """Test suite for global history service instance management."""
    
    @pytest.mark.unit
    @patch('tarsy.services.history_service._history_service', None)
    def test_get_history_service_singleton(self):
        """Test that get_history_service returns a singleton instance."""
        with patch('tarsy.services.history_service.HistoryService') as mock_service_class:
            mock_instance = Mock()
            mock_service_class.return_value = mock_instance
            
            # First call should create instance
            service1 = get_history_service()
            
            # Second call should return same instance
            service2 = get_history_service()
            
            assert service1 == service2
            mock_service_class.assert_called_once()
    
    @pytest.mark.unit
    @patch('tarsy.services.history_service._history_service', None)
    def test_get_history_service_initialization(self):
        """Test that get_history_service initializes the service."""
        with patch('tarsy.services.history_service.HistoryService') as mock_service_class:
            mock_instance = Mock()
            mock_service_class.return_value = mock_instance
            
            service = get_history_service()
            
            assert service == mock_instance
            mock_instance.initialize.assert_called_once()


class TestHistoryServiceErrorHandling:
    """Test suite for HistoryService error handling scenarios."""
    
    @pytest.fixture
    def history_service_with_errors(self):
        """Create HistoryService that simulates various error conditions."""
        mock_settings = Mock(spec=Settings)
        mock_settings.history_enabled = True
        mock_settings.history_database_url = "sqlite:///test_history.db"
        mock_settings.history_retention_days = 90
        
        with patch('tarsy.services.history_service.get_settings', return_value=mock_settings):
            service = HistoryService()
            service._initialization_attempted = True
            service._is_healthy = False  # Simulate unhealthy state
            return service
    
    @pytest.mark.unit
    def test_graceful_degradation_repository_unavailable(self, history_service_with_errors):
        """Test graceful degradation when repository is unavailable."""
        with patch.object(history_service_with_errors, 'get_repository') as mock_get_repo:
            mock_get_repo.return_value.__enter__.return_value = None
            mock_get_repo.return_value.__exit__.return_value = None
            
            # All operations should return safe defaults
            session_id = history_service_with_errors.create_session("test", {}, "agent", "alert")
            assert session_id is None
            
            result = history_service_with_errors.update_session_status("test", "completed")
            assert result == False
            
            sessions, count = history_service_with_errors.get_sessions_list()
            assert sessions == []
            assert count == 0
    
    @pytest.mark.unit
    def test_exception_handling_in_operations(self, history_service_with_errors):
        """Test exception handling in various operations."""
        with patch.object(history_service_with_errors, 'get_repository') as mock_get_repo:
            mock_get_repo.side_effect = Exception("Simulated error")
            
            # All operations should handle exceptions gracefully
            session_id = history_service_with_errors.create_session("test", {}, "agent", "alert")
            assert session_id is None
            
            result = history_service_with_errors.log_llm_interaction("test", "prompt", "response", "model", "step")
            assert result == False
            
            result = history_service_with_errors.log_mcp_communication("test", "server", "type", "tool", "step")
            assert result == False


class TestDashboardMethods:
    """Test suite for new dashboard-specific methods in HistoryService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create mock repository for dashboard methods."""
        repo = Mock()
        repo.get_dashboard_metrics.return_value = {
            "active_sessions": 5,
            "completed_sessions": 20,
            "failed_sessions": 3,
            "total_interactions": 100,
            "avg_session_duration": 30.5,
            "error_rate": 12.5,
            "last_24h_sessions": 8
        }
        repo.get_filter_options.return_value = {
            "agent_types": ["kubernetes", "network"],
            "alert_types": ["PodCrashLooping"],
            "status_options": ["pending", "in_progress", "completed", "failed"],
            "time_ranges": [
                {"label": "Last Hour", "value": "1h"},
                {"label": "Today", "value": "today"}
            ]
        }
        return repo
    
    @pytest.fixture
    def history_service_with_mock_repo(self, mock_repository):
        """Create HistoryService with mocked repository."""
        service = HistoryService()
        service.is_enabled = True
        service._is_healthy = True
        
        # Mock the get_repository context manager
        with patch.object(service, 'get_repository') as mock_get_repo:
            mock_get_repo.return_value.__enter__.return_value = mock_repository
            mock_get_repo.return_value.__exit__.return_value = None
            yield service, mock_repository
    
    @pytest.mark.unit
    def test_get_dashboard_metrics_success(self, history_service_with_mock_repo):
        """Test successful dashboard metrics retrieval."""
        service, mock_repo = history_service_with_mock_repo
        
        result = service.get_dashboard_metrics()
        
        # Verify the result
        assert result["active_sessions"] == 5
        assert result["completed_sessions"] == 20
        assert result["failed_sessions"] == 3
        assert result["total_interactions"] == 100
        assert result["avg_session_duration"] == 30.5
        assert result["error_rate"] == 12.5
        assert result["last_24h_sessions"] == 8
        
        # Verify repository was called
        mock_repo.get_dashboard_metrics.assert_called_once()
    
    @pytest.mark.unit
    def test_get_dashboard_metrics_no_repository(self):
        """Test dashboard metrics when repository is unavailable."""
        service = HistoryService()
        service.is_enabled = True
        service._is_healthy = False
        
        with patch.object(service, 'get_repository') as mock_get_repo:
            mock_get_repo.return_value.__enter__.return_value = None
            
            result = service.get_dashboard_metrics()
            
            # Should return default values
            assert result["active_sessions"] == 0
            assert result["completed_sessions"] == 0
            assert result["failed_sessions"] == 0
            assert result["total_interactions"] == 0
            assert result["avg_session_duration"] == 0.0
            assert result["error_rate"] == 0.0
            assert result["last_24h_sessions"] == 0
    
    @pytest.mark.unit
    def test_get_dashboard_metrics_exception(self):
        """Test dashboard metrics with repository exception."""
        service = HistoryService()
        service.is_enabled = True
        
        with patch.object(service, 'get_repository') as mock_get_repo:
            mock_get_repo.side_effect = Exception("Database error")
            
            result = service.get_dashboard_metrics()
            
            # Should return default values on exception
            assert result["active_sessions"] == 0
            assert result["completed_sessions"] == 0
            assert result["failed_sessions"] == 0
    
    @pytest.mark.unit
    def test_get_filter_options_success(self, history_service_with_mock_repo):
        """Test successful filter options retrieval."""
        service, mock_repo = history_service_with_mock_repo
        
        result = service.get_filter_options()
        
        # Verify the result
        assert "agent_types" in result
        assert "alert_types" in result
        assert "status_options" in result
        assert "time_ranges" in result
        assert len(result["agent_types"]) == 2
        assert "kubernetes" in result["agent_types"]
        assert len(result["time_ranges"]) == 2
        
        # Verify repository was called
        mock_repo.get_filter_options.assert_called_once()
    
    @pytest.mark.unit
    def test_get_filter_options_no_repository(self):
        """Test filter options when repository is unavailable."""
        service = HistoryService()
        service.is_enabled = True
        service._is_healthy = False
        
        with patch.object(service, 'get_repository') as mock_get_repo:
            mock_get_repo.return_value.__enter__.return_value = None
            
            result = service.get_filter_options()
            
            # Should return default values
            assert result["agent_types"] == []
            assert result["alert_types"] == []
            assert len(result["status_options"]) == 4
            assert len(result["time_ranges"]) == 4
    
    @pytest.mark.unit
    def test_get_filter_options_exception(self):
        """Test filter options with repository exception."""
        service = HistoryService()
        service.is_enabled = True
        
        with patch.object(service, 'get_repository') as mock_get_repo:
            mock_get_repo.side_effect = Exception("Database error")
            
            result = service.get_filter_options()
            
            # Should return default values on exception
            assert result["agent_types"] == []
            assert result["alert_types"] == []
            assert len(result["status_options"]) == 4


class TestExportAndSearchMethods:
    """Test suite for export and search functionality in HistoryService."""
    
    @pytest.fixture
    def service(self):
        """Create HistoryService instance for testing."""
        return HistoryService()
    
    @pytest.fixture
    def mock_repo(self):
        """Create mock repository."""
        return Mock()
    
    @pytest.mark.unit
    def test_export_session_data_success(self, service, mock_repo):
        """Test successful session data export."""
        # Setup mock repository
        mock_repo.export_session_data.return_value = {
            "session_id": "test_session",
            "format": "json",
            "data": {
                "session": {"session_id": "test_session", "status": "completed"},
                "timeline": {"interactions": []},
                "export_metadata": {"exported_at": "2025-01-25T00:00:00Z"}
            },
            "error": None
        }
        
        # Mock the repository context manager
        service.get_repository = Mock(return_value=mock_repo)
        mock_repo.__enter__ = Mock(return_value=mock_repo)
        mock_repo.__exit__ = Mock(return_value=None)
        
        # Call method
        result = service.export_session_data("test_session", "json")
        
        # Verify result
        assert result["session_id"] == "test_session"
        assert result["format"] == "json"
        assert result["data"]["session"]["session_id"] == "test_session"
        assert result["error"] is None
        
        # Verify repository was called
        mock_repo.export_session_data.assert_called_once_with("test_session", "json")
    
    @pytest.mark.unit
    def test_export_session_data_csv_format(self, service, mock_repo):
        """Test session data export with CSV format."""
        # Setup mock repository
        mock_repo.export_session_data.return_value = {
            "session_id": "test_session",
            "format": "csv",
            "data": {
                "session": {
                    "session_id": "test_session",
                    "alert_id": "test_alert",
                    "status": "completed"
                },
                "timeline": {"interactions": []},
                "export_metadata": {"exported_at": "2025-01-25T00:00:00Z"}
            },
            "error": None
        }
        
        # Mock the repository context manager
        service.get_repository = Mock(return_value=mock_repo)
        mock_repo.__enter__ = Mock(return_value=mock_repo)
        mock_repo.__exit__ = Mock(return_value=None)
        
        # Call method
        result = service.export_session_data("test_session", "csv")
        
        # Verify result
        assert result["format"] == "csv"
        assert result["data"]["session"]["session_id"] == "test_session"
        
        # Verify repository was called with CSV format
        mock_repo.export_session_data.assert_called_once_with("test_session", "csv")
    
    @pytest.mark.unit
    def test_export_session_data_no_repository(self, service):
        """Test export when repository is unavailable."""
        # Mock get_repository to return a context manager that yields None
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=None)
        mock_context.__exit__ = Mock(return_value=None)
        service.get_repository = Mock(return_value=mock_context)
        
        # Call method
        result = service.export_session_data("test_session", "json")
        
        # Verify error response
        assert result["error"] == "Repository unavailable"
        assert result["session_id"] == "test_session"
        assert result["format"] == "json"
        assert result["data"] is None
    
    @pytest.mark.unit
    def test_export_session_data_repository_exception(self, service, mock_repo):
        """Test export when repository raises exception."""
        # Setup mock repository to raise exception
        mock_repo.export_session_data.side_effect = Exception("Database error")
        
        # Mock the repository context manager
        service.get_repository = Mock(return_value=mock_repo)
        mock_repo.__enter__ = Mock(return_value=mock_repo)
        mock_repo.__exit__ = Mock(return_value=None)
        
        # Call method
        result = service.export_session_data("test_session", "json")
        
        # Verify error response
        assert result["error"] == "Database error"
        assert result["session_id"] == "test_session"
        assert result["format"] == "json"
        assert result["data"] is None
    
    @pytest.mark.unit
    def test_search_sessions_success(self, service, mock_repo):
        """Test successful session search."""
        # Setup mock repository
        expected_results = [
            {
                "session_id": "session_1",
                "alert_id": "namespace_alert",
                "agent_type": "KubernetesAgent",
                "status": "completed"
            },
            {
                "session_id": "session_2", 
                "alert_id": "another_namespace_alert",
                "agent_type": "KubernetesAgent",
                "status": "failed"
            }
        ]
        mock_repo.search_sessions.return_value = expected_results
        
        # Mock the repository context manager
        service.get_repository = Mock(return_value=mock_repo)
        mock_repo.__enter__ = Mock(return_value=mock_repo)
        mock_repo.__exit__ = Mock(return_value=None)
        
        # Call method
        result = service.search_sessions("namespace", 5)
        
        # Verify result
        assert result == expected_results
        assert len(result) == 2
        assert result[0]["session_id"] == "session_1"
        assert result[1]["session_id"] == "session_2"
        
        # Verify repository was called
        mock_repo.search_sessions.assert_called_once_with("namespace", 5)
    
    @pytest.mark.unit
    def test_search_sessions_empty_results(self, service, mock_repo):
        """Test search with no matching results."""
        # Setup mock repository to return empty list
        mock_repo.search_sessions.return_value = []
        
        # Mock the repository context manager
        service.get_repository = Mock(return_value=mock_repo)
        mock_repo.__enter__ = Mock(return_value=mock_repo)
        mock_repo.__exit__ = Mock(return_value=None)
        
        # Call method
        result = service.search_sessions("nonexistent", 10)
        
        # Verify empty result
        assert result == []
        
        # Verify repository was called
        mock_repo.search_sessions.assert_called_once_with("nonexistent", 10)
    
    @pytest.mark.unit
    def test_search_sessions_default_limit(self, service, mock_repo):
        """Test search with default limit parameter."""
        # Setup mock repository
        mock_repo.search_sessions.return_value = []
        
        # Mock the repository context manager
        service.get_repository = Mock(return_value=mock_repo)
        mock_repo.__enter__ = Mock(return_value=mock_repo)
        mock_repo.__exit__ = Mock(return_value=None)
        
        # Call method without limit parameter
        result = service.search_sessions("test")
        
        # Verify repository was called with default limit
        mock_repo.search_sessions.assert_called_once_with("test", 10)
    
    @pytest.mark.unit
    def test_search_sessions_no_repository(self, service):
        """Test search when repository is unavailable."""
        # Mock get_repository to return a context manager that yields None
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=None)
        mock_context.__exit__ = Mock(return_value=None)
        service.get_repository = Mock(return_value=mock_context)
        
        # Call method
        result = service.search_sessions("test", 5)
        
        # Verify empty result
        assert result == []
    
    @pytest.mark.unit
    def test_search_sessions_repository_exception(self, service, mock_repo):
        """Test search when repository raises exception."""
        # Setup mock repository to raise exception
        mock_repo.search_sessions.side_effect = Exception("Database connection failed")
        
        # Mock the repository context manager
        service.get_repository = Mock(return_value=mock_repo)
        mock_repo.__enter__ = Mock(return_value=mock_repo)
        mock_repo.__exit__ = Mock(return_value=None)
        
        # Call method
        result = service.search_sessions("test", 5)
        
        # Verify empty result on exception
        assert result == [] 