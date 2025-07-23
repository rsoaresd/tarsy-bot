"""
API Models for Request/Response Serialization

Defines Pydantic models for API request/response structures.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Request Models
class SessionFilters(BaseModel):
    """Query filters for session list endpoint."""
    status: Optional[str] = Field(None, description="Filter by session status (e.g., 'in_progress', 'completed', 'error')")
    agent_type: Optional[str] = Field(None, description="Filter by agent type (e.g., 'kubernetes')")
    alert_type: Optional[str] = Field(None, description="Filter by alert type (e.g., 'NamespaceTerminating')")
    start_date: Optional[datetime] = Field(None, description="Filter sessions started after this date (ISO format)")
    end_date: Optional[datetime] = Field(None, description="Filter sessions started before this date (ISO format)")
    page: int = Field(1, ge=1, description="Page number for pagination")
    page_size: int = Field(20, ge=1, le=100, description="Number of items per page (1-100)")

# Response Models
class PaginationInfo(BaseModel):
    """Pagination information for paginated responses."""
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")
    total_items: int = Field(description="Total number of items")

class SessionSummary(BaseModel):
    """Summary information for a session in list responses."""
    session_id: str = Field(description="Unique session identifier")
    alert_id: str = Field(description="Alert identifier that triggered this session")
    agent_type: str = Field(description="Type of agent that processed the alert")
    alert_type: Optional[str] = Field(description="Type/category of the alert")
    status: str = Field(description="Current status of the session")
    started_at: datetime = Field(description="When the session started")
    completed_at: Optional[datetime] = Field(description="When the session completed (if finished)")
    error_message: Optional[str] = Field(description="Error message if session failed")
    duration_ms: Optional[int] = Field(description="Session duration in milliseconds (if completed)")
    llm_interaction_count: int = Field(description="Number of LLM interactions in this session")
    mcp_communication_count: int = Field(description="Number of MCP communications in this session")

class SessionsListResponse(BaseModel):
    """Response for the sessions list endpoint."""
    sessions: List[SessionSummary] = Field(description="List of session summaries")
    pagination: PaginationInfo = Field(description="Pagination information")
    filters_applied: Dict[str, Any] = Field(description="Applied filters for this query")

class TimelineEvent(BaseModel):
    """Single event in a session timeline."""
    event_id: str = Field(description="Unique event identifier")
    type: str = Field(description="Event type ('llm_interaction' or 'mcp_communication')")
    timestamp: datetime = Field(description="When the event occurred")
    step_description: str = Field(description="Human-readable description of this step")
    details: Dict[str, Any] = Field(description="Event-specific details")
    duration_ms: Optional[int] = Field(description="Event duration in milliseconds (if available)")

class SessionDetailResponse(BaseModel):
    """Response for the individual session detail endpoint."""
    session_id: str = Field(description="Unique session identifier")
    alert_id: str = Field(description="Alert identifier that triggered this session")
    alert_data: Dict[str, Any] = Field(description="Original alert data")
    agent_type: str = Field(description="Type of agent that processed the alert")
    alert_type: Optional[str] = Field(description="Type/category of the alert")
    status: str = Field(description="Current status of the session")
    started_at: datetime = Field(description="When the session started")
    completed_at: Optional[datetime] = Field(description="When the session completed (if finished)")
    error_message: Optional[str] = Field(description="Error message if session failed")
    duration_ms: Optional[int] = Field(description="Total session duration in milliseconds (if completed)")
    session_metadata: Optional[Dict[str, Any]] = Field(description="Additional session metadata")
    
    # Timeline
    chronological_timeline: List[TimelineEvent] = Field(description="Chronologically ordered list of all events")
    summary: Dict[str, Any] = Field(description="Session summary statistics")

class HealthCheckResponse(BaseModel):
    """Response for health check endpoints."""
    service: str = Field(description="Service name")
    status: str = Field(description="Service status ('healthy', 'unhealthy', 'disabled')")
    timestamp: datetime = Field(description="Health check timestamp")
    details: Dict[str, Any] = Field(description="Additional health check details")

class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(description="Error type or category")
    message: str = Field(description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(description="Additional error details")
    timestamp: datetime = Field(description="When the error occurred") 