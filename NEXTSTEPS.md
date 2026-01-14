# Next Steps & Roadmap (v0.8.0)

## 📍 Aktueller Status (v0.8.0)
- [x] **High Throughput:** 43+ Dokumente verarbeitet, 3400+ Chunks im Graph.
- [x] **Phase D (Vectorization):** 2409 Chunks in `data/chroma_db` indexiert.
- [x] **Parallel Rule Extraction:** Multithreaded Extractor aktiv.
- [x] **Interactive Dashboard:** `docs/dashboard.html` visualisiert den Dokumenten-Graph.
- [x] **API Access:** IONOS/Mistral Keys funktionieren nun stabil.

## 🛠️ Meilensteine & Tasks

### Phase B: Extraction & Mining (Priorität: Hoch)
- [ ] **Completion:** Führe den `rule_extractor.py` Full Run zu Ende (Ziel: Alle relevanten Chunks mit Regeln).
- [ ] **Validation:** Stichprobenartige Prüfung der extrahierten Regeln (Vergabe-Schwellenwerte).

### Phase C: Dashboard & UI (Priorität: Medium)
- [ ] **Search UI:** Integration einer Suchleiste im Dashboard.
- [ ] **Rule View:** Anzeige der extrahierten Regeln direkt am Dokumenten-Knoten im Dashboard.

### Phase D: Graph-RAG Integration (Priorität: Kritisch)
- [ ] **Hybrid Search Engine:** Implementiere `src/parser/hybrid_search.py`.
- [ ] **Context Stitching:** Logik, um bei einem RAG-Treffer automatisch die "Breadcrumbs" (Kapitelüberschriften) und das "Source PDF" (URL) mitzuliefern.

## 🚀 Session-Start Befehl
"Lies `AGENTS.md`, `optimizing.md` und `NEXTSTEPS.md`. Implementiere die `HybridSearchEngine` (Phase D), um semantische Suche mit Graphen-Kontext zu verknüpfen."
