# Next Steps & Roadmap (v1.0.0-rc4)

**Fokus:** Transformation vom Prototypen zum "High-Density Knowledge Graph". Siehe `PRD.md`.

## 📍 Aktueller Status (v1.0.0-rc4)
- [x] **Full Spectrum Graph:** 57+ Dokumente (BMWK, BMFSFJ) integriert.
- [x] **Basis-Intelligenz:** Metadaten-Mapping und Versionierung (`SUPERSEDES`) funktionieren.
- [x] **Visualisierung:** Dashboard (D3.js) live und mit API verbunden.

## 🛠️ Meilensteine & Tasks

### Phase A: Graph Density (Das "Gehirn") - ⭐ PRIORITÄT
*Ziel: Den Graphen "schlau" machen durch Querverweise.*
- [ ] **Citation Parser:** Entwickle ein Modul (`src/parser/citation_extractor.py`), das Verweise wie "BNBest-P" oder "§ 44 BHO" im Text findet.
- [ ] **Reference Linking:** Generiere `REFERENCES` Kanten zwischen Dokument-Knoten basierend auf den Citations.
- [ ] **External Nodes:** Erstelle "Stub-Nodes" für Gesetze (z.B. BHO), die oft zitiert werden, aber (noch) nicht als PDF vorliegen.

### Phase B: Local Stability & Refinement
*Ziel: Robuste lokale Entwicklungsumgebung.*
- [ ] **Config Management:** Zentralisiere Ports und Pfade in `config/settings.yaml`.
- [ ] **Robust Crawler:** Erweitere den Crawler um automatische Retry-Logik und bessere Ministeriums-Erkennung.
- [ ] **Testing:** Baue eine einfache Test-Suite für die wichtigsten Pfade (kein Over-Engineering).

### Phase C: Graph-Guided RAG (Die "Muskeln")
*Ziel: Nutzung der neuen Graph-Struktur für Antworten.*
- [ ] **Multi-Hop Retrieval:** Implementiere Logik in der API, die bei einer Suche auch Nachbarn (via `REFERENCES` oder `SUPERSEDES`) in den Kontext lädt.
- [ ] **Answer Engine Tuning:** Verbessere die Prompts, um Widersprüche zwischen Versionen aufzulösen.

## 🚀 Session-Start Befehl
"Lies `PRD.md` und `NEXTSTEPS.md`. Fokus heute: **Phase A (Graph Density)**. Starte mit der Analyse, wie wir 'BNBest' Referenzen in den Texten finden können."
