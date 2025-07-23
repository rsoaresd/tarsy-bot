"""
History-specific event hooks for capturing LLM and MCP interactions.

Implements specialized hooks for logging LLM interactions and MCP communications
to the history service with microsecond-precision timestamps and human-readable
step descriptions for chronological timeline reconstruction.
"""

from typing import Any, Dict, Optional
from datetime import datetime, timezone
import logging

from .base_hooks import BaseEventHook, generate_step_description
from app.services.history_service import get_history_service

logger = logging.getLogger(__name__)


class LLMHooks(BaseEventHook):
    """
    Event hooks for capturing LLM interactions.
    
    Captures all LLM prompts, responses, tool calls, and performance metrics
    with microsecond-precision timestamps for exact chronological ordering.
    """
    
    def __init__(self):
        """Initialize LLM history hooks."""
        super().__init__("llm_history_hook")
        self.history_service = get_history_service()
    
    async def execute(self, event_type: str, **kwargs) -> None:
        """
        Execute LLM interaction logging.
        
        Args:
            event_type: Type of LLM event (pre, post, error)
            **kwargs: LLM interaction context data
        """
        # Only process post-execution events (when we have results)
        if not event_type.endswith('.post'):
            return
        
        session_id = kwargs.get('session_id')
        if not session_id:
            logger.warning("LLM hook triggered without session_id")
            return
        
        # Extract interaction details
        method_args = kwargs.get('args', {})
        result = kwargs.get('result', {})
        
        # Extract core interaction data
        prompt_text = method_args.get('prompt', '') or method_args.get('messages', '')
        response_text = self._extract_response_text(result)
        model_used = method_args.get('model', 'unknown')
        
        # Extract tool calls and results if present
        tool_calls = self._extract_tool_calls(method_args, result)
        tool_results = self._extract_tool_results(result)
        
        # Extract token usage and timing
        token_usage = self._extract_token_usage(result)
        duration_ms = self._calculate_duration(kwargs.get('start_time'), kwargs.get('end_time'))
        
        # Generate human-readable step description
        step_description = generate_step_description("llm_interaction", {
            "model": model_used,
            "purpose": self._infer_purpose(prompt_text),
            "has_tools": bool(tool_calls)
        })
        
        # Log the interaction to history service
        success = self.history_service.log_llm_interaction(
            session_id=session_id,
            prompt_text=str(prompt_text)[:10000],  # Limit size to prevent DB issues
            response_text=str(response_text)[:10000],
            model_used=model_used,
            step_description=step_description,
            tool_calls=tool_calls,
            tool_results=tool_results,
            token_usage=token_usage,
            duration_ms=duration_ms
        )
        
        if success:
            logger.debug(f"Logged LLM interaction for session {session_id}: {step_description}")
        else:
            logger.warning(f"Failed to log LLM interaction for session {session_id}")
    
    def _extract_response_text(self, result: Any) -> str:
        """
        Extract response text from LLM result.
        
        Args:
            result: LLM response result
            
        Returns:
            Response text content
        """
        if isinstance(result, str):
            return result
        elif isinstance(result, dict):
            # Try common response field names
            for field in ['content', 'text', 'response', 'message']:
                if field in result:
                    return str(result[field])
            return str(result)
        elif hasattr(result, 'content'):
            return str(result.content)
        elif hasattr(result, 'text'):
            return str(result.text)
        else:
            return str(result)
    
    def _extract_tool_calls(self, args: Dict, result: Any) -> Optional[Dict]:
        """
        Extract tool calls from LLM interaction.
        
        Args:
            args: Method arguments
            result: LLM response result
            
        Returns:
            Tool calls data if present
        """
        # Check for tool calls in various formats
        tool_calls = None
        
        # Check result for tool calls
        if isinstance(result, dict):
            if 'tool_calls' in result:
                tool_calls = result['tool_calls']
            elif 'function_calls' in result:
                tool_calls = result['function_calls']
        
        # Check args for tools configuration
        if not tool_calls and 'tools' in args:
            return {"available_tools": args['tools']}
        
        return tool_calls if tool_calls else None
    
    def _extract_tool_results(self, result: Any) -> Optional[Dict]:
        """
        Extract tool execution results.
        
        Args:
            result: LLM response result
            
        Returns:
            Tool results if present
        """
        if isinstance(result, dict):
            for field in ['tool_results', 'function_results', 'tool_outputs']:
                if field in result:
                    return result[field]
        
        return None
    
    def _extract_token_usage(self, result: Any) -> Optional[Dict]:
        """
        Extract token usage statistics.
        
        Args:
            result: LLM response result
            
        Returns:
            Token usage data if present
        """
        if isinstance(result, dict):
            if 'usage' in result:
                return result['usage']
            elif 'token_usage' in result:
                return result['token_usage']
        elif hasattr(result, 'usage'):
            usage = result.usage
            if hasattr(usage, 'dict'):
                return usage.dict()
            else:
                return str(usage)
        
        return None
    
    def _calculate_duration(self, start_time: Optional[datetime], end_time: Optional[datetime]) -> int:
        """
        Calculate interaction duration in milliseconds.
        
        Args:
            start_time: Start timestamp
            end_time: End timestamp
            
        Returns:
            Duration in milliseconds
        """
        if start_time and end_time:
            return int((end_time - start_time).total_seconds() * 1000)
        return 0
    
    def _infer_purpose(self, prompt_text: str) -> str:
        """
        Infer the purpose of the LLM interaction from prompt.
        
        Args:
            prompt_text: The prompt text
            
        Returns:
            Inferred purpose description
        """
        prompt_lower = str(prompt_text).lower()
        
        if any(word in prompt_lower for word in ['analyze', 'analysis', 'investigate']):
            return "analysis"
        elif any(word in prompt_lower for word in ['fix', 'resolve', 'solve', 'repair']):
            return "resolution"
        elif any(word in prompt_lower for word in ['check', 'status', 'inspect']):
            return "inspection"
        elif any(word in prompt_lower for word in ['plan', 'strategy', 'approach']):
            return "planning"
        else:
            return "processing"


class MCPHooks(BaseEventHook):
    """
    Event hooks for capturing MCP communications.
    
    Captures tool discovery, invocations, and results with microsecond-precision
    timestamps to maintain exact chronological ordering with LLM interactions.
    """
    
    def __init__(self):
        """Initialize MCP history hooks."""
        super().__init__("mcp_history_hook")
        self.history_service = get_history_service()
    
    async def execute(self, event_type: str, **kwargs) -> None:
        """
        Execute MCP communication logging.
        
        Args:
            event_type: Type of MCP event (pre, post, error)
            **kwargs: MCP interaction context data
        """
        # Process both successful completions and errors
        if not (event_type.endswith('.post') or event_type.endswith('.error')):
            return
        
        session_id = kwargs.get('session_id')
        if not session_id:
            logger.warning("MCP hook triggered without session_id")
            return
        
        # Extract communication details
        method_args = kwargs.get('args', {})
        result = kwargs.get('result')
        error = kwargs.get('error')
        success = not bool(error)
        
        # Extract MCP-specific data
        server_name = method_args.get('server_name', 'unknown')
        communication_type = self._infer_communication_type(kwargs.get('method', ''), method_args)
        tool_name = method_args.get('tool_name')
        tool_arguments = method_args.get('tool_arguments') or method_args.get('arguments')
        tool_result = self._extract_tool_result(result) if success else None
        available_tools = self._extract_available_tools(result) if communication_type == "tool_list" else None
        
        # Calculate timing
        duration_ms = self._calculate_duration(kwargs.get('start_time'), kwargs.get('end_time'))
        
        # Generate human-readable step description
        step_description = self._generate_step_description(communication_type, server_name, tool_name, method_args)
        
        # Log the communication to history service
        log_success = self.history_service.log_mcp_communication(
            session_id=session_id,
            server_name=server_name,
            communication_type=communication_type,
            step_description=step_description,
            success=success,
            duration_ms=duration_ms,
            tool_name=tool_name,
            tool_arguments=tool_arguments,
            tool_result=tool_result,
            available_tools=available_tools,
            error_message=str(error) if error else None
        )
        
        if log_success:
            logger.debug(f"Logged MCP communication for session {session_id}: {step_description}")
        else:
            logger.warning(f"Failed to log MCP communication for session {session_id}")
    
    def _infer_communication_type(self, method_name: str, args: Dict) -> str:
        """
        Infer the type of MCP communication.
        
        Args:
            method_name: The method being called
            args: Method arguments
            
        Returns:
            Communication type (tool_list, tool_call, result)
        """
        method_lower = method_name.lower()
        
        if 'list' in method_lower or 'discover' in method_lower or 'tools' in method_lower:
            return "tool_list"
        elif 'call' in method_lower or 'execute' in method_lower or args.get('tool_name'):
            return "tool_call"
        elif 'result' in method_lower or 'response' in method_lower:
            return "result"
        else:
            return "tool_call"  # Default assumption
    
    def _extract_tool_result(self, result: Any) -> Optional[Dict]:
        """
        Extract tool execution result.
        
        Args:
            result: MCP call result
            
        Returns:
            Tool result data if present
        """
        if result is None:
            return None
        
        if isinstance(result, dict):
            return result
        elif isinstance(result, (str, int, float, bool)):
            return {"result": result}
        else:
            return {"result": str(result)}
    
    def _extract_available_tools(self, result: Any) -> Optional[Dict]:
        """
        Extract available tools from tool discovery result.
        
        Args:
            result: Tool discovery result
            
        Returns:
            Available tools data if present
        """
        if isinstance(result, dict):
            if 'tools' in result:
                return result
            elif isinstance(result, list):
                return {"tools": result}
        elif isinstance(result, list):
            return {"tools": result}
        
        return None
    
    def _calculate_duration(self, start_time: Optional[datetime], end_time: Optional[datetime]) -> int:
        """
        Calculate communication duration in milliseconds.
        
        Args:
            start_time: Start timestamp
            end_time: End timestamp
            
        Returns:
            Duration in milliseconds
        """
        if start_time and end_time:
            return int((end_time - start_time).total_seconds() * 1000)
        return 0
    
    def _generate_step_description(self, comm_type: str, server_name: str, tool_name: Optional[str], args: Dict) -> str:
        """
        Generate human-readable step description for MCP communication.
        
        Args:
            comm_type: Communication type
            server_name: MCP server name
            tool_name: Tool name if applicable
            args: Method arguments
            
        Returns:
            Human-readable step description
        """
        if comm_type == "tool_list":
            return f"Discover available tools from {server_name}"
        elif comm_type == "tool_call" and tool_name:
            # Try to make tool calls more descriptive based on common patterns
            if 'kubectl' in tool_name.lower():
                namespace = args.get('tool_arguments', {}).get('namespace', '')
                if namespace:
                    return f"Execute {tool_name} in {namespace} namespace"
                else:
                    return f"Execute Kubernetes command {tool_name}"
            elif 'file' in tool_name.lower():
                path = args.get('tool_arguments', {}).get('path', '')
                if path:
                    return f"File operation {tool_name} on {path}"
                else:
                    return f"Execute file operation {tool_name}"
            else:
                return f"Execute {tool_name} via {server_name}"
        else:
            return f"Communicate with {server_name}"


def register_history_hooks():
    """
    Register history hooks with the global hook manager.
    
    This function should be called during application startup to enable
    automatic history capture for LLM and MCP interactions.
    """
    from .base_hooks import get_hook_manager
    
    hook_manager = get_hook_manager()
    
    # Register LLM hooks
    llm_hooks = LLMHooks()
    hook_manager.register_hook("llm.post", llm_hooks)
    hook_manager.register_hook("llm.error", llm_hooks)
    
    # Register MCP hooks  
    mcp_hooks = MCPHooks()
    hook_manager.register_hook("mcp.post", mcp_hooks)
    hook_manager.register_hook("mcp.error", mcp_hooks)
    
    logger.info("History hooks registered successfully")
    return hook_manager 