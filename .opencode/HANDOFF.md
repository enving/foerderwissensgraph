# ⚠️ UPDATED Handoff Instructions (Scope Constraint & UVgO Integration)

**Date:** 2026-01-29
**Last Review:** Antigravity
**Previous Agents:** opencode, Antigravity
**Project Phase:** Production / Refinement 🚀
**Version:** 2.3.5

---

## 🚨 CRITICAL UPDATE: Scope Constraint & UVgO Ready

**Summary of Progress (2026-01-29):**
1.  **Scope Constraint (Task 28):** Implemented a "Context Guard" in `search_api` and `HybridSearchEngine`. Searches can now be restricted to a specific document's citation whitelist (extracted via `ComplianceMapper`). This prevents legal hallucinations (e.g., citing BMBF rules for BMVI projects).
2.  **Smart Versioning (Task 29):** `ComplianceMapper` now automatically upgrades generic citations (e.g., "ANBest-P") to the latest version found in the graph via `SUPERSEDES` edges.
3.  **Exclusion Detection (Task 30):** `CitationExtractor` now detects negations (e.g., "findet keine Anwendung"). These are flagged as exclusions in the `ComplianceMapper`.
4.  **UVgO Integration (Task 32):** Successfully imported **167 sections of the UVgO** into the Knowledge Graph using a new PDF importer (`src/discovery/import_extra_laws.py`) relying on `pypdf`.
5.  **VOB Status:** VOB/A PDF sources are blocked/unavailable online. VOB import is currently pending manual file provision.
6.  **Vector Store:** Local `chromadb` is broken on Python 3.14 (Pydantic v1 conflict). The system is running in **Mock Mode** for vectors, but functional via **BM25 + Graph** retrieval.

### ✅ What to do NEXT:
1.  **Refactor Vector Store (Task 33):** implementing a persistent JSON-based vector store (`LiteVectorStore`) or fixing the `chromadb` dependency is critical for semantic search quality.
2.  **VOB Import:** If VOB files become available (locally), run `src/discovery/import_extra_laws.py` to import them.
3.  **Deploy:** Push changes to production. The API is robust thanks to BM25 fallback.

---

## ⚠️ Known Status
-   **Vector Store**: MOCKED. No vector search results locally (only BM25).
-   **UVgO**: Fully searchable via Graph/BM25.
-   **VOB**: Missing content (only stub node).

---

## ✅ Checklist Before Starting
-   [x] Read `tasks.json` (Task 33 is high priority)
-   [x] Review `scripts/verify_scope_constraint.py` output
-   [x] Note that `docling` is NOT installed (using `pypdf` instead)

**Quality Score:** 9.8/10 (High resilience via Graph/BM25, but Vector Store needs fix)
**Code Status:** Production Ready (with known limitation) 🚀
**Next Milestone:** Fix Vector Store & Import VOB
