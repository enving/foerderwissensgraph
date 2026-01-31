import json
import logging
from pathlib import Path
from collections import Counter
import networkx as nx

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def generate_report():
    """Generates a health and coverage report for the Knowledge Graph."""
    graph_path = Path("data/knowledge_graph.json")
    if not graph_path.exists():
        logger.error(f"Graph file not found at {graph_path}")
        return

    with open(graph_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        G = nx.node_link_graph(data)
    except:
        G = nx.node_link_graph(data, edges="edges")

    nodes = G.nodes(data=True)
    edges = G.edges(data=True)

    print("\n" + "=" * 40)
    print(" KNOWLEDGE GRAPH HEALTH REPORT ")
    print("=" * 40)

    # 1. Basic Stats
    print(f"\n[Basic Statistics]")
    print(f"Total Nodes: {len(nodes)}")
    print(f"Total Edges: {len(edges)}")

    type_counts = Counter(
        [d.get("node_type", d.get("type", "unknown")) for n, d in nodes]
    )
    for ntype, count in type_counts.items():
        print(f"  - {ntype}: {count}")

    # 2. Coverage Analysis
    print(f"\n[Coverage Analysis]")
    laws = [
        n for n, d in nodes if d.get("node_type") == "law" or d.get("type") == "law"
    ]

    def has_content_recursive(node_id, visited=None):
        if visited is None:
            visited = set()
        if node_id in visited:
            return False
        visited.add(node_id)

        for u, v, d in edges:
            if u == node_id:
                if d.get("relation") == "HAS_CHUNK":
                    return True
                if d.get("relation") == "HAS_PART":
                    if has_content_recursive(v, visited):
                        return True
        return False

    laws_with_content = [l for l in laws if has_content_recursive(l)]

    print(f"Total Laws: {len(laws)}")
    print(f"Laws with Content (Direct or Parts): {len(laws_with_content)}")
    print(f"Coverage: {(len(laws_with_content) / len(laws) * 100 if laws else 0):.1f}%")

    dead_angles = [l for l in laws if l not in laws_with_content]
    if dead_angles:
        print(f"\n[Dead Angles (Laws without content - Top 10)]")
        for l in dead_angles[:10]:
            # Try to get kuerzel or title
            d = G.nodes[l]
            name = d.get("kuerzel", d.get("title", l))
            print(f"  - {l} ({name})")

    # 3. Centrality (Citation Impact)
    print(f"\n[Top 10 Most Cited Laws/Docs]")
    # Edges with relation "REFERENCES"
    citations = [v for u, v, d in edges if d.get("relation") == "REFERENCES"]
    top_cited = Counter(citations).most_common(10)
    for doc_id, count in top_cited:
        d = G.nodes.get(doc_id, {})
        name = d.get("kuerzel", d.get("title", doc_id))
        print(f"  {count:3d} citations: {name} ({doc_id})")

    # 4. Ministry Distribution
    print(f"\n[Ministry Distribution]")
    ministries = Counter(
        [
            d.get("ministerium", "Unknown/Federal")
            for n, d in nodes
            if d.get("node_type") == "document"
        ]
    )
    for min_name, count in ministries.most_common():
        print(f"  - {min_name}: {count}")

    print("\n" + "=" * 40)


if __name__ == "__main__":
    generate_report()
