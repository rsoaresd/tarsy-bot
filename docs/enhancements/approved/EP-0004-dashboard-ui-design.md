# EP-0004: Tarsy Dashboard UI for Alert History - Design Document

**Status:** Approved  
**Created:** 2025-01-19  
**Phase:** Design Approved
**Requirements Document:** `docs/enhancements/approved/EP-0004-dashboard-ui-requirements.md`
**Next Phase:** Implementation Plan

---

## Design Overview

This design creates a standalone React dashboard application (`dashboard/`) that provides SRE engineers with comprehensive **read-only observability** into alert processing workflows. The dashboard will be implemented as a sibling directory to the existing `alert-dev-ui/`, maintaining complete separation between the two applications. The dashboard emphasizes the distinction between **active alerts** (currently processing) and **historical alerts** (completed processing), leveraging the existing EP-0003 history service API and **integrating with the existing EP-0003 hook system** for real-time updates.

### Integrated Hook System Approach

This design leverages the existing EP-0003 hook infrastructure to provide real-time dashboard updates, creating a **shared event pipeline** that serves both history logging and dashboard broadcasting:

**Key Benefits:**
- **Single Event Source**: Both systems use the same LLM/MCP interaction events
- **Data Consistency**: Identical timestamps, session IDs, and interaction context
- **No Service Modifications**: Existing LLM/MCP clients remain unchanged
- **Reduced Complexity**: No separate event infrastructure needed
- **Concurrent Execution**: Dashboard hooks run alongside history hooks without performance impact

### Architecture Summary

The dashboard follows a modern React SPA architecture with Material-UI components, implemented as an independent application in the `dashboard/` directory (sibling to `alert-dev-ui/`). The architecture implements a layered approach:
- **Presentation Layer**: React components with Material-UI theming
- **State Management Layer**: React hooks and context for local state management  
- **Communication Layer**: Axios for REST API calls and multiplexed WebSocket for real-time updates
- **Service Layer**: Dashboard-specific API clients and WebSocket subscription managers

**Directory Structure**: `dashboard/` as independent sibling to existing `alert-dev-ui/` directory.

### Key Design Principles

- **Read-Only Observability**: Dashboard provides monitoring and analysis without control operations
- **Active/Historical Distinction**: Clear separation between currently processing and completed alerts
- **Separation of Concerns**: Dashboard operates independently from alert dev UI
- **Reusable Patterns**: Leverage proven patterns from existing alert dev UI
- **Real-time First**: WebSocket integration for live operational monitoring
- **Performance Conscious**: Efficient data loading and virtual scrolling for large datasets
- **Accessibility First**: WCAG 2.1 AA compliance built into component design

### Design Goals

- **Operational Observability**: Provide comprehensive read-only visibility into alert processing workflows
- **Real-Time Awareness**: Enable immediate visibility into active alert processing status
- **Historical Analysis**: Support efficient filtering and analysis of completed alerts
- **Performance**: Handle 1000+ sessions with responsive UI interactions
- **Scalability**: Support multiple concurrent users without performance degradation
- **Maintainability**: Clean, testable architecture following React best practices

## System Architecture

### High-Level Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                        Tarsy Dashboard                        │
├───────────────────────────────────────────────────────────────┤
│                    React SPA (dashboard/)                     │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐  │
│  │  Session List   │ │  Session Detail │ │  Real-time      │  │
│  │  Components     │ │  Components     │ │  Components     │  │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘  │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐  │
│  │  API Service    │ │  WebSocket      │ │  State          │  │
│  │  Layer          │ │  Manager        │ │  Management     │  │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘  │
├───────────────────────────────────────────────────────────────┤
│                Backend Services (Integrated Hook System)      │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐  │
│  │  History API    │ │  Shared Hook    │ │  WebSocket      │  │
│  │  (EP-0003)      │ │  System         │ │  Broadcasting   │  │
│  │                 │ │  ┌───────────┐  │ │  (NEW)          │  │
│  │                 │ │  │ History   │  │ │                 │  │
│  │                 │ │  │ Hooks     │  │ │                 │  │
│  │                 │ │  ├───────────┤  │ │                 │  │
│  │                 │ │  │Dashboard  │  │ │                 │  │
│  │                 │ │  │ Hooks     │  │ │                 │  │
│  │                 │ │  │ (NEW)     │  │ │                 │  │
│  │                 │ │  └───────────┘  │ │                 │  │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘  │
│                               ↑                               │
│  ┌─────────────────┐          │          ┌─────────────────┐  │
│  │  LLM/MCP        │ ───────────────────→│  Alert Dev UI   │  │
│  │  Interactions   │    Hook Events      │  (Unchanged)    │  │
│  └─────────────────┘                     └─────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

### Component Architecture

#### New Components

- **DashboardApp**: Main application component with routing and layout
- **DashboardView**: Main dashboard page displaying active and historical alert summaries
- **SessionDetailPage**: Dedicated page for detailed session timeline (unified for both active & historical)
- **ActiveAlertsPanel**: Panel displaying currently processing alerts with summary information
- **HistoricalSessionsList**: Paginated list of completed alert sessions with filtering
- **FilterPanel**: Advanced filtering interface for historical sessions
- **TimelineVisualization**: Interactive timeline showing LLM and MCP interactions (real-time for active sessions)
- **RealTimeMonitor**: Live status display and counters for currently processing alerts
- **ActiveAlertCard**: Summary card for active alerts (click → navigate to detail page)
- **HistoricalSessionCard**: Summary card for historical sessions (click → navigate to detail page)
- **SessionHeader**: Session metadata and status display (shows active/historical status)
- **InteractionDetails**: Detailed view of individual LLM/MCP interactions
- **SessionActions**: Action buttons for copying, exporting, and navigation
- **ErrorBoundary**: Application-wide error handling component

#### New Service Components (Dashboard-Specific)

**Note**: While similar to existing alert-dev-ui components, these are entirely new implementations for the dashboard application in the `dashboard/` directory.

- **DashboardWebSocketManager**: New multiplexed WebSocket manager specifically for dashboard:
  - Single connection for all dashboard communications
  - Dynamic subscription management for sessions and dashboard updates
  - Intelligent message routing based on subscription channels
  - Connection optimization to avoid browser connection limits
  - Auto-reconnection with subscription state restoration
  - **Difference from alert-dev-ui**: Subscription-based vs. single-session WebSocket
- **DashboardAPIClient**: New API client service for dashboard endpoints:
  - History service endpoints integration
  - Pagination support for large datasets
  - Dashboard-specific error handling and retry logic
  - **Difference from alert-dev-ui**: Read-only history API vs. alert submission API
- **SharedThemeProvider**: Shared Material-UI theme configuration:
  - **Reusable**: Could potentially be shared between alert-dev-ui and dashboard
  - **Implementation**: Copy existing theme or create shared theme package

#### Component Interactions

```
DashboardApp
├── Router
    ├── DashboardView                    # Route: /dashboard
    │   ├── FilterPanel
    │   ├── ActiveAlertsPanel           # Summary cards → navigate to detail
    │   │   └── ActiveAlertCard[]
    │   ├── HistoricalSessionsList      # Summary cards → navigate to detail
    │   │   └── HistoricalSessionCard[]
    │   └── RealTimeMonitor
    │
    └── SessionDetailPage               # Route: /sessions/{id} (both active & historical)
        ├── SessionHeader               # Shows active/historical status
        ├── TimelineVisualization       # Real-time updates for active sessions
        ├── InteractionDetails          # Live interaction details
        └── SessionActions              # Copy, export, back navigation
```

### Data Flow Design

#### Data Flow Diagrams

**Session List Data Flow (Hook System Integration):**
```
User Filter Action → FilterPanel → APIClient → History API → SessionListView → SessionCard[]
                                            ↓
                  → WebSocketManager.subscribe('dashboard_updates', filters)
                                            ↓
Hook Events → Dashboard Broadcast Hooks → WebSocket Channel Router → RealTimeMonitor → Session Status Updates
```

**Session Detail Data Flow (Hook System Integration for Active & Historical):**
```
Session Card Click → Navigate to /sessions/{id} → SessionDetailPage → APIClient → History API → Timeline Data
                                                        ↓
                                                → WebSocketManager.subscribe('session_{id}')
                                                        ↓
Hook Events → Dashboard Broadcast Hooks → WebSocket Channel Router → Real-time Timeline Updates (Active Sessions)
                                                        ↓
Navigate Back/Away → WebSocketManager.unsubscribe('session_{id}')
```

**WebSocket Message Flow (Hook System Integration):**
```
Client: { type: 'subscribe', channel: 'dashboard_updates', filters: {...} }
                              ↓
Server: Hook Events → Dashboard Broadcast Hooks → Format for WebSocket → Push Updates
                              ↓
Client: { type: 'dashboard_update', channel: 'dashboard_updates', data: {...} }
```

#### Data Processing Steps

1. **Initial Load**: Fetch paginated session list with default filters
2. **Filter Application**: Apply user filters and re-fetch filtered results
3. **Hook-Based Real-time Updates**: Process WebSocket messages generated from EP-0003 hook events for live session status on dashboard
4. **Session Detail Navigation**: Navigate to dedicated page and load detailed timeline data
5. **Timeline Rendering**: Process chronological data for timeline visualization
6. **Active Session Hook Updates**: For active sessions on detail pages, continuously update timeline with new interactions from hook events
7. **Live Status Monitoring**: Update session status, progress, and completion in real-time via integrated hook system

## Backend Dependencies & Requirements

This dashboard design leverages the existing EP-0003 hook system infrastructure, significantly reducing backend implementation requirements while ensuring consistency between historical and real-time data.

### Required Backend Changes

#### New WebSocket Implementation (Priority 1)

**Multiplexed WebSocket Endpoint**: `/ws/dashboard/{user_id}`
- **Location**: New endpoint in backend FastAPI application
- **Purpose**: Single connection supporting multiple subscription channels
- **Implementation Requirements**:
  - WebSocket connection management with user identification
  - Subscription-based message routing system
  - Channel management (subscribe/unsubscribe operations)
  - Message batching and optimization for performance
  - Graceful connection cleanup and resource management

**Subscription Channel System**:
- `dashboard_updates`: Real-time session list updates with filter support
- `session_{id}`: Individual session timeline and status updates  
- `system_health`: Service status and connectivity notifications

#### Integrated Hook System Extensions (Priority 2)

**Dashboard Broadcast Hooks** (NEW - extends existing hook system):
- **Purpose**: Capture same LLM/MCP events as EP-0003 history hooks for dashboard broadcasting
- **Architecture**: Works alongside existing history hooks using shared event pipeline
- **Implementation**: Extends `BaseEventHook` class from existing hook infrastructure
- **Benefits**: 
  - Same event timing and session context as history service
  - No modifications needed to LLM/MCP clients
  - Concurrent execution with history hooks

**Dashboard Update Service**:
- **Purpose**: Format hook event data for WebSocket broadcasting to dashboard subscribers
- **Responsibilities**:
  - Transform hook event data into dashboard-friendly messages
  - Apply user filters to session data for targeted updates
  - Batch multiple session changes into single update messages
  - Optimize update frequency to prevent dashboard flooding

**Enhanced Hook Registration**:
- **Modify**: Existing hook registration system to include dashboard hooks
- **Integration**: Dashboard hooks registered alongside history hooks at application startup
- **Execution**: Both hook types execute concurrently for same LLM/MCP events

#### Simplified Integration Points (Priority 3)

**Hook System Integration**:
- **Leverage**: Existing EP-0003 hook infrastructure without modifications
- **Events Available**: All existing LLM/MCP interaction events automatically available
  - LLM interactions (prompts, responses, timing, errors)
  - MCP communications (tool calls, results, errors)
  - Session lifecycle events (creation, completion, status changes)
- **Event Format**: Uses existing hook event format with additional dashboard formatting

**Authentication Integration**:
- **Modify**: Existing authentication system to support WebSocket user identification
- **Requirements**:
  - User ID extraction from WebSocket connection
  - Session-based or token-based WebSocket authentication
  - Connection authorization for dashboard access

### Backend Implementation Priority

1. **Phase 1 - Core WebSocket** (Must complete first)
   - Implement `/ws/dashboard/{user_id}` endpoint
   - Build subscription management system
   - Create basic message routing infrastructure

2. **Phase 2 - Hook System Integration** (Required for dashboard functionality)
   - Create dashboard broadcast hooks extending existing EP-0003 hook system
   - Integrate dashboard hooks with existing hook registration
   - Implement dashboard update service for hook data formatting

3. **Phase 3 - Optimization** (Performance and reliability)
   - Add message batching and throttling
   - Implement connection recovery mechanisms
   - Add monitoring and health checks for WebSocket system

### Backend Code Architecture

The backend implementation will follow this integrated hook system architectural pattern:

```python
# Integrated Hook System Architecture
class DashboardBroadcastHooks(BaseEventHook):
    """Dashboard broadcast hooks that work alongside existing EP-0003 history hooks"""
    
    def __init__(self, dashboard_broadcaster):
        super().__init__("dashboard_broadcast_hook")
        self.broadcaster = dashboard_broadcaster
        self.update_service = DashboardUpdateService()
    
    async def execute(self, event_type: str, **kwargs):
        """Execute dashboard broadcasting for hook events"""
        session_id = kwargs.get('session_id')
        if not session_id:
            return
            
        # Format hook data for dashboard consumption
        dashboard_data = self.update_service.format_hook_event(event_type, **kwargs)
        
        # Broadcast to appropriate subscription channels
        if event_type.endswith('.post'):
            await self.broadcaster.broadcast_session_update(session_id, dashboard_data)
        elif event_type.endswith('.error'):
            await self.broadcaster.broadcast_error_update(session_id, dashboard_data)

# Integrated Hook Registration (extends existing EP-0003 system)
def register_all_hooks():
    """Register both history and dashboard hooks together"""
    hook_manager = get_hook_manager()  # Uses existing hook manager
    
    # Existing EP-0003 hooks (unchanged)
    llm_history_hooks = LLMHooks()
    mcp_history_hooks = MCPHooks()
    hook_manager.register_hook("llm.post", llm_history_hooks)
    hook_manager.register_hook("mcp.post", mcp_history_hooks)
    
    # New EP-0004 dashboard hooks (same events, different actions)
    dashboard_broadcaster = get_dashboard_broadcaster()
    llm_dashboard_hooks = DashboardBroadcastHooks(dashboard_broadcaster)
    mcp_dashboard_hooks = DashboardBroadcastHooks(dashboard_broadcaster)
    hook_manager.register_hook("llm.post", llm_dashboard_hooks)
    hook_manager.register_hook("mcp.post", mcp_dashboard_hooks)
    
    # Both hook types execute concurrently for the same events!

# WebSocket endpoint (connects to hook-based broadcasting system)
@app.websocket("/ws/dashboard/{user_id}")
async def dashboard_websocket(websocket: WebSocket, user_id: str):
    await websocket.accept()
    connection_manager = DashboardConnectionManager()
    
    try:
        await connection_manager.register_connection(user_id, websocket)
        
        while True:
            message = await websocket.receive_json()
            await handle_dashboard_message(user_id, websocket, message)
            
    except WebSocketDisconnect:
        await connection_manager.cleanup_connection(user_id, websocket)

# Service classes (simplified due to hook integration)
class DashboardConnectionManager:
    """Manages dashboard WebSocket connections and subscriptions"""
    
class DashboardBroadcaster:
    """Broadcasts dashboard updates received from hook events"""
    
class DashboardUpdateService:
    """Formats hook event data for dashboard consumption"""
```

## Data Design

### Data Models

#### New Data Models

```typescript
DashboardSession {
  - id: string (session ID)
  - alert_type: string (alert classification)
  - agent_type: string (processing agent)
  - status: SessionStatus (current status)
  - created_at: string (ISO timestamp)
  - completed_at: string | null (completion timestamp)
  - duration_ms: number | null (processing duration)
  - summary: string (brief description)
  - error_message: string | null (error details if failed)
}

SessionFilter {
  - status: SessionStatus[] (status filter)
  - agent_type: string[] (agent type filter)
  - alert_type: string[] (alert type filter)
  - start_date: string | null (start date filter)
  - end_date: string | null (end date filter)
  - search_query: string (text search)
}

TimelineItem {
  - id: string (unique identifier)
  - type: 'llm' | 'mcp' (interaction type)
  - timestamp: string (ISO timestamp with microseconds)
  - title: string (interaction summary)
  - details: LLMInteraction | MCPCommunication (detailed data)
  - duration_ms: number | null (operation duration)
}

PaginationState {
  - page: number (current page)
  - page_size: number (items per page)
  - total_count: number (total items)
  - has_next: boolean (more pages available)
}
```

#### Modified Data Models

```typescript
// Enhanced WebSocket message model with subscription management
WebSocketMessage {
  - type: 'subscribe' | 'unsubscribe' | 'session_update' | 'session_complete' | 'dashboard_update' | 'error' (message type)
  - channel: string (subscription channel identifier)
  - session_id?: string (session identifier for session-specific messages)
  - data: SubscriptionRequest | SessionUpdate | SessionComplete | DashboardUpdate | ErrorMessage (payload)
  - timestamp: string (message timestamp)
  - user_id?: string (user identifier for connection management)
}

// Client-to-server subscription management
SubscriptionRequest {
  - action: 'subscribe' | 'unsubscribe' (subscription action)
  - channel: 'dashboard_updates' | 'session_{id}' | 'system_health' (channel name)
  - filters?: SessionFilter (optional filters for dashboard updates)
  - session_id?: string (session ID for session-specific subscriptions)
}

// Server-to-client update messages
DashboardUpdate {
  - sessions: SessionSummary[] (updated session list)
  - total_count: number (total sessions matching filters)
  - active_count: number (currently processing sessions)
  - filters_applied: SessionFilter (current filters)
}

APIResponse<T> {
  - data: T (response data)
  - pagination: PaginationState | null (pagination info)
  - error: string | null (error message)
  - timestamp: string (response timestamp)
}
```

### Database Design

No database changes required - dashboard consumes existing EP-0003 history service data through REST API endpoints.

#### Schema Changes

- No schema changes needed
- Dashboard operates as read-only consumer of existing data

#### Migration Strategy

- No data migration required
- Dashboard deployment independent of backend changes

## API Design

### New API Endpoints

Dashboard will consume existing EP-0003 endpoints without requiring new backend API endpoints:

#### Existing Endpoints Used

- **GET /api/v1/history/sessions**: Session list with filtering and pagination
- **GET /api/v1/history/sessions/{session_id}**: Detailed session with timeline
- **GET /api/v1/history/health**: Health check endpoint

### Modified API Endpoints

No modifications to existing API endpoints required.

### API Integration Points

#### History Service Integration
- **Base URL**: Configurable backend URL (development/production)
- **Authentication**: Bearer token or session-based (if implemented)
- **Error Handling**: Graceful degradation with user-friendly error messages
- **Caching**: Client-side caching for session list and details

#### WebSocket Integration Points

**Optimized Multiplexed Architecture**
- **Single Dashboard WebSocket**: `/ws/dashboard/{user_id}` (replaces multiple endpoint approach)
- **Subscription-Based Communication**: Dynamic subscription management within single connection
- **Channel-Based Message Routing**: Messages routed by subscription channels rather than separate connections
- **Connection Limit Optimization**: Eliminates browser 6-connection limit issues

**Connection Management Features**
- **Auto-reconnection**: Exponential backoff with subscription state restoration
- **Subscription State Persistence**: Automatic re-subscription after reconnection
- **Message Buffering**: Handle temporary connection losses with message queuing
- **Graceful Cleanup**: Proper unsubscription and resource cleanup on disconnect

**Subscription Channels**
- `dashboard_updates`: Real-time session list updates with filter support
- `session_{id}`: Individual session timeline and status updates
- `system_health`: Service status and connectivity notifications

## User Interface Design

### UI Components

#### New UI Components

**Core Dashboard Components:**
- **SessionGrid**: Virtualized grid component for large session lists
- **ActiveAlertsPanel**: Expandable panel showing currently processing alerts with progress indicators
- **FilterChip**: Interactive filter tag components
- **StatusIndicator**: Color-coded status indicators with icons
- **SearchBar**: Debounced search input with suggestions

**Timeline & Detail Components:**
- **TimelineChart**: SVG-based timeline visualization

- **ProgressIndicator**: Real-time progress bars and status displays
- **ErrorExpansionPanel**: Expandable error details with copy functionality

**Utility Components:**
- **DurationBadge**: Human-readable duration display component
- **LoadingSkeletons**: Placeholder components during data loading
- **QuickFilterBar**: Preset filter buttons for common queries (Failed, Timeout, Success)
- **CopyButton**: Reusable copy-to-clipboard button component

#### Adapted UI Components (From alert-dev-ui patterns)

- **DashboardLayout**: Adapted from alert dev UI layout with dashboard-specific navigation
- **DashboardErrorDisplay**: Enhanced error component with retry mechanisms and dashboard context
- **WebSocketConnectionStatus**: Connection status indicator specifically for dashboard WebSocket

### User Experience Flow

#### User Journey

1. **Dashboard Load**: User navigates to dashboard, sees active alerts at top and historical list below  
2. **Active Monitoring**: User monitors real-time processing status with live progress indicators and status summaries
3. **Active Alert Detail**: User clicks active alert → navigates to dedicated detail page with real-time timeline updates
4. **Historical Analysis**: User applies quick filters to historical data for pattern analysis
5. **Historical Detail**: User clicks historical session → navigates to dedicated detail page with complete timeline
6. **Timeline Exploration**: User reviews chronological interactions and final resolution (with live updates for active sessions)
7. **Data Export**: User copies timeline details or exports data for reporting
8. **Consistent Navigation**: Same interaction pattern for both active and historical alerts

#### User Interface Mockups

**Main Dashboard - Active/Historical Split:**
```
┌─────────────────────────────────────────────────────────────────┐
│ Tarsy SRE Dashboard                      [🔄 Auto-refresh: ●●●] │
├─────────────────────────────────────────────────────────────────┤
│ ┌─ ACTIVE ALERTS ────────────────────────────────────────────┐  │
│ │ [3 Processing] [2 Failed] [0 Pending]                      │  │
│ │                                                            │  │
│ │ 🔴 FAILED │ kubernetes-prod │ PodCrashLooping │ 00:34      │  │
│ │ ┌────────────────────────────────────────────────────────┐ │  │
│ │ │ ❌ Processing Failed │ Error: MCP timeout after 15s    │ │  │
│ │ │ Last step: kubectl get pods --namespace=prod-app       │ │  │
│ │ │ Duration: 15.3s │ [👁 View Details] [📋 Copy Error]    │ │  │
│ │ └────────────────────────────────────────────────────────┘ │  │
│ │                                                            │  │
│ │ 🟡 PROCESSING │ network-core │ LatencySpike │ 02:45        │  │
│ │ ┌────────────────────────────────────────────────────────┐ │  │
│ │ │ 🔄 In Progress │ LLM: Analyzing network metrics...     │ │  │
│ │ │ ████████████▓▓▓░░░░░ 67% │ Step 3 of 5 │ [👁 Watch]    │ │   │
│ │ │ Current: Checking bandwidth utilization                │ │   │
│ │ └────────────────────────────────────────────────────────┘ │   │
│ │                                                            │   │
│ │ 🟢 COMPLETING │ database-cluster │ ConnPoolLow │ 00:12     │   │
│ │ ┌────────────────────────────────────────────────────────┐ │   │
│ │ │ ✅ Analysis Complete │ Finalizing response...          │ │   │
│ │ │ ████████████████████░ 95% │ ETA: 8s │ [👁 View Details]│ │   │
│ │ │ Resolution: Connection pool automatically scaled       │ │   │
│ │ └────────────────────────────────────────────────────────┘ │   │
│ └──────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ ┌─ ALERT HISTORY ────────────────────────────────────────────┐   │
│ │ Quick Filters: [🔴Failed][🟡Timeout][🟢Success] │ [All Agents▼] │   │
│ │ Time: [1h][4h][Today][Week] │ 🔍[Search: ____________]      │   │
│ │                                                           │   │
│ │ Status │Agent│Alert Type      │Time │Dur │Actions         │   │
│ │ ──────┼─────┼───────────────┼─────┼────┼──────────────── │   │
│ │ 🟢 ✓  │ k8s │ServiceRestart  │12:34│0.8s│[👁 Details]    │   │
│ │ 🔴 ✗  │ net │PacketLoss      │12:28│15s │[👁 Details]    │   │
│ │ 🟢 ✓  │ db  │BackupComplete  │12:25│2.1s│[👁 Details]    │   │
│ │ 🟡 ⚠  │ k8s │MemoryPressure  │12:22│45s │[👁 Details]    │   │
│ │ 🟢 ✓  │ net │BandwidthCheck  │12:18│1.2s│[👁 Details]    │   │
│ │                                                           │   │
│ │ [◀ Prev] Page 1 of 47 [Next ▶] │ Show: [25▼] per page    │   │
│ └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Active Alert Detail Expansion:**
```
│ 🔴 FAILED │ kubernetes-prod │ PodCrashLooping │ 00:34    │ [▼]
│ ┌───────────────────────────────────────────────────────────────┐
│ │ Processing Timeline (Read-Only):                             │
│ │ ──────────────────────────────────────────────────────────── │
│ │ 00:00 🚨 Alert received: Pod crash-loop in prod-app-ns      │
│ │ 00:03 🧠 LLM analyzing: "Kubernetes pod stability issue"    │
│ │ 00:12 🔧 MCP executing: kubectl describe pod crash-pod-xyz  │
│ │ 00:28 🧠 LLM generating response...                         │
│ │ 15:30 ❌ Processing failed: MCP timeout                     │
│ │                                                             │
│ │ Error Details:                                              │
│ │ ┌─────────────────────────────────────────────────────────┐ │
│ │ │ Error: MCP server timeout after 15s                    │ │
│ │ │ Command: kubectl get events --namespace=prod-app       │ │
│ │ │ Agent: KubernetesAgent                                  │ │
│ │ │ Last successful step: kubectl describe pod             │ │
│ │ └─────────────────────────────────────────────────────────┘ │
│ │                                                             │
│ │ Actions: [👁 View Full Timeline] [📋 Copy Error Details]    │
│ └───────────────────────────────────────────────────────────────┘
```

**Session Detail Page (Historical Example):**
```
┌─────────────────────────────────────────────────────────────────┐
│ [← Back to Dashboard] Alert Details: k8s-20240119-122834       │
├─────────────────────────────────────────────────────────────────┤
│ kubernetes | ServiceRestart | ✅ Completed in 0.8s | 12:28:34  │
├─────────────────────────────────────────────────────────────────┤
│ Processing Timeline:                                            │
│ 00:00.000 ●─ Alert received                                     │
│ 00:00.045 ├─ [LLM] Initial analysis (234ms)                     │
│ 00:00.279 ├─ [MCP] Service status check (156ms)                 │
│ 00:00.435 ├─ [LLM] Response generation (365ms)                  │
│ 00:00.800 └─ ✅ Processing complete                             │
│                                                                 │
│ Final Resolution:                                               │
│ "Service restart completed successfully. Health checks passing."│
│                                                                 │
│ [📋 Copy Timeline] [📤 Export Details]                         │
└─────────────────────────────────────────────────────────────────┘
```

## Security Design

### Security Architecture

Dashboard implements client-side security measures following React security best practices:
- **XSS Prevention**: Sanitized data rendering and CSP headers
- **CSRF Protection**: CSRF tokens for API requests (if required by backend)
- **Secure Communication**: HTTPS/WSS for all API and WebSocket connections

### Authentication & Authorization

- **Authentication**: Leverage existing backend authentication mechanism
- **Authorization**: Read-only access to history data (no write operations)
- **Session Management**: Standard browser session management

### Data Protection

- **Sensitive Data**: Alert data displayed securely without logging
- **Client Storage**: Minimal localStorage usage for user preferences only
- **Memory Management**: Proper cleanup of sensitive data in component unmounting

### Security Controls

- **Input Validation**: Client-side validation of all user inputs
- **Output Encoding**: Proper HTML encoding of all displayed data
- **Error Handling**: Secure error messages without sensitive information disclosure

## Performance Design

### Performance Requirements

Based on requirements document:
- **Initial Load**: Reasonable speed for dashboard productivity
- **Pagination**: Handle 1000+ sessions efficiently  
- **Filter Operations**: Interactive performance for data exploration
- **Real-time Updates**: Prompt display of current operational status

### WebSocket Optimization Strategy

**Connection Limit Solution**
The browser's 6-connection limit per domain posed a significant constraint for the original multi-WebSocket approach. The optimized multiplexed design solves this through:
- **Single Connection Architecture**: One WebSocket handles all dashboard communications
- **Dynamic Subscription Management**: Subscribe/unsubscribe to specific data channels as needed
- **Intelligent Message Routing**: Server-side routing based on subscription channels
- **Connection Pool Preservation**: Leaves connections available for API calls and other resources

**Implementation Benefits**
- **Reduced Resource Usage**: Single persistent connection vs. multiple connections
- **Better Reconnection Handling**: Centralized reconnection logic with state restoration
- **Simplified Debugging**: All WebSocket traffic flows through single connection
- **Scalability**: Supports unlimited session subscriptions without additional connections

**Performance Optimizations**
- **Message Batching**: Multiple updates can be batched in single WebSocket message
- **Selective Updates**: Only subscribed channels receive relevant updates
- **Connection Reuse**: Same connection serves session list, details, and status updates
- **Reduced Handshake Overhead**: Single WebSocket handshake vs. multiple handshakes

### Performance Architecture

#### Virtual Scrolling
- **Implementation**: React-window for large session lists
- **Benefits**: Constant memory usage regardless of dataset size
- **Configuration**: Configurable item heights and buffer sizes

#### Efficient State Management
- **Local State**: React hooks for component-level state
- **Shared State**: Context API for cross-component state
- **Caching**: Intelligent caching of API responses with TTL

#### Lazy Loading
- **Route Splitting**: Code splitting for session detail view
- **Component Lazy Loading**: On-demand component loading
- **Data Lazy Loading**: Incremental timeline data loading

### Scalability Design

#### Client-Side Scalability
- **Memory Management**: Proper component cleanup and memory leak prevention
- **Bundle Optimization**: Tree shaking and webpack optimization
- **Progressive Loading**: Incremental data loading strategies

#### API Interaction Scalability
- **Request Debouncing**: Debounced search and filter operations
- **Batch Operations**: Batched API requests where possible
- **Connection Pooling**: Efficient WebSocket connection management

### Performance Optimizations

- **Memoization**: React.memo and useMemo for expensive computations
- **Virtualization**: Virtual scrolling for large lists and timelines
- **Image Optimization**: Optimized icons and graphics
- **Bundle Splitting**: Route-based code splitting
- **Service Worker**: Optional caching for static assets

## Error Handling & Resilience

### Error Handling Strategy

#### Error Categories
- **Network Errors**: API connection failures and timeouts
- **Data Errors**: Invalid or corrupted response data
- **Application Errors**: Component rendering and state management errors
- **WebSocket Errors**: Connection drops and message parsing failures

#### Error Handling Pattern
```typescript
interface ErrorState {
  hasError: boolean;
  error: Error | null;
  errorBoundary?: string;
  retryAction?: () => void;
}
```

### Failure Modes

- **API Unavailability**
  - **Impact**: Cannot load session data or updates
  - **Detection**: HTTP error responses and timeout detection
  - **Recovery**: Retry mechanism with exponential backoff, offline message

- **WebSocket Connection Loss**
  - **Impact**: No real-time updates received
  - **Detection**: WebSocket close/error events
  - **Recovery**: Automatic reconnection with status indicator

- **Large Dataset Performance**
  - **Impact**: UI becomes unresponsive
  - **Detection**: Performance monitoring and user feedback
  - **Recovery**: Progressive loading and virtualization

### Resilience Patterns

- **Circuit Breaker**: Prevent cascade failures in API calls
- **Retry Pattern**: Exponential backoff for failed requests
- **Graceful Degradation**: Functional UI even with limited backend connectivity
- **Error Boundaries**: Component-level error isolation

## Configuration & Deployment

## Project Structure

### Directory Layout

The dashboard application will be implemented as an independent sibling directory to maintain clear separation:

```
tarsy-bot/
├── alert-dev-ui/          # Existing development/testing UI (unchanged)
│   ├── src/
│   ├── package.json
│   └── ...
├── dashboard/             # New SRE operational dashboard  
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── types/
│   ├── package.json
│   ├── tsconfig.json
│   └── ...
├── backend/               # Backend services (WebSocket additions required)
└── ...
```

### Application Independence

- **Separate Deployments**: Each application can be built and deployed independently
- **Separate Dependencies**: Each maintains its own `package.json` and dependency management
- **Shared Infrastructure**: Both connect to the same backend services
- **Independent Development**: Teams can work on each application without conflicts

### Configuration Changes

#### New Configuration Options

- **REACT_APP_API_BASE_URL**: Backend API base URL (default: http://localhost:8000)
- **REACT_APP_WS_BASE_URL**: WebSocket base URL (default: ws://localhost:8000)
- **REACT_APP_PAGE_SIZE**: Default pagination size (default: 25)
- **REACT_APP_ENABLE_MOCK_DATA**: Enable mock data mode for development (default: false)

#### Environment-Specific Configuration

- **Development**: Mock data support and debug logging
- **Production**: Optimized builds and error reporting
- **Testing**: Test-specific API endpoints and reduced animations

## Testing Strategy

### Unit Testing

#### Test Coverage Areas

- **Component Rendering**: Snapshot and rendering tests for all components
- **State Management**: Hook and context testing
- **API Integration**: Mock API response handling
- **Utility Functions**: Pure function testing with comprehensive edge cases

#### Testing Tools
- **Jest**: Test runner and assertion framework
- **React Testing Library**: Component testing utilities
- **MSW**: API mocking for testing
- **Jest-WebSocket-Mock**: WebSocket mocking

### Integration Testing

#### Integration Points to Test

- **API Service Integration**: Full API request/response cycle testing
- **WebSocket Integration**: Real-time message handling and reconnection
- **Component Integration**: Parent-child component communication
- **Router Integration**: Navigation and route parameter handling

### End-to-End Testing (Mock Services Only)

#### Test Scenarios

- **Session List Workflow**: Load dashboard, apply filters, view results
- **Session Detail Workflow**: Navigate to session detail, view timeline
- **Real-time Updates**: Simulate live session updates and verify UI updates
- **Error Scenarios**: Test error handling and recovery mechanisms

## Monitoring & Observability

### Logging Strategy

#### Client-Side Logging
- **Error Logging**: Comprehensive error logging with stack traces
- **Performance Logging**: Performance mark and measure API
- **User Action Logging**: Optional user interaction analytics
- **Debug Logging**: Development-only detailed logging

#### Log Levels
- **ERROR**: Application errors and API failures
- **WARN**: Performance issues and deprecated feature usage
- **INFO**: User actions and application state changes
- **DEBUG**: Detailed development information

## Migration & Backward Compatibility

### Migration Strategy

No migration required as this is a new standalone application.

### Backward Compatibility

- **API Compatibility**: Compatible with existing EP-0003 history service
- **Browser Compatibility**: Support for modern browsers (Chrome 90+, Firefox 88+, Safari 14+)
- **Accessibility Compatibility**: WCAG 2.1 AA compliance maintained

### Migration Steps

1. **Development Environment Setup**: Initialize React application in `dashboard/` directory
2. **Component Development**: Build components incrementally with testing
3. **API Integration**: Connect to existing history service endpoints
4. **WebSocket Integration**: Implement optimized multiplexed WebSocket system with subscription management
5. **Production Deployment**: Deploy as standalone application


## Implementation Sequence & Priorities

### Development Order (Backend First with Integrated Hook System)

As identified in the requirements analysis, the backend WebSocket infrastructure must be implemented before meaningful frontend development can begin. However, leveraging the existing EP-0003 hook system significantly simplifies the backend implementation.

#### Phase 1: Backend WebSocket Infrastructure  
**Priority: Critical - Must complete first**
- Implement new `/ws/dashboard/{user_id}` WebSocket endpoint
- Build subscription management system (`dashboard_updates`, `session_{id}` channels)
- Create message routing and channel management infrastructure
- Create dashboard broadcaster service for WebSocket message distribution

#### Phase 2: Integrated Hook System Implementation
**Priority: High - Required for dashboard functionality**
- Create dashboard broadcast hooks extending existing EP-0003 `BaseEventHook`
- Integrate dashboard hooks with existing hook registration system
- Implement dashboard update service for formatting hook events
- Register dashboard hooks alongside existing history hooks for concurrent execution

#### Phase 3: Frontend Dashboard Development
**Priority: Medium - Depends on backend completion**
- Initialize `dashboard/` React application structure
- Implement core dashboard components and layout
- Build WebSocket client with subscription management
- Create session list and detail views

#### Phase 4: Integration & Testing
**Priority: Low - Final integration**
- End-to-end testing of integrated hook system and WebSocket communication
- Performance optimization and load testing
- Documentation and deployment preparation

### Implementation Dependencies

```
Backend WebSocket Infrastructure
    ↓
Integrated Hook System Implementation
    ↓
Frontend Dashboard Core
    ↓
Frontend Real-time Features
    ↓
Integration Testing
```

**Critical Path**: Backend WebSocket implementation blocks all frontend real-time functionality.

**Key Advantage**: Hook system integration eliminates the need to modify existing LLM/MCP clients or history service, reducing implementation complexity and ensuring data consistency.

## Implementation Considerations

### Technical Advantages of Integrated Hook System

- **Reduced Complexity**: No need to create separate event infrastructure
- **Data Consistency**: Same event timing and context as history service
- **No Service Modifications**: Existing LLM/MCP clients remain unchanged
- **Performance**: Concurrent hook execution with existing history hooks
- **Maintainability**: Single event pipeline reduces potential inconsistencies
- **Future Extensions**: Same hook system can support additional features

### Dependencies

- **React 18.2.0**: Core framework dependency
- **Material-UI v5.15.0**: Component library dependency  
- **Axios**: HTTP client library
- **React-Window**: Virtual scrolling performance optimization
- **React-Router-Dom**: Client-side routing
- **EP-0003 Hook System**: Existing hook infrastructure (BaseEventHook, HookManager)

### Integrated Hook System Implementation Details

**Backend Hook Implementation Pattern**
```python
class DashboardBroadcastHooks(BaseEventHook):
    """Extends existing EP-0003 hook system for dashboard broadcasting"""
    
    def __init__(self, dashboard_broadcaster):
        super().__init__("dashboard_broadcast_hook")
        self.broadcaster = dashboard_broadcaster
        self.update_service = DashboardUpdateService()
    
    async def execute(self, event_type: str, **kwargs):
        """Same signature as existing history hooks"""
        session_id = kwargs.get('session_id')
        if not session_id:
            return
            
        # Format hook data for dashboard
        dashboard_data = self.update_service.format_hook_event(event_type, **kwargs)
        
        # Broadcast via WebSocket
        if event_type.endswith('.post'):
            await self.broadcaster.broadcast_session_update(session_id, dashboard_data)

# Registration alongside existing hooks
def register_integrated_hooks():
    hook_manager = get_hook_manager()  # Uses existing EP-0003 infrastructure
    
    # Existing history hooks (unchanged)
    llm_history_hooks = LLMHooks()
    hook_manager.register_hook("llm.post", llm_history_hooks)
    
    # New dashboard hooks (same events, different actions)
    dashboard_broadcaster = get_dashboard_broadcaster()
    llm_dashboard_hooks = DashboardBroadcastHooks(dashboard_broadcaster)
    hook_manager.register_hook("llm.post", llm_dashboard_hooks)
    
    # Both execute concurrently!
```

**Frontend WebSocket Integration (Unchanged)**
```typescript
class MultiplexedWebSocketManager {
  // Same implementation as original design
  // Receives formatted messages from dashboard hooks
}
```

### Constraints

- **Browser Compatibility**: Modern browser requirement for performance features
- **Network Dependency**: Requires stable network connection for real-time features
- **Screen Size**: Optimized for desktop/tablet usage primarily
- **Hook System Dependency**: Requires existing EP-0003 hook infrastructure to be operational

## Documentation Requirements

### Code Documentation

- **Component Documentation**: JSDoc comments for all components and hooks
- **API Documentation**: Inline comments for API service methods
- **Type Documentation**: Comprehensive TypeScript interfaces and types

### API Documentation

- **Integration Guide**: How to connect dashboard to backend services
- **WebSocket Protocol**: Message format and connection handling documentation
- **Configuration Guide**: Environment variable and deployment configuration

---

## Design Review Checklist

### Architecture Review
- [x] Architecture is sound and scalable with proper separation of concerns
- [x] Components are well-defined with clear responsibilities and interfaces
- [x] Data flow is logical and efficient with proper state management
- [x] Integration points are well-defined with existing EP-0003 API
- [x] Security considerations are addressed with React best practices

### Implementation Review
- [x] Design is implementable with React 18.2.0 and Material-UI v5.15.0
- [x] Performance requirements can be met with virtual scrolling and optimization
- [x] Error handling is comprehensive with proper fallback mechanisms
- [x] Testing strategy is adequate with unit, integration, and e2e coverage
- [x] Monitoring and observability are addressed with client-side metrics

### Requirements Traceability
- [x] All functional requirements from requirements doc are addressed
- [x] All non-functional requirements (performance, security, usability) are met
- [x] Design decisions support SRE operational monitoring needs
- [x] Real-time WebSocket requirements are comprehensively designed
- [x] Success criteria can be met with this technical design

---

## Next Steps

After design approval:
1. **Begin Backend Implementation**: Start with Phase 1 backend WebSocket infrastructure
2. **Implement Integrated Hook System**: Create dashboard broadcast hooks extending existing EP-0003 hook system
3. **Create Implementation Plan**: `docs/enhancements/pending/EP-0004-dashboard-ui-implementation.md` 
4. **Backend Development**: Complete Phases 1-2 with integrated hook system before frontend work
5. **Frontend Development**: Initialize `dashboard/` directory structure after backend integration is functional

**Development Priority**: Backend WebSocket infrastructure must be completed first, followed by integrated hook system implementation as the foundation for all dashboard functionality.

**Key Integration Advantage**: The integrated hook system approach reduces backend complexity by leveraging existing EP-0003 infrastructure while ensuring data consistency between historical and real-time dashboard data.

**AI Prompt for Next Phase:**
```
Create an implementation plan using the template at docs/templates/ep-implementation-template.md for EP-0004 based on the approved integrated hook system design in this document and the requirements in EP-0004-dashboard-ui-requirements.md. Prioritize backend WebSocket implementation followed by integrated hook system as Phase 1-2 dependencies.
``` 