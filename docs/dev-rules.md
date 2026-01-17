# Development Rules & Workflow

Dieser Guide ist für alle Agenten VERPFLICHTEND. Er sichert die Qualität und Konsistenz des Projekts.

## 🛠️ Arbeitsprinzipien

1. **Test-First (UI):** 
   - Jede visuelle Änderung oder API-Erweiterung MUSS mit dem `webapp-testing` Skill (Playwright) verifiziert werden.
   - **Pflicht-Screenshot:** Erstelle nach UI-Änderungen IMMER Screenshots (Vorher/Nachher) und lege sie in `docs/screenshots/` ab.
   - **Server-Check:** Wenn du die UI testest, stelle sicher, dass der lokale Server (Python/API) läuft (Port 5001/8000). Wenn Playwright fehlschlägt, ist das ein *critical failure* – ignoriere es nicht!

2. **Commit-Disziplin:**
   - Erstelle nach JEDEM abgeschlossenen Meilenstein (Task) einen aussagekräftigen Git-Commit.
   - Nutze `git status`, um sicherzustellen, dass keine neuen Module als "untracked" liegen bleiben.

3. **Data Quality & Task Management:**
   - Vertraue nicht blind auf "große Zahlen" im Graph. Prüfe stichprobenartig, ob Metadaten (Ministry, Date) auch bei *Kind-Knoten (Chunks)* ankommen, nicht nur bei den Dokument-Roots.
   - **Task Sync:** Halte `.opencode/tasks.json` IMMER aktuell. Markiere Tasks erst nach Verifikation als completed.
   - **Review Policy:** Tasks mit `requires_review: true` dürfen nur vom NÄCHSTEN Agenten reviewed werden.

4. **Kanonische Daten:**
   - Nutze für Ministerien IMMER die `MinistryRegistry`. 
   - Behandle Ministeriumsnamen nie als statische Strings, sondern mappt historische Namen (BMWE/BMWi) immer auf die aktuellen Kürzel (BMWK).

## 🚀 Workflow bei Session-Start

1. **Kontext-Check:** Lies zuerst `.opencode/tasks.json`, `next-steps.md` und `.opencode/HANDOFF.md`.
2. **Setup:** Starte die API (`python src/api/search_api.py`) im Hintergrund.
3. **Task-Planung:** Wähle einen Task aus `tasks.json` mit Status `pending`.
4. **Validierung:** Beende die Session erst, wenn ein Playwright-Test grün ist und die `tasks.json` aktualisiert wurde.

## ⚠️ KRITISCHE REGEL: Graph RAG Testing

**WICHTIG für Phase 1+2 Graph RAG:**
- **Code ist fertig** (BM25, Reranking, PPR, k-hop) ✅
- **Embeddings fehlen noch** - Docling läuft auf anderem Computer ⏳
- **End-to-End Tests KÖNNEN NICHT laufen** ohne vollständige ChromaDB Daten ❌

**Was der nächste Agent tun KANN:**
1. ✅ **Unit Tests schreiben** (BM25Index, Reranker, GraphAlgorithms isoliert testen)
2. ✅ **Code Review** (Qualität prüfen, Refactoring)
3. ✅ **Dokumentation** (README, API Docs erweitern)
4. ✅ **Phase 3 vorbereiten** (Query Enhancement Grundstruktur)
5. ✅ **Mock Tests** (Mit Fake-Daten testen)

**Was der nächste Agent NICHT tun soll:**
- ❌ **End-to-End Tests** mit `/api/search/advanced` (warten auf Embeddings)
- ❌ **Benchmarking** (Hit@k, MRR) - benötigt vollständige Daten
- ❌ **Production Deployment** - System nicht E2E getestet

**Wann kann E2E getestet werden?**
- Wenn User sagt: "Docling fertig, Embeddings in ChromaDB"
- Dann: TASK-008 (Automated Embedding Sync) ausführen
- Erst dann: Full E2E Testing mit echten Queries

## 📋 PFLICHT: Status-Check vor Session-Ende

Bevor du die Session beendest, aktualisiere:
1. `.opencode/tasks.json` - Deine completed tasks
2. `.opencode/HANDOFF.md` - Was ist der Stand? Was fehlt noch?
3. `.opencode/STATUS_REPORT.md` - Wenn du ein Major Feature abgeschlossen hast
