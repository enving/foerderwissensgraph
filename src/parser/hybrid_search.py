import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import networkx as nx
import json

from src.parser.vector_store import VectorStore
from src.parser.embedding_engine import EmbeddingEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridSearchEngine:
    def __init__(
        self,
        graph_path: Path = Path("data/knowledge_graph.json"),
        db_path: str = "data/chroma_db",
    ):
        self.vector_store = VectorStore(db_path=db_path)
        self.graph_path = graph_path
        self.graph = self._load_graph()

    def _load_graph(self) -> nx.MultiDiGraph:
        if not self.graph_path.exists():
            logger.error(f"Graph file not found: {self.graph_path}")
            return nx.MultiDiGraph()

        with open(self.graph_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return nx.node_link_graph(data)

    def search(
        self,
        query: str,
        limit: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        multi_hop: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Performs a hybrid search:
        1. Semantic search in ChromaDB.
        2. Graph traversal to fetch 'Breadcrumbs' and 'Source URL'.
        3. Context expansion (Multi-Hop) if requested.
        """
        logger.info(f"Hybrid search for: '{query}'")

        results = self.vector_store.collection.query(
            query_texts=[query], n_results=limit, where=filter_dict
        )

        hybrid_results = []

        if not results or not results.get("ids"):
            return []

        ids = results.get("ids", [[]])[0]
        distances = (
            results.get("distances", [[]])[0]
            if results.get("distances")
            else [0] * len(ids)
        )
        metadatas = (
            results.get("metadatas", [[]])[0] if results.get("metadatas") else []
        )
        documents = (
            results.get("documents", [[]])[0] if results.get("documents") else []
        )

        for i in range(len(ids)):
            chunk_id = ids[i]
            score = 1 - distances[i]

            entry = {
                "id": chunk_id,
                "text": documents[i],
                "score": score,
                "breadcrumbs": "",
                "source_url": "",
                "doc_title": "",
                "rules": [],
                "neighbor_context": [],
            }

            if chunk_id in self.graph:
                node_data = self.graph.nodes[chunk_id]
                entry["breadcrumbs"] = node_data.get("context", "")
                entry["rules"] = node_data.get("rules", [])

                # 3. Context Expansion (Multi-Hop)
                if multi_hop:
                    # Get sibling chunks (chunks belonging to the same document)
                    parents = list(self.graph.predecessors(chunk_id))
                    for p in parents:
                        p_data = self.graph.nodes[p]
                        if p_data.get("type") == "document":
                            entry["source_url"] = p_data.get("url", "")
                            entry["doc_title"] = p_data.get("title", "")

                            # Fetch siblings
                            siblings = list(self.graph.successors(p))
                            for sib_id in siblings:
                                if sib_id != chunk_id:
                                    sib_data = self.graph.nodes[sib_id]
                                    if sib_data.get("type") == "chunk":
                                        entry["neighbor_context"].append(
                                            {
                                                "id": sib_id,
                                                "text": sib_data.get("text", "")[:200]
                                                + "...",
                                                "breadcrumbs": sib_data.get(
                                                    "context", ""
                                                ),
                                            }
                                        )
                            break

            hybrid_results.append(entry)

        return hybrid_results


if __name__ == "__main__":
    engine = HybridSearchEngine()
    query = "Vergaberecht Schwellenwerte"
    results = engine.search(query)

    for res in results:
        print(f"[{res['score']:.2f}] {res['doc_title']} > {res['breadcrumbs']}")
        print(f"URL: {res['source_url']}")
        print(f"Rules: {len(res['rules'])}")
        print("-" * 20)
