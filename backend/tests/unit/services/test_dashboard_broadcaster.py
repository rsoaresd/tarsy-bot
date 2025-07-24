"""
Unit tests for DashboardBroadcaster and related functionality.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from tarsy.models.websocket_models import (
    ChannelType,
    DashboardUpdate,
    SessionUpdate,
    SystemHealthUpdate,
)
from tarsy.services.dashboard_broadcaster import DashboardBroadcaster, MessageBatch


class TestMessageBatch:
    """Test MessageBatch functionality."""
    
    @pytest.mark.unit
    def test_message_batch_creation(self):
        """Test MessageBatch creation."""
        batch = MessageBatch(max_size=5, max_age_seconds=2.0)
        
        assert batch.max_size == 5
        assert batch.max_age_seconds == 2.0
        assert len(batch.messages) == 0
        assert batch.created_at is not None
        assert isinstance(batch.created_at, datetime)
    
    @pytest.mark.unit
    def test_add_message(self):
        """Test adding messages to batch."""
        batch = MessageBatch(max_size=3, max_age_seconds=1.0)
        message1 = DashboardUpdate(data={"test": "data1"})
        message2 = SessionUpdate(session_id="123", data={"test": "data2"})
        
        # Add first message
        is_full = batch.add_message(message1)
        assert is_full is False
        assert len(batch.messages) == 1
        assert batch.messages[0] == message1
        
        # Add second message
        is_full = batch.add_message(message2)
        assert is_full is False
        assert len(batch.messages) == 2
        
        # Add third message - should be full
        message3 = SystemHealthUpdate(status="healthy", services={})
        is_full = batch.add_message(message3)
        assert is_full is True
        assert len(batch.messages) == 3
    
    @pytest.mark.unit
    def test_is_ready_by_size(self):
        """Test batch readiness by size."""
        batch = MessageBatch(max_size=2, max_age_seconds=10.0)
        
        assert batch.is_ready() is False
        
        batch.add_message(DashboardUpdate(data={"test": "data"}))
        assert batch.is_ready() is False
        
        batch.add_message(DashboardUpdate(data={"test": "data2"}))
        assert batch.is_ready() is True
    
    @pytest.mark.unit
    def test_is_ready_by_timeout(self):
        """Test batch readiness by timeout logic."""
        # Test with past creation time to simulate timeout without actual waiting
        batch = MessageBatch(max_size=10, max_age_seconds=1.0)
        batch.add_message(DashboardUpdate(data={"test": "data"}))
        
        # Manually set created_at to simulate timeout condition
        from datetime import datetime, timedelta
        batch.created_at = datetime.now() - timedelta(seconds=2.0)  # 2 seconds ago
        
        # Should be ready due to age
        assert batch.is_ready() is True
    
    @pytest.mark.unit
    def test_get_combined_message(self):
        """Test getting combined batch message."""
        batch = MessageBatch(max_size=5, max_age_seconds=1.0)
        
        message1 = DashboardUpdate(data={"key1": "value1"})
        message2 = SessionUpdate(session_id="123", data={"key2": "value2"})
        
        batch.add_message(message1)
        batch.add_message(message2)
        
        combined = batch.get_batched_message()
        
        assert combined["type"] == "message_batch"
        assert len(combined["messages"]) == 2
        assert combined["count"] == 2
        assert "timestamp" in combined
        
        # Verify individual messages are properly serialized
        messages = combined["messages"]
        assert messages[0]["type"] == "dashboard_update"
        assert messages[1]["type"] == "session_update"
    
    @pytest.mark.unit
    def test_empty_batch_combined_message(self):
        """Test getting combined message from empty batch."""
        batch = MessageBatch(max_size=5, max_age_seconds=1.0)
        
        combined = batch.get_batched_message()
        
        assert combined["type"] == "message_batch"
        assert combined["messages"] == []
        assert combined["count"] == 0


class TestDashboardBroadcasterThrottling:
    """Test DashboardBroadcaster throttling functionality."""
    
    @pytest.fixture
    def mock_connection_manager(self):
        """Create mock connection manager."""
        return Mock()
    
    @pytest.fixture
    def broadcaster(self, mock_connection_manager):
        """Create DashboardBroadcaster instance for testing."""
        return DashboardBroadcaster(mock_connection_manager)
    
    @pytest.mark.unit
    def test_set_throttle_limit(self, broadcaster):
        """Test setting throttle limits for a channel."""
        broadcaster.set_throttle_limit("test_channel", max_messages=10, time_window_seconds=60)
        
        assert "test_channel" in broadcaster.throttle_limits
        limits = broadcaster.throttle_limits["test_channel"]
        assert limits["max_messages"] == 10
        assert limits["time_window"] == 60
    
    @pytest.mark.unit
    def test_should_throttle_within_limit(self, broadcaster):
        """Test throttling when within limits."""
        broadcaster.set_throttle_limit("test_channel", max_messages=3, time_window_seconds=60)
        
        # Add messages within limit
        for i in range(3):
            should_throttle = broadcaster._should_throttle_user("test_user", "test_channel")
            assert should_throttle is False
            broadcaster._record_user_message("test_user", "test_channel")
    
    @pytest.mark.unit
    def test_should_throttle_exceeds_limit(self, broadcaster):
        """Test throttling when exceeding limits."""
        broadcaster.set_throttle_limit("test_channel", max_messages=2, time_window_seconds=60)
        
        # Add messages up to limit
        for i in range(2):
            assert broadcaster._should_throttle_user("test_user", "test_channel") is False
            broadcaster._record_user_message("test_user", "test_channel")
        
        # Next message should be throttled
        assert broadcaster._should_throttle_user("test_user", "test_channel") is True
    
    @pytest.mark.unit
    def test_throttle_automatic_cleanup(self, broadcaster):
        """Test automatic cleanup of old timestamps."""
        broadcaster.set_throttle_limit("test_channel", max_messages=5, time_window_seconds=1)
        
        # Add old timestamps manually
        old_time = datetime.now() - timedelta(seconds=2)
        recent_time = datetime.now()
        
        user_messages = broadcaster.user_message_counts["test_user"]["test_channel"]
        user_messages.extend([old_time, recent_time])
        
        # _should_throttle_user should clean up old timestamps
        should_throttle = broadcaster._should_throttle_user("test_user", "test_channel")
        
        # Old timestamp should be removed, only recent one remains
        assert len(user_messages) == 1
        assert user_messages[0] == recent_time
        assert should_throttle is False  # Still within limit
    
    @pytest.mark.unit
    def test_no_throttling_without_limits(self, broadcaster):
        """Test that channels without throttle limits are not throttled."""
        # Don't set any throttle limits
        should_throttle = broadcaster._should_throttle_user("test_user", "test_channel")
        assert should_throttle is False
        
        # Record many messages
        for i in range(100):
            broadcaster._record_user_message("test_user", "test_channel")
        
        # Still should not throttle
        should_throttle = broadcaster._should_throttle_user("test_user", "test_channel")
        assert should_throttle is False
    
    @pytest.mark.unit
    def test_throttling_per_user_per_channel(self, broadcaster):
        """Test that throttling is applied per user per channel."""
        broadcaster.set_throttle_limit("channel1", max_messages=2, time_window_seconds=60)
        broadcaster.set_throttle_limit("channel2", max_messages=3, time_window_seconds=60)
        
        # User1 on channel1 - exceed limit
        for i in range(2):
            broadcaster._record_user_message("user1", "channel1")
        assert broadcaster._should_throttle_user("user1", "channel1") is True
        
        # User1 on channel2 - should not be throttled (different channel)
        assert broadcaster._should_throttle_user("user1", "channel2") is False
        
        # User2 on channel1 - should not be throttled (different user)
        assert broadcaster._should_throttle_user("user2", "channel1") is False


class TestDashboardBroadcaster:
    """Test DashboardBroadcaster main functionality."""
    
    @pytest.fixture
    def mock_connection_manager(self):
        """Create mock connection manager."""
        manager = Mock()
        manager.broadcast_to_channel = AsyncMock(return_value=0)
        manager.get_channel_subscribers = Mock(return_value={"user1", "user2", "user3"})
        manager.send_to_user = AsyncMock(return_value=True)
        return manager
    
    @pytest.fixture
    def broadcaster(self, mock_connection_manager):
        """Create DashboardBroadcaster instance."""
        return DashboardBroadcaster(mock_connection_manager)

    @pytest.mark.unit
    def test_broadcaster_initialization(self, broadcaster):
        """Test DashboardBroadcaster initialization."""
        assert broadcaster.connection_manager is not None
        assert isinstance(broadcaster.active_batches, dict)
        assert isinstance(broadcaster.throttle_limits, dict)
        assert broadcaster.batching_enabled is True
        assert broadcaster.batch_size == 5
        assert broadcaster.running is False
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_broadcaster_start_stop(self, broadcaster):
        """Test starting and stopping broadcaster."""
        assert broadcaster.running is False
        
        # Start broadcaster
        await broadcaster.start()
        assert broadcaster.running is True
        assert broadcaster.batch_processor_task is not None
        
        # Stop broadcaster
        await broadcaster.stop()
        assert broadcaster.running is False
    
    @pytest.mark.unit
    def test_configure_batching(self, broadcaster):
        """Test configuring batching settings."""
        broadcaster.configure_batching(
            enabled=True,
            batch_size=10,
            timeout_seconds=5.0
        )
        
        assert broadcaster.batching_enabled is True
        assert broadcaster.batch_size == 10
        assert broadcaster.batch_timeout_seconds == 5.0
    
    @pytest.mark.unit
    def test_set_throttle_limit(self, broadcaster):
        """Test setting throttle limits."""
        channel = ChannelType.DASHBOARD_UPDATES
        
        broadcaster.set_throttle_limit(channel, max_messages=20, time_window_seconds=120)
        
        assert channel in broadcaster.throttle_limits
        limits = broadcaster.throttle_limits[channel]
        assert limits["max_messages"] == 20
        assert limits["time_window"] == 120
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_broadcast_message_basic(self, broadcaster, mock_connection_manager):
        """Test basic message broadcasting without batching."""
        # Disable batching for this test to get immediate sending
        broadcaster.configure_batching(enabled=False)
        
        message = DashboardUpdate(data={"test": "data"})
        channel = ChannelType.DASHBOARD_UPDATES
        
        sent_count = await broadcaster.broadcast_message(channel, message)
        
        # With batching disabled, it should call send_to_user for each user
        assert mock_connection_manager.send_to_user.call_count == 3
        assert sent_count == 3
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_broadcast_message_with_exclusions(self, broadcaster, mock_connection_manager):
        """Test broadcasting with user exclusions."""
        # Disable batching for this test to get immediate sending
        broadcaster.configure_batching(enabled=False)
        
        message = SessionUpdate(session_id="123", data={"status": "active"})
        channel = "session_123"
        exclude_users = {"user1", "user2"}
        
        sent_count = await broadcaster.broadcast_message(channel, message, exclude_users)
        
        # With exclusions, only 1 user should receive the message (3 - 2 excluded)
        assert mock_connection_manager.send_to_user.call_count == 1
        assert sent_count == 1
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_broadcast_message_throttled(self, broadcaster, mock_connection_manager):
        """Test broadcasting when throttled."""
        # Disable batching for this test to get immediate sending
        broadcaster.configure_batching(enabled=False)
        
        channel = ChannelType.DASHBOARD_UPDATES
        message = DashboardUpdate(data={"test": "data"})
        
        # Set up throttling - 1 message per 60 seconds per user
        broadcaster.set_throttle_limit(channel, max_messages=1, time_window_seconds=60)
        
        # First message should go through to all users
        sent_count1 = await broadcaster.broadcast_message(channel, message)
        assert sent_count1 == 3  # All 3 users receive the message
        
        # Second message should be throttled for all users
        sent_count2 = await broadcaster.broadcast_message(channel, message)
        assert sent_count2 == 0  # All users are throttled
        
        # Verify first call sent to all users, second call sent to none
        assert mock_connection_manager.send_to_user.call_count == 3  # Only from first message
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_broadcast_message_with_batching(self, broadcaster, mock_connection_manager):
        """Test broadcasting with batching enabled."""
        broadcaster.configure_batching(enabled=True, batch_size=2, timeout_seconds=10.0)
        
        channel = ChannelType.DASHBOARD_UPDATES
        message1 = DashboardUpdate(data={"test": "data1"})
        message2 = DashboardUpdate(data={"test": "data2"})
        
        # Test batching behavior without relying on background processor timing
        # Send first message - should be queued in batch
        await broadcaster.broadcast_message(channel, message1)
        
        # Verify message was batched (not sent immediately)
        assert mock_connection_manager.broadcast_to_channel.call_count == 0
        assert channel in broadcaster.active_batches
        assert len(broadcaster.active_batches[channel].messages) == 1
        
        # Send second message - should complete the batch and trigger immediate send
        await broadcaster.broadcast_message(channel, message2)
        
        # Batch should have been sent immediately when size limit reached
        assert mock_connection_manager.broadcast_to_channel.call_count == 1
        assert channel not in broadcaster.active_batches  # Batch should be cleared
    
    @pytest.mark.unit
    def test_get_broadcast_stats(self, broadcaster):
        """Test getting broadcast statistics."""
        # Add some test data
        broadcaster.stats["messages_sent"] = 100
        broadcaster.stats["messages_throttled"] = 5
        broadcaster.stats["batches_sent"] = 20
        
        stats = broadcaster.get_broadcast_stats()
        
        assert stats["messages_sent"] == 100
        assert stats["messages_throttled"] == 5
        assert stats["batches_sent"] == 20
        assert stats["batching_enabled"] == broadcaster.batching_enabled
        assert "active_batches" in stats
        assert "throttle_limits" in stats
        assert "message_filters" in stats

class TestAdvancedBroadcastMethods:
    """Test advanced broadcast methods."""
    
    @pytest.fixture
    def mock_connection_manager(self):
        """Create mock connection manager."""
        manager = Mock()
        manager.broadcast_to_channel = AsyncMock(return_value=0)
        manager.get_channel_subscribers = Mock(return_value={"user1", "user2", "user3"})
        manager.send_to_user = AsyncMock(return_value=True)
        return manager
    
    @pytest.fixture  
    def broadcaster(self, mock_connection_manager):
        """Create DashboardBroadcaster instance."""
        return DashboardBroadcaster(mock_connection_manager)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_broadcast_dashboard_update(self, broadcaster, mock_connection_manager):
        """Test broadcasting dashboard update."""
        # Disable batching for this test to get immediate sending
        broadcaster.configure_batching(enabled=False)
        
        data = {"sessions": 5, "active_alerts": 2}
        
        sent_count = await broadcaster.broadcast_dashboard_update(data)
        
        # With batching disabled, it should call send_to_user for each user
        assert mock_connection_manager.send_to_user.call_count == 3
        assert sent_count == 3
        
        # Verify the message content
        call_args = mock_connection_manager.send_to_user.call_args_list[0]
        message_data = call_args[0][1]  # Second argument is the message
        assert message_data["type"] == "dashboard_update"
        assert message_data["data"] == data
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_broadcast_session_update(self, broadcaster, mock_connection_manager):
        """Test broadcasting session update."""
        # Disable batching for this test to get immediate sending
        broadcaster.configure_batching(enabled=False)
        
        session_id = "session_123"
        data = {"status": "processing", "progress": 75}
        
        sent_count = await broadcaster.broadcast_session_update(session_id, data)
        
        # With batching disabled, it should call send_to_user for each user
        assert mock_connection_manager.send_to_user.call_count == 3
        assert sent_count == 3
        
        # Verify the message content
        call_args = mock_connection_manager.send_to_user.call_args_list[0]
        message_data = call_args[0][1]  # Second argument is the message
        assert message_data["type"] == "session_update"
        assert message_data["session_id"] == session_id
        assert message_data["data"] == data
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_broadcast_system_health(self, broadcaster, mock_connection_manager):
        """Test broadcasting system health update."""
        # Disable batching for this test to get immediate sending
        broadcaster.configure_batching(enabled=False)
        
        status = "degraded"
        services = {"database": "healthy", "llm": "degraded"}
        
        sent_count = await broadcaster.broadcast_system_health_update(status, services)
        
        # With batching disabled, it should call send_to_user for each user
        assert mock_connection_manager.send_to_user.call_count == 3
        assert sent_count == 3
        
        # Verify the message content
        call_args = mock_connection_manager.send_to_user.call_args_list[0]
        message_data = call_args[0][1]  # Second argument is the message
        assert message_data["type"] == "system_health"
        assert message_data["status"] == status
        assert message_data["services"] == services
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_broadcast_alert_status(self, broadcaster, mock_connection_manager):
        """Test broadcasting alert status update."""
        # Disable batching for this test to get immediate sending
        broadcaster.configure_batching(enabled=False)
        
        alert_data = {
            "alert_id": "alert_456",
            "status": "completed",
            "progress": 100,
            "current_step": "Resolution complete",
            "result": "Issue resolved"
        }
        
        sent_count = await broadcaster.broadcast_alert_status_update(**alert_data)
        
        # With batching disabled, it should call send_to_user for each user
        assert mock_connection_manager.send_to_user.call_count == 3
        assert sent_count == 3
        
        # Verify the message content
        call_args = mock_connection_manager.send_to_user.call_args_list[0]
        message_data = call_args[0][1]  # Second argument is the message
        assert message_data["type"] == "alert_status"
        assert message_data["alert_id"] == "alert_456"
        assert message_data["status"] == "completed"
        assert message_data["progress"] == 100


class TestConcurrencyAndStress:
    """Test broadcaster under concurrent load."""
    
    @pytest.fixture
    def mock_connection_manager(self):
        """Create mock connection manager."""
        manager = Mock()
        manager.broadcast_to_channel = AsyncMock(return_value=1)
        manager.get_channel_subscribers = Mock(return_value={"user1", "user2", "user3"})
        manager.send_to_user = AsyncMock(return_value=True)
        return manager
    
    @pytest.fixture
    def broadcaster(self, mock_connection_manager):
        """Create DashboardBroadcaster instance."""
        return DashboardBroadcaster(mock_connection_manager)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_concurrent_broadcasting(self, broadcaster, mock_connection_manager):
        """Test concurrent message broadcasting."""
        channel = ChannelType.DASHBOARD_UPDATES
        
        # Start broadcaster
        await broadcaster.start()
        
        try:
            # Send multiple messages concurrently
            tasks = []
            for i in range(10):
                message = DashboardUpdate(data={"message": f"test_{i}"})
                task = asyncio.create_task(
                    broadcaster.broadcast_message(channel, message)
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            assert all(result >= 0 for result in results)
            
        finally:
            await broadcaster.stop()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_multiple_channels_concurrent(self, broadcaster, mock_connection_manager):
        """Test broadcasting to multiple channels concurrently."""
        # Disable batching to test direct concurrent broadcasting
        broadcaster.configure_batching(enabled=False)
        
        channels = [
            ChannelType.DASHBOARD_UPDATES,
            ChannelType.SYSTEM_HEALTH,
            "session_123",
            "session_456"
        ]
        
        # Send messages to different channels concurrently
        tasks = []
        for i, channel in enumerate(channels):
            if channel.startswith("session_"):
                message = SessionUpdate(
                    session_id=channel.split("_")[1],
                    data={"test": f"data_{i}"}
                )
            else:
                message = DashboardUpdate(data={"test": f"data_{i}"})
            
            task = asyncio.create_task(
                broadcaster.broadcast_message(channel, message)
            )
            tasks.append(task)
        
        # Wait for all broadcasts to complete
        results = await asyncio.gather(*tasks)
        
        # All broadcasts should succeed
        assert all(result >= 0 for result in results)
        
        # Total calls should equal number of channels * users per channel
        expected_calls = len(channels) * 3  # 3 users per channel
        assert mock_connection_manager.send_to_user.call_count == expected_calls
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_broadcaster_resilience(self, broadcaster, mock_connection_manager):
        """Test broadcaster resilience to connection manager failures."""
        # Disable batching so messages go directly through send_to_user
        broadcaster.configure_batching(enabled=False)
        
        # Configure connection manager send_to_user to sometimes fail
        call_count = 0
        
        async def sometimes_fail(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:  # Fail every 3rd call
                return False  # Simulate send failure
            return True
        
        mock_connection_manager.send_to_user.side_effect = sometimes_fail
        
        await broadcaster.start()
        
        try:
            # Send multiple messages
            total_sent = 0
            for i in range(3):  # Send 3 messages to 3 users each = 9 total sends
                message = DashboardUpdate(data={"test": f"data_{i}"})
                sent_count = await broadcaster.broadcast_message(ChannelType.DASHBOARD_UPDATES, message)
                total_sent += sent_count
            
            # Should have had some successful sends despite failures
            # 9 total sends, every 3rd fails = 6 successful
            assert total_sent == 6  
            
        finally:
            await broadcaster.stop()


if __name__ == "__main__":
    pytest.main([__file__]) 