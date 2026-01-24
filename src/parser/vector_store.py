import json
import logging
import os
from pathlib import Path
from typing import Optional

try:
    import chromadb
    from chromadb.config import Settings
except Exception:
    # Catch ImportError AND RuntimeErrors from broken Pydantic/Python 3.14
    chromadb = None

import requests
from src.parser.embedding_engine import EmbeddingEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RestChromaClient:
    """Minimal REST client to bypass broken chromadb package on Python 3.14"""

    def __init__(self, host: str, port: str):
        self.base_url = f"http://{host}:{port}/api/v1"
        # v2 API path for some operations
        self.base_url_v2 = f"http://{host}:{port}/api/v2"

    def get_or_create_collection(self, name: str, metadata: Optional[dict] = None):
        # Ensure collection exists via REST

        # 1. Try V1 GET (Legacy)
        try:
            resp = requests.get(f"{self.base_url}/collections/{name}")
            if resp.status_code == 200:
                return RestCollection(self, name, resp.json()["id"])
        except Exception:
            pass

        # 2. Try V2 List to find by name
        host = self.base_url.split("//")[1].split(":")[0]
        port = self.base_url.split(":")[2].split("/")[0]
        tenant_base = f"http://{host}:{port}/api/v2/tenants/default_tenant/databases/default_database"

        try:
            resp = requests.get(f"{tenant_base}/collections")
            if resp.status_code == 200:
                for col in resp.json():
                    if col["name"] == name:
                        return RestCollection(self, name, col["id"])
        except Exception as e:
            logger.warning(f"Failed to list V2 collections: {e}")

        # 3. Create (V1)
        resp = requests.post(
            f"{self.base_url}/collections", json={"name": name, "metadata": metadata}
        )
        if resp.status_code == 200:
            return RestCollection(self, name, resp.json()["id"])

        # 4. Create (V2)
        logger.warning(
            "REST Client: v1 collection create failed, trying v2/tenant path..."
        )
        resp = requests.post(
            f"{tenant_base}/collections", json={"name": name, "metadata": metadata}
        )

        if resp.status_code == 409:
            resp_list = requests.get(f"{tenant_base}/collections")
            if resp_list.status_code == 200:
                for col in resp_list.json():
                    if col["name"] == name:
                        return RestCollection(self, name, col["id"])

        resp.raise_for_status()
        return RestCollection(self, name, resp.json()["id"])

        # 4. Create (V2)
        logger.warning(
            "REST Client: v1 collection create failed, trying v2/tenant path..."
        )
        resp = requests.post(
            f"{tenant_base}/collections", json={"name": name, "metadata": metadata}
        )

        if resp.status_code == 409:  # Conflict - already exists
            # We should have found it in step 2, but maybe race condition or step 2 failed.
            # Try listing again? Or maybe 409 response has ID? No.
            # Retry listing one more time
            resp_list = requests.get(f"{tenant_base}/collections")
            if resp_list.status_code == 200:
                for col in resp_list.json():
                    if col["name"] == name:
                        return RestCollection(self, name, col["id"])

        resp.raise_for_status()
        return RestCollection(self, name, resp.json()["id"])


class RestCollection:
    def __init__(self, client, name, id):
        self.client = client
        self.name = name
        self.id = id

    def query(
        self, query_embeddings, n_results, where=None, where_document=None, include=None
    ):
        url = f"{self.client.base_url_v2}/tenants/default_tenant/databases/default_database/collections/{self.id}/query"
        payload = {
            "query_embeddings": query_embeddings,
            "n_results": n_results,
            "include": include or ["documents", "metadatas", "distances"],
        }
        if where:
            payload["where"] = where
        if where_document:
            payload["where_document"] = where_document

        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()

    def upsert(self, ids, embeddings, documents, metadatas):
        url = f"{self.client.base_url_v2}/tenants/default_tenant/databases/default_database/collections/{self.id}/upsert"
        payload = {
            "ids": ids,
            "embeddings": embeddings,
            "documents": documents,
            "metadatas": metadatas,
        }
        resp = requests.post(url, json=payload)
        resp.raise_for_status()


class VectorStore:
    def __init__(self, db_path: str = "data/chroma_db"):
        self.embedding_engine = EmbeddingEngine()

        # Check if we should use HTTP client (for Podman/Docker)
        self.host = os.getenv("CHROMA_HOST")
        self.port = os.getenv("CHROMA_PORT", "8000")

        if self.host:
            logger.info(f"Connecting to ChromaDB at {self.host}:{self.port}")
            if chromadb:
                try:
                    self.client = chromadb.HttpClient(
                        host=self.host, port=int(self.port)
                    )
                except Exception as e:
                    logger.warning(
                        f"Standard ChromaDB client failed ({e}), failing back to REST client"
                    )
                    self.client = RestChromaClient(host=self.host, port=self.port)
            else:
                logger.info("Using REST Client (chromadb package missing/broken)")
                self.client = RestChromaClient(host=self.host, port=self.port)
        else:
            logger.info(f"Using local persistent ChromaDB at {db_path}")
            if chromadb and hasattr(chromadb, "PersistentClient"):
                try:
                    self.client = chromadb.PersistentClient(path=db_path)
                except Exception as e:
                    logger.warning(
                        f"Failed to init PersistentClient: {e}. Fallback to Mock."
                    )
                    self.client = self._get_mock_client()
            else:
                logger.warning("Full chromadb package missing. Using Mock Client.")
                self.client = self._get_mock_client()

        self.collection = self.client.get_or_create_collection(
            name="chunks", metadata={"hnsw:space": "cosine"}
        )

    def _get_mock_client(self):
        class MockClient:
            def get_or_create_collection(self, name, metadata=None):
                return MockCollection()

        class MockCollection:
            def query(self, **kwargs):
                return {"ids": [], "distances": [], "metadatas": [], "documents": []}

            def upsert(self, **kwargs):
                pass

            def get(self, ids):
                return {"documents": []}

        return MockClient()

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
