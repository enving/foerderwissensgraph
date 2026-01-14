import json
import re
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONTHS = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}


def extract_date(title: str):
    match = re.search(r"([a-zA-Zä]+)\s+(\d{4})", title, re.IGNORECASE)
    if match:
        month_str = match.group(1).lower()
        year = int(match.group(2))
        month = MONTHS.get(month_str, 1)
        return datetime(year, month, 1)
    return None


def apply_versioning(graph_path: Path):
    if not graph_path.exists():
        return

    with open(graph_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data.get("nodes", [])
    edges = [e for e in data.get("links", []) if e.get("relation") != "SUPERSEDES"]

    groups = {"ANBest-P-Kosten": [], "ANBest-P": [], "ANBest-GK": [], "ANBest-I": []}

    for node in nodes:
        if node.get("type") == "document":
            title = node.get("title", "")
            for key in ["ANBest-P-Kosten", "ANBest-P", "ANBest-GK", "ANBest-I"]:
                if key in title:
                    date = extract_date(title)
                    if date:
                        groups[key].append({"id": node["id"], "date": date})
                    break

    new_edges_count = 0
    for key, docs in groups.items():
        docs.sort(key=lambda x: x["date"])

        for i in range(len(docs) - 1):
            older = docs[i]
            newer = docs[i + 1]

            exists = any(
                e
                for e in edges
                if e["source"] == newer["id"]
                and e["target"] == older["id"]
                and e.get("relation") == "SUPERSEDES"
            )

            if not exists:
                edges.append(
                    {
                        "source": newer["id"],
                        "target": older["id"],
                        "relation": "SUPERSEDES",
                    }
                )
                new_edges_count += 1
                logger.info(f"Added: {newer['id']} SUPERSEDES {older['id']}")

    if new_edges_count > 0:
        data["links"] = edges
        with open(graph_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Updated graph with {new_edges_count} SUPERSEDES edges.")
    else:
        logger.info("No new versioning edges to add.")


if __name__ == "__main__":
    apply_versioning(Path("data/knowledge_graph.json"))
