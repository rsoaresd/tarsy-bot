"""
Summary agent for generating concise 1-2 line final analysis summary for external notifications.

This lightweight agent creates AI-powered summaries after chain completion,
specifically for Slack notifications and other external integrations.
"""

from typing import Optional, TYPE_CHECKING

from tarsy.models.constants import LLMInteractionType
from tarsy.models.unified_interactions import LLMConversation, LLMMessage, MessageRole
from tarsy.utils.logger import get_module_logger
from tarsy.agents.prompts.builders import PromptBuilder


if TYPE_CHECKING:
    from tarsy.integrations.llm.client import LLMClient

logger = get_module_logger(__name__)


class SummaryAgent:
    """
    Lightweight agent for generating concise final analysis summaries of completed alert investigations.
    
    This agent uses LLM to create 1-2 line final analysis summaries
    suitable for external notifications (Slack, etc.).
    """
    
    def __init__(self, llm_client: 'LLMClient'):
        """
        Initialize summarizer with LLM client and prompt builder.
        
        Args:
            llm_client: The LLM client (actually LLMManager) to use for summarization
        """
        self.llm_client = llm_client
        self.prompt_builder = PromptBuilder()
    
    async def generate_summary(
        self,
        content: str,
        session_id: str,
        stage_execution_id: Optional[str] = None,
        max_tokens: int = 150
    ) -> Optional[str]:
        """
        Generate a concise 1-2 line final analysis summary of the content.
        
        This final analysis summary is optimized for external notifications (Slack, etc.) where
        brevity is crucial.
        
        Args:
            content: The content to summarize
            session_id: Session ID for tracking
            stage_execution_id: Optional stage execution ID (typically None for post-chain)
            max_tokens: Maximum tokens for final analysis summary (default: 150 for 1-2 lines)
            
        Returns:
            1-2 line final analysis summary string, or None if generation fails
            
        Raises:
            Exception: If summarization fails critically
        """
        if not content:
            logger.warning("No content provided for final analysis summary")
            return None
        
        try:
            # Build summarization prompt using the existing builder
            summary_prompt = self.prompt_builder.build_summary_prompt(content)
            
            # Create system message
            system_message = LLMMessage(
                role=MessageRole.SYSTEM,
                content="You are a helpful assistant that creates concise summaries for alert notifications."
            )
            
            # Create user message with the prompt
            user_message = LLMMessage(
                role=MessageRole.USER,
                content=summary_prompt
            )
            
            # Create conversation with both messages
            conversation = LLMConversation(messages=[system_message, user_message])
            
            # Generate summary using LLM client with RESULT_SUMMARY interaction type
            response_conversation = await self.llm_client.generate_response(
                conversation=conversation,
                session_id=session_id,
                stage_execution_id=stage_execution_id,
                max_tokens=max_tokens,
                interaction_type=LLMInteractionType.FINAL_ANALYSIS_SUMMARY.value  # NEW TYPE
            )
            
            # Extract summary from response
            assistant_message = response_conversation.get_latest_assistant_message()
            if not assistant_message:
                logger.error("No assistant response received for final analysis summary generation")
                return None
            
            final_analysis_summary_response = assistant_message.content.strip()
            
            # Clean up the response (remove common prefixes)
            if final_analysis_summary_response.startswith("Resume:"):
                final_analysis_summary_response = final_analysis_summary_response[7:].strip()
            elif final_analysis_summary_response.startswith("Summary:"):
                final_analysis_summary_response = final_analysis_summary_response[8:].strip()

            logger.info(f"Generated result summary for session {session_id}: {final_analysis_summary_response[:100]}...")
            return final_analysis_summary_response
            
        except Exception as e:
            logger.error(f"Failed to generate result summary for session {session_id}: {e}")
            return None
