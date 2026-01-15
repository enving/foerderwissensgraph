# Bund-ZuwendungsGraph

**Vision:** Ein 'Sovereign Knowledge Source' Werkzeug, das den Bundes-Formularschrank (Easy-Online) in einen maschinenlesbaren, versionierten Knowledge Graph überführt.

👉 **[Siehe PRD.md für die detaillierte Produktvision und Roadmap.](PRD.md)**

## Status: v1.0.0-rc4 (Stable Prototype)
Dieses Repository baut einen Graphen aus Förderrichtlinien (BMWK, BMFSFJ, etc.), der nicht nur Text speichert, sondern **Beziehungen** (z.B. "Ersetzt Vorversion", "Gehört zu Programm X").

## Kernfunktionen
- **Discovery:** Automatischer Crawl des Easy-Online Formularschranks.
- **Extraction:** Hierarchisches Parsing von PDF-Richtlinien mit Docling.
- **Knowledge Graph:** Vernetzung von Programmen, Richtlinien und Regeln.
- **Graph-RAG:** Verbindung von strukturellem Wissen mit semantischer Suche.

## Architektur
- **Frontend:** D3.js Dashboard zur Visualisierung (Port 8000)
- **Backend:** Flask API für Hybrid Search (Port 5001)
- **Data:** ChromaDB (Vector Store) + NetworkX (Graph Logic)

## Quickstart

```bash
# 1. Installieren
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# 2. Server starten (API + Frontend)
# (Aktuell noch manuell, siehe docs/next-steps.md für Docker-Pläne)
python src/api/search_api.py &
python -m http.server 8000 --directory docs
```
