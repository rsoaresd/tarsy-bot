"""
Alert Service for multi-layer agent architecture.

This module provides the service that delegates alert processing to
specialized agents based on alert type. It implements the multi-layer
agent architecture for alert processing.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Callable, Optional

from tarsy.config.settings import Settings
from tarsy.integrations.llm.client import LLMManager
from tarsy.integrations.mcp.client import MCPClient
from tarsy.models.alert import Alert
from tarsy.models.constants import AlertSessionStatus
from tarsy.services.agent_factory import AgentFactory
from tarsy.services.agent_registry import AgentRegistry
from tarsy.services.history_service import get_history_service
from tarsy.services.mcp_server_registry import MCPServerRegistry
from tarsy.services.runbook_service import RunbookService
from tarsy.utils.logger import get_module_logger

logger = get_module_logger(__name__)


class AlertService:
    """
    Service for alert processing with agent delegation.
    
    This class implements a multi-layer architecture that delegates 
    processing to specialized agents based on alert type.
    """
    
    # Class-level dictionary to track processing locks for alerts
    _processing_locks = {}
    _locks_lock = asyncio.Lock()
    
    def __init__(self, settings: Settings):
        """
        Initialize the alert service with required services.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        
        # Initialize services
        self.runbook_service = RunbookService(settings)
        self.history_service = get_history_service()
        
        # Initialize registries first
        self.agent_registry = AgentRegistry()
        self.mcp_server_registry = MCPServerRegistry()
        
        # Initialize services that depend on registries
        self.mcp_client = MCPClient(settings, self.mcp_server_registry)
        self.llm_manager = LLMManager(settings)
        
        # Initialize agent factory with dependencies
        self.agent_factory = None  # Will be initialized in initialize()
        
        logger.info("AlertService initialized with agent delegation support")

    async def _get_alert_lock(self, alert_key: str) -> asyncio.Lock:
        """Get or create a lock for a specific alert to prevent concurrent processing."""
        async with self._locks_lock:
            if alert_key not in self._processing_locks:
                self._processing_locks[alert_key] = asyncio.Lock()
            return self._processing_locks[alert_key]
    
    async def _cleanup_alert_lock(self, alert_key: str):
        """Clean up the lock for an alert after processing is complete."""
        async with self._locks_lock:
            # Only remove if no one is waiting on the lock
            if alert_key in self._processing_locks:
                lock = self._processing_locks[alert_key]
                if not lock.locked():
                    del self._processing_locks[alert_key]
    
    def _generate_alert_key(self, alert: Alert) -> str:
        """Generate a unique key for an alert to use for concurrency control."""
        return f"{alert.alert_type}_{alert.environment}_{alert.namespace}_{alert.message[:50]}"

    async def initialize(self):
        """
        Initialize the service and all dependencies.
        """
        try:
            # Initialize MCP client
            await self.mcp_client.initialize()
            
            # Validate LLM availability
            if not self.llm_manager.is_available():
                available_providers = self.llm_manager.list_available_providers()
                status = self.llm_manager.get_availability_status()
                raise Exception(
                    f"No LLM providers are available. "
                    f"Configured providers: {available_providers}, Status: {status}"
                )
            
            # Initialize agent factory with dependencies
            self.agent_factory = AgentFactory(
                llm_client=self.llm_manager,
                mcp_client=self.mcp_client,
                progress_callback=None,  # Will be set per-request
                mcp_registry=self.mcp_server_registry
            )
            
            logger.info("AlertService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AlertService: {str(e)}")
            raise

    
    async def process_alert(
        self, 
        alert: Alert, 
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        Process an alert by delegating to the appropriate specialized agent.
        
        Args:
            alert: The alert to process
            progress_callback: Optional callback for progress updates
            
        Returns:
            Analysis result as a string
        """
        # Generate alert key for concurrency control
        alert_key = self._generate_alert_key(alert)
        
        # Get alert-specific lock to prevent concurrent processing
        alert_lock = await self._get_alert_lock(alert_key)
        
        async with alert_lock:
            try:
                return await self._process_alert_internal(alert, progress_callback)
            finally:
                # Clean up the lock after processing
                await self._cleanup_alert_lock(alert_key)
    
    async def _process_alert_internal(
        self, 
        alert: Alert, 
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        Internal alert processing logic with all the actual processing steps.
        
        Args:
            alert: The alert to process
            progress_callback: Optional callback for progress updates
            
        Returns:
            Analysis result as a string
        """
        session_id = None
        try:
            # Will create history session after determining agent type
            
            # Step 1: Validate prerequisites
            if not self.llm_manager.is_available():
                raise Exception("Cannot process alert: No LLM providers are available")
                
            if not self.agent_factory:
                raise Exception("Agent factory not initialized - call initialize() first")
            
            # Step 2: Determine appropriate agent
            if progress_callback:
                await progress_callback(5, "Selecting specialized agent")
            
            agent_class_name = self.agent_registry.get_agent_for_alert_type(alert.alert_type)
            
            if not agent_class_name:
                error_msg = (
                    f"No specialized agent available for alert type: '{alert.alert_type}'. "
                    f"Supported alert types: {self.agent_registry.get_supported_alert_types()}"
                )
                logger.error(error_msg)
                
                # Update history session with error
                self._update_session_error(session_id, error_msg)
                
                if progress_callback:
                    await progress_callback(100, f"Error: {error_msg}")
                    
                return self._format_error_response(alert, error_msg)
            
            logger.info(f"Selected agent {agent_class_name} for alert type: {alert.alert_type}")
            
            # Create history session now that we have the agent type
            session_id = self._create_history_session(alert, agent_class_name)
            
            # Update history session with agent selection
            self._update_session_status(session_id, AlertSessionStatus.IN_PROGRESS, f"Selected agent: {agent_class_name}")
            
            # Step 3: Download runbook
            if progress_callback:
                await progress_callback(10, "Downloading runbook")
            
            runbook_content = await self.runbook_service.download_runbook(alert.runbook)
            
            # Step 4: Create agent instance
            if progress_callback:
                await progress_callback(15, f"Initializing {agent_class_name}")
            
            try:
                # Update factory's progress callback for this request
                self.agent_factory.progress_callback = progress_callback
                
                agent = self.agent_factory.create_agent(agent_class_name)
                logger.info(f"Created {agent_class_name} instance")
                
            except ValueError as e:
                error_msg = f"Failed to create agent: {str(e)}"
                logger.error(error_msg)
                
                # Update history session with agent creation error
                self._update_session_error(session_id, error_msg)
                
                if progress_callback:
                    await progress_callback(100, f"Error: {error_msg}")
                    
                return self._format_error_response(alert, error_msg)
            
            # Step 5: Delegate processing to agent
            if progress_callback:
                await progress_callback(20, f"Delegating to {agent_class_name}")
            
            # Create progress wrapper that includes agent context
            agent_progress_callback = None
            if progress_callback:
                agent_progress_callback = lambda status: progress_callback(
                    status.get('progress', 50),
                    f"[{agent_class_name}] {status.get('message', 'Processing...')}"
                )
            
            # Process alert with agent (pass session_id for history tracking)
            agent_result = await agent.process_alert(
                alert=alert,
                runbook_content=runbook_content,
                callback=agent_progress_callback,
                session_id=session_id
            )
            
            # Step 6: Format and return results
            if agent_result.get('status') == 'success':
                analysis = agent_result.get('analysis', 'No analysis provided')
                iterations = agent_result.get('iterations', 0)
                
                # Format final result with agent context
                final_result = self._format_success_response(
                    alert=alert,
                    agent_name=agent_class_name,
                    analysis=analysis,
                    iterations=iterations,
                    timestamp=agent_result.get('timestamp')
                )
                
                # Mark history session as completed successfully
                self._update_session_completed(session_id, AlertSessionStatus.COMPLETED, final_analysis=final_result)
                
                if progress_callback:
                    await progress_callback(100, "Analysis completed successfully")
                
                return final_result
                
            else:
                # Handle agent processing error
                error_msg = agent_result.get('error', 'Unknown agent error')
                logger.error(f"Agent {agent_class_name} failed: {error_msg}")
                
                # Update history session with agent error
                self._update_session_error(session_id, error_msg)
                
                if progress_callback:
                    await progress_callback(100, f"Agent error: {error_msg}")
                
                return self._format_error_response(
                    alert=alert,
                    error=error_msg,
                    agent_name=agent_class_name
                )
                
        except Exception as e:
            error_msg = f"Alert processing failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Update history session with general processing error
            self._update_session_error(session_id, error_msg)
            
            if progress_callback:
                await progress_callback(100, f"Error: {error_msg}")
            
            return self._format_error_response(alert, error_msg)
    
    def _format_success_response(
        self,
        alert: Alert,
        agent_name: str,
        analysis: str,
        iterations: int,
        timestamp: Optional[str] = None
    ) -> str:
        """
        Format successful analysis response.
        
        Args:
            alert: The processed alert
            agent_name: Name of the agent that processed the alert
            analysis: Analysis result from the agent
            iterations: Number of iterations performed
            timestamp: Processing timestamp
            
        Returns:
            Formatted response string
        """
        response_parts = [
            "# Alert Analysis Report",
            "",
            f"**Alert Type:** {alert.alert_type}",
            f"**Processing Agent:** {agent_name}",
            f"**Environment:** {alert.environment}",
            f"**Severity:** {alert.severity}",
            f"**Timestamp:** {timestamp or datetime.now(timezone.utc).isoformat()}",
            "",
            "## Analysis",
            "",
            analysis,
            "",
            "---",
            f"*Processed by {agent_name} in {iterations} iterations*"
        ]
        
        return "\n".join(response_parts)
    
    def _format_error_response(
        self,
        alert: Alert,
        error: str,
        agent_name: Optional[str] = None
    ) -> str:
        """
        Format error response.
        
        Args:
            alert: The alert that failed processing
            error: Error message
            agent_name: Name of the agent if known
            
        Returns:
            Formatted error response string
        """
        response_parts = [
            "# Alert Processing Error",
            "",
            f"**Alert Type:** {alert.alert_type}",
            f"**Environment:** {alert.environment}",
            f"**Error:** {error}",
        ]
        
        if agent_name:
            response_parts.append(f"**Failed Agent:** {agent_name}")
        
        response_parts.extend([
            "",
            "## Troubleshooting",
            "",
            "1. Check that the alert type is supported",
            "2. Verify agent configuration in settings",
            "3. Ensure all required services are available",
            "4. Review logs for detailed error information"
        ])
        
        return "\n".join(response_parts)
    
    # History Session Management Methods
    def _create_history_session(self, alert: Alert, agent_class_name: Optional[str] = None) -> Optional[str]:
        """
        Create a history session for alert processing.
        
        Args:
            alert: The alert being processed
            agent_class_name: Optional agent class name (if already determined)
            
        Returns:
            Session ID if created successfully, None if history service unavailable
        """
        try:
            if not self.history_service or not self.history_service.enabled:
                return None
            
            # Use provided agent class name or determine it
            if agent_class_name is None:
                agent_class_name = self.agent_registry.get_agent_for_alert_type(alert.alert_type)
            agent_type = agent_class_name or 'unknown'
            
            # Generate alert ID from alert data if not present
            if hasattr(alert, 'id') and alert.id:
                alert_id = alert.id
            else:
                # Use nanosecond timestamp and random component to prevent collisions
                timestamp_ns = int(datetime.now(timezone.utc).timestamp() * 1000000)  # microseconds
                random_suffix = uuid.uuid4().hex[:8]  # 8 chars of randomness
                alert_id = f"{alert.alert_type}_{alert.environment}_{alert.namespace}_{timestamp_ns}_{random_suffix}"
            
            session_id = self.history_service.create_session(
                alert_id=alert_id,
                alert_data={
                    'alert_type': alert.alert_type,
                    'environment': alert.environment,
                    'cluster': alert.cluster,
                    'namespace': alert.namespace,
                    'runbook': alert.runbook,
                    'message': alert.message,
                    'severity': alert.severity,
                    'pod': getattr(alert, 'pod', None),
                    'context': getattr(alert, 'context', None),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                 },
                agent_type=agent_type,
                alert_type=alert.alert_type
            )
            
            logger.info(f"Created history session {session_id} for alert {alert_id}")
            return session_id
            
        except Exception as e:
            logger.warning(f"Failed to create history session: {str(e)}")
            return None
    
    def _update_session_status(self, session_id: Optional[str], status: str, message: Optional[str] = None):
        """
        Update history session status.
        
        Args:
            session_id: Session ID to update
            status: New status
            message: Optional status message (not used by current history service API)
        """
        try:
            if not session_id or not self.history_service or not self.history_service.enabled:
                return
                
            self.history_service.update_session_status(
                session_id=session_id,
                status=status
            )
            
        except Exception as e:
            logger.warning(f"Failed to update session status: {str(e)}")
    
    def _update_session_completed(self, session_id: Optional[str], status: str, final_analysis: Optional[str] = None):
        """
        Mark history session as completed.
        
        Args:
            session_id: Session ID to complete
            status: Final status (e.g., 'completed', 'error')
            final_analysis: Final formatted analysis if status is completed successfully
        """
        try:
            if not session_id or not self.history_service or not self.history_service.enabled:
                return
                
            # The history service automatically sets completed_at when status is 'completed' or 'failed'
            self.history_service.update_session_status(
                session_id=session_id,
                status=status,
                final_analysis=final_analysis
            )
            
        except Exception as e:
            logger.warning(f"Failed to mark session completed: {str(e)}")
    
    def _update_session_error(self, session_id: Optional[str], error_message: str):
        """
        Mark history session as failed with error.
        
        Args:
            session_id: Session ID to update
            error_message: Error message
        """
        try:
            if not session_id or not self.history_service or not self.history_service.enabled:
                return
                
            # Status 'failed' will automatically set completed_at in the history service
            self.history_service.update_session_status(
                session_id=session_id,
                status='failed',
                error_message=error_message
            )
            
        except Exception as e:
            logger.warning(f"Failed to update session error: {str(e)}")
    
    async def close(self):
        """
        Clean up resources.
        """
        try:
            await self.runbook_service.close()
            await self.mcp_client.close()
            logger.info("AlertService resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
