"""
OpenAI-Compatible LLM Provider

Works with:
- OpenAI API
- IONOS Cloud LLM (OpenAI-compatible)
- Any OpenAI-compatible endpoint
"""

import json
import logging
import requests
from typing import List, Dict, Any, Optional

from .base_provider import BaseLLMProvider, Message, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI-compatible LLM provider.

    Supports:
    - OpenAI API (api.openai.com)
    - IONOS Cloud LLM (OpenAI-compatible)
    - Other OpenAI-compatible APIs
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        api_url: str = "https://api.openai.com/v1",
        timeout: int = 30,
        **kwargs,
    ):
        super().__init__(api_key, model, **kwargs)
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout

        # Ensure chat completions endpoint
        if not self.api_url.endswith("/chat/completions"):
            self.api_url += "/chat/completions"

    def generate(
        self, prompt: str, max_tokens: int = 500, temperature: float = 0.7, **kwargs
    ) -> LLMResponse:
        """Generate text completion from prompt."""
        messages = [Message(role="user", content=prompt)]
        return self.chat(
            messages, max_tokens=max_tokens, temperature=temperature, **kwargs
        )

    def generate_json(
        self, prompt: str, max_tokens: int = 1000, **kwargs
    ) -> Dict[str, Any]:
        """Generate JSON-structured output."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            **kwargs,
        }

        try:
            response = requests.post(
                self.api_url, headers=headers, json=payload, timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            return json.loads(content)

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API request failed: {e}")
            raise
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            raise

    def chat(
        self,
        messages: List[Message],
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs,
    ) -> LLMResponse:
        """Chat completion with message history."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Convert Message objects to dict
        messages_dict = [{"role": msg.role, "content": msg.content} for msg in messages]

        payload = {
            "model": self.model,
            "messages": messages_dict,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs,
        }

        try:
            response = requests.post(
                self.api_url, headers=headers, json=payload, timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            choice = result["choices"][0]

            # Handle cases where content is None (e.g. reasoning models cut off or tool calls)
            content = choice["message"].get("content")
            if content is None:
                content = ""

            return LLMResponse(
                content=content,
                model=result.get("model", self.model),
                tokens_used=result.get("usage", {}).get("total_tokens"),
                finish_reason=choice.get("finish_reason"),
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API request failed: {e}")
            raise
        except KeyError as e:
            logger.error(f"Unexpected OpenAI response format: {e}")
            raise


class IONOSProvider(OpenAIProvider):
    """
    IONOS Cloud LLM Provider (OpenAI-compatible).

    Wrapper around OpenAIProvider with IONOS defaults.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-oss-120b",
        api_url: str = "https://openai.inference.de-txl.ionos.com/v1",
        **kwargs,
    ):
        super().__init__(api_key=api_key, model=model, api_url=api_url, **kwargs)
        logger.info(f"Initialized IONOS provider with model: {model}")

    def get_provider_name(self) -> str:
        return "ionos"
