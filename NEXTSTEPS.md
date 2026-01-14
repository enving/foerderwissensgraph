# Next Steps & Roadmap (v0.5.0)

## 📍 Aktueller Status (v0.5.0)
- [x] Full Scale-up (BMWK): 50 PDFs verarbeitet, 3500+ Chunks im Graph.
- [x] **Versioning Fix:** `SUPERSEDES`-Kanten (ANBest-P Historie) sind nun fest im Graphen gespeichert.
- [x] **Environment:** `.env` Datei mit IONOS-Zugang hinterlegt.
- [x] **Rule Extraction Skeleton:** Bereit für den ersten Full-Run.
- [x] **D3.js Export:** Erste Visualisierungsgrundlage geschaffen.

## 🛠️ Meilensteine & Tasks

### Phase B: Extraction & Processing (Priorität: Hoch)
- [ ] **Rule Extraction Full Run:** Führe `src/parser/rule_extractor.py` für alle relevanten Chunks aus. Nutze primär IONOS (siehe `optimizing.md`).
- [ ] **Metadata Enrichment:** Stand-Datum (JJJJ-MM) als sortierbares Feld in die Knoten extrahieren.

### Phase C: Knowledge Graph & Dashboard (Priorität: Medium)
- [ ] **D3.js Dashboard:** Erstelle ein einfaches HTML-Frontend (`docs/dashboard.html`), das die `data/d3_graph_documents.json` visualisiert.
- [ ] **Complex Relationships:** Identifiziere Verweise zwischen Dokumenten (z.B. Merkblatt A verweist auf Richtlinie B) via Regex/LLM.

### Phase D: Graph-RAG Integration (Priorität: Kritisch)
- [ ] **IONOS Embeddings:** Implementiere `src/parser/embedding_engine.py`, um Chunks via IONOS Embedding API zu vektorisieren.
- [ ] **ChromaDB Setup:** Initialisierung einer lokalen Vektor-DB mit Verknüpfung zur `node_id` des Graphen.
- [ ] **Context-Aware Retrieval:** Erste Test-Abfrage: "Gib mir alle Regeln zur Vergabe > 500€ inkl. übergeordneter Sektions-Überschriften."

## 🚀 Session-Start Befehl
"Lies `AGENTS.md`, `optimizing.md` und `NEXTSTEPS.md`. Starte mit dem Full-Run der Rule Extraction und der Implementierung der IONOS Embeddings (Phase D)."
