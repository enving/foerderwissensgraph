# Bund-ZuwendungsGraph

**Vision:** Ein 'Sovereign Knowledge Source' Werkzeug, das den Bundes-Formularschrank (Easy-Online) via Playwright & Docling in einen maschinenlesbaren, versionierten Knowledge Graph (NetworkX) + Vector Store (RAG) überführt.

## Status: Initialer Aufbau
Dieses Repository wurde aus dem FAPS-Projekt (Förderantrags-Prüfungssystem) ausgegliedert, um eine eigenständige, offene Datenquelle für Bundes-Zuwendungsrichtlinien zu schaffen.

## Kernfunktionen
- **Discovery:** Automatischer Crawl des Easy-Online Formularschranks.
- **Extraction:** Hierarchisches Parsing von PDF-Richtlinien mit Docling.
- **Knowledge Graph:** Vernetzung von Programmen, Richtlinien und Regeln.
- **Graph-RAG:** Verbindung von strukturellem Wissen mit semantischer Suche.

## Anforderungen
- Python 3.10+
- Playwright (mit Chromium)
- Docling
- NetworkX

## Erste Schritte
```bash
pip install -r requirements.txt
playwright install chromium
python src/discovery/test_discovery.py
```
