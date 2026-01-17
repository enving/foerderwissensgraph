"""
Base LLM Provider Interface

Abstract base class for all LLM providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class Message(BaseModel):
    """Chat message format."""
    role: str  # "system", "user", "assistant"
    content: str


class LLMResponse(BaseModel):
    """Standardized LLM response."""
    content: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers must implement:
    - generate(): Text generation
    - generate_json(): JSON-structured output
    - chat(): Chat completion
    """

    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model
        self.kwargs = kwargs

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text completion from a prompt.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            **kwargs: Provider-specific parameters

        Returns:
            LLMResponse with generated content
        """
        pass

    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        max_tokens: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate JSON-structured output.

        Args:
            prompt: Input prompt (should specify JSON schema)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Returns:
            Parsed JSON dictionary
        """
        pass

    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Chat completion with message history.

        Args:
            messages: List of Message objects
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Provider-specific parameters

        Returns:
            LLMResponse with assistant's reply
        """
        pass

    def get_provider_name(self) -> str:
        """Return provider name (e.g., 'ionos', 'openai')."""
        return self.__class__.__name__.replace("Provider", "").lower()
