"""
LLM Provider Factory

Creates LLM provider instances based on environment configuration.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

from .base_provider import BaseLLMProvider
from .openai_provider import OpenAIProvider, IONOSProvider
from .anthropic_provider import AnthropicProvider

load_dotenv()
logger = logging.getLogger(__name__)


def get_llm_provider(
    provider_name: Optional[str] = None,
    **override_kwargs
) -> BaseLLMProvider:
    """
    Get LLM provider instance based on configuration.

    Args:
        provider_name: Override provider (ionos, openai, anthropic)
                      If None, uses LLM_PROVIDER from .env
        **override_kwargs: Override provider-specific parameters

    Returns:
        BaseLLMProvider instance

    Raises:
        ValueError: If provider not configured or unknown

    Example:
        >>> provider = get_llm_provider()  # Uses .env config
        >>> provider = get_llm_provider("anthropic")  # Force Anthropic
        >>> response = provider.generate("Explain RAG systems")
    """

    # Determine provider
    provider = provider_name or os.getenv("LLM_PROVIDER", "ionos")
    provider = provider.lower()

    logger.info(f"Initializing LLM provider: {provider}")

    # IONOS Provider
    if provider == "ionos":
        api_key = os.getenv("IONOS_API_KEY")
        if not api_key:
            raise ValueError("IONOS_API_KEY not found in environment")

        return IONOSProvider(
            api_key=api_key,
            model=override_kwargs.get("model") or os.getenv("IONOS_MODEL", "openai/gpt-oss-120b"),
            api_url=override_kwargs.get("api_url") or os.getenv("IONOS_API_URL", "https://openai.inference.de-txl.ionos.com/v1"),
            **{k: v for k, v in override_kwargs.items() if k not in ["model", "api_url"]}
        )

    # OpenAI Provider
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        return OpenAIProvider(
            api_key=api_key,
            model=override_kwargs.get("model") or os.getenv("OPENAI_MODEL", "gpt-4"),
            api_url=override_kwargs.get("api_url") or os.getenv("OPENAI_API_URL", "https://api.openai.com/v1"),
            **{k: v for k, v in override_kwargs.items() if k not in ["model", "api_url"]}
        )

    # Anthropic Provider
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        return AnthropicProvider(
            api_key=api_key,
            model=override_kwargs.get("model") or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            **{k: v for k, v in override_kwargs.items() if k != "model"}
        )

    # Mistral Provider (Future)
    elif provider == "mistral":
        # TODO: Implement MistralProvider if needed
        raise NotImplementedError("Mistral provider not yet implemented. Use IONOS or Anthropic.")

    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Supported: ionos, openai, anthropic")


def list_available_providers() -> dict:
    """
    List all available LLM providers and their configuration status.

    Returns:
        Dict with provider status
    """
    providers = {}

    # Check IONOS
    providers["ionos"] = {
        "configured": bool(os.getenv("IONOS_API_KEY")),
        "model": os.getenv("IONOS_MODEL", "openai/gpt-oss-120b"),
        "api_url": os.getenv("IONOS_API_URL", "https://openai.inference.de-txl.ionos.com/v1")
    }

    # Check OpenAI
    providers["openai"] = {
        "configured": bool(os.getenv("OPENAI_API_KEY")),
        "model": os.getenv("OPENAI_MODEL", "gpt-4"),
        "api_url": os.getenv("OPENAI_API_URL", "https://api.openai.com/v1")
    }

    # Check Anthropic
    providers["anthropic"] = {
        "configured": bool(os.getenv("ANTHROPIC_API_KEY")),
        "model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    }

    # Check Mistral
    providers["mistral"] = {
        "configured": bool(os.getenv("MISTRAL_API_KEY")),
        "model": "mistral-large-latest",
        "note": "Not yet integrated via abstraction layer"
    }

    return providers


if __name__ == "__main__":
    # CLI for testing provider configuration
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    print("=" * 60)
    print("LLM PROVIDER CONFIGURATION")
    print("=" * 60)

    providers = list_available_providers()

    for name, config in providers.items():
        status = "✓ Configured" if config["configured"] else "✗ Not configured"
        print(f"\n{name.upper()}: {status}")
        for key, value in config.items():
            if key != "configured":
                print(f"  {key}: {value}")

    # Test active provider
    active_provider = os.getenv("LLM_PROVIDER", "ionos")
    print(f"\n\nACTIVE PROVIDER: {active_provider.upper()}")

    if providers[active_provider]["configured"]:
        try:
            provider = get_llm_provider()
            print(f"✓ Successfully initialized {provider.get_provider_name()} provider")
            print(f"  Model: {provider.model}")

            # Test generation
            if "--test" in sys.argv:
                print("\n" + "=" * 60)
                print("TESTING GENERATION...")
                print("=" * 60)

                response = provider.generate("Was ist ein Knowledge Graph? Antworte auf Deutsch in 2 Sätzen.", max_tokens=100)
                print(f"\nResponse:\n{response.content}")
                print(f"\nTokens used: {response.tokens_used}")

        except Exception as e:
            print(f"✗ Failed to initialize provider: {e}")
    else:
        print(f"✗ Provider not configured (missing API key)")
