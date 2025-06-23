"""
Kubernetes MCP client for interacting with Kubernetes MCP server.
"""

from typing import Any, Dict, List, Optional
from app.integrations.mcp.base import BaseMCPClient


class KubernetesMCPClient(BaseMCPClient):
    """MCP client for Kubernetes operations."""
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available Kubernetes tools."""
        try:
            response = await self._make_request("GET", "/tools")
            return response.get("tools", [])
        except Exception as e:
            print(f"Failed to list Kubernetes tools: {str(e)}")
            return []
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call a Kubernetes tool."""
        payload = {
            "tool": tool_name,
            "parameters": parameters
        }
        
        try:
            response = await self._make_request("POST", "/tools/call", payload)
            return response
        except Exception as e:
            raise Exception(f"Failed to call Kubernetes tool {tool_name}: {str(e)}")
    
    async def get_namespace_status(self, cluster_url: str, namespace: str) -> Dict[str, Any]:
        """Get namespace status and details."""
        return await self.call_tool("get_namespace", {
            "cluster": cluster_url,
            "namespace": namespace,
            "output": "yaml"
        })
    
    async def list_namespace_resources(self, cluster_url: str, namespace: str) -> Dict[str, Any]:
        """List all resources in a namespace."""
        return await self.call_tool("list_resources", {
            "cluster": cluster_url,
            "namespace": namespace
        })
    
    async def get_pods_in_namespace(self, cluster_url: str, namespace: str) -> Dict[str, Any]:
        """Get all pods in a namespace."""
        return await self.call_tool("get_pods", {
            "cluster": cluster_url,
            "namespace": namespace
        })
    
    async def get_events_in_namespace(self, cluster_url: str, namespace: str) -> Dict[str, Any]:
        """Get events in a namespace."""
        return await self.call_tool("get_events", {
            "cluster": cluster_url,
            "namespace": namespace
        })
    
    async def describe_resource(self, cluster_url: str, resource_type: str, 
                              resource_name: str, namespace: str = None) -> Dict[str, Any]:
        """Describe a specific Kubernetes resource."""
        params = {
            "cluster": cluster_url,
            "resource_type": resource_type,
            "resource_name": resource_name
        }
        
        if namespace:
            params["namespace"] = namespace
        
        return await self.call_tool("describe_resource", params)
    
    async def get_resource_finalizers(self, cluster_url: str, resource_type: str, 
                                    resource_name: str, namespace: str = None) -> Dict[str, Any]:
        """Get finalizers for a specific resource."""
        params = {
            "cluster": cluster_url,
            "resource_type": resource_type,
            "resource_name": resource_name
        }
        
        if namespace:
            params["namespace"] = namespace
        
        return await self.call_tool("get_finalizers", params)
    
    async def check_stuck_resources(self, cluster_url: str, namespace: str) -> Dict[str, Any]:
        """Check for resources that might be preventing namespace deletion."""
        return await self.call_tool("check_stuck_resources", {
            "cluster": cluster_url,
            "namespace": namespace
        }) 