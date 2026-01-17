"""
Anthropic Claude LLM Provider
"""

import json
import logging
import requests
from typing import List, Dict, Any

from .base_provider import BaseLLMProvider, Message, LLMResponse

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude API provider.

    Supports Claude models via Anthropic API.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        api_url: str = "https://api.anthropic.com/v1/messages",
        timeout: int = 30,
        **kwargs
    ):
        super().__init__(api_key, model, **kwargs)
        self.api_url = api_url
        self.timeout = timeout
        self.api_version = kwargs.get("api_version", "2023-06-01")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate text completion from prompt."""
        messages = [Message(role="user", content=prompt)]
        return self.chat(messages, max_tokens=max_tokens, temperature=temperature, **kwargs)

    def generate_json(
        self,
        prompt: str,
        max_tokens: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate JSON-structured output.

        Note: Anthropic doesn't have native JSON mode, so we rely on prompt engineering.
        """
        json_prompt = f"{prompt}\n\nRespond ONLY with valid JSON. No additional text."

        response = self.generate(json_prompt, max_tokens=max_tokens, temperature=0.0, **kwargs)

        try:
            # Try to extract JSON from response
            content = response.content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            return json.loads(content.strip())

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Anthropic response: {e}")
            logger.error(f"Response content: {response.content}")
            raise

    def chat(
        self,
        messages: List[Message],
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Chat completion with message history."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "content-type": "application/json",
        }

        # Anthropic requires system message separate
        system_message = None
        user_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                user_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        payload = {
            "model": self.model,
            "messages": user_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }

        if system_message:
            payload["system"] = system_message

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            content_block = result["content"][0]

            return LLMResponse(
                content=content_block["text"],
                model=result.get("model", self.model),
                tokens_used=result.get("usage", {}).get("output_tokens"),
                finish_reason=result.get("stop_reason")
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Anthropic API request failed: {e}")
            raise
        except KeyError as e:
            logger.error(f"Unexpected Anthropic response format: {e}")
            raise

    def get_provider_name(self) -> str:
        return "anthropic"
