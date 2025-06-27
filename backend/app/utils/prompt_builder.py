"""
Prompt builder utility for constructing LLM prompts.
"""

import json
from typing import Dict, List

# Constants
TOOL_RESULT_TRUNCATION_THRESHOLD = 3000  # Characters before truncating tool results


class PromptBuilder:
    """Builds prompts for LLM analysis."""
    
    def build_analysis_prompt(self, 
                            alert_data: Dict, 
                            runbook_data: Dict, 
                            mcp_data: Dict) -> str:
        """Build a comprehensive analysis prompt."""
        
        prompt_parts = [
            self._build_context_section(),
            self._build_alert_section(alert_data),
            self._build_runbook_section(runbook_data),
            self._build_mcp_data_section(mcp_data),
            self._build_analysis_instructions()
        ]
        
        return "\n\n".join(prompt_parts)
    
    def _build_context_section(self) -> str:
        """Build the context section of the prompt."""
        return """# SRE Alert Analysis Request

You are an expert Site Reliability Engineer (SRE) analyzing a system alert. 
Your task is to provide a comprehensive analysis of the incident based on:
1. The alert information
2. The associated runbook
3. Real-time system data from MCP servers

Please provide detailed, actionable insights about what's happening and potential next steps."""
    
    def _build_alert_section(self, alert_data: Dict) -> str:
        """Build the alert section of the prompt."""
        return f"""
**Alert Type:** {alert_data.get('alert', 'Unknown')}
**Severity:** {alert_data.get('severity', 'Unknown')}
**Environment:** {alert_data.get('environment', 'Unknown')}
**Cluster:** {alert_data.get('cluster', 'Unknown')}
**Namespace:** {alert_data.get('namespace', 'Unknown')}
**Pod:** {alert_data.get('pod', 'N/A')}
**Message:** {alert_data.get('message', 'No message provided')}
**Timestamp:** {alert_data.get('timestamp', 'Unknown')}"""
    
    def _build_runbook_section(self, runbook_data: Dict) -> str:
        """Build the runbook section of the prompt."""
        
        runbook_text = f"""## Associated Runbook

**Raw Content:**
```markdown
<!-- RUNBOOK START -->
{runbook_data.get('raw_content', 'No runbook content available')}
<!-- RUNBOOK END -->
```
"""
        
        return runbook_text
    
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
    
    def build_mcp_tool_selection_prompt(self, 
                                   alert_data: Dict, 
                                   runbook_data: Dict, 
                                   available_tools: Dict) -> str:
        """Build a prompt to determine which MCP tools to call."""
        
        return f"""# MCP Tool Selection Request

Based on the following alert and runbook, determine which MCP tools should be called to gather additional information.

## Alert Information
{self._build_alert_section(alert_data)}

## Runbook Content
```markdown
<!-- RUNBOOK START -->
{runbook_data.get('raw_content', 'No runbook available')}
<!-- RUNBOOK END -->
```

## Available MCP Tools
{json.dumps(available_tools, indent=2)}

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

    def build_iterative_mcp_tool_selection_prompt(self,
                                                alert_data: Dict,
                                                runbook_data: Dict,
                                                available_tools: Dict,
                                                iteration_history: List[Dict],
                                                current_iteration: int) -> str:
        """Build a prompt for iterative MCP tool selection."""
        
        return f"""# Iterative MCP Tool Selection Request (Iteration {current_iteration})

You are analyzing a multi-step runbook. Based on the alert, runbook, and previous iterations, determine if more MCP tools need to be called or if you have sufficient information to complete the analysis.

## Alert Information
{self._build_alert_section(alert_data)}

## Runbook Content
```markdown
<!-- RUNBOOK START -->
{runbook_data.get('raw_content', 'No runbook available')}
<!-- RUNBOOK END -->
```

## Available MCP Tools
{json.dumps(available_tools, indent=2)}

## Previous Iterations History
{self._format_iteration_history(iteration_history)}

## Instructions
Based on the runbook steps and what has been discovered so far, determine if you need to call more MCP tools or if the analysis can be completed.

**IMPORTANT**: You are currently on iteration {current_iteration} of {5 if current_iteration <= 5 else current_iteration} maximum iterations. Be judicious about continuing - only continue if you genuinely need critical missing information that prevents completing the analysis.

**Stop if you have ACTUALLY COMPLETED the diagnostic data gathering outlined in the runbook:**
- You have collected ALL the data specified in the runbook diagnostic steps
- You have the actual content/details of any resources mentioned as remaining or problematic
- You have specific identifiers, configurations, and states needed for remediation
- The runbook diagnostic phase is truly complete, not just understood

**Continue if ANY of these are true:**
- The runbook mentions specific resources/data that you haven't actually retrieved yet
- System status indicates remaining resources but you haven't fetched their details
- Error messages or conditions reference specific items you haven't examined
- The runbook has explicit diagnostic steps you haven't executed yet
- You know something exists but don't have its actual details

**CRITICAL: Don't confuse "knowing about" something with "having the actual data". If system status mentions specific items/resources/components, you need their detailed configuration/content, not just knowledge that they exist.**

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

    def build_partial_analysis_prompt(self,
                                    alert_data: Dict,
                                    runbook_data: Dict,
                                    iteration_history: List[Dict],
                                    current_iteration: int) -> str:
        """Build a prompt for partial analysis during iterations."""
        
        return f"""# Partial Analysis Request (Iteration {current_iteration})

Analyze the current findings from this iteration and provide insights about what has been discovered so far.

## Alert Information
{self._build_alert_section(alert_data)}

## Runbook Content
```markdown
<!-- RUNBOOK START -->
{runbook_data.get('raw_content', 'No runbook available')}
<!-- RUNBOOK END -->
```

## Iteration History
{self._format_iteration_history(iteration_history)}

## Instructions
Provide a concise analysis of what has been discovered in this iteration:

1. **Key Findings**: What important information was gathered in this iteration?
2. **Progress Assessment**: How does this align with the runbook steps?
3. **Next Steps Guidance**: What should be investigated next (if anything)?
4. **Confidence Level**: How confident are you in the current understanding of the issue?

Keep this analysis focused and concise - this is an intermediate step, not the final analysis."""

    def _format_iteration_history(self, iteration_history: List[Dict]) -> str:
        """Format iteration history for display in prompts."""
        if not iteration_history:
            return "No previous iterations."
        
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
                            if tool_name == 'resources_list' and 'kind' in params:
                                result_key = f"{tool_name}_{params['kind']}_result"
                            elif tool_name == 'resources_get' and 'kind' in params:
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