# Next Steps & Roadmap (v0.1.0-alpha)

Dieses Dokument dient als dynamischer Status-Bericht und Übergabepunkt für Agenten-Sessions.

## 📍 Aktueller Status (v0.4.0)
- [x] Repository-Initialisierung.
- [x] Full Sync BMWK (69 Dokumente).
- [x] **Extraction Pipeline:** Alle 50 PDFs via Docling verarbeitet und hierarchisch gechunkt.
- [x] **Smart Metadata:** Download-URLs in allen Graph-Knoten verankert.
- [x] **Rule Extraction:** `src/parser/rule_extractor.py` für IONOS/Mistral Integration bereit.
- [x] **Versioning:** Automatische Verknüpfung von ANBest-P Generationen via `SUPERSEDES`-Kanten implementiert.

## 🛠️ Meilensteine & Tasks

### Phase B: Extraction & Processing (Priorität: Hoch)
- [x] **Full Processing:** Pipeline für alle BMWK-PDFs ausgeführt.
- [x] **Requirement Extraction Skeleton:** LLM-Logik implementiert (IONOS/Mistral).
- [x] **Metadata Enrichment:** Download-URLs integriert.

### Phase C: Knowledge Graph & Versioning (Priorität: Medium)
- [x] **Temporal Linking:** `SUPERSEDES`-Kanten erstellt.
- [ ] **D3.js Export:** Erstellung eines Export-Moduls für das Admin-Dashboard (Visualisierung).

### Phase D: Graph-RAG (Priorität: Hoch)
- [ ] **Vector Indexing:** Anbindung von ChromaDB für die semantische Suche über die Graph-Knoten.
- [ ] **Requirement Mining:** Erster Full-Run der Rule-Extraction über alle Chunks.


## 🔄 Versionierung & Kontinuität
- **Versionierung des Crawlers:** Wir folgen Semantic Versioning (aktuell v0.1.0).
- **Dokument-Versionierung:**
    - Jeder Download wird gehasht.
    - Änderungen im Hash lösen eine neue Version im Graphen aus.
    - Die `manifest.json` ist die zentrale "Source of Truth" für den aktuellen Crawl-Stand.

## 🚀 Session-Start Befehl für neue Agenten
"Analysiere `AGENTS.md` und `NEXTSTEPS.md`. Setze Phase A (Full-Portal Scraper) fort."
