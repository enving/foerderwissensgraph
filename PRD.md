# Product Requirements Document (PRD): Bund-ZuwendungsGraph

**Version:** 1.1 (Draft)
**Status:** Active Development
**Vision:** Der fortschrittlichste, souveräne Knowledge Graph für den deutschen Förderdschungel. Wir verwandeln "totes PDF-Wissen" in einen lebendigen, abfragbaren Graphen für Sachbearbeiter und Antragsteller.

## 1. Problemstellung
- **Fragmentierung:** Förderrichtlinien sind über hunderte PDFs und Portale verstreut.
- **Referenz-Chaos:** Dokumente verweisen aufeinander ("siehe BNBest-P"), aber diese Links sind nicht klickbar oder maschinenlesbar.
- **Kontext-Verlust:** Eine Vektorsuche findet Text, versteht aber nicht, ob eine Richtlinie veraltet ist oder hierarchisch einer anderen untergeordnet ist.

## 2. Kernsäulen (Product Pillars)

### A. The Brain: Graph Density (Referenz-Erkennung)
*Das System muss Zusammenhänge verstehen, die nicht explizit im Dateinamen stehen.*
- **Ziel:** Jeder Verweis im Text (z.B. "gemäß § 44 BHO", "siehe Nummer 5.1 ANBest-P") wird eine harte Kante im Graphen (`REFERENCES`).
- **Feature:** Automatischer Citation-Parser (Regex/NER), der Text-Referenzen in Graph-Edges umwandelt.

### B. The Muscle: Graph-Guided RAG
*Das System nutzt die Struktur des Graphen für bessere Antworten.*
- **Ziel:** RAG, das nicht nur ähnliche Chunks sucht, sondern dem Graphen folgt.
- **Feature:** "Multi-Hop Retrieval". Wenn Nutzer nach "Reisekosten" fragen, prüft das System:
    1. Die aktuelle Richtlinie.
    2. Das referenzierte Bundesreisekostengesetz (via `REFERENCES` Kante).
    3. Die übergeordnete Rahmenrichtlinie (via `PART_OF` Kante).

### C. The Skeleton: Developer Experience (DX)
*Das System muss lokal einfach zu entwickeln sein.*
- **Ziel:** Einfacher Start für Entwickler ohne komplexe Container-Magie.
- **Feature:** Standardisierte `requirements.txt`, klare `python` Start-Skripte, strukturierte Configs.

## 3. User Stories
1. **Als Fördermittelberater** möchte ich wissen, welche Version der BNBest für ein Programm aus 2021 gilt, ohne manuell Versionsnummern zu vergleichen.
2. **Als Entwickler** möchte ich das System schnell lokal starten und Änderungen sofort sehen.
3. **Als Analyst** möchte ich sehen, welche Richtlinien am häufigsten referenziert werden (Zentralitäts-Analyse).

## 4. Tech Stack & Architektur
- **Core:** Python 3.10+, NetworkX (Graph Logik).
- **Ingestion:** Playwright (Crawl), Docling (PDF Parsing).
- **Storage:**
  - Graph: JSON (File-based).
  - Vector: ChromaDB (Local).
- **Frontend:** D3.js (Visualisierung), TailwindCSS.
- **API:** Flask/FastAPI.

## 5. Success Metrics
- **Node Density:** Verhältnis von Kanten zu Knoten (Ziel: > 1.5, aktuell ~0.4).
- **Query Accuracy:** Korrekte Beantwortung von "Gilt X noch?" Fragen (Test via Golden Dataset).
- **Setup Time:** < 5 Minuten für neue Devs (via venv).

## 6. Implementierungs-Status
- [x] **Graph Density (The Brain):** Citation-Parser und Reference-Linking implementiert. (v1.1.0)
- [x] **Local Stability:** Zentrales Config-Management und UI-Filter Fixes abgeschlossen.
- [ ] **Graph-Guided RAG:** Multi-Hop Retrieval in Arbeit (Phase C).
