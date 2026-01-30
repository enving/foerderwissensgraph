import logging
import json
import re
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.graph.graph_builder import GraphBuilder
from pypdf import PdfReader

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def import_extra_laws():
    output_graph_path = Path("data/knowledge_graph.json")
    builder = GraphBuilder()

    if output_graph_path.exists():
        builder.load_graph(output_graph_path)

    # Dictionary of law abbreviation -> PDF path
    extra_laws = {
        "UVgO": Path("data/raw/laws/uvgo.pdf"),
        "VOB_A": Path("data/raw/laws/vob-a.pdf"),
    }

    logger.info(f"Starting import of extra laws: {list(extra_laws.keys())}")

    for law_abbr, pdf_path in extra_laws.items():
        if not pdf_path.exists():
            logger.warning(f"File not found: {pdf_path}. Skipping {law_abbr}")
            continue

        try:
            logger.info(f"Processing {law_abbr} via PyPDF...")
            reader = PdfReader(pdf_path)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"

            # Simple paragraph splitting (Heuristic: § number)
            # Find all § markers
            sections = re.split(r"(?=\n§\s*\d+)", full_text)

            law_node_id = f"law_{law_abbr}"
            builder.add_law(
                law_node_id,
                {
                    "title": f"Ordnung: {law_abbr}",
                    "kuerzel": law_abbr,
                    "category": "Vergabeordnung",
                    "source": "BMWK PDF",
                },
            )

            for i, section_text in enumerate(sections):
                if not section_text.strip():
                    continue

                para_match = re.search(r"§\s*(\d+[a-z]*)", section_text)
                para_num = para_match.group(1) if para_match else str(i)
                para_label = para_match.group(0) if para_match else f"Abschnitt {i}"

                chunk_id = f"{law_node_id}_{para_num}".replace(" ", "_")

                builder.add_chunk(
                    law_node_id,
                    chunk_id,
                    {
                        "text": section_text.strip(),
                        "paragraph": para_label,
                        "title": f"{law_abbr} - {para_label}",
                        "section_type": "law_section",
                    },
                )

            logger.info(
                f"Successfully imported {len(sections)} sections for {law_abbr}"
            )

        except Exception as e:
            logger.error(f"Failed to import {law_abbr}: {e}")

    builder.create_reference_edges()
    builder.save_graph(output_graph_path)
    logger.info("Extra law import complete.")


if __name__ == "__main__":
    import_extra_laws()
