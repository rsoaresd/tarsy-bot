# EP-0004: Tarsy Dashboard UI for Alert History - Implementation Plan

**Status:** Approved  
**Created:** 2025-01-19  
**Phase:** Implementation Approved  
**Last Updated:** 2025-01-25 (Backend API endpoints implemented)
**Requirements Document:** `docs/enhancements/approved/EP-0004-dashboard-ui-requirements.md`
**Design Document:** `docs/enhancements/approved/EP-0004-dashboard-ui-design.md`

---

## Implementation Overview

### Implementation Summary
This implementation creates a standalone React dashboard application (`dashboard/`) that provides SRE engineers with comprehensive read-only observability into alert processing workflows. The dashboard will be implemented as a sibling directory to the existing `alert-dev-ui/`, maintaining complete separation between the two applications. The implementation follows a backend-first approach with **integrated hook system architecture**, leveraging the existing EP-0003 hook infrastructure to provide real-time dashboard updates through the same event pipeline used for history logging.

### Implementation Goals
- Create independent SRE dashboard application for operational monitoring
- Implement multiplexed WebSocket system for real-time updates
- Provide comprehensive read-only visibility into alert processing workflows
- Support efficient filtering and analysis of 1000+ alert sessions
- Maintain clear separation between active and historical alert processing states

### Implementation Strategy
**CRITICAL**: This is a **New Application Development with Integrated Hook System** approach:
- **New Standalone Application**: Dashboard implemented as independent React SPA in `dashboard/` directory
- **Integrated Hook System**: Dashboard broadcast hooks work alongside existing EP-0003 history hooks using the same event pipeline
- **Backend Extensions**: New WebSocket endpoints and dashboard-specific services added to existing backend
- **Hook System Reuse**: Leverages existing LLM/MCP hook infrastructure for event capture
- **API Integration**: Consumes existing EP-0003 history service without modifications
- **Independent Deployment**: Dashboard can be built and deployed separately from alert-dev-ui

### Implementation Constraints
- Must maintain existing EP-0003 API endpoint contracts without breaking changes
- Backend WebSocket infrastructure must be completed before frontend real-time features
- Dashboard must operate independently from existing alert-dev-ui application
- Must support browser connection limits through multiplexed WebSocket architecture
- Performance requirements: Handle 1000+ sessions with responsive UI interactions
- Must not modify existing EP-0003 hook system behavior or history service functionality

### Integrated Hook System Benefits
The integrated approach provides significant advantages over separate event systems:
- **Single Event Source**: Both history logging and dashboard broadcasting use the same LLM/MCP interaction events
- **Consistent Data**: Same timestamps, session IDs, and interaction context for historical and real-time data
- **No Service Modifications**: No changes needed to existing LLM/MCP clients or history service
- **Concurrent Execution**: Dashboard hooks run alongside history hooks without performance impact
- **Reduced Implementation Complexity**: Leverages existing EP-0003 hook infrastructure (`BaseEventHook`, `HookManager`)
- **Data Consistency Guarantee**: Same event timing and session context as history service
- **Maintainability**: Single event pipeline reduces complexity and potential inconsistencies
- **Future Extensions**: Same hook system can support additional features (monitoring, analytics, etc.)

### Integrated Architecture Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM/MCP Interactions                         │
│  ┌─────────────────┐    ┌─────────────────────────────────────┐ │
│  │ LLM Client      │    │ MCP Client                          │ │
│  │ (Existing)      │    │ (Existing)                          │ │
│  └─────────────────┘    └─────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HookContext (Existing)
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                 Shared Hook System (EP-0003)                    │
│  ┌─────────────────┐    ┌─────────────────────────────────────┐ │
│  │ History Hooks   │    │ Dashboard Hooks                     │ │
│  │ (Existing)      │    │ (NEW - EP-0004)                     │ │
│  │                 │    │                                     │ │
│  └─────────────────┘    └─────────────────────────────────────┘ │
└─────────────────────────┬───────────────────┬───────────────────┘
                          │                   │
          ┌───────────────↓                   ↓─────────────────┐
          │                                                     │
┌─────────────────┐                                ┌─────────────────┐
│ History Service │                                │ Dashboard       │
│ Database        │                                │ WebSocket       │
│ (Existing)      │                                │ Broadcasting    │
└─────────────────┘                                │ (NEW)           │
                                                   └─────────────────┘
                                                            │
                                                            ↓
                                                   ┌─────────────────┐
                                                   │ Dashboard       │
                                                   │ React App       │
                                                   │ (NEW)           │
                                                   └─────────────────┘
```

## UI/UX Design Requirements

### User Interface Specifications

#### Dashboard UI Mockups and Layout

**Reference**: Complete UI mockups are available in `docs/enhancements/pending/EP-0004-dashboard-ui-design.md` (lines 540-650)

**Main Dashboard Layout Requirements:**
- **Split-panel design**: Active alerts (top), Historical sessions (bottom)
- **Auto-refresh indicator**: Visual indicator showing real-time update status
- **Status counters**: Live counters for Processing/Failed/Pending alerts
- **Responsive breakpoints**: Desktop (1200px+), Tablet (768px+), Mobile (320px+)

#### Component Visual Specifications

**ActiveAlertsPanel Requirements:**
- **Status color coding**: 🔴 Failed (red), 🟡 Processing (yellow), 🟢 Completing (green)
- **Progress indicators**: Animated progress bars with percentage and ETA
- **Expandable cards**: Click to expand details, keyboard navigation support
- **Actions**: "View Details", "Copy Error", "Watch" buttons with consistent styling
- **Real-time updates**: Smooth animations for status changes and progress updates

**HistoricalSessionsList Requirements:**
- **Virtual scrolling**: Handle 1000+ items with react-window
- **Quick filter buttons**: Preset filters with badge counts [🔴Failed(5)][🟡Timeout(2)][🟢Success(245)]
- **Search functionality**: Debounced search with autocomplete suggestions
- **Table layout**: Sortable columns with clear headers and alignment
- **Pagination controls**: Previous/Next with page numbers and items per page selector

**SessionDetailPage Requirements:**
- **Timeline visualization**: SVG-based timeline with chronological markers
- **Interactive elements**: Clickable timeline points showing interaction details
- **Copy functionality**: Copy buttons for individual interactions and full timeline
- **Navigation**: Breadcrumb navigation back to dashboard
- **Real-time updates**: Live timeline updates for active sessions with smooth animations

#### Typography and Visual Design

**Color Palette:**
- **Primary**: Material-UI primary colors (blue theme)
- **Status Colors**: Success (#4CAF50), Warning (#FF9800), Error (#F44336), Info (#2196F3)
- **Background**: Light gray (#FAFAFA) with white content cards
- **Text**: Dark gray (#333333) for primary text, medium gray (#666666) for secondary

**Typography Scale:**
- **Headers**: Roboto 24px/20px/18px (H1/H2/H3)
- **Body**: Roboto 16px/14px (primary/secondary)
- **Code**: Roboto Mono 14px for timestamps and technical details
- **Captions**: Roboto 12px for metadata and helper text

**Spacing System:**
- **Base unit**: 8px grid system
- **Component padding**: 16px standard, 8px compact
- **Card margins**: 16px between cards, 24px section margins
- **Button spacing**: 8px between buttons, 12px padding inside buttons

### User Experience Requirements

#### User Journey Workflows 

**Primary Workflow: Active Alert Monitoring**
1. **Dashboard Entry**: User lands on dashboard, immediately sees active alerts status
2. **Status Overview**: User scans active alerts summary counters (3 Processing, 2 Failed, 0 Pending)
3. **Alert Investigation**: User clicks on failed alert to see error details in expanded view
4. **Detail Navigation**: User clicks "View Details" to navigate to full session timeline
5. **Real-time Monitoring**: User watches active session timeline update in real-time
6. **Action Taking**: User copies error details or timeline for external documentation
7. **Return Navigation**: User navigates back to dashboard to monitor other alerts

**Secondary Workflow: Historical Analysis**
1. **Filter Application**: User applies quick filters to find specific alert patterns
2. **Search Refinement**: User uses search to find alerts by specific criteria
3. **Session Selection**: User clicks on historical session to view complete timeline
4. **Timeline Analysis**: User reviews chronological LLM/MCP interactions
5. **Data Export**: User exports timeline data for post-incident analysis
6. **Pattern Recognition**: User identifies recurring issues from historical data

#### Accessibility Requirements (WCAG 2.1 AA)

**Keyboard Navigation:**
- **Tab order**: Logical tab sequence through all interactive elements
- **Focus indicators**: Clear visual focus indicators on all interactive elements
- **Keyboard shortcuts**: Arrow keys for timeline navigation, Enter/Space for activation
- **Skip links**: Skip to main content and skip to navigation options

**Screen Reader Support:**
- **ARIA labels**: Comprehensive ARIA labels for all interactive elements
- **Live regions**: ARIA live regions for real-time status updates
- **Semantic HTML**: Proper heading hierarchy and semantic markup
- **Alt text**: Descriptive alt text for all status icons and visual indicators

**Visual Accessibility:**
- **Color contrast**: Minimum 4.5:1 contrast ratio for all text
- **Color independence**: Status information conveyed through icons and text, not just color
- **Font scaling**: Support for browser zoom up to 200%
- **Focus management**: Clear focus management for modal dialogs and navigation

#### Responsive Design Requirements

**Desktop (1200px+):**
- **Full two-panel layout**: Active alerts and historical sessions side-by-side or stacked
- **Extended timeline**: Full horizontal timeline with detailed interaction points
- **Expanded tables**: Full table columns with sorting and filtering controls

**Tablet (768px-1199px):**
- **Stacked layout**: Active alerts above historical sessions
- **Collapsed navigation**: Hamburger menu for secondary navigation
- **Touch-friendly buttons**: Minimum 44px touch targets for all interactive elements

**Mobile (320px-767px):**
- **Single column**: Full-width cards with vertical stacking
- **Swipe navigation**: Swipe gestures for session detail navigation
- **Bottom navigation**: Fixed bottom navigation for primary actions

#### Performance Requirements

**Loading Performance:**
- **Initial render**: Dashboard visible within 2 seconds on 3G connection
- **Skeleton loading**: Loading skeletons for all data-dependent components
- **Progressive loading**: Load critical data first, secondary data asynchronously

**Real-time Performance:**
- **Update latency**: Real-time updates visible within 500ms of WebSocket message
- **Smooth animations**: 60fps animations for progress bars and status changes
- **Memory management**: Efficient handling of large session lists with virtualization

### Implementation Validation Requirements

#### User Testing Criteria
- [ ] **Task completion**: Users can complete primary workflows without assistance
- [ ] **Error recovery**: Users can recover from common error scenarios
- [ ] **Accessibility**: All workflows completable using only keyboard
- [ ] **Performance**: No perceived lag in real-time updates
- [ ] **Visual clarity**: Status information clearly understood by SRE engineers

#### UI Component Testing
- [ ] **Visual regression**: Automated screenshot comparison for all components
- [ ] **Interaction testing**: Automated testing of all user interactions
- [ ] **Responsive testing**: Component behavior across all breakpoints
- [ ] **Accessibility testing**: Automated accessibility testing with axe-core

### Success Criteria
- [ ] SRE engineers can monitor active alert processing in real-time with progress indicators
- [ ] Historical alert analysis supports efficient filtering of 1000+ sessions with virtualized scrolling
- [ ] Single multiplexed WebSocket connection handles all real-time communications without browser limits
- [ ] Dashboard loads and operates independently from alert-dev-ui application
- [ ] Session detail navigation works uniformly for both active and historical alerts
- [ ] Real-time updates appear within 500ms of backend events

### Backward Compatibility Guidelines
**External API Compatibility (Always Required):**
- Maintain existing EP-0003 REST endpoint paths, methods, and response formats
- Preserve existing WebSocket communication contracts (if any)
- Keep same backend configuration file formats
- Maintain existing alert-dev-ui functionality unchanged

**Internal Compatibility (NOT Required for New Applications):**
- New dashboard components have no legacy compatibility requirements
- New WebSocket endpoints have no backward compatibility constraints
- New service classes can use modern architectural patterns
- Dashboard directory structure is entirely new

## Phase 1: Backend WebSocket Infrastructure

### Phase 1 Overview
**Dependencies:** None - foundational phase
**Goal:** Implement multiplexed WebSocket system for dashboard real-time communications

#### Step 1.1: WebSocket Endpoint Implementation
**Goal:** Create new dashboard WebSocket endpoint with connection management
**Files to Create/Modify:**
- `backend/tarsy/services/websocket_manager.py` (modify - add dashboard methods)
- `backend/tarsy/services/dashboard_connection_manager.py` (new)
- `backend/tarsy/main.py` (modify - add dashboard WebSocket endpoint)

**AI Prompt:** `Implement Step 1.1 of EP-0004: Create dashboard WebSocket endpoint /ws/dashboard/{user_id} with basic connection management and subscription system`

**Tasks:**
- [ ] Add `/ws/dashboard/{user_id}` WebSocket endpoint to FastAPI application
- [ ] Create DashboardConnectionManager class for connection tracking
- [ ] Implement basic message routing infrastructure for subscription channels
- [ ] Add connection lifecycle management (connect, disconnect, cleanup)
- [ ] Create subscription state tracking per connection

**Dependencies:**
- Existing WebSocket infrastructure in websocket_manager.py
- FastAPI application structure

**Validation Criteria:**
- [ ] WebSocket endpoint accepts connections at `/ws/dashboard/{user_id}`
- [ ] Connection manager tracks active dashboard connections
- [ ] Basic message routing system handles subscribe/unsubscribe messages
- [ ] Connection cleanup occurs properly on disconnect
- [ ] Multiple concurrent connections are supported

**Success Check:**
```bash
# Start backend server
cd backend && python -m tarsy.main

# Test WebSocket connection (separate terminal)
wscat -c ws://localhost:8000/ws/dashboard/test_user

# Send subscription message
{"type": "subscribe", "channel": "dashboard_updates"}

# Verify connection tracking in logs
grep "dashboard_connection" backend/logs/app.log
```

#### Step 1.2: Subscription Channel System
**Goal:** Implement subscription management for dashboard_updates, session_id, and system_health channels
**Files to Create/Modify:**
- `backend/tarsy/services/subscription_manager.py` (new)
- `backend/tarsy/services/dashboard_connection_manager.py` (modify - add subscription tracking)
- `backend/tarsy/models/websocket_models.py` (new)

**AI Prompt:** `Implement Step 1.2 of EP-0004: Create subscription channel system supporting dashboard_updates, session_{id}, and system_health channels with message routing`

**Tasks:**
- [ ] Create SubscriptionManager class for channel management
- [ ] Implement dashboard_updates channel subscription logic
- [ ] Implement session_{id} channel subscription logic
- [ ] Implement system_health channel subscription logic
- [ ] Add message routing based on subscription channels
- [ ] Create WebSocket message models for type safety

**Dependencies:**
- Step 1.1 must be complete
- Dashboard connection manager functionality

**Validation Criteria:**
- [ ] Clients can subscribe to dashboard_updates channel
- [ ] Clients can subscribe to specific session_{id} channels
- [ ] Clients can subscribe to system_health channel
- [ ] Message routing delivers messages only to subscribed channels
- [ ] Subscription state persists during connection lifetime
- [ ] Unsubscribe functionality removes channel subscriptions

**Success Check:**
```bash
# Test subscription system
wscat -c ws://localhost:8000/ws/dashboard/test_user

# Subscribe to dashboard updates
{"type": "subscribe", "channel": "dashboard_updates"}

# Subscribe to specific session
{"type": "subscribe", "channel": "session_12345"}

# Verify subscription tracking
grep "subscription_added" backend/logs/app.log
```

#### Step 1.3: Message Broadcasting Infrastructure
**Goal:** Create broadcasting system for sending updates to subscribed dashboard clients
**Files to Create/Modify:**
- `backend/tarsy/services/dashboard_broadcaster.py` (new)
- `backend/tarsy/services/dashboard_connection_manager.py` (modify - add broadcasting methods)
- `backend/tarsy/models/dashboard_models.py` (new)

**AI Prompt:** `Implement Step 1.3 of EP-0004: Create dashboard broadcasting system for sending filtered updates to subscribed clients with message batching`

**Tasks:**
- [ ] Create DashboardBroadcaster class for message distribution
- [ ] Implement filtered broadcasting for dashboard_updates channel
- [ ] Add session-specific broadcasting for session_{id} channels
- [ ] Create dashboard update message models
- [ ] Implement message batching and throttling for performance

**Dependencies:**
- Step 1.2 must be complete
- Subscription management functionality

**Validation Criteria:**
- [ ] Broadcaster can send messages to dashboard_updates subscribers
- [ ] Broadcaster can send messages to specific session subscribers
- [ ] Message filtering works correctly based on subscription criteria
- [ ] Message batching prevents flooding of client connections
- [ ] Broadcasting performance handles multiple concurrent subscribers

**Success Check:**
```bash
# Test broadcasting system
python backend/tests/test_dashboard_broadcasting.py

# Verify message delivery
grep "broadcast_sent" backend/logs/app.log

# Check message batching
grep "batch_processed" backend/logs/app.log
```

### Phase 1 Completion Criteria
- [ ] Dashboard WebSocket endpoint operational with connection management
- [ ] Subscription system supports dashboard_updates, session_{id}, and system_health channels
- [ ] Broadcasting infrastructure delivers messages to correct subscribers
- [ ] Multiple concurrent dashboard connections supported
- [ ] WebSocket connection cleanup prevents resource leaks

## Phase 2: Backend Service Integration

### Phase 2 Overview
**Dependencies:** Phase 1 completion
**Goal:** Integrate WebSocket system with existing EP-0003 hook system for real-time events

#### Step 2.1: Dashboard Broadcast Hooks Integration
**Goal:** Create dashboard broadcast hooks that work alongside existing EP-0003 history hooks
**Files to Create/Modify:**
- `backend/tarsy/hooks/dashboard_hooks.py` (new)
- `backend/tarsy/services/dashboard_broadcaster.py` (modify - add hook integration)
- `backend/tarsy/hooks/history_hooks.py` (modify - add registration integration)

**AI Prompt:** `Implement Step 2.1 of EP-0004: Create dashboard broadcast hooks extending BaseEventHook that work alongside existing EP-0003 history hooks using the same event pipeline for LLM and MCP interactions`

**Tasks:**
- [ ] Create DashboardBroadcastHooks class extending BaseEventHook
- [ ] Implement LLM interaction broadcasting in dashboard hooks
- [ ] Implement MCP communication broadcasting in dashboard hooks
- [ ] Integrate dashboard broadcaster with hook system
- [ ] Register dashboard hooks alongside existing history hooks

**Dependencies:**
- Phase 1 completion
- Existing EP-0003 hook system functionality

**Validation Criteria:**
- [ ] Dashboard hooks receive same events as history hooks
- [ ] LLM interactions trigger dashboard_updates broadcasts
- [ ] MCP communications trigger dashboard_updates broadcasts
- [ ] Session timeline updates broadcast in real-time to dashboard
- [ ] Dashboard broadcasting does not impact existing history service performance

**Success Check:**
```bash
# Submit test alert and monitor dashboard events
curl -X POST http://localhost:8000/api/v1/alerts -d '{"alert": "test"}'

# Verify dashboard hook execution
grep "dashboard_broadcast_hook" backend/logs/app.log

# Check WebSocket broadcasts
grep "broadcast_sent" backend/logs/app.log
```

#### Step 2.2: Hook Registration Integration
**Goal:** Integrate dashboard hooks with existing EP-0003 hook registration system
**Files to Create/Modify:**
- `backend/tarsy/hooks/__init__.py` (modify - add dashboard hooks exports)
- `backend/tarsy/main.py` (modify - register dashboard hooks at startup)
- `backend/tarsy/hooks/history_hooks.py` (modify - update registration function)

**AI Prompt:** `Implement Step 2.2 of EP-0004: Integrate dashboard hooks with existing EP-0003 hook registration system to enable concurrent hook execution for both history logging and dashboard broadcasting`

**Tasks:**
- [ ] Update hook package exports to include dashboard hooks
- [ ] Create integrated hook registration function
- [ ] Register dashboard hooks alongside history hooks at application startup
- [ ] Ensure concurrent execution of both hook types
- [ ] Add hook status monitoring for dashboard broadcasting

**Dependencies:**
- Step 2.1 must be complete
- Existing hook registration system

**Validation Criteria:**
- [ ] Dashboard hooks register successfully at application startup
- [ ] Both history and dashboard hooks execute concurrently for same events
- [ ] Hook registration does not impact application startup time
- [ ] Hook execution statistics include dashboard hooks
- [ ] Dashboard hook failures do not affect history hooks

**Success Check:**
```bash
# Check hook registration at startup
python -m tarsy.main

# Verify both hook types registered
grep "hook.*registered" backend/logs/app.log

# Test concurrent execution
curl -X POST http://localhost:8000/api/v1/alerts -d '{"alert": "test"}'
grep -E "(llm_history_hook|dashboard_broadcast_hook)" backend/logs/app.log
```

#### Step 2.3: Dashboard Update Service Integration
**Goal:** Create dashboard update service that formats hook data for WebSocket broadcasting
**Files to Create/Modify:**
- `backend/tarsy/services/dashboard_update_service.py` (new)
- `backend/tarsy/hooks/dashboard_hooks.py` (modify - add update service integration)
- `backend/tarsy/models/dashboard_models.py` (modify - add formatted message models)

**AI Prompt:** `Implement Step 2.3 of EP-0004: Create dashboard update service that formats hook event data into WebSocket messages with intelligent batching and subscription filtering`

**Tasks:**
- [ ] Create DashboardUpdateService for message formatting
- [ ] Implement hook data transformation for dashboard messages
- [ ] Add session status tracking for dashboard summaries
- [ ] Create update batching logic to prevent client flooding
- [ ] Implement subscription-based filtering for targeted updates

**Dependencies:**
- Step 2.2 must be complete
- Dashboard broadcasting infrastructure

**Validation Criteria:**
- [ ] Hook events are properly formatted for dashboard consumption
- [ ] Update batching prevents excessive WebSocket message frequency
- [ ] Session summaries include real-time status information
- [ ] Subscription filters work correctly for targeted updates
- [ ] Update service performance handles high interaction volumes

**Success Check:**
```bash
# Test dashboard updates from hook events
wscat -c ws://localhost:8000/ws/dashboard/test_user
{"type": "subscribe", "channel": "dashboard_updates"}

# Trigger LLM interaction and verify dashboard update
curl -X POST http://localhost:8000/api/v1/alerts -d '{"alert": "test"}'

# Verify formatted messages
grep "dashboard_update_formatted" backend/logs/app.log
```

### Phase 2 Completion Criteria
- [ ] Dashboard hooks execute alongside history hooks using shared event pipeline
- [ ] Hook registration system includes both history and dashboard hooks
- [ ] Dashboard update service formats hook events for WebSocket broadcasting
- [ ] Concurrent hook execution maintains existing EP-0003 performance
- [ ] Real-time updates flow from hook events to dashboard clients

## Phase 2.5: Dashboard API Endpoints

### Phase 2.5 Overview
**Dependencies:** Phase 2 completion
**Goal:** Implement dashboard-specific REST API endpoints for metrics, active sessions, and filter options

#### Step 2.5.1: Dashboard API Endpoints Implementation
**Goal:** Create new REST API endpoints for dashboard-specific data
**Files to Create/Modify:**
- `backend/tarsy/controllers/history_controller.py` (modify - add dashboard endpoints)
- `backend/tarsy/services/history_service.py` (modify - add dashboard methods)
- `backend/tarsy/repositories/history_repository.py` (modify - add dashboard queries)

**AI Prompt:** `Implement Step 2.5.1 of EP-0004: Create dashboard-specific REST API endpoints with proper database queries for metrics, active sessions, and filter options`

**Tasks:**
- [x] Add `GET /api/v1/history/metrics` endpoint for dashboard overview metrics
- [x] Add `GET /api/v1/history/active-sessions` endpoint for currently processing sessions
- [x] Add `GET /api/v1/history/filter-options` endpoint for dynamic filter options
- [x] Add `GET /api/v1/history/sessions/{session_id}/export` endpoint for session data export (JSON/CSV)
- [x] Add `GET /api/v1/history/search` endpoint for multi-field session search
- [x] Implement `HistoryService.get_dashboard_metrics()` with session counts and statistics
- [x] Implement `HistoryService.get_filter_options()` with database-driven filter options
- [x] Implement `HistoryService.export_session_data()` with timeline reconstruction and format handling
- [x] Implement `HistoryService.search_sessions()` with multi-field search coordination
- [x] Create `HistoryRepository.get_dashboard_metrics()` with optimized database queries
- [x] Create `HistoryRepository.get_filter_options()` with distinct value queries
- [x] Create `HistoryRepository.export_session_data()` with complete session data retrieval
- [x] Create `HistoryRepository.search_sessions()` with SQLite full-text search across multiple fields
- [x] Add comprehensive error handling with graceful fallbacks

**Dependencies:**
- Existing EP-0003 history service and repository infrastructure
- Database models for AlertSession, LLMInteraction, MCPCommunication

**Validation Criteria:**
- [x] `/api/v1/history/metrics` returns session counts, error rates, and interaction statistics
- [x] `/api/v1/history/active-sessions` returns currently processing sessions with real-time status
- [x] `/api/v1/history/filter-options` returns dynamic filter options based on actual data
- [x] `/api/v1/history/sessions/{session_id}/export` supports both JSON and CSV export formats
- [x] `/api/v1/history/search` performs multi-field search with query parameter and result limiting
- [x] All endpoints handle errors gracefully with appropriate HTTP status codes
- [x] Database queries are optimized using indexed fields and COUNT aggregations

**Success Check:**
```bash
# Test metrics endpoint
curl http://localhost:8000/api/v1/history/metrics

# Test active sessions endpoint
curl http://localhost:8000/api/v1/history/active-sessions

# Test filter options endpoint
curl http://localhost:8000/api/v1/history/filter-options

# Test export endpoint (JSON format)
curl "http://localhost:8000/api/v1/history/sessions/{session_id}/export?format=json"

# Test export endpoint (CSV format)
curl "http://localhost:8000/api/v1/history/sessions/{session_id}/export?format=csv"

# Test search endpoint
curl "http://localhost:8000/api/v1/history/search?q=namespace&limit=5"

# Verify response formats match frontend expectations
```

#### Step 2.5.2: API Testing and Validation
**Goal:** Create comprehensive tests for dashboard API endpoints
**Files to Create/Modify:**
- `backend/tests/unit/controllers/test_history_controller.py` (modify - add dashboard endpoint tests)
- `backend/tests/unit/services/test_history_service.py` (modify - add dashboard method tests)
- `backend/tests/unit/repositories/test_history_repository.py` (modify - add dashboard query tests)

**AI Prompt:** `Implement Step 2.5.2 of EP-0004: Create comprehensive test suite for dashboard API endpoints covering success cases, error scenarios, and edge cases`

**Tasks:**
- [x] Create controller tests for all dashboard endpoints (success and error cases)
- [x] Create service tests for dashboard methods with mocked repositories
- [x] Create repository tests for dashboard queries with real database operations
- [x] Create comprehensive export and search endpoint tests (8 controller tests)
- [x] Create export and search service method tests (9 service tests)
- [x] Create export and search repository tests (8 repository tests)
- [x] Test error handling and graceful degradation scenarios
- [x] Validate response formats and data structures (JSON/CSV export, search results)
- [x] Test database model compliance and constraint validation

**Dependencies:**
- Step 2.5.1 completion
- Existing test infrastructure and fixtures

**Validation Criteria:**
- [x] All dashboard endpoints have comprehensive test coverage (25 new tests total)
- [x] Tests cover success paths, error scenarios, and edge cases
- [x] Database queries are tested with realistic data scenarios
- [x] Export functionality tested for both JSON and CSV formats with proper headers
- [x] Search functionality tested with multi-field queries and JSON field extraction
- [x] All tests pass consistently with 100% success rate

**Success Check:**
```bash
# Run all dashboard endpoint tests
cd backend && python -m pytest tests/unit/controllers/test_history_controller.py::TestExportAndSearchEndpoints -v

# Run service layer tests
cd backend && python -m pytest tests/unit/services/test_history_service.py::TestExportAndSearchMethods -v

# Run repository layer tests
cd backend && python -m pytest tests/unit/repositories/test_history_repository.py -k "test_export_session_data or test_search_sessions" -v

# Run all new dashboard tests together
cd backend && python -m pytest tests/unit/controllers/test_history_controller.py::TestExportAndSearchEndpoints tests/unit/services/test_history_service.py::TestExportAndSearchMethods -v

# Verify all tests pass
echo "All dashboard API tests should pass"
```

### Phase 2.5 Completion Criteria
- [x] Dashboard API endpoints return proper data with optimized database queries
- [x] All endpoints handle errors gracefully with appropriate fallbacks
- [x] Comprehensive test coverage validates functionality and performance (25 new tests, 100% pass rate)
- [x] API responses match frontend data structure requirements
- [x] Route conflicts resolved (active-sessions vs sessions/{id})
- [x] Export functionality implemented with JSON/CSV format support and proper streaming responses
- [x] Search functionality implemented with multi-field queries and JSON field extraction
- [x] Database model compliance ensured with proper required field handling

## Phase 3: Frontend Dashboard Application

### Phase 3 Overview
**Dependencies:** Phase 2.5 completion
**Goal:** Create standalone React dashboard application with real-time capabilities

#### Step 3.1: Dashboard Application Structure
**Goal:** Initialize React dashboard application with routing and basic layout
**Files to Create/Modify:**
- `dashboard/package.json` (new)
- `dashboard/tsconfig.json` (new)
- `dashboard/src/App.tsx` (new)
- `dashboard/src/index.tsx` (new)
- `dashboard/src/components/DashboardLayout.tsx` (new)
- `dashboard/public/index.html` (new)

**AI Prompt:** `Implement Step 3.1 of EP-0004: Initialize React dashboard application structure with routing, Material-UI theme, and basic layout components following the UI/UX specifications in the implementation plan UI section`

**Tasks:**
- [ ] Create dashboard directory structure as sibling to alert-dev-ui
- [ ] Initialize React application with TypeScript and Material-UI
- [ ] Set up routing for dashboard view and session detail pages
- [ ] Create basic dashboard layout with navigation following responsive design requirements
- [ ] Configure Material-UI theme with specified color palette (primary blue, status colors)
- [ ] Implement typography scale (Roboto font family with specified sizes)
- [ ] Set up 8px grid spacing system and component padding standards

**Dependencies:**
- Phase 2 completion
- Node.js and npm/yarn environment

**Validation Criteria:**
- [ ] Dashboard application starts successfully on development server
- [ ] Routing navigates between dashboard and session detail views
- [ ] Material-UI theme renders correctly across components
- [ ] Application structure follows React best practices
- [ ] Dashboard operates independently from alert-dev-ui

**Success Check:**
```bash
# Initialize and start dashboard
cd dashboard
npm install
npm start

# Verify application loads
curl http://localhost:3001

# Check routing
open http://localhost:3001/dashboard
open http://localhost:3001/sessions/test
```

#### Step 3.2: WebSocket Client Implementation
**Goal:** Create multiplexed WebSocket client for dashboard real-time communications
**Files to Create/Modify:**
- `dashboard/src/services/WebSocketManager.ts` (new)
- `dashboard/src/hooks/useWebSocket.ts` (new)
- `dashboard/src/types/websocket.ts` (new)
- `dashboard/src/services/api.ts` (new)

**AI Prompt:** `Implement Step 3.2 of EP-0004: Create multiplexed WebSocket client with subscription management, auto-reconnection, and message routing for dashboard communications`

**Tasks:**
- [ ] Create MultiplexedWebSocketManager class
- [ ] Implement subscription-based message routing
- [ ] Add auto-reconnection with exponential backoff
- [ ] Create React hooks for WebSocket state management
- [ ] Implement subscription state persistence across reconnections

**Dependencies:**
- Step 3.1 must be complete
- Backend WebSocket endpoint operational

**Validation Criteria:**
- [ ] WebSocket client connects to dashboard endpoint successfully
- [ ] Subscription management works for multiple channels
- [ ] Auto-reconnection restores subscriptions after connection loss
- [ ] Message routing delivers updates to correct React components
- [ ] WebSocket connection status visible in dashboard UI

**Success Check:**
```bash
# Start dashboard and verify WebSocket connection
cd dashboard && npm start

# Check browser console for WebSocket connection
# Open browser dev tools and verify:
# - WebSocket connection established
# - Subscription messages sent
# - Reconnection works after network interruption
```

#### Step 3.3: Dashboard Core Components
**Goal:** Implement main dashboard view with active alerts panel and historical sessions list
**Files to Create/Modify:**
- `dashboard/src/components/DashboardView.tsx` (new)
- `dashboard/src/components/ActiveAlertsPanel.tsx` (new)
- `dashboard/src/components/HistoricalSessionsList.tsx` (new)
- `dashboard/src/components/FilterPanel.tsx` (new)
- `dashboard/src/components/RealTimeMonitor.tsx` (new)

**AI Prompt:** `Implement Step 3.3 of EP-0004: Create main dashboard components following the detailed UI/UX specifications including split-panel layout, status color coding, virtual scrolling, and accessibility requirements`

**Tasks:**
- [ ] Create DashboardView with split-panel design (active alerts top, historical bottom)
- [ ] Implement ActiveAlertsPanel with status color coding (🔴🟡🟢), progress indicators, and expandable cards
- [ ] Create HistoricalSessionsList with react-window virtual scrolling, quick filter buttons with badge counts
- [ ] Build FilterPanel with debounced search, autocomplete suggestions, and sortable table columns
- [ ] Add RealTimeMonitor with auto-refresh indicator and live status counters
- [ ] Implement ARIA labels and keyboard navigation for accessibility (WCAG 2.1 AA)
- [ ] Add responsive breakpoints (desktop 1200px+, tablet 768px+, mobile 320px+)

**Dependencies:**
- Step 3.2 must be complete
- WebSocket client functionality

**Validation Criteria:**
- [ ] Dashboard view displays both active and historical sections
- [ ] Active alerts panel shows real-time processing status
- [ ] Historical sessions list handles large datasets efficiently
- [ ] Filter panel applies filters and updates results
- [ ] Real-time monitor displays current operational metrics

**Success Check:**
```bash
# Verify dashboard components render
cd dashboard && npm start
open http://localhost:3001/dashboard

# Check component functionality:
# - Active alerts panel shows processing status
# - Historical list displays sessions with pagination
# - Filters apply and update results
# - Real-time updates appear automatically
```

### Phase 3 Completion Criteria
- [ ] Dashboard application runs independently with proper routing
- [ ] WebSocket client provides reliable real-time communication
- [ ] Core dashboard components display active and historical alerts
- [ ] Filtering and pagination work efficiently for large datasets
- [ ] Real-time updates appear promptly in dashboard interface

## Phase 4: Advanced Features & Integration

### Phase 4 Overview
**Dependencies:** Phase 3 completion
**Goal:** Complete dashboard implementation with session details, timeline visualization, and performance optimization

#### Step 4.1: Session Detail Implementation
**Goal:** Create unified session detail page for both active and historical alerts
**Files to Create/Modify:**
- `dashboard/src/components/SessionDetailPage.tsx` (new)
- `dashboard/src/components/SessionHeader.tsx` (new)
- `dashboard/src/components/TimelineVisualization.tsx` (new)
- `dashboard/src/components/InteractionDetails.tsx` (new)
- `dashboard/src/components/SessionActions.tsx` (new)

**AI Prompt:** `Implement Step 4.1 of EP-0004: Create session detail page following UI/UX specifications with SVG-based timeline visualization, interactive elements, and accessibility requirements`

**Tasks:**
- [ ] Create SessionDetailPage with routing parameter handling and breadcrumb navigation
- [ ] Implement SessionHeader showing active/historical status with clear visual indicators
- [ ] Build TimelineVisualization with SVG-based timeline, chronological markers, and clickable interaction points
- [ ] Create InteractionDetails with copy functionality for individual interactions and full timeline
- [ ] Add SessionActions with consistent button styling and keyboard navigation support
- [ ] Implement smooth animations for real-time timeline updates (active sessions only)
- [ ] Add focus management and ARIA live regions for screen reader support

**Dependencies:**
- Step 3.3 must be complete
- Session detail routing infrastructure

**Validation Criteria:**
- [ ] Session detail page loads for both active and historical sessions
- [ ] Timeline visualization displays chronological interactions clearly
- [ ] Real-time updates appear for active sessions automatically
- [ ] Interaction details show comprehensive LLM and MCP information
- [ ] Session actions provide copy and export functionality

**Success Check:**
```bash
# Test session detail navigation
open http://localhost:3001/sessions/active_session_id
open http://localhost:3001/sessions/historical_session_id

# Verify functionality:
# - Timeline renders with interactions
# - Real-time updates for active sessions
# - Copy/export actions work
# - Navigation back to dashboard works
```

#### Step 4.2: Performance Optimization
**Goal:** Implement virtualization, caching, and performance optimizations for large datasets
**Files to Create/Modify:**
- `dashboard/src/components/VirtualizedSessionGrid.tsx` (new)
- `dashboard/src/hooks/useSessionCache.ts` (new)
- `dashboard/src/services/cacheManager.ts` (new)
- `dashboard/src/hooks/useVirtualization.ts` (new)

**AI Prompt:** `Implement Step 4.2 of EP-0004: Add performance optimizations including virtual scrolling, session data caching, and React optimization patterns for handling 1000+ sessions`

**Tasks:**
- [ ] Implement virtualized scrolling for session lists using react-window
- [ ] Create session data caching with TTL and invalidation
- [ ] Add React optimization patterns (memo, useMemo, useCallback)
- [ ] Implement lazy loading for session timeline data
- [ ] Create performance monitoring and metrics collection

**Dependencies:**
- Step 4.1 must be complete
- react-window library integration

**Validation Criteria:**
- [ ] Session list handles 1000+ items with constant memory usage
- [ ] Data caching reduces API calls and improves response times
- [ ] React optimizations prevent unnecessary re-renders
- [ ] Lazy loading provides smooth user experience
- [ ] Performance metrics meet requirements specifications

**Success Check:**
```bash
# Test performance with large dataset
cd dashboard && npm start

# Verify performance:
# - Smooth scrolling through 1000+ sessions
# - Fast filter application
# - Memory usage remains stable
# - No performance warnings in React DevTools
```

#### Step 4.3: Error Handling & Resilience
**Goal:** Implement comprehensive error handling, retry mechanisms, and graceful degradation
**Files to Create/Modify:**
- `dashboard/src/components/ErrorBoundary.tsx` (new)
- `dashboard/src/components/ConnectionStatus.tsx` (new)
- `dashboard/src/hooks/useErrorHandling.ts` (new)
- `dashboard/src/services/retryManager.ts` (new)

**AI Prompt:** `Implement Step 4.3 of EP-0004: Create comprehensive error handling system with error boundaries, connection status monitoring, retry mechanisms, and graceful degradation`

**Tasks:**
- [ ] Create ErrorBoundary for application-wide error handling
- [ ] Implement ConnectionStatus component for WebSocket monitoring
- [ ] Add retry mechanisms with exponential backoff for API calls
- [ ] Create graceful degradation for offline/limited connectivity
- [ ] Implement user-friendly error messages and recovery actions

**Dependencies:**
- Step 4.2 must be complete
- Error handling infrastructure

**Validation Criteria:**
- [ ] Error boundaries catch and display component errors gracefully
- [ ] Connection status accurately reflects WebSocket state
- [ ] Retry mechanisms recover from temporary failures
- [ ] Offline mode provides basic functionality without real-time updates
- [ ] Error messages guide users toward resolution actions

**Success Check:**
```bash
# Test error scenarios
cd dashboard && npm start

# Verify error handling:
# - Disconnect network and verify graceful degradation
# - Force component errors and verify error boundaries
# - Test API failure scenarios with retry behavior
# - Verify connection status updates correctly
```

### Phase 4 Completion Criteria
- [ ] Session detail pages provide comprehensive timeline visualization
- [ ] Performance optimizations handle large datasets efficiently
- [ ] Error handling provides robust user experience
- [ ] All dashboard features work reliably with real-time updates
- [ ] Application meets all requirements specifications

## Phase 5: Testing & Documentation

### Phase 5 Overview
**Dependencies:** Phase 4 completion
**Goal:** Complete testing coverage and documentation for production readiness

#### Step 5.1: Unit Testing Implementation
**Goal:** Create comprehensive unit tests for all dashboard components and services
**Files to Create/Modify:**
- `dashboard/src/components/__tests__/` (new directory)
- `dashboard/src/services/__tests__/` (new directory)
- `dashboard/src/hooks/__tests__/` (new directory)
- `dashboard/jest.config.js` (new)
- `dashboard/src/setupTests.ts` (new)

**AI Prompt:** `Implement Step 5.1 of EP-0004: Create comprehensive unit test suite for all dashboard components, services, and hooks using Jest and React Testing Library`

**Tasks:**
- [ ] Set up Jest and React Testing Library configuration
- [ ] Create unit tests for all React components with snapshot testing
- [ ] Test WebSocket service functionality with mocked connections
- [ ] Add tests for custom hooks and state management
- [ ] Create utility function tests with edge case coverage

**Dependencies:**
- Phase 4 completion
- Jest and React Testing Library setup

**Validation Criteria:**
- [ ] All components have unit tests with >80% coverage
- [ ] WebSocket service tests cover subscription and messaging
- [ ] Hook tests verify state management and side effects
- [ ] Snapshot tests catch unintended component changes
- [ ] All tests pass consistently in CI environment

**Success Check:**
```bash
# Run unit tests
cd dashboard && npm test

# Check coverage
npm run test:coverage

# Verify coverage meets requirements
grep -A 10 "Coverage summary" coverage/lcov-report/index.html
```

#### Step 5.2: Integration Testing
**Goal:** Test component integration and API communication with mock services
**Files to Create/Modify:**
- `dashboard/src/__tests__/integration/` (new directory)
- `dashboard/src/__tests__/mocks/` (new directory)
- `dashboard/src/__tests__/integration/dashboard.integration.test.tsx` (new)
- `dashboard/src/__tests__/integration/websocket.integration.test.tsx` (new)

**AI Prompt:** `Implement Step 5.2 of EP-0004: Create integration tests for dashboard component interactions, API communication, and WebSocket functionality using mock services`

**Tasks:**
- [ ] Create integration tests for dashboard workflow scenarios
- [ ] Test WebSocket communication with mock backend
- [ ] Verify component interactions and data flow
- [ ] Test error scenarios and recovery mechanisms
- [ ] Create mock data generators for testing

**Dependencies:**
- Step 5.1 must be complete
- Mock service infrastructure

**Validation Criteria:**
- [ ] Integration tests cover major user workflows
- [ ] WebSocket integration tests verify real-time functionality
- [ ] Component integration tests verify parent-child communication
- [ ] Error scenario tests verify graceful failure handling
- [ ] Mock services provide realistic test environments

**Success Check:**
```bash
# Run integration tests
cd dashboard && npm run test:integration

# Verify workflow coverage
npm run test:integration -- --coverage

# Check integration test results
cat integration-test-results.xml
```

#### Step 5.3: UI/UX Validation Testing
**Goal:** Validate UI implementation against design specifications and user experience requirements
**Files to Create/Modify:**
- `dashboard/src/__tests__/ui-validation/` (new directory)
- `dashboard/src/__tests__/ui-validation/accessibility.test.tsx` (new)
- `dashboard/src/__tests__/ui-validation/responsive.test.tsx` (new)
- `dashboard/src/__tests__/ui-validation/visual-regression.test.tsx` (new)
- `dashboard/src/__tests__/ui-validation/user-journey.test.tsx` (new)

**AI Prompt:** `Implement Step 5.3 of EP-0004: Create comprehensive UI/UX validation tests to verify implementation matches design specifications including accessibility, responsive design, visual regression, and user journey workflows`

**Tasks:**
- [ ] Create accessibility tests using axe-core for WCAG 2.1 AA compliance
- [ ] Implement responsive design tests across all breakpoints (320px, 768px, 1200px+)
- [ ] Set up visual regression testing with screenshot comparison
- [ ] Create user journey tests for primary and secondary workflows
- [ ] Test keyboard navigation and focus management
- [ ] Validate color contrast ratios and status information clarity
- [ ] Test real-time update animations and performance

**Dependencies:**
- Step 5.2 must be complete
- All UI components implemented

**Validation Criteria:**
- [ ] All accessibility tests pass (WCAG 2.1 AA compliance)
- [ ] Responsive design works correctly across all breakpoints
- [ ] Visual regression tests show no unintended changes
- [ ] User journey workflows complete successfully
- [ ] Performance requirements met (2s initial load, 500ms update latency)

**Success Check:**
```bash
# Run UI validation test suite
cd dashboard && npm run test:ui-validation

# Check accessibility compliance
npm run test:accessibility

# Verify responsive design
npm run test:responsive

# Run visual regression tests
npm run test:visual-regression
```

#### Step 5.4: Documentation Creation
**Goal:** Create comprehensive documentation for dashboard application
**Files to Create/Modify:**
- `dashboard/README.md` (new)
- `dashboard/docs/DEVELOPMENT.md` (new)
- `dashboard/docs/DEPLOYMENT.md` (new)
- `dashboard/docs/API_INTEGRATION.md` (new)
- `dashboard/docs/UI_GUIDELINES.md` (new)
- `docs/requirements.md` (update - add dashboard section)

**AI Prompt:** `Implement Step 5.4 of EP-0004: Create comprehensive documentation including README, development guide, deployment instructions, API integration, and UI guidelines documentation`

**Tasks:**
- [ ] Create dashboard README with overview and quick start
- [ ] Write development documentation with setup and contribution guidelines
- [ ] Create deployment documentation for production environments
- [ ] Document API integration and WebSocket communication protocols
- [ ] Create UI guidelines documentation referencing design specifications
- [ ] Update main project documentation to include dashboard

**Dependencies:**
- Step 5.3 must be complete
- Complete dashboard implementation and validation

**Validation Criteria:**
- [ ] README provides clear overview and installation instructions
- [ ] Development documentation enables new contributor onboarding
- [ ] Deployment documentation supports production deployment  
- [ ] API documentation accurately describes integration points
- [ ] UI guidelines help maintain design consistency
- [ ] Documentation examples work correctly

**Success Check:**
```bash
# Verify documentation completeness
find dashboard/docs -name "*.md" -exec wc -l {} \;

# Test documentation examples
cd dashboard && npm run verify-docs

# Validate deployment instructions
docker build -t dashboard-test .
```

### Phase 5 Completion Criteria
- [ ] Unit test coverage exceeds 80% for all components and services
- [ ] Integration tests verify major user workflows and error scenarios
- [ ] **UI/UX validation confirms implementation matches design specifications**
- [ ] **Accessibility tests pass WCAG 2.1 AA compliance requirements**
- [ ] **Responsive design works correctly across all breakpoints (320px, 768px, 1200px+)**
- [ ] **User journey workflows complete successfully for primary and secondary use cases**
- [ ] **Performance requirements met (2s initial load, 500ms real-time update latency)**
- [ ] Documentation provides comprehensive guidance for development and deployment
- [ ] All tests pass consistently in automated test environments
- [ ] Dashboard application ready for production deployment

## Testing Strategy

### Test Plans

#### Unit Tests
- **Component Tests**: Snapshot testing and behavior verification for all React components
- **Service Tests**: WebSocket manager, API client, and utility function testing with mocks
- **Hook Tests**: Custom React hooks testing with renderHook and act utilities
- **Type Tests**: TypeScript interface and type definition validation

#### Integration Tests (Mock Services Only)
- **Dashboard Workflow**: Complete user journey from dashboard load to session detail
- **WebSocket Integration**: Real-time update flow with mock WebSocket server
- **API Integration**: REST API communication with mock backend responses
- **Error Scenario Testing**: Network failures, API errors, and recovery mechanisms

#### End-to-End Tests (Mock Services Only)
- **User Journey Testing**: Complete SRE workflow scenarios with mock data
- **Performance Testing**: Large dataset handling and virtual scrolling validation
- **Browser Compatibility**: Cross-browser testing with automated browser drivers
- **Accessibility Testing**: WCAG 2.1 AA compliance verification

### Test Execution

#### Automated Testing Pipeline
```bash
# Complete test suite execution
npm run test:all

# Individual test suites
npm run test:unit
npm run test:integration
npm run test:e2e
npm run test:performance
```

## Resource Requirements

### Technical Resources
- **Development Environment**: Node.js 18+, npm/yarn, React development tools
- **Testing Tools**: Jest, React Testing Library, WebSocket mocking capabilities
- **Build Tools**: Webpack, TypeScript compiler, ESLint/Prettier configuration
- **Deployment Infrastructure**: Static hosting for React SPA, CDN capabilities

### External Dependencies
- **Backend WebSocket Support**: Requires Phase 1-2 backend implementation completion
- **EP-0003 History Service**: Must remain operational during dashboard development
- **Material-UI v5.15.0**: Component library for consistent UI design
- **React-Window**: Virtual scrolling library for performance optimization

## Documentation Updates Required

### Main Documentation Updates

#### requirements.md Updates
- [ ] **Section 5.2**: Add dashboard UI requirements and specifications
- [ ] **Section 6.1**: Include dashboard performance requirements
- [ ] **New Section 7.3**: Dashboard deployment and configuration requirements

#### design.md Updates
- [ ] **Section 3.4**: Add dashboard architecture to system design
- [ ] **Section 8.2**: Include dashboard components in technical architecture
- [ ] **New Section 9**: Dashboard UI/UX design specifications

#### Other Documentation
- [ ] **DEPLOYMENT.md**: Add dashboard deployment instructions and configuration
- [ ] **README.md**: Update project overview to include dashboard application
- [ ] **docs/todo.md**: Remove completed dashboard items and add maintenance tasks

---

## Implementation Checklist

### Pre-Implementation
- [ ] Requirements document approved
- [ ] Design document approved
- [ ] Implementation plan approved
- [ ] Backend development environment ready
- [ ] Frontend development environment ready

### During Implementation
- [ ] Follow phase-by-phase process with backend-first approach
- [ ] Validate each step before proceeding to next phase
- [ ] Update progress regularly with step completion tracking
- [ ] Escalate issues promptly to prevent cascade failures
- [ ] Document decisions and changes in implementation notes

### Post-Implementation
- [ ] All unit and integration tests passing
- [ ] Performance benchmarks meet requirements
- [ ] Documentation complete and validated
- [ ] Success metrics achieved and verified

---

## AI Implementation Guide

### Implementation Approach Reminder
**CRITICAL**: This is a new standalone application with integrated hook system:
- Create entirely new `dashboard/` directory structure
- Build new React components without legacy constraints
- Implement new backend WebSocket endpoints and services
- **Extend existing EP-0003 hook system** with dashboard broadcast hooks
- **Reuse hook infrastructure** - no modifications to LLM/MCP clients needed
- Focus on clean, modern architecture patterns leveraging proven hook system
- Maintain API compatibility with existing EP-0003 endpoints

### Step-by-Step Execution
1. **Implement each phase sequentially** starting with backend infrastructure
2. **Validate each step** using the success check commands before proceeding
3. **Backend-first approach** - complete Phases 1-2 before frontend development
4. **Test integration points** between new components and existing services
5. **Update progress** by checking off completed tasks and validation criteria


---

## Completion Criteria

### Final Success Criteria
- [ ] All requirements from EP-0004 requirements document are met
- [ ] All design elements from EP-0004 design document are implemented
- [ ] **Integrated hook system** provides consistent data to both history service and dashboard
- [ ] Backend WebSocket infrastructure supports real-time dashboard communication
- [ ] Frontend dashboard application provides comprehensive SRE monitoring capabilities
- [ ] **Dashboard hooks execute alongside history hooks** without impacting existing functionality
- [ ] All test cases pass with adequate coverage
- [ ] All documentation is complete and accurate
- [ ] Performance requirements met for 1000+ session handling
- [ ] Dashboard operates independently with reliable real-time updates

### Implementation Complete
When all phases are complete and all success criteria are met, this EP implementation is considered complete and can be moved to the implemented directory.

**Final AI Prompt:**
```

---
Review EP-0004 implementation and mark it as completed. Move all three documents (requirements, design, implementation) to the implemented directory and update the project documentation.
``` 