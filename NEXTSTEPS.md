# Next Steps & Roadmap (v1.0.0-rc2)

## 📍 Aktueller Status (v1.0.0-rc2)
- [x] **Full Spectrum Graph:** 50+ Dokumente, 3500+ Chunks, 990+ extrahierte Regeln.
- [x] **Metadata Power:** Ministerium, Herausgeber, Stand (Datum) und Kürzel extrahiert und im Graph verankert.
- [x] **Hybrid Search Engine:** Semantische Suche + Graphen-Breadcrumbs + Context Expansion aktiv.
- [x] **Dashboard UI:** Professionelle Visualisierung mit Regel-Karten, Metadaten-Anzeige und Filter-Sidebar.
- [x] **Cross-Ministry Prep:** Equivalence Mapper (`EQUIVALENT_TO`) bereit.

## 🛠️ Meilensteine & Tasks

### Phase A: Expansion (Priorität: Hoch)
- [ ] **Multi-Cabinet Sync:** Crawle die Formularschränke von **BMBF** und **BMF** via `src/discovery/easy_crawler.py`.
- [ ] **Cross-Graph Mining:** Führe die Pipeline für die neuen Ministerien aus und nutze den `EquivalenceMapper`, um identische ANBest-P Versionen zu verlinken.

### Phase B: Extraction & Mining (Finalizing)
- [ ] **Rule Quality Audit:** Manuelle Prüfung der extrahierten Regeln (Vergabeschwellen) für BMBF vs. BMWK.
- [ ] **Data Cleaning:** Entferne veraltete Test-Chunks ohne Graphen-Bezug.

### Phase C: Dashboard & UI (Release Candidate)
- [ ] **Visual Audit:** UI-Test mit Playwright durchführen, um die Filter-Sidebar bei wachsender Ministeriums-Anzahl zu prüfen.
- [ ] **PDF Preview:** (Optional) Integration einer PDF-Vorschau direkt im Dashboard bei Klick auf ein Suchergebnis.

### Phase D: Graph-RAG Integration (Production)
- [ ] **Power Answer Engine:** Verbinde das Answer-Engine Backend (`search_api.py`) mit der IONOS API für echte RAG-Synthese.

## 🚀 Session-Start Befehl
"Lies `AGENTS.md`, `optimizing.md` und `NEXTSTEPS.md`. Starte Phase A: Crawle den BMBF-Formularschrank und integriere ihn in den existierenden Graphen."
