import json
import re
from pathlib import Path
from datetime import datetime

# Mapping internal cabinet codes to full names
MINISTRY_MAP = {
    "bmwe": "BMWK",
    "bmwk": "BMWK",
    "bmbf": "BMBF",
    "bmf": "BMF",
    "bmel": "BMEL",
    "bmuv": "BMUV",
}

MONTHS = {
    "januar": "01",
    "februar": "02",
    "märz": "03",
    "april": "04",
    "mai": "05",
    "juni": "06",
    "juli": "07",
    "august": "08",
    "september": "09",
    "oktober": "10",
    "november": "11",
    "dezember": "12",
}


def refine_metadata():
    graph_path = Path("data/knowledge_graph.json")
    if not graph_path.exists():
        print("Graph not found.")
        return

    with open(graph_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("Refining metadata for document nodes...")

    doc_count = 0
    for node in data.get("nodes", []):
        if node.get("type") == "document":
            title = node.get("title", "")

            # 1. Base Ministry (from cabinet)
            cab_min = node.get("ministerium", "unbekannt").lower()
            node["ministerium"] = MINISTRY_MAP.get(cab_min, cab_min.upper())

            # 2. Specific Issuer (from title)
            issuer = node["ministerium"]  # Default to cabinet
            if "BMBF" in title:
                issuer = "BMBF"
            elif "BMWK" in title or "BMWE" in title:
                issuer = "BMWK"
            elif "BMF" in title:
                issuer = "BMF"
            node["herausgeber"] = issuer

            # 3. Extraction of "Stand" (Date)
            # Pattern: (Month Year) or (Month; Year) or (DD.MM.YY)
            stand = None

            # Try "Month Year" or "(Month Year)"
            date_match = re.search(r"([a-zA-Zä]+)\s+(\d{4})", title, re.IGNORECASE)
            if date_match:
                m = date_match.group(1).lower()
                y = date_match.group(2)
                if m in MONTHS:
                    stand = f"{y}-{MONTHS[m]}"

            # Try "(August 2018)" or "August 2018"
            if not stand:
                month_year_paren = re.search(
                    r"\((?:Stand[:\s]+)?([a-zA-Zä]+)\s+(\d{4})\)", title, re.IGNORECASE
                )
                if month_year_paren:
                    m = month_year_paren.group(1).lower()
                    y = month_year_paren.group(2)
                    if m in MONTHS:
                        stand = f"{y}-{MONTHS[m]}"

            # Try "98" style (common in old BMBF docs)
            if not stand:
                short_year = re.search(r"\b(\d{2})\b(?!\s+\d{2})", title)
                if short_year and int(short_year.group(1)) > 80:
                    stand = f"19{short_year.group(1)}"

            # Try "01.10.88"
            if not stand:
                dot_date = re.search(r"(\d{2})\.(\d{2})\.(\d{2})", title)
                if dot_date:
                    stand = f"19{dot_date.group(3)}-{dot_date.group(2)}"

            node["stand"] = stand

            # 4. Extraction of "Kürzel" (Abbreviation)
            # Pattern: AZA, AZK, ANBest-P, etc.
            kuerzel_match = re.search(r"\b([A-Z][A-Za-z-]{2,15}(?:-[A-Z])?)\b", title)
            if kuerzel_match:
                # Filter out generic words
                k = kuerzel_match.group(1)
                if k not in [
                    "Richtlinien",
                    "Anlage",
                    "Anlagen",
                    "Hinweise",
                    "Besondere",
                    "Allgemeine",
                ]:
                    node["kuerzel"] = k

            # Manual override for some common ones if regex misses
            if "ANBest-P" in title:
                node["kuerzel"] = "ANBest-P"
            if "ANBest-GK" in title:
                node["kuerzel"] = "ANBest-GK"
            if "ANBest-I" in title:
                node["kuerzel"] = "ANBest-I"
            if "AZA" in title:
                node["kuerzel"] = "AZA"
            if "AZK" in title:
                node["kuerzel"] = "AZK"

            doc_count += 1

    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Metadata refinement complete. Updated {doc_count} documents.")


if __name__ == "__main__":
    refine_metadata()
