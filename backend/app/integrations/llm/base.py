"""
Base LLM client using LangChain for different LLM providers.
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_xai import ChatXAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel

from app.config.settings import Settings
from app.models.llm import LLMMessage, AvailableLLMs


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


class BaseLLMClient(ABC):
    """Base class for LLM clients using LangChain."""
    
    def __init__(self, provider_name: str, config: Dict):
        self.provider_name = provider_name
        self.config = config
        self.model = config.get("model", "default")
        self.api_key = config.get("api_key", "")
        self.temperature = config.get("temperature", 0.3)
        self.llm_client: Optional[BaseChatModel] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the LangChain LLM client."""
        try:
            if self.provider_name in LLM_PROVIDERS:
                if not self.api_key:
                    print(f"No API key provided for {self.provider_name}")
                    self.available = False
                    return
                
                self.llm_client = LLM_PROVIDERS[self.provider_name](
                    self.temperature, 
                    self.api_key, 
                    self.model
                )
                self.available = True
                print(f"Successfully initialized {self.provider_name} with LangChain")
            else:
                print(f"Unknown LLM provider: {self.provider_name}")
                self.available = False
        except Exception as e:
            print(f"Failed to initialize {self.provider_name}: {str(e)}")
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
        
        try:
            langchain_messages = self._convert_messages(messages)
            response = await self.llm_client.ainvoke(langchain_messages)
            return response.content
        except Exception as e:
            raise Exception(f"{self.provider_name} API error: {str(e)}")
    
    @abstractmethod
    async def analyze_alert(self, 
                          alert_data: Dict, 
                          runbook_data: Dict, 
                          mcp_data: Dict,
                          **kwargs) -> str:
        """Analyze an alert with runbook and MCP data."""
        pass
    
    @abstractmethod
    async def determine_mcp_tools(self,
                                alert_data: Dict,
                                runbook_data: Dict,
                                available_tools: Dict,
                                **kwargs) -> List[Dict]:
        """Determine which MCP tools to call based on alert and runbook."""
        pass


class LLMManager:
    """Manages multiple LLM providers using LangChain."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.clients: Dict[str, BaseLLMClient] = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients using unified implementation."""
        from app.integrations.llm.client import UnifiedLLMClient
        
        # Initialize each configured LLM provider
        for provider_name, provider_config in self.settings.llm_providers.items():
            try:
                config = self.settings.get_llm_config(provider_name)
                
                if not config.get("api_key"):
                    print(f"Skipping {provider_name}: No API key provided")
                    continue
                
                # Use unified client for all providers
                client = UnifiedLLMClient(provider_name, config)
                self.clients[provider_name] = client
                print(f"Initialized LLM client: {provider_name}")
                
            except Exception as e:
                print(f"Failed to initialize LLM client {provider_name}: {str(e)}")
    
    def get_client(self, provider: str = None) -> Optional[BaseLLMClient]:
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