import sys
import os
from pathlib import Path

# Fix path to include project root
sys.path.append(str(Path(__file__).parent.parent))

from unittest.mock import MagicMock, patch

# Mock heavy dependencies
sys.modules["chromadb"] = MagicMock()
# sys.modules["pydantic"] = MagicMock() # Don't mock pydantic if possible
sys.modules["dotenv"] = MagicMock()
sys.modules["networkx"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["spacy"] = MagicMock()

import logging
from src.parser.hybrid_search import HybridSearchEngine
from src.parser.query_enhancer import QueryEnhancer
from src.llm.base_provider import BaseLLMProvider, LLMResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockLLMProvider(BaseLLMProvider):
    def generate(self, prompt, max_tokens=500, temperature=0.7, **kwargs):
        if "alternative Formulierungen" in prompt:
            return LLMResponse(content="Variation 1\nVariation 2", model="mock")
        if "hypothetische" in prompt:
            return LLMResponse(
                content="Dies ist ein hypothetischer Gesetzestext gemäß § 123 VgV.",
                model="mock",
            )
        if "Teilfragen" in prompt:
            return LLMResponse(content='["Teilfrage 1", "Teilfrage 2"]', model="mock")
        return LLMResponse(content="Mock response", model="mock")

    def generate_json(self, prompt, max_tokens=1000, **kwargs):
        if "Teilfragen" in prompt:
            return {"sub_queries": ["Teilfrage 1", "Teilfrage 2"]}
        return {}

    def chat(self, messages, max_tokens=500, temperature=0.7, **kwargs):
        return LLMResponse(content="Mock chat response", model="mock")


def test_query_enhancer_logic():
    logger.info("Testing QueryEnhancer logic...")
    mock_llm = MockLLMProvider(api_key="mock", model="mock")
    enhancer = QueryEnhancer(mock_llm)

    query = "Wie hoch sind die Schwellenwerte im Vergaberecht?"
    enhanced = enhancer.enhance(query)

    assert enhanced["original_query"] == query
    assert len(enhanced["variations"]) == 2
    assert "hypothetischer Gesetzestext" in enhanced["hyde_text"]
    assert len(enhanced["sub_queries"]) >= 1

    logger.info("QueryEnhancer logic test passed!")


def test_hybrid_search_with_enhancement():
    logger.info("Testing HybridSearchEngine with QueryEnhancement...")

    # Setup mocks
    mock_llm = MockLLMProvider(api_key="mock", model="mock")

    with patch("src.parser.hybrid_search.get_llm_provider", return_value=mock_llm):
        # We need to mock the components of HybridSearchEngine to avoid file IO and real DB calls
        with (
            patch("src.parser.hybrid_search.VectorStore"),
            patch("src.parser.hybrid_search.EmbeddingEngine"),
            patch("src.parser.hybrid_search.GraphAlgorithms"),
        ):
            # Conditionally patch BM25Index
            bm25_patcher = None
            import src.parser.hybrid_search as hs

            if hasattr(hs, "BM25Index"):
                bm25_patcher = patch("src.parser.hybrid_search.BM25Index")
                bm25_patcher.start()

            engine = HybridSearchEngine()

            # Mock the internal calls that search_v2 makes
            engine.vector_store.embedding_engine.get_embeddings = MagicMock(
                return_value=[[0.1] * 384]
            )
            engine.vector_store.collection.query = MagicMock(
                return_value={"ids": [["chunk1", "chunk2"]], "distances": [[0.1, 0.2]]}
            )
            if engine.bm25_index:
                engine.bm25_index.search = MagicMock(return_value=[("chunk3", 0.5)])

            query = "Test query"
            results = engine.search_v2(query, use_query_enhancement=True)

            # Verify QueryEnhancer was called (implicitly by checking if multiple queries were processed)
            # vector_store.collection.query should be called multiple times:
            # 1 (original) + 2 (variations) + 2 (sub_queries) + 1 (hyde) = 6
            # But they might overlap, so we check if it was called more than once.
            assert engine.vector_store.collection.query.call_count > 1
            logger.info(
                f"Vector query called {engine.vector_store.collection.query.call_count} times."
            )

    logger.info("HybridSearchEngine enhancement integration test passed!")


if __name__ == "__main__":
    try:
        test_query_enhancer_logic()
        test_hybrid_search_with_enhancement()
        logger.info("All enhancement tests passed!")
    except Exception as e:
        logger.exception(f"Tests failed: {e}")
        sys.exit(1)
