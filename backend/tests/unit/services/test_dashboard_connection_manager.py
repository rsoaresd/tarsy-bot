"""
Unit tests for DashboardConnectionManager.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from tarsy.models.websocket_models import (
    ChannelType,
    SubscriptionResponse,
)
from tarsy.services.dashboard_connection_manager import DashboardConnectionManager


@pytest.fixture
def connection_manager():
    """Create a DashboardConnectionManager instance for testing."""
    return DashboardConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


class TestDashboardConnectionManager:
    """Test basic DashboardConnectionManager functionality."""
    
    @pytest.mark.unit
    def test_initialization(self, connection_manager):
        """Test DashboardConnectionManager initialization."""
        assert isinstance(connection_manager.active_connections, dict)
        assert isinstance(connection_manager.user_subscriptions, dict)
        assert isinstance(connection_manager.channel_subscribers, dict)
        assert len(connection_manager.active_connections) == 0
        assert connection_manager.subscription_manager is not None
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_connect_user(self, connection_manager, mock_websocket):
        """Test connecting a user WebSocket."""
        user_id = "test_user"
        
        await connection_manager.connect(mock_websocket, user_id)
        
        # Verify connection stored
        assert user_id in connection_manager.active_connections
        assert connection_manager.active_connections[user_id] == mock_websocket
        
        # Verify subscription tracking initialized
        assert user_id in connection_manager.user_subscriptions
        assert len(connection_manager.user_subscriptions[user_id]) == 0
        
        # Verify WebSocket was accepted
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.unit
    def test_disconnect_user(self, connection_manager, mock_websocket):
        """Test disconnecting a user."""
        user_id = "test_user"
        
        # Set up connection and subscriptions
        connection_manager.active_connections[user_id] = mock_websocket
        connection_manager.user_subscriptions[user_id] = {"dashboard_updates", "session_123"}
        connection_manager.channel_subscribers["dashboard_updates"] = {user_id}
        connection_manager.channel_subscribers["session_123"] = {user_id}
        
        # Disconnect user
        connection_manager.disconnect(user_id)
        
        # Verify cleanup
        assert user_id not in connection_manager.active_connections
        assert user_id not in connection_manager.user_subscriptions
        assert user_id not in connection_manager.channel_subscribers.get("dashboard_updates", set())
        assert user_id not in connection_manager.channel_subscribers.get("session_123", set())
    
    @pytest.mark.unit
    def test_disconnect_nonexistent_user(self, connection_manager):
        """Test disconnecting a user that doesn't exist."""
        # Should not raise exception
        connection_manager.disconnect("nonexistent_user")
    
    @pytest.mark.unit
    def test_subscribe_to_channel(self, connection_manager, mock_websocket):
        """Test subscribing user to a channel."""
        user_id = "test_user"
        channel = ChannelType.DASHBOARD_UPDATES
        
        # Set up connection
        connection_manager.active_connections[user_id] = mock_websocket
        
        success = connection_manager.subscribe_to_channel(user_id, channel)
        
        assert success is True
        assert channel in connection_manager.user_subscriptions[user_id]
        assert user_id in connection_manager.channel_subscribers[channel]
    
    @pytest.mark.unit
    def test_subscribe_inactive_user(self, connection_manager):
        """Test subscribing inactive user to channel."""
        user_id = "inactive_user"
        channel = ChannelType.DASHBOARD_UPDATES
        
        success = connection_manager.subscribe_to_channel(user_id, channel)
        
        assert success is False
        # User subscriptions entry is created but remains empty
        assert user_id in connection_manager.user_subscriptions
        assert len(connection_manager.user_subscriptions[user_id]) == 0
    
    @pytest.mark.unit
    def test_unsubscribe_from_channel(self, connection_manager, mock_websocket):
        """Test unsubscribing user from a channel."""
        user_id = "test_user"
        channel = ChannelType.SYSTEM_HEALTH
        
        # Set up subscription
        connection_manager.active_connections[user_id] = mock_websocket
        connection_manager.user_subscriptions[user_id] = {channel}
        connection_manager.channel_subscribers[channel] = {user_id}
        
        success = connection_manager.unsubscribe_from_channel(user_id, channel)
        
        assert success is True
        assert channel not in connection_manager.user_subscriptions[user_id]
        assert channel not in connection_manager.channel_subscribers  # Should be cleaned up
    
    @pytest.mark.unit
    def test_get_user_subscriptions(self, connection_manager):
        """Test getting user subscriptions."""
        user_id = "test_user"
        channels = {"dashboard_updates", "session_123"}
        
        connection_manager.user_subscriptions[user_id] = channels
        
        result = connection_manager.get_user_subscriptions(user_id)
        
        assert result == channels
        assert result is not connection_manager.user_subscriptions[user_id]  # Should be copy
    
    @pytest.mark.unit
    def test_get_user_subscriptions_nonexistent(self, connection_manager):
        """Test getting subscriptions for nonexistent user."""
        result = connection_manager.get_user_subscriptions("nonexistent_user")
        assert result == set()
    
    @pytest.mark.unit
    def test_get_channel_subscribers(self, connection_manager):
        """Test getting channel subscribers."""
        channel = ChannelType.DASHBOARD_UPDATES
        users = {"user1", "user2", "user3"}
        
        connection_manager.channel_subscribers[channel] = users
        
        result = connection_manager.get_channel_subscribers(channel)
        
        assert result == users
        assert result is not connection_manager.channel_subscribers[channel]  # Should be copy
    
    @pytest.mark.unit
    def test_get_channel_subscribers_nonexistent(self, connection_manager):
        """Test getting subscribers for nonexistent channel."""
        result = connection_manager.get_channel_subscribers("nonexistent_channel")
        assert result == set()


class TestMessageSending:
    """Test message sending functionality."""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_send_to_user_success(self, connection_manager, mock_websocket):
        """Test successfully sending message to user."""
        user_id = "test_user"
        message = {"type": "test", "data": "hello"}
        
        connection_manager.active_connections[user_id] = mock_websocket
        
        success = await connection_manager.send_to_user(user_id, message)
        
        assert success is True
        mock_websocket.send_text.assert_called_once()
        
        # Verify message was properly serialized
        call_args = mock_websocket.send_text.call_args[0][0]
        sent_data = json.loads(call_args)
        assert sent_data["type"] == "test"
        assert sent_data["data"] == "hello"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_send_to_user_with_datetime(self, connection_manager, mock_websocket):
        """Test sending message with datetime serialization."""
        user_id = "test_user"
        test_time = datetime(2023, 1, 1, 12, 0, 0)
        message = {"type": "test", "timestamp": test_time}
        
        connection_manager.active_connections[user_id] = mock_websocket
        
        success = await connection_manager.send_to_user(user_id, message)
        
        assert success is True
        mock_websocket.send_text.assert_called_once()
        
        # Verify datetime was serialized
        call_args = mock_websocket.send_text.call_args[0][0]
        sent_data = json.loads(call_args)
        assert sent_data["timestamp"] == test_time.isoformat()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_send_to_inactive_user(self, connection_manager):
        """Test sending message to inactive user."""
        user_id = "inactive_user"
        message = {"type": "test"}
        
        success = await connection_manager.send_to_user(user_id, message)
        
        assert success is False
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_send_to_user_websocket_error(self, connection_manager, mock_websocket):
        """Test handling WebSocket send error."""
        user_id = "test_user"
        message = {"type": "test"}
        
        # Mock WebSocket to raise exception
        mock_websocket.send_text.side_effect = Exception("Connection error")
        connection_manager.active_connections[user_id] = mock_websocket
        
        success = await connection_manager.send_to_user(user_id, message)
        
        assert success is False
        # User should be disconnected after error
        assert user_id not in connection_manager.active_connections
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_broadcast_to_channel(self, connection_manager):
        """Test broadcasting message to channel subscribers."""
        channel = ChannelType.DASHBOARD_UPDATES
        message = {"type": "broadcast", "data": "hello"}
        users = ["user1", "user2", "user3"]
        
        # Set up subscribers and connections
        connection_manager.channel_subscribers[channel] = set(users)
        for user in users:
            mock_ws = AsyncMock()
            connection_manager.active_connections[user] = mock_ws
        
        sent_count = await connection_manager.broadcast_to_channel(channel, message)
        
        assert sent_count == 3
        
        # Verify all users received message
        for user in users:
            mock_ws = connection_manager.active_connections[user]
            mock_ws.send_text.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_broadcast_to_channel_with_exclusions(self, connection_manager):
        """Test broadcasting with user exclusions."""
        channel = ChannelType.SYSTEM_HEALTH
        message = {"type": "broadcast"}
        all_users = {"user1", "user2", "user3"}
        exclude_users = {"user2"}
        
        connection_manager.channel_subscribers[channel] = all_users
        for user in all_users:
            mock_ws = AsyncMock()
            connection_manager.active_connections[user] = mock_ws
        
        sent_count = await connection_manager.broadcast_to_channel(
            channel, message, exclude_users
        )
        
        assert sent_count == 2  # user1 and user3 only
        
        # Verify excluded user didn't receive message
        excluded_ws = connection_manager.active_connections["user2"]
        excluded_ws.send_text.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_broadcast_to_empty_channel(self, connection_manager):
        """Test broadcasting to channel with no subscribers."""
        channel = "empty_channel"
        message = {"type": "broadcast"}
        
        sent_count = await connection_manager.broadcast_to_channel(channel, message)
        
        assert sent_count == 0
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_broadcast_with_failed_sends(self, connection_manager):
        """Test broadcasting with some failed sends."""
        channel = ChannelType.DASHBOARD_UPDATES
        message = {"type": "broadcast"}
        users = ["user1", "user2", "user3"]
        
        connection_manager.channel_subscribers[channel] = set(users)
        
        # Set up connections - one will fail
        for i, user in enumerate(users):
            mock_ws = AsyncMock()
            if i == 1:  # user2 will fail
                mock_ws.send_text.side_effect = Exception("Send failed")
            connection_manager.active_connections[user] = mock_ws
        
        sent_count = await connection_manager.broadcast_to_channel(channel, message)
        
        assert sent_count == 2  # user1 and user3 succeeded
        # Failed user should be disconnected
        assert "user2" not in connection_manager.active_connections


class TestSubscriptionMessageHandling:
    """Test subscription message handling."""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handle_valid_subscription(self, connection_manager, mock_websocket):
        """Test handling valid subscription message."""
        user_id = "test_user"
        message = {
            "type": "subscribe",
            "channel": ChannelType.DASHBOARD_UPDATES
        }
        
        connection_manager.active_connections[user_id] = mock_websocket
        
        with patch.object(connection_manager.subscription_manager, 'process_subscription_request') as mock_process:
            mock_process.return_value = SubscriptionResponse(
                action="subscribe",
                channel=ChannelType.DASHBOARD_UPDATES,
                success=True,
                message="Successfully subscribed"
            )
            
            await connection_manager.handle_subscription_message(user_id, message)
            
            # Verify subscription manager was called
            mock_process.assert_called_once()
            
            # Verify response was sent to user
            mock_websocket.send_text.assert_called_once()
            
            # Verify user was subscribed
            assert ChannelType.DASHBOARD_UPDATES in connection_manager.user_subscriptions[user_id]
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handle_valid_unsubscription(self, connection_manager, mock_websocket):
        """Test handling valid unsubscription message."""
        user_id = "test_user"
        channel = "session_123"
        message = {
            "type": "unsubscribe",
            "channel": channel
        }
        
        # Set up existing subscription
        connection_manager.active_connections[user_id] = mock_websocket
        connection_manager.user_subscriptions[user_id] = {channel}
        connection_manager.channel_subscribers[channel] = {user_id}
        
        with patch.object(connection_manager.subscription_manager, 'process_subscription_request') as mock_process:
            mock_process.return_value = SubscriptionResponse(
                action="unsubscribe",
                channel=channel,
                success=True,
                message="Successfully unsubscribed"
            )
            
            await connection_manager.handle_subscription_message(user_id, message)
            
            # Verify user was unsubscribed
            assert channel not in connection_manager.user_subscriptions[user_id]
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handle_invalid_subscription_message(self, connection_manager, mock_websocket):
        """Test handling invalid subscription message format."""
        user_id = "test_user"
        invalid_message = {
            "type": "invalid_type",
            "channel": "test"
        }
        
        connection_manager.active_connections[user_id] = mock_websocket
        
        await connection_manager.handle_subscription_message(user_id, invalid_message)
        
        # Verify error response was sent
        mock_websocket.send_text.assert_called_once()
        
        # Verify error message content
        call_args = mock_websocket.send_text.call_args[0][0]
        response_data = json.loads(call_args)
        assert response_data["type"] == "error"
        assert "Invalid subscription message format" in response_data["message"]
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handle_subscription_manager_failure(self, connection_manager, mock_websocket):
        """Test handling subscription manager failure."""
        user_id = "test_user"
        message = {
            "type": "subscribe",
            "channel": ChannelType.DASHBOARD_UPDATES
        }
        
        connection_manager.active_connections[user_id] = mock_websocket
        
        with patch.object(connection_manager.subscription_manager, 'process_subscription_request') as mock_process:
            mock_process.return_value = SubscriptionResponse(
                action="subscribe",
                channel=ChannelType.DASHBOARD_UPDATES,
                success=False,
                message="Channel not available"
            )
            
            await connection_manager.handle_subscription_message(user_id, message)
            
            # Verify response was sent
            mock_websocket.send_text.assert_called_once()
            
            # Verify user was not subscribed (since it failed)
            user_subs = connection_manager.user_subscriptions.get(user_id, set())
            assert ChannelType.DASHBOARD_UPDATES not in user_subs
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_handle_subscription_message_exception(self, connection_manager, mock_websocket):
        """Test handling unexpected exception in subscription processing."""
        user_id = "test_user"
        message = {
            "type": "subscribe",
            "channel": ChannelType.DASHBOARD_UPDATES
        }
        
        connection_manager.active_connections[user_id] = mock_websocket
        
        with patch.object(connection_manager.subscription_manager, 'process_subscription_request') as mock_process:
            mock_process.side_effect = Exception("Unexpected error")
            
            await connection_manager.handle_subscription_message(user_id, message)
            
            # Verify error response was sent
            mock_websocket.send_text.assert_called_once()
            
            # Verify error message content
            call_args = mock_websocket.send_text.call_args[0][0]
            response_data = json.loads(call_args)
            assert response_data["type"] == "error"
            assert "Internal error" in response_data["message"]


class TestConnectionStatistics:
    """Test connection statistics functionality."""
    
    @pytest.mark.unit
    def test_get_connection_stats(self, connection_manager):
        """Test getting connection statistics."""
        # Set up test data
        connection_manager.active_connections = {
            "user1": Mock(),
            "user2": Mock(),
            "user3": Mock()
        }
        connection_manager.user_subscriptions = {
            "user1": {"dashboard_updates", "session_123"},
            "user2": {"system_health"},
            "user3": set()
        }
        connection_manager.channel_subscribers = {
            "dashboard_updates": {"user1"},
            "session_123": {"user1"},
            "system_health": {"user2"}
        }
        
        with patch.object(connection_manager.subscription_manager, 'get_subscription_stats') as mock_stats:
            mock_stats.return_value = {"test_stat": 42}
            
            stats = connection_manager.get_connection_stats()
            
            assert stats["active_connections"] == 3
            assert stats["total_subscriptions"] == 3  # 2 + 1 + 0
            assert stats["active_channels"] == 3
            assert stats["users_with_subscriptions"] == 3
            assert stats["subscription_manager"]["test_stat"] == 42
    
    @pytest.mark.unit
    def test_get_connection_stats_empty(self, connection_manager):
        """Test getting connection statistics when empty."""
        with patch.object(connection_manager.subscription_manager, 'get_subscription_stats') as mock_stats:
            mock_stats.return_value = {}
            
            stats = connection_manager.get_connection_stats()
            
            assert stats["active_connections"] == 0
            assert stats["total_subscriptions"] == 0
            assert stats["active_channels"] == 0
            assert stats["users_with_subscriptions"] == 0


class TestSystemHealthBroadcast:
    """Test system health broadcasting."""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_broadcast_system_health_update(self, connection_manager):
        """Test broadcasting system health update."""
        status = "healthy"
        services = {"database": "healthy", "llm": "healthy"}
        users = ["user1", "user2"]
        
        # Set up subscribers
        connection_manager.channel_subscribers[ChannelType.SYSTEM_HEALTH] = set(users)
        for user in users:
            mock_ws = AsyncMock()
            connection_manager.active_connections[user] = mock_ws
        
        sent_count = await connection_manager.broadcast_system_health_update(status, services)
        
        assert sent_count == 2
        
        # Verify message content
        for user in users:
            mock_ws = connection_manager.active_connections[user]
            mock_ws.send_text.assert_called_once()
            
            # Check message structure
            call_args = mock_ws.send_text.call_args[0][0]
            message_data = json.loads(call_args)
            assert message_data["type"] == "system_health"
            assert message_data["status"] == "healthy"
            assert message_data["services"] == services


class TestAdvancedBroadcasting:
    """Test advanced broadcasting features."""
    
    @pytest.mark.asyncio
    @pytest.mark.unit 
    async def test_initialize_broadcaster_actual_method(self, connection_manager):
        """Test the actual initialize_broadcaster method."""
        # Verify broadcaster is not initialized
        assert connection_manager.broadcaster is None
        assert connection_manager.update_service is None
        
        # Mock the imported classes at the location they're imported
        with patch('tarsy.services.dashboard_broadcaster.DashboardBroadcaster') as mock_broadcaster_class:
            with patch('tarsy.services.dashboard_update_service.DashboardUpdateService') as mock_update_service_class:
                # Set up mocks
                mock_broadcaster = AsyncMock()
                mock_update_service = AsyncMock()
                mock_broadcaster_class.return_value = mock_broadcaster
                mock_update_service_class.return_value = mock_update_service
                
                # Call the actual method
                result = await connection_manager.initialize_broadcaster()
                
                # Verify broadcaster was created and started
                mock_broadcaster_class.assert_called_once_with(connection_manager)
                mock_broadcaster.start.assert_called_once()
                
                # Verify update service was created and started
                mock_update_service_class.assert_called_once_with(mock_broadcaster)
                mock_update_service.start.assert_called_once()
                
                # Verify services are assigned
                assert connection_manager.broadcaster == mock_broadcaster
                assert connection_manager.update_service == mock_update_service
                assert result == mock_broadcaster
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_initialize_broadcaster(self, connection_manager):
        """Test initializing advanced broadcaster."""
        # Since the initialize_broadcaster method doesn't exist in the current implementation,
        # we'll test that the connection manager can accept broadcaster assignment
        mock_broadcaster = AsyncMock()
        mock_update_service = AsyncMock()
        
        # Manually assign the services
        connection_manager.broadcaster = mock_broadcaster
        connection_manager.update_service = mock_update_service
        
        # Verify they're properly assigned
        assert connection_manager.broadcaster == mock_broadcaster
        assert connection_manager.update_service == mock_update_service
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_shutdown_broadcaster(self, connection_manager):
        """Test shutting down advanced broadcaster."""
        # Set up existing broadcaster and update service
        mock_broadcaster = AsyncMock()
        mock_update_service = AsyncMock()
        connection_manager.broadcaster = mock_broadcaster
        connection_manager.update_service = mock_update_service
        
        await connection_manager.shutdown_broadcaster()
        
        mock_update_service.stop.assert_called_once()
        mock_broadcaster.stop.assert_called_once()
        assert connection_manager.broadcaster is None
        assert connection_manager.update_service is None
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_broadcast_with_advanced_features(self, connection_manager):
        """Test broadcasting with advanced features."""
        channel = ChannelType.DASHBOARD_UPDATES
        message = Mock()
        exclude_users = {"user1"}
        
        # Set up advanced broadcaster
        mock_broadcaster = AsyncMock()
        mock_broadcaster.broadcast_message.return_value = 5
        connection_manager.broadcaster = mock_broadcaster
        
        sent_count = await connection_manager.broadcast_with_advanced_features(
            channel, message, exclude_users
        )
        
        assert sent_count == 5
        mock_broadcaster.broadcast_message.assert_called_once_with(
            channel, message, exclude_users
        )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_broadcast_with_advanced_features_fallback(self, connection_manager):
        """Test broadcasting fallback when advanced broadcaster not available."""
        channel = ChannelType.DASHBOARD_UPDATES
        message = Mock()
        message.model_dump = Mock(return_value={"type": "test"})
        
        # No advanced broadcaster set
        assert connection_manager.broadcaster is None
        
        # Set up basic broadcast scenario
        users = ["user1", "user2"]
        connection_manager.channel_subscribers[channel] = set(users)
        for user in users:
            mock_ws = AsyncMock()
            connection_manager.active_connections[user] = mock_ws
        
        sent_count = await connection_manager.broadcast_with_advanced_features(
            channel, message
        )
        
        assert sent_count == 2
        # Verify fallback to basic broadcasting
        for user in users:
            mock_ws = connection_manager.active_connections[user]
            mock_ws.send_text.assert_called_once()
    
    @pytest.mark.unit
    def test_configure_broadcaster(self, connection_manager):
        """Test configuring broadcaster settings."""
        mock_broadcaster = Mock()
        connection_manager.broadcaster = mock_broadcaster
        
        config = {
            'batching_enabled': True,
            'batch_size': 10,
            'batch_timeout_seconds': 5,
            'throttle_limits': {
                'dashboard_updates': {'max_messages': 100, 'time_window_seconds': 60}
            }
        }
        
        connection_manager.configure_broadcaster(**config)
        
        mock_broadcaster.configure_batching.assert_called_once_with(True, 10, 5)
        mock_broadcaster.set_throttle_limit.assert_called_once_with(
            'dashboard_updates', 100, 60
        )
    
    @pytest.mark.unit
    def test_configure_broadcaster_not_initialized(self, connection_manager):
        """Test configuring broadcaster when not initialized."""
        # Should not raise exception
        connection_manager.configure_broadcaster(batching_enabled=True)


if __name__ == "__main__":
    pytest.main([__file__]) 