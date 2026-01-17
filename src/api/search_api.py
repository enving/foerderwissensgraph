from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import List, Optional, Dict, Any
from src.parser.hybrid_search import HybridSearchEngine
from src.parser.rule_extractor import RuleExtractor
from src.config_loader import settings
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Bund-ZuwendungsGraph API",
    description="API für Hybrid Search und Graph-RAG über Förderrichtlinien.",
    version="1.2.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Engines
engine = HybridSearchEngine(
    graph_path=Path(settings.get("paths.knowledge_graph")),
    db_path=settings.get("paths.chroma_db"),
)
answer_engine = RuleExtractor()


@app.get("/api/search")
async def search(
    q: str = Query(..., description="Die Suchanfrage"),
    limit: int = Query(5, description="Maximale Anzahl der Ergebnisse"),
    ministerium: Optional[str] = Query(None, description="Filter nach Ministerium"),
    kuerzel: Optional[str] = Query(None, description="Filter nach Kürzel"),
    stand_after: Optional[str] = Query(
        None, description="Filter nach Datum (Stand nach)"
    ),
):
    """
    Führt eine hybride Suche (Vektor + Graph) durch und generiert optional eine KI-Antwort.
    """
    if not q:
        return []

    results = engine.search(q, limit=limit)

    # Apply filters to results
    filtered_results = []
    for res in results:
        match = True
        if (
            ministerium
            and res.get("ministerium") != ministerium
            and res.get("herausgeber") != ministerium
        ):
            match = False
        if kuerzel and kuerzel not in res.get("kuerzel", ""):
            match = False
        if stand_after and res.get("stand"):
            res_stand = res.get("stand")
            if res_stand and res_stand < stand_after:
                match = False

        if match:
            filtered_results.append(res)

    # Generate RAG Answer if results found and query is complex enough
    if filtered_results and len(q.split()) > 2:
        top_results = filtered_results[:3]
        context_chunks = []
        for r in top_results:
            # Primary Chunk
            context_chunks.append(
                f"Titel: {r.get('doc_title', 'Unbekannt')}\nText: {r.get('text', '')}"
            )
            # Graph-based Neighbor Context (Multi-Hop)
            for neighbor in r.get("neighbor_context", []):
                n_type = neighbor.get("type", "reference").upper()
                context_chunks.append(
                    f"[{n_type}] Quelle: {neighbor.get('breadcrumbs', 'Verknüpftes Dokument')}\nText: {neighbor.get('text', '')}"
                )

        try:
            answer = answer_engine.generate_answer(q, context_chunks)
            if answer:
                return {"answer": answer, "results": filtered_results}
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")

    return filtered_results


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Bund-ZuwendungsGraph"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.get("api.host", "0.0.0.0"),
        port=settings.get("api.port", 5001),
    )
