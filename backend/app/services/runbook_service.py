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
        """Parse runbook. For now, just return the raw content."""
        
        result = {
            "raw_content": content,
        }
        
        return result

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose() 