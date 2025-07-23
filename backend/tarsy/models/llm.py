"""
LLM-related models and enums.
"""

from pydantic import BaseModel


class LLMMessage(BaseModel):
    """Message for LLM conversations."""
    role: str  # "system", "user", "assistant"
    content: str 