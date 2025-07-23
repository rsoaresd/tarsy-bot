"""
History Controller

FastAPI controller for alert processing history endpoints.
Provides REST API for querying historical data with filtering, pagination,
and chronological timeline reconstruction.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from tarsy.models.api_models import (
    ErrorResponse,
    HealthCheckResponse,
    PaginationInfo,
    SessionDetailResponse,
    SessionsListResponse,
    SessionSummary,
    TimelineEvent,
)
from tarsy.services.history_service import HistoryService, get_history_service

router = APIRouter(prefix="/api/v1/history", tags=["history"])

@router.get(
    "/sessions", 
    response_model=SessionsListResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request - invalid parameters"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="List Alert Processing Sessions",
    description="""
    Retrieve a paginated list of alert processing sessions with optional filtering.
    
    **Filtering Support:**
    - Multiple filters use AND logic (all conditions must be met)
    - Combine filters for precise queries (e.g., alert_type + status + time_range)
    
    **Common Use Cases:**
    1. Recent completed alerts: `status=completed&start_date=2024-12-18T00:00:00Z`
    2. Kubernetes alerts: `agent_type=kubernetes&status=completed`
    3. Specific alert types: `alert_type=NamespaceTerminating`
    4. Time range analysis: `start_date=2024-12-18T00:00:00Z&end_date=2024-12-19T23:59:59Z`
    """
)
async def list_sessions(
    status: Optional[str] = Query(None, description="Filter by session status"),
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    start_date: Optional[datetime] = Query(None, description="Filter sessions started after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter sessions started before this date"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (1-100)"),
    history_service: HistoryService = Depends(get_history_service)
) -> SessionsListResponse:
    """
    List alert processing sessions with filtering and pagination.
    
    Args:
        status: Optional status filter (e.g., 'in_progress', 'completed', 'error')
        agent_type: Optional agent type filter (e.g., 'kubernetes')
        alert_type: Optional alert type filter (e.g., 'NamespaceTerminating')
        start_date: Optional start date filter (inclusive)
        end_date: Optional end date filter (inclusive)
        page: Page number (starting from 1)
        page_size: Number of items per page (1-100)
        history_service: Injected history service
        
    Returns:
        SessionsListResponse containing paginated session list with filters applied
        
    Raises:
        HTTPException: 400 for invalid parameters, 500 for internal errors
    """
    try:
        # Build filters dictionary
        filters = {}
        if status is not None:
            filters['status'] = status
        if agent_type is not None:
            filters['agent_type'] = agent_type
        if alert_type is not None:
            filters['alert_type'] = alert_type
        if start_date is not None:
            filters['start_date'] = start_date
        if end_date is not None:
            filters['end_date'] = end_date
            
        # Validate date range
        if start_date and end_date and start_date >= end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date must be before end_date"
            )
        
        # Get sessions from history service with pagination
        sessions, total_count = history_service.get_sessions_list(
            filters=filters,
            page=page,
            page_size=page_size
        )
        
        # Convert to response models
        session_summaries = []
        for session in sessions:
            # Calculate duration if completed
            duration_ms = None
            if session.completed_at and session.started_at:
                duration_ms = int((session.completed_at - session.started_at).total_seconds() * 1000)
            
            # Get interaction/communication counts
            llm_count = len(session.llm_interactions) if hasattr(session, 'llm_interactions') else 0
            mcp_count = len(session.mcp_communications) if hasattr(session, 'mcp_communications') else 0
            
            session_summary = SessionSummary(
                session_id=session.session_id,
                alert_id=session.alert_id,
                agent_type=session.agent_type,
                alert_type=session.alert_type,
                status=session.status,
                started_at=session.started_at,
                completed_at=session.completed_at,
                error_message=session.error_message,
                duration_ms=duration_ms,
                llm_interaction_count=llm_count,
                mcp_communication_count=mcp_count
            )
            session_summaries.append(session_summary)
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        pagination = PaginationInfo(
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            total_items=total_count
        )
        
        return SessionsListResponse(
            sessions=session_summaries,
            pagination=pagination,
            filters_applied=filters
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve sessions: {str(e)}"
        )

@router.get(
    "/sessions/{session_id}",
    response_model=SessionDetailResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get Session Details with Timeline",
    description="""
    Retrieve detailed information for a specific alert processing session.
    
    **Response includes:**
    - Complete session metadata and processing details
    - Chronological timeline of all LLM interactions and MCP communications
    - Session summary statistics and performance metrics
    - Full audit trail with microsecond-precision timing
    """
)
async def get_session_detail(
    session_id: str = Path(..., description="Unique session identifier"),
    history_service: HistoryService = Depends(get_history_service)
) -> SessionDetailResponse:
    """
    Get detailed session information with chronological timeline.
    
    Args:
        session_id: Unique session identifier
        history_service: Injected history service
        
    Returns:
        SessionDetailResponse containing complete session details and timeline
        
    Raises:
        HTTPException: 404 if session not found, 500 for internal errors
    """
    try:
        # Get session details from history service
        session_data = history_service.get_session_timeline(session_id)
        
        if not session_data:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        # Extract session information
        session_info = session_data.get('session', {})
        timeline = session_data.get('chronological_timeline', [])
        # No summary in repository response - create empty dict for now
        summary = {}
        
        # Calculate total duration if completed
        duration_ms = None
        started_at = session_info.get('started_at')
        completed_at = session_info.get('completed_at')
        if completed_at and started_at:
            if isinstance(started_at, str):
                started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            if isinstance(completed_at, str):
                completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)
        
        # Convert timeline to response models
        timeline_events = []
        for event in timeline:
            timeline_event = TimelineEvent(
                event_id=event.get('event_id', event.get('interaction_id', event.get('communication_id', 'unknown'))),
                type=event.get('type', 'unknown'),
                timestamp=event['timestamp'],
                step_description=event.get('step_description', 'No description available'),
                details=event.get('details', {}),
                duration_ms=event.get('duration_ms')
            )
            timeline_events.append(timeline_event)
        
        return SessionDetailResponse(
            session_id=session_info['session_id'],
            alert_id=session_info['alert_id'],
            alert_data=session_info.get('alert_data', {}),
            agent_type=session_info['agent_type'],
            alert_type=session_info.get('alert_type'),
            status=session_info['status'],
            started_at=started_at,
            completed_at=completed_at,
            error_message=session_info.get('error_message'),
            duration_ms=duration_ms,
            session_metadata=session_info.get('session_metadata', {}),
            chronological_timeline=timeline_events,
            summary=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve session details: {str(e)}"
        )

@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="History Service Health Check",
    description="""
    Check the health status of the history service.
    
    **Status Values:**
    - `healthy`: Service is operational and database is accessible
    - `unhealthy`: Service has issues (e.g., database connection failed)
    - `disabled`: Service is disabled via configuration (HISTORY_ENABLED=false)
    """
)
async def health_check(
    history_service: HistoryService = Depends(get_history_service)
) -> HealthCheckResponse:
    """
    Perform history service health check.
    
    Args:
        history_service: Injected history service
        
    Returns:
        HealthCheckResponse containing service health status and details
    """
    try:
        # Check if history service is enabled
        if not history_service.enabled:
            return HealthCheckResponse(
                service="alert_processing_history",
                status="disabled",
                timestamp=datetime.now(timezone.utc),
                details={
                    "message": "History service is disabled via configuration",
                    "history_enabled": False
                }
            )
        
        # Test database connectivity
        test_result = history_service.test_database_connection()
        
        if test_result:
            return HealthCheckResponse(
                service="alert_processing_history",
                status="healthy",
                timestamp=datetime.now(timezone.utc),
                details={
                    "database_connection": "ok",
                    "history_enabled": True,
                    "database_url": history_service.settings.history_database_url.split('/')[-1]  # Just the DB name for security
                }
            )
        else:
            return HealthCheckResponse(
                service="alert_processing_history",
                status="unhealthy",
                timestamp=datetime.now(timezone.utc),
                details={
                    "database_connection": "failed",
                    "history_enabled": True,
                    "error": "Database connection test failed"
                }
            )
            
    except Exception as e:
        return HealthCheckResponse(
            service="alert_processing_history",
            status="unhealthy",
            timestamp=datetime.now(timezone.utc),
            details={
                "error": str(e),
                "message": "Health check failed with exception"
            }
        )

# Note: Exception handlers should be registered at the app level in main.py 