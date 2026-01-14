# Next Steps & Roadmap (v0.6.1)

## 📍 Aktueller Status (v0.6.1)
- [x] Full Scale-up (BMWK): 50 PDFs verarbeitet, 3500+ Chunks im Graph.
- [x] **Graph-RAG Infrastructure:** `embedding_engine.py` und `vector_store.py` (ChromaDB) bereit.
- [x] **Versioning:** 14 `SUPERSEDES`-Kanten verankert.
- [x] **Visualization:** D3.js Export vorhanden.
- [!] **Blocker:** IONOS/Mistral API-Keys liefern aktuell 401 Unauthorized (siehe `optimizing.md`).

## 🛠️ Meilensteine & Tasks

### Phase B: Extraction & Mining (Priorität: Hoch)
- [ ] **API Validation:** Debugge den IONOS 401 Fehler (Prüfe Header/Token-Ablauf).
- [ ] **Rule Extraction Full Run:** Führe `src/parser/rule_extractor.py` für alle relevanten Chunks aus.

### Phase C: Dashboard & UI (Priorität: Medium)
- [ ] **Dashboard Implementation:** Einfaches HTML/JS Frontend erstellen (Browser-Visualisierung).

### Phase D: Graph-RAG Integration (Priorität: Kritisch)
- [ ] **Full Vectorization:** Alle 3500+ Chunks in ChromaDB indexieren.
- [ ] **Hybrid Search:** Implementiere eine Test-Abfrage: "Suche nach Reisekosten-Regeln und reichere Ergebnisse mit übergeordneten Graphen-Metadaten an."

## 🚀 Session-Start Befehl
"Lies `AGENTS.md`, `optimizing.md` und `NEXTSTEPS.md`. Löse den 401-Blocker und starte die Vektorisierung in ChromaDB (Phase D)."
