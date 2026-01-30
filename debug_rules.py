import json
import networkx as nx
from pathlib import Path

graph_path = Path("data/knowledge_graph.json")

if graph_path.exists():
    with open(graph_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        G = nx.node_link_graph(data)
    except:
        G = nx.node_link_graph(data, edges="edges")

    print(f"Nodes: {len(G.nodes)}")

    # Check Chunk IDs and Rules
    sample_chunks = []
    rule_counts = 0

    for n, d in G.nodes(data=True):
        if d.get("type") == "chunk":
            if d.get("rules"):
                rule_counts += 1
                sample_chunks.append(n)

    print(f"Chunks with rules: {rule_counts}")
    print("Sample IDs:", sample_chunks[:10])

    # Check specific doc IDs vs Chunk IDs
    bho_chunks = [n for n in sample_chunks if "BHO" in str(n)]
    print("BHO Chunks:", bho_chunks[:5])

    nkbf_chunks = [n for n in sample_chunks if "0347" in str(n)]
    print("NKBF Chunks:", nkbf_chunks[:5])
