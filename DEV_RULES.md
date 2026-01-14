# Development Rules & Workflow

Dieser Guide ist für alle Agenten VERPFLICHTEND. Er sichert die Qualität und Konsistenz des Projekts.

## 🛠️ Arbeitsprinzipien

1. **Test-First (UI):** 
   - Jede visuelle Änderung oder API-Erweiterung MUSS mit dem `webapp-testing` Skill (Playwright) verifiziert werden.
   - Erstelle Screenshots von neuen UI-Features und lege sie in `docs/screenshots/` ab.
   - Prüfe Filter und Suchmasken auf doppelte Einträge oder Inkonsistenzen.

2. **Commit-Disziplin:**
   - Erstelle nach JEDEM abgeschlossenen Meilenstein (Task) einen aussagekräftigen Git-Commit.
   - Nutze `git status`, um sicherzustellen, dass keine neuen Module als "untracked" liegen bleiben.

3. **Tribal Knowledge Preservation:**
   - Dokumentiere neue Erkenntnisse über die Struktur des Bundes-Formularschranks sofort in `optimizing.md`.
   - Halte die `NEXTSTEPS.md` immer aktuell (neue Version bei großen Sprüngen).

4. **Kanonische Daten:**
   - Nutze für Ministerien IMMER die `MinistryRegistry`. 
   - Behandle Ministeriumsnamen nie als statische Strings, sondern mappt historische Namen (BMWE/BMWi) immer auf die aktuellen Kürzel (BMWK).

## 🚀 Workflow bei Session-Start

1. Analysiere `docs/PRD.md` (Vision).
2. Lies `optimizing.md` (Fehlervermeidung).
3. Checke `NEXTSTEPS.md` (Offene Tasks).
4. **Validierung:** Starte die API und führe einen ersten UI-Test durch, um den Ist-Zustand zu prüfen.
