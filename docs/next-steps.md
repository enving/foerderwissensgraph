# Next Steps & Roadmap (v1.1.2)

**Fokus:** Transformation vom Prototypen zum "High-Density Knowledge Graph". Siehe `../PRD.md`.

## 📍 Aktueller Status (v1.1.2)
- [x] **Full Spectrum Graph:** 57+ Dokumente (BMWK, BMFSFJ) integriert.
- [x] **Basis-Intelligenz:** Metadaten-Mapping und Versionierung (`SUPERSEDES`) funktionieren.
- [x] **Visualisierung:** Dashboard (D3.js) live und mit API verbunden.
- [x] **Repository Checkpoint:** Dokumentation und Struktur bereinigt.

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

## 🚀 Kommende Ziele (Phase D)
- [ ] **Full E2E Test Suite (TASK-006):** Playwright Abdeckung für alle UI-Elemente und Filter.
- [ ] **Dockerization (TASK-005):** Erstellung von Dockerfiles und docker-compose.
- [ ] **Multi-User:** Authentifizierung und Benutzerverwaltung.

## 🚀 Session-Start Befehl
"Lies `.opencode/tasks.json` und `docs/next-steps.md`. Fokus heute: **Phase D (Deployment & Testing)**. Starte mit TASK-006: E2E Test Suite."
