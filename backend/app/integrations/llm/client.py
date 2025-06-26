"""
Unified LLM client implementation using LangChain.
Handles all LLM providers through LangChain's abstraction.
"""

import json
import uuid
from typing import Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_xai import ChatXAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel

from app.config.settings import Settings
from app.models.llm import LLMMessage
from app.utils.prompt_builder import PromptBuilder
from app.utils.logger import get_module_logger

# Setup logger for this module
logger = get_module_logger(__name__)

# Setup separate logger for LLM communications
llm_comm_logger = get_module_logger("llm.communications")


# LLM Providers mapping using LangChain
LLM_PROVIDERS = {
    "openai": lambda temp, api_key, model: ChatOpenAI(
        model_name=model or "gpt-4-1106-preview", 
        temperature=temp, 
        api_key=api_key
    ),
    "gemini": lambda temp, api_key, model: ChatGoogleGenerativeAI(
        model=model or "gemini-2.5-pro-exp-03-25", 
        temperature=temp, 
        google_api_key=api_key
    ),
    "grok": lambda temp, api_key, model: ChatXAI(
        model_name=model or "grok-3-latest", 
        api_key=api_key, 
        temperature=temp
    ),
}


class LLMClient:
    """Unified LLM client that works with all providers via LangChain."""
    
    def __init__(self, provider_name: str, config: Dict):
        self.provider_name = provider_name
        self.config = config
        self.model = config.get("model", "default")
        self.api_key = config.get("api_key", "")
        self.temperature = config.get("temperature", 0.3)
        self.llm_client: Optional[BaseChatModel] = None
        self.prompt_builder = PromptBuilder()
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the LangChain LLM client."""
        try:
            if self.provider_name in LLM_PROVIDERS:
                if not self.api_key:
                    logger.warning(f"No API key provided for {self.provider_name}")
                    self.available = False
                    return
                
                self.llm_client = LLM_PROVIDERS[self.provider_name](
                    self.temperature, 
                    self.api_key, 
                    self.model
                )
                self.available = True
                logger.info(f"Successfully initialized {self.provider_name} with LangChain")
            else:
                logger.error(f"Unknown LLM provider: {self.provider_name}")
                self.available = False
        except Exception as e:
            logger.error(f"Failed to initialize {self.provider_name}: {str(e)}")
            self.available = False
    
    def _convert_messages(self, messages: List[LLMMessage]) -> List:
        """Convert LLMMessage objects to LangChain message objects."""
        langchain_messages = []
        for msg in messages:
            if msg.role == "system":
                langchain_messages.append(SystemMessage(content=msg.content))
            elif msg.role == "user":
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                langchain_messages.append(AIMessage(content=msg.content))
        return langchain_messages
    
    async def generate_response(self, messages: List[LLMMessage], **kwargs) -> str:
        """Generate a response from the LLM using LangChain."""
        if not self.available or not self.llm_client:
            raise Exception(f"{self.provider_name} client not available")
        
        # Generate unique request ID for tracking
        request_id = str(uuid.uuid4())[:8]
        
        # Log the outgoing prompt/messages
        self._log_llm_request(messages, request_id, **kwargs)
        
        try:
            langchain_messages = self._convert_messages(messages)
            response = await self.llm_client.ainvoke(langchain_messages)
            
            # Log the response
            self._log_llm_response(response.content, request_id)
            
            return response.content
        except Exception as e:
            # Log the error
            self._log_llm_error(str(e), request_id)
            raise Exception(f"{self.provider_name} API error: {str(e)}")
    
    def _log_llm_request(self, messages: List[LLMMessage], request_id: str, **kwargs):
        """Log the outgoing LLM request."""
        llm_comm_logger.info(f"=== LLM REQUEST [{self.provider_name}] [ID: {request_id}] ===")
        llm_comm_logger.info(f"Request ID: {request_id}")
        llm_comm_logger.info(f"Provider: {self.provider_name}")
        llm_comm_logger.info(f"Model: {self.model}")
        llm_comm_logger.info(f"Temperature: {self.temperature}")
        if kwargs:
            llm_comm_logger.info(f"Additional kwargs: {kwargs}")
        
        llm_comm_logger.info("--- MESSAGES ---")
        for i, msg in enumerate(messages):
            llm_comm_logger.info(f"Message {i+1} [{msg.role.upper()}]:")
            llm_comm_logger.info(f"{msg.content}")
            llm_comm_logger.info("---")
        
        llm_comm_logger.info(f"=== END REQUEST [ID: {request_id}] ===")
    
    def _log_llm_response(self, response_content: str, request_id: str):
        """Log the LLM response."""
        llm_comm_logger.info(f"=== LLM RESPONSE [{self.provider_name}] [ID: {request_id}] ===")
        llm_comm_logger.info(f"Request ID: {request_id}")
        llm_comm_logger.info(f"Response length: {len(response_content)} characters")
        llm_comm_logger.info("--- RESPONSE CONTENT ---")
        llm_comm_logger.info(response_content)
        llm_comm_logger.info(f"=== END RESPONSE [ID: {request_id}] ===")
    
    def _log_llm_error(self, error_message: str, request_id: str):
        """Log LLM communication errors."""
        llm_comm_logger.error(f"=== LLM ERROR [{self.provider_name}] [ID: {request_id}] ===")
        llm_comm_logger.error(f"Request ID: {request_id}")
        llm_comm_logger.error(f"Error: {error_message}")
        llm_comm_logger.error(f"=== END ERROR [ID: {request_id}] ===")
    
    async def analyze_alert(self, 
                          alert_data: Dict, 
                          runbook_data: Dict, 
                          mcp_data: Dict,
                          **kwargs) -> str:
        """Analyze an alert using any LLM provider via LangChain."""
        if not self.available:
            raise Exception(f"{self.provider_name} client not available")
        
        # Log the context of this alert analysis
        logger.info(f"Starting alert analysis with {self.provider_name} - Alert: {alert_data.get('alert', 'unknown')}")
        
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
            result = await self.generate_response(messages, **kwargs)
            logger.info(f"Alert analysis completed with {self.provider_name}")
            return result
        except Exception as e:
            logger.error(f"Alert analysis failed with {self.provider_name}: {str(e)}")
            raise Exception(f"{self.provider_name} analysis error: {str(e)}")
    
    async def determine_mcp_tools(self,
                                alert_data: Dict,
                                runbook_data: Dict,
                                available_tools: Dict,
                                **kwargs) -> List[Dict]:
        """Determine which MCP tools to call based on alert and runbook."""
        if not self.available:
            raise Exception(f"{self.provider_name} client not available")
        
        # Log the context of this tool selection
        logger.info(f"Starting MCP tool selection with {self.provider_name} - Alert: {alert_data.get('alert', 'unknown')}")
        
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
            
            logger.info(f"MCP tool selection completed with {self.provider_name} - Selected {len(tools_to_call)} tools")
            return tools_to_call
            
        except json.JSONDecodeError as e:
            logger.error(f"MCP tool selection failed with {self.provider_name} - JSON parsing error: {str(e)}")
            raise Exception(f"Failed to parse LLM response as JSON: {str(e)}")
        except Exception as e:
            logger.error(f"MCP tool selection failed with {self.provider_name}: {str(e)}")
            raise Exception(f"{self.provider_name} tool selection error: {str(e)}")


class LLMManager:
    """Manages multiple LLM providers using LangChain."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.clients: Dict[str, LLMClient] = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients using unified implementation."""
        # Initialize each configured LLM provider
        for provider_name, provider_config in self.settings.llm_providers.items():
            try:
                config = self.settings.get_llm_config(provider_name)
                
                if not config.get("api_key"):
                    logger.warning(f"Skipping {provider_name}: No API key provided")
                    continue
                
                # Use unified client for all providers
                client = LLMClient(provider_name, config)
                self.clients[provider_name] = client
                logger.info(f"Initialized LLM client: {provider_name}")
                
            except Exception as e:
                logger.error(f"Failed to initialize LLM client {provider_name}: {str(e)}")
    
    def get_client(self, provider: str = None) -> Optional[LLMClient]:
        """Get an LLM client by provider name."""
        if not provider:
            provider = self.settings.default_llm_provider
        
        return self.clients.get(provider)
    
    async def analyze_alert(self, 
                          alert_data: Dict, 
                          runbook_data: Dict, 
                          mcp_data: Dict,
                          provider: str = None) -> str:
        """Analyze an alert using the specified or default LLM provider."""
        client = self.get_client(provider)
        if not client:
            available = list(self.clients.keys())
            raise Exception(f"LLM provider not available. Available: {available}")
        
        return await client.analyze_alert(alert_data, runbook_data, mcp_data)
    
    async def determine_mcp_tools(self,
                                alert_data: Dict,
                                runbook_data: Dict,
                                available_tools: Dict,
                                provider: str = None) -> List[Dict]:
        """Determine which MCP tools to call using the specified or default LLM provider."""
        client = self.get_client(provider)
        if not client:
            available = list(self.clients.keys())
            raise Exception(f"LLM provider not available. Available: {available}")
        
        return await client.determine_mcp_tools(alert_data, runbook_data, available_tools)
    
    def list_available_providers(self) -> List[str]:
        """List available LLM providers."""
        return list(self.clients.keys()) 