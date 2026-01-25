#!/usr/bin/env python3
"""
Simple test to verify the data pipeline results and application structure.
"""

import json
import sqlite3
from pathlib import Path


def test_data_pipeline():
    """Test if data pipeline completed successfully"""
    print("🔍 Testing Bund-ZuwendungsGraph Data Pipeline")
    print("=" * 50)

    # Test knowledge graph
    kg_file = Path("data/knowledge_graph.json")
    if kg_file.exists():
        with open(kg_file, "r") as f:
            kg = json.load(f)

        nodes = kg.get("nodes", [])
        edges = kg.get("edges", [])

        print(f"✅ Knowledge Graph:")
        print(f"   Nodes: {len(nodes)}")
        print(f"   Edges: {len(edges)}")

        # Sample node analysis
        if nodes:
            document_nodes = [n for n in nodes if n.get("type") == "document"]
            print(f"   Document nodes: {len(document_nodes)}")

            # Show sample document
            sample_doc = document_nodes[0]
            print(f"   Sample document:")
            print(f"     Title: {sample_doc.get('title', 'N/A')}")
            print(f"     Ministry: {sample_doc.get('ministerium', 'N/A')}")
            print(f"     Category: {sample_doc.get('category', 'N/A')}")
    else:
        print("❌ Knowledge graph not found")

    print()

    # Test ChromaDB
    chroma_db = Path("data/chroma_db/chroma.sqlite3")
    if chroma_db.exists():
        conn = sqlite3.connect(chroma_db)
        cursor = conn.cursor()

        # Count embeddings
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        embedding_count = cursor.fetchone()[0]

        print(f"✅ ChromaDB:")
        print(f"   Embeddings: {embedding_count}")

        conn.close()
    else:
        print("❌ ChromaDB not found")

    print()

    # Test PDF files
    pdf_count = len(list(Path("data/raw").rglob("*.pdf")))
    print(f"✅ PDFs downloaded: {pdf_count}")

    # Test data by ministry
    ministries = {}
    raw_dir = Path("data/raw")
    if raw_dir.exists():
        for ministry_dir in raw_dir.iterdir():
            if ministry_dir.is_dir():
                pdfs = list(ministry_dir.rglob("*.pdf"))
                ministries[ministry_dir.name] = len(pdfs)

        print(f"✅ Files by ministry:")
        for ministry, count in sorted(ministries.items()):
            print(f"   {ministry}: {count} PDFs")

    print()
    print("🎉 Data pipeline verification complete!")


def test_api_structure():
    """Test if API structure is valid"""
    print("\n🔍 Testing API Structure")
    print("=" * 30)

    api_file = Path("src/api/search_api.py")
    if api_file.exists():
        with open(api_file, "r") as f:
            content = f.read()

        # Check for key components
        checks = [
            ("FastAPI app", "app = FastAPI"),
            ("CORS middleware", "CORSMiddleware"),
            ("Hybrid search", "HybridSearchEngine"),
            ("Search endpoint", "@app.get"),
        ]

        for check_name, check_pattern in checks:
            if check_pattern in content:
                print(f"✅ {check_name}: Found")
            else:
                print(f"❌ {check_name}: Missing")
    else:
        print("❌ API file not found")


if __name__ == "__main__":
    test_data_pipeline()
    test_api_structure()
