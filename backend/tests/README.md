# Tarsy - Tests 🧪

**✅ Status**: **100% SUCCESS** - Comprehensive test suite with unit and integration tests for tarsy.

## 🚀 **Quick Start - Simple Commands**

```bash
cd backend

# Install test dependencies
uv sync --extra test

# Simple test commands
python tests/run_integration_tests.py   # Run integration tests only
python tests/run_unit_tests.py          # Run unit tests only  
python tests/run_all_tests.py           # Run all tests

# Alternative: Use the unified test runner
python tests/run_tests.py integration   # Run integration tests
python tests/run_tests.py unit          # Run unit tests
python tests/run_tests.py all           # Run all tests
python tests/run_tests.py all -v        # Run all tests with verbose output
```

## 📋 **Test Coverage**

The integration tests validate:

- **Complete Alert Processing**: From submission to final analysis
- **Agent Specialization**: KubernetesAgent with focused MCP server access  
- **LLM Integration**: Multi-step iterative analysis with mocked providers
- **MCP Tool Execution**: Kubernetes server tool discovery and execution
- **Error Handling**: Service failures, malformed responses, timeouts
- **Performance**: Concurrent processing, resource exhaustion, stress testing
- **Edge Cases**: Unicode support, large inputs, boundary conditions

All external services (LLM APIs, MCP servers, GitHub) are comprehensively mocked.

## 🎯 **Running Tests**

### **Simple Test Commands**
```bash
# Quick commands for specific test types
python tests/run_integration_tests.py   # Integration tests only
python tests/run_unit_tests.py          # Unit tests only
python tests/run_all_tests.py           # All tests (unit + integration)

# Unified test runner with options  
python tests/run_tests.py integration   # Integration tests
python tests/run_tests.py unit          # Unit tests  
python tests/run_tests.py all           # All tests
python tests/run_tests.py all -v        # All tests with verbose output
```

### **Advanced Pytest Commands**
```bash
# Run integration tests only
uv run pytest -m integration -v

# Run specific categories
uv run pytest -k "kubernetes" -v              # Kubernetes tests
uv run pytest -k "error" -v                   # Error handling
uv run pytest -k "concurrency" -v             # Performance tests

# Run specific test files
uv run pytest tests/integration/test_alert_processing_e2e.py -v
uv run pytest tests/integration/test_component_integration.py -v
uv run pytest tests/integration/test_edge_cases.py -v
```

### **Coverage & Reporting**
```bash
# Generate coverage report
uv run pytest tests/integration/ --cov=app --cov-report=html

# Run tests in parallel
uv run pytest tests/integration/ -n auto

# Debug single test
uv run pytest tests/integration/test_alert_processing_e2e.py::TestAlertProcessingE2E::test_happy_path_kubernetes_alert_processing -v -s
```

## 📁 **Test Structure**

```
tests/integration/
├── conftest.py                     # Pytest fixtures and comprehensive mocks
├── test_alert_processing_e2e.py    # End-to-end pipeline tests
├── test_component_integration.py   # Service interaction tests
├── test_edge_cases.py              # Edge cases and stress tests
└── run_integration_tests.py        # Test runner script
```

## 🎭 **Mock Architecture**

All external dependencies are mocked with realistic behaviors:

- **LLM Providers**: Context-aware JSON responses for tool selection and analysis
- **MCP Servers**: Kubernetes tool simulation with realistic command outputs
- **GitHub Integration**: Mock runbook downloading
- **Progress Callbacks**: Full callback chain validation

## 📊 **Test Categories**

### **End-to-End Tests** (`test_alert_processing_e2e.py`)
- Happy path Kubernetes alert processing
- Agent selection and delegation
- Iterative LLM-MCP interaction loops
- Error handling scenarios
- Data flow validation

### **Component Tests** (`test_component_integration.py`)  
- Agent Registry and Factory integration
- MCP Server Registry management
- Service interaction patterns
- Error propagation between components

### **Edge Cases** (`test_edge_cases.py`)
- Large inputs (17KB+ messages)
- Unicode and special characters
- Concurrent processing (10+ simultaneous alerts)
- Resource exhaustion simulation
- Boundary conditions and limits

## 🔧 **Troubleshooting**

### **Common Issues**
- **Import Errors**: Run `uv sync --extra test` to install dependencies
- **Mock Behavior**: Check fixture configuration in `conftest.py`
- **Timeout Issues**: Adjust timeout values for slower environments

### **Debug Mode**
```bash
# Detailed debugging
uv run pytest tests/integration/ -v -s --tb=long

# Single test debugging  
uv run pytest tests/integration/test_alert_processing_e2e.py::TestAlertProcessingE2E::test_happy_path_kubernetes_alert_processing -v -s
``` 