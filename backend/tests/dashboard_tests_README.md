# Tarsy Backend Test Suite

This directory contains comprehensive unit and integration tests for the Tarsy backend system, with particular focus on the dashboard real-time features implemented in Phases 1 and 2 of EP-0004.

## Overview

The test suite validates the complete backend system including:
- **Dashboard Real-time System**: WebSocket infrastructure, broadcasting, and session management
- **Hook System Integration**: LLM and MCP event processing with real-time updates
- **History System**: Alert processing history and data persistence
- **Agent System**: Multi-layer agent architecture and orchestration
- **Integration Points**: End-to-end workflows and system resilience

## Test Structure

### Unit Tests (`tests/unit/`)
Tests individual components in isolation with mocked dependencies:

```
tests/unit/
├── models/
│   └── test_websocket_models.py      # WebSocket message models (40+ tests)
├── services/
│   ├── test_subscription_manager.py   # Channel subscription logic (30+ tests)  
│   ├── test_dashboard_connection_manager.py  # WebSocket connections (35+ tests)
│   ├── test_dashboard_broadcaster.py  # Message broadcasting (40+ tests)
│   ├── test_dashboard_update_service.py  # Session & metrics (30+ tests)
│   └── test_history_service.py       # History system tests
├── hooks/
│   └── test_dashboard_hooks.py       # LLM/MCP hooks (35+ tests)
├── agents/
│   └── test_base_agent.py           # Agent system tests
└── controllers/
    └── test_history_controller.py   # REST API tests
```

### Integration Tests (`tests/integration/`)
Tests component interactions and end-to-end workflows:

```
tests/integration/
├── test_dashboard_integration.py     # Dashboard system integration (20+ tests)
├── test_component_integration.py     # Cross-component workflows
├── test_history_integration.py       # History system integration  
├── test_alert_processing_e2e.py     # Complete alert processing flows
└── test_edge_cases.py               # Error scenarios and edge cases
```

## Key Test Features

### Dashboard System Tests
- **WebSocket Infrastructure**: Connection management, subscription channels, message routing
- **Real-time Broadcasting**: Message batching, throttling, filtering, and delivery optimization
- **Session Management**: Active session tracking, metrics calculation, lifecycle management
- **Hook Integration**: LLM/MCP event processing with fallback mechanisms
- **Error Resilience**: Graceful handling of connection failures, service restarts, and high load

### Comprehensive Coverage
- **200+ individual test cases** across all backend components
- **Unit tests** with AsyncMock for isolated component testing
- **Integration tests** for end-to-end workflow validation
- **Performance tests** for high throughput and concurrent user scenarios
- **Error handling tests** for various failure conditions

### Advanced Testing Patterns
- **Fixture-based setup** for reusable test infrastructure
- **Async test support** with proper asyncio integration
- **Mock WebSocket connections** for real-time communication testing
- **Concurrent execution testing** for multi-user scenarios
- **Resource cleanup** ensuring no test pollution

## Running Tests

### Using the Test Runner

The `run_dashboard_tests.py` script provides a unified interface for running all backend tests:

```bash
# Run all tests (unit + integration)
python tests/run_dashboard_tests.py

# Run only unit tests
python tests/run_dashboard_tests.py --type unit

# Run only integration tests  
python tests/run_dashboard_tests.py --type integration

# Run with coverage reporting
python tests/run_dashboard_tests.py --coverage

# Quick run (skip slow tests)
python tests/run_dashboard_tests.py --quick

# Verbose output
python tests/run_dashboard_tests.py --verbose

# Combined options
python tests/run_dashboard_tests.py --type unit --coverage --verbose
```

### Using pytest directly

```bash
# All tests
pytest tests/

# Unit tests only
pytest -m unit tests/

# Integration tests only
pytest -m integration tests/

# With coverage
pytest --cov=tarsy --cov-report=html tests/

# Specific test file
pytest tests/unit/services/test_dashboard_broadcaster.py -v
```

## Test Quality Metrics

### Coverage Targets
- **Overall backend coverage**: 85%+ 
- **Dashboard system coverage**: 90%+
- **Critical path coverage**: 95%+
- **Error handling coverage**: 80%+

### Test Categories
- **Unit tests**: Fast, isolated, deterministic
- **Integration tests**: Realistic, end-to-end, comprehensive
- **Performance tests**: Load testing, concurrency, throughput
- **Error tests**: Failure scenarios, recovery, resilience

## Dependencies

### Required Packages
```bash
pip install pytest pytest-asyncio pytest-cov
```

### Test Infrastructure
- **pytest**: Test framework and runner
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **unittest.mock**: Mocking and AsyncMock
- **asyncio**: Concurrent execution testing

## Implementation Details

### Dashboard System Architecture

The tests validate this architecture:

```
WebSocket Clients
       ↓
DashboardConnectionManager (connection lifecycle, subscription tracking)
       ↓  
SubscriptionManager (channel validation, message filtering)
       ↓
DashboardBroadcaster (batching, throttling, broadcasting)
       ↓
DashboardUpdateService (session management, metrics)
       ↓
DashboardHooks (LLM/MCP event processing)
       ↓
Existing Hook System (EP-0003 integration)
```

### Key Integration Points

1. **Hook System Integration**: Dashboard hooks integrate with existing EP-0003 history system
2. **WebSocket Multiplexing**: Single connection handles multiple logical channels
3. **Real-time Session Tracking**: Active sessions monitored with live metrics
4. **Intelligent Broadcasting**: Message optimization with batching and throttling
5. **Graceful Degradation**: Fallback mechanisms for service failures

## Maintenance Guidelines

### Adding New Tests
1. **Unit tests**: Add to appropriate `tests/unit/` subdirectory
2. **Integration tests**: Add to `tests/integration/` with proper setup/teardown
3. **Use markers**: Add `@pytest.mark.unit` or `@pytest.mark.integration`
4. **Async tests**: Use `@pytest.mark.asyncio` for async test methods
5. **Mock dependencies**: Use AsyncMock for WebSocket and async services

### Test Naming Conventions
- Test files: `test_<component_name>.py`
- Test classes: `Test<ComponentName>` or `Test<Functionality>`
- Test methods: `test_<specific_behavior>`
- Async tests: Include `async` in method name when helpful

### Coverage Guidelines
- **New features**: 90%+ coverage required
- **Critical paths**: 95%+ coverage required  
- **Error handling**: Test both success and failure scenarios
- **Integration points**: Test cross-component interactions

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run Backend Tests
  run: |
    cd backend
    python tests/run_dashboard_tests.py --coverage
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: backend/coverage.xml
```

### Local Development
```bash
# Pre-commit testing
python tests/run_dashboard_tests.py --quick

# Full validation before PR
python tests/run_dashboard_tests.py --coverage --verbose
```

The test suite ensures the dashboard system is production-ready, maintainable, and integrates seamlessly with the existing Tarsy backend architecture. 