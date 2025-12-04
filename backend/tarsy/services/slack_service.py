"""
Slack Notification Service
Handles sending notifications to Slack channel for alert processing events.
Supports webhooks and provides formatted messages.
"""

from typing import Dict, Any, Optional
import httpx

from tarsy.config.settings import Settings
from tarsy.utils.logger import get_module_logger
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = get_module_logger(__name__)


class SlackService:
    """
    Service for sending notifications to Slack channels.
    
    Supports:
    - Alert processing completion notifications
    - Alert processing failure notifications  
    - System error notifications
    - Configurable webhook URLs and formatting
    """

    def __init__(self, settings: Settings):
        """
        Initialize Slack service with settings.
        
        Args:
            settings: Application settings containing Slack configuration
        """
        self.settings = settings

        # Create HTTP client for Slack API calls
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={'Content-Type': 'application/json'}
        )

        # Check if Slack is configured
        self.enabled = bool(
            self.settings.slack_bot_token and 
            self.settings.slack_bot_token.strip() and
            self.settings.slack_channel and 
            self.settings.slack_channel.strip()
        )

        self.client = WebClient(self.settings.slack_bot_token)

        if self.enabled:
            logger.info(f"Slack notifications enabled for channel {self.settings.slack_channel}")
        else:
            logger.info("Slack notifications disabled - no webhook URL configured")

    async def send_alert_notification(
        self,
        alert_type: str,
        analysis: Optional[str] = None,
        error: Optional[str] = None,
        session_id: Optional[str] = None,
        alert_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send notification for alert processing event.
        
        Args:
            alert_type: Type of alert processed
            analysis: Analysis result (for successful processing)
            error: Error message (for failed processing)
            session_id: Session ID for tracking
            alert_data: Complete alert data for detailed formatting
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Slack notifications disabled - skipping")
            return False

        try:
            print(f"alert_data: {alert_data}")

            # Extract fingerprint from alert_data
            fingerprint = None
            if alert_data and 'message' in alert_data:
                message = alert_data['message']
                # Look for "fingerprint: <value>" pattern in the message
                import re
                match = re.search(r'fingerprint:\s*([^\s\n]+)', message, re.IGNORECASE)
                if match:
                    fingerprint = match.group(1)
                
                print(f"fingerprint: {fingerprint}")
            
            if not fingerprint:
                logger.warning(f"No fingerprint found in alert_data for {alert_type}")
                return False


            find_alert_message = await self.find_alert_message(
                alert_identifier=fingerprint,
                lookback_hours=24
            )
            
            if not find_alert_message:
                logger.warning(f"Failed to find alert message for {alert_type} alert")
                return False
        
            success = await self.reply_to_alert_directly(
                    message_ts=find_alert_message,
                    summary=analysis,
                    session_id=session_id,
                    error=error,
                )

            if success:
                logger.info(f"Slack notification sent for {alert_type} alert")
            else:
                logger.warning(f"Failed to send Slack notification for {alert_type} alert")

            return success

        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
            return False

    async def find_alert_message(
        self, 
        alert_identifier: str,
        lookback_hours: int = 24
    ) -> Optional[str]:
        """
        Find the original alert message from the target bot.
        
        Args:
            alert_identifier: Unique text to search for (alert name, fingerprint, etc)
            lookback_hours: How far back to search
        
        Returns:
            Message timestamp (ts) if found, None otherwise
        """
        if not self.enabled:
            return None
            
        try:
            print("Searching for alert message in channel")
            # Get channel ID from name
      #      channels_response = self.client.conversations_list(
           #         types="private_channel,public_channel"
          #      )

            #    print(f"channels_response: {channels_response}")
            
            #    channel_id = None
            #    for channel in channels_response["channels"]:
             #       if channel["name"] == "test-tarsy":
              #          channel_id = channel["id"]
              #          break
            
           #     print(f"channel_id: {channel_id}")
             #   if not channel_id:
               #     return None
        # Calculate oldest timestamp (Unix timestamp)
            import time
            current_time = time.time()
            lookback_seconds = lookback_hours * 3600
            oldest = current_time - lookback_seconds

            print(f"current_time: {current_time}")
            print(f"lookback_hours: {lookback_hours}")
            print(f"lookback_seconds: {lookback_seconds}")
            print(f"oldest: {oldest}")
            
            # Search for messages in the channel from the alerts bot
            history = self.client.conversations_history(
                channel=self.settings.slack_channel,
                oldest=str(oldest),
                limit=20
            )

            print(f"history: {history}")
            
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
                if alert_identifier in message_text:
                    logger.info(f"Found message with fingerprint {alert_identifier}: ts={message['ts']}")
                    return message["ts"]
            
            logger.warning(f"No message found with fingerprint: {alert_identifier}")
            return None

        except SlackApiError as e:
            print(f"Slack API error: {e.response['error']}")
            return None

    async def reply_to_alert_directly(
        self,
        message_ts: str,
        summary: str,
        session_id: str,
        error: Optional[str] = None,
    ) -> bool:
        """Reply directly to a message using its ts - no search needed."""
        if not self.enabled:
            return False
        
        try:
            channel_id = self.settings.slack_channel
            
            message_data = self._format_alert_message(analysis=summary, error=error, session_id=session_id)
            
            #TODO: add title
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
            analysis: Optional[str] = None,
            error: Optional[str] = None,
            session_id: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Format alert message for Slack."""
            text_parts = []

            if analysis:
                text_parts.extend(["*Analysis:*", "", analysis])
            elif error:
                text_parts.extend(["*Error:*", "", error])

            if session_id:
                text_parts.extend([
                    "",
                    f"*View Analysis Details:* http://localhost:5173/sessions/{session_id}"
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

    async def _send_to_slack(self, message: Dict[str, Any]) -> bool:
        """
        Send formatted message to Slack webhook.
        
        Args:
            message: Formatted Slack message
            
        Returns:
            bool: True if sent successfully
        """
        try:
            response = await self.http_client.post(
                self.settings.slack_webhook_url,
                json=message
            )

            if response.status_code == 200:
                return True
            else:
                logger.error(f"Slack webhook returned status {response.status_code}: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to send to Slack webhook: {str(e)}")
            return False