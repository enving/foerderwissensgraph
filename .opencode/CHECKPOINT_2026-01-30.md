# Checkpoint: Semantic Search & Context Guard Release
**Datum:** 2026-01-30 10:25 Uhr
**Version:** v2.3.6

---

## ✅ Abgeschlossene Aufgaben

### 1. Semantic Search wiederhergestellt (LiteVectorStore)
- **Problem:** `chromadb` war inkompatibel mit Python 3.14 (Pydantic v1 Konflikt).
- **Lösung:** Implementierung eines eigenen, robusten JSON-basierten Vektorspeichers (`src/parser/vector_store.py`).
- **Funktionen:**
  - Persistente Speicherung (`data/chroma_db/lite_store.json`).
  - Cosine-Similarity Suche via `numpy`.
  - Unterstützung für Metadaten-Filterung (wichtig für Context Guard).
  - Performance: <100ms für 4000 Chunks.

### 2. Context Guard & Scope Constraint (Compliance)
- **Problem:** Chatbot nutzte BMBF-Regeln für BMVI-Projekte ("Halluzinationen").
- **Lösung:** Implementierung einer harten Filter-Logik (`Scope Constraint`).
- **Ablauf:**
  1. `CitationExtractor` findet "herrschende Gesetze" im Dokument (z.B. "gemäß § 44 BHO").
  2. `HybridSearchEngine` erhält eine Whitelist von erlaubten Dokumenten.
  3. `LiteVectorStore` filtert Ergebnisse strikt auf diese Whitelist.
- **Ergebnis:** mFUND-Fragen werden nur noch mit mFUND/BMVI/BHO-Wissen beantwortet.

### 3. Hybrid Law Crawler (HTML Fallback)
- **Problem:** VOB und BHO XML-Downloads waren defekt oder fehlten.
- **Lösung:** Erweiterung des `LawCrawler` um einen HTML-Parser für `gesetze-im-internet.de`.
- **Status:**
  - BHO: Erfolgreich via HTML geparst (125 Paragraphen).
  - VgV: Via XML importiert.
  - VOB: Weiterhin schwer zugänglich (404), aber Infrastruktur ist bereit.

### 4. UVgO Integration
- **Import:** 167 Paragraphen der Unterschwellenvergabeordnung (UVgO) importiert.
- **Quelle:** PDF-Parsing via `pypdf`.

---

## 🌐 Live-Status

| Komponente | Status | Details |
|-----|----------|--------|
| **API** | ✅ Online | Port 5001, Python 3.14 |
| **Vector Store** | ✅ Aktiv | LiteVectorStore (87 MB, 3.888 Chunks) |
| **LLM** | ✅ Verbunden | IONOS (GPT-120B) via OpenAI-Interface |
| **Search** | ✅ Hybrid | BM25 + Vector + Reranking + Context Guard |

---

## 📁 Wichtige Dateien (geändert/erstellt)

```
src/
├── parser/vector_store.py     # NEU: LiteVectorStore Implementation
├── discovery/law_crawler.py   # UPDATE: Hybrid XML/HTML Crawler
├── api/search_api.py          # UPDATE: Integration Context Guard
├── llm/openai_provider.py     # FIX: Reasoning Model Patch

scripts/
├── debug_ionos_chat.py        # Test-Skript für LLM
├── sync_vectors_only.py       # Helper für Vector-Sync

docs/
├── verarbeitungskonzept.md    # NEU: Architektur & Datenschutz-Doku
```

---

## 📋 Offene Punkte / Next Steps

1.  **VOB Beschaffung:** Manuelles Einpflegen der VOB-Texte oder Suche nach alternativer Quelle (`dejure.org`), da `gesetze-im-internet` 404 liefert.
2.  **Deployment:** Code auf VPS pullen und `python src/api/search_api.py` neustarten (oder Docker Container rebuilden).
3.  **On-Demand Trigger:** Crawler automatisch starten, wenn unbekanntes Gesetz gefunden wird.

---

## 📊 Stats

-   **Knowledge Graph:** ~12.000 Nodes
-   **Vector Index:** 3.888 Chunks (qualitativ hochwertig)
-   **Response Time:** ~1.2s (Search), ~4s (LLM Answer)
