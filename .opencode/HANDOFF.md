# ⚠️ UPDATED Handoff Instructions (AGVO & UI Search)

**Date:** 2026-01-31
**Last Review:** Antigravity
**Previous Agents:** opencode, Antigravity
**Project Phase:** Production / Scaling 🚀
**Version:** 2.4.1

---

## 🚨 NEW ARCHITECTURE: Expert Knowledge & AGVO

**Summary of Progress (2026-01-31):**
1.  **Expert Knowledge Externalization (Task 43):** Hardcoded concept maps moved to `config/compliance_concepts.json`. Easily extensible without code changes.
2.  **EU-Beihilferecht Integration (Task 44):** AGVO (Allgemeine Gruppenfreistellungsverordnung) integrated into the graph. Key articles (Art 1, 2, 3, 4, 6) are available for RAG.
3.  **UI Rule Search (Task 42):** Sidebar in `dashboard.html` now has a real-time search field to filter extracted rules.
4.  **Graph Reporting (Task 41):** New script `scripts/generate_graph_report.py` provides deep insights into graph health and coverage.
5.  **Autonomous Law Discovery (Task 38):** Fully operational and verified. Missing laws are fetched at runtime.
6.  **Performance:** Vector store load time optimized to <2s using Hybrid Pickle Cache.

### ✅ What to do NEXT:
1.  **Deployment:** Fresh sync of `data/knowledge_graph.json` and `config/` to VPS.
2.  **Expand AGVO:** Add remaining articles of Kapitel III (Specific aid groups) to `src/discovery/import_agvo_manual.py`.
3.  **LSP Cleanup:** Investigate NetworkX `in_edges` callable warnings in `compliance_mapper.py`.

---

## ⚠️ Known Status
-   **Vector Store**: Hybrid (Fast). ~12.9k chunks.
-   **Graph**: 12,870 nodes. High coverage for base laws.
-   **On-Demand**: Active. Tested & Verified.

---

## ✅ Checklist Before Starting
-   [x] Run `venv/bin/python scripts/generate_graph_report.py` for current status.
-   [x] Check `config/compliance_concepts.json` for mapping logic.
-   [x] Open `dashboard.html` and test the new rule search.

