import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.parser.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def sync_only():
    graph_path = Path("data/knowledge_graph.json")
    if not graph_path.exists():
        logger.error(f"Graph file not found: {graph_path}")
        return

    logger.info("Starting Embedding Sync to ChromaDB...")
    try:
        store = VectorStore()
        store.add_chunks_from_graph(graph_path)
        logger.info("Embedding Sync completed.")
    except Exception as e:
        logger.error(f"Embedding Sync failed: {e}")
        import traceback

        logger.error(traceback.format_exc())


if __name__ == "__main__":
    sync_only()
