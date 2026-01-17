import json
import os
import requests
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from src.models.schemas import RequirementRuleResult, RequirementRule

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

    def generate_answer(self, query: str, context: List[str]) -> str:
        """
        Generates an answer based on the query and provided context chunks.
        """
        if not self.api_key and not self.mistral_api_key:
            return "Answer generation unavailable (No API Key)."

        context_str = "\n\n".join(context)
        prompt = f"""
        Du bist ein Experte für deutsche Zuwendungsrichtlinien. Beantworte die folgende Frage basierend auf den bereitgestellten Kontext-Informationen.
        Der Kontext enthält primäre Textabschnitte sowie verknüpfte Informationen aus dem Knowledge Graph (Markiert mit [REFERENCE] oder [WARNING]).

        WICHTIG:
        - Wenn ein [WARNING] vorliegt, das besagt, dass ein Dokument ersetzt wurde, erwähne dies unbedingt zuerst.
        - Integriere Informationen aus [REFERENCE] Quellen, um die Antwort zu vervollständigen (Multi-Hop RAG).
        - Nenne die Quellen (Titel der Richtlinie oder Paragraph), wenn sie im Kontext angegeben sind.

        Frage: {query}
        
        Kontext:
        {context_str}
        
        Antwort (präzise, auf Deutsch, unter Berücksichtigung von Querverweisen):
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
                    "max_tokens": 500,
                }

                logger.info(f"Generating answer via IONOS ({self.model})...")
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=30,
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    if content:
                        return str(content)
                    else:
                        logger.warning("IONOS returned empty content.")
                else:
                    logger.warning(
                        f"IONOS Answer gen failed: {response.status_code} {response.text}"
                    )
            except Exception as e:
                logger.error(f"IONOS Answer gen error: {e}")

        # Try Mistral fallback
        if self.mistral_api_key:
            try:
                from mistralai import Mistral

                client = Mistral(api_key=self.mistral_api_key)
                response = client.chat.complete(
                    model="mistral-large-latest",
                    messages=[{"role": "user", "content": prompt}],
                )
                content = response.choices[0].message.content
                return str(content) if content else ""  # type: ignore
            except Exception as e:
                logger.error(f"Mistral Answer gen error: {e}")

        return "Antwort konnte nicht generiert werden (Dienst nicht verfügbar)."

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
                    validated = RequirementRuleResult.model_validate_json(content)
                    return [rule.model_dump() for rule in validated.rules]
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
                if content and isinstance(content, str):
                    validated = RequirementRuleResult.model_validate_json(content)  # type: ignore
                    return [rule.model_dump() for rule in validated.rules]
                return []
            except Exception as e:
                logger.error(f"Mistral Fallback Extraction failed: {e}")

        return []


from concurrent.futures import ThreadPoolExecutor, as_completed


def process_graph_rules(graph_path: Path):
    if not graph_path.exists():
        logger.error(f"Graph file not found: {graph_path}")
        return

    with open(graph_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    extractor = RuleExtractor()
    nodes = data.get("nodes", [])

    chunks_to_process = []
    for i, node in enumerate(nodes):
        if node.get("type") == "chunk":
            if "rules" in node and isinstance(node["rules"], list):
                continue
            text = node.get("text", "")
            if len(text) > 80:
                chunks_to_process.append(node)

    if not chunks_to_process:
        logger.info("No new chunks to process.")
        return

    logger.info(
        f"Starting rule extraction for {len(chunks_to_process)} chunks in {graph_path}"
    )

    save_interval = 20
    chunk_count = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_node = {
            executor.submit(extractor.extract_rules, node.get("text", "")): node
            for node in chunks_to_process
        }

        for future in as_completed(future_to_node):
            node = future_to_node[future]
            try:
                rules = future.result()
                node["rules"] = rules
                chunk_count += 1

                if chunk_count % save_interval == 0:
                    with open(graph_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    logger.info(f"Intermediate save: {chunk_count} chunks processed.")
            except Exception as e:
                logger.error(f"Rule extraction for chunk {node['id']} failed: {e}")

    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(
        f"Full run complete. Updated graph with extracted rules for {chunk_count} additional chunks."
    )


if __name__ == "__main__":
    process_graph_rules(Path("data/knowledge_graph.json"))
