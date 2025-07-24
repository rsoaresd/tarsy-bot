"""
Dashboard broadcast hooks for real-time WebSocket updates.

Implements specialized hooks for broadcasting LLM interactions and MCP communications
to dashboard clients via WebSocket connections using the same event pipeline as
history hooks for consistent data and timing.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from tarsy.services.websocket_manager import WebSocketManager
from tarsy.models.websocket_models import ChannelType
from tarsy.utils.logger import get_module_logger

from .base_hooks import BaseEventHook, generate_step_description

logger = get_module_logger(__name__)


class DashboardLLMHooks(BaseEventHook):
    """
    Dashboard broadcast hooks for LLM interactions.
    
    Captures LLM interactions and broadcasts real-time updates to dashboard
    clients subscribed to relevant channels, working alongside history hooks
    using the same event data for consistency.
    """
    
    def __init__(self, websocket_manager: WebSocketManager, update_service=None):
        """
        Initialize dashboard LLM broadcast hooks.
        
        Args:
            websocket_manager: WebSocket manager for dashboard broadcasting
            update_service: Optional dashboard update service for intelligent batching
        """
        super().__init__("llm_dashboard_broadcast_hook")
        self.websocket_manager = websocket_manager
        self.update_service = update_service
    
    async def execute(self, event_type: str, **kwargs) -> None:
        """
        Execute LLM interaction broadcasting.
        
        Args:
            event_type: Type of LLM event (pre, post, error)
            **kwargs: LLM interaction context data
        """
        # Process both successful completions and errors for real-time updates
        if not (event_type.endswith('.post') or event_type.endswith('.error')):
            return
        
        session_id = kwargs.get('session_id')
        if not session_id:
            logger.debug("Dashboard LLM hook triggered without session_id")
            return
        
        # Extract interaction details (same as history hooks for consistency)
        method_args = kwargs.get('args', {})
        result = kwargs.get('result', {})
        error = kwargs.get('error')
        success = not bool(error)
        
        # Extract core interaction data
        prompt_text = method_args.get('prompt', '') or method_args.get('messages', '')
        response_text = self._extract_response_text(result) if success else None
        model_used = method_args.get('model', 'unknown')
        
        # Extract tool calls and timing
        tool_calls = self._extract_tool_calls(method_args, result) if success else None
        duration_ms = self._calculate_duration(kwargs.get('start_time'), kwargs.get('end_time'))
        
        # Generate human-readable step description
        step_description = generate_step_description("llm_interaction", {
            "model": model_used,
            "purpose": self._infer_purpose(prompt_text),
            "has_tools": bool(tool_calls)
        })
        
        # Create dashboard update for session-specific channel
        session_update_data = {
            "interaction_type": "llm",
            "session_id": session_id,
            "step_description": step_description,
            "model_used": model_used,
            "success": success,
            "duration_ms": duration_ms,
            "timestamp": kwargs.get('end_time', datetime.now()).isoformat(),
            "tool_calls_present": bool(tool_calls),
            "error_message": str(error) if error else None
        }
        
        # Include truncated content for debugging (not full content due to size)
        if prompt_text:
            session_update_data["prompt_preview"] = str(prompt_text)[:200] + "..." if len(str(prompt_text)) > 200 else str(prompt_text)
        if response_text:
            session_update_data["response_preview"] = str(response_text)[:200] + "..." if len(str(response_text)) > 200 else str(response_text)
        
        # Use dashboard update service if available, otherwise fallback to direct broadcasting
        dashboard_manager = self.websocket_manager.dashboard_manager
        if dashboard_manager.update_service:
            # Use update service for intelligent batching and session tracking
            sent_count = await dashboard_manager.update_service.process_llm_interaction(
                session_id, session_update_data, broadcast_immediately=not success  # Broadcast errors immediately
            )
            
            if sent_count > 0:
                logger.debug(f"Dashboard update service processed LLM interaction for session {session_id}: {step_description}")
        else:
            # Fallback to direct broadcasting
            session_sent = await self.websocket_manager.broadcast_session_update_advanced(
                session_id, session_update_data
            )
            
            dashboard_update_data = {
                "type": "llm_interaction",
                "session_id": session_id,
                "step_description": step_description,
                "model": model_used,
                "status": "completed" if success else "error",
                "duration_ms": duration_ms,
                "timestamp": kwargs.get('end_time', datetime.now()).isoformat()
            }
            
            dashboard_sent = await self.websocket_manager.broadcast_dashboard_update_advanced(
                dashboard_update_data
            )
            
            if session_sent or dashboard_sent:
                logger.debug(f"Broadcast LLM interaction for session {session_id} to {session_sent + dashboard_sent} subscribers: {step_description}")
    

    
    def _extract_response_text(self, result: Any) -> str:
        """Extract response text from LLM result (same logic as history hooks)."""
        if isinstance(result, str):
            return result
        elif isinstance(result, dict):
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
        """Extract tool calls from LLM interaction (same logic as history hooks)."""
        tool_calls = None
        
        if isinstance(result, dict):
            if 'tool_calls' in result:
                tool_calls = result['tool_calls']
            elif 'function_calls' in result:
                tool_calls = result['function_calls']
        
        if not tool_calls and 'tools' in args:
            return {"available_tools": args['tools']}
        
        return tool_calls if tool_calls else None
    
    def _calculate_duration(self, start_time: Optional[datetime], end_time: Optional[datetime]) -> int:
        """Calculate interaction duration in milliseconds."""
        if start_time and end_time:
            return int((end_time - start_time).total_seconds() * 1000)
        return 0
    
    def _infer_purpose(self, prompt_text: str) -> str:
        """Infer the purpose of the LLM interaction from prompt (same logic as history hooks)."""
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


class DashboardMCPHooks(BaseEventHook):
    """
    Dashboard broadcast hooks for MCP communications.
    
    Captures MCP communications and broadcasts real-time updates to dashboard
    clients, maintaining exact chronological ordering with LLM interactions.
    """
    
    def __init__(self, websocket_manager: WebSocketManager, update_service=None):
        """
        Initialize dashboard MCP broadcast hooks.
        
        Args:
            websocket_manager: WebSocket manager for dashboard broadcasting
            update_service: Optional dashboard update service for intelligent batching
        """
        super().__init__("mcp_dashboard_broadcast_hook")
        self.update_service = update_service
        self.websocket_manager = websocket_manager
    
    async def execute(self, event_type: str, **kwargs) -> None:
        """
        Execute MCP communication broadcasting.
        
        Args:
            event_type: Type of MCP event (pre, post, error)
            **kwargs: MCP interaction context data
        """
        # Process both successful completions and errors
        if not (event_type.endswith('.post') or event_type.endswith('.error')):
            return
        
        session_id = kwargs.get('session_id')
        if not session_id:
            logger.debug("Dashboard MCP hook triggered without session_id")
            return
        
        # Extract communication details (same as history hooks)
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
        
        # Calculate timing
        duration_ms = self._calculate_duration(kwargs.get('start_time'), kwargs.get('end_time'))
        
        # Generate human-readable step description
        step_description = self._generate_step_description(communication_type, server_name, tool_name, method_args)
        
        # Create dashboard update for session-specific channel
        session_update_data = {
            "interaction_type": "mcp",
            "session_id": session_id,
            "step_description": step_description,
            "server_name": server_name,
            "communication_type": communication_type,
            "tool_name": tool_name,
            "success": success,
            "duration_ms": duration_ms,
            "timestamp": kwargs.get('end_time', datetime.now()).isoformat(),
            "error_message": str(error) if error else None
        }
        
        # Include tool details if present
        if tool_arguments:
            session_update_data["tool_arguments"] = tool_arguments
        if tool_result:
            # Truncate large results
            result_str = str(tool_result)
            session_update_data["tool_result_preview"] = result_str[:300] + "..." if len(result_str) > 300 else result_str
        
        # Use dashboard update service if available, otherwise fallback to direct broadcasting
        dashboard_manager = self.websocket_manager.dashboard_manager
        if dashboard_manager.update_service:
            # Use update service for intelligent batching and session tracking
            sent_count = await dashboard_manager.update_service.process_mcp_communication(
                session_id, session_update_data, broadcast_immediately=not success  # Broadcast errors immediately
            )
            
            if sent_count > 0:
                logger.debug(f"Dashboard update service processed MCP communication for session {session_id}: {step_description}")
        else:
            # Fallback to direct broadcasting
            session_sent = await self.websocket_manager.broadcast_session_update_advanced(
                session_id, session_update_data
            )
            
            dashboard_update_data = {
                "type": "mcp_communication",
                "session_id": session_id,
                "step_description": step_description,
                "server": server_name,
                "tool": tool_name,
                "status": "completed" if success else "error",
                "duration_ms": duration_ms,
                "timestamp": kwargs.get('end_time', datetime.now()).isoformat()
            }
            
            dashboard_sent = await self.websocket_manager.broadcast_dashboard_update_advanced(
                dashboard_update_data
            )
            
            if session_sent or dashboard_sent:
                logger.debug(f"Broadcast MCP communication for session {session_id} to {session_sent + dashboard_sent} subscribers: {step_description}")
    

    
    def _infer_communication_type(self, method_name: str, args: Dict) -> str:
        """Infer the type of MCP communication (same logic as history hooks)."""
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
        """Extract tool execution result (same logic as history hooks)."""
        if result is None:
            return None
        
        if isinstance(result, dict):
            return result
        elif isinstance(result, (str, int, float, bool)):
            return {"result": result}
        else:
            return {"result": str(result)}
    
    def _calculate_duration(self, start_time: Optional[datetime], end_time: Optional[datetime]) -> int:
        """Calculate communication duration in milliseconds."""
        if start_time and end_time:
            return int((end_time - start_time).total_seconds() * 1000)
        return 0
    
    def _generate_step_description(self, comm_type: str, server_name: str, tool_name: Optional[str], args: Dict) -> str:
        """Generate human-readable step description for MCP communication (same logic as history hooks)."""
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


def register_dashboard_hooks(websocket_manager: WebSocketManager):
    """
    Register dashboard broadcast hooks with the global hook manager.
    
    This function should be called during application startup to enable
    automatic dashboard broadcasting for LLM and MCP interactions.
    
    Args:
        websocket_manager: WebSocket manager for dashboard broadcasting
    """
    from .base_hooks import get_hook_manager
    
    hook_manager = get_hook_manager()
    
    # Register dashboard LLM hooks
    llm_dashboard_hooks = DashboardLLMHooks(websocket_manager=websocket_manager)
    hook_manager.register_hook("llm.post", llm_dashboard_hooks)
    hook_manager.register_hook("llm.error", llm_dashboard_hooks)
    
    # Register dashboard MCP hooks
    mcp_dashboard_hooks = DashboardMCPHooks(websocket_manager=websocket_manager)
    hook_manager.register_hook("mcp.post", mcp_dashboard_hooks)
    hook_manager.register_hook("mcp.error", mcp_dashboard_hooks)
    
    logger.info("Dashboard broadcast hooks registered successfully")
    return hook_manager


def register_integrated_hooks(websocket_manager: WebSocketManager):
    """
    Register both history and dashboard hooks with the global hook manager.
    
    This function integrates dashboard broadcasting with the existing EP-0003
    history hooks, ensuring both systems receive the same event data for
    consistency between historical records and real-time dashboard updates.
    
    Args:
        websocket_manager: WebSocket manager for dashboard broadcasting
    """
    from .base_hooks import get_hook_manager
    
    # Register history hooks first (existing EP-0003 functionality)
    register_history_hooks()
    
    # Register dashboard hooks alongside history hooks
    register_dashboard_hooks(websocket_manager)
    
    hook_manager = get_hook_manager()
    logger.info("Integrated hook system registered: history + dashboard broadcasting")
    
    return hook_manager


# Import at module level to make it patchable for tests
from .history_hooks import register_history_hooks 