import json
from pathlib import Path


def export_to_d3(graph_path: Path, output_path: Path):
    """
    Exports the NetworkX JSON graph to a D3.js compatible format.
    Focuses on Document-to-Document (SUPERSEDES) and Document-to-Chunk relations.
    """
    if not graph_path.exists():
        print(f"Error: {graph_path} not found.")
        return

    with open(graph_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # D3 force graph typically expects { nodes: [], links: [] }
    # Our graph already has this structure, but we might want to filter it
    # for better performance in the browser.

    # Example: Filter to only show Document nodes and SUPERSEDES edges
    doc_nodes = [n for n in data["nodes"] if n.get("type") == "document"]

    # Find all edges between document nodes (mostly SUPERSEDES)
    doc_ids = {n["id"] for n in doc_nodes}
    edge_key = "links" if "links" in data else "edges"
    doc_links = [
        l
        for l in data.get(edge_key, [])
        if l["source"] in doc_ids and l["target"] in doc_ids
    ]

    d3_data = {"nodes": doc_nodes, "links": doc_links}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(d3_data, f, indent=2, ensure_ascii=False)

    print(f"D3.js compatible graph exported to {output_path}")
    print(f"Nodes: {len(doc_nodes)}, Links: {len(doc_links)}")


if __name__ == "__main__":
    export_to_d3(
        Path("data/knowledge_graph.json"), Path("data/d3_graph_documents.json")
    )
