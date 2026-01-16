import os
import requests
import logging
from typing import List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingEngine:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("IONOS_API_KEY")
        self.api_url = (
            os.getenv("IONOS_EMBEDDING_API_URL")
            or "https://openai.inference.de-txl.ionos.com/v1/embeddings"
        )
        self.model_name = os.getenv("IONOS_EMBEDDING_MODEL") or "BAAI/bge-m3"

        self.mistral_api_key = os.getenv("MISTRAL_API_KEY")

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key and not self.mistral_api_key:
            raise ValueError(
                "No API Keys found (IONOS/Mistral). Local fallback is disabled."
            )

        # Try IONOS first
        if self.api_key:
            try:
                response = requests.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model_name,
                        "input": texts,
                    },
                    timeout=60,
                )
                if response.status_code == 200:
                    data = response.json()
                    sorted_data = sorted(data["data"], key=lambda x: x["index"])
                    return [item["embedding"] for item in sorted_data]
                elif response.status_code == 401:
                    logger.warning("IONOS API Key unauthorized for embeddings.")
                else:
                    response.raise_for_status()
            except Exception as e:
                logger.error(f"IONOS Embedding generation failed: {e}")

        # Try Mistral fallback
        if self.mistral_api_key:
            try:
                from mistralai import Mistral

                client = Mistral(api_key=self.mistral_api_key)
                logger.info(f"Using Mistral for batch of {len(texts)} texts")
                response = client.embeddings.create(model="mistral-embed", inputs=texts)
                embeddings: List[List[float]] = []
                for item in response.data:
                    if item.embedding is not None:
                        embeddings.append(item.embedding)
                    else:
                        raise RuntimeError("Mistral returned empty embeddings")
                return embeddings
            except Exception as e:
                logger.error(f"Mistral Fallback Embedding failed: {e}")

        raise RuntimeError(
            "Remote embedding failed or unavailable through all providers."
        )


if __name__ == "__main__":
    # Quick test
    engine = EmbeddingEngine()
    test_texts = ["Dies ist ein Test.", "Vergaberecht ist komplex."]
    embeddings = engine.get_embeddings(test_texts)
    if embeddings:
        logger.info(f"Successfully generated {len(embeddings)} embeddings.")
        logger.info(f"Embedding dimension: {len(embeddings[0])}")
