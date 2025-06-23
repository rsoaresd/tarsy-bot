"""
Unified LLM client implementation using LangChain.
Handles all LLM providers through LangChain's abstraction.
"""

from typing import Dict

from app.integrations.llm.base import BaseLLMClient
from app.models.llm import LLMMessage
from app.utils.prompt_builder import PromptBuilder


class UnifiedLLMClient(BaseLLMClient):
    """Unified LLM client that works with all providers via LangChain."""
    
    def __init__(self, provider_name: str, config: Dict):
        super().__init__(provider_name, config)
        self.prompt_builder = PromptBuilder()
    
    async def analyze_alert(self, 
                          alert_data: Dict, 
                          runbook_data: Dict, 
                          mcp_data: Dict,
                          **kwargs) -> str:
        """Analyze an alert using any LLM provider via LangChain."""
        if not self.available:
            raise Exception(f"{self.provider_name} client not available")
        
        # Build comprehensive prompt
        prompt = self.prompt_builder.build_analysis_prompt(
            alert_data, runbook_data, mcp_data
        )
        
        # Create structured messages for LangChain
        messages = [
            LLMMessage(
                role="system",
                content="You are an expert SRE (Site Reliability Engineer) with deep knowledge of Kubernetes, cloud infrastructure, and incident response. Analyze system alerts thoroughly and provide actionable insights based on the alert, runbook, and system data provided."
            ),
            LLMMessage(
                role="user",
                content=prompt
            )
        ]
        
        try:
            return await self.generate_response(messages, **kwargs)
        except Exception as e:
            raise Exception(f"{self.provider_name} analysis error: {str(e)}") 