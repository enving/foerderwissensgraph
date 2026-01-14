# Next Steps & Roadmap (v1.0.0-rc2)

## 📍 Aktueller Status (v1.0.0-rc2)
- [x] **Full Spectrum Graph:** 50+ Dokumente, 3500+ Chunks, 990+ extrahierte Regeln.
- [x] **Metadata Power:** Ministerium, Herausgeber, Stand (Datum) und Kürzel extrahiert und im Graph verankert.
- [x] **Hybrid Search Engine:** Semantische Suche + Graphen-Breadcrumbs + Context Expansion aktiv.
- [x] **Dashboard UI:** Professionelle Visualisierung mit Regel-Karten und Metadaten-Anzeige.
- [x] **Deployment Guide:** `DEPLOYMENT.md` erstellt.

## 🛠️ Meilensteine & Tasks

### Phase B: Extraction & Mining (Validation)
- [ ] **Data Audit:** Stichprobenartige Prüfung der extrahierten "Stand"-Daten und Regeln auf Richtigkeit.
- [ ] **Cross-Ministry Mapping:** Identifikation von identischen Regelwerken über Ministeriumsgrenzen hinweg (`EQUIVALENT_TO`).

### Phase C: Dashboard & UI (Final Polish)
- [ ] **Filter UI:** Möglichkeit, die Suche auf spezifische Ministerien oder Zeiträume (Stand) einzugrenzen.
- [ ] **Export Feature:** Möglichkeit, Suchergebnisse (inkl. Regeln und Kontext) als PDF/JSON zu exportieren.

### Phase D: Graph-RAG Integration (Optimization)
- [ ] **Context Weighting:** Feinjustierung der 70/30 Gewichtung zwischen Vektor-Score und Graph-Centrality.
- [ ] **LLM Answer Engine:** Integration eines Moduls, das auf Basis der Hybrid-Search Ergebnisse eine finale Antwort formuliert (RAG-Completion).

## 🚀 Session-Start Befehl
"Lies `AGENTS.md`, `optimizing.md` und `NEXTSTEPS.md`. Starte das System mit `src/api/search_api.py` und führe einen Audit der extrahierten Metadaten durch."
