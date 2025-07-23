"""
MCP Server configuration data models.

This module defines the data models for MCP server configurations
used in the multi-layer agent architecture.
"""

from typing import Any, Dict

from pydantic import BaseModel, Field


class MCPServerConfig(BaseModel):
    """
    Configuration for an MCP server instance.
    
    This model represents the complete configuration for an MCP server,
    including connection parameters and embedded LLM instructions.
    """
    
    server_id: str = Field(
        ..., 
        description="Unique identifier for the MCP server (e.g., 'kubernetes-server')"
    )
    
    server_type: str = Field(
        ..., 
        description="Type of MCP server (e.g., 'kubernetes', 'argocd', 'aws')"
    )
    
    enabled: bool = Field(
        default=True, 
        description="Whether this MCP server is enabled"
    )
    
    connection_params: Dict[str, Any] = Field(
        ..., 
        description="Connection parameters for the MCP server (e.g., command, args)"
    )
    
    instructions: str = Field(
        default="", 
        description="Embedded LLM instructions specific to this MCP server"
    )
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "server_id": "kubernetes-server",
                "server_type": "kubernetes",
                "enabled": True,
                "connection_params": {
                    "command": "npx",
                    "args": ["-y", "kubernetes-mcp-server@latest"]
                },
                "instructions": "For Kubernetes operations:\n- Be careful with cluster-scoped listings..."
            }
        } 