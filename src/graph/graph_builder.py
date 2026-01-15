import networkx as nx
from typing import Dict, List, Any
from pathlib import Path
import json


class GraphBuilder:
    """
    Builds a Knowledge Graph using NetworkX.
    """

    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def add_law(self, law_id: str, metadata: Dict[str, Any]):
        self.graph.add_node(law_id, node_type="law", **metadata)

    def add_document(self, doc_id: str, metadata: Dict[str, Any]):
        self.graph.add_node(doc_id, node_type="document", **metadata)

    def add_chunk(self, doc_id: str, chunk_id: str, chunk_data: Dict[str, Any]):
        self.graph.add_node(chunk_id, node_type="chunk", **chunk_data)
        self.graph.add_edge(doc_id, chunk_id, relation="HAS_CHUNK")

    def save_graph(self, output_path: Path):
        """
        Saves the graph in GraphML or JSON format.
        """
        # Using JSON format for better compatibility with RAG tools
        data = nx.node_link_data(self.graph)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_graph(self, input_path: Path):
        """
        Loads the graph from a JSON file.
        """
        if input_path.exists():
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.graph = nx.node_link_graph(data)

    def create_reference_edges(self):
        """
        Iterates over all chunks and creates REFERENCES edges based on extracted citations.
        Also creates stub-nodes for external laws (BHO, etc.).
        """
        kuerzel_map = {}
        for node_id, data in self.graph.nodes(data=True):
            if data.get("type") == "document" and data.get("kuerzel"):
                k = data["kuerzel"].strip()
                if k and k not in kuerzel_map:
                    kuerzel_map[k] = node_id

        new_edges = []
        external_nodes = {}

        for node_id, data in self.graph.nodes(data=True):
            if data.get("type") == "chunk" and "citations" in data:
                for cit in data["citations"]:
                    target = cit["target"]

                    if cit["type"] == "regulation":
                        if target in kuerzel_map:
                            new_edges.append(
                                (node_id, kuerzel_map[target], "REFERENCES")
                            )

                    elif cit["type"] == "law":
                        law_id = f"law_{target}"
                        if law_id not in self.graph and law_id not in external_nodes:
                            external_nodes[law_id] = {
                                "type": "external",
                                "title": f"Gesetz: {target}",
                                "kuerzel": target,
                            }
                        new_edges.append((node_id, law_id, "REFERENCES"))

        for eid, edata in external_nodes.items():
            self.graph.add_node(eid, **edata)

        for u, v, rel in new_edges:
            exists = False
            if self.graph.has_edge(u, v):
                for key, edata in self.graph.get_edge_data(u, v).items():
                    if edata.get("relation") == rel:
                        exists = True
                        break

            if not exists:
                self.graph.add_edge(u, v, relation=rel)
