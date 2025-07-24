# EP-0004: Tarsy Dashboard UI for Alert History - Design Document

**Status:** Draft  
**Created:** 2025-01-19  
**Phase:** Technical Design
**Requirements Document:** `docs/enhancements/pending/EP-0004-dashboard-ui-requirements.md`
**Next Phase:** Implementation Plan

---

## Design Overview

This design creates a standalone React dashboard application (`dashboard/`) that provides SRE engineers with comprehensive visibility into alert processing history and real-time monitoring capabilities. The dashboard leverages the existing EP-0003 history service API and extends the proven technical patterns from the alert dev UI.

### Architecture Summary

The dashboard follows a modern React SPA architecture with Material-UI components, implementing a layered approach:
- **Presentation Layer**: React components with Material-UI theming
- **State Management Layer**: React hooks and context for local state management
- **Communication Layer**: Axios for REST API calls and WebSocket for real-time updates
- **Service Layer**: Abstracted API clients and WebSocket managers

### Key Design Principles

- **Separation of Concerns**: Dashboard operates independently from alert dev UI
- **Reusable Patterns**: Leverage proven patterns from existing alert dev UI
- **Real-time First**: WebSocket integration for live operational monitoring
- **Performance Conscious**: Efficient data loading and virtual scrolling for large datasets
- **Accessibility First**: WCAG 2.1 AA compliance built into component design

### Design Goals

- **Operational Excellence**: Provide comprehensive alert processing visibility
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
│                     Backend Services                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐  │
│  │  History API    │ │  WebSocket      │ │  Alert Dev UI   │  │
│  │  (EP-0003)      │ │  Service        │ │  (Unchanged)    │  │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

### Component Architecture

#### New Components

- **DashboardApp**: Main application component with routing and layout
- **SessionListView**: Paginated list of alert sessions with filtering controls
- **SessionDetailView**: Detailed session timeline with chronological interactions
- **FilterPanel**: Advanced filtering interface for sessions
- **TimelineVisualization**: Interactive timeline showing LLM and MCP interactions
- **RealTimeMonitor**: Live status display of currently processing alerts
- **SessionCard**: Reusable session summary card component
- **ErrorBoundary**: Application-wide error handling component

#### Modified Components

- **WebSocketManager**: Extended from alert dev UI to support dashboard-wide monitoring
- **APIClient**: Enhanced with history service endpoints and pagination support
- **ThemeProvider**: Shared Material-UI theme configuration

#### Component Interactions

```
DashboardApp
├── Router
    ├── SessionListView
    │   ├── FilterPanel
    │   ├── SessionCard[] (virtualized)
    │   └── RealTimeMonitor
    └── SessionDetailView
        ├── SessionHeader
        ├── TimelineVisualization
        └── InteractionDetails
```

### Data Flow Design

#### Data Flow Diagrams

**Session List Data Flow:**
```
User Filter Action → FilterPanel → APIClient → History API → SessionListView → SessionCard[]
                                            ↓
WebSocket Updates → WebSocketManager → RealTimeMonitor → Session Status Updates
```

**Session Detail Data Flow:**
```
Session Selection → Router → SessionDetailView → APIClient → History API → Timeline Data
                                              ↓
Individual WebSocket → WebSocketManager → Live Updates → Timeline Updates
```

#### Data Processing Steps

1. **Initial Load**: Fetch paginated session list with default filters
2. **Filter Application**: Apply user filters and re-fetch filtered results
3. **Real-time Updates**: Process WebSocket messages for live session status
4. **Session Detail**: Load detailed timeline data for selected session
5. **Timeline Rendering**: Process chronological data for timeline visualization
6. **Live Monitoring**: Continuously update active session statuses

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
WebSocketMessage {
  - type: 'session_update' | 'session_complete' | 'error' (message type)
  - session_id: string (affected session)
  - data: SessionUpdate | SessionComplete | ErrorMessage (payload)
  - timestamp: string (message timestamp)
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
- **Dashboard WebSocket**: `/ws/dashboard` (new endpoint needed in backend)
- **Session WebSocket**: `/ws/sessions/{session_id}` (existing from alert dev UI)
- **Connection Management**: Auto-reconnection with exponential backoff
- **Message Buffering**: Handle temporary connection losses

## User Interface Design

### UI Components

#### New UI Components

- **SessionGrid**: Virtualized grid component for large session lists
- **FilterChip**: Interactive filter tag components
- **StatusIndicator**: Color-coded status indicators with icons
- **TimelineChart**: SVG-based timeline visualization
- **DurationBadge**: Human-readable duration display component
- **SearchBar**: Debounced search input with suggestions
- **LoadingSkeletons**: Placeholder components during data loading

#### Modified UI Components

- **Layout**: Adapted from alert dev UI with dashboard-specific navigation
- **ErrorDisplay**: Enhanced error component with retry mechanisms
- **WebSocketStatus**: Connection status indicator for dashboard

### User Experience Flow

#### User Journey

1. **Dashboard Load**: User navigates to dashboard, sees loading skeleton
2. **Session List Display**: Paginated list loads with default filters applied
3. **Filter Application**: User applies filters, list updates with loading states
4. **Real-time Updates**: Live session status updates appear automatically
5. **Session Selection**: User clicks session, detail view loads with timeline
6. **Timeline Exploration**: User scrolls through chronological interactions
7. **Navigation**: User returns to list or selects different session

#### User Interface Mockups

**Session List View:**
```
┌─────────────────────────────────────────────────────────────────┐
│ [Tarsy Dashboard]                              [Real-time: ●●●] │
├─────────────────────────────────────────────────────────────────┤
│ [Search: ___________] [Filters: Status ▼ Agent ▼ Type ▼ Date] │
├─────────────────────────────────────────────────────────────────┤
│ Session Cards (Virtualized):                                   │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ [●] kubernetes | NamespaceTerminating | 2m 34s ago        │   │
│ │     Completed in 1.2s | View Details →                   │   │
│ └───────────────────────────────────────────────────────────┘   │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ [⚠] kubernetes | PodCrashLooping | 5m 12s ago            │   │
│ │     Failed after 15.3s | Error: timeout | View Details → │   │
│ └───────────────────────────────────────────────────────────┘   │
│ [Load More] [Page 1 of 25]                                     │
└─────────────────────────────────────────────────────────────────┘
```

**Session Detail View:**
```
┌─────────────────────────────────────────────────────────────────┐
│ [← Back] Session Details | kubernetes | NamespaceTerminating   │
├─────────────────────────────────────────────────────────────────┤
│ Status: Completed | Duration: 1.234s | Started: 2m 34s ago     │
├─────────────────────────────────────────────────────────────────┤
│ Timeline:                                                       │
│ 00:00.000 ├─ Alert Received                                    │
│ 00:00.045 ├─ [LLM] Initial Analysis (234ms)                   │
│ 00:00.279 ├─ [MCP] Kubernetes Query (156ms)                   │
│ 00:00.435 ├─ [LLM] Response Generation (799ms)                │
│ 00:01.234 └─ Alert Processing Complete                         │
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

### Deployment Considerations

#### Deployment Strategy

- **Build Process**: Standard React build with webpack optimization
- **Static Hosting**: Deployable to static hosting (S3, Netlify, etc.)
- **Docker Support**: Optional containerization with nginx
- **CI/CD Integration**: Build and test pipeline integration

#### Rollback Strategy

- **Version Tagging**: Git-based version management
- **Deployment Slots**: Blue-green deployment support
- **Feature Flags**: Runtime feature toggling capability
- **Graceful Degradation**: Backward compatible API usage

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

### Monitoring Requirements

Dashboard monitoring focuses on client-side performance and user experience:
- **Page Load Performance**: Time to interactive and first contentful paint
- **API Response Times**: Client-side API call duration tracking
- **Error Rates**: JavaScript errors and API failure rates
- **User Interactions**: Feature usage and workflow completion rates

### Metrics to Track

- **Performance Metrics**: Page load time < 2s, API response time < 500ms
- **Error Metrics**: JavaScript error rate < 0.1%, API error rate < 5%
- **Usage Metrics**: Active users, session duration, feature adoption rates
- **Availability Metrics**: Dashboard uptime and accessibility

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

### Alerting Strategy

- **Error Rate Alerts**: Alert on high JavaScript error rates
- **Performance Alerts**: Alert on degraded performance metrics
- **Availability Alerts**: Alert on dashboard accessibility issues
- **Usage Alerts**: Alert on significant drops in usage metrics

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
4. **WebSocket Integration**: Implement real-time update mechanisms
5. **Production Deployment**: Deploy as standalone application

## Alternative Designs Considered

### Alternative 1: Extend Alert Dev UI

- **Description**: Add dashboard features to existing alert dev UI application
- **Pros**: Single application maintenance, shared components and configuration
- **Cons**: Mixing development and operational concerns, potential performance impact
- **Decision**: Rejected - Requirements explicitly specify separate applications for different user personas

### Alternative 2: Server-Side Rendered Dashboard

- **Description**: Use Next.js or similar SSR framework for dashboard
- **Pros**: Better SEO, faster initial page loads, simplified deployment
- **Cons**: Additional complexity, different patterns from existing codebase
- **Decision**: Rejected - Consistency with existing React SPA patterns more valuable

### Alternative 3: Native Desktop Application

- **Description**: Build dashboard as Electron or Tauri desktop application
- **Pros**: Native performance, offline capabilities, system integration
- **Cons**: Additional deployment complexity, platform-specific testing
- **Decision**: Rejected - Web-based solution meets requirements and simplifies deployment

## Implementation Considerations

### Technical Debt

- **Shared Code**: Potential duplication with alert dev UI components
- **API Client**: Shared API client library could reduce duplication
- **Testing Infrastructure**: Shared testing utilities and mock data

### Dependencies

- **React 18.2.0**: Core framework dependency
- **Material-UI v5.15.0**: Component library dependency  
- **Axios**: HTTP client library
- **React-Window**: Virtual scrolling performance optimization
- **React-Router-Dom**: Client-side routing

### Constraints

- **Browser Compatibility**: Modern browser requirement for performance features
- **Network Dependency**: Requires stable network connection for real-time features
- **Screen Size**: Optimized for desktop/tablet usage primarily

## Documentation Requirements

### Code Documentation

- **Component Documentation**: JSDoc comments for all components and hooks
- **API Documentation**: Inline comments for API service methods
- **Type Documentation**: Comprehensive TypeScript interfaces and types

### API Documentation

- **Integration Guide**: How to connect dashboard to backend services
- **WebSocket Protocol**: Message format and connection handling documentation
- **Configuration Guide**: Environment variable and deployment configuration

### User Documentation

- **User Guide**: SRE engineer guide for dashboard usage
- **Feature Documentation**: Detailed feature descriptions and workflows
- **Troubleshooting Guide**: Common issues and resolution steps

### Architecture Documentation

- **Component Architecture**: Component hierarchy and interaction patterns
- **Data Flow Documentation**: State management and data flow patterns
- **Performance Guide**: Performance optimization and monitoring practices

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
1. Create Implementation Plan: `docs/enhancements/pending/EP-0004-dashboard-ui-implementation.md`
2. Reference this design document in the implementation phase
3. Ensure implementation plan addresses all design elements and component development

**AI Prompt for Next Phase:**
```
Create an implementation plan using the template at docs/templates/ep-implementation-template.md for EP-0004 based on the approved design in this document and the requirements in EP-0004-dashboard-ui-requirements.md.
``` 