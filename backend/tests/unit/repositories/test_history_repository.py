"""
Unit tests for HistoryRepository.

Tests the repository layer functionality with in-memory database to ensure
proper data access layer implementation and database operations.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timezone, timedelta
from sqlmodel import SQLModel, create_engine, Session

from app.repositories.history_repository import HistoryRepository
from app.models.history import AlertSession, LLMInteraction, MCPCommunication


class TestHistoryRepository:
    """Test suite for HistoryRepository class."""
    
    @pytest.fixture
    def in_memory_engine(self):
        """Create in-memory SQLite engine for testing."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        SQLModel.metadata.create_all(engine)
        return engine
    
    @pytest.fixture
    def db_session(self, in_memory_engine):
        """Create database session for testing."""
        with Session(in_memory_engine) as session:
            yield session
    
    @pytest.fixture
    def repository(self, db_session):
        """Create HistoryRepository instance with test database session."""
        return HistoryRepository(db_session)
    
    @pytest.fixture
    def sample_alert_session(self):
        """Create sample AlertSession for testing."""
        return AlertSession(
            session_id="test-session-123",
            alert_id="alert-456",
            alert_data={
                "alert_type": "NamespaceTerminating",
                "environment": "production",
                "cluster": "k8s-prod",
                "namespace": "stuck-namespace"
            },
            agent_type="KubernetesAgent",
            alert_type="NamespaceTerminating",
            status="in_progress",
            started_at=datetime.now(timezone.utc),
            session_metadata={"test": "metadata"}
        )
    
    @pytest.fixture
    def sample_llm_interaction(self):
        """Create sample LLMInteraction for testing."""
        return LLMInteraction(
            interaction_id="llm-interaction-789",
            session_id="test-session-123",
            prompt_text="Analyze the namespace termination issue",
            response_text="The namespace is stuck due to finalizers",
            model_used="gpt-4",
            timestamp=datetime.now(timezone.utc),
            step_description="Initial analysis",
            duration_ms=1500
        )
    
    @pytest.fixture
    def sample_mcp_communication(self):
        """Create sample MCPCommunication for testing."""
        return MCPCommunication(
            communication_id="mcp-comm-101",
            session_id="test-session-123",
            server_name="kubernetes-server",
            communication_type="tool_call",
            tool_name="kubectl_get_namespace",
            tool_arguments={"namespace": "stuck-namespace"},
            tool_result={"status": "Terminating", "finalizers": ["test-finalizer"]},
            timestamp=datetime.now(timezone.utc),
            step_description="Check namespace status",
            duration_ms=800,
            success=True
        )
    
    def test_create_alert_session_success(self, repository, sample_alert_session):
        """Test successful alert session creation."""
        created_session = repository.create_alert_session(sample_alert_session)
        
        assert created_session.session_id == sample_alert_session.session_id
        
        # Verify session was saved to database
        retrieved_session = repository.get_alert_session(created_session.session_id)
        assert retrieved_session is not None
        assert retrieved_session.alert_id == sample_alert_session.alert_id
        assert retrieved_session.agent_type == sample_alert_session.agent_type
        assert retrieved_session.status == sample_alert_session.status
    
    def test_get_alert_session_not_found(self, repository):
        """Test getting alert session that doesn't exist."""
        session = repository.get_alert_session("non-existent-session")
        assert session is None
    
    def test_update_alert_session_success(self, repository, sample_alert_session):
        """Test successful alert session update."""
        # Create session first
        repository.create_alert_session(sample_alert_session)
        
        # Update session
        sample_alert_session.status = "completed"
        sample_alert_session.completed_at = datetime.now(timezone.utc)
        
        result = repository.update_alert_session(sample_alert_session)
        assert result == True
        
        # Verify update
        updated_session = repository.get_alert_session(sample_alert_session.session_id)
        assert updated_session.status == "completed"
        assert updated_session.completed_at is not None
    
    def test_create_llm_interaction_success(self, repository, sample_alert_session, sample_llm_interaction):
        """Test successful LLM interaction creation."""
        # Create session first
        repository.create_alert_session(sample_alert_session)
        
        # Create interaction
        created_interaction = repository.create_llm_interaction(sample_llm_interaction)
        
        assert created_interaction.interaction_id == sample_llm_interaction.interaction_id
        
        # Verify interaction was saved
        interactions = repository.get_llm_interactions_for_session(sample_alert_session.session_id)
        assert len(interactions) == 1
        assert interactions[0].prompt_text == sample_llm_interaction.prompt_text
        assert interactions[0].response_text == sample_llm_interaction.response_text
    
    def test_create_mcp_communication_success(self, repository, sample_alert_session, sample_mcp_communication):
        """Test successful MCP communication creation."""
        # Create session first
        repository.create_alert_session(sample_alert_session)
        
        # Create communication
        created_communication = repository.create_mcp_communication(sample_mcp_communication)
        
        assert created_communication.communication_id == sample_mcp_communication.communication_id
        
        # Verify communication was saved
        communications = repository.get_mcp_communications_for_session(sample_alert_session.session_id)
        assert len(communications) == 1
        assert communications[0].server_name == sample_mcp_communication.server_name
        assert communications[0].tool_name == sample_mcp_communication.tool_name
    
    def test_get_alert_sessions_with_filters(self, repository, sample_alert_session):
        """Test getting alert sessions with various filters."""
        # Create multiple sessions with different attributes
        session1 = sample_alert_session
        repository.create_alert_session(session1)
        
        session2 = AlertSession(
            session_id="test-session-456",
            alert_id="alert-789",
            alert_data={"alert_type": "HighCPU"},
            agent_type="KubernetesAgent",
            alert_type="HighCPU",
            status="completed",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc)
        )
        repository.create_alert_session(session2)
        
        # Test status filter
        result = repository.get_alert_sessions(status="completed")
        assert len(result["sessions"]) == 1
        assert result["sessions"][0].session_id == session2.session_id
        
        # Test agent_type filter
        result = repository.get_alert_sessions(agent_type="KubernetesAgent")
        assert len(result["sessions"]) == 2
        
        # Test alert_type filter
        result = repository.get_alert_sessions(alert_type="NamespaceTerminating")
        assert len(result["sessions"]) == 1
        assert result["sessions"][0].session_id == session1.session_id
    
    def test_get_alert_sessions_with_date_filters(self, repository):
        """Test getting alert sessions with date range filters."""
        # Create sessions with different timestamps
        now = datetime.now(timezone.utc)
        old_session = AlertSession(
            session_id="old-session",
            alert_id="old-alert",
            alert_data={},
            agent_type="TestAgent",
            alert_type="test",
            status="completed",
            started_at=now - timedelta(days=5),
            completed_at=now - timedelta(days=5)
        )
        
        new_session = AlertSession(
            session_id="new-session",
            alert_id="new-alert",
            alert_data={},
            agent_type="TestAgent",
            alert_type="test",
            status="completed",
            started_at=now - timedelta(hours=1),
            completed_at=now - timedelta(hours=1)
        )
        
        repository.create_alert_session(old_session)
        repository.create_alert_session(new_session)
        
        # Test start_date filter
        result = repository.get_alert_sessions(start_date=now - timedelta(days=2))
        assert len(result["sessions"]) == 1
        assert result["sessions"][0].session_id == new_session.session_id
        
        # Test end_date filter
        result = repository.get_alert_sessions(end_date=now - timedelta(days=2))
        assert len(result["sessions"]) == 1
        assert result["sessions"][0].session_id == old_session.session_id
    
    def test_get_alert_sessions_with_pagination(self, repository):
        """Test getting alert sessions with pagination."""
        # Create multiple sessions
        for i in range(5):
            session = AlertSession(
                session_id=f"session-{i}",
                alert_id=f"alert-{i}",
                alert_data={},
                agent_type="TestAgent",
                alert_type="test",
                status="completed",
                started_at=datetime.now(timezone.utc) - timedelta(minutes=i)
            )
            repository.create_alert_session(session)
        
        # Test first page
        result = repository.get_alert_sessions(page=1, page_size=2)
        assert len(result["sessions"]) == 2
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["page_size"] == 2
        assert result["pagination"]["total_items"] == 5
        assert result["pagination"]["total_pages"] == 3
        
        # Test second page
        result = repository.get_alert_sessions(page=2, page_size=2)
        assert len(result["sessions"]) == 2
        assert result["pagination"]["page"] == 2
        
        # Test last page
        result = repository.get_alert_sessions(page=3, page_size=2)
        assert len(result["sessions"]) == 1
        assert result["pagination"]["page"] == 3
    
    def test_get_session_timeline_chronological_order(self, repository, sample_alert_session):
        """Test session timeline reconstruction with chronological ordering."""
        # Create session
        repository.create_alert_session(sample_alert_session)
        
        # Create interactions and communications with specific timestamps
        base_time = datetime.now(timezone.utc)
        
        llm1 = LLMInteraction(
            interaction_id="llm-1",
            session_id=sample_alert_session.session_id,
            prompt_text="First prompt",
            response_text="First response",
            model_used="gpt-4",
            timestamp=base_time,
            step_description="First LLM interaction"
        )
        
        mcp1 = MCPCommunication(
            communication_id="mcp-1",
            session_id=sample_alert_session.session_id,
            server_name="kubernetes-server",
            communication_type="tool_call",
            tool_name="kubectl_get",
            timestamp=base_time + timedelta(seconds=1),
            step_description="First MCP call",
            success=True
        )
        
        llm2 = LLMInteraction(
            interaction_id="llm-2",
            session_id=sample_alert_session.session_id,
            prompt_text="Second prompt",
            response_text="Second response",
            model_used="gpt-4",
            timestamp=base_time + timedelta(seconds=2),
            step_description="Second LLM interaction"
        )
        
        repository.create_llm_interaction(llm1)
        repository.create_mcp_communication(mcp1)
        repository.create_llm_interaction(llm2)
        
        # Get timeline
        timeline = repository.get_session_timeline(sample_alert_session.session_id)
        
        assert timeline is not None
        assert "session" in timeline
        assert "chronological_timeline" in timeline
        assert "llm_interactions" in timeline
        assert "mcp_communications" in timeline
        
        # Verify chronological order
        events = timeline["chronological_timeline"]
        assert len(events) == 3
        assert events[0]["type"] == "llm_interaction"
        assert events[1]["type"] == "mcp_communication"
        assert events[2]["type"] == "llm_interaction"
        
        # Verify timeline is ordered by timestamp
        for i in range(len(events) - 1):
            assert events[i]["timestamp"] <= events[i + 1]["timestamp"]
    
    def test_get_active_sessions(self, repository):
        """Test getting active sessions."""
        # Create active and completed sessions
        active_session = AlertSession(
            session_id="active-session",
            alert_id="active-alert",
            alert_data={},
            agent_type="TestAgent",
            alert_type="test",
            status="in_progress",
            started_at=datetime.now(timezone.utc)
        )
        
        completed_session = AlertSession(
            session_id="completed-session",
            alert_id="completed-alert",
            alert_data={},
            agent_type="TestAgent",
            alert_type="test",
            status="completed",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc)
        )
        
        repository.create_alert_session(active_session)
        repository.create_alert_session(completed_session)
        
        # Get active sessions
        active_sessions = repository.get_active_sessions()
        
        assert len(active_sessions) == 1
        assert active_sessions[0].session_id == active_session.session_id
        assert active_sessions[0].status == "in_progress"
    
    def test_cleanup_old_sessions(self, repository):
        """Test cleanup of old sessions."""
        # Create old and new sessions
        now = datetime.now(timezone.utc)
        
        old_session = AlertSession(
            session_id="old-session",
            alert_id="old-alert",
            alert_data={},
            agent_type="TestAgent",
            alert_type="test",
            status="completed",
            started_at=now - timedelta(days=100),
            completed_at=now - timedelta(days=100)
        )
        
        new_session = AlertSession(
            session_id="new-session",
            alert_id="new-alert",
            alert_data={},
            agent_type="TestAgent",
            alert_type="test",
            status="completed",
            started_at=now - timedelta(days=1),
            completed_at=now - timedelta(days=1)
        )
        
        repository.create_alert_session(old_session)
        repository.create_alert_session(new_session)
        
        # Cleanup sessions older than 90 days
        cleaned_count = repository.cleanup_old_sessions(retention_days=90)
        
        assert cleaned_count == 1
        
        # Verify old session was deleted and new session remains
        assert repository.get_alert_session("old-session") is None
        assert repository.get_alert_session("new-session") is not None
    
    def test_complex_filter_combinations(self, repository):
        """Test complex filter combinations with AND logic."""
        # Create sessions with various attributes
        now = datetime.now(timezone.utc)
        
        sessions_data = [
            ("session-1", "NamespaceTerminating", "KubernetesAgent", "completed", now - timedelta(hours=1)),
            ("session-2", "NamespaceTerminating", "KubernetesAgent", "in_progress", now - timedelta(hours=2)),
            ("session-3", "HighCPU", "KubernetesAgent", "completed", now - timedelta(hours=3)),
            ("session-4", "NamespaceTerminating", "GenericAgent", "completed", now - timedelta(hours=4)),
        ]
        
        for session_id, alert_type, agent_type, status, started_at in sessions_data:
            session = AlertSession(
                session_id=session_id,
                alert_id=f"alert-{session_id}",
                alert_data={"alert_type": alert_type},
                agent_type=agent_type,
                alert_type=alert_type,
                status=status,
                started_at=started_at,
                completed_at=started_at + timedelta(minutes=10) if status == "completed" else None
            )
            repository.create_alert_session(session)
        
        # Test alert_type + status combination
        result = repository.get_alert_sessions(
            alert_type="NamespaceTerminating",
            status="completed"
        )
        assert len(result["sessions"]) == 2  # session-1 and session-4
        
        # Test alert_type + status + agent_type combination
        result = repository.get_alert_sessions(
            alert_type="NamespaceTerminating",
            status="completed",
            agent_type="KubernetesAgent"
        )
        assert len(result["sessions"]) == 1  # only session-1
        assert result["sessions"][0].session_id == "session-1"
        
        # Test agent_type + status + time_range combination
        result = repository.get_alert_sessions(
            agent_type="KubernetesAgent",
            status="completed",
            start_date=now - timedelta(hours=3.5)  # Should get session-1 and session-3
        )
        assert len(result["sessions"]) == 2
        session_ids = [s.session_id for s in result["sessions"]]
        assert "session-1" in session_ids
        assert "session-3" in session_ids


class TestHistoryRepositoryErrorHandling:
    """Test suite for HistoryRepository error handling scenarios."""
    
    @pytest.fixture
    def sample_alert_session(self):
        """Create sample AlertSession for testing."""
        return AlertSession(
            session_id="test-session-123",
            alert_id="alert-456",
            alert_data={
                "alert_type": "NamespaceTerminating",
                "environment": "production",
                "cluster": "k8s-prod",
                "namespace": "stuck-namespace"
            },
            agent_type="KubernetesAgent",
            alert_type="NamespaceTerminating",
            status="in_progress",
            started_at=datetime.now(timezone.utc),
            session_metadata={"test": "metadata"}
        )
    
    @pytest.fixture
    def repository_with_session_error(self):
        """Create repository with session that will raise errors."""
        mock_session = Mock()
        mock_session.exec.side_effect = Exception("Database error")
        mock_session.add.side_effect = Exception("Database error")
        mock_session.commit.side_effect = Exception("Database error")
        
        return HistoryRepository(mock_session)
    
    def test_create_alert_session_database_error(self, repository_with_session_error, sample_alert_session):
        """Test alert session creation with database error."""
        result = repository_with_session_error.create_alert_session(sample_alert_session)
        assert result is None
    
    def test_get_alert_sessions_database_error(self, repository_with_session_error):
        """Test getting alert sessions with database error."""
        result = repository_with_session_error.get_alert_sessions()
        
        # Should return empty result structure
        assert result["sessions"] == []
        assert result["pagination"]["total_items"] == 0
    
    def test_get_session_timeline_database_error(self, repository_with_session_error):
        """Test getting session timeline with database error."""
        result = repository_with_session_error.get_session_timeline("test-session")
        assert result is None
    
    def test_cleanup_old_sessions_database_error(self, repository_with_session_error):
        """Test cleanup old sessions with database error."""
        result = repository_with_session_error.cleanup_old_sessions(90)
        assert result == 0


class TestHistoryRepositoryPerformance:
    """Test suite for HistoryRepository performance scenarios."""
    
    @pytest.fixture
    def in_memory_engine(self):
        """Create in-memory SQLite engine for testing."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        SQLModel.metadata.create_all(engine)
        return engine
    
    @pytest.fixture
    def db_session(self, in_memory_engine):
        """Create database session for testing."""
        with Session(in_memory_engine) as session:
            yield session
    
    @pytest.fixture
    def repository(self, db_session):
        """Create HistoryRepository instance with test database session."""
        return HistoryRepository(db_session)
    
    @pytest.fixture
    def repository_with_large_dataset(self, repository):
        """Create repository with large dataset for performance testing."""
        # Create 100 sessions with interactions and communications
        now = datetime.now(timezone.utc)
        
        for i in range(100):
            session = AlertSession(
                session_id=f"perf-session-{i}",
                alert_id=f"perf-alert-{i}",
                alert_data={"alert_type": f"TestAlert{i % 5}"},
                agent_type="TestAgent",
                alert_type=f"TestAlert{i % 5}",
                status="completed" if i % 2 == 0 else "in_progress",
                started_at=now - timedelta(minutes=i),
                completed_at=now - timedelta(minutes=i-5) if i % 2 == 0 else None
            )
            repository.create_alert_session(session)
            
            # Add some interactions for every 10th session
            if i % 10 == 0:
                interaction = LLMInteraction(
                    interaction_id=f"perf-interaction-{i}",
                    session_id=session.session_id,
                    prompt_text=f"Prompt {i}",
                    response_text=f"Response {i}",
                    model_used="gpt-4",
                    timestamp=now - timedelta(minutes=i-1),
                    step_description=f"Interaction {i}"
                )
                repository.create_llm_interaction(interaction)
        
        return repository
    
    def test_pagination_performance_large_dataset(self, repository_with_large_dataset):
        """Test pagination performance with large dataset."""
        # Test that pagination works efficiently with large dataset
        result = repository_with_large_dataset.get_alert_sessions(page=1, page_size=10)
        
        assert len(result["sessions"]) == 10
        assert result["pagination"]["total_items"] == 100
        assert result["pagination"]["total_pages"] == 10
        
        # Test middle page
        result = repository_with_large_dataset.get_alert_sessions(page=5, page_size=10)
        assert len(result["sessions"]) == 10
        assert result["pagination"]["page"] == 5
    
    def test_filtering_performance_large_dataset(self, repository_with_large_dataset):
        """Test filtering performance with large dataset."""
        # Test status filter performance
        result = repository_with_large_dataset.get_alert_sessions(status="completed", page_size=100)
        assert len(result["sessions"]) == 50  # Half of the sessions
        
        # Test combined filters performance
        result = repository_with_large_dataset.get_alert_sessions(
            status="completed",
            alert_type="TestAlert0"
        )
        # Should get completed sessions with TestAlert0 (sessions 0, 10, 20, etc.)
        assert len(result["sessions"]) == 10 