import sys
import logging
from pathlib import Path

# Add src to path
sys.path.append(".")

# Mock settings to avoid loading everything
from unittest.mock import MagicMock

sys.modules["src.config_loader"] = MagicMock()
sys.modules["src.config_loader"].settings = {
    "paths.knowledge_graph": "data/knowledge_graph.json"
}

from src.models.schemas import ExpandContextRequest
from src.graph.compliance_mapper import ComplianceMapper

# Setup logging
logging.basicConfig(level=logging.INFO)


def test_analysis_flow():
    print("--- Testing Compliance Mapper Analysis Flow ---")

    # Load Mapper
    graph_path = Path("data/knowledge_graph.json")
    if not graph_path.exists():
        print("Skipping: Graph not found")
        return

    try:
        mapper = ComplianceMapper(graph_path)
    except Exception as e:
        print(f"CRITICAL: Failed to init ComplianceMapper: {e}")
        return

    # Simulate Text Input (from the Drohne Example)
    text_chunk = """
    Der Bund gewährt die Zuwendungen nach Maßgabe dieser Förderrichtlinie, der §§ 23 und 44 der Bundeshaushaltsordnung (BHO).
    Es gelten die NKBF 2017 und die BNBest-mittelbarer Abruf-BMBF.
    """

    req = ExpandContextRequest(
        context_label="Test Upload", text_chunks=[text_chunk], metadata={}
    )

    try:
        print("Running expand_context...")
        response = mapper.expand_context(req)
        print("✅ Success!")
        print(f"Compliance Context ID: {response.compliance_context_id}")
        for reg in response.mapped_regulations:
            print(f" - Found: {reg.source_doc} ({reg.category})")
            for r in reg.rules[:2]:
                print(f"   > Rule: {r.content[:50]}...")

    except Exception as e:
        print(f"❌ CRASHED: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_analysis_flow()
