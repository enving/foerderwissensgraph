import os
from pathlib import Path
from typing import List, Dict, Any, Iterator
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker.hierarchical_chunker import HierarchicalChunker


class DoclingEngine:
    """
    Engine to convert PDFs to hierarchical Markdown using Docling.
    """

    def __init__(self):
        self.converter = DocumentConverter()
        self.chunker = HierarchicalChunker()

    def convert_to_markdown(self, pdf_path: Path) -> str:
        """
        Converts a PDF file to Markdown.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        result = self.converter.convert(str(pdf_path))
        return result.document.export_to_markdown()

    def process_document(self, pdf_path: Path) -> Iterator[Any]:
        """
        Converts PDF and returns hierarchical chunks using Docling's native chunker.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        result = self.converter.convert(str(pdf_path))
        return self.chunker.chunk(result.document)


class LegacyHierarchicalChunker:
    """
    Chunks Markdown content based on headers (H1, H2, H3, etc.)
    while preserving context. (Ported logic/Fallback)
    """

    def chunk(self, markdown_text: str) -> List[Dict[str, Any]]:
        chunks = []
        lines = markdown_text.split("\n")

        current_context: Dict[str, Any] = {
            "h1": None,
            "h2": None,
            "h3": None,
            "h4": None,
        }

        current_chunk_content = []

        for line in lines:
            if line.startswith("# "):
                self._flush_chunk(chunks, current_context, current_chunk_content)
                current_context["h1"] = line[2:].strip()
                current_context["h2"] = None
                current_context["h3"] = None
                current_context["h4"] = None
            elif line.startswith("## "):
                self._flush_chunk(chunks, current_context, current_chunk_content)
                current_context["h2"] = line[3:].strip()
                current_context["h3"] = None
                current_context["h4"] = None
            elif line.startswith("### "):
                self._flush_chunk(chunks, current_context, current_chunk_content)
                current_context["h3"] = line[4:].strip()
                current_context["h4"] = None
            elif line.startswith("#### "):
                self._flush_chunk(chunks, current_context, current_chunk_content)
                current_context["h4"] = line[5:].strip()
            else:
                current_chunk_content.append(line)

        self._flush_chunk(chunks, current_context, current_chunk_content)
        return chunks

    def _flush_chunk(self, chunks, context, content):
        if not content:
            return

        text = "\n".join(content).strip()
        if text:
            chunks.append({"context": context.copy(), "content": text})
        content.clear()


if __name__ == "__main__":
    # Test with a dummy or sample if possible
    pass
