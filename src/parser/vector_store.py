import json
import logging
from pathlib import Path
import chromadb
from src.parser.embedding_engine import EmbeddingEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, db_path: str = "data/chroma_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_engine = EmbeddingEngine()
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
                    ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas
                )
            else:
                logger.error(f"Failed to get embeddings for batch starting at {i}")


if __name__ == "__main__":
    store = VectorStore()
    store.add_chunks_from_graph(Path("data/knowledge_graph.json"))
