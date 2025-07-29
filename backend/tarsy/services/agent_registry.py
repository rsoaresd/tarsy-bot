"""
Agent Registry for mapping alert types to specialized agent classes.

This module provides a simple static registry that maps alert types to
their corresponding agent class names. The registry is loaded once at
startup with predefined mappings.
"""

from typing import Dict, Optional

from tarsy.utils.logger import get_module_logger

logger = get_module_logger(__name__)


class AgentRegistry:
    """
    Static registry for alert type to agent class mappings.
    
    This class maintains a simple dictionary mapping from alert types
    to agent class names. The registry is immutable after initialization
    to ensure consistency.
    """
    
    # Static mappings defined in the registry itself
    _DEFAULT_MAPPINGS = {
        "kubernetes": "KubernetesAgent",  # Generic kubernetes alerts  
        "NamespaceTerminating": "KubernetesAgent",
        # Future mappings will be added here:
        # "ArgoCD Sync Failed": "ArgoCDAgent", 
        # "EKS Node Group Issues": "KubernetesAWSAgent",
    }
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        """
        Initialize the agent registry with mappings.
        
        Args:
            config: Optional dictionary mapping alert types to agent class names.
                   If None, uses default mappings defined in the registry.
        """
        # Use provided config or fall back to default mappings
        self.static_mappings: Dict[str, str] = config or self._DEFAULT_MAPPINGS.copy()
            
        logger.info(f"Initialized Agent Registry with {len(self.static_mappings)} mappings")
    
    def get_agent_for_alert_type(self, alert_type: str) -> Optional[str]:
        """
        Get the agent class name for a given alert type.
        Simple dictionary lookup - no complex logic.
        
        Args:
            alert_type: The type of alert to find an agent for
            
        Returns:
            Agent class name if found, None otherwise
        """
        return self.static_mappings.get(alert_type)
    
    def get_supported_alert_types(self) -> list[str]:
        """
        Get all alert types that have registered agents.
        
        Returns:
            List of supported alert types
        """
        return list(self.static_mappings.keys()) 