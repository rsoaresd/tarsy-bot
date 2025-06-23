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
        return f"""## Alert Information

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
        sections = runbook_data.get('sections', {})
        troubleshooting_steps = runbook_data.get('troubleshooting_steps', [])
        commands = runbook_data.get('commands', [])
        
        runbook_text = f"""## Associated Runbook

**Raw Content:**
```
{runbook_data.get('raw_content', 'No runbook content available')}
```

**Extracted Sections:**
{json.dumps(sections, indent=2)}

**Troubleshooting Steps:**
{chr(10).join(f"- {step}" for step in troubleshooting_steps)}

**Identified Commands:**
{chr(10).join(f"- `{cmd}`" for cmd in commands)}"""
        
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

Please provide a comprehensive analysis that includes:

1. **Root Cause Analysis:**
   - What is the primary cause of this alert?
   - What evidence from the system data supports this conclusion?

2. **Current System State:**
   - What is the current state of the affected resources?
   - Are there any stuck resources or finalizers preventing cleanup?

3. **Impact Assessment:**
   - What is the impact of this issue?
   - How does this affect system functionality?

4. **Recommended Actions:**
   - What immediate actions should be taken?
   - What commands need to be executed (if any)?

5. **Prevention Measures:**
   - How can this issue be prevented in the future?
   - What monitoring or automation improvements are recommended?

6. **Additional Investigation:**
   - What additional data or investigation might be needed?
   - Are there related systems that should be checked?

Please be specific and reference the actual data provided. Format your response with clear sections and actionable recommendations."""
    
    def _format_data(self, data) -> str:
        """Format data for display in prompt."""
        if isinstance(data, (dict, list)):
            try:
                return json.dumps(data, indent=2, default=str)
            except:
                return str(data)
        return str(data)
    
    def build_mcp_instruction_prompt(self, 
                                   alert_data: Dict, 
                                   runbook_data: Dict, 
                                   available_tools: Dict) -> str:
        """Build a prompt to determine which MCP tools to call."""
        
        return f"""# MCP Tool Selection Request

Based on the following alert and runbook, determine which MCP tools should be called to gather additional information.

## Alert Information
{self._build_alert_section(alert_data)}

## Runbook Content
{runbook_data.get('raw_content', 'No runbook available')}

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