"""
Alert data models for tarsy.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Alert(BaseModel):
    """Flexible alert model with minimal required fields and arbitrary data payload."""
    
    alert_type: str = Field(..., description="Alert type for agent selection")
    runbook: str = Field(..., description="Processing runbook URL or reference")
    data: Dict[str, Any] = Field(default_factory=dict, description="Flexible alert payload")
    
    # Optional fields with defaults (will be applied in API layer if not provided)
    severity: Optional[str] = Field(None, description="Alert severity (defaults to 'warning')")
    timestamp: Optional[int] = Field(None, description="Alert timestamp in unix microseconds (defaults to current time)")


class AlertResponse(BaseModel):
    """Response model for alert submission."""
    
    alert_id: str
    status: str
    message: str


class ProcessingStatus(BaseModel):
    """Processing status model for tracking alert processing."""
    
    alert_id: str
    status: str = Field(..., description="Processing status (queued/processing/completed/error)")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    current_step: str = Field(..., description="Current processing step")
    current_agent: Optional[str] = Field(None, description="Name of the agent currently processing")
    assigned_mcp_servers: Optional[List[str]] = Field(None, description="MCP servers assigned to current agent")
    result: Optional[str] = Field(None, description="Final processing result")
    error: Optional[str] = Field(None, description="Error message if processing failed")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 