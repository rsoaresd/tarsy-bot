"""
Base MCP client for communicating with MCP servers.
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import httpx

from app.config.settings import Settings


class MCPServerConfig:
    """Configuration for an MCP server."""
    
    def __init__(self, url: str, server_type: str, enabled: bool = True):
        self.url = url
        self.server_type = server_type
        self.enabled = enabled


class BaseMCPClient(ABC):
    """Base class for MCP clients."""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=30.0)
        self.connected = False
    
    async def connect(self) -> bool:
        """Connect to the MCP server."""
        try:
            # Test connection with a simple health check or capabilities request
            response = await self.client.get(f"{self.config.url}/health")
            self.connected = response.status_code == 200
            return self.connected
        except Exception:
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        await self.client.aclose()
        self.connected = False
    
    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server."""
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool on the MCP server."""
        pass
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the MCP server."""
        if not self.connected:
            raise Exception("Not connected to MCP server")
        
        url = f"{self.config.url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = await self.client.get(url)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            raise Exception(f"MCP server request failed: {str(e)}")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            if hasattr(self, 'client'):
                # Note: This is not ideal for async cleanup, but serves as a fallback
                pass
        except Exception:
            pass


class MCPOrchestrator:
    """Orchestrates communication with multiple MCP servers."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.clients: Dict[str, BaseMCPClient] = {}
    
    async def initialize(self):
        """Initialize all configured MCP servers."""
        from app.integrations.mcp.kubernetes import KubernetesMCPClient
        
        # Initialize each configured MCP server
        for server_name, server_config in self.settings.mcp_servers.items():
            if not server_config.get("enabled", True):
                continue
            
            try:
                # Create appropriate client based on type
                if server_config["type"] == "kubernetes":
                    config = MCPServerConfig(
                        url=self.settings.kubernetes_mcp_url,
                        server_type="kubernetes"
                    )
                    client = KubernetesMCPClient(config)
                else:
                    raise ValueError(f"Unknown MCP server type: {server_config['type']}")
                
                # Attempt to connect
                if await client.connect():
                    self.clients[server_name] = client
                    print(f"Connected to MCP server: {server_name}")
                else:
                    print(f"Failed to connect to MCP server: {server_name}")
                    
            except Exception as e:
                print(f"Error initializing MCP server {server_name}: {str(e)}")
    
    async def get_client(self, server_name: str) -> Optional[BaseMCPClient]:
        """Get an MCP client by name."""
        return self.clients.get(server_name)
    
    async def call_tool(self, server_name: str, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on a specific MCP server."""
        client = await self.get_client(server_name)
        if not client:
            raise Exception(f"MCP server not available: {server_name}")
        
        return await client.call_tool(tool_name, parameters)
    
    async def list_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all tools from all connected MCP servers."""
        all_tools = {}
        
        for server_name, client in self.clients.items():
            try:
                tools = await client.list_tools()
                all_tools[server_name] = tools
            except Exception as e:
                print(f"Error listing tools for {server_name}: {str(e)}")
                all_tools[server_name] = []
        
        return all_tools
    
    async def close_all(self):
        """Close all MCP client connections."""
        for client in self.clients.values():
            try:
                await client.disconnect()
            except Exception as e:
                print(f"Error closing MCP client: {str(e)}")
        
        self.clients.clear() 