"""
LLM-related models and enums.
"""

from enum import Enum
from pydantic import BaseModel
from typing import Dict, Any, Optional


class LLMMessage(BaseModel):
    """Message for LLM conversations."""
    role: str  # "system", "user", "assistant"
    content: str
    

class AvailableLLMs(str, Enum):
    """Available LLM providers."""
    CHATGPT_4_1 = "ChatGPT 4.1"
    GEMINI_2_5_PRO = "Gemini 2.5 Pro"
    GROK_3 = "Grok 3"


class LLMRequest(BaseModel):
    """Request to LLM."""
    messages: list[LLMMessage]
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = 2000
    

class LLMResponse(BaseModel):
    """Response from LLM."""
    content: str
    provider: str
    model: str
    metadata: Optional[Dict[str, Any]] = None 