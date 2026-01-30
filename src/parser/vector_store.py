import json
import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    import chromadb
    from chromadb.config import Settings
except Exception:
    # Catch ImportError AND RuntimeErrors from broken Pydantic/Python 3.14
    chromadb = None

import requests
import numpy as np
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

    def count(self) -> int:
        url = f"{self.client.base_url_v2}/tenants/default_tenant/databases/default_database/collections/{self.id}"
        resp = requests.get(url)
        if resp.status_code == 200:
            # V2 API returns metadata including count
            return resp.json().get("count", 0)
        return 0

    def get(self, ids: Optional[List[str]] = None, where: Optional[Dict] = None):
        url = f"{self.client.base_url_v2}/tenants/default_tenant/databases/default_database/collections/{self.id}/get"
        payload = {}
        if ids:
            payload["ids"] = ids
        if where:
            payload["where"] = where

        resp = requests.post(url, json=payload)
        if resp.status_code == 200:
            return resp.json()
        return {"ids": [], "documents": [], "metadatas": []}


class LiteCollection:
    """A lightweight, JSON-persistent vector store for Python 3.14 compat."""

    def __init__(self, name: str, persistence_path: Path):
        self.name = name
        self.persistence_path = persistence_path
        self.data = {}  # id -> {embedding, document, metadata}
        self._load()

    def _load(self):
        if self.persistence_path.exists():
            try:
                with open(self.persistence_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    for item in raw:
                        # Convert embedding to np array
                        item["embedding"] = np.array(
                            item["embedding"], dtype=np.float32
                        )
                        self.data[item["id"]] = item
                logger.info(
                    f"LiteVectorStore: Loaded {len(self.data)} chunks from {self.persistence_path}"
                )
            except Exception as e:
                logger.error(f"LiteVectorStore: Failed to load data: {e}")

    def _save(self):
        out = []
        for pid, item in self.data.items():
            c = item.copy()
            c["embedding"] = c["embedding"].tolist()
            out.append(c)

        # Atomic write pattern
        temp_path = self.persistence_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(out, f)
            os.replace(temp_path, self.persistence_path)
        except Exception as e:
            logger.error(f"LiteVectorStore: Failed to save data: {e}")
            if temp_path.exists():
                os.remove(temp_path)

    def upsert(self, ids, embeddings, documents, metadatas):
        for i, pid in enumerate(ids):
            self.data[pid] = {
                "id": pid,
                "embedding": np.array(embeddings[i], dtype=np.float32),
                "document": documents[i],
                "metadata": metadatas[i] if metadatas else {},
            }
        self._save()

    def query(
        self, query_embeddings, n_results, where=None, where_document=None, include=None
    ):
        results = {"ids": [], "distances": [], "metadatas": [], "documents": []}

        for q_emb in query_embeddings:
            q_vec = np.array(q_emb, dtype=np.float32)
            # Normalize query
            q_norm = np.linalg.norm(q_vec)
            if q_norm > 0:
                q_vec = q_vec / q_norm

            scored = []
            for pid, item in self.data.items():
                # Filter
                if where:
                    if not self._check_filter(item["metadata"], where):
                        continue

                # Similarity
                d_vec = item["embedding"]
                d_norm = np.linalg.norm(d_vec)
                score = 0.0
                if d_norm > 0:
                    score = np.dot(q_vec, d_vec / d_norm)

                dist = 1.0 - score
                scored.append((dist, item))

            scored.sort(key=lambda x: x[0])
            top = scored[:n_results]

            results["ids"].append([x[1]["id"] for x in top])
            results["distances"].append([x[0] for x in top])
            results["metadatas"].append([x[1]["metadata"] for x in top])
            results["documents"].append([x[1]["document"] for x in top])

        return results

    def _check_filter(self, metadata, where):
        if not metadata:
            return False

        for k, v in where.items():
            val = metadata.get(k)
            if isinstance(v, dict):
                # Operators
                if "$in" in v:
                    if val not in v["$in"]:
                        return False
            else:
                # Equality
                if val != v:
                    return False
        return True

    def count(self):
        return len(self.data)

    def get(self, ids: Optional[List[str]] = None):
        res = {"ids": [], "documents": [], "metadatas": []}
        if not ids:
            return res

        for pid in ids:
            if pid in self.data:
                res["ids"].append(pid)
                res["documents"].append(self.data[pid]["document"])
                res["metadatas"].append(self.data[pid]["metadata"])
        return res


class LiteChromaClient:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.file_path = self.path / "lite_store.json"

    def get_or_create_collection(self, name: str, metadata=None):
        return LiteCollection(name, self.file_path)


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
            # Check if LiteStore already exists (Migration/Fallback preference)
            lite_path = Path(db_path) / "lite_store.json"
            if lite_path.exists():
                logger.info(
                    f"Found existing LiteVectorStore at {lite_path}. Forcing LiteClient."
                )
                self.client = LiteChromaClient(path=db_path)
            elif chromadb and hasattr(chromadb, "PersistentClient"):
                try:
                    self.client = chromadb.PersistentClient(path=db_path)
                except Exception as e:
                    logger.warning(
                        f"Failed to init PersistentClient: {e}. Fallback to LiteVectorStore."
                    )
                    self.client = LiteChromaClient(path=db_path)
            else:
                logger.warning("Full chromadb package missing. Using LiteVectorStore.")
                self.client = LiteChromaClient(path=db_path)

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
        chunks_to_process = [
            n
            for n in nodes
            if n.get("type") == "chunk" or n.get("node_type") == "chunk"
        ]

        # Check if already indexed (simple check)
        existing_count = self.collection.count()
        # Only skip if we have at least as many as we want to process
        if existing_count >= len(chunks_to_process):
            logger.info(
                f"Vector store already has {existing_count} chunks. Skipping re-indexing."
            )
            return

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

            # Check if batch already exists to resume interruption
            try:
                existing = self.collection.get(ids=ids)
                # Chroma get returns dict with ids list
                found_ids = existing.get("ids", []) if existing else []
                if len(found_ids) == len(ids):
                    logger.info(
                        f"Batch {i // batch_size + 1} already indexed. Skipping."
                    )
                    continue
            except Exception as e:
                # Fallback if get fails (e.g. not implemented in some client version)
                pass

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
