import logging
import sys
import json
from pathlib import Path
import networkx as nx

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def link_law_stubs():
    """Links generic law stubs to their specific parts (e.g., VOB -> VOB/A, VOB/B)."""
    graph_path = Path("data/knowledge_graph.json")
    if not graph_path.exists():
        return

    with open(graph_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        G = nx.node_link_graph(data)
    except:
        G = nx.node_link_graph(data, edges="edges")

    # Mapping: Generic Stub -> [Specific Parts]
    STUB_MAP = {
        "law_VOB": ["law_VOB_A", "law_VOB_B"],
        "law_AEUV": ["law_AEUV_Art_107", "law_AEUV_Art_108"],  # Stubs for now
    }

    modified = False
    for stub_id, parts in STUB_MAP.items():
        if stub_id in G:
            for part_id in parts:
                if part_id in G:
                    if not G.has_edge(stub_id, part_id):
                        G.add_edge(stub_id, part_id, relation="HAS_PART")
                        logger.info(f"Linked {stub_id} --HAS_PART--> {part_id}")
                        modified = True

    if modified:
        # Save back
        out_data = nx.node_link_data(G)
        # Handle NetworkX version divergence for 'edges' vs 'links'
        if "links" in out_data and "edges" not in out_data:
            out_data["edges"] = out_data.pop("links")

        with open(graph_path, "w", encoding="utf-8") as f:
            json.dump(out_data, f, ensure_ascii=False, indent=2)
        logger.info("Graph updated successfully.")
    else:
        logger.info("No changes needed.")


if __name__ == "__main__":
    link_law_stubs()
