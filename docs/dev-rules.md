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

1. **Kontext-Check:** Lies zuerst `.opencode/tasks.json` und `next-steps.md`.
2. **Setup:** Starte die API (`python src/api/search_api.py`) im Hintergrund.
3. **Task-Planung:** Wähle einen Task aus `tasks.json` mit Status `pending`.
4. **Validierung:** Beende die Session erst, wenn ein Playwright-Test grün ist und die `tasks.json` aktualisiert wurde.
