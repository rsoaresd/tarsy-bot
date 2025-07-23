# SRE AI Agent

An intelligent Site Reliability Engineering agent that automatically processes alerts, retrieves runbooks, and uses MCP (Model Context Protocol) servers to gather system information for comprehensive incident analysis.

## Documentation

- **[README.md](README.md)**: This file - project overview and quick start
- **[setup.sh](setup.sh)**: Automated setup script (run this first!)
- **[DEPLOYMENT.md](DEPLOYMENT.md)**: Advanced deployment, production setup, and development
- **[backend/DEVELOPMENT.md](backend/DEVELOPMENT.md)**: Development setup guide and testing workflow
- **[docs/requirements.md](docs/requirements.md)**: Application requirements and specifications
- **[docs/design.md](docs/design.md)**: System design and architecture documentation

> **New Users**: Run `./setup.sh` to get started quickly!

## Key Features

### 🧠 Multi-Layer Agent Architecture (EP-0002)
The system implements a sophisticated multi-layer architecture:
- **Orchestrator Layer**: Routes alerts to specialized agents based on alert type
- **Specialized Agents**: Domain-specific agents (KubernetesAgent) with focused MCP server subsets
- **Intelligent Tool Selection**: LLM-driven selection of appropriate MCP tools from agent's assigned servers
- **Inheritance-Based Design**: Common processing logic shared across all specialized agents

### 📊 Comprehensive Audit Trail (EP-0003)
Complete visibility into alert processing workflows:
- **Session Tracking**: Persistent storage of all alert processing sessions with lifecycle management
- **Interaction Logging**: Automatic capture of all LLM interactions and MCP communications
- **Chronological Timeline**: Microsecond-precision reconstruction of complete processing workflows
- **Advanced Querying**: REST API with filtering, pagination, and complex query support
- **Dashboard Ready**: Foundation for SRE monitoring dashboards with comprehensive historical data

## Architecture

The SRE AI Agent implements a modern, multi-layer architecture:

- **Multi-Layer Backend**: FastAPI-based service with orchestrator and specialized agent layers
- **Agent Specialization**: Domain-specific agents (KubernetesAgent) with focused MCP server subsets
- **History Service**: Comprehensive audit trail capture with SQLModel database persistence
- **Alert Dev UI**: React TypeScript development interface for testing and demonstration
- **MCP Integration**: Official `mcp` library with agent-specific server assignments and hook context
- **LLM Support**: Unified LLM client supporting multiple providers (OpenAI, Google, xAI) with automatic interaction logging

## Features

### Core Processing
- **Multi-Layer Agent Architecture**: Orchestrator delegates to specialized agents based on alert type
- **Intelligent Tool Selection**: Agents use LLM to select appropriate tools from their assigned MCP server subset
- **Runbook Integration**: Automatic GitHub runbook download and distribution to specialized agents
- **Agent Specialization**: Domain-specific agents (KubernetesAgent) with focused capabilities

### History & Monitoring
- **Comprehensive Audit Trail**: Persistent capture of all alert processing workflows
- **Chronological Timeline**: Microsecond-precision reconstruction of complete processing history
- **Advanced Query API**: REST endpoints with filtering, pagination, and complex queries
- **Real-time & Historical Access**: Support for both active session monitoring and historical analysis

### Technical Features
- **Multi-LLM Support**: Configurable providers (OpenAI, Google, xAI) with unified client interface
- **Real-time Updates**: WebSocket-based progress tracking with agent identification
- **Database Flexibility**: SQLite with PostgreSQL migration support
- **Extensible Design**: Configuration-driven addition of new agents and MCP servers
- **Graceful Degradation**: Robust error handling with service-level fault tolerance

## How It Works

### Multi-Layer Processing Pipeline
1. **Alert Received**: System receives an alert (e.g., "Namespace stuck in Terminating")
2. **Agent Selection**: Orchestrator uses agent registry to select appropriate specialized agent (KubernetesAgent)
3. **History Session Created**: System creates persistent session for complete audit trail
4. **Runbook Downloaded**: Fetches the relevant runbook from GitHub and provides to selected agent
5. **Agent Initialization**: Agent configures with its assigned MCP server subset (kubernetes-server)
6. **Iterative Analysis**: Agent uses LLM to intelligently select and call tools from its server subset
7. **Comprehensive Logging**: All LLM interactions and MCP communications automatically captured
8. **Final Analysis**: Agent provides specialized domain analysis with complete processing history

### Audit Trail Capture
- **Automatic Logging**: HookContext system transparently captures all interactions
- **Microsecond Precision**: Exact chronological ordering of all processing steps
- **Complete Visibility**: Full audit trail available for debugging and monitoring
- **API Access**: Historical data accessible via REST endpoints for dashboard integration

## Project Structure

```
sre/
├── backend/                # FastAPI backend with multi-layer agent architecture
│   ├── app/
│   │   ├── agents/         # Specialized agent classes (KubernetesAgent, BaseAgent)
│   │   ├── controllers/    # API controllers and REST endpoints
│   │   ├── database/       # Database initialization and schema management
│   │   ├── hooks/          # Event hooks for automatic interaction capture
│   │   ├── models/         # Data models (Alert, History, API schemas)
│   │   ├── repositories/   # Database access layer with SQLModel
│   │   ├── services/       # Business logic (AlertService, HistoryService, AgentRegistry)
│   │   ├── integrations/   # External integrations (LLM providers, MCP servers)
│   │   ├── config/         # Configuration management
│   │   └── utils/          # Utility functions and logging
│   ├── tests/              # Comprehensive test suite (unit, integration, e2e)
│   ├── pyproject.toml      # Python dependencies and project configuration
│   └── env.template        # Environment variables template
├── alert-dev-ui/           # React TypeScript development interface
│   ├── src/
│   │   ├── components/     # React components (AlertForm, ProcessingStatus, ResultDisplay)
│   │   ├── services/       # API and WebSocket clients
│   │   └── types/          # TypeScript type definitions
│   └── package.json        # Node.js dependencies
├── docs/                   # Comprehensive documentation
│   ├── requirements.md     # Application requirements and specifications
│   ├── design.md           # Technical design and architecture documentation
│   └── enhancements/       # Enhancement proposal system
│       ├── implemented/    # Completed EPs (EP-0002 Multi-Layer Agents, EP-0003 History Service)
│       ├── pending/        # Pending enhancement proposals
│       └── templates/      # EP document templates
├── setup.sh                # Automated setup script
├── DEPLOYMENT.md           # Production deployment guide
└── docker-compose.yml      # Docker development environment
```

## Quick Start

### Automated Setup (Recommended)

```bash
./setup.sh
```

This will automatically:
- Check prerequisites
- Set up both backend and alert dev UI
- Create the environment file
- Install all dependencies
- Provide next steps for starting the services

### Manual Setup

For advanced users or troubleshooting, see [DEPLOYMENT.md](DEPLOYMENT.md) for detailed manual setup instructions.

## Running the Applications

After setup is complete, you can run both applications:

### Backend (FastAPI Server)
```bash
# Make sure you're in the project root directory first
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```
The backend will be available at: http://localhost:8000

### Alert Dev UI (React App)
```bash
# From the project root directory
cd alert-dev-ui
PORT=3001 npm start
```
The frontend will be available at: http://localhost:3001

> **Note**: Start the backend first, then the frontend. The React app is configured to proxy API requests to the backend.

### Troubleshooting

**If you get "No such file or directory" for .venv/bin/activate:**
- Make sure you're in the `backend/` directory, not the project root
- Run `pwd` to check your current location

**If you get "ModuleNotFoundError" for sqlmodel or other packages:**
```bash
cd backend
source .venv/bin/activate
uv sync  # This reinstalls all dependencies
uvicorn app.main:app --reload --port 8000
```

### Environment Configuration

The setup script will create `backend/.env` from the template. You'll need to add your API keys:

- **Google (Gemini)**: Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
- **OpenAI**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
- **xAI (Grok)**: Get from [xAI Console](https://console.x.ai/)
- **GitHub Token**: Get from [GitHub Settings](https://github.com/settings/tokens)

> **Note**: You need at least one LLM API key and the GitHub token for the agent to work.

## Usage

1. **Start the Backend**: The FastAPI server runs on http://localhost:8000
2. **Start the Alert Dev UI**: The React app runs on http://localhost:3001
3. **Submit an Alert**: Use the alert dev UI form to simulate an alert
4. **Monitor Progress**: Watch real-time progress updates
5. **View Results**: See the detailed LLM analysis

## Supported Alert Types

Currently supported:
- **Namespace stuck in Terminating**: Analyzes stuck Kubernetes namespaces

The LLM-driven approach means new alert types can be handled without code changes, as long as:
- A runbook exists for the alert
- The MCP servers have relevant tools available

## API Endpoints

### Core API
- `GET /` - Health check endpoint
- `GET /health` - Comprehensive health check with service status
- `POST /alerts` - Submit a new alert for processing
- `GET /alert-types` - Get supported alert types
- `GET /processing-status/{alert_id}` - Get processing status
- `WebSocket /ws/{alert_id}` - Real-time progress updates

### History API (EP-0003)
- `GET /api/v1/history/sessions` - List alert processing sessions with filtering and pagination
- `GET /api/v1/history/sessions/{session_id}` - Get detailed session with chronological timeline
- `GET /api/v1/history/health` - History service health check and database status

## Development

### Adding New Components

- **Alert Types**: Add to `supported_alerts` in `config/settings.py` and create corresponding runbooks
- **MCP Servers**: Update `mcp_servers` configuration in `settings.py` 
- **LLM Providers**: See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions

### Running Tests

```bash
# Install test dependencies and run integration tests
cd backend
uv sync --extra test
python tests/run_integration_tests.py
```

The test suite includes comprehensive end-to-end integration tests covering the complete alert processing pipeline, agent specialization, error handling, and performance scenarios with full mocking of external services.

### Architecture Documents

- [docs/requirements.md](docs/requirements.md): Application requirements and specifications
- [docs/design.md](docs/design.md): System design and architecture documentation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment and advanced configuration
