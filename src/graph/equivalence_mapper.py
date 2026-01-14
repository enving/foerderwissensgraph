import json
from pathlib import Path


def create_equivalent_edges():
    graph_path = Path("data/knowledge_graph.json")
    if not graph_path.exists():
        print("Graph not found.")
        return

    with open(graph_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    docs = [n for n in nodes if n.get("type") == "document"]

    # Group by kuerzel and stand
    mapping = {}
    for d in docs:
        kuerzel = d.get("kuerzel")
        stand = d.get("stand")
        if not kuerzel or not stand:
            continue

        key = (kuerzel, stand)
        if key not in mapping:
            mapping[key] = []
        mapping[key].append(d["id"])

    new_edges_count = 0
    # For each group, create bi-directional EQUIVALENT_TO edges
    for key, ids in mapping.items():
        if len(ids) > 1:
            print(f"Found equivalents for {key}: {ids}")
            for i in range(len(ids)):
                for j in range(len(ids)):
                    if i != j:
                        # Check if edge already exists
                        exists = any(
                            e["source"] == ids[i]
                            and e["target"] == ids[j]
                            and e["relation"] == "EQUIVALENT_TO"
                            for e in edges
                        )
                        if not exists:
                            edges.append(
                                {
                                    "source": ids[i],
                                    "target": ids[j],
                                    "relation": "EQUIVALENT_TO",
                                }
                            )
                            new_edges_count += 1

    data["edges"] = edges

    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Added {new_edges_count} EQUIVALENT_TO edges.")


if __name__ == "__main__":
    create_equivalent_edges()
