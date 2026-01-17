import unittest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure src is in path
sys.path.append(str(Path(__file__).parent.parent))

from src.parser.reranker import Reranker, NoOpReranker, create_reranker


class TestReranker(unittest.TestCase):
    def test_lazy_initialization(self):
        """Test that the model is not loaded until first use (lazy init)."""
        with patch("src.parser.reranker.SENTENCE_TRANSFORMERS_AVAILABLE", True):
            with patch(
                "src.parser.reranker.CrossEncoder", create=True
            ) as mock_cross_encoder:
                reranker = Reranker()
                self.assertFalse(reranker.is_initialized)
                self.assertIsNone(reranker.model)

                # Trigger lazy init
                reranker._lazy_init()
                self.assertTrue(reranker.is_initialized)
                mock_cross_encoder.assert_called_once()

    def test_rerank_logic(self):
        """Test the reranking logic with mocked scores."""
        # Force backend to be available for this test
        with patch("src.parser.reranker.SENTENCE_TRANSFORMERS_AVAILABLE", True):
            with patch(
                "src.parser.reranker.CrossEncoder", create=True
            ) as mock_cross_encoder:
                mock_model = MagicMock()

                # Return scores in order of input pairs
                mock_model.predict.return_value = [0.1, 0.9, 0.5]
                mock_cross_encoder.return_value = mock_model

                reranker = Reranker()
                chunks = [
                    {"id": "c1", "text": "text1"},
                    {"id": "c2", "text": "text2"},
                    {"id": "c3", "text": "text3"},
                ]

                results = reranker.rerank("query", chunks, top_k=2)

                # Highest score (0.9) is c2, then c3 (0.5)
                self.assertEqual(len(results), 2)
                self.assertEqual(results[0]["id"], "c2")
                self.assertEqual(results[1]["id"], "c3")
                self.assertAlmostEqual(results[0]["reranker_score"], 0.9)

    def test_no_op_reranker(self):
        """Test that NoOpReranker returns chunks unchanged."""
        reranker = NoOpReranker()
        chunks = [{"id": "c1", "text": "t1"}, {"id": "c2", "text": "t2"}]
        results = reranker.rerank("query", chunks, top_k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "c1")
        self.assertNotIn("reranker_score", results[0])

    def test_factory_enabled(self):
        """Test factory creation when enabled and backend is available."""
        with patch("src.parser.reranker.SENTENCE_TRANSFORMERS_AVAILABLE", True):
            reranker = create_reranker(enabled=True)
            self.assertIsInstance(reranker, Reranker)

    def test_factory_disabled(self):
        """Test factory creation when disabled or backend is missing."""
        # Case 1: Disabled via parameter
        reranker = create_reranker(enabled=False)
        self.assertIsInstance(reranker, NoOpReranker)

        # Case 2: Disabled because backend missing
        with patch("src.parser.reranker.SENTENCE_TRANSFORMERS_AVAILABLE", False):
            reranker = create_reranker(enabled=True)
            self.assertIsInstance(reranker, NoOpReranker)

    def test_rerank_error_handling(self):
        """Test fallback to original chunks when reranking fails."""
        reranker = Reranker()
        reranker.model = MagicMock()
        reranker.model.predict.side_effect = Exception("Model failed")
        reranker.is_initialized = True

        chunks = [{"id": "c1", "text": "t1"}, {"id": "c2", "text": "t2"}]
        results = reranker.rerank("query", chunks)
        # Should return chunks[:top_k]
        self.assertEqual(results, chunks)


if __name__ == "__main__":
    unittest.main()
