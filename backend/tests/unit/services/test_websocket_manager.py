"""
Unit tests for WebSocketManager - Manages WebSocket connections for real-time updates.

Tests basic WebSocket management for alerts, dashboard integration through
delegation, advanced broadcasting features, error handling, and cleanup logic.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch, call

from tarsy.services.websocket_manager import WebSocketManager
from tarsy.models.alert import ProcessingStatus


@pytest.mark.unit
class TestWebSocketManagerInitialization:
    """Test WebSocketManager initialization and basic setup."""
    
    def test_initialization(self):
        """Test WebSocketManager initialization with proper dependencies."""
        manager = WebSocketManager()
        
        # Should initialize with empty connections
        assert isinstance(manager.active_connections, dict)
        assert len(manager.active_connections) == 0
        
        # Should create dashboard connection manager
        assert manager.dashboard_manager is not None
        assert hasattr(manager.dashboard_manager, 'connect')
        assert hasattr(manager.dashboard_manager, 'disconnect')
        assert hasattr(manager.dashboard_manager, 'broadcast_to_channel')
    
    def test_initialization_creates_dashboard_manager(self):
        """Test that initialization creates DashboardConnectionManager instance."""
        with patch('tarsy.services.websocket_manager.DashboardConnectionManager') as mock_dcm:
            mock_instance = Mock()
            mock_dcm.return_value = mock_instance
            
            manager = WebSocketManager()
            
            # Should create DashboardConnectionManager
            mock_dcm.assert_called_once()
            assert manager.dashboard_manager == mock_instance
    
    def test_datetime_serializer_with_datetime(self):
        """Test datetime serializer with datetime objects."""
        manager = WebSocketManager()
        test_datetime = datetime(2024, 1, 1, 12, 0, 0)
        
        result = manager._datetime_serializer(test_datetime)
        assert result == "2024-01-01T12:00:00"
    
    def test_datetime_serializer_with_non_datetime(self):
        """Test datetime serializer with non-datetime objects raises TypeError."""
        manager = WebSocketManager()
        
        with pytest.raises(TypeError, match="Object of type .* is not JSON serializable"):
            manager._datetime_serializer("not a datetime")
        
        with pytest.raises(TypeError):
            manager._datetime_serializer(123)
        
        with pytest.raises(TypeError):
            manager._datetime_serializer({"key": "value"})


@pytest.mark.unit 
class TestBasicWebSocketManagement:
    """Test basic WebSocket connection management for alerts."""
    
    @pytest.fixture
    def manager(self):
        """Create WebSocketManager instance for testing."""
        return WebSocketManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket for testing."""
        websocket = AsyncMock()
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        return websocket
    
    async def test_connect_new_alert(self, manager, mock_websocket):
        """Test connecting WebSocket for new alert."""
        alert_id = "alert-123"
        
        await manager.connect(mock_websocket, alert_id)
        
        # Should accept the WebSocket
        mock_websocket.accept.assert_called_once()
        
        # Should store connection
        assert alert_id in manager.active_connections
        assert mock_websocket in manager.active_connections[alert_id]
        assert len(manager.active_connections[alert_id]) == 1
    
    async def test_connect_existing_alert(self, manager, mock_websocket):
        """Test connecting multiple WebSockets for same alert."""
        alert_id = "alert-123"
        mock_websocket2 = AsyncMock()
        
        # Connect first WebSocket
        await manager.connect(mock_websocket, alert_id)
        await manager.connect(mock_websocket2, alert_id)
        
        # Both should be accepted
        mock_websocket.accept.assert_called_once()
        mock_websocket2.accept.assert_called_once()
        
        # Both should be stored
        assert len(manager.active_connections[alert_id]) == 2
        assert mock_websocket in manager.active_connections[alert_id]
        assert mock_websocket2 in manager.active_connections[alert_id]
    
    def test_disconnect_existing_connection(self, manager, mock_websocket):
        """Test disconnecting existing WebSocket connection."""
        alert_id = "alert-123"
        
        # Manually add connection
        manager.active_connections[alert_id] = [mock_websocket]
        
        manager.disconnect(mock_websocket, alert_id)
        
        # Should remove the connection but keep the alert_id entry if empty
        assert alert_id not in manager.active_connections
    
    def test_disconnect_multiple_connections(self, manager):
        """Test disconnecting one of multiple connections for same alert."""
        alert_id = "alert-123"
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        
        # Manually add connections
        manager.active_connections[alert_id] = [mock_websocket1, mock_websocket2]
        
        manager.disconnect(mock_websocket1, alert_id)
        
        # Should remove only the specified connection
        assert alert_id in manager.active_connections
        assert mock_websocket1 not in manager.active_connections[alert_id]
        assert mock_websocket2 in manager.active_connections[alert_id]
        assert len(manager.active_connections[alert_id]) == 1
    
    def test_disconnect_last_connection_cleans_up(self, manager, mock_websocket):
        """Test that disconnecting last connection cleans up alert entry."""
        alert_id = "alert-123"
        
        # Manually add connection
        manager.active_connections[alert_id] = [mock_websocket]
        
        manager.disconnect(mock_websocket, alert_id)
        
        # Should remove the entire alert_id entry
        assert alert_id not in manager.active_connections
    
    def test_disconnect_non_existing_alert(self, manager, mock_websocket):
        """Test disconnecting from non-existing alert does nothing."""
        # Should not raise exception
        manager.disconnect(mock_websocket, "non-existent-alert")
        
        # Should not create new entries
        assert len(manager.active_connections) == 0
    
    def test_disconnect_non_existing_websocket(self, manager):
        """Test disconnecting non-existing WebSocket from existing alert."""
        alert_id = "alert-123"
        existing_websocket = AsyncMock()
        non_existing_websocket = AsyncMock()
        
        # Manually add one connection
        manager.active_connections[alert_id] = [existing_websocket]
        
        # Try to disconnect non-existing WebSocket
        manager.disconnect(non_existing_websocket, alert_id)
        
        # Should not affect existing connection
        assert len(manager.active_connections[alert_id]) == 1
        assert existing_websocket in manager.active_connections[alert_id]


@pytest.mark.unit
class TestStatusUpdateSending:
    """Test sending status updates to alert WebSocket connections."""
    
    @pytest.fixture
    def manager(self):
        """Create WebSocketManager instance for testing."""
        return WebSocketManager()
    
    @pytest.fixture
    def mock_status(self):
        """Create mock ProcessingStatus for testing."""
        status = Mock(spec=ProcessingStatus)
        status.model_dump.return_value = {
            "progress": 50,
            "status": "processing",
            "message": "Test message",
            "timestamp": datetime.now()
        }
        return status
    
    async def test_send_status_update_no_connections(self, manager, mock_status):
        """Test sending status update when no connections exist for alert."""
        alert_id = "non-existent-alert"
        
        # Should not raise exception
        await manager.send_status_update(alert_id, mock_status)
        
        # No WebSocket calls should be made
        assert True  # Test passes if no exception is raised
    
    async def test_send_status_update_single_connection(self, manager, mock_status):
        """Test sending status update to single connection."""
        alert_id = "alert-123"
        mock_websocket = AsyncMock()
        
        # Setup connection
        manager.active_connections[alert_id] = [mock_websocket]
        
        await manager.send_status_update(alert_id, mock_status)
        
        # Should send message to WebSocket
        mock_websocket.send_text.assert_called_once()
        
        # Verify message content
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)
        
        assert message["type"] == "status_update"
        assert "data" in message
        assert message["data"]["progress"] == 50
        assert message["data"]["status"] == "processing"
    
    async def test_send_status_update_multiple_connections(self, manager, mock_status):
        """Test sending status update to multiple connections."""
        alert_id = "alert-123"
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        
        # Setup connections
        manager.active_connections[alert_id] = [mock_websocket1, mock_websocket2]
        
        await manager.send_status_update(alert_id, mock_status)
        
        # Should send to both WebSockets
        mock_websocket1.send_text.assert_called_once()
        mock_websocket2.send_text.assert_called_once()
        
        # Both should receive same message
        call1 = mock_websocket1.send_text.call_args[0][0]
        call2 = mock_websocket2.send_text.call_args[0][0]
        assert call1 == call2
    
    async def test_send_status_update_broken_connection(self, manager, mock_status):
        """Test handling broken connection during status update."""
        alert_id = "alert-123"
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        
        # Make one WebSocket fail
        mock_websocket1.send_text.side_effect = Exception("Connection broken")
        
        # Setup connections
        manager.active_connections[alert_id] = [mock_websocket1, mock_websocket2]
        
        await manager.send_status_update(alert_id, mock_status)
        
        # Should attempt to send to both
        mock_websocket1.send_text.assert_called_once()
        mock_websocket2.send_text.assert_called_once()
        
        # Should remove broken connection
        assert mock_websocket1 not in manager.active_connections[alert_id]
        assert mock_websocket2 in manager.active_connections[alert_id]
    
    async def test_send_status_update_all_connections_broken(self, manager, mock_status):
        """Test when all connections are broken during status update."""
        alert_id = "alert-123"
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        
        # Make all WebSockets fail
        mock_websocket1.send_text.side_effect = Exception("Connection broken")
        mock_websocket2.send_text.side_effect = Exception("Connection broken")
        
        # Setup connections
        manager.active_connections[alert_id] = [mock_websocket1, mock_websocket2]
        
        await manager.send_status_update(alert_id, mock_status)
        
        # Should clean up the alert entry
        assert alert_id not in manager.active_connections
    
    async def test_send_status_update_datetime_serialization(self, manager):
        """Test that datetime objects in status are properly serialized."""
        alert_id = "alert-123"
        mock_websocket = AsyncMock()
        
        # Create status with datetime
        status = Mock(spec=ProcessingStatus)
        test_datetime = datetime(2024, 1, 1, 12, 0, 0)
        status.model_dump.return_value = {
            "timestamp": test_datetime,
            "status": "processing"
        }
        
        # Setup connection
        manager.active_connections[alert_id] = [mock_websocket]
        
        await manager.send_status_update(alert_id, status)
        
        # Verify datetime was serialized
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)
        
        assert message["data"]["timestamp"] == "2024-01-01T12:00:00"


@pytest.mark.unit
class TestCustomMessageSending:
    """Test sending custom messages to alert WebSocket connections."""
    
    @pytest.fixture
    def manager(self):
        """Create WebSocketManager instance for testing."""
        return WebSocketManager()
    
    async def test_send_message_no_connections(self, manager):
        """Test sending message when no connections exist for alert."""
        alert_id = "non-existent-alert"
        message = {"type": "custom", "data": "test"}
        
        # Should not raise exception
        await manager.send_message(alert_id, message)
        
        # Test passes if no exception is raised
        assert True
    
    async def test_send_message_single_connection(self, manager):
        """Test sending custom message to single connection."""
        alert_id = "alert-123"
        mock_websocket = AsyncMock()
        custom_message = {"type": "custom", "data": "test message"}
        
        # Setup connection
        manager.active_connections[alert_id] = [mock_websocket]
        
        await manager.send_message(alert_id, custom_message)
        
        # Should send message to WebSocket
        mock_websocket.send_text.assert_called_once()
        
        # Verify message content
        call_args = mock_websocket.send_text.call_args[0][0]
        received_message = json.loads(call_args)
        
        assert received_message == custom_message
    
    async def test_send_message_with_datetime(self, manager):
        """Test sending message with datetime objects."""
        alert_id = "alert-123"
        mock_websocket = AsyncMock()
        test_datetime = datetime(2024, 1, 1, 12, 0, 0)
        custom_message = {
            "type": "custom",
            "timestamp": test_datetime,
            "data": "test"
        }
        
        # Setup connection
        manager.active_connections[alert_id] = [mock_websocket]
        
        await manager.send_message(alert_id, custom_message)
        
        # Verify datetime was serialized
        call_args = mock_websocket.send_text.call_args[0][0]
        received_message = json.loads(call_args)
        
        assert received_message["timestamp"] == "2024-01-01T12:00:00"
    
    async def test_send_message_broken_connection_cleanup(self, manager):
        """Test that broken connections are cleaned up during message sending."""
        alert_id = "alert-123"
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        custom_message = {"type": "test", "data": "message"}
        
        # Make one WebSocket fail
        mock_websocket1.send_text.side_effect = Exception("Connection broken")
        
        # Setup connections
        manager.active_connections[alert_id] = [mock_websocket1, mock_websocket2]
        
        await manager.send_message(alert_id, custom_message)
        
        # Should remove broken connection
        assert mock_websocket1 not in manager.active_connections[alert_id]
        assert mock_websocket2 in manager.active_connections[alert_id]


@pytest.mark.unit
class TestDashboardIntegration:
    """Test dashboard WebSocket integration through DashboardConnectionManager."""
    
    @pytest.fixture
    def manager(self):
        """Create WebSocketManager with mocked dashboard manager."""
        manager = WebSocketManager()
        manager.dashboard_manager = Mock()
        manager.dashboard_manager.connect = AsyncMock()
        manager.dashboard_manager.disconnect = Mock()
        manager.dashboard_manager.handle_subscription_message = AsyncMock()
        manager.dashboard_manager.broadcast_to_channel = AsyncMock()
        manager.dashboard_manager.get_connection_stats = Mock()
        manager.dashboard_manager.initialize_broadcaster = AsyncMock()
        manager.dashboard_manager.shutdown_broadcaster = AsyncMock()
        manager.dashboard_manager.broadcaster = None
        return manager
    
    async def test_connect_dashboard(self, manager):
        """Test connecting dashboard WebSocket delegates to dashboard manager."""
        mock_websocket = AsyncMock()
        user_id = "user-123"
        
        await manager.connect_dashboard(mock_websocket, user_id)
        
        manager.dashboard_manager.connect.assert_called_once_with(mock_websocket, user_id)
    
    def test_disconnect_dashboard(self, manager):
        """Test disconnecting dashboard WebSocket delegates to dashboard manager."""
        user_id = "user-123"
        
        manager.disconnect_dashboard(user_id)
        
        manager.dashboard_manager.disconnect.assert_called_once_with(user_id)
    
    async def test_handle_dashboard_message(self, manager):
        """Test handling dashboard message delegates to dashboard manager."""
        user_id = "user-123"
        message = {"type": "subscribe", "channel": "test-channel"}
        
        await manager.handle_dashboard_message(user_id, message)
        
        manager.dashboard_manager.handle_subscription_message.assert_called_once_with(
            user_id, message
        )
    
    async def test_broadcast_dashboard_update(self, manager):
        """Test broadcasting dashboard update delegates to dashboard manager."""
        channel = "test-channel"
        message = {"type": "update", "data": "test"}
        exclude_users = {"user-1", "user-2"}
        
        manager.dashboard_manager.broadcast_to_channel.return_value = 5
        
        result = await manager.broadcast_dashboard_update(channel, message, exclude_users)
        
        manager.dashboard_manager.broadcast_to_channel.assert_called_once_with(
            channel, message, exclude_users
        )
        assert result == 5
    
    async def test_broadcast_dashboard_update_default_exclude(self, manager):
        """Test broadcasting dashboard update with default exclude_users."""
        channel = "test-channel"
        message = {"type": "update", "data": "test"}
        
        manager.dashboard_manager.broadcast_to_channel.return_value = 3
        
        result = await manager.broadcast_dashboard_update(channel, message)
        
        manager.dashboard_manager.broadcast_to_channel.assert_called_once_with(
            channel, message, None
        )
        assert result == 3
    
    def test_get_dashboard_stats_without_broadcaster(self, manager):
        """Test getting dashboard stats when broadcaster is None."""
        expected_stats = {
            "active_connections": 5,
            "total_subscriptions": 10,
            "active_channels": 3
        }
        manager.dashboard_manager.get_connection_stats.return_value = expected_stats
        manager.dashboard_manager.broadcaster = None
        
        result = manager.get_dashboard_stats()
        
        assert result == expected_stats
        manager.dashboard_manager.get_connection_stats.assert_called_once()
    
    def test_get_dashboard_stats_with_broadcaster(self, manager):
        """Test getting dashboard stats when broadcaster exists."""
        connection_stats = {
            "active_connections": 5,
            "total_subscriptions": 10
        }
        broadcaster_stats = {
            "messages_sent": 100,
            "broadcasts_sent": 25
        }
        
        manager.dashboard_manager.get_connection_stats.return_value = connection_stats
        mock_broadcaster = Mock()
        mock_broadcaster.get_broadcast_stats.return_value = broadcaster_stats
        manager.dashboard_manager.broadcaster = mock_broadcaster
        
        result = manager.get_dashboard_stats()
        
        expected = {
            **connection_stats,
            "broadcaster": broadcaster_stats
        }
        assert result == expected
        mock_broadcaster.get_broadcast_stats.assert_called_once()
    
    async def test_initialize_dashboard_broadcaster(self, manager):
        """Test initializing dashboard broadcaster delegates to dashboard manager."""
        mock_broadcaster = Mock()
        manager.dashboard_manager.initialize_broadcaster.return_value = mock_broadcaster
        
        result = await manager.initialize_dashboard_broadcaster()
        
        manager.dashboard_manager.initialize_broadcaster.assert_called_once()
        assert result == mock_broadcaster
    
    async def test_shutdown_dashboard_broadcaster(self, manager):
        """Test shutting down dashboard broadcaster delegates to dashboard manager."""
        await manager.shutdown_dashboard_broadcaster()
        
        manager.dashboard_manager.shutdown_broadcaster.assert_called_once()


@pytest.mark.unit
class TestAdvancedDashboardFeatures:
    """Test advanced dashboard broadcasting features."""
    
    @pytest.fixture
    def manager(self):
        """Create WebSocketManager with mocked dashboard and broadcaster."""
        manager = WebSocketManager()
        manager.dashboard_manager = Mock()
        
        # Mock broadcaster
        mock_broadcaster = Mock()
        mock_broadcaster.broadcast_dashboard_update = AsyncMock()
        mock_broadcaster.broadcast_session_update = AsyncMock()
        mock_broadcaster.broadcast_system_health_update = AsyncMock()
        manager.dashboard_manager.broadcaster = mock_broadcaster
        
        return manager
    
    async def test_broadcast_dashboard_update_advanced_with_broadcaster(self, manager):
        """Test advanced dashboard update broadcasting when broadcaster exists."""
        data = {"type": "update", "content": "test"}
        exclude_users = {"user-1"}
        
        manager.dashboard_manager.broadcaster.broadcast_dashboard_update.return_value = 8
        
        result = await manager.broadcast_dashboard_update_advanced(data, exclude_users)
        
        manager.dashboard_manager.broadcaster.broadcast_dashboard_update.assert_called_once_with(
            data, exclude_users
        )
        assert result == 8
    
    async def test_broadcast_dashboard_update_advanced_without_broadcaster(self, manager):
        """Test advanced dashboard update when broadcaster is None."""
        manager.dashboard_manager.broadcaster = None
        data = {"type": "update", "content": "test"}
        
        result = await manager.broadcast_dashboard_update_advanced(data)
        
        assert result == 0
    
    async def test_broadcast_session_update_advanced_with_broadcaster(self, manager):
        """Test advanced session update broadcasting when broadcaster exists."""
        session_id = "session-123"
        data = {"status": "active", "progress": 50}
        exclude_users = {"user-2"}
        
        manager.dashboard_manager.broadcaster.broadcast_session_update.return_value = 6
        
        result = await manager.broadcast_session_update_advanced(session_id, data, exclude_users)
        
        manager.dashboard_manager.broadcaster.broadcast_session_update.assert_called_once_with(
            session_id, data, exclude_users
        )
        assert result == 6
    
    async def test_broadcast_session_update_advanced_without_broadcaster(self, manager):
        """Test advanced session update when broadcaster is None."""
        manager.dashboard_manager.broadcaster = None
        session_id = "session-123"
        data = {"status": "active"}
        
        result = await manager.broadcast_session_update_advanced(session_id, data)
        
        assert result == 0
    
    async def test_broadcast_system_health_advanced_with_broadcaster(self, manager):
        """Test advanced system health broadcasting when broadcaster exists."""
        status = "healthy"
        services = {"api": "running", "database": "running"}
        exclude_users = {"admin-1"}
        
        manager.dashboard_manager.broadcaster.broadcast_system_health_update.return_value = 12
        
        result = await manager.broadcast_system_health_advanced(status, services, exclude_users)
        
        manager.dashboard_manager.broadcaster.broadcast_system_health_update.assert_called_once_with(
            status, services, exclude_users
        )
        assert result == 12
    
    async def test_broadcast_system_health_advanced_without_broadcaster(self, manager):
        """Test advanced system health when broadcaster is None."""
        manager.dashboard_manager.broadcaster = None
        status = "degraded"
        services = {"api": "slow"}
        
        result = await manager.broadcast_system_health_advanced(status, services)
        
        assert result == 0
    
    async def test_advanced_features_default_exclude_users(self, manager):
        """Test that advanced features handle default exclude_users correctly."""
        # Test dashboard update
        result1 = await manager.broadcast_dashboard_update_advanced({"test": "data"})
        manager.dashboard_manager.broadcaster.broadcast_dashboard_update.assert_called_with(
            {"test": "data"}, None
        )
        
        # Test session update
        result2 = await manager.broadcast_session_update_advanced("session-1", {"data": "test"})
        manager.dashboard_manager.broadcaster.broadcast_session_update.assert_called_with(
            "session-1", {"data": "test"}, None
        )
        
        # Test system health
        result3 = await manager.broadcast_system_health_advanced("ok", {"service": "up"})
        manager.dashboard_manager.broadcaster.broadcast_system_health_update.assert_called_with(
            "ok", {"service": "up"}, None
        )


@pytest.mark.unit
class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases in WebSocketManager."""
    
    @pytest.fixture
    def manager(self):
        """Create WebSocketManager instance for testing."""
        return WebSocketManager()
    
    def test_empty_active_connections_operations(self, manager):
        """Test operations on empty active_connections dict."""
        # Disconnect from non-existing alert
        manager.disconnect(AsyncMock(), "non-existent")
        assert len(manager.active_connections) == 0
        
        # Status update to non-existing alert should not crash
        # (tested in async context in other test class)
    
    def test_multiple_disconnects_same_websocket(self, manager):
        """Test multiple disconnects of same WebSocket."""
        alert_id = "alert-123"
        mock_websocket = AsyncMock()
        
        # Add connection
        manager.active_connections[alert_id] = [mock_websocket]
        
        # Disconnect multiple times
        manager.disconnect(mock_websocket, alert_id)
        manager.disconnect(mock_websocket, alert_id)  # Second disconnect
        
        # Should not cause errors
        assert alert_id not in manager.active_connections
    
    async def test_send_status_update_json_serialization_error(self, manager):
        """Test handling JSON serialization errors in status updates."""
        alert_id = "alert-123"
        mock_websocket = AsyncMock()
        
        # Create status that will cause serialization error
        bad_status = Mock(spec=ProcessingStatus)
        bad_status.model_dump.return_value = {
            "data": object()  # Non-serializable object
        }
        
        manager.active_connections[alert_id] = [mock_websocket]
        
        # Should handle serialization error gracefully
        with pytest.raises(TypeError):
            await manager.send_status_update(alert_id, bad_status)
    
    async def test_dashboard_methods_with_none_dashboard_manager(self):
        """Test dashboard methods when dashboard_manager is None."""
        # This is a pathological case that shouldn't happen in normal operation
        # but testing for robustness
        manager = WebSocketManager()
        manager.dashboard_manager = None
        
        with pytest.raises(AttributeError):
            await manager.connect_dashboard(AsyncMock(), "user-1")
    
    def test_get_dashboard_stats_with_none_dashboard_manager(self):
        """Test get_dashboard_stats when dashboard_manager is None."""
        manager = WebSocketManager()
        manager.dashboard_manager = None
        
        with pytest.raises(AttributeError):
            manager.get_dashboard_stats()
    
    async def test_concurrent_connection_modifications(self, manager):
        """Test that concurrent connection modifications are handled safely."""
        alert_id = "alert-123"
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        
        # Add connections
        await manager.connect(mock_websocket1, alert_id)
        await manager.connect(mock_websocket2, alert_id)
        
        # Simulate concurrent disconnect and status update
        manager.disconnect(mock_websocket1, alert_id)
        
        # Status update should still work with remaining connection
        status = Mock(spec=ProcessingStatus)
        status.model_dump.return_value = {"status": "test"}
        
        await manager.send_status_update(alert_id, status)
        
        # Should not crash and should send to remaining connection
        mock_websocket2.send_text.assert_called_once()
    
    def test_active_connections_structure_integrity(self, manager):
        """Test that active_connections maintains proper structure."""
        alert_id = "alert-123"
        mock_websocket = AsyncMock()
        
        # Initially empty
        assert isinstance(manager.active_connections, dict)
        
        # After connect (async, so manually simulate)
        manager.active_connections[alert_id] = [mock_websocket]
        assert isinstance(manager.active_connections[alert_id], list)
        assert mock_websocket in manager.active_connections[alert_id]
        
        # After disconnect
        manager.disconnect(mock_websocket, alert_id)
        assert alert_id not in manager.active_connections


@pytest.mark.unit
class TestIntegrationScenarios:
    """Test integration scenarios combining multiple WebSocketManager features."""
    
    @pytest.fixture
    def manager(self):
        """Create WebSocketManager with partially mocked dashboard manager."""
        manager = WebSocketManager()
        manager.dashboard_manager = Mock()
        manager.dashboard_manager.connect = AsyncMock()
        manager.dashboard_manager.disconnect = Mock()
        manager.dashboard_manager.broadcast_to_channel = AsyncMock(return_value=3)
        manager.dashboard_manager.get_connection_stats = Mock(return_value={"connections": 5})
        manager.dashboard_manager.broadcaster = None
        return manager
    
    async def test_mixed_alert_and_dashboard_connections(self, manager):
        """Test handling both alert and dashboard connections simultaneously."""
        # Alert connections
        alert_websocket1 = AsyncMock()
        alert_websocket2 = AsyncMock()
        await manager.connect(alert_websocket1, "alert-1")
        await manager.connect(alert_websocket2, "alert-2")
        
        # Dashboard connections
        dashboard_websocket1 = AsyncMock()
        dashboard_websocket2 = AsyncMock()
        await manager.connect_dashboard(dashboard_websocket1, "user-1")
        await manager.connect_dashboard(dashboard_websocket2, "user-2")
        
        # Verify both types of connections work
        assert len(manager.active_connections) == 2
        assert "alert-1" in manager.active_connections
        assert "alert-2" in manager.active_connections
        
        # Dashboard connections should be delegated
        assert manager.dashboard_manager.connect.call_count == 2
    
    async def test_broadcast_while_sending_status_updates(self, manager):
        """Test broadcasting dashboard updates while sending alert status updates."""
        # Setup alert connection
        alert_websocket = AsyncMock()
        await manager.connect(alert_websocket, "alert-1")
        
        # Send status update
        status = Mock(spec=ProcessingStatus)
        status.model_dump.return_value = {"status": "processing"}
        await manager.send_status_update("alert-1", status)
        
        # Send dashboard broadcast
        await manager.broadcast_dashboard_update("test-channel", {"data": "test"})
        
        # Both should work independently
        alert_websocket.send_text.assert_called_once()
        manager.dashboard_manager.broadcast_to_channel.assert_called_once()
    
    async def test_cleanup_during_active_operations(self, manager):
        """Test cleanup operations during active WebSocket operations."""
        alert_id = "alert-123"
        good_websocket = AsyncMock()
        bad_websocket = AsyncMock()
        bad_websocket.send_text.side_effect = Exception("Connection broken")
        
        # Setup connections
        manager.active_connections[alert_id] = [good_websocket, bad_websocket]
        
        # Send status update (should clean up broken connection)
        status = Mock(spec=ProcessingStatus)
        status.model_dump.return_value = {"status": "test"}
        await manager.send_status_update(alert_id, status)
        
        # Verify cleanup
        assert good_websocket in manager.active_connections[alert_id]
        assert bad_websocket not in manager.active_connections[alert_id]
        assert len(manager.active_connections[alert_id]) == 1
    
    async def test_dashboard_features_interaction(self, manager):
        """Test interaction between different dashboard features."""
        # Setup broadcaster
        mock_broadcaster = Mock()
        mock_broadcaster.broadcast_dashboard_update = AsyncMock(return_value=5)
        manager.dashboard_manager.broadcaster = mock_broadcaster
        
        # Use both basic and advanced dashboard features
        await manager.broadcast_dashboard_update("basic-channel", {"type": "basic"})
        await manager.broadcast_dashboard_update_advanced({"type": "advanced"})
        
        # Basic should use dashboard_manager
        manager.dashboard_manager.broadcast_to_channel.assert_called_once()
        
        # Advanced should use broadcaster
        mock_broadcaster.broadcast_dashboard_update.assert_called_once()
    
    def test_stats_aggregation_from_components(self, manager):
        """Test that stats are properly aggregated from different components."""
        # Mock dashboard manager stats
        dashboard_stats = {
            "active_connections": 10,
            "total_subscriptions": 25
        }
        manager.dashboard_manager.get_connection_stats.return_value = dashboard_stats
        
        # Mock broadcaster stats
        broadcaster_stats = {
            "messages_sent": 100,
            "broadcasts_sent": 20
        }
        mock_broadcaster = Mock()
        mock_broadcaster.get_broadcast_stats.return_value = broadcaster_stats
        manager.dashboard_manager.broadcaster = mock_broadcaster
        
        # Get aggregated stats
        stats = manager.get_dashboard_stats()
        
        # Should include both dashboard and broadcaster stats
        assert stats["active_connections"] == 10
        assert stats["total_subscriptions"] == 25
        assert stats["broadcaster"]["messages_sent"] == 100
        assert stats["broadcaster"]["broadcasts_sent"] == 20 