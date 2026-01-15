import sys
import os
from pathlib import Path

sys.path.append(os.getcwd())

from src.graph.graph_builder import GraphBuilder


def test_graph_linking():
    builder = GraphBuilder()

    builder.add_document("doc_anbest_p", {"title": "ANBest-P", "kuerzel": "ANBest-P"})

    builder.add_chunk(
        "doc_main",
        "chunk_1",
        {
            "text": "Siehe ANBest-P und § 44 BHO.",
            "citations": [
                {"type": "regulation", "target": "ANBest-P"},
                {"type": "law", "target": "BHO"},
            ],
        },
    )

    print("Graph before linking:")
    print(f"Nodes: {builder.graph.number_of_nodes()}")
    print(f"Edges: {builder.graph.number_of_edges()}")

    builder.create_reference_edges()

    print("\nGraph after linking:")
    print(f"Nodes: {builder.graph.number_of_nodes()}")
    print(f"Edges: {builder.graph.number_of_edges()}")

    edges = list(builder.graph.edges(data=True))
    ref_edges = [e for e in edges if e[2].get("relation") == "REFERENCES"]

    for u, v, data in ref_edges:
        print(f"  Edge: {u} --({data['relation']})--> {v}")

    assert len(ref_edges) == 2
    targets = [e[1] for e in ref_edges]
    assert "doc_anbest_p" in targets
    assert "law_BHO" in targets

    print("\n✅ Graph linking test passed!")


if __name__ == "__main__":
    test_graph_linking()
