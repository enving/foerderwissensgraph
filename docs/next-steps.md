# Next Steps & Roadmap (v2.2.2)

**Fokus:** Transformation vom Prototypen zum "High-Density Knowledge Graph" & Cloud Readiness. Siehe `../PRD.md`.

## 📍 Aktueller Status (v2.2.2)
- [x] **Full Spectrum Graph:** 57+ Dokumente (BMWK, BMFSFJ) integriert.
- [x] **Basis-Intelligenz:** Metadaten-Mapping und Versionierung (`SUPERSEDES`) funktionieren.
- [x] **Visualisierung:** Dashboard (D3.js) live und mit API verbunden.
- [x] **Data Completeness:** Full Crawler & Embedding Sync implementiert (Phase E complete).

## 🛠️ Meilensteine & Tasks

### Phase A: Graph Density (Das "Gehirn") - ✅ ERLEDIGT
*Ziel: Den Graphen "schlau" machen durch Querverweise.*
- [x] **Citation Parser:** Entwickle ein Modul (`src/parser/citation_extractor.py`), das Verweise wie "BNBest-P" oder "§ 44 BHO" im Text findet.
- [x] **Reference Linking:** Generiere `REFERENCES` Kanten zwischen Dokument-Knoten basierend auf den Citations.
- [x] **External Nodes:** Erstelle "Stub-Nodes" für Gesetze (z.B. BHO), die oft zitiert werden, aber (noch) nicht als PDF vorliegen.

### Phase B: Local Stability & Refinement - ✅ ERLEDIGT
*Ziel: Robuste lokale Entwicklungsumgebung.*
- [x] **BUGFIX UI Filter:** Der Typ-Filter (z.B. "Merkblatt") ist inaktiv. (ERLEDIGT)
- [x] **Config Management:** Zentralisiere Ports/Pfade in `config/settings.yaml`. (ERLEDIGT)
- [x] **Law Integration:** Erster Import von Bundesgesetzen (BHO, VwVfG) erfolgreich. (ERLEDIGT)
- [x] **Robust Crawler:** Erweitere Crawler um Retry-Logik und Ministeriums-Erkennung. (ERLEDIGT)
- [x] **E2E Testing:** Erweiterung der Playwright-Tests für alle Filter-Kombinationen. (ERLEDIGT)

### Phase C: Graph-Guided RAG (Die "Muskeln") - ✅ ERLEDIGT
*Ziel: Nutzung der neuen Graph-Struktur für Antworten.*
- [x] **Multi-Hop Retrieval:** Implementiere Logik in der API, die bei einer Suche auch Nachbarn (via `REFERENCES` oder `SUPERSEDES`) in den Kontext lädt. (ERLEDIGT)
- [x] **Answer Engine Tuning:** Verbessere die Prompts, um Widersprüche zwischen Versionen aufzulösen. (ERLEDIGT)
- [x] **Cross-Document QA:** Ermögliche Fragen, die Informationen aus mehreren verknüpften Dokumenten kombinieren. (ERLEDIGT)
- [x] **API Documentation:** Migration zu FastAPI für automatische Swagger-Docs (/docs). (ERLEDIGT)

### Phase D: Advanced Graph RAG & Testing - ✅ ERLEDIGT
*Ziel: Erhöhung der Retrieval-Genauigkeit und Test-Abdeckung.*
- [x] **Unit Testing (TASK-013):** Vollständige Unit Tests für BM25Index, Reranker und LLM Provider. (ERLEDIGT)
- [x] **Query Enhancement (TASK-012):** Implementierung von Multi-Query, HyDE und Query Decomposition. (ERLEDIGT)
- [x] **API Documentation (TASK-015):** Detaillierte Dokumentation von `/api/search/advanced` in `docs/API.md`. (ERLEDIGT)

### Phase E: Data Completeness & Hosting - ✅ ERLEDIGT
- [x] **Full Crawler (TASK-007):** Vollständige Implementierung des Easy-Online Crawlers für den gesamten Dokumentenbestand. (ERLEDIGT)
- [x] **Embedding Sync (TASK-008):** Integration der Vektorisierung in die Haupt-Pipeline (Remote API + lokale Speicherung). (ERLEDIGT)

### Phase F: Resource Optimization & Cloud Scaling - ⏳ IN ARBEIT
- [x] **Resource Profiling (TASK-009):** Optimierung für 4 GB RAM VPS Hosting. (Peak Memory ~800MB, HyDE Bottleneck identified)
- [x] **UX Polish (TASK-013):** Auto-Focus, Dynamische Filter, Kategorie-Filter ("Formularschrank").
- [ ] **Docker Optimization:** Multi-stage builds verfeinern.

## 🚀 Kommende Ziele (Phase G)
- [ ] **Multi-User:** Authentifizierung und Benutzerverwaltung.
- [ ] **Advanced Graph Analytics:** Berechnung von Centrality Scores für Förderprogramme.


## 🚀 Session-Start Befehl
"Lies `.opencode/tasks.json` und `docs/next-steps.md`. Fokus heute: **Phase F (Resource Optimization)**. Starte mit TASK-009: Resource & Performance Profiling."
