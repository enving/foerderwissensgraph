import sys
import os
import psutil
import time
import json
import logging
from pathlib import Path
import networkx as nx

# Add src to path
sys.path.append(os.getcwd())

# Setup basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB


def profile_step(name, func, *args, **kwargs):
    start_mem = get_memory_usage()
    start_time = time.time()

    result = func(*args, **kwargs)

    end_mem = get_memory_usage()
    end_time = time.time()

    diff_mem = end_mem - start_mem
    duration = end_time - start_time

    print(f"[{name}]")
    print(f"  Duration: {duration:.4f} sec")
    print(f"  Memory Diff: {diff_mem:+.2f} MB")
    print(f"  Total Memory: {end_mem:.2f} MB")
    print("-" * 30)
    return result


def load_graph_only():
    graph_path = Path("data/knowledge_graph.json")
    if graph_path.exists():
        with open(graph_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return nx.node_link_graph(data)
    return nx.MultiDiGraph()


def load_vector_store():
    # Mock VectorStore and RestCollection for profiling
    class MockVectorStore:
        def __init__(self):
            self.embedding_engine = None
            self.collection = None

            # Mock EmbeddingEngine inside
            class MockEmbeddingEngine:
                def get_embeddings(self, texts):
                    # Return dummy embeddings
                    return [[0.1] * 384 for _ in texts]

            self.embedding_engine = MockEmbeddingEngine()

            # Mock Collection inside
            class MockCollection:
                def query(self, query_embeddings, n_results, where=None):
                    # Return dummy results
                    return {
                        "ids": [["doc_1", "doc_2", "doc_3"]],
                        "distances": [[0.1, 0.2, 0.3]],
                        "metadatas": [[{}, {}, {}]],
                        "documents": [["Doc 1 text", "Doc 2 text", "Doc 3 text"]],
                    }

                def get(self, ids):
                    # For reranking fetch
                    return {"documents": ["Dummy content"]}

            self.collection = MockCollection()

    try:
        from src.parser.vector_store import VectorStore

        # Force REST client mode to avoid local import error
        os.environ["CHROMA_HOST"] = "mock_host"

        # Monkey patch VectorStore to return our Mock if actual init fails
        # But we can't easily patch the class init from here if we want to measure the REAL init memory
        # of the OTHER components.
        # Actually, let's just use the mock for everything related to VectorStore.
        return MockVectorStore()
    except Exception as e:
        print(f"  [Warn] VectorStore load failed: {e}. Using Mock.")
        return MockVectorStore()


# Monkey patch the module so HybridSearchEngine picks it up
import src.parser.vector_store

src.parser.vector_store.VectorStore = lambda *args, **kwargs: load_vector_store()


def load_bm25():
    from src.parser.bm25_index import BM25Index

    return BM25Index(
        graph_path=Path("data/knowledge_graph.json"),
        index_path=Path("data/bm25_index.pkl"),
        use_spacy=True,
        rebuild=False,
    )


def load_reranker():
    # Simulate Reranker Memory Usage (approx 500MB for mMiniLM-L12 + Overhead)
    # Since we can't install torch in this environment due to timeouts
    class SimulatedReranker:
        def __init__(self):
            print("  [Simulated] Allocating 500MB to mimic Reranker model...")
            self._memory_hog = bytearray(500 * 1024 * 1024)  # 500MB

        def rerank(self, query, chunks, top_k=10, text_key="text"):
            # Dummy reranking logic
            for i, c in enumerate(chunks):
                c["reranker_score"] = 0.9 - (i * 0.01)
            return sorted(
                chunks, key=lambda x: x.get("reranker_score", 0), reverse=True
            )[:top_k]

    return SimulatedReranker()


def main():
    print(f"Initial Baseline Memory: {get_memory_usage():.2f} MB")
    print("-" * 30)

    # 1. Profile Graph Loading
    graph = profile_step("Load NetworkX Graph", load_graph_only)
    if graph:
        print(f"  Nodes: {graph.number_of_nodes()}")
        print(f"  Edges: {graph.number_of_edges()}")

    # 2. Profile VectorStore (ChromaDB)
    # We create a new instance (simulating what happens in HybridSearchEngine)
    # Note: EmbeddingEngine is lightweight (API based)
    vs = profile_step("Load VectorStore", load_vector_store)

    # 3. Profile BM25 Loading
    # Check if BM25 index exists
    if Path("data/bm25_index.pkl").exists():
        bm25 = profile_step("Load BM25 Index", load_bm25)
    else:
        print("[Load BM25 Index] Skipped (Index not found)")

    # 4. Profile Reranker Loading
    # This is expected to be the heaviest
    reranker = profile_step("Load Cross-Encoder Reranker", load_reranker)

    # 5. Full HybridSearchEngine Initialization
    # This might double-count if we keep previous objects, but let's see standalone cost
    # We clear references to free memory if possible (though Python GC is lazy)
    del graph
    del vs
    del bm25
    del reranker
    import gc

    gc.collect()

    print(f"Memory after GC cleanup: {get_memory_usage():.2f} MB")
    print("-" * 30)

    from src.parser.hybrid_search import HybridSearchEngine

    engine = profile_step("Initialize HybridSearchEngine", HybridSearchEngine)

    # 6. Simulate a Query
    query = "Förderung für KI Projekte"
    print(f"Simulating Query: '{query}'")
    results = profile_step("Execute Search", engine.search_v2, query, limit=5)
    print(f"  Results found: {len(results)}")


if __name__ == "__main__":
    main()
