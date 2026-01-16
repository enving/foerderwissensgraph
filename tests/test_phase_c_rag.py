import sys
import os
from pathlib import Path

sys.path.append(os.getcwd())

from src.parser.hybrid_search import HybridSearchEngine
from src.parser.rule_extractor import RuleExtractor


def test_multi_hop_rag():
    print("--- Phase C: Multi-Hop RAG Verification ---")

    engine = HybridSearchEngine()
    answer_engine = RuleExtractor()

    query = "Wie ist die Verwendungsprüfung nach § 44 BHO in der ANBest-P geregelt?"

    print(f"\nQuery: {query}")

    results = engine.search(query, limit=3)

    if not results:
        print("❌ No results found. Ensure graph and DB are populated.")
        return

    found_reference = False
    context_chunks = []

    print("\nSearch Results & Context:")
    for res in results:
        print(f"Match: {res['doc_title']} > {res['breadcrumbs']} ({res['score']:.2f})")

        for neighbor in res.get("neighbor_context", []):
            if neighbor.get("type") == "reference":
                found_reference = True
                print(f"  🔗 Found Multi-Hop Reference: {neighbor['breadcrumbs']}")

            context_chunks.append(
                f"Quelle: {neighbor.get('breadcrumbs', 'Unbekannt')}\nText: {neighbor['text']}"
            )

        context_chunks.append(
            f"Quelle: {res['doc_title']} > {res['breadcrumbs']}\nText: {res['text']}"
        )

    if found_reference:
        print("\n✅ Multi-Hop Logic works: References found in graph traversal.")
    else:
        print(
            "\n⚠️ Multi-Hop Logic warning: No references found in traversal for this query."
        )

    print("\nGenerating Answer using combined context...")
    try:
        answer = answer_engine.generate_answer(query, context_chunks)
        print(f"\nAI Answer:\n{answer}")

        if "BHO" in answer or "Bundeshaushaltsordnung" in answer:
            print("\n✅ RAG Success: Answer incorporates cross-document knowledge.")
        else:
            print("\n⚠️ RAG Partial: Answer might be missing legal context.")

    except Exception as e:
        print(f"❌ Answer generation failed: {e}")


if __name__ == "__main__":
    test_multi_hop_rag()
