# MCP and LLM Integration

This document explains how the SRE Alert Analyzer now uses LLMs to dynamically determine which MCP tools to call based on the alert and runbook content.

## Overview

Instead of using hardcoded rules to determine which MCP tools to call, the system now:

1. **Downloads and parses the runbook** for the alert
2. **Lists available MCP tools** from configured MCP servers
3. **Uses an LLM to determine** which tools should be called based on:
   - The alert details (type, severity, cluster, namespace, etc.)
   - The runbook content and troubleshooting steps
   - The available MCP tools and their descriptions
4. **Executes the selected tools** to gather system data
5. **Performs final analysis** using the LLM with all collected data

## Key Components

### 1. MCPClient (`app/integrations/mcp/mcp_client.py`)

This client uses the official MCP SDK to integrate with MCP servers. It provides:

- Automatic MCP server initialization using command/args configuration
- Tool listing from MCP servers
- LangChain tool creation for seamless integration
- Direct tool calling capabilities
- Stdio transport for connecting to MCP servers

### 2. Enhanced LLM Client (`app/integrations/llm/client.py`)

The LLM client now includes a `determine_mcp_tools` method that:

- Takes alert data, runbook data, and available tools as input
- Prompts the LLM to determine which tools to call
- Returns a structured JSON array of tool calls with parameters

### 3. Updated Alert Service (`app/services/alert_service.py`)

The alert service now:

- Uses `MCPClient` with the official MCP SDK
- Calls the LLM to determine which MCP tools to use
- Has fallback logic for when LLM is unavailable

## Configuration

### MCP Server Configuration

The MCP server configuration is now in `settings.py`:

```python
mcp_servers: Dict[str, Any] = Field(
    default={
        "kubernetes": {
            "type": "kubernetes",
            "enabled": True,
            "command": "npx",
            "args": ["-y", "kubernetes-mcp-server@latest"]
        }
    }
)
```

This uses the npx command to run the Kubernetes MCP server directly, without needing a separate server process.

### Environment Variables

The only required environment variables are now:

- `GITHUB_TOKEN`: For downloading runbooks from GitHub
- LLM API keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, etc.
- `DEFAULT_LLM_PROVIDER`: Which LLM provider to use by default

## How It Works

### Example Flow

1. **Alert Received**:
   ```json
   {
     "alert": "Namespace is stuck in Terminating",
     "cluster": "production-k8s",
     "namespace": "test-app",
     "severity": "high"
   }
   ```

2. **LLM Determines Tools**:
   The LLM analyzes the alert and runbook, then returns:
   ```json
   [
     {
       "server": "kubernetes",
       "tool": "resources_get",
       "parameters": {
         "apiVersion": "v1",
         "kind": "Namespace",
         "name": "test-app"
       },
       "reason": "Get namespace details including finalizers"
     },
     {
       "server": "kubernetes",
       "tool": "events_list",
       "parameters": {
         "namespace": "test-app"
       },
       "reason": "Check for events explaining the stuck state"
     }
   ]
   ```

3. **Tools Executed**:
   The system calls the selected MCP tools and gathers data.

4. **Final Analysis**:
   The LLM analyzes all collected data and provides recommendations.

## Benefits

1. **Adaptive**: The system adapts to different alert types without hardcoding
2. **Contextual**: Tool selection is based on actual runbook content
3. **Extensible**: New MCP servers and tools are automatically available
4. **Intelligent**: LLM understands the relationship between alerts, runbooks, and available tools

## Fallback Behavior

If the LLM is unavailable or fails, the system falls back to:

1. Basic rule-based tool selection for known alert types
2. Simplified analysis without LLM insights
3. Manual review recommendations

## Available Kubernetes MCP Tools

The Kubernetes MCP server (https://github.com/manusa/kubernetes-mcp-server) provides tools like:

- `namespaces_list`: List all namespaces
- `resources_get`: Get any Kubernetes resource
- `resources_list`: List resources of any type
- `resources_create_or_update`: Create or update resources
- `resources_delete`: Delete resources
- `pods_list`: List pods
- `pods_exec`: Execute commands in pods
- `events_list`: List events
- And many more...

The LLM can intelligently select from these tools based on the alert context.

## Technical Details

### MCP SDK Integration

The implementation uses the official MCP SDK's stdio transport to connect to MCP servers. This provides:

- Reliable bidirectional communication
- Proper session management
- Tool discovery and invocation
- Error handling and recovery

### LangChain Integration

The MCPClient creates LangChain-compatible tools from MCP tools, enabling:

- Seamless integration with LangChain agents
- Tool calling through the LLM
- Consistent interface for all tools
- Type safety and validation 