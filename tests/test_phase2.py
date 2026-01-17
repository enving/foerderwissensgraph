import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

sys.path.append(str(Path(__file__).parent.parent))

sys.modules["chromadb"] = MagicMock()

import logging
from src.parser.hybrid_search import HybridSearchEngine
import networkx as nx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_graph_algorithms():
    logger.info("Testing GraphAlgorithms...")
    engine = HybridSearchEngine()

    all_nodes = list(engine.graph.nodes)
    if not all_nodes:
        logger.error("Graph is empty!")
        return

    chunk_nodes = [
        n for n in all_nodes if engine.graph.nodes[n].get("node_type") == "chunk"
    ]
    if not chunk_nodes:
        chunk_nodes = all_nodes[:10]

    seed_nodes = chunk_nodes[:5]
    logger.info(f"Seed nodes: {seed_nodes}")

    ppr = engine.graph_algorithms.personalized_pagerank(seed_nodes)
    logger.info(f"PPR computed for {len(ppr)} nodes")

    subgraph = engine.graph_algorithms.extract_ppr_subgraph(seed_nodes, top_k=10)
    logger.info(f"Extracted subgraph with {len(subgraph)} nodes")

    expanded = engine.graph_algorithms.smart_k_hop_expansion(seed_nodes, k=1)
    logger.info(f"Expanded to {len(expanded)} nodes with 1-hop")

    scores = engine.graph_algorithms.get_centrality_scores(list(expanded)[:10])
    logger.info(f"Centrality scores: {list(scores.values())[:5]}")


def test_search_v2():
    logger.info("Testing search_v2 with mocked vector store...")
    engine = HybridSearchEngine()

    engine.vector_store.embedding_engine.get_embeddings = MagicMock(
        return_value=[[0.1] * 384]
    )
    engine.vector_store.collection.query = MagicMock(
        return_value={"ids": [list(engine.graph.nodes)[:10]], "distances": [[0.1] * 10]}
    )

    query = "Vergaberecht"
    results = engine.search_v2(query, limit=3, use_ppr=True)
    logger.info(f"Search results: {len(results)}")
    for res in results:
        logger.info(
            f"Result: {res['id']} - Score: {res['score']:.4f} - Centrality: {res.get('graph_centrality', 'N/A')}"
        )
        logger.info(f"Neighbors: {len(res['neighbor_context'])}")


if __name__ == "__main__":
    try:
        test_graph_algorithms()
        test_search_v2()
        logger.info("All tests passed!")
    except Exception as e:
        logger.exception(f"Tests failed: {e}")
