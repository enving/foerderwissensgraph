import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.graph.compliance_mapper import ComplianceMapper
from src.models.schemas import ExpandContextRequest

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def test_external_concepts():
    graph_path = Path("data/knowledge_graph.json")
    mapper = ComplianceMapper(graph_path=graph_path, on_demand_enabled=True)

    # Text mentioning AGVO (should be mapped via concept_map now)
    text = "Das Vorhaben wird als Beihilfe nach der AGVO eingestuft."

    logger.info("Testing implicit expansion for 'AGVO' via external config...")
    req = ExpandContextRequest(context_label="Test_AGVO", text_chunks=[text])

    response = mapper.expand_context(req)

    found_agvo = False
    for reg in response.mapped_regulations:
        if "AGVO" in reg.source_doc.upper():
            found_agvo = True
            logger.info(f"SUCCESS: Found AGVO via implicit mapping: {reg.source_doc}")

    if not found_agvo:
        logger.error("FAILED: AGVO not found via implicit mapping.")


if __name__ == "__main__":
    test_external_concepts()
