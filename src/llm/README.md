# LLM Provider Abstraction Layer

This directory contains the LLM provider abstraction layer, which allows the system to switch between different LLM providers (OpenAI, IONOS, Anthropic) seamlessly.

## Structure

- `base_provider.py`: Defines the `BaseLLMProvider` abstract class and common data schemas (`Message`, `LLMResponse`).
- `provider_factory.py`: Factory function `get_llm_provider()` to instantiate the correct provider based on configuration.
- `openai_provider.py`: Implementation for OpenAI and OpenAI-compatible APIs (like IONOS).
- `anthropic_provider.py`: Implementation for Anthropic Claude API.

## How to add a new provider

To add a new LLM provider (e.g., Mistral):

1. **Create the provider class:**
   Create a new file `src/llm/mistral_provider.py` and inherit from `BaseLLMProvider`.

   ```python
   from .base_provider import BaseLLMProvider, Message, LLMResponse
   
   class MistralProvider(BaseLLMProvider):
       def generate(self, prompt, **kwargs):
           # Implementation logic here
           pass
           
       def generate_json(self, prompt, **kwargs):
           # Implementation logic here
           pass
           
       def chat(self, messages, **kwargs):
           # Implementation logic here
           pass
   ```

2. **Update the factory:**
   In `src/llm/provider_factory.py`:
   - Import your new provider class.
   - Add a new branch in `get_llm_provider()` to handle the provider name string.
   - Update `list_available_providers()` to include the new provider in the status report.

3. **Configure via environment:**
   Add the necessary environment variables to your `.env` file (e.g., `MISTRAL_API_KEY`, `MISTRAL_MODEL`).

## Configuration

The active provider is determined by the `LLM_PROVIDER` environment variable in your `.env` file.

| Provider Name | Required ENV Variable | Default Model |
|---------------|-----------------------|---------------|
| `ionos`       | `IONOS_API_KEY`       | `openai/gpt-oss-120b` |
| `openai`      | `OPENAI_API_KEY`      | `gpt-4` |
| `anthropic`   | `ANTHROPIC_API_KEY`   | `claude-3-5-sonnet-20241022` |
