# KI-Agenten und Skills: Förderwissensgraph

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

### Session 2026-01-24 (Antigravity - VPS Deployment & SSL Fixes)
- **Status:** Production Deployment & Automation Complete.
- **Erledigt:**
    - **Deployment Fixes (TASK-015):**
        - Nginx Konfiguration korrigiert (Domain punycode, http2 Deprecation, Docker Resolver).
        - SSL Zertifikat-Mapping in Docker-Compose repariert.
        - Dashboard Static-File Serving via Nginx-Proxy gefixt.
        - VectorStore Bug behoben (Verbindung zum Chroma-Container via Hostname).
    - **Automatisierung:**
        - `setup_cron.sh` für monatliche Updates (Crawl + Embedding) implementiert.
        - `quick_deploy.sh` für automatisierten Transfer und Neustart via SSH/User graph erstellt.
    - **API:** Version auf 2.2.x (RRF + Reranking aktiv).
- **Nächster Schritt:** Monitoring und Initialisierung einer größeren Datenmenge (Full Crawl).

### Session 2026-01-18 (Antigravity - UX Polish & Testing)
- **Status:** UX Overhaul & Robust Testing.
- **Erledigt:**
    - **UX Features (TASK-013):**
        - Auto-Focus bei Suche und Filter.
        - Dynamische Filter-Optionen.
        - Kategorie-Filter (Formularschrank/Gesetze).
        - Visuelle Verbesserungen (Gesetze orange).
    - **Bugfixes:** Filter-Reset bei Tooltip-Hide behoben.
    - **Infrastructure:** Skill `webapp-testing` repariert.
- **Nächster Schritt:** Docker Optimization.

### Session 2026-01-18 (Antigravity - Checkpoint)
- **Status:** Repository Checkpoint & Phase E Completion.
- **Erledigt:**
    - Repository-Reinigung.
    - Update von `.opencode/tasks.json` (Phase E Completed).
    - Update `next-steps.md` (Version v2.2.2, Phase E ✅).
    - Update `PRD.md` (Version v2.2.2).
- **Nächster Schritt:** Fokus auf TASK-009: Resource & Performance Profiling.

### Session 2026-01-18 (Antigravity - Crawler Implementation)
- **Status:** Full Easy-Online Crawler implemented (v2.2.2).
- **Erledigt:**
    - `EasyCrawler` implementiert in `src/discovery/easy_crawler.py`.
    - Recursion, Rate Limiting, und Global Crawl Modus hinzugefügt.
    - `MinistryRegistry` mit fehlenden Ministerien (BISP, BLE, BAFA, etc.) aktualisiert.
    - Erfolgreicher Testlauf mit BMWK (404-Handling verifiziert).
- **Nächster Schritt:** Fokus auf TASK-009: Resource & Performance Profiling.

### Session 2026-01-18 (Antigravity - Checkpoint)
- **Status:** Repository Checkpoint.
- **Erledigt:**
    - Repository-Reinigung.
    - Dokumentation und Tasks synchronisiert.
    - Vorbereitung für nächsten Agenten (Crawler-Implementierung).
- **Nächster Schritt:** Fokus auf TASK-007: Full Crawler Implementation.

### Session 2026-01-15 (Tristan Häfele - Checkpoint)
- **Status:** Repository aufgeräumt & dokumentiert (Checkpoint).
- **Erledigt:**
    - `__pycache__`, `.pyc` und temporäre Dateien entfernt.
    - `.opencode/tasks.json` initialisiert und Meta-Daten aktualisiert.
    - `docs/next-steps.md` synchronisiert und Prioritäten geschärft (Fokus Phase C).
    - `PRD.md` Implementierungs-Status aktualisiert.
    - Git-Checkpoint mit standardisierter Commit-Message erstellt.
- **Nächster Schritt:** Implementierung des Multi-Hop Retrieval (Phase C).

### Session 2026-01-17 (Antigravity - Checkpoint & Cleanup)
- **Status:** Repository Checkpoint abgeschlossen.
- **Erledigt:**
    - Repository-Reinigung (Caches, __pycache__).
    - Update von `.opencode/tasks.json` (Meta-Daten & TASK-004 auf abgeschlossen gesetzt).
    - Synchronisation aller Dokumentationsdateien (`next-steps.md`, `agents.md`).
    - Git-Commit für Checkpoint erstellt.
- **Nächster Schritt:** Fokus auf TASK-003: Multi-Hop Retrieval in `src/parser/hybrid_search.py`.

### Session 2026-01-17 (opencode - Checkpoint & Documentation)
- **Status:** Repository Checkpoint & Task Management Migration.
- **Erledigt:**
    - `.opencode/tasks.json` mit tatsächlichen Projekt-Tasks initialisiert.
    - `PRD.md` Implementierungs-Status für Phase C auf abgeschlossen gesetzt.
    - `docs/next-steps.md` mit neuen Prioritäten (Phase D) synchronisiert.
    - Repository-Reinigung (Caches, __pycache__).
- **Nächster Schritt:** Fokus auf TASK-006: Full E2E Test Suite für Dashboard und API.

### Session 2026-01-17 (opencode - Checkpoint & Documentation)
- **Status:** Repository Checkpoint & Documentation Sync.
- **Erledigt:**
    - Repository-Reinigung (Caches, __pycache__, venv).
    - Update von `.opencode/tasks.json` (Meta-Daten auf v1.3.0 aktualisiert).
    - Synchronisation von `PRD.md` und `next-steps.md` (Phase D als erledigt markiert).
    - Git-Commit für Checkpoint erstellt.
- **Nächster Schritt:** Fokus auf Phase E (Advanced Features & Security).

### Session 2026-01-17 (opencode - Checkpoint & Cleanup)
- **Status:** Repository Checkpoint abgeschlossen.
- **Erledigt:**
    - Repository-Reinigung (Caches, __pycache__).
    - Update von `.opencode/tasks.json` (Meta-Daten aktualisiert).
    - Synchronisation aller Dokumentationsdateien (`next-steps.md`, `agents.md`).
    - Git-Commit für Checkpoint erstellt.
- **Nächster Schritt:** Fokus auf TASK-003: Multi-Hop Retrieval in `src/parser/hybrid_search.py`.

### Session 2026-01-16 (Antigravity - Checkpoint & Cleanup)
- **Status:** Repository Checkpoint abgeschlossen.
- **Erledigt:**
    - Repository-Reinigung (Caches, __pycache__).
    - Update von `.opencode/tasks.json` (Meta-Daten & TASK-004 auf abgeschlossen gesetzt).
    - Synchronisation aller Dokumentationsdateien (`next-steps.md`, `agents.md`).
    - Git-Commit für Checkpoint erstellt.
- **Nächster Schritt:** Fokus auf TASK-003: Multi-Hop Retrieval in `src/parser/hybrid_search.py`.

### Session 2026-01-15 (Antigravity - Checkpoint & Cleanup)
- **Status:** Repository Checkpoint abgeschlossen.
- **Erledigt:**
    - Erneute Repository-Reinigung (Caches).
    - Update von `.opencode/tasks.json` (Meta-Daten & TASK-004).
    - Synchronisation aller Dokumentationsdateien.
    - Git-Commit für Checkpoint erstellt.
- **Nächster Schritt:** Fokus auf TASK-003: Multi-Hop Retrieval in `src/parser/hybrid_search.py`.
