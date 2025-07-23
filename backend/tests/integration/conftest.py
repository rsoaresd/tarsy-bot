"""
Pytest configuration and fixtures for integration tests.

This module provides fixtures for mocking external services in e2e tests.
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from sqlmodel import Session, SQLModel, create_engine

from tarsy.agents.kubernetes_agent import KubernetesAgent
from tarsy.config.settings import Settings
from tarsy.integrations.llm.client import LLMClient, LLMManager
from tarsy.integrations.mcp.client import MCPClient
from tarsy.models.alert import Alert
from tarsy.models.history import AlertSession, LLMInteraction, MCPCommunication
from tarsy.models.mcp_config import MCPServerConfig
from tarsy.services.agent_factory import AgentFactory
from tarsy.services.agent_registry import AgentRegistry
from tarsy.services.alert_service import AlertService
from tarsy.services.history_service import HistoryService
from tarsy.services.mcp_server_registry import MCPServerRegistry
from tarsy.services.runbook_service import RunbookService


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
        alert_type="NamespaceTerminating",
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
This runbook helps resolve issues where a Kubernetes NamespaceTerminating state.

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
    registry.get_supported_alert_types.return_value = ["NamespaceTerminating"]
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
            async def mock_process_alert(alert, runbook_content, callback=None, session_id=None):
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


# History Service Test Fixtures

@pytest.fixture
def history_test_database_engine():
    """Create in-memory SQLite engine for history service testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def mock_history_service():
    """Create mock history service for testing."""
    service = Mock(spec=HistoryService)
    service.enabled = True
    service.is_enabled = True
    service.create_session.return_value = "mock-session-123"
    service.update_session_status.return_value = True
    service.log_llm_interaction.return_value = True
    service.log_mcp_communication.return_value = True
    service.get_sessions_list.return_value = ([], 0)
    service.get_session_timeline.return_value = None
    service.test_database_connection.return_value = True
    service.health_check.return_value = {
        "enabled": True,
        "healthy": True,
        "database_url": "sqlite:///test.db",
        "retention_days": 90
    }
    return service


@pytest.fixture
def sample_alert_session():
    """Create sample AlertSession for testing."""
    return AlertSession(
        session_id="test-session-123",
        alert_id="test-alert-456",
        alert_data={
            "alert_type": "NamespaceTerminating",
            "environment": "production",
            "cluster": "k8s-prod",
            "namespace": "stuck-namespace",
            "message": "Test alert message",
            "severity": "high"
        },
        agent_type="KubernetesAgent",
        alert_type="NamespaceTerminating",
        status="in_progress",
        started_at=pytest.lazy_fixture('datetime_now_utc'),
        session_metadata={"test": "metadata"}
    )


@pytest.fixture
def sample_llm_interaction():
    """Create sample LLMInteraction for testing."""
    return LLMInteraction(
        interaction_id="llm-interaction-789",
        session_id="test-session-123",
        prompt_text="Analyze the namespace termination issue",
        response_text="The namespace is stuck due to finalizers",
        model_used="gpt-4",
        timestamp=pytest.lazy_fixture('datetime_now_utc'),
        step_description="Initial analysis",
        duration_ms=1500,
        token_usage={"prompt_tokens": 150, "completion_tokens": 50, "total_tokens": 200}
    )


@pytest.fixture
def sample_mcp_communication():
    """Create sample MCPCommunication for testing."""
    return MCPCommunication(
        communication_id="mcp-comm-101",
        session_id="test-session-123",
        server_name="kubernetes-server",
        communication_type="tool_call",
        tool_name="kubectl_get_namespace",
        tool_arguments={"namespace": "stuck-namespace"},
        tool_result={"status": "Terminating", "finalizers": ["test-finalizer"]},
        timestamp=pytest.lazy_fixture('datetime_now_utc'),
        step_description="Check namespace status",
        duration_ms=800,
        success=True,
        available_tools=["kubectl_get_namespace", "kubectl_describe_namespace"]
    )


@pytest.fixture
def datetime_now_utc():
    """Provide current UTC datetime for testing."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)


@pytest.fixture
def history_service_with_test_db(history_test_database_engine):
    """Create HistoryService with test database for integration testing."""
    from unittest.mock import patch
    
    mock_settings = Mock()
    mock_settings.history_enabled = True
    mock_settings.history_database_url = "sqlite:///:memory:"
    mock_settings.history_retention_days = 90
    
    with patch('tarsy.services.history_service.get_settings', return_value=mock_settings):
        service = HistoryService()
        
        # Override database engine for testing
        service.db_manager.engine = history_test_database_engine
        service.db_manager.SessionLocal = lambda: Session(history_test_database_engine)
        service._is_healthy = True
        service._initialization_attempted = True
        
        return service


@pytest.fixture
def mock_history_timeline_data():
    """Create mock timeline data for testing."""
    from datetime import datetime, timezone
    
    return {
        "session_info": {
            "session_id": "test-session-123",
            "alert_id": "test-alert-456",
            "alert_type": "NamespaceTerminating",
            "agent_type": "KubernetesAgent",
            "status": "completed",
            "started_at": datetime.now(timezone.utc),
            "completed_at": datetime.now(timezone.utc),
            "error_message": None
        },
        "chronological_timeline": [
            {
                "type": "llm_interaction",
                "timestamp": datetime.now(timezone.utc),
                "step_description": "Initial analysis",
                "prompt_text": "Analyze the issue",
                "response_text": "Found the problem",
                "model_used": "gpt-4",
                "duration_ms": 1500
            },
            {
                "type": "mcp_communication",
                "timestamp": datetime.now(timezone.utc),
                "step_description": "Check namespace status",
                "server_name": "kubernetes-server",
                "tool_name": "kubectl_get_namespace",
                "success": True,
                "duration_ms": 800
            }
        ],
        "summary": {
            "total_interactions": 2,
            "llm_interactions": 1,
            "mcp_communications": 1,
            "total_duration_ms": 2300
        }
    } 