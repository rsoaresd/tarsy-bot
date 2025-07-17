"""
Main alert processing service that orchestrates the entire workflow.
"""

import json
from typing import Any, Callable, Dict, List, Optional

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
        
        # Validate LLM availability
        if not self.llm_manager.is_available():
            available_providers = self.llm_manager.list_available_providers()
            status = self.llm_manager.get_availability_status()
            raise Exception(f"No LLM providers are available. Configured providers: {available_providers}, Status: {status}")
        
        logger.info("Alert service initialized successfully")
    
    async def process_alert(self, 
                          alert: Alert, 
                          progress_callback: Optional[Callable] = None) -> str:
        """Process an alert through the complete iterative workflow."""
        
        # Validate LLM availability before processing
        if not self.llm_manager.is_available():
            available_providers = self.llm_manager.list_available_providers()
            status = self.llm_manager.get_availability_status()
            raise Exception(f"Cannot process alert: No LLM providers are available. Configured providers: {available_providers}, Status: {status}")
        
        try:
            # Step 1: Download runbook
            if progress_callback:
                await progress_callback(10, "Downloading runbook")
            
            runbook_content = await self.runbook_service.download_runbook(alert.runbook)
            
            # Step 2: Get available MCP tools
            if progress_callback:
                await progress_callback(15, "Getting available MCP tools")
            
            available_tools = await self.mcp_client.list_tools()
            
            # Step 3: Iterative LLM->MCP loop processing
            iteration_history = []
            all_mcp_data = {}
            max_iterations = self.settings.max_llm_mcp_iterations
            
            logger.info(f"Starting iterative processing - max iterations: {max_iterations}")
            
            for iteration in range(1, max_iterations + 1):
                logger.info(f"=== Starting Iteration {iteration}/{max_iterations} ===")
                
                # Calculate progress for this iteration (20% to 85% of total progress)
                iteration_progress_start = 20 + ((iteration - 1) * 65 // max_iterations)
                iteration_progress_end = 20 + (iteration * 65 // max_iterations)
                
                if progress_callback:
                    await progress_callback(
                        iteration_progress_start, 
                        f"Iteration {iteration}/{max_iterations}: Determining next steps"
                    )
                
                # Determine what tools to call next (or if we should stop)
                next_action = await self._determine_next_mcp_tools_with_llm(
                    alert, runbook_content, available_tools, iteration_history, iteration
                )
                
                # Apply safeguards to prevent infinite loops
                total_tools_called = sum(len(it.get('tools_called', [])) for it in iteration_history)
                total_data_points = sum(sum(len(data) if isinstance(data, list) else 1 for data in it.get('mcp_data', {}).values()) for it in iteration_history)
                
                # Hard stop conditions
                should_force_stop = False
                force_stop_reason = ""
                
                if iteration >= max_iterations:
                    should_force_stop = True
                    force_stop_reason = f"Reached maximum iterations ({max_iterations})"
                elif total_tools_called >= self.settings.max_total_tool_calls:
                    should_force_stop = True
                    force_stop_reason = f"Called too many tools ({total_tools_called}) - likely sufficient data collected"
                elif total_data_points >= self.settings.max_data_points and iteration >= 3:
                    should_force_stop = True
                    force_stop_reason = f"Collected substantial data ({total_data_points} data points) over {iteration} iterations"
                
                if should_force_stop:
                    logger.warning(f"Force stopping iteration loop: {force_stop_reason}")
                    break
                
                if not next_action.get("continue", False):
                    logger.info(f"LLM decided to stop after {iteration} iterations: {next_action.get('reasoning', 'No reason provided')}")
                    break
                
                tools_to_call = next_action.get("tools", [])
                if not tools_to_call:
                    logger.info(f"No tools to call in iteration {iteration}, stopping")
                    break
                
                # Update progress
                if progress_callback:
                    await progress_callback(
                        iteration_progress_start + (iteration_progress_end - iteration_progress_start) // 3,
                        f"Iteration {iteration}/{max_iterations}: Gathering data ({len(tools_to_call)} tools)"
                    )
                
                # Execute the determined tools
                iteration_mcp_data = await self._gather_mcp_data(alert, tools_to_call)
                
                # Update accumulated data
                for server_name, server_data in iteration_mcp_data.items():
                    if server_name not in all_mcp_data:
                        all_mcp_data[server_name] = []
                    # server_data is a list of results, so extend the list instead of update
                    if isinstance(server_data, list):
                        all_mcp_data[server_name].extend(server_data)
                    else:
                        # Handle legacy dict format if needed
                        all_mcp_data[server_name].append(server_data)
                
                # Update progress
                if progress_callback:
                    await progress_callback(
                        iteration_progress_start + 2 * (iteration_progress_end - iteration_progress_start) // 3,
                        f"Iteration {iteration}/{max_iterations}: Analyzing results"
                    )
                
                # Record this iteration in history (WITHOUT partial analysis first)
                iteration_record = {
                    "iteration": iteration,
                    "reasoning": next_action.get("reasoning", ""),
                    "tools_called": tools_to_call,
                    "mcp_data": iteration_mcp_data,
                    "partial_analysis": ""  # Will be filled after analysis
                }
                
                # Add current iteration to history so partial analysis can see it
                iteration_history.append(iteration_record)
                
                # Perform partial analysis of this iteration's results (with current data)
                partial_analysis = await self._perform_partial_analysis(
                    alert, runbook_content, iteration_history, iteration
                )
                
                # Update the iteration record with the analysis
                iteration_record["partial_analysis"] = partial_analysis
                
                logger.info(f"=== Completed Iteration {iteration}/{max_iterations} ===")
                logger.info(f"Tools called: {len(tools_to_call)}, Data points: {sum(len(data) if isinstance(data, list) else 1 for data in iteration_mcp_data.values())}")
            
            # Step 4: Final comprehensive analysis
            if progress_callback:
                await progress_callback(90, "Performing final comprehensive analysis")
            
            final_analysis = await self._perform_final_analysis(alert, runbook_content, all_mcp_data, iteration_history)
            
            # Step 5: Complete
            if progress_callback:
                await progress_callback(100, "Analysis complete")
            
            logger.info(f"Alert processing completed after {len(iteration_history)} iterations")
            
            return final_analysis
            
        except Exception as e:
            error_msg = f"Alert processing failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            if progress_callback:
                await progress_callback(0, error_msg)
            raise Exception(error_msg)
    
    async def _determine_next_mcp_tools_with_llm(self, 
                                               alert: Alert, 
                                               runbook_content: str, 
                                               available_tools: Dict,
                                               iteration_history: List[Dict],
                                               current_iteration: int) -> Dict:
        """Use LLM to determine which MCP tools to call based on current context."""
        
        # Get the default LLM client
        llm_client = self.llm_manager.get_client()
        if not llm_client:
            logger.error("No LLM client available")
            raise Exception("LLM client not available - cannot process alert without LLM")
        
        # Prepare alert data
        alert_data = alert.model_dump()
        
        # For first iteration, use the original method
        if current_iteration == 1:
            tools_to_call = await llm_client.determine_mcp_tools(
                alert_data, runbook_content, available_tools
            )
            
            # Update cluster information in parameters
            for tool_call in tools_to_call:
                if "parameters" in tool_call and "cluster" in tool_call["parameters"]:
                    tool_call["parameters"]["cluster"] = alert.cluster
                if "parameters" in tool_call and "namespace" in tool_call["parameters"]:
                    if tool_call["parameters"]["namespace"] in ["namespace_name_here", ""]:
                        tool_call["parameters"]["namespace"] = alert.namespace
            
            return {
                "continue": len(tools_to_call) > 0,
                "tools": tools_to_call,
                "reasoning": f"Initial tool selection - {len(tools_to_call)} tools determined"
            }
        else:
            # For subsequent iterations, use the iterative method
            return await llm_client.determine_next_mcp_tools(
                alert_data, runbook_content, available_tools, iteration_history, current_iteration
            )
    
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
            server_results = []  # Use a list to preserve all results with their metadata
            
            for tool_call in server_tools:
                try:
                    tool_name = tool_call["tool"]
                    parameters = tool_call["parameters"]
                    reason = tool_call.get("reason", "No reason provided")
                    
                    logger.info(f"Calling {server_name}.{tool_name} - Reason: {reason}")
                    
                    result = await self.mcp_client.call_tool(
                        server_name, tool_name, parameters
                    )
                    
                    # Store result with tool metadata
                    server_results.append({
                        'tool': tool_name,
                        'parameters': parameters,
                        'reason': reason,
                        'result': result
                    })
                    logger.info(f"Successfully executed {server_name}.{tool_name}")
                    
                except Exception as e:
                    server_results.append({
                        'tool': tool_call['tool'],
                        'parameters': tool_call.get('parameters', {}),
                        'reason': tool_call.get('reason', ''),
                        'error': str(e)
                    })
                    logger.error(f"Error calling {server_name}.{tool_call['tool']}: {str(e)}")
            
            if server_results:
                mcp_data[server_name] = server_results
                logger.info(f"Collected {len(server_results)} results from {server_name}")
        
        total_results = sum(len(data) for data in mcp_data.values())
        logger.info(f"MCP data gathering completed - {total_results} total results collected")
        
        return mcp_data
    
    async def _perform_partial_analysis(self,
                                       alert: Alert,
                                       runbook_content: str,
                                       iteration_history: List[Dict],
                                       current_iteration: int) -> str:
        """Perform partial analysis of current iteration results."""
        
        # Prepare alert data for LLM
        alert_data = alert.model_dump()
        
        try:
            # Use the LLM manager to analyze partial results
            analysis = await self.llm_manager.analyze_partial_results(
                alert_data, runbook_content, iteration_history, current_iteration
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Partial analysis failed: {str(e)}")
            return f"Partial analysis error: {str(e)}"
    
    async def _perform_final_analysis(self,
                                    alert: Alert,
                                    runbook_content: str,
                                    all_mcp_data: Dict,
                                    iteration_history: List[Dict]) -> str:
        """Perform final comprehensive analysis with all gathered data."""
        
        # Use the enhanced LLM analysis that includes iteration context
        analysis = await self._perform_llm_analysis_with_iterations(
            alert, runbook_content, all_mcp_data, iteration_history
        )
        
        return analysis

    async def _perform_llm_analysis_with_iterations(self,
                                                  alert: Alert,
                                                  runbook_content: str,
                                                  mcp_data: Dict,
                                                  iteration_history: List[Dict]) -> str:
        """Perform LLM analysis including iteration context."""
        
        # Prepare alert data for LLM
        alert_data = alert.model_dump()
        
        try:
            # Use the LLM manager to analyze the alert with enhanced context
            analysis = await self.llm_manager.analyze_alert(
                alert_data, runbook_content, mcp_data
            )
            
            # Add iteration summary to the analysis
            if iteration_history:
                iteration_summary = self._generate_iteration_summary(iteration_history)
                analysis = f"{analysis}\n\n---\n\n## Iteration Summary\n\n{iteration_summary}"
            
            return analysis
            
        except Exception as e:
            logger.error(f"LLM analysis with iterations failed: {str(e)}")
            raise e

    async def _perform_llm_analysis(self, 
                                  alert: Alert, 
                                  runbook_content: str, 
                                  mcp_data: Dict) -> str:
        """Perform LLM analysis of the alert, runbook, and MCP data."""
        
        # Prepare alert data for LLM
        alert_data = alert.model_dump()
        
        # Use the LLM manager to analyze the alert
        analysis = await self.llm_manager.analyze_alert(
            alert_data, runbook_content, mcp_data
        )
        
        return analysis
    
    def _generate_iteration_summary(self, iteration_history: List[Dict]) -> str:
        """Generate a summary of all iterations for the final analysis."""
        
        if not iteration_history:
            return "No iterations were performed."
        
        summary_parts = [
            f"This analysis was completed through {len(iteration_history)} iterative steps:",
            ""
        ]
        
        for i, iteration in enumerate(iteration_history, 1):
            tools_called = iteration.get('tools_called', [])
            reasoning = iteration.get('reasoning', 'No reasoning provided')
            
            summary_parts.append(f"**Iteration {i}:**")
            summary_parts.append(f"- **Reasoning:** {reasoning}")
            summary_parts.append(f"- **Tools Called:** {len(tools_called)} tools")
            
            # List the tools
            for tool in tools_called:
                server = tool.get('server', 'unknown')
                tool_name = tool.get('tool', 'unknown')
                reason = tool.get('reason', 'No reason provided')
                summary_parts.append(f"  - {server}.{tool_name}: {reason}")
            
            # Add partial analysis summary if available
            if iteration.get('partial_analysis'):
                # Take first 2 lines of partial analysis as summary  
                partial_lines = iteration['partial_analysis'].split('\n')[:2]
                partial_summary = ' '.join(partial_lines).strip()
                if partial_summary:
                    summary_parts.append(f"- **Key Findings:** {partial_summary}")
            
            summary_parts.append("")
        
        summary_parts.extend([
            f"**Total MCP Tool Calls:** {sum(len(it.get('tools_called', [])) for it in iteration_history)}",
            f"**Total Data Points Collected:** {sum(sum(len(data) if isinstance(data, list) else 1 for data in it.get('mcp_data', {}).values()) for it in iteration_history)}"
        ])
        
        return "\n".join(summary_parts)
    
    async def close(self):
        """Clean up resources."""
        await self.runbook_service.close()
        await self.mcp_client.close()

    def _format_mcp_results(self, mcp_results: Dict[str, Any]) -> str:
        """Format MCP results for LLM consumption"""
        if not mcp_results:
            return "No MCP data collected."
        
        formatted_parts = []
        for server, data in mcp_results.items():
            # Data should now always be a list
            if isinstance(data, list):
                data_count = len(data)
                formatted_parts.append(f"**{server}**: {data_count} data points collected")
                
                # Format each result in the list
                for item in data:
                    tool_name = item.get('tool', 'unknown_tool')
                    params = item.get('parameters', {})
                    
                    # Create a unique result key based on tool and parameters
                    if tool_name == 'resources_list' and 'kind' in params:
                        result_key = f"{tool_name}_{params['kind']}_result"
                    elif tool_name == 'resources_get' and 'kind' in params:
                        result_key = f"{tool_name}_{params['kind']}_result"
                    else:
                        # For other tools, use the tool name directly
                        result_key = f"{tool_name}_result"
                    
                    result_key = result_key.replace('.', '_')
                    
                    # Handle both successful results and errors
                    if 'result' in item:
                        result = item['result']
                        formatted_parts.append(f"  - **{result_key}**:")
                        formatted_parts.append("```")
                        formatted_parts.append(json.dumps({"result": result}, indent=2))
                        formatted_parts.append("```")
                    elif 'error' in item:
                        formatted_parts.append(f"  - **{result_key}_error**: {item['error']}")
            else:
                # Handle unexpected non-list data (should not happen with new structure)
                formatted_parts.append(f"**{server}**: 1 data point collected")
                formatted_parts.append(f"  - **result**:")
                formatted_parts.append("```")
                formatted_parts.append(json.dumps(data, indent=2))
                formatted_parts.append("```")
        
        return "\n".join(formatted_parts) 