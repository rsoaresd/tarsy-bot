"""
Dashboard update service for formatting and managing real-time updates.

Provides centralized management of dashboard updates with intelligent batching,
session status tracking, and subscription-based filtering for optimal
performance and user experience.
"""

import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, asdict

from tarsy.utils.logger import get_module_logger
from tarsy.models.websocket_models import (
    ChannelType,
    DashboardUpdate,
    SessionUpdate,
    SystemHealthUpdate,
    AlertStatusUpdate
)
from tarsy.services.dashboard_broadcaster import DashboardBroadcaster

logger = get_module_logger(__name__)


@dataclass
class SessionSummary:
    """Summary information for active sessions."""
    session_id: str
    status: str  # "active", "completed", "error", "timeout"
    agent_type: Optional[str] = None
    start_time: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    interactions_count: int = 0
    llm_interactions: int = 0
    mcp_communications: int = 0
    errors_count: int = 0
    current_step: Optional[str] = None
    progress_percentage: int = 0


@dataclass
class DashboardMetrics:
    """Current dashboard metrics."""
    active_sessions: int = 0
    completed_sessions: int = 0
    failed_sessions: int = 0
    total_interactions: int = 0
    avg_session_duration: float = 0.0
    error_rate: float = 0.0
    last_updated: datetime = None


class DashboardUpdateService:
    """
    Service for formatting and managing dashboard updates.
    
    Provides intelligent batching, session tracking, and filtering
    for optimal dashboard performance and user experience.
    """
    
    def __init__(self, broadcaster: DashboardBroadcaster):
        """
        Initialize dashboard update service.
        
        Args:
            broadcaster: Dashboard broadcaster for message distribution
        """
        self.broadcaster = broadcaster
        
        # Session tracking
        self.active_sessions: Dict[str, SessionSummary] = {}
        self.session_history: deque = deque(maxlen=1000)  # Keep last 1000 sessions
        
        # Metrics tracking
        self.metrics = DashboardMetrics(last_updated=datetime.now())
        self.metrics_update_interval = 30  # Update metrics every 30 seconds
        
        # Update batching and filtering
        self.pending_session_updates: Dict[str, List[Dict]] = defaultdict(list)
        self.batch_timeout = 2.0  # Batch updates for 2 seconds
        self.max_updates_per_session = 10  # Max updates per session per batch
        
        # Background tasks
        self.metrics_task: Optional[asyncio.Task] = None
        self.batch_processor_task: Optional[asyncio.Task] = None
        self.running = False
    
    async def start(self):
        """Start background tasks for metrics and batching."""
        if not self.running:
            self.running = True
            self.metrics_task = asyncio.create_task(self._metrics_updater())
            self.batch_processor_task = asyncio.create_task(self._batch_processor())
            logger.info("DashboardUpdateService started")
    
    async def stop(self):
        """Stop background tasks."""
        self.running = False
        
        if self.metrics_task:
            self.metrics_task.cancel()
            try:
                await self.metrics_task
            except asyncio.CancelledError:
                pass
        
        if self.batch_processor_task:
            self.batch_processor_task.cancel()
            try:
                await self.batch_processor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("DashboardUpdateService stopped")
    
    async def process_llm_interaction(
        self, 
        session_id: str, 
        interaction_data: Dict[str, Any],
        broadcast_immediately: bool = False
    ) -> int:
        """
        Process LLM interaction update for dashboard.
        
        Args:
            session_id: Session identifier
            interaction_data: LLM interaction data from hooks
            broadcast_immediately: Whether to bypass batching
            
        Returns:
            Number of clients the update was sent to
        """
        # Update session tracking
        self._update_session_from_llm(session_id, interaction_data)
        
        # Format update for dashboard
        formatted_update = self._format_llm_update(session_id, interaction_data)
        
        if broadcast_immediately:
            # Send immediately
            return await self._broadcast_update(formatted_update)
        else:
            # Add to batch
            self._add_to_batch(session_id, formatted_update)
            return 0
    
    async def process_mcp_communication(
        self, 
        session_id: str, 
        communication_data: Dict[str, Any],
        broadcast_immediately: bool = False
    ) -> int:
        """
        Process MCP communication update for dashboard.
        
        Args:
            session_id: Session identifier
            communication_data: MCP communication data from hooks
            broadcast_immediately: Whether to bypass batching
            
        Returns:
            Number of clients the update was sent to
        """
        # Update session tracking
        self._update_session_from_mcp(session_id, communication_data)
        
        # Format update for dashboard
        formatted_update = self._format_mcp_update(session_id, communication_data)
        
        if broadcast_immediately:
            # Send immediately
            return await self._broadcast_update(formatted_update)
        else:
            # Add to batch
            self._add_to_batch(session_id, formatted_update)
            return 0
    
    async def process_session_status_change(
        self, 
        session_id: str, 
        status: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Process session status change (started, completed, error, etc.).
        
        Args:
            session_id: Session identifier
            status: New session status
            details: Additional status details
            
        Returns:
            Number of clients the update was sent to
        """
        # Update session summary
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = SessionSummary(
                session_id=session_id,
                status=status,
                start_time=datetime.now(),
                last_activity=datetime.now()
            )
        else:
            self.active_sessions[session_id].status = status
            self.active_sessions[session_id].last_activity = datetime.now()
        
        # Add details if provided
        if details:
            session = self.active_sessions[session_id]
            if 'agent_type' in details:
                session.agent_type = details['agent_type']
            if 'current_step' in details:
                session.current_step = details['current_step']
            if 'progress_percentage' in details:
                session.progress_percentage = details['progress_percentage']
        
        # Create status update
        status_update = {
            "type": "session_status_change",
            "session_id": session_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add details if provided
        if details:
            status_update.update(details)
        
        # Broadcast immediately for status changes
        sent_count = await self._broadcast_update(status_update)
        
        # Move to history if session is completed
        if status in ["completed", "error", "timeout"]:
            self._archive_session(session_id)
        
        return sent_count
    
    async def broadcast_system_metrics(self) -> int:
        """
        Broadcast current system metrics to dashboard.
        
        Returns:
            Number of clients the update was sent to
        """
        metrics_data = {
            "type": "system_metrics",
            "metrics": asdict(self.metrics),
            "active_sessions_list": [
                {
                    "session_id": s.session_id,
                    "status": s.status,
                    "agent_type": s.agent_type,
                    "current_step": s.current_step,
                    "progress": s.progress_percentage,
                    "interactions": s.interactions_count,
                    "errors": s.errors_count
                }
                for s in self.active_sessions.values()
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        return await self.broadcaster.broadcast_dashboard_update(metrics_data)
    
    def get_session_summary(self, session_id: str) -> Optional[SessionSummary]:
        """Get summary for a specific session."""
        return self.active_sessions.get(session_id)
    
    def get_all_active_sessions(self) -> List[SessionSummary]:
        """Get all active session summaries."""
        return list(self.active_sessions.values())
    
    def get_dashboard_metrics(self) -> DashboardMetrics:
        """Get current dashboard metrics."""
        return self.metrics
    
    # Private methods
    
    def _update_session_from_llm(self, session_id: str, interaction_data: Dict[str, Any]):
        """Update session summary from LLM interaction."""
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = SessionSummary(
                session_id=session_id,
                status="active",
                start_time=datetime.now(),
                last_activity=datetime.now()
            )
        
        session = self.active_sessions[session_id]
        session.last_activity = datetime.now()
        session.interactions_count += 1
        session.llm_interactions += 1
        
        if not interaction_data.get('success', True):
            session.errors_count += 1
        
        # Update current step based on if the interaction was successful or not
        if interaction_data.get('success', True):
            session.current_step = "LLM processing completed"
        else:
            session.current_step = "LLM processing failed"
        
        # Update current step if provided directly
        if 'step_description' in interaction_data:
            session.current_step = interaction_data['step_description']
    
    def _update_session_from_mcp(self, session_id: str, communication_data: Dict[str, Any]):
        """Update session summary from MCP communication."""
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = SessionSummary(
                session_id=session_id,
                status="active",
                start_time=datetime.now(),
                last_activity=datetime.now()
            )
        
        session = self.active_sessions[session_id]
        session.last_activity = datetime.now()
        session.interactions_count += 1
        session.mcp_communications += 1
        
        if not communication_data.get('success', True):
            session.errors_count += 1
        
        # Update current step based on tool name
        tool_name = communication_data.get('tool_name')
        if tool_name:
            session.current_step = f"Executing tool: {tool_name}"
        
        # Update current step if provided directly
        if 'step_description' in communication_data:
            session.current_step = communication_data['step_description']
    
    def _format_llm_update(self, session_id: str, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format LLM interaction data for dashboard."""
        return {
            "type": "llm_interaction",
            "session_id": session_id,
            "step_description": interaction_data.get('step_description', 'LLM interaction'),
            "model_used": interaction_data.get('model_used', 'unknown'),
            "success": interaction_data.get('success', True),
            "duration_ms": interaction_data.get('duration_ms', 0),
            "has_tools": interaction_data.get('tool_calls_present', False),
            "timestamp": interaction_data.get('timestamp', datetime.now().isoformat()),
            "error_message": interaction_data.get('error_message')
        }
    
    def _format_mcp_update(self, session_id: str, communication_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format MCP communication data for dashboard."""
        return {
            "type": "mcp_communication",
            "session_id": session_id,
            "step_description": communication_data.get('step_description', 'MCP communication'),
            "server_name": communication_data.get('server_name', 'unknown'),
            "tool_name": communication_data.get('tool_name'),
            "success": communication_data.get('success', True),
            "duration_ms": communication_data.get('duration_ms', 0),
            "timestamp": communication_data.get('timestamp', datetime.now().isoformat()),
            "error_message": communication_data.get('error_message')
        }
    
    def _add_to_batch(self, session_id: str, update: Dict[str, Any]):
        """Add update to batching queue."""
        if len(self.pending_session_updates[session_id]) < self.max_updates_per_session:
            self.pending_session_updates[session_id].append(update)
    
    async def _broadcast_update(self, update: Dict[str, Any]) -> int:
        """Broadcast single update via broadcaster."""
        try:
            return await self.broadcaster.broadcast_dashboard_update(update)
        except Exception as e:
            logger.error(f"Failed to broadcast dashboard update: {str(e)}")
            return 0
    
    def _archive_session(self, session_id: str):
        """Move completed session to history."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            self.session_history.append(session)
            del self.active_sessions[session_id]
            logger.debug(f"Archived completed session: {session_id}")
    
    async def _metrics_updater(self):
        """Background task to update dashboard metrics."""
        while self.running:
            try:
                # Calculate metrics
                active_count = len(self.active_sessions)
                completed_count = len([s for s in self.session_history if s.status == "completed"])
                failed_count = len([s for s in self.session_history if s.status in ["error", "timeout"]])
                
                total_interactions = sum(s.interactions_count for s in self.active_sessions.values())
                total_interactions += sum(s.interactions_count for s in self.session_history)
                
                # Calculate average session duration
                completed_sessions = [s for s in self.session_history if s.status == "completed" and s.start_time]
                if completed_sessions:
                    durations = [
                        (s.last_activity - s.start_time).total_seconds()
                        for s in completed_sessions
                        if s.last_activity and s.start_time
                    ]
                    avg_duration = sum(durations) / len(durations) if durations else 0.0
                else:
                    avg_duration = 0.0
                
                # Calculate error rate
                total_sessions = active_count + completed_count + failed_count
                error_rate = (failed_count / total_sessions * 100) if total_sessions > 0 else 0.0
                
                # Update metrics
                self.metrics = DashboardMetrics(
                    active_sessions=active_count,
                    completed_sessions=completed_count,
                    failed_sessions=failed_count,
                    total_interactions=total_interactions,
                    avg_session_duration=avg_duration,
                    error_rate=error_rate,
                    last_updated=datetime.now()
                )
                
                # Broadcast metrics update
                await self.broadcast_system_metrics()
                
                # Wait for next update
                await asyncio.sleep(self.metrics_update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics updater: {str(e)}")
                await asyncio.sleep(5)  # Wait before retry
    
    async def _batch_processor(self):
        """Background task to process batched updates."""
        while self.running:
            try:
                # Process pending batches
                if self.pending_session_updates:
                    sessions_to_process = list(self.pending_session_updates.keys())
                    
                    for session_id in sessions_to_process:
                        updates = self.pending_session_updates[session_id]
                        if updates:
                            # Create batched update
                            batched_update = {
                                "type": "batched_session_updates",
                                "session_id": session_id,
                                "updates": updates,
                                "count": len(updates),
                                "timestamp": datetime.now().isoformat()
                            }
                            
                            # Broadcast batch
                            await self._broadcast_update(batched_update)
                            
                            # Clear processed updates
                            del self.pending_session_updates[session_id]
                
                # Wait before next batch processing
                await asyncio.sleep(self.batch_timeout)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch processor: {str(e)}")
                await asyncio.sleep(1)  # Wait before retry 