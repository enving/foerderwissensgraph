# Next Steps & Roadmap (v0.1.0-alpha)

Dieses Dokument dient als dynamischer Status-Bericht und Übergabepunkt für Agenten-Sessions.

## 📍 Aktueller Status (v0.3.0)
- [x] Repository-Initialisierung.
- [x] Playwright Discovery-Test & Full Sync BMWK (69 Dokumente).
- [x] **Docling Integration:** `src/parser/docling_engine.py` für hierarchisches Markdown-Parsing fertiggestellt.
- [x] **Graph-Architektur:** `src/graph/graph_builder.py` mit NetworkX implementiert.
- [x] **Initialer Graph:** Erste 5 Dokumente via `src/main_pipeline.py` verarbeitet.

## 🛠️ Meilensteine & Tasks

### Phase B: Extraction & Processing (Priorität: Hoch)
- [ ] **Full Processing:** Pipeline für alle 69 BMWK-Dokumente ausführen (Scale-up).
- [ ] **Requirement Extraction:** Implementierung der LLM-Logik (IONOS/Mistral), um aus den MD-Chunks konkrete Regeln zu extrahieren. Fokus: **Vergaberechtliche Schwellenwerte** (z.B. >500€), **Berichtspflichten**, **Einstufungskriterien** und **Formularstrukturen**. 
- [ ] **Metadata Enrichment:** Stand-Datum, Ministerium-Metadaten und **Download-URLs** (Traceability) tiefer in die Knoten integrieren.

### Phase C: Knowledge Graph & Versioning (Priorität: Medium)
- [ ] **Temporal Linking:** Automatische Erstellung von `SUPERSEDES`-Kanten zwischen Dokumentversionen basierend auf Titeln und Daten (wichtig für ANBest-P Historie).
- [ ] **D3.js Export:** Erstellung eines Export-Moduls für das Admin-Dashboard (Visualisierung).

### Phase D: Graph-RAG (Priorität: Hoch)
- [ ] **Vector Indexing:** Anbindung von ChromaDB für die semantische Suche über die Graph-Knoten.


## 🔄 Versionierung & Kontinuität
- **Versionierung des Crawlers:** Wir folgen Semantic Versioning (aktuell v0.1.0).
- **Dokument-Versionierung:**
    - Jeder Download wird gehasht.
    - Änderungen im Hash lösen eine neue Version im Graphen aus.
    - Die `manifest.json` ist die zentrale "Source of Truth" für den aktuellen Crawl-Stand.

## 🚀 Session-Start Befehl für neue Agenten
"Analysiere `AGENTS.md` und `NEXTSTEPS.md`. Setze Phase A (Full-Portal Scraper) fort."
