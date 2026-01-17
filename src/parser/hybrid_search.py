import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import networkx as nx
import json

from src.parser.vector_store import VectorStore
from src.parser.embedding_engine import EmbeddingEngine

# Graph RAG enhancements (Phase 1)
try:
    from src.parser.bm25_index import BM25Index
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logging.warning("BM25Index not available. Sparse retrieval disabled.")

try:
    from src.parser.reranker import Reranker, create_reranker
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    logging.warning("Reranker not available. Reranking disabled.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridSearchEngine:
    def __init__(
        self,
        graph_path: Path = Path("data/knowledge_graph.json"),
        db_path: str = "data/chroma_db",
        bm25_index_path: Path = Path("data/bm25_index.pkl"),
        enable_bm25: bool = True,
        enable_reranking: bool = True,
    ):
        self.vector_store = VectorStore(db_path=db_path)
        self.graph_path = graph_path
        self.graph = self._load_graph()

        # Phase 1: BM25 Sparse Retrieval
        self.bm25_index = None
        if enable_bm25 and BM25_AVAILABLE:
            try:
                logger.info("Initializing BM25 index...")
                self.bm25_index = BM25Index(
                    graph_path=graph_path,
                    index_path=bm25_index_path,
                    use_spacy=True,
                    rebuild=False
                )
                logger.info(f"BM25 index ready: {self.bm25_index.get_stats()}")
            except Exception as e:
                logger.warning(f"Failed to initialize BM25 index: {e}")
                self.bm25_index = None

        # Phase 1: Cross-Encoder Reranking
        self.reranker = None
        if enable_reranking and RERANKER_AVAILABLE:
            try:
                logger.info("Initializing reranker (lazy-loaded)...")
                self.reranker = create_reranker(enabled=True, model_name="mmarco-mMiniLM-L12")
                logger.info(f"Reranker ready: {self.reranker.get_stats()}")
            except Exception as e:
                logger.warning(f"Failed to initialize reranker: {e}")
                self.reranker = None

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
                    # A. Direct references from the chunk itself
                    for _, target_id, edata in self.graph.out_edges(
                        chunk_id, data=True
                    ):
                        if edata.get("relation") == "REFERENCES":
                            self._add_neighbor_context(entry, target_id)

                    # B. References from the parent document
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
                                    self._add_neighbor_context(entry, target_id)

                            # C. Versioning (SUPERSEDES) from the parent document
                            for replaced_by, _, edata in self.graph.in_edges(
                                p, data=True
                            ):  # type: ignore
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

    def _add_neighbor_context(self, entry: Dict[str, Any], target_id: str):
        """Helper to add neighbor info to results."""
        target_node = self.graph.nodes[target_id]
        target_title = target_node.get("title", target_id)

        # If it's a law, try to find specific paragraphs
        referenced_text = f"Referenz: {target_title}"
        if (
            target_node.get("node_type") == "law"
            or target_node.get("type") == "external"
        ):
            law_chunks = [
                (s, self.graph.nodes[s])
                for s in self.graph.successors(target_id)
                if self.graph.nodes[s].get("section_type") == "law_section"
            ]
            if law_chunks:
                for lc_id, lc_data in law_chunks[:2]:
                    entry["neighbor_context"].append(
                        {
                            "id": lc_id,
                            "text": lc_data.get("text", "")[:300] + "...",
                            "breadcrumbs": f"{target_title} > {lc_data.get('paragraph', '')}",
                            "type": "reference",
                        }
                    )
                return

        entry["neighbor_context"].append(
            {
                "id": target_id,
                "text": referenced_text,
                "breadcrumbs": "Graph Reference",
                "type": "reference",
            }
        )

    # ===== PHASE 1: GRAPH RAG ENHANCEMENTS =====

    def _reciprocal_rank_fusion(
        self,
        ranked_lists: List[List[Tuple[str, float]]],
        k: int = 60
    ) -> List[Tuple[str, float]]:
        """
        Reciprocal Rank Fusion (RRF) for combining multiple ranked lists.

        Formula: score(d) = sum(1 / (k + rank_i(d)))

        Args:
            ranked_lists: List of [(chunk_id, score), ...] from different retrievers
            k: Constant (typically 60)

        Returns:
            List of (chunk_id, rrf_score) sorted by score descending
        """
        rrf_scores: Dict[str, float] = {}

        for ranked_list in ranked_lists:
            for rank, (chunk_id, _) in enumerate(ranked_list, start=1):
                if chunk_id not in rrf_scores:
                    rrf_scores[chunk_id] = 0.0
                rrf_scores[chunk_id] += 1.0 / (k + rank)

        # Sort by RRF score
        sorted_results = sorted(
            rrf_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_results

    def search_v2(
        self,
        query: str,
        limit: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        multi_hop: bool = True,
        use_bm25: bool = True,
        use_reranking: bool = True,
        retrieval_candidates: int = 20,
        rerank_top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        PHASE 1: State-of-the-Art Hybrid Search with BM25 + RRF + Reranking.

        Pipeline:
        1. Multi-Retrieval: BM25 (sparse) + Vector (dense)
        2. RRF Fusion: Combine rankings
        3. Cross-Encoder Reranking: Semantic reranking
        4. Graph Expansion: Multi-hop context (REFERENCES, SUPERSEDES)

        Args:
            query: Search query
            limit: Final number of results
            filter_dict: ChromaDB metadata filters
            multi_hop: Enable graph traversal
            use_bm25: Enable BM25 sparse retrieval
            use_reranking: Enable cross-encoder reranking
            retrieval_candidates: Number of candidates from each retriever
            rerank_top_k: Number of candidates to rerank

        Returns:
            List of enriched result dictionaries
        """
        logger.info(f"[v2] Hybrid search for: '{query}' (BM25={use_bm25}, Rerank={use_reranking})")

        # Step 1: Multi-Retrieval (Vector + BM25)
        retrieval_results = []

        # 1A. Vector Search (Dense)
        query_embeddings = self.vector_store.embedding_engine.get_embeddings([query])
        if query_embeddings:
            vector_results = self.vector_store.collection.query(
                query_embeddings=list(query_embeddings),
                n_results=retrieval_candidates,
                where=filter_dict,
            )

            if vector_results and vector_results.get("ids"):
                ids = vector_results["ids"][0]
                distances = vector_results.get("distances", [[]])[0]

                vector_scored = [
                    (chunk_id, 1.0 - (dist / 2.0))  # Convert distance to similarity
                    for chunk_id, dist in zip(ids, distances)
                ]
                retrieval_results.append(vector_scored)
                logger.info(f"Vector search: {len(vector_scored)} results")
        else:
            logger.warning("Failed to generate query embeddings")

        # 1B. BM25 Search (Sparse)
        if use_bm25 and self.bm25_index:
            try:
                bm25_results = self.bm25_index.search(query, k=retrieval_candidates)
                retrieval_results.append(bm25_results)
                logger.info(f"BM25 search: {len(bm25_results)} results")
            except Exception as e:
                logger.warning(f"BM25 search failed: {e}")

        # Step 2: RRF Fusion
        if not retrieval_results:
            logger.warning("No retrieval results, returning empty")
            return []

        fused_results = self._reciprocal_rank_fusion(retrieval_results, k=60)
        logger.info(f"RRF fusion: {len(fused_results)} unique results")

        # Limit to top candidates for reranking
        fused_results = fused_results[:rerank_top_k]

        # Step 3: Prepare chunks for reranking
        chunks_for_reranking = []
        chunk_metadata = {}  # Store original data

        for chunk_id, rrf_score in fused_results:
            # Fetch chunk text from graph
            if chunk_id in self.graph:
                node_data = self.graph.nodes[chunk_id]
                chunk_text = node_data.get("text", "")

                chunks_for_reranking.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "rrf_score": rrf_score
                })

                chunk_metadata[chunk_id] = node_data
            else:
                # Fetch from vector store if not in graph
                try:
                    vs_result = self.vector_store.collection.get(ids=[chunk_id])
                    if vs_result and vs_result.get("documents"):
                        chunk_text = vs_result["documents"][0]
                        chunks_for_reranking.append({
                            "id": chunk_id,
                            "text": chunk_text,
                            "rrf_score": rrf_score
                        })
                except Exception as e:
                    logger.warning(f"Failed to fetch chunk {chunk_id}: {e}")

        # Step 4: Cross-Encoder Reranking
        if use_reranking and self.reranker and chunks_for_reranking:
            try:
                reranked_chunks = self.reranker.rerank(
                    query=query,
                    chunks=chunks_for_reranking,
                    top_k=limit * 2,  # Get more for graph expansion
                    text_key="text"
                )
                logger.info(f"Reranked: {len(reranked_chunks)} results")
            except Exception as e:
                logger.warning(f"Reranking failed: {e}, using RRF results")
                reranked_chunks = chunks_for_reranking[:limit * 2]
        else:
            reranked_chunks = chunks_for_reranking[:limit * 2]

        # Step 5: Build results with graph enrichment
        hybrid_results = []

        for chunk in reranked_chunks[:limit]:
            chunk_id = chunk["id"]

            entry = {
                "id": chunk_id,
                "text": chunk.get("text", ""),
                "score": chunk.get("reranker_score", chunk.get("rrf_score", 0.0)),
                "rrf_score": chunk.get("rrf_score", 0.0),
                "reranker_score": chunk.get("reranker_score", 0.0),
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

            # Graph enrichment
            if chunk_id in self.graph:
                node_data = self.graph.nodes[chunk_id]
                entry["breadcrumbs"] = node_data.get("context", "")
                entry["rules"] = node_data.get("rules", [])

                # Multi-Hop Context Expansion
                if multi_hop:
                    # A. Direct references from chunk
                    for _, target_id, edata in self.graph.out_edges(chunk_id, data=True):
                        if edata.get("relation") == "REFERENCES":
                            self._add_neighbor_context(entry, target_id)

                    # B. References from parent document
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

                            for _, target_id, edata in self.graph.out_edges(p, data=True):
                                if edata.get("relation") == "REFERENCES":
                                    self._add_neighbor_context(entry, target_id)

                            # C. Versioning (SUPERSEDES)
                            for replaced_by, _, edata in self.graph.in_edges(p, data=True):
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

        logger.info(f"Final results: {len(hybrid_results)}")
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
