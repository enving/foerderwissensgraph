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
        vector_weight: float = 0.7,
        graph_weight: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Performs a hybrid search:
        1. Semantic search in ChromaDB.
        2. Graph traversal to fetch 'Breadcrumbs' and 'Source URL'.
        3. Context expansion (Multi-Hop) if requested.
        4. (Optional) Re-ranking based on graph structural importance.
        """
        logger.info(f"Hybrid search for: '{query}'")

        query_embeddings = self.vector_store.embedding_engine.get_embeddings([query])
        if not query_embeddings:
            logger.error("Failed to generate embedding for query")
            return []

        results = self.vector_store.collection.query(
            query_embeddings=list(query_embeddings),
            n_results=limit * 2,
            where=filter_dict,
        )

        hybrid_results = []

        if not results:
            return []

        ids_list = results.get("ids")
        if not ids_list or len(ids_list) == 0:
            return []
        ids = ids_list[0]

        distances_list = results.get("distances")
        distances = distances_list[0] if distances_list else [0.0] * len(ids)

        metadatas_list = results.get("metadatas")
        metadatas = metadatas_list[0] if metadatas_list else []

        documents_list = results.get("documents")
        documents = documents_list[0] if documents_list else []

        for i in range(len(ids)):
            chunk_id = ids[i]
            semantic_score = 1.0 - (distances[i] / 2.0)

            graph_score = 0.5
            if chunk_id in self.graph:
                deg = len(list(self.graph.neighbors(chunk_id)))
                graph_score = min(1.0, float(deg) / 10.0)

            combined_score = (semantic_score * vector_weight) + (
                graph_score * graph_weight
            )

            entry = {
                "id": chunk_id,
                "text": documents[i],
                "score": combined_score,
                "semantic_score": semantic_score,
                "graph_score": graph_score,
                "breadcrumbs": "",
                "source_url": "",
                "doc_title": "",
                "ministerium": "",
                "herausgeber": "",
                "stand": "",
                "kuerzel": "",
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
                            entry["ministerium"] = p_data.get("ministerium", "")
                            entry["herausgeber"] = p_data.get("herausgeber", "")
                            entry["stand"] = p_data.get("stand", "")
                            entry["kuerzel"] = p_data.get("kuerzel", "")

                            for _, target_id, edata in self.graph.out_edges(
                                p, data=True
                            ):
                                if edata.get("relation") == "REFERENCES":
                                    target_node = self.graph.nodes[target_id]
                                    target_title = target_node.get("title", target_id)

                                    # If it's a law, try to find specific paragraphs mentioned in the original chunk text
                                    referenced_text = f"Referenz: {target_title}"
                                    if target_node.get("node_type") == "law":
                                        # Optimization: Check if the original chunk text mentions a paragraph of this law
                                        # For now, we fetch the 2 most connected paragraphs as 'context'
                                        law_chunks = [
                                            (s, self.graph.nodes[s])
                                            for s in self.graph.successors(target_id)
                                            if self.graph.nodes[s].get("section_type")
                                            == "law_section"
                                        ]
                                        if law_chunks:
                                            # Simple heuristic: first 2 paragraphs
                                            for lc_id, lc_data in law_chunks[:2]:
                                                entry["neighbor_context"].append(
                                                    {
                                                        "id": lc_id,
                                                        "text": lc_data.get("text", "")[
                                                            :300
                                                        ]
                                                        + "...",
                                                        "breadcrumbs": f"{target_title} > {lc_data.get('paragraph', '')}",
                                                        "type": "reference",
                                                    }
                                                )
                                            continue  # Already added specific sections

                                    entry["neighbor_context"].append(
                                        {
                                            "id": target_id,
                                            "text": referenced_text,
                                            "breadcrumbs": "Graph Reference",
                                            "type": "reference",
                                        }
                                    )

                            for replaced_by, _, edata in self.graph.in_edges(
                                p, data=True
                            ):
                                if edata.get("relation") == "SUPERSEDES":
                                    new_doc = self.graph.nodes[replaced_by]
                                    entry["neighbor_context"].insert(
                                        0,
                                        {
                                            "id": replaced_by,
                                            "text": f"Hinweis: Dokument wurde durch {new_doc.get('title')} ersetzt.",
                                            "breadcrumbs": "Version Warning",
                                            "type": "warning",
                                        },
                                    )

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
