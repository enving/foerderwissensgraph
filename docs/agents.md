# KI-Agenten und Skills: Bund-ZuwendungsGraph

Dieser Guide definiert die Rollen und Erwartungen für KI-Agenten, die an diesem Repository arbeiten.

## 🤖 Agenten-Rollen

### 1. Discovery-Agent (Scraper)
- **Fokus:** Navigation durch `easy-Online` Portale.
- **Skills:** Playwright-Automatisierung, DOM-Analyse von Legacy-Systemen, Fehlerbehandlung bei instabilen Bundes-Servern.
- **Tools:** Playwright (Chromium), BeautifulSoup.

### 2. Parser-Agent (Extraction)
- **Fokus:** Umwandlung von PDFs in Wissen.
- **Skills:** Docling-Konfiguration, hierarchisches Chunking, Metadaten-Extraktion (Stand-Datum, Ministerium).
- **Tools:** Docling, PyMuPDF (fitz).

### 3. Graph-Architekt
- **Fokus:** Strukturierung des Wissens.
- **Skills:** NetworkX (MultiDiGraph), Temporal Graph Logic, Versionierung (Hashing).
- **Tools:** NetworkX, Pydantic (Node-Schemas).

## 🛠️ Zentrale Skills & Patterns

- **Hashing-First:** Bevor ein Dokument verarbeitet wird, muss ein SHA-256 Hash berechnet werden. Identische Hashes werden nicht erneut geparst.
- **Hierarchisches Chunking:** Markdown muss in logische Sektionen (H1-H3) unterteilt werden, wobei der Header-Stack als Kontext erhalten bleibt.
- **Souveränität:** Alle Daten müssen lokal verarbeitbar sein (Docling). Cloud-LLMs (Mistral/IONOS) werden nur für die semantische Extraktion und Embeddings genutzt.

## 📜 Kontext-Transfer für neue Sessions
Bevor du eine neue Aufgabe startest, lies:
1. `.opencode/tasks.json` (Strukturierte Tasks & Features)
2. `../README.md` (Vision & Setup)
3. `next-steps.md` (Aktueller Fortschritt & Versionierung)
4. `src/discovery/test_discovery.py` (Beispiel für Portal-Zugriff)


## 🕒 Session Historie

### Session 2026-01-15 (opencode)
- **Status:** Checkpoint & Aufräumen.
- **Erledigt:**
    - Repository aufgeräumt (Logs, Cache, __pycache__ entfernt).
    - Strukturierte Task-Verfolgung in `.opencode/tasks.json` aktualisiert (TASK-004 hinzugefügt).
    - Dokumentation verifiziert und in `docs/` konsolidiert.
    - `../PRD.md` und `next-steps.md` auf Übereinstimmung mit `tasks.json` geprüft.
- **Nächster Schritt:** Fehlerbehebung im UI-Filter (Phase B, TASK-003).
