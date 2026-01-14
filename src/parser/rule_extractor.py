import json
import os
import requests
import logging
from pathlib import Path
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RuleExtractor:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("IONOS_MISTRAL_API_KEY")
        self.api_url = "https://api.ionos.com/llm/v1/chat/completions"

    def extract_rules(self, text: str) -> List[Dict[str, Any]]:
        if not self.api_key:
            logger.warning("No API Key found. Skipping LLM extraction.")
            return []

        prompt = f"""
        Analysiere den folgenden Text aus einer deutschen Zuwendungsrichtlinie und extrahiere prozessuale Regeln.
        Suche speziell nach:
        1. Vergaberechtlichen Schwellenwerten (z.B. Beträge in Euro, ab denen Angebote eingeholt werden müssen).
        2. Berichtspflichten (Zeitpunkte, Formate für Verwendungsnachweise oder Berichte).
        3. Definitionen von zuwendungsfähigen Ausgaben (Was darf abgerechnet werden?).
        4. Formular-Strukturen (Hinweise auf notwendige Anlagen oder spezifische Felder).

        Gib die Ergebnisse als JSON-Liste von Objekten zurück mit:
        - "category": (Vergabe, Bericht, Ausgaben, Formular)
        - "rule": (Kurze Beschreibung der Regel)
        - "value": (Spezifischer Schwellenwert oder Frist, falls vorhanden)
        
        Text:
        {text}
        """

        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "mistral-large-latest",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                },
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            return json.loads(content).get("rules", [])
        except Exception as e:
            logger.error(f"LLM Extraction failed: {e}")
            return []


def process_graph_rules(graph_path: Path):
    if not graph_path.exists():
        return

    with open(graph_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    extractor = RuleExtractor()
    nodes = data.get("nodes", [])

    chunk_count = 0
    max_chunks = 10

    for node in nodes:
        if node.get("type") == "chunk" and chunk_count < max_chunks:
            text = node.get("text", "")
            if len(text) > 100:
                logger.info(f"Extracting rules from chunk {node['id']}")
                rules = extractor.extract_rules(text)
                if rules:
                    node["rules"] = rules
                chunk_count += 1

    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Updated graph with extracted rules for {chunk_count} chunks.")


if __name__ == "__main__":
    process_graph_rules(Path("data/knowledge_graph.json"))
