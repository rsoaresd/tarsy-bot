# SRE AI Agent

An intelligent Site Reliability Engineering agent that automatically processes alerts, retrieves runbooks, and uses MCP (Model Context Protocol) servers to gather system information for comprehensive incident analysis.

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
- **MCP Integration**: Uses `mcp-use` library for seamless MCP server integration
- **LLM Support**: Multiple LLM providers (OpenAI, Gemini, Anthropic, Grok)

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
│   │   │   │   └── mcp_use_client.py  # New mcp-use based client
│   │   │   └── llm/        # LLM provider integrations
│   │   ├── config/         # Configuration management
│   │   └── utils/          # Utility functions
│   ├── MCP_LLM_INTEGRATION.md  # Documentation for MCP/LLM integration
│   ├── pyproject.toml      # uv project configuration
│   └── requirements.txt    # Python dependencies
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   ├── types/          # TypeScript type definitions
│   │   └── utils/          # Utility functions
│   ├── package.json        # Node.js dependencies
│   └── tsconfig.json       # TypeScript configuration
├── .env.example           # Environment variables template
└── docker-compose.yml     # Docker setup for development
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- uv (Python package manager)
- npx (for running Kubernetes MCP server)

### Backend Setup

```bash
cd backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
cp env.template .env
# Edit .env with your API keys
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

### Environment Configuration

Copy `backend/env.template` to `backend/.env` and configure:

```env
# GitHub Configuration (for downloading runbooks)
GITHUB_TOKEN=your_github_token_here

# LLM API Keys (add the ones you want to use)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...
X_AI_API_KEY=xai-...

# Default LLM Provider
DEFAULT_LLM_PROVIDER=openai
```

Note: The Kubernetes MCP server is now automatically configured to use `npx` command.

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

- `POST /alerts` - Submit a new alert for processing
- `GET /alert-types` - Get supported alert types
- `GET /processing-status/{alert_id}` - Get processing status
- `WebSocket /ws/{alert_id}` - Real-time progress updates

## Development

### Adding New Alert Types

1. Add the alert type to `supported_alerts` in `config/settings.py`
2. Create a runbook in your GitHub repository
3. The LLM will automatically determine relevant MCP tools

### Adding New MCP Servers

1. Update the MCP server configuration in `settings.py`
2. The new server's tools will be automatically available to the LLM

### Adding New LLM Providers

Follow the existing pattern in `integrations/llm/` - the system uses LangChain for unified LLM access.
