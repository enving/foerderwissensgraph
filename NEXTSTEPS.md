# Next Steps & Roadmap (v0.9.0)

## 📍 Aktueller Status (v0.9.0)
- [x] **High Throughput:** 43+ Dokumente verarbeitet, 3400+ Chunks im Graph.
- [x] **Phase D (Vectorization):** 2409 Chunks in `data/chroma_db` indexiert.
- [x] **Hybrid Search Engine:** `src/parser/hybrid_search.py` implementiert (ChromaDB + NetworkX).
- [x] **API Support:** Flask-Backend in `src/api/search_api.py` für Hybrid Search.
- [x] **Rule Extraction Upgrade:** Pydantic-Validierung (`src/models/schemas.py`) integriert.
- [x] **UI Enhancement:** Hybrid Search Bar im `docs/dashboard.html` integriert.

## 🛠️ Meilensteine & Tasks

### Phase B: Extraction & Mining (Priorität: Hoch)
- [x] **Pydantic Migration:** Regel-Extraktion nutzt nun strukturierte Schemas.
- [ ] **Full-Run Completion:** Fortsetzen der Extraktion für die restlichen ~1300 Chunks.
- [ ] **Data Cleaning:** Entfernung von Duplikaten oder leeren Regel-Arrays.

### Phase C: Dashboard & UI (Priorität: Medium)
- [x] **Hybrid Search UI:** Suchmaske für semantische Suche + Graphen-Context aktiv.
- [ ] **Rule Filtering:** Filter im Dashboard nach Kategorien (Vergabe, Bericht, etc.).

### Phase D: Graph-RAG Integration (Priorität: Kritisch)
- [x] **Hybrid Search Logic:** Erste Version der Engine verknüpft Vektor-IDs mit Graphen-Breadcrumbs.
- [ ] **Context Expansion:** Implementierung von Multi-Hop-Retrieval (Nachbarknoten in den LLM-Context laden).

## 🚀 Session-Start Befehl
"Lies `AGENTS.md`, `optimizing.md` und `NEXTSTEPS.md`. Implementiere die `HybridSearchEngine` (Phase D), um semantische Suche mit Graphen-Kontext zu verknüpfen."
