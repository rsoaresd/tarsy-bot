"""
MCP Server Registry for managing MCP server configurations.

This module provides a simple static registry for MCP server configurations
with embedded LLM instructions. The registry is loaded once at startup and
serves as the single source of truth for all MCP server configurations.
"""

from typing import Dict, List, Optional

from ..models.mcp_config import MCPServerConfig
from ..utils.logger import get_module_logger

logger = get_module_logger(__name__)


class MCPServerRegistry:
    """
    Static registry for MCP server configurations.
    
    This class manages all MCP server configurations in the system,
    providing a simple dictionary-based lookup mechanism. The registry
    is immutable after initialization to ensure consistency.
    
    This is the SINGLE SOURCE OF TRUTH for all MCP server configurations.
    """
    
    # Static server configurations defined in the registry itself
    _DEFAULT_SERVERS = {
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
- Focus on namespace-specific resources first (kubectl get pods -n <namespace>)
- Use kubectl describe before kubectl get for detailed information
- Check pod logs only when necessary (they can be large)
- Consider resource quotas and limits when analyzing issues
- Look for events related to the problematic resources
- Check node capacity and scheduling constraints for pod placement issues
- Verify RBAC permissions when access issues occur
- Consider network policies for connectivity problems
- Check for resource conflicts and naming collisions"""
        },
        # Future servers can be added here:
        # "argocd-server": {...},
        # "aws-server": {...},
    }
    
    def __init__(self, config: Optional[Dict[str, Dict]] = None):
        """
        Initialize the MCP server registry with configurations.
        
        Args:
            config: Optional dictionary of server configurations.
                   If None, uses default configurations defined in the registry.
        """
        # Static servers - no runtime changes, just a dictionary
        self.static_servers: Dict[str, MCPServerConfig] = {}
        
        # Use provided config or fall back to default configurations
        server_configs = config or self._DEFAULT_SERVERS
        
        # Simple conversion to MCPServerConfig objects
        for server_id, server_config in server_configs.items():
            self.static_servers[server_id] = MCPServerConfig(**server_config)
        
        logger.info(f"Initialized MCP Server Registry with {len(self.static_servers)} servers")
    
    def get_server_configs(self, server_ids: List[str]) -> List[MCPServerConfig]:
        """
        Get MCP server configurations for the specified server IDs.
        Simple dictionary lookup - no complex logic.
        
        Args:
            server_ids: List of server IDs to retrieve configurations for
            
        Returns:
            List of MCPServerConfig objects for the requested servers
        """
        return [
            self.static_servers[server_id] 
            for server_id in server_ids 
            if server_id in self.static_servers
        ]
    
    def get_server_config(self, server_id: str) -> Optional[MCPServerConfig]:
        """
        Get configuration for a single MCP server.
        Simple dictionary lookup - no complex logic.
        
        Args:
            server_id: The server ID to retrieve
            
        Returns:
            MCPServerConfig if found, None otherwise
        """
        return self.static_servers.get(server_id)
    
    def get_all_server_ids(self) -> List[str]:
        """
        Get all server IDs that are configured in the registry.
        
        Returns:
            List of all server IDs
        """
        return list(self.static_servers.keys()) 