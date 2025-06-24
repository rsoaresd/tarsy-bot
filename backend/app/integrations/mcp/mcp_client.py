"""
MCP client using the official MCP SDK for integration with MCP servers.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain.tools import Tool
from langchain_core.utils.function_calling import convert_to_openai_function

from app.config.settings import Settings


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
                print(f"Initialized MCP server: {server_name}")
                
            except Exception as e:
                print(f"Failed to initialize MCP server {server_name}: {str(e)}")
        
        self._initialized = True
    
    async def list_tools(self, server_name: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """List available tools from MCP servers."""
        if not self._initialized:
            await self.initialize()
        
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
                except Exception as e:
                    print(f"Error listing tools from {server_name}: {str(e)}")
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
                except Exception as e:
                    print(f"Error listing tools from {name}: {str(e)}")
                    all_tools[name] = []
        
        return all_tools
    
    async def create_langchain_tools(self, server_name: Optional[str] = None) -> List[Tool]:
        """Create LangChain tools from MCP servers."""
        if not self._initialized:
            await self.initialize()
        
        langchain_tools = []
        
        if server_name:
            # Create tools from specific server
            if server_name in self.sessions:
                tools = await self._create_tools_for_server(server_name)
                langchain_tools.extend(tools)
        else:
            # Create tools from all servers
            for name in self.sessions.keys():
                tools = await self._create_tools_for_server(name)
                langchain_tools.extend(tools)
        
        return langchain_tools
    
    async def _create_tools_for_server(self, server_name: str) -> List[Tool]:
        """Create LangChain tools for a specific server."""
        tools = []
        session = self.sessions.get(server_name)
        
        if not session:
            return tools
        
        try:
            tools_result = await session.list_tools()
            
            for tool in tools_result.tools:
                # Create a function that calls the MCP tool
                async def call_tool(server=server_name, tool_name=tool.name, **kwargs):
                    return await self.call_tool(server, tool_name, kwargs)
                
                # Create LangChain tool
                langchain_tool = Tool(
                    name=f"{server_name}_{tool.name}",
                    description=tool.description or f"Tool {tool.name} from {server_name}",
                    func=lambda **kwargs: asyncio.run(call_tool(**kwargs)),
                    coroutine=call_tool
                )
                
                tools.append(langchain_tool)
                
        except Exception as e:
            print(f"Error creating tools for {server_name}: {str(e)}")
        
        return tools
    
    async def call_tool(self, server_name: str, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool on an MCP server."""
        if not self._initialized:
            await self.initialize()
        
        if server_name not in self.sessions:
            raise Exception(f"MCP server not found: {server_name}")
        
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
                    return {"result": "\n".join(text_parts)}
                else:
                    return {"result": str(content)}
            else:
                return {"result": str(result)}
                
        except Exception as e:
            raise Exception(f"Failed to call tool {tool_name} on {server_name}: {str(e)}")
    
    async def close(self):
        """Close all MCP client connections."""
        await self.exit_stack.aclose()
        self.sessions.clear()
        self._initialized = False 