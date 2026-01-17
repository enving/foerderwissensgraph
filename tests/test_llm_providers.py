import unittest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure src is in path
sys.path.append(str(Path(__file__).parent.parent))

from src.llm.base_provider import Message, LLMResponse
from src.llm.openai_provider import OpenAIProvider, IONOSProvider
from src.llm.anthropic_provider import AnthropicProvider
from src.llm.provider_factory import get_llm_provider


class TestLLMProviders(unittest.TestCase):
    def test_message_schema(self):
        """Test the Message pydantic model."""
        msg = Message(role="user", content="hello")
        self.assertEqual(msg.role, "user")
        self.assertEqual(msg.content, "hello")

    @patch("requests.post")
    def test_openai_provider_chat(self, mock_post):
        """Test OpenAIProvider chat method with mocked API response."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hi there!"}, "finish_reason": "stop"}],
            "model": "gpt-4",
            "usage": {"total_tokens": 10},
        }
        mock_post.return_value = mock_response

        provider = OpenAIProvider(api_key="test-key", model="gpt-4")
        messages = [Message(role="user", content="Hello")]
        response = provider.chat(messages)

        self.assertIsInstance(response, LLMResponse)
        self.assertEqual(response.content, "Hi there!")
        self.assertEqual(response.tokens_used, 10)
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_anthropic_provider_chat(self, mock_post):
        """Test AnthropicProvider chat method with mocked API response."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "Hello from Claude"}],
            "model": "claude-3",
            "usage": {"output_tokens": 15},
            "stop_reason": "end_turn",
        }
        mock_post.return_value = mock_response

        provider = AnthropicProvider(api_key="test-key", model="claude-3")
        messages = [Message(role="user", content="Hello")]
        response = provider.chat(messages)

        self.assertIsInstance(response, LLMResponse)
        self.assertEqual(response.content, "Hello from Claude")
        self.assertEqual(response.tokens_used, 15)
        mock_post.assert_called_once()

    @patch("os.getenv")
    def test_provider_factory_openai(self, mock_getenv):
        """Test that the factory returns an OpenAIProvider correctly configured."""

        def getenv_side_effect(key, default=None):
            if key == "LLM_PROVIDER":
                return "openai"
            if key == "OPENAI_API_KEY":
                return "test-openai-key"
            if key == "OPENAI_MODEL":
                return "gpt-4"
            return default

        mock_getenv.side_effect = getenv_side_effect

        provider = get_llm_provider("openai")
        self.assertIsInstance(provider, OpenAIProvider)
        self.assertEqual(provider.model, "gpt-4")
        self.assertEqual(provider.api_key, "test-openai-key")

    @patch("os.getenv")
    def test_provider_factory_ionos(self, mock_getenv):
        """Test that the factory returns an IONOSProvider correctly configured."""

        def getenv_side_effect(key, default=None):
            if key == "LLM_PROVIDER":
                return "ionos"
            if key == "IONOS_API_KEY":
                return "test-ionos-key"
            return default

        mock_getenv.side_effect = getenv_side_effect

        provider = get_llm_provider("ionos")
        self.assertIsInstance(provider, IONOSProvider)
        self.assertEqual(provider.get_provider_name(), "ionos")
        self.assertEqual(provider.api_key, "test-ionos-key")

    def test_provider_factory_invalid(self):
        """Test that the factory raises ValueError for unknown providers."""
        with self.assertRaises(ValueError):
            get_llm_provider("unknown_provider")

    @patch("requests.post")
    def test_openai_generate_json(self, mock_post):
        """Test generate_json for OpenAIProvider."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"result": "success"}'}}]
        }
        mock_post.return_value = mock_response

        provider = OpenAIProvider(api_key="test", model="gpt-4")
        result = provider.generate_json("Give me JSON")
        self.assertEqual(result, {"result": "success"})


if __name__ == "__main__":
    unittest.main()
