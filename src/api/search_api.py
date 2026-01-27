from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import List, Optional, Dict, Any
from src.parser.hybrid_search import HybridSearchEngine
from src.parser.rule_extractor import RuleExtractor
from src.graph.compliance_mapper import ComplianceMapper
from src.models.schemas import ExpandContextRequest, ExpandContextResponse
from src.config_loader import settings
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Bund-ZuwendungsGraph API 🕸️",
    description="""
**Sovereign Knowledge Source** für den Bundes-Formularschrank.

Diese API ermöglicht den programmatischen Zugriff auf den Knowledge Graph der deutschen Förderrichtlinien. 
Sie kombiniert semantische Vektorsuche mit Graph-RAG (Beziehungen zwischen Dokumenten) und bietet 
automatisierte Regel-Extraktion via LLM.

### Kernfunktionen:
- **Hybrid Search**: BM25 + Vector Embeddings (IONOS/Mistral).
- **Graph Traversal**: Auflösung von Dokumenten-Beziehungen (REFERENCES, SUPERSEDES).
- **Deep Parsing**: Strukturierte Extraktion aus PDFs via Docling.
- **RAG Answer Engine**: Kontextbezogene Antworten basierend auf offiziellen Richtlinien.

*Entwickelt als Teil der Forschungsinitiative für transparente Zuwendungsprozesse.*
""",
    version="2.2.2",
    root_path="/api",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "DigitalAlchemisten Team",
        "url": "https://digitalalchemisten.de",
    },
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
compliance_mapper = ComplianceMapper(
    graph_path=Path(settings.get("paths.knowledge_graph"))
)


# Serve UI (Dashboard) at the very root of the domain
@app.get("/", include_in_schema=False)
async def serve_ui():
    """
    Serves the dashboard.html at the root of the application.
    """
    # Try multiple common paths (local dev vs docker)
    paths = [
        Path("docs/dashboard.html"),
        Path("/app/docs/dashboard.html"),
        Path("index.html")
    ]
    for p in paths:
        if p.exists():
            return FileResponse(p)
    
    return HTMLResponse(content="<h1>Bund-ZuwendungsGraph</h1><p>Dashboard not found.</p>", status_code=404)


# Mount Data and Docs for static access
# These will be available at /static/... and /data/...
app.mount("/static", StaticFiles(directory="docs"), name="static")
app.mount("/data", StaticFiles(directory="data"), name="data")


@app.get("/api-info", tags=["System"])
async def api_info():
    """
    Returns API metadata and links.
    """
    return {
        "message": "Bund-ZuwendungsGraph API 🕸️",
        "version": "2.2.7",
        "docs": "/api/docs",
        "redoc": "/api/redoc",
        "health": "/api/health",
        "search": "/api/search",
        "advanced_search": "/api/search/advanced",
    }
    """
    API Root with links to documentation.
    """
    return {
        "message": "Bund-ZuwendungsGraph API 🕸️",
        "version": "2.2.2",
        "docs": "/api/docs",
        "redoc": "/api/redoc",
        "health": "/api/health",
        "search": "/api/search",
        "advanced_search": "/api/search/advanced",
    }


@app.get("/health", include_in_schema=False)
async def health_check():
    """
    Health-Check Endpoint
    """
    return {"status": "healthy", "service": "Bund-ZuwendungsGraph"}


@app.get("/search")
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


@app.get("/search/advanced")
async def search_advanced(
    q: str = Query(..., description="Die Suchanfrage"),
    limit: int = Query(5, description="Maximale Anzahl der Ergebnisse"),
    ministerium: Optional[str] = Query(None, description="Filter nach Ministerium"),
    kuerzel: Optional[str] = Query(None, description="Filter nach Kürzel"),
    stand_after: Optional[str] = Query(
        None, description="Filter nach Datum (Stand nach)"
    ),
    use_bm25: bool = Query(True, description="BM25 Sparse Retrieval aktivieren"),
    use_reranking: bool = Query(True, description="Cross-Encoder Reranking aktivieren"),
    use_query_enhancement: bool = Query(
        False, description="LLM-basierte Query-Optimierung (HyDE) aktivieren (langsam!)"
    ),
    multi_hop: bool = Query(True, description="Multi-Hop Graph Traversal aktivieren"),
    generate_answer: bool = Query(True, description="KI-Antwort generieren"),
):
    """
    PHASE 1 GRAPH RAG: Advanced Hybrid Search with BM25 + RRF + Reranking.

    Pipeline:
    1. Multi-Retrieval: BM25 (sparse) + Vector (dense)
    2. RRF Fusion: Reciprocal Rank Fusion
    3. Cross-Encoder Reranking: Semantic reranking for German legal text
    4. Graph Expansion: Multi-hop context (REFERENCES, SUPERSEDES)
    5. Answer Generation: LLM-based answer with provenance

    Returns:
        {
            "answer": str (if generate_answer=true),
            "results": List[Dict],
            "metadata": {
                "retrieval_strategy": "bm25+vector+reranking",
                "num_results": int,
                "features_enabled": {...}
            }
        }
    """
    if not q:
        return {"error": "Query cannot be empty"}

    # Call search_v2 (Phase 1 implementation)
    results = engine.search_v2(
        query=q,
        limit=limit * 2,  # Get more for filtering
        filter_dict=None,
        multi_hop=multi_hop,
        use_bm25=use_bm25,
        use_reranking=use_reranking,
        use_query_enhancement=use_query_enhancement,
        retrieval_candidates=20,
        rerank_top_k=10,
    )

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

    # Limit final results
    filtered_results = filtered_results[:limit]

    # Metadata
    metadata = {
        "retrieval_strategy": f"{'bm25+' if use_bm25 else ''}vector{'+ reranking' if use_reranking else ''}",
        "num_results": len(filtered_results),
        "features_enabled": {
            "bm25": use_bm25,
            "reranking": use_reranking,
            "query_enhancement": use_query_enhancement,
            "multi_hop": multi_hop,
            "answer_generation": generate_answer,
        },
        "api_version": "2.0.0",
        "phase": "1",
    }

    # Generate RAG Answer if requested
    if generate_answer and filtered_results and len(q.split()) > 2:
        top_results = filtered_results[:3]
        context_chunks = []
        for r in top_results:
            # Primary Chunk with scores
            context_chunks.append(
                f"[Score: {r.get('score', 0):.3f}] Titel: {r.get('doc_title', 'Unbekannt')}\nText: {r.get('text', '')}"
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
                return {
                    "answer": answer,
                    "results": filtered_results,
                    "metadata": metadata,
                }
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            metadata["answer_generation_error"] = str(e)

    return {"results": filtered_results, "metadata": metadata}


@app.post("/graph/expand-context", response_model=ExpandContextResponse, tags=["Graph Logic"])
async def expand_context_endpoint(request: ExpandContextRequest):
    """
    **Context-Aware Compliance Mapping**
    
    Analysiert übergebene Text-Chunks (z.B. aus einer neuen Förderrichtlinie) und expandiert 
    diese gegen den Knowledge Graph.
    
    Prozess:
    1. **Citation Matching**: Findet harte Referenzen (z.B. "NKBF 98").
    2. **Concept Expansion**: Findet implizite Regeln für erkannte Konzepte (z.B. "Reisekosten" -> "BRKG").
    
    Returns:
        Ein strukturiertes Regel-Paket (`mapped_regulations`), das für den Prüfagenten optimiert ist.
    """
    try:
        return compliance_mapper.expand_context(request)
    except Exception as e:
        logger.error(f"Error in expand_context: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/health-raw")
async def health_raw():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Bund-ZuwendungsGraph"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.get("api.host", "0.0.0.0"),
        port=settings.get("api.port", 5001),
    )
