import logging
import json
from typing import List, Dict, Any, Optional
from src.llm.base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


class QueryEnhancer:
    """
    QueryEnhancer implements techniques to improve search hit rates:
    - Multi-Query Generation
    - HyDE (Hypothetical Document Embeddings)
    - Query Decomposition
    """

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    def generate_variations(self, query: str, num_variations: int = 2) -> List[str]:
        """
        Generates variations of the user query.
        """
        prompt = f"""Du bist ein Experte für deutsches Vergaberecht und Zuwendungsrecht.
Generiere {num_variations} alternative Formulierungen für die folgende Nutzeranfrage.
Nutze dabei Synonyme, juristische Fachbegriffe und präzisere Formulierungen, die in deutschen Gesetzestexten oder Richtlinien vorkommen könnten.

Nutzeranfrage: "{query}"

Gib die Variationen als einfache Liste zurück, eine pro Zeile. Keine Nummerierung, kein Text davor oder danach.
Variationen:"""

        try:
            logger.info(f"Generating variations for: {query}")
            response = self.llm.generate(prompt, max_tokens=200, temperature=0.7)
            logger.info(f"LLM Response: {response.content}")
            variations = [
                v.strip() for v in response.content.strip().split("\n") if v.strip()
            ]
            return variations[:num_variations]
        except Exception as e:
            logger.error(f"Failed to generate query variations: {e}")
            return []

    def generate_hyde_response(self, query: str) -> str:
        """
        Generates a hypothetical answer (HyDE).
        """
        prompt = f"""Du bist ein Experte für deutsches Vergaberecht und Zuwendungsrecht.
Schreibe eine hypothetische, fachlich fundierte Antwort auf die folgende Frage im Stil eines deutschen Gesetzestextes oder einer offiziellen Förderrichtlinie.
Die Antwort muss nicht faktisch korrekt sein, aber sie sollte die typische Sprache, Struktur und Fachbegriffe enthalten (z.B. Paragraphen, Verweise auf VgV, GWB, BHO).

Frage: "{query}"

Hypothetischer Text:"""

        try:
            logger.info(f"Generating HyDE for: {query}")
            response = self.llm.generate(prompt, max_tokens=400, temperature=0.5)
            logger.info(f"LLM Response: {response.content}")
            return response.content.strip()
        except Exception as e:
            logger.error(f"Failed to generate HyDE response: {e}")
            return ""

    def decompose_query(self, query: str) -> List[str]:
        """
        Decomposes complex, multi-part questions into simple sub-questions.
        """
        prompt = f"""Zerlege die folgende komplexe Anfrage zum deutschen Zuwendungs- oder Vergaberecht in einfache, separate Teilfragen.
Jede Teilfrage sollte eigenständig beantwortbar sein.

Komplexe Anfrage: "{query}"

Gib die Teilfragen als JSON-Liste von Strings zurück.
Beispiel: ["Teilfrage 1", "Teilfrage 2"]
JSON:"""

        try:
            # Try using generate_json if supported, otherwise parse manually
            try:
                sub_queries = self.llm.generate_json(prompt, max_tokens=300)
                if isinstance(sub_queries, list):
                    return sub_queries
                if isinstance(sub_queries, dict) and "sub_queries" in sub_queries:
                    return sub_queries["sub_queries"]
                if isinstance(sub_queries, dict):
                    # Fallback for other dict structures
                    return list(sub_queries.values())[0] if sub_queries else []
            except (AttributeError, NotImplementedError):
                response = self.llm.generate(prompt, max_tokens=300, temperature=0.3)
                content = response.content.strip()
                # Find JSON part
                start = content.find("[")
                end = content.rfind("]") + 1
                if start != -1 and end != 0:
                    return json.loads(content[start:end])
                return [query]  # Fallback to original query

            return [query]
        except Exception as e:
            logger.error(f"Failed to decompose query: {e}")
            return [query]

    def enhance(self, query: str) -> Dict[str, Any]:
        """
        Performs full query enhancement.
        """
        logger.info(f"Enhancing query: {query}")

        variations = self.generate_variations(query)
        hyde_text = self.generate_hyde_response(query)
        sub_queries = (
            self.decompose_query(query) if len(query.split()) > 10 else [query]
        )

        return {
            "original_query": query,
            "variations": variations,
            "hyde_text": hyde_text,
            "sub_queries": sub_queries,
            "all_queries": list(set([query] + variations + sub_queries)),
        }
