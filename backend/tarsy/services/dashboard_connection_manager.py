"""
Dashboard connection manager for WebSocket connections.
"""

import json
from datetime import datetime
from typing import Dict, List, Set

from fastapi import WebSocket
from pydantic import ValidationError

from tarsy.utils.logger import get_module_logger
from tarsy.services.subscription_manager import SubscriptionManager
from tarsy.models.websocket_models import (
    ChannelType,
    SubscriptionMessage,
    SubscriptionResponse,
    ConnectionEstablished,
    ErrorMessage,
    OutgoingMessage
)

logger = get_module_logger(__name__)


class DashboardConnectionManager:
    """Manages WebSocket connections for dashboard real-time updates."""
    
    def __init__(self):
        # Dictionary to store active connections by user_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Track subscriptions per user: user_id -> set of channels
        self.user_subscriptions: Dict[str, Set[str]] = {}
        # Track channels to users mapping for efficient broadcasting
        self.channel_subscribers: Dict[str, Set[str]] = {}
        # Enhanced subscription management
        self.subscription_manager = SubscriptionManager()
        # Advanced broadcasting with batching and throttling
        self.broadcaster = None  # Will be initialized after connection manager is created
        # Dashboard update service for intelligent update management
        self.update_service = None  # Will be initialized after broadcaster is created
    
    def _datetime_serializer(self, obj):
        """Custom JSON serializer for datetime objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a WebSocket for a specific user."""
        await websocket.accept()
        
        # Store connection
        self.active_connections[user_id] = websocket
        
        # Initialize subscription tracking
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        
        logger.info(f"Dashboard connection established for user: {user_id}")
    
    def disconnect(self, user_id: str):
        """Disconnect a WebSocket and clean up subscriptions."""
        if user_id in self.active_connections:
            # Remove from active connections
            del self.active_connections[user_id]
            
            # Clean up subscriptions
            if user_id in self.user_subscriptions:
                user_channels = self.user_subscriptions[user_id].copy()
                for channel in user_channels:
                    self._unsubscribe_from_channel(user_id, channel)
                del self.user_subscriptions[user_id]
            
            logger.info(f"Dashboard connection disconnected for user: {user_id}")
    
    def subscribe_to_channel(self, user_id: str, channel: str):
        """Subscribe user to a specific channel."""
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        
        if user_id not in self.active_connections:
            logger.warning(f"Attempted to subscribe inactive user {user_id} to channel {channel}")
            return False
        
        # Add to user subscriptions
        self.user_subscriptions[user_id].add(channel)
        
        # Add to channel subscribers
        if channel not in self.channel_subscribers:
            self.channel_subscribers[channel] = set()
        self.channel_subscribers[channel].add(user_id)
        
        logger.info(f"User {user_id} subscribed to channel: {channel}")
        return True
    
    def unsubscribe_from_channel(self, user_id: str, channel: str):
        """Unsubscribe user from a specific channel."""
        return self._unsubscribe_from_channel(user_id, channel)
    
    def _unsubscribe_from_channel(self, user_id: str, channel: str):
        """Internal method to unsubscribe user from channel."""
        # Remove from user subscriptions
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(channel)
        
        # Remove from channel subscribers
        if channel in self.channel_subscribers:
            self.channel_subscribers[channel].discard(user_id)
            # Clean up empty channels
            if not self.channel_subscribers[channel]:
                del self.channel_subscribers[channel]
        
        logger.info(f"User {user_id} unsubscribed from channel: {channel}")
        return True
    
    def _internal_subscribe(self, user_id: str, channel: str):
        """Internal method to handle subscription state management."""
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        
        if user_id not in self.active_connections:
            logger.warning(f"Attempted to subscribe inactive user {user_id} to channel {channel}")
            return False
        
        # Add to user subscriptions
        self.user_subscriptions[user_id].add(channel)
        
        # Add to channel subscribers
        if channel not in self.channel_subscribers:
            self.channel_subscribers[channel] = set()
        self.channel_subscribers[channel].add(user_id)
        
        return True
    
    def _internal_unsubscribe(self, user_id: str, channel: str):
        """Internal method to handle unsubscription state management."""
        # Remove from user subscriptions
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(channel)
        
        # Remove from channel subscribers
        if channel in self.channel_subscribers:
            self.channel_subscribers[channel].discard(user_id)
            # Clean up empty channels
            if not self.channel_subscribers[channel]:
                del self.channel_subscribers[channel]
        
        return True
    
    def get_user_subscriptions(self, user_id: str) -> Set[str]:
        """Get all channels a user is subscribed to."""
        return self.user_subscriptions.get(user_id, set()).copy()
    
    def get_channel_subscribers(self, channel: str) -> Set[str]:
        """Get all users subscribed to a channel."""
        return self.channel_subscribers.get(channel, set()).copy()
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send a message to a specific user."""
        if user_id not in self.active_connections:
            logger.warning(f"Attempted to send message to inactive user: {user_id}")
            return False
        
        try:
            message_json = json.dumps(message, default=self._datetime_serializer)
            await self.active_connections[user_id].send_text(message_json)
            return True
        except Exception as e:
            logger.error(f"Failed to send message to user {user_id}: {str(e)}")
            # Clean up broken connection
            self.disconnect(user_id)
            return False
    
    async def broadcast_to_channel(self, channel: str, message: dict, exclude_users: Set[str] = None):
        """Broadcast message to all users subscribed to a channel."""
        if channel not in self.channel_subscribers:
            logger.debug(f"No subscribers for channel: {channel}")
            return 0
        
        exclude_users = exclude_users or set()
        subscribers = self.channel_subscribers[channel] - exclude_users
        
        if not subscribers:
            logger.debug(f"No eligible subscribers for channel {channel} after exclusions")
            return 0
        
        sent_count = 0
        failed_users = []
        
        for user_id in subscribers:
            success = await self.send_to_user(user_id, message)
            if success:
                sent_count += 1
            else:
                failed_users.append(user_id)
        
        if failed_users:
            logger.warning(f"Failed to send to {len(failed_users)} users in channel {channel}")
        
        logger.debug(f"Broadcast to channel {channel}: {sent_count} successful, {len(failed_users)} failed")
        return sent_count
    
    async def handle_subscription_message(self, user_id: str, message: dict):
        """Handle subscription/unsubscription messages from clients."""
        try:
            # Validate and parse subscription message
            subscription_msg = SubscriptionMessage(**message)
            
            # Process subscription request through subscription manager
            response = self.subscription_manager.process_subscription_request(
                user_id, subscription_msg
            )
            
            # If subscription manager approved, update connection state
            if response.success:
                if subscription_msg.type == "subscribe":
                    self._internal_subscribe(user_id, subscription_msg.channel)
                elif subscription_msg.type == "unsubscribe":
                    self._internal_unsubscribe(user_id, subscription_msg.channel)
            
            # Send response to user
            await self.send_to_user(user_id, response.model_dump())
            
        except ValidationError as e:
            # Handle invalid message format
            error_response = ErrorMessage(
                message=f"Invalid subscription message format: {str(e)}"
            )
            await self.send_to_user(user_id, error_response.model_dump())
        except Exception as e:
            # Handle other errors
            logger.error(f"Error handling subscription message from {user_id}: {str(e)}")
            error_response = ErrorMessage(
                message="Internal error processing subscription request"
            )
            await self.send_to_user(user_id, error_response.model_dump())
    
    def get_connection_stats(self):
        """Get connection statistics for monitoring."""
        connection_stats = {
            "active_connections": len(self.active_connections),
            "total_subscriptions": sum(len(subs) for subs in self.user_subscriptions.values()),
            "active_channels": len(self.channel_subscribers),
            "users_with_subscriptions": len(self.user_subscriptions)
        }
        
        # Include subscription manager statistics
        subscription_stats = self.subscription_manager.get_subscription_stats()
        
        return {
            **connection_stats,
            "subscription_manager": subscription_stats
        }
    
    async def broadcast_system_health_update(self, status: str, services: dict):
        """Broadcast system health update to system_health channel subscribers."""
        from tarsy.models.websocket_models import SystemHealthUpdate
        
        health_update = SystemHealthUpdate(
            status=status,
            services=services
        )
        
        sent_count = await self.broadcast_to_channel(
            ChannelType.SYSTEM_HEALTH, 
            health_update.model_dump()
        )
        
        logger.debug(f"Broadcast system health update to {sent_count} subscribers")
        return sent_count
    
    async def initialize_broadcaster(self):
        """Initialize the advanced broadcaster and update service."""
        from tarsy.services.dashboard_broadcaster import DashboardBroadcaster
        from tarsy.services.dashboard_update_service import DashboardUpdateService
        
        if self.broadcaster is None:
            self.broadcaster = DashboardBroadcaster(self)
            await self.broadcaster.start()
            logger.info("Dashboard broadcaster initialized and started")
            
            # Initialize update service with broadcaster
            self.update_service = DashboardUpdateService(self.broadcaster)
            await self.update_service.start()
            logger.info("Dashboard update service initialized and started")
        
        return self.broadcaster
    
    async def shutdown_broadcaster(self):
        """Shutdown the broadcaster and update service."""
        if self.update_service:
            await self.update_service.stop()
            self.update_service = None
            logger.info("Dashboard update service stopped")
            
        if self.broadcaster:
            await self.broadcaster.stop()
            self.broadcaster = None
            logger.info("Dashboard broadcaster stopped")
    
    async def broadcast_with_advanced_features(
        self, 
        channel: str, 
        message: OutgoingMessage, 
        exclude_users: Set[str] = None
    ) -> int:
        """Broadcast message using advanced broadcaster if available, fallback to basic broadcast."""
        if self.broadcaster:
            return await self.broadcaster.broadcast_message(channel, message, exclude_users)
        else:
            # Fallback to basic broadcasting
            message_dict = message.model_dump() if hasattr(message, 'model_dump') else message
            return await self.broadcast_to_channel(channel, message_dict, exclude_users)
    
    def configure_broadcaster(self, **kwargs):
        """Configure broadcaster settings."""
        if self.broadcaster:
            # Configure batching
            if 'batching_enabled' in kwargs:
                self.broadcaster.configure_batching(
                    kwargs.get('batching_enabled', True),
                    kwargs.get('batch_size', 5),
                    kwargs.get('batch_timeout_seconds', 2)
                )
            
            # Configure throttling
            if 'throttle_limits' in kwargs:
                for channel, limits in kwargs['throttle_limits'].items():
                    self.broadcaster.set_throttle_limit(
                        channel, 
                        limits['max_messages'], 
                        limits['time_window_seconds']
                    )
            
            logger.info("Broadcaster configuration updated")
        else:
            logger.warning("Broadcaster not initialized, cannot configure") 