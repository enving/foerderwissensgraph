# ⚠️ UPDATED Handoff Instructions (On-Demand Discovery & Speed-Up)

**Date:** 2026-01-31
**Last Review:** Antigravity
**Previous Agents:** opencode, Antigravity
**Project Phase:** Production / Scaling 🚀
**Version:** 2.4.0

---

## 🚨 NEW ARCHITECTURE: Self-Expanding Knowledge Graph

**Summary of Progress (2026-01-31):**
1.  **On-Demand Discovery (Task 38):** The system is now autonomous. If the `ComplianceMapper` identifies a law citation (e.g. "§ 1 LuftVG") that is missing from the Knowledge Graph, it automatically:
    *   Triggers the `LawCrawler` (XML/HTML fallback).
    *   Creates a new Law Node and Chunk Nodes.
    *   Updates the Vector Store at runtime.
    *   Persistence is guaranteed in `knowledge_graph.json`.
2.  **10x Startup Speedup (Task 39):** The `LiteVectorStore` now uses a **Hybrid Cache System**. 
    *   **Pickle Cache:** Rapid binary loading (<2s for 12.5k chunks).
    *   **JSON Backup:** Maintains "Sovereign Data" transparency (human-readable 282MB file).
3.  **VOB Integrated (Task 37):** Key sections of VOB/A and VOB/B were manually imported to ensure baseline coverage for construction-related funding.
4.  **Apify Actor Upgrade:** Updated to support `search_v2` and automated answer generation.

### ✅ What to do NEXT:
1.  **Deployment:** Push the updated `data/knowledge_graph.json` and `data/chroma_db/lite_store.json` to the VPS.
2.  **Reasoning UI:** In `dashboard.html`, add a "Reasoning Trace" to show which laws were automatically discovered during the session.
3.  **Refine Extraction:** Add even more specialized laws to `src/parser/citation_extractor.py` regex as they appear in documents.

---

## ⚠️ Known Status
-   **Vector Store**: Hybrid (Fast). 12.8k chunks.
-   **On-Demand**: Active. Tested with AtG and LuftVG.
-   **Python**: 3.14 compatible.

---

## ✅ Checklist Before Starting
-   [x] Run `venv/bin/python scripts/test_on_demand_crawl.py` to see the magic.
-   [x] Verify `lite_store.pkl` exists for fast loading.

