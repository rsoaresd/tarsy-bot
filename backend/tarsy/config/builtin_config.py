"""
Centralized configuration for all built-in agents and MCP servers.

This module serves as the SINGLE SOURCE OF TRUTH for:
- Built-in agent class names and import paths
- Built-in agent mappings (alert type → agent class)
- Built-in MCP server configurations

When adding new built-in agents or MCP servers, edit only this file.
All other modules (AgentRegistry, AgentFactory, MCPServerRegistry, ConfigurationLoader)
import their built-in definitions from here.

Note: This module contains only data structures to avoid circular imports.
Agent classes are imported dynamically by AgentFactory when needed.
"""

from typing import Dict, Any


# ==============================================================================
# BUILT-IN AGENT CLASS NAMES
# ==============================================================================

# Central registry of all built-in agent class names
# Format: "ClassName" -> "import.path.ClassName"
BUILTIN_AGENT_CLASS_IMPORTS: Dict[str, str] = {
    "KubernetesAgent": "tarsy.agents.kubernetes_agent.KubernetesAgent",
    # Future agents will be added here:
    # "ArgoCDAgent": "tarsy.agents.argocd_agent.ArgoCDAgent",
    # "KubernetesAWSAgent": "tarsy.agents.kubernetes_aws_agent.KubernetesAWSAgent",
}


# ==============================================================================
# BUILT-IN AGENT MAPPINGS  
# ==============================================================================

# Central registry of alert type to agent class mappings
# Format: "alert_type" -> "ClassName"
BUILTIN_AGENT_MAPPINGS: Dict[str, str] = {
    "kubernetes": "KubernetesAgent",           # Generic kubernetes alerts
    "NamespaceTerminating": "KubernetesAgent", # Specific kubernetes alert type
    # Future mappings will be added here:
    # "argocd": "ArgoCDAgent",
    # "aws-kubernetes": "KubernetesAWSAgent",
}


# ==============================================================================
# BUILT-IN MCP SERVERS
# ==============================================================================

# Central registry of all built-in MCP server configurations
# Format: "server-id" -> configuration_dict
BUILTIN_MCP_SERVERS: Dict[str, Dict[str, Any]] = {
    "kubernetes-server": {
        "server_id": "kubernetes-server",
        "server_type": "kubernetes",
        "enabled": True,
        "connection_params": {
            "command": "npx",
            "args": ["-y", "kubernetes-mcp-server@latest"]
        },
        "instructions": """For Kubernetes operations:
- Be careful with cluster-scoped resource listings in large clusters
- Always prefer namespaced queries when possible
- Use kubectl explain for resource schema information
- Check resource quotas before creating new resources"""
    },
    # Future MCP servers will be added here:
    # "argocd-server": {
    #     "server_id": "argocd-server", 
    #     "server_type": "argocd",
    #     "enabled": True,
    #     "connection_params": {
    #         "command": "npx",
    #         "args": ["-y", "argocd-mcp-server@latest"]
    #     },
    #     "instructions": "ArgoCD-specific instructions..."
    # },
}


# ==============================================================================
# CONVENIENCE ACCESSORS
# ==============================================================================

def get_builtin_agent_class_names() -> set[str]:
    """Get all built-in agent class names."""
    return set(BUILTIN_AGENT_CLASS_IMPORTS.keys())


def get_builtin_mcp_server_ids() -> set[str]:
    """Get all built-in MCP server IDs.""" 
    return set(BUILTIN_MCP_SERVERS.keys())


def get_builtin_alert_types() -> set[str]:
    """Get all built-in alert types."""
    return set(BUILTIN_AGENT_MAPPINGS.keys()) 