import json
import logging
from pathlib import Path
from src.parser.docling_engine import DoclingEngine
from src.graph.graph_builder import GraphBuilder
from src.discovery.law_crawler import LawCrawler
from src.config_loader import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def enrich_graph_with_laws(builder: GraphBuilder):
    crawler = LawCrawler()
    referenced_laws = set()

    for node_id, data in builder.graph.nodes(data=True):
        if (
            data.get("type") == "external" or data.get("node_type") == "external"
        ) and node_id.startswith("law_"):
            referenced_laws.add(data.get("kuerzel"))

    if not referenced_laws:
        return

    logger.info(f"Enriching graph with {len(referenced_laws)} referenced laws...")

    for law_abbr in referenced_laws:
        try:
            logger.info(f"Fetching content for law: {law_abbr}")
            xml_content = crawler.fetch_law(law_abbr)
            norms = crawler.parse_law_xml(xml_content)

            law_node_id = f"law_{law_abbr}"
            builder.graph.nodes[law_node_id].update(
                {"node_type": "law", "source": "gesetze-im-internet.de"}
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
        except Exception as e:
            logger.warning(f"Could not enrich law {law_abbr}: {e}")


def main():
    base_raw_dir = Path(settings.get("paths.raw_data", "data/raw"))
    output_graph_path = Path(
        settings.get("paths.knowledge_graph", "data/knowledge_graph.json")
    )

    engine = DoclingEngine()
    builder = GraphBuilder()

    # Load existing graph if available
    existing_hashes = set()
    if output_graph_path.exists():
        builder.load_graph(output_graph_path)
        for node_id, data in builder.graph.nodes(data=True):
            if (
                data.get("type") == "document" or data.get("node_type") == "document"
            ) and "hash" in data:
                existing_hashes.add(data["hash"])

    processed_count = 0
    limit = None

    # Iterate over all directories in data/raw (sorted for predictability)
    dirs = sorted([d for d in base_raw_dir.iterdir() if d.is_dir()])
    for raw_dir in dirs:
        manifest_path = raw_dir / "manifest.json"
        if not manifest_path.exists():
            continue

        logger.info(f"Found manifest in {raw_dir}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        ministerium = manifest.get("ministerium", "unbekannt")

        for nr, file_info in manifest.get("files", {}).items():
            if limit is not None and processed_count >= limit:
                break

            file_hash = file_info["hash"]
            filename = file_info["filename"]

            if file_hash in existing_hashes:
                logger.info(f"Updating metadata for {nr} ({ministerium})")
                builder.add_document(
                    nr,
                    {
                        "title": file_info["title"],
                        "category": file_info["category"],
                        "hash": file_info["hash"],
                        "filename": filename,
                        "url": file_info.get("url"),
                        "ministerium": ministerium,
                    },
                )
                continue

            if not filename.endswith(".pdf"):
                continue

            category = file_info["category"].split(" ")[0]
            pdf_path = raw_dir / category / filename

            # Fallback: sometimes files might be directly in raw_dir (unlikely based on structure but good for safety)
            if not pdf_path.exists():
                pdf_path = raw_dir / filename

            if not pdf_path.exists():
                logger.warning(f"File not found: {pdf_path}")
                continue

            logger.info(f"Processing {nr}: {file_info['title']}")

            try:
                # Add document node
                builder.add_document(
                    nr,
                    {
                        "title": file_info["title"],
                        "category": file_info["category"],
                        "hash": file_info["hash"],
                        "filename": filename,
                        "url": file_info.get("url"),
                        "ministerium": ministerium,
                    },
                )

                # Extract chunks
                chunks = engine.process_document(pdf_path)

                for i, chunk in enumerate(chunks):
                    chunk_id = f"{nr}_chunk_{i}"

                    # Breadcrumb context
                    headings = getattr(chunk.meta, "headings", [])
                    if headings is None:
                        headings = []
                    context_path = " > ".join(headings)

                    citations = engine.citation_extractor.extract(chunk.text)

                    builder.add_chunk(
                        nr,
                        chunk_id,
                        {
                            "text": chunk.text,
                            "context": context_path,
                            "headings": headings,
                            "citations": citations,
                        },
                    )

                processed_count += 1
                builder.save_graph(output_graph_path)

            except Exception as e:
                logger.error(f"Error processing {nr}: {e}")

    builder.create_reference_edges()
    enrich_graph_with_laws(builder)
    builder.save_graph(output_graph_path)
    logger.info(
        f"Successfully processed {processed_count} new documents. Graph saved to {output_graph_path}"
    )


if __name__ == "__main__":
    main()
