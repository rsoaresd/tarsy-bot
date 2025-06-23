"""
Main alert processing service that orchestrates the entire workflow.
"""

import json
import asyncio
from typing import Callable, Dict, Optional

from app.config.settings import Settings
from app.models.alert import Alert
from app.services.runbook_service import RunbookService
from app.integrations.mcp.base import MCPOrchestrator
from app.integrations.llm.base import LLMManager
from app.utils.prompt_builder import PromptBuilder


class AlertService:
    """Main service for processing alerts."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.runbook_service = RunbookService(settings)
        self.mcp_orchestrator = MCPOrchestrator(settings)
        self.llm_manager = LLMManager(settings)
        self.prompt_builder = PromptBuilder()
    
    async def initialize(self):
        """Initialize the alert service and all dependencies."""
        # Initialize MCP servers
        await self.mcp_orchestrator.initialize()
        
        print("Alert service initialized successfully")
    
    async def process_alert(self, 
                          alert: Alert, 
                          progress_callback: Optional[Callable] = None) -> str:
        """Process an alert through the complete workflow."""
        
        try:
            # Step 1: Download and parse runbook
            if progress_callback:
                await progress_callback(20, "Downloading runbook")
            
            runbook_content = await self.runbook_service.download_runbook(alert.runbook)
            runbook_data = self.runbook_service.parse_runbook(runbook_content)
            
            # Step 2: Determine which MCP tools to call
            if progress_callback:
                await progress_callback(30, "Analyzing runbook and determining data requirements")
            
            mcp_tools_to_call = await self._determine_mcp_tools(alert, runbook_data)
            
            # Step 3: Gather data from MCP servers
            if progress_callback:
                await progress_callback(50, "Gathering system data from MCP servers")
            
            mcp_data = await self._gather_mcp_data(alert, mcp_tools_to_call)
            
            # Step 4: Perform LLM analysis
            if progress_callback:
                await progress_callback(80, "Performing AI analysis")
            
            analysis_result = await self._perform_llm_analysis(alert, runbook_data, mcp_data)
            
            # Step 5: Complete
            if progress_callback:
                await progress_callback(100, "Analysis complete")
            
            return analysis_result
            
        except Exception as e:
            error_msg = f"Alert processing failed: {str(e)}"
            if progress_callback:
                await progress_callback(0, error_msg)
            raise Exception(error_msg)
    
    async def _determine_mcp_tools(self, alert: Alert, runbook_data: Dict) -> list:
        """Determine which MCP tools to call based on alert and runbook."""
        
        # Get available tools from all MCP servers
        available_tools = await self.mcp_orchestrator.list_all_tools()
        
        # For now, use a simple rule-based approach for "Namespace stuck in Terminating"
        # In the future, this could be enhanced with LLM-based tool selection
        if alert.alert == "Namespace is stuck in Terminating":
            return [
                {
                    "server": "kubernetes",
                    "tool": "get_namespace_status",
                    "parameters": {
                        "cluster": alert.cluster,
                        "namespace": alert.namespace
                    },
                    "reason": "Check namespace status and finalizers"
                },
                {
                    "server": "kubernetes",
                    "tool": "list_namespace_resources",
                    "parameters": {
                        "cluster": alert.cluster,
                        "namespace": alert.namespace
                    },
                    "reason": "List resources that might be preventing deletion"
                },
                {
                    "server": "kubernetes",
                    "tool": "get_events_in_namespace",
                    "parameters": {
                        "cluster": alert.cluster,
                        "namespace": alert.namespace
                    },
                    "reason": "Check for events that might explain the stuck state"
                }
            ]
        
        # Default fallback for other alert types
        return []
    
    async def _gather_mcp_data(self, alert: Alert, tools_to_call: list) -> Dict:
        """Gather data from MCP servers based on the determined tools."""
        mcp_data = {}
        
        # Group tools by server for efficient processing
        tools_by_server = {}
        for tool_call in tools_to_call:
            server = tool_call["server"]
            if server not in tools_by_server:
                tools_by_server[server] = []
            tools_by_server[server].append(tool_call)
        
        # Execute tool calls for each server
        for server_name, server_tools in tools_by_server.items():
            server_data = {}
            
            for tool_call in server_tools:
                try:
                    tool_name = tool_call["tool"]
                    parameters = tool_call["parameters"]
                    
                    result = await self.mcp_orchestrator.call_tool(
                        server_name, tool_name, parameters
                    )
                    
                    server_data[f"{tool_name}_result"] = result
                    
                except Exception as e:
                    server_data[f"{tool_call['tool']}_error"] = str(e)
                    print(f"Error calling {server_name}.{tool_call['tool']}: {str(e)}")
            
            if server_data:
                mcp_data[server_name] = server_data
        
        return mcp_data
    
    async def _perform_llm_analysis(self, 
                                  alert: Alert, 
                                  runbook_data: Dict, 
                                  mcp_data: Dict) -> str:
        """Perform LLM analysis of the alert, runbook, and MCP data."""
        
        # Prepare alert data for LLM
        alert_data = alert.model_dump()
        
        try:
            # Use the LLM manager to analyze the alert
            analysis = await self.llm_manager.analyze_alert(
                alert_data, runbook_data, mcp_data
            )
            
            return analysis
            
        except Exception as e:
            # If LLM analysis fails, provide a basic summary
            fallback_analysis = self._generate_fallback_analysis(alert, runbook_data, mcp_data)
            return f"LLM Analysis Error: {str(e)}\n\n{fallback_analysis}"
    
    def _generate_fallback_analysis(self, 
                                  alert: Alert, 
                                  runbook_data: Dict, 
                                  mcp_data: Dict) -> str:
        """Generate a basic analysis when LLM is not available."""
        
        analysis_parts = [
            "# Alert Analysis (Fallback Mode)",
            "",
            f"**Alert:** {alert.alert}",
            f"**Severity:** {alert.severity}",
            f"**Environment:** {alert.environment}",
            f"**Cluster:** {alert.cluster}",
            f"**Namespace:** {alert.namespace}",
            f"**Message:** {alert.message}",
            "",
            "## Runbook Information",
            "The following runbook was retrieved and parsed:",
            f"- Sections identified: {len(runbook_data.get('sections', {}))}", 
            f"- Troubleshooting steps: {len(runbook_data.get('troubleshooting_steps', []))}",
            f"- Commands found: {len(runbook_data.get('commands', []))}",
            "",
            "## System Data",
            "The following data was gathered from MCP servers:",
        ]
        
        for server_name, server_data in mcp_data.items():
            analysis_parts.append(f"- {server_name}: {len(server_data)} data points collected")
        
        analysis_parts.extend([
            "",
            "## Recommendation",
            "Please review the runbook instructions and system data manually.",
            "LLM analysis was not available for automated insights.",
        ])
        
        return "\n".join(analysis_parts)
    
    async def close(self):
        """Clean up resources."""
        await self.runbook_service.close()
        await self.mcp_orchestrator.close_all() 