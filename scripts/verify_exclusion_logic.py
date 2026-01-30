import sys
from pathlib import Path
import json

# Setup path
sys.path.append(str(Path(__file__).parent.parent))

from src.graph.compliance_mapper import ComplianceMapper
from src.parser.citation_extractor import CitationExtractor
from src.models.schemas import ExpandContextRequest


def test_negation_detection():
    print("=== Testing Negation & Exclusion Detection ===")
    extractor = CitationExtractor()

    # Example 1: Regular citation
    text1 = "Es gelten die BNBest-P."
    cits1 = extractor.extract(text1)
    print(f"Text: '{text1}'")
    for c in cits1:
        print(f"  Target: {c['target']}, Excluded: {c['is_excluded']}")
    assert not cits1[0]["is_excluded"]

    # Example 2: Explicitly excluded
    text2 = "Die BNBest-BMBF findet keine Anwendung."
    cits2 = extractor.extract(text2)
    print(f"\nText: '{text2}'")
    for c in cits2:
        print(f"  Target: {c['target']}, Excluded: {c['is_excluded']}")
    assert cits2[0]["is_excluded"]

    # Example 3: Excluded before
    text3 = "Abweichend von den ANBest-P wird folgendes vereinbart..."
    cits3 = extractor.extract(text3)
    print(f"\nText: '{text3}'")
    for c in cits3:
        print(f"  Target: {c['target']}, Excluded: {c['is_excluded']}")
    assert cits3[0]["is_excluded"]


def test_compliance_mapper_exclusion():
    print("\n=== Testing ComplianceMapper Exclusion Logic ===")
    mapper = ComplianceMapper(graph_path=Path("data/knowledge_graph.json"))

    # 1. Without exclusion
    req1 = ExpandContextRequest(
        context_label="test_normal", text_chunks=["Es gelten die NKBF 98."]
    )
    resp1 = mapper.expand_context(req1)
    found_nkbf = any("NKBF" in reg.source_doc for reg in resp1.mapped_regulations)
    print(f"Normal request found NKBF: {found_nkbf}")

    # 2. With exclusion
    req2 = ExpandContextRequest(
        context_label="test_excluded",
        text_chunks=["Die NKBF 98 findet keine Anwendung."],
    )
    resp2 = mapper.expand_context(req2)
    found_nkbf_ex = any("NKBF" in reg.source_doc for reg in resp2.mapped_regulations)
    print(f"Excluded request found NKBF: {found_nkbf_ex}")

    assert not found_nkbf_ex


if __name__ == "__main__":
    try:
        test_negation_detection()
        test_compliance_mapper_exclusion()
        print("\nAll tests passed! ✅")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
