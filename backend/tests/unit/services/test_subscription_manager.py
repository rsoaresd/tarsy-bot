"""
Unit tests for SubscriptionManager.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from tarsy.services.subscription_manager import SubscriptionManager
from tarsy.models.websocket_models import (
    ChannelType,
    SubscriptionMessage,
    SubscriptionResponse,
    OutgoingMessage,
    DashboardUpdate
)


class TestSubscriptionManager:
    """Test SubscriptionManager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = SubscriptionManager()
    
    @pytest.mark.unit
    def test_initialization(self):
        """Test SubscriptionManager initialization."""
        assert isinstance(self.manager.channel_config, dict)
        assert ChannelType.DASHBOARD_UPDATES in self.manager.channel_config
        assert ChannelType.SYSTEM_HEALTH in self.manager.channel_config
        assert isinstance(self.manager.session_channels, set)
        assert len(self.manager.session_channels) == 0
    
    @pytest.mark.unit
    def test_validate_predefined_channel(self):
        """Test validation of predefined channels."""
        # Test dashboard_updates channel
        is_valid, error = self.manager.validate_channel(ChannelType.DASHBOARD_UPDATES)
        assert is_valid is True
        assert error is None
        
        # Test system_health channel
        is_valid, error = self.manager.validate_channel(ChannelType.SYSTEM_HEALTH)
        assert is_valid is True
        assert error is None
    
    @pytest.mark.unit
    def test_validate_session_channel(self):
        """Test validation of session channels."""
        # Valid session channel
        is_valid, error = self.manager.validate_channel("session_123")
        assert is_valid is True
        assert error is None
        assert "session_123" in self.manager.session_channels
        
        # Another valid session channel
        is_valid, error = self.manager.validate_channel("session_abc_def")
        assert is_valid is True
        assert error is None
        assert "session_abc_def" in self.manager.session_channels
    
    @pytest.mark.unit
    def test_validate_invalid_channel(self):
        """Test validation of invalid channels."""
        is_valid, error = self.manager.validate_channel("invalid_channel")
        assert is_valid is False
        assert error is not None
        assert "Unknown channel" in error
    
    @pytest.mark.unit
    def test_validate_malformed_session_channel(self):
        """Test validation of malformed session channels."""
        # Empty session ID
        is_valid, error = self.manager.validate_channel("session_")
        assert is_valid is False  # Empty session_id is invalid
        assert error is not None
    
    @pytest.mark.unit
    def test_get_channel_info_predefined(self):
        """Test getting info for predefined channels."""
        info = self.manager.get_channel_info(ChannelType.DASHBOARD_UPDATES)
        assert info is not None
        assert info["max_subscribers"] == 100
        assert info["requires_auth"] is False
        assert info["persistent"] is True
        assert "description" in info
        
        info = self.manager.get_channel_info(ChannelType.SYSTEM_HEALTH)
        assert info is not None
        assert info["max_subscribers"] == 50
    
    @pytest.mark.unit
    def test_get_channel_info_session(self):
        """Test getting info for session channels."""
        channel = "session_test_123"
        info = self.manager.get_channel_info(channel)
        assert info is not None
        assert info["max_subscribers"] == 10
        assert info["requires_auth"] is False
        assert info["persistent"] is False
        assert info["session_id"] == "test_123"
        assert "session test_123" in info["description"]
    
    @pytest.mark.unit
    def test_get_channel_info_invalid(self):
        """Test getting info for invalid channels."""
        info = self.manager.get_channel_info("invalid_channel")
        assert info is None


class TestSubscriptionProcessing:
    """Test subscription request processing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = SubscriptionManager()
    
    @pytest.mark.unit
    def test_process_valid_subscription(self):
        """Test processing valid subscription request."""
        message = SubscriptionMessage(type="subscribe", channel=ChannelType.DASHBOARD_UPDATES)
        response = self.manager.process_subscription_request("user1", message)
        
        assert isinstance(response, SubscriptionResponse)
        assert response.action == "subscribe"
        assert response.channel == ChannelType.DASHBOARD_UPDATES
        assert response.success is True
        assert "Successfully" in response.message
    
    @pytest.mark.unit
    def test_process_valid_unsubscription(self):
        """Test processing valid unsubscription request."""
        message = SubscriptionMessage(type="unsubscribe", channel="session_123")
        response = self.manager.process_subscription_request("user1", message)
        
        assert response.action == "unsubscribe"
        assert response.channel == "session_123"
        assert response.success is True
    
    @pytest.mark.unit
    def test_process_invalid_subscription(self):
        """Test processing invalid subscription request."""
        message = SubscriptionMessage(type="subscribe", channel="invalid_channel")
        response = self.manager.process_subscription_request("user1", message)
        
        assert response.success is False
        assert "Unknown channel" in response.message
    
    @pytest.mark.unit
    def test_process_session_subscription(self):
        """Test processing session channel subscription."""
        message = SubscriptionMessage(type="subscribe", channel="session_abc123")
        response = self.manager.process_subscription_request("user1", message)
        
        assert response.success is True
        assert "session_abc123" in self.manager.session_channels
        assert "session_abc123" in self.manager.channel_activity
    
    @pytest.mark.unit
    def test_subscription_updates_activity(self):
        """Test that subscriptions update channel activity."""
        channel = ChannelType.DASHBOARD_UPDATES
        before_time = datetime.now()
        
        message = SubscriptionMessage(type="subscribe", channel=channel)
        self.manager.process_subscription_request("user1", message)
        
        assert channel in self.manager.channel_activity
        activity_time = self.manager.channel_activity[channel]
        assert activity_time >= before_time


class TestSubscriptionCallbacks:
    """Test subscription callback functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = SubscriptionManager()
        self.callback_calls = []
    
    def mock_callback(self, channel, user_id, action):
        """Mock callback function."""
        self.callback_calls.append((channel, user_id, action))
    
    @pytest.mark.unit
    def test_add_subscription_callback(self):
        """Test adding subscription callbacks."""
        channel = ChannelType.DASHBOARD_UPDATES
        self.manager.add_subscription_callback(channel, self.mock_callback)
        
        assert channel in self.manager.subscription_callbacks
        assert self.mock_callback in self.manager.subscription_callbacks[channel]
    
    @pytest.mark.unit
    def test_callback_triggered_on_subscription(self):
        """Test that callbacks are triggered on subscription."""
        channel = ChannelType.DASHBOARD_UPDATES
        self.manager.add_subscription_callback(channel, self.mock_callback)
        
        message = SubscriptionMessage(type="subscribe", channel=channel)
        self.manager.process_subscription_request("user1", message)
        
        assert len(self.callback_calls) == 1
        assert self.callback_calls[0] == (channel, "user1", "subscribe")
    
    @pytest.mark.unit
    def test_callback_triggered_on_unsubscription(self):
        """Test that callbacks are triggered on unsubscription."""
        channel = "session_test"
        self.manager.add_subscription_callback(channel, self.mock_callback)
        
        message = SubscriptionMessage(type="unsubscribe", channel=channel)
        self.manager.process_subscription_request("user2", message)
        
        assert len(self.callback_calls) == 1
        assert self.callback_calls[0] == (channel, "user2", "unsubscribe")
    
    @pytest.mark.unit
    def test_callback_error_handling(self):
        """Test error handling in callbacks."""
        def error_callback(channel, user_id, action):
            raise Exception("Callback error")
        
        channel = ChannelType.SYSTEM_HEALTH
        self.manager.add_subscription_callback(channel, error_callback)
        
        # Should not raise exception
        message = SubscriptionMessage(type="subscribe", channel=channel)
        response = self.manager.process_subscription_request("user1", message)
        
        # Subscription should still succeed despite callback error
        assert response.success is True


class TestMessageFiltering:
    """Test message filtering functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = SubscriptionManager()
        self.filter_calls = []
    
    def mock_filter_allow(self, message, user_id):
        """Mock filter that allows messages."""
        self.filter_calls.append((message, user_id, True))
        return True
    
    def mock_filter_deny(self, message, user_id):
        """Mock filter that denies messages."""
        self.filter_calls.append((message, user_id, False))
        return False
    
    @pytest.mark.unit
    def test_add_message_filter(self):
        """Test adding message filters."""
        channel = ChannelType.DASHBOARD_UPDATES
        self.manager.add_message_filter(channel, self.mock_filter_allow)
        
        assert channel in self.manager.channel_filters
        assert self.mock_filter_allow in self.manager.channel_filters[channel]
    
    @pytest.mark.unit
    def test_message_delivery_allowed(self):
        """Test message delivery when filters allow."""
        channel = ChannelType.DASHBOARD_UPDATES
        self.manager.add_message_filter(channel, self.mock_filter_allow)
        
        message = DashboardUpdate(data={"test": "data"})
        should_deliver = self.manager.should_deliver_message(channel, message, "user1")
        
        assert should_deliver is True
        assert len(self.filter_calls) == 1
        assert self.filter_calls[0][1] == "user1"  # user_id
        assert self.filter_calls[0][2] is True  # result
    
    @pytest.mark.unit
    def test_message_delivery_denied(self):
        """Test message delivery when filters deny."""
        channel = ChannelType.SYSTEM_HEALTH
        self.manager.add_message_filter(channel, self.mock_filter_deny)
        
        message = DashboardUpdate(data={"test": "data"})
        should_deliver = self.manager.should_deliver_message(channel, message, "user2")
        
        assert should_deliver is False
        assert len(self.filter_calls) == 1
    
    @pytest.mark.unit
    def test_multiple_filters(self):
        """Test message filtering with multiple filters."""
        channel = ChannelType.DASHBOARD_UPDATES
        self.manager.add_message_filter(channel, self.mock_filter_allow)
        self.manager.add_message_filter(channel, self.mock_filter_deny)
        
        message = DashboardUpdate(data={"test": "data"})
        should_deliver = self.manager.should_deliver_message(channel, message, "user1")
        
        # Should be denied because one filter denies
        assert should_deliver is False
        assert len(self.filter_calls) == 2
    
    @pytest.mark.unit
    def test_filter_error_handling(self):
        """Test error handling in message filters."""
        def error_filter(message, user_id):
            raise Exception("Filter error")
        
        channel = ChannelType.DASHBOARD_UPDATES
        self.manager.add_message_filter(channel, error_filter)
        
        message = DashboardUpdate(data={"test": "data"})
        # Should default to allowing message on filter error
        should_deliver = self.manager.should_deliver_message(channel, message, "user1")
        assert should_deliver is True
    
    @pytest.mark.unit
    def test_no_filters(self):
        """Test message delivery with no filters."""
        channel = ChannelType.DASHBOARD_UPDATES
        message = DashboardUpdate(data={"test": "data"})
        
        should_deliver = self.manager.should_deliver_message(channel, message, "user1")
        assert should_deliver is True


class TestChannelCleanup:
    """Test channel cleanup functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = SubscriptionManager()
    
    @pytest.mark.unit
    def test_cleanup_inactive_channels(self):
        """Test cleanup of inactive session channels."""
        # Add some session channels with different activity times
        old_time = datetime.now() - timedelta(hours=2)
        recent_time = datetime.now() - timedelta(minutes=30)
        
        self.manager.session_channels.add("session_old")
        self.manager.session_channels.add("session_recent")
        self.manager.channel_activity["session_old"] = old_time
        self.manager.channel_activity["session_recent"] = recent_time
        
        # Add some callbacks and filters to test cleanup
        self.manager.subscription_callbacks["session_old"] = [lambda x, y, z: None]
        self.manager.channel_filters["session_old"] = [lambda x, y: True]
        
        # Clean up channels older than 1 hour
        cleaned_count = self.manager.cleanup_inactive_channels(max_age_minutes=60)
        
        assert cleaned_count == 1
        assert "session_old" not in self.manager.session_channels
        assert "session_recent" in self.manager.session_channels
        assert "session_old" not in self.manager.channel_activity
        assert "session_old" not in self.manager.subscription_callbacks
        assert "session_old" not in self.manager.channel_filters
    
    @pytest.mark.unit
    def test_cleanup_no_inactive_channels(self):
        """Test cleanup when no channels are inactive."""
        # Add recent channel
        recent_time = datetime.now() - timedelta(minutes=10)
        self.manager.session_channels.add("session_recent")
        self.manager.channel_activity["session_recent"] = recent_time
        
        cleaned_count = self.manager.cleanup_inactive_channels(max_age_minutes=60)
        
        assert cleaned_count == 0
        assert "session_recent" in self.manager.session_channels
    
    @pytest.mark.unit
    def test_cleanup_preserves_predefined_channels(self):
        """Test that cleanup doesn't affect predefined channels."""
        # This test ensures predefined channels are not affected by cleanup
        # even if they had activity tracking (which they shouldn't in practice)
        original_config = self.manager.channel_config.copy()
        
        self.manager.cleanup_inactive_channels(max_age_minutes=0)  # Clean everything
        
        # Predefined channels should still be in config
        assert self.manager.channel_config == original_config
    
    @pytest.mark.unit
    def test_get_active_session_channels(self):
        """Test getting list of active session channels."""
        self.manager.session_channels.add("session_1")
        self.manager.session_channels.add("session_2")
        
        active_channels = self.manager.get_active_session_channels()
        
        assert isinstance(active_channels, list)
        assert "session_1" in active_channels
        assert "session_2" in active_channels
        assert len(active_channels) == 2
    
    @pytest.mark.unit
    def test_is_channel_persistent(self):
        """Test checking if channels are persistent."""
        # Predefined channels should be persistent
        assert self.manager.is_channel_persistent(ChannelType.DASHBOARD_UPDATES) is True
        assert self.manager.is_channel_persistent(ChannelType.SYSTEM_HEALTH) is True
        
        # Session channels should not be persistent
        assert self.manager.is_channel_persistent("session_123") is False
        
        # Unknown channels should default to False
        assert self.manager.is_channel_persistent("unknown_channel") is False


class TestSubscriptionStatistics:
    """Test subscription statistics functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = SubscriptionManager()
    
    @pytest.mark.unit
    def test_get_subscription_stats_empty(self):
        """Test statistics when no subscriptions exist."""
        stats = self.manager.get_subscription_stats()
        
        assert stats["predefined_channels"] == 2  # dashboard_updates, system_health
        assert stats["session_channels"] == 0
        assert stats["total_channels"] == 2
        assert stats["channels_with_callbacks"] == 0
        assert stats["channels_with_filters"] == 0
        assert stats["recent_activity"] == 0
    
    @pytest.mark.unit
    def test_get_subscription_stats_with_data(self):
        """Test statistics with various data."""
        # Add session channels
        self.manager.session_channels.add("session_1")
        self.manager.session_channels.add("session_2")
        
        # Add callbacks and filters
        self.manager.subscription_callbacks["session_1"] = [lambda x, y, z: None]
        self.manager.channel_filters[ChannelType.DASHBOARD_UPDATES] = [lambda x, y: True]
        
        # Add recent activity
        recent_time = datetime.now() - timedelta(minutes=2)
        old_time = datetime.now() - timedelta(minutes=10)
        self.manager.channel_activity["session_1"] = recent_time
        self.manager.channel_activity["session_2"] = old_time
        
        stats = self.manager.get_subscription_stats()
        
        assert stats["predefined_channels"] == 2
        assert stats["session_channels"] == 2
        assert stats["total_channels"] == 4
        assert stats["channels_with_callbacks"] == 1
        assert stats["channels_with_filters"] == 1
        assert stats["recent_activity"] == 1  # Only session_1 is recent


if __name__ == "__main__":
    pytest.main([__file__]) 