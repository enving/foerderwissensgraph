import logging
from pathlib import Path
from src.graph.graph_builder import GraphBuilder
from src.discovery.law_crawler import LawCrawler

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def import_core_laws():
    output_graph_path = Path("data/knowledge_graph.json")
    builder = GraphBuilder()
    crawler = LawCrawler()

    if output_graph_path.exists():
        builder.load_graph(output_graph_path)

    core_laws = {
        "BHO": "bho",
        "VwVfG": "vwvfg",
        "AO": "ao_1977",
        "BGB": "bgb",
        "VgV": "vgv_2016",
        "GWB": "gwb",
        "BRKG": "brkg_2005",
    }

    logger.info(f"Starting initial import of core laws: {list(core_laws.keys())}")

    for law_abbr, search_abbr in core_laws.items():
        try:
            logger.info(f"Importing {law_abbr} (using {search_abbr})...")
            xml_content = crawler.fetch_law(search_abbr)
            norms = crawler.parse_law_xml(xml_content)

            law_node_id = f"law_{law_abbr}"

            builder.add_law(
                law_node_id,
                {
                    "title": f"Gesetz: {law_abbr}",
                    "kuerzel": law_abbr,
                    "category": "Gesetz",
                    "source": "gesetze-im-internet.de",
                },
            )

            for norm in norms:
                para_id = f"{law_node_id}_{norm['paragraph']}".replace(" ", "_")
                builder.add_chunk(
                    law_node_id,
                    para_id,
                    {
                        "text": norm["content"],
                        "paragraph": norm["paragraph"],
                        "title": norm["title"],
                        "section_type": "law_section",
                    },
                )
            logger.info(f"Successfully imported {len(norms)} sections for {law_abbr}")

        except Exception as e:
            logger.error(f"Failed to import {law_abbr}: {e}")

    builder.create_reference_edges()
    builder.save_graph(output_graph_path)
    logger.info("Core law import and reference linking complete.")


if __name__ == "__main__":
    import_core_laws()
