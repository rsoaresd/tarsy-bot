"""
Subscription manager for dashboard WebSocket channels.
"""

from typing import Dict, List, Set, Optional, Callable, Any
from datetime import datetime

from tarsy.utils.logger import get_module_logger
from tarsy.models.websocket_models import (
    ChannelType, 
    OutgoingMessage,
    SubscriptionMessage,
    SubscriptionResponse,
)

logger = get_module_logger(__name__)


class SubscriptionManager:
    """Advanced subscription management for dashboard channels."""
    
    def __init__(self):
        # Channel metadata and configuration
        self.channel_config: Dict[str, Dict[str, Any]] = {
            ChannelType.DASHBOARD_UPDATES: {
                "max_subscribers": 100,
                "requires_auth": False,
                "persistent": True,
                "description": "General dashboard updates and alerts"
            },
            ChannelType.SYSTEM_HEALTH: {
                "max_subscribers": 50,
                "requires_auth": False, 
                "persistent": True,
                "description": "System health status updates"
            }
        }
        
        # Dynamic session channel tracking
        self.session_channels: Set[str] = set()
        
        # Subscription event callbacks
        self.subscription_callbacks: Dict[str, List[Callable]] = {}
        
        # Channel activity tracking
        self.channel_activity: Dict[str, datetime] = {}
        
        # Message filters per channel
        self.channel_filters: Dict[str, List[Callable]] = {}
    
    def validate_channel(self, channel: str) -> tuple[bool, Optional[str]]:
        """Validate if a channel is valid for subscription."""
        # Check predefined channels
        if channel in self.channel_config:
            config = self.channel_config[channel]
            # Could add authorization checks here if needed
            return True, None
        
        # Check session channels
        if ChannelType.is_session_channel(channel):
            session_id = ChannelType.extract_session_id(channel)
            if session_id:
                # Add to tracked session channels
                self.session_channels.add(channel)
                return True, None
            else:
                return False, "Invalid session channel format"
        
        # Unknown channel
        return False, f"Unknown channel: {channel}"
    
    def get_channel_info(self, channel: str) -> Optional[Dict[str, Any]]:
        """Get information about a channel."""
        if channel in self.channel_config:
            return self.channel_config[channel].copy()
        elif ChannelType.is_session_channel(channel):
            session_id = ChannelType.extract_session_id(channel)
            return {
                "max_subscribers": 10,
                "requires_auth": False,
                "persistent": False,
                "description": f"Updates for session {session_id}",
                "session_id": session_id
            }
        return None
    
    def process_subscription_request(
        self, 
        user_id: str, 
        message: SubscriptionMessage
    ) -> SubscriptionResponse:
        """Process a subscription request and return appropriate response."""
        channel = message.channel
        action = message.type
        
        # Validate channel
        is_valid, error_msg = self.validate_channel(channel)
        if not is_valid:
            logger.warning(f"Invalid subscription request from {user_id} to channel {channel}: {error_msg}")
            return SubscriptionResponse(
                action=action,
                channel=channel,
                success=False,
                message=error_msg
            )
        
        # Update channel activity
        self.channel_activity[channel] = datetime.now()
        
        # Check channel limits (if any)
        channel_info = self.get_channel_info(channel)
        if channel_info and "max_subscribers" in channel_info:
            # This would require integration with connection manager to check current subscriber count
            # For now, we'll assume it's within limits
            pass
        
        # Log successful subscription request
        logger.info(f"Processed {action} request from {user_id} for channel {channel}")
        
        # Trigger subscription callbacks
        self._trigger_subscription_callbacks(channel, user_id, action)
        
        return SubscriptionResponse(
            action=action,
            channel=channel, 
            success=True,
            message=f"Successfully {action}d to {channel}"
        )
    
    def add_subscription_callback(self, channel: str, callback: Callable):
        """Add a callback function for subscription events on a channel."""
        if channel not in self.subscription_callbacks:
            self.subscription_callbacks[channel] = []
        self.subscription_callbacks[channel].append(callback)
    
    def _trigger_subscription_callbacks(self, channel: str, user_id: str, action: str):
        """Trigger subscription callbacks for a channel."""
        callbacks = self.subscription_callbacks.get(channel, [])
        for callback in callbacks:
            try:
                callback(channel, user_id, action)
            except Exception as e:
                logger.error(f"Subscription callback error for channel {channel}: {str(e)}")
    
    def add_message_filter(self, channel: str, filter_func: Callable):
        """Add a message filter for a specific channel."""
        if channel not in self.channel_filters:
            self.channel_filters[channel] = []
        self.channel_filters[channel].append(filter_func)
    
    def should_deliver_message(self, channel: str, message: OutgoingMessage, user_id: str) -> bool:
        """Check if a message should be delivered to a user based on channel filters."""
        filters = self.channel_filters.get(channel, [])
        
        for filter_func in filters:
            try:
                if not filter_func(message, user_id):
                    return False
            except Exception as e:
                logger.error(f"Message filter error for channel {channel}: {str(e)}")
                # On filter error, default to allowing message
                continue
        
        return True
    
    def get_subscription_stats(self) -> Dict[str, Any]:
        """Get subscription statistics."""
        return {
            "predefined_channels": len(self.channel_config),
            "session_channels": len(self.session_channels),
            "total_channels": len(self.channel_config) + len(self.session_channels),
            "channels_with_callbacks": len(self.subscription_callbacks),
            "channels_with_filters": len(self.channel_filters),
            "recent_activity": len([
                channel for channel, last_activity in self.channel_activity.items()
                if (datetime.now() - last_activity).seconds < 300  # Active in last 5 minutes
            ])
        }
    
    def cleanup_inactive_channels(self, max_age_minutes: int = 60):
        """Clean up inactive session channels."""
        cutoff_time = datetime.now()
        inactive_channels = []
        
        for channel in list(self.session_channels):
            last_activity = self.channel_activity.get(channel)
            if last_activity and (cutoff_time - last_activity).seconds > (max_age_minutes * 60):
                inactive_channels.append(channel)
        
        # Remove inactive channels
        for channel in inactive_channels:
            self.session_channels.discard(channel)
            self.channel_activity.pop(channel, None)
            self.subscription_callbacks.pop(channel, None)
            self.channel_filters.pop(channel, None)
            
        if inactive_channels:
            logger.info(f"Cleaned up {len(inactive_channels)} inactive session channels")
        
        return len(inactive_channels)
    
    def get_active_session_channels(self) -> List[str]:
        """Get list of currently active session channels."""
        return list(self.session_channels)
    
    def is_channel_persistent(self, channel: str) -> bool:
        """Check if a channel is persistent (should not be auto-cleaned)."""
        channel_info = self.get_channel_info(channel)
        return channel_info.get("persistent", False) if channel_info else False 