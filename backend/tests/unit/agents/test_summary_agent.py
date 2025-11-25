"""Tests for SummaryAgent."""

import pytest
from unittest.mock import AsyncMock, Mock

from tarsy.agents.summary_agent import SummaryAgent
from tarsy.models.unified_interactions import LLMConversation, LLMMessage, MessageRole


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    client = Mock()
    client.generate_response = AsyncMock()
    return client


@pytest.fixture
def summary_agent(mock_llm_client):
    """Create SummaryAgent with mocked dependencies."""
    return SummaryAgent(llm_client=mock_llm_client)


class TestSummaryAgent:
    """Test suite for SummaryAgent."""
    
    @pytest.mark.asyncio
    async def test_generate_summary_success(self, summary_agent, mock_llm_client):
        """Test successful summary generation."""

        response_conversation = LLMConversation(messages=[
            LLMMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            LLMMessage(role=MessageRole.ASSISTANT, content="Brief summary of the analysis")
        ])
        mock_llm_client.generate_response.return_value = response_conversation
        
        result = await summary_agent.generate_summary(
            content="Long analysis text here...",
            session_id="test-session"
        )
        
        assert result == "Brief summary of the analysis" 
        mock_llm_client.generate_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_summary_empty_analysis(self, summary_agent):
        """Test with empty analysis text."""
        result = await summary_agent.generate_summary(
            content="",
            session_id="test-session"
        ) 
        
        assert result is None