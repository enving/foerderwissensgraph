import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.graph.compliance_mapper import ComplianceMapper
from src.models.schemas import ExpandContextRequest

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def test_on_demand():
    graph_path = Path("data/knowledge_graph.json")
    mapper = ComplianceMapper(graph_path=graph_path, on_demand_enabled=True)

    # Text mentioning AtG with paragraph
    text = "Der Zuwendungsempfänger muss § 1 AtG beachten."

    logger.info("Triggering compliance mapping with missing law 'AtG'...")
    req = ExpandContextRequest(context_label="Test", text_chunks=[text])

    response = mapper.expand_context(req)

    for reg in response.mapped_regulations:
        logger.info(f"Detected: {reg.source_doc} (ID: {reg.doc_id})")

    found = False
    for reg in response.mapped_regulations:
        if "ATG" in reg.source_doc.upper():
            found = True
            logger.info(
                f"SUCCESS: Found regulation: {reg.source_doc} (ID: {reg.doc_id})"
            )
            logger.info(f"Rules found: {len(reg.rules)}")

    if not found:
        logger.error("FAILED: AtG not found in mapped regulations.")


if __name__ == "__main__":
    test_on_demand()
