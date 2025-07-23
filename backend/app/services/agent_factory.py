"""
Agent Factory for creating specialized agent instances.

This module provides a factory for instantiating agent classes with
proper dependency injection. It maintains a static registry of available
agent classes and handles their creation.
"""

from typing import Any, Dict, Optional, Type

from app.agents.base_agent import BaseAgent
from app.integrations.llm.client import LLMClient
from app.integrations.mcp.client import MCPClient
from app.utils.logger import get_module_logger

from .mcp_server_registry import MCPServerRegistry

logger = get_module_logger(__name__)


class AgentFactory:
    """
    Factory for creating agent instances with dependency injection.
    
    This class maintains a static registry of agent classes and provides
    a method to instantiate them with all required dependencies.
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        mcp_client: MCPClient,
        mcp_registry: MCPServerRegistry,
        progress_callback: Optional[Any] = None
    ):
        """
        Initialize the agent factory with dependencies.
        
        Args:
            llm_client: Client for LLM interactions
            mcp_client: Client for MCP server interactions
            mcp_registry: Registry of MCP server configurations (REQUIRED)
            progress_callback: Optional callback for progress updates
        """
        self.llm_client = llm_client
        self.mcp_client = mcp_client
        self.mcp_registry = mcp_registry
        self.progress_callback = progress_callback
        
        # Static registry of available agent classes - loaded once, no runtime changes
        self.static_agent_classes: Dict[str, Type[BaseAgent]] = {}
        self._register_available_agents()
        
        logger.info(f"Initialized Agent Factory with {len(self.static_agent_classes)} agent classes")
    
    def _register_available_agents(self) -> None:
        """
        Register all available agent classes in static registry.
        Simple imports without error handling - fail fast if agents are missing.
        """
        from app.agents.kubernetes_agent import KubernetesAgent
        
        self.static_agent_classes = {
            "KubernetesAgent": KubernetesAgent,
            # Future agents will be added here:
            # "ArgoCDAgent": ArgoCDAgent,
            # "KubernetesAWSAgent": KubernetesAWSAgent,
        }
    
    def create_agent(self, agent_class_name: str) -> BaseAgent:
        """
        Create an agent instance with dependency injection.
        Simple class resolution - no complex logic.
        
        Args:
            agent_class_name: Name of the agent class to instantiate
            
        Returns:
            Instantiated agent with injected dependencies
            
        Raises:
            ValueError: If the agent class is not registered
        """
        if agent_class_name not in self.static_agent_classes:
            raise ValueError(f"Unknown agent class: {agent_class_name}")
        
        agent_class = self.static_agent_classes[agent_class_name]
        
        # Instantiate agent with dependency injection
        agent = agent_class(
            llm_client=self.llm_client,
            mcp_client=self.mcp_client,
            mcp_registry=self.mcp_registry,
            progress_callback=self.progress_callback
        )
        
        logger.info(f"Created agent instance: {agent_class_name}")
        return agent 