import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.graph.graph_builder import GraphBuilder

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def import_agvo_manual():
    """
    Manually imports key articles of the EU General Block Exemption Regulation (AGVO)
    (Commission Regulation (EU) No 651/2014).
    """
    output_graph_path = Path("data/knowledge_graph.json")
    builder = GraphBuilder()

    if output_graph_path.exists():
        builder.load_graph(output_graph_path)

    agvo_articles = [
        {
            "paragraph": "Art. 1",
            "title": "Anwendungsbereich",
            "content": "Diese Verordnung gilt für folgende Gruppen von Beihilfen: Regionalbeihilfen, Beihilfen für KMU, Beihilfen für Umweltschutz, Beihilfen für Forschung und Entwicklung und Innovation...",
        },
        {
            "paragraph": "Art. 2",
            "title": "Begriffsbestimmungen",
            "content": "(1) 'Beihilfe': jede Maßnahme, die alle Voraussetzungen des Artikels 107 Absatz 1 AEUV erfüllt. (2) 'KMU': Unternehmen, die die Kriterien des Anhangs I erfüllen. (18) 'Unternehmen in Schwierigkeiten': ein Unternehmen, auf das mindestens einer der folgenden Umstände zutrifft...",
        },
        {
            "paragraph": "Art. 3",
            "title": "Voraussetzungen für die Freistellung",
            "content": "Beihilferegelungen, Einzelbeihilfen auf der Grundlage einer Beihilferegelung und Ad-hoc-Beihilfen sind im Sinne des Artikels 107 Absatz 3 AEUV mit dem Binnenmarkt vereinbar und von der Anmeldepflicht nach Artikel 108 Absatz 3 AEUV freigestellt, sofern sie alle Voraussetzungen des Kapitels I dieser Verordnung sowie die für die betreffende Gruppe von Beihilfen geltenden besonderen Voraussetzungen des Kapitels III erfüllen.",
        },
        {
            "paragraph": "Art. 4",
            "title": "Anmeldeschwellen",
            "content": "Diese Verordnung gilt nicht für Beihilfen, die die folgenden Anmeldeschwellen überschreiten: (c) für Forschungs- und Entwicklungsbeihilfen: wenn die Beihilfe für ein Vorhaben, das überwiegend die Grundlagenforschung betrifft, mehr als 40 Mio. EUR pro Unternehmen und Vorhaben beträgt...",
        },
        {
            "paragraph": "Art. 6",
            "title": "Anreizeffekt",
            "content": "(1) Diese Verordnung gilt nur für Beihilfen, die einen Anreizeffekt haben. (2) Beihilfen gelten als Beihilfen mit Anreizeffekt, wenn der Beihilfeempfänger vor Beginn der Arbeiten für das Vorhaben oder die Tätigkeit einen schriftlichen Beihilfeantrag in dem betreffenden Mitgliedstaat gestellt hat.",
        },
    ]

    law_id = "law_AGVO"
    builder.add_law(
        law_id,
        {
            "title": "Allgemeine Gruppenfreistellungsverordnung (AGVO) - Verordnung (EU) Nr. 651/2014",
            "kuerzel": "AGVO",
            "category": "EU-Verordnung",
            "source": "Manual Import (EUR-Lex)",
        },
    )

    for i, s in enumerate(agvo_articles):
        # Clean ID
        p_clean = s["paragraph"].replace(" ", "_").replace(".", "")
        chunk_id = f"{law_id}_{p_clean}"

        builder.add_chunk(
            law_id,
            chunk_id,
            {
                "text": s["content"],
                "paragraph": s["paragraph"],
                "title": f"AGVO {s['paragraph']} {s['title']}",
                "section_type": "law_section",
                "type": "chunk",
            },
        )

    # Also add AEUV Art 107/108 as stubs/references
    builder.add_law(
        "law_AEUV",
        {
            "title": "Vertrag über die Arbeitsweise der Europäischen Union (AEUV)",
            "kuerzel": "AEUV",
            "category": "EU-Vertrag",
            "source": "Reference",
        },
    )

    builder.create_reference_edges()
    builder.save_graph(output_graph_path)
    logger.info("Manual AGVO import complete.")


if __name__ == "__main__":
    import_agvo_manual()
