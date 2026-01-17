"""
Cross-Encoder Reranking for German Legal Text

This module implements semantic reranking using cross-encoder models optimized for German text.
Uses sentence-transformers library with multilingual cross-encoder models.

Memory: ~120MB (lazy-loaded)
Latency: ~150ms for 20 pairs
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import CrossEncoder
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available. Reranking disabled.")


class Reranker:
    """
    Cross-encoder reranker for German legal text.

    Features:
    - Lazy loading: model loaded only on first use
    - Multilingual cross-encoder optimized for German
    - Batch processing for efficiency
    - Fallback to no-op if sentence-transformers not available

    Models:
    - Default: cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 (multilingual, German-optimized, 120MB)
    - Alternative: cross-encoder/ms-marco-MiniLM-L-6-v2 (English-primary, smaller, 80MB)

    Example:
        >>> reranker = Reranker()
        >>> chunks = [{"id": "...", "text": "..."}, ...]
        >>> reranked = reranker.rerank("Vergaberecht", chunks, top_k=10)
    """

    # Available cross-encoder models
    MODELS = {
        "mmarco-mMiniLM-L12": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",  # Best for German
        "ms-marco-MiniLM-L6": "cross-encoder/ms-marco-MiniLM-L-6-v2",        # Smaller, English-focused
        "ms-marco-MiniLM-L12": "cross-encoder/ms-marco-MiniLM-L-12-v2",      # Larger, more accurate
    }

    def __init__(
        self,
        model_name: str = "mmarco-mMiniLM-L12",
        max_length: int = 512,
        device: str = "cpu"
    ):
        """
        Initialize reranker with lazy loading.

        Args:
            model_name: Model identifier (see MODELS dict)
            max_length: Max sequence length for cross-encoder
            device: Device to run on ("cpu" or "cuda")
        """
        if model_name not in self.MODELS:
            raise ValueError(f"Unknown model: {model_name}. Available: {list(self.MODELS.keys())}")

        self.model_path = self.MODELS[model_name]
        self.model_name = model_name
        self.max_length = max_length
        self.device = device

        # Lazy loading: model loaded on first rerank() call
        self.model: Optional[CrossEncoder] = None
        self.is_initialized = False

    def _lazy_init(self):
        """
        Lazy load cross-encoder model.

        Only loads model on first use to save memory.
        """
        if self.is_initialized:
            return

        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("sentence-transformers not available. Reranking will be no-op.")
            self.model = None
            self.is_initialized = True
            return

        try:
            logger.info(f"Loading cross-encoder model: {self.model_path}")
            self.model = CrossEncoder(
                self.model_path,
                max_length=self.max_length,
                device=self.device
            )
            logger.info(f"Cross-encoder loaded successfully on {self.device}")
            self.is_initialized = True
        except Exception as e:
            logger.error(f"Failed to load cross-encoder: {e}")
            logger.warning("Reranking will be disabled (no-op)")
            self.model = None
            self.is_initialized = True

    def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int = 10,
        text_key: str = "text"
    ) -> List[Dict[str, Any]]:
        """
        Rerank chunks using cross-encoder.

        Args:
            query: Search query
            chunks: List of chunk dictionaries with text field
            top_k: Number of top results to return
            text_key: Key for text field in chunk dict (default: "text")

        Returns:
            Reranked chunks (top_k), sorted by cross-encoder score descending
            Original chunks if reranking disabled
        """
        # Lazy load model
        self._lazy_init()

        # If model not available, return original chunks
        if not self.model:
            logger.debug("Reranker not available, returning original chunks")
            return chunks[:top_k]

        # If no chunks, return empty
        if not chunks:
            return []

        # Create (query, chunk_text) pairs
        try:
            pairs = [
                (query, chunk.get(text_key, ""))
                for chunk in chunks
            ]

            # Score all pairs
            scores = self.model.predict(pairs)

            # Combine chunks with scores
            scored_chunks = list(zip(chunks, scores))

            # Sort by score descending
            scored_chunks.sort(key=lambda x: x[1], reverse=True)

            # Extract top-k chunks and add reranker score
            reranked = []
            for chunk, score in scored_chunks[:top_k]:
                chunk_copy = chunk.copy()
                chunk_copy["reranker_score"] = float(score)
                reranked.append(chunk_copy)

            logger.debug(f"Reranked {len(chunks)} chunks to top {len(reranked)}")

            return reranked

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            logger.warning("Falling back to original chunks")
            return chunks[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get reranker statistics.

        Returns:
            Dictionary with model metadata
        """
        if not self.is_initialized:
            return {
                "status": "not_initialized",
                "model": self.model_name
            }

        return {
            "status": "ready" if self.model else "disabled",
            "model": self.model_name,
            "model_path": self.model_path,
            "max_length": self.max_length,
            "device": self.device,
            "backend_available": SENTENCE_TRANSFORMERS_AVAILABLE
        }


class NoOpReranker:
    """
    No-op reranker that returns chunks unchanged.

    Useful for testing or when cross-encoder is disabled.
    """

    def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int = 10,
        text_key: str = "text"
    ) -> List[Dict[str, Any]]:
        """Return original chunks, truncated to top_k."""
        return chunks[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        """Return disabled status."""
        return {
            "status": "disabled",
            "model": "none",
            "reason": "no-op reranker"
        }


# Factory function
def create_reranker(
    enabled: bool = True,
    model_name: str = "mmarco-mMiniLM-L12"
) -> Reranker | NoOpReranker:
    """
    Factory to create reranker instance.

    Args:
        enabled: Whether to enable reranking
        model_name: Model identifier

    Returns:
        Reranker or NoOpReranker
    """
    if not enabled:
        logger.info("Reranker disabled via config")
        return NoOpReranker()

    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        logger.warning("sentence-transformers not available, using NoOpReranker")
        return NoOpReranker()

    return Reranker(model_name=model_name)


if __name__ == "__main__":
    # Test reranker
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create reranker
    reranker = Reranker()

    # Test query
    query = "Schwellenwerte für Vergaben"

    # Test chunks
    chunks = [
        {"id": "chunk_1", "text": "Die Schwellenwerte für öffentliche Vergaben betragen 1000 Euro."},
        {"id": "chunk_2", "text": "Zuwendungen werden nach Maßgabe des Haushaltsplans gewährt."},
        {"id": "chunk_3", "text": "Bei Bagatellvergaben unter 1000 Euro entfällt das förmliche Verfahren."},
        {"id": "chunk_4", "text": "Die Förderrichtlinie tritt am 1. Januar in Kraft."},
    ]

    print("\n" + "=" * 60)
    print("RERANKER TEST")
    print("=" * 60)
    print(f"Query: {query}")
    print(f"Chunks: {len(chunks)}")

    # Rerank
    reranked = reranker.rerank(query, chunks, top_k=3)

    print("\nReranked Results:")
    for i, chunk in enumerate(reranked, 1):
        score = chunk.get("reranker_score", 0)
        print(f"{i}. [{score:.4f}] {chunk['id']}: {chunk['text'][:60]}...")

    # Stats
    print("\nReranker Stats:")
    stats = reranker.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
