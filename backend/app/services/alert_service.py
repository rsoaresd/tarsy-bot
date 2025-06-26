"""
Main alert processing service that orchestrates the entire workflow.
"""

import json
import asyncio
from typing import Callable, Dict, Optional

from app.config.settings import Settings
from app.models.alert import Alert
from app.services.runbook_service import RunbookService
from app.integrations.mcp.mcp_client import MCPClient
from app.integrations.llm.client import LLMManager
from app.utils.prompt_builder import PromptBuilder
from app.utils.logger import get_module_logger

# Setup logger for this module
logger = get_module_logger(__name__)


class AlertService:
    """Main service for processing alerts."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.runbook_service = RunbookService(settings)
        self.mcp_client = MCPClient(settings)
        self.llm_manager = LLMManager(settings)
        self.prompt_builder = PromptBuilder()
    
    async def initialize(self):
        """Initialize the alert service and all dependencies."""
        # Initialize MCP servers
        await self.mcp_client.initialize()
        
        logger.info("Alert service initialized successfully")
    
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
            
            # Step 2: Get available MCP tools and let LLM determine which ones to call
            if progress_callback:
                await progress_callback(30, "Analyzing runbook and determining data requirements")
            
            # Get available tools from MCP servers
            available_tools = await self.mcp_client.list_tools()
            
            # Use LLM to determine which tools to call
            mcp_tools_to_call = await self._determine_mcp_tools_with_llm(alert, runbook_data, available_tools)
            
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
    
    async def _determine_mcp_tools_with_llm(self, alert: Alert, runbook_data: Dict, available_tools: Dict) -> list:
        """Use LLM to determine which MCP tools to call based on alert and runbook."""
        
        # Get the default LLM client
        llm_client = self.llm_manager.get_client()
        if not llm_client:
            logger.error("No LLM client available")
            # Fallback to basic tool selection if no LLM is available
            return self._get_fallback_tools(alert)
        
        try:
            # Prepare alert data
            alert_data = alert.model_dump()
            
            # Let the LLM determine which tools to call
            tools_to_call = await llm_client.determine_mcp_tools(
                alert_data, runbook_data, available_tools
            )
            
            # Update cluster information in parameters
            for tool_call in tools_to_call:
                if "parameters" in tool_call and "cluster" in tool_call["parameters"]:
                    # Replace placeholder with actual cluster
                    tool_call["parameters"]["cluster"] = alert.cluster
                if "parameters" in tool_call and "namespace" in tool_call["parameters"]:
                    # Ensure namespace is set correctly
                    if tool_call["parameters"]["namespace"] in ["namespace_name_here", ""]:
                        tool_call["parameters"]["namespace"] = alert.namespace
            
            return tools_to_call
            
        except Exception as e:
            logger.error(f"LLM tool selection failed: {str(e)}")
            # Fallback to basic tool selection
            return self._get_fallback_tools(alert)
    
    def _get_fallback_tools(self, alert: Alert) -> list:
        """Fallback tool selection when LLM is not available."""
        # Basic rule-based fallback for common alerts
        # if alert.alert == "Namespace is stuck in Terminating":
        #     return [
        #         {
        #             "server": "kubernetes",
        #             "tool": "namespaces_list",
        #             "parameters": {},
        #             "reason": "List all namespaces to verify the stuck namespace"
        #         },
        #         {
        #             "server": "kubernetes",
        #             "tool": "resources_get",
        #             "parameters": {
        #                 "apiVersion": "v1",
        #                 "kind": "Namespace",
        #                 "name": alert.namespace
        #             },
        #             "reason": "Get namespace details including finalizers"
        #         },
        #         {
        #             "server": "kubernetes",
        #             "tool": "resources_list",
        #             "parameters": {
        #                 "apiVersion": "v1",
        #                 "kind": "Pod",
        #                 "namespace": alert.namespace
        #             },
        #             "reason": "List pods that might be preventing deletion"
        #         },
        #         {
        #             "server": "kubernetes",
        #             "tool": "events_list",
        #             "parameters": {
        #                 "namespace": alert.namespace
        #             },
        #             "reason": "Check for events that might explain the stuck state"
        #         }
        #     ]
        
        # Default fallback for other alerts
        return []
    
    async def _gather_mcp_data(self, alert: Alert, tools_to_call: list) -> Dict:
        """Gather data from MCP servers based on the determined tools."""
        logger.info(f"Starting MCP data gathering for alert: {alert.alert} - {len(tools_to_call)} tools to call")
        
        mcp_data = {}
        
        # Group tools by server for efficient processing
        tools_by_server = {}
        for tool_call in tools_to_call:
            server = tool_call["server"]
            if server not in tools_by_server:
                tools_by_server[server] = []
            tools_by_server[server].append(tool_call)
        
        logger.info(f"MCP tools grouped by server: {', '.join([f'{server}({len(tools)})' for server, tools in tools_by_server.items()])}")
        
        # Execute tool calls for each server
        for server_name, server_tools in tools_by_server.items():
            logger.info(f"Executing {len(server_tools)} tools on {server_name} server")
            server_data = {}
            
            for tool_call in server_tools:
                try:
                    tool_name = tool_call["tool"]
                    parameters = tool_call["parameters"]
                    reason = tool_call.get("reason", "No reason provided")
                    
                    logger.info(f"Calling {server_name}.{tool_name} - Reason: {reason}")
                    
                    result = await self.mcp_client.call_tool(
                        server_name, tool_name, parameters
                    )
                    
                    server_data[f"{tool_name}_result"] = result
                    logger.info(f"Successfully executed {server_name}.{tool_name}")
                    
                except Exception as e:
                    server_data[f"{tool_call['tool']}_error"] = str(e)
                    logger.error(f"Error calling {server_name}.{tool_call['tool']}: {str(e)}")
            
            if server_data:
                mcp_data[server_name] = server_data
                logger.info(f"Collected {len(server_data)} results from {server_name}")
        
        total_results = sum(len(data) for data in mcp_data.values())
        logger.info(f"MCP data gathering completed - {total_results} total results collected")
        
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
            "# LLM not available!!! Alert Analysis (Fallback Mode)",
            "",
            f"**Alert:** {alert.alert}",
            f"**Severity:** {alert.severity}",
            f"**Environment:** {alert.environment}",
            f"**Cluster:** {alert.cluster}",
            f"**Namespace:** {alert.namespace}",
            f"**Message:** {alert.message}",
            "",
            "## Runbook Information",
            "The following runbook was retrieved:",
            f"- Raw content: {runbook_data.get('raw_content', 'No runbook available')}",
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
        await self.mcp_client.close() 