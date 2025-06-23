# SRE AI Agent

An intelligent Site Reliability Engineering agent that automatically processes alerts, retrieves runbooks, and uses MCP (Model Context Protocol) servers to gather system information for comprehensive incident analysis.

## Architecture

The SRE AI Agent consists of:

- **Backend**: FastAPI-based service that processes alerts and orchestrates LLM analysis
- **Frontend**: React TypeScript application for alert simulation and result viewing  
- **MCP Integration**: Kubernetes MCP server integration for system data gathering
- **LLM Support**: Multiple LLM providers (Gemini, OpenAI, Grok)

## Features

- **Alert Processing**: Handles "Namespace stuck in Terminating" alerts
- **Runbook Integration**: Downloads and processes runbooks from GitHub
- **MCP Server Communication**: Integrates with Kubernetes MCP server for real-time data
- **Multi-LLM Support**: Configurable LLM providers for analysis
- **Real-time Updates**: WebSocket-based progress tracking
- **Extensible Design**: Easy to add new alert types and MCP servers

## Project Structure

```
sre/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI application entry point
│   │   ├── models/         # Pydantic models
│   │   ├── services/       # Business logic services
│   │   ├── integrations/   # MCP and LLM integrations
│   │   ├── config/         # Configuration management
│   │   └── utils/          # Utility functions
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
- Kubernetes MCP Server running

### Backend Setup

```bash
cd backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
cp ../.env.example .env
# Edit .env with your API keys and configuration
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```env
# LLM API Keys
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
GROK_API_KEY=your_grok_api_key

# GitHub Configuration
GITHUB_TOKEN=your_github_token

# MCP Server Configuration
KUBERNETES_MCP_URL=http://localhost:8080

# Application Settings
DEFAULT_LLM_PROVIDER=gemini
LOG_LEVEL=INFO
```

## Usage

1. **Start the Backend**: The FastAPI server runs on http://localhost:8000
2. **Start the Frontend**: The React app runs on http://localhost:3001
3. **Submit an Alert**: Use the frontend form to simulate an alert
4. **Monitor Progress**: Watch real-time progress updates
5. **View Results**: See the detailed LLM analysis

## Supported Alert Types

Currently supported:
- **Namespace stuck in Terminating**: Analyzes stuck Kubernetes namespaces

## API Endpoints

- `POST /alerts` - Submit a new alert for processing
- `GET /alert-types` - Get supported alert types
- `GET /processing-status/{alert_id}` - Get processing status
- `WebSocket /ws/{alert_id}` - Real-time progress updates

## Development

### Adding New Alert Types

1. Add the alert type to `supported_alerts` in `config/settings.py`
2. Create corresponding runbook processing logic
3. Update the frontend form options

### Adding New MCP Servers

1. Create a new MCP client in `integrations/mcp/`
2. Register the server in `config/settings.py`
3. Update the MCP orchestrator to handle the new server

### Adding New LLM Providers

1. Create a new LLM client in `integrations/llm/`
2. Register the provider in `config/settings.py`
3. Update the LLM manager to support the new provider

## License

MIT License 