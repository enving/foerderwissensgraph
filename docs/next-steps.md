# Next Steps & Roadmap (v1.0.0-rc4)

**Fokus:** Transformation vom Prototypen zum "High-Density Knowledge Graph". Siehe `../PRD.md`.

## 📍 Aktueller Status (v1.0.0-rc4)
- [x] **Full Spectrum Graph:** 57+ Dokumente (BMWK, BMFSFJ) integriert.
- [x] **Basis-Intelligenz:** Metadaten-Mapping und Versionierung (`SUPERSEDES`) funktionieren.
- [x] **Visualisierung:** Dashboard (D3.js) live und mit API verbunden.

## 🛠️ Meilensteine & Tasks

### Phase A: Graph Density (Das "Gehirn") - ✅ ERLEDIGT
*Ziel: Den Graphen "schlau" machen durch Querverweise.*
- [x] **Citation Parser:** Entwickle ein Modul (`src/parser/citation_extractor.py`), das Verweise wie "BNBest-P" oder "§ 44 BHO" im Text findet.
- [x] **Reference Linking:** Generiere `REFERENCES` Kanten zwischen Dokument-Knoten basierend auf den Citations.
- [x] **External Nodes:** Erstelle "Stub-Nodes" für Gesetze (z.B. BHO), die oft zitiert werden, aber (noch) nicht als PDF vorliegen.

### Phase B: Local Stability & Refinement - ⭐ PRIORITÄT
*Ziel: Robuste lokale Entwicklungsumgebung.*
- [ ] **BUGFIX UI Filter:** Der Typ-Filter (z.B. "Merkblatt") ist inaktiv/ohne Funktion. Nur der Ministeriums-Filter funktioniert aktuell.
- [ ] **Config Management:** Zentralisiere Ports und Pfade in `config/settings.yaml`.
- [ ] **Robust Crawler:** Erweitere den Crawler um automatische Retry-Logik und bessere Ministeriums-Erkennung.
- [ ] **Testing:** Baue eine einfache Test-Suite für die wichtigsten Pfade (kein Over-Engineering).

### Phase C: Graph-Guided RAG (Die "Muskeln")
*Ziel: Nutzung der neuen Graph-Struktur für Antworten.*
- [ ] **Multi-Hop Retrieval:** Implementiere Logik in der API, die bei einer Suche auch Nachbarn (via `REFERENCES` oder `SUPERSEDES`) in den Kontext lädt.
- [ ] **Answer Engine Tuning:** Verbessere die Prompts, um Widersprüche zwischen Versionen aufzulösen.

## 🚀 Session-Start Befehl
"Lies `.opencode/tasks.json` und `docs/next-steps.md`. Fokus heute: **Phase B (Local Stability)**. Starte mit dem Fix für den UI-Filter."
