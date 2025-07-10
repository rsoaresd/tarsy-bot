"""
MCP client using the official MCP SDK for integration with MCP servers.
"""

import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config.settings import Settings
from app.utils.logger import get_module_logger

# Setup logger for this module
logger = get_module_logger(__name__)

# Setup separate logger for MCP communications
mcp_comm_logger = get_module_logger("mcp.communications")


class MCPClient:
    """MCP client using the official MCP SDK."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        self._initialized = False
    
    async def initialize(self):
        """Initialize MCP servers based on configuration."""
        if self._initialized:
            return
            
        for server_name, server_config in self.settings.mcp_servers.items():
            if not server_config.get("enabled", True):
                continue
                
            try:
                # Create server parameters for stdio connection
                server_params = StdioServerParameters(
                    command=server_config["command"],
                    args=server_config.get("args", []),
                    env=server_config.get("env", None)
                )
                
                # Connect to the server
                read_stream, write_stream = await self.exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                
                # Create session
                session = await self.exit_stack.enter_async_context(
                    ClientSession(read_stream, write_stream)
                )
                
                # Initialize the session
                await session.initialize()
                
                self.sessions[server_name] = session
                logger.info(f"Initialized MCP server: {server_name}")
                
            except Exception as e:
                logger.error(f"Failed to initialize MCP server {server_name}: {str(e)}")
        
        self._initialized = True
    
    async def list_tools(self, server_name: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """List available tools from MCP servers."""
        if not self._initialized:
            await self.initialize()
        
        # Generate unique request ID for tracking
        request_id = str(uuid.uuid4())[:8]
        
        # Log the tools listing request
        self._log_mcp_list_tools_request(server_name, request_id)
        
        all_tools = {}
        
        if server_name:
            # List tools from specific server
            if server_name in self.sessions:
                try:
                    session = self.sessions[server_name]
                    tools_result = await session.list_tools()
                    tools = []
                    for tool in tools_result.tools:
                        tool_dict = {
                            "name": tool.name,
                            "description": tool.description or "",
                            "inputSchema": tool.inputSchema
                        }
                        tools.append(tool_dict)
                    all_tools[server_name] = tools
                    
                    # Log the successful response
                    self._log_mcp_list_tools_response(server_name, tools, request_id)
                    
                except Exception as e:
                    logger.error(f"Error listing tools from {server_name}: {str(e)}")
                    self._log_mcp_list_tools_error(server_name, str(e), request_id)
                    all_tools[server_name] = []
        else:
            # List tools from all servers
            for name, session in self.sessions.items():
                try:
                    tools_result = await session.list_tools()
                    tools = []
                    for tool in tools_result.tools:
                        tool_dict = {
                            "name": tool.name,
                            "description": tool.description or "",
                            "inputSchema": tool.inputSchema
                        }
                        tools.append(tool_dict)
                    all_tools[name] = tools
                    
                    # Log the successful response for this server
                    self._log_mcp_list_tools_response(name, tools, request_id)
                    
                except Exception as e:
                    logger.error(f"Error listing tools from {name}: {str(e)}")
                    self._log_mcp_list_tools_error(name, str(e), request_id)
                    all_tools[name] = []
        
        return all_tools
    
    async def call_tool(self, server_name: str, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool on an MCP server."""
        if not self._initialized:
            await self.initialize()
        
        if server_name not in self.sessions:
            raise Exception(f"MCP server not found: {server_name}")
        
        # Generate unique request ID for tracking
        request_id = str(uuid.uuid4())[:8]
        
        # Log the outgoing tool call
        self._log_mcp_request(server_name, tool_name, parameters, request_id)
        
        session = self.sessions[server_name]
        
        try:
            result = await session.call_tool(tool_name, parameters)
            
            # Convert result to dictionary
            if hasattr(result, 'content'):
                # Handle different content types
                content = result.content
                if isinstance(content, list):
                    # Extract text content from the list
                    text_parts = []
                    for item in content:
                        if hasattr(item, 'text'):
                            text_parts.append(item.text)
                        elif hasattr(item, 'type') and item.type == 'text':
                            text_parts.append(str(item))
                    response_dict = {"result": "\n".join(text_parts)}
                else:
                    response_dict = {"result": str(content)}
            else:
                response_dict = {"result": str(result)}
            
            # Log the successful response
            self._log_mcp_response(server_name, tool_name, response_dict, request_id)
            
            return response_dict
                
        except Exception as e:
            # Log the error
            error_msg = f"Failed to call tool {tool_name} on {server_name}: {str(e)}"
            self._log_mcp_error(server_name, tool_name, str(e), request_id)
            raise Exception(error_msg)
    
    def _log_mcp_request(self, server_name: str, tool_name: str, parameters: Dict[str, Any], request_id: str):
        """Log the outgoing MCP tool call request."""
        mcp_comm_logger.info(f"=== MCP REQUEST [{server_name}] [ID: {request_id}] ===")
        mcp_comm_logger.info(f"Request ID: {request_id}")
        mcp_comm_logger.info(f"Server: {server_name}")
        mcp_comm_logger.info(f"Tool: {tool_name}")
        mcp_comm_logger.info(f"Parameters: {json.dumps(parameters, indent=2, default=str)}")
        mcp_comm_logger.info(f"=== END REQUEST [ID: {request_id}] ===")
    
    def _log_mcp_response(self, server_name: str, tool_name: str, response: Dict[str, Any], request_id: str):
        """Log the MCP tool call response."""
        response_content = response.get("result", str(response))
        mcp_comm_logger.info(f"=== MCP RESPONSE [{server_name}] [ID: {request_id}] ===")
        mcp_comm_logger.info(f"Request ID: {request_id}")
        mcp_comm_logger.info(f"Server: {server_name}")
        mcp_comm_logger.info(f"Tool: {tool_name}")
        mcp_comm_logger.info(f"Response length: {len(response_content)} characters")
        mcp_comm_logger.info("--- RESPONSE CONTENT ---")
        mcp_comm_logger.info(response_content)
        mcp_comm_logger.info(f"=== END RESPONSE [ID: {request_id}] ===")
    
    def _log_mcp_error(self, server_name: str, tool_name: str, error_message: str, request_id: str):
        """Log MCP tool call errors."""
        mcp_comm_logger.error(f"=== MCP ERROR [{server_name}] [ID: {request_id}] ===")
        mcp_comm_logger.error(f"Request ID: {request_id}")
        mcp_comm_logger.error(f"Server: {server_name}")
        mcp_comm_logger.error(f"Tool: {tool_name}")
        mcp_comm_logger.error(f"Error: {error_message}")
        mcp_comm_logger.error(f"=== END ERROR [ID: {request_id}] ===")
    
    def _log_mcp_list_tools_request(self, server_name: Optional[str], request_id: str):
        """Log the MCP list tools request."""
        target = server_name if server_name else "ALL_SERVERS"
        mcp_comm_logger.info(f"=== MCP LIST TOOLS REQUEST [{target}] [ID: {request_id}] ===")
        mcp_comm_logger.info(f"Request ID: {request_id}")
        mcp_comm_logger.info(f"Target: {target}")
        mcp_comm_logger.info(f"=== END LIST TOOLS REQUEST [ID: {request_id}] ===")
    
    def _log_mcp_list_tools_response(self, server_name: str, tools: List[Dict[str, Any]], request_id: str):
        """Log the MCP list tools response."""
        mcp_comm_logger.info(f"=== MCP LIST TOOLS RESPONSE [{server_name}] [ID: {request_id}] ===")
        mcp_comm_logger.info(f"Request ID: {request_id}")
        mcp_comm_logger.info(f"Server: {server_name}")
        mcp_comm_logger.info(f"Tools count: {len(tools)}")
        mcp_comm_logger.info("--- TOOLS ---")
        for i, tool in enumerate(tools):
            mcp_comm_logger.info(f"Tool {i+1}: {tool['name']}")
            mcp_comm_logger.info(f"  Description: {tool['description']}")
            mcp_comm_logger.info(f"  Schema: {json.dumps(tool['inputSchema'], indent=2, default=str)}")
        mcp_comm_logger.info(f"=== END LIST TOOLS RESPONSE [ID: {request_id}] ===")
    
    def _log_mcp_list_tools_error(self, server_name: str, error_message: str, request_id: str):
        """Log MCP list tools errors."""
        mcp_comm_logger.error(f"=== MCP LIST TOOLS ERROR [{server_name}] [ID: {request_id}] ===")
        mcp_comm_logger.error(f"Request ID: {request_id}")
        mcp_comm_logger.error(f"Server: {server_name}")
        mcp_comm_logger.error(f"Error: {error_message}")
        mcp_comm_logger.error(f"=== END LIST TOOLS ERROR [ID: {request_id}] ===")

    async def close(self):
        """Close all MCP client connections."""
        await self.exit_stack.aclose()
        self.sessions.clear()
        self._initialized = False 