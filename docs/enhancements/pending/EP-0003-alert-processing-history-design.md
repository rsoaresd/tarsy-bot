# EP-0003: Alert Processing History Service - Design Document

**Status:** Draft  
**Created:** 2024-12-19  
**Updated:** 2024-12-19  
**Phase:** Technical Design
**Requirements Document:** `docs/enhancements/pending/EP-0003-alert-processing-history-requirements.md`
**Next Phase:** Implementation Plan

---

## Design Overview

This design document outlines the technical solution for implementing a comprehensive Alert Processing History Service that captures and stores the complete lifecycle of alert processing, including all LLM and MCP communications, to enable future dashboard development and operational insights.

### Architecture Summary

The solution introduces a new History Service that acts as a persistent data layer for alert processing workflows. It integrates transparently with existing components through event hooks and database abstraction, providing comprehensive audit trails without disrupting current functionality.

### Key Design Principles

- **Non-intrusive Integration**: Hooks into existing workflow without changing core alert processing logic
- **Database Agnostic**: Abstract data layer allows switching from SQLite to PostgreSQL (data loss acceptable)  
- **Comprehensive Audit Trail**: Captures every interaction and state change during alert processing
- **Simple Concurrency**: Supports concurrent alert processing with timestamp-based chronological ordering
- **Future-Ready API**: REST endpoints designed for dashboard and monitoring integration

### Design Goals

- Provide complete historical visibility into alert processing workflows
- Enable debugging and performance analysis through comprehensive audit trails
- Establish foundation for SRE monitoring dashboard development
- Maintain high performance and reliability of existing alert processing
- Support scalable data storage and retrieval patterns

## System Architecture

### High-Level Architecture

The Alert Processing History Service integrates with existing components through a combination of service hooks, event listeners, and database persistence. The service operates alongside current workflows, capturing data without blocking or modifying core processing logic.

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Alert Service  │    │  History API    │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
         v                        v                        v
┌─────────────────────────────────────────────────────────────────┐
│                    WebSocket Manager                            │
└─────────────────────────────────────────────────────────────────┘
         │                        │                        │
         │                        v                        │
         │              ┌──────────────────┐               │
         │              │     Agents       │               │
         │              │  (Kubernetes,    │               │
         │              │   Base, etc.)    │               │
         │              └──────────────────┘               │
         │                        │                        │
         v                        v                        v
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   LLM Client    │    │   MCP Client     │    │ History Service │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                                  v
                     ┌──────────────────┐
                     │ Database Layer   │
                     │   (SQLite →      │
                     │   PostgreSQL)    │
                     └──────────────────┘
```

### Component Architecture

#### New Components

- **History Service** (`backend/app/services/history_service.py`): Core service responsible for capturing, storing, and retrieving alert processing history
- **History Models** (`backend/app/models/history.py`): Data models for alert sessions, LLM interactions, and MCP communications
- **Database Repository** (`backend/app/repositories/history_repository.py`): Database abstraction layer for CRUD operations
- **History API Controller** (`backend/app/controllers/history_controller.py`): REST API endpoints for querying historical data
- **Event Hooks** (`backend/app/hooks/history_hooks.py`): Integration points for capturing data from existing components

#### Modified Components

- **Alert Service** (`backend/app/services/alert_service.py`): Add history tracking hooks for session lifecycle events
- **LLM Client** (`backend/app/integrations/llm/client.py`): Add hooks to capture all prompt/response interactions
- **MCP Client** (`backend/app/integrations/mcp/client.py`): Add hooks to capture tool availability and invocations
- **Main Application** (`backend/app/main.py`): Register new API routes and initialize history service

#### Component Interactions

1. **Alert Processing Initiation**: Alert Service creates history session
2. **Chronological LLM Interaction Capture**: LLM Client hooks automatically log interactions with:
   - Microsecond-precision timestamp (ensures exact chronological ordering)
   - Human-readable step description
   - Full prompts, responses, and tool calls
3. **Chronological MCP Communication Logging**: MCP Client hooks capture communications with:
   - Microsecond-precision timestamp (maintains exact chronological order across all interactions)
   - Human-readable step description
   - Tool discoveries, invocations, and results
4. **Status Updates**: Agents update processing status through History Service
5. **Timeline Reconstruction**: History API Controller queries Database Repository and sorts by timestamp for chronological flow
6. **Data Retrieval**: Response includes both detailed interactions and unified timeline for step-by-step debugging

### Data Flow Design

#### Data Processing Steps

1. **Session Initialization**: Alert received → History Service creates new processing session
2. **Chronological Interaction Capture**: Each LLM/MCP interaction → Hook captures data with:
   - Microsecond-precision timestamp (ensures exact chronological ordering across all interaction types)
   - Human-readable step description (for easy flow understanding)
3. **Status Updates**: Agent progress updates → History Service records status changes
4. **Session Completion**: Alert processing finishes → History Service marks session complete
5. **Timeline Reconstruction**: API requests → Database Repository queries and reconstructs chronological flow by timestamp
6. **Data Retrieval**: Response includes both raw interactions and sorted timeline for step-by-step analysis

## Data Design

### Data Models

#### New Data Models

```python
AlertSession:
  - session_id: UUID (primary key)
  - alert_id: str (external alert identifier)
  - alert_data: JSON (original alert payload)
  - agent_type: str (processing agent type)
  - status: str (pending, in_progress, completed, failed)
  - started_at: datetime
  - completed_at: datetime (nullable)
  - error_message: str (nullable)
  - metadata: JSON (additional context)

LLMInteraction:
  - interaction_id: UUID (primary key)
  - session_id: UUID (foreign key to AlertSession)
  - timestamp: datetime (microsecond precision for exact chronological ordering across all interactions)
  - prompt_text: text (full prompt sent to LLM)
  - response_text: text (full response from LLM)
  - tool_calls: JSON (list of tool calls made)
  - tool_results: JSON (results from tool calls)
  - model_used: str (LLM model identifier)
  - token_usage: JSON (input/output token counts)
  - duration_ms: int
  - step_description: str (human-readable step description, e.g. "Initial alert analysis")

MCPCommunication:
  - communication_id: UUID (primary key)
  - session_id: UUID (foreign key to AlertSession)
  - timestamp: datetime (microsecond precision for exact chronological ordering across all interactions)
  - server_name: str (MCP server identifier)
  - communication_type: str (tool_list, tool_call, result)
  - tool_name: str (nullable, for tool calls)
  - tool_arguments: JSON (nullable, tool call arguments)
  - tool_result: JSON (nullable, tool call result)
  - available_tools: JSON (nullable, for tool_list type)
  - duration_ms: int
  - success: boolean
  - error_message: str (nullable)
  - step_description: str (human-readable step description, e.g. "Kubectl pod status check")
```

### Database Design

#### Schema Changes

- Create new tables: `alert_sessions`, `llm_interactions`, `mcp_communications`
- Establish foreign key relationships between session and interaction tables
- Create indexes on frequently queried fields:
  - `session_id` (for filtering by session)
  - `timestamp` (for chronological ordering and time-based queries)
  - `status` (for filtering by processing status)
- Implement schema creation scripts for SQLite

#### Migration Strategy

1. **Development Phase**: Use SQLite with simple schema creation scripts
2. **Production Migration**: Database abstraction layer allows switching to PostgreSQL (data loss acceptable)
3. **Fresh Start**: New database deployments start with empty schema - no data transfer needed
4. **Schema Management**: Simple SQL scripts for schema creation, no complex migration tools needed

## API Design

### New API Endpoints

#### Endpoint 1: Get Alert Sessions
- **Method**: GET
- **Path**: `/api/v1/history/sessions`
- **Purpose**: Retrieve alert processing sessions (active or completed) with filtering and pagination
- **Query Parameters**:
  - `status`: Filter by processing status (pending, in_progress, completed, failed)
  - `agent_type`: Filter by agent type
  - `start_date`: Filter sessions after date
  - `end_date`: Filter sessions before date
  - `page`: Page number for pagination
  - `page_size`: Number of results per page
- **Response Format**:
  ```json
  {
    "sessions": [
      {
        "session_id": "uuid",
        "alert_id": "alert-123",
        "agent_type": "kubernetes", 
        "status": "completed",
        "started_at": "2024-12-19T10:00:00Z",
        "completed_at": "2024-12-19T10:05:00Z",
        "duration_ms": 300000
      },
      {
        "session_id": "uuid",
        "alert_id": "alert-456",
        "agent_type": "kubernetes",
        "status": "in_progress", 
        "started_at": "2024-12-19T10:10:00Z",
        "elapsed_ms": 45000
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_pages": 5,
      "total_items": 100
    }
  }
  ```

#### Endpoint 2: Get Session Details
- **Method**: GET
- **Path**: `/api/v1/history/sessions/{session_id}`
- **Purpose**: Retrieve complete details for a specific alert processing session with chronological timeline
- **Response Format**:
  ```json
  {
    "session": {
      "session_id": "uuid",
      "alert_id": "alert-123", 
      "alert_data": {...},
      "agent_type": "kubernetes",
      "status": "completed",
      "started_at": "2024-12-19T10:00:00Z",
      "completed_at": "2024-12-19T10:05:00Z",
      "total_interactions": 8
    },
    "chronological_timeline": [
      {
        "timestamp": "2024-12-19T10:00:15.123456Z",
        "type": "mcp_communication",
        "step_description": "Discover available kubectl tools",
        "server_name": "kubernetes-mcp",
        "communication_type": "tool_list",
        "duration_ms": 45
      },
      {
        "timestamp": "2024-12-19T10:00:16.789012Z", 
        "type": "llm_interaction",
        "step_description": "Initial alert analysis",
        "model_used": "claude-3-sonnet",
        "token_usage": {"input": 1200, "output": 450},
        "duration_ms": 2300
      },
      {
        "timestamp": "2024-12-19T10:00:18.345678Z",
        "type": "mcp_communication", 
        "step_description": "Check pod status",
        "server_name": "kubernetes-mcp",
        "tool_name": "kubectl_get_pods",
        "success": true,
        "duration_ms": 890
      }
    ],
    "llm_interactions": [...],
    "mcp_communications": [...]
  }
  ```


### API Integration Points

- REST endpoints integrate with existing FastAPI router structure
- Authentication/authorization reuses existing security middleware
- Error handling follows established API error response patterns
- Response formats compatible with future frontend dashboard integration
- Active sessions retrieved using `/sessions?status=in_progress` or `/sessions?status=pending`
- Same detail level provided for all sessions regardless of status
- **Chronological Timeline**: Primary feature for step-by-step debugging and flow analysis
- **Timestamp Precision**: Microsecond timestamps ensure exact chronological reconstruction across all interaction types
- **Human-Readable Steps**: Step descriptions provide context for each interaction in the timeline

## User Interface Design

### UI Components

*Note: UI development is out of scope for this EP per requirements document*

#### Integration Points for Future UI Development
- API endpoints provide structured data for dashboard components
- **Chronological Timeline View**: Ready-to-use timeline data for step-by-step visualization
- **Interactive Flow Debugging**: Precise timestamps enable interactive debugging UI with exact timing information
- **Progress Visualization**: Real-time status updates can be integrated with WebSocket manager in future EP
- Pagination and filtering support large dataset visualization
- **Detailed Session Analysis**: Drill-down from timeline overview to detailed interaction data
- Single consistent interface for both active and historical session data
- **Step-by-Step Navigation**: Human-readable step descriptions perfect for UI flow diagrams

## Security Design

### Security Architecture

- Database access controlled through application-level authentication
- Sensitive alert data encrypted at rest using database encryption features
- Access control integrated with existing security middleware

### Authentication & Authorization

- API endpoints protected by existing authentication mechanisms
- Role-based access control for historical data retrieval
- Audit trail access limited to authorized SRE personnel

### Data Protection

- Database connections use encrypted communication channels
- Sensitive fields in alert data can be masked or redacted
- Data retention policies configurable for compliance requirements

### Security Controls

- Input validation on all API endpoints
- SQL injection protection through ORM/prepared statements

## Performance Design

### Performance Requirements

- Support reasonable concurrent alert processing without significant performance impact
- Query responses should be responsive for typical dashboard usage

### Performance Architecture

- Synchronous database operations are acceptable given low concurrency expectations
- Simple database connections with basic optimization
- Indexed database queries optimize historical data retrieval

### Scalability Design

- Database abstraction layer supports switching to PostgreSQL when needed
- Pagination prevents large dataset performance issues
- Simple data retention policies manageable through configuration

### Performance Optimizations

- Selective field indexing on commonly queried columns
- Simple database connections with ORM optimization

## Error Handling & Resilience

### Error Handling Strategy

- Database failures do not interrupt alert processing workflow
- Failed history writes logged but do not propagate errors to processing
- Retry mechanisms for transient database connectivity issues

### Failure Modes

- **Database Connectivity Failure**
  - **Impact**: History data not persisted, processing continues
  - **Detection**: Connection timeouts and database exceptions
  - **Recovery**: Automatic retry with exponential backoff, fallback to logging
  
### Resilience Patterns

- Circuit breaker pattern for database connections
- Graceful degradation when history service unavailable
- History capture failures do not interrupt alert processing flow

## Configuration & Deployment

### Configuration Changes

#### New Configuration Options

- **HISTORY_DATABASE_URL**: Database connection string (default: sqlite:///history.db)
- **HISTORY_ENABLED**: Enable/disable history capture (default: true)
- **HISTORY_RETENTION_DAYS**: Data retention period (default: 90)

### Deployment Considerations

#### Deployment Strategy
- Deploy as part of existing backend service
- Database schema created automatically on first startup

#### Rollback Strategy
- History service can be disabled via configuration
- Simple schema recreation for rollbacks if needed
- No impact on core alert processing if history service disabled

## Testing Strategy

### Unit Testing

#### Test Coverage Areas
- History service CRUD operations with mocked database
- API endpoint response formatting and error handling  
- Database repository abstraction layer functionality
- Event hook integration without side effects

### Integration Testing

#### Integration Points to Test
- Alert service integration captures session lifecycle correctly
- LLM client hooks capture all interaction data accurately
- MCP client hooks log tool communications completely
- Database abstraction layer works correctly with SQLite

### End-to-End Testing (Mock Services Only)

#### Test Scenarios
- Complete alert processing with full history capture verification
- Concurrent alert processing without data corruption
- API retrieval of captured historical data matches expectations
- Database abstraction layer provides foundation for future PostgreSQL migration

## Monitoring & Observability

### Logging Strategy

- Structured logging for all database operations
- Error logging for failed history capture attempts
- Performance logging for slow operations exceeding thresholds

## Migration & Backward Compatibility

### Migration Strategy

- Phase 1: Deploy with SQLite database for development and testing
- Phase 2: Switch to PostgreSQL for production scalability (fresh deployment)
- Phase 3: Implement data archiving and retention policies

### Backward Compatibility

- No breaking changes to existing API endpoints
- Alert processing workflow unchanged
- Existing frontend interfaces unaffected

### Migration Steps

1. Deploy history service with feature flag disabled
2. Enable history capture in development environment
3. Validate data capture accuracy through integration testing
4. Enable in production with monitoring
5. Switch to PostgreSQL when needed (fresh start acceptable)

## Implementation Considerations

### Dependencies

- SQLAlchemy ORM for database abstraction
- pydantic for data validation and serialization

### Constraints

- Must work within existing FastAPI/Python backend architecture
- Cannot modify existing alert processing API contracts
- Focus on SQLite initially with architecture that allows future PostgreSQL adoption
- History capture should not significantly impact alert processing flow
- Chronological ordering must be maintained across all interaction types using microsecond-precision timestamps

## Documentation Requirements

### Code Documentation

- Comprehensive docstrings for all history service classes and methods
- Database model documentation with field descriptions
- API endpoint documentation with request/response examples

### API Documentation

- OpenAPI/Swagger documentation for new history endpoints
- Integration examples for future dashboard development
- Query parameter documentation with filtering examples

### Architecture Documentation

- Database schema diagrams and relationship documentation
- Integration flow diagrams showing data capture points
- Deployment and migration procedures

---

## Next Steps

After design approval:
1. Create Implementation Plan: `docs/enhancements/pending/EP-0003-alert-processing-history-implementation.md`
2. Reference this design document in the implementation phase
3. Ensure implementation plan addresses all design elements

**AI Prompt for Next Phase:**
```
Create an implementation plan using the template at docs/templates/ep-implementation-template.md for EP-0003 based on the approved design in this document and the requirements in EP-0003-alert-processing-history-requirements.md.
``` 