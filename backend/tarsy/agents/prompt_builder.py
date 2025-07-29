"""
Prompt builder for constructing LLM prompts used in agent analysis.

This module centralizes all prompt template logic, making it easier to maintain
and modify prompts without touching business logic in agents.
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class PromptContext:
    """Context data needed for prompt building."""
    agent_name: str
    alert_data: Dict[str, Any]
    runbook_content: str
    mcp_data: Dict[str, Any]
    mcp_servers: List[str]
    server_guidance: str = ""
    agent_specific_guidance: str = ""
    available_tools: Optional[Dict] = None
    iteration_history: Optional[List[Dict]] = None
    current_iteration: Optional[int] = None
    max_iterations: Optional[int] = None

class PromptBuilder:
    """
    Centralized prompt builder for all agent operations.
    
    This class handles the construction of all prompts used by agents,
    separating template logic from business logic in agents.
    
    This class is stateless and designed to be shared across agent instances.
    """
    
    def __init__(self):
        """Initialize the prompt builder."""
        pass
    
    def build_analysis_prompt(self, context: PromptContext) -> str:
        """
        Build comprehensive analysis prompt for alert analysis.
        
        Args:
            context: Prompt context containing all necessary data
            
        Returns:
            Formatted analysis prompt
        """
        prompt_parts = [
            self._build_context_section(context),
            self._build_alert_section(context.alert_data),
            self._build_runbook_section(context.runbook_content),
            self._build_mcp_data_section(context.mcp_data),
            self._build_agent_specific_analysis_guidance(context),
            self._build_analysis_instructions()
        ]
        
        return "\n\n".join(prompt_parts)
    
    def build_mcp_tool_selection_prompt(self, context: PromptContext) -> str:
        """
        Build MCP tool selection prompt for initial tool selection.
        
        Args:
            context: Prompt context containing all necessary data
            
        Returns:
            Formatted tool selection prompt
        """
        return f"""# MCP Tool Selection Request

Based on the following alert and runbook, determine which MCP tools should be called to gather additional information.

{context.server_guidance}

## Alert Information
{self._build_alert_section(context.alert_data)}

{self._build_runbook_section(context.runbook_content)}

## Available MCP Tools
{json.dumps(context.available_tools, indent=2)}

## Instructions
Analyze the alert and runbook to determine which MCP tools should be called and with what parameters.
Return a JSON list of tool calls in this format:

```json
[
  {{
    "server": "kubernetes",
    "tool": "get_namespace_status",
    "parameters": {{
      "cluster": "cluster_url_here",
      "namespace": "namespace_name_here"
    }},
    "reason": "Need to check namespace status to understand why it's stuck"
  }}
]
```

Focus on gathering the most relevant information to diagnose the issue described in the alert."""
    
    def build_iterative_mcp_tool_selection_prompt(self, context: PromptContext) -> str:
        """
        Build iterative MCP tool selection prompt for follow-up tool selection.
        
        Args:
            context: Prompt context containing all necessary data
            
        Returns:
            Formatted iterative tool selection prompt
        """
        max_iterations = context.max_iterations or 5
        display_max = max_iterations if context.current_iteration <= max_iterations else context.current_iteration
        
        return f"""# Iterative MCP Tool Selection Request (Iteration {context.current_iteration})

You are analyzing a multi-step runbook. Based on the alert, runbook, and previous iterations, determine if more MCP tools need to be called or if you have sufficient information to complete the analysis.

{context.server_guidance}

## Alert Information
{self._build_alert_section(context.alert_data)}

{self._build_runbook_section(context.runbook_content)}

## Available MCP Tools
{json.dumps(context.available_tools, indent=2)}

## Previous Iterations History
{self._format_iteration_history(context.iteration_history)}

## Instructions
Based on the runbook steps and what has been discovered so far, determine if you need to call more MCP tools or if the analysis can be completed.

**IMPORTANT**: You are currently on iteration {context.current_iteration} of {display_max} maximum iterations. Be judicious about continuing - only continue if you genuinely need critical missing information that prevents completing the analysis.

Return a JSON object in this format:

If more tools are needed:
```json
{{
  "continue": true,
  "reasoning": "Specific explanation of what critical information is missing and why it's needed to complete the runbook steps",
  "tools": [
    {{
      "server": "kubernetes",
      "tool": "tool_name",
      "parameters": {{
        "param1": "value1"
      }},
      "reason": "Why this specific tool call is needed"
    }}
  ]
}}
```

If analysis can be completed:
```json
{{
  "continue": false,  
  "reasoning": "Explanation of what sufficient information has been gathered and why analysis can now be completed"
}}
```

**Default to stopping if you have reasonable data to work with.** The analysis doesn't need to be perfect - it needs to be actionable based on the runbook steps."""
    
    def build_partial_analysis_prompt(self, context: PromptContext) -> str:
        """
        Build partial analysis prompt for intermediate analysis steps.
        
        Args:
            context: Prompt context containing all necessary data
            
        Returns:
            Formatted partial analysis prompt
        """
        return f"""# Partial Analysis Request (Iteration {context.current_iteration})

Analyze the current findings from this iteration and provide insights about what has been discovered so far.

## Alert Information
{self._build_alert_section(context.alert_data)}

{self._build_runbook_section(context.runbook_content)}

## Iteration History
{self._format_iteration_history(context.iteration_history)}

## Instructions
Provide a concise analysis of what has been discovered in this iteration:

1. **Key Findings**: What important information was gathered in this iteration?
2. **Progress Assessment**: How does this align with the runbook steps?
3. **Next Steps Guidance**: What should be investigated next (if anything)?
4. **Confidence Level**: How confident are you in the current understanding of the issue?

Keep this analysis focused and concise - this is an intermediate step, not the final analysis."""
    
    def _build_context_section(self, context: PromptContext) -> str:
        """Build the context section of the prompt."""
        server_list = ", ".join(context.mcp_servers)
        
        return f"""# SRE Alert Analysis Request

You are an expert Site Reliability Engineer (SRE) analyzing a system alert using the {context.agent_name}.
This agent specializes in {server_list} operations and has access to domain-specific tools and knowledge.

Your task is to provide a comprehensive analysis of the incident based on:
1. The alert information
2. The associated runbook
3. Real-time system data from MCP servers

Please provide detailed, actionable insights about what's happening and potential next steps."""
    
    def _build_alert_section(self, alert_data: Dict) -> str:
        """
        Build the alert section of the prompt with flexible data support.
        
        Uses LLM-First Processing approach: displays all alert data as key-value pairs
        for intelligent interpretation by the LLM, rather than hardcoding field expectations.
        """
        if not alert_data:
            return "## Alert Details\n\nNo alert data provided."
        
        alert_text = "## Alert Details\n\n"
        
        # Process all alert data dynamically - LLM-First Processing
        for key, value in alert_data.items():
            # Format the key as human-readable
            formatted_key = key.replace('_', ' ').title()
            
            # Handle different value types intelligently
            if isinstance(value, dict):
                # Nested object - format as JSON for LLM interpretation
                formatted_value = f"\n```json\n{json.dumps(value, indent=2)}\n```"
            elif isinstance(value, list):
                # Array - format as JSON for LLM interpretation
                formatted_value = f"\n```json\n{json.dumps(value, indent=2)}\n```"
            elif isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                # Potential JSON string - try to format it
                try:
                    parsed_json = json.loads(value)
                    formatted_value = f"\n```json\n{json.dumps(parsed_json, indent=2)}\n```"
                except json.JSONDecodeError:
                    # Not valid JSON, treat as regular string
                    formatted_value = str(value)
            elif isinstance(value, str) and '\n' in value:
                # Multi-line string (like YAML) - preserve formatting
                formatted_value = f"\n```\n{value}\n```"
            else:
                # Simple value - display as-is
                formatted_value = str(value) if value is not None else "N/A"
            
            alert_text += f"**{formatted_key}:** {formatted_value}\n"
        
        return alert_text.strip()
    
    def _build_runbook_section(self, runbook_content: str) -> str:
        """Build the runbook section of the prompt."""
        return f"""## Runbook Content
```markdown
<!-- RUNBOOK START -->
{runbook_content if runbook_content else 'No runbook available'}
<!-- RUNBOOK END -->
```"""
    
    def _build_mcp_data_section(self, mcp_data: Dict) -> str:
        """Build the MCP data section of the prompt."""
        if not mcp_data:
            return "## System Data (MCP Servers)\n\nNo system data available from MCP servers."
        
        mcp_text = "## System Data (MCP Servers)\n\n"
        
        for server_name, server_data in mcp_data.items():
            mcp_text += f"### {server_name.title()} MCP Server Data\n\n"
            
            if isinstance(server_data, list):
                # Handle list of tool results
                for i, item in enumerate(server_data):
                    tool_name = item.get('tool', f'result_{i+1}')
                    if 'result' in item:
                        mcp_text += f"**{tool_name}_result:**\n```\n{self._format_data(item['result'])}\n```\n\n"
                    elif 'error' in item:
                        mcp_text += f"**{tool_name}_error:** {item['error']}\n\n"
                    else:
                        mcp_text += f"**{tool_name}:**\n```\n{self._format_data(item)}\n```\n\n"
            elif isinstance(server_data, dict):
                # Handle legacy dict format (for backward compatibility)
                for key, value in server_data.items():
                    mcp_text += f"**{key}:**\n```\n{self._format_data(value)}\n```\n\n"
            else:
                # Handle other data types
                mcp_text += f"```\n{self._format_data(server_data)}\n```\n\n"
        
        return mcp_text.strip()
    
    def _build_agent_specific_analysis_guidance(self, context: PromptContext) -> str:
        """Build agent-specific analysis guidance."""
        guidance_parts = []
        
        # Add server-specific guidance if available
        if context.server_guidance:
            guidance_parts.append("## Domain-Specific Analysis Guidance")
            guidance_parts.append(context.server_guidance)
        
        # Add custom agent guidance if available
        if context.agent_specific_guidance:
            guidance_parts.append("### Agent-Specific Guidance")
            guidance_parts.append(context.agent_specific_guidance)
        
        return "\n\n".join(guidance_parts) if guidance_parts else ""
    
    def _build_analysis_instructions(self) -> str:
        """Build the analysis instructions section."""
        return """## Analysis Instructions

Please provide your analysis in the following structured format:

# 🚨 1. QUICK SUMMARY
**Provide a brief, concrete summary (2-3 sentences maximum):**
- What specific resource is affected (include **name**, **type**, **namespace** if applicable)
- What exactly is wrong with it
- Root cause in simple terms

---

# ⚡ 2. RECOMMENDED ACTIONS

## 🔧 Immediate Fix Actions (if any):
**List specific commands that could potentially resolve the issue, in order of priority:**
- Command 1. Explanation of what this does
```command
command here
```
- Command 2. Explanation of what this does
```command
command here
```

## 🔍 Investigation Actions (if needed):
**List commands for further investigation:**
- Command 1. What information this will provide
```command
command here
```
- Command 2. What information this will provide
```command
command here
```

---

## 3. DETAILED ANALYSIS

### Root Cause Analysis:
- What is the primary cause of this alert?
- What evidence from the system data supports this conclusion?
- Technical details and context

### Current System State:
- Detailed state of affected systems and resources
- Any blocked processes or dependencies preventing resolution
- Related system dependencies and interactions

### Impact Assessment:
- Current impact on system functionality
- Potential escalation scenarios
- Affected services or users

### Prevention Measures:
- How can this issue be prevented in the future?
- Monitoring improvements needed
- Process or automation recommendations

### Additional Context:
- Related systems that should be monitored
- Historical patterns or similar incidents
- Any other relevant technical details

Please be specific and reference the actual data provided. Use exact resource names, namespaces, and status information from the system data."""
    
    def _format_data(self, data) -> str:
        """Format data for display in prompt."""
        if isinstance(data, (dict, list)):
            try:
                return json.dumps(data, indent=2, default=str)
            except:
                return str(data)
        return str(data)
    
    def _format_iteration_history(self, iteration_history: List[Dict]) -> str:
        """Format iteration history for display in prompts."""
        if not iteration_history:
            return "No previous iterations."
        
        TOOL_RESULT_TRUNCATION_THRESHOLD = 3000  # Characters before truncating
        
        history_text = ""
        for i, iteration in enumerate(iteration_history, 1):
            history_text += f"### Iteration {i}\n"
            
            # Tools called
            if "tools_called" in iteration and iteration["tools_called"]:
                history_text += "**Tools Called:**\n"
                for tool in iteration["tools_called"]:
                    history_text += f"- {tool.get('server', 'unknown')}.{tool.get('tool', 'unknown')}: {tool.get('reason', 'No reason provided')}\n"
                history_text += "\n"
            
            # Results with actual data content
            if "mcp_data" in iteration and iteration["mcp_data"]:
                history_text += "**Results:**\n"
                for server_name, server_data in iteration["mcp_data"].items():
                    data_count = len(server_data) if isinstance(server_data, list) else 1
                    history_text += f"- **{server_name}**: {data_count} data points collected\n"
                    
                    # Handle both list format (new) and dict format (legacy)
                    if isinstance(server_data, list):
                        # New format: list of results with metadata
                        for item in server_data:
                            tool_name = item.get('tool', 'unknown_tool')
                            params = item.get('parameters', {})
                            
                            # Create a descriptive key for the result
                            if tool_name == 'resources_list' and 'kind' in params or tool_name == 'resources_get' and 'kind' in params:
                                result_key = f"{tool_name}_{params['kind']}_result"
                            else:
                                result_key = f"{tool_name}_result"
                            
                            # Handle both result and error cases
                            if 'result' in item:
                                result = item['result']
                                if result:  # Only show non-empty results
                                    formatted_data = self._format_data({"result": result})
                                    if len(formatted_data) > TOOL_RESULT_TRUNCATION_THRESHOLD:
                                        formatted_data = formatted_data[:TOOL_RESULT_TRUNCATION_THRESHOLD] + "\n... [truncated for brevity]"
                                    history_text += f"  - **{result_key}**:\n```\n{formatted_data}\n```\n"
                            elif 'error' in item:
                                history_text += f"  - **{result_key}_error**: {item['error']}\n"
                    elif isinstance(server_data, dict):
                        # Legacy format: dict with keys like "tool_name_result"
                        for key, value in server_data.items():
                            formatted_data = self._format_data(value)
                            if len(formatted_data) > TOOL_RESULT_TRUNCATION_THRESHOLD:
                                formatted_data = formatted_data[:TOOL_RESULT_TRUNCATION_THRESHOLD] + "\n... [truncated for brevity]"
                            history_text += f"  - **{key}**:\n```\n{formatted_data}\n```\n"
                    else:
                        formatted_data = self._format_data(server_data)
                        if len(formatted_data) > TOOL_RESULT_TRUNCATION_THRESHOLD:
                            formatted_data = formatted_data[:TOOL_RESULT_TRUNCATION_THRESHOLD] + "\n... [truncated for brevity]"
                        history_text += f"```\n{formatted_data}\n```\n"
                history_text += "\n"
            
            # Partial analysis
            if "partial_analysis" in iteration:
                history_text += f"**Partial Analysis:**\n{iteration['partial_analysis']}\n\n"
            
            history_text += "---\n\n"
        
        return history_text.strip()


    def get_general_instructions(self) -> str:
        """
        Get general SRE instructions common to all agents.
        
        Returns:
            General instruction text for system messages
        """
        return """## General SRE Agent Instructions

You are an expert Site Reliability Engineer (SRE) with deep knowledge of:
- Kubernetes and container orchestration
- Cloud infrastructure and services
- Incident response and troubleshooting
- System monitoring and alerting
- GitOps and deployment practices

Analyze alerts thoroughly and provide actionable insights based on:
1. Alert information and context
2. Associated runbook procedures
3. Real-time system data from available tools

Always be specific, reference actual data, and provide clear next steps.
Focus on root cause analysis and sustainable solutions."""

    def get_mcp_tool_selection_system_message(self) -> str:
        """Get system message for MCP tool selection."""
        return "You are an expert SRE analyzing alerts. Based on the alert, runbook, and available MCP tools, determine which tools should be called to gather the necessary information for diagnosis. Return only a valid JSON array with no additional text."
    
    def get_iterative_mcp_tool_selection_system_message(self) -> str:
        """Get system message for iterative MCP tool selection."""
        return "You are an expert SRE analyzing alerts through multi-step runbooks. Based on the alert, runbook, available MCP tools, and previous iteration results, determine what tools should be called next or if the analysis is complete. Return only a valid JSON object with no additional text."
    
    def get_partial_analysis_system_message(self) -> str:
        """Get system message for partial analysis."""
        return "You are an expert SRE analyzing alerts through multi-step runbooks. Analyze the current findings and provide insights about what has been discovered so far and what might be needed next."


# Shared instance since PromptBuilder is stateless
_shared_prompt_builder = PromptBuilder()


def get_prompt_builder() -> PromptBuilder:
    """Get the shared PromptBuilder instance."""
    return _shared_prompt_builder 