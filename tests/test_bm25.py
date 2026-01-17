import unittest
import json
import pickle
from pathlib import Path
from unittest.mock import MagicMock, patch
import networkx as nx
import tempfile
import os
import sys

# Ensure src is in path
sys.path.append(str(Path(__file__).parent.parent))

from src.parser.bm25_index import BM25Index


class TestBM25Index(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.graph_path = Path(self.temp_dir.name) / "test_graph.json"
        self.index_path = Path(self.temp_dir.name) / "test_index.pkl"

        # Create a small mock graph
        self.graph = nx.Graph()
        # Node with 'type'
        self.graph.add_node(
            "chunk1",
            type="chunk",
            text="Das Vergaberecht regelt die öffentliche Beschaffung.",
        )
        # Node with 'node_type'
        self.graph.add_node(
            "chunk2",
            node_type="chunk",
            text="Schwellenwerte sind wichtig für Ausschreibungen.",
        )
        # Third chunk to ensure IDF > 0 for terms in only one doc
        self.graph.add_node(
            "chunk3", type="chunk", text="Ein ganz anderer Text ohne die Keywords."
        )
        # Non-chunk node
        self.graph.add_node("program1", type="program", name="Test Programm")

        self.graph.add_edge("chunk1", "program1")

        with open(self.graph_path, "w", encoding="utf-8") as f:
            json.dump(nx.node_link_data(self.graph), f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_initialization_and_search(self):
        """Test building index from graph and performing search."""
        index = BM25Index(self.graph_path, self.index_path, use_spacy=False)
        self.assertEqual(len(index.chunk_ids), 3)
        self.assertIn("chunk1", index.chunk_ids)
        self.assertIn("chunk2", index.chunk_ids)
        self.assertIn("chunk3", index.chunk_ids)

        # Test search with keyword from chunk1
        results = index.search("Vergaberecht")
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0][0], "chunk1")

        # Test search with keyword from chunk2
        results = index.search("Schwellenwerte")
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0][0], "chunk2")

    def test_save_load(self):
        """Test that the index can be saved to and loaded from disk."""
        # Build and save
        index1 = BM25Index(self.graph_path, self.index_path, use_spacy=False)
        self.assertTrue(self.index_path.exists())

        # Load (should use the existing file)
        index2 = BM25Index(
            self.graph_path, self.index_path, use_spacy=False, rebuild=False
        )
        self.assertEqual(index1.chunk_ids, index2.chunk_ids)
        self.assertEqual(len(index2.chunk_ids), 3)

        # Force rebuild
        index3 = BM25Index(
            self.graph_path, self.index_path, use_spacy=False, rebuild=True
        )
        self.assertEqual(len(index3.chunk_ids), 3)

    def test_tokenize_fallback(self):
        """Test the fallback tokenization when SpaCy is not used."""
        index = BM25Index(self.graph_path, self.index_path, use_spacy=False)
        tokens = index._tokenize("Das Vergaberecht ist komplex.")
        # Expected: lowercase, split, filter > 2 chars
        # "das" (3), "vergaberecht" (12), "ist" (3), "komplex." (8) -> wait, "komplex." might be kept with dot if not cleaned
        # Actually simple split: ["das", "vergaberecht", "ist", "komplex."]
        self.assertIn("vergaberecht", tokens)
        self.assertIn("komplex.", tokens)
        self.assertNotIn("is", tokens)  # too short if it was 'is'

    @patch("src.parser.bm25_index.spacy")
    def test_tokenization_spacy(self, mock_spacy):
        """Test tokenization using a mocked SpaCy model."""
        # Mock nlp model
        mock_nlp = MagicMock()
        mock_spacy.load.return_value = mock_nlp

        # Mock doc and tokens
        mock_doc = MagicMock()

        def mock_token(text, lemma, is_stop, is_punct):
            t = MagicMock()
            t.text = text
            t.lemma_ = lemma
            t.is_stop = is_stop
            t.is_punct = is_punct
            return t

        mock_doc.__iter__.return_value = [
            mock_token("vergaberecht", "vergaberecht", False, False),
            mock_token("ist", "sein", True, False),
            mock_token(".", ".", False, True),
        ]
        mock_nlp.return_value = mock_doc

        # We need to force use_spacy to True for this test
        with patch("src.parser.bm25_index.SPACY_AVAILABLE", True):
            index = BM25Index(self.graph_path, self.index_path, use_spacy=True)
            # Ensure it actually uses the mock
            index.nlp = mock_nlp
            index.use_spacy = True

            tokens = index._tokenize("Vergaberecht ist.")
            self.assertEqual(tokens, ["vergaberecht"])

    def test_empty_search(self):
        """Test search with no matches or empty query."""
        index = BM25Index(self.graph_path, self.index_path, use_spacy=False)

        # No match
        results = index.search("Astronomie")
        self.assertEqual(results, [])

        # Empty query
        results = index.search("")
        self.assertEqual(results, [])

    def test_get_stats(self):
        """Test the get_stats method."""
        index = BM25Index(self.graph_path, self.index_path, use_spacy=False)
        stats = index.get_stats()
        self.assertEqual(stats["status"], "ready")
        self.assertEqual(stats["num_chunks"], 3)
        self.assertEqual(stats["tokenizer"], "simple")


if __name__ == "__main__":
    unittest.main()
