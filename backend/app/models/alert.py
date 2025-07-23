"""
Alert data models for the SRE AI Agent.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Alert(BaseModel):
    """Alert model representing an incoming alert."""
    
    alert_type: str = Field(..., description="Alert type")
    severity: str = Field(..., description="Alert severity level")
    environment: str = Field(..., description="Environment (production/staging)")
    cluster: str = Field(..., description="Cluster URL")
    namespace: str = Field(..., description="Affected namespace")
    pod: Optional[str] = Field(None, description="Affected pod")
    message: str = Field(..., description="Alert message")
    runbook: str = Field(..., description="Runbook URL")
    context: Optional[str] = Field(None, description="Additional context or details about the alert")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


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