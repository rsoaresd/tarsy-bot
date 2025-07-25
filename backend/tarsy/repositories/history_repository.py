"""
History repository for alert processing audit trail data.

Provides specialized database operations for alert sessions, LLM interactions,
and MCP communications with filtering, pagination, and chronological timeline
reconstruction capabilities.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import asc, desc, func
from sqlmodel import Session, and_, or_, select

from ..models.history import AlertSession, LLMInteraction, MCPCommunication
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class HistoryRepository:
    """
    Repository for alert processing history data operations.
    
    Provides comprehensive database operations for alert sessions and their
    associated interactions with filtering, pagination, and timeline support.
    """
    
    def __init__(self, session: Session):
        """
        Initialize history repository with database session.
        
        Args:
            session: SQLModel database session
        """
        self.session = session
        self.alert_session_repo = BaseRepository(session, AlertSession)
        self.llm_interaction_repo = BaseRepository(session, LLMInteraction)
        self.mcp_communication_repo = BaseRepository(session, MCPCommunication)
    
    # AlertSession operations
    def create_alert_session(self, alert_session: AlertSession) -> Optional[AlertSession]:
        """
        Create a new alert processing session.
        
        Args:
            alert_session: AlertSession instance to create
            
        Returns:
            The created AlertSession with database-generated fields, or None if creation failed
        """
        try:
            return self.alert_session_repo.create(alert_session)
        except Exception as e:
            logger.error(f"Failed to create alert session {alert_session.session_id}: {str(e)}")
            return None
    
    def get_alert_session(self, session_id: str) -> Optional[AlertSession]:
        """
        Retrieve an alert session by ID.
        
        Args:
            session_id: The session identifier
            
        Returns:
            AlertSession instance if found, None otherwise
        """
        return self.alert_session_repo.get_by_id(session_id)
    
    def update_alert_session(self, alert_session: AlertSession) -> bool:
        """
        Update an existing alert session.
        
        Args:
            alert_session: AlertSession instance to update
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            self.alert_session_repo.update(alert_session)
            return True
        except Exception as e:
            logger.error(f"Failed to update alert session {alert_session.session_id}: {str(e)}")
            return False
    
    def get_alert_sessions(
        self,
        status: Optional[str] = None,
        agent_type: Optional[str] = None,
        alert_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Retrieve alert sessions with filtering and pagination.
        
        Supports complex filter combinations using AND logic as specified
        in the design document.
        
        Args:
            status: Filter by processing status
            agent_type: Filter by agent type
            alert_type: Filter by alert type
            start_date: Filter sessions after this date
            end_date: Filter sessions before this date
            page: Page number for pagination
            page_size: Number of results per page
            
        Returns:
            Dictionary containing sessions list and pagination info
        """
        try:
            # Build the base query
            statement = select(AlertSession)
            conditions = []
            
            # Apply filters using AND logic (multiple filters narrow results)
            if status:
                conditions.append(AlertSession.status == status)
            if agent_type:
                conditions.append(AlertSession.agent_type == agent_type)
            if alert_type:
                conditions.append(AlertSession.alert_type == alert_type)
            if start_date:
                conditions.append(AlertSession.started_at >= start_date)
            if end_date:
                conditions.append(AlertSession.started_at <= end_date)
            
            # Apply all conditions with AND logic
            if conditions:
                statement = statement.where(and_(*conditions))
            
            # Order by started_at descending (most recent first)
            statement = statement.order_by(desc(AlertSession.started_at))
            
            # Count total results for pagination
            count_statement = select(func.count(AlertSession.session_id))
            if conditions:
                count_statement = count_statement.where(and_(*conditions))
            total_items = self.session.exec(count_statement).first() or 0
            
            # Apply pagination
            offset = (page - 1) * page_size
            statement = statement.offset(offset).limit(page_size)
            
            # Execute query
            sessions = self.session.exec(statement).all()
            
            # Get interaction counts for each session to avoid lazy loading issues
            # Create subqueries for efficient counting
            interaction_counts = {}
            
            if sessions:
                session_ids = [s.session_id for s in sessions]
                
                # Count LLM interactions for each session
                llm_count_query = select(
                    LLMInteraction.session_id,
                    func.count(LLMInteraction.interaction_id).label('count')
                ).where(
                    LLMInteraction.session_id.in_(session_ids)
                ).group_by(LLMInteraction.session_id)
                
                llm_results = self.session.exec(llm_count_query).all()
                llm_counts = {result.session_id: result.count for result in llm_results}
                
                # Count MCP communications for each session
                mcp_count_query = select(
                    MCPCommunication.session_id,
                    func.count(MCPCommunication.communication_id).label('count')
                ).where(
                    MCPCommunication.session_id.in_(session_ids)
                ).group_by(MCPCommunication.session_id)
                
                mcp_results = self.session.exec(mcp_count_query).all()
                mcp_counts = {result.session_id: result.count for result in mcp_results}
                
                # Combine counts for each session
                for session_id in session_ids:
                    interaction_counts[session_id] = {
                        'llm_interactions': llm_counts.get(session_id, 0),
                        'mcp_communications': mcp_counts.get(session_id, 0)
                    }
            
            # Calculate pagination info
            total_pages = (total_items + page_size - 1) // page_size
            
            return {
                "sessions": sessions,
                "interaction_counts": interaction_counts,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages,
                    "total_items": total_items
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get alert sessions: {str(e)}")
            return {
                "sessions": [],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0,
                    "total_items": 0
                }
            }
    
    # LLMInteraction operations
    def create_llm_interaction(self, llm_interaction: LLMInteraction) -> LLMInteraction:
        """
        Create a new LLM interaction record.
        
        Args:
            llm_interaction: LLMInteraction instance to create
            
        Returns:
            The created LLMInteraction with database-generated fields
        """
        return self.llm_interaction_repo.create(llm_interaction)
    
    def get_session_llm_interactions(self, session_id: str) -> List[LLMInteraction]:
        """
        Get all LLM interactions for a session, ordered chronologically.
        
        Args:
            session_id: The session identifier
            
        Returns:
            List of LLMInteraction instances ordered by timestamp
        """
        try:
            statement = select(LLMInteraction).where(
                LLMInteraction.session_id == session_id
            ).order_by(asc(LLMInteraction.timestamp))
            
            return self.session.exec(statement).all()
        except Exception as e:
            logger.error(f"Failed to get LLM interactions for session {session_id}: {str(e)}")
            raise
    
    # MCPCommunication operations
    def create_mcp_communication(self, mcp_communication: MCPCommunication) -> MCPCommunication:
        """
        Create a new MCP communication record.
        
        Args:
            mcp_communication: MCPCommunication instance to create
            
        Returns:
            The created MCPCommunication with database-generated fields
        """
        return self.mcp_communication_repo.create(mcp_communication)
    
    def get_session_mcp_communications(self, session_id: str) -> List[MCPCommunication]:
        """
        Get all MCP communications for a session, ordered chronologically.
        
        Args:
            session_id: The session identifier
            
        Returns:
            List of MCPCommunication instances ordered by timestamp
        """
        try:
            statement = select(MCPCommunication).where(
                MCPCommunication.session_id == session_id
            ).order_by(asc(MCPCommunication.timestamp))
            
            return self.session.exec(statement).all()
        except Exception as e:
            logger.error(f"Failed to get MCP communications for session {session_id}: {str(e)}")
            raise
    
    # Timeline reconstruction operations
    def get_session_timeline(self, session_id: str) -> Dict[str, Any]:
        """
        Reconstruct chronological timeline for a session.
        
        Combines LLM interactions and MCP communications in chronological order
        using microsecond-precision timestamps for exact ordering.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Dictionary containing session details and chronological timeline
        """
        try:
            # Get the session
            session = self.get_alert_session(session_id)
            if not session:
                return {}
            
            # Get all interactions and communications
            llm_interactions = self.get_session_llm_interactions(session_id)
            mcp_communications = self.get_session_mcp_communications(session_id)
            
            # Build chronological timeline
            timeline_events = []
            
            # Add LLM interactions to timeline
            for interaction in llm_interactions:
                timeline_events.append({
                    "timestamp": interaction.timestamp,
                    "type": "llm_interaction",
                    "step_description": interaction.step_description,
                    "model_used": interaction.model_used,
                    "token_usage": interaction.token_usage,
                    "duration_ms": interaction.duration_ms,
                    "interaction_id": interaction.interaction_id
                })
            
            # Add MCP communications to timeline
            for communication in mcp_communications:
                timeline_events.append({
                    "timestamp": communication.timestamp,
                    "type": "mcp_communication",
                    "step_description": communication.step_description,
                    "server_name": communication.server_name,
                    "communication_type": communication.communication_type,
                    "tool_name": communication.tool_name,
                    "success": communication.success,
                    "duration_ms": communication.duration_ms,
                    "communication_id": communication.communication_id
                })
            
            # Sort all events by timestamp for exact chronological ordering
            timeline_events.sort(key=lambda x: x["timestamp"])
            
            # Convert timestamps to ISO format for JSON serialization
            for event in timeline_events:
                event["timestamp"] = event["timestamp"].isoformat() + "Z"
            
            return {
                "session": {
                    "session_id": session.session_id,
                    "alert_id": session.alert_id,
                    "alert_data": session.alert_data,
                    "agent_type": session.agent_type,
                    "alert_type": session.alert_type,
                    "status": session.status,
                    "started_at": session.started_at.isoformat() + "Z" if session.started_at else None,
                    "completed_at": session.completed_at.isoformat() + "Z" if session.completed_at else None,
                    "total_interactions": len(llm_interactions) + len(mcp_communications)
                },
                "chronological_timeline": timeline_events,
                "llm_interactions": llm_interactions,
                "mcp_communications": mcp_communications
            }
            
        except Exception as e:
            logger.error(f"Failed to get session timeline for {session_id}: {str(e)}")
            return None
    
    # Utility operations
    def get_active_sessions(self) -> List[AlertSession]:
        """
        Get all currently active (in_progress or pending) sessions.
        
        Returns:
            List of AlertSession instances that are currently active
        """
        try:
            statement = select(AlertSession).where(
                or_(
                    AlertSession.status == "in_progress",
                    AlertSession.status == "pending"
                )
            ).order_by(desc(AlertSession.started_at))
            
            return self.session.exec(statement).all()
        except Exception as e:
            logger.error(f"Failed to get active sessions: {str(e)}")
            raise
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard metrics from the database.
        
        Returns:
            Dictionary containing session counts, statistics, and metrics
        """
        try:
            # Get session counts by status
            active_count = self.session.exec(
                select(func.count(AlertSession.session_id)).where(
                    or_(
                        AlertSession.status == "in_progress",
                        AlertSession.status == "pending"
                    )
                )
            ).first() or 0
            
            completed_count = self.session.exec(
                select(func.count(AlertSession.session_id)).where(
                    AlertSession.status == "completed"
                )
            ).first() or 0
            
            failed_count = self.session.exec(
                select(func.count(AlertSession.session_id)).where(
                    or_(
                        AlertSession.status == "failed",
                        AlertSession.status == "error"
                    )
                )
            ).first() or 0
            
            # Get total interaction counts
            total_llm_interactions = self.session.exec(
                select(func.count(LLMInteraction.interaction_id))
            ).first() or 0
            
            total_mcp_communications = self.session.exec(
                select(func.count(MCPCommunication.communication_id))
            ).first() or 0
            
            # Get sessions from last 24 hours
            last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
            last_24h_count = self.session.exec(
                select(func.count(AlertSession.session_id)).where(
                    AlertSession.started_at >= last_24h
                )
            ).first() or 0
            
            # Calculate average session duration for completed sessions
            completed_sessions_with_duration = self.session.exec(
                select(AlertSession).where(
                    and_(
                        AlertSession.status == "completed",
                        AlertSession.completed_at.is_not(None)
                    )
                )
            ).all()
            
            avg_duration = 0.0
            if completed_sessions_with_duration:
                total_duration = sum([
                    (session.completed_at - session.started_at).total_seconds()
                    for session in completed_sessions_with_duration
                ])
                avg_duration = total_duration / len(completed_sessions_with_duration)
            
            # Calculate error rate
            total_sessions = active_count + completed_count + failed_count
            error_rate = (failed_count / total_sessions * 100) if total_sessions > 0 else 0.0
            
            return {
                "active_sessions": active_count,
                "completed_sessions": completed_count,
                "failed_sessions": failed_count,
                "total_interactions": total_llm_interactions + total_mcp_communications,
                "avg_session_duration": round(avg_duration, 2),
                "error_rate": round(error_rate, 2),
                "last_24h_sessions": last_24h_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard metrics: {str(e)}")
            raise
    
    def get_filter_options(self) -> Dict[str, Any]:
        """
        Get dynamic filter options based on actual data in the database.
        
        Returns:
            Dictionary containing available filter options
        """
        try:
            # Get distinct agent types from the database
            agent_types = self.session.exec(
                select(AlertSession.agent_type).distinct()
                .where(AlertSession.agent_type.is_not(None))
            ).all()
            
            # Get distinct alert types from the database
            alert_types = self.session.exec(
                select(AlertSession.alert_type).distinct()
                .where(AlertSession.alert_type.is_not(None))
            ).all()
            
            # Get distinct statuses from the database
            statuses = self.session.exec(
                select(AlertSession.status).distinct()
            ).all()
            
            return {
                "agent_types": sorted(list(agent_types)) if agent_types else [],
                "alert_types": sorted(list(alert_types)) if alert_types else [],
                "status_options": sorted(list(statuses)) if statuses else [],
                "time_ranges": [
                    {"label": "Last Hour", "value": "1h"},
                    {"label": "Last 4 Hours", "value": "4h"},
                    {"label": "Today", "value": "today"},
                    {"label": "This Week", "value": "week"},
                    {"label": "This Month", "value": "month"}
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get filter options: {str(e)}")
            raise
    
    def export_session_data(self, session_id: str, format: str = 'json') -> Dict[str, Any]:
        """
        Export comprehensive session data including timeline.
        
        Args:
            session_id: The session ID to export
            format: Export format ('json' or 'csv')
            
        Returns:
            Dictionary containing session data and export metadata
        """
        try:
            # Get session details
            session = self.get_alert_session(session_id)
            if not session:
                return {
                    "error": f"Session {session_id} not found",
                    "session_id": session_id,
                    "format": format,
                    "data": None
                }
            
            # Get timeline data
            timeline_data = self.get_session_timeline(session_id)
            
            # Prepare export data
            export_data = {
                "session": {
                    "session_id": session.session_id,
                    "alert_id": session.alert_id,
                    "agent_type": session.agent_type,
                    "alert_type": session.alert_type,
                    "status": session.status,
                    "started_at": session.started_at.isoformat(),
                    "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                    "error_message": session.error_message,
                    "alert_data": session.alert_data,
                    "session_metadata": session.session_metadata
                },
                "timeline": timeline_data,
                "export_metadata": {
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                    "format": format,
                    "total_interactions": len(timeline_data.get("chronological_timeline", [])),
                    "session_duration_seconds": (
                        (session.completed_at - session.started_at).total_seconds()
                        if session.completed_at else
                        (datetime.now(timezone.utc) - session.started_at).total_seconds()
                    )
                }
            }
            
            return {
                "session_id": session_id,
                "format": format,
                "data": export_data,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Failed to export session data for {session_id}: {str(e)}")
            raise
    
    def search_sessions(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search sessions by various fields using full-text search.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of matching session summaries
        """
        try:
            # Build search query - search across multiple fields
            search_pattern = f"%{query}%"
            
            statement = select(AlertSession).where(
                or_(
                    AlertSession.alert_id.ilike(search_pattern),
                    AlertSession.agent_type.ilike(search_pattern),
                    AlertSession.alert_type.ilike(search_pattern),
                    AlertSession.error_message.ilike(search_pattern),
                    # Search in JSON fields using SQLite JSON functions
                    func.json_extract(AlertSession.alert_data, '$.alert_type').ilike(search_pattern),
                    func.json_extract(AlertSession.alert_data, '$.environment').ilike(search_pattern),
                    func.json_extract(AlertSession.alert_data, '$.cluster').ilike(search_pattern),
                    func.json_extract(AlertSession.alert_data, '$.namespace').ilike(search_pattern),
                    func.json_extract(AlertSession.session_metadata, '$.description').ilike(search_pattern)
                )
            ).order_by(desc(AlertSession.started_at)).limit(limit)
            
            sessions = self.session.exec(statement).all()
            
            # Convert to summary format
            results = []
            for session in sessions:
                duration_seconds = (
                    (session.completed_at - session.started_at).total_seconds()
                    if session.completed_at else
                    (datetime.now(timezone.utc) - session.started_at).total_seconds()
                )
                
                results.append({
                    "session_id": session.session_id,
                    "alert_id": session.alert_id,
                    "agent_type": session.agent_type,
                    "alert_type": session.alert_type,
                    "status": session.status,
                    "started_at": session.started_at.isoformat(),
                    "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                    "error_message": session.error_message,
                    "duration_seconds": duration_seconds
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search sessions with query '{query}': {str(e)}")
            raise
    
    def cleanup_old_sessions(self, retention_days: int) -> int:
        """
        Clean up sessions older than retention period.
        
        Args:
            retention_days: Number of days to retain data
            
        Returns:
            Number of sessions deleted
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
            
            # Get sessions to delete
            statement = select(AlertSession).where(
                and_(
                    AlertSession.completed_at < cutoff_date,
                    AlertSession.status.in_(["completed", "failed"])
                )
            )
            sessions_to_delete = self.session.exec(statement).all()
            
            # Delete related records first (foreign key constraints)
            for session in sessions_to_delete:
                # Delete LLM interactions
                llm_statement = select(LLMInteraction).where(
                    LLMInteraction.session_id == session.session_id
                )
                llm_interactions = self.session.exec(llm_statement).all()
                for interaction in llm_interactions:
                    self.session.delete(interaction)
                
                # Delete MCP communications
                mcp_statement = select(MCPCommunication).where(
                    MCPCommunication.session_id == session.session_id
                )
                mcp_communications = self.session.exec(mcp_statement).all()
                for communication in mcp_communications:
                    self.session.delete(communication)
                
                # Finally delete the session
                self.session.delete(session)
            
            self.session.commit()
            return len(sessions_to_delete)
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to cleanup old sessions: {str(e)}")
            return 0
    
    def get_llm_interactions_for_session(self, session_id: str) -> List[LLMInteraction]:
        """
        Get all LLM interactions for a specific session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            List of LLMInteraction objects for the session
        """
        try:
            statement = select(LLMInteraction).where(
                LLMInteraction.session_id == session_id
            ).order_by(LLMInteraction.timestamp)
            
            return self.session.exec(statement).all()
            
        except Exception as e:
            logger.error(f"Failed to get LLM interactions for session {session_id}: {str(e)}")
            return []
    
    def get_mcp_communications_for_session(self, session_id: str) -> List[MCPCommunication]:
        """
        Get all MCP communications for a specific session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            List of MCPCommunication objects for the session
        """
        try:
            statement = select(MCPCommunication).where(
                MCPCommunication.session_id == session_id
            ).order_by(MCPCommunication.timestamp)
            
            return self.session.exec(statement).all()
            
        except Exception as e:
            logger.error(f"Failed to get MCP communications for session {session_id}: {str(e)}")
            return [] 