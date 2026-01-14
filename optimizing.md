# Optimization & Feedback Log

## Review Status: v0.4.1 (14.01.2026)

### ✅ Positive Feedback to the Agent
- **Crash-Resilience:** The improvement of `src/main_pipeline.py` to be resumeable via hashing is excellent and crucial for large crawls.
- **Structural Integrity:** Hierarchical chunking context (H1 > H2 > H3) is correctly preserved in the graph nodes.
- **Traceability:** Download-URLs are correctly mapped from the manifest to the graph nodes.

### 🛠️ Improvements Made (Post-Review)
1. **Versioning Logic Fix:** Fixed a bug in `src/graph/versioning_logic.py` where the JSON key was hardcoded to `links` instead of `edges` (NetworkX default), preventing `SUPERSEDES` edges from being saved. All 16 versioning links are now permanent.
2. **Rule Extractor Refinement:** 
   - Added `.env` support (via `python-dotenv`).
   - Integrated logic to auto-switch between IONOS (Primary) and Mistral (Quality).
   - Ensured procedural focus: Extraction now explicitly targets compliance/process rules found in the form cabinet.
3. **Environment Setup:** Created the `.env` file with IONOS credentials.
4. **Visualisation:** Added `src/graph/export_d3.py` to allow easy graph exploration in browsers.

### ⚠️ Requirements for Next Phase
- **Embeddings:** IONOS has embedding models available. The next step should utilize these for the RAG integration.
- **Rule Extraction Scale:** Now that the API key is present, a full run is required.
