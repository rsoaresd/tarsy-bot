"""
Unified LLM client implementation using LangChain.
Handles all LLM providers through LangChain's abstraction.
"""

import json
from typing import Dict, List

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
    
    async def determine_mcp_tools(self,
                                alert_data: Dict,
                                runbook_data: Dict,
                                available_tools: Dict,
                                **kwargs) -> List[Dict]:
        """Determine which MCP tools to call based on alert and runbook."""
        if not self.available:
            raise Exception(f"{self.provider_name} client not available")
        
        # Build prompt for tool selection
        prompt = self.prompt_builder.build_mcp_tool_selection_prompt(
            alert_data, runbook_data, available_tools
        )
        
        # Create messages
        messages = [
            LLMMessage(
                role="system",
                content="You are an expert SRE analyzing alerts. Based on the alert, runbook, and available MCP tools, determine which tools should be called to gather the necessary information for diagnosis. Return only a valid JSON array with no additional text."
            ),
            LLMMessage(
                role="user",
                content=prompt
            )
        ]
        
        try:
            response = await self.generate_response(messages, **kwargs)
            
            # Parse the JSON response
            # Try to extract JSON from the response
            response = response.strip()
            
            # Find JSON array in the response (handle markdown code blocks)
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()
            
            # Parse the JSON
            tools_to_call = json.loads(response)
            
            # Validate the response format
            if not isinstance(tools_to_call, list):
                raise ValueError("Response must be a JSON array")
            
            # Validate each tool call
            for tool_call in tools_to_call:
                if not isinstance(tool_call, dict):
                    raise ValueError("Each tool call must be a JSON object")
                
                required_fields = ["server", "tool", "parameters", "reason"]
                for field in required_fields:
                    if field not in tool_call:
                        raise ValueError(f"Missing required field: {field}")
            
            return tools_to_call
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse LLM response as JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"{self.provider_name} tool selection error: {str(e)}") 