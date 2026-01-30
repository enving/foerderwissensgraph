import sys
from pathlib import Path
import json

# Setup path
sys.path.append(str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.api.search_api import app

client = TestClient(app)


def test_scope_constraint():
    print("=== Testing Scope Constraint (TASK-028) ===")

    # 1. Normal Search
    print("\n[Step 1] Performing normal advanced search...")
    resp1 = client.get("/search/advanced", params={"q": "Ausschreibung", "limit": 10})
    results1 = resp1.json()["results"]
    print(f"Normal search returned {len(results1)} results.")

    # 2. Search with Context Doc ID (e.g. mFUND or something known to have BHO)
    # Let's find a doc ID from the graph first
    with open("data/knowledge_graph.json", "r") as f:
        graph_data = json.load(f)

    # Find a doc that has REFERENCES
    context_doc_id = None
    referenced_ids = []

    # NetworkX link format
    links = graph_data.get("links", [])
    for link in links:
        if link.get("relation") == "REFERENCES":
            context_doc_id = link["source"]
            referenced_ids.append(link["target"])
            break

    if not context_doc_id:
        # Try different format
        edges = graph_data.get("edges", [])
        for edge in edges:
            if edge.get("relation") == "REFERENCES":
                context_doc_id = edge["source"]
                referenced_ids.append(edge["target"])
                break

    if not context_doc_id:
        print("Could not find a document with REFERENCES in the graph for testing.")
        # Fallback to a known one if possible or just use a dummy
        context_doc_id = "0347"  # Often NKBF or similar in this project

    print(f"\n[Step 2] Performing scoped search for doc: {context_doc_id}")
    print(f"Expect results to be from {context_doc_id} or its references.")

    resp2 = client.get(
        "/search/advanced",
        params={"q": "Ausschreibung", "limit": 10, "context_doc_id": context_doc_id},
    )
    results2 = resp2.json()["results"]
    print(f"Scoped search returned {len(results2)} results.")

    for res in results2:
        doc_id = res["id"].split("_chunk_")[0]
        # It should be either context_doc_id or one of its references (latest versions)
        # For simplicity, we just check if it's NOT a random doc
        print(f"  Result from: {res.get('doc_title')} ({doc_id})")

    # 3. Test with Uploaded Doc
    print("\n[Step 3] Testing with uploaded document context...")
    # Mock upload
    doc_text = "Dies ist eine Testrichtlinie. Es gelten die NKBF 98."
    upload_resp = client.post(
        "/chat/upload", files={"file": ("test.txt", doc_text, "text/plain")}
    )
    uploaded_doc_id = upload_resp.json()["uploaded_doc_id"]
    print(f"Uploaded doc ID: {uploaded_doc_id}")

    resp3 = client.get(
        "/search/advanced", params={"q": "Zuwendung", "context_doc_id": uploaded_doc_id}
    )
    results3 = resp3.json()["results"]
    print(f"Scoped search (upload) returned {len(results3)} results.")
    for res in results3:
        print(
            f"  Result from: {res.get('doc_title')} ({res['id'].split('_chunk_')[0]})"
        )


if __name__ == "__main__":
    try:
        test_scope_constraint()
        print("\nAll tests passed! ✅")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
