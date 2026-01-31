import networkx as nx
import logging
from typing import List, Dict, Set, Any, Optional
import time

logger = logging.getLogger(__name__)


class GraphAlgorithms:
    """
    Advanced graph algorithms for Graph RAG Phase 2.
    Implements Personalized PageRank, smart k-hop expansion, and temporal filtering.
    """

    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph
        self._global_pagerank_cache = None
        self._last_pagerank_time = 0
        self._pagerank_ttl = 3600

    def get_global_pagerank(self) -> Dict[str, float]:
        """Returns (and caches) global PageRank centrality."""
        now = time.time()
        if (
            self._global_pagerank_cache is None
            or (now - self._last_pagerank_time) > self._pagerank_ttl
        ):
            logger.info("Computing global PageRank...")
            simple_graph = nx.DiGraph(self.graph)
            self._global_pagerank_cache = nx.pagerank(simple_graph, alpha=0.85)
            self._last_pagerank_time = now
        return self._global_pagerank_cache

    def personalized_pagerank(
        self, seed_nodes: List[str], alpha: float = 0.85, max_iter: int = 100
    ) -> Dict[str, float]:
        if not seed_nodes:
            return {}

        valid_seeds = [node for node in seed_nodes if node in self.graph]
        if not valid_seeds:
            logger.warning(f"None of the seed nodes {seed_nodes} found in graph.")
            return {}

        personalization = {node: 1.0 / len(valid_seeds) for node in valid_seeds}

        try:
            simple_graph = nx.DiGraph(self.graph)
            return nx.pagerank(
                simple_graph,
                alpha=alpha,
                personalization=personalization,
                max_iter=max_iter,
            )
        except Exception as e:
            logger.error(f"Error computing PPR: {e}")
            return {}

    def extract_ppr_subgraph(
        self, seed_nodes: List[str], top_k: int = 50, threshold: float = 0.0001
    ) -> nx.MultiDiGraph:
        ppr_scores = self.personalized_pagerank(seed_nodes)
        if not ppr_scores:
            return nx.MultiDiGraph()

        sorted_nodes = sorted(ppr_scores.items(), key=lambda x: x[1], reverse=True)
        top_nodes = [node for node, score in sorted_nodes[:top_k] if score >= threshold]

        relevant_nodes = list(set(top_nodes) | set(seed_nodes))
        existing_nodes = [n for n in relevant_nodes if n in self.graph]

        return nx.MultiDiGraph(self.graph.subgraph(existing_nodes))

    def smart_k_hop_expansion(
        self,
        seed_nodes: List[str],
        k: int = 2,
        max_nodes: int = 100,
        allowed_relations: Optional[Set[str]] = None,
    ) -> Set[str]:
        if allowed_relations is None:
            allowed_relations = {
                "REFERENCES",
                "SUPERSEDES",
                "HAS_CHUNK",
                "EQUIVALENT_TO",
            }

        expanded_nodes = set(seed_nodes)
        frontier = set(seed_nodes)

        for _ in range(k):
            next_frontier = set()
            for node in frontier:
                if node not in self.graph:
                    continue

                # Manual filtering to satisfy LSP and handle both MultiDiGraph and DiGraph
                out_edges = []
                for u, v, d in self.graph.edges(node, data=True):
                    if u == node:
                        out_edges.append((u, v, d))

                for _, target, data in out_edges:
                    if data.get("relation") in allowed_relations:
                        if target not in expanded_nodes:
                            next_frontier.add(target)

                in_edges = []
                for u, v, d in self.graph.edges(node, data=True):
                    if v == node:
                        in_edges.append((u, v, d))

                for source, _, data in in_edges:
                    if data.get("relation") in allowed_relations:
                        if source not in expanded_nodes:
                            next_frontier.add(source)

            expanded_nodes.update(next_frontier)
            frontier = next_frontier

            if len(expanded_nodes) >= max_nodes:
                break

        return set(list(expanded_nodes)[:max_nodes])

    def apply_temporal_filter(self, node_ids: List[str]) -> List[str]:
        current_newest = []
        for node_id in node_ids:
            if node_id not in self.graph:
                current_newest.append(node_id)
                continue

            node_data = self.graph.nodes[node_id]
            doc_node = node_id
            if (
                node_data.get("node_type") == "chunk"
                or node_data.get("type") == "chunk"
            ):
                in_edges = []
                for u, v, d in self.graph.edges(node_id, data=True):
                    if v == node_id:
                        in_edges.append((u, v, d))

                parents = [
                    u for u, v, d in in_edges if d.get("relation") == "HAS_CHUNK"
                ]
                if parents:
                    doc_node = parents[0]
                else:
                    current_newest.append(node_id)
                    continue

            newest_doc = doc_node
            visited = {doc_node}

            while True:
                in_edges = []
                for u, v, d in self.graph.edges(newest_doc, data=True):
                    if v == newest_doc:
                        in_edges.append((u, v, d))

                newer_docs = [
                    u for u, v, d in in_edges if d.get("relation") == "SUPERSEDES"
                ]
                if not newer_docs or newer_docs[0] in visited:
                    break
                newest_doc = newer_docs[0]
                visited.add(newest_doc)

            if newest_doc == doc_node:
                current_newest.append(node_id)
            else:
                current_newest.append(newest_doc)

        return list(dict.fromkeys(current_newest))

    def get_centrality_scores(self, node_ids: List[str]) -> Dict[str, float]:
        pagerank = self.get_global_pagerank()
        scores = {}

        node_list = list(self.graph.nodes)
        max_deg = 1
        for n in node_list:
            # Explicit call for compatibility and LSP
            d = int(self.graph.degree(n))
            if d > max_deg:
                max_deg = d

        for node_id in node_ids:
            if node_id not in self.graph:
                scores[node_id] = 0.5
                continue

            pr = pagerank.get(node_id, 0.0)
            deg = int(self.graph.degree(node_id))

            norm_deg = float(deg) / max_deg

            scores[node_id] = (pr * 1000 * 0.7) + (norm_deg * 0.3)

        return scores
