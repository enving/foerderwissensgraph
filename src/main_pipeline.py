import json
import logging
from pathlib import Path
from src.parser.docling_engine import DoclingEngine
from src.graph.graph_builder import GraphBuilder

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    raw_dir = Path("data/raw/bmwe")
    manifest_path = raw_dir / "manifest.json"
    output_graph_path = Path("data/knowledge_graph.json")

    if not manifest_path.exists():
        logger.error(f"Manifest not found at {manifest_path}")
        return

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    engine = DoclingEngine()
    builder = GraphBuilder()

    # Load existing graph if available
    if output_graph_path.exists():
        builder.load_graph(output_graph_path)

    processed_count = 0
    # Process only a few documents for the first version/test
    # We can scale this up later
    limit = 5

    for nr, file_info in manifest.get("files", {}).items():
        if processed_count >= limit:
            break

        filename = file_info["filename"]
        if not filename.endswith(".pdf"):
            continue

        category = file_info["category"].split(" ")[0]
        pdf_path = raw_dir / category / filename

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

                builder.add_chunk(
                    nr,
                    chunk_id,
                    {"text": chunk.text, "context": context_path, "headings": headings},
                )

            processed_count += 1

        except Exception as e:
            logger.error(f"Error processing {nr}: {e}")

    builder.save_graph(output_graph_path)
    logger.info(
        f"Successfully processed {processed_count} documents. Graph saved to {output_graph_path}"
    )


if __name__ == "__main__":
    main()
