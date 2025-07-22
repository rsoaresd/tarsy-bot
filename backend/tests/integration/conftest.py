"""
Pytest configuration and fixtures for integration tests.

This module provides fixtures for mocking external services in e2e tests.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any, List, Optional

from app.config.settings import Settings
from app.models.alert import Alert
from app.services.alert_service import AlertService
from app.services.agent_registry import AgentRegistry
from app.services.agent_factory import AgentFactory
from app.services.mcp_server_registry import MCPServerRegistry
from app.services.runbook_service import RunbookService
from app.integrations.llm.client import LLMManager, LLMClient
from app.integrations.mcp.client import MCPClient
from app.agents.kubernetes_agent import KubernetesAgent
from app.models.mcp_config import MCPServerConfig


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = Mock(spec=Settings)
    settings.gemini_api_key = "mock-gemini-key"
    settings.openai_api_key = "mock-openai-key"
    settings.github_token = "mock-github-token"
    settings.default_llm_provider = "gemini"
    settings.max_llm_mcp_iterations = 3
    settings.log_level = "INFO"
    
    # LLM providers configuration that LLMManager expects
    settings.llm_providers = {
        "gemini": {
            "model": "gemini-2.5-pro",
            "api_key_env": "GEMINI_API_KEY",
            "type": "gemini"
        },
        "openai": {
            "model": "gpt-4-1106-preview",
            "api_key_env": "OPENAI_API_KEY", 
            "type": "openai"
        }
    }
    
    # Mock the get_llm_config method that Settings class provides
    def mock_get_llm_config(provider: str):
        if provider not in settings.llm_providers:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        config = settings.llm_providers[provider].copy()
        if provider == "gemini":
            config["api_key"] = settings.gemini_api_key
        elif provider == "openai":
            config["api_key"] = settings.openai_api_key
        return config
    
    settings.get_llm_config = mock_get_llm_config
    return settings


@pytest.fixture
def sample_alert():
    """Create a sample alert for testing."""
    return Alert(
        alert_type="Namespace is stuck in Terminating",
        severity="high",
        environment="production",
        cluster="https://k8s-cluster.example.com",
        namespace="stuck-namespace",
        pod="problematic-pod-12345",
        message="Namespace 'stuck-namespace' has been in Terminating state for 30+ minutes",
        runbook="https://github.com/company/runbooks/blob/main/k8s-namespace-terminating.md",
        context="Multiple pods in the namespace are stuck with finalizers"
    )


@pytest.fixture
def sample_runbook_content():
    """Sample runbook content for testing."""
    return """# Kubernetes Namespace Stuck in Terminating

## Overview
This runbook helps resolve issues where a Kubernetes namespace is stuck in Terminating state.

## Steps
1. Check for pods with finalizers
2. Examine resource quotas
3. Check for stuck resources
4. Review finalizer cleanup

## Commands
- `kubectl get namespace <name> -o yaml`
- `kubectl get pods -n <name>`
- `kubectl patch pod <pod-name> -n <name> -p '{"metadata":{"finalizers":null}}'`
"""


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = Mock(spec=LLMClient)
    client.available = True
    
    # Mock successful responses
    async def mock_generate_response(messages, **kwargs):
        """Generate mock responses based on message content."""
        if not messages:
            return "No analysis available"
        
        user_content = ""
        for msg in messages:
            if hasattr(msg, 'content') and 'tool' in msg.content.lower():
                user_content = msg.content
                break
        
        # Mock tool selection response
        if "select tools" in user_content.lower() or "mcp tools" in user_content.lower():
            return '''```json
[
    {
        "server": "kubernetes-server",
        "tool": "kubectl_get_namespace",
        "parameters": {"namespace": "stuck-namespace"},
        "reason": "Check namespace status and finalizers"
    },
    {
        "server": "kubernetes-server", 
        "tool": "kubectl_get_pods",
        "parameters": {"namespace": "stuck-namespace"},
        "reason": "List pods in the terminating namespace"
    }
]
```'''
        
        # Mock continue/stop decision
        if "continue" in user_content.lower() and "next" in user_content.lower():
            return '''```json
{
    "continue": false,
    "reason": "Sufficient data collected for analysis"
}
```'''
        
        # Mock final analysis
        return """## Analysis Results

**Issue Identified**: The namespace 'stuck-namespace' is stuck in Terminating state due to pods with finalizers.

**Root Cause**: Pods in the namespace have finalizers that are preventing clean deletion.

**Resolution Steps**:
1. Identify pods with finalizers using kubectl
2. Remove finalizers manually if safe to do so
3. Force delete remaining resources if necessary

**Immediate Actions**:
- Check pod finalizers: `kubectl get pods -n stuck-namespace -o yaml`
- Remove finalizers: `kubectl patch pod <pod-name> -n stuck-namespace -p '{"metadata":{"finalizers":null}}'`

**Status**: Issue can be resolved by removing pod finalizers"""
    
    client.generate_response = AsyncMock(side_effect=mock_generate_response)
    return client


@pytest.fixture
def mock_llm_manager():
    """Mock LLM manager for testing."""
    manager = Mock(spec=LLMManager)
    manager.is_available.return_value = True
    manager.list_available_providers.return_value = ["gemini", "openai"]
    manager.get_availability_status.return_value = {"gemini": "available", "openai": "available"}
    
    # Create mock client
    mock_client = Mock(spec=LLMClient)
    mock_client.available = True
    
    def mock_generate_response_sync(messages, **kwargs):
        """Generate mock responses based on message content."""
        if not messages:
            return "No analysis available"
        
        user_content = ""
        system_content = ""
        for msg in messages:
            if hasattr(msg, 'content') and msg.content:
                if hasattr(msg, 'role'):
                    if msg.role == "system":
                        system_content += str(msg.content)
                    elif msg.role == "user":
                        user_content += str(msg.content)
                else:
                    user_content += str(msg.content)
        
        # Determine response type based on content
        combined_content = (user_content + " " + system_content).lower()
        
        # Mock tool selection response (initial)
        if ("select tools" in combined_content or "mcp tool selection" in combined_content) and "iterative" not in combined_content:
            return '''```json
[
    {
        "server": "kubernetes-server",
        "tool": "kubectl_get_namespace", 
        "parameters": {"namespace": "stuck-namespace"},
        "reason": "Check namespace status and finalizers"
    }
]
```'''
        
        # Mock iterative tool selection (continue/stop decision)
        if "iterative" in combined_content or "continue" in combined_content:
            return '''```json
{"continue": false, "reason": "Analysis complete"}
```'''
        
        # Mock final analysis
        return "**Analysis**: Namespace stuck due to finalizers. Remove finalizers to resolve."
    
    # Create AsyncMock that can track calls and return dynamic responses
    mock_client.generate_response = AsyncMock(side_effect=mock_generate_response_sync)
    manager.get_client.return_value = mock_client
    return manager


@pytest.fixture
def mock_mcp_server_config():
    """Mock MCP server configuration."""
    return MCPServerConfig(
        server_id="kubernetes-server",
        server_type="kubernetes",
        enabled=True,
        connection_params={
            "command": "npx",
            "args": ["-y", "kubernetes-mcp-server@latest"]
        },
        instructions="Kubernetes server instructions for testing"
    )


@pytest.fixture
def mock_mcp_server_registry(mock_mcp_server_config):
    """Mock MCP server registry."""
    registry = Mock(spec=MCPServerRegistry)
    registry.get_server_configs.return_value = [mock_mcp_server_config]
    registry.get_server_config.return_value = mock_mcp_server_config
    registry.get_all_server_ids.return_value = ["kubernetes-server"]
    return registry


@pytest.fixture
def mock_mcp_client():
    """Mock MCP client for testing."""
    client = Mock(spec=MCPClient)
    
    # Mock initialization
    client.initialize = AsyncMock()
    client.close = AsyncMock()
    
    # Mock tool listing - use simpler return structure
    def mock_list_tools_sync(server_name=None):
        """Mock tool listing response - synchronous version."""
        if server_name == "kubernetes-server":
            return {
                "kubernetes-server": [
                    {
                        "name": "kubectl_get_namespace",
                        "description": "Get namespace information",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "namespace": {"type": "string", "description": "Namespace name"}
                            },
                            "required": ["namespace"]
                        }
                    },
                    {
                        "name": "kubectl_get_pods", 
                        "description": "List pods in namespace",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "namespace": {"type": "string", "description": "Namespace name"}
                            },
                            "required": ["namespace"]
                        }
                    }
                ]
            }
        return {}
    
    # Use AsyncMock with side_effect to track calls and return dynamic responses
    client.list_tools = AsyncMock(side_effect=mock_list_tools_sync)
    
    # Mock tool execution - use simpler return structure  
    def mock_call_tool_sync(server_name, tool_name, parameters):
        """Mock tool execution response - synchronous version."""
        if server_name == "kubernetes-server":
            if tool_name == "kubectl_get_namespace":
                return {
                    "status": "success",
                    "output": """NAME             STATUS        AGE
stuck-namespace  Terminating   45m"""
                }
            elif tool_name == "kubectl_get_pods":
                return {
                    "status": "success", 
                    "output": """NAME                    READY   STATUS        RESTARTS   AGE
problematic-pod-12345   0/1     Terminating   0          45m"""
                }
        return {"status": "error", "output": "Tool not found"}
    
    # Use AsyncMock with side_effect to track calls and return dynamic responses
    client.call_tool = AsyncMock(side_effect=mock_call_tool_sync)
    return client


@pytest.fixture
def mock_runbook_service(sample_runbook_content):
    """Mock runbook service."""
    service = Mock(spec=RunbookService)
    service.download_runbook = AsyncMock(return_value=sample_runbook_content)
    service.close = AsyncMock()
    return service


@pytest.fixture
def mock_agent_registry():
    """Mock agent registry."""
    registry = Mock(spec=AgentRegistry)
    registry.get_agent_for_alert_type.return_value = "KubernetesAgent"
    registry.get_supported_alert_types.return_value = ["Namespace is stuck in Terminating"]
    return registry


@pytest.fixture
def mock_agent_factory(mock_llm_manager, mock_mcp_client, mock_mcp_server_registry):
    """Mock agent factory."""
    factory = Mock(spec=AgentFactory)
    
    # Create a semi-mocked agent that calls dependencies but returns controlled results
    def create_mock_agent(agent_class_name):
        if agent_class_name == "KubernetesAgent":
            mock_agent = Mock(spec=KubernetesAgent)
            
            # Mock the process_alert method to actually call dependencies for test verification
            async def mock_process_alert(alert, runbook_content, callback=None):
                # Simulate calling LLM client multiple times as a real agent would
                llm_client = mock_llm_manager.get_client()
                
                # Call for tool selection (initial)
                await llm_client.generate_response([
                    Mock(role="system", content="You are an expert SRE analyzing Kubernetes namespace issues. Use available MCP tools to diagnose problems."),
                    Mock(role="user", content="select tools for Kubernetes namespace analysis")
                ])
                
                # Call for iterative decision
                await llm_client.generate_response([
                    Mock(role="system", content="You are an expert SRE with Kubernetes expertise. Determine if more analysis is needed."), 
                    Mock(role="user", content="iterative analysis - should we continue?")
                ])
                
                # Call for final analysis
                analysis_result = await llm_client.generate_response([
                    Mock(role="system", content="You are an expert SRE specializing in Kubernetes troubleshooting. Provide actionable analysis."),
                    Mock(role="user", content="final analysis of namespace issue")
                ])
                
                # Simulate calling MCP client for tool listing and execution (iterative analysis)
                await mock_mcp_client.list_tools(server_name="kubernetes-server")
                await mock_mcp_client.call_tool("kubernetes-server", "kubectl_get_namespace", {"namespace": "stuck-namespace"})
                # Second iteration of MCP calls for iterative analysis
                await mock_mcp_client.call_tool("kubernetes-server", "kubectl_get_pods", {"namespace": "stuck-namespace"})
                
                return {
                    "status": "success",
                    "agent": "KubernetesAgent",
                    "analysis": f"**Analysis**: Namespace 'stuck-namespace' stuck due to finalizers. {analysis_result}",
                    "iterations": 1,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            
            mock_agent.process_alert = mock_process_alert
            return mock_agent
        raise ValueError(f"Unknown agent class: {agent_class_name}")
    
    factory.create_agent = Mock(side_effect=create_mock_agent)
    factory.progress_callback = None
    return factory


@pytest.fixture
def progress_callback_mock():
    """Mock progress callback for testing."""
    callback = AsyncMock()
    return callback


@pytest.fixture
async def alert_service(mock_settings, mock_runbook_service, mock_agent_registry, 
                       mock_mcp_server_registry, mock_mcp_client, mock_llm_manager,
                       mock_agent_factory):
    """Create AlertService with mocked dependencies."""
    service = AlertService(mock_settings)
    
    # Replace dependencies with mocks
    service.runbook_service = mock_runbook_service
    service.agent_registry = mock_agent_registry
    service.mcp_server_registry = mock_mcp_server_registry
    service.mcp_client = mock_mcp_client
    service.llm_manager = mock_llm_manager
    
    # Initialize the service (this creates the real agent_factory)
    await service.initialize()
    
    # Replace the agent_factory with our mock AFTER initialization
    service.agent_factory = mock_agent_factory
    
    yield service
    
    # Cleanup
    await service.close() 