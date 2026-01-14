# Next Steps & Roadmap (v0.6.0)

## 📍 Aktueller Status (v0.6.0)
- [x] Full Scale-up (BMWK): 50 PDFs verarbeitet, 3500+ Chunks im Graph.
- [x] **Graph-RAG Infrastructure:** `embedding_engine.py` und `vector_store.py` (ChromaDB) implementiert.
- [x] **Versioning:** 14 `SUPERSEDES`-Kanten fest im Graphen verankert.
- [x] **Visualization:** D3.js Export funktionsfähig.
- [!] **Blocker:** API-Keys (IONOS/Mistral) liefern aktuell 401 Unauthorized.

## 🛠️ Meilensteine & Tasks

### Phase B: Extraction & Mining (Priorität: Hoch)
- [ ] **Rule Extraction Full Run:** Führe `src/parser/rule_extractor.py` für alle relevanten Chunks aus (sobald API-Key valide).
- [ ] **Data Cleaning:** Entferne redundante Chunks oder Header-only Knoten aus der Verarbeitung.

### Phase C: Dashboard & UI (Priorität: Medium)
- [ ] **Dashboard Implementation:** Einfaches HTML/JS Frontend erstellen, um den Graphen interaktiv zu explorieren.

### Phase D: Graph-RAG Integration (Priorität: Kritisch)
- [ ] **Full Vectorization:** Alle 3500+ Chunks in ChromaDB indexieren (sobald API-Key valide).
- [ ] **Hybrid Search:** Implementiere eine Test-Abfrage, die Graph-Beziehungen nutzt, um RAG-Ergebnisse mit Kontext (Breadcrumbs) anzureichern.

## 🚀 Session-Start Befehl
"Lies `AGENTS.md`, `optimizing.md` und `NEXTSTEPS.md`. Validiere die API-Keys und starte die Voll-Vektorisierung der Chunks in ChromaDB (Phase D)."
