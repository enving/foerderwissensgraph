import json
import logging
import os
from pathlib import Path
from typing import Optional

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    # Fallback for lightweight client if full chromadb (with ONNX) fails to install
    try:
        import chromadb_client as chromadb
        from chromadb_client.config import Settings
    except ImportError:
        chromadb = None

from src.parser.embedding_engine import EmbeddingEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, db_path: str = "data/chroma_db"):
        self.embedding_engine = EmbeddingEngine()

        # Check if we should use HTTP client (for Podman/Docker)
        self.host = os.getenv("CHROMA_HOST")
        self.port = os.getenv("CHROMA_PORT", "8000")

        if self.host:
            logger.info(f"Connecting to ChromaDB at {self.host}:{self.port}")
            self.client = chromadb.HttpClient(host=self.host, port=self.port)
        else:
            logger.info(f"Using local persistent ChromaDB at {db_path}")
            if hasattr(chromadb, "PersistentClient"):
                self.client = chromadb.PersistentClient(path=db_path)
            else:
                raise ImportError(
                    "Full chromadb package required for local persistence. Use CHROMA_HOST for client mode."
                )

        self.collection = self.client.get_or_create_collection(
            name="chunks", metadata={"hnsw:space": "cosine"}
        )

    def add_chunks_from_graph(self, graph_path: Path):
        if not graph_path.exists():
            logger.error(f"Graph file not found: {graph_path}")
            return

        with open(graph_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        nodes = data.get("nodes", [])
        chunks_to_process = [n for n in nodes if n.get("type") == "chunk"]

        batch_size = 50
        for i in range(0, len(chunks_to_process), batch_size):
            batch = chunks_to_process[i : i + batch_size]
            ids = [n["id"] for n in batch]
            texts = [n.get("text", "") for n in batch]
            metadatas = []

            for n in batch:
                meta = {
                    "doc_id": n["id"].split("_chunk_")[0],
                    "context": n.get("context", ""),
                }
                metadatas.append(meta)

            logger.info(
                f"Vectorizing batch {i // batch_size + 1}/{(len(chunks_to_process) - 1) // batch_size + 1}"
            )
            embeddings = self.embedding_engine.get_embeddings(texts)

            if embeddings:
                self.collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                )
            else:
                logger.error(f"Failed to get embeddings for batch starting at {i}")


if __name__ == "__main__":
    store = VectorStore()
    store.add_chunks_from_graph(Path("data/knowledge_graph.json"))
