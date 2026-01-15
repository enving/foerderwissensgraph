# Next Steps & Roadmap (v1.0.0-rc4)

## 📍 Aktueller Status (v1.0.0-rc4)
- [x] **Full Spectrum Graph (BMWK & BMFSFJ):** 57+ Dokumente im Graph.
- [x] **New Expansion (BMBF/BMFSFJ):** `bmbfsfj` Daten (Abrufrichtlinien, BNBest) erfolgreich integriert und gelabelt.
- [x] **Metadata & Equivalence:** Metadaten korrekt gemappt (BMFSFJ statt BMBF für 0324), Äquivalenz-Links (SUPERSEDES) generiert.
- [x] **Local Embeddings:** Vektordatenbank aktualisiert.
- [x] **UI Verification:** Dashboard Visualisierung und Suche getestet (Port 8000/5001).

## 🛠️ Meilensteine & Tasks

### Phase A: Further Expansion (Priorität: Mittel)
- [ ] **BMBF Core:** Crawle und integriere weitere Kern-Richtlinien des BMBF (Bildung & Forschung), da `bmbfsfj` primär Familienministerium war.
- [ ] **Automated Crawler:** Erweitere den Crawler um automatische Ministeriums-Erkennung (nicht nur manuell per Argument).

### Phase D: Graph-RAG Optimization
- [ ] **Answer Engine Tuning:** Verbessere die Prompts der Answer Engine für spezifische Regel-Vergleiche.
- [ ] **Frontend:** "Suche läuft..." Anzeige verbessern, damit User Feedback bekommt.

## 🚀 Session-Start Befehl
"Lies `AGENTS.md` und `NEXTSTEPS.md`. Starte `python -m http.server 8000 --directory docs` und `python src/api/search_api.py`, um die App zu demonstrieren."
