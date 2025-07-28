# EP-0005: Flexible Alert Data Structure Support - Implementation Plan

**Status:** Approved  
**Created:** 2025-07-28  
**Phase:** Implementation Planning  
**Requirements Document:** `docs/enhancements/approved/EP-0005-flexible-alert-data-structure-requirements.md`  
**Design Document:** `docs/enhancements/approved/EP-0005-flexible-alert-data-structure-design.md`  

---

## Implementation Overview

### Summary
Transform the current rigid, Kubernetes-specific alert data model into a flexible, agent-agnostic system using minimal validation with JSON payload storage. This implementation will use a fresh database deployment approach, eliminating migration complexity while preserving core Kubernetes alert processing functionality.

### Implementation Strategy
- **Fresh Database Setup**: Use existing initialization with enhanced JSON indexing capabilities  
- **Minimal Disruption**: Preserve existing workflows while adding flexibility
- **Component-by-Component**: Systematic update of each system layer
- **LLM-First Processing**: "Dump everything to LLM" approach - agents receive complete payloads for intelligent interpretation instead of hardcoded field extraction
- **Hybrid Storage**: alert_type in separate column for fast routing, flexible data in JSON field

### Key Implementation Goals
- Enable support for diverse monitoring sources beyond Kubernetes
- Eliminate need for core system modifications when adding new agent types  
- Maintain current performance and reliability standards
- Preserve existing Kubernetes alert processing capabilities
- Support seamless addition of new alert types without schema changes

---

## Implementation Phases

### Phase 1: Database Schema and Core Data Models
**Objective:** Establish foundation with flexible data structures and optimized JSON storage

#### Tasks
1. **Update Alert Session Model** (`tarsy/models/history.py`)
   - Add GIN index for flexible JSON queries: `Index('ix_alert_data_gin', 'alert_data', postgresql_using='gin')`
   - Create indexes on common JSON paths: `Index('ix_alert_data_severity', text("((alert_data->>'severity'))"))`
   - Add indexes for environment and cluster fields using same pattern
   - Add __table_args__ for PostgreSQL JSON optimization
   - The AlertSession model already has the JSON alert_data field we need

2. **Create Flexible Alert Model** (`tarsy/models/alert.py`)
   - Replace rigid Alert model with FlexibleAlert model
   - Required fields: alert_type (str) and runbook (str)
   - Add data field (Dict[str, Any]) for arbitrary JSON payload
   - Optional fields with defaults: severity (defaults to "warning"), timestamp (defaults to current unix microseconds)

#### Files to Modify
- `tarsy/models/alert.py` - New FlexibleAlert model
- `tarsy/models/history.py` - Enhanced AlertSession with JSON indexing

#### Validation Commands
```bash
# Test database models and initialization
python -m pytest tests/unit/models/ -v
python -m pytest tests/integration/test_database_setup.py -v

# Check database connectivity and schema (using existing initialization)
python -c "from tarsy.database.init_db import initialize_database; initialize_database()"

# Type checking
mypy tarsy/models/
```

#### Success Criteria
- [ ] FlexibleAlert model validates alert_type and runbook fields
- [ ] AlertSession supports optimized JSON querying  
- [ ] Database initializes with proper JSON indexes
- [ ] All model tests pass with new schema
- [ ] Type annotations are complete and valid

---

### Phase 2: API Layer and Alert Ingestion  
**Objective:** Update API endpoints to accept flexible JSON payloads with minimal validation

#### Tasks
1. **Redesign Alert Submission Endpoint** (`tarsy/main.py`)
   - Modify POST /alerts to accept FlexibleAlert model
   - Implement minimal validation (alert_type + runbook required)
   - Add inline default application (severity: "warning", timestamp: current unix microseconds, environment: "production")
   - Convert any datetime timestamps to Unix microseconds format (preserving existing system format)
   - Enhanced error handling for malformed JSON

2. **Update Alert Service** (`tarsy/services/alert_service.py`)  
   - Modify alert processing to handle flexible data structure
   - Update _create_history_session() to store alert_type in separate AlertSession column
   - Store runbook + all data contents in AlertSession.alert_data JSON field
   - Extract runbook from alert data before passing to agents
   - Remove rigid validation, add simple inline normalization
   - Preserve existing agent routing logic

3. **API Response Updates**
   - Maintain existing AlertResponse format for compatibility
   - Update error responses with helpful validation messages
   - Add support for debugging malformed JSON submissions

#### Files to Modify
- `tarsy/main.py` - POST /alerts endpoint redesign
- `tarsy/services/alert_service.py` - Flexible alert processing
- `tarsy/models/api_models.py` - Update response models if needed

#### Validation Commands
```bash
# Test API endpoints
python -m pytest tests/integration/test_alert_processing_e2e.py -v
python -m pytest tests/unit/services/test_alert_service.py -v

# API compatibility tests
python -m pytest tests/api/ -v

# Manual API testing
curl -X POST http://localhost:8000/alerts \
  -H "Content-Type: application/json" \
  -d '{"alert_type": "kubernetes", "runbook": "https://example.com/runbook", "data": {"cluster": "test", "severity": "critical"}}'
```

#### Success Criteria
- [ ] API accepts flexible JSON payloads with minimal validation
- [ ] Default values are applied correctly for missing fields
- [ ] Alert routing to agents works with new data structure
- [ ] Error messages are clear and helpful for malformed requests
- [ ] Existing Kubernetes alerts continue to process correctly
- [ ] WebSocket status updates work unchanged

---

### Phase 3: Agent Processing Enhancement
**Objective:** Update agents to handle flexible alert data and include all information in LLM prompts

#### Tasks  
1. **Update Base Agent** (`tarsy/agents/base_agent.py`)
   - Remove _prepare_alert_data() method
   - Modify agents to receive AlertSession.alert_data directly (with runbook extracted by service layer)
   - Update prompt building to include all remaining data as key-value pairs
   - Handle complex data structures (nested objects, arrays, YAML strings, any JSON structure)
   - Service layer extracts runbook before passing data to agent

2. **Update Kubernetes Agent** (`tarsy/agents/kubernetes_agent.py`)
   - Verify compatibility with new flexible data structure
   - Ensure Kubernetes-specific processing still works effectively
   - Test with Kubernetes alerts submitted in the new flexible format

3. **Update Prompt Builder** (`tarsy/agents/prompt_builder.py`)
   - Enhance prompt building to serialize complex JSON structures
   - Include all alert data fields in LLM context
   - Handle various data types (strings, objects, arrays, YAML content)
   - Maintain existing MCP data integration

#### Files to Modify
- `tarsy/agents/base_agent.py` - Remove rigid data preparation, add flexible processing
- `tarsy/agents/kubernetes_agent.py` - Verify compatibility
- `tarsy/agents/prompt_builder.py` - Enhanced JSON serialization for prompts

#### Validation Commands  
```bash
# Test agent processing
python -m pytest tests/unit/agents/ -v
python -m pytest tests/integration/test_component_integration.py -v

# Test prompt building
python -m pytest tests/unit/agents/test_prompt_builder.py -v

# End-to-end agent testing
python -m pytest tests/integration/test_alert_processing_e2e.py::test_flexible_alert_processing -v
```

#### Success Criteria
- [ ] Agents receive complete alert data without preprocessing
- [ ] LLM prompts include all available alert information as key-value pairs
- [ ] Complex data structures (objects, arrays) are properly serialized
- [ ] Kubernetes alerts process correctly with new agent logic
- [ ] Agent selection and routing work unchanged
- [ ] MCP integration continues to function properly

---

### Phase 4: UI Component Updates
**Objective:** Update UI components to display arbitrary alert data fields dynamically

#### Tasks
1. **Update Dashboard Components** (`dashboard/src/components/`)
   - Modify OriginalAlertCard to render generic key-value pairs for all fields in alert_data
   - Remove hardcoded Kubernetes field display logic  
   - Implement dynamic field rendering for any alert data structure
   - Other components (AlertListItem, ActiveAlertCard) display session metadata and don't need changes
   - Maintain existing layout and styling consistency

2. **Update Alert Development UI** (`alert-dev-ui/src/components/`)
   - Redesign AlertForm with required fields (alert_type dropdown, runbook input)
   - Add dynamic key-value pair inputs for flexible data
   - Remove hardcoded form fields (severity select, environment select, etc.)
   - Implement add/remove functionality for key-value pairs

3. **UI Data Handling**
   - Update API service calls to handle flexible alert data
   - Add JSON parsing and rendering utilities
   - Implement safe rendering for complex data structures
   - Add XSS prevention for dynamic content rendering

#### Files to Modify
- `dashboard/src/components/OriginalAlertCard.tsx` - Generic key-value rendering
- `alert-dev-ui/src/components/AlertForm.tsx` - Dynamic form with key-value pairs
- `dashboard/src/services/api.ts` - Handle flexible alert data
- `alert-dev-ui/src/services/api.ts` - Update API calls

#### Validation Commands
```bash
# Frontend tests
cd dashboard && npm test
cd alert-dev-ui && npm test

# Linting and type checking
cd dashboard && npm run lint && npm run type-check
cd alert-dev-ui && npm run lint && npm run type-check

# Build verification
cd dashboard && npm run build
cd alert-dev-ui && npm run build

# Manual UI testing
npm start # Test both UIs with flexible alert data
```

#### Success Criteria
- [ ] OriginalAlertCard displays all available alert fields dynamically
- [ ] AlertForm supports adding/removing arbitrary key-value pairs
- [ ] Required fields (alert_type, runbook) are clearly marked and validated
- [ ] Complex data structures display properly without breaking UI
- [ ] Existing alert workflows continue to work
- [ ] No XSS vulnerabilities in dynamic content rendering

---

### Phase 5: Error Handling and Edge Cases
**Objective:** Implement comprehensive error handling and test edge cases

#### Tasks
1. **API Error Handling**
   - Add comprehensive JSON validation error messages
   - Implement graceful handling of malformed payloads
   - Add input sanitization for security
   - Test with various invalid JSON structures

2. **Agent Error Handling**  
   - Handle missing expected fields gracefully
   - Implement fallback processing for incomplete data
   - Add logging for debugging unusual alert structures
   - Test agent behavior with minimal data sets

3. **UI Error Handling**
   - Add error boundaries for dynamic rendering failures
   - Implement fallback displays for corrupted alert data
   - Handle API errors gracefully in form submission
   - Add loading states for dynamic components

4. **Edge Case Testing**
   - Test with extremely large JSON payloads
   - Verify handling of nested objects and arrays
   - Test with various timestamp formats
   - Verify performance with complex data structures

#### Files to Modify
- `tarsy/main.py` - Enhanced error handling in API endpoints
- `tarsy/agents/base_agent.py` - Graceful degradation for missing data
- `dashboard/src/components/` - Error boundaries and fallback rendering
- `alert-dev-ui/src/components/` - Form validation and error handling

#### Validation Commands
```bash
# Comprehensive testing
python -m pytest tests/ -v
cd dashboard && npm test
cd alert-dev-ui && npm test

# Error case testing
python -m pytest tests/integration/test_edge_cases.py -v

# Load testing (if applicable)
python -m pytest tests/performance/ -v
```

#### Success Criteria
- [ ] All error conditions are handled gracefully
- [ ] Error messages are helpful and actionable
- [ ] System degrades gracefully with malformed or incomplete data
- [ ] UI components handle rendering failures safely
- [ ] Performance remains acceptable with complex data structures
- [ ] Security measures prevent XSS and injection attacks

---

### Phase 6: Integration Testing and Validation
**Objective:** Comprehensive system testing and validation of all functionality

#### Tasks
1. **End-to-End Testing**
   - Test complete alert processing pipeline with flexible data
   - Verify Kubernetes alerts still process correctly
   - Test new alert types with arbitrary data structures
   - Validate WebSocket updates work with new system

2. **Performance Testing**
   - Test JSON query performance with large datasets
   - Verify database indexing efficiency
   - Test UI rendering performance with complex alert data
   - Validate memory usage with large JSON payloads

3. **Compatibility Testing**
   - Ensure existing integrations continue to work
   - Test with various alert data formats
   - Verify agent selection and routing accuracy
   - Test historical alert data access

4. **Documentation Updates**
   - Update API documentation with flexible schema examples
   - Document new alert submission format
   - Update agent development guidelines
   - Create migration guide for users

#### Files to Modify
- Documentation files as needed
- Test files for comprehensive coverage

#### Validation Commands
```bash
# Full test suite
python -m pytest tests/ -v
cd dashboard && npm test
cd alert-dev-ui && npm test

# Integration tests
python -m pytest tests/integration/ -v

# Performance validation
python -m pytest tests/performance/ -v --benchmark-only

# Manual end-to-end testing
# Submit various alert types and verify processing
```

#### Success Criteria
- [ ] All existing functionality continues to work unchanged
- [ ] New flexible alert processing works for various data structures (nested objects, arrays, YAML strings)
- [ ] New alert types can be added without code changes to core system
- [ ] Diverse monitoring sources beyond Kubernetes can be supported
- [ ] Performance meets or exceeds current standards
- [ ] All tests pass consistently
- [ ] Documentation is complete and accurate
- [ ] System is ready for production deployment

---

## Implementation Notes

### Dependencies
- PostgreSQL with JSON/JSONB support and GIN indexing
- React for dynamic UI component rendering
- Existing agent-MCP architecture
- Current WebSocket infrastructure

### Constraints
- **Fresh Database Setup**: Since existing DB was deleted, use current `initialize_database()` function with enhanced schema
- **Backward Compatibility**: Kubernetes alerts must continue to process correctly
- **Performance**: Must maintain current response times and throughput
- **UI Compatibility**: Existing user workflows should not be disrupted

### Risk Mitigation
- **Phased Approach**: Each phase can be validated independently
- **Backward Compatibility**: Preserve existing Kubernetes alert processing
- **Existing Infrastructure**: Use current database initialization, just add JSON indexes
- **Comprehensive Testing**: Multiple validation points throughout implementation

### Quality Gates
Before marking implementation complete:
- [ ] All requirements from EP-0005 requirements document are met
- [ ] All design elements from EP-0005 design document are implemented  
- [ ] All validation commands pass consistently across all phases
- [ ] Critical functionality has comprehensive test coverage
- [ ] Code includes proper documentation and error handling
- [ ] Integration points work as specified in design
- [ ] Implementation is ready for production use
- [ ] Existing Kubernetes alert processing is fully preserved

---

**Implementation Ready**: This plan provides a systematic approach to implementing flexible alert data structure support while preserving existing functionality and ensuring production readiness.