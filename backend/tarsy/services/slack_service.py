"""
Slack Notification Service
Handles sending notifications to Slack channel for alert processing events.
"""

import time
from typing import Any, Dict, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from tarsy.config.settings import Settings
from tarsy.utils.logger import get_module_logger


logger = get_module_logger(__name__)


class SlackService:
    """
    Service for sending notifications to Slack channels.
    
    Supports:
    - Alert processing completion notifications
    - Alert processing failure notifications  
    - System error notifications
    """

    def __init__(self, settings: Settings):
        """
        Initialize Slack service with settings.
        
        Args:
            settings: Application settings containing Slack configuration
        """
        self.settings = settings

        # Check if Slack is configured
        self.enabled = bool(
            self.settings.slack_bot_token and 
            self.settings.slack_bot_token.strip() and
            self.settings.slack_channel and 
            self.settings.slack_channel.strip()
        )

        if self.enabled:
            self.client = WebClient(self.settings.slack_bot_token)
            logger.info(f"Slack notifications enabled for channel {self.settings.slack_channel}")
        else:
            self.client = None
            logger.info("Slack notifications disabled - no webhook URL configured")

    async def send_alert_notification(
        self,
        session_id: str,
        fingerprint: Optional[str] = None,
        analysis: Optional[str] = None,
        error: Optional[str] = None,
    ) -> bool:
        """
        Send notification for alert processing event.
        
        Args:
            session_id: Session ID for tracking
            fingerprint: Fingerprint of the alert
            analysis: Analysis result (for successful processing)
            error: Error message (for failed processing)
                    
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Slack notifications disabled - skipping")
            return False

        try:
            if not fingerprint or not fingerprint.strip():
                logger.error(f"No fingerprint found for {session_id}")
                return False

            if analysis and error:
                logger.error(f"Both analysis and error provided for session {session_id}")
                return False

            find_alert_message = await self.find_alert_message(
                fingerprint=fingerprint,
            )

            if not find_alert_message:
                logger.error(f"Failed to find alert message for session {session_id}")
                return False
        
            success = await self.reply_to_alert_directly(
                    session_id=session_id,
                    message_ts=find_alert_message,
                    analysis=analysis,
                    error=error,
                )

            if success:
                logger.info(f"Slack notification sent for session {session_id}")
            else:
                logger.warning(f"Failed to send Slack notification for session {session_id}")

            return success

        except Exception as e:
            logger.error(f"Error sending Slack notification for session {session_id}: {str(e)}")
            return False

    async def find_alert_message(
        self, 
        fingerprint: str,
    ) -> Optional[str]:
        """
        Find the target alert message to reply to.
        
        Args:
            fingerprint: identifier of the alert
        
        Returns:
            Message timestamp (ts) if found, None otherwise
        """
            
        try:
            # last 24 hours
            current_time = time.time()
            lookback_seconds = 24 * 3600
            oldest = current_time - lookback_seconds

            # Search for messages in the channel
            history = self.client.conversations_history(
                channel=self.settings.slack_channel,
                oldest=str(int(oldest)),
                limit=20
            )
            
            # Find message containing the fingerprint identifier
            for message in history["messages"]:
                # Check in message text
                message_text = message.get("text", "")
                
                # Also check in attachments if present (many alert bots use attachments)
                attachments = message.get("attachments", [])
                for attachment in attachments:
                    attachment_text = attachment.get("text", "") + attachment.get("fallback", "")
                    message_text += " " + attachment_text
                
                # Search for fingerprint in combined text
                if fingerprint in message_text:
                    logger.info(f"Found message with fingerprint {fingerprint}: ts={message['ts']}")
                    return message["ts"]
            
            logger.error(f"No message found with fingerprint: {fingerprint}")
            return None

        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return None

    async def reply_to_alert_directly(
        self,
        session_id: str,
        message_ts: str,
        analysis: Optional[str] = None,
        error: Optional[str] = None,
    ) -> bool:
        """Reply directly to a message using its ts - no search needed."""

        try:
            channel_id = self.settings.slack_channel
            
            message_data = self._format_alert_message(session_id=session_id, analysis=analysis, error=error)
            
            self.client.chat_postMessage(
                channel=channel_id,
                attachments=message_data["attachments"],
                thread_ts=message_ts
            )
            
            return True
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return False

    def _format_alert_message(
            self,
            session_id: str,
            analysis: Optional[str] = None,
            error: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Format alert message for Slack."""
            text_parts = []

            if analysis:
                text_parts.extend(["*Analysis:*", "", analysis])
            elif error:
                text_parts.extend(["*Error:*", "", error])

            dashboard_url = self.settings.cors_origins[0] if self.settings.cors_origins else "http://localhost:5173"

            text_parts.extend([
                "",
                f"*View Analysis Details:* {dashboard_url}/sessions/{session_id}"
            ])

            return {
                "channel": self.settings.slack_channel,
                "attachments": [
                    {
                        "color": "danger",
                        "text": "\n".join(text_parts),
                        "mrkdwn_in": ["text"]
                    }
                ]
            }
