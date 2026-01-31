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
    version="2.3.3",
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
logger.info(
    "Initializing Bund-ZuwendungsGraph Engines (v2.3.2 - with Inverse Search)..."
)
logger.info(f"Working directory: {Path.cwd()}")
logger.info(f"Data directory: {Path('data').absolute()}")

# Startup Check for Environment Variables
import os

ionos_key = os.getenv("IONOS_API_KEY")
if ionos_key:
    logger.info(f"IONOS_API_KEY found (Length: {len(ionos_key)})")
else:
    logger.warning(
        "CRITICAL: IONOS_API_KEY not found in environment! LLM features will fail."
    )

engine = HybridSearchEngine(
    graph_path=Path(settings.get("paths.knowledge_graph")),
    db_path=settings.get("paths.chroma_db"),
)
answer_engine = RuleExtractor()
if not answer_engine.provider:
    logger.error("RuleExtractor failed to initialize provider (Check API Keys).")

compliance_mapper = ComplianceMapper(
    graph_path=Path(settings.get("paths.knowledge_graph")),
    vector_store=engine.vector_store,
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
        Path("index.html"),
    ]
    for p in paths:
        if p.exists():
            return FileResponse(p)

    return HTMLResponse(
        content="<h1>Bund-ZuwendungsGraph</h1><p>Dashboard not found.</p>",
        status_code=404,
    )


# Mount Data and Docs for static access
# These will be available at /static/... and /data/...
app.mount("/static", StaticFiles(directory=str(Path("docs").absolute())), name="static")
app.mount("/data", StaticFiles(directory=str(Path("data").absolute())), name="data")


@app.get("/api-info", tags=["System"])
async def api_info():
    """
    Returns API metadata and links.
    """
    return {
        "message": "Bund-ZuwendungsGraph API 🕸️",
        "version": "2.3.3",
        "docs": "/api/docs",
        "redoc": "/api/redoc",
        "health": "/api/health",
        "search": "/api/search",
        "advanced_search": "/api/search/advanced",
        "graph_expansion": "/api/graph/expand-context",
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
    context_doc_id: Optional[str] = Query(
        None,
        description="Scope-Constraint: Suche auf referenzierte Gesetze dieses Dokuments einschränken",
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

    # Resolve scope whitelist if context_doc_id is provided
    scope_whitelist = None
    if context_doc_id:
        scope_whitelist = []

        # Case A: Document is in Knowledge Graph
        if context_doc_id in engine.graph:
            scope_whitelist.append(context_doc_id)
            for _, target_id, edata in engine.graph.out_edges(
                context_doc_id, data=True
            ):
                if edata.get("relation") == "REFERENCES":
                    scope_whitelist.append(target_id)

        # Case B: Document is in Upload Cache (extracted text)
        elif context_doc_id in UPLOAD_CACHE:
            text = UPLOAD_CACHE[context_doc_id]
            # Use ComplianceMapper logic to find citations
            from src.models.schemas import ExpandContextRequest

            req = ExpandContextRequest(
                context_label="scope_extraction", text_chunks=[text[:50000]]
            )
            expansion = compliance_mapper.expand_context(req)
            for reg in expansion.mapped_regulations:
                if reg.doc_id:
                    scope_whitelist.append(reg.doc_id)

        if scope_whitelist:
            # Smart Version Resolution: always use latest
            resolved_whitelist = []
            for d_id in scope_whitelist:
                resolved_whitelist.append(compliance_mapper._find_latest_version(d_id))
            scope_whitelist = list(set(resolved_whitelist))
            logger.info(f"Active Scope Whitelist: {scope_whitelist}")

    # Call search_v2 (Phase 1 implementation)
    results = engine.search_v2(
        query=q,
        limit=limit * 2,  # Get more for filtering
        filter_dict=None,
        scope_whitelist=scope_whitelist,
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


@app.post(
    "/graph/expand-context", response_model=ExpandContextResponse, tags=["Graph Logic"]
)
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
    """Health check endpoint with diagnostics."""
    import os

    # Check Graph
    graph_status = "Not loaded"
    node_count = 0
    if compliance_mapper and compliance_mapper.graph:
        node_count = len(compliance_mapper.graph.nodes)
        graph_status = f"Loaded ({node_count} nodes)"

    # Check LLM
    llm_status = "Not initialized"
    if answer_engine and answer_engine.provider:
        llm_status = f"Initialized ({answer_engine.provider.get_provider_name()})"

    # Check Vector Store
    vector_status = "Unknown"
    try:
        if engine and engine.vector_store and engine.vector_store.collection:
            count = engine.vector_store.collection.count()
            vector_status = f"Connected ({count} embeddings)"
    except Exception as e:
        vector_status = f"Error: {str(e)}"

    # Check Env
    env_vars = {
        "IONOS_API_KEY": "Set" if os.getenv("IONOS_API_KEY") else "Missing",
        "OPENAI_API_KEY": "Set" if os.getenv("OPENAI_API_KEY") else "Missing",
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "Unknown"),
    }

    return {
        "status": "healthy" if node_count > 0 else "degraded",
        "service": "Bund-ZuwendungsGraph",
        "version": "2.3.4-debug",
        "diagnostics": {
            "graph": graph_status,
            "vector_store": vector_status,
            "llm": llm_status,
            "env": env_vars,
            "upload_cache_size": len(UPLOAD_CACHE),
        },
    }


# --- Chat & Upload Features (v2.3) ---

from fastapi import File, UploadFile, Form
from src.models.schemas import (
    ChatRequest,
    ChatMessage,
    ExpandContextRequest,
    ChatResponse,
)
from pydantic import BaseModel
import uuid
import io

# Simple in-memory storage for uploaded docs (Session -> Text)
# In production, use Redis or a proper DB/Vector Store
UPLOAD_CACHE: Dict[str, str] = {}


@app.post("/chat/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Uploads a document (PDF, DOCX, TXT, MD) for ad-hoc RAG chat.
    Returns a session ID (uploaded_doc_id).
    """
    logger.info(f"Received upload: {file.filename} ({file.content_type})")

    # Support more types
    filename = file.filename.lower() if file.filename else "unknown"
    is_pdf = filename.endswith(".pdf") or file.content_type == "application/pdf"
    is_docx = (
        filename.endswith(".docx")
        or file.content_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    is_text = filename.endswith((".txt", ".md")) or file.content_type in [
        "text/plain",
        "text/markdown",
    ]

    if not (is_pdf or is_docx or is_text):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload PDF, DOCX, TXT, or MD.",
        )

    try:
        content = await file.read()
        text = ""

        if is_pdf:
            from pypdf import PdfReader

            pdf = PdfReader(io.BytesIO(content))
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

        elif is_docx:
            import docx

            doc = docx.Document(io.BytesIO(content))
            text = "\n".join([para.text for para in doc.paragraphs])

        elif is_text:
            text = content.decode("utf-8", errors="ignore")

        # Store text in memory with a unique ID
        doc_id = str(uuid.uuid4())
        # Parse basic metadata if possible? For now just text.

        if not text.strip():
            raise HTTPException(
                status_code=400, detail="Document appears to be empty or unreadable."
            )

        UPLOAD_CACHE[doc_id] = text[:150000]  # Increased limit

        logger.info(
            f"Processed document {file.filename} with ID {doc_id} (Length: {len(text)})"
        )

        return {
            "uploaded_doc_id": doc_id,
            "filename": file.filename,
            "status": "processed",
        }

    except Exception as e:
        logger.error(f"Upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


class DocumentAnalysisRequest(BaseModel):
    uploaded_doc_id: str


@app.post("/chat/analyze-document", response_model=ExpandContextResponse, tags=["Chat"])
async def analyze_document(request: DocumentAnalysisRequest):
    """
    Graph-Guided Analysis (Inverse Search).
    Scans the uploaded document for known entities (Laws, Regulations) from the Knowledge Graph.
    Returns a structured list of detected regulations and relevant rules.
    """
    doc_id = request.uploaded_doc_id

    if doc_id not in UPLOAD_CACHE:
        raise HTTPException(
            status_code=404, detail="Document session not found or expired."
        )

    text = UPLOAD_CACHE[doc_id]

    # Simple Chunking
    chunk_size = 3000
    overlap = 500
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + chunk_size])
        start += chunk_size - overlap

    # Call Compliance Mapper
    try:
        expand_req = ExpandContextRequest(
            context_label=f"User Upload {doc_id}",
            text_chunks=chunks,
            metadata={"source": "user_upload"},
        )
        return compliance_mapper.expand_context(expand_req)

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest):
    """
    Conversational endpoint. Combines Graph-RAG with uploaded document context.
    """
    query = request.message
    history = request.history
    doc_id = request.uploaded_doc_id
    context_doc_id = (
        request.context_doc_id or doc_id
    )  # Use uploaded doc as context by default if available

    # Resolve scope whitelist
    scope_whitelist = None
    if context_doc_id:
        scope_whitelist = []
        if context_doc_id in engine.graph:
            scope_whitelist.append(context_doc_id)
            for _, target_id, edata in engine.graph.out_edges(
                context_doc_id, data=True
            ):
                if edata.get("relation") == "REFERENCES":
                    scope_whitelist.append(target_id)
        elif context_doc_id in UPLOAD_CACHE:
            text = UPLOAD_CACHE[context_doc_id]
            from src.models.schemas import ExpandContextRequest

            req = ExpandContextRequest(
                context_label="scope_extraction", text_chunks=[text[:30000]]
            )
            expansion = compliance_mapper.expand_context(req)
            for reg in expansion.mapped_regulations:
                if reg.doc_id:
                    scope_whitelist.append(reg.doc_id)

        if scope_whitelist:
            resolved = [
                compliance_mapper._find_latest_version(d) for d in scope_whitelist
            ]
            scope_whitelist = list(set(resolved))

    # 1. Search in Knowledge Graph (Hybrid)
    graph_results = engine.search_v2(query, limit=3, scope_whitelist=scope_whitelist)

    # 2. Add Uploaded Doc Context if available
    context_chunks = []

    if doc_id and doc_id in UPLOAD_CACHE:
        doc_text = UPLOAD_CACHE[doc_id]
        # Allow much larger context for "Analyze" tasks (approx 8k tokens safe limit for most models)
        # 30,000 chars ~= 7,500 tokens.
        limit = 30000
        preview = doc_text[:limit]
        if len(doc_text) > limit:
            preview += "\n... [Dokument gekürzt für Kontext-Fenster] ..."

        context_chunks.append(f"[UPLOADED_DOCUMENT]\n{preview}\n[/UPLOADED_DOCUMENT]")

    # 3. Add Graph Context
    for r in graph_results:
        context_chunks.append(
            f"Titel: {r.get('doc_title', 'Unbekannt')}\nText: {r.get('text', '')}"
        )
        for neighbor in r.get("neighbor_context", []):
            n_type = neighbor.get("type", "reference").upper()
            context_chunks.append(
                f"[{n_type}] Quelle: {neighbor.get('breadcrumbs', 'Verknüpftes Dokument')}\nText: {neighbor.get('text', '')}"
            )

    # 4. Construct Prompt with History
    # We format history here since the RuleExtractor doesn't natively handle it yet
    history_str = "\n".join(
        [f"{msg.role.upper()}: {msg.content}" for msg in history[-5:]]
    )  # Limit history

    combined_context = "\n\n".join(context_chunks)

    # Use the existing answer engine but bypass generate_answer for custom prompt
    if not answer_engine.provider:
        logger.error("Attempted chat generation without initialized provider.")
        return {
            "answer": "Fehler: Die KI-Engine ist nicht verfügbar (API-Key fehlt oder Konfigurationsfehler). Bitte Administrator kontaktieren.",
            "results": [],
            "used_upload": False,
            "suggested_questions": [],
        }

    system_prompt = f"""
    Du bist der KI-Assistent für den Förderwissensgraph.
    Nutze den folgenden Kontext (Graph-Wissen und evtl. hochgeladene Dokumente), um die Frage zu beantworten.
    
    WICHTIG:
    - Wenn du auf ein Dokument aus dem Kontext verweist, nutze das Format: [Titel](#graph:ID).
    - Beispiel: "Siehe dazu die [NKBF 2017](#graph:0347)."
    - Die IDs (z.B. '0347' oder 'law_BHO') stehen im Kontext. Wenn keine ID da ist, nutze fetten Text.
    
    ZUSATZAUFGABE (WICHTIG):
    Generiere am Ende deiner Antwort ZWINGEND einen Block mit exakt 3 kurzen Folgefragen, die der Nutzer basierend auf deiner Antwort stellen könnte.
    Trenne diesen Block vom Rest der Antwort mit der Zeile: "---SUGGESTIONS---".
    Schreibe jede Frage in eine neue Zeile, beginnend mit einem Bindestrich "- ".
    
    Beispiel-Format:
    Hier ist die Antwort auf deine Frage...
    
    ---SUGGESTIONS---
    - Wie verhält es sich mit Reisekosten?
    - Gilt das auch für KMU?
    - Wo finde ich das Formular?
    
    Verlauf:
    {history_str}
    
    Kontext:
    {combined_context}
    
    Frage: {query}
    
    Antwort (hilfreich, präzise, auf Deutsch, mit Links, plus Suggestions-Block am Ende):
    """

    try:
        # Check token limit roughly (1 char ~= 0.25 tokens is naive, better cut by char length)
        # IONOS/OpenAI Limit is usually large, but let's be safe.
        if len(system_prompt) > 100000:
            logger.warning(
                f"Prompt too long ({len(system_prompt)} chars). Truncating context."
            )
            system_prompt = system_prompt[:100000] + "\n[...Truncated...]"

        # Robust generation with retries
        import time

        response = None
        for attempt in range(3):
            try:
                response = answer_engine.provider.generate(
                    system_prompt, max_tokens=1500
                )
                if response and response.content:
                    break
                logger.warning(
                    f"Empty response from LLM (Attempt {attempt + 1}/3). Retrying..."
                )
                time.sleep(1)
            except Exception as e:
                logger.warning(f"LLM Generation Error (Attempt {attempt + 1}/3): {e}")
                if attempt == 2:
                    raise e
                time.sleep(1)

        if not response or not response.content:
            logger.error("LLM Provider returned empty response after retries.")
            return {
                "answer": "Die KI hat eine leere Antwort zurückgegeben. Bitte versuchen Sie es erneut.",
                "results": graph_results,
                "used_upload": bool(doc_id),
                "suggested_questions": [],
            }

        raw_content = response.content
        answer = raw_content
        suggestions = []

        # Parse suggestions
        if "---SUGGESTIONS---" in raw_content:
            parts = raw_content.split("---SUGGESTIONS---")
            answer = parts[0].strip()
            suggestions_text = parts[1].strip()
            # Parse lines starting with - or 1.
            for line in suggestions_text.split("\n"):
                clean = line.strip()
                if clean.startswith("-") or clean.startswith("*"):
                    suggestions.append(clean[1:].strip())
                elif len(clean) > 0 and clean[0].isdigit() and ". " in clean:
                    suggestions.append(clean.split(". ", 1)[1].strip())

        # Fallback cleanup if LLM fails format but includes separator
        answer = answer.replace("---SUGGESTIONS---", "").strip()

        return {
            "answer": answer,
            "results": graph_results,
            "used_upload": bool(doc_id),
            "suggested_questions": suggestions[:3],
        }

    except Exception as e:
        logger.error(f"Chat generation failed: {e}")
        import traceback

        traceback_str = traceback.format_exc()
        print(traceback_str)  # To Stdout for docker logs

        with open("debug_error.log", "a") as f:
            f.write(f"Chat Error: {str(e)}\n")
            f.write(traceback_str)

        return {
            "answer": f"Es gab einen Fehler bei der Antwortgenerierung. \nTechnisches Detail: {str(e)}\nBitte Logs prüfen.",
            "results": [],
            "used_upload": False,
            "suggested_questions": [],
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.get("api.host", "0.0.0.0"),
        port=settings.get("api.port", 5001),
    )
