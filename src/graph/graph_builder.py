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

    def add_document(self, doc_id: str, metadata: Dict[str, Any]):
        """
        Adds a document node to the graph.
        """
        self.graph.add_node(doc_id, type="document", **metadata)

    def add_chunk(self, doc_id: str, chunk_id: str, chunk_data: Dict[str, Any]):
        """
        Adds a chunk node and connects it to the document.
        """
        self.graph.add_node(chunk_id, type="chunk", **chunk_data)
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
