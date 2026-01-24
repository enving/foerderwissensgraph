"""
BM25 Sparse Retrieval Index for German Legal Text

This module implements BM25Okapi sparse retrieval optimized for German funding regulations.
Uses SpaCy for German tokenization and lemmatization.

Memory: ~50MB for 100k chunks
Latency: <100ms for top-k retrieval
"""

import json
import pickle
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import logging

try:
    import spacy
    from spacy.lang.de import German

    SPACY_AVAILABLE = True
except Exception as e:
    # Catch both ImportError and RuntimeErrors (e.g. Pydantic v1 issues in Python 3.14)
    SPACY_AVAILABLE = False
    spacy = None
    logging.warning(f"SpaCy not available ({e}). Falling back to simple tokenization.")

from rank_bm25 import BM25Okapi
import networkx as nx

logger = logging.getLogger(__name__)


class BM25Index:
    """
    BM25 sparse retrieval index with German tokenization.

    Features:
    - SpaCy-based tokenization with lemmatization
    - Fallback to simple whitespace split if SpaCy unavailable
    - Persistent index (save/load via pickle)
    - Fast retrieval (<100ms for 100k chunks)

    Example:
        >>> index = BM25Index(graph_path, index_path)
        >>> results = index.search("Vergaberecht Schwellenwerte", k=20)
        >>> [(chunk_id, score), ...]
    """

    def __init__(
        self,
        graph_path: Path,
        index_path: Path,
        use_spacy: bool = True,
        rebuild: bool = False,
    ):
        """
        Initialize BM25 index.

        Args:
            graph_path: Path to knowledge_graph.json
            index_path: Path to save/load BM25 index pickle
            use_spacy: Whether to use SpaCy tokenization (default: True)
            rebuild: Force rebuild even if index exists
        """
        self.graph_path = graph_path
        self.index_path = index_path
        self.use_spacy = use_spacy and SPACY_AVAILABLE

        # Initialize tokenizer
        if self.use_spacy:
            try:
                # Load small German model
                self.nlp = spacy.load("de_core_news_sm", disable=["parser", "ner"])
                logger.info("SpaCy German model loaded successfully")
            except OSError:
                logger.warning(
                    "SpaCy model 'de_core_news_sm' not found. Run: python -m spacy download de_core_news_sm"
                )
                logger.warning("Falling back to simple tokenization")
                self.use_spacy = False
                self.nlp = None
        else:
            self.nlp = None

        # Index components
        self.bm25_index: Optional[BM25Okapi] = None
        self.chunk_ids: List[str] = []
        self.tokenized_corpus: List[List[str]] = []

        # Load or build index
        if index_path.exists() and not rebuild:
            logger.info(f"Loading existing BM25 index from {index_path}")
            self._load_index()
        else:
            logger.info(f"Building new BM25 index from {graph_path}")
            self._build_index()
            self._save_index()

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize and normalize text.

        With SpaCy: lemmatization, stopword removal, lowercase
        Without SpaCy: simple lowercase + split

        Args:
            text: Input text

        Returns:
            List of tokens
        """
        if self.use_spacy and self.nlp:
            # SpaCy tokenization with lemmatization
            doc = self.nlp(text.lower())
            tokens = [
                token.lemma_
                for token in doc
                if not token.is_stop and not token.is_punct and len(token.text) > 2
            ]
            return tokens
        else:
            # Simple fallback: lowercase + split + filter short words
            tokens = [word.lower() for word in text.split() if len(word) > 2]
            return tokens

    def _build_index(self):
        """
        Build BM25 index from graph chunks.

        Process:
        1. Load graph from JSON
        2. Extract all chunk nodes
        3. Tokenize chunk texts
        4. Build BM25Okapi index
        """
        # Load graph
        if not self.graph_path.exists():
            raise FileNotFoundError(f"Graph not found at {self.graph_path}")

        with open(self.graph_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            graph = nx.node_link_graph(data)

        logger.info(f"Loaded graph with {graph.number_of_nodes()} nodes")

        # Extract chunks
        chunks = []
        for node_id, node_data in graph.nodes(data=True):
            if (
                node_data.get("type") == "chunk"
                or node_data.get("node_type") == "chunk"
            ):
                text = node_data.get("text", "")
                if text:
                    chunks.append({"id": node_id, "text": text})

        logger.info(f"Found {len(chunks)} chunk nodes")

        if not chunks:
            raise ValueError("No chunks found in graph. Cannot build BM25 index.")

        # Tokenize corpus
        self.chunk_ids = [chunk["id"] for chunk in chunks]
        self.tokenized_corpus = [self._tokenize(chunk["text"]) for chunk in chunks]

        # Build BM25 index
        self.bm25_index = BM25Okapi(self.tokenized_corpus)

        logger.info(f"BM25 index built with {len(self.chunk_ids)} chunks")

    def _save_index(self):
        """Save BM25 index to disk (pickle format)."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "chunk_ids": self.chunk_ids,
            "tokenized_corpus": self.tokenized_corpus,
            "bm25_index": self.bm25_index,
        }

        with open(self.index_path, "wb") as f:
            pickle.dump(data, f)

        logger.info(
            f"BM25 index saved to {self.index_path} ({self.index_path.stat().st_size / 1024 / 1024:.2f} MB)"
        )

    def _load_index(self):
        """Load BM25 index from disk."""
        with open(self.index_path, "rb") as f:
            data = pickle.load(f)

        self.chunk_ids = data["chunk_ids"]
        self.tokenized_corpus = data["tokenized_corpus"]
        self.bm25_index = data["bm25_index"]

        logger.info(f"BM25 index loaded with {len(self.chunk_ids)} chunks")

    def search(self, query: str, k: int = 20) -> List[Tuple[str, float]]:
        """
        Search for top-k chunks using BM25.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of (chunk_id, bm25_score) tuples, sorted by score descending
        """
        if not self.bm25_index:
            raise ValueError("BM25 index not initialized. Call _build_index() first.")

        # Tokenize query
        query_tokens = self._tokenize(query)

        if not query_tokens:
            logger.warning(f"Query tokenization resulted in empty tokens: '{query}'")
            return []

        # Get BM25 scores
        scores = self.bm25_index.get_scores(query_tokens)

        # Sort by score and get top-k
        scored_chunks = list(zip(self.chunk_ids, scores))
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        # Filter out zero scores
        scored_chunks = [
            (chunk_id, score) for chunk_id, score in scored_chunks if score > 0
        ]

        return scored_chunks[:k]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics.

        Returns:
            Dictionary with index metadata
        """
        if not self.bm25_index:
            return {"status": "not_initialized"}

        avg_doc_len = sum(len(doc) for doc in self.tokenized_corpus) / len(
            self.tokenized_corpus
        )

        return {
            "status": "ready",
            "num_chunks": len(self.chunk_ids),
            "avg_tokens_per_chunk": round(avg_doc_len, 2),
            "tokenizer": "spacy" if self.use_spacy else "simple",
            "index_path": str(self.index_path),
            "index_size_mb": round(self.index_path.stat().st_size / 1024 / 1024, 2)
            if self.index_path.exists()
            else 0,
        }


# Utility function for rebuilding index
def rebuild_bm25_index(
    graph_path: Path = Path("data/knowledge_graph.json"),
    index_path: Path = Path("data/bm25_index.pkl"),
    use_spacy: bool = True,
) -> BM25Index:
    """
    Rebuild BM25 index from scratch.

    Usage:
        python -c "from src.parser.bm25_index import rebuild_bm25_index; rebuild_bm25_index()"

    Args:
        graph_path: Path to knowledge graph JSON
        index_path: Path to save index
        use_spacy: Whether to use SpaCy tokenization

    Returns:
        BM25Index instance
    """
    logger.info("=" * 60)
    logger.info("REBUILDING BM25 INDEX")
    logger.info("=" * 60)

    index = BM25Index(
        graph_path=graph_path, index_path=index_path, use_spacy=use_spacy, rebuild=True
    )

    stats = index.get_stats()
    logger.info(f"Index built successfully:")
    logger.info(f"  - Chunks: {stats['num_chunks']}")
    logger.info(f"  - Avg tokens/chunk: {stats['avg_tokens_per_chunk']}")
    logger.info(f"  - Tokenizer: {stats['tokenizer']}")
    logger.info(f"  - Size: {stats['index_size_mb']} MB")

    return index


if __name__ == "__main__":
    # CLI for rebuilding index
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    graph_path = Path("data/knowledge_graph.json")
    index_path = Path("data/bm25_index.pkl")

    if len(sys.argv) > 1 and sys.argv[1] == "--no-spacy":
        use_spacy = False
    else:
        use_spacy = True

    rebuild_bm25_index(graph_path, index_path, use_spacy)
