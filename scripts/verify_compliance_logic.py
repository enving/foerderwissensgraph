import sys
import json
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.graph.compliance_mapper import ComplianceMapper
from src.models.schemas import ExpandContextRequest

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ComplianceVerifier")


def verify_compliance():
    # Initialize Mapper
    graph_path = Path("data/knowledge_graph.json")
    if not graph_path.exists():
        print(f"ERROR: Graph not found at {graph_path}")
        return

    mapper = ComplianceMapper(graph_path)

    # Test Case 1: mFUND (Real World Example from Chat)
    # Problem: Found BMBF rules instead of BMVI/General ANBest-P
    mfund_text = """
    Förderrichtlinie mFUND (BMVI)
    ...
    1.6 Das BMVI gewährt die Zuwendungen für FuE-Vorhaben des mFUND nach Maßgabe dieser Richtlinie, der
    §§ 23 und 44 der Bundeshaushaltsordnung (BHO) und den dazu erlassenen Allgemeinen Verwaltungsvorschriften
    (VV-BHO).
    ...
    6.1 Bestandteil eines Zuwendungsbescheids auf Ausgabenbasis werden die „Allgemeinen Nebenbestimmungen
    für Zuwendungen zur Projektförderung“ (ANBest-P), die „Allgemeinen Nebenbestimmungen für Zuwendungen
    zur Projektförderung auf Kostenbasis“ (ANBest-P-Kosten).
    """

    # Test Case 2: Explicit BMBF (Control Group)
    bmbf_text = """
    Bekanntmachung des BMBF
    Grundlagen:
    Die Zuwendungen werden nach Maßgabe dieser Richtlinie, der BHO und der BNBest-BMBF 98 gewährt.
    """

    # Test Case 3: Mixed/Confusing (Adversarial)
    mixed_text = """
    Das Bundesministerium für Verkehr (BMVI) fördert Projekte.
    Es wird darauf hingewiesen, dass in ähnlichen Fällen das BMBF die BNBest-BMBF 98 anwendet.
    Für dieses Projekt gilt jedoch die ANBest-GK.
    """

    test_cases = [
        ("mFUND_BMVI", mfund_text, ["ANBest-P", "ANBest-P-Kosten", "BHO"]),
        ("BMBF_Standard", bmbf_text, ["BNBest-BMBF 98"]),
        (
            "Mixed_Context",
            mixed_text,
            ["ANBest-GK"],
        ),  # Should ideally NOT match BNBest-BMBF as governing
    ]

    print(f"\n{'=' * 60}")
    print(f"COMPLIANCE LOGIC VERIFICATION REPORT")
    print(f"{'=' * 60}\n")

    for label, text, expected in test_cases:
        print(f"--- Testing: {label} ---")
        request = ExpandContextRequest(context_label=label, text_chunks=[text])

        try:
            response = mapper.expand_context(request)

            found_sources = [r.source_doc for r in response.mapped_regulations]
            found_categories = [r.category for r in response.mapped_regulations]

            print(f"Expected Keywords: {expected}")
            print(f"Found Sources:     {found_sources}")

            # Check for BMBF contamination in mFUND
            if label == "mFUND_BMVI":
                bmbf_hits = [s for s in found_sources if "BMBF" in s]
                if bmbf_hits:
                    print(
                        f"❌ CRITICAL: Found BMBF regulations in BMVI context: {bmbf_hits}"
                    )
                else:
                    print(f"✅ PASSED: No BMBF contamination.")

                anbest_hits = [s for s in found_sources if "ANBest-P" in s]
                if not anbest_hits:
                    print(f"❌ WARNING: Missed explicit citation of ANBest-P")

            # Check for Mixed Context
            if label == "Mixed_Context":
                if "BNBest-BMBF 98" in found_sources:
                    print(
                        f"⚠️  NOTE: Found BNBest-BMBF 98 despite it being a side-note."
                    )

        except Exception as e:
            print(f"ERROR: {e}")

        print("\n")


if __name__ == "__main__":
    verify_compliance()
