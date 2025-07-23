# Development Setup Guide 🛠️

Fast, modern development setup for tarsy using **uv** for dependency management.

## 🚀 **Quick Start**

```bash
# Clone and setup development environment
cd sre/backend
uv sync --extra all

# Run integration tests
python tests/run_integration_tests.py
```

## 📦 **Environment Setup**

### **Development Environment**
```bash
# Full development setup with all tools
uv sync --extra all

# Test environment only
uv sync --extra test

# Production environment (minimal)
uv sync
```

### **Virtual Environment (Optional)**
```bash
# Create isolated environment
uv venv dev_env
source dev_env/bin/activate  # Linux/Mac
uv sync --extra all
```

## 🧪 **Running Tests**

### **Integration Tests**
```bash
# Run all integration tests
python tests/run_integration_tests.py

# Run with pytest directly
uv run pytest -m integration -v

# Run specific test categories
uv run pytest -k "kubernetes" -v          # Kubernetes-related tests
uv run pytest -k "error" -v               # Error handling tests
uv run pytest -k "concurrency" -v         # Performance tests
```

### **Test Coverage & Reporting**
```bash
# Generate coverage report
uv run pytest tests/integration/ --cov=app --cov-report=html

# Run tests in parallel
uv run pytest tests/integration/ -n auto

# Debug single test
uv run pytest tests/integration/test_alert_processing_e2e.py::TestAlertProcessingE2E::test_happy_path_kubernetes_alert_processing -v -s
```

## 🛠️ **Development Tools**

```bash
# Code formatting and linting
uv run black app/ tests/
uv run ruff check app/ tests/
uv run mypy app/
```

## 🐳 **Docker Development**

```dockerfile
# Dockerfile with uv
FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --extra test --frozen

COPY . .
CMD ["python", "tests/run_integration_tests.py"]
```

## 🔄 **CI/CD Setup**

```yaml
# GitHub Actions
- name: Set up uv
  uses: astral-sh/setup-uv@v1
  
- name: Install dependencies
  run: uv sync --extra test
  
- name: Run tests
  run: python tests/run_integration_tests.py
```

## 📋 **Test Overview**

The integration test suite validates the complete multi-layer agent architecture:

- **End-to-End Processing**: Complete alert processing pipeline
- **Agent Specialization**: KubernetesAgent with focused MCP server access
- **Error Handling**: Service failures, malformed responses, timeouts
- **Performance**: Concurrent processing, resource exhaustion, stress testing
- **Edge Cases**: Unicode support, large inputs, boundary conditions

All external services (LLM APIs, MCP servers, GitHub) are comprehensively mocked for reliable, fast testing.

## 📁 **Project Structure**

```
backend/
├── app/                    # Main application code
├── tests/
│   └── integration/        # Integration test suite
│       ├── conftest.py     # Test fixtures and mocks
│       ├── test_alert_processing_e2e.py
│       ├── test_component_integration.py
│       └── test_edge_cases.py
├── pyproject.toml          # Dependencies and configuration
└── uv.lock                # Locked dependencies
```

## 🎯 **Key Commands**

```bash
# Setup
uv sync --extra all

# Test
python tests/run_integration_tests.py

# Code Quality  
uv run black app/ tests/ && uv run ruff check app/ tests/

# Coverage
uv run pytest --cov=app --cov-report=html
``` 