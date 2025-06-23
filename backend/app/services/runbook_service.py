"""
Runbook service for downloading and processing runbooks from GitHub.
"""

import re
from typing import Optional
import httpx
import markdown
from urllib.parse import urlparse

from app.config.settings import Settings


class RunbookService:
    """Service for handling runbook operations."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = httpx.AsyncClient()
        
        # GitHub API headers
        self.headers = {
            "Accept": "application/vnd.github.v3.raw",
            "User-Agent": "SRE-AI-Agent/1.0"
        }
        
        if self.settings.github_token:
            self.headers["Authorization"] = f"token {self.settings.github_token}"
    
    async def download_runbook(self, url: str) -> str:
        """Download runbook content from GitHub URL."""
        try:
            # Convert GitHub URL to raw content URL
            raw_url = self._convert_to_raw_url(url)
            
            # Download the runbook
            response = await self.client.get(raw_url, headers=self.headers)
            response.raise_for_status()
            
            return response.text
            
        except httpx.HTTPError as e:
            raise Exception(f"Failed to download runbook from {url}: {str(e)}")
    
    def _convert_to_raw_url(self, github_url: str) -> str:
        """Convert GitHub URL to raw content URL."""
        # Example: https://github.com/user/repo/blob/master/file.md
        # Should become: https://raw.githubusercontent.com/user/repo/master/file.md
        
        if "raw.githubusercontent.com" in github_url:
            return github_url
        
        if "github.com" in github_url:
            # Parse the URL
            parts = github_url.replace("https://github.com/", "").split("/")
            if len(parts) >= 5 and parts[2] == "blob":
                user = parts[0]
                repo = parts[1]
                branch = parts[3]
                file_path = "/".join(parts[4:])
                
                return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{file_path}"
        
        # If we can't convert, return as-is and let the request fail
        return github_url
    
    def parse_runbook(self, content: str) -> dict:
        """Parse runbook content and extract structured information."""
        # Convert markdown to HTML for better parsing
        html = markdown.markdown(content)
        
        result = {
            "raw_content": content,
            "html_content": html,
            "sections": self._extract_sections(content),
            "troubleshooting_steps": self._extract_troubleshooting_steps(content),
            "commands": self._extract_commands(content)
        }
        
        return result
    
    def _extract_sections(self, content: str) -> dict:
        """Extract sections from the runbook."""
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('#'):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                
                # Start new section
                current_section = line.strip('#').strip().lower()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _extract_troubleshooting_steps(self, content: str) -> list:
        """Extract troubleshooting steps from the runbook."""
        steps = []
        
        # Look for the troubleshooting section
        lines = content.split('\n')
        in_troubleshooting = False
        
        for line in lines:
            if "troubleshooting" in line.lower() and line.startswith('#'):
                in_troubleshooting = True
                continue
            
            if in_troubleshooting:
                if line.startswith('#') and "troubleshooting" not in line.lower():
                    # End of troubleshooting section
                    break
                
                # Look for numbered steps or bullet points
                if re.match(r'^\d+\.', line) or line.strip().startswith('-') or line.strip().startswith('*'):
                    steps.append(line.strip())
        
        return steps
    
    def _extract_commands(self, content: str) -> list:
        """Extract shell commands from the runbook."""
        commands = []
        
        # Look for code blocks with shell commands
        code_block_pattern = r'```(?:shell|bash|sh)?\n(.*?)```'
        matches = re.findall(code_block_pattern, content, re.DOTALL)
        
        for match in matches:
            # Split by lines and clean up
            for line in match.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    commands.append(line)
        
        # Also look for inline code that looks like commands
        inline_pattern = r'`([^`]+)`'
        inline_matches = re.findall(inline_pattern, content)
        
        for match in inline_matches:
            # Check if it looks like a command (contains common command prefixes)
            if any(match.startswith(cmd) for cmd in ['oc ', 'kubectl ', 'docker ', 'curl ']):
                commands.append(match)
        
        return commands
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose() 