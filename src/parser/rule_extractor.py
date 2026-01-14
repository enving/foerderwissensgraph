import json
import os
import requests
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RuleExtractor:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (
            api_key or os.getenv("IONOS_API_KEY") or os.getenv("IONOS_MISTRAL_API_KEY")
        )
        self.api_url = (
            os.getenv("IONOS_API_URL")
            or "https://openai.inference.de-txl.ionos.com/v1/chat/completions"
        )
        if "/chat/completions" not in self.api_url:
            self.api_url = self.api_url.rstrip("/") + "/chat/completions"

        self.model = os.getenv("IONOS_MODEL") or "mistral-large-latest"
        self.mistral_api_key = os.getenv("MISTRAL_API_KEY")

    def extract_rules(self, text: str) -> List[Dict[str, Any]]:
        if not self.api_key and not self.mistral_api_key:
            logger.warning("No API Keys found. Skipping LLM extraction.")
            return []

        prompt = f"""
        Analysiere den folgenden Text aus einer deutschen Zuwendungsrichtlinie und extrahiere prozessuale Regeln.
        Suche speziell nach:
        1. Vergaberechtlichen Schwellenwerten (z.B. Beträge in Euro, ab denen Angebote eingeholt werden müssen).
        2. Berichtspflichten (Zeitpunkte, Formate für Verwendungsnachweise oder Berichte).
        3. Definitionen von zuwendungsfähigen Ausgaben (Was darf abgerechnet werden?).
        4. Formular-Strukturen (Hinweise auf notwendige Anlagen oder spezifische Felder).

        Gib die Ergebnisse als JSON-Liste von Objekten zurück mit dem Key "rules". Jedes Objekt in der Liste muss folgende Felder haben:
        - "category": (Vergabe, Bericht, Ausgaben, Formular)
        - "rule": (Kurze Beschreibung der Regel)
        - "value": (Spezifischer Schwellenwert oder Frist, falls vorhanden)
        
        Text:
        {text}
        """

        # Try IONOS first
        if self.api_key:
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                }

                logger.info(f"Sending request to IONOS API ({self.model})...")
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=60,
                )

                if response.status_code == 401:
                    logger.error(
                        "IONOS API Key Unauthorized (401). Check permissions for the model hub."
                    )
                else:
                    response.raise_for_status()
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    data = json.loads(content)
                    if isinstance(data, list):
                        return data
                    return data.get("rules", [])
            except Exception as e:
                logger.error(f"IONOS Extraction failed: {e}")

        # Try Mistral fallback
        if self.mistral_api_key:
            try:
                from mistralai import Mistral

                logger.info("Using Mistral fallback...")
                client = Mistral(api_key=self.mistral_api_key)
                response = client.chat.complete(
                    model="mistral-large-latest",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content
                if content:
                    data = json.loads(content)
                    if isinstance(data, list):
                        return data
                    return data.get("rules", [])
            except Exception as e:
                logger.error(f"Mistral Fallback Extraction failed: {e}")

        return []


def process_graph_rules(graph_path: Path):
    if not graph_path.exists():
        logger.error(f"Graph file not found: {graph_path}")
        return

    with open(graph_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    extractor = RuleExtractor()
    nodes = data.get("nodes", [])

    chunk_count = 0
    save_interval = 20

    logger.info(f"Starting rule extraction for all chunks in {graph_path}")

    for i, node in enumerate(nodes):
        if node.get("type") == "chunk":
            # Skip if already processed (marked as list, even if empty)
            if "rules" in node and isinstance(node["rules"], list):
                continue

            text = node.get("text", "")
            if len(text) > 150:
                logger.info(
                    f"[{i}/{len(nodes)}] Extracting rules from chunk {node['id']}"
                )
                rules = extractor.extract_rules(text)
                node["rules"] = rules  # Will be empty list if extraction failed
                chunk_count += 1

                # Periodic save
                if chunk_count > 0 and chunk_count % save_interval == 0:
                    with open(graph_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    logger.info(f"Intermediate save: {chunk_count} chunks processed.")

    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(
        f"Full run complete. Updated graph with extracted rules for {chunk_count} additional chunks."
    )


if __name__ == "__main__":
    process_graph_rules(Path("data/knowledge_graph.json"))
