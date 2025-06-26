"""
Prompt builder utility for constructing LLM prompts.
"""

import json
from typing import Dict, List


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
            
            if isinstance(server_data, dict):
                for key, value in server_data.items():
                    mcp_text += f"**{key}:**\n```\n{self._format_data(value)}\n```\n\n"
            else:
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
- Detailed state of affected resources
- Any stuck resources or finalizers preventing cleanup
- Related resource dependencies

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