from pathlib import Path
import sys
import os

sys.path.append(os.getcwd())

from src.parser.docling_engine import DoclingEngine


def test_integration():
    engine = DoclingEngine()

    class MockChunk:
        def __init__(self, text):
            self.text = text
            self.meta = type("obj", (object,), {"headings": ["Test Section"]})

    text_with_citations = "Dies ist ein Test gemäß § 44 BHO und BNBest-P."

    mock_chunk = MockChunk(text_with_citations)

    print(f"Testing text: {text_with_citations}")
    citations = engine.citation_extractor.extract(mock_chunk.text)

    print(f"Extracted citations: {citations}")

    assert len(citations) == 2
    assert citations[0]["target"] == "BHO"
    assert citations[1]["target"] == "BNBest-P"
    print("✅ Integration test passed!")


if __name__ == "__main__":
    test_integration()
