# MCP and LLM Integration - Iterative Processing Architecture

This document explains how the SRE AI Agent uses an advanced iterative approach with LLMs to dynamically investigate alerts through multi-step MCP tool execution, mimicking human troubleshooting methodology.

## Overview

The system uses an **iterative, multi-step approach**:

1. **Downloads and parses the runbook** for the alert
2. **Lists available MCP tools** from configured MCP servers  
3. **Iterative LLM-driven processing** (up to 5 iterations by default):
   - **Initial Tool Selection**: LLM determines which tools to call based on alert, runbook, and available tools
   - **Data Gathering**: Execute selected MCP tools to collect system data
   - **Partial Analysis**: LLM analyzes current findings and determines next steps
   - **Continuation Decision**: LLM decides whether to continue with more tools or stop
   - **Tool Selection for Next Iteration**: If continuing, LLM selects additional tools based on current findings
4. **Final Comprehensive Analysis**: LLM performs complete analysis with all gathered data and iteration history
5. **Iteration Summary**: Detailed summary of the entire investigative process

## Key Components

### 1. MCPClient (`app/integrations/mcp/mcp_client.py`)

This client uses the official MCP SDK to integrate with MCP servers. It provides:

- Automatic MCP server initialization using command/args configuration
- Tool listing from MCP servers
- LangChain tool creation for seamless integration
- Direct tool calling capabilities
- Stdio transport for connecting to MCP servers

### 2. Enhanced LLM Client (`app/integrations/llm/client.py`)

The LLM client now includes multiple methods for iterative processing:

- **`determine_mcp_tools`**: Initial tool selection for first iteration
  - Takes alert data, runbook data, and available tools as input
  - Returns structured JSON array of tool calls with parameters

- **`determine_next_mcp_tools`**: Iterative tool selection for subsequent iterations
  - Takes current context plus iteration history
  - Decides whether to continue processing or stop
  - Returns next tools to call or completion signal

- **`analyze_partial_results`**: Analyzes findings from each iteration
  - Provides insights on current data collected
  - Guides decision making for next iteration

- **`analyze_alert`**: Final comprehensive analysis
  - Integrates all data and iteration history
  - Provides complete incident analysis and recommendations

### 3. Updated Alert Service (`app/services/alert_service.py`)

The alert service now implements sophisticated iterative processing:

- **Iterative Loop Management**: Controls up to 5 iterations of LLM→MCP→Analysis cycles
- **Progress Tracking**: Real-time progress updates via WebSocket
- **Iteration History**: Maintains complete history of all iterations for context
- **Safety Mechanisms**: Prevents infinite loops with multiple safeguards:
  - Maximum iteration limit (configurable, default: 5)
  - Maximum tool call limit (hard limit: 15 total)
  - Data collection thresholds (stops after substantial data is collected)
- **Smart Continuation Logic**: LLM decides whether to continue or stop based on findings
- **Comprehensive Fallback**: Graceful degradation when LLM is unavailable
- **Enhanced Data Structure**: Preserves tool metadata, reasoning, and results across iterations

## Configuration

### MCP Server Configuration

The MCP server configuration is in `backend/app/config/settings.py`:

```python
# MCP Servers Configuration
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

# Alert Processing Configuration  
max_llm_mcp_iterations: int = Field(
    default=5,
    description="Maximum number of LLM->MCP iterative loops for multi-step runbook processing"
)
```

This uses the npx command to run the Kubernetes MCP server directly via stdio transport, without needing a separate server process. The `max_llm_mcp_iterations` setting controls how many iterative cycles are allowed.

### Environment Variables

The required environment variables are:

- `GITHUB_TOKEN`: For downloading runbooks from GitHub
- **LLM API keys** (at least one required):
  - `GEMINI_API_KEY`: Google Gemini API key
  - `OPENAI_API_KEY`: OpenAI API key  
  - `GROK_API_KEY`: xAI Grok API key
- `DEFAULT_LLM_PROVIDER`: Which LLM provider to use by default (gemini, openai, or grok)

## How It Works

### Example Iterative Flow

1. **Alert Received**:
   ```json
   {
     "alert": "Namespace is stuck in Terminating",
     "cluster": "production-k8s",
     "namespace": "test-app", 
     "severity": "high"
   }
   ```

2. **Iteration 1 - Initial Investigation**:
   
   **LLM Tool Selection**:
   ```json
   [
     {
       "server": "kubernetes",
       "tool": "resources_get",
       "parameters": {"apiVersion": "v1", "kind": "Namespace", "name": "test-app"},
       "reason": "Get namespace details including finalizers"
     },
     {
       "server": "kubernetes", 
       "tool": "events_list",
       "parameters": {"namespace": "test-app"},
       "reason": "Check for events explaining the stuck state"
     }
   ]
   ```

   **Data Gathered**: Namespace details show finalizers, events show deletion attempts
   
   **Partial Analysis**: "Namespace has finalizers blocking deletion. Need to investigate resources preventing cleanup."

3. **Iteration 2 - Deep Dive into Resources**:
   
   **LLM Determines Next Steps**:
   ```json
   {
     "continue": true,
     "reasoning": "Found finalizers, need to check what resources are preventing deletion",
     "tools": [
       {
         "server": "kubernetes",
         "tool": "resources_list", 
         "parameters": {"apiVersion": "v1", "kind": "Pod", "namespace": "test-app"},
         "reason": "Check for pods that might be stuck"
       },
       {
         "server": "kubernetes",
         "tool": "resources_list",
         "parameters": {"apiVersion": "v1", "kind": "PersistentVolumeClaim", "namespace": "test-app"}, 
         "reason": "Check for PVCs that might prevent deletion"
       }
     ]
   }
   ```

   **Data Gathered**: Found stuck pods and PVCs
   
   **Partial Analysis**: "Identified specific pods and PVCs blocking namespace deletion."

4. **Iteration 3 - Root Cause Analysis**:
   
   **LLM Determines Completion**:
   ```json
   {
     "continue": false,
     "reasoning": "Sufficient data collected to identify root cause and provide solution"
   }
   ```

5. **Final Comprehensive Analysis**:
   LLM analyzes all data across iterations and provides:
   - Root cause identification
   - Step-by-step remediation plan
   - Prevention recommendations
   - Complete iteration summary

## Benefits

1. **Iterative Intelligence**: Multi-step investigation mimics human troubleshooting approach
2. **Context-Aware**: Each iteration builds on previous findings for deeper analysis
3. **Adaptive**: System adapts to different alert types and complexities without hardcoding
4. **Comprehensive**: Captures complete investigation history and reasoning
5. **Efficient**: Stops automatically when sufficient data is collected
6. **Safe**: Multiple safeguards prevent infinite loops and excessive resource usage
7. **Extensible**: New MCP servers and tools are automatically available
8. **Transparent**: Complete audit trail of all decisions and data collection

## Safety Mechanisms

The iterative system includes multiple safeguards:

1. **Maximum Iterations**: Hard limit (default: 5) prevents infinite loops
2. **Tool Call Limits**: Maximum 15 total tool calls across all iterations  
3. **Data Thresholds**: Automatic stop when substantial data is collected
4. **LLM Decision Control**: LLM can decide to stop at any iteration
5. **Error Handling**: Graceful handling of failed tool calls
6. **Progress Tracking**: Real-time monitoring of processing status

## Fallback Behavior

If the LLM is unavailable or fails:

1. **First Iteration**: Falls back to basic rule-based tool selection for known alert types
2. **Later Iterations**: Stops processing and provides fallback analysis
3. **Comprehensive Fallback Analysis**: Detailed summary of collected data and manual review steps
4. **Iteration History Preservation**: All collected data and partial analyses are still available

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

## Data Structures

### Iteration History

Each iteration maintains a comprehensive record:

```python
iteration_record = {
    "iteration": 1,
    "reasoning": "LLM reasoning for tool selection",
    "tools_called": [
        {
            "server": "kubernetes",
            "tool": "resources_get", 
            "parameters": {"apiVersion": "v1", "kind": "Namespace", "name": "test-app"},
            "reason": "Get namespace details including finalizers"
        }
    ],
    "mcp_data": {
        "kubernetes": [
            {
                "tool": "resources_get",
                "parameters": {...},
                "reason": "Get namespace details...",
                "result": {...}  # or "error": "..." if failed
            }
        ]
    },
    "partial_analysis": "Namespace has finalizers blocking deletion..."
}
```

### Tool Call Results

Each MCP tool call result preserves complete context:

```python
tool_result = {
    "tool": "resources_get",
    "parameters": {"apiVersion": "v1", "kind": "Namespace", "name": "test-app"},
    "reason": "Get namespace details including finalizers", 
    "result": {...}  # Success result
    # OR
    "error": "Connection failed"  # Error message
}
```

## Technical Details

### MCP SDK Integration

The implementation uses the official MCP SDK's stdio transport to connect to MCP servers. This provides:

- Reliable bidirectional communication
- Proper session management  
- Tool discovery and invocation
- Error handling and recovery
- Automatic server lifecycle management

### LangChain Integration

The MCPClient creates LangChain-compatible tools from MCP tools, enabling:

- Seamless integration with LangChain agents
- Tool calling through the LLM
- Consistent interface for all tools
- Type safety and validation
- Unified error handling across providers

### Iterative Processing Engine

The alert service implements a sophisticated processing engine:

- **State Management**: Tracks complete iteration state and history
- **Progress Reporting**: Real-time WebSocket updates with detailed progress
- **Resource Management**: Automatic cleanup and connection management
- **Error Recovery**: Graceful handling of failures at any stage
- **Performance Monitoring**: Tracks tool call counts and data collection metrics

## Monitoring and Observability

The iterative system provides comprehensive observability:

### Logging

- **MCP Communications**: Detailed request/response logging for all MCP interactions
- **LLM Communications**: Complete prompt/response logging with request IDs
- **Iteration Progress**: Step-by-step iteration logging with timing and decisions
- **Error Tracking**: Comprehensive error logging with context and recovery actions

### Metrics

- **Iteration Counts**: Number of iterations per alert type
- **Tool Usage**: Most frequently used MCP tools
- **Processing Time**: Time spent in each phase (LLM analysis, MCP calls, etc.)
- **Success Rates**: LLM decision accuracy and MCP tool success rates
- **Data Collection**: Volume of data collected per iteration

### Real-time Progress

- **WebSocket Updates**: Live progress updates to frontend clients
- **Status Tracking**: Current iteration, tools being called, analysis phase
- **Progress Percentage**: Estimated completion percentage with step details

### Configuration Parameters

```python
# Tunable parameters in settings.py
max_llm_mcp_iterations: int = 5        # Maximum iterations allowed
max_total_tool_calls: int = 15         # Hard limit on total tool calls  
data_collection_threshold: int = 10    # Stop after this many data points
min_iterations_before_data_stop: int = 3  # Minimum iterations before data threshold applies
```

This monitoring ensures the system operates efficiently while providing complete visibility into the investigation process. 