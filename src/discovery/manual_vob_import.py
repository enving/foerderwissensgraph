import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.graph.graph_builder import GraphBuilder

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def import_vob_manual():
    """
    Manually imports key sections of VOB/A and VOB/B since official XML/HTML sources
    on gesetze-im-internet.de are currently returning 404 and PDFs are empty.
    """
    output_graph_path = Path("data/knowledge_graph.json")
    builder = GraphBuilder()

    if output_graph_path.exists():
        builder.load_graph(output_graph_path)

    vob_a_sections = [
        {
            "paragraph": "§ 1",
            "title": "Bauleistungen",
            "content": "Bauleistungen sind Arbeiten jeder Art, durch die eine bauliche Anlage hergestellt, instand gehalten, geändert oder beseitigt wird.",
        },
        {
            "paragraph": "§ 2",
            "title": "Grundsätze",
            "content": "(1) Bauleistungen sind so zu vergeben, dass eine wirtschaftliche und sparsame Verwendung der Haushaltsmittel gewährleistet ist. (2) Im Wettbewerb sind die Teilnehmer gleich zu behandeln. (3) Die Vergabe erfolgt an fachkundige, leistungsfähige und zuverlässige Unternehmen zu angemessenen Preisen.",
        },
        {
            "paragraph": "§ 3",
            "title": "Arten der Vergabe",
            "content": "(1) Die Vergabe von Bauleistungen erfolgt im Wege der Öffentlichen Ausschreibung, der Beschränkten Ausschreibung oder der Freihändigen Vergabe. (2) Die Öffentliche Ausschreibung ist das Verfahren, in dem eine unbeschränkte Zahl von Unternehmen zur Abgabe von Angeboten öffentlich aufgefordert wird.",
        },
        {
            "paragraph": "§ 3a",
            "title": "Zulässigkeitsvoraussetzungen",
            "content": "(1) Die Öffentliche Ausschreibung muss die Regel sein. (2) Eine Beschränkte Ausschreibung mit Teilnahmewettbewerb ist zulässig, wenn die Öffentliche Ausschreibung für den Auftraggeber oder die Bewerber einen unverhältnismäßigen Aufwand verursachen würde.",
        },
    ]

    vob_b_sections = [
        {
            "paragraph": "§ 1",
            "title": "Art und Umfang der Leistung",
            "content": "(1) Die Leistung wird nach dem Vertrag und der Leistungsbeschreibung ausgeführt. (2) Bei Widersprüchen im Vertrag gelten nacheinander: 1. die Leistungsbeschreibung, 2. die Besonderen Vertragsbedingungen, 3. etwaige Zusätzliche Vertragsbedingungen, 4. die Allgemeinen Vertragsbedingungen für die Ausführung von Bauleistungen (VOB/B).",
        },
        {
            "paragraph": "§ 2",
            "title": "Vergütung",
            "content": "(1) Durch die vereinbarten Preise werden alle Leistungen abgegolten, die nach der Leistungsbeschreibung, den Vertragsbedingungen und den Technischen Vertragsbedingungen zur vertraglichen Leistung gehören.",
        },
    ]

    # Import VOB/A
    law_a_id = "law_VOB_A"
    builder.add_law(
        law_a_id,
        {
            "title": "Vergabe- und Vertragsordnung für Bauleistungen - Teil A (VOB/A)",
            "kuerzel": "VOB/A",
            "category": "Vergabeordnung",
            "source": "Manual Import (Reference: dejure.org)",
        },
    )

    for i, s in enumerate(vob_a_sections):
        chunk_id = f"{law_a_id}_{s['paragraph'].replace(' ', '_').replace('§', 'S')}"
        builder.add_chunk(
            law_a_id,
            chunk_id,
            {
                "text": s["content"],
                "paragraph": s["paragraph"],
                "title": f"VOB/A {s['paragraph']} {s['title']}",
                "section_type": "law_section",
                "type": "chunk",
            },
        )

    # Import VOB/B
    law_b_id = "law_VOB_B"
    builder.add_law(
        law_b_id,
        {
            "title": "Vergabe- und Vertragsordnung für Bauleistungen - Teil B (VOB/B)",
            "kuerzel": "VOB/B",
            "category": "Vergabeordnung",
            "source": "Manual Import (Reference: dejure.org)",
        },
    )

    for i, s in enumerate(vob_b_sections):
        chunk_id = f"{law_b_id}_{s['paragraph'].replace(' ', '_').replace('§', 'S')}"
        builder.add_chunk(
            law_b_id,
            chunk_id,
            {
                "text": s["content"],
                "paragraph": s["paragraph"],
                "title": f"VOB/B {s['paragraph']} {s['title']}",
                "section_type": "law_section",
                "type": "chunk",
            },
        )

    builder.create_reference_edges()
    builder.save_graph(output_graph_path)
    logger.info("Manual VOB import complete.")


if __name__ == "__main__":
    import_vob_manual()
