import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.discovery.law_crawler import LawCrawler
from src.graph.graph_builder import GraphBuilder

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def import_health_laws():
    """
    Imports SGB V and KHG into the Knowledge Graph.
    Uses the Hybrid LawCrawler (XML/HTML).
    """
    crawler = LawCrawler()
    builder = GraphBuilder()
    graph_path = Path("data/knowledge_graph.json")

    if graph_path.exists():
        builder.load_graph(graph_path)

    laws_to_import = {
        "sgb_5": "Sozialgesetzbuch (SGB) Fünftes Buch (V) - Gesetzliche Krankenversicherung",
        "khg": "Krankenhausfinanzierungsgesetz",
    }

    for abbr, title in laws_to_import.items():
        logger.info(f"--- Importing {abbr.upper()} ---")
        try:
            # Crawl
            norms = crawler.crawl_law_hybrid(abbr)
            if not norms:
                logger.error(f"Failed to crawl {abbr}")
                continue

            logger.info(f"Fetched {len(norms)} sections for {abbr}")

            # Add Law Node
            law_id = f"law_{abbr.upper()}"
            builder.add_law(
                law_id,
                {
                    "title": title,
                    "kuerzel": abbr.upper(),
                    "category": "Gesetz",
                    "source": "gesetze-im-internet.de",
                },
            )

            # Add Chunks
            for i, norm in enumerate(norms):
                chunk_id = f"{law_id}_{norm['paragraph'].replace(' ', '_')}"
                # Fallback ID if paragraph is empty
                if not norm["paragraph"]:
                    chunk_id = f"{law_id}_chunk_{i}"

                builder.add_chunk(
                    law_id,
                    chunk_id,
                    {
                        "text": norm["content"],
                        "paragraph": norm["paragraph"],
                        "title": f"{abbr.upper()} {norm['paragraph']} {norm['title']}",
                        "section_type": "law_section",
                    },
                )

        except Exception as e:
            logger.error(f"Error importing {abbr}: {e}")

    # Save
    logger.info("Saving updated graph...")
    builder.create_reference_edges()
    builder.save_graph(graph_path)
    logger.info("Done.")


if __name__ == "__main__":
    import_health_laws()
