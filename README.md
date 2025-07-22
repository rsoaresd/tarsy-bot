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

### 🧠 LLM-Driven MCP Tool Selection
The agent uses Large Language Models to intelligently determine which MCP tools to call based on:
- Alert context and severity
- Runbook content and troubleshooting steps  
- Available MCP server capabilities

This adaptive approach means the agent can handle various alert types without hardcoded rules.

## Architecture

The SRE AI Agent consists of:

- **Backend**: FastAPI-based service that processes alerts and orchestrates LLM analysis
- **Frontend**: React TypeScript application for alert simulation and result viewing  
- **MCP Integration**: Uses official `mcp` library for seamless MCP server integration
- **LLM Support**: Multiple LLM providers (OpenAI, Google, xAI)

## Features

- **Intelligent Alert Processing**: LLM determines relevant MCP tools dynamically
- **Runbook Integration**: Downloads and processes runbooks from GitHub
- **MCP Server Communication**: Integrates with Kubernetes MCP server for real-time data
- **Multi-LLM Support**: Configurable LLM providers for analysis and tool selection
- **Real-time Updates**: WebSocket-based progress tracking
- **Extensible Design**: Easy to add new alert types and MCP servers
- **Fallback Logic**: Graceful degradation when LLM is unavailable

## How It Works

1. **Alert Received**: System receives an alert (e.g., "Namespace stuck in Terminating")
2. **Runbook Downloaded**: Fetches the relevant runbook from GitHub
3. **LLM Tool Selection**: LLM analyzes the alert and runbook to determine which MCP tools to call
4. **Data Collection**: Selected MCP tools gather system data
5. **Final Analysis**: LLM provides comprehensive analysis and recommendations

## Project Structure

```
sre/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI application entry point
│   │   ├── models/         # Pydantic models
│   │   ├── services/       # Business logic services
│   │   ├── integrations/   # MCP and LLM integrations
│   │   │   ├── mcp/        # MCP server integrations
│   │   │   │   └── client.py      # Official MCP SDK client
│   │   │   └── llm/        # LLM provider integrations
│   │   ├── config/         # Configuration management
│   │   └── utils/          # Utility functions
│   ├── pyproject.toml      # uv project configuration and dependencies
│   ├── uv.lock            # Locked dependencies for reproducible builds
│   └── tests/             # Comprehensive integration test suite
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   ├── types/          # TypeScript type definitions
│   │   └── utils/          # Utility functions
│   ├── package.json        # Node.js dependencies
│   └── tsconfig.json       # TypeScript configuration
├── backend/env.template   # Environment variables template
└── docker-compose.yml     # Docker setup for development
```

## Quick Start

### Automated Setup (Recommended)

```bash
./setup.sh
```

This will automatically:
- Check prerequisites
- Set up both backend and frontend
- Create the environment file
- Install all dependencies
- Provide next steps for starting the services

### Manual Setup

For advanced users or troubleshooting, see [DEPLOYMENT.md](DEPLOYMENT.md) for detailed manual setup instructions.

### Environment Configuration

The setup script will create `backend/.env` from the template. You'll need to add your API keys:

- **Google (Gemini)**: Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
- **OpenAI**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
- **xAI (Grok)**: Get from [xAI Console](https://console.x.ai/)
- **GitHub Token**: Get from [GitHub Settings](https://github.com/settings/tokens)

> **Note**: You need at least one LLM API key and the GitHub token for the agent to work.

## Usage

1. **Start the Backend**: The FastAPI server runs on http://localhost:8000
2. **Start the Frontend**: The React app runs on http://localhost:3001
3. **Submit an Alert**: Use the frontend form to simulate an alert
4. **Monitor Progress**: Watch real-time progress updates
5. **View Results**: See the detailed LLM analysis

## Supported Alert Types

Currently supported:
- **Namespace stuck in Terminating**: Analyzes stuck Kubernetes namespaces

The LLM-driven approach means new alert types can be handled without code changes, as long as:
- A runbook exists for the alert
- The MCP servers have relevant tools available

## API Endpoints

- `GET /` - Health check endpoint
- `GET /health` - Health check endpoint
- `POST /alerts` - Submit a new alert for processing
- `GET /alert-types` - Get supported alert types
- `GET /processing-status/{alert_id}` - Get processing status
- `WebSocket /ws/{alert_id}` - Real-time progress updates

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
