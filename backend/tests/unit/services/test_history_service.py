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
        with patch('app.services.history_service.get_settings', return_value=mock_settings):
            service = HistoryService()
            service._initialization_attempted = True
            service._is_healthy = True
            return service
    
    def test_initialization_enabled(self, history_service, mock_settings):
        """Test service initialization when history is enabled."""
        assert history_service.is_enabled == True
        assert history_service.settings.history_enabled == True
        assert history_service.settings.history_database_url == "sqlite:///test_history.db"
    
    def test_initialization_disabled(self):
        """Test service initialization when history is disabled."""
        mock_settings = Mock(spec=Settings)
        mock_settings.history_enabled = False
        
        with patch('app.services.history_service.get_settings', return_value=mock_settings):
            service = HistoryService()
            assert service.is_enabled == False
    
    def test_enabled_property(self, history_service):
        """Test the enabled property."""
        assert history_service.enabled == True
        
        history_service.is_enabled = False
        assert history_service.enabled == False
    
    @patch('app.services.history_service.HistoryRepository')
    def test_get_repository_context_manager(self, mock_repo_class, history_service, mock_db_manager):
        """Test the repository context manager."""
        history_service.db_manager = mock_db_manager
        mock_repo_instance = Mock()
        mock_repo_class.return_value = mock_repo_instance
        
        # Test successful context manager usage
        with history_service.get_repository() as repo:
            assert repo == mock_repo_instance
    
    @patch('app.services.history_service.HistoryRepository')
    def test_get_repository_disabled_service(self, mock_repo_class, history_service):
        """Test repository access when service is disabled."""
        history_service.is_enabled = False
        
        with history_service.get_repository() as repo:
            assert repo is None
    
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
    
    def test_update_session_status_disabled_service(self, history_service):
        """Test session status update when service is disabled."""
        history_service.is_enabled = False
        
        result = history_service.update_session_status(
            session_id="test-session-id",
            status="completed"
        )
        
        assert result == False
    
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
    
    def test_get_sessions_list_disabled_service(self, history_service):
        """Test sessions list retrieval when service is disabled."""
        history_service.is_enabled = False
        
        sessions, total_count = history_service.get_sessions_list()
        
        assert sessions == []
        assert total_count == 0
    
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
    
    def test_test_database_connection_success(self, history_service, mock_repository):
        """Test successful database connection test."""
        with patch.object(history_service, 'get_repository') as mock_get_repo:
            mock_get_repo.return_value.__enter__.return_value = mock_repository
            mock_get_repo.return_value.__exit__.return_value = None
            
            result = history_service.test_database_connection()
            
            assert result == True
            mock_repository.get_alert_sessions.assert_called_once_with(page=1, page_size=1)
    
    def test_test_database_connection_failure(self, history_service):
        """Test database connection test failure."""
        with patch.object(history_service, 'get_repository') as mock_get_repo:
            mock_get_repo.side_effect = Exception("Connection failed")
            
            result = history_service.test_database_connection()
            
            assert result == False
    
    def test_health_check(self, history_service):
        """Test health check functionality."""
        health = history_service.health_check()
        
        assert health["enabled"] == True
        assert health["healthy"] == True
        assert "database_url" in health
        assert "retention_days" in health
    
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
    
    def test_cleanup_old_sessions(self, history_service, mock_repository):
        """Test cleanup of old sessions."""
        mock_repository.cleanup_old_sessions.return_value = 5
        
        with patch.object(history_service, 'get_repository') as mock_get_repo:
            mock_get_repo.return_value.__enter__.return_value = mock_repository
            mock_get_repo.return_value.__exit__.return_value = None
            
            cleaned_count = history_service.cleanup_old_sessions()
            
            assert cleaned_count == 5
            mock_repository.cleanup_old_sessions.assert_called_once()


class TestHistoryServiceGlobalInstance:
    """Test suite for global history service instance management."""
    
    @patch('app.services.history_service._history_service', None)
    def test_get_history_service_singleton(self):
        """Test that get_history_service returns a singleton instance."""
        with patch('app.services.history_service.HistoryService') as mock_service_class:
            mock_instance = Mock()
            mock_service_class.return_value = mock_instance
            
            # First call should create instance
            service1 = get_history_service()
            
            # Second call should return same instance
            service2 = get_history_service()
            
            assert service1 == service2
            mock_service_class.assert_called_once()
    
    @patch('app.services.history_service._history_service', None)
    def test_get_history_service_initialization(self):
        """Test that get_history_service initializes the service."""
        with patch('app.services.history_service.HistoryService') as mock_service_class:
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
        
        with patch('app.services.history_service.get_settings', return_value=mock_settings):
            service = HistoryService()
            service._initialization_attempted = True
            service._is_healthy = False  # Simulate unhealthy state
            return service
    
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