# Tarsy-bot 🤖

An intelligent Site Reliability Engineering agent that automatically processes alerts, retrieves runbooks, and uses MCP (Model Context Protocol) servers to gather system information for comprehensive incident analysis.

Inspired by the spirit of sci-fi AI, TARSy is your reliable SRE operations companion for SRE operations. 🚀

## Documentation

- **[README.md](README.md)**: This file - project overview and quick start
- **[setup.sh](setup.sh)**: Automated setup script (run this first!)
- **[DEPLOYMENT.md](DEPLOYMENT.md)**: Advanced deployment, production setup, and development
- **[backend/DEVELOPMENT.md](backend/DEVELOPMENT.md)**: Development setup guide and testing workflow
- **[docs/requirements.md](docs/requirements.md)**: Application requirements and specifications
- **[docs/design.md](docs/design.md)**: System design and architecture documentation

> **New Users**: Run `./setup.sh` to get started quickly! 🎯

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

Tarsy implements a modern, multi-layer architecture:

- **Multi-Layer Backend**: FastAPI-based service with orchestrator and specialized agent layers
- **Agent Specialization**: Domain-specific agents (KubernetesAgent) with focused MCP server subsets
- **History Service**: Comprehensive audit trail capture with SQLModel database persistence
- **Alert Dev UI**: React TypeScript development interface for testing and demonstration
- **MCP Integration**: Official `mcp` library with agent-specific server assignments and hook context
- **LLM Support**: Unified LLM client supporting multiple providers (OpenAI, Google, xAI) with automatic interaction logging

## Features

### 🤖 Core Processing
- **Multi-Layer Agent Architecture**: Orchestrator delegates to specialized agents based on alert type
- **Intelligent Tool Selection**: Agents use LLM to select appropriate tools from their assigned MCP server subset
- **Runbook Integration**: Automatic GitHub runbook download and distribution to specialized agents
- **Agent Specialization**: Domain-specific agents (KubernetesAgent) with focused capabilities

### 📈 History & Monitoring
- **Comprehensive Audit Trail**: Persistent capture of all alert processing workflows
- **Chronological Timeline**: Microsecond-precision reconstruction of complete processing history
- **Advanced Query API**: REST endpoints with filtering, pagination, and complex queries
- **Real-time & Historical Access**: Support for both active session monitoring and historical analysis

### ⚡ Technical Features
- **Multi-LLM Support**: Configurable providers (OpenAI, Google, xAI) with unified client interface
- **Real-time Updates**: WebSocket-based progress tracking with agent identification
- **Database Flexibility**: SQLite with PostgreSQL migration support
- **Extensible Design**: Configuration-driven addition of new agents and MCP servers
- **Graceful Degradation**: Robust error handling with service-level fault tolerance

## How It Works

### 🔄 Multi-Layer Processing Pipeline
1. **Alert Received**: System receives an alert (e.g., "Namespace stuck in Terminating")
2. **Agent Selection**: Orchestrator uses agent registry to select appropriate specialized agent (KubernetesAgent)
3. **History Session Created**: System creates persistent session for complete audit trail
4. **Runbook Downloaded**: Fetches the relevant runbook from GitHub and provides to selected agent
5. **Agent Initialization**: Agent configures with its assigned MCP server subset (kubernetes-server)
6. **Iterative Analysis**: Agent uses LLM to intelligently select and call tools from its server subset
7. **Comprehensive Logging**: All LLM interactions and MCP communications automatically captured
8. **Final Analysis**: Agent provides specialized domain analysis with complete processing history

### 📝 Audit Trail Capture
- **Automatic Logging**: HookContext system transparently captures all interactions
- **Microsecond Precision**: Exact chronological ordering of all processing steps
- **Complete Visibility**: Full audit trail available for debugging and monitoring
- **API Access**: Historical data accessible via REST endpoints for dashboard integration

## Project Structure

```