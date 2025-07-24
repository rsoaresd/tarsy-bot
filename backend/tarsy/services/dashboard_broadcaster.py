"""
Dashboard broadcaster for sending filtered updates to subscribed clients.
"""

import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Set, Any, Optional, Callable

from tarsy.utils.logger import get_module_logger
from tarsy.models.websocket_models import (
    ChannelType,
    OutgoingMessage,
    DashboardUpdate,
    SessionUpdate,
    SystemHealthUpdate,
    AlertStatusUpdate
)

logger = get_module_logger(__name__)


class MessageBatch:
    """Container for batched messages."""
    
    def __init__(self, max_size: int = 10, max_age_seconds: int = 1):
        self.messages: List[OutgoingMessage] = []
        self.created_at = datetime.now()
        self.max_size = max_size
        self.max_age_seconds = max_age_seconds
    
    def add_message(self, message: OutgoingMessage) -> bool:
        """Add message to batch. Returns True if batch is ready to send."""
        self.messages.append(message)
        return self.is_ready()
    
    def is_ready(self) -> bool:
        """Check if batch is ready to send."""
        age = (datetime.now() - self.created_at).total_seconds()
        return len(self.messages) >= self.max_size or age >= self.max_age_seconds
    
    def get_batched_message(self) -> Dict[str, Any]:
        """Create a batched message containing all messages."""
        return {
            "type": "message_batch",
            "timestamp": datetime.now().isoformat(),
            "count": len(self.messages),
            "messages": [msg.model_dump() if hasattr(msg, 'model_dump') else msg 
                        for msg in self.messages]
        }


class DashboardBroadcaster:
    """Advanced message broadcasting system for dashboard clients."""
    
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        
        # Message batching configuration
        self.batching_enabled = True
        self.batch_size = 5
        self.batch_timeout_seconds = 2
        
        # Active batches per channel
        self.active_batches: Dict[str, MessageBatch] = {}
        
        # Message filtering and throttling
        self.message_filters: Dict[str, List[Callable]] = {}
        self.throttle_limits: Dict[str, Dict[str, Any]] = {}
        self.user_message_counts: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        
        # Background task for batch processing
        self.batch_processor_task: Optional[asyncio.Task] = None
        self.running = False
        
        # Statistics
        self.stats = {
            "messages_sent": 0,
            "messages_batched": 0,
            "messages_filtered": 0,
            "messages_throttled": 0,
            "broadcasts_sent": 0
        }
    
    async def start(self):
        """Start the broadcaster background tasks."""
        if not self.running:
            self.running = True
            self.batch_processor_task = asyncio.create_task(self._batch_processor())
            logger.info("DashboardBroadcaster started")
    
    async def stop(self):
        """Stop the broadcaster background tasks."""
        self.running = False
        if self.batch_processor_task:
            self.batch_processor_task.cancel()
            try:
                await self.batch_processor_task
            except asyncio.CancelledError:
                pass
        logger.info("DashboardBroadcaster stopped")
    
    async def _batch_processor(self):
        """Background task to process message batches."""
        while self.running:
            try:
                # Check for ready batches
                ready_batches = []
                for channel, batch in list(self.active_batches.items()):
                    if batch.is_ready():
                        ready_batches.append((channel, batch))
                
                # Send ready batches
                for channel, batch in ready_batches:
                    await self._send_batch(channel, batch)
                    del self.active_batches[channel]
                
                # Wait before next check
                await asyncio.sleep(0.5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch processor: {str(e)}")
                await asyncio.sleep(1)
    
    async def _send_batch(self, channel: str, batch: MessageBatch):
        """Send a message batch to channel subscribers."""
        batched_message = batch.get_batched_message()
        sent_count = await self.connection_manager.broadcast_to_channel(
            channel, 
            batched_message
        )
        
        self.stats["broadcasts_sent"] += 1
        self.stats["messages_batched"] += len(batch.messages)
        
        logger.debug(f"Sent batch of {len(batch.messages)} messages to {sent_count} subscribers on channel {channel}")
    
    def add_message_filter(self, channel: str, filter_func: Callable):
        """Add a message filter for a specific channel."""
        if channel not in self.message_filters:
            self.message_filters[channel] = []
        self.message_filters[channel].append(filter_func)
        logger.debug(f"Added message filter for channel: {channel}")
    
    def set_throttle_limit(self, channel: str, max_messages: int, time_window_seconds: int):
        """Set throttle limits for a channel."""
        self.throttle_limits[channel] = {
            "max_messages": max_messages,
            "time_window": time_window_seconds
        }
        logger.debug(f"Set throttle limit for channel {channel}: {max_messages} messages per {time_window_seconds}s")
    
    def _should_throttle_user(self, user_id: str, channel: str) -> bool:
        """Check if user should be throttled for this channel."""
        if channel not in self.throttle_limits:
            return False
        
        limits = self.throttle_limits[channel]
        user_messages = self.user_message_counts[user_id][channel]
        
        # Clean old messages outside time window
        cutoff_time = datetime.now() - timedelta(seconds=limits["time_window"])
        while user_messages and user_messages[0] < cutoff_time:
            user_messages.popleft()
        
        # Check if user exceeds limit
        return len(user_messages) >= limits["max_messages"]
    
    def _record_user_message(self, user_id: str, channel: str):
        """Record that a message was sent to a user."""
        self.user_message_counts[user_id][channel].append(datetime.now())
    
    def _apply_message_filters(self, channel: str, message: OutgoingMessage, user_id: str) -> bool:
        """Apply message filters to determine if message should be sent."""
        filters = self.message_filters.get(channel, [])
        
        for filter_func in filters:
            try:
                if not filter_func(message, user_id):
                    self.stats["messages_filtered"] += 1
                    return False
            except Exception as e:
                logger.error(f"Message filter error for channel {channel}: {str(e)}")
                # On filter error, default to allowing message
                continue
        
        return True
    
    async def broadcast_dashboard_update(
        self, 
        data: Dict[str, Any], 
        exclude_users: Set[str] = None
    ) -> int:
        """Broadcast a dashboard update to dashboard_updates channel."""
        update = DashboardUpdate(data=data)
        return await self.broadcast_message(
            ChannelType.DASHBOARD_UPDATES, 
            update, 
            exclude_users
        )
    
    async def broadcast_session_update(
        self, 
        session_id: str, 
        data: Dict[str, Any],
        exclude_users: Set[str] = None
    ) -> int:
        """Broadcast a session-specific update."""
        update = SessionUpdate(session_id=session_id, data=data)
        channel = ChannelType.session_channel(session_id)
        return await self.broadcast_message(channel, update, exclude_users)
    
    async def broadcast_system_health_update(
        self, 
        status: str, 
        services: Dict[str, Any],
        exclude_users: Set[str] = None
    ) -> int:
        """Broadcast system health update."""
        update = SystemHealthUpdate(status=status, services=services)
        return await self.broadcast_message(
            ChannelType.SYSTEM_HEALTH, 
            update, 
            exclude_users
        )
    
    async def broadcast_alert_status_update(
        self,
        alert_id: str,
        status: str,
        progress: int,
        current_step: str,
        current_agent: Optional[str] = None,
        assigned_mcp_servers: Optional[List[str]] = None,
        result: Optional[str] = None,
        error: Optional[str] = None,
        exclude_users: Set[str] = None
    ) -> int:
        """Broadcast alert processing status update."""
        update = AlertStatusUpdate(
            alert_id=alert_id,
            status=status,
            progress=progress,
            current_step=current_step,
            current_agent=current_agent,
            assigned_mcp_servers=assigned_mcp_servers,
            result=result,
            error=error
        )
        return await self.broadcast_message(
            ChannelType.DASHBOARD_UPDATES, 
            update, 
            exclude_users
        )
    
    async def broadcast_message(
        self, 
        channel: str, 
        message: OutgoingMessage, 
        exclude_users: Set[str] = None
    ) -> int:
        """Core broadcast method with filtering, batching, and throttling."""
        exclude_users = exclude_users or set()
        
        # Get channel subscribers
        subscribers = self.connection_manager.get_channel_subscribers(channel)
        if not subscribers:
            logger.debug(f"No subscribers for channel: {channel}")
            return 0
        
        # Apply user exclusions
        target_users = subscribers - exclude_users
        if not target_users:
            logger.debug(f"No target users for channel {channel} after exclusions")
            return 0
        
        # Filter users based on throttling and message filters
        eligible_users = set()
        for user_id in target_users:
            # Check throttling
            if self._should_throttle_user(user_id, channel):
                self.stats["messages_throttled"] += 1
                logger.debug(f"Throttled user {user_id} for channel {channel}")
                continue
            
            # Apply message filters
            if not self._apply_message_filters(channel, message, user_id):
                continue
            
            eligible_users.add(user_id)
        
        if not eligible_users:
            logger.debug(f"No eligible users for channel {channel} after filtering")
            return 0
        
        # Handle batching vs immediate sending
        if self.batching_enabled and len(eligible_users) > 1:
            # Add to batch
            if channel not in self.active_batches:
                self.active_batches[channel] = MessageBatch(
                    max_size=self.batch_size,
                    max_age_seconds=self.batch_timeout_seconds
                )
            
            batch = self.active_batches[channel]
            if batch.add_message(message):
                # Batch is ready, send immediately
                await self._send_batch(channel, batch)
                del self.active_batches[channel]
            
            # Record messages for throttling
            for user_id in eligible_users:
                self._record_user_message(user_id, channel)
            
            sent_count = len(eligible_users)
        else:
            # Send immediately without batching
            message_dict = message.model_dump() if hasattr(message, 'model_dump') else message
            sent_count = 0
            
            for user_id in eligible_users:
                success = await self.connection_manager.send_to_user(user_id, message_dict)
                if success:
                    sent_count += 1
                    self._record_user_message(user_id, channel)
        
        self.stats["messages_sent"] += sent_count
        logger.debug(f"Broadcast message to {sent_count} users on channel {channel}")
        return sent_count
    
    def get_broadcast_stats(self) -> Dict[str, Any]:
        """Get broadcasting statistics."""
        return {
            **self.stats,
            "active_batches": len(self.active_batches),
            "message_filters": sum(len(filters) for filters in self.message_filters.values()),
            "throttle_limits": len(self.throttle_limits),
            "batching_enabled": self.batching_enabled,
            "batch_size": self.batch_size,
            "batch_timeout": self.batch_timeout_seconds
        }
    
    def configure_batching(self, enabled: bool, batch_size: int = 5, timeout_seconds: int = 2):
        """Configure message batching settings."""
        self.batching_enabled = enabled
        self.batch_size = batch_size
        self.batch_timeout_seconds = timeout_seconds
        logger.info(f"Batching configured: enabled={enabled}, size={batch_size}, timeout={timeout_seconds}s") 