# Next Steps & Roadmap (v1.0.0-rc1)

## 📍 Aktueller Status (v1.0.0-rc1)
- [x] **High Throughput:** 43+ Dokumente verarbeitet, 3400+ Chunks im Graph.
- [x] **Phase D (Context Expansion):** Multi-Hop Retrieval in `hybrid_search.py` implementiert. Suchergebnisse enthalten nun automatisiert Nachbarknoten aus dem Graphen.
- [x] **Rule Mining Finalized:** Schwellenwert auf 80 Zeichen gesenkt und Final Run für restliche Chunks durchgeführt.
- [x] **Frontend Polish:** Dashboard zeigt Regeln nun als strukturierte Karten an. Graph-Kontext ist via Akkordeon-View einsehbar.
- [x] **API Support:** Hybrid Search Engine ist voll integriert und über REST-API abfragbar.

## 🛠️ Meilensteine & Tasks

### Phase B: Extraction & Mining (Abgeschlossen)
- [x] **Final Run:** Alle relevanten Chunks (>80 Zeichen) haben nun extrahierte Regeln.
- [ ] **Manual Audit:** Stichprobenartige Prüfung der v1.0.0 Datenqualität.

### Phase C: Dashboard & UI (Stabil)
- [x] **Rule Cards:** Visualisierung der Compliance-Regeln direkt in den Suchergebnissen.
- [x] **Graph Context:** Visualisierung der Nachbarschafts-Beziehungen bei RAG-Treffern.

### Phase D: Graph-RAG Integration (Stabil)
- [x] **Multi-Hop Retrieval:** Navigation im Graphen zur Kontext-Erweiterung aktiv.
- [ ] **Context Weighting:** Optimierung der Relevanz-Gewichtung zwischen Vektor-Score und Graphen-Distanz.

## 🚀 Session-Start Befehl
"Lies `AGENTS.md`, `optimizing.md` und `NEXTSTEPS.md`. Implementiere die `HybridSearchEngine` (Phase D), um semantische Suche mit Graphen-Kontext zu verknüpfen."
