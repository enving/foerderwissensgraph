# Bund-ZuwendungsGraph 🕸️

**Sovereign Knowledge Source** für den Bundes-Formularschrank (Easy-Online). Transformiert unstrukturierte Förderrichtlinien in einen maschinenlesbaren Knowledge Graph mit Hybrid Search (Vector + Graph-RAG).

## 🚀 Live Demo
**Dashboard:** [https://förderwissensgraph.digitalalchemisten.de](https://förderwissensgraph.digitalalchemisten.de)  
**API-Docs:** [https://förderwissensgraph.digitalalchemisten.de/api/docs](https://förderwissensgraph.digitalalchemisten.de/api/docs)  
**API-Index:** [https://förderwissensgraph.digitalalchemisten.de/api/](https://förderwissensgraph.digitalalchemisten.de/api/)

## ✨ Kernfunktionen
- **Automatisierter Crawl:** Monatliche Erfassung neuer Richtlinien aus Easy-Online.
- **Deep Parsing:** Strukturierte Extraktion von Inhalten mit Docling.
- **Hybrid Search:** Kombination aus BM25 (Keyword) und Vektorsuche (Semantik).
- **Graph-RAG:** Kontextuelle Erweiterung von Suchergebnissen durch Beziehungen (z.B. "Ersetzt durch", "Verweist auf").

## 🛠️ Architektur
- **Frontend:** D3.js visualisiertes Dashboard (Nginx).
- **Backend:** FastAPI (Python 3.11) für Suche und RAG-Logik.
- **Vector DB:** ChromaDB.
- **Deployment:** Docker Compose mit Nginx Reverse Proxy.

## 📦 Deployment & Betrieb

### Voraussetzungen
- Docker & Docker Compose
- API Keys (IONOS Cloud oder Mistral) in `.env`

### Starten
```bash
docker compose up -d --build
```

### Daten-Update (Manuell)
Um neue Dokumente zu crawlen und den Index zu aktualisieren:
```bash
# 1. Neue Dokumente crawlen
docker exec app-backend-1 python src/crawler/easy_online_crawler.py
# 2. Ingest in Vector Store
docker exec app-backend-1 python src/parser/vector_store.py
```

## 📅 Automatisierung
Auf dem Server ist ein monatlicher Update-Zyklus vorgesehen:
1. `easy_online_crawler.py` (Suche nach neuen PDFs)
2. `docling_parser.py` (Extraktion & Graph-Update)
3. `vector_store.py` (Embedding & Index-Update)

---
*Entwickelt als Teil der Forschungsinitiative für transparente Zuwendungsprozesse.*
