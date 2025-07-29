"""
Alert Service for multi-layer agent architecture.

This module provides the service that delegates alert processing to
specialized agents based on alert type. It implements the multi-layer
agent architecture for alert processing.
Uses Unix timestamps (microseconds since epoch) throughout for optimal
performance and consistency with the rest of the system.
"""

import asyncio
import hashlib
import json
import logging
import uuid
from typing import Callable, Optional, Dict, Any

from tarsy.config.settings import Settings
from tarsy.integrations.llm.client import LLMManager
from tarsy.integrations.mcp.client import MCPClient
from tarsy.models.constants import AlertSessionStatus
from tarsy.models.history import now_us
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
    
    def _generate_data_hash(self, data: Dict[str, Any], length: int = 12) -> str:
        """Generate a deterministic hash from alert data."""
        data_json = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(data_json.encode('utf-8')).hexdigest()[:length]

    def _generate_alert_key(self, alert_data: Dict[str, Any]) -> str:
        """Generate a deterministic key for alert concurrency control."""
        # Use content hash for consistent concurrency control of identical alerts
        data = alert_data.get('data', {})
        alert_type = alert_data.get('alert_type', 'unknown')
        
        # Combine alert type with content hash for better key distribution
        content_hash = self._generate_data_hash(data, length=12)
        return f"{alert_type}_{content_hash}"

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
        alert_data: Dict[str, Any], 
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        Process an alert by delegating to the appropriate specialized agent.
        
        Args:
            alert_data: Flexible alert data dictionary with alert_type and alert_data fields
            progress_callback: Optional callback for progress updates
            
        Returns:
            Analysis result as a string
        """
        # Generate alert key for concurrency control
        alert_key = self._generate_alert_key(alert_data)
        
        # Get alert-specific lock to prevent concurrent processing
        alert_lock = await self._get_alert_lock(alert_key)
        
        async with alert_lock:
            try:
                return await self._process_alert_internal(alert_data, progress_callback)
            finally:
                # Clean up the lock after processing
                await self._cleanup_alert_lock(alert_key)
    
    async def _process_alert_internal(
        self, 
        alert_data: Dict[str, Any], 
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        Internal alert processing logic with all the actual processing steps.
        
        Args:
            alert_data: Flexible alert data dictionary
            progress_callback: Optional callback for progress updates
            
        Returns:
            Analysis result as a string
        """
        session_id = None
        try:
            # Step 1: Validate prerequisites
            if not self.llm_manager.is_available():
                raise Exception("Cannot process alert: No LLM providers are available")
                
            if not self.agent_factory:
                raise Exception("Agent factory not initialized - call initialize() first")
            
            # Step 2: Determine appropriate agent
            if progress_callback:
                await progress_callback(5, "Selecting specialized agent")
            
            alert_type = alert_data.get("alert_type")
            agent_class_name = self.agent_registry.get_agent_for_alert_type(alert_type)
            
            if not agent_class_name:
                error_msg = (
                    f"No specialized agent available for alert type: '{alert_type}'. "
                    f"Supported alert types: {self.agent_registry.get_supported_alert_types()}"
                )
                logger.error(error_msg)
                
                # Update history session with error
                self._update_session_error(session_id, error_msg)
                
                if progress_callback:
                    await progress_callback(100, f"Error: {error_msg}")
                    
                return self._format_error_response(alert_data, error_msg)
            
            logger.info(f"Selected agent {agent_class_name} for alert type: {alert_type}")
            
            # Create history session with flexible data
            session_id = self._create_history_session(alert_data, agent_class_name)
            
            # Update history session with agent selection
            self._update_session_status(session_id, AlertSessionStatus.IN_PROGRESS, f"Selected agent: {agent_class_name}")
            
            # Step 3: Extract runbook from alert data
            if progress_callback:
                await progress_callback(10, "Extracting runbook")
            
            runbook = alert_data.get("alert_data", {}).get("runbook")
            if not runbook:
                error_msg = "No runbook specified in alert data"
                logger.error(error_msg)
                self._update_session_error(session_id, error_msg)
                if progress_callback:
                    await progress_callback(100, f"Error: {error_msg}")
                return self._format_error_response(alert_data, error_msg)
            
            runbook_content = await self.runbook_service.download_runbook(runbook)
            
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
                    
                return self._format_error_response(alert_data, error_msg)
            
            # Step 5: Delegate processing to agent with flexible data
            if progress_callback:
                await progress_callback(20, f"Delegating to {agent_class_name}")
            
            # Create progress wrapper that includes agent context
            agent_progress_callback = None
            if progress_callback:
                agent_progress_callback = lambda status: progress_callback(
                    status.get('progress', 50),
                    f"[{agent_class_name}] {status.get('message', 'Processing...')}"
                )
            
            # Process alert with agent - pass alert_data directly with flexible structure
            agent_result = await agent.process_alert(
                alert_data=alert_data.get("alert_data", {}),
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
                    alert_data,
                    agent_class_name,
                    analysis,
                    iterations,
                    agent_result.get('timestamp_us')
                )
                
                # Mark history session as completed successfully
                self._update_session_completed(session_id, AlertSessionStatus.COMPLETED, final_analysis=final_result)
                
                if progress_callback:
                    await progress_callback(100, "Analysis completed successfully")
                
                return final_result
            else:
                # Handle agent processing error
                error_msg = agent_result.get('error', 'Agent processing failed')
                logger.error(f"Agent processing failed: {error_msg}")
                
                # Update history session with processing error
                self._update_session_error(session_id, error_msg)
                
                if progress_callback:
                    await progress_callback(100, f"Error: {error_msg}")
                
                return self._format_error_response(alert_data, error_msg)
                
        except Exception as e:
            error_msg = f"Alert processing failed: {str(e)}"
            logger.error(error_msg)
            
            # Update history session with processing error
            self._update_session_error(session_id, error_msg)
            
            if progress_callback:
                await progress_callback(100, f"Error: {error_msg}")
            
            return self._format_error_response(alert_data, error_msg)

    def _format_success_response(
        self,
        alert_data: Dict[str, Any],
        agent_name: str,
        analysis: str,
        iterations: int,
        timestamp_us: Optional[int] = None
    ) -> str:
        """
        Format successful analysis response for flexible alert data.
        
        Args:
            alert_data: The flexible alert data dictionary
            agent_name: Name of the agent that processed the alert
            analysis: Analysis result from the agent
            iterations: Number of iterations performed
            timestamp_us: Processing timestamp in microseconds since epoch UTC
            
        Returns:
            Formatted response string
        """
        # Convert unix timestamp to string for display
        if timestamp_us:
            timestamp_str = f"{timestamp_us}"  # Keep as unix timestamp for consistency
        else:
            timestamp_str = f"{now_us()}"  # Current unix timestamp
        
        data = alert_data.get("alert_data", {})
        response_parts = [
            "# Alert Analysis Report",
            "",
            f"**Alert Type:** {alert_data.get('alert_type', 'unknown')}",
            f"**Processing Agent:** {agent_name}",
            f"**Environment:** {data.get('environment', 'unknown')}",
            f"**Severity:** {data.get('severity', 'unknown')}",
            f"**Timestamp:** {timestamp_str}",
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
        alert_data: Dict[str, Any],
        error: str,
        agent_name: Optional[str] = None
    ) -> str:
        """
        Format error response for flexible alert data.
        
        Args:
            alert_data: The flexible alert data dictionary
            error: Error message
            agent_name: Name of the agent if known
            
        Returns:
            Formatted error response string
        """
        data = alert_data.get("alert_data", {})
        response_parts = [
            "# Alert Processing Error",
            "",
            f"**Alert Type:** {alert_data.get('alert_type', 'unknown')}",
            f"**Environment:** {data.get('environment', 'unknown')}",
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
    def _create_history_session(self, alert_data: Dict[str, Any], agent_class_name: Optional[str] = None) -> Optional[str]:
        """
        Create a history session for flexible alert processing.
        
        Args:
            alert_data: Flexible alert data dictionary
            agent_class_name: Agent class name for the session
            
        Returns:
            Session ID if created successfully, None if history service unavailable
        """
        try:
            if not self.history_service or not self.history_service.enabled:
                return None
            
            # Extract data from dictionary format
            alert_type = alert_data.get('alert_type')
            data = alert_data.get("alert_data", {})
            
            # Use provided agent class name or determine it
            if agent_class_name is None:
                agent_class_name = self.agent_registry.get_agent_for_alert_type(alert_type)
            agent_type = agent_class_name or 'unknown'
            
            # Generate unique alert ID for this processing session
            timestamp_us = now_us()
            random_suffix = uuid.uuid4().hex[:8]
            
            # Use content hash as base but make it unique per session
            content_hash = self._generate_data_hash(data, length=8)
            alert_id = f"{alert_type or 'unknown'}_{content_hash}_{timestamp_us}_{random_suffix}"
            
            # Store alert_type separately and all flexible data in alert_data JSON field 
            session_id = self.history_service.create_session(
                alert_id=alert_id,
                alert_data=data,  # Store all flexible data in JSON field
                agent_type=agent_type,
                alert_type=alert_type  # Store in separate column for fast routing
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
                
            # The history service automatically sets completed_at_us when status is 'completed' or 'failed'
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
                
            # Status 'failed' will automatically set completed_at_us in the history service
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
